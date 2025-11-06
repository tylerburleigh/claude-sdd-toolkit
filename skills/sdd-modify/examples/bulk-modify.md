# Example: Bulk Modifications from JSON

This example demonstrates creating and applying bulk modifications from a JSON file, useful for planned refactoring or systematic spec updates.

## Scenario

Your team has completed Phase 3 of a payment processing spec (`payment-system-001`) and discovered during retrospective that task descriptions need clarification, verification commands need updating, and some metadata needs corrections.

You want to apply all these changes systematically in one batch operation.

## Initial State

**Spec:** `specs/active/payment-system-001.json`

**Phase 3 Tasks (before modifications):**
- `task-3-1`: "Process payments" (vague description)
- `task-3-2`: "Handle refunds" (vague description)
- `task-3-3`: "Add webhooks" (missing verification command)
- `task-3-4`: "Update docs" (incorrect estimated_hours: 2, actually took 5)

**Goal:** Update all task descriptions to be more specific, add missing verification command, correct metadata, and add new verification steps based on implementation learnings.

## Step 1: Create Modification File

Create a JSON file with all desired modifications:

**File:** `payment-improvements.json`

```json
{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-3-1",
      "field": "description",
      "value": "Process payments via Stripe API with idempotency keys, webhook confirmation, and automatic retry logic for failed transactions",
      "rationale": "Clarify implementation details discovered during development"
    },
    {
      "operation": "update_task",
      "task_id": "task-3-2",
      "field": "description",
      "value": "Handle refunds through Stripe refund API with partial refund support, refund reason tracking, and audit logging",
      "rationale": "Specify refund capabilities implemented"
    },
    {
      "operation": "update_task",
      "task_id": "task-3-3",
      "field": "description",
      "value": "Add webhook endpoints for payment.succeeded, payment.failed, and refund.processed events with signature verification",
      "rationale": "Document specific webhook events handled"
    },
    {
      "operation": "add_verification",
      "task_id": "task-3-1",
      "verify_id": "verify-3-1-4",
      "description": "Verify idempotency prevents duplicate charges",
      "command": "pytest tests/test_payment.py::test_idempotency -v",
      "rationale": "Add verification for idempotency implementation"
    },
    {
      "operation": "add_verification",
      "task_id": "task-3-1",
      "verify_id": "verify-3-1-5",
      "description": "Verify automatic retry logic handles transient failures",
      "command": "pytest tests/test_payment.py::test_retry_logic -v",
      "rationale": "Add verification for retry mechanism"
    },
    {
      "operation": "update_task",
      "task_id": "task-3-3",
      "field": "command",
      "value": "pytest tests/test_webhooks.py -v --cov=src/webhooks",
      "rationale": "Add missing verification command for webhook implementation"
    },
    {
      "operation": "add_verification",
      "task_id": "task-3-3",
      "verify_id": "verify-3-3-3",
      "description": "Verify webhook signature validation rejects invalid signatures",
      "command": "pytest tests/test_webhooks.py::test_signature_validation -v",
      "rationale": "Ensure webhook security is verified"
    },
    {
      "operation": "update_metadata",
      "task_id": "task-3-4",
      "field": "actual_hours",
      "value": 5.0,
      "rationale": "Correct actual hours spent on documentation"
    },
    {
      "operation": "update_task",
      "task_id": "task-3-4",
      "field": "task_category",
      "value": "documentation",
      "rationale": "Correct task category classification"
    }
  ],
  "metadata": {
    "created_by": "team-retrospective",
    "created_at": "2025-11-06T10:00:00Z",
    "purpose": "Phase 3 improvements from implementation learnings",
    "total_modifications": 9
  }
}
```

Save this as `payment-improvements.json`.

## Step 2: Validate Modification File

Before applying, validate the modification file structure:

```bash
sdd validate-modifications payment-improvements.json
```

**Output:**
```
🔍 Validating Modification File

File: payment-improvements.json
Loading and parsing...

✓ Valid JSON structure
✓ Contains 'modifications' array
✓ Total modifications: 9

Checking modification structure...

[1/9] ✓ update_task (task-3-1, field: description)
      - task_id format valid
      - field 'description' is updatable
      - value provided (125 chars)

[2/9] ✓ update_task (task-3-2, field: description)
      - task_id format valid
      - field 'description' is updatable
      - value provided (117 chars)

[3/9] ✓ update_task (task-3-3, field: description)
      - task_id format valid
      - field 'description' is updatable
      - value provided (142 chars)

[4/9] ✓ add_verification (task-3-1, verify-3-1-4)
      - task_id format valid
      - verify_id format valid
      - description provided
      - command provided

[5/9] ✓ add_verification (task-3-1, verify-3-1-5)
      - task_id format valid
      - verify_id format valid
      - description provided
      - command provided

[6/9] ✓ update_task (task-3-3, field: command)
      - task_id format valid
      - field 'command' is updatable
      - value provided (46 chars)

[7/9] ✓ add_verification (task-3-3, verify-3-3-3)
      - task_id format valid
      - verify_id format valid
      - description provided
      - command provided

[8/9] ✓ update_metadata (task-3-4, field: actual_hours)
      - task_id format valid
      - field 'actual_hours' is updatable metadata
      - value type correct (number)

[9/9] ✓ update_task (task-3-4, field: task_category)
      - task_id format valid
      - field 'task_category' is updatable
      - value provided (13 chars)

✅ VALIDATION PASSED

Summary:
  - Total modifications: 9
  - update_task operations: 5
  - add_verification operations: 3
  - update_metadata operations: 1
  - Schema violations: 0
  - Format errors: 0

⚠️  Note: This only validates the modification file structure.
    Task references will be validated against the spec when you apply.

Ready to apply. Next step:
  sdd apply-modifications payment-system-001 --from payment-improvements.json --dry-run
```

Good! The file structure is valid. Now validate against the actual spec.

## Step 3: Check Task References Against Spec

Validate that all task IDs referenced in the modification file actually exist:

```bash
sdd validate-modifications payment-improvements.json --spec payment-system-001
```

**Output:**
```
🔍 Validating Modifications Against Spec

Modification file: payment-improvements.json
Spec: payment-system-001

Loading...
✓ Loaded modification file (9 modifications)
✓ Loaded spec (active/payment-system-001.json)

Checking task references...

✓ task-3-1 exists in Phase 3
✓ task-3-2 exists in Phase 3
✓ task-3-3 exists in Phase 3
✓ task-3-4 exists in Phase 3

Checking verification ID conflicts...

✓ verify-3-1-4 is available (no conflict)
✓ verify-3-1-5 is available (no conflict)
✓ verify-3-3-3 is available (no conflict)

Checking field updates...

✓ All fields are updatable
✓ No read-only field violations

✅ ALL VALIDATIONS PASSED

The modification file is ready to apply to spec payment-system-001.

Next step:
  sdd apply-modifications payment-system-001 --from payment-improvements.json --dry-run
```

Perfect! All references are valid.

## Step 4: Preview Modifications (Dry-Run)

See exactly what will change before applying:

```bash
sdd apply-modifications payment-system-001 --from payment-improvements.json --dry-run
```

**Output:**
```
📋 Modification Preview (Dry-Run Mode)

Spec: payment-system-001
Modifications file: payment-improvements.json
Total modifications: 9

═══════════════════════════════════════════════════════════════

TASKS TO UPDATE (5 tasks, 6 field changes)

───────────────────────────────────────────────────────────────
Task: task-3-1 (Phase 3 - Payment Processing)
Field: description
Current: "Process payments"
New:     "Process payments via Stripe API with idempotency keys, webhook confirmation, and automatic retry logic for failed transactions"
Length:  17 chars → 125 chars (+108 chars)
───────────────────────────────────────────────────────────────
Task: task-3-2 (Phase 3 - Payment Processing)
Field: description
Current: "Handle refunds"
New:     "Handle refunds through Stripe refund API with partial refund support, refund reason tracking, and audit logging"
Length:  14 chars → 117 chars (+103 chars)
───────────────────────────────────────────────────────────────
Task: task-3-3 (Phase 3 - Payment Processing)
Field: description
Current: "Add webhooks"
New:     "Add webhook endpoints for payment.succeeded, payment.failed, and refund.processed events with signature verification"
Length:  12 chars → 142 chars (+130 chars)
───────────────────────────────────────────────────────────────
Task: task-3-3 (Phase 3 - Payment Processing)
Field: command
Current: (none)
New:     "pytest tests/test_webhooks.py -v --cov=src/webhooks"
───────────────────────────────────────────────────────────────
Task: task-3-4 (Phase 3 - Payment Processing)
Field: task_category
Current: "implementation"
New:     "documentation"
───────────────────────────────────────────────────────────────

METADATA TO UPDATE (1 task, 1 field change)

───────────────────────────────────────────────────────────────
Task: task-3-4 (Phase 3 - Payment Processing)
Field: actual_hours
Current: 0.0
New:     5.0
───────────────────────────────────────────────────────────────

VERIFICATION STEPS TO ADD (3 steps)

───────────────────────────────────────────────────────────────
Task: task-3-1
Verify ID: verify-3-1-4
Description: "Verify idempotency prevents duplicate charges"
Command: pytest tests/test_payment.py::test_idempotency -v
───────────────────────────────────────────────────────────────
Task: task-3-1
Verify ID: verify-3-1-5
Description: "Verify automatic retry logic handles transient failures"
Command: pytest tests/test_payment.py::test_retry_logic -v
───────────────────────────────────────────────────────────────
Task: task-3-3
Verify ID: verify-3-3-3
Description: "Verify webhook signature validation rejects invalid signatures"
Command: pytest tests/test_webhooks.py::test_signature_validation -v
───────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════

IMPACT SUMMARY

Tasks affected:               4 tasks
Task fields updated:          6 changes
Metadata updated:             1 field
Verification steps added:     3 steps
Phases affected:              1 (Phase 3)
Estimated hours adjustment:   +3.0 hours (actual_hours corrected)

Validation prediction: ✓ No errors expected

═══════════════════════════════════════════════════════════════

DRY-RUN MODE: No changes were made to the spec.

To apply these modifications, run without --dry-run:
  sdd apply-modifications payment-system-001 --from payment-improvements.json
```

The preview looks good - all changes are intentional and correct.

## Step 5: Apply Modifications

Apply all 9 modifications in one transaction:

```bash
sdd apply-modifications payment-system-001 --from payment-improvements.json
```

**Output:**
```
🔄 Applying Modifications to payment-system-001

✓ Loaded spec: specs/active/payment-system-001.json
✓ Loaded modifications: payment-improvements.json (9 modifications)
✓ Backup created: specs/.backups/payment-system-001-20251106-143815.json

Starting transaction...

Applying modifications...

[1/9] ✓ Updated task-3-1 description (17 → 125 chars)
[2/9] ✓ Updated task-3-2 description (14 → 117 chars)
[3/9] ✓ Updated task-3-3 description (12 → 142 chars)
[4/9] ✓ Added verification step verify-3-1-4 to task-3-1
[5/9] ✓ Added verification step verify-3-1-5 to task-3-1
[6/9] ✓ Updated task-3-3 command
[7/9] ✓ Added verification step verify-3-3-3 to task-3-3
[8/9] ✓ Updated task-3-4 metadata: actual_hours = 5.0
[9/9] ✓ Updated task-3-4 task_category = documentation

✓ All modifications applied successfully (9/9)

Running validation...

Validating spec structure...
✓ Valid JSON structure
✓ All required fields present
✓ All task IDs follow pattern
✓ All phase references valid
✓ All verification IDs unique
✓ No duplicate task IDs
✓ No schema violations

✓ Validation passed

Committing transaction...
✓ Transaction committed

═══════════════════════════════════════════════════════════════

✅ MODIFICATIONS APPLIED SUCCESSFULLY

Applied:          9 modifications
Skipped:          0 modifications
Failed:           0 modifications
Validation:       ✓ PASSED

Changes Summary:
  - Updated 5 task fields
  - Updated 1 metadata field
  - Added 3 verification steps
  - 4 tasks modified
  - 1 phase affected (Phase 3)

Files:
  Backup:  specs/.backups/payment-system-001-20251106-143815.json
  Spec:    specs/active/payment-system-001.json
  Applied: payment-improvements.json

═══════════════════════════════════════════════════════════════

Next steps:
  1. Review updated spec: sdd context show payment-system-001
  2. Run new verification steps: sdd verify payment-system-001
  3. Document changes: sdd add-journal payment-system-001
```

Perfect! All modifications applied successfully in one transaction.

## Step 6: Verify Applied Changes

Confirm the spec was updated correctly:

```bash
sdd context show payment-system-001 --phase 3
```

**Output (excerpt):**
```
Spec: payment-system-001 - Payment Processing System

Phase 3: Payment Processing
  Status: in_progress
  Progress: 4/4 tasks (100%)

  task-3-1: Process payments via Stripe API with idempotency keys, webhook confirmation, and automatic retry logic for failed transactions [completed]
    Category: implementation
    Verification:
      verify-3-1-1: ✓ Payment succeeds with valid card
      verify-3-1-2: ✓ Payment fails with invalid card
      verify-3-1-3: ✓ Payment refund works correctly
      verify-3-1-4: ⏳ Verify idempotency prevents duplicate charges
        Command: pytest tests/test_payment.py::test_idempotency -v
      verify-3-1-5: ⏳ Verify automatic retry logic handles transient failures
        Command: pytest tests/test_payment.py::test_retry_logic -v

  task-3-2: Handle refunds through Stripe refund API with partial refund support, refund reason tracking, and audit logging [completed]
    Category: implementation
    Verification:
      verify-3-2-1: ✓ Full refund works correctly
      verify-3-2-2: ✓ Partial refund works correctly

  task-3-3: Add webhook endpoints for payment.succeeded, payment.failed, and refund.processed events with signature verification [completed]
    Category: implementation
    Command: pytest tests/test_webhooks.py -v --cov=src/webhooks
    Verification:
      verify-3-3-1: ✓ Webhook receives payment.succeeded event
      verify-3-3-2: ✓ Webhook receives payment.failed event
      verify-3-3-3: ⏳ Verify webhook signature validation rejects invalid signatures
        Command: pytest tests/test_webhooks.py::test_signature_validation -v

  task-3-4: Update docs [completed]
    Category: documentation
    Metadata:
      estimated_hours: 2.0
      actual_hours: 5.0
```

Excellent! All updates are visible:
- ✅ Task descriptions expanded and clarified
- ✅ 3 new verification steps added
- ✅ Webhook command added
- ✅ actual_hours corrected to 5.0
- ✅ task_category corrected to "documentation"

## Step 7: Run New Verification Steps

Execute the newly added verification steps:

```bash
# Run all pending verifications for Phase 3
sdd verify payment-system-001 --phase 3 --status pending
```

**Output:**
```
🔍 Running Pending Verifications for Phase 3

Found 3 pending verification steps:
  - verify-3-1-4 (task-3-1)
  - verify-3-1-5 (task-3-1)
  - verify-3-3-3 (task-3-3)

───────────────────────────────────────────────────────────────
[1/3] Running: verify-3-1-4
Description: Verify idempotency prevents duplicate charges
Command: pytest tests/test_payment.py::test_idempotency -v

============================= test session starts ==============================
collected 1 item

tests/test_payment.py::test_idempotency PASSED                          [100%]

============================== 1 passed in 0.34s ===============================

✓ PASSED
───────────────────────────────────────────────────────────────
[2/3] Running: verify-3-1-5
Description: Verify automatic retry logic handles transient failures
Command: pytest tests/test_payment.py::test_retry_logic -v

============================= test session starts ==============================
collected 1 item

tests/test_payment.py::test_retry_logic PASSED                          [100%]

============================== 1 passed in 0.28s ===============================

✓ PASSED
───────────────────────────────────────────────────────────────
[3/3] Running: verify-3-3-3
Description: Verify webhook signature validation rejects invalid signatures
Command: pytest tests/test_webhooks.py::test_signature_validation -v

============================= test session starts ==============================
collected 1 item

tests/test_webhooks.py::test_signature_validation PASSED                [100%]

============================== 1 passed in 0.19s ===============================

✓ PASSED
───────────────────────────────────────────────────────────────

✅ All Verification Steps Passed

Results: 3/3 passed, 0 failed
```

Perfect! All new verification steps pass.

## Step 8: Document Bulk Update

Add journal entry documenting the bulk modification:

```bash
sdd add-journal payment-system-001 \
  --title "Bulk Spec Improvements from Team Retrospective" \
  --content "Applied 9 modifications to Phase 3 based on implementation learnings. Updated task descriptions to reflect Stripe API specifics, added 3 verification steps for idempotency, retry logic, and webhook security. Corrected task-3-4 metadata (actual_hours: 5.0, category: documentation). All modifications validated and verification steps passing." \
  --entry-type note
```

**Output:**
```
✓ Journal entry added to payment-system-001

Entry Details:
  Title:       "Bulk Spec Improvements from Team Retrospective"
  Type:        note
  Timestamp:   2025-11-06T14:42:30Z
  Content:     [112 words]

✓ Spec updated
```

## Step 9: Compare Before/After

Compare the spec with the backup to see all changes:

```bash
# Show diff summary
sdd diff payment-system-001 --backup specs/.backups/payment-system-001-20251106-143815.json --summary
```

**Output:**
```
📊 Spec Diff Summary

Comparing:
  Original: specs/.backups/payment-system-001-20251106-143815.json
  Current:  specs/active/payment-system-001.json

Changes:

Tasks Modified: 4
  - task-3-1: description updated, 2 verification steps added
  - task-3-2: description updated
  - task-3-3: description updated, command added, 1 verification step added
  - task-3-4: task_category updated, actual_hours updated

Verification Steps: +3
  - verify-3-1-4: Added to task-3-1
  - verify-3-1-5: Added to task-3-1
  - verify-3-3-3: Added to task-3-3

Metadata Changes:
  - task-3-4: actual_hours (0.0 → 5.0)
  - task-3-4: task_category ("implementation" → "documentation")

Journal Entries: +1
  - "Bulk Spec Improvements from Team Retrospective" (note)

Total modifications: 9
Backup preserved: specs/.backups/payment-system-001-20251106-143815.json
```

## Summary

This example demonstrated bulk modifications workflow:

1. ✅ **Created modification file** - Defined all 9 modifications in structured JSON
2. ✅ **Validated structure** - Ensured modification file is well-formed
3. ✅ **Validated references** - Confirmed all task IDs exist in spec
4. ✅ **Previewed changes** - Reviewed exactly what would change
5. ✅ **Applied in transaction** - All modifications applied atomically with rollback protection
6. ✅ **Verified updates** - Confirmed spec changes are correct
7. ✅ **Ran verifications** - Executed new verification steps
8. ✅ **Documented changes** - Added journal entry explaining bulk update

**Key Takeaways:**
- Bulk modifications enable systematic spec updates
- Validation catches errors before applying
- Preview shows exactly what will change
- Transactions ensure all-or-nothing application
- Backups enable easy rollback if needed
- Idempotency makes retries safe

**Best Practices:**
- Always validate modification file structure first
- Always preview with --dry-run before applying
- Keep modification files for documentation
- Document bulk changes in journal entries
- Run verification steps after applying
- Preserve backups until changes verified

**When to Use Bulk Modifications:**
- Team retrospectives identify multiple spec issues
- Systematic refactoring needed across tasks
- Correcting metadata after phase completion
- Adding verification steps for new implementation features
- Updating descriptions for clarity after implementation
