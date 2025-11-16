---
name: sdd-next
description: Task preparation skill for spec-driven workflows. Reads specifications, identifies next actionable tasks, and creates detailed execution plans. Use when ready to implement a task from an existing spec - bridges the gap between planning and coding.
---

# SDD-Next: Concise Playbook

## Overview

- **Purpose:** Repeatable workflow for discovering specs, selecting actionable tasks, and keeping the user in the loop from planning through wrap-up.
- **Scope:** Single-task pulls and phase-focused loops; work happens inside project root.
- **Audience:** AI agents orchestrating SDD workflows who must respect human checkpoints and CLI guardrails.

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

---

## CRITICAL: Global Requirements & Conventions

### Working Directory & Commands
- Stay inside repo root and keep commands one-per-line (no `&&` chaining)
- Remember spec folders map to lifecycle (`specs/pending`, `specs/active`, `specs/completed`)

### ⚠️ CRITICAL: Spec Reading Rules (NEVER VIOLATE)

**ALWAYS use `sdd` commands to read spec JSON files:**
```bash
✅ sdd prepare-task {spec-id}
✅ sdd task-info {spec-id} {task-id}
✅ sdd progress {spec-id}
```

**NEVER use these tools/commands on spec JSON:**
```bash
❌ Read(/path/to/spec.json)          # Wastes 10,000+ tokens (specs are 50KB+)
❌ cat specs/active/spec.json        # Bypasses validation and hooks
❌ head specs/active/spec.json       # Wastes context
❌ jq '.tasks' spec.json             # Bypasses error handling
❌ grep "task-1" spec.json           # Inefficient, error-prone
```

**Why:** Spec files are large JSON (machine-readable, not human-readable). Direct reading wastes valuable context tokens and bypasses built-in validation, error handling, and hooks.

### User Interaction Requirements

### Context Gathering Best Practices

**Default workflow (stick to this unless spec says otherwise)**
1. Run `sdd prepare-task` with no flags. The returned `context` block already includes the previous sibling, parent metadata, phase progress, sibling files, and the latest journal summary.
2. Only call `sdd task-info`, `sdd get-task`, or `sdd progress` if the spec explicitly asks for extra metadata or you need files that are not exposed in `context`.
3. After completing the task, re-run `sdd prepare-task` to surface the next recommendation and refreshed context.

**When to use enhancement flags (`extended_context`)**
- `--include-full-journal`: You need the full journal history for the previous sibling (long-running refactors, nuanced design notes).
- `--include-phase-history`: You are preparing phase summaries or retrospectives and need every entry tied to the current phase.
- `--include-spec-overview`: You must report spec-wide progress without running `sdd progress`.
- Combine flags only when you plan to read the extra data—each flag increases the JSON payload.

**Decision guide**
- Need additional detail beyond `context`?
  - **Yes → Task metadata/files**: `sdd task-info {spec_id} {task_id}` (or `sdd get-task` if the spec mentions nested metadata).
  - **Yes → Journal history**: Use `--include-full-journal` (previous sibling) or `sdd get-journal` for arbitrary tasks.
  - **Yes → Phase backlog/alternatives**: `sdd query-tasks --parent {phase_id}` when presenting options to the user.
  - **No**: Stick with prepare-task output; avoid redundant commands.

**Anti-patterns to avoid**
- Running `task-info`, `check-deps`, and `get-task` back-to-back “just in case.” Call them only when `context` is insufficient.
- Re-running `sdd progress` or `sdd list-phases` after every plan change. Use `context.phase` for quick updates and run `sdd progress` only before reporting global status.
- Fetching the entire spec or invoking doc-query before inspecting the prepare-task payload.

#### Command Value Matrix

| Command | Returns | Use when | Redundant / Notes |
| --- | --- | --- | --- |
| `sdd prepare-task` | Recommended task plus `context` (previous sibling, parent, phase, sibling files, journal summary) | **Always** – first call for every task | N/A |
| `sdd task-info` | Raw task metadata straight from the spec | Spec explicitly references metadata not surfaced in `context` (acceptance criteria, detailed instructions) | Usually covered by `prepare-task`; only call when spec requires |
| `sdd get-task` | Full JSON node, including deep metadata blobs | Rare audits where you must inspect the spec data exactly as stored | Redundant with `task-info` for normal flows |
| `sdd progress` | Spec-wide counts, percentages, current phase | Preparing a status report or verifying completion prompts | `context.phase` already shows local progress; only run when reporting overall stats |
| `sdd list-phases` | Every phase with completion % | Re-prioritizing phases or presenting alternate scopes to the user | Typically unnecessary after `progress`; use only on request |
| `sdd get-journal` | Journal entries for any task | Need history beyond summaries (retro write-ups, deep audits) | `--include-full-journal` adds previous sibling history; `get-journal` is for arbitrary tasks |


**Gate key decisions with `AskUserQuestion` (MANDATORY):**
- Spec selection (when multiple available)
- Task selection (recommended vs alternatives)
- Plan approval (before implementation)
- Blocker handling (alternative tasks or resolve)
- Completion verification (for verify tasks)

**Anti-Pattern:** Never use text-based numbered lists like "1. Option A, 2. Option B". Always use `AskUserQuestion` tool for structured choices.

---

## ⚠️ CRITICAL: Context Checking Pattern

**Before checking context, you MUST generate a session marker first.**

This is a **two-step process** that must run **sequentially**:

### Step 1: Generate Session Marker (REQUIRED FIRST)
```bash
sdd session-marker
```

### Step 2: Check Context Using the Marker
```bash
sdd context --session-marker "SESSION_MARKER_<hash>"
```

**Output Format:**
```json
{"context_percentage_used": 78}
```

### CRITICAL REQUIREMENTS

✅ **Run as TWO SEPARATE Bash tool calls** (never combine)
✅ **Run SEQUENTIALLY, not in parallel** (step 2 depends on step 1 being logged)
❌ **NEVER combine with && or $()** - The marker must be logged to transcript first
❌ **NEVER run in parallel** - Step 2 will fail if step 1 hasn't been logged

### Context Thresholds

- **< 75%**: Safe to continue
- **≥ 75%**: Stop and recommend to the user that they `/clear` and then `/sdd-begin` for the next task

### CRITICAL: Never Anticipate Context Usage

⚠️ **ONLY check actual context percentage – NEVER speculate about future consumption:**

❌ DO NOT stop early because:
  - "Phase 2 implementation will consume context"
  - "File reading tasks are coming"
  - "I predict I'll hit 75% during the next phase"
  - "I should have buffer space for future work"

✅ DO ONLY stop when:
  - Context is CURRENTLY at or above 75%
  - You have JUST checked context and confirmed actual usage

**Rationale:** Predicting context usage is unreliable and defeats the purpose of checking. The threshold (75%) is designed to give adequate headroom; stopping earlier wastes that safety margin.

### When to Check Context

- **Autonomous mode**: After EVERY task completion (REQUIRED)
- **Single-task mode**: After task completion (recommended)
- **Session start**: Before intensive work (optional)

---

## Session Kickoff & Work Mode Selection

Before running `sdd-next`, follow the start-helper workflow documented in `commands/sdd-begin.md`:
1. Use `sdd skills-dev start-helper` commands (permissions → git → format-output) to surface active specs.
2. Present the user with the Work Mode `AskUserQuestion` immediately after they choose a spec or resume task.
   - **Options (exact text from sdd-begin.md):**
     1. Single Task Mode (Plan and execute one task at a time)
     2. Autonomous Mode (Complete all tasks in current phase within context limits)
3. If the user selects Autonomous Mode, run the two-step context check **before** calling `sdd-next`:
   ```bash
   sdd session-marker
   sdd context --session-marker "SESSION_MARKER_<hash>" --json
   ```
   - If `context_percentage_used > 75`, warn the user and use `AskUserQuestion` to confirm whether to stay in Autonomous Mode or switch to Single Task Mode.
4. Record the chosen mode. Single Task Mode uses Sections 3.1–3.6. Autonomous Mode uses the dedicated section later in this document. Do not switch modes mid-task unless the user explicitly requests it.

---

## Single Task Workflow

Use this workflow when the Work Mode selection is **Single Task Mode**. Stop after each task, gather confirmation, and re-run the Work Mode prompt if the user wants to continue.

### 3.1 Choose the Spec

- If user supplies spec id, confirm it exists via `sdd progress {spec-id}`
- Otherwise list candidates: `sdd find-specs`
- Apply recommendation heuristic:
  - Prefer `status: active` with non-zero progress (started but incomplete)
  - If multiple qualify, pick highest completion % or with `in_progress` tasks
  - If none have progress, pick most recently touched active spec
- Surface recommendation explicitly: tag as `(Recommended)` in `AskUserQuestion`
- Present options via `AskUserQuestion` (include "Other / provide id")

### 3.2 Gather High-Level Context

- Use `sdd progress {spec-id}` and `sdd list-phases {spec-id}` for status summary
- Highlight objectives, blockers, completion percentages
- Offer additional context commands (`sdd list-blockers`, `sdd render`) only on request

### 3.3 Select the Task

- Ask via `AskUserQuestion`: accept recommended task or browse alternatives?
- **Recommendation path**: `sdd prepare-task {spec-id}` → surface task id, file, estimates, blockers
- **Browsing path**: Use `sdd query-tasks {spec-id}` (filter `--parent`, `--status`) + `sdd list-blockers {spec-id}` → present shortlist via `AskUserQuestion`

### 3.4 Deep Dive & Plan Approval

Gather every detail with a single call (omit `{task-id}` to accept the recommended task):
```bash
sdd prepare-task {spec-id} {task-id}
```

That response already contains everything you need:
- `task_data` → title, metadata, instructions pulled from the spec
- `dependencies` → current blocking status plus any downstream tasks
- `context` → stitched data from the previous sibling, parent task, current phase, sibling files, and the latest journal summary

Treat `context` as the authoritative source rather than chaining `sdd task-info`, `sdd check-deps`, and `sdd get-task`. Typical fields:

```json
"context": {
  "previous_sibling": {
    "task_id": "task-3-1-2",
    "title": "Tighten plan creation language",
    "summary": "Updated scope guardrails for Section 3.3"
  },
  "parent_task": {
    "task_id": "task-3-1",
    "title": "Polish the planning workflow",
    "position_label": "Phase 3 · Task 1"
  },
  "phase": {
    "name": "Implementation",
    "percentage": 58,
    "blockers": []
  },
  "sibling_files": [
    {"path": "skills/sdd-next/SKILL.md", "reason": "Touched by previous sibling"}
  ]
}
```

- `context.previous_sibling`: reference recent work for continuity or reuse its journal summary when explaining why the new task matters (`context.previous_sibling.title`).
- `context.parent_task`: verify how this subtask fits into the backlog; use `context.parent_task.position_label` to show progress.
- `context.phase`: surface phase health (`context.phase.percentage`, `context.phase.blockers`) without calling `sdd progress`.
- `context.sibling_files`: prime file navigation by reviewing whatever the spec already touched before opening new files.

Only fall back to `sdd task-info` or `sdd check-deps` when the spec explicitly calls for metadata that is not surfaced through the standard payload.

Draft the execution plan around the spec intent, dependency gates, and the insights above. Example:
1. Confirm previous edits in `context.sibling_files` to maintain consistent tone.
2. Align deliverables with `context.parent_task.title`/`position_label`.
3. Call out open risks or blockers via `context.phase`.
4. Reference `context.previous_sibling.summary` if you need to explain how the work continues an earlier change.

**Present plan and get approval via `AskUserQuestion`:**
- Options: "Approve & Start", "Request Changes", "More Details", "Defer"
- Handle response appropriately

If recommended task is blocked, pause for guidance or loop back to task selection.

### 3.5 Implementation Handoff

**Before coding:**
```bash
sdd update-status {spec-id} {task-id} in_progress --note "context"
```

**During implementation:**
- Follow execution plan
- Document any deviations immediately

**After implementation:**

Mark task complete using sdd-update subagent (atomically marks complete + creates journal):
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Complete task {task-id} in spec {spec-id}. Completion note: [Summary of what was accomplished, tests run, verification performed].",
  description: "Mark task complete"
)
```

Journal content must include:
- What was accomplished
- Tests run and results
- Verification performed
- Files created/modified
- Any deviations from plan

### 3.6 Surface Next Recommendation

**Immediately after completion:**
```bash
sdd prepare-task {spec-id}
```

- Summarize next task's scope and blockers
- Check with user before proceeding
- If no pending work or spec complete, surface that clearly and confirm next steps

---

## ⚠️ CRITICAL: Completion Requirements

### When Marking Tasks Complete

**ONLY mark a task as completed when you have FULLY accomplished it.**

### Never Mark Complete If:

❌ Tests are failing
❌ Implementation is partial
❌ You encountered unresolved errors
❌ You couldn't find necessary files or dependencies
❌ Blockers exist that prevent verification

### If Blocked or Incomplete:

✅ Keep task as `in_progress`
✅ Create new task describing what needs resolution
✅ Document blocker using `sdd-update` subagent
✅ Present alternatives to user via `AskUserQuestion`

### Completion Journal Requirements

**MUST provide journal content** describing:
- What was accomplished
- Tests run and results
- Verification performed
- Any deviations from plan
- Files created/modified

**Example:**
```
Task(
  subagent_type: "sdd-toolkit:sdd-update-subagent",
  prompt: "Complete task task-2-3 in spec my-spec-001. Completion note: Implemented JWT auth middleware with PKCE flow. All 12 unit tests passing. Manual verification: login flow works in dev environment. Created src/middleware/auth.ts (180 lines) and tests/middleware/auth.spec.ts (45 tests).",
  description: "Mark task-2-3 complete"
)
```

### 3.7 Journal vs Git History

| Use the Spec Journal When… | Use Git History When… |
|----------------------------|------------------------|
| Closing **any** SDD task (journaling is mandatory and captures intent, verification, and follow-ups). | Investigating merge conflicts, bisects, or broader repo archaeology unrelated to a single spec task. |
| You need implementation details, test results, deviations, or next-task hints (`journal.entries[]` already hold this context in structured JSON). | You must inspect low-level commit metadata, e.g., to see who touched a file outside the spec workflow. |
| Preparing status updates: previous sibling journal summaries come bundled in `sdd prepare-task`. | You’re debugging historical code paths predating the current spec. |

**Anti-pattern:** Running `git log` / `git show` to understand a recently completed SDD task when the journal already documents the work. That wastes time and risks contradicting the canonical record. Start with the spec journal; escalate to git history only if a fact is missing or you are diagnosing repo-level issues (rebases, conflicts, regressions).

**Journal advantages**
- Full implementation narrative (what changed and why) tied to `task_id`.
- Test and verification results in one place, ready for audits.
- Deviations, blockers, and next-task hints captured while they are fresh.
- Structured JSON makes it trivial for `sdd prepare-task` to surface the latest context without extra commands.
- Archives context even if commits are squashed or rebased later.

---

## ⚠️ CRITICAL: Verification Tasks

### Detecting Verification Tasks

Check task metadata for `type: verify` or `verification_type` field:

```bash
sdd task-info {spec-id} {task-id}
```

### Dispatch by Verification Type

| verification_type | Action |
|-------------------|--------|
| `"auto"` | Invoke `sdd-toolkit:run-tests-subagent` |
| `"fidelity"` | Invoke `sdd-toolkit:sdd-fidelity-review-subagent` |
| `"manual"` | Present checklist to user for manual confirmation |

### Automated Tests (`verification_type: "auto"`)

```
Task(
  subagent_type: "sdd-toolkit:run-tests-subagent",
  prompt: "Run tests for {task-id} in spec {spec-id}. Execute tests and handle failures.",
  description: "Run tests"
)
```

After tests complete:
1. Present findings to user
2. Use `AskUserQuestion` to get approval before marking complete
3. Options: "Accept & Complete", "Fix Failures", "Review Details"

### Fidelity Review (`verification_type: "fidelity"`)

```
Task(
  subagent_type: "sdd-toolkit:sdd-fidelity-review-subagent",
  prompt: "Review {scope} '{target}' in spec {spec-id}. Compare completed tasks against requirements.",
  description: "Fidelity review for {scope}"
)
```

After review completes:
1. Present fidelity report
2. Use `AskUserQuestion` for decision:
   - "Accept & Complete" - Mark verification complete, journal deviations
   - "Revise Implementation" - Reopen parent tasks for fixes
   - "Update Spec" - Document accepted deviations

### Manual Review (`verification_type: "manual"`)

Present checklist from task metadata to user for confirmation via `AskUserQuestion`.

---

## Post-Implementation Checklist

After completing a task:

- [ ] Task status updated (`in_progress` → `completed`) with journal entry
- [ ] Follow-up commands or monitoring notes captured in journal
- [ ] Blockers or deviations surfaced to user; next steps agreed
- [ ] **Context check performed** (two-step pattern above)
- [ ] Next recommended task retrieved via `sdd prepare-task {spec-id}` and shared with user
- [ ] Spec context refreshed via `sdd progress {spec-id}` for reporting

---

## Autonomous Mode (Phase Completion)

Use this workflow only when the Work Mode selection is **Autonomous Mode** and the initial context check (from the Work Mode step) has confirmed there is enough headroom. If the user switches back to Single Task Mode, jump to Section 3.

### When to Use

- User explicitly requests "autonomous mode" during session setup
- Invocation mentions "autonomous mode" or "complete all tasks in current phase"
- User wants to complete multiple tasks without per-task approval

### Key Characteristics

- **Phase-scoped**: Completes all tasks within current phase only (does not cross phase boundaries)
- **Context-aware**: Checks context after EVERY task, stops if ≥75%
- **Defensive stops**: Stops for blocked tasks and plan deviations (requires user approval)
- **No plan approval**: Creates execution plans internally without showing user

### Autonomous Workflow Loop

#### Step 1: Task Execution Loop

For each task in current phase:

1. **Prepare next task:**
   ```bash
   sdd prepare-task {spec-id}
   ```

2. **Check phase complete:** If no more tasks in current phase → Exit loop

3. **Check for blockers:**
   - If next task blocked: **STOP**
   - Present blocker info via `AskUserQuestion`
   - Options: alternative tasks, resolve blocker, or stop
   - Exit autonomous mode

4. **Create execution plan (silently):**
   - Analyze task metadata from `prepare-task` output
   - Create detailed internal plan (no user approval needed)
   - Include all standard components: prerequisites, steps, success criteria

5. **Mark task in_progress:**
   ```bash
   sdd update-status {spec-id} {task-id} in_progress
   ```

6. **Execute implementation** according to internal plan

7. **Handle plan deviations:**
   - If implementation deviates: **STOP**
   - Document deviation
   - Present to user via `AskUserQuestion`
   - Options: revise plan, update spec, explain more, rollback
   - Exit autonomous mode

8. **Mark task complete:**
   ```
   Task(
     subagent_type: "sdd-toolkit:sdd-update-subagent",
     prompt: "Complete task {task-id} in spec {spec-id}. Completion note: [Brief summary of what was accomplished, tests run, verification performed].",
     description: "Mark task complete"
   )
   ```

9. **⚠️ CRITICAL: Check context usage (REQUIRED):**

   Run two-step pattern as SEPARATE, SEQUENTIAL Bash calls:
   ```bash
   # First call:
   sdd session-marker
   ```
   ```bash
   # Second call (only after first completes):
   sdd context --session-marker "SESSION_MARKER_<hash>"
   ```

   **Check ACTUAL context percentage reported, do NOT speculate:**
   - If context ACTUALLY ≥75% (as reported by command): **STOP**, exit loop, go to Summary
   - If context <75%: Continue to next iteration

   **CRITICAL:** Do not stop based on predictions like "upcoming work will use context" or "I should have buffer space for the next phase." Only stop when actual usage reaches the threshold. The 75% threshold already provides safety margin.

10. **Check phase completion:**
    - If current phase complete: Exit loop, go to Summary
    - Otherwise: Return to step 1

#### Step 2: Present Summary Report

When autonomous mode exits:

```markdown
## Autonomous Execution Summary

**Mode:** Phase Completion (Autonomous)
**Spec:** {spec-title} ({spec-id})
**Phase:** {phase-title} ({phase-id})

### Tasks Completed
✅ task-1-1: [title] - Duration: X min
✅ task-1-2: [title] - Duration: Y min

### Phase Progress
Phase {phase-id}: {completed}/{total} tasks ({percentage}%)
Overall: {total_completed}/{total_tasks} tasks ({overall_percentage}%)

### Context Usage
Current context: {context_percentage}%

### Exit Reason
{One of:}
- ✅ Phase Complete
- ⏸️ Context Limit: ≥75% threshold
- 🚧 Blocked Task
- ⚠️ Plan Deviation
- ❌ No Actionable Tasks

### Next Steps
{Contextual recommendations based on exit reason}
```

### Autonomous Mode Best Practices

**DO:**
- ✅ Check context after EVERY task completion
- ✅ Stop immediately when context ≥75%
- ✅ Base stopping decisions on ACTUAL context percentage, never predictions
- ✅ Use the full safety margin (continue until ≥75% reported)
- ✅ Stop for blocked tasks (don't auto-pivot)
- ✅ Stop for plan deviations (don't auto-revise)
- ✅ Create detailed internal plans
- ✅ Present comprehensive summary at end

**DON'T:**
- ❌ Cross phase boundaries
- ❌ Skip plan creation (always plan, just don't show)
- ❌ Continue past 75% context
- ❌ Stop early based on predictions of future context usage
- ❌ Auto-resolve blockers
- ❌ Auto-revise plans on deviations
- ❌ Batch task completions

---

## Phase Loop with Human Checkpoints

### Scope Confirmation

Show `sdd list-phases {spec-id}` with progress. Ask via `AskUserQuestion`:
- Focus on target phase
- Adjust scope
- Revert to single-task mode

### Queue Preparation

Prime backlog:
```bash
sdd query-tasks {spec-id} --parent {phase-id} --status pending
```

If queue empty or blocked:
```bash
sdd list-blockers {spec-id}
```
Pause for user direction.

### Task Loop

Reuse Single Task Workflow (steps 3.3–3.6) for each pending task.

After each completion:
- Refresh phase: `sdd check-complete {spec-id} --phase {phase-id}`
- If granted "auto-continue for this phase", note permission but still report blockers immediately

### Phase Wrap-Up

Summarize results:
```bash
sdd progress {spec-id}
sdd query-tasks {spec-id} --parent {phase-id}
```

Present accomplishments, verification outcomes, blockers.

Ask via `AskUserQuestion`: continue to next phase, perform phase review, or stop.

---

## Troubleshooting

### Spec File Not Found / Path Errors

**Cause:** Wrong working directory or relative paths

**Solution:**
- Provide absolute path: `sdd prepare-task {spec-id} --path /absolute/path/to/specs`
- Run `sdd find-specs` to discover available specs

### All Tasks Blocked

**Diagnosis:**
```bash
sdd list-blockers {spec-id}
sdd check-complete {spec-id}
```

**Solution:** Present alternatives via `AskUserQuestion` or resolve blockers before continuing

---

## Quick Reference

### Core Commands

```bash
# Discovery
sdd find-specs
sdd progress {spec-id}
sdd list-phases {spec-id}

# Task Selection
sdd prepare-task {spec-id}
sdd next-task {spec-id}
sdd task-info {spec-id} {task-id}
sdd check-deps {spec-id} {task-id}

# Context Checking (TWO STEPS)
sdd session-marker
sdd context --session-marker "SESSION_MARKER_<hash>"

# Advanced
sdd query-tasks {spec-id} --status pending --parent {phase-id}
sdd list-blockers {spec-id}
sdd check-complete {spec-id} --phase {phase-id}
```

### Critical Patterns Summary

| Pattern | Requirement |
|---------|-------------|
| **Spec reading** | Always use `sdd` commands, NEVER `Read()` or `cat` on JSON |
| **Context checking** | Two-step sequential (marker → context), never combined |
| **Task completion** | Never mark complete if tests failing/partial/errors |
| **Autonomous mode** | Check context after EVERY task, stop at ≥75% |
| **Verification** | Dispatch to appropriate subagent by `verification_type` |
| **User decisions** | Always use `AskUserQuestion`, never text lists |
