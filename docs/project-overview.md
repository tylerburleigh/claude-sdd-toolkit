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

## Research Findings

### 1. Executive Summary

The `claude-sdd-toolkit` project implements a Spec-Driven Development (SDD) framework designed to enhance AI-assisted software development, particularly within the Claude Code environment. It provides a Python library and CLI toolkit that structures development around machine-readable JSON specifications. These specifications define tasks, manage dependencies, and track development progress, aiming to bring systematic order to AI-driven coding workflows.

This toolkit targets developers seeking to mitigate common issues in AI-assisted development, such as scope creep, loss of context, ambiguous progress tracking, and difficulties in resuming work. By enforcing a "plan-first" approach, atomic task breakdowns, automated progress monitoring, and multi-model AI consultation for quality assurance, it streamlines the development lifecycle. The project distinguishes itself through a modular, skill-based architecture, a flexible provider abstraction layer that integrates multiple AI tools (e.g., Gemini, Cursor Agent, Claude, OpenCode), and a robust system for generating and querying codebase documentation with AI enhancements.

### 2. Key Features

*   **Spec-Driven Development Workflow**: Organizes development through a lifecycle of JSON specifications (e.g., `specs/pending`, `specs/active`, `specs/completed`). Commands like `sdd-plan` for creation, `sdd-next` for task orchestration, `sdd-update` for progress tracking, and `sdd-validate` for integrity checks provide a structured, traceable path from concept to completion.
*   **Multi-Model AI Consultation**: Leverages a unified `ProviderContext` abstraction layer to integrate and consult various AI models (Gemini, Cursor Agent, Codex, Claude, OpenCode). Skills such as `sdd-plan-review` and `sdd-fidelity-review` utilize parallel AI analyses to offer diverse perspectives for quality assessments and to verify implementation against specifications.
*   **Comprehensive Code Documentation & Analysis**: Features `llm-doc-gen` and `doc-query` skills for AI-powered documentation generation and intelligent code analysis. It can create structural documentation (`docs/DOCUMENTATION.md`, `docs/ARCHITECTURE.md`), provide codebase statistics, and enable complex queries such as call graphs, function callers/callees, complexity analysis, and refactoring candidates.
*   **Automated Progress & Context Tracking**: Automatically monitors task status, recording `started_at` and `completed_at` timestamps for calculating `actual_hours`. It also tracks Claude token usage during `sdd-next` operations to proactively warn users about approaching context window limits, aiding in efficient session management.
*   **Optional Git Integration**: Offers capabilities for agent-controlled file staging (`sdd create-task-commit`), AI-powered Pull Request (PR) creation (`sdd-pr skill`), automatic branch creation, and task-based auto-committing. This facilitates seamless integration with Git-based version control workflows.

### 3. Architecture Highlights

*   **Modular Skill-Based Design**: The core architecture is built upon independent, composable "skills" (e.g., `sdd-plan`, `sdd-next`, `doc-query` located in `src/claude_skills/claude_skills/`). This design promotes strong separation of concerns, enables independent development and testing of functionalities, and makes the system highly extensible without introducing breaking changes.
*   **Provider Abstraction Layer**: A key architectural decision is the `ProviderContext` (see `README.md` and `CHANGELOG.md` entry for `0.5.1`) which provides a unified interface for interacting with various AI tools. This allows the system to support multiple AI providers (Gemini, Cursor Agent, Codex, Claude, OpenCode) interchangeably and to perform parallel consultations, optimizing for robustness and diverse AI perspectives.
*   **JSON Specification as Primary State**: The project's primary state is maintained through machine-readable JSON specifications, stored in designated lifecycle folders (`specs/pending`, `specs/active`, `specs/completed`, `specs/archived`). This approach ensures that all development tasks, dependencies, and progress are Git-trackable and structured, forming a clear, machine-readable record of the project's evolution.
*   **Subagent System**: For more complex, multi-step tasks, the toolkit employs a subagent architecture (e.g., `sdd-validate`, `sdd-plan-review`, `sdd-update`, `run-tests`, `sdd-modify` use specialized subagents). This delegates intricate workflows to dedicated Claude instances, enhancing modularity and task management.
*   **Tree-sitter for Language Agnostic Analysis**: The project leverages `tree-sitter` for Abstract Syntax Tree (AST) parsing across multiple programming languages (Python, JavaScript/TypeScript, Go, HTML, CSS). This enables deep, language-agnostic code analysis, which is crucial for features like documentation generation, complexity analysis, and accurate code querying.

### 4. Development Overview

*   **Prerequisites**:
    *   **Required**: Claude Code (latest version), Python 3.9+, `pip` (Python package installer), Node.js >= 18.x (specifically for the OpenCode provider).
    *   **Optional**: Git for version control features, `tree-sitter` libraries for specific language parsing, and AI CLI tools (e.g., `gemini`, `codex`, `cursor-agent`) for direct AI provider integration.
*   **Key Setup/Installation Steps**:
    1.  Launch Claude Code and add `tylerburleigh/claude-sdd-toolkit` from the marketplace via the `/plugins` command.
    2.  Completely exit Claude Code.
    3.  Navigate to the plugin's Python source directory (`~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills`) and install Python dependencies using `pip install -e .`.
    4.  Run the unified dependency installer `sdd skills-dev install` from the same directory, which handles both Python and Node.js dependencies.
    5.  Restart Claude Code to activate the plugin.
    6.  Inside your project in Claude Code, execute `/sdd-setup` to configure necessary permissions and create project-specific configuration files (`.claude/settings.local.json`, `.claude/sdd_config.json`, `.claude/ai_config.yaml`).
*   **Primary Development Commands**:
    *   **Installation/Verification**:
        *   `pip install -e .`: Installs the Python package in editable mode.
        *   `sdd skills-dev install`: Unified installer for all dependencies.
        *   `sdd skills-dev verify-install`: Verifies proper installation of all components.
        *   `/sdd-setup`: Initializes project configurations and permissions.
    *   **Specification Management**:
        *   `sdd create <spec_name>`: Initiates a new JSON specification.
        *   `sdd activate-spec <spec_id>`: Moves a pending spec to active status.
        *   `sdd next-task <spec_id>`: Identifies and prepares the next actionable task within a spec.
        *   `sdd update-status <spec> <task>`: Changes the status of a task.
        *   `sdd validate <spec.json>`: Checks the integrity and dependencies of a specification.
        *   `sdd list-specs [--status STATUS]`: Lists specifications based on their status.
    *   **Documentation & Analysis**:
        *   `sdd doc analyze-with-ai .`: Generates AI-enhanced documentation for the codebase.
        *   `sdd doc search "pattern"`: Searches the generated documentation for specific patterns.
        *   `sdd doc callers "function_name"`: Finds all callers of a specified function.
    *   **Testing**:
        *   `sdd test run tests/`: Executes project tests (e.g., using `pytest`).
        *   `sdd test check-tools`: Verifies the availability and configuration of AI tools.
    *   **Reviews**:
        *   `sdd plan-review <spec>`: Initiates a multi-model review of a specification.
        *   `sdd fidelity-review <spec>`: Verifies the implementation's fidelity against the spec.
        *   `sdd render <spec>`: Generates a human-readable markdown rendering of a spec.

---

## Documentation Map

For detailed information, see:

- `index.md` - Master documentation index
- `architecture.md` - Detailed architecture
- `development-guide.md` - Development workflow

---

*Generated using LLM-based documentation workflow*