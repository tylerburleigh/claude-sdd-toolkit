---
name: sdd-begin
description: Resume or start spec-driven development work by detecting active tasks and providing interactive options
---

# SDD Session Start Helper

**⛔ CRITICAL: NEVER manually read .json spec files. Always use `sdd-next` skill or `sdd skills-dev` helper commands.**

This command helps you resume spec-driven development (SDD) work at the start of a session. It will:
1. Scan for active SDD specifications
2. Show you resumable work with progress indicators
3. Provide interactive options to continue, start new, or do something else
4. Automatically execute your chosen action (sdd-next or sdd-plan)

## Workflow

**You are assisting the user with resuming their spec-driven development work.**

### Phase 1: Check Project Permissions

**FIRST**, check if SDD permissions are configured for this project:

```bash
sdd skills-dev start-helper check-permissions
```

**If check returns `status: "fully_configured"`:**
- Proceed directly to Phase 2 (Git Configuration)

**If check returns `status: "partially_configured"`:**

Present this message to the user:
```
⚠️  Some SDD permissions are missing (35/41 configured)

Missing permissions:
  • 2 skill permissions
  • 4 bash/git permissions
```

Then use the AskUserQuestion tool:
- **Header**: "Permissions"
- **Question**: "Would you like to add the missing permissions now?"
- **Options**:
  1. Yes, add missing permissions
  2. No, continue anyway

**If user chooses "Yes, add missing permissions":**
```bash
# Run the setup helper to add missing permissions
sdd skills-dev setup-permissions update .

# Inform the user
echo "✅ SDD permissions updated! Added missing permissions."

# Then proceed to Phase 2 to configure git
```

**If user chooses "No, continue anyway":**
```
⚠️  Continuing with partial permissions. Some features may not work.
```
- Proceed to Phase 2 (Git Configuration)

**If check returns `status: "not_configured"`:**

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
sdd skills-dev setup-permissions update .

# Inform the user
echo "✅ SDD permissions configured! You can now use SDD skills in this project."

# Then proceed to Phase 2 to configure git
```

**If user chooses "No, skip for now":**
- Proceed directly to Phase 2 (Git Configuration)

---

### Phase 2: Check Git Configuration

**AFTER permissions are configured**, check if git integration is configured:

```bash
sdd skills-dev start-helper check-git-config .
```

**If `needs_setup: true`** (git config not configured):

Present this message to the user:
```
I noticed git integration hasn't been configured yet.

Git integration enables automatic branch creation, commits, and AI-powered PR generation. Would you like to set it up now?
```

Then use the AskUserQuestion tool:
- **Header**: "Git Setup"
- **Question**: "Configure git integration?"
- **Options**:
  1. Yes, configure now (runs interactive wizard)
  2. No, skip for now (continue without git features)

**If user chooses "Yes, configure now":**
```bash
# Run the interactive setup wizard
sdd skills-dev setup-git-config .

# The wizard will ask questions like:
# - Enable git integration? (yes/no)
# - Auto-create branches? (yes/no)
# - Auto-commit on task completion? (yes/no)
# - Show files before commit? (yes/no)
# - Enable AI-powered PRs? (yes/no)
# etc.

# Configuration will be saved to .claude/git_config.json
```

**If user chooses "No, skip for now"**:
- Proceed directly to Phase 3

**If git already configured**:

Optionally display current git config status (brief, non-intrusive):
```
Git integration: ✅ Enabled (auto-branch, auto-commit per task, AI PRs)
```

Then proceed directly to Phase 3.

---

### Phase 3: Discover Active Work

**⚠️ USE HELPER SCRIPT ONLY - DO NOT READ SPEC FILES DIRECTLY**

Use the helper script to find and format active specifications:

```bash
sdd skills-dev start-helper format-output
```

The script will return properly formatted text with active specs, their progress, and status. It also discovers pending specs in the backlog (from `specs/pending/` folder).

**IMPORTANT**:
- The `format-output` command returns pre-formatted text with proper newlines and indentation
- Display this output EXACTLY as returned - do not reformat or modify it
- **NEVER use Read() on .json spec files** - the helper script handles all spec parsing efficiently
- JSON specs can be 50KB+ and waste context tokens when read directly

### Phase 4: Present Options Based on Findings

**If active work found:**

The formatted output from `format-output` already includes:
- Number of specifications found (active and pending combined)
- For each spec: ID, title, progress, and folder status
  - Active specs: ⚡ (in_progress) or 📝 (pending status)
  - Pending specs: ⏸️ with [PENDING] label (backlog)
- 🕐 Last-accessed task information (if available)
- 💡 Count of in-progress tasks

Simply display the formatted output directly.

**Then check for last-accessed task:**

Run `get-session-info` to get structured session data:
```bash
sdd skills-dev start-helper get-session-info
```

**If last-accessed task exists:**

First check if there are pending specs using the get-session-info output (check `pending_specs` array).

Present these options with AskUserQuestion tool:
- **Header**: "Action"
- **Question**: "What would you like to do?"
- **Options**:
  1. Resume last task (auto-runs sdd-next with specific task)
  2. Continue with next task (auto-runs sdd-next)
  3. Write new spec (auto-runs sdd-plan)
  4. View pending backlog (M specs) - **Only show if pending_specs array has items**
  5. Something else (exit)

**If NO last-accessed task:**

First check if there are pending specs using the get-session-info output (check `pending_specs` array).

Present these options:
- **Header**: "Action"
- **Question**: "What would you like to do?"
- **Options**:
  1. Continue with next task (auto-runs sdd-next)
  2. Write new spec (auto-runs sdd-plan)
  3. View pending backlog (M specs) - **Only show if pending_specs array has items**
  4. Something else (exit)

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

### Phase 5: Execute User's Choice

Based on the user's selection:

**Option 1: "Resume last task"** (if last-accessed task available)
```bash
# Get the last task info from get-session-info output
# Then ask the user how they want to work

I'll help you resume work on task [task-id] from [spec-name]...
```

**Ask the user to configure the work mode:**

Use AskUserQuestion tool:
- **Header**: "Work Mode"
- **Question**: "How would you like to work on this task?"
- **Options**:
  1. Single Task Mode (Plan and execute one task at a time)
  2. Autonomous Mode (Complete all tasks in current phase within context limits)

**If user selects Autonomous Mode, check context first:**

Use the two-command session marker pattern:
```bash
# Step 1: Generate session marker
sdd session-marker

# Step 2: Check context using the marker (in SEPARATE command)
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

Parse the output to get context percentage.

If context percentage > 50%:
```
⚠️  Context usage is already at X%

Autonomous mode works best with lower context usage to ensure you can complete multiple tasks within the 75% limit.
```

Use AskUserQuestion:
- **Header**: "High Context"
- **Question**: "Context is already at X%. How would you like to proceed?"
- **Options**:
  1. Continue with Autonomous Mode (May hit 75% limit quickly)
  2. Switch to Single Task Mode (Safer option)

**Then invoke sdd-next based on the final selected mode:**

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

**IMPORTANT**: When invoking sdd-next:
- Mention the spec_id from the last_task data
- Mention the task_id if known
- **Mention the selected work mode** in the prompt:
  - For Single Task Mode: "Execute sdd-next for [spec-id] in single-task mode"
  - For Autonomous Mode: "Execute sdd-next for [spec-id] in autonomous mode - complete all tasks in current phase"
- This helps sdd-next know which workflow to use

**Option 2: "Continue with next task"**
```bash
# If multiple specs, ask which one (if not obvious)
# Then ask the user how they want to work

I'll use the sdd-next skill to find and prepare the next task from [spec-name]...
```

**Ask the user to configure the work mode:**

Use AskUserQuestion tool:
- **Header**: "Work Mode"
- **Question**: "How would you like to work on this task?"
- **Options**:
  1. Single Task Mode (Plan and execute one task at a time)
  2. Autonomous Mode (Complete all tasks in current phase within context limits)

**If user selects Autonomous Mode, check context first:**

Use the two-command session marker pattern:
```bash
# Step 1: Generate session marker
sdd session-marker

# Step 2: Check context using the marker (in SEPARATE command)
sdd context --session-marker "SESSION_MARKER_<hash>" --json
```

Parse the output to get context percentage.

If context percentage > 50%:
```
⚠️  Context usage is already at X%

Autonomous mode works best with lower context usage to ensure you can complete multiple tasks within the 75% limit.
```

Use AskUserQuestion:
- **Header**: "High Context"
- **Question**: "Context is already at X%. How would you like to proceed?"
- **Options**:
  1. Continue with Autonomous Mode (May hit 75% limit quickly)
  2. Switch to Single Task Mode (Safer option)

**Then invoke sdd-next based on the final selected mode:**

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

**IMPORTANT**: When invoking sdd-next:
- **Mention the selected work mode** in the prompt:
  - For Single Task Mode: "Execute sdd-next for [spec-id] in single-task mode"
  - For Autonomous Mode: "Execute sdd-next for [spec-id] in autonomous mode - complete all tasks in current phase"
- This helps sdd-next know which workflow to use

**Option 3: "Write new spec"**
```bash
I'll use the sdd-plan skill to help you create a new specification...

What feature or change would you like to plan?
```

Use the Skill tool to invoke sdd-plan:
```
Skill(sdd-toolkit:sdd-plan)
```

**Option 4: "View pending backlog"** (if pending_specs array has items)

Show the user the list of pending specs with their titles:

```bash
# Get the list of pending specs from get-session-info
# Display formatted list to user
```

Example display:
```
📋 Pending Backlog (3 specs):

1. user-onboarding-2025-10-15-001
   Title: User Onboarding Flow Redesign

2. api-versioning-2025-10-18-002
   Title: API Versioning Strategy

3. monitoring-dashboard-2025-10-20-001
   Title: Monitoring Dashboard Implementation
```

Then use AskUserQuestion to let user select which spec to activate:
```javascript
AskUserQuestion(
  questions: [{
    question: "Which pending spec would you like to activate?",
    header: "Activate",
    multiSelect: false,
    options: [
      {
        label: "spec-1-id",
        description: "Spec 1 title"
      },
      {
        label: "spec-2-id",
        description: "Spec 2 title"
      },
      // ... one option for each pending spec (up to 4 max for AskUserQuestion)
    ]
  }]
)
```

**After user selects a spec:**
```bash
# Activate the selected spec
sdd activate-spec SELECTED_SPEC_ID

# Inform user of success
echo "✅ Spec activated! The spec has been moved to specs/active/"

# Then automatically continue with sdd-next to find first task
I'll now help you find the first task to work on...
```

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

**If user selects "Other" or cancels:**
Exit gracefully without activating any spec.

**Option 5: "Something else"**
```bash
No problem! Let me know if you need any help with your project.
```

Exit gracefully without invoking any skills.

### Phase 6: Handle Multiple Specs (if applicable)

If user chose "Continue with next task" and there are multiple specs:

**Show spec selection:**
```
Which specification would you like to work on?
```

Use AskUserQuestion to let them choose the spec, then invoke sdd-next with that context.

## Important Notes

- **⛔ NEVER READ SPECS DIRECTLY**: Do NOT use Read() on .json spec files. Always use `sdd-next` skill or helper commands.
- **Auto-execution**: This command automatically invokes skills based on user choice (no additional confirmation needed)
- **Non-intrusive**: If no active work found, gracefully offer to start new or exit
- **Fast**: Discovery should complete in <500ms using helper commands
- **Robust**: Handle missing directories or malformed JSON spec files gracefully
- **Token efficiency**: Helper scripts parse specs efficiently - reading 50KB JSON files wastes tokens

## Helper Script Reference

The `skills-dev start-helper` CLI provides:
- `check-permissions` - Check if SDD permissions are configured (returns JSON)
- `check-git-config` - Check if git integration is configured (returns JSON)
- `setup-git-config` - Interactive git configuration wizard
- `format-output` - Returns human-readable formatted text with last-accessed task info (PREFERRED - use this for display)
- `get-session-info` - Returns session state with last-accessed task as JSON (for programmatic access)
- `find-active-work` - Returns JSON with all resumable specs (for programmatic use)

**Always use `format-output` for presenting information to the user** - it ensures proper newlines, indentation, and formatting. Use `get-session-info` when you need programmatic access to last-accessed task data.

**Note**: All commands use the unified CLI: `sdd skills-dev start-helper <command>`

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
