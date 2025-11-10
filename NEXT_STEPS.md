## Remaining Migration Work

### Phase 3 – Legacy Unit Suites
- Relocate the remaining `tests/unit/` modules into the package-scoped hierarchy, keeping `pytest.mark.unit` in the migrated files and updating package `__init__` exports where needed:
  - `tests/unit/test_fidelity_cli_incremental.py` → `src/claude_skills/claude_skills/tests/unit/test_sdd_fidelity_review/`
    - Confirm the new home already has supporting fixtures for CLI handler calls.
    - Ensure the incremental flag assertions reuse the direct `_handle_fidelity_review` invocation pattern established for the existing CLI tests.
  - `tests/unit/test_issue_aggregation_panel.py` → `src/claude_skills/claude_skills/tests/unit/test_sdd_fidelity_review/`
    - Align Rich panel expectations with the latest renderer helpers.
  - `tests/unit/test_recommendation_consensus.py` → `src/claude_skills/claude_skills/tests/unit/test_sdd_fidelity_review/`
    - Verify any `FidelityRecommendation` import paths reflect current module locations.
  - `tests/unit/test_status_report_layout.py` → `src/claude_skills/claude_skills/tests/unit/test_sdd_update/`
    - Reconcile fixtures with the new status report rendering tests that already exist under `test_sdd_update`.
  - `tests/unit/test_cache_manager.py` (legacy root copy) → confirm the migrated coverage in `test_common/test_cache_manager.py` is fully equivalent, then delete or archive the root duplicate.
  - `tests/unit/test_common/test_sdd_config.py` → evaluate whether this legacy helper should move under `test_common` or a skill-specific subpackage for parity.

- After each migration:
  - Update the relevant `__init__.py` to surface the new module.
  - Extend `docs/tests/MIGRATION_NOTES.md` with a short entry describing the relocation and any behavioural adjustments.
  - Run targeted `pytest` selections for the new module plus the aggregated package (e.g., `pytest src/.../test_sdd_fidelity_review`).

### Phase 4 – Tooling & Documentation Sync
- Sweep documentation and configuration references for the legacy `tests/` path:
  - `README.md`, `INSTALLATION.md`, `docs/tests/` notes, and any developer playbooks should reference `src/claude_skills/claude_skills/tests`.
  - Confirm `pytest.ini` / `pyproject.toml` no longer mention the root suite; adjust comments if they still describe the migration as in-progress.
- Review shared fixtures used by the migrated suites:
  - Deduplicate helper functions now duplicated between legacy and new locations—fold them into existing `conftest.py` files where appropriate.
  - Ensure any new fixtures added during migration are documented in the skill-specific `README` or `MIGRATION_NOTES`.

### Phase 5 – Validation & Cleanup
- Execute a final pass of the full test matrix once all suites are migrated (`pytest`, targeted CLI smoke tests, any workflow scripts).
- Remove the deprecated `tests/` tree once parity is confirmed:
  - Delete orphaned files and update `.gitignore` / tooling scripts that might still look for the old structure.
- Update `CHANGELOG.md` with a summary of the test harness consolidation.
- Consider adding a short post-mortem entry in `docs/tests/MIGRATION_NOTES.md` that captures lessons learned and follow-up actions (e.g., automation for future migrations).
