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

## Contract Field Definitions

### Core Fields (Always Present)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `task_id` | string | Unique task identifier | `"task-1-2"` |
| `title` | string | Concise task description | `"Update prepare-task contract"` |
| `can_start` | boolean | Whether task can be started now | `true` |
| `blocked_by` | array[string] | Task IDs blocking this task | `["task-1-1"]` or `[]` |
| `git.needs_branch` | boolean | Whether new branch should be created | `false` |
| `git.suggested_branch` | string | Suggested branch name | `"feat/context-upgrade"` |
| `git.dirty` | boolean | Whether working tree has uncommitted changes | `false` |
| `spec_complete` | boolean | Whether spec is finished | `false` |
| `context` | object | Enhanced context payload (see below) | `{...}` |

### Context Block Fields (New Default)

| Field | Type | Description | Always Present? |
|-------|------|-------------|-----------------|
| `context.previous_sibling` | object\|null | Previous task in same group | Yes |
| `context.previous_sibling.id` | string | Sibling task ID | If present |
| `context.previous_sibling.title` | string | Sibling task title | If present |
| `context.previous_sibling.status` | string | Sibling task status | If present |
| `context.previous_sibling.journal_excerpt` | object\|null | Latest journal summary | If present |
| `context.parent_task` | object\|null | Parent task/group | Yes |
| `context.parent_task.id` | string | Parent ID | If present |
| `context.parent_task.title` | string | Parent title | If present |
| `context.parent_task.position_label` | string | Position in siblings (e.g., "2 of 5 children") | If present |
| `context.parent_task.remaining_tasks` | integer | Tasks left in parent | If present |
| `context.phase` | object\|null | Current phase context | Yes |
| `context.phase.title` | string | Phase title | If present |
| `context.phase.percentage` | integer | Phase completion % | If present |
| `context.phase.blockers` | array[string] | Phase-level blockers | If present |
| `context.sibling_files` | array[object] | Files modified by siblings | Yes (may be empty) |
| `context.task_journal` | object | Journal entries for current task | Yes |

### Optional Fields (Conditionally Included)

| Field | Type | Included When | Description |
|-------|------|---------------|-------------|
| `file_path` | string | Task has `metadata.file_path` | Target file for implementation |
| `details` | array[string] | Task has `metadata.details` | Implementation steps/hints |
| `task_metadata` | object | Metadata has enrichment fields | Full task metadata |
| `task_metadata.category` | string | Has `task_category` | Task type (research, implementation, verification) |
| `task_metadata.estimated_hours` | number | Has `estimated_hours` | Time estimate |
| `task_metadata.acceptance_criteria` | array[string] | Has `acceptance_criteria` | Success criteria |
| `task_metadata.verification_type` | string | Has `verification_type` | Verification method (auto, manual, fidelity) |
| `status` | string | Status != "pending" | Current task status |
| `validation_warnings` | array[string] | Non-empty warnings | Spec validation issues |
| `completion_info` | object | `spec_complete` is true | Completion details |
| `extended_context` | object | Enhancement flags used | Additional context from flags |

### Field Gating Semantics

**Smart Defaults Principle:**
- Core fields always present (no null checks needed)
- Context block always present, but sub-fields may be null
- Optional fields only included when they have meaningful values
- Empty arrays/objects omitted unless structurally required

**Consumer Compatibility:**
```python
# Older consumers (before context block)
if contract.get("can_start"):
    # Works fine, context is ignored

# New consumers (context-aware)
if contract.get("can_start"):
    prev_sibling = contract.get("context", {}).get("previous_sibling")
    if prev_sibling:
        # Use rich context
```

## Compatibility Matrix

### Version Detection

Consumers can detect payload version by checking for presence of `context` field:

```python
def get_contract_version(contract):
    if "context" in contract:
        if "task_metadata" in contract:
            return "v3"  # Full enhanced context
        return "v2"  # Basic context block
    return "v1"  # Legacy minimal contract
```

### Version Comparison

| Feature | v1 (Legacy) | v2 (Basic Context) | v3 (Full Enhanced) |
|---------|-------------|--------------------|--------------------|
| Core fields (task_id, title, can_start, etc.) | ✅ | ✅ | ✅ |
| Git fields (needs_branch, dirty, etc.) | ✅ | ✅ | ✅ |
| Context block | ❌ | ✅ | ✅ |
| Previous sibling context | ❌ | ✅ (basic) | ✅ (with journal) |
| Parent task context | ❌ | ✅ | ✅ |
| Phase context | ❌ | ✅ | ✅ |
| Task metadata extraction | ❌ | ❌ | ✅ |
| Acceptance criteria | ❌ | ❌ | ✅ |
| Verification type | ❌ | ❌ | ✅ |
| Extended context support | ❌ | ✅ | ✅ |

### Migration Path

**Phase 1: v1 → v2 (Add context block)**
- Status: **Current implementation** (as of task-1-2)
- Changes: Add `context` field to contract extraction
- Backwards compatible: Yes (additive only)
- Consumers: Can ignore context if not ready

**Phase 2: v2 → v3 (Add task metadata)**
- Status: **Planned** (implementation phase)
- Changes: Add `task_metadata` extraction
- Backwards compatible: Yes (additive only)
- Consumers: Optional field, can be ignored

**Phase 3: Full Enhancement (Promote flags to defaults)**
- Status: **Future**
- Changes: Include full journal in previous_sibling by default
- Backwards compatible: Yes (existing flags still work)
- Performance: May add 10-15ms, within budget

### Consumer Guidance

**For Older Consumers (v1):**
```python
# No changes needed - contract structure unchanged
task_id = contract["task_id"]
can_start = contract["can_start"]
```

**For Context-Aware Consumers (v2):**
```python
# Optionally use context for better decisions
task_id = contract["task_id"]
can_start = contract["can_start"]

# Safe access to context
context = contract.get("context", {})
prev_sibling = context.get("previous_sibling")
if prev_sibling:
    print(f"Follows: {prev_sibling['title']}")
```

**For Full Enhancement Consumers (v3):**
```python
# Use all available context
task_id = contract["task_id"]
can_start = contract["can_start"]

# Access task metadata
metadata = contract.get("task_metadata", {})
category = metadata.get("category", "unknown")
est_hours = metadata.get("estimated_hours", 0)

# Access rich context
context = contract["context"]
if context["previous_sibling"]:
    journal = context["previous_sibling"].get("journal_excerpt", {})
    print(f"Previous work: {journal.get('summary', 'N/A')}")
```

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

## Doc Context Integration Design (Task 1-2)

### Overview

This section defines the contract for integrating codebase documentation context into `sdd prepare-task` output. The design balances rich context delivery with performance constraints and graceful degradation when documentation is unavailable.

### Enhanced doc_context Schema

```python
"doc_context": {
    # Core availability fields (always present)
    "available": bool,              # True if documentation exists and is accessible
    "status": str,                  # "available", "stale", "unavailable", "generating"
    "message": str,                 # Human-readable status message

    # Context payload (present when available=True)
    "suggested_files": List[str],   # File paths ranked by relevance
    "relevant_modules": List[Dict], # Module summaries with statistics
    "relevant_functions": List[Dict], # Function matches with signatures
    "relevant_classes": List[Dict], # Class matches with methods
    "dependencies": List[str],      # Module dependencies extracted from docs
    "similar_implementations": List[Dict], # Similar code patterns for reference
    "complexity_insights": Dict,    # Complexity analysis for suggested files
    "test_context": Optional[Dict], # Test files and coverage estimates (if file_path specified)

    # Telemetry and provenance (always present)
    "telemetry": {
        "query_time_ms": int,       # Time taken to gather context
        "keywords_extracted": List[str], # Keywords used for search
        "result_count": Dict,       # Counts by entity type
        "doc_generation_date": Optional[str], # ISO timestamp when docs were generated
        "doc_location": Optional[str] # Path to codebase.json
    },

    # Freshness metadata (present when available=True)
    "freshness": {
        "generated_at": str,        # ISO timestamp
        "generated_at_commit": str, # Git SHA when docs were generated
        "current_commit": str,      # Current HEAD commit SHA
        "commits_since": int,       # Number of commits since generation
        "files_changed": int,       # Files changed since generation
        "is_stale": bool,           # True if commits_since exceeds threshold
        "stale_reason": Optional[str], # Explanation if stale
        "refresh_recommended": bool # True if refresh would improve quality
    }
}
```

### Schema Field Definitions

#### Core Fields

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `available` | bool | Yes | True if documentation query succeeded |
| `status` | str | Yes | One of: "available", "stale", "unavailable", "generating" |
| `message` | str | Yes | User-facing status description |

#### Context Payload Fields (when available=True)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `suggested_files` | List[str] | File paths ranked by relevance score | `["src/auth.py", "tests/test_auth.py"]` |
| `relevant_modules` | List[Dict] | Module summaries with stats | `[{"name": "auth", "file": "src/auth.py", "statistics": {...}}]` |
| `relevant_functions` | List[Dict] | Function matches | `[{"name": "login", "file": "src/auth.py", "signature": "def login(user, pwd)"}]` |
| `relevant_classes` | List[Dict] | Class matches with methods | `[{"name": "AuthHandler", "methods": ["login", "logout"]}]` |
| `dependencies` | List[str] | Module dependencies | `["jwt", "bcrypt", "database"]` |
| `similar_implementations` | List[Dict] | Similar patterns | `[{"name": "oauth_login", "file": "src/oauth.py"}]` |
| `complexity_insights` | Dict | Complexity analysis | `{"high_complexity_functions": [...], "refactor_candidates": [...]}` |
| `test_context` | Dict\|None | Test coverage info (only when task has file_path) | `{"test_files": [...], "coverage_estimate": "medium"}` |

#### Telemetry Fields (always present)

| Field | Type | Description |
|-------|------|-------------|
| `query_time_ms` | int | Milliseconds spent gathering doc context |
| `keywords_extracted` | List[str] | Keywords extracted from task description |
| `result_count` | Dict | Entity counts: `{"classes": 3, "functions": 12, "modules": 5}` |
| `doc_generation_date` | str\|None | ISO timestamp when docs were generated |
| `doc_location` | str\|None | Path to codebase.json |

#### Freshness Fields (when available=True)

| Field | Type | Description |
|-------|------|-------------|
| `generated_at` | str | ISO timestamp of doc generation |
| `generated_at_commit` | str | Git SHA when documentation was generated |
| `current_commit` | str | Current HEAD commit SHA |
| `commits_since` | int | Number of commits since doc generation |
| `files_changed` | int | Number of files changed since doc generation |
| `is_stale` | bool | True if commits_since exceeds threshold (default: 10) |
| `stale_reason` | str\|None | Explanation if stale (e.g., "15 commits since generation") |
| `refresh_recommended` | bool | True if refresh would improve quality |

### Gating Rules and Status States

#### Status State Definitions

| Status | Condition | Behavior |
|--------|-----------|----------|
| `"available"` | Docs exist, fresh (commits_since < threshold), query succeeded | Return full context payload |
| `"stale"` | Docs exist but commits_since ≥ threshold | Return context payload with freshness warning |
| `"unavailable"` | No docs found or `check_doc_query_available()` failed | Return minimal payload with generation suggestion |
| `"generating"` | Doc generation in progress (reserved for future) | Return minimal payload with wait message |

#### Gating Logic Flow

```python
def determine_doc_context_status(task_data):
    # Check availability first
    doc_check = check_doc_query_available()

    if not doc_check["available"]:
        return {
            "available": False,
            "status": "unavailable",
            "message": "No documentation found. Run `sdd doc generate` to enable context gathering."
        }

    # Check git-based freshness
    generated_at_commit = doc_check["stats"].get("generated_at_commit")
    if not generated_at_commit:
        # Missing git metadata, treat as available but unknown freshness
        return query_docs_and_build_payload(task_data, is_stale=False)

    # Get current commit and count commits since generation
    current_commit = get_current_git_commit()
    commits_since = count_commits_between(generated_at_commit, current_commit)
    commit_threshold = get_commit_staleness_threshold()  # Default: 10 commits

    is_stale = commits_since >= commit_threshold

    if is_stale:
        return {
            "available": True,
            "status": "stale",
            "message": f"{commits_since} commits since doc generation (threshold: {commit_threshold}). Consider running `sdd doc generate --refresh`.",
            **query_docs_and_build_payload(task_data, is_stale=True)
        }

    # Fresh and available
    return {
        "available": True,
        "status": "available",
        "message": f"Found {result_count} relevant entities from fresh documentation ({commits_since} commits since generation)",
        **query_docs_and_build_payload(task_data, is_stale=False)
    }
```

### Freshness Policy

#### Commit-Based Thresholds

| Documentation Type | Commit Threshold | Rationale |
|-------------------|------------------|-----------|
| **Default** | 10 commits | Balance between freshness and regeneration cost |
| **Fast-changing repos** | 5 commits | High commit velocity, frequent changes |
| **Stable repos** | 25 commits | Infrequent changes, stable APIs |

Configuration via `.claude/sdd_config.json`:
```json
{
  "doc_context": {
    "staleness_commit_threshold": 10,
    "auto_refresh_on_stale": false,
    "skip_stale_warning": false
  }
}
```

#### Staleness Detection

```python
def is_documentation_stale(doc_stats, commit_threshold=10):
    """
    Determine if documentation is stale based on commits since generation.

    Returns:
        tuple[bool, str]: (is_stale, reason)
    """
    generated_at_commit = doc_stats.get("generated_at_commit")
    if not generated_at_commit:
        return (False, "Unknown generation commit")

    current_commit = get_current_git_commit()
    commits_since = count_commits_between(generated_at_commit, current_commit)

    if commits_since >= commit_threshold:
        return (True, f"{commits_since} commits since doc generation (threshold: {commit_threshold})")

    return (False, None)
```

#### Cache Invalidation Triggers

Documentation should be regenerated when:

1. **Commit-based**: Commits since generation exceed threshold (default: 10)
2. **File-based**: Significant code changes detected
   - New Python/JS/etc files added in tracked directories
   - Major refactoring (>20% of tracked files modified)
   - Dependency changes (package.json, requirements.txt, pyproject.toml modified)
3. **Branch-based**: Switched to different branch since generation
4. **Manual**: User runs `sdd doc generate --force`

#### Refresh Strategies

| Strategy | When to Use | Implementation |
|----------|-------------|----------------|
| **Passive** | Default behavior | Show staleness warning, suggest refresh |
| **Auto-refresh** | CI/CD pipelines | Set `auto_refresh_on_stale: true` in config |
| **On-demand** | User-triggered | Call `sdd doc generate` before prepare-task |

### Fallback Behavior

#### When Documentation Unavailable

```python
{
    "available": False,
    "status": "unavailable",
    "message": "No documentation found. Run `sdd doc generate` to enable context gathering.",
    "telemetry": {
        "query_time_ms": 0,
        "keywords_extracted": [],
        "result_count": {},
        "doc_generation_date": None,
        "doc_location": None
    }
}
```

**Agent behavior:**
- Proceed with task using only spec-provided context
- Rely on manual exploration (`Read`, `Glob`, `Grep`)
- Log recommendation to generate docs

#### When Documentation Stale

```python
{
    "available": True,
    "status": "stale",
    "message": "15 commits since doc generation (threshold: 10). Results may be outdated.",
    "suggested_files": [...],  # Include results despite staleness
    "freshness": {
        "generated_at": "2025-11-21T12:00:00Z",
        "generated_at_commit": "abc123def456",
        "current_commit": "789ghi012jkl",
        "commits_since": 15,
        "files_changed": 42,
        "is_stale": True,
        "stale_reason": "15 commits since doc generation (threshold: 10)",
        "refresh_recommended": True
    },
    "telemetry": {...}
}
```

**Agent behavior:**
- Use stale context as starting point
- Verify critical files with `Read` before implementation
- Recommend refresh if results seem outdated

#### When Query Fails

```python
{
    "available": False,
    "status": "unavailable",
    "message": "Documentation query failed: TimeoutError",
    "telemetry": {
        "query_time_ms": 5000,
        "keywords_extracted": ["auth", "login"],
        "result_count": {},
        "doc_generation_date": None,
        "doc_location": "/path/to/codebase.json"
    }
}
```

**Agent behavior:**
- Log error for debugging
- Fall back to manual exploration
- Continue with task using spec context only

### Integration with prepare_task()

#### Modified prepare_task() Flow

```python
def prepare_task(spec_id, task_id=None, ...):
    # ... existing logic ...

    # Gather doc context (enhanced)
    doc_context = None
    if check_sdd_integration_available():
        try:
            # Build task description for query
            task_description = build_task_description(task_data)

            # Gather context with timeout
            gatherer = SDDContextGatherer()
            start_time = time.time()

            context_data = gatherer.get_task_context(task_description)
            query_time_ms = int((time.time() - start_time) * 1000)

            # Build enhanced payload
            doc_context = build_doc_context_payload(
                context_data,
                query_time_ms,
                task_data
            )

        except Exception as e:
            # Graceful degradation
            doc_context = {
                "available": False,
                "status": "unavailable",
                "message": f"Documentation query failed: {type(e).__name__}",
                "telemetry": {
                    "query_time_ms": 0,
                    "keywords_extracted": [],
                    "result_count": {},
                    "doc_generation_date": None,
                    "doc_location": None
                }
            }

    result["doc_context"] = doc_context
    # ... rest of prepare_task ...
```

#### Helper Functions

```python
def build_task_description(task_data):
    """
    Build comprehensive task description for doc query.

    Combines:
    - Task title
    - Metadata details
    - File path (if specified)
    """
    parts = [task_data["title"]]

    if "details" in task_data.get("metadata", {}):
        parts.extend(task_data["metadata"]["details"])

    if "file_path" in task_data.get("metadata", {}):
        parts.append(f"Target file: {task_data['metadata']['file_path']}")

    return " ".join(parts)

def build_doc_context_payload(context_data, query_time_ms, task_data):
    """
    Build standardized doc_context payload from SDDContextGatherer results.
    """
    doc_stats = context_data.get("metadata", {})
    generated_at = doc_stats.get("generated_at")
    generated_at_commit = doc_stats.get("generated_at_commit")

    # Calculate git-based freshness
    freshness = None
    is_stale = False
    if generated_at_commit:
        current_commit = get_current_git_commit()
        commits_since = count_commits_between(generated_at_commit, current_commit)
        files_changed = count_files_changed_between(generated_at_commit, current_commit)
        commit_threshold = get_commit_staleness_threshold()
        is_stale = commits_since >= commit_threshold

        freshness = {
            "generated_at": generated_at,
            "generated_at_commit": generated_at_commit,
            "current_commit": current_commit,
            "commits_since": commits_since,
            "files_changed": files_changed,
            "is_stale": is_stale,
            "stale_reason": f"{commits_since} commits since doc generation (threshold: {commit_threshold})" if is_stale else None,
            "refresh_recommended": is_stale
        }

    # Determine status
    status = "stale" if is_stale else "available"
    message = (
        f"{freshness['commits_since']} commits since doc generation. Consider refreshing." if is_stale
        else f"Found {len(context_data['suggested_files'])} relevant files ({freshness['commits_since']} commits since generation)"
    )

    return {
        "available": True,
        "status": status,
        "message": message,
        "suggested_files": context_data["suggested_files"],
        "relevant_modules": context_data["module_summaries"],
        "relevant_functions": [f.data for f in context_data["relevant_functions"]],
        "relevant_classes": [c.data for c in context_data["relevant_classes"]],
        "dependencies": context_data["dependencies"],
        "similar_implementations": [],  # TODO: implement in Phase 2
        "complexity_insights": {},      # TODO: implement in Phase 2
        "test_context": None,           # TODO: implement if file_path specified
        "telemetry": {
            "query_time_ms": query_time_ms,
            "keywords_extracted": context_data["keywords"],
            "result_count": {
                "classes": len(context_data["relevant_classes"]),
                "functions": len(context_data["relevant_functions"]),
                "modules": len(context_data["relevant_modules"]),
                "files": len(context_data["suggested_files"])
            },
            "doc_generation_date": generated_at,
            "doc_location": doc_stats.get("location")
        },
        "freshness": freshness
    }
```

### Performance Considerations

#### Latency Budget

| Operation | Target | Maximum |
|-----------|--------|---------|
| Doc availability check | <5ms | 10ms |
| Context query | <50ms | 200ms |
| Total overhead | <55ms | 210ms |

#### Optimization Strategies

1. **Cache availability check**: Store `check_doc_query_available()` result for session
2. **Limit result sets**: Cap entities per type (e.g., top 10 functions, top 5 modules)
3. **Lazy loading**: Defer `test_context` and `complexity_insights` to Phase 2
4. **Timeout handling**: Abort query after 200ms, return partial results

#### Token Usage Impact

| Scenario | Token Increase | Justification |
|----------|----------------|---------------|
| Docs unavailable | +50 tokens | Minimal fallback payload |
| Docs available, few results | +200 tokens | Small suggested_files list |
| Docs available, many results | +500 tokens | Full payload with modules/functions |
| Docs stale | +550 tokens | Full payload + freshness warning |

**Trade-off:** 200-500 token increase eliminates 2-3 subsequent CLI calls (saving 600-1200 tokens net).

### Configuration Options

Add to `.claude/sdd_config.json`:

```json
{
  "doc_context": {
    "enabled": true,
    "staleness_commit_threshold": 10,
    "auto_refresh_on_stale": false,
    "skip_stale_warning": false,
    "max_suggested_files": 20,
    "max_results_per_type": 10,
    "query_timeout_ms": 200,
    "include_test_context": true,
    "include_complexity_insights": false
  }
}
```

### Testing Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Docs never generated | `status: "unavailable"`, suggest generation |
| Docs fresh (<10 commits) | `status: "available"`, full payload with commit count |
| Docs stale (≥10 commits) | `status: "stale"`, full payload with freshness warning |
| Query timeout | `status: "unavailable"`, graceful degradation |
| Empty results | `status: "available"`, empty lists, message indicates no matches |
| Task with file_path | Include `test_context` field |
| Task without file_path | Omit `test_context` field |
| Non-git repository | Treat as fresh (missing commit metadata) |

### Design Decision: Git-Based vs Time-Based Freshness

**Decision:** Use git commit history for freshness detection instead of time-based TTL.

**Rationale:**
1. **Accuracy**: Documentation staleness should reflect code changes, not arbitrary time periods
2. **Efficiency**: Stable repos won't regenerate unnecessarily
3. **Responsiveness**: Active repos get fresh docs immediately when commits accumulate
4. **Provenance**: Git SHA provides precise tracking of what code version docs represent
5. **CI/CD friendly**: Integrates naturally with git-based workflows

**Trade-offs accepted:**
- Requires git integration (gracefully degrades if unavailable)
- Slightly more complex implementation than time-based
- Needs configuration tuning per repo velocity (5-25 commit threshold range)

**Fallback behavior:**
- Non-git repositories: Treat as fresh (missing commit metadata)
- Git metadata missing: Treat as available but unknown freshness
- Git command failures: Log error, treat as fresh

### Implementation Checklist

- [ ] Add `doc_context` field to prepare-task contract extraction
- [ ] Implement `build_task_description()` helper
- [ ] Implement `build_doc_context_payload()` helper
- [ ] Implement `get_commit_staleness_threshold()` config reader
- [ ] Implement `get_current_git_commit()` helper
- [ ] Implement `count_commits_between(commit_a, commit_b)` helper
- [ ] Implement `count_files_changed_between(commit_a, commit_b)` helper
- [ ] Add git-based freshness calculation logic
- [ ] Add gating logic for status determination
- [ ] Add telemetry tracking
- [ ] Store git commit SHA when generating docs (`sdd doc generate`)
- [ ] Update contract tests for new schema
- [ ] Document agent consumption patterns in sdd-next SKILL.md

## References

- **Source files**:
  - `src/claude_skills/claude_skills/sdd_next/discovery.py`: prepare_task() implementation
  - `src/claude_skills/claude_skills/sdd_next/context_utils.py`: Context gathering functions
  - `src/claude_skills/claude_skills/common/contracts.py`: Contract extraction logic
  - `src/claude_skills/claude_skills/common/doc_helper.py`: Documentation availability checks
  - `src/claude_skills/claude_skills/doc_query/sdd_integration.py`: SDDContextGatherer implementation

- **Related specs**:
  - prepare-task-doc-context-2025-11-24-001: Current specification

- **Documentation**:
  - sdd-next SKILL.md (lines 430-460): Context gathering best practices
