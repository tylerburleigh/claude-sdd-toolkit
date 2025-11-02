# Claude SDD Toolkit - Architecture Documentation

**Version:** 0.4.0
**Generated:** 2025-11-02

This document provides a comprehensive architectural overview of the Claude SDD Toolkit, synthesized from multiple AI model analyses (Gemini and Codex).

---

## System Overview

The Claude SDD Toolkit is a Python-based command-line interface designed to facilitate **Spec-Driven Development (SDD)**—a methodology that structures the entire software development lifecycle around machine-readable JSON specification files. The toolkit provides a suite of modular "skills" that enable developers, particularly those working with the Claude AI assistant, to adopt a systematic, plan-first approach to software development.

### Core Purpose

The toolkit solves the problem of unstructured, ad-hoc development by:
- **Enforcing explicit task definitions** with dependencies and status tracking
- **Maintaining a single source of truth** through version-controlled JSON specs
- **Providing AI-assisted insights** via integration with external AI models
- **Automating documentation** and codebase analysis
- **Tracking progress** with detailed journaling and metrics

### Target Users

Software developers using Claude AI who want to:
- Maintain high organization and structure in their development process
- Leverage AI assistance within defined "guardrails"
- Track tasks, dependencies, and progress systematically
- Generate and maintain comprehensive code documentation

---

## High-Level Architecture

### Architectural Style

The toolkit follows a **modular CLI architecture** with:
- **Unified entry point** (`sdd` command) that dispatches to specialized skills
- **Plugin-style registry** for extensible skill loading
- **File-based state management** using JSON specs on the filesystem
- **External AI tool integration** via subprocess orchestration

### Key Architectural Decisions

1. **JSON as Single Source of Truth**
   - All task information centralized in version-controlled JSON files
   - Minimizes ambiguity and makes state changes explicit and auditable
   - Enables git-based collaboration and change tracking

2. **Modular "Skills" Architecture**
   - Each skill is a self-contained module with its own CLI
   - New capabilities can be added without disrupting existing functionality
   - Clear separation of concerns across the toolkit

3. **Filesystem-Based State Management**
   - No database required—all state lives in the filesystem
   - Specs can be versioned alongside code in git
   - Directory conventions (`specs/active/`, `specs/completed/`) enforce workflow structure
   - Trade-off: Potential merge conflicts in concurrent scenarios

4. **Delegation to External AI Tools**
   - Orchestrates external AI CLIs (gemini, codex, cursor-agent) rather than implementing AI internally
   - Focuses on workflow management as core competency
   - Allows leveraging specialized, powerful AI tools
   - Opportunistic integration: Commands detect available tools and gracefully degrade

5. **Append-Only Metrics and Telemetry**
   - Durability-focused approach using JSONL format
   - Test environment suppression to avoid noise
   - Rotation and cleanup for long-running systems

---

## Component Architecture

### 1. CLI Layer

**Location:** `src/claude_skills/claude_skills/cli/sdd/`

**Key Files:**
- `__init__.py:16` - Main entry point, reorders global flags and dispatches to subcommands
- `registry.py:18` - Registers all skills into nested subparsers

**Responsibilities:**
- Unified command dispatch via `sdd` CLI
- Argument parsing and validation
- Pretty-printing configuration
- Telemetry logging

**Design Patterns:**
- **Facade Pattern:** Single interface to rich underlying functionality
- **Command Pattern:** Each subcommand encapsulates a specific action
- **Plugin Registry:** Modular skill loading via `register_*` hooks

---

### 2. Core Skills

#### **sdd-plan** - Specification Creation

**Location:** `src/claude_skills/claude_skills/sdd_plan/`

**Purpose:** Create new development specifications from templates

**Key Operations:**
- `sdd create <feature-name>` - Bootstrap new spec in `specs/pending/`
- Template-based spec generation
- Entry point for all new development work

**Data Flow:**
1. User invokes `sdd create`
2. Template loaded from common templates
3. New JSON spec written to `specs/pending/`
4. Spec ID returned to user

---

#### **sdd-validate** - Specification Validation

**Location:** `src/claude_skills/claude_skills/sdd_validate/`

**Purpose:** Ensure spec integrity and prevent workflow-breaking errors

**Key Operations:**
- Schema validation against JSON schema
- Circular dependency detection
- Hierarchy consistency checks
- Auto-fix capabilities for common issues

**Design Pattern:** **Validator Pattern** with configurable rules

---

#### **sdd-next** - Task Discovery and Preparation

**Location:** `src/claude_skills/claude_skills/sdd_next/`

**Key Files:**
- `cli.py:600` - `next-task` command
- `cli.py:709` - `prepare-task` command with doc integration

**Purpose:** Identify the next actionable task and provide execution context

**Key Operations:**
- Analyze dependencies to find unblocked tasks
- Aggregate spec data, dependency analysis, and codebase context
- Generate detailed implementation guidance

**Data Flow:**
1. Read active spec from `specs/active/`
2. Compute dependency graph
3. Filter for pending/in-progress tasks with satisfied dependencies
4. Optionally query `doc-query` for relevant codebase context
5. Return structured execution plan

**Integration:** Deep integration with `doc-query` for context enrichment

---

#### **sdd-update** - State Management

**Location:** `src/claude_skills/claude_skills/sdd_update/`

**Key Files:**
- `cli.py:50` - Main update operations
- `cli.py:166` - Spec mutation workflows

**Purpose:** Manage spec lifecycle and task state transitions

**Key Operations:**
- `update-status` - Change task status (pending → in_progress → completed)
- `add-journal` - Append decision logs and notes
- `activate-spec` - Move spec from pending to active
- `complete-spec` - Archive completed spec
- `list-specs` - List specs by status
- `execute-verify` - Run verification tasks

**Workflow Pattern:**
```
specs/pending/ → [activate-spec] → specs/active/ → [complete-spec] → specs/completed/
```

---

#### **sdd-render** - Specification Rendering

**Location:** `src/claude_skills/claude_skills/sdd_render/`

**Key Features:**
- Three rendering modes: basic (fast), enhanced (AI-powered)
- Three enhancement levels: summary, standard, full
- AI-powered executive summaries
- Dependency graph visualization (Mermaid)
- Progressive disclosure with collapsible sections
- Complexity scoring and priority ranking

**Architecture:**
- **Orchestrator Pattern:** `AIEnhancedRenderer` coordinates 4-stage pipeline
- **Strategy Pattern:** Pluggable rendering strategies (basic vs. enhanced)
- Multi-agent AI consultation for comprehensive analysis

---

#### **sdd-plan-review** - AI-Assisted Spec Review

**Location:** `src/claude_skills/claude_skills/sdd_plan_review/`

**Purpose:** Multi-model spec review for quality assurance

**Key Operations:**
- Parallel consultation with 2+ AI models
- Architecture, security, and feasibility analysis
- Actionable feedback generation

**Design Pattern:** **Strategy Pattern** with AI tool selection

---

### 3. Documentation System

#### **code-doc** - Documentation Generation

**Location:** `src/claude_skills/claude_skills/code_doc/`

**Key Files:**
- `cli.py:108` - Main documentation commands
- `generator.py:36` - Multi-language parser orchestration
- `generator.py:60` - Statistics computation
- `generator.py:113` - Markdown/JSON persistence

**Purpose:** Generate structural and AI-enhanced codebase documentation

**Supported Languages:**
- Python, JavaScript/TypeScript, Go, HTML, CSS

**Outputs:**
- `DOCUMENTATION.md` - Human-readable reference
- `documentation.json` - Machine-readable data
- `ARCHITECTURE.md` - AI-synthesized architecture docs (with `analyze-with-ai`)
- `AI_CONTEXT.md` - AI assistant quick reference (with `analyze-with-ai`)

**Architecture:**
- **Factory Pattern:** Language-specific parser selection
- **Orchestrator Pattern:** Multi-stage documentation pipeline
- **Multi-agent AI consultation** for enhanced documentation

---

#### **doc-query** - Documentation Query Engine

**Location:** `src/claude_skills/claude_skills/doc_query/`

**Key Files:**
- `cli.py:58` - Query operation dispatch
- `cli.py:69` - Freshness checks
- `cli.py:90` - Auto-regeneration
- `cli.py:100` - Structured result formatting

**Purpose:** Query generated documentation to provide context for development tasks

**Key Operations:**
- Search classes, functions, modules
- Find high-complexity code
- Trace dependencies
- Gather feature area context

**Design Pattern:** **Proxy Pattern** - Ensures doc freshness by regenerating when stale

**Integration Point:** Critical for `sdd-next` context enrichment

---

### 4. Testing Infrastructure

#### **run-tests** - Test Execution and AI Debugging

**Location:** `src/claude_skills/claude_skills/run_tests/`

**Key Files:**
- `cli.py:55` - Test runner coordination
- `cli.py:67` - AI consultation for debugging

**Purpose:** pytest integration with AI-assisted failure analysis

**Features:**
- Test discovery and preset management
- Parallel AI consultation for debugging
- Systematic failure investigation

---

### 5. Support Systems

#### **context-tracker** - Token Usage Monitoring

**Location:** `src/claude_skills/claude_skills/context_tracker/`

**Key Files:**
- `cli.py:142` - Transcript analysis

**Purpose:** Monitor Claude AI token usage to prevent context window overflow

**Data Source:** Claude transcript JSONL files from `~/.claude`

---

#### **Common Utilities**

**Location:** `src/claude_skills/claude_skills/common/`

**Key Modules:**
- `__init__.py:10` - Shared exports
- `printer.py:12` - `PrettyPrinter` facade for consistent output styling
- `metrics.py:74` - Telemetry and usage tracking
- `spec.py` - Spec file I/O operations
- `validation.py` - Shared validation logic
- `ai_config.py` - Unified AI tool configuration (NEW in v0.4.0)
- `paths.py` - Path discovery utilities
- `dependency_analysis.py` - Dependency graph operations

**Design Pattern:** **Facade Pattern** (`PrettyPrinter`) centralizes output formatting

---

## Data Flow Architecture

### Primary Workflow: Spec-Driven Development Lifecycle

```
1. CREATE
   sdd create → specs/pending/<spec-id>.json

2. VALIDATE & REVIEW
   sdd validate → Check integrity
   sdd plan-review → AI quality assurance

3. ACTIVATE
   sdd activate-spec → Move to specs/active/

4. EXECUTE LOOP
   while tasks remaining:
     sdd next-task → Identify next task
     sdd prepare-task → Get context (integrates doc-query)
     [Developer implements]
     sdd complete-task → Update status + journal

5. COMPLETE
   sdd complete-spec → Move to specs/completed/
```

### Secondary Workflow: Documentation-Driven Context

```
1. GENERATE DOCS
   sdd doc analyze-with-ai → Parallel AI consultation
     ↓
   DOCUMENTATION.md + documentation.json (structural)
   ARCHITECTURE.md + AI_CONTEXT.md (synthesized)

2. QUERY DOCS
   sdd doc <query-cmd> → Fast lookups
     ↓
   Used by sdd-next for task context enrichment
```

### Data Persistence

- **Specs:** `specs/[pending|active|completed]/<spec-id>.json`
- **Documentation:** `docs/DOCUMENTATION.md`, `docs/documentation.json`
- **Rendered Specs:** `.human-readable/<spec-id>.md`
- **Reviews:** `.reviews/<spec-id>-review-<timestamp>.md`
- **Metrics:** `~/.claude-skills/metrics.jsonl` (append-only)
- **Transcripts:** `~/.claude/sessions/<session-id>/transcript_*`

---

## Design Patterns Summary

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Command** | CLI layer | Encapsulate actions as subcommands |
| **Facade** | `PrettyPrinter` | Unified output interface |
| **Factory** | `code_doc` parsers | Language-specific parser creation |
| **Orchestrator** | `code_doc`, `sdd_render` | Multi-stage pipeline coordination |
| **Strategy** | `sdd_render`, `sdd_plan_review` | Pluggable algorithms (rendering modes, AI tools) |
| **Proxy** | `doc_query` | Lazy doc regeneration with freshness checks |
| **Plugin Registry** | Skill registration | Modular skill loading |
| **Decorator** | Metrics collection | Non-invasive telemetry wrapping |

---

## Technology Stack

### Core Technologies

- **Python 3.9+** - Primary implementation language
- **argparse** - CLI framework
- **pathlib** - Modern path handling
- **json** / **jsonschema** - Spec and doc validation

### Optional Dependencies

- **tree-sitter** family - Multi-language AST parsing
  - `tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`
  - `tree-sitter-go`, `tree-sitter-html`, `tree-sitter-css`
- **pytest** - Test framework integration
- **External AI CLIs:**
  - `gemini` - Fast structured analysis
  - `codex` - Code understanding
  - `cursor-agent` (with cheetah model) - Large codebase analysis (1M context)

### Rationale

- **Python:** Ideal for CLI tooling, strong standard library, excellent for developer tools
- **JSON:** Machine-readable, human-editable, language-agnostic, git-friendly
- **Filesystem state:** Simplifies architecture, eliminates database dependency, enables version control
- **External AI integration:** Leverages specialized tools, maintains focus on workflow management
- **tree-sitter:** Robust, language-agnostic AST parsing

---

## Architectural Trade-offs

### Strengths

✅ **Simplicity:** No database, no server, pure filesystem operations
✅ **Version control friendly:** Specs live alongside code in git
✅ **Extensibility:** Plugin architecture for easy skill additions
✅ **Portability:** Pure Python, runs anywhere with Python 3.9+
✅ **Offline-capable:** Core functionality works without network (AI features optional)
✅ **Explicit state:** JSON specs make all task information visible and auditable

### Limitations

⚠️ **Concurrency:** File-based state may conflict with multiple simultaneous users (requires git merge discipline)
⚠️ **AI dependency:** Enhanced features require external AI CLI tools to be installed and configured
⚠️ **Directory conventions:** Enforced structure (`specs/active/`, etc.) must be adopted
⚠️ **Workflow rigidity:** SDD methodology adds overhead, trading flexibility for structure
⚠️ **External tool quality:** AI features depend entirely on third-party tool performance

---

## Extension Points

### Adding New Skills

1. Create skill directory: `src/claude_skills/claude_skills/<skill_name>/`
2. Implement `cli.py` with `register_<skill_name>(subparsers)` function
3. Add registration call in `cli/sdd/registry.py:register_all_subcommands`
4. Follow common patterns:
   - Use `PrettyPrinter` for output
   - Emit metrics via `@track_command_usage` decorator
   - Leverage common utilities (`spec.py`, `validation.py`, etc.)

### Adding AI Tool Support

1. Add tool configuration in `common/ai_config.py`
2. Implement subprocess orchestration following existing patterns
3. Add fallback logic for tool unavailability
4. Document tool requirements in skill documentation

### Adding Language Support (code-doc)

1. Add tree-sitter language dependency
2. Create parser in `code_doc/parsers/<language>.py`
3. Register in parser factory (`code_doc/parsers/factory.py`)
4. Follow `BaseParser` interface

---

## Security and Reliability

### Security Measures

- **No code execution from specs:** Specs are declarative data, not executable code
- **Subprocess sandboxing:** External tools invoked with timeouts
- **Path validation:** All file operations validate paths are within project
- **Schema validation:** JSON specs validated before processing

### Reliability Features

- **Auto-fix validation:** `sdd-validate` can repair common spec errors
- **Graceful degradation:** AI features fall back to structural-only output
- **Append-only metrics:** Durable telemetry with rotation
- **Test coverage:** Unit and integration tests for core functionality

---

## Performance Characteristics

### Fast Operations (< 1s)

- Spec validation
- Task status updates
- Documentation queries (with cached docs)
- Next task identification

### Moderate Operations (1-30s)

- Basic spec rendering
- Code documentation generation (small projects)
- Test execution (depends on test suite)

### Slow Operations (30s - 5min)

- AI-enhanced rendering (standard: ~60s, full: ~90s)
- AI-assisted code documentation (multi-agent: ~5min)
- Multi-model spec reviews (parallel, ~2-3min)

### Optimization Strategies

- **Caching:** Documentation queries check freshness, avoid unnecessary regeneration
- **Parallel AI consultation:** Multiple models queried simultaneously
- **Progressive enhancement:** Three rendering levels (summary/standard/full) balance speed vs. features
- **Lazy loading:** Context only gathered when explicitly requested

---

## Future Architectural Considerations

### Potential Enhancements

- **Concurrent access:** File-locking or operational transformation for multi-user scenarios
- **Cloud sync:** Optional backend for team collaboration
- **Web UI:** Visual spec editor and dashboard
- **Webhook integration:** CI/CD pipeline triggers
- **Plugin marketplace:** Community-contributed skills

### Backward Compatibility

- JSON schema versioning for spec evolution
- Graceful handling of legacy spec formats
- Deprecation warnings for old CLI flags

---

## Conclusion

The Claude SDD Toolkit's architecture reflects a deliberate choice to prioritize **simplicity, portability, and extensibility** over complex infrastructure. By embracing filesystem-based state, modular skills, and external AI tool orchestration, the toolkit provides a powerful yet accessible framework for spec-driven development that scales from individual developers to small teams.

The plugin-style architecture ensures that new capabilities can be added without disrupting existing workflows, while the JSON-based specs provide a clear, version-controllable contract between planning and execution. This architecture enables developers to harness AI assistance within well-defined guardrails, maintaining both structure and flexibility throughout the development lifecycle.
