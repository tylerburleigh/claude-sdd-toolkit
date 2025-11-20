# claude-sdd-toolkit - Architecture Documentation

**Date:** 2025-11-20
**Project Type:** Software Project
**Primary Language(s):** python, javascript

## Technology Stack Details

### Core Technologies

- **Languages:** python, javascript

---

Here are the research findings from the architecture analysis of the `claude-sdd-toolkit` codebase:

### 1. Executive Summary

The `claude-sdd-toolkit` is a Python-based CLI and library designed for Spec-Driven Development (SDD), enabling AI-assisted software engineering. Its high-level architecture centers around machine-readable JSON specifications that define tasks, dependencies, and track progress, integrating seamlessly with various AI models. The primary architectural pattern is a **Plugin Architecture** (referred to as "Modular Skill-Based Design"), complemented by a **Layered Architecture** and a conceptual **Client-Server** model where Claude Code interacts with the toolkit. Key architectural characteristics include high modularity, extensibility through skills, a robust AI provider abstraction layer, declarative state management via JSON specifications, and a powerful CLI.

### 2. Architecture Pattern Identification

*   **Plugin Architecture (Modular Skill-Based Design):**
    *   **Evidence:** The `README.md` explicitly details a "Modular Skill-Based Design" with independent Python modules for each major capability (e.g., `sdd-plan`, `sdd-next`, `doc-query`, `llm-doc-gen`). The `src/claude_skills/claude_skills/` directory listing confirms individual directories for each skill (e.g., `sdd_plan`, `doc_query`, `llm_doc_gen`).
    *   **Implementation:** Each skill module encapsulates specific business logic. The `pyproject.toml` defines `sdd = "claude_skills.cli.sdd:main"` as a unified entry point, suggesting a central dispatcher that loads and executes the relevant skill logic based on user commands.
    *   **Benefits:** This pattern fosters independent development, testing, and deployment of features. It promotes clear separation of concerns, enhances extensibility by allowing new skills to be added without modifying the core system, and enables composable workflows.

*   **Layered Architecture:**
    *   **Evidence:** The organization, though not explicitly termed "layered," reveals distinct conceptual layers: CLI for interaction, skills for business logic, and common utilities/AI provider abstraction for infrastructure.
    *   **Implementation:**
        *   **Presentation Layer:** The `src/claude_skills/claude_skills/cli/` module, coupled with the overall `sdd` command structure, provides the user-facing interface. Output modes (`rich`, `plain`, `json`) further define this layer's capabilities.
        *   **Application/Business Logic Layer:** The various skill modules (e.g., `sdd_plan`, `sdd_next`, `run_tests`) contain the core logic for specific SDD workflows and task orchestration.
        *   **Infrastructure/Utility Layer:** The `src/claude_skills/claude_skills/common/` module, `context_tracker`, and the AI provider abstraction handle foundational services, cross-cutting concerns, and integration with external systems (AI models, file system for specifications).
    *   **Benefits:** This structure ensures a strong separation of concerns, making the system easier to understand, test, and maintain. Modifications within one layer (e.g., changing an AI provider) are isolated, minimizing impact on other parts of the system.

*   **Client-Server (Conceptual):**
    *   **Evidence:** The `README.md` and `INSTALLATION.md` describe user interaction primarily through "Claude Code" (an AI assistant acting as a client) or directly via the `sdd` CLI, which then invokes functionalities provided by the toolkit (acting as a service/server).
    *   **Implementation:** Claude Code or the user's shell sends commands to the `sdd` CLI. The toolkit processes these commands, executes operations (e.g., reading/writing JSON specs, consulting AI models), and returns structured (JSON) or formatted (Rich/plain text) output.
    *   **Benefits:** Establishes a clear interaction boundary between the AI assistant/user and the toolkit's functionalities, supporting flexible integration and execution models.

### 3. Key Architectural Decisions

| Decision Category            | Choice Made

---

## Related Documentation

For additional information, see:

- `index.md` - Master documentation index
- `project-overview.md` - Project overview and summary
- `development-guide.md` - Development workflow and setup

---

*Generated using LLM-based documentation workflow*