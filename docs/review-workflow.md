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
