# claude-sdd-toolkit - Architecture Documentation

**Date:** 2025-11-20
**Project Type:** Software Project
**Primary Language(s):** Python

## Technology Stack Details

### Core Technologies

- **Language:** Python

---

## Architecture Analysis Research Findings

### 1. Executive Summary

The `claude-sdd-toolkit` project, branded as `claude-skills`, is a Python-based software toolkit designed to streamline multi-language codebase documentation and implement Spec-Driven Development (SDD) workflows. Its architecture is predominantly a modular, plugin-like design, providing a unified Command-Line Interface (CLI) for user interaction. Key architectural characteristics include extensive code analysis powered by Tree-sitter, rich terminal user experience, and a strong emphasis on specification validation and AI-enhanced documentation generation.

### 2. Architecture Pattern Identification

The dominant architecture pattern identified in the `claude-sdd-toolkit` is a **Plugin Architecture** (or a highly modular monolithic application).

*   **Evidence from the codebase:**
    *   The `src/claude_skills/claude_skills/` directory contains numerous distinct subdirectories such as `code_doc`, `doc_query`, `llm_doc_gen`, `sdd_fidelity_review`, `sdd_next`, `sdd_plan`, `sdd_pr`, `sdd_render`, `sdd_spec_mod`, `sdd_update`, and `sdd_validate`. Each of these represents a specific "skill" or functional module.
    *   The `src/claude_skills/claude_skills/__init__.py` explicitly imports and exposes components from modules like `common` and `sdd_render`, serving as a central integration point.
    *   The `[project.scripts]` section in `pyproject.toml` defines a primary CLI entry point (`sdd = "claude_skills.cli.sdd:main"`) which is responsible for dispatching commands to the various underlying skill modules.
    *   The `skills/` directory in the root (`/home/tyler/Documents/GitHub/claude-sdd-toolkit/skills/`) contains `SKILL.md` files for each of these modules, further emphasizing their role as distinct, pluggable units.

*   **How the pattern is implemented:**
    The `claude_skills` Python package acts as a host for various "skills" (modules). Each skill module encapsulates its specific logic, potentially including its own CLI subcommands and data models. The `common/` module provides a foundational layer of shared utilities and infrastructure (e.g., configuration, UI components, schema loading, validation, and AI provider abstractions) that these skill plugins can leverage. The `cli/sdd` module functions as the central command dispatcher, routing user input to the appropriate skill's functionality.

*   **Benefits this pattern provides for this project:**
    *   **Modularity and Separation of Concerns:** Each skill can be developed, tested, and maintained with minimal interdependencies, reducing coupling.
    *   **Extensibility:** New features or "skills" can be added by creating new modules and integrating them into the existing CLI dispatch mechanism, fostering agile development.
    *   **Reusability:** Common functionalities are centralized in the `common` module, preventing code duplication and promoting consistency across different skills.
    *   **Scalability:** The modular design allows the project to grow in features without significantly increasing the complexity of the

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `development-guide.md` - Development workflow and setup

---

*Generated using LLM-based documentation workflow*