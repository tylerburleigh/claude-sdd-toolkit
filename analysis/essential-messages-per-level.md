# Essential Messages Per Verbosity Level

## Document Information
- **Spec ID:** cli-verbosity-reduction-2025-11-09-001
- **Task:** task-1-2-2 (Document essential messages per level)
- **Date:** 2025-11-15
- **Status:** Draft for Review

---

## Overview

This document provides comprehensive field mappings for each verbosity level (QUIET, NORMAL, VERBOSE) across all high-impact SDD CLI commands. It serves as the implementation specification for phase 2 development.

---

## Field Classification System

### Field Categories

1. **ESSENTIAL** - Always included (all verbosity levels)
2. **STANDARD** - Included in NORMAL and VERBOSE modes
3. **OPTIONAL** - Included only in VERBOSE mode
4. **EMPTY-CONDITIONAL** - Omitted in QUIET when null/empty

---

## Command: list-specs

**Current output:** 7,520 chars (30 specs × 10 fields)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| spec_id | ESSENTIAL | ✓ | ✓ | ✓ |
| status | ESSENTIAL | ✓ | ✓ | ✓ |
| title | ESSENTIAL | ✓ | ✓ | ✓ |
| progress_percentage | ESSENTIAL | ✓ | ✓ | ✓ |
| total_tasks | STANDARD | ✗ | ✓ | ✓ |
| completed_tasks | STANDARD | ✗ | ✓ | ✓ |
| current_phase | STANDARD | ✗ | ✓ | ✓ |
| version | EMPTY-CONDITIONAL | ✗ | ✓ | ✓ |
| created_at | EMPTY-CONDITIONAL | ✗ | ✓ | ✓ |
| updated_at | EMPTY-CONDITIONAL | ✗ | ✓ | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

### Output Examples

**QUIET Mode:**
```json
[
  {
    "spec_id": "cli-verbosity-reduction-2025-11-09-001",
    "status": "active",
    "title": "CLI Verbosity Reduction Improvements",
    "progress_percentage": 23
  },
  ...
]
```
**Estimated size:** ~3,000 chars (60% reduction)

**NORMAL Mode:** (Current behavior, no change)

**VERBOSE Mode:**
```json
[
  {
    "spec_id": "cli-verbosity-reduction-2025-11-09-001",
    "status": "active",
    "title": "CLI Verbosity Reduction Improvements",
    "progress_percentage": 23,
    "total_tasks": 13,
    "completed_tasks": 3,
    "current_phase": "phase-1",
    "version": null,
    "created_at": null,
    "updated_at": null,
    "_debug": {
      "file_path": "/path/to/spec.json",
      "file_size_bytes": 45120,
      "last_modified": "2025-11-15T13:45:06Z",
      "tasks_by_status": {
        "completed": 3,
        "in_progress": 0,
        "pending": 10
      }
    }
  },
  ...
]
```
**Estimated size:** ~9,000 chars

---

## Command: query-tasks

**Current output:** 5,761 chars (20 tasks × 8 fields)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| id | ESSENTIAL | ✓ | ✓ | ✓ |
| title | ESSENTIAL | ✓ | ✓ | ✓ |
| type | ESSENTIAL | ✓ | ✓ | ✓ |
| status | ESSENTIAL | ✓ | ✓ | ✓ |
| parent | ESSENTIAL | ✓ | ✓ | ✓ |
| completed_tasks | STANDARD | ✗ | ✓ | ✓ |
| total_tasks | STANDARD | ✗ | ✓ | ✓ |
| metadata | STANDARD | ✗ | ✓ | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

### Output Examples

**QUIET Mode:**
```json
[
  {
    "id": "task-1-1",
    "title": "Inventory noisy CLI outputs",
    "type": "task",
    "status": "completed",
    "parent": "phase-1-files"
  },
  ...
]
```
**Estimated size:** ~2,400 chars (58% reduction)

**NORMAL Mode:** (Current behavior)

**VERBOSE Mode:**
```json
[
  {
    "id": "task-1-1",
    "title": "Inventory noisy CLI outputs",
    "type": "task",
    "status": "completed",
    "parent": "phase-1-files",
    "completed_tasks": 2,
    "total_tasks": 2,
    "metadata": {
      "task_category": "investigation",
      "estimated_hours": 4
    },
    "_debug": {
      "dependencies": {
        "blocks": ["task-1-2"],
        "blocked_by": [],
        "depends": []
      },
      "file_associations": [
        "analysis/cli-verbosity-transcripts.md",
        "analysis/cli-message-volume-metrics.md"
      ],
      "time_tracking": {
        "estimated_hours": 4,
        "actual_hours": 3.5,
        "started_at": "2025-11-15T13:30:00Z",
        "completed_at": "2025-11-15T13:43:00Z"
      }
    }
  },
  ...
]
```
**Estimated size:** ~7,000 chars

---

## Command: prepare-task

**Current output:** 1,027 chars (19 fields, 53% empty)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| success | ESSENTIAL | ✓ | ✓ | ✓ |
| task_id | ESSENTIAL | ✓ | ✓ | ✓ |
| task_data | ESSENTIAL | ✓ | ✓ | ✓ |
| dependencies | ESSENTIAL | ✓ | ✓ | ✓ |
| repo_root | STANDARD | ✗ | ✓ | ✓ |
| needs_branch_creation | STANDARD | ✗ | ✓ | ✓ |
| dirty_tree_status | STANDARD | ✗ | ✓ | ✓ |
| needs_commit_cadence | STANDARD | ✗ | ✓ | ✓ |
| spec_complete | STANDARD | ✗ | ✓ | ✓ |
| task_details | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| spec_file | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| doc_context | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| validation_warnings | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| git_warnings | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| suggested_branch_name | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| commit_cadence_options | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| suggested_commit_cadence | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| completion_info | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| error | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

*Included in NORMAL only if not null/empty

### Output Examples

**QUIET Mode:**
```json
{
  "success": true,
  "task_id": "task-1-2-2",
  "task_data": {
    "id": "task-1-2-2",
    "type": "subtask",
    "title": "Document essential messages per level",
    "status": "pending",
    "parent": "task-1-2"
  },
  "dependencies": {
    "task_id": "task-1-2-2",
    "can_start": true
  }
}
```
**Estimated size:** ~480 chars (53% reduction)

**NORMAL Mode:** (Current behavior, but omit null/empty fields)

**VERBOSE Mode:**
```json
{
  "success": true,
  "task_id": "task-1-2-2",
  "task_data": { ... },
  "dependencies": { ... },
  "repo_root": "/home/tyler/Documents/GitHub/claude-sdd-toolkit",
  "needs_branch_creation": false,
  "dirty_tree_status": {
    "is_dirty": false,
    "message": "Clean"
  },
  "_debug": {
    "task_resolution": {
      "method": "prepare-task",
      "query_time_ms": 15,
      "cache_hit": true
    },
    "spec_metadata": {
      "spec_size_bytes": 45120,
      "total_phases": 2,
      "estimated_completion_date": "2025-11-18"
    }
  }
}
```
**Estimated size:** ~1,300 chars

---

## Command: progress

**Current output:** 330 chars (10 fields, 0% empty)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| spec_id | ESSENTIAL | ✓ | ✓ | ✓ |
| total_tasks | ESSENTIAL | ✓ | ✓ | ✓ |
| completed_tasks | ESSENTIAL | ✓ | ✓ | ✓ |
| percentage | ESSENTIAL | ✓ | ✓ | ✓ |
| current_phase | ESSENTIAL | ✓ | ✓ | ✓ |
| title | STANDARD | ✗ | ✓ | ✓ |
| status | STANDARD | ✗ | ✓ | ✓ |
| node_id | STANDARD | ✗ | ✓ | ✓ |
| type | STANDARD | ✗ | ✓ | ✓ |
| remaining_tasks | STANDARD | ✗ | ✓ | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

### Output Examples

**QUIET Mode:**
```json
{
  "spec_id": "cli-verbosity-reduction-2025-11-09-001",
  "total_tasks": 13,
  "completed_tasks": 3,
  "percentage": 23,
  "current_phase": {
    "id": "phase-1",
    "title": "Analysis & Baseline Assessment",
    "completed": 3,
    "total": 5
  }
}
```
**Estimated size:** ~200 chars (40% reduction)

**NORMAL Mode:** (Current behavior)

**VERBOSE Mode:**
```json
{
  "spec_id": "cli-verbosity-reduction-2025-11-09-001",
  "title": "CLI Verbosity Reduction Improvements",
  "status": "in_progress",
  "total_tasks": 13,
  "completed_tasks": 3,
  "percentage": 23,
  "remaining_tasks": 10,
  "current_phase": {
    "id": "phase-1",
    "title": "Analysis & Baseline Assessment",
    "completed": 3,
    "total": 5
  },
  "_debug": {
    "query_time_ms": 12,
    "phases": [
      {
        "id": "phase-1",
        "completed": 3,
        "total": 5,
        "percentage": 60
      },
      {
        "id": "phase-2",
        "completed": 0,
        "total": 8,
        "percentage": 0
      }
    ],
    "tasks_by_category": {
      "investigation": 2,
      "decision": 1,
      "implementation": 0
    }
  }
}
```
**Estimated size:** ~550 chars

---

## Command: validate

**Current output:** 305 chars (6 fields, 33% empty in schema)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| status | ESSENTIAL | ✓ | ✓ | ✓ |
| spec_id | STANDARD | ✗ | ✓ | ✓ |
| errors | STANDARD | ✗ | ✓ | ✓ |
| warnings | STANDARD | ✗ | ✓ | ✓ |
| auto_fixable_issues | STANDARD | ✗ | ✓ | ✓ |
| schema | STANDARD | ✗ | ✓ | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

### Output Examples

**QUIET Mode (Success):**
```json
{"status":"valid"}
```
**Estimated size:** ~18 chars (94% reduction for success)

**QUIET Mode (Error):**
```json
{
  "status": "invalid",
  "errors": [
    {
      "path": "tasks[3].dependencies",
      "message": "Circular dependency detected",
      "fix": "Remove task-2-1 from task-3-1.dependencies.depends"
    }
  ]
}
```
**Estimated size:** ~150-500 chars (depends on error count)

**NORMAL Mode:** (Current behavior)

**VERBOSE Mode:**
```json
{
  "spec_id": "cli-verbosity-reduction-2025-11-09-001",
  "status": "valid",
  "errors": 0,
  "warnings": 0,
  "auto_fixable_issues": 0,
  "schema": {
    "source": "/path/to/schema.json",
    "errors": [],
    "warnings": []
  },
  "_debug": {
    "validation_time_ms": 45,
    "checks_performed": [
      "schema_validation",
      "circular_dependencies",
      "orphaned_tasks",
      "missing_references"
    ],
    "spec_stats": {
      "total_nodes": 27,
      "max_depth": 4,
      "total_dependencies": 12
    }
  }
}
```
**Estimated size:** ~450 chars

---

## Command: check-deps

**Current output:** 88 chars (5 fields, 60% empty)

### Field Mapping

| Field | Category | QUIET | NORMAL | VERBOSE |
|-------|----------|-------|--------|---------|
| task_id | ESSENTIAL | ✓ | ✓ | ✓ |
| can_start | ESSENTIAL | ✓ | ✓ | ✓ |
| blocked_by | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| soft_depends | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| blocks | EMPTY-CONDITIONAL | ✗ | ✓* | ✓ |
| _debug | OPTIONAL | ✗ | ✗ | ✓ |

*Included in NORMAL only if not empty

### Output Examples

**QUIET Mode:**
```json
{
  "task_id": "task-1-2-2",
  "can_start": true
}
```
**Estimated size:** ~45 chars (49% reduction)

**NORMAL Mode (empty deps):**
```json
{
  "task_id": "task-1-2-2",
  "can_start": true
}
```

**NORMAL Mode (with deps):**
```json
{
  "task_id": "task-2-1",
  "can_start": false,
  "blocked_by": ["task-1-2"],
  "soft_depends": [],
  "blocks": ["task-2-2", "task-2-3"]
}
```

**VERBOSE Mode:**
```json
{
  "task_id": "task-2-1",
  "can_start": false,
  "blocked_by": ["task-1-2"],
  "soft_depends": [],
  "blocks": ["task-2-2", "task-2-3"],
  "_debug": {
    "dependency_graph": {
      "upstream_count": 1,
      "downstream_count": 2,
      "critical_path": true
    },
    "blocking_reason": "task-1-2 status is 'pending'",
    "estimated_unblock_date": "2025-11-15"
  }
}
```
**Estimated size:** ~250 chars

---

## Command: find-specs

**Current output:** 54 chars (plain text path)

### Output Behavior

| Mode | Output | Size |
|------|--------|------|
| QUIET | Plain text path | 54 chars |
| NORMAL | Plain text path | 54 chars |
| VERBOSE | JSON with metadata | ~150 chars |

**VERBOSE Mode:**
```json
{
  "specs_dir": "/home/tyler/Documents/GitHub/claude-sdd-toolkit/specs",
  "_debug": {
    "search_paths_checked": [
      "specs/",
      ".sdd/specs/",
      ".specs/"
    ],
    "total_specs_found": 30,
    "by_status": {
      "active": 1,
      "pending": 3,
      "completed": 25,
      "archived": 1
    }
  }
}
```

---

## Command: list-blockers

**Current output:** 3 chars (empty array when no blockers)

### Output Behavior

| Mode | Empty | With Blockers |
|------|-------|---------------|
| QUIET | `[]` | Minimal blocker info |
| NORMAL | `[]` | Full blocker info |
| VERBOSE | `[]` | Full info + debug |

**QUIET Mode (with blockers):**
```json
[
  {
    "task_id": "task-2-1",
    "blocked_by": ["task-1-2"]
  }
]
```

**VERBOSE Mode (with blockers):**
```json
[
  {
    "task_id": "task-2-1",
    "title": "Refine verbosity options handling",
    "blocked_by": ["task-1-2"],
    "blocking_since": "2025-11-15",
    "_debug": {
      "blocker_details": {
        "task-1-2": {
          "title": "Define verbosity policy",
          "status": "in_progress",
          "estimated_completion": "2025-11-15"
        }
      }
    }
  }
]
```

---

## Summary: Reduction Targets

### Per-Command Quiet Mode Reductions

| Command | Current | Quiet | Reduction |
|---------|---------|-------|-----------|
| list-specs | 7,520 | 3,000 | 60% |
| query-tasks | 5,761 | 2,400 | 58% |
| prepare-task | 1,027 | 480 | 53% |
| validate (success) | 305 | 18 | 94% |
| check-deps | 88 | 45 | 49% |
| progress | 330 | 200 | 39% |
| find-specs | 54 | 54 | 0% |
| list-blockers | 3 | 3 | 0% |

### Overall Impact

**Total measured (9 commands):** 23,478 chars
**Total quiet mode:** 8,600 chars
**Overall reduction:** 63% for measured commands

**Typical workflow session estimate:**
- Current: ~106,000 chars
- With quiet mode: ~40,000 chars
- **Session reduction: 62%**

---

## Implementation Notes

### JSON Field Omission Strategy

**Approach 1: Dynamic field filtering (Recommended)**
```python
def filter_fields_by_verbosity(data, level):
    if level == VerbosityLevel.QUIET:
        # Keep only ESSENTIAL and non-empty EMPTY-CONDITIONAL fields
        return {k: v for k, v in data.items()
                if is_essential(k) or (is_empty_conditional(k) and v)}
    elif level == VerbosityLevel.NORMAL:
        # Keep all except OPTIONAL
        return {k: v for k, v in data.items() if not is_optional(k)}
    else:  # VERBOSE
        # Include everything
        return data
```

**Approach 2: Schema-driven field filtering**
- Define field categories in JSON schema
- Filter based on verbosity level at serialization time
- Maintain single data structure internally

### Backward Compatibility Testing

**Test Matrix:**
| Test Case | QUIET | NORMAL | VERBOSE |
|-----------|-------|--------|---------|
| JSON parsability | ✓ | ✓ | ✓ |
| Required fields present | ✓ | ✓ | ✓ |
| Exit codes unchanged | ✓ | ✓ | ✓ |
| Pipe/jq compatibility | ✓ | ✓ | ✓ |
| Script compatibility | N/A | ✓ | N/A |

---

## Next Steps (Phase 2 Implementation)

**Tasks to reference this document:**
- task-2-1: Refine verbosity options handling
- task-2-2: Propagate verbosity policy through command registry
- task-2-3: Adjust shared printer defaults for quiet mode

**Implementation order:**
1. Implement field filtering utility functions
2. Update each command's output formatter
3. Add _debug section infrastructure for verbose mode
4. Update tests for all three verbosity levels
5. Update documentation with mode examples

