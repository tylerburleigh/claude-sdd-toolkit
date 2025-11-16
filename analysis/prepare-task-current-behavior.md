# Current `sdd prepare-task` Behavior

## Sample Output (2025-11-15)

Command executed from repo root:

```bash
sdd prepare-task sdd-next-context-optimization-2025-11-15-001
```

The CLI returns a single JSON object:

```json
{
  "success": true,
  "task_id": "task-1-1",
  "task_data": {
    "type": "task",
    "title": "Document current prepare-task behavior",
    "status": "pending",
    "parent": "phase-1-files",
    "children": [],
    "dependencies": {
      "blocks": ["task-1-3"],
      "blocked_by": [],
      "depends": []
    },
    "total_tasks": 1,
    "completed_tasks": 0,
    "metadata": {
      "task_category": "investigation",
      "estimated_hours": 1,
      "description": "Analyze and document the exact output structure..."
    }
  },
  "dependencies": {
    "task_id": "task-1-1",
    "can_start": true,
    "blocked_by": [],
    "soft_depends": [],
    "blocks": [
      {"id": "task-1-3", "title": "Create design document...", "status": "pending", "file": ""}
    ]
  },
  "doc_context": null,
  "validation_warnings": [],
  "repo_root": "/home/tyler/Documents/GitHub/claude-sdd-toolkit",
  "needs_branch_creation": false,
  "dirty_tree_status": {
    "is_dirty": true,
    "message": "Dirty: 1 staged, 4 unstaged, 2 untracked"
  },
  "suggested_branch_name": null,
  "needs_commit_cadence": false,
  "spec_complete": false,
  "completion_info": null
}
```

### Top-Level Fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `success` | Boolean flag for CLI execution | No additional metadata |
| `task_id` | Recommended task identifier | Not paired with spec title/phase |
| `task_data` | Minimal spec record | Mirrors raw spec data without additional context |
| `dependencies` | Simplified dependency graph | Only IDs/status, no explanation |
| `doc_context` | Placeholder for inlined references | Usually `null`; never populated automatically |
| `validation_warnings` | Array of validation issues | Empty for most runs |
| `repo_root` | Absolute path to repo | Useful for multi-root setups |
| `needs_branch_creation` / `needs_commit_cadence` | Workflow hints | Boolean flags only |
| `dirty_tree_status` | Basic git summary | Message string, no file list |
| `suggested_branch_name` | Naming helper | Often `null` unless heuristics trigger |
| `spec_complete` / `completion_info` | Whether spec has remaining tasks | Does not include progress numbers |

### `task_data` Payload

- Identifies the task but only echoes spec JSON properties.
- Parent information is a bare ID (`"phase-1-files"`) with no title, sequence, or progress.
- Metadata is limited to `task_category`, `estimated_hours`, and `description`.
- No file paths, verification info, acceptance criteria, or related documentation.

## Context Gaps Driving 20+ Extra Calls

The sdd-next workflow relies on many other commands because the `prepare-task` payload lacks core context (see `skills/sdd-next/SKILL.md:133-205` and `skills/sdd-next/SKILL.md:150-163`). Missing data forces the agent to issue additional calls for every task:

| Missing context | Why it is needed | Commands currently required |
| --- | --- | --- |
| **Spec overview (title, % complete, remaining work)** | Needed at the start of every task to confirm we are on the right spec and to brief the user (`Single Task Workflow` step 3.1-3.2). | `sdd progress {spec}` |
| **Phase breakdown (phase titles, completion %, task counts)** | Agents must explain where the task lives and highlight nearby work; parent ID alone is insufficient. | `sdd list-phases {spec}` |
| **Backlog/alternative tasks and blockers** | To offer alternatives or confirm blockers before starting implementation. | `sdd query-tasks {spec}` + `sdd list-blockers {spec}` |
| **Detailed task metadata (verification type, files, doc links, acceptance criteria)** | Required to build the execution plan and determine verification mode. `task_data.metadata` only contains category/hour estimate/description. | `sdd task-info {spec} {task}` and, when more structure is needed, `sdd get-task {spec} {task} --json` |
| **Dependency readiness explanations** | The embedded `dependencies` block lists IDs, but the agent still has to confirm readiness, soft dependencies, and missing prerequisites. | `sdd check-deps {spec} {task}` |
| **Contextual documents or references** | `doc_context` is always `null`, so agents must run secondary queries (render, doc-query, or manual file reads) to gather docs mentioned in the spec. | `sdd render`, doc-query commands, or plain file reads |
| **Spec/phase blockers vs dirty tree** | Dirty tree summary is shallow (`"Dirty: 1 staged..."`). To know whether the tree state blocks the next task, agents re-run `git status` or `sdd list-blockers`. | `git status`, `sdd list-blockers {spec}` |
| **Next steps after completion** | Because `prepare-task` only covers the recommended task, agents must call it again post-implementation plus rerun `sdd progress`/`sdd list-phases` for updated summaries. | Repeat `sdd prepare-task`, `sdd progress`, `sdd list-phases` |

### Resulting Call Volume

Following the published workflow requires at least the following per task:

1. `sdd progress` – confirm spec selection.
2. `sdd list-phases` – brief phase context.
3. `sdd prepare-task` – recommended task payload.
4. `sdd task-info` + `sdd check-deps` (+ `sdd get-task` when metadata missing) – gather implementation details.
5. `sdd query-tasks` / `sdd list-blockers` – present alternatives or blockers.
6. `sdd progress` + `sdd list-phases` again after completion to report updated status.
7. `sdd prepare-task` again to surface the next recommendation.

That baseline already accounts for 8–10 commands for a straightforward task. Any deviation (blocked tasks, manual verification, additional documentation) quickly pushes total CLI calls past 20, because every missing context item above maps to another command. Enhancing `prepare-task` with spec/phase metadata, richer task payloads, and inline doc context would eliminate most of these follow-up calls and satisfy the spec goal of shrinking context gathering to 2–3 commands.
