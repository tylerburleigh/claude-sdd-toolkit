---
name: sdd-update
description: Progress tracking for spec-driven development. Use to update task status, track progress, journal decisions, move specs between folders, and maintain spec files. Handles the administrative/clerical aspects of specification documents during development.
---

# Spec-Driven Development: Update Skill

## When to Use This Skill

Use `Skill(sdd-toolkit:sdd-update)` to:
- Mark tasks as in_progress, completed, or blocked
- Document decisions and deviations in journal entries
- Add verification results to specs
- Move specs between lifecycle folders (e.g., pending => active, active => completed)
- Update spec metadata fields

**Do NOT use for:**
- Creating specifications
- Finding what to work on next
- Writing code or running tests

## Core Philosophy

**Document Reality**: JSON spec files are living documents that evolve during implementation. This skill ensures the spec accurately reflects current progress, decisions, and status. All updates are made through CLI commands that handle validation, backups, and progress recalculation automatically.

## Reading Specifications (CRITICAL)

**When working with spec files, ALWAYS use `sdd` CLI commands:**
- ✅ **ALWAYS** use `sdd` commands to read/query spec files (e.g., `sdd update-status`, `sdd add-journal`, `sdd list-blockers`)
- ❌ **NEVER** use `Read()` tool on .json spec files - bypasses hooks and wastes context tokens (specs can be 50KB+)
- ❌ **NEVER** use Bash commands to read spec files (e.g., `cat`, `head`, `tail`, `grep`, `jq`)
- ❌ **NEVER** use command chaining to access specs (e.g., `sdd --version && cat specs/active/spec.json`)
- The `sdd` CLI provides efficient, structured access with proper parsing and validation
- Spec files are large and reading them directly wastes valuable context window space

## Skill Family

This skill is part of the **Spec-Driven Development** workflow:
- **sdd-plan** - Creates specifications → **sdd-next** - Finds next task → **Implementation** → **sdd-update** (this skill) - Updates progress

## Workflow 1: Starting a Task

Mark a task as in_progress when you begin work:

```bash
sdd update-status {spec-id} {task-id} in_progress
```

The CLI automatically records the start timestamp for tracking purposes.

## Workflow 2: Tracking Progress

### Add Journal Entries

Document decisions, deviations, or important notes:

```bash
# Document a decision
sdd add-journal {spec-id} --title "Decision Title" --content "Explanation of decision and rationale" --task-id {task-id} --entry-type decision

# Document a deviation from the plan
sdd add-journal {spec-id} --title "Deviation: Changed Approach" --content "Created separate service file instead of modifying existing. Improves separation of concerns." --task-id {task-id} --entry-type deviation

# Document task completion (use status_change, NOT completion)
sdd add-journal {spec-id} --title "Task Completed: Implement Auth" --content "Successfully implemented authentication with JWT tokens. All tests passing." --task-id {task-id} --entry-type status_change

# Document a note
sdd add-journal {spec-id} --title "Implementation Note" --content "Using Redis for session storage as discussed." --task-id {task-id} --entry-type note
```

**Entry types:** `decision`, `deviation`, `blocker`, `note`, `status_change`

⚠️ **IMPORTANT:** Do NOT use `completion` as an entry-type value. While `completion` exists as a template option for `bulk-journal --template completion`, it is NOT a valid entry type for `add-journal --entry-type`.

**To document task completion:**
- Use `--entry-type status_change` for individual completion journal entries
- OR use `sdd bulk-journal {spec-id} --template completion` to journal multiple completed tasks at once

### Bulk Journal Completed Tasks

The CLI tracks which completed tasks need journal entries:

```bash
# Check which tasks need journaling
sdd check-journaling {spec-id}

# Journal all unjournaled tasks at once
sdd bulk-journal {spec-id}

# Preview what will be journaled
sdd bulk-journal {spec-id} --dry-run
```

**Best Practice:** Use `bulk-journal` periodically to document multiple completed tasks efficiently.

## Workflow 3: Handling Blockers

### Mark Task as Blocked

When a task cannot proceed:

```bash
sdd mark-blocked {spec-id} {task-id} --reason "Description of blocker" --type {type} --ticket "TICKET-123"
```

**Blocker types:**
- `dependency` - Waiting on external dependency
- `technical` - Technical issue blocking progress
- `resource` - Resource unavailability
- `decision` - Awaiting architectural/product decision

### Unblock Task

When blocker is resolved:

```bash
sdd unblock-task {spec-id} {task-id} --resolution "Description of how it was resolved"
```

### List All Blockers

```bash
sdd list-blockers {spec-id}
```

## Workflow 4: Adding Verification Results

### Manual Verification Recording

Document verification results:

```bash
# Verification passed
sdd add-verification {spec-id} {verify-id} PASSED --command "npm test" --output "All tests passed" --notes "Optional notes"

# Verification failed
sdd add-verification {spec-id} {verify-id} FAILED --command "npm test" --output "3 tests failed" --issues "List of issues found"

# Partial success
sdd add-verification {spec-id} {verify-id} PARTIAL --notes "Most checks passed, minor issues remain"
```

### Automatic Verification Execution

If verification tasks have metadata specifying how to execute them, run automatically:

```bash
# Execute verification based on metadata
sdd execute-verify {spec-id} {verify-id}

# Execute and automatically record result
sdd execute-verify {spec-id} {verify-id} --record
```

**Requirements:** Verification task must have `skill` or `command` in its metadata.

### Verify on Task Completion

Automatically run verifications when marking a task complete:

```bash
sdd update-status {spec-id} {task-id} completed --verify
```

The `--verify` flag runs all associated verify tasks. If any fail, the task reverts to `in_progress`.

### Configurable Failure Handling

Verification tasks can specify custom failure behavior via `on_failure` metadata:

```json
{
  "verify-1-1": {
    "metadata": {
      "on_failure": {
        "consult": true,
        "revert_status": "in_progress",
        "max_retries": 2,
        "continue_on_failure": false
      }
    }
  }
}
```

**on_failure fields:**
- `consult` (boolean) - Recommend AI consultation for debugging
- `revert_status` (string) - Status to revert parent task to on failure
- `max_retries` (integer) - Number of automatic retry attempts (0-5)
- `continue_on_failure` (boolean) - Continue with other verifications if this fails

## Workflow 5: Completing Tasks

Mark a task as completed when finished:

```bash
sdd update-status {spec-id} {task-id} completed --note "Brief completion note"
```

The CLI automatically records the completion timestamp.

### Complete a Spec

When all phases are verified and complete:

```bash
# Check if ready to complete
sdd check-complete {spec-id}

# Complete spec (updates metadata, regenerates docs, moves to completed/)
sdd complete-spec {spec-id}

# Skip documentation regeneration
sdd complete-spec {spec-id} --skip-doc-regen
```

## Workflow 6: Moving Specs Between Folders

### Activate from Backlog

Move a spec from pending/ to active/ when ready to start work:

```bash
sdd activate-spec {spec-id}
```

This updates metadata status to "active" and makes the spec visible to sdd-next.

### Move to Completed

Use `complete-spec` (see Workflow 5) to properly complete and move a spec.

### Archive Superseded Specs

Move specs that are no longer relevant:

```bash
sdd move-spec {spec-id} archived
```

## Common CLI Patterns

### Preview Changes

Use `--dry-run` to preview changes before applying:

```bash
sdd update-status {spec-id} {task-id} completed --dry-run
sdd mark-blocked {spec-id} {task-id} --reason "Test" --dry-run
```

### Query Spec State

```bash
# Get overall progress
sdd status-report {spec-id}

# List all phases with progress
sdd list-phases {spec-id}

# Find tasks by status
sdd query-tasks {spec-id} --status pending
sdd query-tasks {spec-id} --status blocked

# Find tasks by type
sdd query-tasks {spec-id} --type verify

# Get specific task details
sdd get-task {spec-id} {task-id}
```

### Update Metadata

```bash
# Update spec metadata fields
sdd update-frontmatter {spec-id} status "active"
sdd update-frontmatter {spec-id} owner "user@example.com"
sdd update-frontmatter {spec-id} priority "high"

# Sync metadata with hierarchy state
sdd sync-metadata {spec-id}
```

### Validation

For comprehensive spec validation, use the sdd-validate subagent:

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/{spec-id}.json",
  description: "Validate spec file"
)
```

For deep audits:

```bash
sdd audit-spec {spec-id}
```

## JSON Structure Reference

### Task Status Values

- `pending` - Not yet started
- `in_progress` - Currently being worked on
- `completed` - Successfully finished
- `blocked` - Cannot proceed due to dependencies or issues

### Journal Entry Structure

Journal entries are stored in a top-level `journal` array:

```json
{
  "journal": [
    {
      "timestamp": "2025-10-18T14:30:00Z",
      "entry_type": "decision",
      "title": "Brief title",
      "task_id": "task-1-2",
      "author": "claude-sonnet-4.5",
      "content": "Detailed explanation",
      "metadata": {}
    }
  ]
}
```

### Verification Result Structure

Stored in verification task metadata:

```json
{
  "verify-1-1": {
    "metadata": {
      "verification_result": {
        "date": "2025-10-18T16:45:00Z",
        "status": "PASSED",
        "output": "Command output",
        "notes": "Additional context"
      }
    }
  }
}
```

### Folder Structure

```
specs/
├── pending/      # Backlog - planned but not activated
├── active/       # Currently being implemented
├── completed/    # Finished and verified
└── archived/     # Old or superseded
```

## Best Practices

### When to Update

- **Update immediately** - Don't wait; update status as work happens
- **Be specific** - Vague notes aren't helpful later
- **Document WHY** - Always explain rationale, not just what changed

### Journaling

- **Link to evidence** - Reference tickets, PRs, discussions
- **Decision rationale** - Explain why decisions were made
- **Use bulk-journal** - Efficiently document multiple completed tasks

### Multi-Tool Coordination

- **Read before write** - Always load latest state before updating
- **Update your tasks only** - Don't modify other tools' work
- **Clear handoffs** - Add journal entry when passing work to another tool

### File Organization

- **Clean transitions** - Move specs promptly when status changes
- **Never rename specs** - Spec file names are based on spec_id
- **Backup before changes** - CLI handles automatic backups

## Troubleshooting

### Spec File Corruption

**Recovery:**
1. Check for backup: `specs/active/{spec-id}.json.backup`
2. If no backup, regenerate from original spec
3. Manually mark completed tasks based on journal entries
4. Validate repaired file

### Orphaned Tasks

**Resolution:**
1. If task in file but not in spec: Check if spec was updated; remove if confirmed deleted
2. If task in spec but not in file: Regenerate spec file using sdd-plan
3. Always preserve completed task history even if spec changed

### Merge Conflicts

**When:** Multiple tools update state simultaneously

**Resolution:**
1. Load both versions
2. Identify conflicting nodes
3. Choose most recent update (check timestamps)
4. Recalculate progress from leaf nodes up
5. Validate merged state

## Common Mistakes

### Using `--entry-type completion`

**Error:**
```bash
sdd add-journal: error: argument --entry-type: invalid choice: 'completion'
Exit code: 2
```

**Cause:** Confusing the `bulk-journal --template` option with `add-journal --entry-type`

**Fix:** Use `--entry-type status_change` instead:

```bash
# ❌ WRONG - "completion" is not a valid entry type
sdd add-journal {spec-id} --task-id {task-id} --entry-type completion --title "..." --content "..."

# ✅ CORRECT - Use "status_change" for task completion entries
sdd add-journal {spec-id} --task-id {task-id} --entry-type status_change --title "Task Completed" --content "..."

# ✅ ALTERNATIVE - Use bulk-journal with completion template
sdd bulk-journal {spec-id} --template completion
```

**Why this happens:** The `bulk-journal` command has a `--template` parameter that accepts `completion` as a value for batch journaling. However, `add-journal` has an `--entry-type` parameter with different valid values. These are two separate parameters for different purposes:
- `bulk-journal --template completion` - Batch journal multiple completed tasks using a template
- `add-journal --entry-type status_change` - Add individual journal entry about task status changes

### Reading Spec Files Directly

**Error:** Using Read tool, cat, grep, or jq on spec files

**Fix:** Always use `sdd` CLI commands:

```bash
# ❌ WRONG - Wastes context tokens and bypasses validation
Read("specs/active/my-spec.json")
cat specs/active/my-spec.json

# ✅ CORRECT - Use sdd CLI for structured access
sdd status-report {spec-id}
sdd get-task {spec-id} {task-id}
sdd query-tasks {spec-id} --status pending
```

## Command Reference

### Status Management
- `update-status` - Change task status
- `mark-blocked` - Mark task as blocked with reason
- `unblock-task` - Unblock a task with resolution

### Documentation
- `add-journal` - Add journal entry to spec
- `bulk-journal` - Add entries for multiple completed tasks
- `check-journaling` - Detect tasks without journal entries
- `add-verification` - Document verification results
- `execute-verify` - Run verification task automatically

### Lifecycle
- `activate-spec` - Move spec from pending/ to active/
- `move-spec` - Move spec between folders
- `complete-spec` - Mark complete and move to completed/

### Query & Reporting
- `status-report` - Get progress and status summary
- `query-tasks` - Filter tasks by status, type, or parent
- `get-task` - Get detailed task information
- `list-phases` - List all phases with progress
- `list-blockers` - List all blocked tasks
- `check-complete` - Verify if spec/phase is ready to complete

### Metadata
- `update-frontmatter` - Update spec metadata fields
- `sync-metadata` - Synchronize metadata with hierarchy

### Validation
- `validate-spec` - Check spec file consistency
- `audit-spec` - Deep audit of spec file integrity

### Common Flags
- `--dry-run` - Preview changes without saving
- `--json` - Output as JSON for scripting
- `--verify` - Auto-run verify tasks on completion
