Below is a **single, clean, enterprise-grade README section** that **covers BOTH issues together** and explains **exactly what to change, where to change it, and why**.

You can copy-paste this **as-is** into your central automation README.

---

# PR Validation Accuracy & Email Notification Control

**(Authoritative Fix Guide)**

This document addresses **two critical production issues** in centralized PR validation:

1. **Email notifications being skipped for all repos**
2. **Extra / unrelated files appearing in validation reports**

Both issues stem from **workflow logic gaps**, not from GitHub bugs.

---

## Issue 1: Email Skipped for All Repositories

### Intended Behavior

| Repo Type                             | Validation | Email      |
| ------------------------------------- | ---------- | ---------- |
| Repo override disables validation     | ❌ skipped  | ❌ skipped  |
| Repo enabled, validation runs & fails | ✅ runs     | ✅ sent     |
| Repo enabled, validation passes       | ✅ runs     | ❌ not sent |

### Current Incorrect Behavior

* Email is skipped **for all repos**, including those where validation runs and fails.

---

## Root Cause (Issue 1)

Email steps are gated using **repo_enabled** or `always()`.

However:

* `repo_enabled = true` does **not** guarantee validation actually ran
* Validation outputs may be missing
* Email logic assumes “no validation → no email”

---

## ✅ Fix 1: Introduce Explicit Validation Execution Flag

### Design Principle

> **Email must depend on whether validation actually executed**, not on repo configuration alone.

---

### Step 1.1 – Initialize Validation State

**WHERE TO ADD**
Immediately **before** the validation step in the central workflow.

```yaml
- name: Initialize validation state
  id: validation-state
  run: |
    echo "validation_executed=false" >> $GITHUB_OUTPUT
```

---

### Step 1.2 – Mark Validation as Executed

**WHERE TO ADD**
Inside the validation step.

```yaml
- name: Run validation engine
  id: validation
  if: steps.repo-enabled.outputs.repo_enabled == 'true'
  run: |
    echo "validation_executed=true" >> $GITHUB_OUTPUT
    # existing validation logic
```

---

### Step 1.3 – Gate ALL Email Steps (Mandatory)

**Apply this condition to ALL email-related steps**:

```yaml
if: >
  always() &&
  steps.validation-state.outputs.validation_executed == 'true'
```

**Steps affected:**

* Generate email notification
* Read email body
* Prepare attachments
* Extract CC emails
* Send consolidated email

---

## Issue 2: Extra Files Appearing in Validation Report

### Symptoms

* Feature branch modifies **1 file**
* Validation reports **multiple unrelated files**
* Files already existing in `master/main` are included
* False positives in validation & reports

---

## Root Cause (Issue 2 – Critical)

Current diff logic uses:

```bash
git diff <base_sha> <head_sha>
```

This fails when:

* Base branch already contains unrelated changes
* PR branch was created long ago
* History diverged

👉 Git compares **two commits**, not the **PR delta**

---

## ✅ Fix 2: Use Git Merge-Base (Correct PR Diff)

### Design Principle

> **PR validation must compare against the merge base, not the branch head**

---

### Step 2.1 – Update Changed Files Collection Logic

**WHERE TO ADD / REPLACE**
Replace the existing “Collect PR changed files” step.

```yaml
- name: Collect PR changed files (PR-accurate)
  id: changed-files
  working-directory: target-repo-head
  run: |
    echo "🔍 Collecting PR-accurate changed files..."

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

### Step 2.2 – Ensure Full Git History Is Available

**MANDATORY (already identified earlier)**
Both checkout steps **must include**:

```yaml
fetch-depth: 0
```

Without this, `merge-base` will fail.

---

## Expected Behavior After Both Fixes

### Validation Accuracy

| Scenario                              | Result                     |
| ------------------------------------- | -------------------------- |
| Single file changed in feature branch | ✅ Only that file validated |
| Old issues in base branch             | ❌ Not included             |
| False positives                       | ❌ Eliminated               |

---

### Email Notifications

| Scenario                        | Email |
| ------------------------------- | ----- |
| Repo disabled via override      | ❌ No  |
| Validation fails (repo enabled) | ✅ Yes |
| Validation skipped              | ❌ No  |

---

## Why This Design Is Enterprise-Grade

* Uses **Git-native PR diff logic**
* Eliminates historical noise
* Deterministic & auditable
* Scales to **10k+ repos**
* No GitHub API limits
* Zero per-repo maintenance

---

## Final Summary

✔ Validation runs **only on real PR changes**
✔ Emails sent **only when validation actually runs and fails**
✔ Repo overrides respected
✔ No extra files
✔ Fully compliant with centralized governance model

---

**End of Document**

---

If you want next, I can:

* Add fallback when merge-base fails
* Add debug annotations to PR comments
* Add rule-level diff filtering
* Convert this into a formal **Org Engineering Standard (OES)**

Just say 👍
