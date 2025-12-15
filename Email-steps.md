Below is the **README-only section** you asked for.
It contains **ONLY what to add / change** so that **email is NOT sent when validation is skipped** (repo disabled).
No redesign, no explanation text beyond documentation style.

---

# 📧 Email Notification Guard (Skip When Validation Is Disabled)

This section ensures **email notifications are not triggered** when repository validation is **explicitly disabled** via the repo override file.

---

## 📍 Applies To

Central workflow:

```
.github/workflows/helm-chart-pr-gatekeeper.yml
```

---

## ➕ Step 1: Expose Validation Execution State

Ensure the **repo-enabled evaluation step** exists and exposes this output:

```yaml
echo "repo_enabled=$REPO_ENABLED" >> $GITHUB_OUTPUT
```

*Output used:*

```
steps.repo-enabled.outputs.repo_enabled
```

---

## ✏️ Step 2: Guard Email Generation Step

Modify the **Generate email notification** step.

### Before

```yaml
- name: Generate email notification
  if: always()
```

### After

```yaml
- name: Generate email notification
  if: |
    always() &&
    steps.repo-enabled.outputs.repo_enabled == 'true' &&
    steps.validation.outputs.validation_completed == 'true'
```

---

## ✏️ Step 3: Guard Email Read & Attachments

Apply the **same condition** to all downstream email steps.

### Read email body

```yaml
- name: Read email body for sending
  if: |
    always() &&
    steps.repo-enabled.outputs.repo_enabled == 'true' &&
    steps.read-email.outputs.email_ready == 'true'
```

### Prepare email attachments

```yaml
- name: Prepare email attachments
  if: |
    always() &&
    steps.repo-enabled.outputs.repo_enabled == 'true' &&
    steps.read-email.outputs.email_ready == 'true'
```

---

## 🧠 Behavior Summary

| Scenario                                  | Email Sent            |
| ----------------------------------------- | --------------------- |
| Validation failed                         | ✅ Yes                 |
| Validation passed                         | ✅ Yes (if configured) |
| Validation skipped (`repo_enabled=false`) | ❌ No                  |
| Override file missing                     | ✅ Yes                 |
| Validation never executed                 | ❌ No                  |

---

## 📄 Repo Override File Example

```json
{
  "repo_enabled": false
}
```

Location:

```
.github/esob-observability-hooks.json
```

---

## ✅ Result

* No false failure emails
* No noise when repo validation is disabled
* Email only reflects **real validation outcomes**
* Centralized governance preserved

---

✔ Production safe
✔ Audit friendly
✔ Enterprise compliant
