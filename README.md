# SDD Toolkit

> Spec-Driven Development: Structured, trackable AI-assisted development through machine-readable specifications

[![Plugin Version](https://img.shields.io/badge/version-0.7.7-blue.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)]()
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()

## What & Why

**The Problem:**
AI-assisted development without structure leads to scope drift, lost context, unclear progress, and difficulty resuming work after interruptions.

**The Solution:**
SDD Toolkit provides a plan-first methodology using machine-readable JSON specifications. Each feature is broken into atomic tasks with dependency tracking, automatic progress recording, and built-in verification.

**The Outcome:**
Systematic development where AI understands the full plan, tracks what's done, knows what's next, and can resume work seamlessly after context clears or session breaks.

**Architecture:**
183 Python modules, 154 classes, and 915 functions organized into independent, composable skills. Claude skills orchestrate workflows, Python CLI executes operations, results inform next steps.

## Quick Start

### Installation

1. **Install Plugin:**
   ```
   claude  # Launch Claude Code
   /plugin → Add from marketplace → tylerburleigh/claude-sdd-toolkit
   ```

2. **Install Dependencies:**
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   sdd skills-dev install  # Installs pip and npm dependencies
   ```

3. **Restart Claude Code**, then **Configure Project:**
   ```
   /sdd-setup
   ```

**Requirements:** Python 3.9+, Node.js >= 18.x. See [Getting Started](docs/getting-started.md) for detailed instructions.

### First Workflow

```
You: Create a spec for a CLI Pomodoro timer

Claude: [Analyzes codebase, creates specs/pending/pomodoro-timer-001.json]

You: /sdd-begin

Claude: Found pending spec "pomodoro-timer-001"
        Ready to activate and start implementing?

You: Yes

Claude: [Moves to specs/active/, starts first task]
        Task 1-1: Create Timer class with start/pause/stop methods
        [Implements task, updates status]

You: /sdd-begin

Claude: Task 1-2: Add notification system...
        [Continues through tasks]
```

## How It Works

### Specifications: Machine-Readable Plans

Specs are JSON files defining features as tasks with dependencies:

```json
{
  "metadata": {
    "name": "User Authentication",
    "version": "1.0.0"
  },
  "phases": [
    {
      "id": "phase-1",
      "title": "Core Auth System",
      "tasks": [...]
    }
  ],
  "tasks": [
    {
      "id": "task-1-1",
      "title": "Create User model",
      "dependencies": [],
      "status": "pending",
      "verification": ["Model validates email", "Password hashing works"]
    }
  ]
}
```

**Lifecycle folders:**
- `specs/pending/` - Planned work
- `specs/active/` - Current implementation
- `specs/completed/` - Finished features
- `specs/archived/` - Cancelled work

All specs are Git-trackable. Validated against JSON Schema.

### Task Orchestration

The `sdd-next` skill uses dependencies to determine which tasks are ready versus blocked. Tasks can't start until their dependencies complete. Independent tasks can be worked on in parallel.

**Automatic time tracking:**
- `started_at` recorded when task status changes to `in-progress`
- `completed_at` recorded when task status changes to `completed`
- `actual_hours` calculated from timestamps

### Multi-Model AI Consultation

Skills like `sdd-plan-review` and `sdd-fidelity-review` consult multiple AI models in parallel (default: cursor-agent + gemini). Results are synthesized into unified reports. Caching reduces API costs on subsequent runs.

**Trade-off:** Higher API cost for multiple perspectives and reduced bias.

### Documentation Integration

Generate machine-readable documentation:

```bash
sdd doc analyze-with-ai . --name "MyProject" --version "1.0.0"
```

**Outputs:**
- `docs/codebase.json` - AST, dependencies, metrics
- `docs/index.md` - Structural reference
- `docs/project-overview.md` - Executive summary
- `docs/architecture.md` - Architecture overview

**Used by:**
- `sdd-plan` - Understands existing patterns
- `sdd-next` - Provides code context for tasks
- `doc-query` - Fast queries without re-parsing

**Query capabilities:**
```bash
sdd doc stats                       # Project statistics
sdd doc search "authentication"     # Find code
sdd doc callers authenticate_user   # Function callers
sdd doc call-graph login_endpoint   # Call relationships
sdd doc scope src/auth.py --plan    # Lightweight context for planning
sdd doc scope src/auth.py --implement  # Detailed implementation context
```

### Context Tracking

Claude Code has a 200k token context window. The toolkit monitors usage and recommends clearing context at 85% (136k tokens). Specs track all progress, so resuming after `/clear` is seamless using `/sdd-begin`.

## Essential Skills Reference

### Planning & Workflow

| Skill | Purpose | Usage |
|-------|---------|-------|
| **sdd-plan** | Create specifications | "Plan a user authentication feature" |
| **sdd-next** | Find next actionable task | "What should I work on next?" |
| **sdd-update** | Update status, journal, move specs | "Mark task complete" |
| **sdd-validate** | Check spec validity | "Validate my spec for errors" |

### Quality Assurance

| Skill | Purpose | Usage |
|-------|---------|-------|
| **sdd-plan-review** | Multi-model spec review | "Review my spec before implementing" |
| **sdd-fidelity-review** | Verify implementation matches spec | "Did I implement what the spec said?" |
| **sdd-modify** | Apply review feedback | "Apply review suggestions to spec" |
| **run-tests** | Test execution with AI debugging | "Run tests and fix failures" |

### Documentation & Analysis

| Skill | Purpose | Usage |
|-------|---------|-------|
| **doc-query** | Query and analyze code | "What calls authenticate()?" |
| **llm-doc-gen** | AI-powered documentation | "Generate architecture docs" |
| **sdd-render** | Generate markdown from specs | "Render spec with AI insights" |

### Workflow Commands

| Command | Purpose |
|---------|---------|
| `/sdd-begin` | Resume work (shows pending/active specs) |
| `/sdd-setup` | Configure project permissions |

See [docs/skills-reference.md](docs/skills-reference.md) for complete skill documentation.

## Documentation

### For Users

- [Getting Started](docs/getting-started.md) - Installation and setup guide
- [Core Concepts](docs/core-concepts.md) - Specifications, tasks, dependencies
- [Workflows](docs/workflows.md) - Common development patterns and examples
- [Configuration](docs/configuration.md) - Setup and configuration options

### For Developers

- [Architecture](docs/architecture.md) - System architecture and design patterns
- [Advanced Topics](docs/advanced-topics.md) - Extension points, design patterns
- [CLI Reference](docs/cli-reference.md) - Command-line interface
- [Skills Reference](docs/skills-reference.md) - Detailed skill documentation

### Project Statistics

- 183 Python modules
- 154 classes
- 915 functions
- 72,268 lines of code
- Average complexity: 6.93

## Version History

**0.7.7** - Documentation context enhancements: automatic `context.file_docs` in `prepare-task` output with file-focused documentation, dependencies, and provenance metadata. Enhanced doc helper with `file_path`/`spec_id` parameters. Git-based staleness detection, call context integration, and test coverage improvements.

**0.7.6** - Prepare-task default context enhancement: comprehensive context in default output including dependencies, phase, siblings, and journal. One-call workflow with <100ms latency. 30% token reduction.

**0.7.5** - Provider security enhancements: read-only/tool restrictions across all AI providers (Codex, Claude, Gemini, Cursor Agent, OpenCode). Comprehensive security documentation with threat model and testing guides.

**0.7.1** - Journal accessibility improvements: ergonomic positional syntax, journal data in `prepare-task` output. Full backward compatibility.

**0.7.0** - New `sdd doc scope` command with `--plan`/`--implement` presets. 49x speedup in llm-doc-gen. Parallel processing, persistent caching, streaming output.

**0.6.8** - New llm-doc-gen skill for LLM-powered narrative documentation. Integrated code-doc as analysis module.

**0.6.5** - OpenCode AI provider with Node.js integration. Read-only security mode.

**0.6.0** - Three-tier verbosity system. AI consultation enhancements. Work mode configuration.

See [docs/changelog.md](docs/changelog.md) for complete version history.

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Docs:** [Claude Code Documentation](https://docs.claude.com/claude-code)
- **Architecture:** [docs/architecture.md](docs/architecture.md)

---

**Version:** 0.7.7 | **License:** MIT | **Author:** Tyler Burleigh
