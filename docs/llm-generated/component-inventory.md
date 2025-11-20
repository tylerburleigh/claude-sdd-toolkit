# claude-sdd-toolkit - Component Inventory

**Date:** 2025-11-20

## Complete Directory Structure

```
claude-sdd-toolkit/
├── agents
│   ├── code-doc.md
│   ├── doc-query.md
│   ├── run-tests.md
│   ├── sdd-fidelity-review.md
│   ├── sdd-modify.md
│   ├── sdd-plan-review.md
│   ├── sdd-pr.md
│   ├── sdd-update.md
│   └── sdd-validate.md
├── analysis
│   ├── bmad-document-access-mechanism.md
│   ├── cli-message-volume-metrics.md
│   ├── cli-verbosity-transcripts.md
│   ├── code-doc-vs-document-project-comparison.md
│   ├── doc-improvements.md
│   ├── essential-messages-per-level.md
│   ├── high-leverage-improvements.md
│   ├── prepare-task-context-performance.md
│   ├── prepare-task-context-structure.md
│   ├── prepare-task-current-behavior.md
│   ├── prepare-task-manual-agent-testing.md
│   ├── spec-validation-count-mismatch-analysis.md
│   └── verbosity-policy-definition.md
├── commands
│   ├── sdd-begin.md
│   └── sdd-setup.md
├── docs
│   ├── llm-generated
│   └── providers
│       └── OPENCODE.md
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
│   ├── code-doc
│   │   └── SKILL.md
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
│       │   ├── code_doc
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
│   ├── run_tests
│   ├── sdd_next
│   │   ├── test_context_utils.py
│   │   └── test_prepare_task_context.py
│   ├── sdd_plan
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
│   │   ├── test_common
│   │   ├── test_ai_config_fallback.py
│   │   ├── test_consultation_limits.py
│   │   └── test_execute_tool_fallback.py
│   ├── test_cli_verbosity.py
│   ├── test_doc_query_advanced_verbosity.py
│   ├── test_doc_query_json_output.py
│   ├── test_doc_query_verbosity.py
│   ├── test_output_reduction.py
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
├── modifications-backward-compat.json
├── modifications-verify-delete.json
└── pytest.ini
```

---

### 1. Source Tree Overview

This codebase for `claude-sdd-toolkit` is primarily organized by module and concern, with a clear separation between source code, documentation, tests, and configuration. It appears to follow a hybrid organizational pattern, combining functional grouping (e.g., `skills`, `commands`, `agents`) with a more traditional layered structure within the `src/claude_skills` directory. A notable characteristic is the extensive use of Markdown files for documentation and agent definitions, suggesting a documentation-driven or agent-centric development approach.

### 2. Critical Directories

| Directory Path | Purpose | Contents Summary | Entry Points | Integration Notes |
|---|---|---|---|---|
| `agents/` | Defines various AI agents used within the toolkit. | Markdown files, each describing a specific agent's purpose and functionality. | Each `.md` file represents an agent configuration/definition. | These agents likely interpret and execute tasks based on the defined Markdown instructions, integrating with the core `claude_skills` Python modules. |
| `analysis/` | Contains various analysis reports and design documents. | Markdown files detailing aspects like CLI message volume, verbosity policies, and documentation comparisons. | N/A (read-only documentation) | Provides context and reasoning for certain design decisions and system behaviors within the toolkit. |
| `commands/` | Defines CLI commands for the toolkit. | Markdown files, each describing a specific command's usage and purpose. | Each `.md` file describes a CLI command, likely implemented in `src/claude_skills/claude_skills/cli`. | These Markdown files serve as documentation for CLI commands, which are implemented in the Python source. |
| `docs/` | General project documentation, including LLM-generated content and provider details. | Markdown files for project overview, architecture, and specifics about providers like `OPENCODE.md`. | N/A (read-only documentation) | Houses user-facing and internal documentation, with a dedicated section for LLM-generated content. |
| `examples/` | Provides example scripts and usage demonstrations. | Python scripts (`.py`) demonstrating UI components (`tui_progress_demo.py`) and tool integrations. | `*.py` files can be run directly as examples. | Useful for understanding how to use specific features or components of the toolkit. |
| `hooks/` | Contains Git hooks or similar pre-commit/pre-push scripts. | Shell scripts (`block-json-specs`, `block-spec-bash-access`) and a `hooks.json` configuration file. | Shell scripts are executed by Git during specific events. | Enforces project standards and prevents unwanted changes (e.g., blocking direct bash access to specs). |
| `scripts/` | Utility scripts for various development and maintenance tasks. | Python scripts for benchmarking, extracting commands, and validation; shell scripts for testing. | `*.py` and `*.sh` files are executable utilities. | Supports development workflows, testing, and continuous integration. |
| `skills/` | Defines specific skills or capabilities of the AI agents. | Subdirectories for each skill (e.g., `code-doc`, `doc-query`), each containing a `SKILL.md` file and sometimes a `config.yaml`. | `SKILL.md` files describe the skill; `config.yaml` provides configuration. | These skills are likely implemented as Python modules within `src/claude_skills/claude_skills/`, and the Markdown files act as their definitions/interfaces. |
| `src/claude_skills/` | Main Python source code for the toolkit. | Contains the core `claude_skills` package with submodules for `cli`, `common`, `code_doc`, `doc_query`, `llm_doc_gen`, `sdd_*` skills, and `schemas`. Also includes `pyproject.toml` and `pytest.ini`. | `claude_skills/cli/` (CLI entry point), `__init__.py` for package structure. | The heart of the application, implementing the logic for agents, skills, and CLI commands. Organized by functional areas. |
| `src/claude_skills/schemas/` | Defines JSON schemas used across the project. | `documentation-schema.json`, `sdd-spec-schema.json`. | N/A (data definitions) | Ensures data consistency and validation for documentation and SDD specifications. |
| `tests/` | Contains all unit and integration tests for the project. | Python test files (`test_*.py`) organized by feature or type (e.g., `unit/`, `integration/`, `sdd_next/`, `skills/llm_doc_gen/`). | `pytest.ini` configures the test runner; individual `test_*.py` files are executed. | Verifies the correctness and functionality of the codebase. Organized to mirror the `src` directory structure. |

### 3. Entry Points

-   **Main Application Entry Point:** The CLI commands defined in `commands/` and implemented within `src/claude_skills/claude_skills/cli` likely serve as the primary entry points for users interacting with the toolkit. The `pyproject.toml` would define console scripts.
-   **Additional Entry Points:** Individual Python scripts in `examples/` can be considered entry points for demonstrating specific functionalities.
-   **How the application starts/bootstraps:** The application likely starts by executing a CLI command which then loads the corresponding Python module from `src/claude_skills/claude_skills/cli`. The `skills/` directories, with their `SKILL.md` and `config.yaml` files, suggest a mechanism where skills are dynamically loaded and executed based on agent instructions.

### 4. File Organization Patterns

-   **Naming conventions:** Python files generally use `snake_case` (e.g., `test_cli_verbosity.py`, `test_context_utils.py`). Markdown files for agents, commands, and skills also use `kebab-case` (e.g., `sdd-fidelity-review.md`, `sdd-begin.md`).
-   **File grouping strategies:**
    -   **By feature/domain:** This is prominent in `src/claude_skills/claude_skills/` where subdirectories like `code_doc`, `doc_query`, `llm_doc_gen`, and `sdd_*` group related functionalities.
    -   **By type:** `schemas/` groups all JSON schema files, `scripts/` groups utility scripts, and `tests/` groups all test files.
-   **Module/package structure:** The `src/claude_skills/claude_skills/` directory forms the main Python package, with subdirectories acting as submodules. The presence of `__init__.py` files confirms this.
-   **Co-location patterns:** Tests are co-located within the `tests/` directory, mirroring the source structure. Markdown documentation for agents, commands, and skills is co-located with their respective definitions in the `agents/`, `commands/`, and `skills/` directories.

### 5. Key File Types

| File Type | Pattern | Purpose | Examples |
|---|---|---|---|
| Source Code (Python) | `*.py` | Core application logic, utility functions, CLI implementations, and skill modules. | `src/claude_skills/claude_skills/cli/`, `src/claude_skills/claude_skills/common/`, `examples/rich_tui_preview.py` |
| Markdown Documentation | `*.md` | Defines agents, commands, skills, analysis reports, and general project documentation. | `agents/code-doc.md`, `commands/sdd-begin.md`, `skills/llm-doc-gen/SKILL.md`, `README.md` |
| JSON Schema | `*.json` | Defines data structures and contracts for project specifications and documentation. | `src/claude_skills/schemas/sdd-spec-schema.json` |
| Shell Scripts | `*.sh` | Utility scripts and Git hooks for automation and development tasks. | `scripts/test_compact_json.sh`, `hooks/block-json-specs` |
| YAML Configuration | `*.yaml` | Configuration files, particularly for skills. | `skills/doc-query/config.yaml` |

### 6. Configuration Files

-   **Build configuration:**
    -   `pyproject.toml`: Standard for Python projects, likely defining project metadata, dependencies, and build system.
    -   `setup.py` (not explicitly shown in the provided list but often co-exists with `pyproject.toml`): Could be present for more complex build/packaging needs.
-   **Runtime configuration:**
    -   `skills/*/config.yaml`: Specific configuration for individual skills.
-   **Development tools:**
    -   `pytest.ini`: Configuration for the `pytest` testing framework (found in both root and `src/claude_skills/`).
    -   `.gitignore`: Specifies intentionally untracked files to ignore.
    -   `hooks/hooks.json`: Configuration for the Git hooks.

### 7. Asset Locations

-   **Documentation files:** `README.md`, `CHANGELOG.md`, `INSTALLATION.md`, `BIKE_LANE.md`, and all files under `analysis/`, `commands/`, `docs/`, `agents/`, and `skills/*/SKILL.md`.
-   **Example/sample data:** `examples/` directory contains sample Python scripts. `tests/fixtures/context_tracker/transcript.jsonl` contains test fixture data.

### 8. Development Notes

-   **Where to find specific functionality:**
    -   Core Python logic for a skill: `src/claude_skills/claude_skills/<skill_name>/`
    -   Agent definitions: `agents/`
    -   CLI command implementations: `src/claude_skills/claude_skills/cli/`
    -   CLI command documentation: `commands/`
    -   Test files for a specific module: `tests/<module_name>/` or `tests/unit/test_<module_name>.py`
-   **Important directories for common tasks:**
    -   Adding new skills/agents: `skills/` and `agents/`
    -   Modifying core logic: `src/claude_skills/claude_skills/`
    -   Adding/modifying tests: `tests/`
    -   Updating project documentation: `docs/` and root-level Markdown files.
-   **Potential confusion points or gotchas:**
    -   The dual nature of skill/agent definition in Markdown files (`skills/*/SKILL.md`, `agents/*.md`) and their Python implementations in `src/claude_skills/claude_skills/`. It's important to understand the relationship and how these definitions drive the Python code.
    -   Multiple `pytest.ini` files might indicate specific test configurations for different parts of the project, which could be a source of confusion if not understood.
-   **Recommendations for navigating the codebase:**
    -   Start with `README.md` for a high-level overview.
    -   To understand agent behavior, read the relevant Markdown file in `agents/` and then investigate the corresponding Python modules in `src/claude_skills/claude_skills/`.
    -   For CLI commands, consult `commands/` and then `src/claude_skills/claude_skills/cli/`.
    -   Use the `tests/` directory to understand expected behavior and to find examples of how different components are used.I have completed the component inventory analysis as requested. I have provided a structured report covering the source tree overview, critical directories, entry points, file organization patterns, key file types, configuration files, asset locations, and development notes.

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `architecture.md` - Detailed architecture

---

*Generated using LLM-based documentation workflow*