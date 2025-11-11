## Overview

- **Purpose:** Provide a repeatable `sdd`-CLI playbook for discovering specs, selecting the next actionable task, and keeping the user in the loop from planning through wrap-up.
- **Scope:** Applies to single-task pulls as well as phase-focused loops; assumes work happens inside `/Users/tylerburleigh/Documents/claude-sdd-toolkit`.
- **Audience:** Agents orchestrating SDD workflows who must respect human checkpoints and CLI guardrails.

### High-Level Flow Diagram

```
Start
  |
  v
Discover Specs -> Gather Context -> Select Task
  |                         |
  |                     Alternatives?
  |                     /         \
  |            yes -> Browse   no -> Prepare Recommended Task
  |                     \         /
  v                      v       v
Draft Plan -> Seek Approval -> Implementation Handoff
  |
  v
Post-Implementation Checklist -> Phase Loop (optional) -> Finish
```

## Global Requirements & Conventions

- Stay inside the repo root (`cd /Users/tylerburleigh/Documents/claude-sdd-toolkit`) and keep commands one-per-line (no `&&`).
- Use `sdd` commands for all spec JSON reading operations
- NEVER use `Read` to read spec JSON directly
- NEVER use `cat` to read spec JSON directly
- NEVER use `head` to read spec JSON directly
- NEVER use `tail` to read spec JSON directly
- NEVER use `grep` to read spec JSON directly
- NEVER use `jq` to read spec JSON directly
- NEVER use `grep` to read spec JSON directly
- Kick off each session with `sdd verify-tools` (once per terminal) if tooling status is unknown.
- Gate key decisions (spec choice, task selection, plan approval) with `AskUserQuestion`.
- Prefer `sdd find-specs`, `sdd list-specs --verbose`, and `sdd query-tasks` over manual filesystem inspection.

## Single Task Workflow

### 3.1 Choose the spec
- If the user supplies a spec id, confirm it exists via `sdd progress {spec-id}`; otherwise list candidates with `sdd find-specs --verbose`.
- After listing, apply a simple recommendation heuristic before asking: prefer specs with `status: active` that show non-zero progress (started but incomplete). If multiple qualify, pick the one with the highest completion percentage or with tasks `in_progress`. If none have progress, fall back to the most recently touched active spec (the first item in verbose output) and note that no clear frontrunner exists.
- Surface the recommended choice explicitly (e.g., tag it as `(Recommended)` in the `AskUserQuestion` options) and explain the reason ("already 1/66 tasks complete", "has in-progress work", etc.). If no recommendation is possible, state that clearly.
- Present options (include “Other / provide id”) and capture the selection via `AskUserQuestion`.
- Remember spec folders map to lifecycle (`specs/pending`, `specs/active`, etc.)—no need to `ls` them.

### 3.2 Gather high-level context
- Use `sdd progress {spec-id}` and `sdd list-phases {spec-id}` to summarize status.
- Highlight objectives, blockers, and completion percentages back to the user.
- Offer additional context commands (`sdd list-blockers`, `sdd render`) only on request.

### 3.3 Select the task
- Ask whether to accept the recommended task or browse alternatives.
- For the recommendation path: run `sdd prepare-task {spec-id}` and surface task id, file path, estimates, and blockers.
- For browsing: use `sdd query-tasks {spec-id}` (filter by `--parent`, `--status`) and, if needed, `sdd list-blockers {spec-id}`; present a concise shortlist for user choice.

### 3.4 Deep dive & plan approval
- Once the task is chosen, gather details with:
  - `sdd task-info {spec-id} {task-id}`
  - `sdd check-deps {spec-id} {task-id}`
  - `sdd get-task {spec-id} {task-id} --json` (only when full metadata is required)
- Draft the execution plan referencing spec intent and dependencies; present it and request explicit approval before implementation.
- If the recommended task is blocked, pause for guidance or loop back to task selection.

### 3.5 Implementation handoff
- Before coding, log progress via `sdd update-status {spec-id} {task-id} in_progress --note "context"`.
- After implementation, complete the task with `sdd complete-task {spec-id} {task-id} --journal-content "summary and verification results"` (add `--journal-title`/`--note` as needed).
- <ClaudeOnly>Run the context check: `sdd session-marker` then `sdd context --session-marker SESSION_MARKER_<hash>` and report the output <Note>IMPORTANT: Ignore this instruction if your name isn't Claude!</Note></ClaudeOnly>

### 3.6 Surface the next recommendation
- Immediately rerun `sdd prepare-task {spec-id}` to fetch the next recommended task, summarize its scope and blockers, and check with the user before proceeding.
- If the command reports no pending work or that the spec is complete, surface that outcome clearly and confirm next steps with the user instead of continuing silently.

## Post-Implementation Checklist

- Task status updated (`in_progress` → `completed`) with journal entry recorded.
- Any follow-up commands or monitoring notes captured in the completion journal.
- Outstanding blockers or deviations surfaced to the user; next steps agreed.
- Next recommended task retrieved via `sdd prepare-task {spec-id}` (or an explicit note that the queue is empty / spec complete) and shared with the user.
- Spec context refreshed via `sdd progress {spec-id}` for reporting.

## Phase Loop with Human Checkpoints

### Scope confirmation
- Show `sdd list-phases {spec-id}` with current progress and ask whether to focus on the target phase, adjust scope, or revert to single-task mode.

### Queue preparation
- Prime the backlog using `sdd query-tasks {spec-id} --parent {phase-id} --status pending`.
- If the queue is empty or blocked, surface issues via `sdd list-blockers {spec-id}` and pause for user direction.

### Task loop referencing previous steps
- Reuse the Single Task Workflow (steps 3.3–3.6) for each pending task in the phase. After completing a task, immediately follow Step 3.6 to gather the next recommendation (or confirm with the user if none remain) before continuing.
- After each completion, refresh the phase with `sdd check-complete {spec-id} --phase {phase-id}`.
- If the user grants “auto-continue for this phase,” note the permission once; still report blockers or unexpected findings immediately.

### Phase wrap-up & user check-in
- Summarize results using `sdd progress {spec-id}` plus `sdd query-tasks {spec-id} --parent {phase-id}` to show remaining work.
- Present accomplishments, verification outcomes, and blockers.
- Ask how to proceed: continue to next phase, perform a phase review of the implementation, or stop.
