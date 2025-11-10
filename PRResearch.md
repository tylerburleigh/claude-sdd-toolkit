# PR Research: feat13 vs origin/main

## 1. Change Inventory

| Area | Files (examples) | Change Type | Category | Summary |
| --- | --- | --- | --- | --- |
| Config & Tooling | `.model-chorusrc`, `.gitignore`, `hooks/block-json-specs`, `hooks/hooks.json`, `pytest.ini`, `scripts/test_compact_json.sh`, `scripts/benchmark_output_tokens.py` | add/update | tooling, workflow guardrails | Introduced ModelChorus defaults, hooked all `Read` operations to block raw JSON spec access, moved pytest discovery under `src/`, and added JSON compact-mode regression script plus richer benchmarking guidance. |
| Docs | `README.md`, `CHANGELOG.md`, `docs/OUTPUT_FORMAT_BENCHMARKS.md`, large deletions under `docs/*.md` | add/update/delete | documentation | Reworked config guidance for `default_mode/json_compact`, documented format benchmarks, and pruned legacy design docs and research artifacts (≈50k lines removed). |
| Specs & Schema | `src/claude_skills/schemas/sdd-spec-schema.json`, new `claude_skills/common/schema_loader.py`, renamed `schemas/documentation-schema.json` | add/update | shared utilities, configuration | Added cached schema loader with env overrides, expanded spec schema metadata/validation requirements, and moved documentation schema into packaged location. |
| CLI Core | `claude_skills/cli/sdd/__init__.py`, `cli/sdd/options.py`, `cli/sdd/registry.py` | update | feature implementation | Unified JSON/compact defaults via config, ensured optional modules load safely, and normalized CLI option behavior for new config shapes. |
| JSON Output & UI | `claude_skills/common/json_output.py`, `ui_factory.py`, `plain_ui.py`, `rich_ui.py`, `paths.py` | add/update | UX, infrastructure | Centralized JSON printing, respected new `default_mode`, ensured plain UI compatibility, tweaked Rich tables, and created `.fidelity-reviews` scaffolding. |
| AI Config & Tools | `claude_skills/common/ai_config.py`, `claude_skills/common/ai_tools.py` | update | infrastructure, security | Shifted skill configs to `.claude/ai_config.yaml`, added merge helpers, enforced safe defaults for tool invocation (json output, read-only sandbox), and added PATH override/env-based retries. |
| Validation Workflow | `sdd_validate/cli.py`, `sdd_validate/diff.py`, `common/validation.py` | update | feature, quality | Surfaced schema validation (optional jsonschema), routed JSON output via helper, respected schema messages in CLI, and made diff views backend-aware. |
| Update Workflow | `sdd_update/status_report.py`, `common/templates/fidelity_reviews_readme.md` | add/update | feature, UX | Refactored status dashboard to work with UI abstraction, added plain/Rich parity, and supplied fidelity directory template. |
| Test Suite | New under `src/claude_skills/claude_skills/tests/**`, removals under top-level `tests/**`, added integration/unit suites (e.g., `tests/unit/test_common/test_cache_cli.py`, `tests/integration/cli_runner.py`) | add/delete/update | tests | Migrated suite into package namespace, added CLI registry and cache tests, introduced CLI runner helpers, and removed duplicate legacy tests. |
| Skills Config | `skills/*` deletions (config.yaml), `skills/.../SKILL.md` updates | delete/update | configuration | Retired per-skill `config.yaml` in favor of centralized AI config, refreshed skill docs to match new workflows. |
| Specs Data | `specs/{active,completed,pending}` additions | add | feature narrative | New spec artifacts documenting output standardization and rich UI projects. |

## 2. Thematic Summary

- **Output & UX modernization**: CLI now honors `default_mode`/`json_compact`, enforces compact JSON toggles, and renders dashboards consistently across Rich/Plain UIs. Documentation and scripts quantify token savings.
- **Configuration consolidation**: Skills load AI settings from `.claude/ai_config.yaml`; spec validation uses packaged schemas with optional `jsonschema` dependency for Draft 07 compliance.
- **Security & workflow guardrails**: Tool invocations enforce read-only modes, and a new pre-tool hook blocks direct spec JSON reads in favor of structured SDD commands.
- **Validation fidelity**: Schema errors/warnings surface in `sdd validate`, diff views respect UI abstraction, and `.fidelity-reviews` scaffolding encourages structured outputs.
- **Test suite reorganization**: All tests now reside under `src/claude_skills/claude_skills/tests`, with new CLI runner helpers and additional coverage around optional module registration and cache behaviors.
- **Docs reset**: Large legacy documentation archives removed; README and benchmarking doc highlight updated workflows and configuration guidance.

## 3. Risks & Breaking Considerations

- **Schema tightening**: Specs missing newly required metadata will now fail validation. Legacy specs may require updates.
- **Hook enforcement**: Automation that reads `specs/*.json` directly now exits with failure; scripts must switch to CLI commands (`sdd next-task`, `sdd query-tasks`, etc.).
- **Config migrations**: Projects relying on `output.json`/`output.compact` need to confirm migration path; defaults favor `rich` mode with compact JSON, potentially changing agent expectations.
- **Tool path resolution**: The new `CLAUDE_SKILLS_TOOL_PATH` env override can mask PATH issues; CI should set it intentionally.
- **Optional dependency**: Schema validation requires `pip install ".[validation]"`; absence yields warnings instead of full enforcement.

## 4. Verification / Follow-Up

- `pytest src/claude_skills/claude_skills/tests -m "unit or integration"`
- `scripts/test_compact_json.sh` (optionally `--verbose`)
- Manual `sdd validate` runs on representative specs with and without `jsonschema` installed
- Confirm pre-tool hook messaging by attempting `Read` on `specs/*.json`
- Verify optional CLI modules (`sdd render`, `sdd fidelity-review`) still register when packages are present

## 5. PR Draft Outline

- **Overview**: Consolidate CLI output configuration, add schema-backed validation, migrate AI tooling configs, and reorganize documentation/tests.
- **Detailed Changes**:
  - Output & UI refactors (JSON helpers, status dashboard parity)
  - Config migrations (AI config loader, SDD config schema)
  - Workflow guardrails (spec read hook, tool command hardening)
  - Validation enhancements (schema loader, CLI messaging, diff UI)
  - Test suite relocation and new coverage
  - Documentation cleanup and benchmarking report
- **Testing**:
  - `pytest src/claude_skills/claude_skills/tests`
  - `scripts/test_compact_json.sh`
  - Manual `sdd validate` scenarios
- **Deployment/Config**:
  - Ensure `.claude/ai_config.yaml` is distributed with deployments
  - Optional `pip install ".[validation]"` to enable schema checks
- **References**:
  - Specs: `specs/active/plain-mode-support-2025-11-08-001.json`, `specs/completed/json-output-standardization-2025-11-08-001.json`, `specs/pending/cli-verbosity-reduction-2025-11-09-001.json`
  - CHANGELOG entry in `[Unreleased]`

## 6. Repository Status

- Working tree clean relative to tracked files (`git status` shows no pending changes beyond committed diff).

