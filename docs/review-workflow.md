# Review Workflow Guide

This guide covers how to apply feedback from fidelity reviews and other code reviews using SDD toolkit tools.

## Table of Contents

- [Overview](#overview)
- [The Review Lifecycle](#the-review-lifecycle)
- [Running Fidelity Reviews](#running-fidelity-reviews)
- [Interpreting Review Results](#interpreting-review-results)
- [Applying Review Feedback](#applying-review-feedback)
- [Tracking Review Iterations](#tracking-review-iterations)
- [Integration with PR Workflow](#integration-with-pr-workflow)
- [Best Practices](#best-practices)
- [Example Workflows](#example-workflows)

---

## Overview

The SDD toolkit provides tools for reviewing implementation fidelity and applying feedback systematically. This guide focuses on the practical workflow of:

1. Running fidelity reviews
2. Understanding review results
3. Applying feedback to code and specs
4. Validating fixes
5. Re-running reviews to confirm improvements

**Key Tools:**

- `sdd fidelity-review` - Compare implementation against spec
- `sdd-validate` - Validate spec structure after modifications
- `sdd-update` - Journal decisions and track changes
- `sdd-plan-review` - Multi-model spec review before implementation

---

## The Review Lifecycle

### Standard Review Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Review Lifecycle                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. IMPLEMENT                                                │
│     ↓                                                         │
│  2. RUN FIDELITY REVIEW                                      │
│     ↓                                                         │
│  3. ANALYZE RESULTS                                          │
│     ├─ PASS → Continue to PR                                │
│     └─ FAIL/PARTIAL → Fix Issues (go to step 4)            │
│                                                               │
│  4. APPLY FEEDBACK                                           │
│     ├─ Update code                                           │
│     ├─ Update spec (if needed)                              │
│     └─ Journal decisions                                     │
│     ↓                                                         │
│  5. VALIDATE CHANGES                                         │
│     ├─ Run sdd-validate (for spec changes)                  │
│     └─ Run tests (for code changes)                         │
│     ↓                                                         │
│  6. RE-REVIEW                                                │
│     ↓                                                         │
│  7. CONFIRM PASS → Create PR                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### When to Review

**During Implementation:**
- ✅ After completing each phase
- ✅ After significant feature additions
- ✅ When uncertain about implementation approach

**Before Milestones:**
- ✅ Before creating pull request
- ✅ Before marking spec as completed
- ✅ Before merging to main branch

**Ad-hoc:**
- ✅ When implementation feels "off track"
- ✅ After receiving stakeholder feedback
- ✅ When debugging complex issues

---

## Running Fidelity Reviews

### Basic Review Commands

**Review entire spec:**
```bash
sdd fidelity-review spec-id
```

**Review specific phase:**
```bash
sdd fidelity-review spec-id --phase phase-2
```

**Review specific task:**
```bash
sdd fidelity-review spec-id --task task-3-1
```

**Review specific files:**
```bash
sdd fidelity-review spec-id --files src/auth.ts src/middleware/auth.ts
```

### Controlling AI Consultation

**Use all available AI tools (default):**
```bash
sdd fidelity-review spec-id
```

**Use specific tools:**
```bash
sdd fidelity-review spec-id --ai-tools gemini codex
```

**Skip AI, show data only:**
```bash
sdd fidelity-review spec-id --no-ai
```

**Increase timeout for slow tools:**
```bash
sdd fidelity-review spec-id --timeout 300
```

### Output Options

**Save review to file:**
```bash
sdd fidelity-review spec-id --output review-phase-2.md --format markdown
```

**JSON output for automation:**
```bash
sdd fidelity-review spec-id --format json > review-results.json
```

**Detailed verbose output:**
```bash
sdd fidelity-review spec-id --verbose
```

---

## Interpreting Review Results

### Understanding Consensus Verdicts

**PASS** ✅
- Implementation matches specification
- Multiple AI tools agree
- Safe to proceed to PR

**PARTIAL** ⚠️
- Some deviations detected
- Mixed agreement among AI tools
- Review issues, decide if acceptable

**FAIL** ❌
- Significant deviations from spec
- Consensus among AI tools
- Must address issues before proceeding

**NEEDS_REVIEW** 🔍
- Unclear or conflicting signals
- Human judgment required
- Review individual model responses

### Reading the Report

**Example Review Output:**
```
================================================================================
IMPLEMENTATION FIDELITY REVIEW
================================================================================

Spec: user-auth-2025-10-24-001
Consulted 3 AI model(s)

Consensus Verdict: PARTIAL
Agreement Rate: 66.7%

--------------------------------------------------------------------------------
ISSUES IDENTIFIED (Consensus):
--------------------------------------------------------------------------------

[CRITICAL] Missing JWT token expiration handling
  Task task-2-1 spec requires token expiration check, but implementation
  doesn't validate exp claim in JWT payload.

  Files: src/middleware/auth.ts:45-67

[WARNING] Test coverage below spec requirements
  Spec requires 80% coverage, actual coverage is 65%

  Files: tests/auth.spec.ts

[INFO] Consider adding rate limiting
  Not required by spec, but recommended for production security

  Files: src/middleware/auth.ts

--------------------------------------------------------------------------------
RECOMMENDATIONS:
--------------------------------------------------------------------------------
- Add JWT expiration validation in src/middleware/auth.ts line 58
- Increase test coverage for edge cases (token expired, invalid signature)
- Consider adding integration tests for token refresh flow
- Document rate limiting decision in journal if skipping
```

### Severity Levels

**CRITICAL** - Must fix before merging
- Core spec requirements missing
- Security vulnerabilities
- Breaking changes to API contracts

**WARNING** - Should fix, may be acceptable
- Quality below spec expectations
- Missing non-essential requirements
- Test coverage gaps

**INFO** - Nice to have
- Suggestions for improvement
- Best practice recommendations
- Optional enhancements

---

## Applying Review Feedback

### Step 1: Categorize Feedback

Group feedback by action needed:

**Code Changes:**
- Implementation bugs
- Missing features
- Quality improvements

**Spec Changes:**
- Spec too strict/unrealistic
- Missing implementation details
- Requirements changed during implementation

**Documentation:**
- Journal decisions
- Update comments
- Add inline documentation

### Step 2: Fix Code Issues

For each code issue identified:

**1. Locate the problem:**
```bash
# Use the file/line info from review
# Example: src/middleware/auth.ts:45-67
```

**2. Implement the fix:**
- Make code changes to address the issue
- Follow spec requirements
- Add tests if needed

**3. Verify the fix:**
```bash
# Run tests
npm test

# Or pytest
pytest tests/test_file.py
```

**Example Fix:**
```typescript
// BEFORE (missing expiration check)
function verifyToken(token: string): User {
  const payload = jwt.verify(token, SECRET_KEY);
  return payload.user;
}

// AFTER (with expiration check per review feedback)
function verifyToken(token: string): User {
  const payload = jwt.verify(token, SECRET_KEY);

  // Added per fidelity review: check token expiration
  if (payload.exp && Date.now() >= payload.exp * 1000) {
    throw new Error('Token expired');
  }

  return payload.user;
}
```

### Step 3: Update Spec if Needed

Sometimes review reveals spec issues:

**When to update spec:**
- ✅ Spec requirement is unrealistic
- ✅ Implementation found better approach
- ✅ Requirements changed during implementation
- ✅ Missing details discovered

**When NOT to update spec:**
- ❌ To make review pass by lowering standards
- ❌ To hide implementation shortcuts
- ❌ To avoid fixing real issues

**How to update:**

```bash
# Edit spec JSON manually
nano specs/active/spec-id.json

# Make changes:
# - Update task descriptions
# - Adjust verification steps
# - Add new tasks if needed
# - Modify acceptance criteria

# Validate changes
```

Use sdd-validate subagent:
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/spec-id.json after updating based on review feedback",
  description: "Validate spec updates"
)
```

### Step 4: Journal Decisions

**Always journal why you made changes:**

```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to task task-2-1 in spec-id. Entry: Added JWT expiration check based on fidelity review feedback. Review identified missing token expiration validation. Implemented exp claim check per JWT RFC 7519.",
  description: "Document review fix"
)
```

**What to journal:**
- Which review issue you're addressing
- What change you made
- Why you chose this approach
- Any alternatives considered

### Step 5: Handle Disagreements

If you disagree with review feedback:

**Document your reasoning:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to task task-3-2 in spec-id. Entry: Review suggested rate limiting, but deferring to Phase 3 as spec focuses on core auth only. Will address in separate performance spec.",
  description: "Document review decision"
)
```

**Update spec to clarify:**
- Add risk notes explaining the decision
- Update verification steps to reflect actual approach
- Add future task for deferred improvements

---

## Tracking Review Iterations

### First Review

1. Run initial review:
```bash
sdd fidelity-review spec-id --output review-v1.md --format markdown
```

2. Save results for comparison

3. Create checklist from issues:
   - [ ] Fix JWT expiration check
   - [ ] Increase test coverage to 80%
   - [ ] Add integration tests

### Subsequent Reviews

After applying fixes:

1. Run review again:
```bash
sdd fidelity-review spec-id --output review-v2.md --format markdown
```

2. Compare with previous review:
```bash
diff review-v1.md review-v2.md
```

3. Verify issues resolved:
   - [x] Fix JWT expiration check
   - [x] Increase test coverage to 80%
   - [ ] Add integration tests (deferred to Phase 3)

### Tracking in Journal

Journal each review iteration:

```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to spec spec-id. Entry: Fidelity review iteration 2 complete. Addressed CRITICAL issue (JWT expiration) and WARNING issue (test coverage now 82%). Deferred INFO suggestion (rate limiting) to Phase 3 performance spec.",
  description: "Document review iteration"
)
```

---

## Integration with PR Workflow

### Review Before PR Creation

**Recommended workflow:**

```bash
# 1. Complete phase or spec
sdd check-complete spec-id

# 2. Run fidelity review
sdd fidelity-review spec-id --output pr-review.md --format markdown

# 3. Address any CRITICAL/WARNING issues
# ... make fixes ...

# 4. Re-review if needed
sdd fidelity-review spec-id

# 5. Create PR once review passes
Skill(sdd-toolkit:sdd-pr)
```

### Including Review in PR Description

The `sdd-pr` skill can include review results:

```
Skill(sdd-toolkit:sdd-pr)

# Automatically includes:
# - Journal entries (including review fixes)
# - Spec metadata
# - Git diff summary
# - Commit messages
```

**Manual PR description enhancement:**

```markdown
## Implementation Fidelity Review

Final review status: **PASS** ✅

Consulted 3 AI models with 100% agreement.

### Issues Addressed During Implementation

1. **[CRITICAL] JWT expiration check** - Added validation in auth middleware
2. **[WARNING] Test coverage** - Increased from 65% to 82%

### Deferred Items

- Rate limiting - Deferred to Phase 3 performance spec (see journal task-3-2)

Review report: [Link to review-v2.md]
```

---

## Best Practices

### Before Review

**DO:**
- ✅ Complete verification steps defined in spec
- ✅ Run all tests and ensure they pass
- ✅ Review code yourself first
- ✅ Ensure git commits are clean

**DON'T:**
- ❌ Review half-finished implementations
- ❌ Skip spec verification steps
- ❌ Review with failing tests
- ❌ Review uncommitted changes

### During Review Analysis

**DO:**
- ✅ Read full review report carefully
- ✅ Understand each issue before fixing
- ✅ Consider all recommendations
- ✅ Check agreement rate and individual responses

**DON'T:**
- ❌ Blindly fix everything without understanding
- ❌ Ignore INFO-level suggestions without consideration
- ❌ Skip reading recommendations
- ❌ Dismiss issues with low agreement without investigation

### When Applying Feedback

**DO:**
- ✅ Fix CRITICAL issues immediately
- ✅ Journal why you made each change
- ✅ Validate spec after updates
- ✅ Re-run review to confirm fixes
- ✅ Update tests along with code

**DON'T:**
- ❌ Modify spec just to make review pass
- ❌ Skip journaling decisions
- ❌ Skip validation after spec changes
- ❌ Assume fixes worked without re-review
- ❌ Update code without updating tests

### After Review Passes

**DO:**
- ✅ Save final review report
- ✅ Include review summary in PR
- ✅ Journal final review status
- ✅ Proceed confidently to merge

**DON'T:**
- ❌ Skip final review before merge
- ❌ Forget to save review artifacts
- ❌ Make changes after final review without re-reviewing

---

## Example Workflows

### Example 1: Phase Review and Fixes

**Scenario**: Completed Phase 2, running review before moving to Phase 3.

**Workflow:**

```bash
# 1. Complete last task in phase
# (via sdd-update subagent)

# 2. Run phase review
sdd fidelity-review spec-id --phase phase-2 --output phase2-review-v1.md

# Output shows PARTIAL verdict with 2 issues:
# - [CRITICAL] Missing error handling in auth middleware
# - [WARNING] Insufficient test coverage (60% vs 80% required)

# 3. Fix critical issue
# Edit src/middleware/auth.ts, add error handling

# 4. Fix warning issue
# Add more test cases to tests/auth.spec.ts

# 5. Journal the fixes
```

Use sdd-update:
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to phase phase-2 in spec-id. Entry: Applied fidelity review feedback. Added error handling to auth middleware (CRITICAL). Increased test coverage from 60% to 85% (WARNING). Both issues resolved.",
  description: "Document review fixes"
)
```

```bash
# 6. Re-run review
sdd fidelity-review spec-id --phase phase-2 --output phase2-review-v2.md

# Output shows PASS verdict

# 7. Proceed to Phase 3
# Use /sdd-begin to continue
```

### Example 2: Spec Update Based on Review

**Scenario**: Review reveals spec requirement is unrealistic.

**Workflow:**

```bash
# 1. Run review
sdd fidelity-review spec-id --task task-3-5

# Output shows:
# [CRITICAL] Task requires 99.9% uptime guarantee
# Implementation: Best-effort caching, no uptime SLA
# Recommendation: Either implement proper high-availability or update spec

# 2. Decide spec is unrealistic for this phase
# Will defer HA to future spec

# 3. Update spec JSON
nano specs/active/spec-id.json

# Change task-3-5 description from:
#   "Implement caching with 99.9% uptime guarantee"
# To:
#   "Implement best-effort caching with monitoring"

# Add risk note:
#   "High availability deferred to Phase 4. Current implementation
#    provides best-effort caching without uptime SLA."

# 4. Validate spec changes
```

Use sdd-validate:
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/spec-id.json after updating task-3-5",
  description: "Validate spec"
)
```

```bash
# 5. Journal the decision
```

Use sdd-update:
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to task task-3-5 in spec-id. Entry: Updated spec based on fidelity review. Original requirement (99.9% uptime) unrealistic for current phase. Changed to best-effort caching with monitoring. HA deferred to Phase 4 infrastructure spec.",
  description: "Document spec change"
)
```

```bash
# 6. Re-run review
sdd fidelity-review spec-id --task task-3-5

# Output shows PASS - implementation now matches updated spec

# 7. Continue with next task
```

### Example 3: Multi-Tool Consensus Analysis

**Scenario**: Different AI tools give conflicting feedback.

**Workflow:**

```bash
# 1. Run review with verbose output
sdd fidelity-review spec-id --verbose

# Output shows:
# Consensus Verdict: NEEDS_REVIEW
# Agreement Rate: 33.3%
#
# Individual Responses:
# - gemini: PASS (no issues)
# - codex: FAIL (missing input validation)
# - cursor-agent: PARTIAL (test coverage low)

# 2. Analyze each response
# - gemini: May have missed validation issue
# - codex: Correctly identified missing validation (security)
# - cursor-agent: Correctly identified test coverage gap

# 3. Use human judgment
# Security issue (codex) is more critical than consensus suggests
# Test coverage (cursor-agent) is valid concern

# 4. Address both issues even though not consensus

# 5. Re-run with specific tools to verify fixes
sdd fidelity-review spec-id --ai-tools codex cursor-agent

# 6. If both now PASS, overall verdict will be better
```

---

## Systematic Feedback Application with sdd-modify

After reviews identify spec/implementation mismatches, use `sdd-modify` to systematically apply fixes to the spec.

### Why Systematic Application?

**Manual spec editing risks:**
- ❌ Typos and formatting errors
- ❌ Forgetting to update related sections
- ❌ No backup before changes
- ❌ No validation after changes
- ❌ Time-consuming for multiple fixes

**Systematic approach benefits:**
- ✅ Automatic extraction from review reports
- ✅ Preview before applying
- ✅ Automatic backup and rollback
- ✅ Validation after every change
- ✅ 70-80% faster than manual editing

### Complete Closed-Loop Workflow

```
1. Implementation Complete
        ↓
2. Run Fidelity Review
   sdd fidelity-review spec-id --output review.md
        ↓
3. Review Identifies Issues
   - Vague task descriptions
   - Missing verification steps
   - Metadata inconsistencies
        ↓
4. Parse Review Report
   sdd parse-review spec-id --review review.md
   → Generates structured modifications.json
        ↓
5. Preview Modifications
   sdd apply-modifications spec-id --from suggestions.json --dry-run
   → Shows exactly what will change
        ↓
6. Apply Modifications
   sdd apply-modifications spec-id --from suggestions.json
   → Automatic backup, validation, rollback
        ↓
7. Document Changes
   sdd add-journal spec-id --title "Applied review feedback"
        ↓
8. Re-Review to Confirm
   sdd fidelity-review spec-id
   → Should show: "Previous issues resolved"
```

### Step-by-Step Example

**Step 1: Review finds issues**

```bash
sdd fidelity-review my-spec-001 --output review-report.md
```

**Output:**
```
Consensus Verdict: PARTIAL
Issues Found: 5

1. [CRITICAL] Task task-2-1 description too vague
   Spec: "Implement auth"
   Actual: OAuth 2.0 with PKCE, JWT tokens, refresh rotation

2. [WARNING] Missing verification for token expiration (task-2-1)

3. [WARNING] Missing verification for rate limiting (task-2-2)

4. [INFO] Task task-3-2 estimated_hours incorrect (8h, actually took 12h)

5. [INFO] Task descriptions don't mention error handling details
```

**Step 2: Parse review feedback**

```bash
sdd parse-review my-spec-001 --review review-report.md --output suggestions.json
```

**Generated suggestions.json:**

```json
{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-2-1",
      "field": "description",
      "value": "Implement OAuth 2.0 authentication with PKCE flow, JWT access tokens (15min expiry), and refresh token rotation (7 days expiry)",
      "confidence": "high",
      "source": "fidelity-review-issue-1"
    },
    {
      "operation": "add_verification",
      "task_id": "task-2-1",
      "verify_id": "verify-2-1-4",
      "description": "Verify token expiration and refresh flow works correctly",
      "command": "pytest tests/test_auth.py::test_token_lifecycle -v",
      "confidence": "high",
      "source": "fidelity-review-issue-2"
    },
    {
      "operation": "add_verification",
      "task_id": "task-2-2",
      "verify_id": "verify-2-2-5",
      "description": "Verify rate limiting prevents abuse with concurrent requests",
      "command": "pytest tests/test_auth.py::test_rate_limiting -v",
      "confidence": "medium",
      "source": "fidelity-review-issue-3"
    },
    {
      "operation": "update_metadata",
      "task_id": "task-3-2",
      "field": "actual_hours",
      "value": 12.0,
      "confidence": "high",
      "source": "fidelity-review-issue-4"
    }
  ]
}
```

**Step 3: Preview modifications**

```bash
sdd apply-modifications my-spec-001 --from suggestions.json --dry-run
```

**Output:**
```
📋 Modification Preview (Dry-Run Mode)

Spec: my-spec-001
Total modifications: 4

═══════════════════════════════════════════════════════════════
TASKS TO UPDATE (1 task)
───────────────────────────────────────────────────────────────
Task: task-2-1 (Phase 2)
Field: description
Current: "Implement auth"
New:     "Implement OAuth 2.0 authentication with PKCE flow, JWT access tokens (15min expiry), and refresh token rotation (7 days expiry)"

═══════════════════════════════════════════════════════════════
VERIFICATION STEPS TO ADD (2 steps)
───────────────────────────────────────────────────────────────
Task: task-2-1
Verify ID: verify-2-1-4
Description: "Verify token expiration and refresh flow works correctly"
Command: pytest tests/test_auth.py::test_token_lifecycle -v
───────────────────────────────────────────────────────────────
Task: task-2-2
Verify ID: verify-2-2-5
Description: "Verify rate limiting prevents abuse with concurrent requests"
Command: pytest tests/test_auth.py::test_rate_limiting -v

═══════════════════════════════════════════════════════════════
METADATA TO UPDATE (1 task)
───────────────────────────────────────────────────────────────
Task: task-3-2
Field: actual_hours
Current: 0.0
New:     12.0

═══════════════════════════════════════════════════════════════
IMPACT SUMMARY

Tasks affected:               3
Verification steps added:     2
Metadata updated:             1
Total modifications:          4

Validation prediction: ✓ No errors expected
```

**Step 4: Apply modifications**

```bash
sdd apply-modifications my-spec-001 --from suggestions.json
```

**Output:**
```
✓ Backup created: specs/.backups/my-spec-001-20251106-153022.json
✓ Applied 4 modifications
✓ Validation passed

Changes:
  - Updated 1 task description
  - Added 2 verification steps
  - Updated 1 metadata field

Backup: specs/.backups/my-spec-001-20251106-153022.json
```

**Step 5: Document changes**

```bash
sdd add-journal my-spec-001 \
  --title "Applied Fidelity Review Feedback" \
  --content "Applied 4 modifications based on fidelity review: clarified OAuth 2.0 implementation details in task-2-1, added 2 verification steps for token expiration and rate limiting, corrected actual_hours for task-3-2. All changes validated successfully." \
  --entry-type note
```

**Step 6: Re-review to confirm**

```bash
sdd fidelity-review my-spec-001
```

**Output:**
```
Consensus Verdict: PASS
Agreement Rate: 100%

Previous issues resolved: 4/4
New issues: 0

✓ Implementation matches updated spec
✓ All verification steps documented
✓ Metadata accurate
```

### Benefits vs Manual Editing

**Time Comparison:**

| Task | Manual | Systematic | Time Saved |
|------|--------|-----------|------------|
| Parse review feedback | 10-15 min | 30 sec | 93% |
| Edit spec JSON | 15-20 min | 1 min | 95% |
| Validate changes | 2-3 min | Automatic | 100% |
| Create backup | Manual | Automatic | 100% |
| Document changes | 5 min | 2 min | 60% |
| **Total** | **35-45 min** | **5-10 min** | **78-89%** |

**Error Reduction:**

- Manual editing error rate: ~15-20% (typos, forgotten fields, invalid JSON)
- Systematic approach error rate: ~0-2% (automatic validation catches issues)

### When to Use Systematic Application

**Always use for:**
- ✅ Fidelity review feedback (spec/implementation mismatches)
- ✅ Plan review consensus recommendations
- ✅ Multiple related spec changes at once
- ✅ Any changes requiring validation

**Manual editing acceptable for:**
- ❌ Single small change (e.g., fix one typo)
- ❌ Experimental spec modifications

### Troubleshooting Systematic Application

**Issue: Parse-review finds nothing**

```bash
# Review report doesn't contain parseable patterns
# Solution: Create modification file manually

{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-2-1",
      "field": "description",
      "value": "New description based on review feedback"
    }
  ]
}
```

**Issue: Validation fails after application**

```bash
# Automatic rollback occurs
# Fix modification file and retry

# Preview to verify fix
sdd apply-modifications spec-id --from fixed-mods.json --dry-run

# Apply
sdd apply-modifications spec-id --from fixed-mods.json
```

**Issue: Need to rollback**

```bash
# Restore from automatic backup
cp specs/.backups/spec-id-TIMESTAMP.json specs/active/spec-id.json
```

### Integration Points

**After sdd-fidelity-review:**

```bash
# Review identifies spec/implementation mismatches
sdd fidelity-review spec-id → Review report

# Systematic application
sdd parse-review spec-id --review report.md
sdd apply-modifications spec-id --from suggestions.json

# Confirm fixes
sdd fidelity-review spec-id → Should show PASS
```

**After sdd-plan-review:**

```bash
# Plan review identifies spec improvements
sdd review spec-id → Multi-model feedback

# Extract consensus recommendations
# (Manual step - create consensus-mods.json)

# Apply consensus improvements
sdd apply-modifications spec-id --from consensus-mods.json --dry-run
sdd apply-modifications spec-id --from consensus-mods.json
```

### Best Practices

**DO:**
- ✅ Always preview with --dry-run first
- ✅ Apply in small batches (5-10 modifications)
- ✅ Document why changes were made (journal entries)
- ✅ Keep modification files for audit trail
- ✅ Re-review after applying to confirm fixes

**DON'T:**
- ❌ Skip preview for significant changes
- ❌ Apply modifications without understanding them
- ❌ Delete backups immediately
- ❌ Use --no-validate (defeats safety checks)
- ❌ Apply conflicting modifications in one batch

### Additional Resources

**See Also:**
- **Skill Documentation:** `skills/sdd-modify/SKILL.md` - Complete reference
- **Examples:** `skills/sdd-modify/examples/apply-review.md` - Detailed walkthrough
- **Spec Modification Guide:** `docs/spec-modification.md` - Comprehensive guide
- **CLI Help:** `sdd parse-review --help`, `sdd apply-modifications --help`

---

## Additional Resources

**Related Documentation:**
- [Spec Modification Guide](./spec-modification.md) - Detailed modification workflow
- [Best Practices](./BEST_PRACTICES.md) - General SDD best practices
- [Architecture](./ARCHITECTURE.md) - System architecture details

**Related Skills:**
- `Skill(sdd-toolkit:sdd-plan-review)` - Multi-model spec review before implementation
- `Skill(sdd-toolkit:sdd-validate)` - Validate spec structure
- `Skill(sdd-toolkit:sdd-update)` - Update task status and journal
- `Skill(sdd-toolkit:sdd-pr)` - Create AI-powered pull requests

**Commands:**
- `sdd fidelity-review --help` - Complete command reference
- `sdd list-review-tools` - Check available AI tools
- `sdd validate-spec` - Quick spec validation

---

## Summary

**Review Workflow Checklist:**

1. ✅ Complete implementation milestone
2. ✅ Run fidelity review
3. ✅ Analyze results (verdict, issues, recommendations)
4. ✅ Categorize feedback (code, spec, documentation)
5. ✅ Apply fixes (prioritize CRITICAL)
6. ✅ Validate changes (tests for code, sdd-validate for spec)
7. ✅ Journal decisions and changes
8. ✅ Re-run review to confirm
9. ✅ Proceed when PASS achieved

**Key Principles:**

- **Review early, review often** - Catch issues before they compound
- **Address consensus issues** - Multiple AI tools agreeing signals real problems
- **Journal everything** - Document why you made changes
- **Validate after changes** - Ensure fixes didn't break anything
- **Re-review to confirm** - Don't assume fixes worked

The review workflow is iterative. It's normal to run multiple review cycles before achieving PASS. The goal is continuous improvement and alignment between spec and implementation.
