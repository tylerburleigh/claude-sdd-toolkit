# CLI Verbosity Analysis - Critical Flow Transcripts

## Collection Date
2025-11-15

## Purpose
This document catalogs verbose CLI outputs from critical SDD workflows to establish a baseline for verbosity reduction improvements (Spec: cli-verbosity-reduction-2025-11-09-001, Task: task-1-1-1).

---

## Critical Flow 1: Help Command

**Command:** `sdd --help`

**Observations:**
- Displays 50+ command names in a single condensed list
- Each command has a brief description
- Global options include multiple verbosity controls (--quiet, --verbose, --json, --compact, --no-color)
- Output is primarily informational, appropriate for help text
- **Verbosity Assessment:** Appropriate - help text should be comprehensive

**Character Count:** ~4,500 characters

---

## Critical Flow 2: find-specs Command

**Command:** `sdd find-specs --verbose`

**Output:**
```
/home/tyler/Documents/GitHub/claude-sdd-toolkit/specs
```

**Observations:**
- Minimal output (single line)
- Returns absolute path to specs directory
- --verbose flag did not add additional output
- **Verbosity Assessment:** Excellent - concise, machine-readable

**Character Count:** ~60 characters

---

## Critical Flow 3: list-specs Command

**Command:** `sdd list-specs --verbose`

**Output:** JSON array with 30 spec objects

**Observations:**
- Returns JSON array of all specs (active, completed, pending, archived)
- Each spec includes: spec_id, status, title, total_tasks, completed_tasks, progress_percentage, current_phase, version, created_at, updated_at
- 30 specs listed with full metadata
- --verbose flag did not add additional output beyond standard JSON
- **Verbosity Assessment:** Appropriate for data query - machine-readable JSON

**Character Count:** ~6,500 characters

---

## Critical Flow 4: progress Command

**Command:** `sdd progress cli-verbosity-reduction-2025-11-09-001 --verbose`

**Output:**
```json
{
  "node_id": "spec-root",
  "spec_id": "cli-verbosity-reduction-2025-11-09-001",
  "title": "CLI Verbosity Reduction Improvements",
  "type": "spec",
  "status": "pending",
  "total_tasks": 13,
  "completed_tasks": 0,
  "percentage": 0,
  "remaining_tasks": 13,
  "current_phase": {
    "id": "phase-1",
    "title": "Analysis & Baseline Assessment",
    "completed": 0,
    "total": 5
  }
}
```

**Observations:**
- Clean JSON output with essential progress information
- Includes hierarchical phase information
- --verbose flag did not add additional output
- **Verbosity Assessment:** Excellent - concise, structured, machine-readable

**Character Count:** ~300 characters

---

## Critical Flow 5: prepare-task Command

**Command:** `sdd prepare-task cli-verbosity-reduction-2025-11-09-001 --verbose`

**Output:** Large JSON object with comprehensive task preparation data

**Observations:**
- Returns extensive JSON structure including:
  - task_id and task_data with full metadata
  - Dependencies (blocked_by, depends, blocks)
  - Git warnings (dirty tree status)
  - Validation warnings
  - Repository root information
  - Branch creation status
  - Commit cadence options
  - Spec completion info
- --verbose flag did not add additional output
- **Verbosity Assessment:** Good - comprehensive for task preparation, but some fields may be unnecessary

**Character Count:** ~1,200 characters

**Potential Improvements:**
- Could suppress git warnings in quiet mode
- Could hide validation_warnings when empty
- Could consolidate boolean flags

---

## Critical Flow 6: validate Command

**Command:** `sdd validate cli-verbosity-reduction-2025-11-09-001`

**Output:**
```json
{
  "spec_id": "cli-verbosity-reduction-2025-11-09-001",
  "errors": 0,
  "warnings": 0,
  "status": "valid",
  "auto_fixable_issues": 0,
  "schema": {
    "source": "/home/tyler/.claude/plugins/cache/sdd-toolkit/src/claude_skills/schemas/sdd-spec-schema.json",
    "errors": [],
    "warnings": []
  }
}
```

**Observations:**
- Clean, concise validation result
- Includes schema path (could be verbose in some contexts)
- Empty arrays for errors/warnings take up space
- **Verbosity Assessment:** Good - could be more concise in quiet mode

**Potential Improvements:**
- Omit empty errors/warnings arrays in quiet mode
- Hide schema.source path unless --verbose
- Could reduce to single-line success message: `{"status": "valid"}`

**Character Count:** ~350 characters

---

## Critical Flow 7: query-tasks Command

**Command:** `sdd query-tasks cli-verbosity-reduction-2025-11-09-001 --status pending`

**Output:** JSON array with 19 task objects (phases, groups, tasks, subtasks)

**Observations:**
- Returns comprehensive task hierarchy
- Includes all pending tasks across all phases
- Each task includes full metadata (type, status, parent, completed_tasks, total_tasks, metadata)
- Metadata includes task_category, estimated_hours, file_path, notes
- **Verbosity Assessment:** Appropriate for query command - comprehensive data needed

**Character Count:** ~4,700 characters

**Potential Improvements:**
- Could add --compact flag to return only essential fields (id, title, status)

---

## Critical Flow 8: list-blockers Command

**Command:** `sdd list-blockers cli-verbosity-reduction-2025-11-09-001`

**Output:**
```json
[]
```

**Observations:**
- Returns empty array when no blockers exist
- Clean, minimal output
- **Verbosity Assessment:** Excellent - concise

**Character Count:** 2 characters

---

## Critical Flow 9: check-deps Command

**Command:** `sdd check-deps cli-verbosity-reduction-2025-11-09-001 task-1-1-1`

**Output:**
```json
{
  "task_id": "task-1-1-1",
  "can_start": true,
  "blocked_by": [],
  "soft_depends": [],
  "blocks": []
}
```

**Observations:**
- Clean dependency check result
- Empty arrays for dependencies
- **Verbosity Assessment:** Good - could omit empty arrays in quiet mode

**Character Count:** ~120 characters

---

## Summary Statistics

| Command | Character Count | Verbosity Level | Improvement Potential |
|---------|----------------|-----------------|----------------------|
| --help | ~4,500 | High (appropriate) | None - help text |
| find-specs --verbose | ~60 | Low (excellent) | None |
| list-specs --verbose | ~6,500 | High | Medium - add --compact |
| progress --verbose | ~300 | Low (excellent) | None |
| prepare-task --verbose | ~1,200 | Medium | Medium - hide empty fields |
| validate | ~350 | Medium | Medium - quiet mode |
| query-tasks | ~4,700 | High | Medium - add --compact |
| list-blockers | 2 | Low (excellent) | None |
| check-deps | ~120 | Low | Low - omit empty arrays |

---

## Key Findings

### Well-Optimized Commands
1. `find-specs` - Minimal, single-line output
2. `list-blockers` - Empty array when appropriate
3. `progress` - Concise JSON with essential data
4. `check-deps` - Small, focused output

### Commands Needing Improvement
1. `prepare-task` - Includes many empty/unnecessary fields
2. `validate` - Could be more concise in quiet mode
3. `query-tasks` - Could benefit from --compact flag
4. `list-specs` - Large output, could use --compact

### Verbosity Flag Observations
- Many commands do NOT respond to --verbose flag (no additional output)
- --quiet flag exists globally but may not be respected by all commands
- --json and --compact flags control output format but not verbosity level

---

## Recommendations for Phase 1

1. **Define verbosity tiers:**
   - QUIET: Minimal output, errors only
   - NORMAL: Current default, structured JSON
   - VERBOSE: Add debugging details, trace information

2. **Commands to target for reduction:**
   - `prepare-task`: Hide empty arrays/fields in quiet mode
   - `validate`: Single-line success in quiet mode
   - Commands with empty arrays: omit them unless --verbose

3. **Preserve current behavior:**
   - Query commands (list-specs, query-tasks) - comprehensive by design
   - Help text - needs to be complete
   - Commands already minimal (find-specs, list-blockers)

4. **Global consistency:**
   - Ensure --quiet flag works across ALL commands
   - Ensure --verbose flag adds meaningful detail
   - Keep JSON output for machine readability
