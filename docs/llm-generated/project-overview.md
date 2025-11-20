# claude-sdd-toolkit - Project Overview

**Date:** 2025-11-20
**Type:** Software Project
**Architecture:** monolith

## Project Classification

- **Repository Type:** monolith
- **Project Type:** Software Project
- **Primary Language(s):** Python

## Technology Stack Summary

- **Language:** Python

---

Here are the research findings for the `claude-sdd-toolkit` project:

## Research Findings

### 1. Executive Summary
The `claude-sdd-toolkit` is a Python library and CLI toolkit implementing Spec-Driven Development (SDD) for AI-assisted software engineering. Its core purpose is to bring systematic structure and trackability to projects utilizing large language models like Claude, Gemini, and others. It operates by defining development tasks and dependencies through machine-readable JSON specifications, thereby providing a clear roadmap for implementation and progress tracking.

This toolkit is primarily aimed at software developers and teams engaged in AI-assisted development who seek to overcome common challenges such as scope creep, context loss, and unorganized workflows. It addresses these problems by enforcing a plan-first methodology, breaking down features into atomic, verifiable tasks, and automating progress tracking. The toolkit's distinctive features include multi-model AI consultation for reviews, AST-based code analysis, AI-powered documentation, and deep integration with version control through its JSON spec files, making AI-driven development more reliable and efficient.

### 2. Key Features
*   **Spec-Driven Development (SDD):** Centralizes development around machine-readable JSON specifications that define tasks, dependencies, and verification steps. Supports a full lifecycle from planning (`sdd-plan`) to activation (`sdd-begin`) and completion.
*   **Multi-Model AI Consultation:** Leverages multiple AI providers (Gemini, Cursor Agent, Codex, Claude, OpenCode) for various tasks like spec reviews (`sdd-plan-review`), implementation verification (`sdd-fidelity-review`), and test debugging (`run-tests`), synthesizing findings to provide comprehensive insights.
*   **AI-Powered Documentation & Code Analysis:** Features skills like `code-doc` for generating codebase documentation (structural, architecture, AI context) based on AST analysis using `tree-sitter`, and `doc-query` for querying code relationships, complexity, dependencies, and call graphs.
*   **Automated Workflow & Context Management:** Orchestrates tasks, tracks progress with automatic time recording, monitors Claude Code context usage to prevent limits, and offers commands to resume work (`/sdd-begin`) and apply review feedback (`sdd-modify`).
*   **Flexible Output & Configuration:** Provides rich terminal-enhanced, plain text, and compact JSON output modes. Offers extensive configuration options for AI models, tool priority, verbosity, and work modes (single-task vs. autonomous phase completion).

### 3. Architecture Highlights
*   **Modular Skill-Based Design:** The project employs a highly modular architecture where each major capability is an independent, composable skill module (e.g., `sdd-plan`, `sdd-next`, `code-doc`). This design promotes clear separation of concerns, independent development, testability, and extensibility.
*   **Provider Abstraction Layer:** A unified interface (`ProviderContext`) abstracts different AI tools (Gemini, Claude, etc.), allowing the toolkit to consult multiple models in parallel or with fallback strategies. This enhances reliability and reduces bias.
*   **JSON Specification-centric Data Flow:** The primary state of the project is managed through JSON specifications, organized into lifecycle folders (`pending/`, `active/`, `completed/`, `archived/`). These files are Git-trackable, enabling version control and clear state transitions for development tasks.
*   **Subagent Architecture:** For multi-step or complex tasks, certain skills (e.g., `sdd-validate`, `run-tests`) launch specialized subagents, which are essentially dedicated Claude instances that execute specific workflows and report back to the main agent.
*   **Notable Design Patterns:** The codebase utilizes several design patterns, including Command Pattern for CLI operations, Factory Pattern for language parsers, Strategy Pattern for AI tool selection, Facade Pattern for documentation queries, Provider Pattern for AI tool abstraction, Repository Pattern for spec file operations, and Mediator Pattern for output formatting.

### 4. Development Overview
*   **Prerequisites:**
    *   Claude Code (latest version)
    *   Python 3.9+ and `pip`
    *   Optional: Node.js >= 18.x (for OpenCode provider), Git, `tree-sitter` libraries, various AI CLIs (`gemini`, `codex`, `cursor-agent`).
*   **Key Setup/Installation Steps:**
    1.  Launch Claude Code and install the `tylerburleigh/claude-sdd-toolkit` plugin from the marketplace.
    2.  Navigate to the plugin directory (`~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills`) in a terminal.
    3.  Install Python dependencies: `pip install -e .`
    4.  Run the unified installer for all dependencies (Python and Node.js): `sdd skills-dev install` (or manually install Node.js dependencies if needed).
    5.  Restart Claude Code.
    6.  Configure the project by running `/sdd-setup` within Claude Code, which creates essential configuration files (`.claude/settings.local.json`, `sdd_config.json`, `ai_config.yaml`).
*   **Primary Development Commands:**
    *   **Installation/Setup:**
        *   `pip install -e .` (within `src/claude_skills` directory)
        *   `sdd skills-dev install` (unified installer)
        *   `/sdd-setup` (in Claude Code)
    *   **Testing:** `pytest` is used for testing. The `pytest.ini` indicates that tests are located in `src/claude_skills/claude_skills/tests` and can be run using `pytest` with options like `-v --tb=short --strict-markers`.
    *   **General CLI Usage:** The `sdd` command provides a unified interface for various operations, including spec management (`sdd create`, `sdd activate-spec`, `sdd next-task`), documentation (`sdd doc generate`, `sdd doc search`), testing (`sdd test run`), and reviews (`sdd plan-review`).

---

## Documentation Map

For detailed information, see:

- `index.md` - Master documentation index
- `architecture.md` - Detailed architecture
- `development-guide.md` - Development workflow

---

*Generated using LLM-based documentation workflow*