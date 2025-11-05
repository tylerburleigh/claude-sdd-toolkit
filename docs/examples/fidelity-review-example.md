# SDD Toolkit Example: Implementation Fidelity Review

## Overview

This example demonstrates the Implementation Fidelity Review skill, which verifies that your code implementation matches the specification requirements. Fidelity review helps catch implementation drift, missing requirements, and specification deviations before they become technical debt.

The fidelity review process works by:
1. Extracting spec requirements for a task
2. Analyzing git diffs to see what was actually implemented
3. Running tests to verify functionality
4. Optionally consulting multiple AI models for consensus-based quality assessment
5. Generating a comprehensive review report with categorized issues

This skill is particularly valuable for:
- Quality-gating critical implementations (security, auth, data handling)
- Reviewing completed phases before moving forward
- Getting multi-model consensus on implementation quality
- Auditing implementation fidelity across a spec

---

## The Scenario

You've just completed implementing a JWT authentication middleware task. The spec defined specific requirements:
- Implement JWT token verification
- Return 401 for invalid tokens
- Attach user data to request on success
- Support token refresh
- Include rate limiting

Before marking the task fully complete and moving on, you want to verify that your implementation actually fulfills all the spec requirements.

---

## The Workflow

### Step 1: Complete the Implementation

First, you've implemented the code and run tests:

```
You: I've finished implementing the JWT middleware. The tests pass.

Claude: Great! Before moving to the next task, would you like to run a
        fidelity review to verify your implementation matches the spec
        requirements?

You: Yes, review it.
```

### Step 2: Invoke the Fidelity Review Skill

Claude invokes the fidelity review skill to analyze your implementation:

```
Claude: I'll use the fidelity review skill to check your implementation
        against the spec requirements.

> Skill(sdd-toolkit:sdd-fidelity-review) is loading...

⏺ I'll review the implementation of task-2-3 (JWT middleware) against
  the spec requirements.

⏺ Bash(sdd fidelity-review user-auth-001 --task task-2-3 --ai-tools gemini codex)
  ⎿ 🔍 Implementation Fidelity Review

    Spec: user-auth-001 (User Authentication System)
    Task: task-2-3 (Implement JWT verification middleware)

    📋 SPEC REQUIREMENTS EXTRACTED:

    Required features:
    ✓ JWT token verification
    ✓ 401 response for invalid tokens
    ✓ Attach user data to request on success
    ✓ Support token refresh
    ✓ Include rate limiting

    📊 GIT DIFF ANALYSIS:

    Files changed: 1
    - src/middleware/jwt.ts (+142 lines)

    Changes include:
    ✓ verifyToken() function
    ✓ Error handling for invalid tokens
    ✓ Request augmentation with user data
    ✓ Token refresh endpoint
    ✗ No rate limiting implementation found

    🧪 TEST RESULTS:

    ✓ test_jwt_verification_success (PASSED)
    ✓ test_jwt_invalid_token_returns_401 (PASSED)
    ✓ test_user_data_attached_to_request (PASSED)
    ✓ test_token_refresh (PASSED)
    ✗ test_rate_limiting (NOT FOUND)

    🤖 AI CONSENSUS REVIEW:

    Consulting: gemini, codex

    Gemini verdict: minor_issues (confidence: 0.85)
    - Missing rate limiting as specified
    - Otherwise well implemented
    - Tests cover main functionality

    Codex verdict: minor_issues (confidence: 0.82)
    - Rate limiting requirement not met
    - Implementation is clean and functional
    - Good error handling

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CONSENSUS: minor_issues (agreement: 100%)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📊 CATEGORIZED ISSUES:

    Major Issues (1):
    • Missing implementation: Rate limiting not implemented
      - Spec requirement: "Include rate limiting"
      - No evidence in diff or tests
      - Recommendation: Add rate limiting middleware

    Minor Issues (0):

    ✅ RECOMMENDATIONS:

    1. Add rate limiting to JWT middleware
       - Consider using express-rate-limit or similar
       - Spec suggests token-based rate limiting
       - Add tests for rate limit behavior

    2. Document rate limiting decision
       - If deferred, journal why
       - If alternate approach, note in spec

    VERDICT: Implementation is functional but incomplete.
             Add rate limiting before marking task fully complete.
```

### Step 3: Analyze the Results

Claude presents the findings:

```
Claude: The fidelity review found that your implementation is functionally
        correct but missing one requirement: rate limiting.

        Both AI models agree (100% consensus) that this is a minor issue.
        The JWT verification, error handling, user data attachment, and
        token refresh are all implemented correctly.

        Options:
        1. Add rate limiting now to fully meet spec requirements
        2. Defer rate limiting and document the decision
        3. Update the spec if rate limiting is no longer needed

        What would you like to do?
```

### Step 4: Take Action

You decide to add the missing feature:

```
You: Let's add rate limiting now.

Claude: I'll implement rate limiting for the JWT middleware.

⏺ Edit(src/middleware/jwt.ts)
  ⎿ Added rate limiting using express-rate-limit
    - 100 requests per 15-minute window
    - Per-token rate limiting
    - 429 status for exceeded limits

⏺ Edit(tests/middleware/jwt.spec.ts)
  ⎿ Added rate limiting test
    - Verifies limit enforcement
    - Checks 429 response
    - Tests limit reset

⏺ Bash(npm test)
  ⎿ ✓ All tests passing (5/5)
```

### Step 5: Re-run Fidelity Review

Now verify the fix:

```
You: Run the fidelity review again.

Claude: I'll verify the implementation now includes all requirements.

⏺ Bash(sdd fidelity-review user-auth-001 --task task-2-3 --ai-tools gemini codex)
  ⎿ 🔍 Implementation Fidelity Review

    ... (similar output as before)

    🤖 AI CONSENSUS REVIEW:

    Gemini verdict: passes (confidence: 0.92)
    - All requirements met
    - Clean implementation
    - Comprehensive tests

    Codex verdict: passes (confidence: 0.90)
    - Complete implementation
    - Follows best practices
    - Good test coverage

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CONSENSUS: passes (agreement: 100%)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✅ VERDICT: Implementation fully meets spec requirements.

Claude: Perfect! The implementation now passes fidelity review. All spec
        requirements are met and both AI models agree.

        Task task-2-3 is ready to be marked complete.
```

### Step 6: Document and Complete

```
You: Great, mark it complete.

Claude: I'll complete the task and document the fidelity review.

⏺ Task(sdd-toolkit:sdd-update-subagent)
  ⎿ Completed task-2-3

    Journal entry:
    - Implemented JWT verification middleware
    - Added rate limiting after fidelity review
    - All tests passing
    - Fidelity review: PASSES (100% AI consensus)

    Task completed: 2025-11-05 15:30:42
    Time spent: 2.5 hours

Claude: Task completed! The implementation has been verified against spec
        requirements and documented.

        Progress: Phase 2 is now 3/8 tasks complete (37.5%)
```

---

## When to Use Fidelity Review

**Use fidelity review for:**
- ✅ Critical implementations (security, auth, data handling)
- ✅ Complex multi-requirement tasks
- ✅ End-of-phase quality gates
- ✅ High-risk changes requiring validation
- ✅ Tasks where you're uncertain about completeness

**Skip for:**
- ❌ Simple single-requirement tasks
- ❌ Exploratory/research tasks
- ❌ Tasks without clear spec requirements
- ❌ When you're confident requirements are met

---

## Review Modes

### 1. Basic Review (No AI)

Quick check without AI consultation:

```bash
sdd fidelity-review user-auth-001 --task task-2-3 --no-ai
```

Shows:
- Extracted requirements
- Git diff analysis
- Test results
- No AI verdict (you decide)

Use when: You just need the raw data to make your own judgment.

### 2. Single AI Model Review

Consult one AI for assessment:

```bash
sdd fidelity-review user-auth-001 --task task-2-3 --ai-tools gemini
```

Shows: Everything from basic + AI analysis from one model.

Use when: You want AI guidance but don't need consensus.

### 3. Multi-Model Consensus Review

Get agreement from multiple AIs:

```bash
sdd fidelity-review user-auth-001 --task task-2-3 --ai-tools gemini codex cursor-agent
```

Shows: Everything + consensus verdict with agreement rate.

Use when: Critical tasks requiring high confidence in assessment.

### 4. Phase Review

Review entire phase at once:

```bash
sdd fidelity-review user-auth-001 --phase phase-2
```

Reviews all completed tasks in the phase.

Use when: Quality-gating before moving to next phase.

---

## Understanding Verdicts

Fidelity reviews return one of four verdicts:

**passes** - Implementation fully meets requirements
- All spec requirements implemented
- Tests verify functionality
- Ready to mark complete

**minor_issues** - Implementation works but has small gaps
- Core functionality correct
- Minor requirements missing or incomplete
- Decide whether to fix now or defer

**major_issues** - Significant requirements missing
- Critical functionality absent
- Tests failing or incomplete
- Should fix before proceeding

**fails** - Implementation doesn't meet spec
- Multiple critical issues
- Fundamental misalignment with spec
- Requires significant rework

---

## Consensus Thresholds

When using multiple AI tools, you can set consensus requirements:

```bash
# Require at least 2 models to agree
sdd fidelity-review spec-001 --task task-1-1 --ai-tools gemini codex cursor-agent --consensus-threshold 2

# Require all 3 to agree
sdd fidelity-review spec-001 --task task-1-1 --ai-tools gemini codex cursor-agent --consensus-threshold 3
```

Default: 2 models must agree.

Higher thresholds increase confidence but may be overly strict.

---

## Tips for Effective Fidelity Reviews

**1. Review early and often**
- Don't wait until the end to discover issues
- Review after each task or at least after each phase

**2. Use multiple AI models for critical tasks**
- Consensus reduces false positives/negatives
- Different models catch different issues

**3. Act on findings promptly**
- Fix issues while context is fresh
- Document deferrals with clear justification

**4. Integrate into workflow**
- Make fidelity review part of your task completion process
- Especially for security, auth, and data handling tasks

**5. Save review reports**
- Use `--output` to keep review history
- Useful for retrospectives and audits

```bash
sdd fidelity-review spec-001 --task task-2-3 --output reviews/task-2-3-review.md --format markdown
```

---

## Common Scenarios

### Scenario: Implementation passes but with minor deviations

```
Verdict: minor_issues
Issue: "Implementation uses async/await instead of Promises as spec suggested"

Action: Document the decision
- Journal why async/await was chosen
- Update spec if this is the new pattern
- No code changes needed
```

### Scenario: Critical requirement completely missing

```
Verdict: major_issues
Issue: "Authorization check not implemented (spec requirement #3)"

Action: Fix immediately
- Implement missing requirement
- Add tests
- Re-run fidelity review
```

### Scenario: Tests not matching implementation

```
Verdict: major_issues
Issue: "Tests verify outdated behavior, not current implementation"

Action: Update tests
- Align tests with actual implementation
- Verify implementation still meets spec
- Re-run fidelity review
```

### Scenario: Spec requirements are wrong

```
Verdict: fails
Issue: "Implementation doesn't match spec"
Reality: Spec requirements were incorrect

Action: Update spec
- Revise spec requirements
- Document why changes were needed
- Re-run fidelity review against updated spec
```

---

## Integration with SDD Workflow

Fidelity review fits naturally into the SDD workflow:

```
1. sdd-plan
   ↓ (creates spec)

2. sdd-next
   ↓ (finds task)

3. Implement task
   ↓

4. Run tests
   ↓

5. sdd-fidelity-review ← QUALITY GATE
   ↓ (verify vs spec)

6. Fix issues (if needed)
   ↓

7. sdd-update
   ↓ (mark complete)

8. Repeat for next task
```

Fidelity review acts as a quality gate between implementation and completion.

---

## Prerequisites

**Required:**
- Active SDD spec with completed tasks
- Git repository with commits for tasks

**Optional (for AI consultation):**
- `gemini` CLI tool installed
- `codex` CLI tool installed
- `cursor-agent` CLI tool installed

Check availability:
```bash
sdd list-review-tools
```

---

## Next Steps

Ready to use fidelity review?

1. ✅ Complete a task implementation
2. ✅ Run tests to verify functionality
3. 🔍 Run fidelity review: `sdd fidelity-review {spec-id} --task {task-id} --ai-tools gemini codex`
4. 📊 Analyze the verdict and issues
5. 🔧 Fix any major issues found
6. ✅ Re-run review if needed
7. 📝 Mark task complete with confidence

**Questions?** See the [fidelity review skill documentation](../../skills/sdd-fidelity-review/SKILL.md) for complete details.
