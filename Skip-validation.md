Below is the **README-ready snippet** you asked for.
It contains **ONLY what to add**, written in **clean, enterprise documentation style**.
No extra explanation, no redesign, no app-repo changes.

---

# 🔕 Repository-Level Validation Disable (Central Workflow)

This section documents how to **disable validation for a specific repository** using a **repo-local override file**, while keeping **all execution centralized**.

---

## 📍 Location

Central workflow file:

```
esgh-central-workflow-aut/
└─ .github/workflows/helm-chart-pr-gatekeeper.yml
```

---

## ➕ Step 1: Add Repo Enablement Evaluation

Add the following step **immediately after** the existing step
`Check for repo-specific overrides`.

```yaml
- name: Evaluate repo_enabled flag
  id: repo-enabled
  working-directory: target-repo-head
  run: |
    OVERRIDE_FILE="${{ inputs.repo-override-path }}"

    # Default behavior
    REPO_ENABLED=true

    if [ -f "$OVERRIDE_FILE" ]; then
      REPO_ENABLED=$(jq -r '.repo_enabled // true' "$OVERRIDE_FILE")
    fi

    echo "repo_enabled=$REPO_ENABLED" >> $GITHUB_OUTPUT

    if [ "$REPO_ENABLED" = "false" ]; then
      echo "🔕 Repository validation DISABLED via override file"
    else
      echo "✅ Repository validation ENABLED"
    fi
```

---

## ➕ Step 2: Guard the Validation Engine Execution

Modify the existing **Run validation engine** step by adding a condition.

### Before

```yaml
- name: Run validation engine
```

### After

```yaml
- name: Run validation engine
  if: steps.repo-enabled.outputs.repo_enabled == 'true'
```

---

## ➕ (Optional) Step 3: Emit Skip Notice

Add this step **after** the validation engine step to improve audit visibility.

```yaml
- name: Validation skipped (repo disabled)
  if: steps.repo-enabled.outputs.repo_enabled == 'false'
  run: |
    echo "🔕 Validation skipped"
    echo "Reason: repo_enabled=false in repo override file"
```

---

## 📄 Repo Override File (Application Repository)

To disable validation for a repository, create:

```
.github/esob-observability-hooks.json
```

```json
{
  "repo_enabled": false
}
```

---

## ✅ Result

* Central workflow is always invoked
* Validation engine does **not** execute when disabled
* No runners or logic exist in app repositories
* Full auditability and governance preserved

---

✔ Enterprise-compliant
✔ Zero app-repo execution
✔ Centralized control maintained
