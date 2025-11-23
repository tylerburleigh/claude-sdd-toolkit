# Prepare-Task Default Context Upgrade - Analysis

## Executive Summary

This analysis captures requirements for upgrading `sdd prepare-task` to include richer default context without requiring enhancement flags. The goal is to reduce redundant CLI calls while maintaining backwards compatibility and meeting a <30ms overhead budget.

## Objectives

1. **Reduce redundant CLI calls**: Eliminate need for agents to call `sdd task-info`, `sdd check-deps`, and `sdd get-task` after running `prepare-task`
2. **Maintain backwards compatibility**: Preserve existing API surface and contract structure
3. **Meet latency budget**: Additional context gathering must add <30ms overhead
4. **Smart defaults**: Include context that 80%+ of task executions need

## Current State Analysis

### Existing Context Payload (from context_utils.py)

The `prepare-task` command already includes a `context` block with:

```python
{
    "previous_sibling": {
        "id": str,
        "title": str,
        "status": str,
        "type": str,
        "file_path": Optional[str],
        "completed_at": Optional[str],
        "journal_excerpt": Optional[Dict]  # timestamp, entry_type, summary (200 char limit)
    },
    "parent_task": {
        "id": str,
        "title": str,
        "type": str,
        "status": str,
        "description": Optional[str],
        "notes": List[str],
        "completed_tasks": int,
        "total_tasks": int,
        "remaining_tasks": int,
        "position_label": str,  # e.g., "2 of 3 subtasks"
        "children": List[Dict]  # id, title, status
    },
    "phase": {
        "id": str,
        "title": str,
        "status": str,
        "sequence_index": Optional[int],
        "completed_tasks": int,
        "total_tasks": int,
        "percentage": Optional[int],
        "summary": Optional[str],
        "blockers": List[str]
    },
    "sibling_files": List[Dict],  # task_id, title, status, file_path, last_modified_by, last_activity
    "task_journal": {
        "entry_count": int,
        "last_entry_at": Optional[str],
        "entries": List[Dict]  # max 3 entries, 160 char summary limit
    }
}
```

### Enhancement Flags (Optional Context)

Currently available via flags:
- `--include-full-journal`: Full journal entries for previous sibling (vs 200 char excerpt)
- `--include-phase-history`: All journal entries for current phase tasks
- `--include-spec-overview`: Spec-wide progress summary

### Existing Contract (from contracts.py)

The `extract_prepare_task_contract()` currently provides:

```python
{
    "task_id": str,
    "title": str,
    "can_start": bool,
    "blocked_by": List[str],
    "git": {
        "needs_branch": bool,
        "suggested_branch": str,
        "dirty": bool
    },
    "spec_complete": bool,

    # Conditional fields
    "file_path": Optional[str],
    "details": Optional[List[str]],
    "status": Optional[str],
    "validation_warnings": Optional[List[str]],
    "completion_info": Optional[Dict]
}
```

## Desired Default Payload Structure

### Core Enhancements

The default payload should include **WITHOUT FLAGS**:

1. **Task Metadata** (from task_data.metadata):
   - `task_category`: str (e.g., "research", "implementation", "verification")
   - `estimated_hours`: int
   - `acceptance_criteria`: Optional[List[str]]
   - `verification_type`: Optional[str] (for verify tasks)

2. **Dependency Details** (enhanced from current `blocked_by` list):
   - For each blocker: `{id, title, status, file_path}`
   - For tasks this blocks: `{id, title, status, file_path}`
   - Soft dependencies: `{id, title, status, file_path}`

3. **Implementation Hints**:
   - Previous sibling's full journal summary (not just 200 chars)
   - Files modified by previous sibling (from journal analysis)
   - Parent task's full description and notes

4. **Validation Context**:
   - Spec validation warnings (already included)
   - Task-specific validation issues

### Plan Validation Context (New Addition)

For tasks with `metadata.plan` field:
```python
"plan_validation": {
    "has_plan": bool,
    "plan_items": List[Dict],  # step, description, status
    "completed_steps": int,
    "total_steps": int,
    "current_step": Optional[Dict]
}
```

### File Context (Enhanced)

Expand `sibling_files` to include:
```python
{
    "task_id": str,
    "title": str,
    "status": str,
    "file_path": str,
    "last_modified_by": Optional[str],
    "last_activity": Optional[str],
    "changes_summary": Optional[str],  # From journal if available
    "lines_changed": Optional[int]     # From journal metadata
}
```

## Data Sources to Reuse

### From prepare-task Enhancement Flags

1. **Previous sibling journal** (`--include-full-journal`):
   - Currently opt-in, should be default
   - Already filtered to relevant task
   - Provides full context vs truncated excerpt

2. **Phase task IDs** (`collect_phase_task_ids`):
   - Already used for phase history
   - Can reuse to build phase progress context

3. **Spec overview** (`get_progress_summary`):
   - Currently behind `--include-spec-overview`
   - Should be default for completion detection

### From Existing Functions

1. **`check_dependencies()`** (discovery.py:192-255):
   - Already provides detailed blocker info
   - Currently called separately by agents
   - Should be included by default

2. **`get_task_info()`** (discovery.py:178-189):
   - Provides full task node data
   - Currently requires separate call
   - Should be merged into default payload

## Backwards Compatibility Expectations

### Must Preserve

1. **Existing contract structure**: All current contract fields remain
2. **Exit codes**: Success/failure semantics unchanged
3. **Flag behavior**: Enhancement flags continue to work
4. **Error messages**: Validation and error reporting unchanged

### Safe to Add

1. **New top-level fields**: Additive changes to contract
2. **Enhanced context fields**: Existing `context` block can grow
3. **New optional fields**: Conditional fields based on task type

### Migration Strategy

```python
# Old contract (still works)
{
    "task_id": "task-1-1",
    "title": "...",
    "can_start": true
}

# New contract (backwards compatible)
{
    "task_id": "task-1-1",
    "title": "...",
    "can_start": true,
    "context": {  # Enhanced, but agents can ignore if not ready
        "previous_sibling": {...},
        "dependencies": {...},  # NEW: detailed blocker info
        "task_metadata": {...}  # NEW: full metadata fields
    }
}
```

## Latency Budget Analysis

### Current Overhead Breakdown

From `prepare_task()` function (discovery.py:258-538):

1. **Spec loading & validation**: ~5-10ms
2. **Git operations**: ~10-15ms (optional)
3. **Context gathering** (lines 460-531):
   - `get_previous_sibling()`: ~2ms
   - `get_parent_context()`: ~2ms
   - `get_phase_context()`: ~3ms
   - `get_sibling_files()`: ~2ms
   - `get_task_journal_summary()`: ~3ms
   - **Total**: ~12ms

4. **Doc-query integration**: ~5-10ms (if available)

**Current total**: ~35-50ms

### Proposed Additions Budget

Target: <30ms additional overhead

1. **Detailed dependency info** (reuse `check_dependencies()`):
   - Already in-memory, just formatting
   - Estimated: ~3-5ms

2. **Full task metadata** (from existing `task_data`):
   - No additional I/O, just field extraction
   - Estimated: ~1-2ms

3. **Enhanced sibling files**:
   - Journal analysis for change summaries
   - Estimated: ~5-8ms (one-time per sibling)

4. **Plan validation context**:
   - Only for tasks with plans
   - Estimated: ~3-5ms (conditional)

**Proposed total additional**: ~15-25ms
**New total**: ~50-75ms (within acceptable range)

### Optimization Opportunities

1. **Lazy journal loading**: Cache journal entries in prepare-task to avoid re-parsing
2. **Parallel context gathering**: Run `get_previous_sibling` and `check_dependencies` concurrently
3. **Conditional enrichment**: Skip expensive operations for simple tasks

## Contract Appendix: Sample Payloads

### Legacy Output (Minimal)

```json
{
    "task_id": "task-1-1",
    "title": "Implement feature X",
    "can_start": true,
    "blocked_by": [],
    "git": {
        "needs_branch": false,
        "suggested_branch": "",
        "dirty": false
    },
    "spec_complete": false
}
```

**Token count**: ~150 tokens

### Enhanced Default Output (Proposed)

```json
{
    "task_id": "task-1-1",
    "title": "Implement feature X",
    "can_start": true,
    "blocked_by": [],
    "git": {
        "needs_branch": false,
        "suggested_branch": "",
        "dirty": false
    },
    "spec_complete": false,
    "context": {
        "previous_sibling": {
            "id": "task-1-0",
            "title": "Set up project structure",
            "status": "completed",
            "journal_excerpt": {
                "summary": "Created initial directory structure with src/, tests/, docs/. Initialized package.json with dependencies.",
                "timestamp": "2025-11-23T10:30:00Z"
            },
            "files_modified": ["package.json", "src/index.ts", "README.md"]
        },
        "parent_task": {
            "id": "phase-1",
            "title": "Foundation",
            "position_label": "2 of 5 children",
            "remaining_tasks": 3
        },
        "phase": {
            "title": "Phase 1: Foundation",
            "percentage": 40,
            "blockers": []
        },
        "dependencies": {
            "blocking": [],
            "blocked_by_details": [],
            "soft_depends": []
        },
        "task_metadata": {
            "category": "implementation",
            "estimated_hours": 2,
            "details": [
                "Create FeatureX class in src/features/",
                "Implement core methods: init(), process(), cleanup()",
                "Add unit tests with 80% coverage"
            ]
        }
    }
}
```

**Token count**: ~450 tokens
**Token increase**: ~300 tokens (3x)
**Value**: Eliminates 2-3 additional CLI calls (~600-900 tokens saved)

### With Enhancement Flags

```json
{
    "task_id": "task-1-1",
    "title": "Implement feature X",
    "can_start": true,
    "blocked_by": [],
    "git": {...},
    "spec_complete": false,
    "context": {...},  // Default context as above
    "extended_context": {
        "previous_sibling_journal": [
            {
                "timestamp": "2025-11-23T10:30:00Z",
                "entry_type": "completion",
                "content": "Full journal entry with all details about setup..."
            }
        ],
        "phase_journal": [...],
        "spec_overview": {
            "total_tasks": 24,
            "completed_tasks": 1,
            "percentage": 4
        }
    }
}
```

**Token count**: ~800-1000 tokens (with full journals)

## Recommendations

### Immediate Actions

1. **Add detailed dependencies to default context**: Reuse `check_dependencies()` output
2. **Include full previous sibling journal**: Promote `--include-full-journal` to default
3. **Extract task metadata fields**: Surface category, estimated_hours, details by default
4. **Update contract extraction**: Add new fields to `extract_prepare_task_contract()`

### Phased Rollout

**Phase 1** (Low risk, high value):
- Add dependency details to context
- Include task metadata in context
- Update contract extraction

**Phase 2** (Medium risk, medium value):
- Promote full previous sibling journal to default
- Add plan validation context for tasks with plans
- Enhanced sibling files with change summaries

**Phase 3** (Future enhancement):
- Spec overview as default (currently behind flag)
- Cross-phase dependency visualization
- Predictive next-task suggestions

## Success Criteria

1. **Reduced CLI calls**: Agents should not need to call `task-info` or `check-deps` after `prepare-task`
2. **Performance**: Total overhead remains <100ms for 95% of tasks
3. **Compatibility**: Existing consumers continue to work without changes
4. **Agent satisfaction**: sdd-next playbook shows reduced command usage in workflow sections

## References

- **Source files**:
  - `src/claude_skills/claude_skills/sdd_next/discovery.py`: prepare_task() implementation
  - `src/claude_skills/claude_skills/sdd_next/context_utils.py`: Context gathering functions
  - `src/claude_skills/claude_skills/common/contracts.py`: Contract extraction logic

- **Related specs**:
  - None (this is the foundational analysis)

- **Documentation**:
  - sdd-next SKILL.md (lines 430-460): Context gathering best practices
