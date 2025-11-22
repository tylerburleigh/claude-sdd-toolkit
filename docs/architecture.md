# Architecture

System architecture and design patterns for the SDD Toolkit.

## Table of Contents

- [Overview](#overview)
- [Project Statistics](#project-statistics)
- [Architectural Patterns](#architectural-patterns)
- [Modular Skill-Based Design](#modular-skill-based-design)
- [Provider Abstraction Layer](#provider-abstraction-layer)
- [Data Flow](#data-flow)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)

---

## Overview

The SDD Toolkit is a Python-based CLI and library for Spec-Driven Development, enabling AI-assisted software engineering. The architecture centers around machine-readable JSON specifications that define tasks, dependencies, and track progress.

**Key Characteristics:**
- High modularity through skill-based design
- Extensibility via plugin architecture
- Robust AI provider abstraction
- Declarative state management with JSON specs
- Powerful, configurable CLI

---

## Project Statistics

**Codebase Metrics:**
- **183 Python modules**
- **154 classes**
- **915 functions**
- **72,268 lines of code**
- **Average complexity:** 6.93

**Primary Languages:**
- Python 3.9+ (core toolkit)
- JavaScript (OpenCode provider integration)

---

## Architectural Patterns

### 1. Modular Monolith

**Description:** Single codebase with internal modularity

**Implementation:**
- All functionalities bundled in `src/claude_skills` package
- Deployed as single Python package
- Logically separated into independent modules

**Benefits:**
- Simplified development, testing, deployment
- Clear separation of concerns
- Avoids "big ball of mud" anti-pattern

---

### 2. Plugin Architecture (Skills)

**Description:** Independent, composable skill modules

**Implementation:**
- Each skill is self-contained module
- Skills directory structure:
  ```
  skills/
  ├── sdd-plan/
  ├── sdd-next/
  ├── doc-query/
  ├── llm-doc-gen/
  └── common/
  ```

**Benefits:**
- Independent development and testing
- Easy feature extension
- Flexible, composable workflows

**See:** [Advanced Topics - Extension Points](advanced-topics.md#extension-points)

---

### 3. Layered Architecture

**Presentation Layer:**
- CLI interface (`sdd` command)
- Output formatting (rich/plain/json)
- Located in `src/claude_skills/cli/`

**Application Layer:**
- Skill modules (sdd-plan, sdd-next, etc.)
- Task orchestration
- AI consultation logic
- Subagent system

**Infrastructure Layer:**
- AI configuration
- Provider abstraction
- Caching
- File I/O
- Template system
- Located in `src/claude_skills/common/`

**Benefits:**
- Strong separation of concerns
- Isolated changes (new provider doesn't affect UI)
- Easier testing and maintenance

---

### 4. Client-Server (Conceptual)

**Client:** Claude Code or terminal
**Server:** SDD CLI

**Interaction Flow:**
```
Claude Code
    ↓ (command)
  SDD CLI
    ↓ (execute)
  Operations (read specs, call AI, analyze code)
    ↓ (results)
  Claude Code
```

**Benefits:**
- Clear interaction boundary
- Supports multiple clients (Claude Code, terminal, scripts)
- Flexible integration models

---

## Modular Skill-Based Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Skill Architecture                         │
└─────────────────────────────────────────────────────────────────┘

         Core Workflow Skills (Main)
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  sdd-plan    │  │  sdd-next    │  │  sdd-update  │
│              │  │              │  │              │
│  Create      │  │  Orchestrate │  │  Track       │
│  Specs       │  │  Tasks       │  │  Progress    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼────┐     ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│ code-  │     │    doc-   │   │ llm-doc-  │   │   run-    │
│ doc    │     │   query   │   │   gen     │   │   tests   │
│        │     │           │   │           │   │           │
│ Docs   │     │  Analyze  │   │  AI Docs  │   │  Testing  │
└───┬────┘     └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
    │                │               │               │
    └────────────────┴───────────────┴───────────────┘
                         │
              Supporting Skills
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼──────────┐  ┌──────▼──────┐   ┌────────▼──────┐
│ sdd-validate │  │ sdd-fidelity│   │ sdd-plan-     │
│ sdd-render   │  │    -review  │   │    review     │
│ sdd-modify   │  │             │   │               │
└──────────────┘  └─────────────┘   └───────────────┘
                         │
                  ┌──────▼──────┐
                  │   common    │
                  │             │
                  │  Shared     │
                  │  Utilities  │
                  └─────────────┘
```

### Skill Categories

**Core Workflow:**
- **sdd-plan** - Specification creation
- **sdd-next** - Task orchestration
- **sdd-update** - Progress tracking

**Documentation & Analysis:**
- **doc-query** - Code queries
- **llm-doc-gen** - AI documentation

**Quality Assurance:**
- **sdd-validate** - Spec validation
- **sdd-fidelity-review** - Implementation verification
- **sdd-plan-review** - Multi-model review
- **sdd-modify** - Spec modifications

**Testing:**
- **run-tests** - Test execution with AI debugging

**Utilities:**
- **sdd-render** - Human-readable output
- **sdd-pr** - Pull request creation

---

## Provider Abstraction Layer

### Architecture

```
         Skills
           ↓
   ProviderContext (Abstract)
           ↓
    ┌──────┴──────┐
    │             │
┌───▼───┐   ┌─────▼─────┐
│Gemini │   │  Cursor   │
│       │   │  Agent    │
└───────┘   └───────────┘
    │             │
┌───▼───┐   ┌─────▼─────┐
│Codex  │   │  Claude   │
│       │   │(read-only)│
└───────┘   └───────────┘
    │
┌───▼────┐
│OpenCode│
│        │
└────────┘
```

### Provider Features

| Provider | Models | Tool Support | Security |
|----------|--------|--------------|----------|
| **Gemini** | Pro, Flash | No | Full access |
| **Cursor** | Composer 1M | Yes | Full access |
| **Codex** | Sonnet, Haiku | No | Full access |
| **Claude** | Sonnet, Haiku | Limited | Read-only |
| **OpenCode** | Various | Yes | Read-only |

**Read-Only Mode:**
- ✅ Allowed: Read, Grep, Glob, WebSearch
- ❌ Blocked: Write, Edit, Bash

**See:** [Advanced Topics - Provider Abstraction](advanced-topics.md#provider-abstraction-layer)

---

## Data Flow

### Primary State: JSON Specifications

```
specs/
├── pending/      # Planned work
├── active/       # Current implementation
├── completed/    # Finished features
└── archived/     # Cancelled work
```

### Lifecycle

```
Plan → Validate → Activate → Implement → Track → Review → Complete
  ↓        ↓          ↓           ↓         ↓        ↓         ↓
sdd-plan  validate  activate  sdd-next  update  fidelity    archive
```

### Integration Flow

```
User Request
    ↓
Claude Code (Skills)
    ↓
Python CLI (sdd commands)
    ↓
Operations (spec I/O, AI calls, code analysis)
    ↓
Results
    ↓
Claude Code (Next Steps)
```

---

## Project Structure

### Repository Layout

```
claude-sdd-toolkit/
├── skills/                          # Claude Code skills
│   ├── sdd-plan/
│   ├── sdd-next/
│   ├── doc-query/
│   └── common/
│
├── src/claude_skills/               # Python package
│   ├── sdd_plan/                    # Skill implementations
│   ├── sdd_next/
│   ├── doc_query/
│   ├── llm_doc_gen/
│   ├── run_tests/
│   ├── common/                      # Shared utilities
│   │   ├── providers/               # AI provider abstraction
│   │   ├── ai_config.py
│   │   ├── cache.py
│   │   ├── spec.py
│   │   └── templates/
│   └── cli/                         # CLI entry points
│
├── tests/                           # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                            # Documentation
│   ├── core-concepts.md
│   ├── skills-reference.md
│   ├── workflows.md
│   ├── configuration.md
│   └── architecture.md (this file)
│
├── specs/                           # Specification examples
│   ├── pending/
│   ├── active/
│   └── completed/
│
└── README.md
```

### User Project Structure

```
your-project/
├── specs/
│   ├── pending/
│   ├── active/
│   ├── completed/
│   ├── archived/
│   ├── .reports/        # Gitignored
│   ├── .reviews/        # Gitignored
│   └── .backups/        # Gitignored
│
├── .claude/
│   ├── settings.local.json
│   ├── sdd_config.json
│   └── ai_config.yaml
│
├── docs/                # Optional
│   ├── codebase.json
│   └── index.md
│
└── [source code]
```

---

## Technology Stack

### Core Technologies

**Python 3.9+**
- Modern async/await
- Type hints
- Standard library utilities

**Key Libraries:**
- **Rich** - Terminal UI (colors, tables, progress)
- **tree-sitter** - AST parsing (Python, JavaScript, TypeScript)
- **JSON Schema** - Spec validation
- **pytest** - Testing framework

### AI Integration

**External CLIs:**
- `gemini` - Google Gemini
- `cursor-agent` - Cursor Composer
- `codex` - Anthropic Codex
- `claude` - Claude API
- `opencode` - OpenCode AI (Node.js)

**Integration Method:**
```python
# Subprocess-based CLI calls
result = subprocess.run([provider, prompt], capture_output=True)
```

### File Formats

**Specifications:**
- JSON with JSON Schema validation
- Git-trackable version control

**Documentation:**
- Markdown (human-readable)
- JSON (machine-readable)

**Configuration:**
- JSON (CLI settings)
- YAML (AI configuration)

---

## Related Documentation

- [Core Concepts](core-concepts.md) - Fundamental concepts
- [Advanced Topics](advanced-topics.md) - Design patterns and extension points
- [Skills Reference](skills-reference.md) - Skill documentation
- [Configuration](configuration.md) - Configuration options

---

*Last updated: 2025-11-22*