Thanks for the screenshots — I **see both problems still happening:**

✅ Only *one* file changed in the PR
❌ Validation is still scanning *many* files
❌ Email notification is still being skipped even though validation ran and failed

Let’s fix this with **precise, concrete changes**.

---

# ✅ Updated Single README Section — Clear Steps

This version includes **exact fixes** for:

1. **Accurate PR diff with merge-base**
2. **Validation engine scanning only PR-changed files**
3. **Email only when validation actually ran and failed**

---

## 📌 Step A — Fetch Full Git History

**Why:** Needed for merge-base comparison.

### Apply to BOTH checkouts:

**Checkout HEAD**

```yaml
- name: Checkout target repo (HEAD - PR changes)
  uses: actions/checkout@v4
  with:
    repository: ${{ inputs.target-repo }}
    ref: ${{ inputs.pr-head-sha }}
    path: target-repo-head
    token: ${{ secrets.PERSONAL_ACCESS_TOKEN || github.token }}
    fetch-depth: 0
```

**Checkout BASE**

```yaml
- name: Checkout target repo (BASE - main branch)
  uses: actions/checkout@v4
  with:
    repository: ${{ inputs.target-repo }}
    ref: ${{ inputs.pr-base-sha }}
    path: target-repo-base
    token: ${{ secrets.PERSONAL_ACCESS_TOKEN || github.token }}
    fetch-depth: 0
```

---

## 📌 Step B — Correct PR Changed Files Logic

Replace existing “Collect PR changed files” with:

```yaml
- name: Collect PR changed files (PR diff via merge-base)
  id: changed-files
  working-directory: target-repo-head
  run: |
    echo "🔍 Collecting PR changed files via merge base..."

    BASE_SHA="${{ inputs.pr-base-sha }}"
    HEAD_SHA="${{ inputs.pr-head-sha }}"

    MERGE_BASE=$(git merge-base "$BASE_SHA" "$HEAD_SHA")

    echo "Merge base: $MERGE_BASE"

    git diff --name-only "$MERGE_BASE" "$HEAD_SHA" > changed_files.txt

    echo "Changed files (PR delta only):"
    cat changed_files.txt || true

    echo "changed_files_path=changed_files.txt" >> $GITHUB_OUTPUT
```

---

## 📌 Step C — Tell Validation Engine to Only Scan Changed Files

In your validation job, set:

```yaml
env:
  SCAN_MODE: changed-only
  CHANGED_FILES_PATH: ${{ github.workspace }}/target-repo-head/${{ steps.changed-files.outputs.changed_files_path }}
```

Then **inside your engine** logic, only validate files from `changed_files.txt`.

---

## 📌 Step D — Email Notification Logic Must Depend on Validation Execution

### 1) Initialize validation executed flag

Before validation:

```yaml
- name: Initialize validation state
  id: validation-state
  run: |
    echo "validation_executed=false" >> $GITHUB_OUTPUT
```

---

### 2) Mark it true *only inside the validation run*

In your validation step:

```yaml
- name: Run validation engine
  id: validation
  if: steps.repo-enabled.outputs.repo_enabled == 'true'
  run: |
    echo "validation_executed=true" >> $GITHUB_OUTPUT
    # (existing engine invocation)
```

---

### 3) Gate email by this

Replace email steps’ condition with:

```yaml
if: >
  always() &&
  steps.validation-state.outputs.validation_executed == 'true' &&
  steps.validation.outputs.validation_failed == 'true'
```

> *Assumes your validation step outputs `validation_failed=true` when the engine fails.*

---

## 🔍 Why This Works

### Accurate Changed Files

`git diff $(git merge-base)` gives you **only the delta of the PR**, accounting for:

* Branch diverging from main
* Prior master changes unrelated to this PR
* Single-file PRs

Your old logic was diffing HEAD vs BASE raw, which can include unrelated changes.

---

### Email Logic Only on Actual Validation

Previously:

* `repo_enabled == true` triggered email gates even when:

  * validation never ran
  * validation had no outputs
  * your email workflow skipped body/attachment steps

Now emails only trigger if:

* Validation actually executed
* Validation failed
* Email content can be assembled

---

## 🎯 Quick Validation Checklist

| Expected                             | Actual                  |
| ------------------------------------ | ----------------------- |
| Only the PR file gets validated      | ✔️ after merge-base fix |
| Validation runs                      | ✔️                      |
| Email triggers for failed validation | ✔️ after email gate fix |
| No email for skipped validation      | ✔️                      |
| No noise from unrelated files        | ✔️                      |

---

## 🚀 Testing Notes

1. Create a PR with **1 file changed**
2. Confirm validation only reports that file
3. Confirm email triggers only on failure
4. Confirm no email when validation passes
5. Confirm no email when repo is disabled

---

If you need, I can also provide a **ready-made engine diff patch** so your validation script respects `SCAN_MODE=changed-only` automatically.

Just ask for the patch.
