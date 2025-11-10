Completed today
- [x] Make tool discovery honour `CLAUDE_SKILLS_TOOL_PATH` so mock binaries win during tests.
- [x] Refresh `run-tests consult` dry-run output to show bullet plans, prompt length, and consistent error messaging.
- [x] Updated integration fixtures to set the new env var; targeted pytest checks now pass locally.

Next up
- Run the full pytest suite when convenient to ensure no regressions lurk outside the focused cases.
- Share the new CLI behaviour with docs or release notes if external consumers rely on the old messages.
