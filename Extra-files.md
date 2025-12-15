Below is a **README-ready section** that gives **Option 1 (Validate ONLY changed files)** and shows **exactly WHERE to add it in your CENTRAL workflow**.
Only actionable content, no extra explanation.

---

# 🔍 Option 1: Validate Only PR-Changed Files (Diff-Based Validation)

This option restricts validation to **only the files modified in the pull request**, preventing unrelated or legacy files from being validated.

---

## 📍 Applies To

Central workflow:

```
.github/workflows/helm-chart-pr-gatekeeper.yml
```

---

## 📌 Where to Add

Add the following step **AFTER**:

```
Checkout target repo (BASE - main branch)
Checkout target repo (HEAD - PR changes)
```

and **BEFORE**:

```
Run validation engine
```

---

## ➕ Step 1: Collect Changed Files (PR Diff)

```yaml
- name: Collect PR changed files
  id: changed-files
  working-directory: target-repo-head
  run: |
    echo "🔍 Collecting files changed in PR..."

    git diff --name-only \
      ${{ inputs.pr-base-sha }} \
      ${{ inputs.pr-head-sha }} > changed_files.txt

    echo "Changed files:"
    cat changed_files.txt || true

    echo "changed_files_path=changed_files.txt" >> $GITHUB_OUTPUT
```

---

## ➕ Step 2: Pass Changed Files to Validation Engine

Modify the **Run validation engine** step.

### Add these environment variables

```yaml
env:
  SCAN_MODE: changed-only
  CHANGED_FILES_PATH: ${{ github.workspace }}/target-repo-head/${{ steps.changed-files.outputs.changed_files_path }}
```

---

## 🧠 Expected Validation Engine Behavior

When `SCAN_MODE=changed-only`:

* Only files listed in `changed_files.txt` are validated
* Files outside the PR diff are ignored
* No legacy or unrelated files are scanned

---

## 📄 Example `changed_files.txt`

```
helm/app1/values.yaml
src/config/settings.py
.github/workflows/pr-validation.yml
```

---

## ✅ Result

* Validation runs **only on PR-modified files**
* No false failures from untouched files
* Faster execution
* Predictable behavior across all repos

---

## 🧩 Notes

* BASE and HEAD checkouts **must remain**
* This logic works with **dynamic runners**
* No app-repo changes required

---

✔ Centralized
✔ Deterministic
✔ Enterprise-safe
