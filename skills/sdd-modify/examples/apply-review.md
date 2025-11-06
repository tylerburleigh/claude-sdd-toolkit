# Example: Apply Fidelity Review Feedback

This example demonstrates the complete workflow for applying feedback from an sdd-fidelity-review to a specification.

## Scenario

You've implemented Phase 2 of your authentication spec (`auth-system-001`) and want to verify the implementation matches the plan. The fidelity review identifies several areas where the spec needs updates to reflect implementation learnings.

## Initial State

**Spec:** `specs/active/auth-system-001.json`

**Phase 2 Tasks (before review):**
- `task-2-1`: "Implement auth" (status: completed)
- `task-2-2`: "Add login endpoint" (status: completed)
- `task-2-3`: "Write tests" (status: in_progress)

**Implementation Status:** Phase 2 is mostly complete, but spec descriptions are vague and don't reflect actual implementation details.

## Step 1: Run Fidelity Review

Run the fidelity review to compare implementation against spec:

```bash
Skill(sdd-toolkit:sdd-fidelity-review) "Review implementation for spec auth-system-001"
```

**Output:**
```
🔍 Running Fidelity Review for auth-system-001

Analyzing implementation...
✓ Loaded spec: auth-system-001
✓ Found implementation files:
  - src/auth/oauth.py (342 lines)
  - src/auth/endpoints.py (218 lines)
  - tests/test_auth.py (156 lines)

Comparing against spec...

📋 Review Summary

Issues Found: 5

1. Task task-2-1 description too vague
   Current: "Implement auth"
   Actual implementation: OAuth 2.0 with PKCE flow, refresh tokens
   Recommendation: Update description to reflect OAuth 2.0 specifics

2. Task task-2-2 missing rate limiting detail
   Current: "Add login endpoint"
   Actual implementation: /auth/login with rate limiting (10 req/min)
   Recommendation: Update description to mention rate limiting

3. Task task-2-3 missing test coverage details
   Current: "Write tests"
   Recommendation: Update to specify comprehensive test coverage including edge cases

4. Missing verification step for token expiration
   Implementation includes token expiration but spec has no verification step
   Recommendation: Add verify-2-1-3 to check token expiration handling

5. Missing verification step for rate limiting
   Implementation includes rate limiting but spec has no verification step
   Recommendation: Add verify-2-2-4 to check rate limiting with concurrent requests

✓ Review report saved: reports/auth-system-001-fidelity-review.md
```

## Step 2: Review the Report

Examine the generated review report:

```bash
cat reports/auth-system-001-fidelity-review.md
```

**Report Contents (excerpt):**
```markdown
# Fidelity Review: auth-system-001

## Overview
- Spec ID: auth-system-001
- Review Date: 2025-11-06
- Phase Reviewed: Phase 2 - Authentication Implementation
- Issues Found: 5

## Issues

### Issue 1: Task Description Too Vague (task-2-1)

**Current Description:**
"Implement auth"

**Actual Implementation:**
- OAuth 2.0 authentication with PKCE flow
- JWT token generation with RS256 signing
- Refresh token rotation
- Token expiration handling (access: 15min, refresh: 7 days)

**Recommendation:**
Update task description to: "Implement OAuth 2.0 authentication with PKCE flow, including JWT access tokens (15min expiry), refresh tokens (7 days expiry), and token rotation"

**Severity:** Medium
**Category:** Documentation

### Issue 2: Missing Rate Limiting Detail (task-2-2)

**Current Description:**
"Add login endpoint"

**Actual Implementation:**
- POST /auth/login endpoint
- Rate limiting: 10 requests per minute per IP
- Response includes access_token, refresh_token, expires_in

**Recommendation:**
Update task description to: "Add /auth/login endpoint with rate limiting (10 req/min per IP)"

**Severity:** Low
**Category:** Documentation

### Issue 3: Test Coverage Not Specified (task-2-3)

**Current Description:**
"Write tests"

**Actual Implementation:**
- 23 test cases covering happy path, error cases, edge cases
- Tests for token expiration, refresh flow, rate limiting
- 95% code coverage

**Recommendation:**
Update task description to: "Write comprehensive tests covering OAuth flow, token expiration, refresh tokens, rate limiting, and error handling. Target 90%+ coverage."

**Severity:** Medium
**Category:** Documentation

### Issue 4: Missing Token Expiration Verification

**Current State:**
No verification step exists for token expiration handling

**Actual Implementation:**
Implementation includes token expiration logic but spec doesn't verify it

**Recommendation:**
Add verification step to task-2-1:
- verify_id: verify-2-1-3
- Description: "Verify token expiration handling works correctly"
- Command: "pytest tests/test_auth.py::test_token_expiration -v"

**Severity:** Medium
**Category:** Missing Verification

### Issue 5: Missing Rate Limiting Verification

**Current State:**
No verification step exists for rate limiting

**Actual Implementation:**
Rate limiting implemented but not verified in spec

**Recommendation:**
Add verification step to task-2-2:
- verify_id: verify-2-2-4
- Description: "Verify rate limiting prevents abuse with concurrent requests"
- Command: "pytest tests/test_auth.py::test_rate_limiting_concurrent -v"

**Severity:** Medium
**Category:** Missing Verification
```

## Step 3: Parse Review Report

Convert the review report into structured modification JSON:

```bash
sdd parse-review auth-system-001 \
  --review reports/auth-system-001-fidelity-review.md \
  --output auth-fixes.json
```

**Output:**
```
📝 Parsing Review Report

✓ Loaded review report (78 lines)
✓ Loaded spec auth-system-001
✓ Identified modification patterns

Parsing results:
  - Found 5 modification suggestions
  - Extracted 3 task description updates
  - Extracted 2 verification step additions
  - All task references valid

Confidence scores:
  - High confidence: 4 modifications (clear patterns, valid references)
  - Medium confidence: 1 modification (inference required)
  - Low confidence: 0 modifications

✓ Saved to auth-fixes.json
```

**Generated auth-fixes.json:**
```json
{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-2-1",
      "field": "description",
      "value": "Implement OAuth 2.0 authentication with PKCE flow, including JWT access tokens (15min expiry), refresh tokens (7 days expiry), and token rotation",
      "confidence": "high",
      "source": "fidelity-review-issue-1"
    },
    {
      "operation": "update_task",
      "task_id": "task-2-2",
      "field": "description",
      "value": "Add /auth/login endpoint with rate limiting (10 req/min per IP)",
      "confidence": "high",
      "source": "fidelity-review-issue-2"
    },
    {
      "operation": "update_task",
      "task_id": "task-2-3",
      "field": "description",
      "value": "Write comprehensive tests covering OAuth flow, token expiration, refresh tokens, rate limiting, and error handling. Target 90%+ coverage.",
      "confidence": "high",
      "source": "fidelity-review-issue-3"
    },
    {
      "operation": "add_verification",
      "task_id": "task-2-1",
      "verify_id": "verify-2-1-3",
      "description": "Verify token expiration handling works correctly",
      "command": "pytest tests/test_auth.py::test_token_expiration -v",
      "confidence": "high",
      "source": "fidelity-review-issue-4"
    },
    {
      "operation": "add_verification",
      "task_id": "task-2-2",
      "verify_id": "verify-2-2-4",
      "description": "Verify rate limiting prevents abuse with concurrent requests",
      "command": "pytest tests/test_auth.py::test_rate_limiting_concurrent -v",
      "confidence": "medium",
      "source": "fidelity-review-issue-5"
    }
  ],
  "metadata": {
    "source": "reports/auth-system-001-fidelity-review.md",
    "parsed_at": "2025-11-06T14:30:22Z",
    "spec_id": "auth-system-001",
    "total_modifications": 5,
    "parser_version": "1.0"
  }
}
```

## Step 4: Preview Modifications

Before applying, preview what will change:

```bash
sdd apply-modifications auth-system-001 --from auth-fixes.json --dry-run
```

**Output:**
```
📋 Modification Preview (Dry-Run Mode)

Spec: auth-system-001
Modifications file: auth-fixes.json
Total modifications: 5

═══════════════════════════════════════════════════════════════

TASKS TO UPDATE (3 tasks)

───────────────────────────────────────────────────────────────
Task: task-2-1 (Phase 2)
Field: description
Current: "Implement auth"
New:     "Implement OAuth 2.0 authentication with PKCE flow, including JWT access tokens (15min expiry), refresh tokens (7 days expiry), and token rotation"
───────────────────────────────────────────────────────────────
Task: task-2-2 (Phase 2)
Field: description
Current: "Add login endpoint"
New:     "Add /auth/login endpoint with rate limiting (10 req/min per IP)"
───────────────────────────────────────────────────────────────
Task: task-2-3 (Phase 2)
Field: description
Current: "Write tests"
New:     "Write comprehensive tests covering OAuth flow, token expiration, refresh tokens, rate limiting, and error handling. Target 90%+ coverage."
───────────────────────────────────────────────────────────────

VERIFICATION STEPS TO ADD (2 steps)

───────────────────────────────────────────────────────────────
Task: task-2-1
Verify ID: verify-2-1-3
Description: "Verify token expiration handling works correctly"
Command: pytest tests/test_auth.py::test_token_expiration -v
───────────────────────────────────────────────────────────────
Task: task-2-2
Verify ID: verify-2-2-4
Description: "Verify rate limiting prevents abuse with concurrent requests"
Command: pytest tests/test_auth.py::test_rate_limiting_concurrent -v
───────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════

IMPACT SUMMARY

Tasks affected:         3
Verification steps:     2 added
Phases affected:        1 (Phase 2)
Estimated time impact:  +1.5 hours (verification steps)

No validation errors predicted.

═══════════════════════════════════════════════════════════════

DRY-RUN MODE: No changes were made to the spec.

To apply these modifications, run without --dry-run:
  sdd apply-modifications auth-system-001 --from auth-fixes.json
```

## Step 5: Apply Modifications

The preview looks good. Apply the modifications:

```bash
sdd apply-modifications auth-system-001 --from auth-fixes.json
```

**Output:**
```
🔄 Applying Modifications to auth-system-001

✓ Loaded spec: auth-system-001
✓ Loaded modifications: auth-fixes.json (5 modifications)
✓ Backup created: specs/.backups/auth-system-001-20251106-143245.json

Applying modifications...

[1/5] ✓ Updated task-2-1 description
[2/5] ✓ Updated task-2-2 description
[3/5] ✓ Updated task-2-3 description
[4/5] ✓ Added verification step verify-2-1-3 to task-2-1
[5/5] ✓ Added verification step verify-2-2-4 to task-2-2

✓ All modifications applied successfully

Running validation...
✓ Spec structure valid
✓ All task references valid
✓ All verification IDs unique
✓ No schema violations

✓ Validation passed

═══════════════════════════════════════════════════════════════

✅ MODIFICATIONS APPLIED SUCCESSFULLY

Applied:    5 modifications
Skipped:    0 modifications (already applied)
Failed:     0 modifications

Changes:
  - Updated 3 task descriptions
  - Added 2 verification steps

Backup:     specs/.backups/auth-system-001-20251106-143245.json
Spec:       specs/active/auth-system-001.json

═══════════════════════════════════════════════════════════════

Next steps:
  1. Review updated spec: sdd context show auth-system-001
  2. Run verification steps: sdd verify auth-system-001
  3. Re-run fidelity review to confirm issues resolved
```

## Step 6: Document Changes

Add journal entry documenting the spec update:

```bash
sdd add-journal auth-system-001 \
  --title "Spec Updated from Fidelity Review Feedback" \
  --content "Applied 5 modifications based on fidelity review of Phase 2 implementation. Updated task descriptions to reflect actual OAuth 2.0 implementation details (PKCE flow, JWT tokens, refresh tokens, rate limiting). Added 2 verification steps for token expiration and rate limiting. All changes validated successfully." \
  --entry-type note
```

**Output:**
```
✓ Journal entry added to auth-system-001

Entry Details:
  Title:       "Spec Updated from Fidelity Review Feedback"
  Type:        note
  Timestamp:   2025-11-06T14:33:15Z
  Content:     [79 words]

✓ Spec updated
```

## Step 7: Verify Results

Check the updated spec to confirm changes:

```bash
sdd context show auth-system-001 --tasks
```

**Output (excerpt):**
```
Spec: auth-system-001 - Authentication System

Phase 2: Authentication Implementation
  task-2-1: Implement OAuth 2.0 authentication with PKCE flow, including JWT access tokens (15min expiry), refresh tokens (7 days expiry), and token rotation [completed]
    Verification:
      verify-2-1-1: ✓ User can authenticate with valid credentials
      verify-2-1-2: ✓ Invalid credentials are rejected
      verify-2-1-3: ⏳ Verify token expiration handling works correctly
        Command: pytest tests/test_auth.py::test_token_expiration -v

  task-2-2: Add /auth/login endpoint with rate limiting (10 req/min per IP) [completed]
    Verification:
      verify-2-2-1: ✓ Login endpoint returns valid tokens
      verify-2-2-2: ✓ Refresh endpoint works correctly
      verify-2-2-3: ✓ Logout endpoint invalidates tokens
      verify-2-2-4: ⏳ Verify rate limiting prevents abuse with concurrent requests
        Command: pytest tests/test_auth.py::test_rate_limiting_concurrent -v

  task-2-3: Write comprehensive tests covering OAuth flow, token expiration, refresh tokens, rate limiting, and error handling. Target 90%+ coverage. [in_progress]
```

Perfect! The spec now accurately reflects the implementation.

## Step 8: Run Verification Steps

Run the newly added verification steps:

```bash
sdd verify auth-system-001 verify-2-1-3
sdd verify auth-system-001 verify-2-2-4
```

**Output:**
```
Running verification: verify-2-1-3 (task-2-1)
Command: pytest tests/test_auth.py::test_token_expiration -v

============================= test session starts ==============================
collected 1 item

tests/test_auth.py::test_token_expiration PASSED                         [100%]

============================== 1 passed in 0.23s ===============================

✓ Verification passed

---

Running verification: verify-2-2-4 (task-2-2)
Command: pytest tests/test_auth.py::test_rate_limiting_concurrent -v

============================= test session starts ==============================
collected 1 item

tests/test_auth.py::test_rate_limiting_concurrent PASSED                 [100%]

============================== 1 passed in 1.45s ===============================

✓ Verification passed
```

## Step 9: Re-run Fidelity Review

Confirm all issues are resolved:

```bash
Skill(sdd-toolkit:sdd-fidelity-review) "Re-review spec auth-system-001 to confirm issues resolved"
```

**Output:**
```
🔍 Running Fidelity Review for auth-system-001

Analyzing implementation...
✓ Loaded spec: auth-system-001
✓ Found implementation files

Comparing against spec...

📋 Review Summary

✅ No issues found!

The specification accurately reflects the implementation:
  - Task descriptions include OAuth 2.0 specifics
  - Rate limiting is documented
  - Comprehensive test requirements specified
  - Token expiration verification present
  - Rate limiting verification present

Previous issues resolved: 5/5

✓ Spec and implementation are aligned
```

Success! The spec now accurately reflects the implementation, and all fidelity review issues are resolved.

## Summary

This example demonstrated the complete closed-loop workflow:

1. ✅ **Run fidelity review** - Identified 5 issues where spec didn't match implementation
2. ✅ **Parse review report** - Automatically extracted 5 modifications
3. ✅ **Preview modifications** - Reviewed changes before applying
4. ✅ **Apply modifications** - Applied with automatic backup and validation
5. ✅ **Document changes** - Added journal entry explaining updates
6. ✅ **Verify results** - Confirmed spec updates and ran new verification steps
7. ✅ **Re-review** - Confirmed all issues resolved

**Key Takeaways:**
- Fidelity review automatically identifies spec/implementation mismatches
- Parse-review extracts modifications without manual transcription
- Preview provides clear view of changes before applying
- Automatic backup, validation, and rollback ensure safety
- Re-review confirms issues are resolved

**Time Saved:**
- Manual approach: ~30-45 minutes (read review, manually edit spec, validate, check)
- Systematic approach: ~5-10 minutes (parse, preview, apply, verify)
- **Benefit:** Faster, less error-prone, more reliable
