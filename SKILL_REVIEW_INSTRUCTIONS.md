# CLI Output Audit Instructions

## Purpose

Apply YAGNI (You Aren't Gonna Need It) and KISS (Keep It Simple, Stupid) principles to CLI output. Users should see **outcomes, not process steps**. Internal implementation details should be silent unless they fail.

## Automation with Task Tool

**Recommended approach:** Use the Task tool with a general-purpose Haiku agent to perform these audits efficiently.

### Why Haiku?

This audit process is:
- ✅ **Well-documented** - Clear step-by-step instructions
- ✅ **Process-following** - No complex reasoning required
- ✅ **Structured** - Known file locations and patterns
- ✅ **Repetitive** - Same steps for each command

**Cost comparison:**
- Haiku: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- Sonnet: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Haiku is ~12x cheaper** for output-heavy tasks like this

**When to use Sonnet instead:**
- Complex codebase exploration with vague requirements
- Creative problem-solving needed
- Multiple architectural decisions
- Ambiguous or incomplete instructions

### Example Invocation

```python
Task(
  subagent_type="general-purpose",
  model="haiku",  # Explicit Haiku for cost/speed
  description="Audit sdd-next CLI output",
  prompt="""Follow the audit process documented in SKILL_REVIEW_INSTRUCTIONS.md
to analyze the `sdd-next` command for YAGNI/KISS compliance.

Start by:
1. Examining the registry to find the sdd-next module path
2. Finding the related SKILL.md file (should be in skills/sdd-next/SKILL.md)
3. Reading the CLI implementation to trace all printer output
4. Simulating what the actual output looks like for a typical command
5. Applying the YAGNI/KISS analysis to determine if output is too verbose
6. Documenting findings following the format in the instructions

Provide a complete analysis similar to what was done for sdd-update, including:
- Current output simulation (line by line)
- Classification of each line (keep/remove/consolidate)
- Proposed minimal output
- Line count reduction percentage
- Root cause explanation
- Final verdict (Appropriate/Minor issues/Too verbose)

Save your complete analysis to: docs/research/cli-output-audit-sdd-next.md"""
)
```

### When NOT to Use Automation

**Manual audit is better when:**
- First audit ever (to validate the instructions work)
- Instructions need refinement based on edge cases
- Command has unusual architecture requiring human judgment
- Results will inform major architectural changes

**Rule of thumb:** Do the first 2-3 audits manually, then automate the rest once the process is proven.

### Batch Processing

To audit all commands efficiently:

```python
# Get list of commands from registry
commands_to_audit = [
  "sdd-next",
  "sdd-plan",
  "sdd-plan-review",
  "sdd-fidelity-review",
  "sdd-pr",
  "sdd-render"
]

# Launch all audits in parallel
for command in commands_to_audit:
    Task(
      subagent_type="general-purpose",
      model="haiku",
      description=f"Audit {command} CLI output",
      prompt=f"Follow SKILL_REVIEW_INSTRUCTIONS.md to audit `{command}` command..."
    )
```

**Note:** Launch these in a **single message with multiple Task calls** for true parallel execution, not in a loop.

## Output Location and File Naming

All audit results must be saved to a consistent location with descriptive filenames.

### Directory

**Location:** `docs/research/`

This directory contains all research outputs, analysis documents, and audit reports. It is separate from:
- `docs/` - Production documentation for users
- `specs/` - Specification files for active development

### Filename Convention

**Pattern:** `cli-output-audit-<command-name>.md`

**Examples:**
- `cli-output-audit-sdd-update.md`
- `cli-output-audit-sdd-validate.md`
- `cli-output-audit-sdd-next.md`
- `cli-output-audit-sdd-plan.md`

**Multi-file audits:**
When creating multiple related documents:
- Main audit: `cli-output-audit-<command-name>.md` (detailed line-by-line analysis)
- Summary: `cli-output-audit-<command-name>-summary.md` (action items & priorities)
- Comparative: `cli-output-audit-comparative.md` (cross-command patterns)

### Required in Task Prompts

When invoking the Task tool, **always** include the save location in the prompt:

```python
prompt="""Follow SKILL_REVIEW_INSTRUCTIONS.md to audit sdd-next...

[...rest of prompt...]

Save your complete analysis to: docs/research/cli-output-audit-sdd-next.md"""
```

This ensures agents know exactly where to save their output and maintains consistency across all audits.

## Audit Process

### Step 1: Identify the Command Module

1. Open the registry file: `/src/claude_skills/claude_skills/cli/sdd/registry.py`
2. Select one registered module (e.g., `register_update`, `register_validate`, `register_plan`)
3. Note the module path from the import statement

**Example:**
```python
from claude_skills.sdd_update.cli import register_update
# Module: sdd_update
# CLI file: /src/claude_skills/claude_skills/sdd_update/cli.py
```

### Step 2: Find Related Documentation

1. Search for SKILL.md files that reference these commands:
   ```bash
   find . -name "SKILL.md" -exec grep -l "sdd command-name" {} \;
   ```

2. Read the SKILL.md to understand:
   - What the command is supposed to do (user's mental model)
   - What examples show as expected output
   - What information users need to make decisions

### Step 3: Trace the Implementation

1. Read the CLI command handler (e.g., `cmd_complete_task`)
2. Follow the call chain to see all operations
3. For each operation, grep for printer calls:
   ```bash
   grep -n "printer\.\(action\|success\|info\|warning\|error\)" file.py
   ```

4. Document each message with:
   - Line number
   - Message type (action/info/success)
   - Message content
   - Whether it's called during composition (e.g., complete-task calls update-status)

**Example:**
```
status.py:89   action   "Loading state for {spec_id}..."           [internal]
status.py:137  action   "Recalculating progress..."                [internal]
status.py:141  action   "Saving JSON spec..."                      [internal]
status.py:146  success  "Task {task_id} status updated to '{new_status}'" [outcome]
```

### Step 4: Simulate Actual Output

Create a realistic example of what the user sees when running the command:

```
$ sdd complete-task my-spec task-1-1

Completing task task-1-1...
Tracking updates...
Loading state for my-spec...           ← Implementation detail
Task: Implement authentication
Status: in_progress → completed
Recalculating progress...              ← Implementation detail
Saving JSON spec...                    ← Implementation detail
Task task-1-1 status updated to 'completed'
Automatically calculated time: 2.345h
Journal Entry:                         ← Verbose structure
  Title: Task Completed: ...
  Type: status_change
  Content: ...
Journal entry added to my-spec.json
Metadata updates:                      ← Internal operation
  progress_percentage: 25 → 50
Synchronized 2 metadata field(s)
Auto-journaled 1 parent node(s): phase-1
Creating git commit...
Created commit: a1b2c3d4
```

Count the lines. Typical commands produce 15-25 lines.

### Step 5: Apply YAGNI/KISS Analysis

For each line of output, ask:

1. **Does the user need this to:**
   - Know if the command succeeded? (required)
   - Understand what changed? (required)
   - Make a decision about next steps? (required)
   - Debug an error? (only if error occurred)

2. **Is this an implementation detail?**
   - Loading files → YES (internal)
   - Saving files → YES (internal)
   - Recalculating → YES (internal)
   - Status transition → NO (outcome)
   - Side effects → NO (outcome)

3. **Is this redundant?**
   - If task completion includes journaling, don't separately confirm journal was added
   - If metadata sync always happens, don't announce it unless it fails

**Classification:**
- ✅ **Keep** - Outcome, side effect, or error
- ❌ **Remove** - Implementation detail, internal operation
- 🔄 **Consolidate** - Can be merged into a more concise message

### Step 6: Design Minimal Output

What would the output look like if we only showed what users need?

**Principles:**
- **One success indicator** per command (not per sub-operation)
- **Show state transitions** (before → after)
- **Show side effects** (parent completions, commits, file changes)
- **Omit internal operations** (load, save, recalculate, sync)
- **Use compact formatting** (indented details, not separate "Metadata updates:" sections)

**Example Minimal Output:**
```
$ sdd complete-task my-spec task-1-1

✓ Task completed: Implement authentication (task-1-1)
  Status: in_progress → completed
  Time: 2.35h
  Auto-completed: phase-1
  Commit: a1b2c3d4
```

**Calculate reduction:** 5 lines instead of 20 = **75% reduction**

### Step 7: Identify Root Causes

Explain WHY the output is verbose:

Common patterns:
1. **Sub-operation verbosity:** Each function (update, journal, sync) prints its own workflow because it can be called standalone
2. **Defensive logging:** "Saving..." messages to show progress for slow operations
3. **Over-explanation:** Showing what fields changed in metadata (internal state)
4. **Structural announcements:** "Journal Entry:", "Metadata updates:" headers with indented details

**Example:**
```
Root Cause: Each operation (update_task_status, add_journal_entry, sync_metadata_from_state)
was designed to be called independently via CLI, so each prints its own complete workflow.
When composed into complete-task, all these messages stack up.
```

### Step 8: Document Findings

Create a summary with:

1. **Command analyzed:** `sdd complete-task`
2. **Current line count:** ~20 lines
3. **Proposed line count:** ~5 lines
4. **Reduction:** 75%
5. **Issues found:**
   - List specific issues with file:line references
   - Classify as: implementation detail, redundant, over-verbose
6. **Recommended output:**
   - Show the minimal version
7. **Root cause:**
   - Explain the structural reason for verbosity

### Step 9: Record Verdict

**Assessment categories:**
- ✅ **Appropriate** - Output follows YAGNI/KISS, shows only outcomes
- ⚠️ **Minor issues** - Mostly good, 1-2 improvements needed
- ❌ **Too verbose** - Significant reduction possible (>50% of lines are internal details)

**For this example:** ❌ Too Verbose

## Quick Reference Card

| Message Type | Keep? | Reason |
|--------------|-------|--------|
| `printer.action("Loading...")` | ❌ | Implementation detail |
| `printer.action("Saving...")` | ❌ | Implementation detail |
| `printer.action("Recalculating...")` | ❌ | Internal operation |
| `printer.success("Task updated")` | ✅ | Outcome |
| `printer.info("Status: X → Y")` | ✅ | State transition |
| `printer.info("Auto-completed: phase-1")` | ✅ | Side effect |
| `printer.info("Metadata updates:")` | ❌ | Internal structure |
| `printer.error("Failed to load")` | ✅ | Error (always show) |

## JSON Output Exception

If the command supports `--json` flag:
- Text output: Apply YAGNI/KISS strictly (minimal human-readable)
- JSON output: Include complete data (machines need everything)

**Example:**
```bash
# Text mode (minimal)
$ sdd complete-task my-spec task-1-1
✓ Task completed: task-1-1

# JSON mode (complete)
$ sdd complete-task my-spec task-1-1 --json
{
  "task_id": "task-1-1",
  "status": "completed",
  "actual_hours": 2.35,
  "metadata": {...},
  "journal_entries_added": 1,
  "parents_completed": ["phase-1"],
  "commit_sha": "a1b2c3d4"
}
```

## Next Steps After Audit

Once the audit is complete:

1. **Create an issue/spec** describing the changes needed
2. **Design the new output format** for each command
3. **Implement a verbosity control:**
   - Default: Minimal (outcomes only)
   - `--verbose`: Show internal operations
   - `--quiet`: Only errors
4. **Update SKILL.md examples** to match new output
5. **Update tests** to expect new output format

## Examples from Other Commands

### Good Example: Git commit

```
$ git commit -m "Fix bug"
[main a1b2c3d] Fix bug
 3 files changed, 42 insertions(+), 7 deletions(-)
```

Concise: Shows branch, commit SHA, summary, file stats. No "Loading repository...", "Saving commit...", etc.

### Bad Example: Verbose npm

```
$ npm install package
npm WARN deprecated ...
npm WARN deprecated ...
npm notice created a lockfile as package-lock.json
added 42 packages from 17 contributors
audited 42 packages in 2.3s
found 0 vulnerabilities
```

Verbose: Multiple warnings, implementation details (lockfile), audit results (not requested).

## Conclusion

**Golden Rule:** The user asked for an outcome. Show them the outcome. Everything else is optional at best, noise at worst.
