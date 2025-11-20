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

### Phase 1: Run the Session Summary Once

Start every `/sdd-begin` invocation with a single command that gathers permissions, git status, and active work in one shot:

```bash
sdd skills-dev start-helper session-summary . --json
```

The JSON response contains:
- `permissions.status` (e.g., `fully_configured`, `partially_configured`, `not_configured`)
- `git.needs_setup` plus current `git.settings` when configured
- `active_work.text` (pre-formatted summary) and `active_work.pending_specs`
- `session_state.last_task`, `session_state.in_progress_count`, etc.

Use this single payload to decide what to do next:

1. **Permissions not fully configured** (`permissions.status != "fully_configured"`):
   - Explain what’s missing and offer to run `sdd skills-dev setup-permissions update .`.
   - After the helper finishes, rerun the session-summary command to refresh the status before proceeding.
2. **Git integration needs setup** (`git.needs_setup: true`):
   - Offer to run `sdd skills-dev setup-git-config .` (interactive wizard).
   - If the user declines, continue with read-only mode.
3. **Git already configured**:
   - Optionally display a short summary, e.g., `Git integration: ✅ Enabled (auto-branch, auto-commit per task, AI PRs)`.

---

### Phase 2: Review Active Work (No Extra Commands)

Use the `active_work.text` field from the session summary output. Display it exactly as returned—no manual formatting—and remind the user:
- **Never read specs directly.** Always rely on the helper output and SDD skills.
- The text already includes spec IDs, titles, progress, folder status, last accessed task, and in-progress counts.

Since `session-summary` also returns structured data, you can avoid additional helper invocations when presenting options later.

---

### Phase 3: Present Options Based on Findings

**If active work found:**

The formatted summary already includes:
- Number of specifications found (active and pending combined)
- For each spec: ID, title, progress, and folder status
  - Active specs: ⚡ (in_progress) or 📝 (pending status)
  - Pending specs: ⏸️ with [PENDING] label (backlog)
- 🕐 Last-accessed task information (if available)
- 💡 Count of in-progress tasks

Simply display the `active_work.text` block directly—no extra commands required.

**Determine what actionable work exists:**

Before presenting options, check the session summary data to understand what work is available:
- `session_state.active_specs`: Array of active specs with their status
- `session_state.in_progress_count`: Number of tasks currently in progress
- `active_work.specs`: All specs (with completed ones now filtered out by the helper)

**Has actionable incomplete tasks** if:
- Any spec in `active_work.specs` has `status == "in_progress"` AND `percentage < 100`, OR
- `session_state.in_progress_count > 0`

**If last-accessed task exists AND actionable tasks available:**

Use `session_state.last_task` and `active_work.pending_specs` from the session summary (no additional CLI calls needed).

Ask the user what they would like to do, with options:
1. Resume last task (auto-runs sdd-next with specific task)
2. Continue with next task (auto-runs sdd-next)
3. Write new spec (auto-runs sdd-plan)
4. View pending backlog (M specs) - **Only show if pending_specs array has items**
5. Something else (exit)

**If NO last-accessed task AND actionable tasks available:**

Use the pending backlog array from the session summary (`active_work.pending_specs`).

Ask the user what they would like to do, with options:
1. Continue with next task (auto-runs sdd-next)
2. Write new spec (auto-runs sdd-plan)
3. View pending backlog (M specs) - **Only show if pending_specs array has items**
4. Something else (exit)

**If NO actionable tasks (only pending specs OR no work):**

When there are no in-progress tasks, only pending specs with 0% progress:

Ask the user what they would like to do, with options:
1. View pending backlog (M specs) - **Show this as the PRIMARY option if pending_specs array has items**
2. Write new spec (auto-runs sdd-plan)
3. Something else (exit)

Do NOT show "Continue with next task" option when there are no actionable incomplete tasks.

**If NO active work found:**

The session summary's `active_work.text` will show:
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

**Before invoking sdd-next:**

If `session_state.active_specs` has more than 1 spec, ask the user which spec they want to work on:
- Use `AskUserQuestion` tool to present spec choices
- Show up to 4 specs (sorted by completion % as provided by the helper)
- Each option: `label` = spec_id, `description` = "title (XX% complete)"
- Set `header` = "Spec" and `multiSelect` = false

Example:
```
AskUserQuestion(
  questions: [{
    question: "Which specification would you like to work on?",
    header: "Spec",
    multiSelect: false,
    options: [
      { label: "spec-id-1", description: "Feature Title (45% complete)" },
      { label: "spec-id-2", description: "Another Feature (23% complete)" }
    ]
  }]
)
```

After user selects a spec (or if only 1 active spec exists), use the Skill tool to invoke sdd-next:
```
Skill(sdd-toolkit:sdd-next)
```

**IMPORTANT**: When invoking sdd-next, mention the spec_id from the last_task data (or selected spec) and the task_id if known.

**Option 2: "Continue with next task"**
```bash
I'll use the sdd-next skill to find and prepare the next task...
```

**Before invoking sdd-next:**

If `session_state.active_specs` has more than 1 spec, ask the user which spec they want to work on:
- Use `AskUserQuestion` tool to present spec choices
- Show up to 4 specs (sorted by completion % as provided by the helper)
- Each option: `label` = spec_id, `description` = "title (XX% complete)"
- Set `header` = "Spec" and `multiSelect` = false

Example:
```
AskUserQuestion(
  questions: [{
    question: "Which specification would you like to work on?",
    header: "Spec",
    multiSelect: false,
    options: [
      { label: "spec-id-1", description: "Feature Title (45% complete)" },
      { label: "spec-id-2", description: "Another Feature (23% complete)" }
    ]
  }]
)
```

After user selects a spec (or if only 1 active spec exists), use the Skill tool to invoke sdd-next:
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

Use `active_work.pending_specs` from the session-summary output to display the backlog (no additional commands required).

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

### Phase 6: Invoke sdd-next with Context

After the user has selected a spec (from Phase 5), invoke sdd-next with the appropriate context:

**For "Resume last task":**
- Mention both the spec_id and task_id from `session_state.last_task`
- Example: "I'll help you resume work on task `task-2-1` from spec `user-auth-2025-10-15-001`..."

**For "Continue with next task":**
- Mention the spec_id that was selected (or the only active spec if there was only one)
- Example: "I'll use sdd-next to find the next task in spec `api-refactor-2025-10-18-002`..."

**For newly activated specs (from pending backlog):**
- After activation succeeds, mention the spec_id
- Example: "Spec activated! I'll now help you find the first task in `monitoring-2025-10-20-001`..."

The sdd-next skill will use this context to:
1. Load the correct specification
2. Identify the appropriate task to work on
3. Present the task plan for user approval
4. Guide the implementation

## Important Notes

- **⛔ NEVER READ SPECS DIRECTLY**: Do NOT use Read() on .json spec files. Always use `sdd-next` skill or helper commands.
- **Auto-execution**: This command automatically invokes skills based on user choice (no additional confirmation needed)
- **Non-intrusive**: If no active work found, gracefully offer to start new or exit
- **Fast**: Discovery should complete in <500ms using helper commands
- **Robust**: Handle missing directories or malformed JSON spec files gracefully
- **Token efficiency**: Helper scripts parse specs efficiently - reading 50KB JSON files wastes tokens
