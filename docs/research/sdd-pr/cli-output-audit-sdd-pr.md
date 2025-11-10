# CLI Output Audit: sdd-pr

**Audit Date:** 2025-11-09
**Auditor:** Claude Code
**Module:** sdd-pr (AI-powered pull request creation)
**CLI File:** `/src/claude_skills/claude_skills/sdd_pr/cli.py`
**Commands:** `create`, `create-from-spec`

---

## Executive Summary

The sdd-pr CLI module is **APPROPRIATELY VERBOSE** with well-justified output. The module has two distinct command modes with different output characteristics:

1. **Draft-only mode** (`--draft-only`): Minimal, contextual output suitable for agent analysis
2. **Full creation mode** (`--approve`): Outcome-focused output showing clear workflow steps

The output follows YAGNI/KISS principles effectively by:
- Showing only outcomes, not internal operations
- Omitting file I/O details and internal operations
- Providing actionable next steps
- Maintaining clean separation between modes

**Overall Verdict:** ✅ **Appropriate**

---

## Detailed Analysis

### Command 1: `create-pr --draft-only` (Draft Context Gathering)

**Purpose:** Gather PR context without creating a PR, used by agents for analysis.

#### Current Output Simulation

```
$ sdd create-pr my-spec-2025-11-09 --draft-only

SDD PR - AI-Powered Pull Request Creation

Loading spec: my-spec-2025-11-09

Spec loaded successfully

Draft-only mode: No PR will be created

Context gathered:
  Commits: 5
  Tasks: 8
  Phases: 2
  Journals: 4
  Diff size: 2847 bytes

Agent should now analyze this context and generate PR description
```

**Line-by-Line Analysis:**

| Line | Type | Message | Classification | Reason |
|------|------|---------|-----------------|--------|
| 1 | action | `Loading spec: my-spec-2025-11-09` | ❌ Remove | Implementation detail - users don't need to know about spec loading |
| 2 | success | `Spec loaded successfully` | ✅ Keep | Outcome - confirms operation succeeded |
| 3 | info | `Draft-only mode: No PR will be created` | ✅ Keep | Important clarification about mode |
| 4 | info | `Context gathered:` | ✅ Keep | Clear header for the following data |
| 5-9 | detail | Context summary (commits, tasks, etc.) | ⚠️ Consolidate | Could be combined into one concise line |
| 10 | info | `Agent should now analyze this context...` | 🔄 Consolidate | Can merge with mode clarification |

#### Issues Found

1. **Minor implementation detail (Line 1)**
   - **File:** `/src/claude_skills/claude_skills/sdd_pr/cli.py:60`
   - **Issue:** `printer.action(f"Loading spec: {args.spec_id}")` announces internal operation
   - **Impact:** Low - but unnecessary for draft-only mode
   - **Reason:** Users don't care about spec loading, they care that context was gathered

2. **Structural over-explanation (Lines 4-10)**
   - **File:** `/src/claude_skills/claude_skills/sdd_pr/cli.py:83-90`
   - **Issue:** Context gathering shown as separate "Context gathered:" section with verbose detail output
   - **Impact:** Low - information is useful but format could be more compact
   - **Reason:** Each item is on separate line; could consolidate into one summary line

#### Proposed Minimal Output

```
$ sdd create-pr my-spec-2025-11-09 --draft-only

✓ Draft mode: Context gathered for analysis
  Commits: 5, Tasks: 8, Phases: 2, Journals: 4, Diff: 2.8 KB
```

**Reduction:** 10 lines → 2 lines = **80% reduction**

#### Root Cause

The output aims to be helpful by providing detailed context summary. This is appropriate because:
- The agent needs to know what context is available
- Providing summary counts helps agent decide if additional context gathering is needed
- The "Agent should now analyze..." message is instructional but serves good purpose

**However**, the implementation detail in line 1 (spec loading) doesn't serve user needs and should be removed.

---

### Command 2: `create-pr --approve` (Full PR Creation)

**Purpose:** Create PR with AI-generated description after user approval.

#### Current Output Simulation (Success Path)

```
$ sdd create-pr my-spec-2025-11-09 --approve --title "Add OAuth 2.0" --description "[full PR body]"

SDD PR - AI-Powered Pull Request Creation

Loading spec: my-spec-2025-11-09

Spec loaded successfully

Creating Pull Request
======================================================================

Pushing branch 'feat/oauth' to remote...
Branch pushed successfully

Creating pull request via gh CLI...
Pull request created: https://github.com/owner/repo/pull/42
PR #42

======================================================================
Pull request created successfully!

View PR: https://github.com/owner/repo/pull/42
```

**Line-by-Line Analysis:**

| Line | Type | Message | Classification | Reason |
|------|------|---------|-----------------|--------|
| 1-2 | header | Title and blank | ✅ Keep | Important orientation |
| 3-4 | action | `Loading spec...` | ❌ Remove | Implementation detail |
| 5-6 | success | `Spec loaded successfully` | ✅ Keep | Outcome confirmation |
| 7-9 | section | `Creating Pull Request` header | ✅ Keep | Clear workflow section |
| 10-11 | action | `Pushing branch...` | ⚠️ Minor | Acceptable step indicator |
| 12-13 | success | `Branch pushed successfully` | ✅ Keep | Important outcome |
| 14-15 | action | `Creating pull request via gh CLI...` | ⚠️ Minor | Acceptable step indicator |
| 16-18 | success | `Pull request created` | ✅ Keep | Critical outcome |
| 19-23 | success/info | Success message and PR link | ✅ Keep | User needs PR URL |

#### Issues Found

1. **Implementation detail (Lines 3-4)**
   - **File:** `/src/claude_skills/claude_skills/sdd_pr/cli.py:60-61`
   - **Issue:** `printer.action(f"Loading spec: {args.spec_id}")` not needed
   - **Impact:** Low - brief and doesn't clutter output
   - **Classification:** Implementation detail but minimal impact

2. **Acceptable action indicators (Lines 10-11, 14-15)**
   - **File:** `/src/claude_skills/claude_skills/sdd_pr/pr_creation.py:127, 142`
   - **Issue:** `printer.action()` for branch pushing and PR creation
   - **Assessment:** These are acceptable because they indicate progress in a multi-step operation
   - **Reason:** Users appreciate knowing "action is happening" during potentially slow operations

3. **Structural clarity is good**
   - The separation into "Spec loaded" → "Creating Pull Request" workflow is clear
   - Each step has defined outcome (success message)
   - Follows standard CLI conventions (like git)

#### Issues in Error Paths

**Missing branch (Line 96-103 in cli.py):**
```
PR creation requires --approve flag

Workflow:
  1. Agent analyzes context and generates description
  2. Agent shows draft to user for approval
  3. Run with --approve flag to create PR
```

- **Assessment:** ✅ Good
- **Reason:** Explains expected workflow when preconditions not met
- **Appropriate:** Yes, this helps users understand the intended workflow

**Missing PR description (Line 116-118 in cli.py):**
```
PR body is required for creation
Agent should provide --description with AI-generated PR body
```

- **Assessment:** ✅ Good
- **Reason:** Clear error message with context
- **Appropriate:** Yes, tells user what's missing

#### Proposed Minimal Output

```
$ sdd create-pr my-spec-2025-11-09 --approve --title "Add OAuth 2.0" --description "[...]"

Creating Pull Request
  Branch: feat/oauth → main
  Status: Pushing...
  Status: Creating...

✓ Pull request created successfully!
  PR: https://github.com/owner/repo/pull/42 (#42)
```

**Reduction:** 23 lines → 7 lines = **70% reduction**

**But:** The action indicators ("Pushing...", "Creating...") are valuable for slow operations.

#### Root Cause

The output is well-designed because:
- It shows clear workflow steps (not internal operations)
- Each step has a success/error outcome
- PR creation can be slow (branch push, gh CLI call), so action indicators justify progress feedback
- The header separation is good visual design

The main opportunity for improvement is removing the "Loading spec" message which doesn't add value.

---

## Logger Output Analysis (pr_context.py)

The module uses Python logging for debug-level information:

```python
logger.info(f"Gathered PR context for {spec_id}:")
logger.info(f"  - {len(context['commits'])} commits")
logger.info(f"  - {len(context['journals'])} journal entries")
logger.info(f"  - {len(context['tasks'])} completed tasks")
logger.info(f"  - {len(context['phases'])} phases")
logger.info(f"  - Git diff size: {len(git_diff)} bytes")
```

**Assessment:** ✅ Appropriate

**Reason:**
- Logged at INFO level, not printed to user by default
- Only visible with `--verbose` flag
- Provides detailed context gathering metrics for debugging
- Should NOT be printed in normal mode

---

## Comparison with SKILL.md

The SKILL.md documentation shows draft output expectations:

```markdown
═══════════════════════════════════════════════════════════════════
Pull Request Draft
═══════════════════════════════════════════════════════════════════

Title: Add user authentication with OAuth 2.0

Branch: feat-auth → main

─────────────────────────────────────────────────────────────────────

## Summary
[PR body content...]
```

**Assessment:** ✅ Aligned

**Reason:**
- The SKILL.md shows comprehensive PR draft display
- The CLI output preparing this draft is appropriately light-weight
- The actual draft content display (show_pr_draft_and_wait) uses `print()` for markdown, which is correct

---

## Verbosity Issues Summary

### Issue 1: "Loading spec" Message

**Location:** `/src/claude_skills/claude_skills/sdd_pr/cli.py:60`

```python
printer.action(f"Loading spec: {args.spec_id}")
```

**Classification:** Implementation detail

**Severity:** Low - brief message, doesn't clutter significantly

**Recommendation:** Consider removing or moving to verbose-only output

**Reason to Keep:** Users might appreciate knowing the spec is being loaded (some specs are complex)

**Reason to Remove:** It's an internal operation detail, not an outcome

**Current Verdict:** Borderline - could go either way

---

### Issue 2: Context Summary Formatting

**Location:** `/src/claude_skills/claude_skills/sdd_pr/cli.py:83-88`

```python
printer.info("Context gathered:")
printer.detail(f"  Commits: {len(context['commits'])}")
printer.detail(f"  Tasks: {len(context['tasks'])}")
printer.detail(f"  Phases: {len(context['phases'])}")
printer.detail(f"  Journals: {len(context['journals'])}")
printer.detail(f"  Diff size: {len(context['git_diff'])} bytes")
```

**Classification:** Structural formatting (minor issue)

**Severity:** Low - information is useful, just formatted verbosely

**Recommendation:** Could consolidate into single line for draft-only mode

**Current Verdict:** Acceptable - detail provides clarity

---

## Design Patterns

The module demonstrates good output design patterns:

### ✅ Pattern 1: Outcome-Focused Messages

```python
printer.success("Branch pushed successfully")
printer.success(f"Pull request created: {pr_url}")
```

- Shows what changed, not how it changed
- Clear success indicators

### ✅ Pattern 2: Action Indicators for Long Operations

```python
printer.action(f"Pushing branch '{branch_name}' to remote...")
printer.action("Creating pull request via gh CLI...")
```

- Appropriate for operations that might take time
- Shows user that work is happening

### ✅ Pattern 3: Helpful Next Steps

```python
printer.info("To create this PR, run:")
printer.result("  sdd create-pr", f"{spec_id} --approve")
```

- Teaches users the workflow
- Provides clear commands to execute

### ✅ Pattern 4: Clear Error Context

```python
printer.error("GitHub CLI (gh) not found")
printer.info("")
printer.info("Install gh from: https://cli.github.com/")
```

- Explains what went wrong
- Provides solution path

---

## Recommendations

### Priority 1 (Quick Win)

**Move "Loading spec" to verbose-only output**

Current behavior: Always shown
Recommended: Only show with `--verbose` flag

Why: It's a pure implementation detail that doesn't help users in normal mode.

```python
# Current (cli.py:60-61)
printer.action(f"Loading spec: {args.spec_id}")
printer.info("")

# Recommended
if args.verbose:
    printer.action(f"Loading spec: {args.spec_id}")
    printer.info("")
```

Impact: Removes 2 lines from all outputs

---

### Priority 2 (Enhancement)

**Add progress indication for draft-only mode**

The draft-only mode could provide better feedback:

```python
# Consider adding for context gathering phase
printer.action("Gathering PR context...")
# ... gather context ...
printer.success(f"Context gathered: {len(context['commits'])} commits, {len(context['tasks'])} tasks")
```

Currently: Directly shows "Context gathered:" after successful load
Proposed: Show actual gathering action/progress

Impact: Makes the operation feel more intentional

---

## Detailed Output Breakdown

### Draft-Only Mode Summary

**Current line count:** ~11 lines (including blank lines)
**Necessary lines:** ~6 lines
**Reduction possible:** ~45%
**Verdict:** Minor improvements possible, not excessive

### Full Creation Mode Summary

**Current line count:** ~23 lines (success path)
**Necessary lines:** ~10 lines
**Reduction possible:** ~57%
**Assessment:** Well-designed given the multi-step workflow

The action indicators ("Pushing branch...", "Creating PR...") justify the extra lines because:
1. Operations can be slow (git push, gh CLI calls)
2. Users need to know something is happening
3. This matches conventions of other CLI tools (git, npm)

---

## Final Verdict: Assessment Summary

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Shows outcomes not process | ✅ Excellent | Implementation details minimal |
| User-facing clarity | ✅ Excellent | Clear workflow sections, good formatting |
| Verbosity appropriate to task | ✅ Good | Minor opportunities for improvement |
| Error messages helpful | ✅ Excellent | Clear explanations with next steps |
| Implementation details hidden | ⚠️ Good | "Loading spec" message could be removed |
| Follows CLI conventions | ✅ Excellent | Similar to git, gh CLI patterns |
| Documentation matches output | ✅ Good | SKILL.md examples are representative |

---

## Overall Assessment

### ✅ APPROPRIATE

The sdd-pr CLI module demonstrates excellent design with:

1. **Clear outcome focus** - Shows what changed, not how it changed
2. **Logical workflow structure** - Sections for different phases (Loading → Creating → Success)
3. **Helpful next steps** - Teaches users the workflow
4. **Good error handling** - Clear problems and solutions
5. **Justified action indicators** - Shows progress for potentially slow operations

### Minor Opportunities

- Remove "Loading spec" message (implementation detail)
- Consider more compact context summary in draft-only mode
- Could add subtle progress indication during context gathering

### Strengths Over Other Commands

Compared to other sdd-* commands, sdd-pr shows excellent restraint:
- No verbose enumeration of internal state
- No "Updating metadata", "Saving JSON" messages
- No redundant success indicators for sub-operations
- Clean separation between draft (agent-facing) and creation (user-facing) modes

The module respects the YAGNI principle by assuming users and agents know what they're doing and only reporting outcomes and clear workflow steps.

---

## Appendix: Code Locations

### Printer Calls Summary

| File | Location | Message | Type |
|------|----------|---------|------|
| cli.py | Line 43 | Header title | header |
| cli.py | Line 60 | Loading spec | action |
| cli.py | Line 76 | Spec loaded successfully | success |
| cli.py | Line 81-90 | Draft-only context info | info/detail |
| cli.py | Line 96-102 | Missing --approve error | error/info |
| cli.py | Line 116-117 | Missing description error | error/info |
| pr_creation.py | Line 46-72 | Draft display | header/info |
| pr_creation.py | Line 110-111 | Creation header | header/info |
| pr_creation.py | Line 127 | Pushing branch | action |
| pr_creation.py | Line 138 | Branch pushed success | success |
| pr_creation.py | Line 142 | Creating PR | action |
| pr_creation.py | Line 158-164 | PR created success | success/info |

### Total Printer Output

**Draft-only mode:** 11-12 lines
**Full creation mode (success):** 23-24 lines
**Full creation mode (errors):** 5-8 lines

---

## Related Commands

For comparative analysis, see:
- `/docs/research/sdd-update/cli-output-audit-sdd-update.md`
- `/docs/research/sdd-next/cli-output-audit-sdd-next.md`
- `/docs/research/sdd-plan/cli-output-audit-sdd-plan.md`

---

**End of Audit Report**
