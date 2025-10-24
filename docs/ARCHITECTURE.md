# Architecture Documentation

**Project:** claude-sdd-toolkit
**Version:** 0.1.0
**Generated:** 2025-10-24

---

## 1. System Overview

The SDD Toolkit is a Claude Code plugin designed to enforce a structured, spec-driven development workflow. It uses machine-readable JSON specifications to define tasks, dependencies, and track progress throughout the development lifecycle. By formalizing the development process, the toolkit addresses common challenges in AI-assisted development: scope drift, forgotten requirements, and lost context.

**Intended Users:** Software developers working with Claude Code on complex projects who need systematic planning, execution tracking, and comprehensive audit trails.

**Core Problem:** During complex, AI-assisted development sessions, maintaining focus and continuity is challenging. The toolkit solves this by requiring all work to be defined in a specification before implementation begins, providing "guardrails" for both developers and AI assistants.

---

## 2. Component Architecture

The system follows a layered architecture where each layer has distinct responsibilities and clear boundaries.

### A. Skills Layer (`~/.claude/skills/`)

**Purpose:** Extend Claude with specialized workflows that are automatically invoked based on user intent.

**Location:** `skills/*/SKILL.md`

**Key Skills:**
- **`sdd-plan`**: Creates JSON specifications from predefined templates (simple, medium, complex)
- **`sdd-next`**: Core progression engine that identifies the next actionable task based on status and dependencies
- **`sdd-update`**: State management for updating task statuses, journaling decisions, and time tracking
- **`sdd-validate`**: Quality assurance tool for validating spec structure, checking for circular dependencies, and auto-fixing common errors
- **`sdd-render`**: Presentation utility that converts JSON specs to human-readable Markdown
- **`sdd-plan-review`**: Multi-model AI review system that consults multiple AI tools for comprehensive feedback
- **`code-doc`**: Generates comprehensive codebase documentation with optional AI-enhanced architecture analysis
- **`doc-query`**: Provides CLI interface to search and query generated documentation
- **`run-tests`**: Test runner with AI-powered debugging assistance

### B. Commands Layer (`~/.claude/commands/`)

**Purpose:** User-invoked interactive workflows triggered with `/` prefix.

**Location:** `commands/*.md`

**Key Commands:**
- **`/sdd-setup`**: First-time configuration and project permissions setup
- **`/sdd-start`**: Interactive workflow to resume work on active specs

### C. Hooks Layer (`~/.claude/hooks/`)

**Purpose:** Event-triggered automation for proactive assistance.

**Location:** `hooks/*`

**Key Hooks:**
- **`session-start`**: Detects active specs when a new Claude session begins
- **`pre-tool-use`**: Pre-tool validation and safety checks
- **`post-tool-use`**: Post-execution validation and cleanup

### D. CLI Tools Layer (`src/claude_skills/claude_skills/`)

**Purpose:** Reusable Python tools that provide the core functionality.

**Location:** Python package installed via pip

**Unified CLI Structure:**
- **`sdd`**: Core SDD workflows (next-task, update-status, validate, plan, review)
- **`sdd doc`**: Documentation operations (generate, query, search, analyze-with-ai)
- **`sdd test`**: Testing workflows (run, consult, discover, check-tools)
- **`sdd skills-dev`**: Development utilities for skill/command/hook creation

### Component Relationships

```
Claude Code (User Interface)
    ↓
Skills/Commands/Hooks (Orchestration Layer)
    ↓
CLI Tools (Business Logic)
    ↓
File System (State Management)
    ↓
Project Files (specs/, code, docs)
```

**Interaction Pattern:** Skills and commands invoke CLI tools; CLI tools execute operations on files; hooks trigger automatically based on events. All components share a common utilities library for consistent behavior.

---

## 3. Data Flow & State Management

### Specification Structure

JSON specs use a hierarchical tree model:

```
spec-root (type: "spec")
    ├── phase-1 (type: "phase")
    │   ├── group-1 (type: "group")
    │   │   ├── task-1-1 (type: "task")
    │   │   │   ├── task-1-1-1 (type: "subtask")
    │   │   │   └── task-1-1-2 (type: "subtask")
    │   │   └── verify-1-1 (type: "verify")
    │   └── group-2 (type: "group")
    └── phase-2 (type: "phase")
```

**Node Properties:**
- **Identification:** `type`, `title`, `id`, `parent`, `children`
- **Dependencies:** `blocks`, `blocked_by`, `depends`
- **Status:** `status` (pending, in_progress, completed, blocked)
- **Progress:** `total_tasks`, `completed_tasks`
- **Metadata:** Task-specific data, journal entries, time tracking

### Request/Response Lifecycle

**Creating a Specification:**
1. User: "Create spec for feature X"
2. Claude detects intent → invokes `Skill(sdd-toolkit:sdd-plan)`
3. Skill loads instructions from `SKILL.md`
4. Skill executes CLI: `sdd plan create`
5. CLI generates JSON spec from template
6. Spec saved to `specs/active/`
7. Claude reports success to user

**Resuming Work:**
1. User: `/sdd-start`
2. Command loads workflow from `commands/sdd-start.md`
3. CLI: `sdd skills-dev start-helper -- detect-active`
4. CLI scans `specs/active/` directory
5. Returns JSON with active spec list
6. Claude presents interactive menu
7. User selects spec → `Skill(sdd-toolkit:sdd-next)`
8. CLI: `sdd next-task <spec-id>`
9. Returns next task details with full context
10. Claude assists with implementation

**Updating Progress:**
1. Task implementation completed
2. Claude invokes `Skill(sdd-toolkit:sdd-update)`
3. CLI: `sdd update-status <spec-id> <task-id> completed`
4. Spec file updated with new status
5. Progress counters recalculated
6. Journal entry added for audit trail
7. State synchronized

### State Management Strategy

**Primary Storage:**
- **Active specs:** `specs/active/` - work in progress
- **Completed specs:** `specs/completed/` - finished work
- **Archived specs:** `specs/archived/` - historical reference
- **State files:** `specs/.state/` - optional progress tracking

**State Properties:**
- **Progress tracking:** `completed_tasks`/`total_tasks` per node
- **Status tracking:** Four states (pending, in_progress, completed, blocked)
- **Journal entries:** Decision and change log in `metadata.journal`
- **Time tracking:** Start/end timestamps for tasks

**Consistency Model:**
- Single source of truth: JSON spec file
- Filesystem-based: No database required
- Version-controllable: Works with Git
- Stateless tools: Any command can run at any time

---

## 4. Design Patterns

### Command Pattern
Each CLI subcommand encapsulates a specific operation:
```python
def cmd_next_task(args, printer):
    # Load spec, analyze dependencies, find next task
    return 0  # Success
```

**Benefits:** Clear separation of concerns, easy to test, simple to extend.

### Strategy Pattern
AI tool selection with automatic fallback:
```python
# Auto-routing based on failure type or task requirements
consult_with_auto_routing(failure_type, tool="auto")
```

**Benefits:** Flexible integration with multiple AI providers, graceful degradation.

### Template Method Pattern
Specification generation from templates:
```python
templates = {
    "simple": {...},    # Small features, single file
    "medium": {...},    # Multiple files, moderate complexity
    "complex": {...}    # Large features, multiple phases
}
```

**Benefits:** Consistent structure, customizable content, reusable patterns.

### Factory Pattern
Parser creation for multi-language support:
```python
factory = create_parser_factory(project_dir, exclude_patterns)
parse_result = factory.parse_all()  # Returns appropriate parser per language
```

**Benefits:** Extensible to new languages, clean abstraction, testable.

### Observer Pattern
Event-driven hooks for automation:
- **`session-start`**: React to new sessions
- **`pre-tool-use`**: Validate before execution
- **`post-tool-use`**: Cleanup after execution

**Benefits:** Proactive assistance, separation of concerns, extensible.

### Repository Pattern
Centralized spec operations:
```python
load_json_spec(spec_id, specs_dir)
save_json_spec(spec_id, specs_dir, spec_data)
find_specs_directory(project_root)
```

**Benefits:** Consistent file access, error handling, path normalization.

### Facade Pattern
Unified CLI interface (`sdd`) provides simplified access to complex subsystems:
```bash
sdd plan create          # Access planning subsystem
sdd update-status        # Access state management
sdd doc generate         # Access documentation subsystem
sdd test run             # Access testing subsystem
```

**Benefits:** Consistent user experience, hidden complexity, single entry point.

---

## 5. Technology Stack

### Core Technologies

**Python 3.9+**
- **Rationale:** Robust standard library, excellent for CLI tools and file I/O
- **Usage:** All CLI tools, utilities, and skill logic

**JSON**
- **Rationale:** Machine-readable, validatable, widely supported
- **Usage:** Specification format, documentation output, configuration

**Markdown**
- **Rationale:** Human-readable, version-controllable, widely supported
- **Usage:** Skill instructions, command definitions, rendered documentation

**Tree-sitter**
- **Rationale:** Fast, incremental parsing for multiple languages
- **Usage:** Code analysis for documentation generation

### Key Dependencies

**`argparse`** (Standard Library)
- Purpose: CLI argument parsing and command structure
- Alternative considered: Click (chose standard library for zero dependencies)

**`pytest`**
- Purpose: Test framework integration
- Usage: `run-tests` skill wraps pytest for AI-assisted debugging

**External AI CLIs**
- **cursor-agent** (with cheetah): Fast analysis
- **gemini**: Fast structured analysis
- **codex**: Code understanding and debugging
- Integration: Subprocess execution for flexibility and decoupling

**Tree-sitter language parsers**
- `tree-sitter-python`: Python AST parsing
- `tree-sitter-javascript`: JS/TS parsing
- `tree-sitter-go`: Go parsing
- `tree-sitter-html`: HTML parsing
- `tree-sitter-css`: CSS parsing

### Architectural Technology Choices

**Filesystem as State Store**
- **Choice:** Store all state in version-controlled JSON files
- **Rationale:** Simple, transparent, portable, works with Git
- **Trade-offs:** No concurrent access, manual sync, limited query capabilities

**Subprocess Integration**
- **Choice:** Execute external tools (pytest, AI CLIs) via subprocess
- **Rationale:** Decoupling from implementation details, resilient to API changes
- **Trade-offs:** Requires tools installed locally, environment-dependent

**Unified CLI Architecture**
- **Choice:** Single `sdd` entry point with subcommands
- **Rationale:** Consistent interface, discoverability, extensibility
- **Trade-offs:** Longer command strings, all tools must be installed together

**Modular Skill System**
- **Choice:** Independent skill modules with standard structure
- **Rationale:** Extensibility, maintainability, clear boundaries
- **Trade-offs:** More boilerplate, coordination overhead

---

## 6. Architectural Decisions & Rationale

### A. Skills vs Commands Separation

**Decision:** Skills are automatically invoked by Claude based on intent; commands require explicit user invocation with `/` prefix.

**Rationale:**
- Clear separation between AI-driven and user-driven workflows
- Skills enable proactive assistance
- Commands provide explicit control when needed

**Trade-offs:**
- Additional abstraction layer
- More files to maintain
- Learning curve for users

### B. JSON-Only Specification Format

**Decision:** Use JSON exclusively for specifications (deprecated Markdown specs).

**Rationale:**
- Single source of truth
- Schema validation
- Programmatically queryable
- Machine-readable for tools and AI

**Trade-offs:**
- Less human-readable than Markdown
- More verbose
- Requires tools to view/edit effectively

**Constraints:** Must maintain backward compatibility during migration from Markdown to JSON.

### C. Hierarchical Task Structure

**Decision:** Organize tasks as a tree: spec → phases → groups → tasks → subtasks.

**Rationale:**
- Supports complex dependency graphs
- Enables progress rollup
- Provides clear organization
- Allows granular status tracking

**Trade-offs:**
- Increased complexity
- Potential for deep nesting
- More validation rules

**Limitations:** Maximum nesting depth not enforced; large specs can become unwieldy.

### D. Unified CLI Architecture

**Decision:** Single `sdd` entry point with domain-specific subcommands.

**Rationale:**
- Consistent user experience
- Simplified installation
- Easier documentation
- Clear command structure

**Trade-offs:**
- Longer command invocations
- All modules must be installed together
- Heavier initial installation

**Alternatives Considered:** Separate executables per module (rejected due to installation complexity).

### E. Multi-Agent AI Consultation

**Decision:** Consult 2 AI models in parallel for comprehensive analysis.

**Rationale:**
- Higher confidence through consensus
- Diverse perspectives
- Better coverage
- Reduced single-model bias

**Trade-offs:**
- Increased API costs
- Higher latency
- Requires multiple tools installed

**Optimization:** Automatic fallback to single-agent mode if only one tool available.

### F. Filesystem-Based State Management

**Decision:** Store all state in JSON files on the filesystem within `specs/` directory.

**Rationale:**
- Version-controllable with Git
- Transparent and inspectable
- No database setup required
- Portable across environments
- Simple backup and restore

**Trade-offs:**
- No concurrent access support
- Limited query capabilities
- Manual synchronization required
- Performance limitations for large specs

**Future Consideration:** Optional database backend for large teams.

### G. Separation of Concerns

**Decision:** Clear boundaries between skills (instructions), CLI (operations), and hooks (automation).

**Rationale:**
- Maintainability
- Testability
- Reusability
- Independent evolution

**Trade-offs:**
- More files and directories
- Coordination overhead
- Learning curve

---

## 7. System Constraints & Limitations

### Environmental Constraints

**Claude Code Plugin Ecosystem**
- Must work within Claude Code's skill/command/hook framework
- Limited to file-based interactions
- No direct UI beyond chat interface

**Local Environment Dependencies**
- Requires Python 3.9+
- External AI CLIs must be installed separately
- Pytest required for test functionality

### Design Limitations

**Single-User Focus**
- No multi-user collaboration features
- No real-time synchronization
- No conflict resolution for concurrent edits

**Manual Spec Creation**
- Specs must be explicitly created
- No automatic spec generation from code
- Planning overhead required upfront

**No CI/CD Integration**
- No built-in pipeline integration
- No automatic deployment workflows
- Manual integration required

**No Web UI**
- CLI and chat interface only
- Limited visualization capabilities
- No graphical dependency views

### Performance Considerations

**Large Codebase Analysis**
- Tree-sitter parsing can be slow for very large projects
- Multi-agent consultation increases latency
- Documentation generation can take several minutes

**Spec Complexity**
- Deep nesting can impact performance
- Large dependency graphs are computationally expensive to validate
- No pagination for very large specs

---

## 8. Extension Points & Modularity

### Code Organization

**Modular Structure:**
```
src/claude_skills/claude_skills/
├── common/           # Shared utilities (validation, paths, progress, spec loading)
├── sdd_plan/         # Spec creation and templating
├── sdd_next/         # Next-task discovery
├── sdd_update/       # State management and journaling
├── sdd_validate/     # Validation and auto-fix
├── sdd_render/       # Markdown rendering
├── sdd_plan_review/  # Multi-model review
├── code_doc/         # Documentation generation
├── doc_query/        # Documentation querying
└── run_tests/        # Test execution and debugging
```

**Extension Patterns:**

1. **Custom Skills:** Create `~/.claude/skills/my-skill/SKILL.md` with frontmatter and instructions
2. **Custom Commands:** Create `~/.claude/commands/my-command.md` with workflow definition
3. **Custom Hooks:** Create executable script in `~/.claude/hooks/` that reads JSON from stdin
4. **CLI Extensions:** Add module to `src/claude_skills/`, create `cli.py`, register in unified CLI

**Conventions:**
- Use `PrettyPrinter` from common utilities for consistent output
- Use `find_specs_directory()` for path resolution
- Use `load_json_spec()` for spec loading
- Follow argparse patterns for CLI tools
- Write tests in `tests/` directory

---

## 9. Error Handling & Resilience

### Validation Layers

**Multiple Validation Points:**
1. **Schema validation:** JSON structure conforms to expected format
2. **Dependency validation:** No circular dependencies, valid references
3. **State validation:** Status transitions are valid
4. **Path validation:** File paths are normalized and valid

### Error Handling Strategy

**Graceful Degradation:**
- AI tool failures fall back to alternative tools
- Syntax errors skip files and continue processing
- Missing dependencies logged but don't abort

**Clear Error Messages:**
- User-friendly error descriptions
- Actionable remediation steps
- Detailed logging for debugging

**Dry-Run Support:**
- Preview changes before applying
- Validate specs without executing
- Test workflows without side effects

### Resilience Features

**Auto-Fix Capabilities:**
- Common spec errors automatically corrected
- Orphaned tasks reattached
- Missing metadata populated

**State Recovery:**
- Reconcile state files with spec JSON
- Detect and repair inconsistencies
- Backup before destructive operations

---

## 10. Performance Optimizations

### Lazy Loading
- Parse only required files
- Load spec sections on demand
- Cache parsed results

### Parallel Execution
- Multi-agent AI consultations run in parallel
- File parsing can be parallelized
- Independent validations run concurrently

### Incremental Processing
- Only analyze changed files for docs
- Update only affected spec sections
- Recalculate only modified dependencies

### Caching Strategy
- Parsed AST results cached
- Spec metadata cached
- Dependency graphs memoized

---

## Summary

The SDD Toolkit is a comprehensive, layered plugin for Claude Code that enforces spec-driven development through a combination of skills, commands, hooks, and CLI tools. Its architecture emphasizes:

- **Modularity:** Clear separation of concerns with well-defined boundaries
- **Extensibility:** Plugin architecture supports custom skills, commands, and hooks
- **Validation:** Multiple layers ensure data integrity and prevent errors
- **Transparency:** Filesystem-based state is inspectable and version-controlled
- **AI Integration:** Multi-model consultation for comprehensive analysis
- **Developer Experience:** Unified CLI interface with consistent conventions

The system makes deliberate trade-offs, prioritizing simplicity and transparency over features like real-time collaboration and web UI. This design is well-suited for individual developers and small teams working with AI assistants on complex projects where systematic planning and progress tracking are essential.
