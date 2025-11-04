# AI Context - Quick Reference Guide

**Project:** Claude SDD Toolkit
**Version:** 0.4.2
**Generated:** 2025-11-04

This document provides a concise reference for AI assistants working with the SDD Toolkit codebase. It synthesizes insights from multiple AI model analyses (Gemini and Codex).

---

## Project Overview

The SDD Toolkit is a command-line interface for **Spec-Driven Development (SDD)**—a systematic, plan-first methodology using machine-readable JSON specifications to structure the entire software development lifecycle. It targets Claude AI users who want organized, trackable, and AI-assisted development workflows.

### What It Solves
- Unstructured, ad-hoc development leading to scope drift
- Forgotten requirements and lost context during long sessions
- Lack of progress tracking and audit trails
- Difficulty maintaining focus across complex, multi-task projects

### Core Value Proposition
- **Single source of truth:** JSON specs define all tasks, dependencies, and state
- **Systematic workflow:** Plan → Validate → Execute → Track → Complete
- **AI-enhanced insights:** Multi-model consultations for reviews, documentation, and debugging
- **Git-friendly:** All state is version-controlled files

---

## Domain Concepts

### Specification (Spec)
**What:** A JSON file defining a complete feature or work item with tasks, dependencies, phases, and verification steps.

**Structure:**
- **Metadata:** Name, description, complexity, estimated time
- **Phases:** Logical groupings of tasks (e.g., "Setup", "Core Implementation", "Testing")
- **Tasks:** Atomic units of work with status, dependencies, assignees
- **Journal:** Append-only log of decisions, notes, and status changes
- **Dependencies:** Directed graph showing task relationships

**Locations:**
- `specs/pending/` - Newly created, not yet active
- `specs/active/` - Currently being worked on
- `specs/completed/` - Finished work, archived

**Status Flow:**
```
pending → in_progress → completed (per task)
pending → active → completed (per spec lifecycle)
```

---

### Skill
**What:** A self-contained CLI module providing specialized functionality for the SDD workflow.

**Core Skills:**

| Skill | Purpose | Key Commands |
|-------|---------|--------------|
| **sdd-plan** | Create specs from templates | `sdd create <name>` |
| **sdd-validate** | Validate spec integrity | `sdd validate <spec-id>` |
| **sdd-next** | Find next actionable task | `sdd next-task`, `sdd prepare-task` |
| **sdd-update** | Manage spec state | `sdd update-status`, `sdd add-journal`, `sdd activate-spec`, `sdd complete-spec` |
| **sdd-render** | Convert JSON to Markdown | `sdd render <spec-id> --mode enhanced` (NEW in v0.4.0) |
| **sdd-plan-review** | AI-assisted spec review | `sdd plan-review <spec-id>` |
| **code-doc** | Generate codebase docs | `sdd doc analyze-with-ai .` |
| **doc-query** | Query documentation | `sdd doc search`, `sdd doc complexity` |
| **run-tests** | Run tests with AI debugging | `sdd test run`, `sdd test consult` |

---

### Hierarchy
**What:** The nested structure within a spec JSON showing phase-task-subtask relationships and dependencies.

**Critical for:**
- Dependency analysis (which tasks can run next)
- Progress tracking (completion percentages)
- Validation (detecting circular dependencies)

**Example:**
```json
{
  "phases": [
    {
      "name": "Setup",
      "tasks": [
        {
          "id": "task-1",
          "title": "Create project structure",
          "status": "completed",
          "dependencies": []
        },
        {
          "id": "task-2",
          "title": "Set up CI/CD",
          "status": "pending",
          "dependencies": ["task-1"]
        }
      ]
    }
  ]
}
```

---

### Journal
**What:** An append-only log within each spec file recording decisions, notes, and progress updates.

**Purpose:**
- Historical record of "why" decisions were made
- Context for future developers (or AI assistants)
- Audit trail for compliance

**Managed via:** `sdd add-journal <spec-id> --title "..." --body "..."`

---

### Verification Task
**What:** A special task type (`type: "verify"`) that runs automated checks (tests, linting) to confirm a preceding task is complete.

**Auto-execution:** `sdd execute-verify <spec-id> <task-id>` runs the check and updates status automatically.

---

## Critical Files Analysis

### Must-Know Files for AI Assistants

#### 1. **Spec Files** (`specs/active/*.json`, `specs/completed/*.json`)
**Why critical:** The single source of truth for all work. Every other command reads/writes these files.

**Common operations:**
- Read to determine next task
- Write to update status or add journal entries
- Validate before activating

---

#### 2. **`src/claude_skills/claude_skills/sdd_next/cli.py`**
**Why critical:** The workflow engine. Developers use this constantly to identify and prepare their next task.

**Key functions:**
- `next_task()` - Computes which task to work on next based on dependencies
- `prepare_task()` - Gathers context (doc-query integration) for implementation

**When assisting:** If user asks "what should I work on next?", this is the primary tool.

---

#### 3. **`src/claude_skills/claude_skills/sdd_update/cli.py`**
**Why critical:** State manager. All spec modifications flow through here.

**Key functions:**
- `update_status()` - Change task status
- `add_journal()` - Log decisions
- `activate_spec()` / `complete_spec()` - Lifecycle management

**When assisting:** If user wants to mark task done or log a decision, use these commands.

---

#### 4. **`src/claude_skills/claude_skills/sdd_validate/cli.py`**
**Why critical:** Quality assurance. Prevents broken workflows from invalid specs.

**Key functions:**
- Schema validation
- Circular dependency detection
- Auto-fix for common errors

**When assisting:** Run this before activating a spec or after manual JSON edits.

---

#### 5. **`src/claude_skills/claude_skills/code_doc/cli.py`** & **`doc_query/cli.py`**
**Why critical:** Context provision system. Makes the toolkit "aware" of the codebase.

**Workflow:**
1. `code-doc` generates `docs/documentation.json` from source code
2. `doc-query` provides fast lookups (classes, functions, complexity, dependencies)
3. `sdd-next prepare-task` integrates doc-query to enrich task context

**When assisting:** If user needs to understand codebase before implementing a task, leverage these tools.

---

#### 6. **`src/claude_skills/claude_skills/common/spec.py`**
**Why critical:** Shared utilities for reading/writing specs safely.

**Used by:** Almost every skill. Ensures consistent spec file handling.

---

#### 7. **`src/claude_skills/claude_skills/sdd_render/cli.py`** (NEW in v0.4.0)
**Why critical:** Converts JSON specs into readable Markdown with AI-enhanced features.

**Key features:**
- Basic mode (fast, no AI)
- Enhanced mode with 3 levels (summary, standard, full)
- Executive summaries, dependency graphs, complexity scoring

**When assisting:** If user wants to review a spec in human-readable form, use `sdd render`.

---

## Common Workflow Patterns

### Pattern 1: Starting a New Feature

```bash
# 1. Create spec
sdd create feature-name

# 2. Edit spec manually (add tasks, dependencies)
# (User edits specs/pending/feature-name-YYYY-MM-DD-NNN.json)

# 3. Validate
sdd validate feature-name-YYYY-MM-DD-NNN

# 4. Activate
sdd activate-spec feature-name-YYYY-MM-DD-NNN

# 5. Begin work
sdd next-task feature-name-YYYY-MM-DD-NNN
```

**AI Assistant Role:**
- Help user define tasks and dependencies when creating spec
- Remind to validate before activating
- Guide through first task preparation

---

### Pattern 2: Daily Development Loop

```bash
# Identify next task
sdd next-task <spec-id>

# Get context for task
sdd prepare-task <spec-id> <task-id>
# → Includes: task description, dependencies, related files, doc context

# Implement task
# (Developer codes)

# Mark complete and log decision
sdd complete-task <spec-id> <task-id> --journal-title "Completed X" --journal-body "Decided to use Y because Z"

# Repeat
```

**AI Assistant Role:**
- Execute commands on user request
- Summarize task requirements from prepare-task output
- Suggest relevant code patterns from doc-query results

---

### Pattern 3: Handling Blockers

**Scenario:** User discovers a task is blocked by unforeseen dependency.

```bash
# 1. Update task status to blocked
sdd update-status <spec-id> <task-id> --status blocked

# 2. Add journal entry explaining blocker
sdd add-journal <spec-id> --title "Task X blocked" --body "Waiting for upstream API"

# 3. Find alternative task
sdd next-task <spec-id>
# → Returns different task that's not blocked
```

**AI Assistant Role:**
- Help user identify why task is blocked
- Suggest workaround or alternative approach
- Find next unblocked task automatically

---

### Pattern 4: Generating Comprehensive Codebase Documentation

```bash
# Generate with AI enhancement (recommended)
sdd doc analyze-with-ai . --name "ProjectName" --version "X.Y.Z" --verbose
# → Creates: DOCUMENTATION.md, documentation.json, ARCHITECTURE.md, AI_CONTEXT.md

# Query the docs
sdd doc search "AuthService"
sdd doc complexity --threshold 10
sdd doc find-class ".*Controller" --pattern
```

**AI Assistant Role:**
- Run doc generation proactively when starting new spec
- Query docs to provide context during task preparation
- Identify high-complexity areas that need refactoring

---

### Pattern 5: Running Tests with AI Debugging

```bash
# Run tests
sdd test run --preset unit
# → If failures occur...

# Consult AI for debugging
sdd test consult --preset unit
# → Parallel AI consultation (gemini + codex) analyzes failures
```

**AI Assistant Role:**
- Suggest test presets based on task type
- Interpret AI consultation results
- Propose fixes for failing tests

---

### Pattern 6: AI-Enhanced Spec Rendering (NEW in v0.4.0)

```bash
# Fast rendering (no AI)
sdd render <spec-id> --mode basic

# AI-enhanced rendering
sdd render <spec-id> --mode enhanced --enhancement-level standard
# → Executive summary, dependency graph, priority ranking, complexity scores

# Full AI analysis
sdd render <spec-id> --mode enhanced --enhancement-level full
# → All features + narrative enhancement + detailed insights
```

**AI Assistant Role:**
- Recommend enhancement level based on spec complexity
- Interpret rendered output (e.g., explain critical path from Mermaid diagram)
- Suggest task reordering based on priority scores

---

## Potential Gotchas

### 1. **File-Based State Conflicts**
**Issue:** Multiple users editing same spec simultaneously can cause merge conflicts.

**Solution:**
- Use git branches for separate features
- Communicate when working on same spec
- Leverage `sdd validate` to detect/fix conflicts

**AI Guidance:** Remind users to pull latest changes before activating specs.

---

### 2. **Stale Documentation**
**Issue:** `documentation.json` becomes outdated as code evolves.

**Solution:**
- `doc-query` auto-detects staleness and regenerates
- Manually regenerate with `sdd doc generate` periodically

**AI Guidance:** If doc-query results seem wrong, suggest regenerating docs.

---

### 3. **Circular Dependencies**
**Issue:** Tasks depend on each other in a cycle, blocking all progress.

**Solution:**
- `sdd validate` detects circular dependencies
- Manual fix: break cycle by removing or reordering dependencies

**AI Guidance:** When user reports "no next task available," run validation to check for circles.

---

### 4. **AI Tool Availability**
**Issue:** AI-enhanced features (render, plan-review, code-doc AI mode) fail if external tools not installed.

**Tools required:**
- `gemini` CLI
- `codex` CLI
- `cursor-agent` CLI (optional, best for large codebases)

**Solution:**
- Commands gracefully fall back to structural output
- Check installation: `gemini --version`, `codex --version`

**AI Guidance:** If AI features fail, verify tool installation and suggest fallback commands.

---

### 5. **Forgotten Verification Tasks**
**Issue:** User marks task complete without running verification, introducing bugs.

**Solution:**
- `sdd-next` reminds to run verification before moving on
- Use `sdd execute-verify` to automate checks

**AI Guidance:** Prompt user to run verification after implementation tasks.

---

### 6. **JSON Schema Changes**
**Issue:** Toolkit updates may change spec schema, breaking old specs.

**Solution:**
- `sdd validate --auto-fix` attempts to migrate old specs
- Manual updates for complex cases

**AI Guidance:** If validation fails on old spec, suggest auto-fix or manual migration.

---

## Extension Patterns

### Adding a New Skill

**Steps:**
1. Create `src/claude_skills/claude_skills/<skill_name>/cli.py`
2. Define `register_<skill_name>(subparsers)` function
3. Add registration in `cli/sdd/registry.py:register_all_subcommands`
4. Use `PrettyPrinter` for output, `common.spec` for spec I/O
5. Add metrics with `@track_command_usage` decorator

**Example skeleton:**
```python
def register_my_skill(subparsers):
    parser = subparsers.add_parser('my-skill', help='...')
    parser.add_argument('--flag', help='...')
    parser.set_defaults(func=my_skill_handler)

@track_command_usage('my-skill')
def my_skill_handler(args, printer):
    printer.print_info("Running my-skill...")
    # Implementation
```

---

### Adding AI Tool Integration

**Steps:**
1. Add tool config in `common/ai_config.py`
2. Implement subprocess call with timeout
3. Add fallback logic for tool unavailability
4. Parse tool output and format results

**Example:**
```python
from claude_skills.common.ai_config import get_ai_tool_command

cmd = get_ai_tool_command('gemini', prompt)
result = subprocess.run(cmd, timeout=90, capture_output=True)
if result.returncode != 0:
    # Fall back to non-AI mode
```

---

### Adding Language Support (code-doc)

**Steps:**
1. Add dependency: `tree-sitter-<language>`
2. Create parser: `code_doc/parsers/<language>.py`
3. Implement `BaseParser` interface
4. Register in `parsers/factory.py`

**Example:**
```python
class RustParser(BaseParser):
    def parse_file(self, file_path):
        # Parse Rust AST
        return {
            'classes': [...],
            'functions': [...],
            'dependencies': [...]
        }
```

---

## Quick Reference: Command Cheat Sheet

### Spec Lifecycle
```bash
sdd create <name>                      # Create new spec
sdd validate <spec-id>                 # Validate spec
sdd activate-spec <spec-id>            # Move to active
sdd complete-spec <spec-id>            # Archive as completed
```

### Task Management
```bash
sdd next-task <spec-id>                # Find next task
sdd prepare-task <spec-id> <task-id>   # Get task context
sdd update-status <spec-id> <task-id> --status <status>
sdd complete-task <spec-id> <task-id>  # Mark complete + journal
sdd add-journal <spec-id> --title "..." --body "..."
```

### Documentation
```bash
sdd doc analyze-with-ai .              # Generate with AI
sdd doc generate .                     # Generate (no AI)
sdd doc search "keyword"               # Search docs
sdd doc complexity --threshold 10      # Find complex code
sdd doc find-class "ClassName"         # Locate class
```

### Rendering
```bash
sdd render <spec-id> --mode basic                           # Fast
sdd render <spec-id> --mode enhanced --enhancement-level standard  # AI (default)
sdd render <spec-id> --mode enhanced --enhancement-level full      # Full AI
```

### Testing
```bash
sdd test run --preset unit             # Run tests
sdd test consult --preset unit         # AI debugging
sdd test discover                      # Find test patterns
```

### Review
```bash
sdd plan-review <spec-id>              # Multi-model AI review
```

---

## Performance Expectations

| Operation | Speed | Notes |
|-----------|-------|-------|
| `sdd next-task` | < 1s | Fast dependency analysis |
| `sdd update-status` | < 1s | Simple file write |
| `sdd validate` | < 1s | Fast schema + graph checks |
| `sdd render --mode basic` | < 2s | Pure Markdown conversion |
| `sdd render --mode enhanced --level summary` | ~30s | AI executive summary only |
| `sdd render --mode enhanced --level standard` | ~60s | Balanced AI features (default) |
| `sdd render --mode enhanced --level full` | ~90s | Complete AI analysis |
| `sdd doc generate` | 5-30s | Depends on codebase size |
| `sdd doc analyze-with-ai` | 3-5min | Multi-agent AI consultation |
| `sdd plan-review` | 2-3min | Parallel multi-model review |

---

## Integration Points

### With Git
- Specs should be committed alongside code
- Use branches for separate features
- Journal entries provide commit message material

### With CI/CD
- Verification tasks can trigger CI jobs
- Spec completion can trigger deployment pipelines
- Metrics tracked in `~/.claude-skills/metrics.jsonl`

### With Claude AI
- Skills auto-invoke based on user intent
- Context from doc-query enriches Claude's responses
- Journal entries help Claude remember past decisions

---

## Key Architectural Insights (for AI Assistants)

1. **Everything flows through the JSON spec** - It's the canonical state. Never bypass it.

2. **Dependency graph is king** - `sdd-next` relies entirely on accurate dependencies. Bad deps = bad workflow.

3. **Documentation is the bridge** - `code-doc` + `doc-query` connect high-level specs to low-level code details.

4. **AI is optional but powerful** - All core functionality works without AI tools. AI adds insights, not requirements.

5. **Filesystem == database** - No external DB. All state is files. Embrace it, don't fight it.

6. **Modular by design** - Each skill is independent. You can use `code-doc` without `sdd-plan`, etc.

7. **Graceful degradation** - If AI tools fail, fall back to structural output. Never block user.

8. **Validation is cheap** - Run `sdd validate` liberally. It's fast and prevents workflow breakage.

---

## Conclusion

The SDD Toolkit is designed to keep both developers and AI assistants focused, organized, and productive. As an AI assistant:

- **Proactively run commands** when user intent is clear
- **Query documentation** before suggesting code changes
- **Validate specs** before activating or after manual edits
- **Leverage AI tools** (render, plan-review, doc AI) for deeper insights
- **Log decisions** in journals to preserve context
- **Respect the workflow** - don't skip steps (validate → activate → execute)

By following these patterns, you'll help users harness the full power of spec-driven development while maintaining the structure and traceability that makes complex projects manageable.
