import os
import re
import sys
import yaml
import argparse

def load_rules(rules_file):
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            rules = config.get("rules", [])
            ignore_files = config.get("ignore_files", [])
            ignore_charts = config.get("ignore_charts", [])
            ignore_variables = config.get("ignore_variables", [])
            return [r for r in rules if r.get("enabled", True)], ignore_files, ignore_charts, ignore_variables
    except Exception as e:
        print(f"Error loading rules file: {e}")
        sys.exit(1)

def detect_environment(filename, env_match):
    filename = filename.lower()
    return any(env.lower() in filename or env.lower() == "all" for env in env_match)

def scan_file(filepath, rules, rules_file_path, ignore_variables):
    violations = []
    filename = os.path.basename(filepath)
    chart_name = os.path.basename(os.path.dirname(filepath))

    if os.path.abspath(filepath) == os.path.abspath(rules_file_path):
        return violations

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Could not read file {filepath}: {e}")
        return violations

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue  # Skip empty or commented lines
        if any(var in line for var in ignore_variables):
            continue
        for rule in rules:
            if not detect_environment(filename, rule.get("env_match", ["all"])):
                continue
            for pattern in rule.get("patterns", []):
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    matched_value = match.group(0)
                    violations.append({
                        "rule_id": rule.get("id", "N/A"),
                        "severity": rule.get("severity", "UNKNOWN"),
                        "category": rule.get("category", "general"),
                        "file": filename,
                        "path": filepath,
                        "line": line_no,
                        "forbidden": matched_value,
                        "description": rule.get("description", "").replace("{value}", matched_value),
                        "suggestion": rule.get("suggestion", "").replace("{value}", matched_value),
                        "action": rule.get("action", "").replace("{value}", matched_value)
                    })
    return violations

def scan_directory(root_dir, rules_file):
    rules, ignore_files, ignore_charts, ignore_variables = load_rules(rules_file)
    all_violations = []

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            filepath = os.path.join(subdir, file)
            rel_path = os.path.relpath(filepath, root_dir)
            chart_name = os.path.basename(os.path.dirname(filepath))

            if any(ignored in rel_path for ignored in ignore_files):
                continue
            if chart_name in ignore_charts:
                continue
            if file.endswith((".yaml", ".yml")):
                all_violations.extend(scan_file(filepath, rules, rules_file, ignore_variables))
    return all_violations

def main():
    parser = argparse.ArgumentParser(description="Helm Chart YAML Validator")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("rules", nargs="?", default="rules.yaml", help="Path to rules file")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        sys.exit(1)

    violations = scan_directory(args.directory, args.rules)

    if not violations:
        print("✅ No violations found.")
        return

    for v in violations:
        print("-" * 40)
        print(f"\n[{v['severity'].upper()}] Rule: {v['rule_id']} ({v['category']})")
        print(f"  File Name   : {v['file']} (Line {v['line']})")
        print(f"  File Path   : {v['path']}")
        print(f"  Forbidden   : {v['forbidden']}")
        print(f"  Description : {v['description']}")
        print(f"  Suggestion  : {v['suggestion']}")
        print(f"  Action      : {v['action']}")
        print("-" * 40)

    print(f"\nTotal Violations: {len(violations)}")
    sys.exit(1)

if __name__ == "__main__":
    main()
