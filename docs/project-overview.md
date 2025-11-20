# claude-sdd-toolkit - Project Overview

**Date:** 2025-11-20
**Type:** Software Project
**Architecture:** monolith

## Project Classification

- **Repository Type:** monolith
- **Project Type:** Software Project
- **Primary Language(s):** python, javascript

## Technology Stack Summary

- **Languages:** python, javascript

---

## Project Overview Research Findings

### 1. Executive Summary

The `claude-sdd-toolkit` project is a Python-based library and CLI toolkit designed to facilitate Spec-Driven Development (SDD) within AI-assisted software engineering workflows, particularly for users of Claude Code. It addresses common challenges in AI development such as scope drift, context loss, and unquantifiable progress by introducing a structured, plan-first approach. The toolkit centers around machine-readable JSON specifications that meticulously define development tasks, track dependencies, and record progress.

Its core functionality aims to enhance the developer experience by providing atomic task breakdown, automated progress and time tracking, and robust multi-model AI consultation for quality assurance. The project stands out due to its integration with various AI providers, its sophisticated AST-based code analysis capabilities, and its ability to generate comprehensive AI-powered documentation. By enforcing a systematic approach, the toolkit ensures that AI-generated code aligns with predefined requirements and maintains a clear, version-controlled history of development.

### 2. Key Features

*   **Spec-Driven Development:** Employs machine-readable JSON specifications to outline tasks, manage dependencies, and monitor development progress. This enables a structured, plan-first workflow that minimizes ambiguity and ensures alignment with project goals.
*   **Multi-Model AI Consultation:** Integrates with leading AI providers (Gemini, Cursor Agent, Codex, Claude, OpenCode) through a unified abstraction layer. It supports parallel consultation for quality reviews (e.g., `sdd-plan-review`, `sdd-fidelity-review`), leveraging multiple perspectives to reduce bias and enhance the reliability of AI feedback.
*   **AI-Powered Documentation & Code Analysis:** Features capabilities for generating detailed project documentation (`llm-doc-gen`) and performing in-depth code analysis (`doc-query`). Users can query codebase statistics, search for patterns, identify complex functions, analyze dependencies, and visualize call graphs, all powered by AI insights.
*   **Automated Workflow Orchestration:** Provides core skills like `sdd-plan` for spec creation, `sdd-next` for guiding task execution based on dependencies, and `sdd-update` for tracking task status, journaling decisions, and managing spec lifecycle folders (`pending`, `active`, `completed`, `archived`). It includes automatic time tracking for tasks.
*   **Version Control Integration:** All JSON specification files are designed to be Git-trackable, offering a clear and auditable history of development tasks and architectural decisions. Optional Git integration (`.claude/git_config.json`) supports auto-branching, auto-committing, and auto-PR creation.

### 3. Architecture Highlights

The project exhibits a **modular skill-based design**, where each major capability is implemented as an independent and composable skill module (e.g., `sdd-plan`, `sdd-next`, `doc-query`, `llm-doc-gen`). This promotes clear separation of concerns, independent development, and extensibility.

A **Provider Abstraction Layer** is a key architectural decision, providing a unified interface (`ProviderContext`) for various AI tools (Gemini, Cursor Agent, Codex, Claude, OpenCode). This allows for flexible integration of different AI models and enables parallel consultation, enhancing both capability and resilience.

The **Primary State** of the project is managed through **JSON Specifications**, which are Git-trackable files organized into lifecycle folders (`pending/`, `active/`, `completed/`, `archived/`). This design pattern centralizes task definitions, progress tracking, and development history. The system also leverages Python's `Rich` library for a robust and enhanced terminal UI.

### 5. Development Overview

*   **Prerequisites:**
    *   Claude Code (latest version)
    *   Python 3.9+ and `pip`
    *   (Optional but recommended for full functionality): Git, Node.js >= 18.x (for OpenCode provider), `tree-sitter` libraries, and AI CLIs (e.g., `gemini`, `cursor-agent`, `codex`).

*   **Key Setup/Installation Steps:**
    1.  Launch Claude Code and install the `tylerburleigh/claude-sdd-toolkit` plugin from the marketplace via `/plugins`.
    2.  Exit Claude Code completely.
    3.  Navigate to the plugin's source directory: `cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills`.
    4.  Install Python and Node.js dependencies: `pip install -e .` followed by `sdd skills-dev install`.
    5.  Restart Claude Code.
    6.  In your project, run `/sdd-setup` to configure project permissions and default settings in `.claude/`.

*   **Primary Development Commands (CLI examples):**
    *   **Installation/Dependency Management:**
        *   `pip install -e .` (install Python package)
        *   `sdd skills-dev install` (unified installer for all dependencies)
        *   `sdd skills-dev verify-install` (check installation status)
    *   **Specification Management:**
        *   `sdd create <name>` (create a new spec)
        *   `sdd activate-spec <spec-id>` (move a spec from pending to active)
        *   `sdd next-task <spec-id>` (find the next actionable task)
        *   `sdd update-status <spec> <task>` (update task status)
        *   `sdd validate <spec.json>` (validate a spec against its schema)
        *   `sdd list-specs` (list specifications)
    *   **Documentation Generation & Query:**
        *   `sdd doc generate .` (generate basic documentation)
        *   `sdd doc analyze-with-ai .` (generate AI-enhanced documentation)
        *   `sdd doc search "pattern"` (search codebase documentation)
        *   `sdd doc call-graph "function"` (show call relationships)
    *   **Testing & Review:**
        *   `sdd test run tests/` (execute tests)
        *   `sdd plan-review <spec>` (get multi-model review of a spec plan)
        *   `sdd fidelity-review <spec>` (verify implementation against spec)

---

## Documentation Map

For detailed information, see:

- `index.md` - Master documentation index
- `architecture.md` - Detailed architecture
- `development-guide.md` - Development workflow

---

*Generated using LLM-based documentation workflow*