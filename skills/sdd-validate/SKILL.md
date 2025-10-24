---
name: sdd-validate
description: Validate SDD JSON specs, auto-fix common issues, generate detailed reports, and analyze dependencies.
---

# Spec Validation Skill

## Overview

The **Skill(sdd-validate)** skill provides comprehensive validation for Spec-Driven Development (SDD) JSON specification files. It checks for structural consistency, auto-fixes common issues, generates detailed reports, and analyzes dependencies. Use it to ensure a spec is structurally sound before running other SDD skills.

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

Reach for `Skill(sdd-validate)` when you need to:
- Confirm a freshly created spec parses correctly
- Auto-fix common validation issues like missing metadata or incorrect counts
- Check for structural errors before running `Skill(sdd-next)` or `Skill(sdd-update)`
- Generate detailed validation reports for review or CI/CD
- Analyze spec statistics and complexity metrics
- Detect dependency issues including cycles, orphans, and bottlenecks

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
- `2` – Errors detected (requires fixes)

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