# list-specs Command Field Analysis

## Overview

This document analyzes the field differences between text and JSON output modes for the `sdd list-specs` command.

## Text Mode Fields (6 fields displayed)

The text mode displays a formatted table with the following columns:

1. **ID** - The spec identifier (from `spec_id` field)
2. **Title** - The specification title (from `title` field)
3. **Progress** - Combined visual display including:
   - Progress bar (visual █/░ blocks)
   - Percentage (from `progress_percentage`)
   - Task count (from `completed_tasks/total_tasks`)
4. **Status** - Status with emoji (from `status` field)
   - ⚡ Active
   - ✅ Complete
   - ⏸️ Pending
   - 📦 Archived
5. **Phase** - Current phase identifier (from `current_phase` field)
6. **Updated** - Last update date (from `updated_at` field, date portion only)

**Implementation Reference:** `/src/claude_skills/claude_skills/sdd_update/list_specs.py:151-252`

## JSON Mode Fields (10 fields)

The JSON mode outputs a structured array with the following fields per spec:

1. **spec_id** - Specification identifier
2. **status** - Status folder (active, completed, archived, pending)
3. **title** - Specification title
4. **total_tasks** - Total number of tasks
5. **completed_tasks** - Number of completed tasks
6. **progress_percentage** - Completion percentage (0-100)
7. **current_phase** - Current phase identifier
8. **version** - Specification version
9. **created_at** - Creation timestamp
10. **updated_at** - Last update timestamp

**Implementation Reference:** `/src/claude_skills/claude_skills/sdd_update/list_specs.py:114-125`

## Verbosity Filtering (JSON Mode)

JSON output supports verbosity filtering:

- **QUIET mode**: 4 essential fields only
  - spec_id, status, title, progress_percentage
- **NORMAL mode**: 10 standard fields (default)
  - All fields listed above, empty fields omitted
- **VERBOSE mode**: 10 fields + additional metadata
  - Includes description, author, file_path

**Field Definitions:** `/src/claude_skills/claude_skills/cli/sdd/output_utils.py:150-154`

## Field Mapping Summary

| Display Name (Text) | JSON Field Name | Notes |
|---------------------|-----------------|-------|
| ID | spec_id | Direct mapping |
| Title | title | Direct mapping |
| Progress | progress_percentage + completed_tasks + total_tasks | Combined display |
| Status | status | Text adds emoji decoration |
| Phase | current_phase | Direct mapping |
| Updated | updated_at | Text shows date only (strips time) |
| - | version | JSON only |
| - | created_at | JSON only |

## Key Differences

1. **Field Count**: Text shows 6 display columns, JSON provides 10 data fields
2. **Aggregation**: Text combines multiple JSON fields into single display columns (e.g., Progress)
3. **Formatting**: Text adds visual enhancements (emojis, progress bars, date truncation)
4. **Exclusive Fields**: JSON includes `version` and `created_at` which are not displayed in text mode
5. **Task Details**: JSON exposes separate `total_tasks` and `completed_tasks`, while text combines them in Progress column

## Limit and Sorting Behavior

### No Default Limit

The `sdd list-specs` command returns **all specifications** with no default limit:

- **Current behavior**: Returns all specs across all status folders (36 specs as of 2025-11-17)
- **No pagination**: No built-in limit or pagination parameters
- **Full traversal**: Scans all status directories (active, completed, archived, pending)

**Implementation Reference:** `/src/claude_skills/claude_skills/sdd_update/list_specs.py:85-132`

### Sorting Behavior

Specs are sorted **alphabetically by filename** within each status folder:

- **Sorting implementation**: Uses `sorted(status_dir.glob("*.json"))` on line 92
- **Sort order**: Lexicographic (alphabetical) ordering of JSON filenames
- **No custom sorting options**: No CLI parameters for alternative sort orders (e.g., by date, progress, title)
- **Multi-folder ordering**: Results include specs from multiple status folders in order: active → completed → archived → pending

**Example ordering:**
```
1. add-pending-folder-support-for-2025-10-30-0847 (active)
2. list-specs-improvements-2025-11-09-001 (active)
3. add-pending-folder-support-for-2025-10-30-0847 (completed)
4. ai-consultation-refactor-2025-11-05-001 (completed)
...
```

### Available Filtering

While there is no limit or custom sorting, the command supports:

- **Status filtering**: `--status {active,completed,archived,pending,all}` - Filter by folder
- **Verbosity levels**: `--quiet`, `--verbose` - Control output detail
- **Output format**: `--json` / `--no-json` - Toggle between text table and JSON array
- **Detailed mode**: `--detailed` - Show additional information

**CLI Reference:** `sdd list-specs --help`

## Discrepancy Note

The task description originally stated that text mode shows "2 fields (ID, Title)", but the actual implementation shows **6 display columns** in a formatted table. This documentation reflects the current implementation as of analysis date.
