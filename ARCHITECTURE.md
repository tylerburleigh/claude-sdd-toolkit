# Architecture - SDD Toolkit

> Technical architecture and system design

This document explains how the SDD Toolkit components work together and the flow of data through the system.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Integration Points](#integration-points)
- [Workflow Examples](#workflow-examples)
- [Design Decisions](#design-decisions)

## System Overview

The SDD Toolkit is built as a Claude Code plugin that extends Claude's capabilities with specialized workflows for spec-driven development.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Claude Code                        │
│  (Reads skills, commands, hooks from ~/.claude/)        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ├─── Invokes Skills
                       │    (e.g., Skill(sdd-plan))
                       │
                       ├─── Executes Commands
                       │    (e.g., /sdd-start)
                       │
                       └─── Triggers Hooks
                            (e.g., session-start)
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
    ┌──────────────┐      ┌──────────────┐
    │   Skills     │      │   Commands   │
    │  (SKILL.md)  │      │    (.md)     │
    └──────┬───────┘      └──────┬───────┘
           │                     │
           └──────────┬──────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  CLI Tools      │
            │ (Python Package)│
            └────────┬────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Project Files      │
          │  (specs/, code)      │
          └──────────────────────┘
```

## Component Architecture

### 1. Skills Layer

**Location**: `~/.claude/skills/*/SKILL.md`

**Purpose**: Provide instructions to Claude for specialized workflows

**How it works**:
- Each skill directory contains a `SKILL.md` file
- Claude Code auto-detects and loads skills at startup
- When invoked, Claude reads the skill's instructions
- Skills can call CLI tools to perform operations

**Example Flow**:
```
User: "Create a spec for user authentication"
  ↓
Claude detects intent matches sdd-plan skill
  ↓
Claude reads skills/sdd-plan/SKILL.md
  ↓
Claude follows instructions in SKILL.md
  ↓
Claude calls CLI: sdd plan --title "user authentication"
  ↓
Spec created at specs/active/user-auth-001.json
```

### 2. Commands Layer

**Location**: `~/.claude/commands/*.md`

**Purpose**: User-invoked interactive workflows

**How it works**:
- User types `/command-name` in Claude Code
- Claude reads the corresponding `.md` file
- Claude follows the instructions interactively
- Can invoke skills and CLI tools as needed

**Example Flow**:
```
User: /sdd-start
  ↓
Claude reads commands/sdd-start.md
  ↓
Claude runs: sdd skills-dev start-helper -- detect-active
  ↓
CLI returns list of active specs
  ↓
Claude presents options to user
  ↓
User selects "Continue with next task"
  ↓
Claude invokes Skill(sdd-next)
```

### 3. Hooks Layer

**Location**: `~/.claude/hooks/*`

**Purpose**: Automatic actions triggered by events

**How it works**:
- Claude Code triggers hooks on specific events
- Hooks are bash scripts that run in the background
- Hooks receive event data via stdin
- Hooks can output JSON for Claude to read
- Hooks must exit 0 (non-blocking)

**Example Flow**:
```
User opens Claude Code
  ↓
Claude triggers session-start event
  ↓
hooks/session-start script executes
  ↓
Script checks for specs/active/ directory
  ↓
Script finds active specs
  ↓
Script outputs JSON with spec information
  ↓
Claude reads JSON and proactively suggests /sdd-start
```

### 4. CLI Tools Layer

**Location**: `~/.claude/src/claude_skills/`

**Purpose**: Reusable Python tools for file operations and logic

**How it works**:
- Installed as a Python package via pip
- Provides CLI commands in user's PATH
- Used by skills, commands, and hooks
- Shared utilities and common code

**Unified CLI Architecture**:
```
sdd              # SDD workflows
├── next-task        # Find next task
├── update-status    # Update task status
├── validate         # Validate specs
└── skills-dev       # Development tools
    ├── setup-permissions
    ├── gendocs
    └── start-helper

doc              # Documentation
├── generate         # Generate docs
├── query           # Query docs
└── search          # Search docs

test             # Test execution
└── run             # Run tests with debugging
```

## Data Flow

### Creating a Specification

```
┌──────────────┐
│ User Request │
│"Create spec" │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│ Claude Code     │
│ Detects intent  │
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Skill(sdd-plan)  │
│ Reads SKILL.md   │
└──────┬───────────┘
       │
       ├─── 1. Explore codebase
       │    └─→ Skill(doc-query)
       │        └─→ CLI: doc query "authentication"
       │
       ├─── 2. Generate spec JSON
       │    └─→ Python: spec_generator.create()
       │
       ├─── 3. Validate spec
       │    └─→ CLI: sdd validate spec.json
       │
       └─── 4. Save to specs/active/
            └─→ Write: specs/active/user-auth-001.json
       │
       ▼
┌────────────────────┐
│ Response to User   │
│ "Created spec at..." │
└────────────────────┘
```

### Resuming Work

```
┌──────────────┐
│ User types   │
│ /sdd-start   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ SlashCommand            │
│ Reads commands/sdd-start.md │
└──────┬──────────────────┘
       │
       ▼
┌──────────────────────────┐
│ CLI: sdd skills-dev      │
│      start-helper        │
│      -- detect-active    │
└──────┬───────────────────┘
       │
       ├─── Scans specs/active/
       ├─── Reads .state/ files
       └─── Returns JSON with:
            - Active specs
            - Progress info
            - Recent activity
       │
       ▼
┌────────────────────┐
│ Claude presents    │
│ interactive menu   │
└──────┬─────────────┘
       │
       ▼
┌────────────────────┐
│ User selects       │
│ "Next task"        │
└──────┬─────────────┘
       │
       ▼
┌────────────────────┐
│ Skill(sdd-next)    │
│ Finds next task    │
└──────┬─────────────┘
       │
       ▼
┌────────────────────┐
│ Claude helps       │
│ implement task     │
└────────────────────┘
```

### Session Start Hook

```
┌──────────────────┐
│ Claude Code      │
│ session starts   │
└──────┬───────────┘
       │
       ▼
┌─────────────────────┐
│ Hook: session-start │
└──────┬──────────────┘
       │
       ├─── Check for specs/ directory
       ├─── Find active specs
       ├─── Check recent activity
       └─── Create marker file
       │
       ▼
┌───────────────────────┐
│ Output JSON           │
│ {                     │
│   "active_specs": [...],│
│   "suggest": "/sdd-start"│
│ }                     │
└──────┬────────────────┘
       │
       ▼
┌────────────────────────┐
│ Claude reads marker    │
│ and proactively suggests│
└────────────────────────┘
```

## Integration Points

### Claude Code Integration

**Skills Discovery**:
- Claude Code scans `~/.claude/skills/` for `SKILL.md` files
- Skills are loaded at session start
- Skill metadata in frontmatter is parsed

**Command Discovery**:
- Claude Code scans `~/.claude/commands/` for `.md` files
- Commands are available via `/command-name`
- Command metadata in frontmatter is parsed

**Hook Execution**:
- Hooks are triggered on specific events
- Event data is passed via stdin (JSON)
- Hook output is captured and passed to Claude

**Permissions**:
- Permissions defined in `~/.claude/settings.json`
- Can allow/deny/ask for specific operations
- Project-level permissions in `.claude/settings.json`

### File System Integration

**Spec Directory Structure**:
```
project/
└── specs/
    ├── active/           # Currently active specs
    │   ├── spec-001.json
    │   └── spec-002.json
    ├── completed/        # Completed specs
    ├── archived/         # Archived specs
    └── .state/          # State tracking
        ├── spec-001.json
        └── spec-002.json
```

**State Management**:
- Each spec has a state file in `.state/`
- State tracks task completion, progress, timestamps
- State is updated via `sdd update-status`

### Git Integration

**Automatic Detection**:
- CLI tools detect if directory is a git repo
- Git root is used for relative paths
- Can check git status, branch info

**Spec Folder Recommendations**:
- `specs/` directory typically gitignored
- Or committed for team collaboration
- `.state/` directory always gitignored

## Workflow Examples

### Example 1: Creating and Implementing a Feature

```
1. User: "Add rate limiting feature"
   └─→ Claude: Skill(sdd-plan)
       └─→ CLI: doc query "rate limiting"
       └─→ CLI: sdd plan --title "rate-limiting"
       └─→ Creates: specs/active/rate-limiting-001.json

2. Claude: "Created spec at specs/active/rate-limiting-001.json"

3. User: /sdd-start
   └─→ Claude: SlashCommand(/sdd-start)
       └─→ CLI: sdd skills-dev start-helper -- detect-active
       └─→ Claude presents menu

4. User: "Continue with next task"
   └─→ Claude: Skill(sdd-next)
       └─→ CLI: sdd next-task rate-limiting-001
       └─→ Returns: Task 1 - Add RateLimiter middleware

5. Claude: Implements task
   └─→ Creates/edits files
   └─→ Runs tests

6. User: "Mark task complete"
   └─→ Claude: Skill(sdd-update)
       └─→ CLI: sdd update-status rate-limiting-001 task-1 completed
       └─→ Updates: specs/.state/rate-limiting-001.json

7. Repeat steps 4-6 for remaining tasks
```

### Example 2: Multi-Model Spec Review

```
1. User: "Review my spec with multiple models"
   └─→ Claude: Skill(sdd-plan-review)
       └─→ Reads: specs/active/my-spec-001.json
       └─→ CLI: gemini < spec.json
       └─→ CLI: codex < spec.json
       └─→ CLI: cursor-agent < spec.json
       └─→ Aggregates feedback

2. Claude: "Here's the feedback from 3 models:
   - Model A suggests...
   - Model B recommends...
   - Model C warns..."

3. User: "Apply the recommended changes"
   └─→ Claude: Updates spec based on feedback
       └─→ CLI: sdd validate my-spec-001.json
```

### Example 3: Test-Driven Development

```
1. User: "Run tests and fix failures"
   └─→ Claude: Skill(run-tests)
       └─→ CLI: test run tests/
       └─→ Detects: 3 failures

2. Claude: Analyzes failures
   └─→ Identifies root causes
   └─→ Suggests fixes

3. Claude: Implements fixes
   └─→ Edits files

4. Claude: Re-runs tests
   └─→ CLI: test run tests/
   └─→ Verifies: All pass
```

## Design Decisions

### Why Skills vs Commands?

**Skills** (invoked automatically):
- Used when Claude detects intent from natural language
- Better for workflows Claude should suggest proactively
- Can be combined with other skills
- Example: "Create a spec" → Skill(sdd-plan)

**Commands** (invoked manually):
- Used when user explicitly requests a workflow
- Better for interactive, step-by-step processes
- Clear entry points with `/` prefix
- Example: `/sdd-start` for resuming work

### Why Hooks?

- Provide proactive assistance without user request
- Detect context (active specs, git status, etc.)
- Enable automatic suggestions
- Non-blocking (won't interrupt workflow)

### Why Python CLI Tools?

- Reusable across skills, commands, and hooks
- Easier to test and maintain than bash scripts
- Shared utilities and common code
- Can be used independently of Claude Code

### Why JSON for Specs?

- Machine-readable and parseable
- Easy to validate with schemas
- Can be queried and transformed programmatically
- Supports complex nested structures

### Why Separate Active/Completed/Archived?

- Clear visual organization
- Easy to see current work at a glance
- Enables smart resume suggestions
- Prevents clutter in active directory

## Performance Considerations

### Caching

- Documentation generation results cached
- State files prevent re-reading specs
- Hook results cached between events

### Lazy Loading

- Skills loaded only when needed
- CLI tools imported on-demand
- Large specs read incrementally

### Parallel Execution

- Multiple CLI tools can run concurrently
- Skills can invoke multiple tools in parallel
- Hook execution doesn't block main thread

## Security Considerations

### Permissions

- All operations subject to permission checks
- User can deny/allow/ask for specific operations
- Project-level permissions override global

### Sandboxing

- CLI tools run in sandboxed environment
- Limited file system access
- No network access without permission

### Input Validation

- All spec files validated against schema
- CLI inputs sanitized
- File paths checked for traversal attacks

## Future Enhancements

Potential areas for expansion:

1. **Web UI**: Dashboard for viewing specs and progress
2. **Team Collaboration**: Sync specs across team members
3. **CI/CD Integration**: Automated spec validation in pipelines
4. **Metrics**: Track development velocity and spec quality
5. **Templates**: Pre-built spec templates for common patterns

---

**For implementation details**, see [DEVELOPER.md](DEVELOPER.md).

**For user-facing documentation**, see [README.md](README.md).
