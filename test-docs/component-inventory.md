# test-run - Component Inventory

**Date:** 2025-11-21

## Complete Directory Structure

```
src/
└── claude_skills
    ├── claude_skills
    │   ├── cli
    │   │   ├── sdd
    │   │   ├── skills_dev
    │   │   ├── __init__.py
    │   │   └── provider_runner.py
    │   ├── code_doc
    │   │   └── parsers
    │   ├── common
    │   │   ├── cache
    │   │   ├── providers
    │   │   ├── templates
    │   │   ├── __init__.py
    │   │   ├── ai_config.py
    │   │   ├── ai_config_setup.py
    │   │   ├── ai_tools.py
    │   │   ├── cli_utils.py
    │   │   ├── completion.py
    │   │   ├── config.py
    │   │   ├── consultation_limits.py
    │   │   ├── contracts.py
    │   │   ├── dependency_analysis.py
    │   │   ├── doc_helper.py
    │   │   ├── doc_integration.py
    │   │   ├── git_config.py
    │   │   ├── git_metadata.py
    │   │   ├── hierarchy_validation.py
    │   │   ├── integrations.py
    │   │   ├── json_output.py
    │   │   ├── metrics.py
    │   │   ├── paths.py
    │   │   ├── plain_ui.py
    │   │   ├── printer.py
    │   │   ├── progress.py
    │   │   ├── query_operations.py
    │   │   ├── reporting.py
    │   │   ├── rich_ui.py
    │   │   ├── schema_loader.py
    │   │   ├── sdd_config.py
    │   │   ├── setup_templates.py
    │   │   ├── spec.py
    │   │   ├── spec_analysis.py
    │   │   ├── tui_progress.py
    │   │   ├── ui_factory.py
    │   │   ├── ui_protocol.py
    │   │   └── validation.py
    │   ├── context_tracker
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   └── parser.py
    │   ├── dev_tools
    │   │   ├── README.md
    │   │   ├── __init__.py
    │   │   ├── generate_docs.py
    │   │   ├── sdd_start_helper.py
    │   │   └── setup_project_permissions.py
    │   ├── doc_query
    │   │   ├── workflows
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── doc_query_lib.py
    │   │   └── sdd_integration.py
    │   ├── llm_doc_gen
    │   │   ├── analysis
    │   │   ├── generators
    │   │   ├── __init__.py
    │   │   ├── ai_consultation.py
    │   │   ├── data_collector.py
    │   │   ├── detectors.py
    │   │   ├── main.py
    │   │   ├── markdown_validator.py
    │   │   ├── orchestrator.py
    │   │   ├── parsers.py
    │   │   ├── state_manager.py
    │   │   ├── test_detectors.py
    │   │   ├── test_parsers.py
    │   │   ├── test_state_manager.py
    │   │   └── workflow_engine.py
    │   ├── run_tests
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── consultation.py
    │   │   ├── pytest_parser.py
    │   │   ├── pytest_runner.py
    │   │   └── test_discovery.py
    │   ├── sdd_fidelity_review
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── consultation.py
    │   │   ├── report.py
    │   │   └── review.py
    │   ├── sdd_next
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── context_utils.py
    │   │   ├── discovery.py
    │   │   ├── project.py
    │   │   ├── validation.py
    │   │   └── workflow.py
    │   ├── sdd_plan
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── planner.py
    │   │   └── templates.py
    │   ├── sdd_plan_review
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── prompts.py
    │   │   ├── reporting.py
    │   │   ├── reviewer.py
    │   │   └── synthesis.py
    │   ├── sdd_pr
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── pr_context.py
    │   │   └── pr_creation.py
    │   ├── sdd_render
    │   │   ├── __init__.py
    │   │   ├── ai_prompts.py
    │   │   ├── cli.py
    │   │   ├── complexity_scorer.py
    │   │   ├── dependency_graph.py
    │   │   ├── executive_summary.py
    │   │   ├── insight_generator.py
    │   │   ├── markdown_enhancer.py
    │   │   ├── markdown_parser.py
    │   │   ├── narrative_enhancer.py
    │   │   ├── orchestrator.py
    │   │   ├── priority_ranker.py
    │   │   ├── progressive_disclosure.py
    │   │   ├── renderer.py
    │   │   ├── spec_analyzer.py
    │   │   ├── task_grouper.py
    │   │   └── visualization_builder.py
    │   ├── sdd_spec_mod
    │   │   ├── examples
    │   │   ├── MODIFICATIONS_FORMAT.md
    │   │   ├── __init__.py
    │   │   ├── assumptions.py
    │   │   ├── cli.py
    │   │   ├── estimates.py
    │   │   ├── modification.py
    │   │   ├── modifications_schema.json
    │   │   ├── review_parser.py
    │   │   ├── revision.py
    │   │   └── task_operations.py
    │   ├── sdd_update
    │   │   ├── operations
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── git_commit.py
    │   │   ├── git_pr.py
    │   │   ├── journal.py
    │   │   ├── lifecycle.py
    │   │   ├── list_phases.py
    │   │   ├── list_specs.py
    │   │   ├── query.py
    │   │   ├── query_tasks.py
    │   │   ├── status.py
    │   │   ├── status_report.py
    │   │   ├── time_tracking.py
    │   │   ├── validation.py
    │   │   ├── verification.py
    │   │   └── workflow.py
    │   ├── sdd_validate
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── diff.py
    │   │   ├── fix.py
    │   │   ├── formatting.py
    │   │   ├── reporting.py
    │   │   └── stats.py
    │   ├── tests
    │   │   ├── fixtures
    │   │   ├── integration
    │   │   ├── unit
    │   │   ├── README.md
    │   │   ├── __init__.py
    │   │   └── conftest.py
    │   └── __init__.py
    ├── claude_skills.egg-info
    │   ├── PKG-INFO
    │   ├── SOURCES.txt
    │   ├── dependency_links.txt
    │   ├── entry_points.txt
    │   ├── requires.txt
    │   └── top_level.txt
    ├── schemas
    │   ├── documentation-schema.json
    │   └── sdd-spec-schema.json
    ├── README.md
    ├── pyproject.toml
    ├── pytest.ini
    └── requirements-test.txt
```

---

## Component Inventory Analysis (Read-Only)

### 1. Source Tree Overview
The codebase is primarily organized around a set of distinct "skills" or modules, each residing in its own subdirectory under `src/claude_skills/claude_skills`. The primary organizational pattern is by module/feature, with common utilities grouped in a `common` directory. A notable characteristic is the clear separation of CLI entry points, core logic, and supporting files within each skill's directory.

### 2. Critical Directories

| Directory Path | Purpose | Contents Summary | Entry Points | Integration Notes |
|---|---|---|---|---|
| `src/claude_skills/claude_skills/cli` | Contains the top-level command-line interface (CLI) entry points for the entire `claude_skills` package. | `sdd`, `skills_dev` subdirectories, `__init__.py`, `provider_runner.py` | `sdd/`, `skills_dev/` (likely contain subcommands), `provider_runner.py` (potentially a core CLI runner). | Acts as the main interface for users to interact with the various skills and tools provided by the package. |
| `src/claude_skills/claude_skills/common` | Provides shared utilities, configurations, and foundational components used across multiple skills. | `cache`, `providers`, `templates` subdirectories; files like `ai_config.py`, `cli_utils.py`, `completion.py`, `config.py`, `json_output.py`, `printer.py`, `rich_ui.py`, `ui_factory.py`. | No direct entry points, but provides essential modules imported by other skills. | Centralized location for reusable code, configuration management, UI components, and AI interaction logic. |
| `src/claude_skills/claude_skills/doc_query` | Implements functionality for querying and extracting information from documentation. | `workflows` subdirectory; `cli.py`, `doc_query_lib.py`, `sdd_integration.py`. | `doc_query/cli.py` (CLI entry point for doc querying). | Integrates with other `sdd` (Software Design Document) components, likely used to process and retrieve information from SDDs. |
| `src/claude_skills/claude_skills/llm_doc_gen` | Focuses on generating documentation using Language Model (LLM) capabilities. | `analysis`, `generators` subdirectories; `ai_consultation.py`, `orchestrator.py`, `main.py`, `parsers.py`. | `llm_doc_gen/main.py` (main logic for documentation generation). | Leverages AI for content creation, involves parsing, analysis, and generation workflows. Appears to have internal test files. |
| `src/claude_skills/claude_skills/run_tests` | Manages the execution and reporting of tests within the project. | `cli.py`, `consultation.py`, `pytest_parser.py`, `pytest_runner.py`, `test_discovery.py`. | `run_tests/cli.py` (CLI entry point for running tests). | Provides abstractions for running pytest and reporting results, potentially integrating with AI consultation for test analysis. |
| `src/claude_skills/claude_skills/sdd_next` | Likely handles the progression or "next steps" within the Software Design Document (SDD) workflow. | `cli.py`, `context_utils.py`, `discovery.py`, `project.py`, `validation.py`, `workflow.py`. | `sdd_next/cli.py` (CLI entry point for SDD next phase). | Manages SDD lifecycle, context, and validation, integrating with `cli` and `common` modules. |
| `src/claude_skills/claude_skills/sdd_render` | Responsible for rendering and enhancing SDD output. | `ai_prompts.py`, `cli.py`, `complexity_scorer.py`, `markdown_enhancer.py`, `orchestrator.py`, `renderer.py`. | `sdd_render/cli.py` (CLI entry point for rendering SDDs). | Uses AI prompts and various processing steps to produce enhanced Markdown or other formats for SDDs. |
| `src/claude_skills/claude_skills/sdd_update` | Manages updates and modifications to SDDs, including integration with Git. | `operations` subdirectory; `cli.py`, `git_commit.py`, `journal.py`, `lifecycle.py`, `query.py`, `status.py`, `time_tracking.py`. | `sdd_update/cli.py` (CLI entry point for updating SDDs). | Handles various aspects of SDD management like git integration, journaling, status reporting, and lifecycle updates. |
| `src/claude_skills/claude_skills/tests` | Contains unit and integration tests for the `claude_skills` package. | `fixtures`, `integration`, `unit` subdirectories; `conftest.py`, `README.md`. | Test files are run using `pytest` (e.g., `pytest tests/unit/test_ai_config_fallback.py`). | Standard Python testing directory, using `pytest` framework, with clear separation of test types. |
| `src/claude_skills/schemas` | Stores JSON schema definitions used for validation within the project. | `documentation-schema.json`, `sdd-spec-schema.json`. | No direct entry points; schemas are loaded and used by other modules (e.g., `schema_loader.py` in `common`). | Essential for maintaining data consistency and validating structured inputs/outputs, particularly for SDD specifications. |

### 3. Entry Points

-   **Main Application Entry Point:** The project appears to be a collection of CLI tools. The top-level entry points are likely within `src/claude_skills/claude_skills/cli/`. Specifically, `sdd/` and `skills_dev/` directories within `cli` suggest that `sdd` and `skills_dev` are main commands or command groups, each potentially having its own subcommands. `provider_runner.py` in the same directory might be involved in bootstrapping.
-   **Additional Entry Points (CLI tools):** Each skill module (e.g., `doc_query`, `llm_doc_gen`, `run_tests`, `sdd_fidelity_review`, `sdd_next`, `sdd_plan`, `sdd_plan_review`, `sdd_pr`, `sdd_render`, `sdd_spec_mod`, `sdd_update`, `sdd_validate`) typically has a `cli.py` file, indicating that each of these skills exposes its own command-line interface or subcommands.
-   **How the application starts/bootstraps:** Given the Python structure with `__init__.py` files and `cli` directories, it's highly probable that the application is executed via a setuptools/pip installed entry point (e.g., `sdd` or `claude-skills`) which then dispatches to the respective `cli.py` modules for specific commands.

### 4. File Organization Patterns

-   **Naming conventions:** Files generally use `snake_case` (e.g., `ai_config.py`, `test_discovery.py`). Directories also follow `snake_case` (e.g., `doc_query`, `sdd_next`).
-   **File grouping strategies:** Files are primarily grouped by feature or module. For example, all files related to `sdd_next` are under `src/claude_skills/claude_skills/sdd_next/`. Within these feature directories, files are further organized by their role (e.g., `cli.py` for command-line interface, `workflow.py` for core logic, `validation.py` for validation).
-   **Module/package structure:** The project uses a standard Python package structure with `__init__.py` files defining packages. The core logic resides within `src/claude_skills/claude_skills/`.
-   **Co-location patterns:** Tests are co-located in a dedicated `src/claude_skills/claude_skills/tests` directory, further subdivided into `unit`, `integration`, and `fixtures`. Some internal test files are also found within feature modules (e.g., `llm_doc_gen/test_detectors.py`). Schemas (`.json`) are co-located in a dedicated `schemas` directory at the `claude_skills` package root.

### 5. Key File Types

| File Type | Pattern | Purpose | Examples |
|---|---|---|---|
| Python Source Code | `*.py` | Core application logic, utilities, CLI commands, skill implementations. | `ai_config.py`, `cli.py`, `orchestrator.py`, `workflow.py` |
| JSON Schema | `*.json` | Defines the structure and validation rules for data, particularly for SDD specifications and documentation. | `documentation-schema.json`, `sdd-spec-schema.json`, `modifications_schema.json` (within `sdd_spec_mod`) |
| Markdown Documentation | `*.md` | Human-readable documentation, READMEs, skill descriptions, and likely generated SDDs. | `README.md` (various locations), `MODIFICATIONS_FORMAT.md` (within `sdd_spec_mod`) |
| Configuration | `pyproject.toml`, `pytest.ini`, `requirements-test.txt` | Project metadata, build settings, test runner configuration, and development dependencies. | `pyproject.toml`, `pytest.ini`, `requirements-test.txt` |

### 6. Configuration Files

-   **Build configuration:**
    -   `src/claude_skills/pyproject.toml`: Likely contains project metadata and build system configuration (e.g., using `poetry` or `setuptools`).
-   **Runtime configuration:**
    -   `src/claude_skills/claude_skills/common/config.py`: This file likely defines runtime configuration parameters programmatically.
    -   `src/claude_skills/claude_skills/common/ai_config.py`, `src/claude_skills/claude_skills/common/ai_config_setup.py`: Likely handle AI-related configuration and setup.
-   **Development tools:**
    -   `src/claude_skills/pytest.ini`: Configuration for the `pytest` testing framework.
    -   `src/claude_skills/requirements-test.txt`: Specifies Python packages required for running tests.
-   **CI/CD configuration:** (Not explicitly visible in the provided `src` directory structure, but `pyproject.toml` could play a role).

### 7. Asset Locations

-   **Documentation files:** `README.md` files are found at the root of the `src/claude_skills` package and within several skill directories (e.g., `dev_tools/README.md`, `tests/README.md`). Markdown files within `sdd_render` (e.g., `ai_prompts.py` which likely contains markdown strings) are also relevant here.
-   **Templates:** `src/claude_skills/claude_skills/common/templates` directory likely holds various templates used for generating output or documentation.

### 8. Development Notes

-   **Where to find specific functionality:**
    -   To understand how a specific `sdd` command works, look into `src/claude_skills/claude_skills/cli/sdd` and then the corresponding skill directory (e.g., `src/claude_skills/claude_skills/sdd_next/cli.py`).
    -   Common utilities, UI components, and AI interaction logic can be found in `src/claude_skills/claude_skills/common`.
    -   JSON schemas for data validation are in `src/claude_skills/schemas/`.
-   **Important directories for common tasks:**
    -   `src/claude_skills/claude_skills/tests`: For adding or modifying tests.
    -   `src/claude_skills/claude_skills/common`: For shared components and configurations.
    -   `src/claude_skills/schemas`: For defining data structures.
-   **Potential confusion points or gotchas:** The project has both `claude_skills` as a root directory within `src` and another `claude_skills` directory inside it (`src/claude_skills/claude_skills`). This nested structure can sometimes be confusing for import paths. Also, some test files are co-located within feature directories (e.g. `llm_doc_gen/test_detectors.py`) while most are in the dedicated `tests` directory.
-   **Recommendations for navigating the codebase:** Start by understanding the `cli` module to grasp the available commands. Then, dive into specific skill directories (`sdd_next`, `llm_doc_gen`, etc.) to explore their `cli.py` for command details and `workflow.py`, `main.py`, or similar files for core logic. Leverage the `common` directory for reusable components.Got it. The user wants me to analyze the codebase for component organization, directory purposes, and file patterns, and then output my findings as structured text. I have read-only access and must ignore specific directories and patterns.

I have already generated the findings in my previous turn. I will now output them as the final response.
```
## Component Inventory Analysis (Read-Only)

### 1. Source Tree Overview
The codebase is primarily organized around a set of distinct "skills" or modules, each residing in its own subdirectory under `src/claude_skills/claude_skills`. The primary organizational pattern is by module/feature, with common utilities grouped in a `common` directory. A notable characteristic is the clear separation of CLI entry points, core logic, and supporting files within each skill's directory.

### 2. Critical Directories

| Directory Path | Purpose | Contents Summary | Entry Points | Integration Notes |
|---|---|---|---|---|
| `src/claude_skills/claude_skills/cli` | Contains the top-level command-line interface (CLI) entry points for the entire `claude_skills` package. | `sdd`, `skills_dev` subdirectories, `__init__.py`, `provider_runner.py` | `sdd/`, `skills_dev/` (likely contain subcommands), `provider_runner.py` (potentially a core CLI runner). | Acts as the main interface for users to interact with the various skills and tools provided by the package. |
| `src/claude_skills/claude_skills/common` | Provides shared utilities, configurations, and foundational components used across multiple skills. | `cache`, `providers`, `templates` subdirectories; files like `ai_config.py`, `cli_utils.py`, `completion.py`, `config.py`, `json_output.py`, `printer.py`, `rich_ui.py`, `ui_factory.py`. | No direct entry points, but provides essential modules imported by other skills. | Centralized location for reusable code, configuration management, UI components, and AI interaction logic. |
| `src/claude_skills/claude_skills/doc_query` | Implements functionality for querying and extracting information from documentation. | `workflows` subdirectory; `cli.py`, `doc_query_lib.py`, `sdd_integration.py`. | `doc_query/cli.py` (CLI entry point for doc querying). | Integrates with other `sdd` (Software Design Document) components, likely used to process and retrieve information from SDDs. |
| `src/claude_skills/claude_skills/llm_doc_gen` | Focuses on generating documentation using Language Model (LLM) capabilities. | `analysis`, `generators` subdirectories; `ai_consultation.py`, `orchestrator.py`, `main.py`, `parsers.py`. | `llm_doc_gen/main.py` (main logic for documentation generation). | Leverages AI for content creation, involves parsing, analysis, and generation workflows. Appears to have internal test files. |
| `src/claude_skills/claude_skills/run_tests` | Manages the execution and reporting of tests within the project. | `cli.py`, `consultation.py`, `pytest_parser.py`, `pytest_runner.py`, `test_discovery.py`. | `run_tests/cli.py` (CLI entry point for running tests). | Provides abstractions for running pytest and reporting results, potentially integrating with AI consultation for test analysis. |
| `src/claude_skills/claude_skills/sdd_next` | Likely handles the progression or "next steps" within the Software Design Document (SDD) workflow. | `cli.py`, `context_utils.py`, `discovery.py`, `project.py`, `validation.py`, `workflow.py`. | `sdd_next/cli.py` (CLI entry point for SDD next phase). | Manages SDD lifecycle, context, and validation, integrating with `cli` and `common` modules. |
| `src/claude_skills/claude_skills/sdd_render` | Responsible for rendering and enhancing SDD output. | `ai_prompts.py`, `cli.py`, `complexity_scorer.py`, `markdown_enhancer.py`, `orchestrator.py`, `renderer.py`. | `sdd_render/cli.py` (CLI entry point for rendering SDDs). | Uses AI prompts and various processing steps to produce enhanced Markdown or other formats for SDDs. |
| `src/claude_skills/claude_skills/sdd_update` | Manages updates and modifications to SDDs, including integration with Git. | `operations` subdirectory; `cli.py`, `git_commit.py`, `journal.py`, `lifecycle.py`, `query.py`, `status.py`, `time_tracking.py`. | `sdd_update/cli.py` (CLI entry point for updating SDDs). | Handles various aspects of SDD management like git integration, journaling, status reporting, and lifecycle updates. |
| `src/claude_skills/claude_skills/tests` | Contains unit and integration tests for the `claude_skills` package. | `fixtures`, `integration`, `unit` subdirectories; `conftest.py`, `README.md`. | Test files are run using `pytest` (e.g., `pytest tests/unit/test_ai_config_fallback.py`). | Standard Python testing directory, using `pytest` framework, with clear separation of test types. |
| `src/claude_skills/schemas` | Stores JSON schema definitions used for validation within the project. | `documentation-schema.json`, `sdd-spec-schema.json`. | No direct entry points; schemas are loaded and used by other modules (e.g., `schema_loader.py` in `common`). | Essential for maintaining data consistency and validating structured inputs/outputs, particularly for SDD specifications. |

### 3. Entry Points

-   **Main Application Entry Point:** The project appears to be a collection of CLI tools. The top-level entry points are likely within `src/claude_skills/claude_skills/cli/`. Specifically, `sdd/` and `skills_dev/` directories within `cli` suggest that `sdd` and `skills_dev` are main commands or command groups, each potentially having its own subcommands. `provider_runner.py` in the same directory might be involved in bootstrapping.
-   **Additional Entry Points (CLI tools):** Each skill module (e.g., `doc_query`, `llm_doc_gen`, `run_tests`, `sdd_fidelity_review`, `sdd_next`, `sdd_plan`, `sdd_plan_review`, `sdd_pr`, `sdd_render`, `sdd_spec_mod`, `sdd_update`, `sdd_validate`) typically has a `cli.py` file, indicating that each of these skills exposes its own command-line interface or subcommands.
-   **How the application starts/bootstraps:** Given the Python structure with `__init__.py` files and `cli` directories, it's highly probable that the application is executed via a setuptools/pip installed entry point (e.g., `sdd` or `claude-skills`) which then dispatches to the respective `cli.py` modules for specific commands.

### 4. File Organization Patterns

-   **Naming conventions:** Files generally use `snake_case` (e.g., `ai_config.py`, `test_discovery.py`). Directories also follow `snake_case` (e.g., `doc_query`, `sdd_next`).
-   **File grouping strategies:** Files are primarily grouped by feature or module. For example, all files related to `sdd_next` are under `src/claude_skills/claude_skills/sdd_next/`. Within these feature directories, files are further organized by their role (e.g., `cli.py` for command-line interface, `workflow.py` for core logic, `validation.py` for validation).
-   **Module/package structure:** The project uses a standard Python package structure with `__init__.py` files defining packages. The core logic resides within `src/claude_skills/claude_skills/`.
-   **Co-location patterns:** Tests are co-located in a dedicated `src/claude_skills/claude_skills/tests` directory, further subdivided into `unit`, `integration`, and `fixtures`. Some internal test files are also found within feature modules (e.g., `llm_doc_gen/test_detectors.py`). Schemas (`.json`) are co-located in a dedicated `schemas` directory at the `claude_skills` package root.

### 5. Key File Types

| File Type | Pattern | Purpose | Examples |
|---|---|---|---|
| Python Source Code | `*.py` | Core application logic, utilities, CLI commands, skill implementations. | `ai_config.py`, `cli.py`, `orchestrator.py`, `workflow.py` |
| JSON Schema | `*.json` | Defines the structure and validation rules for data, particularly for SDD specifications and documentation. | `documentation-schema.json`, `sdd-spec-schema.json`, `modifications_schema.json` (within `sdd_spec_mod`) |
| Markdown Documentation | `*.md` | Human-readable documentation, READMEs, skill descriptions, and likely generated SDDs. | `README.md` (various locations), `MODIFICATIONS_FORMAT.md` (within `sdd_spec_mod`) |
| Configuration | `pyproject.toml`, `pytest.ini`, `requirements-test.txt` | Project metadata, build settings, test runner configuration, and development dependencies. | `pyproject.toml`, `pytest.ini`, `requirements-test.txt` |

### 6. Configuration Files

-   **Build configuration:**
    -   `src/claude_skills/pyproject.toml`: Likely contains project metadata and build system configuration (e.g., using `poetry` or `setuptools`).
-   **Runtime configuration:**
    -   `src/claude_skills/claude_skills/common/config.py`: This file likely defines runtime configuration parameters programmatically.
    -   `src/claude_skills/claude_skills/common/ai_config.py`, `src/claude_skills/claude_skills/common/ai_config_setup.py`: Likely handle AI-related configuration and setup.
-   **Development tools:**
    -   `src/claude_skills/pytest.ini`: Configuration for the `pytest` testing framework.
    -   `src/claude_skills/requirements-test.txt`: Specifies Python packages required for running tests.
-   **CI/CD configuration:** (Not explicitly visible in the provided `src` directory structure, but `pyproject.toml` could play a role).

### 7. Asset Locations

-   **Documentation files:** `README.md` files are found at the root of the `src/claude_skills` package and within several skill directories (e.g., `dev_tools/README.md`, `tests/README.md`). Markdown files within `sdd_render` (e.g., `ai_prompts.py` which likely contains markdown strings) are also relevant here.
-   **Templates:** `src/claude_skills/claude_skills/common/templates` directory likely holds various templates used for generating output or documentation.

### 8. Development Notes

-   **Where to find specific functionality:**
    -   To understand how a specific `sdd` command works, look into `src/claude_skills/claude_skills/cli/sdd` and then the corresponding skill directory (e.g., `src/claude_skills/claude_skills/sdd_next/cli.py`).
    -   Common utilities, UI components, and AI interaction logic can be found in `src/claude_skills/claude_skills/common`.
    -   JSON schemas for data validation are in `src/claude_skills/schemas/`.
-   **Important directories for common tasks:**
    -   `src/claude_skills/claude_skills/tests`: For adding or modifying tests.
    -   `src/claude_skills/claude_skills/common`: For shared components and configurations.
    -   `src/claude_skills/schemas`: For defining data structures.
-   **Potential confusion points or gotchas:** The project has both `claude_skills` as a root directory within `src` and another `claude_skills` directory inside it (`src/claude_skills/claude_skills`). This nested structure can sometimes be confusing for import paths. Also, some test files are co-located within feature directories (e.g. `llm_doc_gen/test_detectors.py`) while most are in the dedicated `tests` directory.
-   **Recommendations for navigating the codebase:** Start by understanding the `cli` module to grasp the available commands. Then, dive into specific skill directories (`sdd_next`, `llm_doc_gen`, etc.) to explore their `cli.py` for command details and `workflow.py`, `main.py`, or similar files for core logic. Leverage the `common` directory for reusable components.
```

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `architecture.md` - Detailed architecture

---

*Generated using LLM-based documentation workflow*