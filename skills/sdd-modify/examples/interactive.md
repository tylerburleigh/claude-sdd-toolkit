# Example: Interactive Guided Modification (Future Enhancement)

This example demonstrates the planned interactive guided modification workflow, which will be implemented in Phase 2.

## Status: PLANNED FOR PHASE 2

**Current Status:** The interactive guided modification feature is **NOT YET IMPLEMENTED**. This document describes the planned user experience for future reference.

**For now, use:**
- **Workflow 1:** `apply-review.md` - Apply review feedback
- **Workflow 2:** `bulk-modify.md` - Bulk modifications from JSON

## Scenario (Future)

You want to make a few quick modifications to a spec but don't want to create a full JSON modification file. The interactive mode will guide you through making changes step-by-step with real-time previews and validation.

## Planned User Experience

### Step 1: Invoke Interactive Mode

Start the interactive modification skill:

```bash
Skill(sdd-toolkit:sdd-modify) "Guide me through updating spec my-spec-001 interactively"
```

### Step 2: Initial Prompt

The skill will present an interactive menu:

```
🔧 Interactive Spec Modification

Spec: my-spec-001 - User Authentication System
Status: active
Phases: 3 (15 tasks total)

What would you like to do?

1. Update task description
2. Add verification step
3. Update task metadata
4. Add new task
5. Remove task
6. Review and apply all changes
7. Cancel

Your choice (1-7):
```

### Step 3: Choose Operation

User selects an operation, for example: `1` (Update task description)

```
You selected: Update task description

📋 Tasks in spec my-spec-001:

Phase 1: Setup and Planning
  task-1-1: Initialize project structure [completed]
  task-1-2: Set up development environment [completed]
  task-1-3: Create initial documentation [completed]

Phase 2: Core Implementation
  task-2-1: Implement OAuth 2.0 authentication [in_progress]
  task-2-2: Add login endpoint [pending]
  task-2-3: Add logout endpoint [pending]
  task-2-4: Implement token refresh [pending]

Phase 3: Testing and Deployment
  task-3-1: Write unit tests [pending]
  task-3-2: Write integration tests [pending]
  task-3-3: Deploy to staging [pending]
  task-3-4: Deploy to production [pending]

Which task would you like to update? (enter task-id or type 'back'):
```

### Step 4: Select Target

User enters task ID, for example: `task-2-1`

```
Selected: task-2-1 (Implement OAuth 2.0 authentication)

Current description:
"Implement OAuth 2.0 authentication"

Current details:
  Status: in_progress
  Category: implementation
  Estimated hours: 8.0
  Actual hours: 5.5
  Command: pytest tests/test_auth.py -v

What would you like to change?

1. Update description
2. Update command
3. Update category
4. Back to task selection

Your choice (1-4):
```

### Step 5: Specify Change

User selects field, for example: `1` (Update description)

```
You selected: Update description

Current: "Implement OAuth 2.0 authentication"

Enter new description (or type 'cancel' to abort):
```

User enters new description:
```
Implement OAuth 2.0 authentication with PKCE flow, JWT tokens (15min expiry), and refresh token rotation (7 days expiry)
```

### Step 6: Preview Change

The skill shows a preview:

```
📝 Preview Change

Task: task-2-1 (Phase 2)
Field: description

Current:
  "Implement OAuth 2.0 authentication"

New:
  "Implement OAuth 2.0 authentication with PKCE flow, JWT tokens (15min expiry), and refresh token rotation (7 days expiry)"

Length: 33 chars → 138 chars (+105 chars)

This change will:
  ✓ Make task description more specific
  ✓ Document token expiry details
  ✓ Clarify authentication flow

Validation: ✓ No issues detected

Do you want to:
1. Apply this change now
2. Stage for batch application (add more changes first)
3. Edit again
4. Cancel this change

Your choice (1-4):
```

### Step 7: Stage or Apply

User selects: `2` (Stage for batch application)

```
✓ Change staged for batch application

Staged changes: 1

What would you like to do next?

1. Update task description (add another change)
2. Add verification step (add another change)
3. Update task metadata (add another change)
4. Add new task (add another change)
5. Remove task (add another change)
6. Review and apply all staged changes
7. Cancel all changes

Your choice (1-7):
```

User continues adding more changes, for example: `2` (Add verification step)

### Step 8: Add Verification Step

```
You selected: Add verification step

Which task should this verification step belong to? (enter task-id):
```

User enters: `task-2-1`

```
Task: task-2-1 (Implement OAuth 2.0 authentication with PKCE flow...)

Current verification steps:
  verify-2-1-1: User can authenticate with valid credentials
  verify-2-1-2: Invalid credentials are rejected

Next available verify_id: verify-2-1-3

Verification step description:
```

User enters:
```
Verify token expiration and refresh flow works correctly
```

Skill prompts:
```
Command to run (optional, press Enter to skip):
```

User enters:
```
pytest tests/test_auth.py::test_token_lifecycle -v
```

### Step 9: Preview Verification Addition

```
📝 Preview Change

Task: task-2-1 (Phase 2)
Operation: Add verification step

Details:
  Verify ID: verify-2-1-3
  Description: "Verify token expiration and refresh flow works correctly"
  Command: pytest tests/test_auth.py::test_token_lifecycle -v

This will add a new verification step to task-2-1 (total: 3 steps)

Validation: ✓ No issues detected
  ✓ verify_id format valid
  ✓ verify_id available (no conflict)
  ✓ test command looks valid

Do you want to:
1. Apply this change now
2. Stage for batch application (add more changes first)
3. Edit again
4. Cancel this change

Your choice (1-4):
```

User selects: `2` (Stage for batch)

```
✓ Change staged for batch application

Staged changes: 2

What would you like to do next?

1. Update task description (add another change)
2. Add verification step (add another change)
3. Update task metadata (add another change)
4. Add new task (add another change)
5. Remove task (add another change)
6. Review and apply all staged changes
7. Cancel all changes

Your choice (1-7):
```

User selects: `6` (Review and apply all)

### Step 10: Review All Staged Changes

```
📋 Review Staged Changes

You have 2 staged modifications:

───────────────────────────────────────────────────────────────
[1] Update task description
    Task: task-2-1
    Field: description
    Current: "Implement OAuth 2.0 authentication"
    New: "Implement OAuth 2.0 authentication with PKCE flow, JWT tokens (15min expiry), and refresh token rotation (7 days expiry)"
───────────────────────────────────────────────────────────────
[2] Add verification step
    Task: task-2-1
    Verify ID: verify-2-1-3
    Description: "Verify token expiration and refresh flow works correctly"
    Command: pytest tests/test_auth.py::test_token_lifecycle -v
───────────────────────────────────────────────────────────────

Impact Summary:
  Tasks affected: 1
  Verification steps added: 1
  Total modifications: 2

Validation: ✓ All changes valid

What would you like to do?

1. Apply all changes now
2. Save to JSON file (for later application)
3. Edit a change (enter number 1-2)
4. Remove a change (enter number 1-2)
5. Cancel all changes

Your choice (1-5):
```

### Step 11: Apply or Save

User selects: `1` (Apply all now)

```
🔄 Applying Changes to my-spec-001

✓ Backup created: specs/.backups/my-spec-001-20251106-144522.json
✓ Loaded spec: my-spec-001

Applying staged modifications...

[1/2] ✓ Updated task-2-1 description
[2/2] ✓ Added verification step verify-2-1-3 to task-2-1

Running validation...
✓ Spec structure valid
✓ All references valid
✓ No schema violations

✓ Validation passed

═══════════════════════════════════════════════════════════════

✅ MODIFICATIONS APPLIED SUCCESSFULLY

Applied: 2 modifications
Backup: specs/.backups/my-spec-001-20251106-144522.json

Changes:
  - Updated 1 task description
  - Added 1 verification step

═══════════════════════════════════════════════════════════════

Would you like to:
1. Make more changes to this spec
2. Make changes to a different spec
3. Exit

Your choice (1-3):
```

User selects: `3` (Exit)

```
✓ Interactive modification session complete

Summary:
  - Modified spec: my-spec-001
  - Total modifications: 2
  - Backup: specs/.backups/my-spec-001-20251106-144522.json

Thank you for using interactive spec modification!
```

## Alternative: Save to JSON for Review

In Step 11, if the user had selected `2` (Save to JSON), the workflow would be:

```
💾 Saving Staged Changes to File

Filename to save (default: my-spec-001-interactive-mods.json):
```

User presses Enter to use default:

```
✓ Saved 2 modifications to my-spec-001-interactive-mods.json

File location: my-spec-001-interactive-mods.json

To apply later:
  sdd apply-modifications my-spec-001 --from my-spec-001-interactive-mods.json --dry-run  # preview
  sdd apply-modifications my-spec-001 --from my-spec-001-interactive-mods.json           # apply

Would you like to:
1. Make more changes to this spec
2. Make changes to a different spec
3. Exit

Your choice (1-3):
```

## Planned Features

### Smart Suggestions

The interactive mode will provide context-aware suggestions:

```
Enter new description:
(Press Tab for suggestions based on task category and phase)

Suggestions:
  - "Implement OAuth 2.0 authentication with..."
  - "Add OAuth 2.0 authentication flow using..."
  - "Create OAuth 2.0 authentication system with..."
```

### Undo/Redo in Session

```
Staged changes: 3

Commands:
  - Type 'undo' to remove last staged change
  - Type 'redo' to restore undone change
  - Type 'list' to see all staged changes
  - Type 'clear' to remove all staged changes
```

### Copy from Similar Task

```
Update task description for task-3-1

Current: "Write tests"

Options:
  1. Enter new description manually
  2. Copy from similar task (task-2-3: "Write comprehensive tests...")
  3. Use template

Your choice (1-3):
```

### Validation Warnings

```
⚠️  Warning: Task description is very long (245 characters)

Recommendation: Consider breaking this into multiple tasks or simplifying

Do you want to:
1. Keep it as-is
2. Edit it to be shorter
3. Cancel this change

Your choice (1-3):
```

### Batch Operations

```
You selected: Update multiple task descriptions

Select tasks to update (comma-separated task IDs):
```

User enters: `task-2-1, task-2-2, task-2-3`

```
You selected 3 tasks:
  - task-2-1: Implement OAuth 2.0 authentication
  - task-2-2: Add login endpoint
  - task-2-3: Add logout endpoint

Apply same change to all? (y/n):
```

## When This Will Be Available

**Target:** Phase 2 implementation (Q1 2026)

**Current alternatives:**
1. Use `apply-review.md` workflow for review-based modifications
2. Use `bulk-modify.md` workflow for planned batch modifications
3. Manually edit JSON modification files and apply with CLI

## Design Goals (Phase 2)

1. **Progressive disclosure** - Show only relevant options at each step
2. **Clear previews** - Always show exactly what will change
3. **Undo/redo** - Allow experimentation without fear
4. **Smart suggestions** - Context-aware recommendations
5. **Batch operations** - Group related changes efficiently
6. **Validation feedback** - Real-time validation with helpful messages
7. **Save/resume** - Save in-progress sessions for later
8. **Templates** - Common modification patterns as reusable templates

## Feedback Welcome

If you have ideas for the interactive mode, please share:
- What operations would you use most?
- What workflow patterns would be helpful?
- What validations or suggestions would you want?
- What makes the interaction smooth vs. frustrating?

## Summary

Interactive guided modification (planned for Phase 2) will provide:
- ✅ **Step-by-step guidance** - No need to remember JSON schema
- ✅ **Real-time validation** - Catch errors immediately
- ✅ **Clear previews** - See changes before applying
- ✅ **Flexible workflow** - Apply immediately or stage for batch
- ✅ **Smart suggestions** - Context-aware recommendations
- ✅ **Undo/redo support** - Experiment freely
- ✅ **Save sessions** - Resume later if needed

**For now, use:**
- Workflow 1: Review feedback workflow (`apply-review.md`)
- Workflow 2: Bulk modification workflow (`bulk-modify.md`)

Both workflows provide systematic, safe spec modification with the current CLI tools.
