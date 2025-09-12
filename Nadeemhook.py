#!/usr/bin/env python3
"""
scripts/validate.py

Usage (in CI): python scripts/validate.py --base-ref origin/main --charts-root helm-charts

Outputs:
 - helm-validation-report.pdf
 - helm-validation-summary.json
Exit code 1 if any rule with severity 'error' failed.
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from ruamel.yaml import YAML
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ------------------------------
# Helper utilities
# ------------------------------
yaml_ruamel = YAML()

def run_cmd(cmd, cwd=None, check=True):
    print(f">> Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    if r.stdout:
        print(r.stdout.strip())
    if r.stderr:
        print(r.stderr.strip(), file=sys.stderr)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (rc={r.returncode})")
    return r

def get_changed_files(base_ref):
    # Use git diff base_ref...HEAD to list PR file changes.
    cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    r = run_cmd(cmd, check=False)
    files = []
    if r.stdout:
        files = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return files

def map_files_to_charts(files, charts_root):
    charts = set()
    for f in files:
        if f.startswith(charts_root + "/"):
            parts = f.split("/")
            if len(parts) >= 2:
                charts.add(os.path.join(parts[0], parts[1]))
    return sorted(charts)

def load_rules(rules_file):
    with open(rules_file, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("rules", [])

# glob matching helper
def files_matching_chart(chart_dir, pattern):
    # pattern relative to chart_dir. Use rglob-like match for simple glob patterns.
    root = Path(chart_dir)
    matches = []
    # if pattern is like 'values-prod.yaml' match file directly
    for p in root.rglob("*"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if fnmatch.fnmatch(rel, pattern):
            matches.append(p)
    return matches

def all_yaml_files(chart_dir):
    root = Path(chart_dir)
    return [p for p in root.rglob("*") if p.suffix in (".yml", ".yaml")]

# Read file safe
def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""

# Regex search with line numbers
def regex_find_in_text(text, pattern, flags=re.IGNORECASE):
    try:
        pat = re.compile(pattern, flags)
    except re.error:
        pat = re.compile(re.escape(pattern), flags)
    results = []
    for m in pat.finditer(text):
        start = m.start()
        line = text.count("\n", 0, start) + 1
        snippet = text.splitlines()[line-1].strip() if text else ""
        results.append({"line": line, "match": m.group(0), "snippet": snippet})
    return results

# YAML load with ruamel for possible line numbers
def load_yaml_doc(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
            # ruamel returns Python objects with some line info for nodes
            try:
                obj = yaml_ruamel.load(content)
            except Exception:
                obj = None
            return content, obj
    except Exception:
        return "", None

# lookup dot-path within Python dict/ruamel object, supports '[]' for arrays
def lookup_dot_path(obj, dotpath):
    if obj is None:
        return None
    parts = dotpath.split(".")
    cur = obj
    for p in parts:
        if p.endswith("[]"):
            key = p[:-2]
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
                if isinstance(cur, list) and len(cur) > 0:
                    cur = cur[0]
                else:
                    return None
            else:
                return None
        else:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return None
    return cur

# numeric compares: CPU (500m), memory (1Gi), and integers
def parse_cpu_to_millicores(val):
    try:
        s = str(val).strip()
        if s.endswith("m"):
            return int(float(s[:-1]))
        return int(float(s) * 1000)
    except Exception:
        return None

def parse_memory_to_bytes(val):
    try:
        s = str(val).strip()
        units = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4, "K": 1000, "M": 1000**2, "G": 1000**3}
        for u, mul in units.items():
            if s.endswith(u):
                return int(float(s[:-len(u)]) * mul)
        return int(float(s))
    except Exception:
        return None

def numeric_check_pass(value, min_v=None, max_v=None):
    # Decide CPU or memory or integer by suffix
    if value is None:
        return False
    if min_v is None and max_v is None:
        return True
    # CPU-like?
    if isinstance(value, (int, float)) or re.match(r"^\d+(\.\d+)?(m)?$", str(value)):
        if str(min_v).endswith("m") or str(value).endswith("m") or (min_v and "m" in str(min_v)):
            v = parse_cpu_to_millicores(value)
            vmin = parse_cpu_to_millicores(min_v) if min_v else None
            vmax = parse_cpu_to_millicores(max_v) if max_v else None
            if v is None:
                return False
            if vmin is not None and v < vmin:
                return False
            if vmax is not None and v > vmax:
                return False
            return True
        # memory?
        if any(x in str(min_v or "") for x in ["Mi","Gi","Ki"]) or any(x in str(value) for x in ["Mi","Gi","Ki"]):
            v = parse_memory_to_bytes(value)
            vmin = parse_memory_to_bytes(min_v) if min_v else None
            vmax = parse_memory_to_bytes(max_v) if max_v else None
            if v is None:
                return False
            if vmin is not None and v < vmin:
                return False
            if vmax is not None and v > vmax:
                return False
            return True
        # integer fallback
        try:
            vi = int(value)
            if min_v is not None and vi < int(min_v):
                return False
            if max_v is not None and vi > int(max_v):
                return False
            return True
        except Exception:
            return False
    return False

# ------------------------------
# Validation core
# ------------------------------
def validate_chart(chart_dir, rules):
    chart_dir = Path(chart_dir)
    issues = []
    # collect all YAML files once
    yaml_files = all_yaml_files(chart_dir)

    # run helm lint (non-fatal but capture output as warning)
    try:
        run_cmd(["helm", "lint", str(chart_dir)], check=False)
    except Exception as e:
        issues.append({
            "chart": str(chart_dir),
            "file": str(chart_dir / "Chart.yaml"),
            "line": 0,
            "severity": "warning",
            "rule": "helm-lint",
            "message": f"helm lint had problems: {e}",
            "suggestion": "Run 'helm lint' locally for details."
        })

    for rule in rules:
        rid = rule.get("id") or rule.get("name") or "unnamed"
        name = rule.get("name") or rule.get("id") or rule.get("description", "")
        severity = str(rule.get("severity", "error")).lower()
        suggestion = rule.get("suggestion", "")

        # resolve files list (if omitted => all YAMLs)
        file_patterns = rule.get("files")
        if not file_patterns:
            target_files = yaml_files
        else:
            # if file_patterns is list of strings
            target_files = []
            for pat in file_patterns:
                # supporting wildcard patterns like values*.yaml or templates/*.yaml or Chart.yaml
                matches = files_matching_chart(chart_dir, pat)
                target_files.extend(matches)

        target_files = sorted(set(target_files))

        # apply deny_patterns (regex) to file contents
        for fpath in target_files:
            content = read_file(fpath)
            # deny_patterns can be at rule level or file-level (old schemas). Support both.
            patterns = []
            if rule.get("deny_patterns"):
                patterns = rule.get("deny_patterns")
            # support nested file-specific deny in rule (like 'files' as objects) — we keep simple YAML schema currently
            for pat in patterns:
                hits = regex_find_in_text(content, pat)
                for h in hits:
                    issues.append({
                        "chart": str(chart_dir),
                        "file": str(fpath),
                        "line": h["line"],
                        "severity": severity,
                        "rule": rid,
                        "message": f"Regex '{pat}' matched: {h['match']}",
                        "snippet": h["snippet"],
                        "suggestion": suggestion
                    })

        # apply required_fields: YAML-aware
        for fpath in target_files:
            content, doc = load_yaml_doc(fpath)
            if doc is None:
                # not YAML-parsable (templated) — skip YAML-aware checks for this file
                continue
            for req in rule.get("required_fields", []):
                val = lookup_dot_path(doc, req)
                if val is None:
                    issues.append({
                        "chart": str(chart_dir),
                        "file": str(fpath),
                        "line": 0,
                        "severity": severity,
                        "rule": rid,
                        "message": f"Missing required field '{req}'",
                        "suggestion": suggestion
                    })

        # apply deny_fields: YAML-aware (presence check)
        for fpath in target_files:
            content, doc = load_yaml_doc(fpath)
            if doc is None:
                continue
            for deny in rule.get("deny_fields", []):
                val = lookup_dot_path(doc, deny)
                if val is not None:
                    issues.append({
                        "chart": str(chart_dir),
                        "file": str(fpath),
                        "line": 0,
                        "severity": severity,
                        "rule": rid,
                        "message": f"Forbidden field present '{deny}'",
                        "suggestion": suggestion
                    })

        # apply numeric_check: either compare to min/max constants or to other field (min_field)
        numeric = rule.get("numeric_check")
        if numeric:
            key = numeric.get("key")
            min_val = numeric.get("min")
            max_val = numeric.get("max")
            min_field = numeric.get("min_field")  # compare to other field in same file
            for fpath in target_files:
                content, doc = load_yaml_doc(fpath)
                if doc is None:
                    continue
                val = lookup_dot_path(doc, key)
                if val is None:
                    issues.append({
                        "chart": str(chart_dir),
                        "file": str(fpath),
                        "line": 0,
                        "severity": severity,
                        "rule": rid,
                        "message": f"Numeric key '{key}' not present",
                        "suggestion": suggestion
                    })
                    continue
                # if min_field is specified, fetch its value
                if min_field:
                    min_val_actual = lookup_dot_path(doc, min_field)
                    ok = numeric_check_pass(val, min_val_actual, max_val)
                    if not ok:
                        issues.append({
                            "chart": str(chart_dir),
                            "file": str(fpath),
                            "line": 0,
                            "severity": severity,
                            "rule": rid,
                            "message": f"{key} ({val}) < {min_field} ({min_val_actual}) or fails numeric check",
                            "suggestion": suggestion
                        })
                else:
                    ok = numeric_check_pass(val, min_val, max_val)
                    if not ok:
                        issues.append({
                            "chart": str(chart_dir),
                            "file": str(fpath),
                            "line": 0,
                            "severity": severity,
                            "rule": rid,
                            "message": f"{key} ({val}) fails numeric check min={min_val} max={max_val}",
                            "suggestion": suggestion
                        })

        # conditional and environment-aware rules could be added similarly (skipping for current generic schema)
    return issues

# ------------------------------
# PDF & JSON report generation
# ------------------------------
def generate_pdf_report(issues, out_path="helm-validation-report.pdf"):
    styles = getSampleStyleSheet()
    title = Paragraph("Helm Validation Report", styles["Title"])
    generated = Paragraph(f"Generated: {datetime.utcnow().isoformat()} UTC", styles["Normal"])
    rows = [["Chart", "File", "Line", "Severity", "Rule", "Message", "Snippet", "Suggestion"]]
    for it in issues:
        rows.append([
            it.get("chart", ""),
            it.get("file", ""),
            str(it.get("line", "")),
            it.get("severity", ""),
            it.get("rule", ""),
            it.get("message", "")[:200],
            it.get("snippet", "")[:200],
            it.get("suggestion", "")[:200]
        ])
    doc = SimpleDocTemplate(out_path, pagesize=landscape(A4), leftMargin=12, rightMargin=12, topMargin=12, bottomMargin=12)
    elements = [title, Spacer(1,6), generated, Spacer(1,12)]
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2E86AB")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    elements.append(table)
    doc.build(elements)
    print(f"PDF report written to: {out_path}")

# ------------------------------
# Main
# ------------------------------
def main():
    parser = argparse.ArgumentParser(description="Helm charts validator")
    parser.add_argument("--base-ref", required=True, help="git base ref (eg: origin/main)")
    parser.add_argument("--charts-root", default="helm-charts", help="root folder for charts")
    parser.add_argument("--rules", default="rules.yaml", help="rules file path")
    parser.add_argument("--report-out", default="helm-validation-report.pdf", help="PDF path")
    parser.add_argument("--summary", default="helm-validation-summary.json", help="JSON summary output")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    changed_files = get_changed_files(args.base_ref)
    changed_charts = map_files_to_charts(changed_files, args.charts_root)

    # no changes -> produce empty report and exit 0
    if not changed_charts:
        print("No changed charts detected in this PR. Exiting OK.")
        # empty report
        generate_pdf_report([], out_path=args.report_out)
        with open(args.summary, "w") as fh:
            json.dump({"charts_validated": [], "issues": []}, fh, indent=2)
        sys.exit(0)

    print(f"Found changed charts: {changed_charts}")
    all_issues = []
    for ch in changed_charts:
        print(f"Validating chart: {ch}")
        try:
            issues = validate_chart(ch, rules)
        except Exception as e:
            # if validator itself fails for a chart, add an error record
            issues = [{
                "chart": ch,
                "file": ch,
                "line": 0,
                "severity": "error",
                "rule": "validator-exception",
                "message": str(e),
                "suggestion": "Validator crashed on this chart; inspect logs"
            }]
        all_issues.extend(issues)

    # write summary JSON
    with open(args.summary, "w", encoding="utf-8") as fh:
        json.dump({"charts_validated": changed_charts, "issues": all_issues}, fh, indent=2)

    # generate PDF
    generate_pdf_report(all_issues, out_path=args.report_out)

    # determine exit code
    has_error = any(i.get("severity","").lower() == "error" for i in all_issues)
    if has_error:
        print(f"Validation resulted in {sum(1 for i in all_issues if i.get('severity','').lower()=='error')} error(s). Failing.")
        sys.exit(1)
    print("Validation completed: no errors found.")
    sys.exit(0)

if __name__ == "__main__":
    import argparse
    main()

