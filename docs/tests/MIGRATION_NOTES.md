Legacy Tests Migration Notes
============================

_Last updated: 2025-11-09_

## Phase 1 – Audit & Baseline Documentation

### Legacy Suite Inventory

#### Spec modification workflows (root `tests/`)

- `tests/test_add_node.py`
  - **Intent**: Validates `add_node` happy paths, error handling, and helper `_propagate_task_count_increase`.
  - **Fixtures/helpers**: Local `create_minimal_spec` factory; relies on base `pytest` assertions only.
  - **Coverage**: `claude_skills.sdd_spec_mod.modification.add_node`, `_propagate_task_count_increase`.

```42:58:tests/test_add_node.py
    def test_add_task_to_phase(self):
        """Test adding a basic task to a phase."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X"
        }
```

- `tests/test_move_node.py`
  - **Intent**: Exercises `move_node` permutations (cross-phase moves, ordering, validation failures).
  - **Fixtures/helpers**: Inline `create_minimal_spec`; reuses `add_node` for setup.
  - **Coverage**: `claude_skills.sdd_spec_mod.modification.move_node`, `add_node`.

- `tests/test_remove_node.py`
  - **Intent**: Covers `remove_node` leaf/cascade removal plus helpers `_collect_descendants`, `_cleanup_dependencies`, `_propagate_task_count_decrease`.
  - **Fixtures/helpers**: Inline `create_spec_with_tasks`.
  - **Coverage**: `claude_skills.sdd_spec_mod.modification` suite.

- `tests/test_update_node_field.py`
  - **Intent**: Ensures `update_node_field` handles schema enforcement, metadata merging, dependency validation, and status/type enumerations.
  - **Fixtures/helpers**: Inline `create_minimal_spec`.
  - **Coverage**: `claude_skills.sdd_spec_mod.modification.update_node_field`.

- `tests/test_transaction_support.py`
  - **Intent**: Validates transactional operations (`spec_transaction`, `transactional_modify`, `_validate_spec_integrity`) including rollback scenarios.
  - **Fixtures/helpers**: Inline `create_minimal_spec`.
  - **Coverage**: `claude_skills.sdd_spec_mod.modification` transaction utilities.

- `tests/test_json_output.py`
  - **Intent**: Exercises JSON emitters (`output_json`, `format_json_output`, `print_json_output`) for pretty/compact modes, edge cases, and CLI compatibility.
  - **Fixtures/helpers**: Uses `capsys` fixture and standard library IO; no custom helpers.
  - **Coverage**: `claude_skills.common.json_output`.

- `tests/test_sdd_fidelity_review.py`
  - **Intent**: Comprehensive coverage of `FidelityReviewer` and consultation helpers (artifact loading, caching, prompt generation, consensus, cache interoperability).
  - **Fixtures/helpers**: Heavy use of `unittest.mock`, `tmp_path`, and `pytest` built-ins; no shared helper modules.
  - **Coverage**: `claude_skills.sdd_fidelity_review.review`, `.consultation`, `claude_skills.common.ai_tools`.

```454:511:tests/test_sdd_fidelity_review.py
def test_consult_multiple_ai_success():
    """consult_multiple_ai_on_fidelity should consult multiple tools in parallel."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
            mock_detect.return_value = ["gemini", "codex"]
            mock_execute.return_value = [
                ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good"),
                ToolResponse(tool="codex", status=ToolStatus.SUCCESS, output="Passes review")
            ]

            responses = consult_multiple_ai_on_fidelity("Review this code...")

            assert len(responses) == 2
            assert all(r.success for r in responses)
```

#### Legacy integration suites (`tests/integration/`)

- `test_ai_tools_integration.py`
  - **Intent**: CLI-style invocation coverage for AI tools detection/execution with temporary mock binaries.
  - **Fixtures/helpers**: Local helper functions for fake executables; relies on `subprocess`, `tmp_path`.
  - **Coverage**: `claude_skills.common.ai_tools` command wiring.

- `test_comparison_views.py`
  - **Intent**: Validates rich TUI comparison layouts for fidelity/plan/status summaries.
  - **Fixtures/helpers**: Inline data structures; uses rich renderables indirectly.
  - **Coverage**: `claude_skills.sdd_fidelity_review.report`, `claude_skills.sdd_update.status_report`.

- `test_fidelity_review_integration.py`
  - **Intent**: End-to-end fidelity review with mocked git/spec interactions and consensus aggregation.
  - **Fixtures/helpers**: `tmp_path`, `subprocess` mocks, spec scaffolding inside module.
  - **Coverage**: `claude_skills.sdd_fidelity_review.review` + `.consultation`.

- `test_incremental_consensus.py`
  - **Intent**: Ensures incremental consensus logic merges cached and fresh results (verifies requirement verify-3-3).
  - **Coverage**: `claude_skills.common.ai_tools.ToolResponse`, `claude_skills.common.cache.CacheManager`.

- `test_json_output_integration.py`
  - **Intent**: CLI flag precedence for JSON formatting across commands.
  - **Coverage**: Command runners invoking `output_json`.

- `test_progress_feedback.py`
  - **Intent**: Exercises progress callbacks for AI consultations, pytest, and batch operations.
  - **Coverage**: `claude_skills.common.tui_progress`, `claude_skills.common.ai_tools`.

- `test_run_tests_ai_consultation_integration.py`
  - **Intent**: Integration of run-tests skill consultation pipeline with tool availability checks.
  - **Coverage**: `sdd test` CLI path, AI consultation flows.

- `test_sdd_config_integration.py`
  - **Intent**: Configuration discovery and overrides for CLI operations.
  - **Coverage**: `claude_skills.common.config` via CLI entry points.

- `test_sdd_plan_review_integration.py`
  - **Intent**: Exercises `sdd review` plan-review workflow with mocked tool output.
  - **Coverage**: CLI wrappers around plan-review skill.

- `test_streaming_cache.py`
  - **Intent**: Validates combined streaming progress and caching behaviours for incremental reviews.
  - **Coverage**: `claude_skills.common.cache.CacheManager` streaming integration.

```23:40:tests/integration/test_streaming_cache.py
def test_streaming_cache_combines_cached_and_fresh_results(tmp_path, capsys):
    """Streaming cache should merge cached blocks with fresh streaming output."""
    cache_dir = tmp_path / "cache"
    cache = CacheManager(cache_dir=cache_dir)

    # Simulate cached block
    cached_key = "cached_block"
    cache.set(cached_key, {"output": "Cached summary"})
```

#### Legacy unit subpackages (`tests/unit/`)

- `test_ai_tools.py`
  - **Intent**: Dataclass semantics, command building, execution orchestration for `ai_tools`.
  - **Fixtures/helpers**: `mocker` fixture (pytest-mock), `subprocess` patching.
  - **Coverage**: `claude_skills.common.ai_tools` core API.
- `test_cache.py`, `test_cache_manager.py`, `test_cache_key.py`, `test_cache_merge.py`, `test_cache_cli.py`
  - **Intent**: Comprehensive CacheManager CRUD, TTL, CLI commands, key generation, merge semantics.
  - **Fixtures/helpers**: Module-level `temp_cache_dir`, `cache_manager`; rely on filesystem interactions.
  - **Coverage**: `claude_skills.common.cache`, `.common.cache.cli`.
- `test_config.py`
  - **Intent**: Validates `claude_skills.common.config` accessors and defaults.
  - **Fixtures/helpers**: Uses `tmp_path` for config scaffolding.
- `test_fidelity_cli_incremental.py`
  - **Intent**: Ensures fidelity CLI incremental flag wires into `FidelityReviewer`.
  - **Coverage**: `claude_skills.sdd_fidelity_review.cli`.
- `test_issue_aggregation_panel.py`, `test_recommendation_consensus.py`
  - **Intent**: Rich text rendering for fidelity review issue summaries and consensus panels.
  - **Coverage**: `claude_skills.sdd_fidelity_review.report`.
- `test_pytest_parser.py`
  - **Intent**: Unit tests for pytest output parser utilities (progress tracking, formatting).
  - **Coverage**: `claude_skills.run_tests.pytest_parser`.
- `test_status_report_layout.py`
  - **Intent**: Validates status dashboard composition functions and helper tables.
  - **Coverage**: `claude_skills.sdd_update.status_report`, `claude_skills.common.ui_factory`.
- `test_tui_progress.py`
  - **Intent**: Verifies TUI progress callback protocols and trackers.
  - **Coverage**: `claude_skills.common.tui_progress`, `claude_skills.common.ai_tools`.
- `test_common/test_sdd_config.py`
  - **Intent**: Focused coverage for `claude_skills.common.sdd_config` loading/validation.
  - **Fixtures/helpers**: `tmp_path` for config files.
- `test_cache_manager.pyc`, `test_cache_merge.pyc`, etc.
  - **Note**: Stale `__pycache__` entries exist and should be removed alongside migration.

### Helper & Fixture Dependencies

- PyPI dependencies in use: `pytest`, `pytest-mock` (for `mocker`), `rich` rendering assertions.
- Shared filesystem fixtures: repeated inline `create_minimal_spec`, `create_spec_with_tasks`, cache directory factories; candidates for consolidation under `src/claude_skills/claude_skills/tests/fixtures/`.
- Built-in pytest fixtures leveraged: `tmp_path`, `capsys`, `monkeypatch`, `mocker`.
- No standalone helper modules under legacy `tests/`; all factories/fixtures are declared per file.

### Test Discovery Baseline

- `pytest.ini` restricts discovery to the package-scoped suite:

```1:24:pytest.ini
[pytest]
# Pytest configuration for claude-sdd-toolkit
...
testpaths = src/claude_skills/claude_skills/tests
```

- `src/claude_skills/pyproject.toml` mirrors the same `testpaths` for editable installs, ensuring legacy `tests/` are already excluded.
- CI/tooling search (`*.yml`, `*.toml`, `*.ini`, `*.sh`) surfaced only documentation-oriented patterns (`skills/doc-query/config.yaml` includes globbing for `tests/*.py` to provide context suggestions). No execution pipelines reference the legacy folder.
- Repository contains no `tox.ini`, GitHub workflow, or CI script references to the legacy `tests/` tree (verified via targeted search for `tests/` in `*.yml`, `*.toml`, and shell scripts). Legacy suites are currently dormant unless invoked manually.

### Outstanding Notes

- Migration will require porting inline spec factories into reusable fixtures to avoid duplication.
- Cached `.pyc` files under `tests/unit/__pycache__` and `tests/integration/__pycache__` should be deleted during final cleanup.
- Integration suites depend on CLI helper glue; new `src/claude_skills/claude_skills/tests/integration/cli_runner.py` (currently untracked) can centralise subprocess scaffolding when porting.

## Phase 2 – Integration Coverage Mapping

### Legacy → Package-Scoped Integration Suite

| Legacy test module | Migration decision | Package-scoped coverage |
| --- | --- | --- |
| `tests/integration/test_ai_tools_integration.py` | Superseded | `integration/test_ai_tools_cli.py` exercises mock binaries and CLI glue. |
| `tests/integration/test_run_tests_ai_consultation_integration.py` | Superseded | `integration/test_run_tests_consultation_cli.py` covers the test CLI routing matrix and consultation flows. |
| `tests/integration/test_sdd_config_integration.py` | Superseded | `integration/test_ui_config_integration.py` validates UI/config behaviour under the consolidated CLI. |
| `tests/integration/test_sdd_plan_review_integration.py` | Superseded | `integration/test_sdd_plan_review_cli.py` patches tool detection and artifact generation. |
| `tests/integration/test_json_output_integration.py` | Superseded | JSON toggles now live in `integration/test_sdd_update_cli.py` & `integration/test_sdd_validate_cli.py` (and related command suites). |
| `tests/integration/test_comparison_views.py` | Migrated (new) | Render assertions moved to `integration/test_fidelity_report_views.py`. |
| `tests/integration/test_fidelity_review_integration.py` | Migrated (new) | CLI orchestration covered by `integration/test_sdd_fidelity_review_cli.py`. |
| `tests/integration/test_incremental_consensus.py` | Migrated (new) | Incremental diff/caching flow lives in `integration/test_fidelity_incremental_workflow.py`. |
| `tests/integration/test_streaming_cache.py` | Migrated (new) | Streaming emitter + incremental cache interplay validated via `integration/test_sdd_fidelity_review_cli.py` (progress) and `integration/test_fidelity_incremental_workflow.py` (cache state). |
| `tests/integration/test_progress_feedback.py` | Migrated (new) | Progress signalling now asserted in `integration/test_sdd_fidelity_review_cli.py` (streaming toggle) and existing `integration/test_run_tests_consultation_cli.py` (run-tests prompts). |

Phase 2 introduces three new integration suites that align with the package-scoped helpers:

- `integration/test_sdd_fidelity_review_cli.py` – covers CLI help/no-AI modes, streaming progress toggles, and incremental wiring.
- `integration/test_fidelity_report_views.py` – snapshot-free checks for Rich comparison tables, consensus matrices, and JSON payloads.
- `integration/test_fidelity_incremental_workflow.py` – verifies `FidelityReviewer` incremental hash tracking across consecutive runs.

## Phase 3 – Unit Suite Migration

### Spec Modification Tests

- Ported legacy `tests/test_add_node.py`, `test_move_node.py`, `test_remove_node.py`, `test_update_node_field.py`, and `test_transaction_support.py` into `src/claude_skills/claude_skills/tests/unit/test_sdd_spec_mod/`.
- New package-scoped suite mirrors original scenarios (positioned inserts, cascade deletes, metadata merges, transactional rollbacks) while adopting the shared unit marker and existing fixture conventions.
- Legacy modules remain in place temporarily for diff review; removal scheduled once parity for remaining unit suites is confirmed.

### Common JSON Output

- Legacy `tests/test_json_output.py` coverage has been relocated to `tests/unit/test_common/test_json_output_legacy.py` to keep assertions on pretty vs. compact formatting, unicode preservation, and CLI compatibility close to the package-scoped helpers.
- Marker updated to `pytest.mark.unit`; duplicated assertions will be trimmed once the old `tests/` tree is removed.

### Cache Management

- Migrated `tests/unit/test_cache.py` into `tests/unit/test_common/test_cache_legacy.py`, preserving CRUD, TTL/cleanup, statistics, and key-generation scenarios against `claude_skills.common.cache`.
- Temporary `.legacy` suffix distinguishes the migrated suite from newer targeted tests; once legacy files are removed we can consolidate naming.
- Folded `tests/unit/test_cache_merge.py` scenarios into `test_cache_legacy.py`, covering `CacheManager.merge_results` and `compare_file_hashes` workflows for incremental runs.

### AI Tools

- Relocated `tests/unit/test_ai_tools.py` to `tests/unit/test_common/test_ai_tools_legacy.py`, adapting expectations to the current `ai_tools` API while retaining coverage for `ToolResponse`, `MultiToolResponse`, command assembly, availability checks, and parallel execution helpers.

### Configuration

- Migrated `tests/unit/test_config.py` to `tests/unit/test_common/test_config_legacy.py`, preserving file/env override behaviour and default-merging logic for `claude_skills.common.config`.

### Run Tests

- Relocated `tests/unit/test_pytest_parser.py` to `tests/unit/test_run_tests/test_pytest_parser_legacy.py`, retaining parser, summary formatting, and Rich progress display scenarios for `claude_skills.run_tests.pytest_parser`.
