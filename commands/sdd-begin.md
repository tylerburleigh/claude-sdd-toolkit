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

Ask the user if they would like to add the missing permissions now, with options to add them or continue anyway.

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

Ask the user if they would like to set up SDD permissions now, with options to set up permissions (auto-runs setup) or skip for now.

**If user chooses "Yes, set up permissions":**
```bash
# Run the setup helper to configure .claude/settings.local.json
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

Ask the user if they would like to configure git integration, with options to configure now (runs interactive wizard) or skip for now.

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

Ask the user what they would like to do, with options:
1. Resume last task (auto-runs sdd-next with specific task)
2. Continue with next task (auto-runs sdd-next)
3. Write new spec (auto-runs sdd-plan)
4. View pending backlog (M specs) - **Only show if pending_specs array has items**
5. Something else (exit)

**If NO last-accessed task:**

First check if there are pending specs using the get-session-info output (check `pending_specs` array).

Ask the user what they would like to do, with options:
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

Ask the user what they would like to do, with options to write a new spec (auto-runs sdd-plan) or something else (exit).

### Phase 5: Execute User's Choice

Based on the user's selection:

**Option 1: "Resume last task"** (if last-accessed task available)
```bash
I'll help you resume work on task [task-id] from [spec-name]...
```

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

**IMPORTANT**: When invoking sdd-next, mention the spec_id from the last_task data and the task_id if known.

**Option 2: "Continue with next task"**
```bash
I'll use the sdd-next skill to find and prepare the next task...
```

Use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

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

Ask the user which pending spec they would like to activate, presenting each spec ID as an option with its title as the description (up to 4 max for AskUserQuestion).

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
