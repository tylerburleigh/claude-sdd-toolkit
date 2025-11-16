# CLI Message Volume & Frequency Metrics

## Analysis Date
2025-11-15

## Purpose
Quantitative analysis of message volume and frequency for SDD CLI commands to support verbosity reduction planning (Spec: cli-verbosity-reduction-2025-11-09-001, Task: task-1-1-2).

---

## Methodology

### Data Collection Method
All measurements collected via actual command execution with output piped to `/tmp/` files and measured using:
- `wc -c` for character counts
- `wc -l` for line counts
- `jq` for JSON field analysis

### Commands Analyzed
9 critical CLI commands representing typical SDD workflow operations

---

## Measured Command Outputs

### Raw Measurements Table

| Command | Characters | Lines | JSON Objects | Fields/Object | Empty Fields | Empty % |
|---------|-----------|-------|--------------|---------------|--------------|---------|
| `find-specs` | 54 | 1 | 0 (plain text) | - | - | - |
| `list-blockers` | 3 | 1 | 0 (empty array) | - | - | - |
| `check-deps` | 88 | 1 | 1 | 5 | 3 | 60% |
| `progress` | 330 | 1 | 1 | 10 | 0 | 0% |
| `validate` | 305 | 12 | 1 | 6 | 2* | 33% |
| `prepare-task` | 1,027 | 1 | 1 | 19 | 10 | 53% |
| `query-tasks` | 5,761 | 1 | 20 | 8 | varies | - |
| `list-specs` | 7,520 | 1 | 30 | 10 | varies | - |
| `--help` | 8,390 | 124 | 0 (plain text) | - | - | - |

*Empty fields in nested `schema` object

---

## Detailed Command Analysis

### 1. find-specs
```
Characters: 54
Lines: 1
Format: Plain text path
```
**Assessment:** Optimal - minimal, single-line output

---

### 2. list-blockers
```
Characters: 3 (just "[]" plus newline)
Lines: 1
Format: Empty JSON array
```
**Assessment:** Optimal - appropriate empty response

---

### 3. check-deps
```
Characters: 88
Lines: 1
Fields: 5 total
Empty fields: 3 (blocked_by[], soft_depends[], blocks[])
Empty percentage: 60%
```
**Sample output:**
```json
{
  "task_id": "task-1-1-2",
  "can_start": true,
  "blocked_by": [],
  "soft_depends": [],
  "blocks": []
}
```
**Assessment:** Good structure, but 60% empty fields is wasteful

---

### 4. progress
```
Characters: 330
Lines: 1
Fields: 10 total
Empty fields: 0
Empty percentage: 0%
```
**Assessment:** Excellent - all fields contain data, concise output

---

### 5. validate
```
Characters: 305
Lines: 12 (formatted JSON)
Fields: 6 top-level
Empty fields: 2 (schema.errors[], schema.warnings[])
Empty percentage: 33%
```
**Sample output structure:**
```json
{
  "spec_id": "...",
  "errors": 0,
  "warnings": 0,
  "status": "valid",
  "auto_fixable_issues": 0,
  "schema": {
    "source": "...",
    "errors": [],      // Empty
    "warnings": []     // Empty
  }
}
```
**Assessment:** Could reduce to minimal success message in quiet mode

---

### 6. prepare-task
```
Characters: 1,027
Lines: 1
Fields: 19 total
Empty fields: 10
Empty percentage: 53%
```
**Empty fields identified:**
- `task_details`: null
- `spec_file`: null
- `doc_context`: null
- `validation_warnings`: []
- `git_warnings`: []
- `suggested_branch_name`: null
- `commit_cadence_options`: null
- `suggested_commit_cadence`: null
- `completion_info`: null
- `error`: null

**Assessment:** HIGH reduction opportunity - over half the fields are empty

---

### 7. query-tasks
```
Characters: 5,761
Lines: 1
Objects: 20 task objects
Fields per object: 8
Format: JSON array
```
**Sample object:**
```json
{
  "id": "task-1-1",
  "title": "Inventory noisy CLI outputs",
  "type": "task",
  "status": "pending",
  "parent": "phase-1-files",
  "completed_tasks": 0,
  "total_tasks": 2,
  "metadata": {...}
}
```
**Assessment:** Comprehensive query result - appropriate for data retrieval

---

### 8. list-specs
```
Characters: 7,520
Lines: 1
Objects: 30 spec objects
Fields per object: 10
Format: JSON array
```
**Fields per spec:**
- spec_id
- status
- title
- total_tasks
- completed_tasks
- progress_percentage
- current_phase
- version
- created_at
- updated_at

**Assessment:** HIGHEST character count - good target for --compact mode

---

### 9. --help
```
Characters: 8,390
Lines: 124
Format: Formatted help text
```
**Assessment:** Appropriate verbosity for help documentation

---

## Empty Field Impact Analysis

### Commands with Significant Empty Field Waste

**prepare-task (53% empty):**
- 10 empty fields out of 19 total
- Estimated waste: ~540 characters (53% of 1,027)
- **Potential reduction:** 540 chars per invocation

**check-deps (60% empty):**
- 3 empty arrays out of 5 fields
- Estimated waste: ~35 characters
- **Potential reduction:** 35 chars per invocation

**validate (33% empty):**
- 2 empty arrays in schema object
- Estimated waste: ~40 characters
- **Potential reduction:** 40 chars per invocation

---

## Size Category Distribution

### Verbosity Categories

| Category | Size Range | Commands | Count |
|----------|-----------|----------|-------|
| Minimal | < 100 chars | find-specs, list-blockers, check-deps | 3 |
| Low | 100-500 chars | progress, validate | 2 |
| Medium | 500-2K chars | prepare-task | 1 |
| High | 2K-10K chars | query-tasks, list-specs, --help | 3 |

### Distribution
- Minimal: 33%
- Low: 22%
- Medium: 11%
- High: 33%

---

## Reduction Opportunities (Ranked by Impact)

### Priority 1: Large Output Commands

**1. list-specs (7,520 chars)**
- Current: 10 fields × 30 specs = 300 field instances
- Proposed compact mode: 4 fields (id, status, title, progress_percentage)
- **Estimated reduction:** 60% = ~4,500 chars saved

**2. query-tasks (5,761 chars)**
- Current: 8 fields × 20 tasks = 160 field instances
- Proposed compact mode: 5 fields (id, title, type, status, parent)
- **Estimated reduction:** 38% = ~2,200 chars saved

### Priority 2: High Empty-Field Ratio

**3. prepare-task (1,027 chars, 53% empty)**
- Remove 10 null/empty fields
- **Estimated reduction:** 53% = ~540 chars saved

**4. check-deps (88 chars, 60% empty)**
- Remove 3 empty arrays
- **Estimated reduction:** 40% = ~35 chars saved

**5. validate (305 chars, 33% empty)**
- Simplify success case to: `{"status": "valid"}`
- **Estimated reduction:** 80% for success cases = ~244 chars saved

---

## Summary Statistics

### Total Measured Output
- **Total characters (all 9 commands):** 23,478 chars
- **Average per command:** 2,609 chars
- **Median:** 330 chars

### High-Impact Targets
- **list-specs + query-tasks** = 13,281 chars (57% of total)
- These 2 commands represent the majority of output volume

### Empty Field Waste
- **Total empty fields across commands:** 15 fields
- **Estimated waste:** ~615 chars (2.6% of total)
- **Commands affected:** 3 out of 9

---

## Recommendations

### Tier 1: High Impact
1. **Add --compact flag to list-specs** → saves ~4,500 chars
2. **Add --compact flag to query-tasks** → saves ~2,200 chars

### Tier 2: Medium Impact
3. **Omit empty fields in prepare-task** → saves ~540 chars
4. **Simplify validate success output** → saves ~244 chars

### Tier 3: Low Impact
5. **Omit empty arrays in check-deps** → saves ~35 chars

### Total Potential Savings
**~7,519 characters (32% reduction across all commands)**

---

## Next Steps

Based on this quantitative analysis, task-1-2 (Define verbosity policy) should prioritize:

1. Defining --compact mode behavior for high-volume commands
2. Establishing rules for omitting null/empty fields
3. Creating minimal success responses for validation commands
4. Ensuring backward compatibility with existing JSON consumers

