## Verbosity Reduction Plan

### Context
- Research audits in `docs/research/sdd-plan`, `sdd-modify`, `sdd-plan-review`, `sdd-next`, `sdd-update`, `sdd-render`, `sdd-fidelity-review`, `sdd-validate`, and `sdd-pr` identify repeated YAGNI/KISS violations.
- Common offenders: process announcements (`printer.action/info` before work), structural headers, one-value-per-line metadata dumps, and tutorial-style “next steps”.
- Goal: Default CLI output should highlight outcomes and actionable data, with optional depth via `--verbose` or documentation.

### Guiding Principles
- **Outcomes over process:** remove “starting…” announcements; keep success/error summaries.
- **Compact grouping:** collapse related metadata into single lines or `printer.result` blocks; reserve bullet lists for genuinely separate items.
- **Targeted guidance:** default output shows at most one concise “what now” hint; move workflows/tutorials to docs or verbose mode.
- **Respect global flags:** propagate `--verbose`, `--quiet`, `--json` behavior consistently while shifting detailed context behind verbose.
- **Documentation parity:** update `SKILL.md` examples and tests so expectations match the leaner output.

### Cross-Cutting Tasks
1. Draft a reusable formatting helper (e.g., `format_summary_line`) for compact key/value output where beneficial.
2. Audit shared utilities (`PrettyPrinter`, CLI option parsing) to ensure verbose-only messages stay suppressed otherwise.
3. Update unit/integration tests that assert against prior verbose strings; prefer key substring or structured checks.
4. Refresh skill docs and README snippets that mirror CLI output.

### Module Workstreams

#### 1. `sdd_plan` (`src/claude_skills/claude_skills/sdd_plan/cli.py`)
- `cmd_create`: drop “Creating new specification”; merge metadata into one summary line; condense next steps to single hint; ensure path conveyed once.
- `cmd_analyze`: remove section headers; emit single success block (spec path + doc stats); gate doc-query tips behind `--verbose`.
- `cmd_template list`: replace per-field detail lines with one tabular row per template; keep final usage hint concise.
- Sync `skills/sdd-plan/SKILL.md` examples.

#### 2. `sdd_spec_mod` (`sdd_spec_mod/cli.py`)
- `cmd_apply_modifications`: eliminate “Applying…”/“From…”; compact dry-run preview; merge apply/save messages; move operation counts to verbose.
- `cmd_parse_review`: consolidate metadata + severity counts into one block; merge “Generated”/“Saved” output; remove numbered “Next steps” from default mode; ensure `--show` mode prints compact suggestion blocks.
- Update `skills/sdd-modify/SKILL.md`.

#### 3. `sdd_plan_review`
- `cmd_review`: emit brief overview (spec ID, tools) and single completion summary (time, responding tools, failures); remove redundant headers; only print consensus errors when present.
- `reviewer.py`: stop direct `print` usage; return progress data so CLI can decide what to surface (default minimal, verbose optional per-tool timings).
- `cmd_list_tools`: show availability + recommendation in ≤2 lines.
- Align `skills/sdd-plan-review/SKILL.md`.

#### 4. `sdd_next`
- Remove/gate pervasive `printer.action` messages (verify-tools, find-specs, next-task, task-info, check-deps, etc.).
- Use helper to output single-line task summaries with optional detail when verbose is set.
- Preserve `--json` pathways unchanged.
- Update `skills/sdd-next/SKILL.md`.

#### 5. `sdd_update`
- High-priority commands (`update-status`, `mark-blocked`, `add-journal`, `complete-task`) should emit single outcome blocks summarizing status change, journaling, auto-time, git commit, etc.
- Move workflow-side progress logs in `workflow.py` (e.g., “Tracking updates…”, “Creating git commit…”, “Saved updated spec”) behind verbose or aggregate into final summary.
- Extend cleanup to supporting commands flagged in research (bulk journaling, sync metadata, commit helpers).
- Refresh `skills/sdd-update/SKILL.md`.

#### 6. `sdd_render`
- Replace mode-specific action banners with a concise success summary once rendering completes; verbose mode can still describe pipeline stages.
- Downgrade “AI enhancement failed” warnings to verbose info when fallback succeeds; only raise warnings on degraded output.
- Ensure final block reports destination and key stats (optional verbose details).
- Update `skills/sdd-render/SKILL.md`.

#### 7. `sdd_fidelity_review`
- Swap stderr `print` progress lines for `printer.info` gated by `--verbose`; default mode shows only essential outcomes (report saved, tool failures).
- Consolidate file-save confirmation to a single line.
- Trim `list-review-tools` summary repetition; keep availability + guidance concise.
- Align `skills/sdd-fidelity-review/SKILL.md`.

#### 8. Other Modules
- `sdd_validate`: drop non-TTY “Validating…” message; fold spec path into result summary; keep hints terse.
- `sdd_pr`: remove spec-loading action logs; reformat draft-only context into single summary line; keep instructional text in docs.
- Re-scan remaining SDD CLIs for similar action/detail noise and apply the same pattern where found.

### Testing & Validation
- Run targeted smoke checks (`sdd create`, `sdd analyze`, `sdd apply-modifications`, `sdd parse-review`, `sdd review`, `sdd next-task`, `sdd complete-task`, `sdd render`, `sdd fidelity-review`) in default, `--verbose`, and `--json` modes.
- Execute `pytest` to catch assertion updates.
- Verify lint/format hooks pass.
- Compare final outputs against research “Proposed Minimal Output” examples; confirm line-count reductions align with 40–70% goals.

### Deliverables
- Refactored CLI modules with concise default output.
- Updated tests and documentation reflecting new messaging.
- Optional helper utilities for compact summaries.
- Change log entry summarizing verbosity improvements across SDD CLI.
