---
name: sdd-fidelity-review
description: Review implementation fidelity against specifications by comparing actual code to spec requirements. Identifies deviations, assesses impact, and generates compliance reports for tasks, phases, or entire specs.
---

# Implementation Fidelity Review Skill

## Overview

The `sdd-fidelity-review` skill compares actual implementation against SDD specification requirements to ensure fidelity between plan and code. It identifies deviations, assesses their impact, and generates detailed compliance reports.

## Skill Family

This skill is part of the **Spec-Driven Development** quality assurance family:
- **Skill(sdd-toolkit:sdd-plan)** - Creates specifications
- **Skill(sdd-toolkit:sdd-next)** - Finds next tasks and creates execution plans
- **Implementation** - Code is written
- **sdd-update-subagent** - Updates progress
- **Skill(sdd-toolkit:sdd-fidelity-review)** (this skill) - Reviews implementation fidelity
- **Skill(sdd-toolkit:run-tests)** - Runs tests

## When to Use This Skill

Use this skill when you need to:
- Verify implementation matches specification requirements
- Identify deviations between plan and actual code
- Assess task or phase completion accuracy
- Review pull requests for spec compliance
- Audit completed work for fidelity
- Document implementation variations

**Do NOT use for:**
- Creating specifications (use sdd-plan)
- Finding next tasks (use sdd-next)
- Updating task status (use sdd-update)
- Running tests (use run-tests)

## Review Types

### 1. Full Spec Review
**Scope:** Entire specification across all phases
**When to use:** Post-completion audits, major milestones
**Output:** Comprehensive fidelity report

### 2. Phase Review
**Scope:** Single phase within specification
**When to use:** Phase completion checkpoints
**Output:** Phase-specific fidelity report

### 3. Task Review
**Scope:** Individual task implementation
**When to use:** Task completion verification
**Output:** Task-specific compliance check

### 4. File Review
**Scope:** Specific files against spec
**When to use:** Targeted code review, PR reviews
**Output:** File-level fidelity analysis

### 5. Deviation Analysis
**Scope:** Documented deviations from plan
**When to use:** Investigating implementation changes
**Output:** Deviation impact assessment

## Invocation

**Using Subagent:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review implementation fidelity for spec {spec-id}. [Details about what to review]",
  description: "Review spec fidelity"
)
```

**Using Skill:**
```
Skill(sdd-toolkit:sdd-fidelity-review)
```

Then provide the spec ID and review scope when prompted.

## Required Information

### For Full Review
- ✅ `spec_id` - Valid specification ID
- Optional: `scope` - Review scope (full/phase/task/files)

### For Task Review
- ✅ `spec_id` - Valid specification ID
- ✅ `task_id` - Valid task ID within the spec

### For File Review
- ✅ `spec_id` - Valid specification ID
- ✅ `files` - List of file paths to review

### For Deviation Analysis
- ✅ `spec_id` - Valid specification ID
- ✅ `deviation_description` - What was implemented differently
- Optional: `task_id` - Task context for the deviation

## Workflow

### Phase 1: Load Specification
1. Validate inputs (spec_id, task_id, etc.)
2. Load spec data using SDD CLI
3. Extract requirements from spec

### Phase 2: Analyze Implementation
1. Identify files from task metadata
2. Read implementation code
3. Compare against spec requirements

### Phase 3: Identify Deviations
1. Categorize findings:
   - ✅ Exact match
   - ⚠️ Minor deviation
   - ❌ Major deviation
   - 🚫 Missing functionality
2. Assess impact on other tasks
3. Document deviations

### Phase 4: Generate Report
Create structured report with:
- Summary and fidelity score
- Detailed findings per task
- Recommendations
- Journal analysis

### Phase 5: Update Spec (if needed)
- Recommend journal entries for undocumented deviations
- Suggest spec updates if needed
- Flag items for follow-up

## Report Structure

```markdown
# Implementation Fidelity Review

**Spec:** {spec-title} ({spec-id})
**Scope:** {review-scope}
**Date:** {review-date}

## Summary

- **Tasks Reviewed:** {count}
- **Files Analyzed:** {count}
- **Overall Fidelity:** {percentage}%
- **Deviations Found:** {count}

## Fidelity Score

- ✅ Exact Matches: {count} tasks
- ⚠️ Minor Deviations: {count} tasks
- ❌ Major Deviations: {count} tasks
- 🚫 Missing Functionality: {count} items

## Detailed Findings

### Task: {task-id} - {task-title}

**Specified:**
- {requirement-1}
- {requirement-2}

**Implemented:**
- {actual-1}
- {actual-2}

**Assessment:** {exact-match|minor-deviation|major-deviation}

**Deviations:**
1. {deviation-description}
   - **Impact:** {low|medium|high}
   - **Recommendation:** {action}

## Recommendations

1. {recommendation-1}
2. {recommendation-2}

## Journal Analysis

**Documented Deviations:**
- {task-id}: {deviation-summary} (from journal on {date})

**Undocumented Deviations:**
- {task-id}: {deviation-summary} (should be journaled)
```

## Integration with SDD Workflow

### When to Invoke

1. **After task completion** - Optional verification step
2. **Phase completion** - Review entire phase before next phase
3. **Spec completion** - Final audit before PR creation
4. **PR review** - Automated or manual PR compliance checks

### Handoff to Other Skills

- **To sdd-update:** Document deviations in journal
- **From sdd-next:** Triggered during verification tasks
- **To run-tests:** Verify functional correctness after finding deviations

## Fidelity Assessment

### Exact Match (✅)
Implementation precisely matches specification requirements. No deviations detected.

### Minor Deviation (⚠️)
Small differences from spec with no functional impact:
- Different variable names (but consistent with codebase style)
- Minor refactoring for code quality
- Improved error messages
- Additional logging or comments

### Major Deviation (❌)
Significant differences affecting functionality or architecture:
- Different API signatures than specified
- Missing required features
- Different data structures
- Changed control flow or logic

### Missing Functionality (🚫)
Specified features not implemented:
- Required functions missing
- Incomplete implementation
- Skipped acceptance criteria

## Best Practices

### DO
✅ Compare implementation against actual spec requirements
✅ Check journal entries for documented deviations
✅ Assess impact of deviations on other tasks
✅ Provide actionable recommendations
✅ Use spec verification steps as checklist
✅ Consider functional equivalence vs literal matching

### DON'T
❌ Penalize improvements over original plan
❌ Flag minor stylistic differences
❌ Ignore context from journal entries
❌ Review code quality (separate concern)
❌ Make assumptions about missing requirements
❌ Skip validation of required information

## Example Invocations

**Full spec review:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review implementation fidelity for spec sdd-next-enhancement-001. Perform full review across all completed phases.",
  description: "Full fidelity review"
)
```

**Task-specific review:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review task-2-3 in spec user-auth-001. Compare implementation in src/middleware/auth.ts against specification requirements.",
  description: "Review auth middleware task"
)
```

**Deviation analysis:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Analyze deviation in spec api-refactor-001 task-1-2. Deviation: Used dependency injection instead of singleton pattern as specified. Assess impact and document.",
  description: "Analyze DI deviation"
)
```

## Error Handling

### Missing Required Information
If invoked without required information, the skill returns a structured error indicating which fields are missing.

### Spec Not Found
If the specified spec file doesn't exist, the skill reports which directories were searched and suggests verification steps.

### No Implementation Found
If the specified files don't exist, the skill warns that the task appears incomplete or the file paths are incorrect.

## Success Criteria

A successful fidelity review:
- ✅ Compares all specified requirements against implementation
- ✅ Identifies and categorizes deviations accurately
- ✅ Assesses impact of deviations
- ✅ Provides actionable recommendations
- ✅ Generates clear, structured report
- ✅ Documents findings for future reference

---

*For creating specifications, use Skill(sdd-toolkit:sdd-plan). For task progress updates, use sdd-update-subagent. For running tests, use run-tests-subagent.*
