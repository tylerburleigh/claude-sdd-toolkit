# Spec Modification & Fidelity Review Guide

This guide covers the workflow for modifying SDD specifications and reviewing implementation fidelity against those specs.

## Table of Contents

- [Overview](#overview)
- [When to Modify Specs](#when-to-modify-specs)
- [Modification Workflow](#modification-workflow)
- [Validation After Modification](#validation-after-modification)
- [Implementation Fidelity Review](#implementation-fidelity-review)
- [Best Practices](#best-practices)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)

---

## Overview

The SDD toolkit provides tools for both modifying specifications during implementation and reviewing how well the implementation adheres to the spec.

**Key Capabilities:**

- **sdd-validate**: Validate spec structure and auto-fix common issues
- **sdd fidelity-review**: Review implementation against specification using AI consultation
- **sdd-update**: Journal decisions and track modifications during implementation

**Philosophy**: Specs are living documents. As you implement, you'll discover details that weren't visible during planning. The toolkit helps you keep specs and implementation aligned.

---

## When to Modify Specs

### Valid Reasons to Modify

✅ **Discovery During Implementation**
- Found better approach while coding
- Discovered missing dependencies
- Identified edge cases not in original plan

✅ **Technical Constraints**
- API doesn't work as expected
- Library limitations
- Performance considerations

✅ **Requirement Clarifications**
- User provides additional details
- Stakeholder feedback
- Testing reveals issues

### What NOT to Modify

❌ **Don't Change Core Goals** - If the feature goal changes, create a new spec
❌ **Don't Skip Validation** - Always validate after manual edits
❌ **Don't Modify Completed Tasks** - Journal why completed work differs instead

---

## Modification Workflow

### Step 1: Make Modifications

You can modify specs in two ways:

#### Option A: Using sdd-update (Recommended)

Use the sdd-update subagent to make structured modifications:

**Add journal entry documenting a decision:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Add journal entry to task task-2-1 in spec-id. Entry: Decided to use async/await instead of callbacks based on User model API.",
  description: "Document implementation decision"
)
```

**Mark task as blocked:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Mark task task-3-1 as blocked in spec-id. Reason: Redis server not configured. Type: dependency.",
  description: "Document blocker"
)
```

**Update task status:**
```bash
# Mark in progress
sdd update-status spec-id task-id in_progress

# Mark completed (use sdd-update subagent with journal content instead)
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Complete task task-id in spec-id. Completion note: [what was accomplished]",
  description: "Mark task complete"
)
```

#### Option B: Manual JSON Editing

For structural changes, edit the spec JSON file directly:

```bash
# Open spec file in editor
nano specs/active/spec-id.json

# Make your changes
# - Modify task descriptions
# - Add verification steps
# - Adjust dependencies
# - Update metadata
```

**Common manual edits:**
- Adding verification steps to tasks
- Updating estimated_hours
- Modifying task descriptions
- Adding risk notes

### Step 2: Validate Modifications

**After ANY manual edit, validate the spec:**

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/spec-id.json. Check for structural errors, missing fields, and dependency issues.",
  description: "Validate spec after modifications"
)
```

The validator will:
- ✅ Check JSON structure
- ✅ Validate task dependencies
- ✅ Detect circular dependencies
- ✅ Verify required fields
- ✅ Offer auto-fixes for common issues

**Example validation output:**
```
⚠️  Validation Issues Found (3)

1. [ERROR] Circular dependency: task-2-3 → task-2-4 → task-2-3
2. [WARNING] Task task-3-1 missing estimated_hours
3. [WARNING] Phase phase-2 has no verification steps

Auto-fix available for issues 2-3. Run with --fix to apply.
```

### Step 3: Apply Auto-Fixes (If Available)

If validation found fixable issues:

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Auto-fix validation issues in specs/active/spec-id.json. Apply fixes for missing fields and validation warnings.",
  description: "Auto-fix spec issues"
)
```

Auto-fixes handle:
- Adding missing metadata fields
- Fixing task status inconsistencies
- Correcting timestamp formats
- Adding default values

### Step 4: Re-Validate

After auto-fixes:

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/spec-id.json again after auto-fixes.",
  description: "Re-validate spec"
)
```

**Goal**: Zero critical errors before continuing implementation.

---

## Validation After Modification

### Understanding Validation Severity

**CRITICAL** - Must fix before continuing
- Circular dependencies
- Invalid JSON structure
- Missing required fields
- Broken task references

**WARNING** - Should fix but non-blocking
- Missing estimated_hours
- No verification steps
- Missing risk notes
- Incomplete metadata

**INFO** - Nice to have
- Suggested improvements
- Best practice recommendations

### Validation Commands

**Basic validation:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/spec-id.json",
  description: "Validate spec"
)
```

**Preview auto-fixes before applying:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Preview auto-fixes for specs/active/spec-id.json without applying them.",
  description: "Preview spec fixes"
)
```

**Generate detailed validation report:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Generate detailed validation report for specs/active/spec-id.json. Save to specs/reports/spec-id-validation.md.",
  description: "Generate validation report"
)
```

---

## Implementation Fidelity Review

### What is Fidelity Review?

Fidelity review compares your implementation against the specification to identify:
- **Deviations**: Where implementation differs from spec
- **Missing features**: Spec requirements not implemented
- **Extra features**: Implementation beyond spec scope
- **Quality issues**: Code quality problems relative to spec expectations

### When to Run Fidelity Review

**During Implementation:**
- ✅ After completing each phase
- ✅ Before creating pull requests
- ✅ When implementation feels "off track"

**Before Completion:**
- ✅ Before marking spec as completed
- ✅ Before merging to main branch
- ✅ As part of QA process

### Basic Fidelity Review

**Review entire spec:**
```bash
sdd fidelity-review spec-id
```

**Review specific task:**
```bash
sdd fidelity-review spec-id --task task-2-1
```

**Review specific phase:**
```bash
sdd fidelity-review spec-id --phase phase-2
```

**Review specific files:**
```bash
sdd fidelity-review spec-id --files src/auth.ts src/middleware/auth.ts
```

### AI Consultation Options

By default, `fidelity-review` consults all available AI tools. You can customize this:

**List available AI tools:**
```bash
sdd list-review-tools
```

**Use specific tools:**
```bash
sdd fidelity-review spec-id --ai-tools gemini codex
```

**Skip AI consultation (just show review data):**
```bash
sdd fidelity-review spec-id --no-ai
```

**Specify model:**
```bash
sdd fidelity-review spec-id --model gpt-4
```

### Review Options

**Exclude tests from review:**
```bash
sdd fidelity-review spec-id --no-tests
```

**Change base branch for diff:**
```bash
sdd fidelity-review spec-id --base-branch develop
```

**Set consensus threshold:**
```bash
# Require 3 models to agree for consensus (default: 2)
sdd fidelity-review spec-id --consensus-threshold 3
```

### Output Formats

**Text output (default):**
```bash
sdd fidelity-review spec-id
```

**JSON output:**
```bash
sdd fidelity-review spec-id --format json
```

**Markdown output:**
```bash
sdd fidelity-review spec-id --format markdown
```

**Save to file:**
```bash
sdd fidelity-review spec-id --output review-report.md --format markdown
```

### Understanding Review Results

**Consensus Verdict:**
- **PASS**: Implementation matches spec (consensus across AI tools)
- **FAIL**: Significant deviations detected (consensus)
- **PARTIAL**: Mixed results, some issues detected
- **NEEDS_REVIEW**: Unclear, requires human review

**Agreement Rate:**
- Percentage of AI tools that agree on the verdict
- Higher is better (80%+ is good consensus)

**Issues Identified:**
- Categorized by severity: CRITICAL, WARNING, INFO
- Shows only issues where multiple AI tools agree

**Recommendations:**
- Actionable suggestions for bringing implementation in line with spec
- Prioritized by importance

### Example Review Output

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
Task task-2-1 spec requires token expiration, but implementation doesn't check exp claim

[WARNING] Test coverage below spec requirements
Spec requires 80% coverage, actual coverage is 65%

--------------------------------------------------------------------------------
RECOMMENDATIONS:
--------------------------------------------------------------------------------
- Add JWT expiration validation in src/middleware/auth.ts
- Increase test coverage for edge cases in tests/auth.spec.ts
- Consider adding integration tests for token refresh flow
```

---

## Best Practices

### During Implementation

1. **Journal Decisions**
   - Use sdd-update to document why you deviated from plan
   - Include what alternatives you considered
   - Note any new risks discovered

2. **Update Status Promptly**
   - Mark tasks in_progress when starting
   - Mark completed immediately when done
   - Mark blocked as soon as you hit a blocker

3. **Validate After Manual Edits**
   - Always run validation after editing JSON
   - Fix critical errors before continuing
   - Address warnings when feasible

### Modification Guidelines

**DO:**
- ✅ Document why modifications are needed
- ✅ Update verification steps if implementation approach changes
- ✅ Adjust dependencies when task scope changes
- ✅ Keep modifications focused and minimal

**DON'T:**
- ❌ Modify completed tasks (journal instead)
- ❌ Skip validation after changes
- ❌ Change core feature goals (create new spec)
- ❌ Remove verification steps without good reason

### Fidelity Review Guidelines

**DO:**
- ✅ Run review before major milestones
- ✅ Address CRITICAL issues immediately
- ✅ Review at phase boundaries
- ✅ Save review reports for documentation

**DON'T:**
- ❌ Ignore consensus issues
- ❌ Skip review before PR creation
- ❌ Trust single AI tool results (use consensus)
- ❌ Continue with FAIL verdict without addressing issues

---

## Common Scenarios

### Scenario 1: Discovered Better Approach Mid-Implementation

**Situation**: While implementing task-2-1, you realize async/await is better than callbacks.

**Steps:**
1. Journal the decision:
   ```
   Task(
     subagent_type: "sdd-toolkit:sdd-update-subagent",
     prompt: "Add journal entry to task-2-1 in spec-id. Entry: Switching from callbacks to async/await. Reason: User model API uses promises, async/await provides better error handling and readability.",
     description: "Document approach change"
   )
   ```

2. Update task description (manual edit):
   - Edit specs/active/spec-id.json
   - Update task-2-1 description to reflect async/await approach

3. Validate changes:
   ```
   Task(
     subagent_type: "sdd-toolkit:sdd-validate-subagent",
     prompt: "Validate specs/active/spec-id.json after updating task-2-1",
     description: "Validate spec"
   )
   ```

4. Continue implementation

### Scenario 2: Found Circular Dependency

**Situation**: Validation reports circular dependency: task-3-1 → task-3-2 → task-3-1.

**Steps:**
1. Analyze the dependency chain:
   ```bash
   sdd find-circular-deps spec-id
   ```

2. Manual fix - Edit JSON to break the cycle:
   - Option A: Remove one dependency
   - Option B: Merge tasks if they're too coupled
   - Option C: Introduce intermediate task

3. Validate fix:
   ```
   Task(
     subagent_type: "sdd-toolkit:sdd-validate-subagent",
     prompt: "Validate specs/active/spec-id.json after fixing circular dependency",
     description: "Validate spec"
   )
   ```

### Scenario 3: Phase Complete, Need Fidelity Check

**Situation**: Completed all tasks in phase-2, ready to move to phase-3.

**Steps:**
1. Run fidelity review for the phase:
   ```bash
   sdd fidelity-review spec-id --phase phase-2 --format markdown --output phase-2-review.md
   ```

2. Review the report:
   - Check consensus verdict
   - Identify critical issues
   - Review recommendations

3. Address issues if verdict is FAIL or PARTIAL:
   - Fix critical deviations
   - Document why some differences exist (if intentional)
   - Re-run review

4. Once verdict is PASS, proceed to phase-3:
   - Use /sdd-begin to continue with next phase

### Scenario 4: Implementation Deviated from Spec

**Situation**: Fidelity review shows implementation has extra features not in spec.

**Steps:**
1. Review the issues identified
2. Decide on approach:

   **Option A: Update spec to match implementation** (if extra features are valuable)
   - Edit spec JSON to add tasks for the extra features
   - Mark those tasks as completed
   - Add journal entries explaining why they were added
   - Validate

   **Option B: Remove extra features** (if they're scope creep)
   - Revert the extra implementation
   - Re-run fidelity review

   **Option C: Document as intentional deviation**
   - Journal why the deviation is acceptable
   - Include in PR description
   - Keep for future spec revision

---

## Troubleshooting

### Validation Errors

**Error: "Circular dependency detected"**
- **Cause**: Tasks depend on each other in a loop
- **Fix**: Use `sdd find-circular-deps spec-id` to identify the cycle, then manually break it

**Error: "Invalid JSON structure"**
- **Cause**: Syntax error in JSON file
- **Fix**: Use JSON validator or run spec through `jq` to find the syntax error

**Error: "Missing required field"**
- **Cause**: Task or phase missing mandatory fields
- **Fix**: Use auto-fix or manually add the missing fields

### Fidelity Review Issues

**Issue: "No AI tools available"**
- **Cause**: No AI consultation tools (gemini, codex, cursor-agent) installed
- **Fix**: Install at least one AI tool, or use `--no-ai` to see raw review data

**Issue: "Timeout waiting for AI response"**
- **Cause**: AI tool took too long to respond
- **Fix**: Increase timeout with `--timeout 300` or exclude slow tools with `--ai-tools`

**Issue: "No consensus reached"**
- **Cause**: AI tools disagree on verdict
- **Fix**: Review individual model responses with `--verbose`, use human judgment

### Modification Issues

**Issue: "Changes not reflected after edit"**
- **Cause**: May have edited wrong file or changes not saved
- **Fix**: Verify you're editing the correct spec file in specs/active/, ensure file is saved

**Issue: "Auto-fix didn't work"**
- **Cause**: Issue requires manual intervention
- **Fix**: Read the validation error message and fix manually

**Issue: "Lost custom modifications"**
- **Cause**: Auto-fix or regeneration overwrote custom changes
- **Fix**: Use version control (git) to track spec changes, restore from git history

---

## Additional Resources

**Related Documentation:**
- [SDD Toolkit Best Practices](./BEST_PRACTICES.md) - General SDD workflow guidance
- [Architecture](./ARCHITECTURE.md) - Technical architecture details
- [Contracts](./CONTRACTS.md) - API contracts and interfaces

**Skills:**
- `Skill(sdd-toolkit:sdd-plan)` - Create new specifications
- `Skill(sdd-toolkit:sdd-next)` - Find next tasks and create execution plans
- `Skill(sdd-toolkit:sdd-update)` - Update task status and journal decisions
- `Skill(sdd-toolkit:sdd-validate)` - Validate spec structure

**Commands:**
- `sdd fidelity-review --help` - Full command documentation
- `sdd list-review-tools` - Check available AI tools
- `sdd find-circular-deps` - Detect dependency cycles
- `sdd validate-spec` - Quick validation check

---

## Summary

**Modification Workflow:**
1. Make changes (via sdd-update or manual edit)
2. Validate spec structure
3. Apply auto-fixes if available
4. Re-validate until clean

**Fidelity Review Workflow:**
1. Complete implementation milestone (task/phase/spec)
2. Run `sdd fidelity-review`
3. Review consensus verdict and issues
4. Address critical deviations
5. Re-run review if needed
6. Proceed when verdict is PASS

**Remember**: Specs are living documents. It's normal and expected to modify them during implementation. The key is to validate changes and ensure implementation stays aligned with the spec's intent.
