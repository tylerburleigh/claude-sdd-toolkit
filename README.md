# SDD Toolkit - Spec-Driven Development for Claude Code

> Systematic, trackable, AI-assisted development through machine-readable specifications

[![Plugin Version](https://img.shields.io/badge/version-0.6.0-blue.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)]()
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()

## What is This?

The SDD Toolkit is a Python library and CLI toolkit for Spec-Driven Development (SDD). It structures AI-assisted development around machine-readable JSON specifications that define tasks, dependencies, and track progress.

**Architecture**: 183 Python modules, 154 classes, and 915 functions organized into independent, composable skills.

### Components

**For Claude Code:**
- Skills - Interactive workflows (`sdd-plan`, `sdd-next`, `code-doc`, `doc-query`, etc.)
- Slash Commands - Quick actions (`/sdd-begin`, `/sdd-setup`)
- Subagent System - Specialized agents for multi-step tasks

**For CLI:**
- Unified `sdd` command for SDD, documentation, testing, and validation operations
- Multi-provider support for Gemini, Codex, Cursor Agent, and Claude
- Output modes: Rich (terminal-enhanced), plain text, or JSON

**Integration**:
Claude skills orchestrate workflows → Python CLI executes operations → Results inform next steps

## Why Use This?

AI-assisted development without structure can lead to scope drift, lost context, unclear progress, and difficulty resuming work.

SDD Toolkit provides:

- Plan-first workflow with validated specifications
- Atomic task breakdown with dependency tracking
- Automatic progress tracking with status updates and time recording
- Multi-model AI consultation for quality reviews
- AST-based code analysis with AI enhancement
- Version control integration through JSON files

## Quick Start

### Installation

1. **Install Plugin**:
   ```
   claude  # Launch Claude Code
   /plugin → Add from marketplace → tylerburleigh/claude-sdd-toolkit
   ```

2. **Install Python Package**:
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   ```

3. **Configure Project** (in Claude Code):
   ```
   /sdd-setup
   ```

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

See [docs/examples/complete_task_workflow.md](docs/examples/complete_task_workflow.md) for a complete workflow example.

## Architecture

### Modular Skill-Based Design

Each major capability is implemented as an independent skill module:

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
┌───▼────┐         ┌─────▼─────┐       ┌─────▼─────┐
│ code-  │         │    doc-   │       │   run-    │
│ doc    │         │   query   │       │   tests   │
│        │         │           │       │           │
│ Docs   │         │  Analyze  │       │  Testing  │
└───┬────┘         └─────┬─────┘       └─────┬─────┘
    │                    │                   │
    └────────────────────┼───────────────────┘
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

**Core Workflow:**
- **sdd-plan** - Create specifications with tasks and dependencies
- **sdd-next** - Orchestrate workflow, find next actionable task
- **sdd-update** - Track progress, update status, journal decisions

**Supporting Skills:**
- Documentation: `code-doc`, `doc-query`
- Quality: `sdd-validate`, `sdd-fidelity-review`, `sdd-plan-review`, `sdd-modify`
- Testing: `run-tests`
- Utilities: `sdd-render`, `context-tracker`, `sdd-pr`

Benefits:
- Independent development and testing
- Clear separation of concerns
- Extensible without breaking changes
- Composable workflows

### Provider Abstraction Layer

Unified interface for multiple AI tools:

```python
# All providers implement ProviderContext
providers = ["gemini", "cursor-agent", "codex", "claude"]

# Parallel consultation
results = consult_multi_agent(
    prompt=prompt,
    providers=["gemini", "cursor-agent"],
    mode="parallel"
)
```

**Supported Providers:**
- **Gemini** - Google's Gemini 2.5 Pro/Flash models
- **Cursor Agent** - Cursor IDE's AI with 1M context (Composer)
- **Codex** - Anthropic Codex CLI
- **Claude** - Anthropic Claude with read-only restrictions (Sonnet 4.5/Haiku 4.5)

**Security**: Claude provider enforces read-only tool access (allows Read, Grep, Glob, WebSearch; blocks Write, Edit, Bash).

### Data Flow

**Primary State: JSON Specifications**

```
specs/
├── pending/      # Planned work
├── active/       # Current implementation
├── completed/    # Finished features
└── archived/     # Cancelled work
```

**Lifecycle:**
```
Plan → Validate → Activate → Implement → Track → Review → Complete
  ↓        ↓          ↓           ↓         ↓        ↓         ↓
sdd-plan  validate  activate  sdd-next  update  fidelity      PR
```

All specs are Git-trackable JSON files.

## Skills Reference

### Planning & Workflow

| Skill | Purpose | Example Usage |
|-------|---------|---------------|
| **sdd-plan** | Create specifications | "Plan a user authentication feature" |
| **sdd-next** | Find next actionable task | "What should I work on next?" |
| **sdd-update** | Update status, journal, move specs between folders | "Mark task complete" "Add journal entry" "Move spec to completed" |
| **sdd-validate** | Check spec validity | "Validate my spec for errors" |
| **sdd-render** | Generate markdown docs | "Render spec with AI insights" |

### Quality Assurance

| Skill | Purpose | Example Usage |
|-------|---------|---------------|
| **sdd-plan-review** | Multi-model spec review | "Review my spec before implementing" |
| **sdd-fidelity-review** | Verify implementation | "Did I implement what the spec said?" |
| **sdd-modify** | Apply review feedback | "Apply review suggestions to spec" |
| **run-tests** | Test with AI debugging | "Run tests and fix failures" |

### Documentation & Analysis

| Skill | Purpose | Example Usage |
|-------|---------|---------------|
| **code-doc** | Generate codebase docs | "Document this codebase" |
| **doc-query** | Query & analyze code | "What calls authenticate()?" "Show call graph" |
| **context-tracker** | Monitor Claude usage | "Show my context consumption" |

### Workflow Commands

| Command | Purpose |
|---------|---------|
| `/sdd-begin` | Resume work (shows pending/active specs) |
| `/sdd-setup` | Configure project permissions |

## Core Concepts

### Specifications (Specs)

**Structure:**
```json
{
  "metadata": {
    "name": "User Authentication",
    "version": "1.0.0",
    "complexity": "medium"
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
      "phase_id": "phase-1",
      "dependencies": [],
      "status": "pending",
      "verification": ["Model validates email", "Password hashing works"]
    }
  ],
  "journal": []
}
```

**Schema**: Validated against `specification-schema.json`

**Lifecycle Folders:**
- `pending/` - Backlog awaiting activation
- `active/` - Current work (supports parallel specs)
- `completed/` - Finished features
- `archived/` - Cancelled/deprecated

### Tasks: Atomic Work Units

Each task represents a single, focused change.

**Task Structure:**
```json
{
  "id": "task-1-1",
  "title": "Implement JWT token generation",
  "description": "Create TokenService.generateToken() method...",
  "phase_id": "phase-1",
  "dependencies": ["task-1-0"],
  "verification": [
    "Token contains user ID and expiry",
    "Token passes signature validation"
  ],
  "status": "pending",
  "category": "implementation",
  "estimated_hours": 2.0,
  "actual_hours": null,
  "started_at": null,
  "completed_at": null
}
```

**Automatic Time Tracking:**
- `started_at` recorded when status changes to `in-progress`
- `completed_at` recorded when status changes to `completed`
- `actual_hours` calculated from timestamps
- Spec totals aggregated from all tasks

**Categories:**
- `investigation` - Explore codebase
- `implementation` - Write new code
- `refactoring` - Improve structure
- `decision` - Architecture choices
- `research` - External research

### Dependencies & Orchestration

**Dependency Resolution:**
```json
{
  "id": "task-2-1",
  "dependencies": ["task-1-1", "task-1-2"]
}
```

`sdd-next` uses dependencies to:
- Determine which tasks are ready vs blocked
- Provide correct execution order
- Enable parallel work on independent tasks

**Validation**: `sdd-validate` detects circular dependencies. Use `sdd validate <spec> --show-graph` for visualization.

### Multi-Model Consultation

Skills using multi-agent consultation:
- `sdd-plan-review` - Spec quality assessment
- `sdd-fidelity-review` - Implementation verification
- `code-doc` - Architecture analysis

**Process:**
1. Parallel consultation of 2+ AI models (default: cursor-agent + gemini)
2. Independent analysis by each model
3. Consensus detection for common findings
4. Synthesis into unified report
5. Results cached to reduce API costs

**Trade-offs:**
- Higher API cost (mitigated by caching)
- Multiple perspectives reduce bias
- Parallel execution minimizes latency

### Documentation Integration

**Generated Documentation:**

```bash
sdd doc analyze-with-ai . --name "MyProject" --version "1.0.0"
```

**Outputs:**
- `docs/DOCUMENTATION.md` - Structural reference
- `docs/documentation.json` - Machine-readable data (AST, dependencies, metrics)
- `docs/ARCHITECTURE.md` - Architecture overview
- `docs/AI_CONTEXT.md` - AI assistant reference

**Used By:**
- `sdd-plan` - Understands existing patterns
- `sdd-next` - Provides code context for tasks
- `doc-query` - Fast queries without re-parsing

**Query Capabilities:**
```bash
sdd doc stats                       # Project statistics
sdd doc search "authentication"     # Find code
sdd doc complexity --threshold 10   # High-complexity functions
sdd doc dependencies src/auth.py    # Module dependencies
sdd doc callers authenticate_user   # Function callers
sdd doc callees authenticate_user   # Function callees
sdd doc call-graph login_endpoint   # Call relationships
sdd doc impact change_function      # Refactoring impact
sdd doc refactor-candidates         # Complex code
```

### Context Tracking

Claude Code context limits:
- 200k total context window
- 160k usable before auto-compaction (80% threshold)

Automatic monitoring during `sdd-next`:
```
Claude: [Completes task-1-1]
        Context: 45% (72k/160k tokens)

        [Completes task-1-2]
        Context: 62% (99k/160k)

        Warning: Above 50% - consider saving progress
```

Clear context with `/clear` and resume with `/sdd-begin` when usage exceeds 80%.

### Subagent Architecture

Some skills launch subagents - specialized Claude instances for multi-step tasks:

```
User Request → Main Claude → Task Tool → Subagent → Execute → Report Back
```

**Skills Using Subagents:**
- `sdd-validate`, `sdd-plan-review`, `sdd-fidelity-review`
- `sdd-update`, `run-tests`, `code-doc`, `sdd-modify`

**Skills Running Directly:**
- `sdd-plan`, `sdd-next`, `doc-query`

## Common Workflows

### Plan and Implement a Feature

```
You: Create a spec for rate limiting on the API

Claude: [Creates specs/pending/rate-limiting-001.json]

You: /sdd-begin

Claude: Found pending spec: rate-limiting-001
        Activate and start implementing?

You: Yes

Claude: [Moves to specs/active/]
        Task 1-1: Create RateLimiter middleware class
        [Implements, marks complete]

        ...

        All tasks complete (7/7)
        Move to completed/?

You: Yes

Claude: [Moves to specs/completed/rate-limiting-001.json]
```

### Resume After Break

```
You: /sdd-begin

Claude: Found 2 active specs:
        1. rate-limiting-001 (3/7 tasks, 43%)
        2. user-auth-002 (1/5 tasks, 20%)

        Which spec?

You: 1

Claude: Resuming rate-limiting-001
        Next: Task 1-4 - Add rate limit headers
```

### Generate & Query Documentation

```
You: Document this codebase with AI enhancement

Claude: [Uses code-doc skill]
        Analyzing 183 files...
        Consulting cursor-agent and gemini...

        Generated:
        - docs/DOCUMENTATION.md
        - docs/documentation.json
        - docs/ARCHITECTURE.md
        - docs/AI_CONTEXT.md

You: What classes handle authentication?

Claude: Found 3 authentication classes:

        1. AuthManager (src/auth/manager.py:15)
           - Methods: authenticate(), validateToken(), refreshToken()
           - Complexity: 8

        2. TokenValidator (src/auth/tokens.py:23)
           - Methods: validate(), decode(), verify()
           - Complexity: 5

        3. SessionStore (src/auth/sessions.py:45)
           - Methods: create(), get(), delete()
           - Complexity: 4

You: Show call graph for authenticate()

Claude: AuthManager.authenticate()
        ├── TokenValidator.validate()
        │   ├── decode()
        │   └── verify()
        ├── UserRepository.findByEmail()
        └── SessionStore.create()
            └── RedisClient.set()
```

### Multi-Model Review

```
You: Review my authentication spec

Claude: [Uses sdd-plan-review skill]
        Consulting cursor-agent and gemini...

        cursor-agent completed (34.2s)
        gemini completed (36.8s)

        Consensus findings:
        - Overall approach is sound
        - Task breakdown is appropriate

        cursor-agent suggests:
        - Add retry logic for token validation
        - Consider rate limiting on auth endpoints

        gemini suggests:
        - Add session timeout handling
        - Consider multi-factor authentication hooks
```

### Verify Implementation Fidelity

```
You: Did I implement what the spec said?

Claude: [Uses sdd-fidelity-review skill]
        Reviewing implementation...
        Consulting cursor-agent and gemini...

        Phase 1: Core Auth (3 tasks)
        ✅ task-1-1: User model - COMPLIANT
        ✅ task-1-2: Password hashing - COMPLIANT
        ⚠️ task-1-3: Token generation - DEVIATION

        Deviation in task-1-3:
        - Spec: JWT with 24h expiry
        - Implemented: JWT with 1h expiry

        Recommendation: Update spec or change code to 24h
```

### Debug Test Failures

```
You: Run tests and fix failures

Claude: [Uses run-tests skill]
        Running pytest...

        3 tests failed

        Consulting gemini...

        test_authenticate_user FAILED
        - Issue: Missing mock for UserRepository
        - Fix: Add @patch('auth.UserRepository')

        test_validate_token FAILED
        - Issue: Token expiry not mocked
        - Fix: Use freezegun to control time
```

## Project Structure

```
your-project/
├── specs/
│   ├── pending/
│   ├── active/
│   ├── completed/
│   ├── archived/
│   │
│   ├── .reports/              # Gitignored
│   ├── .reviews/              # Gitignored
│   ├── .backups/              # Gitignored
│   └── .human-readable/       # Gitignored
│
├── .claude/
│   ├── settings.local.json    # Created by /sdd-setup
│   ├── sdd_config.json        # CLI preferences
│   └── ai_config.yaml         # AI defaults
│
├── docs/                      # Optional
│   ├── documentation.json
│   ├── DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   └── AI_CONTEXT.md
│
└── [source code]
```

## Configuration

### Project Setup

```
/sdd-setup
```

This creates:
- `.claude/settings.local.json` - Required permissions
- `.claude/sdd_config.json` - Output preferences
- `.claude/ai_config.yaml` - AI model defaults

**Optional**: Create `.claude/git_config.json` for git integration settings (auto-branch, auto-commit, auto-push). Template available at `claude_skills/common/templates/setup/git_config.json`.

Run once per project.

### CLI Configuration

**File**: `.claude/sdd_config.json`

```json
{
  "work_mode": "single",
  "output": {
    "default_mode": "json",        // "rich", "plain", or "json"
    "json_compact": true,           // Compact JSON (~30% token savings)
    "default_verbosity": "quiet"    // "quiet", "normal", or "verbose"
  }
}
```

**Settings:**
- `work_mode`: "single" (one task at a time) or "autonomous" (complete all tasks in phase)
- `output.default_mode`: Default output format
- `output.json_compact`: Use compact JSON formatting
- `output.default_verbosity`: Default verbosity level

**Precedence:**
1. CLI flags (`--json`, `--compact`, `--verbose`, `--quiet`)
2. Config file
3. Built-in defaults

**Token Savings:**

| Output | Normal | Compact | Savings |
|--------|--------|---------|---------|
| `sdd progress` | ~120 | ~84 | 30% |
| `sdd prepare-task` | ~400 | ~280 | 30% |
| `sdd next-task` | ~55 | ~37 | 33% |

### AI Model Configuration

**File**: `.claude/ai_config.yaml`

```yaml
# Tool/provider fallback priority
tool_priority:
  default:
    - gemini
    - cursor-agent
    - codex
    - claude

# Per-skill configuration
run-tests:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1

code-doc:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-flash
    cursor-agent: composer-1

sdd-plan-review:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1
```

**Key settings:**
- `tool_priority.default`: Fallback order when tool fails
- Per-skill `tool_priority`: Tool consultation order for that skill
- Per-skill `models`: Default model for each tool

**CLI Override:**
```bash
# Single model for all operations
sdd test run --model gemini-2.5-pro

# Tool-specific overrides
sdd doc analyze-with-ai . \
  --model gemini=gemini-2.5-flash \
  --model cursor-agent=composer-2
```

### Git Integration Configuration (Optional)

**File**: `.claude/git_config.json`

```json
{
  "enabled": false,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "auto_pr": false,
  "commit_cadence": "task"
}
```

**Settings:**
- `enabled`: Master switch for git integration (default: false)
- `auto_branch`: Create feature branches when starting specs (default: true)
- `auto_commit`: Commit changes when completing tasks (default: true)
- `auto_push`: Push commits to remote automatically (default: false)
- `auto_pr`: Create pull requests when specs complete (default: false)
- `commit_cadence`: When to commit - "task", "phase", or "manual" (default: "task")

**Note**: This file is not created by `/sdd-setup`. Copy from template at `claude_skills/common/templates/setup/git_config.json` if needed.

## Advanced Topics

### Design Patterns

From architecture analysis:

1. **Command Pattern** - CLI commands as operations
2. **Factory Pattern** - Language parser creation
3. **Strategy Pattern** - AI tool selection
4. **Facade Pattern** - Documentation query interface
5. **Provider Pattern** - AI tool abstraction
6. **Repository Pattern** - Spec file operations
7. **Mediator Pattern** - Output formatting

### Technology Stack

**Core:**
- Python 3.9+ (183 modules, 154 classes, 915 functions)
- JSON for specs and schemas
- Rich for terminal UI
- tree-sitter for AST parsing

**AI Integration:**
- External CLI tools (gemini, cursor-agent, codex, claude)
- Provider abstraction layer
- Parallel consultation

**Testing:**
- pytest framework
- Integration coverage

### Performance

**Scalability:**
- Documentation: Linear with codebase size
- Spec validation: O(n) dependency analysis
- Doc queries: Fast JSON traversal
- AI calls: Parallel execution, cached results

**Optimization:**
- Parallel AI consultation
- TTL-based caching
- Lazy loading
- Progressive rendering

### Extension Points

**Add a Skill:**
1. Create `src/claude_skills/<skill_name>/`
2. Implement `cli.py`
3. Use `common` utilities
4. Register in main CLI
5. Add tests

**Add a Language Parser:**
1. Install tree-sitter grammar
2. Create parser in `code_doc/parsers/`
3. Update factory
4. Add detection
5. Test

**Add an AI Provider:**
1. Extend `ProviderContext`
2. Register in `providers/registry.py`
3. Add detection
4. Update config templates
5. Test

## Troubleshooting

### Skills Not Working

```bash
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
# Should show: sdd-plan, sdd-next, code-doc, etc.
```

### CLI Commands Not Found

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

### After Plugin Update

Always reinstall Python package:

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
# Restart Claude Code
```

### Permission Errors

```
/sdd-setup
```

### Validation Errors

```bash
sdd validate <spec.json>
sdd validate <spec.json> --fix
sdd validate <spec.json> --show-graph
```

### AI Tool Failures

```bash
sdd test check-tools
```

Common issues: rate limits, API key not configured, tool not in PATH.

Multi-agent consultation succeeds if at least one model succeeds.

## CLI Reference

For toolkit developers. Regular users should use natural language with Claude or slash commands.

<details>
<summary>Show CLI commands</summary>

### Spec Operations
```bash
sdd create <name>
sdd activate-spec <spec-id>
sdd next-task <spec-id>
sdd prepare-task <spec-id> <task-id>
sdd update-status <spec> <task>
sdd complete-task <spec-id> <task-id>
sdd complete-spec <spec-id>
sdd validate <spec.json>
sdd list-specs [--status STATUS]
```

### Documentation
```bash
sdd doc generate .
sdd doc analyze-with-ai .
sdd doc stats
sdd doc search "pattern"
sdd doc complexity --threshold 10
sdd doc callers "function"
sdd doc callees "function"
sdd doc call-graph "entry"
sdd doc impact "function"
sdd doc refactor-candidates
```

### Testing
```bash
sdd test run tests/
sdd test debug --test <name>
sdd test check-tools
```

### Reviews
```bash
sdd plan-review <spec>
sdd fidelity-review <spec>
sdd render <spec>
```

</details>

## Updating the Toolkit

1. **Update Marketplace**: `/plugins → Manage marketplaces → claude-sdd-toolkit → Update`
2. **Update Plugin**: `/plugins → Manage and uninstall → Update now`
3. **Restart Claude Code**
4. **Reinstall Package**:
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   ```

## Version History

**0.6.0** - Three-tier verbosity system (QUIET/NORMAL/VERBOSE) with ~50% output reduction. AI consultation enhancements with fallback and retry logic. Context optimization for sdd-next. Work mode configuration. High-level task operations.

**0.5.1** - Provider abstraction with Gemini, Codex, Cursor Agent, Claude. Claude provider has read-only restrictions. 360s timeout for extended reasoning.

**0.5.0** - Plain UI mode, modernized configuration, JSON Schema validation, workflow guardrails.

**0.4.5** - Unified AI consultation infrastructure, type-safe interfaces, parallel execution.

**0.4.2** - Compact mode with 30% token savings.

**0.4.1** - AI-powered PR creation.

See [CHANGELOG.md](CHANGELOG.md) for details.

## Documentation

### For Users
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) - Development guidance
- [docs/examples/](docs/examples/) - Workflow examples
- [docs/spec-modification.md](docs/spec-modification.md) - Validation
- [docs/review-workflow.md](docs/review-workflow.md) - Fidelity review

### For Developers
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/AI_CONTEXT.md](docs/AI_CONTEXT.md) - AI assistant reference
- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) - Structural reference

### Stats
- 183 Python modules
- 154 classes
- 915 functions
- 72,268 lines of code
- Average complexity: 6.93

## Prerequisites

### Required
- Claude Code (latest)
- Python 3.9+
- pip

### Optional
- Git
- tree-sitter libraries (`tree-sitter-python`, `tree-sitter-javascript`, etc.)
- AI CLIs (`gemini`, `codex`, `cursor-agent`)

## Getting Help

- Issues: [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- Docs: [Claude Code Documentation](https://docs.claude.com/claude-code)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Components

**In `~/.claude/`:**
- `skills/` - 12+ skills
- `commands/` - Slash commands
- `hooks/` - Session detection
- `src/claude_skills/` - Python CLI

**In PATH:**
- `sdd` - Unified CLI

## Next Steps

1. Install plugin and Python package
2. Run `/sdd-setup` in your project
3. Create a spec: "Create a spec for [feature]"
4. Implement: `/sdd-begin`
5. Track progress automatically
6. Review with multi-model consultation
7. Create PR with AI

See [INSTALLATION.md](INSTALLATION.md) for setup or [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) for development guidance.

---

**Version**: 0.6.0 | **License**: MIT | **Author**: Tyler Burleigh
