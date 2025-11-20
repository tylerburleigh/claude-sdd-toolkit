# claude-sdd-toolkit - Architecture Documentation

**Date:** 2025-11-20
**Project Type:** Software Project
**Primary Language(s):** python, javascript

## Technology Stack Details

### Core Technologies

- **Languages:** python, javascript

---

## Architecture Analysis Research Findings for `claude-sdd-toolkit`

### 1. Executive Summary

The `claude-sdd-toolkit` is a Python-based Command Line Interface (CLI) and library designed for Spec-Driven Development (SDD), enabling AI-assisted software engineering. Its high-level architecture centers around machine-readable JSON specifications that define tasks, dependencies, and track progress, integrating seamlessly with various AI models. The primary architectural pattern is a **Monolith** that internally employs a **Plugin Architecture** (referred to as "Modular Skill-Based Design"), complemented by a **Layered Architecture** and a conceptual **Client-Server** model where Claude Code interacts with the toolkit. Key architectural characteristics include high modularity, extensibility through skills, a robust AI provider abstraction layer, declarative state management via JSON specifications, and a powerful, configurable CLI.

### 2. Architecture Pattern Identification

*   **Monolith (Internally Modular):**
    *   **Evidence:** The `docs/project-overview.md` explicitly states "Architecture: monolith" and "Repository Type: monolith." The `README.md` mentions "183 Python modules, 154 classes, and 915 functions organized into independent, composable skills," indicating a large, single codebase. The entire project resides within a single repository and is deployed as a single Python package.
    *   **Implementation:** Despite being a monolith, the project achieves significant modularity through its "Skill-Based Design" and extensive use of Python modules. All functionalities are bundled within the `src/claude_skills/claude_skills` package, but are logically separated.
    *   **Benefits:** This pattern simplifies development, testing, and deployment processes compared to distributed systems, while internal modularity maintains a clear separation of concerns, preventing "big ball of mud" issues.

*   **Plugin Architecture (Modular Skill-Based Design):**
    *   **Evidence:** The `README.md` details a "Modular Skill-Based Design" with independent Python modules for capabilities like `sdd-plan`, `sdd-next`, `doc-query`, `llm-doc-gen`, etc. The `skills/` directory at the project root and the `src/claude_skills/claude_skills/` package structure (containing sub-directories for each skill like `sdd_plan`, `doc_query`) confirm this design. Each skill has its own `SKILL.md` file, indicating distinct documentation and purpose.
    *   **Implementation:** Each skill module encapsulates specific business logic and CLI commands. A central dispatcher (likely within `src/claude_skills/claude_skills/cli/sdd.py`) dynamically loads and executes the relevant skill logic based on user input or AI orchestration. This design also extends to Claude Code's plugin system, where the toolkit itself functions as a plugin.
    *   **Benefits:** This pattern fosters independent development, testing, and easy extension of features. It promotes clear separation of concerns, allows new skills to be added without major core modifications, and enables flexible, composable workflows.

*   **Layered Architecture:**
    *   **Evidence:** The project's structure, particularly within `src/claude_skills/claude_skills/`, reveals distinct conceptual layers, although not strictly enforced by physical boundaries.
    *   **Implementation:**
        *   **Presentation Layer:** The `src/claude_skills/claude_skills/cli/` module handles user interaction via the unified `sdd` command. Output modes (`rich`, `plain`, `json`) are configured in `.claude/sdd_config.json` and handled by modules such as `common/ui_factory.py`, `common/rich_ui.py`, `common/plain_ui.py`, and `common/json_output.py`.
        *   **Application/Business Logic Layer:** The various skill modules (e.g., `sdd_plan`, `sdd_next`, `run_tests` located in `src/claude_skills/claude_skills/sdd_plan`, `sdd_next`, etc.) contain the core SDD workflows, task orchestration, and AI consultation logic. Subagents are also part of this layer.
        *   **Infrastructure/Utility Layer:** The `src/claude_skills/claude_skills/common/` module (`ai_config`, `ai_tools`, `cache`, `providers`, `spec`, `paths`, `context_tracker`, `templates`) provides foundational services, cross-cutting concerns (e.g., caching, configuration), and integration with external systems (AI models, file system, `tree-sitter`).
    *   **Benefits:** Ensures strong separation of concerns, making the system easier to understand, test, and maintain. Changes within one layer (e.g., a new AI provider) are isolated, minimizing impact on other layers.

*   **Client-Server (Conceptual):**
    *   **Evidence:** The `README.md` and `INSTALLATION.md` describe user interaction via "Claude Code" (an AI assistant client) or directly via the `sdd` CLI from a terminal. The "Integration" section of the `README.md` states "Claude skills orchestrate workflows → Python CLI executes operations → Results inform next steps."
    *   **Implementation:** Claude Code or the user's terminal acts as the client, sending commands to the `sdd` CLI. The CLI (acting as a server-like component) processes these commands, executes operations (e.g., reading/writing JSON specs, invoking AI models via providers, performing code analysis), and returns results back to the client.
    *   **Benefits:** Establishes a clear interaction boundary between the AI assistant/user and the toolkit's functionalities, supporting flexible integration and execution models (e.g., direct CLI use or AI orchestration).

### 3. Key Architectural Decisions

| Decision Category        | Choice Made

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `development-guide.md` - Development workflow and setup

---

*Generated using LLM-based documentation workflow*