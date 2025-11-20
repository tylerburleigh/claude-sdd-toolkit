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
│   └── codebase.json
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
├── THIRD_PARTY_NOTICES.md
├── modifications-backward-compat.json
├── modifications-verify-delete.json
├── pytest.ini
└── test_import_extraction.py
```

---

## Component Inventory Analysis

### 1. Source Tree Overview
The `claude-sdd-toolkit` project is a Python-based toolkit designed for AI agents, likely focusing on Software Design Document (SDD) generation and related management tasks. The codebase is organized with a clear separation of concerns, featuring a core Python package (`src/claude_skills`), declarative definitions for skills, agents, and commands using Markdown, and comprehensive testing infrastructure.

The primary organizational pattern is a **hybrid** approach, combining organization by module/domain within the main Python source with a top-level grouping of related component types (skills, agents, commands, tests). Notable characteristics include the extensive use of Markdown files (`.md`) for defining AI capabilities and CLI interactions, alongside a dedicated `schemas/` directory for JSON validation.

### 2. Critical Directories

| Directory Path | Purpose | Contents Summary | Entry Points | Integration Notes |
| --- | --- | --- | --- | --- |
| `src/claude_skills/claude_skills/` | Main Python source code for the toolkit's core functionalities, divided into sub-modules like `cli`, `common`, `context_tracker`, and various `sdd_` related components. | Python packages and modules implementing the core logic, utilities, and specific skill functionalities. | `__init__.py` for package definition; `cli/` for command-line interface implementation. | This is the heart of the application, where agents/skills logic is implemented. Other top-level directories (e.g., `skills/`, `agents/`) likely reference or configure components defined here. |
| `skills/` | Contains markdown-based definitions and configurations for various AI skills that the toolkit provides. | `SKILL.md` files describing each skill, and `config.yaml` for some skills (e.g., `doc-query`). Examples of skill definitions (e.g., `sdd-modify/examples`). | `SKILL.md` files serve as entry points for skill definitions and documentation. | These definitions are likely parsed by the core application to enable and configure agent capabilities. The markdown files describe the skill's functionality. |
| `agents/` | Stores markdown-based definitions for different AI agents. | `*.md` files, each describing a specific agent (e.g., `sdd-modify.md`, `doc-query.md`). | The `*.md` files themselves are the entry points, defining agent behavior. | These agent definitions likely orchestrate various `skills/` to perform complex tasks. |
| `commands/` | Defines command-line interface commands for the toolkit. | `*.md` files, each detailing a specific CLI command (e.g., `sdd-begin.md`, `sdd-setup.md`). | `*.md` files serve as documentation and definitions for CLI commands. | These markdown definitions are likely used to generate or configure the actual CLI commands implemented in `src/claude_skills/claude_skills/cli/`. |
| `tests/` | Contains all unit, integration, and skill-specific tests for the project. | Python test files (`test_*.py`) organized by type (unit, integration) and by feature/skill. Fixtures are also present. | Individual `test_*.py` files are executable via `pytest`. | Ensures the correctness and reliability of the `src/` code and the defined `skills/` and `agents/`. Directly corresponds to the project's functional components. |
| `docs/` | Project-level documentation and potentially generated codebase metadata. | Markdown files like `architecture.md`, `project-overview.md`. It also contains `codebase.json`, which might be a generated representation of the codebase. | `README.md` at the root, and specific `.md` files within this directory. | Provides high-level understanding and detailed explanations of the project components. |
| `src/claude_skills/schemas/` | Houses JSON schema definitions used throughout the project. | `documentation-schema.json`, `sdd-spec-schema.json`. | Not directly executable entry points, but critical for data validation. | These schemas are used to validate data structures, such as SDD specifications or documentation formats, ensuring consistency and correctness across different components. |

### 3. Entry Points

-   **Main application entry point:** The primary execution is likely through a command-line interface managed by the `src/claude_skills/claude_skills/cli/` module. The `pyproject.toml` in `src/claude_skills/` likely defines console scripts pointing to this CLI.
-   **Additional entry points:**
    *   **Skill Execution:** Skills defined in `skills/*.md` are probably invoked by agents or directly via the CLI.
    *   **Agent Execution:** Agents defined in `agents/*.md` are likely invoked through the CLI to orchestrate multiple skills.
    *   **Scripts:** Python scripts in `scripts/` serve as standalone utility or development tools.
-   **How the application starts/bootstraps:** The application likely leverages `setuptools` or `poetry` (indicated by `pyproject.toml`) to define console scripts. These scripts typically point to an entry function within `src/claude_skills/claude_skills/cli/`, which then parses command-line arguments and dispatches to the appropriate agent or skill logic.

### 4. File Organization Patterns

-   **Naming conventions:**
    *   Python modules and packages generally adhere to `snake_case` (e.g., `context_tracker`, `sdd_fidelity_review`).
    *   Markdown files for agents, skills, and commands often use `kebab-case` or `snake_case` in their filenames (e.g., `sdd-modify.md`, `doc-query.md`).
    *   JSON schema files use `kebab-case` (e.g., `documentation-schema.json`).
-   **File grouping strategies:**
    *   **By domain/feature:** Within `src/claude_skills/claude_skills/`, modules are grouped by their specific functionality (e.g., `doc_query`, `llm_doc_gen`).
    *   **By type:** Top-level directories group similar types of definitions (e.g., `agents/` for agent definitions, `skills/` for skill definitions).
-   **Module/package structure:** A standard Python package structure is used within `src/claude_skills/claude_skills/` with `__init__.py` files defining packages.
-   **Co-location patterns:**
    *   Some skill-specific examples (`skills/sdd-modify/examples/`) are co-located with their respective skill definitions.
    *   While many tests are centralized in the top-level `tests/` directory, there is some organization mirroring the source structure (e.g., `tests/sdd_next/`, `tests/skills/llm_doc_gen/`).

### 5. Key File Types

| File Type | Pattern | Purpose | Examples |
| --- | --- | --- | --- |
| Source Code (Python) | `*.py` | Implements the core logic, utilities, and functionality of the toolkit. | `src/claude_skills/claude_skills/common/__init__.py`, `src/claude_skills/claude_skills/cli/main.py` (inferred) |
| Source Code (Markdown) | `*.md` | Declarative definitions and documentation for agents, skills, and CLI commands. | `agents/sdd-modify.md`, `skills/doc-query/SKILL.md`, `commands/sdd-begin.md`, `README.md` |
| Tests (Python) | `test_*.py` | Unit, integration, and behavioral tests to ensure correctness and prevent regressions. | `tests/unit/test_ai_config_fallback.py`, `tests/sdd_next/test_context_utils.py`, `test_import_extraction.py` |
| Configuration (YAML) | `*.yaml` | Configuration for specific skills. | `skills/doc-query/config.yaml` |
| Configuration (JSON Schema) | `*.json` | Defines the structure and validation rules for data, such as SDD specifications or documentation. | `src/claude_skills/schemas/sdd-spec-schema.json`, `src/claude_skills/schemas/documentation-schema.json` |
| Configuration (Python) | `pytest.ini`, `pyproject.toml` | Project-wide configuration for testing, build, and dependency management. | `pytest.ini`, `src/claude_skills/pyproject.toml` |
| Shell Scripts | `*.sh` | Utility scripts for various development or CI/CD tasks. | `scripts/test_compact_json.sh` |

### 6. Configuration Files

-   **Build configuration:**
    *   `src/claude_skills/pyproject.toml`: Defines project metadata, dependencies, and specifies the build system.
    *   `src/claude_skills/requirements-test.txt`: Lists dependencies specifically for testing.
-   **Runtime configuration:**
    *   `skills/*/config.yaml`: Provides settings and parameters for individual skills.
    *   `hooks/hooks.json`: Likely configures project-specific Git hooks or similar automated actions.
-   **Development tools:**
    *   `pytest.ini` (at root and `src/claude_skills/`): Configures the `pytest` test runner, including discovery rules and plugins.

### 7. Asset Locations

-   **Documentation files:**
    *   Root-level documents: `README.md`, `CHANGELOG.md`, `INSTALLATION.md`, `BIKE_LANE.md`, `THIRD_PARTY_NOTICES.md`.
    *   Project documentation: Files within the `docs/` directory.
    *   Component documentation: `SKILL.md` files in `skills/`, and agent/command `.md` files in `agents/` and `commands/`.
-   **Example/sample data:**
    *   `examples/`: Contains various demonstration files for the toolkit's capabilities.
    *   `tests/fixtures/context_tracker/transcript.jsonl`: Sample data used for testing purposes.
    *   `skills/sdd-modify/examples/`: Specific examples illustrating the usage of the `sdd-modify` skill.

### 8. Development Notes

-   **Where to find specific functionality:**
    *   Core logic and foundational utilities are in `src/claude_skills/claude_skills/common/`.
    *   The implementation of CLI commands is located in `src/claude_skills/claude_skills/cli/`.
    *   Specific skill implementations are found within `src/claude_skills/claude_skills/<skill_name>/`.
    *   Declarative definitions for skills (what they do) are in `skills/<skill_name>/SKILL.md`.
    *   Agent definitions are in `agents/<agent_name>.md`.
-   **Important directories for common tasks:**
    *   To understand how agents operate and their capabilities, consult `agents/` and `skills/`.
    *   For modifications to the core application logic, refer to `src/claude_skills/claude_skills/`.
    *   To add new CLI commands, both `src/claude_skills/claude_skills/cli/` and `commands/` will be relevant.
    *   To run or review tests, navigate to the `tests/` directory and use the `pytest.ini` configuration.
-   **Potential confusion points or gotchas:**
    *   Distinguishing between a "skill" and an "agent" can be tricky; skills appear to be atomic capabilities, while agents orchestrate one or more skills to achieve a broader goal.
    *   The declarative nature of component definitions in Markdown (`.md` files) requires understanding how these map to and interact with the underlying Python implementations.
-   **Recommendations for navigating the codebase:**
    *   Begin by reviewing the root `README.md` for a high-level project overview.
    *   When investigating a specific feature, first examine its corresponding `.md` definition in `agents/`, `skills/`, or `commands/` to understand its intended behavior, then delve into the Python code in `src/claude_skills/claude_skills/` for implementation details.
    *   Utilize `pyproject.toml` and `pytest.ini` to understand project dependencies, build configurations, and test setup.

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `architecture.md` - Detailed architecture

---

*Generated using LLM-based documentation workflow*