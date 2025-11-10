## 2025-11-09 – Pytest Regression Run

- Command: `pytest`
- Environment: macOS 13.4 (Apple M2), Python 3.11.5 (conda)
- Duration: 82 s
- Result: **46 failed / 1 skipped / 1 393 passed** (1 440 total)

### Failure Buckets

- **List/query CLI JSON output**  
  `sdd list-specs` and `sdd query-tasks` no longer accept `--format json`; tests should switch to the global `--json` flag and parse stdout.

- **`sdd validate` messaging**  
  Exit codes match expectations, but warnings/errors now surface via stdout rather than stderr. Update assertions to combine both streams.

- **Run-test preset discovery**  
  `sdd test run --list` still exits `2` after reverting the parent parser injection; need a follow-up to restore global flag support without colliding with the `--debug` preset name.

- **Schema loader decode regression**  
  The loader now falls back to packaged schemas when an override file is corrupt. Adjust the new test to assert fallback success instead of expecting a `None` schema.

- **UI factory expectations**  
  `create_ui` returns `RichUi` in the harness because stdout is treated as a TTY. Tests should patch `isatty()` (or accept `RichUi` when colors are allowed).

Other integration suites (`doc` CLI, run-tests doc integration, spec modification workflows) run clean with the shared `cli_runner`.
