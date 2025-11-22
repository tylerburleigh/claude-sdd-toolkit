# Journal Accessibility Improvements

## Overview

This document describes improvements to journal entry accessibility in the SDD CLI tools.

## Changes

### 1. Enhanced `get-journal` Command

The `get-journal` command now supports a more ergonomic positional syntax while maintaining backward compatibility.

**New Syntax (Positional):**
```bash
# Get all journal entries for a spec
sdd get-journal SPEC_ID

# Get journal entries for a specific task
sdd get-journal SPEC_ID TASK_ID
```

**Legacy Syntax (Flag-based - deprecated but still supported):**
```bash
sdd get-journal SPEC_ID --task-id TASK_ID
```

**Examples:**
```bash
# All journal entries for a specification
sdd get-journal my-feature-2025-11-01-001 --json

# Journal entries for a specific task (positional)
sdd get-journal my-feature-2025-11-01-001 task-2-1 --json

# Journal entries for a specific task (legacy flag)
sdd get-journal my-feature-2025-11-01-001 --task-id task-2-1 --json
```

### 2. Journal Data in `prepare-task` Output

The `prepare-task` command now includes journal information in the `context` field at all verbosity levels.

**Accessing Journal Data:**
```bash
sdd prepare-task SPEC_ID TASK_ID --json | jq '.context.task_journal'
```

**Response Structure:**
```json
{
  "context": {
    "task_journal": {
      "entry_count": 1,
      "entries": [
        {
          "timestamp": "2025-11-22T12:41:01Z",
          "entry_type": "status_change",
          "title": "Task Completed: ...",
          "content": "...",
          "author": "claude-code"
        }
      ]
    },
    "previous_sibling": { ... },
    "parent_task": { ... },
    "phase": { ... },
    "sibling_files": [ ... ]
  }
}
```

**Verbosity Levels:**
- `--quiet`: Includes essential fields including `context`
- Default: Includes standard fields including `context`
- `--verbose`: Includes all fields including `context` and `extended_context`

## When to Use Each Command

### Use `get-journal` when:
- You need to retrieve all journal entries for a task or spec
- You want historical journal data
- You're querying journal entries independently of task preparation

### Use `prepare-task` when:
- You're preparing to work on a task
- You need task context including recent journal summary
- You want integrated task metadata, dependencies, and journal data

## Migration Notes

### For Users of `--task-id` Flag

The `--task-id` flag is now deprecated in favor of the positional argument. Both work identically:

```bash
# Old (still works)
sdd get-journal my-spec --task-id task-1-1

# New (recommended)
sdd get-journal my-spec task-1-1
```

### For Automated Scripts

Scripts using `prepare-task` can now access journal data without requiring verbose mode:

```bash
# Previously required --verbose to see journal data
# Now works at all verbosity levels
sdd prepare-task my-spec task-1-1 --json --quiet | jq '.context.task_journal.entries[]'
```

## Technical Details

### Output Filtering

The `context` field has been added to both `PREPARE_TASK_ESSENTIAL` and `PREPARE_TASK_STANDARD` field sets in `output_utils.py`, ensuring it's available at all verbosity levels.

### Backward Compatibility

All changes maintain full backward compatibility:
- The `--task-id` flag continues to work
- Existing scripts and workflows are unaffected
- Output structure remains consistent

## Files Modified

1. `src/claude_skills/claude_skills/sdd_update/cli.py`
   - Added positional `task_id` argument to `get-journal` parser
   - Updated `cmd_get_journal` to support both positional and flag-based arguments
   - Enhanced help text to show usage examples

2. `src/claude_skills/claude_skills/cli/sdd/output_utils.py`
   - Added `'context'` to `PREPARE_TASK_ESSENTIAL` field set
   - Added `'context'` to `PREPARE_TASK_STANDARD` field set
