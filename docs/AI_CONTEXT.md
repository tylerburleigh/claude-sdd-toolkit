# AI Context - Quick Reference Guide

**Project:** claude-sdd-toolkit
**Version:** 0.1.0
**Generated:** 2025-10-24

This document provides a concise reference for AI assistants working with the SDD Toolkit codebase.

---

## Project Overview

The SDD Toolkit is a Claude Code plugin for spec-driven development. It uses machine-readable JSON specifications to define tasks, dependencies, and track progress. The toolkit includes Claude skills (interactive workflows), Python CLI tools, and slash commands to keep Claude focused on one task at a time while maintaining a comprehensive record of planned and completed work.

**Target Users:** Developers using Claude Code for complex projects who want to avoid scope drift, forgotten requirements, and lost context.

**Core Value Proposition:** Systematic planning, step-by-step execution, and complete audit trails for AI-assisted development.

---

## Domain Concepts

### Specification (Spec)
A JSON file containing:
- Feature overview and goals
- File-by-file implementation plan
- Task breakdown with dependencies
- Verification steps
- Edge cases and considerations

**Storage Locations:**
- `specs/active/` - work in progress
- `specs/completed/` - finished work
- `specs/archived/` - historical reference

### Skill
Extends Claude's capabilities via `SKILL.md` instruction files. Skills are automatically invoked by Claude based on user intent.

**Key Skills:**
- `sdd-plan` - Create specifications
- `sdd-next` - Find next actionable task
- `sdd-update` - Update progress and journal
- `sdd-validate` - Validate spec structure
- `code-doc` - Generate documentation
- `doc-query` - Query documentation
- `run-tests` - Run tests with AI debugging

### Command
User-invoked workflow triggered with `/` prefix (e.g., `/sdd-begin`).

**Location:** `~/.claude/commands/*.md`

### Hook
Event-triggered automation script.

**Events:**
- `session-start` - New session begins
- `pre-tool-use` - Before tool execution
- `post-tool-use` - After tool execution

**Location:** `~/.claude/hooks/`

### Task Hierarchy
Tree structure: **spec → phases → groups → tasks → subtasks**

Each node has:
- `type` - Node type (spec, phase, group, task, subtask, verify)
- `title` - Human-readable name
- `status` - Current state (pending, in_progress, completed, blocked)
- `parent` - Parent node ID
- `children` - Child node IDs
- `dependencies` - Blocking relationships

### Task Status
- **`pending`** - Not yet started
- **`in_progress`** - Currently being worked on
- **`completed`** - Finished successfully
- **`blocked`** - Waiting on dependencies

### Verification Task
Automated or manual checks with `on_failure` handling:
- `revert` - Undo changes
- `retry` - Try again
- `consult` - Ask AI for help

### Journal Entry
Decision/change log linked to tasks or specs. Used for audit trails and context preservation.

**Fields:** timestamp, author, task_id, entry text

### State File
Tracks task completion and progress in `specs/.state/`. Used for synchronization and progress rollup.

---

## Critical Files & Dependencies

### 1. Common Utilities
**File:** `src/claude_skills/claude_skills/common/__init__.py`

**Purpose:** Shared utilities used across all modules

**Key Functions:**
- `load_json_spec()` - Load spec from file
- `save_json_spec()` - Save spec to file
- `find_specs_directory()` - Locate specs directory
- `validate_path()` - Normalize and validate paths
- `track_progress()` - Calculate completion percentages
- `PrettyPrinter` - Consistent output formatting

### 2. Next Task Discovery
**File:** `src/claude_skills/claude_skills/sdd_next/cli.py`

**Purpose:** Find next actionable task in a spec

**Key Commands:**
- `sdd next-task <spec-id>` - Get next task
- `sdd prepare-task <spec-id> <task-id>` - Prepare task execution plan

**Dependencies:** Common utilities, validation module

### 3. State Management
**File:** `src/claude_skills/claude_skills/sdd_update/cli.py`

**Purpose:** Update task status, journal entries, time tracking

**Key Commands:**
- `sdd update-status <spec-id> <task-id> <status>` - Update task status
- `sdd add-journal <spec-id> --entry "text"` - Add journal entry
- `sdd sync-metadata <spec-id>` - Synchronize metadata

**Dependencies:** Common utilities, progress tracking

### 4. Spec Creation
**File:** `src/claude_skills/claude_skills/sdd_plan/cli.py`

**Purpose:** Create new specifications from templates

**Key Commands:**
- `sdd plan create --template simple` - Create simple spec
- `sdd plan create --template medium` - Create medium complexity spec
- `sdd plan create --template complex` - Create complex spec

**Dependencies:** Template module, validation

### 5. Spec Validation
**File:** `src/claude_skills/claude_skills/sdd_validate/cli.py`

**Purpose:** Validate spec structure and fix common errors

**Key Commands:**
- `sdd validate <spec-id>` - Validate spec
- `sdd fix <spec-id>` - Auto-fix common errors
- `sdd analyze-deps <spec-id>` - Check for circular dependencies

**Dependencies:** Hierarchy validation, formatting module

### 6. Documentation Generation
**File:** `src/claude_skills/claude_skills/code_doc/cli.py`

**Purpose:** Generate codebase documentation with optional AI analysis

**Key Commands:**
- `sdd doc generate <directory>` - Generate structural docs
- `sdd doc analyze-with-ai <directory>` - Generate with AI enhancement
- `sdd doc validate-json <file>` - Validate documentation JSON

**Dependencies:** Parsers (Python, JS, Go, HTML, CSS), AI consultation module

### 7. Documentation Query
**File:** `src/claude_skills/claude_skills/doc_query/cli.py`

**Purpose:** Query generated documentation

**Key Commands:**
- `sdd doc search "term"` - Search all entities
- `sdd doc find-class ClassName` - Find specific class
- `sdd doc complexity --threshold 10` - Find complex functions
- `sdd doc context "feature"` - Gather feature context

**Dependencies:** Query operations module

### 8. Test Execution
**File:** `src/claude_skills/claude_skills/run_tests/cli.py`

**Purpose:** Run tests with AI-powered debugging

**Key Commands:**
- `sdd test run <spec-id>` - Run tests from spec
- `sdd test consult --failures <file>` - Get AI help with failures
- `sdd test discover` - Discover available tests

**Dependencies:** Pytest runner, AI consultation module

### 9. Architecture Documentation
**File:** `ARCHITECTURE.md`

**Purpose:** System design, data flow, component interactions

**Key Sections:** Component architecture, design patterns, technology stack, architectural decisions

### 10. Developer Guide
**File:** `DEVELOPER.md`

**Purpose:** Extension patterns for skills, commands, hooks, CLI tools

**Key Sections:** How to create custom skills, commands, hooks, and CLI extensions

---

## Common Workflow Patterns

### Creating a Specification

```bash
# 1. Invoke skill (Claude does this automatically)
Skill(sdd-toolkit:sdd-plan)

# 2. Underlying CLI command
sdd plan create --template medium --name "Feature Name"

# 3. Spec saved to
specs/active/<spec-id>.json
```

### Implementing a Task

```bash
# 1. Start workflow
/sdd-begin

# 2. Detect active specs
sdd skills-dev start-helper -- detect-active

# 3. Get next task
sdd next-task <spec-id>

# 4. Implement the task
# (Developer writes code)

# 5. Update progress
sdd update-status <spec-id> <task-id> completed

# 6. Add journal entry
sdd add-journal <spec-id> --task <task-id> --entry "Implemented feature X"
```

### Updating Progress

```bash
# Update task status
sdd update-status <spec-id> <task-id> completed

# Add journal entry
sdd add-journal <spec-id> --entry "Decision: chose approach Y"

# Synchronize metadata
sdd sync-metadata <spec-id>

# Track time
sdd track-time <spec-id> <task-id> --start
sdd track-time <spec-id> <task-id> --end
```

### Validating a Spec

```bash
# Validate structure
sdd validate <spec-id>

# Auto-fix common errors
sdd fix <spec-id>

# Check for circular dependencies
sdd analyze-deps <spec-id>

# Generate validation report
sdd validate <spec-id> --report
```

### Generating Documentation

```bash
# Structural documentation only
sdd doc generate ./src --name "Project" --format both

# AI-enhanced documentation (recommended)
sdd doc analyze-with-ai ./src --name "Project"

# Query generated docs
sdd doc search "validation"
sdd doc complexity --threshold 15
sdd doc context "printer" --limit 5
```

### Running Tests

```bash
# Run tests from spec
sdd test run <spec-id>

# Run specific test file
sdd test run --path tests/test_validation.py

# Get AI help with failures
sdd test consult --failures test_output.txt

# Check tool availability
sdd test check-tools
```

---

## Potential Gotchas

### 1. Spec Directory Structure
**Gotcha:** CLI expects specific directory layout.

**Required Structure:**
```
specs/
├── active/       # Work in progress
├── completed/    # Finished work
└── archived/     # Historical reference
```

**Fix:** Create directories manually or use `sdd setup` command.

### 2. JSON-Only Specs
**Gotcha:** Markdown specs are deprecated.

**Solution:** Use JSON format exclusively. Convert old Markdown specs to JSON using migration tool.

### 3. State Synchronization
**Gotcha:** State files can drift from JSON specs.

**Symptoms:** Progress counters incorrect, status inconsistencies

**Fix:** Run `sdd reconcile-state <spec-id>` to synchronize.

### 4. Dependency Cycles
**Gotcha:** Circular dependencies can cause deadlocks.

**Prevention:** Validate before execution:
```bash
sdd analyze-deps <spec-id>
```

**Fix:** Break cycles by removing or reordering dependencies.

### 5. Verification Task Execution
**Gotcha:** Verification tasks have special execution rules.

**Important:**
- Use `sdd execute-verify <spec-id> <verify-id>`
- Configure `on_failure` behavior (revert, retry, consult)
- Manual verifications require user confirmation

### 6. Path Normalization
**Gotcha:** CLI normalizes all paths automatically.

**Implication:** Always use `validate_path()` utilities when working with file paths programmatically.

**Example:**
```python
from claude_skills.common import validate_path

path = validate_path(user_input_path, base_dir)
```

### 7. Journaling Expectations
**Gotcha:** Completed tasks should have journal entries.

**Detection:** Run `sdd check-journaling <spec-id>` to find tasks missing journal entries.

**Best Practice:** Add journal entry when marking task completed:
```bash
sdd update-status <spec-id> <task-id> completed
sdd add-journal <spec-id> --task <task-id> --entry "Completed implementation"
```

### 8. AI Tool Availability
**Gotcha:** AI-enhanced features require external CLI tools.

**Check Availability:**
```bash
cursor-agent --version
gemini --version
codex --version
```

**Fallback:** Use structural-only commands if AI tools unavailable:
- `sdd doc generate` instead of `sdd doc analyze-with-ai`
- Manual review instead of `sdd plan-review`

### 9. Tree-sitter Parsers
**Gotcha:** Language parsers must be installed separately.

**Installation:**
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-go
```

**Fallback:** Documentation generation will skip unsupported files.

### 10. Spec ID Format
**Gotcha:** Spec IDs must follow naming conventions.

**Valid:** `feature-auth`, `bugfix-123`, `refactor-db`

**Invalid:** `feature auth`, `bugfix#123`, `refactor/db`

**Best Practice:** Use kebab-case with alphanumeric characters and hyphens only.

---

## Extension Patterns

### Creating a Custom Skill

**Location:** `~/.claude/skills/my-skill/SKILL.md`

**Structure:**
```markdown
---
name: my-skill
description: Brief description
---

# Skill Instructions

Detailed instructions for Claude...

## When to Use
[Trigger conditions]

## How to Use
[Step-by-step workflow]

## CLI Commands
[Available commands]
```

**Invocation:** Claude detects intent and invokes skill automatically.

### Creating a Custom Command

**Location:** `~/.claude/commands/my-command.md`

**Structure:**
```markdown
---
name: my-command
description: Brief description
---

# Command Workflow

Step-by-step interactive workflow...

## Parameters
[Command arguments]

## Example
[Usage example]
```

**Invocation:** User types `/my-command` in Claude.

### Creating a Custom Hook

**Location:** `~/.claude/hooks/my-hook.sh` (executable)

**Structure:**
```bash
#!/bin/bash

# Read JSON from stdin
input=$(cat)

# Extract data
event=$(echo "$input" | jq -r '.event')

# Perform action
# ...

# Output JSON for Claude (optional)
echo '{"message": "Hook executed"}'

# Exit 0 for success
exit 0
```

**Trigger:** Automatically on event (`session-start`, `pre-tool-use`, `post-tool-use`).

### Creating a CLI Extension

**Steps:**
1. Create module: `src/claude_skills/claude_skills/my_module/`
2. Create `cli.py` with argparse structure
3. Register in unified CLI entry point
4. Add entry point to `pyproject.toml`
5. Write tests in `tests/`

**Example Structure:**
```python
# src/claude_skills/claude_skills/my_module/cli.py

import argparse
from claude_skills.common import PrettyPrinter

def cmd_my_command(args, printer):
    """Implement command logic"""
    printer.success("Command executed")
    return 0

def register_commands(subparsers):
    """Register with main CLI"""
    parser = subparsers.add_parser('my-command')
    parser.add_argument('--option', help='Option help')
    parser.set_defaults(func=cmd_my_command)
```

### Coding Conventions

**Output:**
- Use `PrettyPrinter` for all console output
- Use emoji for visual clarity (✅, ⚠️, ❌, 📊, 🔍)
- Provide clear error messages with remediation steps

**Paths:**
- Use `find_specs_directory()` for spec location
- Use `validate_path()` for path normalization
- Support both absolute and relative paths

**Specs:**
- Use `load_json_spec()` for loading
- Use `save_json_spec()` for saving
- Always validate before saving

**Testing:**
- Write tests in `tests/` directory
- Use pytest framework
- Mock file I/O and subprocess calls
- Test error conditions

**Error Handling:**
- Use specific exception types
- Provide context in error messages
- Log errors for debugging
- Return appropriate exit codes (0 = success, non-zero = error)

---

## Quick Command Reference

### Spec Lifecycle
```bash
sdd plan create --template medium       # Create spec
sdd next-task <spec-id>                 # Get next task
sdd update-status <spec-id> <task> completed
sdd validate <spec-id>                  # Validate spec
sdd lifecycle move <spec-id> completed  # Move to completed
```

### Documentation
```bash
sdd doc analyze-with-ai ./src --name "Project"
sdd doc search "term"
sdd doc complexity --threshold 10
sdd doc context "feature" --limit 5
```

### Testing
```bash
sdd test run <spec-id>
sdd test consult --failures output.txt
sdd test check-tools
```

### Development
```bash
sdd skills-dev start-helper -- detect-active
sdd skills-dev setup-permissions -- check .
```

---

## Summary

This AI context document provides essential information for working with the SDD Toolkit codebase:

- **Domain Concepts:** Specs, skills, commands, hooks, tasks, status, verification
- **Critical Files:** Common utilities, next-task, update, plan, validate, code-doc, doc-query, run-tests
- **Workflows:** Creating specs, implementing tasks, updating progress, validating, documenting, testing
- **Gotchas:** Directory structure, JSON-only, state sync, circular deps, path normalization
- **Extensions:** Custom skills, commands, hooks, CLI tools with coding conventions

**Key Principles:**
- **Plan first:** Always create a spec before implementation
- **Track progress:** Update status and journal regularly
- **Validate often:** Check for errors early and frequently
- **Use conventions:** Follow established patterns for consistency
- **Extend carefully:** Maintain separation of concerns and modularity

For detailed architecture information, see `ARCHITECTURE.md`. For extension development, see `DEVELOPER.md`. For structural code documentation, see `DOCUMENTATION.md`.
