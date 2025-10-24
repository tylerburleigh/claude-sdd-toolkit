---
name: sdd-update
description: Progress tracking for spec-driven development. Use to update task status, track progress, journal decisions, move specs between folders, and maintain spec files. Handles the administrative/clerical aspects of specification documents during development.
---

# Spec-Driven Development: Update Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-plan)** - Creates specifications and task hierarchies
- **Skill(sdd-next)** - Identifies next tasks and creates execution plans
- **Skill(sdd-update)** (this skill) - Tracks progress and maintains documentation

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
│                   task, creates     execution plan   journals in │
│                   execution plan                      JSON       │
│       │               │                  │                │      │
│       └───────────────┴──────────────────┴────────────────┘      │
│                              │                                    │
│                         [Cycle repeats]                          │
│                                                                   │
│  Note: Implementation can be done by human developers,           │
│        Claude with coding tools, or other AI assistants          │
└─────────────────────────────────────────────────────────────────┘
```

**Your Role (UPDATE)**: Maintain accurate documentation of progress, decisions, and status throughout the implementation lifecycle by updating the JSON spec file.

## Core Philosophy

**Document Reality**: JSON spec files are living documents that evolve during implementation. This skill ensures the JSON spec file accurately reflects current progress, decisions, and status. All changes are tracked and documented within the JSON structure.

**Key Capabilities:**
- Update task and phase status in JSON spec files
- Calculate and update progress indicators
- Add journal entries for decisions and deviations (stored in JSON)
- Detect and track missing journal entries automatically
- Bulk journal completed tasks in one operation
- Move JSON spec files between lifecycle folders (active/completed/archived)
- Update spec metadata fields in JSON
- Maintain JSON spec file consistency and integrity
- Document verification results in JSON
- Track time and progress metrics
- Manage spec versioning and revisions

## Core Philosophy

**Document Reality**: JSON spec files are living documents that evolve during implementation. This skill ensures the JSON spec file accurately reflects current progress, decisions, and status. All changes are tracked and documented within the JSON structure.

**Key Capabilities:**
- Update task and phase status in JSON spec files
- Calculate and update progress indicators
- Add journal entries for decisions and deviations (stored in JSON)
- Detect and track missing journal entries automatically
- Bulk journal completed tasks in one operation
- Move JSON spec files between lifecycle folders (active/completed/archived)
- Update spec metadata fields in JSON
- Maintain JSON spec file consistency and integrity
- Document verification results in JSON
- Track time and progress metrics
- Manage spec versioning and revisions

## File Structure

- **JSON spec file** (`specs/active/{spec-id}.json`) - Single source of truth containing:
  - Task hierarchy and status
  - Progress tracking
  - Journal entries
  - Verification results
  - All metadata

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (update-status, add-journal, complete-spec, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd` CLI wrapper commands (e.g., `sdd update-status`, `sdd add-journal`, `sdd complete-spec`)
- ❌ **DO NOT**: Execute Python scripts directly or manipulate JSON files directly (e.g., `python sdd_update.py`, direct JSON editing via scripts)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. All update operations should go through the CLI for consistency.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## Quick Reference: Common Operations

This table shows the most frequently used commands:

| Operation | CLI Command | Notes |
|-----------|-------------|-------|
| Update task status | `sdd update-status {spec-id} {task-id} {status}` | Status: pending, in_progress, completed, blocked. Use `--verify` to auto-run verify tasks on completion |
| Add journal entry | `sdd add-journal {spec-id} --title "..." --content "..."` | Use `--task-id` to link to specific task |
| Mark task blocked | `sdd mark-blocked {spec-id} {task-id} --reason "..." --type {type}` | Types: dependency, technical, resource, decision |
| Unblock task | `sdd unblock-task {spec-id} {task-id} --resolution "..."` | Documents resolution and updates status |
| Execute verification | `sdd execute-verify {spec-id} {verify-id}` | Automatically runs verification task based on metadata |
| Add verification | `sdd add-verification {spec-id} {verify-id} {status}` | Status: PASSED, FAILED, PARTIAL |
| Track time | `sdd track-time {spec-id} {task-id} --actual {hours}` | Records actual hours spent |
| Update metadata | `sdd update-frontmatter {spec-id} {key} "{value}"` | Updates spec-level metadata fields |
| Get status report | `sdd status-report {spec-id}` | Shows overall progress and status |
| Complete spec | `sdd complete-spec {spec-id} --actual-hours {hours}` | Marks complete and moves to completed/ |

## Quick Start

All operations use the `sdd` command. Here's a typical workflow:

```bash
# 1. Start working on a task
sdd update-status user-auth-001 task-1-2 in_progress

# 2. Complete the task
sdd update-status user-auth-001 task-1-2 completed --note "Implemented User model"

# 3. Add a journal entry (if deviations occurred)
sdd add-journal user-auth-001 --title "Database Change" --content "Switched to UUID primary keys" --task-id task-1-2

# 4. Check overall progress
sdd status-report user-auth-001

# 5. When all tasks done, complete the spec
sdd complete-spec user-auth-001 --actual-hours 18.5
```

**Tip**: Use `--dry-run` flag to preview changes before applying them.

For comprehensive command list, see Command Reference below.

### Command Reference

**Status Management:**
- `update-status` - Change task status (pending/in_progress/completed/blocked)
- `mark-blocked` - Mark task as blocked with reason and ticket
- `unblock-task` - Unblock a task with resolution notes

**Documentation:**
- `add-journal` - Add implementation journal entry to spec
- `bulk-journal` - Add journal entries for multiple completed tasks at once
- `check-journaling` - Detect completed tasks without journal entries
- `update-frontmatter` - Update spec metadata fields
- `sync-metadata` - Synchronize spec metadata with hierarchy data
- `add-verification` - Document verification results

**Lifecycle:**
- `move-spec` - Move spec between folders (active/completed/archived)
- `complete-spec` - Mark spec complete and move to completed/

**Time Tracking:**
- `track-time` - Record actual time spent on task
- `time-report` - Generate time analysis report
- `phase-time` - Calculate time breakdown for a specific phase

**Validation & Reporting:**
- `validate-spec` - Check spec file consistency
- `status-report` - Get progress and status summary
- `audit-spec` - Deep audit of spec file integrity

**Query & Filtering:**
- `query-tasks` - Filter tasks by status, type, or parent
- `get-task` - Get detailed information about a specific task
- `list-phases` - List all phases with progress
- `check-complete` - Verify if spec/phase is ready to complete
- `list-blockers` - List all currently blocked tasks

**Common Flags:**
- `--dry-run` - Preview changes without saving
- `--json` - Output as JSON for scripting
- `--path` - Specify specs directory location
- `--verbose` - Show detailed operation logs
- `--quiet` - Minimal output (suppress non-essential messages)

## When to Use This Skill

Use `Skill(sdd-update)` to:
- Mark tasks as in_progress, completed, or blocked
- Update progress percentages across the hierarchy
- Document why a task is blocked or delayed
- Record deviations from the original plan
- Journal important implementation decisions
- Move a completed spec to the completed folder
- Archive old or superseded specs
- Update estimated vs actual time tracking
- Record verification results in the spec
- Update spec metadata fields (status, owner, etc.)

**Do NOT use for:**
- Creating new specifications (use Skill(sdd-plan))
- Writing code or implementing features
- Running tests or verification commands
- Making technical decisions about architecture
- Planning new phases or tasks (use Skill(sdd-plan))
- Finding what to work on next (use Skill(sdd-next))
- Creating execution plans (use Skill(sdd-next))

## Skill Handoff Points

**When to transition to other skills:**

← **From Skill(sdd-next)**:
  - After execution plan is approved, mark task as in_progress
  - Before beginning implementation
  - To update status during implementation

← **From Implementation**:
  - After task is completed, mark as completed
  - When encountering blockers, document the issue
  - When making deviations, journal the decision

→ **To Skill(sdd-next)**:
  - After marking task complete, find next task
  - After resolving blocker, resume implementation
  - After updating progress, continue development

→ **To Skill(sdd-plan)**:
  - When major spec restructuring is needed
  - When adding entirely new phases
  - When spec needs complete regeneration

## Decision Tree: Which Skill to Use?

```
What do you need to do?
├─ Create a new spec → Use `Skill(sdd-plan)`
├─ Find next task → Use `Skill(sdd-next)`
├─ Create execution plan → Use `Skill(sdd-next)`
├─ Update task status → Use `Skill(sdd-update)` (this skill)
├─ Journal a decision → Use `Skill(sdd-update)` (this skill)
├─ Move spec to completed → Use `Skill(sdd-update)` (this skill)
├─ Document blocker → Use `Skill(sdd-update)` (this skill)
└─ Track progress → Use `Skill(sdd-update)` (this skill)

Task Status Changes:
├─ Starting work on task → Mark as in_progress (this skill)
├─ Task completed → Mark as completed (this skill)
├─ Task blocked → Mark as blocked and document (this skill)
└─ Resuming blocked task → Update status to in_progress (this skill)
```

## Document Operations

### Operation 1: Update Task Status

Update the status of tasks in the spec file as work progresses.

#### 1.1 Load Current State

**Steps:**
1. Get the `spec_id` from the JSON spec file name or metadata
2. Load spec file from `specs/active/{spec-id}.json`
3. Parse JSON and validate structure

**Example:**
```bash
# Spec file name contains the spec_id
# File: user-auth-001.json
# Spec ID: user-auth-001

# Load the JSON spec file
cat specs/active/user-auth-001.json
```

#### 1.2 Update Node Status

**Status Values:**
- `pending` - Not yet started
- `in_progress` - Currently being worked on
- `completed` - Successfully finished
- `blocked` - Cannot proceed due to dependencies or issues

**Update Pattern:**
```json
{
  "task-1-2": {
    "status": "in_progress",  // Changed from "pending"
    "metadata": {
      "started_at": "2025-10-18T14:30:00Z",
      "notes": "Started implementing password hashing"
    }
  }
}
```

**Rules:**
- Only update tasks you're responsible for
- Always update `last_updated` timestamp at root
- Include notes explaining status changes
- Recalculate parent progress after changes

#### 1.3 Update Task Status

The CLI handles backups, validation, and automatic progress recalculation up the hierarchy.

**Mark task as in_progress:**
```bash
sdd update-status user-auth-001 task-1-2 in_progress --note "Starting User model implementation"
```

**Mark task as completed:**
```bash
sdd update-status user-auth-001 task-1-2 completed --note "User model finished and tested"
```

**Preview changes (dry-run):**
```bash
sdd update-status user-auth-001 task-1-2 completed --note "User model finished" --dry-run
```

**Mark as completed with automatic verification:**
```bash
sdd update-status user-auth-001 task-1-2 completed --note "User model finished" --verify
```

The `--verify` flag automatically runs associated verify tasks after marking the task as completed. If any verify task fails, the task status reverts to `in_progress`. This ensures quality gates are enforced before marking tasks complete.

### Operation 2: Journal Decisions and Deviations

Document important decisions, deviations from spec, or blockers by adding entries to the JSON spec file.

#### 2.1 Add Implementation Journal Entry

Add a timestamped entry to the JSON spec file tracking implementation progress, decisions, and deviations.

**Location in JSON Spec File:**

Journal entries are stored in a top-level `journal` array in the JSON spec file:

```json
{
  "spec_id": "user-auth-001",
  "generated": "2025-10-18T10:00:00Z",
  "last_updated": "2025-10-18T16:20:00Z",

  "journal": [
    {
      "timestamp": "2025-10-18T14:30:00Z",
      "entry_type": "status_change",
      "title": "Task 1-2 Started",
      "task_id": "task-1-2",
      "author": "claude-sonnet-4.5",
      "content": "Beginning password hashing implementation in User model.",
      "metadata": {
        "status": "in_progress"
      }
    },
    {
      "timestamp": "2025-10-18T15:45:00Z",
      "entry_type": "deviation",
      "title": "Deviation from Plan",
      "task_id": "task-2-1",
      "author": "claude-sonnet-4.5",
      "content": "Created new file src/services/authService.ts instead of modifying src/services/userService.ts. Auth logic was too complex to mix with user CRUD operations. Separation of concerns improves maintainability.",
      "metadata": {
        "original_plan": "Modify src/services/userService.ts",
        "actual_change": "Created new file src/services/authService.ts",
        "impact": "None on external API; internal refactoring only",
        "approved_by": "Team lead (Slack discussion)"
      }
    },
    {
      "timestamp": "2025-10-18T16:20:00Z",
      "entry_type": "blocker",
      "title": "Blocker Encountered",
      "task_id": "task-3-1",
      "author": "claude-sonnet-4.5",
      "content": "Cannot implement session management without Redis connection. DevOps team needs to provision Redis instance.",
      "metadata": {
        "blocker_type": "dependency",
        "blocked_by": "Missing dependency - Redis client not configured",
        "action_required": "DevOps team needs to provision Redis instance",
        "ticket": "OPS-1234"
      }
    }
  ],

  "hierarchy": {
    ...
  }
}
```

**Journal Entry Structure:**
```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",    // ISO 8601 timestamp
  "entry_type": "status_change|deviation|blocker|decision|note",
  "title": "Brief title",                  // Human-readable summary
  "task_id": "task-N-M",                  // Related task (optional)
  "author": "tool-or-developer-name",     // Who made this entry
  "content": "Detailed explanation",       // Main journal content
  "metadata": {                            // Optional additional fields
    // Entry-type specific fields
  }
}
```

**Entry Types:**
- `status_change` - Task status updates
- `deviation` - Deviations from original plan
- `blocker` - Encountered blockers
- `decision` - Important implementation decisions
- `note` - General notes and observations

#### 2.2 Update Spec Revision History

When significant changes occur, update the revision log in the JSON spec file metadata.

**Original Revisions (in JSON):**
```json
{
  "spec_id": "user-auth-001",
  "metadata": {
    "version": "1.0",
    "revisions": [
      {
        "version": "1.0",
        "date": "2025-10-18T10:30:00Z",
        "author": "claude-code",
        "changes": "Initial spec creation"
      }
    ]
  },
  "hierarchy": {...}
}
```

**After Deviation:**
```json
{
  "spec_id": "user-auth-001",
  "metadata": {
    "version": "1.1",
    "revisions": [
      {
        "version": "1.0",
        "date": "2025-10-18T10:30:00Z",
        "author": "claude-code",
        "changes": "Initial spec creation"
      },
      {
        "version": "1.1",
        "date": "2025-10-18T15:45:00Z",
        "author": "claude-code",
        "changes": "Split auth logic into separate service file; updated Phase 2 tasks"
      }
    ]
  },
  "hierarchy": {...}
}
```

**When to Increment Version:**
- Major structural changes to phases
- Adding or removing files from the plan
- Significant scope changes
- Architecture decisions that alter the approach

**Increment Rules:**
- Minor changes (1.0 → 1.1): Task-level adjustments
- Major changes (1.0 → 2.0): Phase-level restructuring

#### 2.3 Add Journal Entries

**Add a journal entry:**
```bash
sdd add-journal user-auth-001 --title "Deviation: Split Auth Logic" --content "Created authService.ts instead of adding to userService.ts. Improves separation of concerns." --task-id task-2-1 --entry-type deviation
```

**Update spec metadata:**
```bash
# Change status in metadata
sdd update-frontmatter user-auth-001 status "active"

# Update owner
sdd update-frontmatter user-auth-001 owner "alice@company.com"

# Preview change
sdd update-frontmatter user-auth-001 priority "high" --dry-run
```

#### 2.4 Automatic Journaling Detection and Bulk Operations

sdd-update automatically tracks which completed tasks need journal entries.

**How It Works:**
- When marking a task as `completed`, a `needs_journaling: true` flag is set in metadata
- When adding a journal entry with `--task-id`, the flag is automatically cleared
- The `status-report` command shows warnings about unjournaled tasks
- You get a reminder message when marking tasks complete

**Detect unjournaled tasks:**
```bash
sdd check-journaling user-auth-001
```

**Output example:**
```
Found 3 completed task(s) without journal entries:

1. task-1-2: User Model Implementation
   Completed: 2025-10-18 14:30

2. task-2-1: Authentication Service
   Completed: 2025-10-18 16:45

3. task-3-3: Session Management
   Completed: 2025-10-19 09:15

To journal these tasks, run:
  bulk-journal user-auth-001 <spec-file>
```

**Bulk journal all unjournaled tasks:**
```bash
# Journal all unjournaled tasks at once
sdd bulk-journal user-auth-001

# Journal specific tasks only
sdd bulk-journal user-auth-001 --tasks task-1-2,task-2-1

# Preview what will be journaled
sdd bulk-journal user-auth-001 --dry-run
```

**Best Practice Workflow:**
1. Mark tasks complete as you go - flags set automatically
2. Periodically run `status-report` to see unjournaled count
3. Run `check-journaling` to see the list
4. Run `bulk-journal` to document all at once
5. Flags cleared automatically when journaled

### Operation 3: Document Verification Results

Record the results of verification steps in the JSON spec file.

#### 3.1 Add Verification Results to JSON

For each verification task, add results to its metadata in the JSON hierarchy.

**Location:** Within the verification task node in the hierarchy:

```json
{
  "hierarchy": {
    "verify-1-1": {
      "type": "verify",
      "title": "Migration runs without errors",
      "status": "completed",
      "parent": "phase-1-verify",
      "children": [],
      "total_tasks": 1,
      "completed_tasks": 1,
      "metadata": {
        "verification_type": "auto",
        "command": "npm run migrate",
        "expected": "Migration completes successfully",
        "verification_result": {
          "date": "2025-10-18T16:45:00Z",
          "status": "PASSED",
          "output": "Running migration 001_add_users.sql...\n✓ Table users created\n✓ Indexes created\n✓ Migration completed in 245ms",
          "notes": "All migrations ran cleanly. Performance acceptable.",
          "executed_by": "claude-sonnet-4.5"
        }
      }
    },
    "verify-1-2": {
      "type": "verify",
      "title": "Type checking passes",
      "status": "completed",
      "parent": "phase-1-verify",
      "children": [],
      "total_tasks": 1,
      "completed_tasks": 1,
      "metadata": {
        "verification_type": "auto",
        "command": "npm run type-check",
        "expected": "No TypeScript errors",
        "verification_result": {
          "date": "2025-10-18T16:47:00Z",
          "status": "PASSED",
          "output": "Checking types...\n✓ 0 errors found",
          "notes": "All type definitions correct.",
          "executed_by": "claude-sonnet-4.5"
        }
      }
    }
  }
}
```

**Verification Result Structure:**
```json
{
  "verification_result": {
    "date": "YYYY-MM-DDTHH:MM:SSZ",      // ISO 8601 timestamp
    "status": "PASSED|FAILED|PARTIAL",   // Verification outcome
    "command": "command executed",       // For automated verifications
    "output": "command output",          // Captured output
    "issues_found": [],                  // Array of issues (if any)
    "notes": "Additional context",       // Human notes
    "executed_by": "tool-or-person"      // Who ran the verification
  }
}
```

**Creating Verification Summaries:**

When documenting multiple verification results, use the `format-verification-summary` command to ensure proper formatting:

```bash
# Create JSON with verification results
cat > /tmp/verifications.json <<EOF
[
  {
    "verify_id": "verify-1-1",
    "title": "Dependencies Install",
    "status": "PASSED",
    "command": "pip install -r requirements.txt",
    "result": "All packages installed successfully",
    "notes": "No conflicts detected"
  },
  {
    "verify_id": "verify-1-2",
    "title": "Configuration Loads",
    "status": "PASSED",
    "command": "python -c \"from app.config import settings; print(settings.langchain_cache_enabled)\"",
    "result": "True"
  }
]
EOF

# Format the summary
sdd format-verification-summary --json-file /tmp/verifications.json
```

**IMPORTANT**: The `format-verification-summary` command returns pre-formatted text with proper newlines and indentation. Display this output EXACTLY as returned - do not reformat or modify it.

#### 3.2 Update Spec File with Verification Status

Mark verification tasks as completed in spec file:

```json
{
  "verify-1-1": {
    "status": "completed",
    "completed_tasks": 1,
    "metadata": {
      "verification_type": "auto",
      "verification_command": "npm run migrate",
      "completed_at": "2025-10-18T16:45:00Z",
      "result": "passed",
      "notes": "Migration successful, 245ms execution time"
    }
  }
}
```

#### 3.3 Add Verification Results

**Add verification result to JSON spec:**
```bash
# Verification passed
sdd add-verification user-auth-001 verify-1-1 PASSED --command "npm run migrate" --output "✓ Migration completed in 245ms" --notes "All tables and indexes created successfully"

# Verification failed
sdd add-verification user-auth-001 verify-1-2 FAILED --command "npm run type-check" --output "Error: Type mismatch in User.ts:42" --issues "Missing return type annotation" --notes "Need to add explicit return types"

# Partial success
sdd add-verification user-auth-001 verify-1-3 PARTIAL --command "npm test" --output "10/12 tests passed" --issues "2 edge case tests failing"
```

#### 3.4 Execute Verification Tasks Automatically

**Automatically run verification tasks based on their metadata:**

If a verification task has metadata specifying a `skill` (like `run-tests`) or a `command`, you can execute it automatically:

```bash
# Execute verification task automatically
sdd execute-verify user-auth-001 verify-1-1

# Execute and automatically record the result
sdd execute-verify user-auth-001 verify-1-1 --record
```

**Requirements:**

The verification task must have metadata in the JSON spec specifying how to execute it:

```json
{
  "verify-1-1": {
    "title": "Run unit tests",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "skill": "run-tests",
      "command": "run tests/auth/"
    }
  }
}
```

**Supported execution methods:**

1. **Skill-based** (recommended): Set `"skill": "run-tests"` to use the Skill(run-tests) skill
2. **Command-based**: Set `"command": "pytest tests/"` to run any shell command

**Output:**

- Shows execution output, duration, and pass/fail status
- With `--record` flag: Automatically records the result to the JSON spec
- Captures errors and issues for failed verifications

#### 3.5 Configurable Failure Handling with on_failure

Verification tasks can specify custom failure handling behavior using the `on_failure` metadata field. This enables intelligent error recovery, retry logic, and automated remediation.

**on_failure Configuration Structure:**

```json
{
  "verify-1-1": {
    "title": "Run unit tests",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "skill": "run-tests",
      "command": "run tests/auth/",
      "on_failure": {
        "consult": true,
        "revert_status": "in_progress",
        "max_retries": 2,
        "notify": "log",
        "continue_on_failure": false
      }
    }
  }
}
```

**on_failure Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `consult` | boolean | `false` | Whether to recommend AI consultation for debugging |
| `revert_status` | string | `"in_progress"` | Status to revert parent task to on failure (`"pending"`, `"in_progress"`, or `"blocked"`) |
| `max_retries` | integer | `0` | Maximum number of automatic retry attempts (0-5) |
| `notify` | string | `"log"` | Notification method (`"log"`, `"email"`, `"slack"`, `"none"`) |
| `continue_on_failure` | boolean | `false` | Whether to continue with other verifications if this one fails |

**Example 1: Retry Logic with AI Consultation**

```json
{
  "verify-1-1": {
    "title": "Integration tests pass",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "skill": "run-tests",
      "command": "run tests/integration/",
      "on_failure": {
        "consult": true,
        "max_retries": 2,
        "revert_status": "in_progress"
      }
    }
  }
}
```

When this verification fails:
1. Automatically retries up to 2 times with 1-second delays
2. If all retries fail, reverts parent task to `in_progress`
3. Recommends AI consultation for debugging
4. Logs all actions taken

**Example 2: Continue on Failure**

```json
{
  "verify-1-1": {
    "title": "Check code style",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "skill": "run-tests",
      "command": "run lint",
      "on_failure": {
        "continue_on_failure": true,
        "revert_status": "in_progress",
        "notify": "log"
      }
    }
  },
  "verify-1-2": {
    "title": "Run unit tests",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "skill": "run-tests",
      "command": "run tests/unit/",
      "on_failure": {
        "continue_on_failure": false,
        "consult": true
      }
    }
  }
}
```

When using `--verify` flag:
- If `verify-1-1` (linting) fails, execution continues to `verify-1-2`
- If `verify-1-2` (tests) fails, execution stops immediately
- Parent task reverts to `in_progress` if any verification fails

**Example 3: Custom Revert Status**

```json
{
  "verify-1-1": {
    "title": "Check external API availability",
    "type": "verify",
    "metadata": {
      "verification_type": "auto",
      "command": "curl https://api.example.com/health",
      "on_failure": {
        "revert_status": "blocked",
        "notify": "slack",
        "consult": false
      }
    }
  }
}
```

When this verification fails:
- Reverts parent task to `blocked` (not `in_progress`)
- Sends notification via Slack
- Does not recommend AI consultation (external dependency)

**Using on_failure with --verify Flag:**

```bash
# The --verify flag automatically uses on_failure configuration
sdd update-status user-auth-001 task-1-1 completed --verify

# Output shows on_failure actions:
# ✓ verify-1-1 passed (succeeded after 1 retry)
# ✗ verify-1-2 failed
#   Actions: Retrying (attempt 1/2), Notification: log, AI consultation recommended
# Task task-1-1 reverted to 'in_progress' due to verification failure
# 💡 AI consultation recommended - consider using run-tests skill for debugging
```

**Best Practices:**

1. **Use retry for flaky tests**: Set `max_retries: 1-2` for tests that occasionally fail due to timing
2. **AI consultation for bugs**: Set `consult: true` for failures that need debugging
3. **Custom revert status**: Use `"blocked"` for external dependencies, `"in_progress"` for fixable issues
4. **Continue on warnings**: Set `continue_on_failure: true` for non-critical checks like linting
5. **Stop on critical failures**: Set `continue_on_failure: false` (default) for essential tests

### Operation 4: Move Specs Between Lifecycle Stages

Organize JSON spec files by their lifecycle status.

#### 4.1 Folder Structure

**JSON spec files** are the only required files and move between lifecycle folders:

```
specs/
├── active/              # Currently being implemented
│   ├── user-auth-001.json
│   └── api-refactor-001.json
├── completed/           # Finished and verified
│   ├── user-profiles-001.json
│   └── database-migration-001.json
└── archived/            # Old or superseded
    └── legacy-auth-001.json
```

**Optional markdown views** (generated via `render-spec`) can exist alongside JSON:

```
specs/
├── active/
│   ├── user-auth-001.json      # Source of truth
│   └── user-auth-001.md        # Optional generated view
├── completed/
│   └── user-profiles-001.json  # Source of truth only
```

**Important:**
- Only JSON files are required and tracked
- Markdown views are optional artifacts for human readability
- Lifecycle operations move JSON files (markdown can be regenerated anytime)

#### 4.2 Move to Completed

When all phases are verified and complete, use the CLI to complete the spec:

**Verify and complete:**
```bash
# Verify all tasks complete
sdd check-complete user-auth-001

# Complete spec (updates metadata and moves to completed/)
sdd complete-spec user-auth-001 --actual-hours 14
```

**Result - JSON Metadata After Completion:**
```json
{
  "spec_id": "user-auth-001",
  "metadata": {
    "status": "completed",
    "completed_date": "2025-10-18T18:00:00Z",
    "actual_hours": 14
  }
}
```

#### 4.3 Archive Superseded Specs

When a spec is replaced or no longer relevant, use the CLI to archive it:

**Archive a spec:**
```bash
# Move spec to archived folder
sdd move-spec legacy-auth-001 archived
```

**Result - JSON Metadata for Archived Spec:**
```json
{
  "spec_id": "legacy-auth-001",
  "metadata": {
    "status": "archived",
    "archived_date": "2025-10-18T18:00:00Z",
    "archived_reason": "Replaced by new OAuth2 implementation (user-auth-v2)",
    "superseded_by": "user-auth-v2-001"
  }
}
```

### Operation 5: Update Spec Metadata

Modify JSON spec file metadata as the project evolves.

#### 5.1 Common Metadata Updates

**Status Changes (in JSON):**
```json
{
  "metadata": {
    // Draft → Approved
    "status": "approved",  // was "draft"

    // Approved → Active
    "status": "active",    // was "approved"
    "started_date": "2025-10-18T10:00:00Z",

    // Active → Completed
    "status": "completed", // was "active"
    "completed_date": "2025-10-18T18:00:00Z",
    "actual_hours": 14,    // vs estimated_hours: 16
    "time_variance": -2
  }
}
```

**Owner/Reviewer Changes:**
```json
{
  "metadata": {
    "owner": "alice@company.com",  // was null
    "reviewers": ["bob@company.com", "charlie@company.com"]  // was []
  }
}
```

**Time Tracking:**
```json
{
  "metadata": {
    "estimated_hours": 16,
    "actual_hours": 14,      // Add when completed
    "time_variance": -2       // Add for analysis
  }
}
```

**Priority Changes:**
```json
{
  "metadata": {
    "priority": "high"  // was "medium" (escalated)
  }
}
```

#### 5.2 Comprehensive JSON Metadata Field Reference

**Core Fields (Required/Recommended):**

```json
{
  "spec_id": "user-auth-001",     // Required: unique identifier

  "metadata": {
    // Identity
    "title": "User Authentication System",    // Required: human-readable title

    // Status tracking
    "status": "active",                       // Required: draft|approved|active|completed|archived
    "owner": "alice@company.com",             // Recommended: primary assignee
    "priority": "high",                       // Optional: low|medium|high|critical

    // Dates
    "created": "2025-10-18T10:00:00Z",       // Required: creation timestamp
    "updated": "2025-10-19T15:30:00Z",       // Required: last modification
    "started_date": "2025-10-18T11:00:00Z",  // When implementation began
    "completed_date": "2025-10-20T18:00:00Z", // When fully finished
    "archived_date": "2025-10-25T12:00:00Z",  // When archived

    // Time tracking
    "estimated_hours": 16,                    // Recommended: initial estimate
    "actual_hours": 18.5,                     // Add when completed
    "time_variance": 2.5,                     // Difference (actual - estimated)

    // Lifecycle
    "archived_reason": "Superseded by v2",   // Why archived
    "superseded_by": "user-auth-v2-001",  // Replacement spec ID

    // Team
    "reviewers": ["bob@company.com"],        // Optional: code reviewers
    "stakeholders": ["product", "security"]  // Optional: interested parties
  }
}
```

**Optional Tracking Fields:**

```json
{
  "metadata": {
    // Blocker tracking (recommended for visibility)
    "blocked_tasks": ["task-3-1", "task-3-2"],  // Tasks currently blocked
    "blocker_count": 2,                          // Number of active blockers
    "current_blockers": [                        // Detailed blocker info
      {
        "task": "task-3-1",
        "reason": "Redis not provisioned",
        "since": "2025-10-18T16:20:00Z",
        "ticket": "OPS-1234"
      }
    ],

    // Progress indicators
    "progress_percentage": 65,                   // Overall completion
    "current_phase": "phase-2",                  // Which phase active

    // Quality metrics
    "test_coverage": 87,                         // Percentage
    "tech_debt_hours": 4,                        // Estimated cleanup time

    // Revision History
    "revisions": [
      {
        "version": "1.0",
        "date": "2025-10-18T10:30:00Z",
        "author": "claude-code",
        "changes": "Initial spec creation"
      },
      {
        "version": "1.1",
        "date": "2025-10-18T15:45:00Z",
        "author": "claude-code",
        "changes": "Split auth into separate service"
      }
    ]
  }
}
```

#### 5.3 Update Metadata with CLI

**Update JSON metadata fields:**
```bash
# All metadata updates use update-frontmatter command

# Change status
sdd update-frontmatter user-auth-001 status "completed"

# Set owner
sdd update-frontmatter user-auth-001 owner "alice@company.com"

# Update priority
sdd update-frontmatter user-auth-001 priority "high"

# Add completed date (CLI auto-adds timestamp)
sdd update-frontmatter user-auth-001 completed_date "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Preview change
sdd update-frontmatter user-auth-001 actual_hours "18.5" --dry-run
```

#### 5.4 Automatic Metadata Synchronization

`Skill(sdd-update)` can automatically sync JSON metadata with the current state in the hierarchy.

**What Gets Synchronized:**
- `updated` - Current timestamp
- `progress_percentage` - Calculated from completed/total tasks
- `status` - "completed" when all tasks done, "active" otherwise
- `current_phase` - ID of first in-progress phase

**When to sync:**
- After marking multiple tasks complete
- Before creating a status report or presentation
- When metadata fields are out of date with hierarchy state
- As part of periodic maintenance

**Sync metadata with hierarchy:**
```bash
# Synchronize all trackable fields
sdd sync-metadata user-auth-001

# Preview what will change
sdd sync-metadata user-auth-001 --dry-run
```

**Example output:**
```
Metadata updates:
  last_updated: 2025-10-18T10:00:00Z → 2025-10-19T16:30:00Z
  progress_percentage: 50 → 65
  current_phase: phase-1 → phase-2

✓ Synchronized 3 metadata field(s)
```

**Best Practice:**
- Run after bulk operations (multiple task completions)
- Include in periodic spec maintenance
- Use before generating reports or reviews
- Preview with `--dry-run` first

### Operation 6: Query and Filter Tasks

Query and filter tasks using various criteria.

#### 6.1 Filter by Status

Find all tasks with a specific status:

```bash
# Find all pending tasks
sdd query-tasks user-auth-001 --status pending

# Find all blocked tasks (or use list-blockers for more detail)
sdd query-tasks user-auth-001 --status blocked

# Find all completed tasks
sdd query-tasks user-auth-001 --status completed

# Get just task IDs for scripting
sdd query-tasks user-auth-001 --status pending --format simple
```

#### 6.2 Filter by Type

Find tasks of a specific type:

```bash
# Find all verification tasks
sdd query-tasks user-auth-001 --type verify

# Find all regular tasks
sdd query-tasks user-auth-001 --type task

# Find all phases
sdd query-tasks user-auth-001 --type phase
```

#### 6.3 Get Specific Task Details

Retrieve detailed information about a specific task:

```bash
# Get task details
sdd get-task user-auth-001 task-1-2

# Get task as JSON for scripting
sdd get-task user-auth-001 task-1-2 --json
```

#### 6.4 List All Blocked Tasks

Find all blocked tasks with their blocker details:

```bash
# List all blockers with details
sdd list-blockers user-auth-001

# Get blockers as JSON
sdd list-blockers user-auth-001 --json
```

#### 6.5 Check Completion Status

Verify if a spec or phase is ready to be marked complete:

```bash
# Check if entire spec is ready to complete
sdd check-complete user-auth-001

# Check if specific phase is ready to complete
sdd check-complete user-auth-001 --phase phase-1

# Get result as JSON for automation
sdd check-complete user-auth-001 --json
```

### Operation 7: Query Spec Status

Retrieve current state and progress information.

#### 7.1 Get Overall Progress

Get comprehensive progress information using the status report:

```bash
sdd status-report user-auth-001
```

#### 7.2 Get Phase Summary

Get progress for each phase:

```bash
# Phase-level summary using Python tool
sdd list-phases user-auth-001

# Or get JSON output for scripting
sdd list-phases user-auth-001 --json
```

#### 7.3 Validate and Audit

**Get comprehensive status report:**
```bash
sdd status-report user-auth-001
```

**Output as JSON for scripting:**
```bash
sdd status-report user-auth-001 --json
```

**Validate spec file integrity:**
```bash
sdd validate-spec user-auth-001
```

**Deep audit of spec file:**
```bash
sdd audit-spec user-auth-001
```

### Operation 8: Handle Blockers

Document and manage blocked tasks.

#### 8.1 Mark Task as Blocked

Update spec file with blocker information:

```json
{
  "task-3-1": {
    "status": "blocked",
    "metadata": {
      "blocked_at": "2025-10-18T16:20:00Z",
      "blocker_type": "dependency",  // or "technical", "resource", "decision"
      "blocker_description": "Waiting on Redis provisioning (ops ticket #1234)",
      "blocked_by_external": true,
      "blocker_ticket": "#1234",
      "notes": "Cannot implement session management without Redis connection"
    }
  }
}
```

#### 8.2 Add Blocker to Journal

Document in implementation journal:

```markdown
### 2025-10-18 16:20 - Blocker: Redis Dependency
**Task**: task-3-1 (Session Management Service)  
**Status**: Marked as blocked  
**Blocker Type**: External dependency  
**Description**: Redis instance not provisioned in development environment  
**Action Required**: DevOps team needs to provision Redis (ops ticket #1234)  
**Estimated Delay**: 1-2 days  
**Workaround**: None - Redis is hard requirement for session management  
**Next Steps**: Check ticket status daily; resume when Redis available
```

#### 8.3 Unblock Task

When blocker is resolved:

1. Update spec file status back to pending or in_progress
2. Remove blocker metadata or move to resolved_blockers
3. Add journal entry documenting resolution

```markdown
### 2025-10-19 10:30 - Blocker Resolved: Redis Available
**Task**: task-3-1  
**Resolution**: Redis instance provisioned at redis://dev.company.com:6379  
**Resolved By**: DevOps team (ops ticket #1234)  
**Downtime**: 18 hours  
**Status**: Resuming implementation
```

#### 8.4 Manage Blockers

**Mark task as blocked:**
```bash
sdd mark-blocked user-auth-001 task-3-1 --reason "Redis instance not provisioned in development environment" --type dependency --ticket "OPS-1234"
```

**Blocker types:**
- `dependency` - Waiting on external dependency
- `technical` - Technical issue blocking progress
- `resource` - Resource unavailability
- `decision` - Awaiting architectural/product decision

**Unblock a task:**
```bash
sdd unblock-task user-auth-001 task-3-1 --resolution "Redis provisioned at redis://dev.company.com:6379"
```

**List all currently blocked tasks:**
```bash
sdd list-blockers user-auth-001
```

**Preview blocker operation:**
```bash
sdd mark-blocked user-auth-001 task-3-1 --reason "Missing API key" --dry-run
```

### Operation 9: Time Tracking

Track estimated vs actual time for better planning.

#### 9.1 Record Time Spent

Add time tracking to task metadata:

```json
{
  "task-1-2": {
    "status": "completed",
    "metadata": {
      "estimated_hours": 2,
      "actual_hours": 2.5,
      "started_at": "2025-10-18T14:00:00Z",
      "completed_at": "2025-10-18T16:30:00Z",
      "time_notes": "Additional time needed for edge case testing"
    }
  }
}
```

#### 9.2 Calculate Phase Time

Sum time across tasks in a phase:

```bash
# Calculate total time for phase using Python tool
sdd phase-time user-auth-001 phase-1

# Or get JSON output for analysis
sdd phase-time user-auth-001 phase-1 --json
```

#### 9.3 Update Spec with Final Times

When phase/spec completes, update metadata:

```json
{
  "metadata": {
    "estimated_hours": 16,
    "actual_hours": 18.5,
    "time_breakdown": {
      "phase_1": 4.5,
      "phase_2": 8.0,
      "phase_3": 6.0
    },
    "time_variance": 2.5,
    "variance_reasons": [
      "Additional edge case testing in Phase 1 (+0.5h)",
      "Redis blocker caused Phase 3 delay (+2h)"
    ]
  }
}
```

#### 9.4 Track and Report Time

**Track time for a task:**
```bash
sdd track-time user-auth-001 task-1-2 --actual 2.5
```

**Generate time tracking report:**
```bash
sdd time-report user-auth-001
```

**Output as JSON for analysis:**
```bash
sdd time-report user-auth-001 --json
```

**Example time report output:**
```
Time Tracking Report: user-auth-001
========================================
Overall:
  Estimated: 16.0 hours
  Actual:    18.5 hours
  Variance:  +2.5 hours (+15.6%)

By Phase:
  phase-1: 4.5h / 4.0h (+0.5h)
  phase-2: 8.0h / 8.0h (on target)
  phase-3: 6.0h / 4.0h (+2.0h)

Tasks over estimate:
  - task-1-2: +0.5h (edge case testing)
  - task-3-1: +2.0h (blocker delay)
```

## Best Practices

### Document Maintenance
- **Update immediately**: Don't wait - update status as work happens
- **Be specific**: Vague notes aren't helpful later
- **Timestamp everything**: All changes need ISO timestamps
- **Preserve history**: Never delete journal entries or old revisions
- **Validate before saving**: Check JSON syntax, verify structure

### Progress Tracking
- **Bottom-up calculation**: Always recalculate from leaf nodes up
- **Consistent status values**: Only use: pending, in_progress, completed, blocked
- **Parent status derivation**: Parents inherit status from children automatically
- **Atomic updates**: Update entire spec file at once, don't partial update

### Journaling
- **Decision rationale**: Always explain WHY, not just WHAT
- **Link to evidence**: Reference tickets, PRs, discussions
- **Tag participants**: Note who made decisions or approved changes
- **Searchable format**: Use consistent headers and formatting
- **Timely documentation**: Document within same day when possible

### File Organization
- **Clean transitions**: Move files promptly when status changes
- **Consistent naming**: Never rename spec files, use spec_id
- **Spec file persistence**: Keep spec files even after archival
- **Backup before changes**: Always backup state before major updates
- **Git discipline**: Commit spec changes, gitignore spec files

### Multi-Tool Coordination
- **Read before write**: Always load latest state before updating
- **Update your tasks only**: Don't modify other tool's work
- **Recalculate parents**: Update progress up the tree
- **Conflict detection**: Check last_updated timestamp
- **Clear handoffs**: Add journal entry when passing work to another tool

## Common Workflows

### Workflow 1: Starting a Task

1. Load spec and spec files
2. Find next available task (or use Skill(sdd-next))
3. Mark task as `in_progress` in state
4. Update `started_at` timestamp in metadata
5. Recalculate parent progress
6. Save spec file
7. Add journal entry noting start

### Workflow 2: Completing a Task

1. Finish the implementation work (outside this skill)
2. Mark task as `completed` in state
3. Update `completed_at` timestamp
4. Add actual_hours if tracking time
5. Recalculate parent progress
6. Save spec file
7. Add journal entry with notes

### Workflow 3: Completing a Phase

1. Verify all tasks in phase are completed
2. Run all verification steps (outside this skill)
3. Mark all verification tasks as completed
4. Document verification results in spec
5. Recalculate phase progress (should be 100%)
6. Update phase status to completed
7. Add journal entry summarizing phase
8. If final phase, move spec to completed folder

### Workflow 4: Handling a Deviation

1. Discover that implementation must diverge from spec
2. Mark current task as blocked if necessary
3. Add journal entry explaining deviation
4. Document reasoning and impact
5. If major deviation, increment spec version
6. Update affected tasks in spec document
7. Update spec file with new structure if needed
8. Get approval (human or team lead)
9. Add approval to journal
10. Resume with updated plan

### Workflow 5: Archiving a Spec

1. Ensure spec is completed or superseded
2. Update JSON metadata with archive reason
3. Add final journal entry
4. Move JSON spec file to archived/ folder
5. Optionally compress JSON spec file
6. Update related specs if this one blocked them
7. Document relationship in superseding spec

## Spec File Operations Reference

### Read Operations

Use the CLI tools for querying and inspecting spec state:

```bash
# Get specific task details
sdd get-task {spec-id} task-1-2

# Get all pending tasks
sdd query-tasks {spec-id} --status pending

# Get all blocked tasks
sdd list-blockers {spec-id}

# Get all tasks of a specific type
sdd query-tasks {spec-id} --type verify

# Get tasks under a specific parent
sdd query-tasks {spec-id} --parent phase-1

# Get progress summary
sdd status-report {spec-id}

# Get just task IDs (for scripting)
sdd query-tasks {spec-id} --status pending --format simple
```

### Validation

Use the CLI tools for comprehensive validation:

```bash
# Quick validation check
sdd validate-spec {spec-id}

# Deep audit (checks for circular dependencies, metadata completeness)
sdd audit-spec {spec-id}

# Get audit results as JSON
sdd audit-spec {spec-id} --json
```

## Troubleshooting

### Spec File Corruption

**Symptoms:**
- Invalid JSON syntax
- Missing nodes
- Inconsistent parent-child relationships
- Wrong task counts

**Recovery:**
1. Check for backup: `specs/active/{spec-id}.json.backup`
2. If no backup, regenerate from spec using sdd-plan
3. Manually mark completed tasks based on journal entries
4. Validate repaired spec file

### Merge Conflicts

**When:** Multiple tools update state simultaneously

**Resolution:**
1. Load both versions
2. Identify conflicting nodes
3. For each conflict, choose most recent update (check timestamps)
4. Recalculate progress from leaf nodes up
5. Validate merged state
6. Save with updated last_updated timestamp

### Orphaned Tasks

**When:** Task in spec file not in spec, or vice versa

**Resolution:**
1. If task in state but not spec: Check if spec was updated; remove orphan if confirmed deleted
2. If task in spec but not state: Regenerate spec file from current spec (use Skill(sdd-plan))
3. Always preserve completed task history even if spec changed

## Summary

This skill provides document management operations for spec-driven development:

**Core Operations:**
- ✅ Update task status (pending → in_progress → completed)
- ✅ Calculate progress across hierarchy
- ✅ Journal decisions and deviations
- ✅ Document verification results
- ✅ Move specs between lifecycle folders
- ✅ Update JSON metadata fields
- ✅ Handle blockers and dependencies
- ✅ Track time spent vs estimated
- ✅ Query spec status and progress
- ✅ Maintain JSON spec file consistency

**Key Principles:**
1. **Update frequently** - Keep docs current
2. **Document everything** - Decisions, deviations, blockers
3. **Validate always** - Check structure before saving
4. **Preserve history** - Never delete records
5. **Coordinate carefully** - Respect multi-tool workflows

**Remember:** This skill manages the documents and tracking, not the code implementation. Use it to keep specifications accurate and current as development progresses.

---

## See Also

**Skill(sdd-plan)** - Use before this skill to:
- Create new specifications
- Generate initial task hierarchies
- Define phases and dependencies
- Set up the project structure

**Skill(sdd-next)** - Use alongside this skill:
- Find next task to work on (read state maintained by Manager)
- Create execution plans (Developer reads, Manager updates)
- Resume after completing tasks (Manager marks complete, Developer finds next)
- Handle blockers (Manager documents, Developer finds alternatives)

---

*For creating new specifications, use Skill(sdd-plan). For finding tasks and creating execution plans, use Skill(sdd-next).*