---
name: sdd-update
description: Progress tracking for spec-driven development. Use to update task status, track progress, journal decisions, move specs between folders, and maintain spec files. Handles the administrative/clerical aspects of specification documents during development.
---

# Spec-Driven Development: Update Skill

## When to Use This Skill

Use `Skill(sdd-toolkit:sdd-update)` to:
- **Complete tasks** (atomically marks as completed AND creates journal entry using `complete-task`)
- Mark tasks as in_progress or blocked
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

⚠️ **IMPORTANT:** Do NOT use `completion` as an entry-type value. Use `--entry-type status_change` for task completion journal entries.

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

### Complete a Task (Recommended: Atomic Status + Journal)

When finishing a task, use `complete-task` to atomically mark it complete AND create a journal entry:

```bash
# Complete with automatic journal entry
sdd complete-task {spec-id} {task-id} --journal-content "Successfully implemented JWT authentication with token refresh. All tests passing including edge cases for expired tokens."

# Customize the journal entry
sdd complete-task {spec-id} {task-id} \
  --journal-title "Task Completed: Authentication Implementation" \
  --journal-content "Detailed description of what was accomplished..." \
  --entry-type status_change

# Add a brief status note
sdd complete-task {spec-id} {task-id} \
  --note "All tests passing" \
  --journal-content "Implemented authentication successfully."
```

**What `complete-task` does automatically:**
1. Updates task status to `completed`
2. Records completion timestamp
3. Creates a journal entry documenting the completion
4. Clears the `needs_journaling` flag
5. Syncs metadata and recalculates progress
6. Automatically journals parent nodes (phases, groups) that auto-complete

**This is the recommended approach** because it ensures proper documentation of task completion.

#### Parent Node Journaling

When completing a task causes parent nodes (phases or task groups) to auto-complete, `complete-task` automatically creates journal entries for those parents:

- **Automatic detection**: The system detects when all child tasks in a phase/group are completed
- **Automatic journaling**: Creates journal entries like "Phase Completed: Phase 1" for each auto-completed parent
- **No manual action needed**: You don't need to manually journal parent completions
- **Hierarchical**: Works for multiple levels (e.g., completing a task can journal both its group AND its phase)

Example output:
```bash
$ sdd complete-task my-spec-001 task-1-2 --journal-content "Completed final task"
✓ Task marked complete
✓ Journal entry added
✓ Auto-journaled 2 parent node(s): group-1, phase-1
```

### Alternative: Status-Only Update (Not Recommended for Completion)

If you need to mark a task completed without journaling (rare), use:

```bash
sdd update-status {spec-id} {task-id} completed --note "Brief completion note"
```

⚠️ **Warning:** This sets `needs_journaling=True` and requires a follow-up `add-journal` call. Use `complete-task` instead to avoid forgetting to journal.

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

## Workflow 7: Git Commit Integration

When git integration is enabled (via `.claude/git_config.json`), the sdd-update skill can automatically create commits after task completion based on configured commit cadence preferences.

### Commit Cadence Configuration

The commit cadence determines when to offer automatic commits:

- **task**: Commit after each task completion (frequent commits, granular history)
- **phase**: Commit after each phase completion (fewer commits, milestone-based)
- **manual**: Never auto-commit (user manages commits manually)

The cadence preference is stored in `metadata.session_preferences.commit_cadence` in the spec file.

### Commit Workflow Steps

When completing a task and git integration is enabled, the workflow follows these steps:

**1. Check Commit Cadence**

First, check if automatic commits should be offered based on the current event:

```python
# From spec JSON
session_prefs = spec_data.get('metadata', {}).get('session_preferences', {})
commit_cadence = session_prefs.get('commit_cadence', 'task')

# For task completion:
should_offer_commit = (commit_cadence == 'task')

# For phase completion:
should_offer_commit = (commit_cadence == 'phase')
```

**2. Check for Changes**

Before offering a commit, verify there are uncommitted changes:

```bash
# Check for changes (run in repo root directory)
git status --porcelain

# If output is empty, skip commit offer (nothing to commit)
# If output has content, proceed with commit workflow
```

**3. Generate Commit Message**

Create a structured commit message from task metadata:

```python
# Format: "{task-id}: {task-title}"
# Example: "task-2-3: Implement JWT verification middleware"

task_id = "task-2-3"
task_title = "Implement JWT verification middleware"
commit_message = f"{task_id}: {task_title}"
```

**4. Stage and Commit Changes**

Execute git commands to stage all changes and create the commit:

```bash
# Stage all changes (no file picker UI - stage everything)
git add --all

# Create commit with generated message
git commit -m "{task-id}: {task-title}"

# Example:
git commit -m "task-2-3: Implement JWT verification middleware"
```

**All git commands use `cwd=repo_root`** obtained from `find_git_root()` to ensure they run in the correct repository directory.

**5. Record Commit Metadata**

After successful commit, capture the commit SHA and update spec metadata:

```bash
# Get the commit SHA
git rev-parse HEAD

# Example output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

Then call `add_commit_metadata(spec_data, task_id, commit_sha)` to record the commit in the task's metadata:

```python
# Updates task metadata in spec JSON:
task_metadata.commits = [
    {
        "sha": "a1b2c3d4e5f6...",
        "timestamp": "2025-11-02T19:30:00Z",
        "message": "task-2-3: Implement JWT verification middleware"
    }
]
```

### Error Handling

Git operations should be non-blocking - failures should not prevent task completion:

```python
# Execute git command
result = subprocess.run(
    ['git', 'commit', '-m', commit_message],
    cwd=repo_root,
    capture_output=True,
    text=True
)

# Check return code
if result.returncode != 0:
    # Log warning but continue
    logger.warning(f"Git commit failed: {result.stderr}")
    # Task completion still succeeds
else:
    # Success - record commit metadata
    commit_sha = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repo_root,
        capture_output=True,
        text=True
    ).stdout.strip()
    add_commit_metadata(spec_data, task_id, commit_sha)
```

**Error handling principles:**

- Check `returncode` for all git commands
- Log warnings for failures but continue execution
- Git failures do NOT prevent task completion
- User can manually commit if automatic commit fails
- Provide clear error messages in logs for debugging

### Repository Root Detection

All git commands must run in the repository root directory:

```python
from claude_skills.common.git_metadata import find_git_root

# Find repository root from spec file location
repo_root = find_git_root(spec_file_path.parent)

if repo_root is None:
    # Not in a git repository - skip git operations
    logger.debug("No git repository found, skipping commit workflow")
else:
    # Execute git commands with cwd=repo_root
    subprocess.run(['git', 'status'], cwd=repo_root, ...)
```

### Complete Example Workflow

```python
# 1. Task completion triggered
complete_task(spec_id, task_id)

# 2. Check if git integration enabled
if not is_git_enabled(repo_root):
    return  # Skip git workflow

# 3. Check commit cadence
if commit_cadence != 'task':  # For task completion
    return  # Don't offer commit for this event

# 4. Find repository root
repo_root = find_git_root(spec_path.parent)
if repo_root is None:
    return  # Not in git repo

# 5. Check for uncommitted changes
result = subprocess.run(
    ['git', 'status', '--porcelain'],
    cwd=repo_root,
    capture_output=True,
    text=True
)
if not result.stdout.strip():
    return  # No changes to commit

# 6. Generate commit message
commit_message = f"{task_id}: {task_data['title']}"

# 7. Stage all changes
subprocess.run(['git', 'add', '--all'], cwd=repo_root)

# 8. Create commit
result = subprocess.run(
    ['git', 'commit', '-m', commit_message],
    cwd=repo_root,
    capture_output=True,
    text=True
)

# 9. Handle result
if result.returncode == 0:
    # Get commit SHA
    sha_result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    commit_sha = sha_result.stdout.strip()

    # Record metadata
    add_commit_metadata(spec_data, task_id, commit_sha)
    logger.info(f"Committed changes: {commit_sha[:8]}")
else:
    # Log error but don't fail
    logger.warning(f"Commit failed: {result.stderr}")
```

### Configuration File

Git integration is configured via `.claude/git_config.json`:

```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "auto_pr": false,
  "commit_cadence": "task"
}
```

**Settings:**
- `enabled`: Enable/disable all git integration
- `auto_commit`: Enable automatic commits (requires enabled: true)
- `commit_cadence`: When to commit - "task", "phase", or "manual"

See **Workflow 7: Git Commit Integration** in sdd-next SKILL.md for branch creation workflow details.

## Workflow 8: Git Push and Pull Request Integration

When a spec is completed, the workflow can automatically push commits to the remote repository and create a pull request for review.

### When PR Workflow is Triggered

The PR workflow is offered when:

1. **Spec completion** is detected (all tasks completed, ready to finalize)
2. Git integration is **enabled** (`.claude/git_config.json` has `enabled: true`)
3. Repository **has uncommitted changes** or **unpushed commits**
4. User confirms they want to push and create PR

### PR Workflow Steps

**1. Push Commits to Remote**

Push the feature branch to the remote repository:

```bash
# Push with upstream tracking (-u flag)
git push -u origin {branch-name}

# Example:
git push -u origin feat/user-auth-001
```

**Key details:**
- Uses `-u` flag to set upstream tracking for the branch
- Branch name comes from `metadata.git.branch_name` in spec
- Runs with `cwd=repo_root` to ensure correct repository context
- Non-blocking: If push fails, log warning but continue

**2. Generate PR Body Template**

Create a structured PR description from spec metadata:

```markdown
## Summary

{spec-title}

{spec-description}

## Completed Tasks

- ✅ {task-1-title}
- ✅ {task-2-title}
- ✅ {task-3-title}
...

## Phases Completed

- **{phase-1-title}**: {phase-1-completed}/{phase-1-total} tasks
- **{phase-2-title}**: {phase-2-completed}/{phase-2-total} tasks
...

## Commits

- {commit-1-sha}: {commit-1-message}
- {commit-2-sha}: {commit-2-message}
...

## Verification

{List of verification tasks and their results}

---
Generated by SDD Toolkit
```

**Template variables:**
- `spec-title`: From `metadata.title`
- `spec-description`: From `metadata.description`
- Tasks: From `hierarchy` with status `completed`
- Phases: From phase nodes in `hierarchy`
- Commits: From `metadata.git.commits[]` array
- Verification: From verification task results

**3. Create Pull Request via GitHub CLI**

Use `gh pr create` to create the PR:

```bash
# Create PR with title and body
gh pr create \
  --title "{spec-title}" \
  --body "{generated-pr-body}" \
  --base {base-branch}

# Example:
gh pr create \
  --title "User Authentication System" \
  --body "$(cat <<'EOF'
## Summary
...
EOF
)" \
  --base main
```

**Required:**
- `gh` CLI must be installed and authenticated
- Repository must be on GitHub
- User must have push access to the repository

**4. Handle gh Unavailability**

If `gh` CLI is not available:

```python
# Check if gh is installed
result = subprocess.run(
    ['which', 'gh'],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    # gh not available
    logger.warning("GitHub CLI (gh) not found")
    logger.info("Install gh: https://cli.github.com/")
    logger.info("Or create PR manually at: https://github.com/{owner}/{repo}/compare/{branch}")
    # Continue without creating PR
    return None
```

**Fallback actions when gh unavailable:**
- Log warning message
- Provide installation instructions
- Provide manual PR creation URL
- Continue workflow (non-blocking)

**5. Record PR Metadata**

After successful PR creation, update spec metadata:

```bash
# Parse PR URL and number from gh output
# Example output: https://github.com/owner/repo/pull/123

# Extract PR number from URL
pr_number = 123
pr_url = "https://github.com/owner/repo/pull/123"
```

Call `update_pr_metadata(spec_data, pr_url, pr_number, status='open')` to record:

```python
# Updates spec metadata.git.pr:
metadata.git.pr = {
    "url": "https://github.com/owner/repo/pull/123",
    "number": 123,
    "status": "open",
    "created_at": "2025-11-03T15:30:00Z"
}
```

### Error Handling for PR Workflow

All PR workflow operations are **non-blocking** - failures should not prevent spec completion:

```python
# Push to remote
push_result = subprocess.run(
    ['git', 'push', '-u', 'origin', branch_name],
    cwd=repo_root,
    capture_output=True,
    text=True
)

if push_result.returncode != 0:
    # Log error but continue
    logger.warning(f"Git push failed: {push_result.stderr}")
    logger.info("Push manually with: git push -u origin {branch_name}")
    # Spec completion still succeeds, PR creation skipped
    return None

# Create PR via gh
pr_result = subprocess.run(
    ['gh', 'pr', 'create', '--title', title, '--body', body, '--base', base_branch],
    cwd=repo_root,
    capture_output=True,
    text=True
)

if pr_result.returncode != 0:
    # Log error but continue
    logger.warning(f"PR creation failed: {pr_result.stderr}")
    logger.info("Create PR manually at: {github_url}")
    # Spec completion still succeeds
    return None
```

**Error handling principles:**
- Check `returncode` for all git/gh commands
- Log warnings for failures with actionable guidance
- Provide manual fallback instructions
- Failures do NOT prevent spec completion
- User can manually push/create PR if automatic workflow fails

### Configuration

PR workflow is controlled via `.claude/git_config.json`:

```json
{
  "enabled": true,
  "auto_commit": true,
  "auto_push": true,
  "auto_pr": true,
  "pr_template": "default"
}
```

**Settings:**
- `enabled`: Master switch for all git integration
- `auto_push`: Enable automatic push after spec completion (requires enabled: true)
- `auto_pr`: Enable automatic PR creation (requires enabled: true and auto_push: true)
- `pr_template`: PR body template style ("default", "detailed", "minimal")

**Dependency chain:**
- `auto_pr` requires `auto_push` to be true
- `auto_push` requires `enabled` to be true
- If any requirement is false, skip that step in the workflow

### Complete Example: Spec Completion with PR

```python
# 1. User triggers spec completion
complete_spec(spec_id)

# 2. Verify all tasks completed
if not all_tasks_completed(spec):
    raise Error("Cannot complete spec - tasks remaining")

# 3. Check if git integration enabled
if not is_git_enabled(repo_root):
    return  # Skip git workflow

# 4. Check if auto_push enabled
config = load_git_config(repo_root)
if not config.get('auto_push'):
    return  # Skip push workflow

# 5. Find repository root
repo_root = find_git_root(spec_path.parent)
if repo_root is None:
    return  # Not in git repo

# 6. Get branch name from spec metadata
branch_name = spec_data['metadata']['git']['branch_name']
base_branch = spec_data['metadata']['git']['base_branch']

# 7. Push commits to remote
result = subprocess.run(
    ['git', 'push', '-u', 'origin', branch_name],
    cwd=repo_root,
    capture_output=True,
    text=True
)

if result.returncode != 0:
    logger.warning(f"Push failed: {result.stderr}")
    return  # Skip PR creation

# 8. Check if auto_pr enabled
if not config.get('auto_pr'):
    logger.info(f"Pushed to {branch_name}. Create PR manually.")
    return

# 9. Generate PR body from spec
pr_body = generate_pr_body(spec_data)
pr_title = spec_data['metadata']['title']

# 10. Create PR via gh CLI
pr_result = subprocess.run(
    ['gh', 'pr', 'create',
     '--title', pr_title,
     '--body', pr_body,
     '--base', base_branch],
    cwd=repo_root,
    capture_output=True,
    text=True
)

if pr_result.returncode == 0:
    # Parse PR URL from output
    pr_url = pr_result.stdout.strip()
    pr_number = extract_pr_number(pr_url)

    # Record PR metadata
    update_pr_metadata(spec_data, pr_url, pr_number, status='open')
    logger.info(f"Created PR #{pr_number}: {pr_url}")
else:
    logger.warning(f"PR creation failed: {pr_result.stderr}")
    logger.info("Create PR manually at: {github_compare_url}")
```

### GitHub CLI (gh) Requirements

The PR workflow requires the GitHub CLI (`gh`):

**Installation:**
- macOS: `brew install gh`
- Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
- Windows: `winget install --id GitHub.cli`

**Authentication:**
```bash
# Login to GitHub
gh auth login

# Verify authentication
gh auth status
```

**Alternative: Manual PR Creation**

If `gh` is unavailable, users can create PRs manually:

1. Push branch: `git push -u origin {branch-name}`
2. Visit: `https://github.com/{owner}/{repo}/compare/{branch-name}`
3. Click "Create pull request"
4. Fill in title and description from spec

The spec completion workflow provides the manual PR creation URL when `gh` is not available.

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
