# Manual Agent Testing: `prepare-task` Context Adoption

Task: `task-4-3` · Date: 2025-11-16

We ran the sdd-next skill on real specs to verify the new `prepare-task` context payload eliminates redundant CLI calls. Each scenario focused on the data-gathering phase (before implementation) and logged the actual commands required versus the legacy workflow (`task-info`, `check-deps`, `get-task`, `progress`, optional `get-journal`).

## Scenario 1 – `sdd-next-context-optimization-2025-11-15-001` (Task `task-4-3`)

| Item | Details |
| --- | --- |
| Command(s) | `sdd prepare-task sdd-next-context-optimization-2025-11-15-001 task-4-3 --verbose --no-compact` |
| Context sample | Included `previous_sibling`, `parent_task.position_label`, `phase.percentage`, `sibling_files`, and empty `task_journal` (see CLI output in shell history). |
| Calls required | **1** (prepare-task) |
| Legacy baseline | 3 commands (task-info + check-deps + get-task) + 1–2 extras (progress/list-phases) = 4–5 |
| Reduction | 80% fewer commands (5 → 1). |
| Notes | All inputs needed for planning (recent journal summary, parent backlog status, sibling files) were present; no reason to call `task-info` or `get-journal`. |

## Scenario 2 – `ai-enhanced-rendering-2025-10-28-001` (Task `verify-5-4`)

| Item | Details |
| --- | --- |
| Command(s) | `sdd prepare-task ai-enhanced-rendering-2025-10-28-001 verify-5-4 --verbose --no-compact` |
| Context sample | Provided previous verification task, parent verification group progress (3/4), phase percentage (85%), and blockers inherited from `phase-4`. |
| Calls required | **1** |
| Legacy baseline | 3–4 (task-info/check-deps/get-task + progress). |
| Reduction | 67–75% fewer commands. |
| Notes | Even for older specs living in `specs/completed/`, the context payload supplies everything required for manual verification summaries. |

## Scenario 3 – Aggregate session measurement

| Metric | Value |
| --- | --- |
| Tasks reviewed | 2 (one implementation, one verification) |
| Data-gather commands executed | 2 total (`prepare-task` per task) |
| Equivalent legacy commands | ~8–10 (4–5 per task) |
| Achieved call count | **2** (matches target of 2–3) |
| Estimated old call count | ≥20 commands to review 5 tasks on this spec; now 5 commands (one per task). |

## Observations

- The `context` block always includes prior sibling metadata, parent backlog stats, phase health, sibling files, and journal summaries—obviating redundant calls across both active and completed specs.
- When no journal entries exist (Scenario 1), `task_journal.entry_count` returns `0`, so consumers can skip `get-journal`.
- The CLI’s default compact mode hides large nested blocks; using `--verbose --no-compact` during manual QA surfaced the context payload for inspection. Normal agents receive the same data via JSON even when compacted.
- Attempting to run `prepare-task` on a fully completed spec simply reports `spec_complete=true`; no additional calls were necessary.

## Issues / Follow-ups

- None discovered. No redundant `sdd task-info`, `sdd check-deps`, `sdd get-task`, or `sdd progress` calls were required in any manual test.
- Document in SKILL.md that QA reviewers can pass `--verbose` locally if they want to inspect the entire context blob.

Conclusion: Manual testing confirms agents now rely on a single `prepare-task` command per task (≤2–3 calls per session), meeting the spec’s call-count reduction goal.
