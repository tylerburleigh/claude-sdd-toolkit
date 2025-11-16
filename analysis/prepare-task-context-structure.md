# Proposed `context` Field for `sdd prepare-task`

## Goals & Scope

This document answers task `task-1-3-1` (“Define context data structure”). The new `context` payload must eliminate the current “horse blinders” issue where agents run 20+ additional commands to gather background data (see `analysis/prepare-task-current-behavior.md:83`). The field lives alongside existing `prepare-task` keys and is always present (using `null` for unavailable subsections) so that a single CLI call surfaces spec, phase, sibling, and journal intelligence required by the `skills/sdd-next/SKILL.md` workflow.

Key sources that the CLI should hydrate automatically:
- In-memory spec hierarchy (`hierarchy` map and metadata)
- Dependency graph already loaded by `prepare_task`
- Spec journal entries (via `get_task_journal`)
- File metadata embedded in sibling tasks

No doc-query or filesystem scans should happen inside this payload—only spec-derived data so we stay within the <30 ms overhead target noted in later performance tasks.

## Top-Level Structure

```jsonc
{
  "context": {
    "previous_sibling": { ... } | null,
    "parent_task": { ... },
    "phase": { ... },
    "sibling_files": [ ... ],
    "task_journal": { ... }
  }
}
```

### Field Summary

| Field | Purpose | Replaces extra commands |
| --- | --- | --- |
| `previous_sibling` | Snapshot of the most recent sibling (same parent) to show continuity and reuse of assets | `sdd task-info` / manual browsing |
| `parent_task` | Rich metadata about the immediate parent group/phase, including progress counts | `sdd query-tasks` + manual spec digging |
| `phase` | Consolidated `list-phases` data for the phase containing this task | `sdd list-phases` |
| `sibling_files` | Filepaths and ownership info for tasks under the same parent | `sdd query-tasks` + metadata scraping |
| `task_journal` | Compact history for current task so agents know what already happened | `sdd get-task`, `sdd get-journal` / manual journal scans |

All objects use consistent conventions:
- `id`, `title`, `status`, `type` (when available)
- Counts named `completed_tasks`, `total_tasks`
- List fields sorted by execution order
- Optional timestamps serialized as ISO 8601 strings

## `previous_sibling`

Represents the sibling task that precedes the current one under the same parent. If the selected task is first in order, this block is `null`.

```json
"previous_sibling": {
  "id": "task-1-2",
  "title": "Audit prepare-task docs",
  "status": "completed",
  "type": "task",
  "file_path": "docs/research/sdd-next/cli-output-audit-sdd-next.md",
  "metadata": {
    "task_category": "analysis",
    "estimated_hours": 1.0
  },
  "completed_at": "2025-11-15T19:04:23Z",
  "journal_excerpt": {
    "timestamp": "2025-11-15T19:05:02Z",
    "entry_type": "decision",
    "summary": "Captured missing context list for prepare-task (10 bullet points)."
  }
}
```

**Derivation notes**
- “Previous” uses the ordering already encoded in `outline` / `children` arrays of the parent node. Walk backwards to find the most recent sibling that is not the current task.
- `journal_excerpt` includes at most the latest entry for that sibling (if present) to surface insights worth reusing.
- `completed_at` comes from the sibling metadata; fallback to `null` when missing.

## `parent_task`

Describes the immediate parent object (which might be another task, a group, or a phase) so the agent can cite its scope without querying additional commands.

```json
"parent_task": {
  "id": "task-1-3",
  "title": "Create design document for enhanced context",
  "type": "task",
  "status": "in_progress",
  "description": "Create comprehensive design document defining new context structure, edge case handling strategy, and performance impact analysis.",
  "completed_tasks": 0,
  "total_tasks": 3,
  "remaining_tasks": 3,
  "children": [
    {"id": "task-1-3-1", "title": "Define context data structure", "status": "pending"},
    {"id": "task-1-3-2", "title": "Document edge case handling", "status": "pending"},
    {"id": "task-1-3-3", "title": "Analyze performance impact", "status": "pending"}
  ],
  "notes": [
    {
      "source": "spec_metadata",
      "content": "Blocks phase-2 design tasks until context contract is approved."
    }
  ]
}
```

**Derivation notes**
- Always include child stubs (ID/title/status) so agents can offer alternatives without `sdd query-tasks`.
- `remaining_tasks` is a convenience field (`total - completed`) flagged by the spec requirement “reduce context gathering from 20+ calls to 2-3 calls.”
- `notes` captures relevant metadata bits such as blockers, doc pointers, or acceptance criteria found in the parent’s metadata. Keep entries short (<200 chars).

## `phase`

Provides the relevant slice from `sdd list-phases` for the phase that contains the current task. This ensures the agent can report phase progress without rerunning another CLI command.

```json
"phase": {
  "id": "phase-1",
  "title": "Analysis & Documentation",
  "status": "in_progress",
  "sequence_index": 1,
  "completed_tasks": 1,
  "total_tasks": 5,
  "percentage": 20,
  "summary": "Document current prepare-task behavior and design enhanced context contract.",
  "blockers": []
}
```

**Derivation notes**
- `sequence_index` is 1-based order within the spec.
- `summary` can reuse the phase description from the spec metadata.
- `blockers` is a list of task IDs currently blocking the phase (if any); data already exists in the hierarchy and `dependencies`.

## `sibling_files`

List of files touched by other tasks under the same parent node. Enables immediate awareness of nearby implementation surfaces and reduces repeated `task-info` calls.

```json
"sibling_files": [
  {
    "task_id": "task-1-3-2",
    "title": "Document edge case handling",
    "status": "pending",
    "file_path": "analysis/prepare-task-context-edge-cases.md",
    "last_modified_by": "agent",
    "last_activity": "2025-11-15T21:12:00Z"
  },
  {
    "task_id": "task-1-3-3",
    "title": "Analyze performance impact",
    "status": "pending",
    "file_path": "analysis/prepare-task-context-performance.md",
    "last_modified_by": null,
    "last_activity": null
  }
]
```

**Derivation notes**
- Source data: sibling tasks’ `metadata.file_path` plus optional `metadata.last_modified` / `last_author` fields if present. Fall back to `null` when unknown.
- Order entries according to the parent’s child list so agents can reason sequentially.
- Exclude duplicates and items without a file path.

## `task_journal`

Summarizes journal history for the active task so the agent can quickly see what has already been logged (decisions, blockers, deviations) before editing files.

```json
"task_journal": {
  "entry_count": 2,
  "last_entry_at": "2025-11-16T13:06:23Z",
  "entries": [
    {
      "timestamp": "2025-11-16T13:06:23Z",
      "entry_type": "note",
      "title": "Completed task-1-1",
      "summary": "Documented current prepare-task output and missing context.",
      "author": "agent"
    },
    {
      "timestamp": "2025-11-16T13:06:15Z",
      "entry_type": "status_change",
      "title": "Started task-1-1",
      "summary": "Documenting prepare-task output structure.",
      "author": "agent"
    }
  ]
}
```

**Derivation notes**
- Use `get_task_journal(spec_id, task_id, specs_dir)` to fetch entries; slice to the most recent 3–5 entries to stay compact.
- `summary` is the first 160 characters of `content`.
- Include `entry_count` so agents know whether full history exists elsewhere.
- If no journal entries exist yet, set `task_journal` to `{"entry_count": 0, "entries": []}`.

## Example Response Snippet

Putting it together, the relevant portion of the enhanced `prepare-task` output would resemble:

```jsonc
{
  "success": true,
  "task_id": "task-1-3-1",
  "task_data": { ... },
  "dependencies": { ... },
  "context": {
    "previous_sibling": { /* as defined above */ },
    "parent_task": { /* ... */ },
    "phase": { /* ... */ },
    "sibling_files": [ /* ... */ ],
    "task_journal": { /* ... */ }
  },
  "repo_root": "...",
  "dirty_tree_status": { ... }
}
```

With this payload, an agent can satisfy the open-loop requirements in `skills/sdd-next/SKILL.md` (spec+phase briefing, dependency awareness, journal history) immediately after a single command. Subsequent subtasks (edge cases, performance analysis, implementation) can now treat this schema as the contract for both CLI output and downstream consumers.

## Edge Case Handling

Task `task-1-3-2` calls for explicit rules to keep the `context` block predictable across unusual scenarios. Each case below maps to one or more of the schema fields defined earlier.

| Scenario | Expected behavior |
| --- | --- |
| **No previous sibling (first child)** | Set `previous_sibling` to `null` and include a `"reason": "first_child"` note if desired for logging. Sibling-derived sections (`sibling_files`) still list other children (if any). |
| **Parent is a phase/group** | Treat the immediate parent uniformly regardless of type. `parent_task.type` mirrors the spec node type (`phase`, `group`, `task`). When the parent is itself a phase, populate `children` with its direct tasks/groups, and still emit the separate `phase` object (which may be the same ID). |
| **No journal entries yet** | Return `task_journal: {"entry_count": 0, "entries": []}` and omit `last_entry_at`. Downstream agents can test `entry_count` rather than checking for `null`. |
| **Parallel tasks / sibling ordering ties** | Preserve the original `children` order from the spec hierarchy. If multiple siblings share the same timestamp or start concurrently, ordering still follows the spec outline; `previous_sibling` simply becomes the entry immediately before the current index, independent of status. |
| **Orphan task (missing parent pointer)** | Leave `parent_task` set to `null` and add a lightweight warning in `context.parent_task_warning` (e.g., `"parent_missing": true`). Phase data is still derived by walking up the hierarchy from the spec root so that the `phase` object remains populated. |
| **Deeply nested phases (phase → group → task)** | Walk ancestors until the nearest `type == "phase"` node and populate the `phase` object from that node. `parent_task` still reflects the immediate parent (possibly a group), ensuring both local and phase-level context are available. |

### Additional Notes
- **Missing file paths:** Skip entries in `sibling_files` when the sibling has no `metadata.file_path` to avoid noise.
- **Journal truncation:** Even when edge cases are present, limit `task_journal.entries` to the newest 3–5 entries so the field stays compact.
- **Null vs empty arrays:** Prefer `null` for absent single objects (`previous_sibling`, `parent_task`) and empty arrays/objects for list containers, matching the rest of the CLI contract style.
