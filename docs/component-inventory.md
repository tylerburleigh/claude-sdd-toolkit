# claude-sdd-toolkit - Component Inventory

**Date:** 2025-11-20

## Complete Directory Structure

```
claude-sdd-toolkit/
├── agents
│   ├── doc-query.md
│   ├── run-tests.md
│   ├── sdd-fidelity-review.md
│   ├── sdd-modify.md
│   ├── sdd-plan-review.md
│   ├── sdd-pr.md
│   ├── sdd-update.md
│   └── sdd-validate.md
├── analysis
├── commands
│   ├── sdd-begin.md
│   └── sdd-setup.md
├── docs
│   ├── providers
│   │   └── OPENCODE.md
│   ├── architecture.md
│   ├── codebase.json
│   ├── component-inventory.md
│   ├── doc-generation-state.json
│   ├── index.md
│   └── project-overview.md
├── examples
│   ├── real_tool_integration_preview.md
│   ├── rich_tui_preview.py
│   └── tui_progress_demo.py
├── hooks
│   ├── block-json-specs
│   ├── block-spec-bash-access
│   └── hooks.json
├── scripts
│   ├── benchmark_output_tokens.py
│   ├── extract_sdd_commands.py
│   ├── measure_token_efficiency.py
│   ├── test_compact_json.sh
│   └── validate_sdd_commands.py
├── skills
│   ├── doc-query
│   │   ├── SKILL.md
│   │   └── config.yaml
│   ├── llm-doc-gen
│   │   └── SKILL.md
│   ├── run-tests
│   │   └── SKILL.md
│   ├── sdd-fidelity-review
│   │   └── SKILL.md
│   ├── sdd-modify
│   │   ├── examples
│   │   │   ├── apply-review.md
│   │   │   ├── bulk-modify.md
│   │   │   └── interactive.md
│   │   └── SKILL.md
│   ├── sdd-next
│   │   └── SKILL.md
│   ├── sdd-plan
│   │   └── SKILL.md
│   ├── sdd-plan-review
│   │   └── SKILL.md
│   ├── sdd-pr
│   │   └── SKILL.md
│   ├── sdd-render
│   │   └── SKILL.md
│   ├── sdd-update
│   │   └── SKILL.md
│   └── sdd-validate
│       └── SKILL.md
├── src
│   └── claude_skills
│       ├── claude_skills
│       │   ├── cli
│       │   ├── common
│       │   ├── context_tracker
│       │   ├── dev_tools
│       │   ├── doc_query
│       │   ├── llm_doc_gen
│       │   ├── run_tests
│       │   ├── sdd_fidelity_review
│       │   ├── sdd_next
│       │   ├── sdd_plan
│       │   ├── sdd_plan_review
│       │   ├── sdd_pr
│       │   ├── sdd_render
│       │   ├── sdd_spec_mod
│       │   ├── sdd_update
│       │   ├── sdd_validate
│       │   ├── tests
│       │   └── __init__.py
│       ├── claude_skills.egg-info
│       │   ├── PKG-INFO
│       │   ├── SOURCES.txt
│       │   ├── dependency_links.txt
│       │   ├── entry_points.txt
│       │   ├── requires.txt
│       │   └── top_level.txt
│       ├── schemas
│       │   ├── documentation-schema.json
│       │   └── sdd-spec-schema.json
│       ├── README.md
│       ├── pyproject.toml
│       ├── pytest.ini
│       └── requirements-test.txt
├── tests
│   ├── fixtures
│   │   └── context_tracker
│   │       └── transcript.jsonl
│   ├── integration
│   │   └── test_fallback_integration.py
│   ├── sdd_next
│   │   ├── test_context_utils.py
│   │   └── test_prepare_task_context.py
│   ├── skills
│   │   └── llm_doc_gen
│   │       ├── __init__.py
│   │       ├── test_ai_consultation.py
│   │       ├── test_architecture_generator.py
│   │       ├── test_component_generator.py
│   │       ├── test_e2e_generators.py
│   │       ├── test_e2e_orchestration.py
│   │       ├── test_overview_generator.py
│   │       └── test_workflow_engine.py
│   ├── unit
│   │   ├── test_ai_config_fallback.py
│   │   ├── test_consultation_limits.py
│   │   └── test_execute_tool_fallback.py
│   ├── verification
│   ├── test_cli_verbosity.py
│   ├── test_doc_query_advanced_verbosity.py
│   ├── test_doc_query_json_output.py
│   ├── test_doc_query_verbosity.py
│   ├── test_indexed_resolution.py
│   ├── test_output_reduction.py
│   ├── test_parallel_parsing.py
│   ├── test_sdd_fidelity_review_verbosity.py
│   ├── test_sdd_next_verbosity.py
│   ├── test_sdd_plan_review_verbosity.py
│   ├── test_sdd_plan_verbosity.py
│   ├── test_sdd_pr_verbosity.py
│   ├── test_sdd_render_verbosity.py
│   ├── test_sdd_spec_mod_verbosity.py
│   ├── test_sdd_update_tasks_verbosity.py
│   ├── test_sdd_update_verbosity.py
│   ├── test_sdd_validate_verbosity.py
│   ├── test_start_helper_contracts.py
│   ├── test_support_verbosity.py
│   ├── test_verbosity_output_reduction.py
│   └── test_verbosity_regression.py
├── BIKE_LANE.md
├── CHANGELOG.md
├── INSTALLATION.md
├── README.md
├── THIRD_PARTY_NOTICES.md
├── modifications-backward-compat.json
├── modifications-verify-delete.json
└── pytest.ini
```

---

### 1. Source Tree Overview

The `claude-sdd-toolkit` codebase is organized as a Python project, primarily structured around a set of "skills" and "agents" which appear to be core functional units. It uses a hybrid organizational pattern, with top-level directories separating different concerns (e.g., `src` for core code, `skills` for skill definitions, `agents` for agent definitions, `docs` for documentation, `tests

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `architecture.md` - Detailed architecture

---

*Generated using LLM-based documentation workflow*