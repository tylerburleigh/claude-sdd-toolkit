# SDD CLI Functional Contracts

This document defines the functional contracts for SDD CLI commands that support semantic (compact) JSON output. These contracts specify what information each command provides, what decisions they enable, and when to include optional fields.

## What Are Functional Contracts?

Functional contracts define:
- **Purpose**: What the command does and why you'd use it
- **Required Fields**: Always present in the output
- **Optional Fields**: Conditionally included based on state
- **Decisions Enabled**: What actions the output helps you decide
- **Inclusion Conditions**: When optional fields appear

This ensures predictable, parseable output for automation and AI agents.

## Format Modes

All commands support two output modes when using `--json`:

### Verbose Mode (Phase 1 default)
- Includes emoji decorators (⚠️, ✅, 🚧, etc.)
- Human-readable formatting
- Best for interactive terminal use

### Compact Mode (Semantic/Machine-readable)
- No emoji decorators
- Plain text values
- Consistent structure
- Best for automation, CI/CD, and AI agents
- Enable with `--compact` flag (Phase 1) or default in Phase 2

## Core Commands

### 1. prepare-task

**Purpose**: Prepare complete context for task implementation by discovering the next actionable task, gathering dependencies, validating the spec, and checking git integration.

**Command Syntax**:
```bash
sdd prepare-task <spec-id> [task-id] [--json] [--compact]
```

**Required Fields**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "task_data": {
    "type": "task",
    "title": "Implement feature X",
    "status": "pending",
    "parent": "phase-2",
    "dependencies": {
      "blocks": [],
      "blocked_by": [],
      "depends": []
    }
  },
  "dependencies": {
    "task_id": "task-2-1",
    "can_start": true,
    "blocked_by": [],
    "soft_depends": [],
    "blocks": []
  },
  "spec_complete": false,
  "error": null
}
```

**Optional Fields**:

| Field | Inclusion Condition | Purpose |
|-------|-------------------|---------|
| `task_details` | Task has implementation details | Provides file paths, categories, estimates |
| `spec_file` | Spec file path is known | Reference to source spec JSON |
| `doc_context` | Codebase docs generated | Related files and context from doc-query |
| `validation_warnings` | Spec has non-critical issues | List of warnings (non-blocking) |
| `git_warnings` | Git drift detected | Warnings about branch/commit mismatches |
| `repo_root` | Git repo found | Path to repository root |
| `needs_branch_creation` | No branch in metadata | Flag to prompt for branch creation |
| `dirty_tree_status` | Git state checked | Working tree status (dirty/clean) |
| `suggested_branch_name` | Branch creation needed | Recommended branch name |
| `needs_commit_cadence` | No cadence preference set | Flag to prompt for commit preference |
| `commit_cadence_options` | Cadence prompt needed | Available cadence options |
| `suggested_commit_cadence` | Cadence prompt needed | Recommended cadence |
| `completion_info` | No actionable tasks | Details about spec completion |

**Decisions Enabled**:
- ✅ Which task to work on next
- ✅ Whether dependencies are satisfied
- ✅ If spec validation is needed
- ✅ Whether to create a git branch
- ✅ What commit cadence to use
- ✅ If spec is complete (ready for PR)

**Example - Task Found**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "task_data": {
    "type": "task",
    "title": "Create AuthService class",
    "status": "pending",
    "parent": "phase-2",
    "metadata": {
      "file_path": "src/services/authService.ts",
      "estimated_hours": 2
    }
  },
  "dependencies": {
    "can_start": true,
    "blocked_by": [],
    "blocks": ["task-2-2", "task-2-3"]
  },
  "validation_warnings": [],
  "git_warnings": [],
  "needs_branch_creation": true,
  "suggested_branch_name": "feat/user-auth",
  "spec_complete": false
}
```

**Example - Spec Complete**:
```json
{
  "success": true,
  "task_id": null,
  "spec_complete": true,
  "completion_info": {
    "is_complete": true,
    "ready_for_completion": true,
    "completed_tasks": 23,
    "total_tasks": 23,
    "message": "All tasks completed"
  }
}
```

---

### 2. task-info

**Purpose**: Get detailed information about a specific task including metadata, status, dependencies, and verification steps.

**Command Syntax**:
```bash
sdd task-info <spec-id> <task-id> [--json] [--compact]
```

**Required Fields**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "task_data": {
    "type": "task",
    "title": "Task title",
    "status": "pending",
    "parent": "phase-2"
  },
  "error": null
}
```

**Optional Fields**:

| Field | Inclusion Condition | Purpose |
|-------|-------------------|---------|
| `metadata` | Task has metadata | File paths, estimates, categories, details |
| `dependencies` | Task has deps | Lists blocked_by, blocks, depends arrays |
| `children` | Task has children | List of child task IDs |
| `verification_steps` | Task is verify type | Steps to verify completion |
| `risk_notes` | Task has risk notes | Risk mitigation information |
| `completed_at` | Task is completed | Completion timestamp |
| `started_at` | Task is in_progress | Start timestamp |

**Decisions Enabled**:
- ✅ Whether to start this specific task
- ✅ What files need to be modified
- ✅ How long the task should take
- ✅ What verification is required
- ✅ What risks to be aware of

**Example**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "task_data": {
    "type": "task",
    "title": "Create AuthService class",
    "status": "pending",
    "parent": "phase-2",
    "metadata": {
      "file_path": "src/services/authService.ts",
      "estimated_hours": 2,
      "task_category": "implementation",
      "details": "Implement JWT-based authentication service"
    },
    "dependencies": {
      "blocked_by": [],
      "blocks": ["task-2-2", "task-2-3"],
      "depends": ["task-1-5"]
    }
  }
}
```

---

### 3. check-deps

**Purpose**: Analyze task dependencies to determine if a task is ready to start and what it blocks.

**Command Syntax**:
```bash
sdd check-deps <spec-id> <task-id> [--json] [--compact]
```

**Required Fields**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "can_start": true,
  "blocked_by": [],
  "soft_depends": [],
  "blocks": [],
  "error": null
}
```

**Optional Fields**:

| Field | Inclusion Condition | Purpose |
|-------|-------------------|---------|
| `blocking_details` | Task is blocked | Details about each blocking dependency |
| `impact_count` | Task blocks others | Number of tasks that depend on this one |
| `critical_path` | On critical path | Flag indicating path criticality |

**Decisions Enabled**:
- ✅ Can I start this task now?
- ✅ What's blocking this task?
- ✅ What other tasks depend on this?
- ✅ Is this on the critical path?

**Example - Ready to Start**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "can_start": true,
  "blocked_by": [],
  "soft_depends": [],
  "blocks": ["task-2-2", "task-2-3"],
  "impact_count": 2
}
```

**Example - Blocked**:
```json
{
  "success": true,
  "task_id": "task-2-3",
  "can_start": false,
  "blocked_by": [
    {
      "task_id": "task-2-1",
      "title": "Create AuthService",
      "status": "in_progress"
    }
  ],
  "soft_depends": [],
  "blocks": []
}
```

---

### 4. progress

**Purpose**: Track overall spec progress including phase completion, task counts, and completion percentage.

**Command Syntax**:
```bash
sdd progress <spec-id> [--json] [--compact]
```

**Required Fields**:
```json
{
  "success": true,
  "spec_id": "user-auth-2025-10-24-001",
  "title": "User Authentication System",
  "total_tasks": 23,
  "completed_tasks": 15,
  "percentage": 65,
  "status": "in_progress",
  "error": null
}
```

**Optional Fields**:

| Field | Inclusion Condition | Purpose |
|-------|-------------------|---------|
| `phases` | Spec has phases | Array of phase progress summaries |
| `by_status` | Multiple statuses exist | Task counts by status |
| `current_phase` | Has active phase | ID of current phase being worked on |
| `next_phase` | Has upcoming phase | ID of next phase to start |
| `estimated_hours_total` | Tasks have estimates | Sum of all estimated hours |
| `estimated_hours_remaining` | Has pending tasks with estimates | Hours left to complete |
| `started_at` | Spec has start timestamp | When work began |
| `last_updated` | Spec has been modified | Last modification timestamp |

**Decisions Enabled**:
- ✅ How far along is the spec?
- ✅ Which phase are we in?
- ✅ How many tasks remain?
- ✅ What's the time estimate to completion?
- ✅ Is the spec ready for review/PR?

**Example**:
```json
{
  "success": true,
  "spec_id": "user-auth-2025-10-24-001",
  "title": "User Authentication System",
  "total_tasks": 23,
  "completed_tasks": 15,
  "percentage": 65,
  "status": "in_progress",
  "by_status": {
    "completed": 15,
    "in_progress": 3,
    "pending": 5,
    "blocked": 0
  },
  "phases": [
    {
      "phase_id": "phase-1",
      "title": "Foundation",
      "completed": 8,
      "total": 8,
      "percentage": 100
    },
    {
      "phase_id": "phase-2",
      "title": "Core Implementation",
      "completed": 7,
      "total": 15,
      "percentage": 47
    }
  ],
  "current_phase": "phase-2",
  "estimated_hours_total": 46,
  "estimated_hours_remaining": 16
}
```

---

### 5. next-task

**Purpose**: Find the next actionable task from a spec, considering dependencies and priorities.

**Command Syntax**:
```bash
sdd next-task <spec-id> [--json] [--compact]
```

**Required Fields**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "error": null
}
```

**Optional Fields**:

| Field | Inclusion Condition | Purpose |
|-------|-------------------|---------|
| `task_data` | Task found | Full task details |
| `reason` | Why this task chosen | Explanation of selection logic |
| `alternatives` | Other tasks available | List of other actionable tasks |
| `phase_info` | Task has parent phase | Phase context |
| `priority` | Task has priority metadata | Priority level (high/medium/low) |

**Decisions Enabled**:
- ✅ What should I work on next?
- ✅ Why was this task chosen?
- ✅ Are there alternative tasks?
- ✅ What phase is this task in?

**Example - Task Found**:
```json
{
  "success": true,
  "task_id": "task-2-1",
  "task_data": {
    "type": "task",
    "title": "Create AuthService",
    "status": "pending",
    "parent": "phase-2"
  },
  "reason": "First pending task in current phase",
  "alternatives": ["task-2-7", "task-4-1"],
  "phase_info": {
    "phase_id": "phase-2",
    "title": "Core Implementation",
    "order": 2
  }
}
```

**Example - No Tasks Available**:
```json
{
  "success": false,
  "task_id": null,
  "error": "No actionable tasks available - 3 tasks blocked, 2 in progress"
}
```

---

## Using Contracts in Automation

### Example 1: Check if Task is Ready

```bash
#!/bin/bash
SPEC_ID="user-auth-2025-10-24-001"
TASK_ID="task-2-3"

# Check dependencies (compact mode for parsing)
DEPS=$(sdd check-deps $SPEC_ID $TASK_ID --json --compact)

CAN_START=$(echo "$DEPS" | jq -r '.can_start')

if [ "$CAN_START" = "true" ]; then
  echo "Task is ready to start!"
  # Create execution plan, begin implementation
else
  echo "Task is blocked. Blocked by:"
  echo "$DEPS" | jq -r '.blocked_by[].task_id'
fi
```

### Example 2: Monitor Progress and Create PR When Done

```bash
#!/bin/bash
SPEC_ID="user-auth-2025-10-24-001"

# Get progress (compact mode)
PROGRESS=$(sdd progress $SPEC_ID --json --compact)

PERCENTAGE=$(echo "$PROGRESS" | jq -r '.percentage')

if [ "$PERCENTAGE" -eq 100 ]; then
  echo "Spec is complete! Creating PR..."
  # Trigger PR creation workflow
  gh pr create --fill
else
  echo "Progress: $PERCENTAGE%"
  REMAINING=$(echo "$PROGRESS" | jq -r '.estimated_hours_remaining')
  echo "Estimated hours remaining: $REMAINING"
fi
```

### Example 3: Autonomous Task Loop

```bash
#!/bin/bash
SPEC_ID="user-auth-2025-10-24-001"

while true; do
  # Prepare next task
  PREP=$(sdd prepare-task $SPEC_ID --json --compact)

  SUCCESS=$(echo "$PREP" | jq -r '.success')
  SPEC_COMPLETE=$(echo "$PREP" | jq -r '.spec_complete')

  if [ "$SPEC_COMPLETE" = "true" ]; then
    echo "Spec complete!"
    break
  fi

  if [ "$SUCCESS" = "false" ]; then
    echo "No actionable tasks. Exiting."
    break
  fi

  TASK_ID=$(echo "$PREP" | jq -r '.task_id')
  echo "Working on: $TASK_ID"

  # Execute task implementation
  # ... (implementation logic) ...

  # Mark complete and continue
  sdd update complete $SPEC_ID $TASK_ID "Implemented feature"
done
```

---

## Field Stability Guarantees

### Stable Fields (Never Removed)

These fields will always be present in future versions:

**All Commands**:
- `success` (boolean)
- `error` (string | null)

**prepare-task**:
- `task_id` (string | null)
- `task_data` (object | null)
- `dependencies` (object | null)
- `spec_complete` (boolean)

**task-info**:
- `task_id` (string)
- `task_data` (object)

**check-deps**:
- `task_id` (string)
- `can_start` (boolean)
- `blocked_by` (array)
- `blocks` (array)

**progress**:
- `spec_id` (string)
- `total_tasks` (number)
- `completed_tasks` (number)
- `percentage` (number)

**next-task**:
- `task_id` (string | null)

### Conditional Fields (May Change)

Optional fields listed in each command section above may be added or removed in future versions as features evolve. Always check for field existence before accessing.

### Deprecated Fields

None currently. Future deprecations will follow this process:
1. Mark field as deprecated in docs
2. Maintain field for 2 minor versions
3. Remove in next major version

---

## Version History

### v1.0 (Phase 1)
- Initial contract documentation
- Compact mode opt-in via `--compact` flag
- All 5 core commands supported

### v2.0 (Phase 2) - Planned
- Compact mode becomes default for `--json`
- Verbose mode via `--verbose` flag
- No breaking changes to field names or structure
