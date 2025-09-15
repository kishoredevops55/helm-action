"""
validator.py

Main dynamic Helm chart validator.
- Loads rule YAMLs from rules/ (recursively)
- Supports rule types: jmespath, regex_on_manifest, exists, allow_forbidden, python_plugin
- Loads Python plugin hooks from rules_plugins/
- Renders helm templates using `helm template`
- Maps rendered manifests back to source files using Helm "# Source:" markers
- Searches template files for offending snippets and reports line numbers
- Prints a console table of failures with absolute file path, line numbers, severity, rule id, message, suggestion
- Exits non-zero when any critical failures are present

Usage:
  python validator.py --charts ./charts --rules ./rules --plugins ./rules_plugins --env prod --values values-prod.yaml --concurrency 8 --out report.json

Requirements:
  pip install pyyaml jmespath openpyxl tabulate
  helm (CLI) on PATH

"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import jmespath
import yaml
from tabulate import tabulate

# ---------------- dataclasses ---------------------------------------------------

@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    chart_path: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

# ---------------- helpers -------------------------------------------------------

def run_cmd(cmd: List[str], cwd: Optional[str] = None, timeout: int = 120) -> (int, str, str):
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def discover_chart_dirs(root: str) -> List[str]:
    charts = []
    for dirpath, dirnames, filenames in os.walk(root):
        if 'Chart.yaml' in filenames:
            charts.append(dirpath)
    return charts


def load_rules_from_folder(rules_folder: str) -> List[Dict[str, Any]]:
    rules = []
    for path in sorted(Path(rules_folder).rglob('*.yml')) + sorted(Path(rules_folder).rglob('*.yaml')):
        try:
            with open(path, 'r') as f:
                raw = yaml.safe_load(f) or {}
                if isinstance(raw, list):
                    rules.extend(raw)
                elif isinstance(raw, dict) and 'rules' in raw:
                    rules.extend(raw['rules'])
                else:
                    # file might contain a single rule or multiple top-level docs
                    # try to parse multiple docs
                    f.seek(0)
                    docs = list(yaml.safe_load_all(f))
                    for d in docs:
                        if d is None:
                            continue
                        if isinstance(d, list):
                            rules.extend(d)
                        elif isinstance(d, dict):
                            rules.append(d)
        except Exception as e:
            print(f"Failed to load rules from {path}: {e}")
    return rules


def render_helm_template(chart_dir: str, values_files: List[str], env: Optional[str], helm_binary: str = 'helm') -> (bool, str, str):
    cmd = [helm_binary, 'template', chart_dir]
    for vf in values_files:
        cmd.extend(['-f', vf])
    if env:
        cmd.extend(['--set', f'global.env={env}'])
    returncode, out, err = run_cmd(cmd, cwd=chart_dir, timeout=180)
    return returncode == 0, out, err


def split_multi_yaml(yaml_text: str) -> List[Dict[str, Any]]:
    docs = []
    for doc in yaml.safe_load_all(yaml_text):
        if doc is None:
            continue
        docs.append(doc)
    return docs


def parse_helm_output_for_sources(helm_output: str) -> List[Dict[str, str]]:
    parts = []
    current = {'source': None, 'manifest': ''}
    for line in helm_output.splitlines():
        if line.strip().startswith('# Source:'):
            src = line.strip()[len('# Source:'):].strip()
            if current['source'] or current['manifest'].strip():
                parts.append(current)
            current = {'source': src, 'manifest': ''}
        else:
            current['manifest'] += line + '\n'
    if current['source'] or current['manifest'].strip():
        parts.append(current)
    return parts


def find_snippet_line_numbers(abs_path: str, snippet_regex: str) -> List[int]:
    if not abs_path or not os.path.exists(abs_path):
        return []
    try:
        pat = re.compile(snippet_regex)
    except re.error:
        try:
            pat = re.compile(re.escape(snippet_regex))
        except Exception:
            return []
    lines = []
    with open(abs_path, 'r', errors='ignore') as f:
        for i, l in enumerate(f, start=1):
            if pat.search(l):
                lines.append(i)
    return lines

# ---------------- validator core ------------------------------------------------

class Validator:
    def __init__(self, rules: List[Dict[str, Any]], plugins_folder: Optional[str] = None):
        self.rules = rules
        self.plugins = {}
        if plugins_folder:
            self.load_plugins(plugins_folder)

    def load_plugins(self, folder: str):
        folder = Path(folder)
        if not folder.exists():
            return
        sys.path.insert(0, str(folder.resolve()))
        for p in folder.glob('*.py'):
            name = p.stem
            try:
                module = __import__(name)
                if hasattr(module, 'register'):
                    hooks = module.register()
                    self.plugins.update(hooks)
            except Exception as e:
                print(f"Plugin load failed {p}: {e}")

    def validate_rendered(self, chart_dir: str, rendered_yaml: str, context: Dict[str, Any]) -> List[RuleResult]:
        results: List[RuleResult] = []
        docs = split_multi_yaml(rendered_yaml)
        for rule in self.rules:
            try:
                rr = self.apply_rule(rule, docs, chart_dir, context)
                results.append(rr)
            except Exception as e:
                results.append(RuleResult(rule_id=rule.get('id','unknown'), rule_name=rule.get('name','unnamed'), chart_path=chart_dir, passed=False, message=f'error applying rule: {e}'))
        return results

    def apply_rule(self, rule: Dict[str, Any], docs: List[Dict[str, Any]], chart_dir: str, context: Dict[str, Any]) -> RuleResult:
        rid = rule.get('id', rule.get('name','anon'))
        name = rule.get('name','unnamed rule')
        rtype = rule.get('type','jmespath')
        # default severity
        severity = rule.get('severity','warning')
        suggestion = rule.get('suggestion','')

        if rtype == 'jmespath':
            expr = rule.get('expr') or rule.get('match')
            match = False
            hits = []
            if not expr:
                return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=True, message='no expr provided')
            for d in docs:
                try:
                    res = jmespath.search(expr, d)
                except Exception:
                    res = None
                if res:
                    hits.append(res)
                    match = True
            expect = rule.get('expect', 'present')
            passed = (not match) if expect == 'absent' else match
            msg = rule.get('message','')
            return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=passed, message=msg, details={'hits': hits, 'severity': severity, 'suggestion': suggestion})

        elif rtype == 'exists':
            field = rule.get('field')
            found = False
            for d in docs:
                v = jmespath.search(field, d)
                if v:
                    found = True
                    break
            passed = found if rule.get('expect','present')=='present' else not found
            return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=passed, message=rule.get('message',''), details={'severity': severity, 'suggestion': suggestion})

        elif rtype == 'regex_on_manifest':
            pat = rule.get('pattern')
            try:
                compiled = re.compile(pat)
            except Exception:
                compiled = re.compile(re.escape(pat))
            manifest_text = '\n'.join([yaml.safe_dump(d) for d in docs])
            matched = bool(compiled.search(manifest_text))
            expect = rule.get('expect','present')
            passed = (not matched) if expect=='absent' else matched
            return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=passed, message=rule.get('message',''), details={'severity': severity, 'suggestion': suggestion, 'pattern': pat})

        elif rtype == 'allow_forbidden':
            allow = [s.lower() for s in rule.get('allow', [])]
            forbidden = [s.lower() for s in rule.get('forbidden', [])]
            manifest_text = '\n'.join([yaml.safe_dump(d).lower() for d in docs])
            found_forbidden = [f for f in forbidden if f in manifest_text]
            found_allowed = [a for a in allow if a in manifest_text]
            passed = (len(found_forbidden)==0)
            details = {'found_forbidden': found_forbidden, 'found_allowed': found_allowed, 'severity': severity, 'suggestion': suggestion}
            return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=passed, message=rule.get('message',''), details=details)

        elif rtype == 'python_plugin':
            plugin = rule.get('plugin')
            if plugin in self.plugins:
                try:
                    out = self.plugins[plugin](docs=docs, context=context, rule=rule)
                    passed, message, details = out
                    details = details or {}
                    details.update({'severity': severity, 'suggestion': suggestion})
                    return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=passed, message=message, details=details)
                except Exception as e:
                    return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=False, message=f'plugin error: {e}', details={'severity': 'critical'})
            else:
                return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=False, message=f'plugin not found: {plugin}', details={'severity': 'critical'})

        else:
            return RuleResult(rule_id=rid, rule_name=name, chart_path=chart_dir, passed=False, message=f'unknown rule type: {rtype}', details={'severity': 'critical'})

# ---------------- reporting ----------------------------------------------------

def write_json_report(results: List[RuleResult], outpath: str):
    arr = []
    for r in results:
        arr.append({
            'rule_id': r.rule_id,
            'rule_name': r.rule_name,
            'chart_path': r.chart_path,
            'passed': r.passed,
            'message': r.message,
            'details': r.details,
        })
    with open(outpath, 'w') as f:
        json.dump(arr, f, indent=2, default=str)


def pretty_print_results_table(results: List[RuleResult]):
    rows = []
    for r in results:
        src = r.details.get('source_file') or r.chart_path
        ln = r.details.get('line_numbers') or []
        ln_text = ','.join([str(x) for x in ln]) if ln else ''
        sev = str(r.details.get('severity') or r.details.get('severity','')).upper()
        rows.append([src, ln_text, sev, r.rule_id, r.message or '', r.details.get('suggestion','')])
    if not rows:
        print('\nNo issues found.\n')
        return
    headers = ['File Path','Line(s)','Severity','Rule','Message','Suggestion']
    print('\n' + tabulate(rows, headers=headers, tablefmt='github') + '\n')

# ---------------- orchestration -------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--charts', required=True)
    ap.add_argument('--rules', required=True)
    ap.add_argument('--plugins', required=False)
    ap.add_argument('--env', required=False)
    ap.add_argument('--values', nargs='*', default=[])
    ap.add_argument('--out', default='chart_validation_report.json')
    ap.add_argument('--concurrency', type=int, default=4)
    ap.add_argument('--helm-binary', default='helm')
    args = ap.parse_args()

    rules = load_rules_from_folder(args.rules)
    validator = Validator(rules=rules, plugins_folder=args.plugins)

    chart_dirs = discover_chart_dirs(args.charts)
    print(f"Found {len(chart_dirs)} charts to validate")

    lock = threading.Lock()
    all_results: List[RuleResult] = []

    def work(chart_dir: str):
        success, out, err = render_helm_template(chart_dir, args.values or [], args.env, helm_binary=args.helm_binary)
        context = {'env': args.env}
        if not success:
            rr = RuleResult(rule_id='helm_template_fail', rule_name='helm template failed', chart_path=chart_dir, passed=False, message=f'helm template failed: {err[:200]}', details={'severity':'critical'})
            with lock:
                all_results.append(rr)
            return
        parts = parse_helm_output_for_sources(out)
        for part in parts:
            source_rel = part.get('source')
            manifest_text = part.get('manifest')
            abs_source = None
            if source_rel:
                if '/' in source_rel:
                    rel_after_chart = source_rel.split('/',1)[1]
                else:
                    rel_after_chart = source_rel
                candidate = os.path.join(chart_dir, rel_after_chart)
                if os.path.exists(candidate):
                    abs_source = os.path.abspath(candidate)
            docs = split_multi_yaml(manifest_text)
            results = validator.validate_rendered(chart_dir, manifest_text, {**context, 'source_file': abs_source})
            for res in results:
                if not res.passed:
                    res.details.setdefault('source_file', abs_source)
                    rule_def = next((rr for rr in rules if rr.get('id',rr.get('name'))==res.rule_id), None)
                    if rule_def:
                        res.details['severity'] = rule_def.get('severity','warning')
                        res.details['suggestion'] = rule_def.get('suggestion','')
                        if rule_def.get('type') == 'regex_on_manifest' and rule_def.get('pattern') and abs_source:
                            ln = find_snippet_line_numbers(abs_source, rule_def.get('pattern'))
                            res.details['line_numbers'] = ln
                        elif rule_def.get('type') == 'allow_forbidden' and abs_source:
                            fterms = rule_def.get('forbidden', [])
                            ln_all = []
                            for t in fterms:
                                ln_all.extend(find_snippet_line_numbers(abs_source, re.escape(t)))
                            res.details['line_numbers'] = sorted(set(ln_all))
                    with lock:
                        all_results.append(res)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(work, c) for c in chart_dirs]
        for f in concurrent.futures.as_completed(futures):
            pass

    write_json_report(all_results, args.out)
    failures = [r for r in all_results if not r.passed]
    pretty_print_results_table(failures)

    # exit codes: 0 = ok, 1 = warnings/failures, 2 = critical failures
    severities = [str(r.details.get('severity','warning')).lower() for r in failures]
    if any(s == 'critical' for s in severities):
        sys.exit(2)
    elif failures:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
