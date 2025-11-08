---
name: sdd-next
description: Task preparation skill for spec-driven workflows. Reads specifications, identifies next actionable tasks, gathers context, and creates detailed execution plans. Use when ready to implement a task from an existing spec - bridges the gap between planning and coding.
---

# Spec-Driven Development: Next Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-toolkit:sdd-plan)** - Creates specifications and task hierarchies
- **Skill(sdd-toolkit:sdd-next)** (this skill) - Identifies next tasks and creates execution plans
- **sdd-update-subagent** - Updates task and spec progress

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│            Spec-Driven Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌─────────┐│
│  │   PLAN   │───>│   NEXT   │───>│IMPLEMENTATION│───>│ UPDATE  ││
│  └──────────┘    └──────────┘    └─────────────┘    └─────────┘│
│       │               │                  │                │      │
│   Creates JSON    Finds next        Writes actual    Updates     │
│   spec file       actionable        code based on    status &    │
│                   task, creates     execution plan   journals    │
│                   execution plan                                  │
│       │               │                  │                │      │
│       └───────────────┴──────────────────┴────────────────┘      │
│                              │                                    │
│                         [Cycle repeats]                          │
│                                                                   │
│  Note: Implementation can be done by human developers,           │
│        Claude with coding tools, or other AI assistants          │
└─────────────────────────────────────────────────────────────────┘
```

**Your Role (NEXT)**: Identify the next actionable task from an existing spec and create a detailed execution plan for implementation.

## Core Philosophy

**Context-Driven Execution**: Every task implementation should begin with full understanding of the spec's intent, the task's role in the larger plan, and all relevant codebase context. This prevents scope creep, ensures alignment with the specification, and produces implementation that integrates cleanly.

**Key Benefits:**
- Identifies the next actionable task automatically
- Gathers all relevant context before implementation
- Creates focused execution plans for specific tasks
- Maintains alignment with overall specification
- Prevents working on wrong tasks or blocked tasks
- Provides clear handoff between spec and code

## Important Notes

**Always Use Absolute Paths:**
- After Phase 1.1/1.2, all paths should be absolute
- Never use relative paths like `specs/active/file.json` - they fail when run from different directories
- Enhanced discovery (Phase 1.1) checks multiple common locations automatically

**JSON Is Source of Truth:**
- Specs live in `specs/<status>/<spec-id>.json`
- All task metadata, dependencies, verification steps, and risk notes are stored in the JSON hierarchy
- Query specs via `sdd` commands; avoid ad-hoc parsing

**Reading Specifications (CRITICAL):**
- ✅ **ALWAYS** use `sdd` commands to read spec files (e.g., `sdd prepare-task`, `sdd task-info`, `sdd context`)
- ❌ **NEVER** use `Read()` tool on .json spec files - bypasses hooks and wastes context tokens (specs can be 50KB+)
- ❌ **NEVER** use Bash commands to read spec files (e.g., `cat`, `head`, `tail`, `grep`, `jq`)
- ❌ **NEVER** use command chaining to access specs (e.g., `sdd --version && cat specs/active/spec.json`)
- The `sdd` CLI provides efficient, structured access with proper parsing and validation
- Spec files are large and reading them directly wastes valuable context window space

**Fast Context Checklist (daily driver):**
1. `sdd prepare-task {spec-id}` (auto-discovers specs, selects the next task, and includes dependency status)
2. If you need more detail, run `sdd task-info {spec-id} {task-id}` and `sdd check-deps {spec-id} {task-id}`
3. Review task metadata, then open the mentioned source/test files; helpers like `sdd find-related-files {path}` and `sdd find-tests --source-file {path}` keep this fast
4. If `prepare-task` or `check-deps` warns about blockers, run `sdd list-blockers {spec-id}`
5. Capture verification steps or linked docs noted in the spec before planning changes

**Command Formatting:**
- **Always use the wrapper script `sdd [command]`**
- **Always use single-line bash commands** (no backslash continuations)
- This ensures compatibility with permission rules and automation
- Long commands are acceptable - parseability matters more than formatting
- **Avoid compound commands with &&** when possible - use separate command invocations instead
- **Never use inline environment variable assignment with &&** - this adds unnecessary complexity

## Output Formatting

**When presenting execution plans and task information:**

**DO:**
- Use clear markdown headers (## or **Header:**)
- Put each item on its own line - never cram multiple items together
- Use blank lines to separate sections
- Use proper markdown lists

**DO NOT:**
- Cram multiple fields on one line (e.g., "Type: Verification TaskPurpose: Test...")
- Create dense text blocks with odd line breaks
- Use inconsistent formatting

### Completion Report Format Template

**CRITICAL: When presenting task completion reports, use this exact structure with proper line breaks:**

```markdown
## Task Completed Successfully! ✓

**Task ID:** task-1-1
**Title:** Create sdd_render_skill directory structure

### What Was Accomplished

✅ Created skills/sdd-render/ directory with proper naming conventions (hyphens)

✅ Created placeholder SKILL.md (2,807 bytes) with foundational structure

✅ Verified Python module (sdd_render) is properly structured and imports successfully

✅ Confirmed naming conventions match established patterns across the toolkit

✅ Validated structure against existing skills (sdd-next pattern)

### Files Created/Modified

**New Files:**
- skills/sdd-render/SKILL.md - Claude Code skill definition (placeholder)

**Verified Existing:**
- src/claude_skills/claude_skills/sdd_render/__init__.py
- src/claude_skills/claude_skills/sdd_render/cli.py
- src/claude_skills/claude_skills/sdd_render/renderer.py

### Next Steps

This task unblocks three dependent tasks:

1. **task-1-2:** Create SKILL.md for sdd-render (flesh out the full skill documentation)
2. **task-1-3:** Implement skill_main.py entry point (clarify requirements)
3. **task-1-4:** Register skill in toolkit (integration work)

The foundational directory structure is now in place and ready for these subsequent tasks to build upon.

### Progress Update

**Spec:** AI-Enhanced Spec Rendering Skill (ai-enhanced-rendering-2025-10-28-001)

**Phase 1 Progress:** 1/6 tasks completed (17%)

**Overall Progress:** 1/49 tasks completed (2%)
```

**Key Formatting Rules:**
1. **Blank line after each section header**
2. **Blank line between each accomplishment item** (✅ items)
3. **Blank line before and after subsections** (Files Created/Modified, Next Steps, etc.)
4. **Each field on its own line** - NEVER combine fields like "Type: X Purpose: Y"
5. **Use proper markdown headers** (## for main title, ### for subsections, ** for emphasis)

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (prepare-task, verify-tools, task-info, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd` CLI wrapper commands (e.g., `sdd prepare-task`, `sdd verify-tools`, `sdd task-info`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python sdd_next.py`, `bash python3 scripts/next_task.py`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## Context Checking Pattern

**⚠️ CRITICAL: Before checking context usage, you MUST generate a session marker first.**

The `sdd context` command requires a session marker to locate the transcript. This is a **two-step process** that must be executed sequentially.

**Correct Pattern (ALWAYS use this):**

```bash
# Step 1: Generate session marker (REQUIRED FIRST)
sdd session-marker

# Step 2: Check context using the marker from step 1
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**Output Format:**

The command returns simplified JSON with just the percentage as a whole number:
```json
{"context_percentage_used": 78}
```

**CRITICAL REQUIREMENTS:**

1. ✅ **Run as TWO SEPARATE commands** - Use separate Bash tool calls
2. ✅ **Run SEQUENTIALLY, not in parallel** - Step 2 depends on step 1 being logged
3. ❌ **NEVER combine with && or $()** - The marker must be logged to transcript before use
4. ❌ **NEVER run in parallel** - Step 2 will fail if step 1 hasn't been logged yet

**Why Sequential Execution Matters:**

The session marker from step 1 must be written to the conversation transcript before step 2 can search for it. Running them in parallel or combining them with `&&` or `$()` breaks this requirement and causes failures.

**Example of WRONG approaches:**

```bash
# ❌ WRONG - Combined with &&
sdd session-marker && sdd context --session-marker "..." --json

# ❌ WRONG - Combined with $()
sdd context --session-marker "$(sdd session-marker)" --json

# ❌ WRONG - Run in parallel (both in same message)
# Bash call 1: sdd session-marker
# Bash call 2: sdd context --session-marker "..." --json
```

**When to Check Context:**

- **Autonomous mode**: After each task completion (REQUIRED to avoid hitting limits)
- **Single-task mode**: After task completion (recommended)
- **Session start**: Before starting intensive work (optional)
- **Before continuing**: When resuming after high context usage (recommended)

**Context Thresholds:**

- **< 75%**: Safe to continue
- **≥ 75%**: Stop and prompt user (use AskUserQuestion)
- **≥ 90%**: Strongly recommend stopping

See [Autonomous Workflow](#autonomous-workflow-phase-completion-mode) and [Post-Implementation](#post-implementation) sections for usage in workflows.

## Automated Workflow (Skill Invocation)

When this skill is invoked automatically (via `Skill(sdd-toolkit:sdd-next)`), use these simplified commands:

**Step 1: Verify tools**
```bash
sdd verify-tools
```

**Step 2: Prepare task (discovers specs automatically)**
```bash
sdd prepare-task {spec-id}
```

**If prepare-task fails:**
- **Specs directory not found**: Specify path explicitly with `--path /absolute/path/to/specs`
- **Spec file not found**: Verify {spec-id} is correct, check `specs/active/` directory
- **No actionable tasks**: All tasks may be completed or blocked (use `list-blockers` to diagnose)
- **Multiple specs found**: If you don't know the {spec-id}, use manual workflow (Phase 1.1)
- **Circular dependencies detected**: Use `find-circular-deps {spec-id}` to diagnose, may need spec revision

The `prepare-task` command handles spec discovery, finds the next actionable task, gathers dependencies, and extracts task details - all in one command. This is the recommended approach for automated workflows.

**Automatic Enhancements:**

The `prepare-task` command includes two automatic enhancements:

1. **Spec Validation**: Validates the JSON spec file before proceeding.

   **Critical errors:** If critical errors are found, stops and shows clear error messages with suggested fixes. You must address critical errors before proceeding using the sdd-validate subagent.

   **Non-critical warnings:** Displayed as informational text and automatically continues. The workflow is not blocked by non-critical warnings.

   **Example output:**
   ```
   ⚠️  Spec Validation Warnings (3 non-critical)

   1. Task task-2-3 missing estimated_hours metadata
   2. Phase phase-2 has no verification steps
   3. Circular dependency detected in task-4-5 (low impact)

   These warnings don't prevent task preparation but may affect tracking accuracy.
   You can fix them later using the sdd-validate subagent (see Manual Spec Validation section).

   Continuing with task preparation...
   ```

   User can interrupt and ask to fix warnings if desired, or address them later.

2. **Codebase Context Gathering**: If codebase documentation has been generated, automatically gathers task-relevant context (via `Skill(sdd-toolkit:doc-query)`) including:
   - Relevant files from the codebase
   - Similar implementations to reference
   - Dependency information

   This context appears in the execution plan output as a "Codebase Context" section.

**If you need to specify a custom specs path:**
```bash
sdd prepare-task {spec-id} --path /absolute/path/to/specs
```

### Manual Spec Validation (Optional)

While `prepare-task` includes automatic spec validation, you may want to validate a spec independently before task preparation. This is useful for:

- **Pre-validation**: Checking spec quality before beginning implementation
- **Debugging**: Diagnosing spec issues when `prepare-task` fails
- **Quality assurance**: Ensuring spec meets standards before team handoff
- **Iterative refinement**: Validating after manual spec edits

**Invoke the sdd-validate subagent:**

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/{spec-id}.json. Check for structural errors, missing fields, and dependency issues.",
  description: "Validate spec structure"
)
```

**Common validation scenarios:**

**1. Basic validation check:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/user-auth-001.json. Check for structural errors, missing fields, and dependency issues.",
  description: "Validate spec file"
)
```

**2. Preview auto-fixes before applying:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Preview auto-fixes for specs/active/user-auth-001.json. Show what would be changed without applying.",
  description: "Preview spec fixes"
)
```

**3. Generate detailed validation report:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Generate a detailed validation report for specs/active/user-auth-001.json. Save the report to specs/reports/user-auth-001.md.",
  description: "Generate validation report"
)
```

**When to use manual validation vs automatic:**

- **Automatic (via prepare-task)**: Default for normal task preparation workflow. Validates on-the-fly and reports issues.
- **Manual (via subagent)**: When you need validation independent of task preparation, want detailed reports, or are debugging spec issues.

For complete validation workflow details, see the [sdd-plan skill validation documentation](../sdd-plan/SKILL.md#validation-workflow-using-sdd-validate-subagent).

## Quick Start: Automated vs Manual Workflow

**Choose your workflow based on your needs:**

### ✅ Use Automated Workflow (Recommended for Most Cases)

**When to use:**
- Standard task preparation and execution planning
- You know the spec ID you want to work on
- You want the fastest path to creating an execution plan
- Typical development workflow

**How to use:**
```bash
# 1. Verify tools available
sdd verify-tools

# 2. Prepare task automatically (handles everything)
sdd prepare-task {spec-id}

# This single command:
# - Discovers specs directory
# - Finds next actionable task
# - Gathers dependencies
# - Extracts task details
# - Returns everything needed for execution plan
```

**Optional: Validate spec before task preparation**

For critical projects or when spec quality is uncertain, validate the spec first using the sdd-validate subagent:

```
# Validate spec before preparing tasks
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/{spec-id}.json. Check for structural errors, missing fields, and dependency issues.",
  description: "Validate spec before task prep"
)

# Then prepare task if validation passes
sdd prepare-task {spec-id}
```

**When to validate first:**
- Working with newly created or manually edited specs
- Critical production implementations
- Specs with complex dependency chains
- After major spec modifications
- When prepare-task returns unexpected results

For more validation options, see [Manual Spec Validation](#manual-spec-validation-optional) section.

**Skip to:** Phase 4 (Execution Plan Creation) after `prepare-task` succeeds

**Note:** When `prepare-task` returns successfully, you do **not** need to call `next-task`, `task-info`, or `check-deps` separately unless you are troubleshooting or drilling into a different task. The JSON payload already includes the recommended task, its metadata, and dependency status.

**If prepare-task fails:**
- Check the error message for specific guidance
- Verify spec file exists and is valid
- Fall back to manual workflow if needed (see below)

---

### Decision Flow Chart

```
┌─────────────────────────────────────────┐
│ Do you know the {spec-id} to work on?  │
└────────────┬────────────────────────────┘
             │
        ┌────▼────┐
        │   YES   │──────────> Use Automated: sdd prepare-task {spec-id}
        └─────────┘            If succeeds: Skip to Phase 4
                               If fails: See troubleshooting or use manual

        ┌────▼────┐
        │   NO    │──────────> Use Manual: Start at Phase 1
        └─────────┘            Discover specs, review options, select spec
```

**Most users should start with automated workflow** and only use manual workflow when needed.

---

## Autonomous Workflow (Phase Completion Mode)

**When to use this workflow:**
- User explicitly requests "autonomous mode" during session setup (via /sdd-begin)
- The invocation prompt mentions "autonomous mode" or "complete all tasks in current phase"
- User wants to complete multiple tasks within a phase without stopping for approval on each one

**Key Characteristics:**
- **Phase-scoped execution**: Completes all tasks within the current phase, does not cross phase boundaries
- **Context-aware**: Checks context usage after each task, stops if ≥75%
- **Defensive stops**: Stops for blocked tasks and plan deviations (requires user approval)
- **No plan approval**: Creates execution plans internally without user approval for each task

### Autonomous Mode Detection

At the beginning of the workflow, check if the invocation prompt mentions autonomous mode:

**Detection keywords:**
- "autonomous mode"
- "complete all tasks in current phase"
- "complete entire phase"
- "phase completion mode"

If detected, execute the autonomous workflow below. Otherwise, use the standard single-task workflow.

### Autonomous Workflow Loop

**Step 1: Initialize**

```bash
# Verify tools (optional, recommended on first task only)
sdd verify-tools
```

**Check initial context (recommended):**

⚠️ **CRITICAL: Use the two-step pattern documented in [Context Checking Pattern](#context-checking-pattern).**

Run these as **TWO SEPARATE, SEQUENTIAL Bash tool calls:**

```bash
# First Bash call: Generate session marker
sdd session-marker
```

```bash
# Second Bash call: Check context using the marker from first call
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**NEVER:**
- ❌ Combine with `&&`: `sdd session-marker && sdd context ...`
- ❌ Combine with `$()`: `sdd context --session-marker "$(sdd session-marker)" ...`
- ❌ Run in parallel (both in same message)

**Why:** The marker from the first call must be logged to the transcript before the second call can find it.

If initial context ≥75%, recommend stopping before starting with AskUserQuestion.

**Step 2: Task Execution Loop**

For each task in the current phase:

1. **Prepare next task:**
```bash
sdd prepare-task {spec-id}
```

2. **Check if phase complete:**
   - If no more tasks in current phase: Exit loop, go to Step 3 (Summary)
   - If all remaining tasks are blocked: Exit loop, go to Step 3 (Summary)

3. **Check for blockers:**
   - If next task is blocked: **STOP**, present blocker info to user with AskUserQuestion
   - Options: alternative tasks, resolve blocker, or stop
   - Exit autonomous mode, handle as normal blocking scenario

4. **Create execution plan (silently):**
   - Analyze task metadata from prepare-task output
   - Create detailed execution plan internally (no user approval needed)
   - Include all standard plan components (prerequisites, steps, success criteria, etc.)

5. **Mark task as in_progress:**
```bash
sdd update-status {spec-id} {task-id} in_progress
```
   This sets the `started_at` timestamp needed for automatic time tracking.

6. **Execute task implementation:**
   - Implement according to the internal execution plan
   - Follow all implementation best practices
   - Perform any required testing or verification

7. **Handle plan deviations:**
   - If implementation deviates from plan: **STOP**, document deviation
   - Present deviation to user with AskUserQuestion
   - Options: revise plan, update spec, explain more, rollback
   - Exit autonomous mode, handle as normal deviation scenario

8. **Mark task complete:**
```bash
# Use sdd-update subagent to mark complete (requires journal content)
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Complete task {task-id} in spec {spec-id}. Completion note: [Brief summary of what was accomplished, tests run, etc.]",
  description: "Mark task complete"
)
```

9. **Check context usage (REQUIRED):**

⚠️ **CRITICAL: Use the two-step pattern documented in [Context Checking Pattern](#context-checking-pattern).**

Run as **TWO SEPARATE, SEQUENTIAL Bash tool calls:**

```bash
# First Bash call: Generate session marker
sdd session-marker
```

```bash
# Second Bash call: Check context using the marker from first call
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**NEVER combine with `&&`, `$()`, or run in parallel.** The marker must be logged to the transcript first.

   - If context ≥75%: **STOP**, exit loop, go to Step 3 (Summary)
   - If context <75%: Continue to next iteration

10. **Check phase completion:**
   - If current phase is complete: Exit loop, go to Step 3 (Summary)
   - Otherwise: Return to step 1 (prepare next task)

**Step 3: Present Summary Report**

When autonomous mode exits (for any reason), present a comprehensive summary:

```markdown
## Autonomous Execution Summary

**Mode:** Phase Completion (Autonomous)

**Spec:** {spec-title} ({spec-id})

**Phase:** {phase-title} ({phase-id})

### Tasks Completed

✅ **task-1-1:** Create directory structure
   - File: skills/sdd-render/
   - Completed: 2025-10-28 14:23:15
   - Duration: 15 minutes

✅ **task-1-2:** Create SKILL.md documentation
   - File: skills/sdd-render/SKILL.md
   - Completed: 2025-10-28 14:45:32
   - Duration: 22 minutes

✅ **task-1-3:** Implement skill entry point
   - File: skills/sdd-render/skill_main.py
   - Completed: 2025-10-28 15:12:08
   - Duration: 26 minutes

### Phase Progress

**Phase {phase-id}:** {completed_in_phase}/{total_in_phase} tasks completed ({percentage}%)

**Overall Spec:** {total_completed}/{total_tasks} tasks completed ({overall_percentage}%)

### Context Usage

**Current context:** {context_percentage}%

### Exit Reason

{One of the following:}
- ✅ **Phase Complete:** All tasks in {phase-id} have been completed
- ⏸️ **Context Limit:** Context usage reached {context_percentage}% (≥75% threshold)
- 🚧 **Blocked Task:** task-{X} is blocked by {dependency/reason}
- ⚠️ **Plan Deviation:** Implementation deviated from plan in task-{X}
- ❌ **No Actionable Tasks:** All remaining tasks in phase are blocked or in progress

### Next Steps

{Contextual recommendations based on exit reason:}

**For Phase Complete:**
- Phase {phase-id} is complete! Ready to move to {next-phase-id}
- Run /sdd-begin to start the next phase
- Consider reviewing phase deliverables before proceeding

**For Context Limit:**
- Consider resetting the session to free up context
- You've completed {N} tasks successfully
- Resume with /sdd-begin after reset

**For Blocked Task:**
- task-{X} requires: {blocker-description}
- Alternative tasks available: {list-alternatives}
- Choose how to proceed using the options provided

**For Plan Deviation:**
- Review the deviation details above
- Decide whether to revise plan or update spec
- Choose how to proceed using the options provided
```

**Step 4: Handle Exit Scenarios**

Based on exit reason:

1. **Phase Complete:**
   - Celebrate completion
   - Summarize phase achievements
   - Offer to start next phase (via /sdd-begin)

2. **Context Limit Reached:**
   - Present summary with context percentage
   - Use AskUserQuestion: "Stop and Reset" vs "Continue Anyway"
   - Recommend stopping to preserve context for next session

3. **Blocked Task Encountered:**
   - Present blocker details
   - Use AskUserQuestion to offer alternatives or resolve blocker
   - Exit autonomous mode, handle as normal blocking scenario

4. **Plan Deviation:**
   - Present deviation details
   - Use AskUserQuestion to get user decision
   - Exit autonomous mode, handle as normal deviation scenario

### Autonomous Mode Best Practices

**DO:**
- ✅ Check context after every task completion
- ✅ Stop immediately when context ≥75%
- ✅ Stop for blocked tasks (don't auto-pivot without user input)
- ✅ Stop for plan deviations (don't auto-revise without user approval)
- ✅ Create detailed internal execution plans for each task
- ✅ Document all completions with proper metadata
- ✅ Present comprehensive summary at end

**DON'T:**
- ❌ Cross phase boundaries (stop at end of current phase)
- ❌ Skip plan creation (always plan, just don't show to user)
- ❌ Continue past 75% context usage
- ❌ Auto-resolve blockers without user input
- ❌ Auto-revise plans on deviations without user approval
- ❌ Batch task completions (mark each complete immediately)

### Transitioning Back to Single-Task Mode

If autonomous mode exits due to blockers or deviations, the workflow naturally transitions back to single-task mode:

1. Present the issue with AskUserQuestion
2. Get user decision on how to proceed
3. Continue with standard single-task workflow
4. User can re-enable autonomous mode via /sdd-begin if desired

---

## Required Tools

This skill uses the `sdd` command that handles:
- JSON spec file parsing and queries
- Task metadata extraction from JSON
- Task discovery and dependency analysis
- Progress tracking and phase management

### The `sdd` tool

You have access to the `sdd` CLI.

**Available Commands:**

**Spec Operations:**
- `verify-tools` - Check system requirements
- `find-specs` - Discover specs directory (supports `-v, --verbose` to show spec files)
- `next-task {spec-id}` - Find next actionable task
- `task-info {spec-id} {task-id}` - Get task details from state
- `check-deps {spec-id} {task-id}` - Check task dependencies
- `progress {spec-id}` - Show overall progress
- `list-phases {spec-id}` - List all phases with status
- `list-blockers {spec-id}` - List all currently blocked tasks
- `query-tasks {spec-id}` - Query tasks by status, type, or parent (supports `--status`, `--type`, `--parent`)
- `check-complete {spec-id}` - Check if spec or phase is ready to be marked complete (supports `--phase {phase-id}`)

**Workflow Commands:**
- `prepare-task {spec-id} [task-id]` - Prepare task for implementation (finds next task if task-id not provided)
- `validate-spec {spec-id}` - Validate spec file structure
- `find-pattern {pattern}` - Find files matching glob pattern
- `format-plan {spec-id} {task-id}` - Format execution plan for display

**Project Analysis Commands:**
- `detect-project` - Detect project type and dependencies
- `find-tests` - Discover test files and testing framework (supports `--source-file {file}`)
- `check-environment` - Verify environmental requirements (supports `--required {deps}`)
- `find-circular-deps {spec-id}` - Detect circular dependencies
- `find-related-files {file}` - Find files related to a source file
- `validate-paths {paths...}` - Validate and normalize file paths (supports `--base-directory {dir}`)
- `spec-stats {spec-id}` - Get comprehensive spec statistics

**Optional Commands (Advanced/Specialized Use):**
- `init-env` - Initialize development environment (one-time setup, supports `--spec-path {path}`, `--export`)
- `--no-color` - Disable colored output
- `--verbose, -v` - Show detailed output (info messages)
- `--quiet, -q` - Minimal output (errors only)

**Command-Specific Common Options:**
- `--json` - Output as JSON (available on most commands)
- `--path <dir>` - Specify specs directory path (spec operations only)
- `--directory <dir>` - Specify project directory (project analysis commands only)
- `--status <status>` - Filter by status: pending, in_progress, completed, blocked (query-tasks only)
- `--type <type>` - Filter by type: task, verify, group, phase (query-tasks only)
- `--parent <id>` - Filter by parent node ID (query-tasks only)
- `--phase <phase-id>` - Check specific phase completion (check-complete only)

## Optional Context Enhancement Tools

**code-doc**: Generate codebase documentation. Use the `code-doc` subagent to create comprehensive docs. Check if docs exist: `sdd doc stats`. See code-doc SKILL.md for details.

**doc-query**: Query generated documentation for rapid codebase understanding. Use `Skill(sdd-toolkit:doc-query)` for smart context gathering (task-specific files, dependencies, test discovery). Falls back to manual exploration (`Explore`, `Glob`, `Grep`) if docs unavailable.

**Plan/Explore subagents**: Built-in Claude Code subagents for codebase exploration. Plan provides research + recommendations (requires approval), Explore provides direct findings. See [Codebase Exploration Subagents](#codebase-exploration-subagents) section for detailed guidance on when to use each.

**When mentioned in workflows**: Optional enhancements, not requirements. Core sdd-next functions without them.

## Codebase Exploration Subagents

**Built-in Claude Code subagents** for codebase exploration. Understanding when to use each maximizes efficiency.

### Plan vs Explore: Key Difference

**Plan Subagent** - Research + recommendations requiring user approval
- Returns analysis with recommended options
- Use when: Multiple approaches exist, need expert recommendation
- Example: "Analyze auth patterns and recommend which to use"

**Explore Subagent** - Direct findings without approval gates
- Returns factual information immediately
- Use when: Clear what you need, just need to find it
- Example: "Find all files related to authentication"

### When to Use Plan Subagent

Use for **decision-making scenarios**:

**Implementation Strategy** - Analyze architecture patterns, evaluate trade-offs, recommend approach
```
Task(subagent_type: "Plan",
     prompt: "Analyze auth implementation in codebase. Task adds JWT middleware
              in src/middleware/auth.ts. Find patterns, recommend approach with
              pros/cons. Thoroughness: medium",
     description: "Research auth patterns")
```

**Assumption Verification** - Verify plan assumptions before implementation starts
- Check API patterns match expectations
- Identify integration issues early
- Recommend adjustments if needed

**Alternative Analysis** - When blocked, find and recommend alternative tasks
- Evaluates spec for parallel-safe alternatives
- Considers value and effort
- Provides reasoning for recommendations

**Risk Assessment** - Identify issues, analyze impact, recommend mitigations

### When to Use Explore Subagent

Use for **straightforward fact-finding**:

**File Discovery** - Find files by pattern, locate tests, identify related code
```
Task(subagent_type: "Explore",
     prompt: "Find TypeScript files in src/ implementing auth logic.
              Include imports/references. Thoroughness: quick",
     description: "Find auth files")
```

**Implementation Reading** - Understand how features work, check API signatures
**Quick Lookups** - Find definitions, locate configs, check dependencies
**Dependency Analysis** - Trace imports, find callers, understand relationships

### Decision Guide

```
Need a recommendation? → Plan (presents options for approval)
Just need facts?       → Explore (returns findings directly)
```

### Thoroughness Levels

- **quick**: Fast answers, straightforward tasks
- **medium**: Standard coverage (default for most tasks)
- **very thorough**: Complex/unfamiliar areas, high-risk changes

### Best Practices

✅ Use Plan for recommendations/decisions, Explore for facts
✅ Specify thoroughness based on complexity
✅ Present Plan results with AskUserQuestion
✅ Include specific paths when known
✅ Combine with doc-query when docs exist

❌ Don't use Plan for file lookups
❌ Don't use Explore when choosing between options
❌ Don't ignore Plan recommendations without user consultation

## Interactive Question Tool

**Tool:** `AskUserQuestion` (Claude Code built-in)

**Purpose**: Present structured, interactive questions to users at key decision points instead of text-based prompting.

**CRITICAL: ALWAYS USE THIS TOOL FOR USER DECISIONS**

When presenting options to the user, you MUST use `AskUserQuestion`. NEVER use text-based numbered lists.

**When to use in this skill:**
- **Phase 2.3**: Presenting task options for user selection
- **Phase 5.2**: Getting approval/feedback on execution plans (REQUIRED after format-plan)
- **Verification tasks**: When verification is complete and seeking approval to mark task complete
- **Any decision point**: When offering multiple clear choices to the user
- **Blocker handling**: When presenting alternatives for blocked tasks

**Benefits:**
- ✅ Structured responses - No need to parse free-form text
- ✅ Clear options - Users see exactly what choices are available
- ✅ Better UX - More interactive and guided experience
- ✅ Consistent - Same interaction pattern across workflows

**This is NOT optional** - it's a core part of the skill's UX design.

**Example Usage:**
```
AskUserQuestion(
  questions: [{
    question: "Which task would you like to work on?",
    header: "Task Selection",
    multiSelect: false,
    options: [
      {
        label: "task-2-1 (Recommended)",
        description: "src/services/authService.ts - Implement core authentication (3 hours)"
      },
      {
        label: "task-1-7",
        description: "tests/user.spec.ts - Write user model tests (1.5 hours)"
      }
    ]
  }]
)
```

**Tool Parameters:**
- `questions`: Array of 1-4 questions to ask
  - `question`: The complete question text
  - `header`: Short label (max 12 chars) displayed as a chip/tag
  - `multiSelect`: Set to true to allow multiple selections (default: false)
  - `options`: 2-4 available choices
    - `label`: Display text for the option (1-5 words)
    - `description`: Explanation of what this option means

**Note:** Users can always select "Other" to provide custom text input if the provided options don't match their needs.

### Decision Point Rules

**When to Use AskUserQuestion:**
- ✅ User needs to make a choice between 2-4 clear options
- ✅ The decision affects workflow direction (which task, how to proceed, etc.)
- ✅ Options are mutually exclusive or can be presented as distinct choices
- ✅ You want structured, unambiguous user input

**When to Use Text Communication:**
- ✅ Presenting data, progress reports, or context information
- ✅ Explaining concepts, showing details, or providing documentation
- ✅ Asking open-ended questions that need free-form responses
- ✅ Showing command outputs or technical information

**The Recommended Pattern:**

```
1. Present Context (Text)
   - Show relevant information
   - Explain the situation
   - Provide recommendations

2. Ask Structured Question (AskUserQuestion)
   - Present 2-4 clear options
   - Each option has label + description
   - User selects their choice

3. Handle Response (Code Logic)
   - Process user selection
   - Execute appropriate workflow branch
   - Continue with next phase
```

**Example Decision Points in This Workflow:**
- Task selection from multiple available tasks
- Plan approval or requesting changes
- Handling blockers (work on alternative or resolve blocker)
- Multiple specs selection
- Resuming work after completion

**Anti-Pattern - Don't Do This:**
```
Would you like to:
1. Option A
2. Option B
3. Option C
```
Instead, use AskUserQuestion with structured options.

## When to Use This Skill

Use `Skill(sdd-toolkit:sdd-next)` when:
- Ready to start implementing from an existing spec
- Need to find the next task to work on
- Want to understand a specific task's context
- Creating execution plan for a task
- Resuming work on a partially-completed spec
- Coordinating work across multiple developers/tools
- Need to understand how a task fits in the bigger picture

**Do NOT use for:**
- Creating new specifications (use `Skill(sdd-toolkit:sdd-plan)`)
- Updating task status or progress (use sdd-update subagent)
- Actual code implementation (use appropriate coding tools)
- Quick bug fixes or one-off changes
- Work outside of a spec-driven workflow

## Skill Handoff Points

**When to transition to other skills:**

← **From Skill(sdd-toolkit:sdd-plan)**:
  - JSON spec file has been created
  - Ready to begin implementation work
  - Need to identify first actionable task

→ **To Implementation Tools**:
  - After execution plan is created and approved
  - Hand off to coding tools (Claude, Cursor, human developers)
  - Execution plan guides the actual code writing

→ **To sdd-update subagent**:
  - Before starting implementation (mark task in_progress)
  - After completing implementation (mark task completed)
  - When encountering blockers (document issue)
  - When making deviations from plan (journal decision)
  - After task completion, to unlock dependent tasks

← **From sdd-update subagent**:
  - After a task is completed, find the next task
  - After resolving a blocker, resume work
  - After updating progress, continue to next work item

## Decision Tree: Which Skill to Use?

```
Have a spec already?
├─ No → Use `Skill(sdd-toolkit:sdd-plan)` first to create one
└─ Yes → Continue below

What do you need to do?
├─ Find next task to work on → Use `Skill(sdd-toolkit:sdd-next)` (this skill)
├─ Create execution plan → Use `Skill(sdd-toolkit:sdd-next)` (this skill)
├─ Update task status → Use sdd-update subagent
├─ Journal a decision → Use sdd-update subagent
├─ Actually write code → Use implementation tools (after Developer creates plan)
└─ Create new spec → Use `Skill(sdd-toolkit:sdd-plan)`

Ready to implement?
├─ Don't know which task → Use this skill to identify next task
├─ Know the task, need plan → Use this skill to create execution plan
├─ Have plan, ready to code → Hand off to implementation tools
└─ Task complete → Use sdd-update subagent to update status
```

## The Developer Workflow

### Quick Start Decision Tree

**Step 1: Check Context (Optional)**

If needed: Check context using the two-step pattern (see [Context Checking Pattern](#context-checking-pattern)). If ≥75%, recommend reset with `AskUserQuestion` (options: "Stop and Reset" or "Continue").

**Step 2: Run Automated Workflow**

```bash
# If you know the spec-id:
sdd prepare-task {spec-id}

# If you don't know the spec-id:
# See "Edge Case: Multiple Specs" below
```

**Step 3: Handle Result**

- ✅ Success → Skip to "Create Execution Plan" below
- ⚠️  Multiple specs found → See "Edge Case: Multiple Specs"
- ❌ No actionable tasks → See "Edge Case: No Actionable Tasks"
- ❌ Other error → See Troubleshooting section

---

### Edge Case: Multiple Specs

**When:** You don't know which spec-id to use, or `prepare-task` returns multiple specs.

**Steps:**

1. **Find available specs:**
```bash
sdd find-specs --verbose
```

2. **Present options to user with AskUserQuestion:**

```
📋 Multiple Specifications Found

Available specs:
- user-auth-2025-10-24-001 (Active, 5 pending tasks, 60% complete)
- api-refactor-2025-10-25-001 (Active, 12 pending tasks, 30% complete)
- bug-fix-2025-10-26-001 (Active, 2 pending tasks, 75% complete)
```

Use `AskUserQuestion`:
- Question: "Which specification would you like to work on?"
- Header: "Select Spec"
- Options: One for each spec (label: spec-id, description: status + progress)
- Include "Other" for custom input

3. **Once user selects, run `prepare-task` with that spec-id**

---

### Edge Case: No Actionable Tasks

**When:** `prepare-task` returns "no actionable tasks" or all tasks are blocked/in_progress.

**Steps:**

1. **Diagnose the situation:**
```bash
sdd list-blockers {spec-id}
sdd check-complete {spec-id}
```

2. **Present situation to user:**

```
⚠️  No Actionable Tasks Available

Spec: user-auth-2025-10-24-001

Status:
- 8 tasks completed
- 3 tasks in_progress
- 2 tasks blocked

Blockers:
- task-2-3: Depends on task-2-1 (in_progress)
- task-2-4: Depends on task-2-1 (in_progress)
```

3. **Use AskUserQuestion with options:**
- "Wait for {task-id}" - Exit gracefully
- "View All Tasks" - Show all tasks with `query-tasks`
- "Work on Different Spec" - Return to Multiple Specs workflow
- "Resolve Blocker" - Provide guidance on resolving blocker

---

### Create Execution Plan

**After `prepare-task` succeeds, create a detailed execution plan.**

**Key components:**

1. **Task Summary**
   - Task ID and title
   - Type (task, verify, group, phase)
   - Phase information
   - Estimated effort

2. **Prerequisites Check**
   - Review dependencies from `prepare-task` output
   - Verify required files/tools exist
   - Note any blockers or risks

3. **Implementation Steps**
   - Break task into 3-7 concrete steps
   - For each step:
     - Action (what to do)
     - Reasoning (why this approach)
     - Duration (time estimate)
     - Key details (important considerations)

4. **Success Criteria**
   - Specific, measurable outcomes
   - How to verify task completion
   - Expected test results

5. **Potential Issues**
   - Known risks or challenges
   - Mitigation strategies
   - Alternative approaches

6. **Testing Strategy**
   - Required test coverage
   - Test file locations
   - Verification commands

**Use context from:**
- Task metadata in `prepare-task` output
- Related files mentioned in spec
- Dependencies and blockers
- Verification steps defined in spec

---

### Present Plan and Get Approval

**After creating the plan, present it to the user for approval.**

**Step 1: Format the plan (optional)**
```bash
sdd format-plan {spec-id} {task-id}
```

**Step 2: Present plan to user**

Show the formatted execution plan with all sections clearly separated.

**Step 3: IMMEDIATELY use AskUserQuestion for approval**

**CRITICAL: Never use text-based options like "1. Approve, 2. Request changes". ALWAYS use AskUserQuestion.**

```javascript
AskUserQuestion(
  questions: [{
    question: "Review the execution plan above. How would you like to proceed?",
    header: "Plan Review",
    multiSelect: false,
    options: [
      {
        label: "Approve & Start",
        description: "Begin implementing this plan"
      },
      {
        label: "Request Changes",
        description: "Suggest modifications to the plan"
      },
      {
        label: "More Details",
        description: "Request additional information or clarification"
      },
      {
        label: "Defer",
        description: "Save plan for later"
      }
    ]
  }]
)
```

**Step 4: Handle user response**

- **Approve & Start:**
  1. Mark task as in_progress using the CLI:
     ```bash
     sdd update-status {spec-id} {task-id} in_progress
     ```
     This sets the `started_at` timestamp needed for automatic time tracking.
  2. Begin implementation according to plan
- **Request Changes:** Ask for specifics, revise plan, re-present with AskUserQuestion
- **More Details:** Provide requested details, then re-ask with AskUserQuestion
- **Defer:** Save plan details and exit gracefully

---

### Post-Implementation

**After completing implementation:**

1. **Mark task complete using sdd-update (requires journal content):**
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Complete task {task-id} in spec {spec-id}. Completion note: Successfully implemented [feature/fix]. [Brief description of what was done, tests run, verification performed].",
  description: "Mark task complete"
)
```

2. **The sdd-update subagent will:**
   - Update task status to "completed"
   - Set completion timestamp
   - Create journal entry documenting the completion
   - Clear the needs_journaling flag
   - Identify next actionable task

3. **Check context usage after completion (REQUIRED):**

After the task is marked complete, you MUST check context usage.

⚠️ **CRITICAL: Use the two-step pattern documented in [Context Checking Pattern](#context-checking-pattern).**

Run as **TWO SEPARATE, SEQUENTIAL Bash tool calls:**

```bash
# First Bash call: Generate session marker
sdd session-marker
```

```bash
# Second Bash call: Check context using the marker from first call
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**NEVER combine with `&&`, `$()`, or run in parallel.** The marker must be logged to the transcript first.

If context usage is ≥75%, use `AskUserQuestion` to prompt the user:

```javascript
AskUserQuestion(
  questions: [{
    question: "Context usage is at X%. Continue or reset?",
    header: "Context Check",
    multiSelect: false,
    options: [
      {
        label: "Stop and Reset",
        description: "End session and recommend resetting context before continuing"
      },
      {
        label: "Continue Anyway",
        description: "Continue working despite high context usage"
      }
    ]
  }]
)
```

Include the current context percentage in the completion report.

4. **Continue with next task or end session**

---

## Common Workflows

### Workflow 1: Starting Fresh
**Situation:** Spec exists, no tasks started yet

Steps:
1. Run `sdd prepare-task {spec-id}`
2. Review task details and dependencies
3. **Optional: Use Plan subagent for complex/architectural tasks**
   - Analyzes codebase patterns, recommends approach
   - Present recommendations with AskUserQuestion
4. Create execution plan (incorporating approved recommendations)
5. Present plan with AskUserQuestion
6. Begin implementation

**Example with Plan subagent:**

```
sdd prepare-task user-auth-001  # Returns task-1-1 "Create AuthService"

Task(subagent_type: "Plan",
     prompt: "Analyze service classes in src/services/ for patterns. Task creates
              AuthService in src/services/authService.ts for JWT. Recommend:
              class structure, DI pattern, error handling, test strategy.
              Thoroughness: medium",
     description: "Research service patterns")

# Present Plan recommendations to user with AskUserQuestion
# Create execution plan based on approved approach
```

**Use Plan subagent when:** First task in new area, architectural tasks, multiple approaches exist, affects many components

**Skip for:** Simple tasks, explicit instructions in spec

### Workflow 2: Resuming Work
**Situation:** Some tasks completed, need to continue

Steps:
1. Run `sdd prepare-task {spec-id}`
2. Review progress information from output
3. Create execution plan for next task
4. Present plan with context of progress:

**Present context and proceed:**
```
📊 Spec Progress: User Authentication System (35% complete, 7/23 tasks)

Current Phase: Phase 2 - Authentication Service (2/8 tasks, 25%)

🎯 Resuming with task-2-2:
   File: src/middleware/auth.ts
   Purpose: JWT verification middleware
   Estimated: 2 hours
   Dependencies: ✅ task-2-1 (AuthService) completed

[Execution plan details...]

Ready to proceed with this task. Reply "different task" to see alternatives,
or "review progress" for detailed status.
```

8. Proceed with execution plan automatically
   - User can interrupt with "different task" to use Phase 2.3 (Present Task Options)
   - User can ask "review progress" to run `sdd progress {spec-id}`
   - User can say "stop" or "pause" to defer
9. Continue implementation

### Workflow 3: Handling Blockers
**Situation:** Next task is blocked by external issue

Steps:
1. Identify next logical task (task-3-1)
2. Check dependencies
3. Discover blocker (e.g., Redis not configured)
4. Document blocker using sdd-update subagent:
   ```
   Task(
     subagent_type: "sdd-toolkit:sdd-update-subagent",
     prompt: "Mark task {task-id} as blocked. Reason: Redis server not configured. Type: dependency.",
     description: "Document blocker"
   )
   ```
5. **Use Plan subagent to analyze alternatives and recommend next steps:**
   ```
   Task(
     subagent_type: "Plan",
     prompt: "Task task-3-1 (src/cache/redis.ts) is blocked by Redis configuration.
             Analyze the spec at specs/active/user-auth-001.json and identify
             alternative tasks that: (1) have no blockers, (2) are parallel-safe
             with task-3-1, (3) provide clear value toward spec completion.
             For each alternative found (aim for 3-5), explain:
             - Why it's a good alternative
             - Estimated effort
             - Dependencies status
             - Value/priority
             Recommend which alternative to work on next with reasoning.
             Thoroughness: medium",
     description: "Analyze blocked task alternatives"
   )
   ```
6. Plan subagent returns analysis with recommended alternatives
7. Use `AskUserQuestion` to present options to user:

**Present context:**
```
⚠️  Task task-3-1 (src/cache/redis.ts) is blocked:
   Dependency: Redis server must be configured

Available alternative tasks:
- task-2-5: src/utils/validators.ts (2 hours, parallel-safe)
- task-4-1: tests/auth.spec.ts (1.5 hours, from Phase 4)
```

**Then ask with AskUserQuestion:**
```
AskUserQuestion(
  questions: [{
    question: "The next task is blocked by Redis configuration. How would you like to proceed?",
    header: "Task Blocked",
    multiSelect: false,
    options: [
      {
        label: "task-2-5 (Validators)",
        description: "src/utils/validators.ts - Input validation (2 hours, parallel-safe)"
      },
      {
        label: "task-4-1 (Tests)",
        description: "tests/auth.spec.ts - Auth tests (1.5 hours, from Phase 4)"
      },
      {
        label: "Resolve Blocker",
        description: "Help me configure Redis first, then continue with task-3-1"
      },
      {
        label: "Stop for Now",
        description: "Document blocker and finish work session"
      }
    ]
  }]
)
```

8. Based on user selection:
   - If alternative task selected: Create plan for that task
   - If "Resolve Blocker": Provide guidance on resolving the blocker
   - If "Stop for Now": Summarize what was blocked and exit
9. Note that original task should resume after blocker cleared

**Benefits of using Plan subagent in Workflow 3:**
- ✅ Comprehensive alternative analysis (spec-aware)
- ✅ Expert recommendations with reasoning
- ✅ Considers parallel-safety and dependencies automatically
- ✅ Saves main agent context for actual implementation
- ✅ Provides structured options ready for AskUserQuestion

### Workflow 4: Spec Completion
**Situation:** All tasks in spec are completed, ready for next steps

**When this happens:**
- sdd-update completes final task
- Detects spec completion with AI PR enabled
- Hands off to sdd-next for orchestration

Steps:
1. Check spec status via `sdd check-complete {spec-id}`
2. Verify all tasks are completed
3. Check git integration status and ai_pr configuration
4. Present completion summary to user
5. Suggest next action based on configuration

**If AI PR is enabled:**
```
🎉 Spec Completed: {spec-title}

All 23 tasks completed across 4 phases.

Branch: {branch-name}
Base: {base-branch}
Commits: {N} commits ready

Next Step: Create Pull Request

To create an AI-powered PR with comprehensive description:
  Skill(sdd-toolkit:sdd-pr)

The sdd-pr skill will:
1. Analyze spec metadata, git diffs, commit history, and journals
2. Generate comprehensive PR description
3. Show draft for your approval
4. Create PR after confirmation

Would you like to create the PR now?
```

**If AI PR is disabled:**
```
🎉 Spec Completed: {spec-title}

All 23 tasks completed.

Next Steps:
1. Create PR manually: gh pr create
2. Move spec to completed: sdd move-spec {spec-id} completed
3. Start new spec: Skill(sdd-toolkit:sdd-next) with different spec

What would you like to do?
```

**Agent actions:**
- Present completion summary
- Check configuration for ai_pr.enabled
- If enabled: Suggest `Skill(sdd-toolkit:sdd-pr)` with spec_id
- If disabled: Provide manual next steps
- Wait for user decision

**Important:** The agent should invoke `Skill(sdd-toolkit:sdd-pr)` only after user confirmation, passing the spec_id clearly.

### Workflow 5: Plan Refinement
**Situation:** Initial plan needs adjustment during implementation

**Recommended: Proactive Verification**

Before starting complex tasks, use Plan subagent to verify assumptions:

```
Task(subagent_type: "Plan",
     prompt: "About to implement task-2-1 (src/services/authService.ts) assuming
              User API uses callbacks. Verify: (1) User API pattern in src/models/User.ts,
              (2) error handling in existing services, (3) any plan mismatches.
              Recommend adjustments if needed. Thoroughness: quick",
     description: "Verify plan assumptions")
```

This catches deviations **before** implementation, saving time and avoiding rework.

**Reactive: Handle Mid-Implementation Deviations**

If deviation discovered during implementation:

1. Pause and use Plan subagent to analyze:
   ```
   Task(subagent_type: "Plan",
        prompt: "Deviation in task-2-1: Plan assumed callbacks, actual uses async/await.
                 Analyze: (1) plan changes needed, (2) impact on tests/deps,
                 (3) alternatives (wrapper vs rewrite vs change API).
                 Recommend approach with pros/cons. Thoroughness: medium",
        description: "Analyze deviation")
   ```

2. Document deviation with sdd-update subagent

3. Present Plan subagent recommendations to user with AskUserQuestion:
   - Options: Revise Plan / Update Spec / Explain More / Rollback
   - User selects approach
   - Execute accordingly

**Use proactive for:** Complex tasks, unfamiliar areas, specific API assumptions
**Use reactive for:** Simple tasks hitting unexpected issues, rapid prototyping

### Verification Tasks

For verification tasks (`type: verify`), invoke the appropriate subagent based on `verification_type`:

#### Automated Tests (`verification_type: "auto"`)

**Metadata:**
```json
{
  "verification_type": "auto",
  "agent": "run-tests",
  "command": "npm test"
}
```

**Invocation:**
```
Task(
  subagent_type: "sdd-toolkit:run-tests-subagent",
  prompt: "Run tests for {task-id} in spec {spec-id}. Execute tests and handle failures.",
  description: "Run tests"
)
```

After verification completes, present findings to user and use `AskUserQuestion` to get approval before marking complete with sdd-update. See run-tests SKILL.md for details.

---

#### Fidelity Review (`verification_type: "fidelity"`)

**Metadata:**
```json
{
  "verification_type": "fidelity",
  "agent": "sdd-fidelity-review",
  "scope": "phase",
  "target": "phase-2"
}
```

**Invocation:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review {scope} '{target}' in spec {spec-id}. Compare completed tasks against requirements.",
  description: "Fidelity review for {scope}"
)
```

**Prompt construction by scope:**
- `"phase"` → "Review phase {target} in spec {spec-id}..."
- `"task"` → "Review task {target} in spec {spec-id}..."

After review completes, present fidelity report and use `AskUserQuestion` to get user decision:
- **Accept & Complete** - Mark verification complete, journal deviations
- **Revise Implementation** - Reopen parent tasks for fixes
- **Update Spec** - Document accepted deviations

See sdd-fidelity-review SKILL.md for details.

---

#### Orchestrating Spec Modifications via sdd-modify-subagent

After review verification tasks complete, sdd-next can orchestrate systematic spec modifications using the `sdd-modify-subagent`.

**Important:** Review skills (sdd-fidelity-review, sdd-plan-review) generate reports but do NOT modify specs. **sdd-next** orchestrates modifications when review findings warrant spec updates.

##### When to Call sdd-modify-subagent

**After Fidelity Review:**
- Review identifies vague task descriptions, missing verifications, or spec/implementation drift
- Present option to user: apply feedback systematically vs. manual review

**After Plan Review (Pre-Implementation):**
- Multi-model consensus identifies spec improvements before work begins
- Present option to user: apply consensus recommendations vs. proceed as-is

**During Task Execution:**
- Developer discovers spec is wrong/unclear during implementation
- Present option to user: update spec now vs. journal deviation vs. revise code

##### What sdd-modify-subagent Needs

**Required Information:**
1. **Spec ID** - Which spec to modify
2. **Either:**
   - Review report path (e.g., `reports/{spec-id}-fidelity-review.md`) for automatic extraction
   - OR specific modification instructions (task ID, field, new value)

**Optional:**
- Preview before applying (`--dry-run`)
- Rationale for modifications
- Consensus threshold (for plan reviews)

##### How to Invoke

**Basic Invocation Pattern:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Parse review report at {review-path} and apply modifications to spec {spec-id}. Preview changes, validate, and report results.",
  description: "Apply review feedback to spec"
)
```

**Example: After Fidelity Review**
```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Parse fidelity review report at reports/my-spec-001-fidelity-review.md and apply modifications to spec my-spec-001. Show preview, apply with validation, report results.",
  description: "Apply fidelity review feedback"
)
```

**Example: Specific Update**
```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Update task-2-3 description in spec my-spec-001 to 'Implement OAuth 2.0 authentication with PKCE flow, JWT tokens, and refresh rotation'. Validate and report.",
  description: "Update task description"
)
```

##### Handling Response

After sdd-modify-subagent completes, it returns:
- Summary of modifications applied
- Validation status (passed/failed)
- Backup file location (if created)
- Any errors encountered

**Then sdd-next should:**
1. Report results to user
2. Document changes in journal (if appropriate)
3. Offer re-verification (if review-triggered)
4. Continue workflow

##### Integration Pattern

```
1. Verification/Review completes → sdd-next receives report
2. Analyze findings for systematic improvements
3. Present options to user (AskUserQuestion)
4. If approved → Task(sdd-modify-subagent)
5. Handle response and continue workflow
```

##### See Also

- **Skill(sdd-toolkit:sdd-modify)** - Complete workflows, examples, CLI commands
- **agents/sdd-modify.md** - Subagent contract with detailed operation specs
- **skills/sdd-modify/examples/** - Full walkthrough examples

---

#### Manual Review (`verification_type: "manual"`)

**Metadata:**
```json
{
  "verification_type": "manual",
  "checklist": ["Item 1", "Item 2"]
}
```

**Action:** Present checklist to user for manual confirmation.

---

#### Note: Metadata vs Invocation Naming

- **Metadata field:** `"agent": "run-tests"` (base identifier)
- **Invocation:** `Task(subagent_type: "sdd-toolkit:run-tests-subagent")` (fully qualified)
- **Why different?** Metadata is concise storage; invocation is namespace-qualified routing

## Git Integration Workflow

The sdd-next skill supports optional git integration when enabled in configuration. This section explains how git operations integrate with the task preparation and execution workflow.

### Overview

When git integration is enabled (`git_config.is_git_enabled()` returns True), the workflow automatically handles:
- Branch creation when starting work on a spec
- Drift detection between spec metadata and actual git state
- Commit cadence preference tracking

All git operations are **optional** and **non-blocking**. If git is disabled or unavailable, the skill continues normally without git features.

### Branch Creation Workflow

When starting work on a spec without an existing branch (no `metadata.git.branch_name`):

**Step 1: Find Git Repository Root**
```python
from claude_skills.common.git_metadata import find_git_root

repo_root = find_git_root()
if not repo_root:
    # Not in a git repository - skip git operations
    continue_without_git()
```

**Step 2: Check for Uncommitted Changes**
```python
from claude_skills.common.git_metadata import check_dirty_tree

is_dirty, message = check_dirty_tree(repo_root)
if is_dirty:
    # Inform user but don't block
    print(f"⚠️  Working tree has uncommitted changes: {message}")
    print("You may want to commit or stash these changes before creating a new branch.")
```

**Step 3: Offer Branch Creation**

Use `AskUserQuestion` to offer branch creation:

```python
AskUserQuestion(
    questions: [{
        question: "Create a new git branch for this spec?",
        header: "Git Branch",
        multiSelect: false,
        options: [
            {
                label: "Create branch",
                description: f"Run: git checkout -b feat/{spec_id}"
            },
            {
                label: "Use current branch",
                description: "Continue on current branch without creating new one"
            },
            {
                label: "Skip git integration",
                description: "Disable git operations for this session"
            }
        ]
    }]
)
```

**Step 4: Execute Branch Creation**

If user selects "Create branch":
```bash
# Use Bash tool to create branch
git checkout -b feat/{spec-id}
```

### Git Command Execution Pattern

All git commands follow this pattern:

**1. Find Repository Root**
```python
repo_root = find_git_root()
if not repo_root:
    # Handle gracefully - git not available
    return
```

**2. Execute with subprocess.run**
```python
import subprocess

result = subprocess.run(
    ["git", "command", "args"],
    cwd=repo_root,  # Always use repo root as cwd
    capture_output=True,
    text=True,
    timeout=10
)
```

**3. Check Return Code**
```python
if result.returncode != 0:
    logger.warning(f"Git command failed: {result.stderr}")
    # Handle error gracefully - don't crash
    return
```

**4. Process Output**
```python
output = result.stdout.strip()
# Use output as needed
```

### Error Handling

Git operations should **never block** the main workflow:

**DO:**
- ✅ Log warnings for git errors
- ✅ Continue without git features if git unavailable
- ✅ Provide informative messages to users
- ✅ Use timeouts on all subprocess calls
- ✅ Handle `CalledProcessError`, `TimeoutExpired`, `FileNotFoundError`

**DON'T:**
- ❌ Raise exceptions that stop task execution
- ❌ Require git to be installed
- ❌ Block on git operations
- ❌ Assume git commands will succeed

### Integration Points

Git workflow integrates at these points in sdd-next:

**1. Task Preparation (prepare-task)**
- Check if git enabled
- Detect repository and branch
- Offer branch creation if needed
- Detect drift and warn user

**2. Execution Plan Creation**
- Include git context in plan
- Mention current branch
- Note any drift warnings

**3. Post-Implementation (via sdd-update)**
- Create commits based on cadence preference
- Update commit metadata in spec
- Track commit SHAs and messages

### Configuration

Git integration is controlled by `git_config.py`:

```python
from claude_skills.common.git_config import is_git_enabled, get_git_setting

# Check if git integration is enabled
if not is_git_enabled():
    # Skip all git operations
    return

# Get specific settings
auto_branch = get_git_setting('auto_branch')  # True/False
auto_commit = get_git_setting('auto_commit')  # True/False
commit_cadence = get_git_setting('commit_cadence')  # "task"/"phase"/"manual"
```

See `.claude/GIT_CONFIG_README.md` for configuration details.

## Advanced Query Techniques

For power users who need complex task filtering beyond simple `next-task`.

### Using query-tasks Command

The `query-tasks` command provides flexible filtering for complex scenarios:

**Find all pending tasks in a specific phase:**
```bash
sdd query-tasks {spec-id} --status pending --parent phase-2
```

**Find all verification tasks:**
```bash
sdd query-tasks {spec-id} --type verify
```

**Combine filters:**
```bash
# Find all completed tasks in phase-1
sdd query-tasks {spec-id} --status completed --parent phase-1
```

### When to Use Each Approach

| Tool | Use Case | Example |
|------|----------|---------|
| `next-task` | Find single next actionable task | "What should I work on now?" |
| `query-tasks` | Filter tasks by criteria | "Show all pending tasks in phase-2" |
| `list-blockers` | Understand what's blocked | "Which tasks are waiting on dependencies?" |

### Common Advanced Queries

**1. Find all tasks that can be started right now:**
```bash
# Pending tasks with no blockers
sdd query-tasks {spec-id} --status pending
```

**2. Analyze blocked tasks:**
```bash
# See what's blocking progress
sdd list-blockers {spec-id}
```

**3. Check phase completion readiness:**
```bash
# Before moving to next phase, verify current phase is complete
sdd check-complete {spec-id} --phase phase-2
```

**4. Get all verification steps:**
```bash
# Find all verifications to understand testing requirements
sdd query-tasks {spec-id} --type verify
```

**5. Find tasks by parent (all tasks in a phase):**
```bash
# Get all tasks under phase-2, regardless of status
sdd query-tasks {spec-id} --parent phase-2
```

## Troubleshooting

### Issue: Context Check Fails - "No transcript path provided"

**Symptoms:**
- Error: `❌ Error: No transcript path provided.`
- Context checking command fails with missing transcript error
- Session marker not found

**Root Cause:**
The `sdd context` command was run without first generating a session marker, or the commands were combined/run in parallel instead of sequentially.

**Solution:**

✅ **ALWAYS use the two-step pattern documented in [Context Checking Pattern](#context-checking-pattern):**

```bash
# First Bash call: Generate session marker
sdd session-marker
```

```bash
# Second Bash call: Check context using the marker from first call
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**Critical Requirements:**
1. Run as **TWO SEPARATE** Bash tool calls
2. Run **SEQUENTIALLY** (not in parallel)
3. **NEVER** combine with `&&` or `$()`
4. Wait for step 1 to complete and be logged before running step 2

**Why This Fails:**
```bash
# ❌ WRONG - Combined with &&
sdd session-marker && sdd context --session-marker "..." --json

# ❌ WRONG - Combined with $()
sdd context --session-marker "$(sdd session-marker)" --json

# ❌ WRONG - Run in parallel (both Bash calls in same message)
```

The session marker must be written to the conversation transcript before the context command can find it. Combining or parallelizing breaks this requirement.

### Issue: Spec File Not Found / Path Errors

**Symptoms:**
- Error: `grep: specs/active/file.json: No such file or directory`
- Commands return "No content" or file not found errors

**Root Cause:**
The skill is run from a different working directory than where specs are located. Relative paths fail because they don't exist relative to the current directory.

**Solutions:**
1. **Provide absolute path** when invoking: Set `SPEC_PATH_PARAM="/absolute/path/to/specs/active/myspec.json"`
2. **Run from correct directory**: Navigate to directory containing `specs/`
3. **Use enhanced discovery**: Phase 1.1 checks multiple common locations automatically

**Prevention:**
Always run `sdd verify-tools` before starting spec work.

### Issue: Can't Find Next Task
**Symptoms:**
- All tasks show as blocked
- No pending tasks in current phase
- Spec file shows 100% but spec shows pending tasks

**Diagnosis:**
1. Check spec file for consistency
2. Verify dependencies are correctly marked
3. Look for circular dependencies
4. Check if phase ordering is wrong

**Solution:**

Use the Python tool for dependency analysis:

```bash
sdd find-circular-deps {spec-id}
sdd next-task {spec-id}
```

Detects circular chains, orphaned tasks, and impossible dependency chains.

### Issue: Spec File Inconsistency
**Symptom:** JSON spec file has inconsistent or incorrect data
**Solution:** Regenerate JSON spec file with `Skill(sdd-toolkit:sdd-plan)`

### Issue: Dependencies Not Clear
**Symptom:** Unsure if task dependencies are met

**Solution:**

1. Use `sdd check-deps {spec-id} {task-id}` to verify dependency status
2. If dependency status is still unclear after checking, explain the concern and ask user:

**Present context and ask:**
```
⚠️  Unclear Dependency Status

Task: task-2-3 (src/middleware/auth.ts)

Dependency Analysis:
- task-2-1 (AuthService) status: completed
- However: No test verification for task-2-1 found
- Risk: AuthService may have issues that could affect this task

Recommendation: Verify task-2-1 is truly complete before proceeding.

Should I proceed with this task anyway, or would you like to:
- Verify task-2-1 completion first
- Work on a different task instead
- See more details about the risk

Let me know how you'd like to proceed.
```

**Handle user response:**
- If user says proceed/yes: Continue with task
- If user asks for verification: Guide through verification steps
- If user wants different task: Use Phase 2.3 (Present Task Options)
- If user asks for details: Explain the specific dependency concern

### Issue: Plan Too Complex
**Symptom:** Plan is too large or exceeds estimates
**Solution:** Split into smaller tasks using sdd-update subagent

## Quick Reference

### Context Checking (Two-Step Pattern)

**⚠️ ALWAYS run session-marker FIRST before checking context:**

```bash
# Step 1: Generate session marker (REQUIRED FIRST)
sdd session-marker

# Step 2: Check context using the marker from step 1
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

**CRITICAL:** Run as TWO SEPARATE, SEQUENTIAL commands. Never combine with `&&` or `$()`. Never run in parallel. See [Context Checking Pattern](#context-checking-pattern) section for details.

### Core Workflow Commands

**Automated Workflow (Recommended):**
```bash
# 1. Prepare task (handles discovery automatically)
sdd prepare-task {spec-id}
```

**Manual Task Discovery:**
```bash
# Find next task
sdd next-task {spec-id}

# Get task details
sdd task-info {spec-id} {task-id}

# Check dependencies
sdd check-deps {spec-id} {task-id}

# View progress
sdd progress {spec-id}
```

**Advanced Querying:**
```bash
# Query tasks by criteria
sdd query-tasks {spec-id} --status pending

# List blocked tasks
sdd list-blockers {spec-id}

# Check completion readiness
sdd check-complete {spec-id} --phase phase-2

```

**Project Analysis:**
```bash
# Detect project type
sdd detect-project

# Find tests
sdd find-tests

# Validate environment
sdd check-environment
```

## Summary

**Core Responsibility:**
Bridge specifications to implementation by identifying next tasks, gathering context, and creating detailed execution plans.

**Path Handling (IMPORTANT):**
- ✅ **Always uses absolute paths** - Works from any working directory
- ✅ **Enhanced discovery** - Checks multiple common locations automatically
- ✅ **Optional path parameter** - Can specify exact spec location
- ✅ **Early validation** - Fails fast with clear errors if paths not found

**Key Operations:**
- ✅ Find specifications in project
- ✅ Load JSON spec files (using Python for JSON parsing)
- ✅ Identify next actionable task (using Python tools)
- ✅ Gather task context and dependencies (using Python tools)
- ✅ Examine related files and patterns
- ✅ Create detailed execution plans
- ✅ Present plans for user approval
- ✅ Handle feedback and revisions
- ✅ Coordinate with Manager for status updates

**Integration Points:**
- Reads specs created by `Skill(sdd-toolkit:sdd-plan)`
- Updates status using sdd-update subagent
- Enables handoff to coding tools
- Coordinates multi-developer workflows

**Remember:** This skill's job is to make the transition from "what to do" (spec) to "how to do it" (execution plan) as smooth and clear as possible. Always ensure full context is gathered before creating a plan.

## See Also

**Skill(sdd-toolkit:sdd-plan)** - Use before this skill to:
- Create new specifications
- Define phases and tasks
- Generate initial spec files
- Set up the project structure

**sdd-update subagent** - Use alongside this skill to:
- Mark tasks as in_progress before implementing
- **Complete tasks** (atomically marks as completed AND creates journal entry - REQUIRES completion note)
- Mark tasks as blocked when encountering obstacles
- Document deviations and decisions during implementation
- Track progress and update metrics
- Journal verification results

**Important:** When completing tasks, you MUST provide a completion note/journal content describing what was accomplished.

Use via: `Task(subagent_type: "sdd-toolkit:sdd-update-subagent", prompt: "Complete task {task-id} in spec {spec-id}. Completion note: [what was done]", description: "...")`

---

*For creating specifications, use `Skill(sdd-toolkit:sdd-plan)`. For tracking progress, use the sdd-update subagent.*
