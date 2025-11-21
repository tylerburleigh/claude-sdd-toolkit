# test-run - Project Overview

**Date:** 2025-11-21
**Type:** Software Project
**Architecture:** monolith

## Project Classification

- **Repository Type:** monolith
- **Project Type:** Software Project
- **Primary Language(s):** python, javascript

## Technology Stack Summary

- **Languages:** python, javascript

---

### 1. Executive Summary

The 'claude-sdd-toolkit' is a Python library and command-line interface designed to bring structure and traceability to AI-assisted software development, specifically within an environment called "Claude Code." Its core purpose is to implement a **Spec-Driven Development (SDD)** workflow, where all development work is guided by machine-readable JSON specifications that define tasks, track progress, and manage dependencies. The toolkit is aimed at software developers who use AI assistants and want to avoid common pitfalls like scope creep, lost context, and unclear progress.

The project solves the problem of unstructured, ad-hoc interaction with development AIs by providing a systematic, plan-first methodology. Its most notable feature is this formal SDD process, which makes the entire development lifecycle transparent, version-controllable (since specs are just JSON files), and resumable. Its uniqueness also stems from a modular, "skill-based" architecture and a provider abstraction layer that allows it to consult multiple AI models (like Gemini, Cursor, and Claude) in parallel for tasks like code review, enhancing the quality of the output.

### 2. Key Features

1.  **Spec-Driven Development (SDD):** The entire development workflow is anchored by JSON specification files. These files outline project phases, tasks, and dependencies. This approach ensures that development is planned, atomic, and automatically tracked, making complex projects manageable.
2.  **Modular Skill-Based Architecture:** The toolkit's functionality is broken down into independent, composable "skills" (e.g., `sdd-plan`, `sdd-next`, `doc-query`). This design makes the system highly extensible and maintains a clear separation of concerns, allowing new capabilities to be added without modifying the core.
3.  **Multi-Model AI Consultation:** For quality assurance tasks like reviewing a plan or verifying an implementation, the toolkit can query multiple AI providers in parallel. This reduces model-specific bias and synthesizes a more robust consensus, which is critical for high-stakes development tasks.
4.  **AI-Powered Codebase Analysis:** Using `tree-sitter` for Abstract Syntax Tree (AST) parsing, the toolkit can generate comprehensive documentation and create a queryable JSON representation of the codebase. This allows users to ask complex questions about the code in natural language (e.g., "Show the call graph for this function").

### 3. Architecture Highlights

-   **High-Level Architecture Pattern:** The system is a **modular monolith**. While deployed as a single Python package, it is internally structured as a **plugin architecture** based on its "skills." It also exhibits a clean **layered architecture**:
    1.  **Presentation Layer:** The `sdd` CLI, which handles all user and AI-assistant interactions.
    2.  **Application Layer:** The individual skill modules that contain the core business logic for planning, coding, testing, etc.
    3.  **Infrastructure Layer:** A `common` module that provides shared services like AI provider management, spec file operations, caching, and UI rendering.
-   **Key Architectural Decisions:**
    -   **JSON Specs as State:** Using version-controllable JSON files as the "single source of truth" for development tasks is the foundational decision. This makes the process transparent, durable, and tool-able.
    -   **Provider Abstraction Layer:** Decoupling the core logic from specific AI models allows for flexibility and resilience. The system can switch between providers or use them in concert.
-   **Notable Design Patterns:** The codebase explicitly uses several design patterns, including the **Command Pattern** for CLI operations, the **Strategy Pattern** for selecting AI providers, and the **Repository Pattern** for managing spec files.

### 4. Development Overview

-   **Prerequisites:**
    -   Python 3.9+
    -   `pip` for package management
    -   "Claude Code" development environment
    -   Optional: Node.js >= 18.x (for the OpenCode AI provider)
-   **Key Setup/Installation Steps:**
    1.  Install the plugin from the marketplace within Claude Code.
    2.  Navigate to the plugin's source directory: `~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills`.
    3.  Install the Python package in editable mode: `pip install -e .`.
    4.  Run the unified dependency installer: `sdd skills-dev install`.
    5.  In a target project, run the one-time setup command: `/sdd-setup`.
-   **Primary Development Commands:**
    -   `pip install -e .`: Installs the `sdd` CLI tool.
    -   `sdd skills-dev install`: A unified command to install all required Python and optional Node.js dependencies.
    -   `pytest`: Tests are located in `src/claude_skills/claude_skills/tests` and run with pytest.
    -   The main user interaction is not through direct CLI use but via natural language and slash commands (`/sdd-begin`, `/sdd-setup`) within the Claude Code environment, which then orchestrates calls to the `sdd` CLI.

---

## Documentation Map

For detailed information, see:

- `index.md` - Master documentation index
- `architecture.md` - Detailed architecture
- `development-guide.md` - Development workflow

---

*Generated using LLM-based documentation workflow*