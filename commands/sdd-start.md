---
name: sdd-start
description: Resume or start spec-driven development work by detecting active tasks and providing interactive options
---

# SDD Session Start Helper

This command helps you resume spec-driven development (SDD) work at the start of a session. It will:
1. Scan for active SDD specifications
2. Show you resumable work with progress indicators
3. Provide interactive options to continue, start new, or do something else
4. Automatically execute your chosen action (sdd-next or sdd-plan)

## Workflow

**You are assisting the user with resuming their spec-driven development work.**

### Phase 0: Check Project Permissions

**FIRST**, check if SDD permissions are configured for this project:

```bash
skills-dev start-helper -- check-permissions
```

**If `needs_setup: true`** (permissions not configured):

Present this message to the user:
```
Hi! I noticed this project needs SDD permission setup.

Before we can work with specifications, I need to configure project-level permissions for SDD tools.
```

Then use the AskUserQuestion tool:
- **Header**: "Action"
- **Question**: "Would you like me to set up SDD permissions now?"
- **Options**:
  1. Yes, set up permissions (auto-runs setup)
  2. No, skip for now (continue without setup)

**If user chooses "Yes, set up permissions":**
```bash
# Run the setup helper to configure .claude/settings.json
skills-dev setup-permissions -- update .

# Inform the user
echo "✅ SDD permissions configured! You can now use SDD skills in this project."

# Then proceed to Phase 1 to discover active work
```

**If user chooses "No, skip for now"** OR **if permissions already configured**:
- Proceed directly to Phase 0.5

---

### Phase 0.5: Ensure Wrapper Scripts Installed

**Check if SDD wrapper scripts are installed in ~/.claude/bin:**

```bash
skills-dev start-helper -- check-wrappers
```

**If wrappers not installed** (exit code 1 or `all_installed: false`):

Present this message:
```
Setting up SDD command-line tools...
```

Then run:
```bash
skills-dev start-helper -- install-wrappers
```

This will:
- Copy wrapper scripts from the SDD plugin to ~/.claude/bin
- Make them executable
- Enable short SDD commands via PATH

Display the success message from the script output.

**Then proceed to Phase 1**

**If wrappers already installed** (exit code 0 or `all_installed: true`):
- Silently proceed to Phase 1 (no message needed)

---

### Phase 1: Discover Active Work

Use the helper script to find and format active specifications:

```bash
skills-dev start-helper -- format-output
```

The script will return properly formatted text with active specs, their progress, and status.

**IMPORTANT**: The `format-output` command returns pre-formatted text with proper newlines and indentation.
Display this output EXACTLY as returned - do not reformat or modify it.

### Phase 2: Present Options Based on Findings

**If active work found:**

The formatted output from `format-output` already includes:
- Number of active specifications
- For each spec: ID, title, progress, current phase, next task, and last updated time
- Priority indicator (⚡ IN PROGRESS for in-progress specs)
- 🕐 Last-accessed task information (if available)
- 💡 Count of in-progress tasks

Simply display the formatted output directly.

**Then check for last-accessed task:**

Run `get-session-info` to get structured session data:
```bash
skills-dev start-helper -- get-session-info
```

**If last-accessed task exists:**

Present these options with AskUserQuestion tool:
- **Header**: "Action"
- **Question**: "What would you like to do?"
- **Options**:
  1. Resume last task (auto-runs sdd-next with specific task)
  2. Continue with next task (auto-runs sdd-next)
  3. Write new spec (auto-runs sdd-plan)
  4. Something else (exit)

**If NO last-accessed task:**

Present these options:
- **Header**: "Action"
- **Question**: "What would you like to do?"
- **Options**:
  1. Continue with next task (auto-runs sdd-next)
  2. Write new spec (auto-runs sdd-plan)
  3. Something else (exit)

**If NO active work found:**

The formatted output from `format-output` will show:
```
📋 No active SDD work found.

No specs/active directory or no pending/in-progress tasks detected.
```

Display this, then ask:
```
What would you like to do?
```

Then use AskUserQuestion tool with options:
- **Header**: "Action"
- **Question**: "What would you like to do?"
- **Options**:
  1. Write new spec (auto-runs sdd-plan)
  2. Something else (exit)

### Phase 3: Execute User's Choice

Based on the user's selection:

**Option 1: "Resume last task"** (if last-accessed task available)
```bash
# Get the last task info from get-session-info output
# Then automatically invoke the sdd-next skill with context

I'll help you resume work on task [task-id] from [spec-name]...
```

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-next)
```

**IMPORTANT**: When invoking sdd-next for resume, provide context about the specific task:
- Mention the spec_id from the last_task data
- Mention the task_id if known
- This helps sdd-next prepare the specific task

**Option 2: "Continue with next task"**
```bash
# If multiple specs, ask which one (if not obvious)
# Then automatically invoke the sdd-next skill

I'll use the sdd-next skill to find and prepare the next task from [spec-name]...
```

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-next)
```

**Option 3: "Write new spec"**
```bash
I'll use the sdd-plan skill to help you create a new specification...

What feature or change would you like to plan?
```

Use the Skill tool to invoke sdd-plan:
```
Skill(sdd-plan)
```

**Option 4: "Something else"**
```bash
No problem! Let me know if you need any help with your project.
```

Exit gracefully without invoking any skills.

### Phase 4: Handle Multiple Specs (if applicable)

If user chose "Continue with next task" and there are multiple specs:

**Show spec selection:**
```
Which specification would you like to work on?
```

Use AskUserQuestion to let them choose the spec, then invoke sdd-next with that context.

## Important Notes

- **Auto-execution**: This command automatically invokes skills based on user choice (no additional confirmation needed)
- **Non-intrusive**: If no active work found, gracefully offer to start new or exit
- **Fast**: Discovery should complete in <500ms using the Python helper
- **Robust**: Handle missing directories or malformed JSON spec files gracefully

## Helper Script Reference

The `sdd_start_helper.py` script (accessed via `skills-dev start-helper --`) provides:
- `check-permissions` - Check if SDD permissions are configured (returns JSON)
- `check-wrappers` - Check if wrapper scripts are installed in ~/.claude/bin (returns JSON, exit code 0 if all installed)
- `install-wrappers` - Install wrapper scripts from source to ~/.claude/bin (returns JSON with created/errors)
- `format-output` - Returns human-readable formatted text with last-accessed task info (PREFERRED - use this for display)
- `get-session-info` - Returns session state with last-accessed task as JSON (NEW - for programmatic access)
- `find-active-work` - Returns JSON with all resumable specs (for programmatic use)

**Always use `format-output` for presenting information to the user** - it ensures proper newlines, indentation, and formatting. Use `get-session-info` when you need programmatic access to last-accessed task data.

**Note**: All commands use the unified CLI: `skills-dev start-helper -- <command>`

## Example Output

```json
{
  "active_work_found": true,
  "specs": [
    {
      "spec_id": "user-auth-2025-10-18-001",
      "spec_file": "/path/to/specs/active/user-auth-2025-10-18-001.json",
      "title": "User Authentication System",
      "progress": {
        "completed": 15,
        "total": 23,
        "percentage": 65
      },
      "current_phase": "phase-2",
      "phase_title": "Authentication Service",
      "next_task": "task-2-1",
      "next_task_file": "src/services/authService.ts",
      "status": "in_progress",
      "last_updated": "2025-10-20T14:30:00Z",
      "resumability_score": 100
    }
  ]
}
```

## Error Handling

- If specs directory not found: Show friendly message, offer to run sdd-plan
- If spec files malformed: Skip that spec, show warning
- If helper script fails: Gracefully degrade to manual mode

## Integration

This command is designed to work seamlessly with:
- `sdd-plan` skill (creating specifications)
- `sdd-next` skill (finding next tasks)
- `sdd-update` skill (updating progress)

After tasks are completed with sdd-update, this command will automatically detect the updated state next time it's run.
