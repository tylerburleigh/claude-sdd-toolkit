# AI Context - Quick Reference Guide

**Project:** Claude SDD Toolkit
**Version:** 0.5.0
**Generated:** 2025-11-09

> This AI context guide was generated using AI-enhanced analysis with gemini.
> **Note**: codex was attempted but failed due to requiring an interactive terminal (TTY).

This document provides a concise reference for AI assistants working with the SDD Toolkit codebase.

---

## 1. Project Overview

The **SDD Toolkit** is a Python-based command-line toolset designed to integrate with the Claude AI assistant. It facilitates a **"spec-driven development"** (SDD) workflow, where development tasks are defined and managed through machine-readable JSON files called "specs."

### Purpose

The toolkit provides a suite of commands (skills) that allow developers and AI assistants to create, plan, execute, and track development work in a structured and systematic way.

### Target Users

Developers who want to leverage AI for coding tasks while maintaining rigorous organization and clear, version-controlled plans.

---

## 2. Domain Concepts

### 1. SDD (Spec-Driven Development)

**Definition**: The core methodology of the toolkit - a plan-first approach where all development work is guided by a formal specification document.

**Usage**: Used throughout the project as the central workflow philosophy.

**Key Principle**: Every task, dependency, and requirement is explicitly defined in a JSON spec before implementation begins.

---

### 2. Spec (Specification)

**Definition**: A JSON file that defines a development task, including purpose, requirements, dependencies, and current status.

**Location**: Managed in the `/specs` directory with subdirectories:
- `pending/` - Newly created specs
- `active/` - Currently being worked on
- `completed/` - Finished specs
- `archived/` - Old/deprecated specs

**Structure**:
- Metadata (name, description, complexity)
- Phases (logical groupings)
- Tasks (atomic work units)
- Dependencies (task relationships)
- Journal (decision log)
- Verification steps

**Central Artifact**: Specs are the single source of truth for all development work.

---

### 3. Skill

**Definition**: A command or set of capabilities exposed to the user or AI assistant.

**Examples**: `sdd-plan`, `sdd-next`, `code-doc`, `run-tests`

**Location**: Each skill is defined in the `/skills` directory and implemented as CLI commands in `src/claude_skills/claude_skills/`

**Purpose**: Skills provide modular functionality for different parts of the SDD workflow.

---

### 4. Agent

**Definition**: An AI persona or automated system that performs tasks based on the SDD workflow.

**Location**: Files in `/agents` directory define prompts and instructions for different AI agents.

**Purpose**: Agents carry out specific parts of the development process:
- Planning
- Modifying specs
- Reviewing work
- Generating documentation

---

### 5. Fidelity Review

**Definition**: A process of comparing implemented code against the original spec to ensure all requirements have been met.

**Skill**: `sdd-fidelity-review` is dedicated to this purpose.

**Purpose**: Quality assurance - ensures implementation matches the plan.

---

### 6. Task

**Definition**: An individual unit of work defined within a spec.

**Structure**:
- ID (unique identifier)
- Title and description
- Status (pending, in_progress, completed, blocked)
- Dependencies (list of prerequisite task IDs)
- Verification steps

**Relationship**: A spec can contain multiple tasks, often with dependencies on each other.

---

### 7. Context Tracker

**Definition**: A mechanism to maintain state and history across different skill executions.

**Implementation**: Referenced in `src/claude_skills/claude_skills/context_tracker/cli.py`

**Purpose**: Provides continuity for the AI assistant as it works through multi-step tasks.

---

## 3. Critical Files Analysis

### Must-Know Files for Development

#### 1. `src/claude_skills/claude_skills/sdd_plan/cli.py`

**Why Critical**: Entry point for the `sdd-plan` skill - the starting point of the entire SDD workflow.

**Responsibility**: Takes an initial idea and generates a structured JSON spec.

**Key Operations**:
- Template-based spec generation
- Initial task definition
- Dependency setup

---

#### 2. `src/claude_skills/claude_skills/sdd_next/cli.py`

**Why Critical**: The engine of the workflow.

**Responsibility**:
- Reads the active spec
- Identifies the next incomplete task
- Provides AI with context needed to work on it

**Central Role**: This is essential for progressing through a development plan.

**Dependencies**: Closely integrated with `doc-query` for context enrichment.

---

#### 3. `src/claude_skills/claude_skills/sdd_update/cli.py`

**Why Critical**: State management - all spec modifications flow through here.

**Key Functions**:
- Mark tasks as complete
- Record results and decisions
- Update spec status
- Manage spec lifecycle (activate, complete, archive)

**Relationship**: Closely tied to `sdd-next` for workflow progression.

---

#### 4. `src/claude_skills/claude_skills/sdd_spec_mod/cli.py`

**Why Critical**: Allows modifying an existing spec.

**Purpose**: Adapt to changing requirements or incorporate feedback without starting from scratch.

**Use Cases**:
- Adding new tasks
- Updating estimates
- Modifying dependencies
- Incorporating review feedback

---

#### 5. `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py`

**Why Critical**: Implements the quality assurance step of the workflow.

**Purpose**: Ensures work done aligns with the plan - a key principle of spec-driven development.

**Dependencies**:
- Reads spec files for requirements
- Analyzes actual source code changes
- Uses AI tools for comparison

---

#### 6. `docs/ARCHITECTURE.md`

**Why Critical**: Provides high-level overview of system design and component interactions.

**Purpose**: Best starting point for understanding the entire system.

**Content**: Architecture decisions, component relationships, design patterns, technology stack.

---

#### 7. `specs/` Directory

**Why Critical**: Not a single file, but contains the source of truth for all development work.

**Structure**: JSON spec files organized by status (pending, active, completed, archived).

**Usage**: All workflow commands operate on these files.

---

## 4. Common Workflow Patterns

### 1. Creating a New Development Plan

**Steps**:
1. User invokes `sdd-begin` or `sdd-plan` with high-level description
2. Tool (with AI assistance) generates new JSON spec in `specs/pending/` or `specs/active/`
3. Spec outlines required tasks, dependencies, and estimates

**AI Assistant Role**:
- Help define tasks based on user requirements
- Suggest appropriate dependencies
- Estimate complexity and time

---

### 2. Working on the Next Task

**Steps**:
1. Developer/AI runs `sdd-next` command
2. Tool inspects active spec, finds next available task, presents details
3. Developer/AI performs the coding task
4. Run `sdd-update` to mark task completed, provide paths to changed files

**AI Assistant Role**:
- Execute `sdd-next` to identify task
- Summarize task requirements
- Suggest implementation approach
- Mark task complete when done

---

### 3. Modifying an Existing Spec

**Scenario**: Requirements change or feedback needs incorporation.

**Steps**:
1. Run `sdd-modify` command
2. Provide instructions (e.g., "add task for unit tests", "update estimate for task-3")
3. Tool updates JSON spec file

**AI Assistant Role**:
- Interpret user's change request
- Execute modification command
- Validate updated spec

---

## 5. Potential Gotchas

### 1. Spec File Management

**Issue**: State is stored in JSON files in `specs/` directory.

**Risks**:
- File corruption
- Modifying wrong spec
- Forgetting to move specs between directories (pending → active → completed)
- Manual edits breaking JSON structure

**AI Assistant Guidance**:
- Always validate after manual edits
- Use CLI commands instead of direct file editing when possible
- Double-check spec ID before modifications

---

### 2. Strict JSON Schema

**Issue**: Spec files adhere to a strict (sometimes undocumented) JSON schema.

**Risks**:
- Adding/removing/modifying fields incorrectly causes CLI tools to fail
- Breaking changes between versions

**AI Assistant Guidance**:
- Learn and respect the schema
- Use `sdd validate` liberally
- Use `--auto-fix` for common schema issues

---

### 3. State Synchronization

**Issue**: The `sdd-update` step is critical for keeping specs in sync with code.

**Risks**:
- Complete coding task but forget `sdd-update`
- Spec becomes out of sync with codebase
- Confusion and potential rework

**AI Assistant Guidance**:
- Always run `sdd-update` after completing tasks
- Remind user if they complete work without updating spec

---

### 4. Tool Inter-dependencies

**Issue**: Commands designed to be used in specific sequence.

**Required Sequence**: `plan` → `next` → `update` (repeat) → `complete`

**Risks**:
- Using commands out of order leads to unpredictable results
- Running `sdd-next` with no active spec fails

**AI Assistant Guidance**:
- Follow the workflow sequence
- Check for active spec before running next-task
- Validate before activating specs

---

### 5. AI Tool Compatibility

**Issue**: Some AI CLI tools may not work in non-interactive mode.

**Known Issues**:
- **codex**: Requires TTY, fails with "stdout is not a terminal" error
- Cannot be used in subprocess/piped mode

**Workarounds**:
- Use gemini or cursor-agent instead
- For codex users: Request non-interactive mode support from maintainers

**AI Assistant Guidance**:
- Check tool availability before AI-enhanced commands
- Suggest alternative tools if preferred tool unavailable
- Gracefully fall back to structural-only output

---

## 6. Extension Patterns

The codebase follows a clear, modular pattern for adding new functionality.

### Adding a New Skill

**Steps**:

1. **Create skill directory**: `src/claude_skills/claude_skills/sdd_new_feature/`

2. **Implement CLI**: Create `cli.py` using CLI library (typer or click inferred from structure)
   - Define command-line interface
   - Add argument parsing
   - Implement command handlers

3. **Add supporting logic**: Place business logic, helpers, classes in additional Python files
   - `core.py` - Core functionality
   - `helpers.py` - Utility functions
   - Other domain-specific modules

4. **Document the skill**: Create `SKILL.md` in `skills/sdd-new-feature/`
   - Explain functionality
   - Document parameters
   - Provide usage examples
   - Serves as documentation for humans and AI

5. **Define agent behavior** (optional): Add `agents/sdd-new-feature.md`
   - Provide prompts for AI agent
   - Define automated behavior instructions

---

### Integration Best Practices

**Use Common Utilities**:
- `common/spec.py` - Spec file I/O
- `common/printer.py` - Consistent output formatting
- `common/validation.py` - Shared validation logic
- `common/ai_config.py` - AI tool configuration

**Follow Patterns**:
- Command pattern for CLI structure
- Factory pattern for language-specific parsers
- Strategy pattern for AI tool selection
- Facade pattern for complex operations

**Maintain Modularity**:
- Keep skills independent
- Use clear interfaces
- Document dependencies
- Enable graceful degradation

---

## Quick Command Reference

### Spec Lifecycle
```bash
sdd create <name>                    # Create new spec
sdd validate <spec-id>               # Validate integrity
sdd activate-spec <spec-id>          # Move to active
sdd complete-spec <spec-id>          # Archive as completed
```

### Task Management
```bash
sdd next-task <spec-id>              # Find next task
sdd prepare-task <spec-id> <task-id> # Get context
sdd update-status <spec-id> <task-id> --status <status>
sdd complete-task <spec-id> <task-id>
sdd add-journal <spec-id> --title "..." --body "..."
```

### Documentation
```bash
sdd doc analyze-with-ai .            # Generate with AI
sdd doc generate .                   # Generate (structural only)
sdd doc search "keyword"             # Search documentation
sdd doc complexity --threshold 10    # Find complex code
sdd doc find-class "ClassName"       # Locate class
sdd doc find-function "func_name"    # Locate function
```

### Testing
```bash
sdd test run --preset unit           # Run tests
sdd test consult --preset unit       # AI debugging
sdd test discover                    # Find test patterns
```

### Review & Quality
```bash
sdd plan-review <spec-id>            # Multi-model spec review
sdd fidelity-review <spec-id>        # Compare code to spec
```

---

## AI Tool Recommendations

### For Documentation Generation

**Recommended**:
- **gemini**: Fast, reliable, works in subprocess mode ✅
- **cursor-agent**: Excellent for large codebases (1M context) ✅

**Not Recommended**:
- **codex**: Requires TTY, incompatible with subprocess capture ❌

### For Plan Reviews

**Multi-Agent Mode** (default):
- Uses 2 AI models in parallel
- Priority order: cursor-agent → gemini → codex
- Best for production documentation

**Single-Agent Mode** (`--single-agent`):
- Faster, lower cost
- Good for quick iterations

---

## Key Insights for AI Assistants

1. **Specs are the source of truth** - Never bypass the JSON spec file
2. **Dependency graphs are critical** - Bad dependencies break the workflow
3. **Documentation bridges high-level and low-level** - Use doc-query to connect specs to code
4. **AI is optional** - Core functionality works without AI tools
5. **Filesystem is the database** - Embrace file-based state management
6. **Modular by design** - Skills are independent, can be used separately
7. **Graceful degradation** - Always provide fallback when AI tools fail
8. **Validation is cheap** - Run `sdd validate` liberally

---

## Conclusion

The SDD Toolkit enables structured, systematic development with AI assistance. As an AI assistant working with this codebase:

- **Follow the workflow** - plan → validate → execute → track → complete
- **Use CLI commands** - Don't manually edit JSON when commands exist
- **Validate frequently** - Before activating, after modifications
- **Provide context** - Use doc-query to inform implementation decisions
- **Log decisions** - Update journals to preserve reasoning
- **Handle failures gracefully** - Fall back when AI tools unavailable

By understanding these concepts and patterns, you can effectively assist developers in leveraging the full power of spec-driven development.
