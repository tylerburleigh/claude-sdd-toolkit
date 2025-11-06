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

### 1. Phase Review
**Scope:** Single phase within specification (typically 3-10 tasks)
**When to use:** Phase completion checkpoints, before moving to next phase
**Output:** Phase-specific fidelity report with per-task breakdown
**Best practice:** Use at phase boundaries to catch drift before starting next phase

### 2. Task Review
**Scope:** Individual task implementation (typically 1 file)
**When to use:** Critical task validation, complex implementation verification
**Output:** Task-specific compliance check with implementation comparison
**Best practice:** Use for high-risk tasks (auth, data handling, API contracts)

**Note:** For full spec reviews, run phase-by-phase reviews for better manageability and quality.

## Invocation

### For Automated Workflows

**Metadata in verification task:**
```json
{
  "verification_type": "fidelity",
  "agent": "sdd-fidelity-review",
  "scope": "phase",
  "target": "phase-1"
}
```

**Invocation from sdd-next:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review implementation fidelity for spec {spec-id}. [Details about scope/target]",
  description: "Review spec fidelity"
)
```

### For Direct User Requests

```
Skill(sdd-toolkit:sdd-fidelity-review)
```

Then provide the spec ID and review scope when prompted.

### Understanding the Naming

- `metadata.agent = "sdd-fidelity-review"` → What to execute (routing identifier)
- `Task(subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent")` → How to invoke (orchestration)
- `Skill(sdd-toolkit:sdd-fidelity-review)` → Direct skill invocation (user-facing)

## Required Information

### For Phase Review
- ✅ `spec_id` - Valid specification ID
- ✅ `phase_id` - Phase to review (e.g., "phase-1")

### For Task Review
- ✅ `spec_id` - Valid specification ID
- ✅ `task_id` - Valid task ID within the spec

## Spec Reading Best Practices

**CRITICAL: Never read spec files directly - use sdd CLI commands**

- ✅ **ALWAYS** use `sdd` commands to read spec files (e.g., `sdd task-info`, `sdd query-tasks`, `sdd get-journal`)
- ❌ **NEVER** use `Read()` tool on .json spec files - bypasses hooks and wastes context tokens (specs can be 50KB+)
- ❌ **NEVER** use Bash commands to read spec files (e.g., `cat`, `head`, `tail`, `grep`, `jq`)
- ❌ **NEVER** use Python code to parse spec JSON directly
- The `sdd` CLI provides efficient, structured access with proper parsing and validation

### Available sdd Commands for Fidelity Review

**Task-Level Review:**
- `sdd task-info {spec-id} {task-id} --json` - Get complete task details (requirements, files, metadata)
- `sdd get-task {spec-id} {task-id} --json` - Alternative task query interface
- `sdd check-deps {spec-id} {task-id} --json` - Check task dependencies status
- `sdd get-journal {spec-id} {task-id} --json` - Get journal entries for task

**Phase-Level Review:**
- `sdd list-phases {spec-id} --json` - List all phases with completion status
- `sdd query-tasks {spec-id} --parent {phase-id} --json` - Get all tasks in phase
- `sdd query-tasks {spec-id} --status completed --parent {phase-id} --json` - Get completed tasks only

**Spec-Level Review:**
- `sdd progress {spec-id} --json` - Overall spec progress summary
- `sdd query-tasks {spec-id} --status completed --json` - All completed tasks
- `sdd list-blockers {spec-id} --json` - Current blockers (useful for identifying incomplete work)

**Verification Review:**
- `sdd query-tasks {spec-id} --type verify --json` - Find all verification tasks

### Command Usage Pattern

Always use `--json` flag for structured output that's easy to parse:

```bash
# Get task details
sdd task-info user-auth-001 task-2-3 --json

# Returns structured JSON:
{
  "id": "task-2-3",
  "title": "Implement JWT middleware",
  "type": "task",
  "status": "completed",
  "files": ["src/middleware/auth.ts"],
  "acceptance_criteria": [...],
  "verification_steps": [...],
  ...
}
```

### Command Execution Best Practices

**CRITICAL: Run sdd commands individually, never in loops or chains**

**DO:**
- ✅ Run each `sdd` command as a separate Bash tool call
- ✅ Wait for each command to complete before running the next
- ✅ Parse JSON output from each command individually

**Example - Phase Review (Correct):**
```bash
# First call: Get phase info
sdd list-phases spec-id --json

# Second call: Get tasks in phase
sdd query-tasks spec-id --parent phase-3 --json

# Third call: Get specific task details
sdd task-info spec-id task-3-1 --json

# Fourth call: Get journal for that task
sdd get-journal spec-id task-3-1 --json

# Fifth call: Next task
sdd task-info spec-id task-3-2 --json
# ... and so on
```

**DON'T:**
- ❌ Use bash loops: `for task_id in task-3-1 task-3-2; do sdd get-journal ...; done`
- ❌ Chain commands: `sdd task-info && sdd get-journal`
- ❌ Combine with echo: `echo "===" && sdd get-journal`
- ❌ Use compound commands or semicolons

**Why?**
- Individual commands are easier to debug
- Better error handling per command
- Clearer permission boundaries
- More observable progress
- Follows SDD toolkit conventions

## Workflow

### Phase 1: Load Specification

**1. Validate inputs:**
   - Check required information is provided
   - Validate spec_id exists:
     ```bash
     sdd find-specs --verbose --json
     ```

**2. Load spec metadata based on review scope:**

**For Task Review:**
```bash
# Get complete task details
sdd task-info {spec-id} {task-id} --json

# Get journal entries to check for documented deviations
sdd get-journal {spec-id} {task-id} --json

# Check dependencies (useful for impact assessment)
sdd check-deps {spec-id} {task-id} --json
```

**For Phase Review:**
```bash
# Get phase metadata
sdd list-phases {spec-id} --json

# Get all completed tasks in the phase
sdd query-tasks {spec-id} --status completed --parent {phase-id} --json

# For each task, get detailed info:
sdd task-info {spec-id} {task-id} --json
sdd get-journal {spec-id} {task-id} --json
```

**3. Extract requirements from JSON output:**
   - Parse the JSON response from sdd commands
   - Extract from task-info: `acceptance_criteria`, `files`, `dependencies`, `verification_steps`
   - Extract from get-journal: Documented deviations and decisions
   - **NEVER read the spec file directly with Read() or cat**

### Phase 2: Analyze Implementation
1. **Identify files** from task metadata (extracted from `sdd task-info` JSON output)
2. **Read implementation code** using Read tool for each file
3. **Compare against spec requirements** from task-info output

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
- **To sdd-modify:** Apply review feedback systematically to update spec

## Applying Review Feedback Systematically

After completing a fidelity review, you can apply the identified spec improvements systematically using `Skill(sdd-toolkit:sdd-modify)`.

### Closed-Loop Workflow

The ideal workflow creates a feedback loop:

```
1. Implementation Complete
       ↓
2. Run Fidelity Review (this skill)
       ↓
3. Review Report Generated
       ↓
4. Parse Review Feedback → sdd-modify
       ↓
5. Apply Modifications → sdd-modify
       ↓
6. Validate Updated Spec
       ↓
7. Re-run Fidelity Review (confirm fixes)
```

This ensures the spec stays synchronized with implementation learnings.

### When to Update the Spec

**DO update the spec when:**
- ✅ Task descriptions are too vague and actual implementation is more specific
- ✅ Verification steps are missing for implemented functionality
- ✅ Implementation discovered better approaches (documented in journal)
- ✅ Acceptance criteria need clarification based on actual implementation
- ✅ Task metadata needs correction (actual_hours, categories, etc.)

**DON'T update the spec for:**
- ❌ Minor implementation details that don't affect requirements
- ❌ Code structure or styling choices
- ❌ Variable naming or internal refactoring
- ❌ Already-documented deviations (check journal first!)

### Systematic Application Process

#### Step 1: Generate Review Report

The fidelity review produces a detailed markdown report identifying:
- Vague task descriptions that need clarification
- Missing verification steps
- Spec/implementation mismatches

**Example review output:**
```markdown
## Issue 1: Task Description Too Vague (task-2-1)

**Current:** "Implement auth"

**Actual Implementation:** OAuth 2.0 with PKCE flow, JWT tokens, refresh rotation

**Recommendation:** Update task description to specify OAuth 2.0, PKCE, and token details
```

#### Step 2: Parse Review Feedback

Use `sdd parse-review` to extract structured modifications from the review report:

```bash
sdd parse-review {spec-id} --review reports/{spec-id}-fidelity-review.md --output suggestions.json
```

This automatically converts review recommendations into structured modification format:
```json
{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-2-1",
      "field": "description",
      "value": "Implement OAuth 2.0 authentication with PKCE flow, JWT access tokens (15min expiry), and refresh token rotation"
    }
  ]
}
```

#### Step 3: Preview Modifications

Before applying, preview what will change:

```bash
sdd apply-modifications {spec-id} --from suggestions.json --dry-run
```

This shows exactly what will be modified without making actual changes.

#### Step 4: Apply Modifications

Apply the modifications with automatic backup and validation:

```bash
sdd apply-modifications {spec-id} --from suggestions.json
```

Features:
- Automatic backup created before changes
- Transaction support with rollback on failure
- Validation runs after applying
- Clear error messages if issues detected

#### Step 5: Verify Results

Run fidelity review again to confirm issues are resolved:

```
Skill(sdd-toolkit:sdd-fidelity-review) "Re-review spec {spec-id} to confirm issues resolved"
```

### Using sdd-modify Subagent

For programmatic workflows, other agents can invoke sdd-modify-subagent directly:

```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Parse review report at reports/{spec-id}-fidelity-review.md and apply modifications to spec {spec-id}. Validate and report results.",
  description: "Apply fidelity review feedback"
)
```

This enables fully automated spec updates in CI/CD pipelines or automated workflows.

### Example: Complete Feedback Loop

```bash
# 1. Run fidelity review
Skill(sdd-toolkit:sdd-fidelity-review) "Review spec my-spec-001"
# → Generates: reports/my-spec-001-fidelity-review.md

# 2. Parse review feedback
sdd parse-review my-spec-001 --review reports/my-spec-001-fidelity-review.md
# → Generates: my-spec-001-suggestions.json

# 3. Preview modifications
sdd apply-modifications my-spec-001 --from my-spec-001-suggestions.json --dry-run
# → Shows what will change

# 4. Apply modifications
sdd apply-modifications my-spec-001 --from my-spec-001-suggestions.json
# → Updates spec with backup and validation

# 5. Re-review to confirm
Skill(sdd-toolkit:sdd-fidelity-review) "Re-review spec my-spec-001"
# → Should show: "Previous issues resolved: 5/5"
```

### Benefits of Systematic Application

**Compared to manual spec editing:**
- ✅ **Faster** - Automatic extraction from review reports
- ✅ **Safer** - Automatic backup, validation, rollback
- ✅ **Traceable** - Clear record of what changed and why
- ✅ **Reliable** - No manual transcription errors
- ✅ **Validated** - Spec structure checked after every change
- ✅ **Idempotent** - Safe to retry if failures occur

**Time savings:**
- Manual approach: ~30-45 minutes per review
- Systematic approach: ~5-10 minutes per review
- **Benefit:** 70-80% time reduction

### Integration Points

**From fidelity review to sdd-modify:**
```
Review finds vague descriptions → parse-review extracts fixes → sdd-modify applies
```

**From sdd-modify back to fidelity review:**
```
Modifications applied → validate updated spec → re-review confirms alignment
```

This creates a continuous improvement loop ensuring specs stay synchronized with implementation reality.

### See Also

- **Skill(sdd-toolkit:sdd-modify)** - Full documentation on spec modification workflows
- **skills/sdd-modify/examples/apply-review.md** - Complete walkthrough example
- **sdd parse-review --help** - CLI command reference
- **sdd apply-modifications --help** - CLI command reference

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

**Phase review:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review phase phase-1 in spec user-auth-001. Compare all completed tasks in Phase 1 (User Model & Authentication) against specification requirements.",
  description: "Phase 1 fidelity review"
)
```

**Task-specific review:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review task task-2-3 in spec user-auth-001. Compare implementation in src/middleware/auth.ts against task requirements for JWT authentication middleware.",
  description: "Review auth middleware task"
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
