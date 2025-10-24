# claude-sdd-toolkit - Architecture Documentation

**Version:** 1.0.0
**Generated:** 2025-10-24 10:59:17

---

## Introduction

This document describes the architecture of the codebase, including system design,
component structure, data flow, and key design decisions.

---

## Architecture Analysis


# Architecture Research Findings

## 1. System Overview

The SDD Toolkit is a Python library for Spec-Driven Development (SDD) in Claude Code. It provides a plan-first workflow: create structured specs, identify next tasks, track progress, and validate specs. It also includes documentation generation/querying and test execution/debugging.

Intended users: developers using Claude Code for AI-assisted development.

Problem solved: reduces AI coding errors, prevents context drift, and keeps implementations aligned with intent.

## 2. Component Identification

### Core Components

**1. Unified CLI System** (`src/claude_skills/cli/sdd/`)
- Single entry point (`sdd`) with subcommands
- Registry pattern for plugin registration
- Global options (`--json`, `--verbose`, `--quiet`, `--debug`)
- Parent parser for shared options

**2. Common Utilities** (`src/claude_skills/common/`)
- Spec operations: load/save JSON specs, backup, node operations
- Progress: recalculation, parent status updates, summaries
- Path utilities: discovery, validation, normalization
- Validation: hierarchy, structure, dependencies, metadata
- Dependency analysis: cycles, deadlocks, bottlenecks
- Query operations: task queries, phase listing, blockers
- Metrics: collection and tracking
- Documentation helpers: doc-query integration
- Cross-skill integrations: spec validation, verify task execution

**3. SDD Core Skills**

**sdd-plan** (`src/claude_skills/sdd_plan/`)
- Creates JSON specs with phases, tasks, dependencies
- Templates (simple, medium, complex, security)
- Codebase analysis for planning

**sdd-next** (`src/claude_skills/sdd_next/`)
- Finds next actionable tasks
- Prepares execution plans
- Checks dependencies and readiness
- Integrates with doc-query for context

**sdd-update** (`src/claude_skills/sdd_update/`)
- Updates task status
- Journals decisions
- Tracks time
- Manages spec lifecycle
- Records verification results

**sdd-validate** (`src/claude_skills/sdd_validate/`)
- Validates JSON spec structure
- Auto-fixes common issues
- Generates reports
- Analyzes dependencies

**sdd-plan-review** (`src/claude_skills/sdd_plan_review/`)
- Multi-model spec review
- Consensus synthesis
- Markdown/JSON reports

**4. Documentation Tools**

**code-doc** (`src/claude_skills/code_doc/`)
- Generates codebase docs (Markdown/JSON)
- Multi-language parsing (Python, JavaScript, TypeScript, Go, HTML, CSS)
- AI-assisted docs (optional)
- Complexity analysis

**doc-query** (`src/claude_skills/doc_query/`)
- Queries generated docs
- Finds classes, functions, modules
- Complexity analysis
- Dependency mapping

**5. Testing Tools**

**run-tests** (`src/claude_skills/run_tests/`)
- Pytest runner with presets
- Test discovery
- AI consultation for debugging
- Multi-agent consensus
- Tool availability checking

**6. Development Tools** (`src/claude_skills/dev_tools/`)
- Session management
- Permission setup
- Documentation generation

### Key Relationships

```
Unified CLI (sdd)
    ├── SDD Core Skills (plan, next, update, validate, review)
    ├── Documentation (doc generate, doc query)
    ├── Testing (test run, test consult)
    └── Dev Tools (skills-dev)
    
Common Utilities
    ├── Used by all SDD skills
    ├── Provides shared operations
    └── Enables cross-skill integration
```

## 3. Data Flow Observations

### Request/Response Lifecycle

1. User invokes a skill or command
2. CLI parses arguments and routes to a handler
3. Handler uses common utilities to load specs/docs
4. Business logic runs
5. Results formatted (JSON or human-readable)
6. Exit code returned

### State Management

- JSON specs in `specs/active/`, `specs/completed/`, `specs/archived/`
- Docs in `docs/documentation.json`
- Metrics in `.claude/metrics/`
- No database; file-based

### Data Flow Example: Creating and Executing a Spec

```
1. User: "Create spec for user authentication"
   ↓
2. Skill(sdd-plan) invoked
   ↓
3. sdd-plan analyzes codebase (uses doc-query if available)
   ↓
4. Creates JSON spec file: specs/active/user-auth-001.json
   ↓
5. Validates spec: sdd validate
   ↓
6. User: "What should I work on next?"
   ↓
7. Skill(sdd-next) invoked
   ↓
8. Loads JSON spec, finds next task
   ↓
9. Creates execution plan with context
   ↓
10. User implements task
    ↓
11. Skill(sdd-update) marks task complete
    ↓
12. Updates progress in JSON spec
    ↓
13. Cycle repeats until spec complete
```

## 4. Design Patterns Detected

### 1. Registry Pattern
- Location: `src/claude_skills/cli/sdd/registry.py`
- Purpose: Register subcommands
- Why: Extensible without modifying core CLI

### 2. Command Pattern
- Location: CLI handlers
- Purpose: Encapsulate operations
- Why: Consistent interface and composability

### 3. Strategy Pattern
- Location: AI consultation routing (`run_tests/consultation.py`)
- Purpose: Select AI tool by failure type
- Why: Flexible tool selection

### 4. Template Method Pattern
- Location: Spec generation templates (`sdd_plan/templates.py`)
- Purpose: Reusable spec structures
- Why: Consistent outputs

### 5. Visitor Pattern
- Location: Hierarchy validation (`common/hierarchy_validation.py`)
- Purpose: Traverse and validate spec hierarchy
- Why: Separation of traversal and validation

### 6. Factory Pattern
- Location: Parser factory (`code_doc/parsers/`)
- Purpose: Create language-specific parsers
- Why: Extensible language support

### 7. Facade Pattern
- Location: Unified CLI (`cli/sdd/__init__.py`)
- Purpose: Single interface to subsystems
- Why: Simpler API

## 5. Technology Stack Analysis

### Core Technologies

**Python 3.9+**
- Language
- Why: CLI tools, parsing, JSON handling

**tree-sitter** (>=0.20.0)
- Multi-language parsing
- Why: Fast, accurate parsing

**Language Parsers**
- tree-sitter-python, tree-sitter-javascript, tree-sitter-typescript, tree-sitter-go, tree-sitter-html, tree-sitter-css
- Why: Language-specific AST parsing

### Key Dependencies

**argparse**
- CLI argument parsing
- Why: Standard library, flexible

**json**
- Spec and doc serialization
- Why: Standard library, portable

**pathlib**
- Path operations
- Why: Cross-platform, modern API

**pytest** (optional)
- Testing
- Why: Common Python testing framework

### External Tool Integration

**AI CLI Tools** (optional)
- gemini, codex, cursor-agent
- Why: Multi-model reviews and debugging

## 6. Architectural Decisions

### 1. Unified CLI Architecture
- Decision: Single `sdd` entry point with subcommands
- Trade-off: Simpler UX vs. more complex routing
- Rationale: Consistent interface, easier discovery

### 2. JSON as Single Source of Truth
- Decision: JSON specs, not Markdown
- Trade-off: Less readable vs. machine-processable
- Rationale: Enables automation and validation

### 3. File-Based State Management
- Decision: No database
- Trade-off: Simpler vs. limited concurrency
- Rationale: Version control friendly, portable

### 4. Plugin Architecture
- Decision: Registry-based subcommand registration
- Trade-off: More setup vs. extensibility
- Rationale: Easy to add skills without core changes

### 5. Common Utilities Module
- Decision: Shared utilities across skills
- Trade-off: Coupling vs. DRY
- Rationale: Consistency and maintainability

### 6. Multi-Agent AI Consultation
- Decision: Optional multi-model reviews
- Trade-off: Higher cost vs. better quality
- Rationale: Higher confidence for critical specs

### 7. Staged Planning Approach
- Decision: Optional phase-only planning before detailed tasks
- Trade-off: Extra step vs. early feedback
- Rationale: Reduces rework

### 8. Documentation-First Analysis
- Decision: Generate docs before planning
- Trade-off: Initial cost vs. faster analysis
- Rationale: 10x faster codebase analysis

### Notable Constraints

1. Python 3.9+ required
2. tree-sitter parsers needed for code analysis
3. File-based state limits concurrent access
4. JSON specs must be valid
5. External AI tools optional but recommended

### Limitations

1. No real-time collaboration
2. No built-in version control integration
3. Limited to supported languages
4. No GUI
5. No cloud sync

---

## Summary

The SDD Toolkit uses a unified CLI with a plugin registry, shared utilities, and JSON-based state. It supports plan-first workflows, documentation generation, and test execution. The design favors extensibility, consistency, and automation over complexity.


---

*This documentation was generated with assistance from AI analysis.*