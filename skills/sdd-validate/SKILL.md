---
name: sdd-validate
description: Validate SDD JSON specs, auto-fix common issues, generate detailed reports, and analyze dependencies.
---

# Spec Validation Skill

## Overview

The **Skill(sdd-toolkit:sdd-validate)** skill provides comprehensive validation for Spec-Driven Development (SDD) JSON specification files. It checks for structural consistency, auto-fixes common issues, generates detailed reports, and analyzes dependencies. Use it to ensure a spec is structurally sound before running other SDD skills.

**Current capabilities:**
- Validate JSON spec structure, hierarchy integrity, and metadata presence
- Auto-fix 13 common issue types with preview and backup support
- Selective and interactive fix application
- Before/after diff reporting for transparency
- Generate detailed validation reports in Markdown or JSON format
- Calculate comprehensive spec statistics including depth, coverage, and complexity
- Analyze dependencies including cycles, orphans, deadlocks, and bottlenecks
- Differentiated exit codes for warnings vs errors

## When to Use This Skill

Reach for `Skill(sdd-toolkit:sdd-validate)` when you need to:
- Confirm a freshly created spec parses correctly
- Auto-fix common validation issues like missing metadata or incorrect counts
- Check for structural errors before running `Skill(sdd-toolkit:sdd-next)` or `Skill(sdd-toolkit:sdd-update)`
- Generate detailed validation reports for review or CI/CD
- Analyze spec statistics and complexity metrics
- Detect dependency issues including cycles, orphans, and bottlenecks

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (validate, fix, report, stats, check-deps, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd` CLI wrapper commands (e.g., `sdd validate`, `sdd fix`, `sdd report`, `sdd stats`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python sdd_validate.py`, `bash python cli.py`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## Quick Start

```bash
# Validate spec (human-readable output)
sdd validate specs/active/my-spec.json

# Validate with verbose issue details
sdd --verbose validate specs/active/my-spec.json

# Preview auto-fixable issues
sdd fix specs/active/my-spec.json --preview

# Apply auto-fixes with backup
sdd fix specs/active/my-spec.json

# Generate detailed report with stats and dependency analysis
sdd report specs/active/my-spec.json --format markdown --output -

# Print comprehensive statistics
sdd stats specs/active/my-spec.json

# Check for dependency issues including cycles and bottlenecks
sdd check-deps specs/active/my-spec.json
```

Global flags available on all commands:
- `--no-color` – disable colored output
- `--quiet` / `-q` – suppress progress messaging (still prints final results)
- `--json` – machine-readable JSON output for automation
- `--verbose` / `-v` – show detailed issue information with locations and categories

### Exit codes
- `0` – Validation succeeded (no errors detected)
- `1` – Validation found warnings only (spec is usable but has issues)
- `2` – Validation found errors (structural issues that need fixing)

**Note for AI assistants:** Exit code 2 indicates the validation tool successfully detected errors in the spec file. This is expected behavior when a spec has validation issues, not a command failure. The tool is working correctly by reporting these errors so they can be fixed.

## Guidelines for AI Assistants

**Important:** When working with `sdd validate` and `sdd fix`, follow these guidelines to avoid confusion and ensure effective validation workflows:

### 1. Exit Code 2 is NOT a Failure

**❌ Don't do this:**
```
I tried to validate the spec but got exit code 2. The command failed. Let me try again...
```

**✅ Do this instead:**
```
Validation found errors (exit code 2), which is expected. The spec has 12 issues that need fixing.
Running sdd fix to address auto-fixable issues...
```

**Why:** Exit code 2 means the validation tool successfully detected errors. This is the tool working correctly, not failing. Only treat exit codes like 127 (command not found) or segfaults as actual failures.

### 2. Always Re-validate After Fixing

**❌ Don't do this:**
```
$ sdd fix my-spec.json
✅ Applied 8 fixes
# Assume we're done and move on
```

**✅ Do this instead:**
```
$ sdd fix my-spec.json
✅ Applied 8 fixes

$ sdd validate my-spec.json
# Check if more issues remain or if new ones were revealed
```

**Why:** Fixing issues can reveal new problems that were previously hidden. Always validate after fixing to see the current state.

### 3. Track Error Count Progression

**❌ Don't do this:**
```
Pass 1: 88 errors
Pass 2: 4 errors
Pass 3: 4 errors
# Report: "Fix command isn't working, still getting errors"
```

**✅ Do this instead:**
```
Pass 1: 88 errors → fixed 84 → success!
Pass 2: 4 errors → no change after fix → plateau detected
# Switch to manual fixes with --verbose
```

**Why:** Error count progression tells you whether to continue auto-fixing or switch to manual intervention. Decreasing count = keep going. Plateau = switch to manual.

### 4. When to Report Issues vs Continue Fixing

**Continue fixing when:**
- Error count is decreasing with each pass
- `sdd fix` reports applying fixes successfully
- You're on pass 1-3 of the fix/validate cycle
- Auto-fixable count > 0

**Switch to manual intervention when:**
- Error count unchanged for 2+ passes (plateau)
- `sdd fix` reports "0 fixes applied" or "skipped issues"
- You've done 5+ passes without reaching exit code 0
- All remaining issues are marked "requires manual intervention"

**Report as a problem when:**
- `sdd validate` command itself fails (exit code 127, crash, etc.)
- `sdd fix` corrupts the spec file (use backup to restore)
- Infinite loop: error count oscillates without converging
- The tool reports an internal error or stack trace

**Example workflow:**
```bash
# Pass 1
$ sdd validate spec.json  # 88 errors (exit 2) ✅ Continue
$ sdd fix spec.json       # Applied 84 fixes ✅ Continue

# Pass 2
$ sdd validate spec.json  # 4 errors (exit 2) ✅ Continue
$ sdd fix spec.json       # Skipped 4 issues ⚠️ Check

# Pass 3
$ sdd validate spec.json  # 4 errors (exit 2) ⚠️ Plateau
# → Switch to manual: sdd validate spec.json --verbose
```

### 5. Use Verbose Mode for Details

When switching to manual fixes, always use `--verbose`:

```bash
$ sdd validate my-spec.json --verbose
❌ Validation found 4 errors

1. [ERROR] task-3-2: Circular dependency detected
   Location: hierarchy.task-3-2.dependencies
   Details: task-3-2 → task-3-5 → task-3-2
   # Now you know exactly what to fix
```

This provides locations, categories, and specific details needed for manual intervention.

## Command Reference

### validate
Validate the JSON spec structure and print a detailed pass/warn/fail summary.

```bash
sdd validate <spec-file.json> [--report] [--report-format {markdown,json}]
```

- Reads the spec file, performs structural validation, and prints a summary.
- With `--verbose`, includes detailed issue information with locations and categories.
- When `--report` is provided, generates a validation report alongside the spec.
- `--report-format` chooses between markdown (default) or json report format.
- With `--json`, prints structured JSON with error/warning counts and auto-fixable issue count.

**Exit codes:**
- `0` – Clean validation (no issues)
- `1` – Warnings only (usable but has non-critical issues)
- `2` – Errors detected (requires fixes) - *This is expected behavior when the spec has validation issues*

**Example output:**

Clean validation (exit code 0):
```bash
$ sdd validate my-spec.json
✅ Validation passed
   0 errors, 0 warnings
   All checks completed successfully

$ echo $?
0
```

Validation with warnings (exit code 1):
```bash
$ sdd validate my-spec.json
⚠️  Validation passed with warnings
   0 errors, 3 warnings
   - Task task-1-2: Missing estimated_hours in metadata
   - Task task-3-1: Verification command may be too broad
   - Phase phase-2: Consider adding risk assessment

$ echo $?
1
```

Validation with errors (exit code 2):
```bash
$ sdd validate my-spec.json
❌ Validation found 12 errors
   8 auto-fixable, 4 require manual intervention

   Errors:
   - 5 incorrect task count rollups
   - 2 missing metadata blocks
   - 1 orphaned node (task-5-3)
   - 2 circular dependencies
   - 2 parent/child mismatches

   Run 'sdd fix my-spec.json' to auto-fix 8 issues
   Use '--verbose' for detailed issue information

$ echo $?
2
```

### fix
Auto-fix common validation issues with preview and backup support.

```bash
sdd fix <spec-file.json> [--preview] [--dry-run] [--no-backup]
```

- Analyzes the spec and identifies auto-fixable issues.
- `--preview` or `--dry-run` shows what would be fixed without modifying files.
- By default, creates a backup file before applying fixes.
- `--no-backup` skips backup creation (use with caution).
- With `--json`, outputs structured fix report with applied/skipped counts.

**Auto-fixable issues (13 types):**
- Incorrect task count rollups (total_tasks, completed_tasks)
- Leaf node task count discrepancies
- Missing metadata blocks on tasks and phases
- Invalid verification_type values
- Parent/child hierarchy mismatches
- Orphaned nodes not reachable from spec-root
- Malformed ISO 8601 timestamps
- Invalid status field values
- Missing required node fields
- Empty node titles
- Invalid node types
- Bidirectional dependency inconsistencies
- Missing dependencies structure

**Important limitations:**
- "Auto-fixable" means the tool can detect and attempt to fix the issue, but some fixes may require additional context or manual review
- Exit code 0 from `sdd fix` means the tool successfully applied the fixes it could determine, not that all validation issues are resolved
- Some issues in the auto-fixable list may be skipped if the tool cannot safely determine the correct fix
- Always run `sdd validate` after fixing to verify the results and check for newly revealed issues

**Selective fix application:**
```bash
# Apply specific fixes by ID
sdd fix spec.json --select counts.recalculate

# Apply all fixes in a category
sdd fix spec.json --select metadata

# Apply multiple specific fixes
sdd fix spec.json --select counts.recalculate metadata.ensure:task-001
```

**Diff reporting:**
```bash
# Show before/after changes in markdown format
sdd fix spec.json --diff

# Show changes in JSON format
sdd fix spec.json --diff --diff-format json
```

**Example output:**

Successful fix with all issues resolved:
```bash
$ sdd fix my-spec.json
🔵 Action: Analyzing spec for auto-fixable issues...
✅ Applied 8 fixes:
   - Fixed 5 task count rollups
   - Added 2 metadata blocks
   - Reconnected 1 orphaned node
   - Corrected 2 parent/child mismatches

Created backup: my-spec.json.backup

$ echo $?
0  # Exit 0: fix succeeded

$ sdd validate my-spec.json
❌ Validation found 4 errors
   0 auto-fixable, 4 require manual intervention
   # Note: Fixing revealed circular dependency issues
```

Partial fix (some issues skipped):
```bash
$ sdd fix my-spec.json
🔵 Action: Analyzing spec for auto-fixable issues...
✅ Applied 3 fixes:
   - Fixed 2 task count rollups
   - Added 1 metadata block

⚠️  Skipped 2 issues requiring manual intervention:
   - task-3-2: Circular dependency (task-3-2 → task-3-5 → task-3-2)
   - task-5-2: Dependency references non-existent task-2-9

Created backup: my-spec.json.backup

$ echo $?
0  # Exit 0: fix succeeded (even though issues remain)
```

Preview mode (no changes applied):
```bash
$ sdd fix my-spec.json --preview
🔵 Action: Analyzing spec for auto-fixable issues...
📋 Would apply 5 fixes:
   - Fix 3 task count rollups (task-1-1, task-2-3, task-3-1)
   - Add 2 metadata blocks (task-4-2, phase-2)

⚠️  Would skip 1 issue:
   - task-6-1: Circular dependency requires manual fix

No changes made (preview mode)

$ echo $?
0
```

### report
Generate a detailed validation report with stats and dependency analysis.

```bash
sdd report <spec-file.json> [--format {markdown,json}] [--output <path>] [--bottleneck-threshold N]
```

- Runs validation checks and generates a comprehensive report.
- `--format` chooses between markdown (default) or json.
- `--output` specifies output file path (use `-` for stdout).
- `--bottleneck-threshold` sets minimum tasks blocked to flag bottleneck (default: 3).
- Report includes: validation summary, categorized issues, statistics, and dependency findings.

### stats
Calculate and display comprehensive spec statistics.

```bash
sdd stats <spec-file.json> [--json]
```

- Reports detailed statistics including:
  - Node, task, phase, and verification counts
  - Status breakdown (pending, in_progress, completed, blocked)
  - Hierarchy maximum depth
  - Average tasks per phase
  - Verification coverage percentage
  - Overall progress percentage
  - File size
- With `--json`, outputs structured JSON for automation.

**Example output:**
```bash
$ sdd stats my-spec.json
📊 Spec Statistics for: User Authentication System

Counts:
  Total nodes: 47
  Tasks: 23
  Phases: 3
  Verifications: 12
  Groups: 9

Status Breakdown:
  Pending: 15 (65%)
  In Progress: 3 (13%)
  Completed: 5 (22%)
  Blocked: 0 (0%)

Hierarchy:
  Maximum depth: 4 levels
  Average tasks per phase: 7.67

Coverage:
  Verification coverage: 52% (12/23 tasks have verifications)
  Overall progress: 22% (5/23 tasks completed)

File Info:
  Size: 28.4 KB
  Last updated: 2025-10-26T15:30:00Z
```

### check-deps
Analyze dependencies for cycles, orphans, deadlocks, and bottlenecks.

```bash
sdd check-deps <spec-file.json> [--bottleneck-threshold N] [--json]
```

- Performs comprehensive dependency analysis:
  - **Cycles**: Circular dependency chains between tasks
  - **Orphaned**: Tasks referencing missing dependencies
  - **Deadlocks**: Tasks blocked by each other
  - **Bottlenecks**: Tasks blocking many others (threshold configurable)
- `--bottleneck-threshold` sets minimum blocked tasks to flag (default: 3).
- With `--json`, outputs structured analysis results.

**Example output:**

Clean dependency analysis:
```bash
$ sdd check-deps my-spec.json
✅ Dependency Analysis: No issues found

Analyzed:
  23 tasks
  45 dependencies
  0 cycles
  0 orphaned dependencies
  0 deadlocks
  1 bottleneck

Bottlenecks (tasks blocking 3+ others):
  task-1-2: User model implementation (blocks 5 tasks)
  └─ This is expected for foundational components
```

Issues detected:
```bash
$ sdd check-deps my-spec.json
⚠️  Dependency Analysis: 3 issues found

Cycles (2):
  1. task-3-2 → task-3-5 → task-3-2
  2. task-4-1 → task-4-3 → task-4-1

Orphaned dependencies (1):
  task-5-2 references non-existent "task-2-9"

Deadlocks: 0

Bottlenecks (1):
  task-1-2: User model implementation (blocks 8 tasks)

Recommendation: Fix circular dependencies first to unblock work
```

## Complete Validation Workflow

### Initial Validation
1. Run `sdd validate <spec.json>` after generating or editing a spec.
2. Use `--verbose` to see detailed issue information.
3. Check exit code: 0 (clean), 1 (warnings), or 2 (errors).

### Auto-Fix Issues
4. Preview fixes: `sdd fix <spec.json> --preview`
5. Apply fixes: `sdd fix <spec.json>` (creates backup automatically)
6. Re-validate to confirm fixes resolved issues.

### Generate Reports
7. Create detailed report: `sdd report <spec.json> --format markdown`
8. Or output to stdout for review: `sdd report <spec.json> --output -`

### Analyze Spec
9. View statistics: `sdd stats <spec.json>`
10. Check dependencies: `sdd check-deps <spec.json>`

### Iterative Fixing

**Important:** Validation and fixing may require multiple passes. Some fixes enable detection of new issues that were previously hidden.

**Why multiple passes are needed:**
- Fixing structural issues (e.g., parent-child mismatches) may reveal dependency problems
- Correcting task counts may expose orphaned nodes
- Some validation checks depend on other data being correct first

**When to stop iterating:**
1. Run `sdd validate <spec.json>` and check the exit code
2. If exit code is 0, validation is complete
3. If exit code is 1 or 2, review the issues:
   - Auto-fixable issues: Run `sdd fix <spec.json>` and re-validate
   - Manual issues: Address them and re-validate
4. Repeat until exit code 0 or only non-fixable warnings remain

**Key point:** `sdd fix` reporting success means it successfully applied fixes, not that all validation issues are resolved. Always re-validate after fixing to check for newly revealed issues.

## Troubleshooting Common Issues

### "Auto-fix succeeded but validation still shows errors"

This is normal and expected behavior. `sdd fix` reports success when it successfully applies the fixes it can determine, not when all validation issues are resolved. Some common reasons:

- **Cascading issues**: Fixing one problem often reveals another. For example, fixing parent-child mismatches may reveal orphaned nodes that were previously hidden.
- **Context-dependent fixes**: Some auto-fixable issues require additional context that the tool cannot safely infer, so they're skipped.
- **Manual-only issues**: Some validation errors cannot be auto-fixed and require human intervention (e.g., logical inconsistencies in task descriptions).

**Solution**: Run `sdd validate` again to see the remaining issues, then run `sdd fix` again or address issues manually.

### "How many times should I run fix?"

**Typical cases:**
- **2-3 passes**: Most specs converge after 2-3 fix/validate cycles
- **5+ passes**: May indicate circular dependencies or deeper structural issues

**Rule of thumb:**
1. If each pass reduces error count significantly → keep iterating
2. If error count plateaus (stays the same for 2 passes) → switch to manual fixes
3. If you hit 5 passes → investigate with `sdd check-deps` for circular dependencies

### "When to give up on auto-fix and fix manually?"

Switch to manual fixing when you see:
- **Repeated warnings**: Same warnings appear after multiple fix passes
- **Context-specific issues**: Errors that require understanding the spec's intent (e.g., "task-2-1 should depend on task-1-3")
- **Logical inconsistencies**: Issues with the spec's structure that require redesign
- **Custom metadata**: Problems with project-specific metadata that the tool doesn't understand

**Tip**: Use `sdd validate --verbose` to see detailed issue information with locations, making manual fixes easier.

### Decision Tree: Should I Keep Auto-Fixing?

Use this flowchart to decide whether to continue with `sdd fix` or switch to manual fixes:

```
┌─────────────────────────┐
│  Run sdd validate       │
└───────────┬─────────────┘
            │
            ▼
      ┌─────────────┐
      │  Errors?    │──No──▶ ✅ Done! (exit code 0)
      └─────┬───────┘
            │ Yes
            ▼
    ┌───────────────────┐
    │  Run sdd fix      │
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────────┐
    │  Re-run sdd validate  │
    └─────────┬─────────────┘
              │
              ▼
        ┌─────────────┐
        │  Errors?    │──No──▶ ✅ Done! (exit code 0)
        └─────┬───────┘
              │ Yes
              ▼
    ┌─────────────────────────────┐
    │  Same error count as before?│──No──▶ ↩ Go back to "Run sdd fix"
    └─────────┬───────────────────┘         (errors decreased, keep going)
              │ Yes (plateau)
              ▼
    ┌───────────────────────────────────┐
    │  Check sdd fix output:            │
    │  Did it apply any fixes?          │
    └─────────┬─────────────────────────┘
              │
        ┌─────┴──────┐
        │            │
       Yes          No
        │            │
        ▼            ▼
  ┌────────────┐  ┌──────────────────┐
  │ New issues │  │ Can't auto-fix   │
  │ revealed   │  │ remaining issues │
  └─────┬──────┘  └────────┬─────────┘
        │                  │
        │                  ▼
        │         ┌─────────────────────┐
        │         │ ⚠️  Switch to manual │
        │         │ Use --verbose to    │
        │         │ identify issues     │
        │         └─────────────────────┘
        │
        └──▶ ↩ Go back to "Run sdd fix"
             (try one more pass)
```

**Key decision points:**
- **Error count decreasing?** → Keep auto-fixing
- **Error count same for 2+ passes?** → Check if fix applied anything
- **Fix applied changes but errors remain?** → Try one more pass (new issues may have been revealed)
- **Fix made no changes?** → Switch to manual fixes

### Real-world scenario

**Case**: A spec had 47 validation errors after initial generation.

**Fix cycle:**
1. **Pass 1**: `sdd fix` → Applied 32 fixes, 23 errors remain
2. **Pass 2**: `sdd fix` → Applied 15 fixes, 8 errors remain
3. **Pass 3**: `sdd fix` → Applied 4 fixes, 5 errors remain (plateau detected)
4. **Manual review**: Used `sdd validate --verbose` to identify remaining issues
5. **Manual fixes**: Corrected 3 logical dependency issues and 2 custom metadata fields
6. **Pass 4**: `sdd fix` → Applied final 2 cascading fixes
7. **Result**: Clean validation (exit code 0)

**Key insight**: The tool handled 53 fixes automatically (91%), but 5 required human judgment (9%). This is typical for complex specs.

### Real-world scenario: When auto-fix plateaus

**Case**: A spec had 88 validation errors after modifications. This example shows complete terminal output and how to interpret plateaus.

**Pass 1: Initial fix attempt**
```bash
$ sdd validate my-spec.json
❌ Validation found 88 errors
- 45 incorrect task count rollups
- 23 missing metadata blocks
- 12 orphaned nodes
- 8 parent/child mismatches

$ sdd fix my-spec.json
✅ Applied 84 fixes:
   - Fixed 45 task count rollups
   - Added 23 metadata blocks
   - Reconnected 8 orphaned nodes
   - Corrected 8 parent/child mismatches
Created backup: my-spec.json.backup

$ echo $?
0  # Exit code 0: fix succeeded
```

**Pass 2: Re-validate reveals new issues**
```bash
$ sdd validate my-spec.json
❌ Validation found 4 errors
- 4 dependency cycle issues

$ sdd fix my-spec.json
⚠️  Cannot auto-fix:
   - task-3-2 depends on task-3-5 which depends on task-3-2 (circular)
   - task-4-1 depends on task-4-3 which depends on task-4-1 (circular)
   - task-5-2 has dependency on non-existent task-2-9
   - task-6-1 metadata references undefined field "custom_priority"
Skipped 4 issues requiring manual intervention

$ echo $?
0  # Exit code 0: fix ran successfully (but skipped issues)
```

**Pass 3: Error count unchanged (plateau detected)**
```bash
$ sdd validate my-spec.json
❌ Validation found 4 errors  # Same count as before
- Same 4 dependency issues remain

# Plateau detected: error count unchanged after fix attempt
# → Time to switch to manual fixes
```

**Manual intervention**
```bash
$ sdd validate my-spec.json --verbose
❌ Validation found 4 errors

1. [ERROR] task-3-2: Circular dependency detected
   Location: hierarchy.task-3-2.dependencies
   Details: task-3-2 → task-3-5 → task-3-2

2. [ERROR] task-4-1: Circular dependency detected
   Location: hierarchy.task-4-1.dependencies
   Details: task-4-1 → task-4-3 → task-4-1

3. [ERROR] task-5-2: Dependency references non-existent node
   Location: hierarchy.task-5-2.dependencies.depends
   Details: References "task-2-9" which does not exist

4. [ERROR] task-6-1: Unknown metadata field
   Location: hierarchy.task-6-1.metadata
   Details: Field "custom_priority" not recognized

# Manual fixes applied to JSON:
# - Removed circular dependency: task-3-5 no longer depends on task-3-2
# - Removed circular dependency: task-4-3 no longer depends on task-4-1
# - Fixed typo: task-5-2 now depends on task-2-8 (not task-2-9)
# - Removed custom field: deleted "custom_priority" from task-6-1
```

**Pass 4: Verify manual fixes**
```bash
$ sdd validate my-spec.json
✅ Validation passed (exit code 0)
```

**Key insights from this scenario:**
- **Exit code 0 from fix ≠ all issues resolved**: The fix command succeeded both times but couldn't resolve the issues
- **Plateau is the signal**: When error count stays the same after fix, switch to manual
- **Use --verbose for details**: Essential for understanding what needs manual intervention
- **Context matters**: The 4 remaining issues required understanding the spec's intent (circular deps, typos, custom fields)
- **88 → 4 is success**: Auto-fix handled 95% of issues (84/88), dramatically reducing manual work

## Advanced Usage

### JSON Output for Automation
```bash
# Validate and parse results
sdd validate spec.json --json | jq '.status'

# Get statistics for dashboards
sdd stats spec.json --json | jq '.progress'

# Check dependency health
sdd check-deps spec.json --json | jq '.status'
```