# CLI Verbosity Policy Definition

## Document Information
- **Spec ID:** cli-verbosity-reduction-2025-11-09-001
- **Task:** task-1-2-1 (Define verbosity levels and thresholds)
- **Date:** 2025-11-15
- **Status:** Draft for Review

---

## Executive Summary

This policy defines three verbosity tiers for the SDD CLI based on empirical measurement data from task-1-1-2. The policy aims to reduce average session output by 32% while maintaining backward compatibility and machine readability.

---

## Verbosity Levels

### Level 1: QUIET Mode (`--quiet` or `-q`)

**Purpose:** Minimal output for automation, scripts, and focused human workflows

**Characteristics:**
- Suppress informational messages
- Show only critical data and errors
- Omit null/empty fields from JSON output
- Use compact JSON formatting (no pretty-print)
- Success operations return minimal confirmation

**Output Rules:**
1. **Success operations:** Return minimal JSON with status only
2. **Data queries:** Return only essential fields
3. **Errors:** Full error details with actionable guidance
4. **Progress indicators:** Suppressed
5. **Warnings:** Suppressed unless critical

**Flag Behavior:**
- `--quiet` overrides default behavior
- Compatible with `--json` (returns compact JSON)
- Incompatible with `--verbose` (error if both specified)

**Example Transformations:**

```bash
# NORMAL MODE
$ sdd validate spec-id
{
  "spec_id": "spec-id",
  "errors": 0,
  "warnings": 0,
  "status": "valid",
  "auto_fixable_issues": 0,
  "schema": {
    "source": "/path/to/schema.json",
    "errors": [],
    "warnings": []
  }
}

# QUIET MODE
$ sdd validate spec-id --quiet
{"status":"valid"}
```

---

### Level 2: NORMAL Mode (Default)

**Purpose:** Balanced output for interactive CLI usage with machine readability

**Characteristics:**
- Current default behavior (baseline)
- Structured JSON output
- Include all relevant fields (even if empty)
- Formatted for readability (pretty-printed JSON by default)
- Moderate informational messages

**Output Rules:**
1. **Success operations:** Return complete JSON structure
2. **Data queries:** Return all available fields
3. **Errors:** Full error details with context
4. **Progress indicators:** Shown for long operations
5. **Warnings:** Shown when applicable

**Flag Behavior:**
- Default when no verbosity flags specified
- Configurable via `.claude/config.json`
- Compatible with all output format flags

---

### Level 3: VERBOSE Mode (`--verbose` or `-v`)

**Purpose:** Detailed output for debugging, development, and troubleshooting

**Characteristics:**
- Maximum information output
- Include debug traces and internal state
- Show performance metrics
- Display file system operations
- Log dependency resolution steps
- Include timing information

**Output Rules:**
1. **Success operations:** Include execution details and timing
2. **Data queries:** Include metadata about query execution
3. **Errors:** Full stack traces and debug context
4. **Progress indicators:** Detailed progress with sub-steps
5. **Warnings:** All warnings with full context
6. **Debug info:** Internal state, caching info, file paths

**Flag Behavior:**
- `--verbose` enables maximum output
- Adds additional fields to JSON responses
- Incompatible with `--quiet`
- Can be stacked: `-vv` for extra verbosity (future enhancement)

**Example Additions:**

```bash
# NORMAL MODE
$ sdd progress spec-id
{
  "spec_id": "spec-id",
  "total_tasks": 13,
  "completed_tasks": 2,
  "percentage": 15
}

# VERBOSE MODE
$ sdd progress spec-id --verbose
{
  "spec_id": "spec-id",
  "total_tasks": 13,
  "completed_tasks": 2,
  "percentage": 15,
  "_debug": {
    "query_time_ms": 12,
    "spec_file_path": "/path/to/spec.json",
    "spec_file_size_bytes": 45120,
    "cache_hit": true,
    "tasks_by_status": {
      "completed": 2,
      "in_progress": 0,
      "pending": 11
    }
  }
}
```

---

## Thresholds and Triggers

### Character Count Thresholds

Based on empirical measurements (task-1-1-2):

| Category | Normal Mode | Quiet Mode | Reduction Target |
|----------|-------------|------------|------------------|
| Minimal | < 100 chars | No change | 0% (already optimal) |
| Low | 100-500 chars | 50-200 chars | 40-60% |
| Medium | 500-2K chars | 200-800 chars | 50-60% |
| High | 2K-10K chars | 800-3K chars | 60-70% |

### Field Inclusion Thresholds

**Quiet Mode - Omit fields when:**
1. Value is `null`
2. Value is empty array `[]`
3. Value is empty object `{}`
4. Field is marked as "optional metadata" in schema
5. Field is debug/diagnostic information

**Verbose Mode - Include additional fields:**
1. Internal state information
2. Performance metrics
3. File system paths
4. Cache status
5. Timing information
6. Dependency resolution details

---

## Command-Specific Policies

### High-Volume Commands (> 5,000 chars)

**list-specs** (7,520 chars in normal mode):
- **Quiet:** 4 fields (spec_id, status, title, progress_percentage) = ~3,000 chars
- **Normal:** 10 fields (current) = 7,520 chars
- **Verbose:** +debug (file paths, timestamps, metadata stats) = ~9,000 chars

**query-tasks** (5,761 chars in normal mode):
- **Quiet:** 5 fields (id, title, type, status, parent) = ~2,400 chars
- **Normal:** 8 fields (current) = 5,761 chars
- **Verbose:** +debug (dependency graph, file associations) = ~7,000 chars

### High Empty-Field Ratio Commands (> 40% empty)

**prepare-task** (53% empty in normal mode):
- **Quiet:** Omit all 10 null/empty fields = ~480 chars
- **Normal:** Include all fields = 1,027 chars
- **Verbose:** +debug (task resolution process, cache info) = ~1,300 chars

**check-deps** (60% empty in normal mode):
- **Quiet:** Omit empty arrays = ~50 chars
- **Normal:** Include all fields = 88 chars
- **Verbose:** +debug (dependency graph analysis) = ~150 chars

### Validation Commands

**validate**:
- **Quiet:** `{"status":"valid"}` or `{"status":"invalid","errors":[...]}` = ~20-500 chars
- **Normal:** Full structure with schema info = 305 chars
- **Verbose:** +debug (validation steps, performance) = ~450 chars

---

## Backward Compatibility

### Compatibility Guarantees

1. **JSON Structure:** Normal mode maintains current field structure
2. **Exit Codes:** Unchanged across all verbosity levels
3. **Error Format:** Errors always include actionable details
4. **Pipe Compatibility:** All modes output valid JSON (when `--json`)

### Migration Path

**Phase 1** (Current spec):
- Implement quiet mode as opt-in
- Normal mode remains default (no changes)
- Verbose mode adds optional fields

**Phase 2** (Future):
- Consider changing default to quiet mode
- Provide `--no-quiet` or `--normal` flag for current behavior
- Add configuration file support for per-project defaults

---

## Configuration

### Global Config

Location: `~/.claude/sdd_config.json` or `.claude/config.json`

```json
{
  "verbosity": {
    "default_level": "normal",
    "quiet_omit_empty_fields": true,
    "verbose_include_debug": true,
    "verbose_include_timing": true
  }
}
```

### Project Config

Location: `<project>/.claude/sdd_config.json`

```json
{
  "verbosity": {
    "default_level": "quiet",
    "commands": {
      "list-specs": "normal",
      "prepare-task": "quiet"
    }
  }
}
```

---

## Implementation Priority

### Tier 1: High-Impact Commands (32% overall reduction)
1. `list-specs` - Quiet mode with 4 essential fields
2. `query-tasks` - Quiet mode with 5 essential fields
3. `prepare-task` - Omit empty fields in quiet mode

### Tier 2: Validation Commands
4. `validate` - Minimal success response in quiet mode
5. `check-deps` - Omit empty arrays in quiet mode

### Tier 3: Verbose Enhancements
6. Add `_debug` section to all commands when `--verbose`
7. Include timing and performance metrics
8. Add dependency graph visualization data

---

## Success Criteria

### Quantitative Metrics

1. **Output Reduction:**
   - Quiet mode: 60% reduction for high-volume commands
   - Quiet mode: 50% reduction for medium-volume commands
   - Overall: 32% reduction in typical workflow session

2. **Performance:**
   - Quiet mode: ≤ 5% performance improvement (less I/O)
   - Verbose mode: ≤ 10% performance penalty (acceptable)

3. **Compatibility:**
   - Zero breaking changes to normal mode JSON structure
   - 100% backward compatibility for existing scripts
   - All tests pass with normal mode

### Qualitative Metrics

1. **Usability:**
   - Reduced visual noise for human users in quiet mode
   - Enhanced debugging capability in verbose mode
   - Clear documentation for mode selection

2. **Consistency:**
   - All commands respect verbosity flags
   - Predictable output format across commands
   - Uniform error handling across all modes

---

## Acceptance Criteria

For this task (task-1-2-1) to be considered complete:

- [x] Three verbosity levels defined (QUIET, NORMAL, VERBOSE)
- [x] Character count thresholds established from empirical data
- [x] Field inclusion/exclusion rules specified
- [x] Command-specific policies defined for high-impact commands
- [x] Backward compatibility strategy documented
- [x] Configuration approach specified
- [x] Implementation priority ranked
- [x] Success criteria and metrics defined

---

## Next Steps

**Task task-1-2-2:** Document essential messages per level
- Create comprehensive field mapping for each verbosity level
- Define essential vs. optional fields per command
- Document message templates for success/error/warning cases
- Create validation test cases for each verbosity level

