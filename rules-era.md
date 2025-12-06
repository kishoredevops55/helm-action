Here’s a **modern-era, world-class `rules.json`** you can drop into:

`observability-hooks/config/rules.json`

It’s designed for:

* **All envs & all code types** (app + infra + CI)
* **Modern practices**: supply chain, SBOM, secrets, IaC, policy-as-code, test-impact, CODEOWNERS, CI runner governance
* **Plugin style** via `python_callable` for your advanced logic (env misconfig, observability, test impact, etc.)

You can **turn things on/off globally** via `enabled: true/false`
and **per-repo** using your existing `override_rules` / `disable_rules`.

---

### `rules.json` (modern, single file)

```json
{
  "rules": {
    "yaml_lint": {
      "description": "Lint all YAML files (Kubernetes manifests, Helm values, CI configs, etc.)",
      "type": "yamllint",
      "enabled": true,
      "paths": ["**/*.yaml", "**/*.yml"]
    },

    "json_lint": {
      "description": "Validate JSON files are well-formed",
      "type": "shell",
      "enabled": true,
      "paths": ["**/*.json"],
      "cmd": "python -m json.tool {files}",
      "fail_on_nonzero": true"
    },

    "no_large_files": {
      "description": "Block accidentally committed large binaries",
      "type": "python_callable",
      "enabled": true,
      "module": "custom_rules.repo_hygiene",
      "callable": "check_large_files",
      "paths": ["**/*"]
    },

    "forbidden_secrets_patterns": {
      "description": "Block obvious secrets in code / config",
      "type": "regex_forbidden",
      "enabled": true,
      "paths": ["**/*.*"],
      "patterns": [
        "AKIA[0-9A-Z]{16}",
        "ASIA[0-9A-Z]{16}",
        "SECRET_KEY\\s*=",
        "password\\s*=",
        "passwd\\s*=",
        "PRIVATE KEY-----",
        "xoxb-[0-9A-Za-z-]{10,}",
        "ghp_[0-9A-Za-z]{36}",
        "github_pat_[0-9A-Za-z_]{20,}",
        "-----BEGIN OPENSSH PRIVATE KEY-----"
      ]
    },

    "secret_scanner_trufflehog": {
      "description": "Deep secret scanning with trufflehog (optional, can be heavy)",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*"],
      "cmd": "trufflehog filesystem {repo_head} --no-update",
      "fail_on_nonzero": true,
      "run_even_if_no_files_changed": true
    },

    "python_quality": {
      "description": "Modern Python quality gate (ruff + black check + pytest)",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.py", "pyproject.toml", "requirements*.txt"],
      "cmd": "cd {repo_head} && ruff check . && black --check . && pytest",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": true
    },

    "node_quality": {
      "description": "Modern Node quality gate (install + lint/test)",
      "type": "shell",
      "enabled": false,
      "paths": ["package.json", "pnpm-lock.yaml", "yarn.lock"],
      "cmd": "cd {repo_head} && if [ -f package.json ]; then (npm ci || pnpm install || yarn install); fi && (npm test || yarn test || pnpm test)",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": true
    },

    "go_quality": {
      "description": "Go fmt + vet + test",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.go", "go.mod", "go.sum"],
      "cmd": "cd {repo_head} && gofmt -w . && go vet ./... && go test ./...",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": true
    },

    "java_maven_test": {
      "description": "Run Maven tests for Java projects",
      "type": "shell",
      "enabled": false,
      "paths": ["pom.xml"],
      "cmd": "cd {repo_head} && mvn -B verify",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": true
    },

    "dotnet_test": {
      "description": ".NET test execution",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.csproj", "**/*.sln"],
      "cmd": "cd {repo_head} && dotnet test",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": true
    },

    "shellcheck": {
      "description": "Static analysis for shell scripts",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.sh"],
      "cmd": "shellcheck {files}",
      "fail_on_nonzero": true
    },

    "dockerfile_lint": {
      "description": "Lint Dockerfiles using hadolint",
      "type": "shell",
      "enabled": false,
      "paths": ["**/Dockerfile", "**/Dockerfile.*"],
      "cmd": "hadolint {files}",
      "fail_on_nonzero": true
    },

    "sbom_syft": {
      "description": "Generate SBOM using Syft (supply chain visibility)",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*"],
      "cmd": "cd {repo_head} && syft dir:. -o json > sbom.json",
      "run_even_if_no_files_changed": true,
      "fail_on_nonzero": false
    },

    "dependency_scan_osv": {
      "description": "Dependency vulnerability scanning via osv-scanner",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*"],
      "cmd": "osv-scanner --recursive {repo_head}",
      "fail_on_nonzero": true,
      "run_even_if_no_files_changed": true
    },

    "terraform_fmt": {
      "description": "Terraform formatting check",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.tf", "**/*.tfvars"],
      "cmd": "terraform -chdir={repo_head} fmt -check",
      "fail_on_nonzero": true,
      "run_even_if_no_files_changed": true
    },

    "terraform_validate": {
      "description": "Terraform validation",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.tf", "**/*.tfvars"],
      "cmd": "terraform -chdir={repo_head} validate",
      "fail_on_nonzero": true,
      "run_even_if_no_files_changed": true
    },

    "ansible_lint": {
      "description": "Lint Ansible playbooks and roles",
      "type": "shell",
      "enabled": false,
      "paths": ["**/playbook*.yml", "**/roles/**/tasks/*.yml", "**/ansible.cfg"],
      "cmd": "ansible-lint {files}",
      "fail_on_nonzero": true
    },

    "helm_lint": {
      "description": "Helm chart linting",
      "type": "shell",
      "enabled": false,
      "paths": ["**/Chart.yaml"],
      "cmd": "for f in {files}; do helm lint \"$(dirname \\\"$f\\\")\"; done",
      "fail_on_nonzero": true
    },

    "kubeconform": {
      "description": "Validate Kubernetes manifests against schemas",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.yaml", "**/*.yml"],
      "cmd": "kubeconform -summary {files}",
      "fail_on_nonzero": true
    },

    "kustomize_build_validate": {
      "description": "Kustomize build sanity check",
      "type": "shell",
      "enabled": false,
      "paths": ["**/kustomization.yaml"],
      "cmd": "for f in {files}; do kustomize build \"$(dirname \\\"$f\\\")\" >/dev/null; done",
      "fail_on_nonzero": true
    },

    "github_actions_lint": {
      "description": "Modern sanity check for GitHub Actions workflows",
      "type": "python_callable",
      "enabled": true,
      "module": "custom_rules.ci_configs",
      "callable": "check_github_actions",
      "paths": [".github/workflows/*.yml", ".github/workflows/*.yaml"]
    },

    "ci_cycles_and_runners": {
      "description": "Enforce central-runner usage and prevent local runner abuse in CI configs",
      "type": "python_callable",
      "enabled": true,
      "module": "custom_rules.ci_configs",
      "callable": "check_runner_policies",
      "paths": [".github/workflows/*.yml", ".github/workflows/*.yaml"]
    },

    "gitlab_ci_lint": {
      "description": "Lint GitLab CI config",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.ci_configs",
      "callable": "check_gitlab_ci",
      "paths": [".gitlab-ci.yml"]
    },

    "azure_pipelines_lint": {
      "description": "Lint Azure Pipelines YAML",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.ci_configs",
      "callable": "check_azure_pipelines",
      "paths": ["azure-pipelines.yml", "azure-pipelines.yaml"]
    },

    "env_misconfig_checks": {
      "description": "Cross-env and cloud misconfiguration rules (AKS vs GKE, prod vs perf, secret usage, etc.)",
      "type": "python_callable",
      "enabled": true,
      "module": "custom_rules.env_misconfig",
      "callable": "run_env_misconfig_checks",
      "paths": ["**/*.yaml", "**/*.yml", "**/*.json"]
    },

    "policy_as_code_opa": {
      "description": "Generic policy-as-code validation using OPA/Conftest",
      "type": "shell",
      "enabled": false,
      "paths": ["**/*.yaml", "**/*.yml", "**/*.json", "**/*.hcl"],
      "cmd": "conftest test {repo_head}",
      "fail_on_nonzero": true,
      "run_even_if_no_files_changed": true
    },

    "observability_config_checks": {
      "description": "Validate logging/metrics/tracing configuration consistency across envs",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.observability",
      "callable": "check_observability_configs",
      "paths": ["**/*.yaml", "**/*.yml", "**/*.json"]
    },

    "test_impact_analysis": {
      "description": "Modern test impact analysis to only run affected tests",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.test_impact",
      "callable": "run_test_impact_analysis",
      "paths": ["**/*"]
    },

    "conventional_commits": {
      "description": "Enforce Conventional Commit messages for better change intelligence",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.git_metadata",
      "callable": "check_conventional_commits",
      "paths": ["**/*"]
    },

    "codeowners_coverage": {
      "description": "Ensure all changed paths are covered by CODEOWNERS for ownership and approvals",
      "type": "python_callable",
      "enabled": false,
      "module": "custom_rules.git_metadata",
      "callable": "check_codeowners_coverage",
      "paths": ["**/*"]
    }
  }
}
```

---

### How this aligns with “modern era” thinking

* **Security-by-default**

  * `forbidden_secrets_patterns`, `no_large_files` always on.
  * Optional deep scans: Trufflehog, OSV, SBOM via Syft.

* **Supply-chain & compliance**

  * SBOM (`sbom_syft`) and `dependency_scan_osv` ready to enable per org policy.
  * `policy_as_code_opa` hook for OPA/Conftest.

* **IaC + Cloud**

  * Terraform fmt/validate, Ansible lint, Helm, Kustomize, Kubeconform.
  * `env_misconfig_checks` for your **AKS vs GKE, prod vs perf, KV usage, etc.** logic.

* **App code quality gates**

  * Single composite rules per stack (`python_quality`, `node_quality`, `go_quality`, etc.)
  * Easy to turn them on **per repo** with overrides when that repo is ready.

* **CI & Governance**

  * `github_actions_lint` and `ci_cycles_and_runners` enforce:

    * No local runners.
    * Only central, approved runners.
    * No unsafe `run: sudo ...` patterns (you implement in the Python rule).

* **Git-aware, org-wide intelligence**

  * `test_impact_analysis` → speed + reliability.
  * `conventional_commits` → standardised history.
  * `codeowners_coverage` → ownership & approval enforcement.

---

If you want, next I can:

* Generate **skeletons** for:

  * `custom_rules.env_misconfig`
  * `custom_rules.ci_configs`
  * `custom_rules.repo_hygiene`
  * `custom_rules.git_metadata`
  * `custom_rules.observability`
  * `custom_rules.test_impact`

so you just drop them in and start filling your AKS/GKE/env rules.
