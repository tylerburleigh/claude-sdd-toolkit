# CLI Reference

Complete command-line reference for the `sdd` CLI tool. This is primarily for toolkit developers and advanced users - regular users should use natural language with Claude Code or slash commands.

## Table of Contents

- [Command Overview](#command-overview)
- [Spec Operations](#spec-operations)
- [Documentation Commands](#documentation-commands)
- [Testing Commands](#testing-commands)
- [Review Commands](#review-commands)
- [Global Options](#global-options)
- [Output Formats](#output-formats)
- [CLI Usage Tips](#cli-usage-tips)

---

## Command Overview

The `sdd` command provides a unified interface for all toolkit operations:

```bash
sdd [CATEGORY] [COMMAND] [ARGUMENTS] [OPTIONS]
```

### Command Categories

| Category | Purpose | Example |
|----------|---------|---------|
| **Spec operations** | Create, validate, manage specs | `sdd validate my-spec.json` |
| **Documentation** | Generate and query docs | `sdd doc stats` |
| **Testing** | Run and debug tests | `sdd test run tests/` |
| **Reviews** | Quality and fidelity reviews | `sdd plan-review my-spec.json` |
| **Utilities** | Helper commands | `sdd skills-dev install` |

---

## Spec Operations

Commands for creating and managing specifications.

### create

Create a new specification from template.

**Syntax:**
```bash
sdd create <name>
```

**Arguments:**
- `<name>`: Spec name (will generate spec-id with timestamp)

**Example:**
```bash
sdd create "User Authentication Feature"
```

**Output:**
```
Created: specs/pending/user-authentication-feature-2025-11-22-001.json
```

**Note:** Most users should use the `sdd-plan` skill instead (via Claude Code).

---

### activate-spec

Move a spec from pending to active.

**Syntax:**
```bash
sdd activate-spec <spec-id>
```

**Arguments:**
- `<spec-id>`: Specification ID

**Example:**
```bash
sdd activate-spec user-auth-2025-11-22-001
```

**Output:**
```
Moved specs/pending/user-auth-2025-11-22-001.json
  to specs/active/user-auth-2025-11-22-001.json
```

---

### next-task

Find the next actionable task in a spec.

**Syntax:**
```bash
sdd next-task <spec-id> [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID

**Options:**
- `--json`: Output as JSON
- `--phase <phase-id>`: Limit to specific phase

**Example:**
```bash
sdd next-task user-auth-2025-11-22-001 --json
```

**Output:**
```json
{
  "task_id": "task-1-2",
  "title": "Implement password hashing",
  "status": "pending",
  "can_start": true,
  "blocked_by": []
}
```

---

### prepare-task

Get comprehensive task information for execution with enhanced default context.

**One-Call Workflow:**

The `prepare-task` command now provides all information needed for task execution in a single call, eliminating the need for separate `task-info` or `check-deps` calls unless specific overrides are required.

**Syntax:**
```bash
sdd prepare-task <spec-id> [task-id] [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID
- `[task-id]`: Optional task ID (defaults to next recommended)

**Options:**
- `--json`: Output as JSON (recommended)
- `--compact`: Compact JSON formatting
- `--include-full-journal`: Include complete journal history
- `--include-phase-history`: Include all phase journal entries
- `--include-spec-overview`: Include spec-wide overview

**Example:**
```bash
# Get next task with enhanced default context (recommended)
sdd prepare-task user-auth-2025-11-22-001 --json

# Get specific task
sdd prepare-task user-auth-2025-11-22-001 task-1-2 --json --compact
```

**Enhanced Default Output:**

The default response now includes rich context without requiring additional flags:

```json
{
  "task_id": "task-1-2",
  "task_data": {
    "title": "Implement password hashing",
    "status": "pending",
    "metadata": {
      "file_path": "src/auth.py",
      "task_category": "implementation"
    }
  },
  "dependencies": {
    "can_start": true,
    "blocked_by": [],
    "soft_depends": []
  },
  "context": {
    "previous_sibling": {
      "id": "task-1-1",
      "title": "Setup auth module",
      "status": "completed",
      "journal_excerpt": {
        "summary": "Created auth.py with basic structure..."
      }
    },
    "parent_task": {
      "id": "phase-1",
      "title": "Authentication Foundation",
      "position_label": "2 of 5 tasks"
    },
    "phase": {
      "title": "Phase 1: Foundation",
      "percentage": 20,
      "blockers": []
    },
    "sibling_files": [
      {
        "task_id": "task-1-1",
        "file_path": "src/auth.py",
        "changes_summary": "Created basic auth module structure..."
      }
    ],
    "task_journal": {
      "entry_count": 0,
      "entries": []
    },
    "dependencies": {
      "blocking": [],
      "blocked_by_details": [],
      "soft_depends": []
    }
  },
  "needs_branch_creation": false,
  "dirty_tree_status": {"is_dirty": false},
  "spec_complete": false
}
```

**Key Default Fields:**

| Field | Description |
|-------|-------------|
| `context.previous_sibling` | Previous task with journal summary for continuity |
| `context.parent_task` | Parent task metadata and position |
| `context.phase` | Current phase progress and blockers |
| `context.sibling_files` | Files touched by related tasks |
| `context.task_journal` | Task-specific journal entries |
| `context.dependencies` | Detailed dependency info with titles/status/files |

**When to Use Additional Commands:**

- `task-info`: Only if you need metadata for a non-recommended task
- `check-deps`: Only if you need to verify dependencies separately
- Enhancement flags: Only for extended context (full journal, phase history, spec overview)

**Performance:** <100ms median latency, <30ms overhead vs minimal context

---

### update-status

Update task status.

**Syntax:**
```bash
sdd update-status <spec-id> <task-id> <status> [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID
- `<task-id>`: Task ID
- `<status>`: New status (`pending`, `in_progress`, `completed`, `blocked`)

**Options:**
- `--note <text>`: Add a note to the status change

**Example:**
```bash
sdd update-status user-auth-2025-11-22-001 task-1-2 in_progress
```

**Output:**
```json
{
  "success": true,
  "task_id": "task-1-2",
  "new_status": "in_progress",
  "started_at": "2025-11-22T14:30:00Z"
}
```

---

### complete-task

Mark a task as complete with journal entry.

**Syntax:**
```bash
sdd complete-task <spec-id> <task-id> [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID
- `<task-id>`: Task ID

**Options:**
- `--note <text>`: Completion note (recommended)

**Example:**
```bash
sdd complete-task user-auth-2025-11-22-001 task-1-2 \
  --note "Implemented bcrypt hashing with cost 12. All tests passing."
```

**Output:**
```json
{
  "success": true,
  "task_id": "task-1-2",
  "status": "completed",
  "completed_at": "2025-11-22T15:45:00Z",
  "actual_hours": 1.25
}
```

**Note:** Most users should use the `sdd-update` skill instead.

---

### validate

Validate specification file.

**Syntax:**
```bash
sdd validate <spec-path> [OPTIONS]
```

**Arguments:**
- `<spec-path>`: Path to spec JSON file

**Options:**
- `--fix`: Auto-fix common issues
- `--show-graph`: Show dependency graph
- `--json`: Output as JSON

**Example:**
```bash
sdd validate specs/active/user-auth-001.json --fix
```

**Output:**
```
✅ Schema validation: PASSED
✅ Task ID uniqueness: PASSED
✅ Dependency references: PASSED
⚠️  Circular dependency detected

Auto-fixing...
✅ Fixed circular dependency
Spec is now valid
```

---

### list-specs

List all specifications.

**Syntax:**
```bash
sdd list-specs [OPTIONS]
```

**Options:**
- `--status <status>`: Filter by folder (`pending`, `active`, `completed`, `archived`)
- `--json`: Output as JSON

**Example:**
```bash
sdd list-specs --status active --json
```

**Output:**
```json
[
  {
    "spec_id": "user-auth-2025-11-22-001",
    "title": "User Authentication",
    "status": "active",
    "progress": "3/10 tasks (30%)"
  }
]
```

---

### progress

Show specification progress.

**Syntax:**
```bash
sdd progress <spec-id> [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID

**Options:**
- `--json`: Output as JSON
- `--compact`: Compact JSON
- `--verbose`: Show all details
- `--quiet`: Minimal output

**Example:**
```bash
sdd progress user-auth-2025-11-22-001 --json --compact
```

**Output:**
```json
{"spec_id":"user-auth-2025-11-22-001","progress":{"completed":3,"total":10,"percentage":30},"status":"active","current_phase":"phase-1"}
```

---

## Documentation Commands

Commands for generating and querying codebase documentation.

### doc generate

Generate machine-readable documentation (AST-based, fast).

**Syntax:**
```bash
sdd doc generate <path> [OPTIONS]
```

**Arguments:**
- `<path>`: Directory to analyze (usually `.`)

**Options:**
- `--parallel`: Use parallel processing (faster)
- `--filter-mode <mode>`: Filtering strategy (`aggressive`, `balanced`, `conservative`)
- `--output <file>`: Output file (default: `docs/codebase.json`)

**Example:**
```bash
sdd doc generate . --parallel --filter-mode balanced
```

**Output:**
```
Analyzing codebase...
✓ Parsed 183 files
✓ Extracted 915 functions
✓ Built dependency graph
✓ Calculated complexity metrics

Generated: docs/codebase.json (2.4 MB)
```

**Performance:** ~10-30 seconds for large codebases

---

### doc analyze-with-ai

Generate AI-enhanced narrative documentation.

**Syntax:**
```bash
sdd doc analyze-with-ai <path> [OPTIONS]
```

**Arguments:**
- `<path>`: Directory to analyze (usually `.`)

**Options:**
- `--name <name>`: Project name
- `--version <version>`: Project version
- `--model <provider=model>`: Override AI models
- `--force`: Regenerate even if exists

**Example:**
```bash
sdd doc analyze-with-ai . \
  --name "My Project" \
  --version "1.0.0" \
  --model gemini=gemini-2.5-pro
```

**Output:**
```
Analyzing codebase structure...
Consulting cursor-agent and gemini...

cursor-agent: Analyzing architecture... (24.3s)
gemini: Generating component docs... (28.7s)

Generated:
✓ docs/codebase.json
✓ docs/index.md
✓ docs/project-overview.md
✓ docs/architecture.md
✓ docs/component-inventory.md
```

**Performance:** ~30-60 seconds (AI consultation)

---

### doc stats

Show project statistics.

**Syntax:**
```bash
sdd doc stats [OPTIONS]
```

**Options:**
- `--json`: Output as JSON

**Example:**
```bash
sdd doc stats --json
```

**Output:**
```json
{
  "modules": 183,
  "classes": 154,
  "functions": 915,
  "lines_of_code": 72268,
  "avg_complexity": 6.93
}
```

**Prerequisites:** Requires `docs/codebase.json` (run `doc generate` first)

---

### doc search

Search for code by keyword.

**Syntax:**
```bash
sdd doc search <query> [OPTIONS]
```

**Arguments:**
- `<query>`: Search term

**Options:**
- `--json`: Output as JSON
- `--type <type>`: Filter by type (`class`, `function`, `module`)

**Example:**
```bash
sdd doc search "authentication" --type class --json
```

**Output:**
```json
[
  {
    "name": "AuthManager",
    "file": "src/auth/manager.py",
    "line": 15,
    "type": "class",
    "complexity": 8
  }
]
```

---

### doc complexity

Find high-complexity code.

**Syntax:**
```bash
sdd doc complexity [OPTIONS]
```

**Options:**
- `--threshold <n>`: Minimum complexity (default: 10)
- `--json`: Output as JSON

**Example:**
```bash
sdd doc complexity --threshold 15 --json
```

**Output:**
```json
[
  {
    "name": "process_payment",
    "file": "src/billing/payment.py",
    "line": 42,
    "complexity": 18
  }
]
```

---

### doc callers

Find who calls a function.

**Syntax:**
```bash
sdd doc callers <function-name> [OPTIONS]
```

**Arguments:**
- `<function-name>`: Function to analyze

**Options:**
- `--json`: Output as JSON

**Example:**
```bash
sdd doc callers authenticate --json
```

**Output:**
```json
[
  {
    "caller": "LoginController.login",
    "file": "controllers/auth.py",
    "line": 42
  }
]
```

---

### doc callees

Show what a function calls.

**Syntax:**
```bash
sdd doc callees <function-name> [OPTIONS]
```

**Arguments:**
- `<function-name>`: Function to analyze

**Options:**
- `--json`: Output as JSON

**Example:**
```bash
sdd doc callees authenticate --json
```

**Output:**
```json
[
  {
    "callee": "UserRepository.findByEmail",
    "file": "repositories/user.py",
    "line": 23
  }
]
```

---

### doc call-graph

Show complete call graph for a function.

**Syntax:**
```bash
sdd doc call-graph <entry-point> [OPTIONS]
```

**Arguments:**
- `<entry-point>`: Starting function

**Options:**
- `--max-depth <n>`: Maximum depth (default: 5)
- `--json`: Output as JSON

**Example:**
```bash
sdd doc call-graph authenticate --max-depth 3
```

**Output:**
```
authenticate()
├── UserRepository.findByEmail()
│   └── Database.query()
├── PasswordHasher.verify()
│   └── bcrypt.checkpw()
└── SessionStore.create()
    └── RedisClient.set()
```

---

### doc scope

Get scoped context for planning or implementation.

**Syntax:**
```bash
sdd doc scope <file-path> [OPTIONS]
```

**Arguments:**
- `<file-path>`: File to analyze

**Options:**
- `--plan`: Lightweight context for planning (signatures, summaries)
- `--implement`: Detailed context for implementation (full code, patterns)
- `--json`: Output as JSON

**Example (Planning):**
```bash
sdd doc scope src/auth/manager.py --plan --json
```

**Output:**
```json
{
  "file": "src/auth/manager.py",
  "classes": [
    {
      "name": "AuthManager",
      "methods": ["authenticate", "validateToken", "refreshToken"],
      "complexity": 8
    }
  ],
  "functions": [],
  "summary": "Main authentication orchestration"
}
```

**Example (Implementation):**
```bash
sdd doc scope src/auth/manager.py --implement
```

**Output:**
```
=== src/auth/manager.py Implementation Details ===

AuthManager.authenticate(email: str, password: str) -> Token
Lines: 42-78

Implementation pattern:
- Validates email format (line 45)
- Fetches user from repository (line 48)
- Verifies password hash (line 52)
- Creates new session (line 65)
- Generates JWT token (line 71)

[Full implementation details...]
```

---

### doc impact

Analyze refactoring impact.

**Syntax:**
```bash
sdd doc impact <function-name> [OPTIONS]
```

**Arguments:**
- `<function-name>`: Function to analyze

**Options:**
- `--json`: Output as JSON

**Example:**
```bash
sdd doc impact authenticate --json
```

**Output:**
```json
{
  "function": "authenticate",
  "direct_callers": 5,
  "indirect_callers": 12,
  "total_affected": 17,
  "risk_level": "medium"
}
```

---

## Testing Commands

Commands for running and debugging tests.

### test run

Run tests with optional AI debugging.

**Syntax:**
```bash
sdd test run <test-path> [OPTIONS]
```

**Arguments:**
- `<test-path>`: Path to tests (file or directory)

**Options:**
- `--model <provider=model>`: Override AI model for debugging
- `--verbose`: Show full output

**Example:**
```bash
sdd test run tests/auth/ --model gemini=gemini-2.5-pro
```

**Output:**
```
Running pytest tests/auth/...

================================
5 passed, 2 failed in 4.21s
================================

Failures detected. Consulting gemini for analysis...

[AI analysis of failures...]
```

**Note:** Most users should use the `run-tests` skill instead.

---

### test debug

Debug a specific failing test.

**Syntax:**
```bash
sdd test debug --test <test-name> [OPTIONS]
```

**Arguments:**
- `--test <test-name>`: Test function name

**Options:**
- `--model <provider=model>`: Override AI model

**Example:**
```bash
sdd test debug --test test_authenticate_user
```

---

### test check-tools

Verify AI tool availability.

**Syntax:**
```bash
sdd test check-tools
```

**Example:**
```bash
sdd test check-tools
```

**Output:**
```
Checking AI tools...
✅ gemini: Available
✅ cursor-agent: Available
❌ codex: Not found in PATH
✅ claude: Available
```

---

## Review Commands

Commands for quality assurance and reviews.

### plan-review

Multi-model spec review.

**Syntax:**
```bash
sdd plan-review <spec-path> [OPTIONS]
```

**Arguments:**
- `<spec-path>`: Path to spec JSON file

**Options:**
- `--model <provider=model>`: Override AI models
- `--output <file>`: Save review to file

**Example:**
```bash
sdd plan-review specs/active/user-auth-001.json \
  --model gemini=gemini-2.5-pro \
  --output specs/.reviews/user-auth-001-review.json
```

**Output:**
```
Consulting cursor-agent and gemini...

cursor-agent: Complete (34.2s)
gemini: Complete (36.8s)

=== Consensus Findings ===
[Review results...]
```

**Note:** Most users should use the `sdd-plan-review` skill instead.

---

### fidelity-review

Verify implementation matches spec.

**Syntax:**
```bash
sdd fidelity-review <spec-id> [OPTIONS]
```

**Arguments:**
- `<spec-id>`: Specification ID

**Options:**
- `--phase <phase-id>`: Review specific phase only
- `--task <task-id>`: Review specific task only
- `--model <provider=model>`: Override AI models

**Example:**
```bash
sdd fidelity-review user-auth-001 --phase phase-1
```

**Output:**
```
Reviewing implementation against spec...

=== Phase 1: Core Auth ===
✅ task-1-1: COMPLIANT
✅ task-1-2: COMPLIANT
⚠️  task-1-3: DEVIATION

[Detailed report...]
```

**Note:** Most users should use the `sdd-fidelity-review` skill instead.

---

### render

Generate human-readable markdown from spec.

**Syntax:**
```bash
sdd render <spec-path> [OPTIONS]
```

**Arguments:**
- `<spec-path>`: Path to spec JSON file

**Options:**
- `--output <file>`: Output file (default: `specs/.human-readable/<spec-id>.md`)
- `--with-insights`: Include AI insights

**Example:**
```bash
sdd render specs/active/user-auth-001.json --with-insights
```

**Output:**
```
Generated: specs/.human-readable/user-auth-001.md

Contents:
- Metadata and overview
- Phase breakdown
- Task list with dependencies
- Journal entries
- AI insights
```

---

## Global Options

Options that work with all commands.

### Output Control

| Option | Effect |
|--------|--------|
| `--json` | Output as JSON |
| `--rich` | Terminal-enhanced output (colors, tables) |
| `--plain` | Plain text output |
| `--compact` | Compact JSON (no whitespace) |
| `--no-compact` | Pretty-printed JSON |

### Verbosity

| Option | Effect |
|--------|--------|
| `--quiet` | Minimal output |
| `--normal` | Standard output (default) |
| `--verbose` | Maximum detail |

### Help

| Option | Effect |
|--------|--------|
| `--help` | Show command help |
| `--version` | Show toolkit version |

**Example:**
```bash
sdd --version
# Output: SDD Toolkit 0.7.1

sdd progress --help
# Output: [Help text for progress command]
```

---

## Output Formats

### JSON Format

**Best for:** Claude Code, scripting, automation

**Example:**
```bash
sdd progress my-spec --json --compact
```

**Output:**
```json
{"spec_id":"my-spec-001","progress":{"completed":3,"total":10,"percentage":30}}
```

### Rich Format

**Best for:** Interactive terminal use

**Example:**
```bash
sdd progress my-spec --rich
```

**Output:**
```
╭─────────────────────────────────╮
│ Spec: my-spec-001               │
│ Progress: 3/10 tasks (30%)      │
│ Status: active                  │
╰─────────────────────────────────╯

Phase 1: Core Features  ━━━━━━━━━━━━━━━━━━━━ 60%
Phase 2: Testing        ━━━━━━━━──────────── 40%
```

### Plain Format

**Best for:** Scripting, simple terminals

**Example:**
```bash
sdd progress my-spec --plain
```

**Output:**
```
Spec: my-spec-001
Progress: 3/10 tasks (30%)
Status: active
```

---

## CLI Usage Tips

### 1. Use JSON with Claude Code

For best integration with Claude Code, always use `--json --compact`:

```bash
sdd progress my-spec --json --compact
```

Configure as default in `.claude/sdd_config.json`:
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

### 2. Pipe to jq for Filtering

```bash
# Get only task IDs
sdd list-specs --json | jq '.[] | .spec_id'

# Get specs with >50% progress
sdd list-specs --json | jq '.[] | select(.progress.percentage > 50)'
```

### 3. Save Reviews for Reference

```bash
sdd plan-review my-spec.json \
  --output reviews/my-spec-$(date +%Y%m%d).json
```

### 4. Check Tools Before Reviews

```bash
# Verify AI tools work before starting multi-hour review
sdd test check-tools
```

### 5. Use Aliases

Add to your shell rc file:

```bash
alias sdd-status='sdd list-specs --status active --json'
alias sdd-prog='sdd progress'
alias sdd-docs='sdd doc stats'
```

### 6. Quiet Mode for Scripts

When scripting, use `--quiet --json` to get only essential data:

```bash
#!/bin/bash
PROGRESS=$(sdd progress my-spec --quiet --json | jq '.progress.percentage')
if [ "$PROGRESS" -eq 100 ]; then
  echo "Spec complete!"
fi
```

### 7. Combine with Watch

Monitor progress in real-time:

```bash
watch -n 5 'sdd progress my-spec --rich'
```

---

## Next Steps

Now that you understand the CLI:

- **Regular users**: Use natural language with Claude Code instead of CLI
- **Power users**: Create shell aliases and scripts
- **Developers**: Integrate CLI into CI/CD pipelines
- **Configure defaults**: Set up `.claude/sdd_config.json` for your workflow

---

**Related Documentation:**
- [Skills Reference](skills-reference.md) - High-level skill interface (recommended for most users)
- [Configuration](configuration.md) - Configure CLI behavior
- [Workflows](workflows.md) - Common development patterns
- [Core Concepts](core-concepts.md) - Understanding the system
