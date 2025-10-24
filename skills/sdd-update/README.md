# sdd-update

A Claude skill for managing specification documents during spec-driven development. Handles status updates, progress tracking, decision journaling, and file organization.

## What This Skill Does

This skill manages the **documents** during implementation, not the code itself. It focuses on:

- ✅ Updating task status in the progress tracker (pending → in_progress → completed)
- ✅ Calculating and updating progress indicators
- ✅ Adding journal entries for decisions and deviations
- ✅ Recording verification results
- ✅ Moving specs between lifecycle folders (active/completed/archived)
- ✅ Managing spec frontmatter metadata
- ✅ Tracking blockers and dependencies
- ✅ Time tracking (estimated vs actual)
- ✅ Multi-tool coordination support

## What This Skill Does NOT Do

- ❌ Create new specifications (use sdd-plan)
- ❌ Write implementation code
- ❌ Run tests or verification commands
- ❌ Make architecture decisions

## When to Use This Skill

Use this skill when:
- You've finished implementing a task and need to mark it complete
- You need to document a decision or deviation from the spec
- You want to check overall progress or find next available tasks
- A task is blocked and you need to document why
- You've completed all verifications for a phase
- Your spec is fully implemented and needs to move to completed/
- You need to update any spec metadata or status

## Two Ways to Use This Skill

### 1. Natural Language (With Claude)

Ask Claude to perform operations in natural language. Claude will use the appropriate tools automatically.

```
"Mark task-1-2 as completed and add a journal entry"
```

### 2. Direct CLI (Without Claude)

Use the command-line tools directly for automation, scripts, or manual updates.

```bash
python3 scripts/sdd-update-tools.py update-status \
  user-auth-2025-10-18-001 task-1-2 completed
```

**CLI Benefits:**
- Faster for batch operations
- Integration with CI/CD pipelines
- No Claude API calls needed
- Scripting and automation
- `--dry-run` preview mode
- `--json` output for parsing

See [CLI Tools Documentation](#python-tools-direct-cli-usage) below for complete reference.

## Quick Start

### 1. Mark a Task as Complete

```
"I just finished implementing task-1-2 (User model). Update the progress tracker and add a journal entry."
```

Claude will:
- Update the task status to "completed" in the progress tracker
- Add completion timestamp
- Recalculate parent progress
- Add a journal entry documenting the completion

### 2. Document a Deviation

```
"I had to split the authentication logic into a separate service file instead of adding it to userService as planned. Document this deviation."
```

Claude will:
- Add a detailed journal entry explaining the deviation
- Update the spec version
- Modify the affected tasks in the spec document
- Document the reasoning and impact

### 3. Check Progress

```
"What's the current progress on user-auth-2025-10-18-001?"
```

Claude will:
- Load the progress tracker
- Show overall progress percentage
- List completed/pending phases
- Identify next available tasks

### 4. Move Completed Spec

```
"All tasks are done and verified. Move user-authentication.md to the completed folder."
```

Claude will:
- Verify 100% completion
- Update frontmatter status
- Add final journal entry
- Move file to specs/completed/

## File Structure

This skill works with the following structure:

```
project/
├── specs/
│   ├── active/                    # Specs being implemented
│   │   └── user-authentication.md
│   ├── completed/                 # Finished specs
│   │   └── user-profiles.md
│   ├── archived/                  # Old/superseded specs
│   │   └── legacy-auth.md
```

## What's Included

### Core Documentation
- **SKILL.md** - Complete skill guide for Claude
- **README.md** - This file
- **LICENSE.txt** - MIT license

### Reference Materials
- **EXAMPLES.md** - Real-world examples of all operations
- **QUICK_REFERENCE.md** - One-page command cheat sheet

## Example Operations

### Update Task Status
```
"Mark task-2-3 as in_progress and add a journal entry that I'm starting work on the auth routes."
```

### Document a Blocker
```
"Task-3-1 is blocked because Redis isn't provisioned yet. Document this blocker with ticket number OPS-1234."
```

### Record Verification Results
```
"All Phase 1 verifications passed. Add the verification results to the spec document."
```

### Check Next Tasks
```
"What tasks are ready to work on next? Show me pending tasks with no blockers."
```

### Complete a Phase
```
"Phase 1 is done - all tasks complete and verified. Update the status and add a completion journal entry."
```

## Integration with sdd-plan

These two skills work together:

1. **sdd-plan** (separate):
   - Creates initial specifications
   - Generates task hierarchies
   - Initializes progress metadata
   - Plans phases and tasks

2. **sdd-update Skill** (this skill):
   - Updates task status during implementation
   - Tracks progress
   - Documents decisions
   - Manages lifecycle

**Workflow:**
1. Use sdd-plan to plan: "Create a spec for user authentication"
2. Review and approve the spec
3. Use sdd-update during work: "Mark task-1-2 as complete"
4. Use sdd-update to finalize: "Move completed spec to completed folder"

## Multi-Tool Support

This skill maintains a shared progress tracker that works across different AI tools:

- **Claude** creates spec, marks some tasks complete
- **Cursor** reads the tracker, implements more tasks, updates progress
- **Windsurf** reads the tracker, implements final tasks
- **Claude** reviews the tracker, verifies everything done, moves to completed/

The shared progress format enables this handoff pattern.

## Key Principles

1. **Document Reality** - Specs reflect actual progress, not wishful thinking
2. **Update Immediately** - Don't wait; update status as work happens
3. **Preserve History** - Never delete journal entries or revisions
4. **Validate Always** - Check JSON structure before saving
5. **Coordinate Carefully** - Respect multi-tool workflows

## Common Use Cases

### During Implementation
- "I finished the User model. Mark task-1-2 complete."
- "What's the next task I should work on?"
- "I'm starting work on task-2-1, update the tracker."

### Handling Issues
- "Task-3-1 is blocked by missing Redis. Document this."
- "I had to change the approach for auth. Document deviation."
- "Phase 2 took longer than expected. Update time tracking."

### Verification & Completion
- "All Phase 1 tests passed. Add verification results."
- "Phase 1 is complete. Update status and add journal entry."
- "Spec is 100% done. Move to completed folder."

### Status & Progress
- "What's the overall progress?"
- "Show me all blocked tasks."
- "How long did Phase 2 actually take?"
- "List all pending tasks in phase-1."

## Tips for Success

1. **Update Often** - Don't batch updates; do them as work happens
2. **Be Specific** - Include details in journal entries for future reference
3. **Track Deviations** - Document why you diverged from the plan
4. **Validate State** - Check JSON is valid before saving
5. **Backup First** - Keep backups of the progress tracker before major updates
6. **Coordinate Handoffs** - Add journal entries when passing work to others

## Troubleshooting

### Progress Tracker Won't Load
- Check JSON syntax with `jq empty TRACKER_FILE`
- Look for backup: `TRACKER_FILE.backup`
- Regenerate from spec if needed

### Progress Seems Wrong
- Recalculate from leaf nodes up
- Verify all parent-child relationships
- Check for orphaned tasks

### Can't Find Next Task
- List all pending tasks
- Check for blockers
- Verify dependencies are met

## Resources

- **Quick Reference**: See QUICK_REFERENCE.md for command cheat sheet
- **Examples**: Check EXAMPLES.md for detailed walkthroughs
- **Spec Creation**: See sdd-plan for planning
- **JSON Spec Format**: Reference json-spec-format.md for structure

## Support

For questions or issues:
1. Check the quick reference guide
2. Review the examples
3. Consult the main SKILL.md documentation

## License

MIT License - See LICENSE.txt for details.

---

**Remember**: This skill manages the documents, not the code. Use it to keep your specifications accurate and current as development progresses.

**Pair with**: sdd-plan for the complete spec-driven development workflow.

---

## Python Tools (Direct CLI Usage)

For advanced users or automation, sdd-update now includes Python command-line tools that can be used directly without Claude.

### Quick Start

```bash
# Update task status
python3 scripts/sdd-update-tools.py update-status my-spec-2025 task-1-1 completed --note "Implementation successful"

# Mark task as blocked
python3 scripts/sdd-update-tools.py mark-blocked my-spec-2025 task-2-1 --reason "Waiting on Redis provisioning" --type dependency

# Add journal entry
python3 scripts/sdd-update-tools.py add-journal specs/active/my-spec.md --title "Blocker Resolved" --content "Redis available"

# Generate status report
python3 scripts/sdd-update-tools.py status-report my-spec-2025
```

### Available Commands

All commands support `--json`, `--dry-run`, `--quiet`, and `--verbose` options.

**Status Management:**
- `update-status` - Update task status with auto progress recalculation
- `mark-blocked` - Mark task as blocked with detailed metadata
- `unblock-task` - Resume a blocked task

**Documentation:**
- `add-journal` - Add entry to Implementation Journal
- `update-frontmatter` - Modify spec frontmatter field
- `add-verification` - Document verification results

**Lifecycle:**
- `move-spec` - Move spec between active/completed/archived
- `complete-spec` - Mark spec complete and move to completed/

**Time Tracking:**
- `track-time` - Record time spent on task
- `time-report` - Generate time variance analysis

**Validation:**
- `validate-spec` - Check progress tracker consistency
- `status-report` - Get comprehensive progress report  
- `audit-spec` - Deep audit with circular dependency detection

### Architecture

The tools use a modular design with shared utilities from `sdd-common`:

```
sdd-update/scripts/
├── sdd-update-tools.py      # CLI entry point
└── operations/               # Modular operations
    ├── status.py
    ├── journal.py
    ├── verification.py
    ├── lifecycle.py
    ├── time_tracking.py
    └── validation.py
```

**Safety features:**
- Automatic backups before tracker updates
- Atomic writes (temp file → rename)
- JSON validation before saving
- Progress recalculation after changes

### Full Documentation

See [Python Tools README](README-tools.md) for complete command reference and examples.
