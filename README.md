# SDD Toolkit - Claude Code Plugin

> Plan-first development with Claude - systematic, trackable, and organized

[![Plugin Version](https://img.shields.io/badge/version-0.4.0-blue.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)]()
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()

## What is This?

The SDD Toolkit is a set of Claude skills and Python CLI tools that enable spec-driven development. It puts Claude on guardrails by having it work from machine-readable JSON specs that define tasks, dependencies, and track progress.

**What it includes:**
- **Claude skills** - Interactive workflows like `sdd-plan`, `sdd-next`, and `sdd-update`
- **Python CLI** - Commands for creating, reading, and updating spec files
- **Integration** - Skills invoke CLI commands to systematically work through tasks

This was built to keep Claude focused on one task at a time while maintaining a complete record of what's planned, what's done, and what's next.

## Why Use This?

Working on complex projects with Claude can lead to scope drift, forgotten requirements, and lost context. The toolkit addresses this by:

- Defining all work upfront in a spec before implementation starts
- Breaking execution into atomic tasks (one file per task) with approval gates
- Tracking progress automatically so you can resume anytime
- Journaling decisions and changes for a complete project record

Specs live in your project as JSON files, giving you a machine-readable history of what was planned and what was actually done.

## Installation

1. Launch Claude Code (`claude` command)
2. Type `/plugin` and press Enter
3. Select **"Add from marketplace"**
4. Enter: `tylerburleigh/claude-sdd-toolkit`
5. Wait for the repository to clone
6. Click **"Install"** when prompted
7. **Exit Claude Code completely**
8. Install Python dependencies:
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   ```
9. **Restart Claude Code**
10. **Configure your project**: Open your project in Claude Code and run:
    ```
    /sdd-setup
    ```
    This configures the necessary permissions for SDD tools to work in your project.

That's it! The plugin is now ready to use.

## Quick Start

### Your First Workflow

In Claude Code, try this:

```
Create a spec for a command line Pomodoro/task timer.
```

Claude will:
1. Explore your codebase (if you have one)
2. Create a detailed specification
3. Break it into actionable tasks
4. Save it as `specs/pending/{spec-id}.json`

Resume anytime with:

```
/sdd-begin
```

### See It In Action

Want to see a complete workflow from start to finish? Check out [docs/examples/complete_task_workflow.md](docs/examples/complete_task_workflow.md) for a real-world demonstration. It shows the full interaction between a user and Claude after the user runs `/sdd-begin` until the first task is completed and journaled. This example gives you a sense of what you can expect using this tool.

(NOTE: This example was generated using version 0.1.0)

## Latest Updates

**Version 0.4.0** brings major enhancements including AI-powered spec rendering, automatic time tracking, context monitoring, and code-doc integration that provides richer task context. See [CHANGELOG.md](CHANGELOG.md) for complete version history.

**Important:** After updating the toolkit, you must reinstall the Python package to get the latest CLI commands. See [Updating the Toolkit](#updating-the-toolkit) below.

## Core Concepts

### Specifications (Specs)

A **spec** is a JSON file containing:
- Feature overview and goals
- File-by-file implementation plan
- Task breakdown with dependencies
- Verification steps
- Edge cases and considerations

Specs live in your project's `specs/` directory:
- `specs/pending/` - Backlog of planned work awaiting activation (specs are created here by default)
- `specs/active/` - Current work (you can have multiple specs representing parallel work streams)
- `specs/completed/` - Finished features
- `specs/archived/` - Old/cancelled work

When you create a spec, it starts in `pending/`. This allows you to plan multiple features without cluttering your active workspace. When you run `/sdd-begin`, Claude will show you pending specs and offer to activate them when you're ready to start working.

### Design Principles

**Atomic Tasks**: Each task represents a single, focused change to one file. This design:
- Enables precise dependency tracking between tasks
- Allows granular progress monitoring
- Supports parallel implementation when tasks are independent
- Makes verification and rollback straightforward
- Prevents scope creep within individual tasks

When a feature requires changes across multiple files, decompose it into multiple tasks or use subtasks with proper dependencies. See [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) for detailed guidance.

**Task Categories**: Each task can be categorized to improve organization and reporting:
- `investigation` - Exploring codebase, understanding existing systems
- `implementation` - Writing new code or features
- `refactoring` - Improving existing code structure
- `decision` - Architecture or design decisions
- `research` - External research, learning new technologies

Categories help with progress tracking and post-project analysis.

**Automatic Time Tracking**: The toolkit automatically tracks time spent on tasks using timestamps:
- When a task transitions to `in_progress`, `started_at` timestamp is recorded
- When marked `completed`, `completed_at` timestamp is recorded
- `actual_hours` is automatically calculated from the duration
- Spec-level totals are aggregated from all task times

No manual time entry needed - the toolkit handles it automatically based on when you actually work on tasks.

**Documentation Integration**: Several skills leverage generated codebase documentation for better context:
- **sdd-plan**: Understands existing code patterns when creating specs
- **sdd-next**: Provides relevant code context when preparing tasks
- **run-tests**: Uses docs to understand test relationships and dependencies

Best practice: Ask Claude to "Document this codebase" before creating specs to enable enhanced context. Skills gracefully degrade to Explore/Glob/Grep when docs are unavailable.

**Context Tracking**: The toolkit monitors your Claude conversation token usage to prevent hitting the 160k "usable context" limit (80% of 200k total before auto-compaction). `sdd-next` automatically checks context after completing tasks and warns when usage exceeds safe thresholds.

### Skills

**Skills** extend Claude's capabilities. The toolkit provides:

| Skill | What It Does | When To Use |
|-------|-------------|-------------|
| `sdd-plan` | Create specifications | "Plan a feature for rate limiting" |
| `sdd-next` | Find next task | "What should I work on next?" |
| `sdd-update` | Track progress | Automatic when tasks complete |
| `sdd-validate` | Check spec validity | "Is my spec valid?" |
| `sdd-render` | Render specs to markdown | Generate human-readable documentation with AI enhancement (3 modes: basic/summary/standard/full) |
| `sdd-plan-review` | Multi-model review | "Review my spec" |
| `code-doc` | Generate docs | "Document this codebase" |
| `doc-query` | Query docs & analyze relationships | "What calls this function?" "Show call graph" "Find refactor candidates" |
| `run-tests` | Run & debug tests | "Run tests and fix failures" |

Claude uses skills automatically based on your requests.

### Subagent Architecture

Some skills use **Claude Code's subagent system** for orchestration. Subagents are specialized instances of Claude that handle complex, multi-step tasks autonomously.

**How it works:**

When you invoke certain skills (like `sdd-validate`, `run-tests`, or `code-doc`), Claude launches a subagent using the `Task` tool:

```
Task(
  subagent_type: "sdd-toolkit:sdd-validate-subagent",
  prompt: "Validate specs/active/my-spec.json",
  description: "Validate spec file"
)
```

**Workflow diagram:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Subagent Workflow                        │
└─────────────────────────────────────────────────────────────┘

User: "Validate my spec"
  │
  ▼
┌──────────────────┐
│  Main Claude     │  Recognizes validation needed
│  (sdd-next)      │
└────────┬─────────┘
         │ Invokes Task tool
         ▼
┌──────────────────┐
│  Task Tool       │  Launches specialized subagent
│  (Claude Code)   │
└────────┬─────────┘
         │ Creates subagent
         ▼
┌──────────────────┐
│  Subagent        │  Autonomous Claude instance
│  (sdd-validate)  │  - Specialized context
└────────┬─────────┘  - Focused tools
         │ Executes commands
         ▼
┌──────────────────┐
│  SDD CLI         │  Runs validation commands
│  (sdd validate)  │  - Checks spec structure
└────────┬─────────┘  - Validates dependencies
         │ Returns results
         ▼
┌──────────────────┐
│  Subagent        │  Analyzes results
│  (sdd-validate)  │  - Summarizes findings
└────────┬─────────┘  - Formats report
         │ Reports back
         ▼
┌──────────────────┐
│  Main Claude     │  Receives report
│  (sdd-next)      │  - Presents to user
└────────┬─────────┘  - Continues workflow
         │
         ▼
User: Sees validation results
```

**Benefits of subagents:**

- **Autonomous execution**: Subagents work independently to complete complex tasks
- **Specialized context**: Each subagent has focused tools and instructions
- **Parallel work**: Multiple subagents can run concurrently
- **Clean handoffs**: Main Claude receives results without context pollution

**Which skills use subagents:**

- `sdd-validate` → Launches validation subagent for spec quality checks
- `sdd-plan-review` → Launches review subagent for multi-model feedback
- `sdd-update` → Launches update subagent for progress tracking and journaling
- `run-tests` → Launches testing subagent for test execution and debugging
- `code-doc` → Launches documentation subagent for codebase analysis

**Other skills** (`sdd-plan`, `sdd-next`, `doc-query`) run directly in the main conversation for tighter integration with your workflow.

### Commands

**Commands** are interactive workflows you invoke with `/`:

- `/sdd-begin` - Resume work (shows both pending and active specs with options to activate or continue)
- `/sdd-setup` - Configure project permissions

Type `/` in Claude Code to see all available commands.

### The SDD Workflow

```
1. Create Spec
   "Plan feature X"
   ↓
2. Review & Refine
   Claude generates detailed spec
   ↓
3. Implement Tasks
   /sdd-begin → pick next task
   ↓
4. Track Progress
   Tasks auto-marked as complete
   ↓
5. Resume Anytime
   /sdd-begin shows progress
```

## Common Workflows

### Create and Implement a Feature

```
You: Create a spec for adding rate limiting to the API

Claude: [Creates detailed spec at specs/pending/rate-limiting-001.json]

You: /sdd-begin

Claude: Found pending spec "rate-limiting-001"
        Would you like to activate it and start working?

You: Yes

Claude: [Moves spec to specs/active/]
        Task 1: Create RateLimiter middleware class
        [Implements the task]

You: /sdd-begin

Claude: Task 2: Add rate limit configuration...
        [Continues through all tasks]

        ✅ All tasks completed (7/7 = 100%)
        This spec is ready to be finalized. Move to completed/?

You: Yes

Claude: [Moves spec to specs/completed/]
```

### Resume Work After a Break

```
You: /sdd-begin

Claude: Found 2 active specs:
        1. rate-limiting-001 (3/7 tasks complete)
        2. user-auth-002 (1/5 tasks complete)

        Which would you like to continue?

You: 1

Claude: Continuing rate-limiting-001
        Next task: Add rate limit headers to responses
        [Shows task details and helps implement]
```

### Generate and Query Documentation

```
You: Document this codebase

Claude: [Uses code-doc skill to generate docs/documentation.json]

You: What classes handle authentication?

Claude: [Uses doc-query skill to search documentation]
        Found 3 classes:
        - AuthManager (src/auth/manager.py)
        - TokenValidator (src/auth/tokens.py)
        - SessionStore (src/auth/sessions.py)
```

### Get Multi-Model Review

```
You: Review my spec with multiple AI models

Claude: [Uses sdd-plan-review skill]
        Consulting Gemini, GPT-5, and Codex...

        Feedback summary:
        - All models agree on the approach
        - Gemini suggests adding retry logic
        - GPT-5 recommends error boundary patterns
        - Codex warns about performance implications
```

### Monitor Context Usage

```
You: /sdd-begin

Claude: [Completes task-1-1]
        Context usage: 45% (72k/160k tokens)
        Continue to next task?

You: Yes

Claude: [Completes task-1-2]
        Context usage: 62% (99k/160k tokens)

        ⚠️ Context usage above 50% - consider saving progress
        Options:
        1. Continue with next task (not recommended above 80%)
        2. Save progress and clear context (/clear, then /sdd-begin to resume)
```

### Validate and Fix a Spec

```
You: Validate my spec

Claude: [Uses sdd-validate skill]
        Found 12 issues:
        - 3 circular dependencies
        - 5 missing dependencies
        - 4 schema violations

        Auto-fix available. Apply fixes?

You: Yes

Claude: Fixed 8 issues automatically
        Remaining 4 issues require manual review:
        [Details of unfixable issues]
```

### Analyze Code Relationships

```
You: What calls the authenticateUser function?

Claude: [Uses doc-query skill]
        Found 5 callers:
        - LoginController.login() (src/controllers/auth.py:45)
        - APIMiddleware.verify() (src/middleware/api.py:23)
        - WebSocketHandler.connect() (src/ws/handler.py:89)
        - AdminPanel.authorize() (src/admin/panel.py:156)
        - TestAuthFlow.test_login() (tests/test_auth.py:34)

You: Show me the call graph starting from the login endpoint

Claude: [Generates call graph visualization]
        LoginController.login()
        ├── authenticateUser()
        │   ├── validateCredentials()
        │   ├── checkUserStatus()
        │   └── generateToken()
        └── createSession()
            └── persistSession()
```

## Project Structure

After using the toolkit, your project will have:

```
your-project/
├── specs/                    # Specifications
│   ├── pending/             # Backlog (planned work)
│   │   └── future-feature.json
│   ├── active/              # Current work
│   │   └── feature-001.json
│   ├── completed/           # Finished
│   ├── archived/            # Old/cancelled
│   │
│   ├── .reports/            # Validation reports (gitignored)
│   ├── .reviews/            # Multi-model reviews (gitignored)
│   ├── .backups/            # Spec backups (gitignored)
│   └── .human-readable/     # Rendered markdown (gitignored)
│
├── .claude/                 # Project settings (optional)
│   └── settings.json        # Permissions
│
└── docs/                    # Generated docs (optional)
    ├── documentation.json   # Machine-readable
    └── documentation.md     # Human-readable
```

The `specs/` directory can be:
- **Gitignored** for personal use
- **Committed** for team collaboration

## Configuration

### Project Setup (Recommended)

Run the setup command in your project:

```
/sdd-setup
```

This automatically:
- Creates `.claude/settings.json` in your project
- Adds all required permissions for SDD skills and tools
- Prepares your project for spec-driven development

You only need to run this once per project.

### What Gets Configured

The setup creates `.claude/settings.json` with permissions like:

```json
{
  "permissions": {
    "allow": [
      "Skill(sdd-toolkit:sdd-plan)",
      "Skill(sdd-toolkit:sdd-next)",
      "Write(//**/specs/active/**)",
      "Write(//**/specs/pending/**)"
    ]
  }
}
```

## Troubleshooting

### Skills Not Working

```bash
# Verify skills are installed
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/

# Should show: sdd-plan, sdd-next, sdd-update, etc.

# If missing, reinstall the plugin from marketplace
```

### CLI Commands Not Found

If `sdd`, `doc`, or `test` commands are not found:

```bash
# Reinstall the Python package
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .

# Verify installation (ONLY for troubleshooting - you should never run these directly)
# Normal workflow: interact with Claude using natural language
sdd --help
doc --help
test --help
```

### Updated Plugin But Commands Still Old

If you updated the plugin (via `git pull` or marketplace update) but CLI commands seem outdated or broken:

```bash
# Reinstall to get latest CLI changes
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .

# Restart Claude Code to reload skills
```

**Why this happens:** The Python package is installed in editable mode, but updates require reinstallation. See [Updating the Toolkit](#updating-the-toolkit) for details.

### Permission Errors

```bash
# Use the slash command in Claude Code:
/sdd-setup

# Or ask Claude to set up permissions for your project
```

### Hooks Not Running

```bash
# Check if hooks are executable
ls -l ~/.claude/hooks/

# Make them executable
chmod +x ~/.claude/hooks/*
```

## Updating the Toolkit

To update to the latest version:

### Step 1: Update the Plugin Marketplace

1. In Claude Code, type `/plugins` and press Enter
2. Select **"Manage marketplaces"**
3. Select **`claude-sdd-toolkit`**
4. Select **"Update marketplace"**
5. Wait for the update to complete

### Step 2: Update the Installed Plugin

1. Type `/plugins` again
2. Select **"Manage and uninstall plugins"**
3. Select **`claude-sdd-toolkit`**
4. Select **`sdd-toolkit`**
5. Select **"Update now"**
6. Wait for the update to complete

### Step 3: Restart Claude Code

Exit Claude Code completely and restart it.

### Step 4: Reinstall Python Package

The plugin files are now updated, but you must reinstall the Python CLI tools:

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**Why all these steps?** The marketplace update gets the latest plugin code, the plugin update installs it to Claude Code, the restart loads the new skills, and the reinstall updates the CLI commands. Skipping any step will leave you with mismatched versions.

**How to verify:** When you start Claude Code, the session-start hook will automatically check for version mismatches and warn you if the update wasn't completed properly.

## Advanced Usage

### For Developers

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System documentation (generated by the `code-doc` skill from this system)

### CLI Reference

**⚠️ For Developers and Advanced Troubleshooting Only**

This CLI reference is for toolkit developers and debugging purposes. **Regular users should NEVER run these commands directly.**

Instead, interact with Claude using:
- Natural language: "Create a spec for X", "What should I work on next?"
- Slash commands: `/sdd-begin`, `/sdd-setup`

The commands below are used internally by the skills. They're documented here for developers working on the toolkit itself or for advanced troubleshooting.

```bash
# SDD workflows
sdd create <name>                     # Create new spec in pending/
sdd activate-spec <spec-id>           # Move spec from pending to active
sdd next-task <spec-id>               # Find next task
sdd prepare-task <spec-id> <task-id>  # Get full context for task
sdd update-status <spec> <task>       # Update progress
sdd complete-task <spec-id> <task-id> # Mark task complete with journal entry
sdd complete-spec <spec-id>           # Move spec to completed/
sdd validate <spec.json>              # Validate spec
sdd render <spec-id|spec.json>        # Render spec to markdown
sdd list-specs [--status STATUS]      # List specs by status
sdd update-task-metadata <spec> <task> --field value  # Update task metadata

# Documentation
sdd doc generate .                    # Generate docs with cross-references
sdd doc query "search term"           # Search docs
sdd doc callers "function_name"       # Who calls this function?
sdd doc callees "function_name"       # What does this function call?
sdd doc call-graph "entry_point"      # Visualize call relationships
sdd doc trace-entry "endpoint"        # Trace request flow from entry point
sdd doc trace-data "Model.field"      # Trace data flow through system
sdd doc impact "function_name"        # Analyze refactoring impact
sdd doc refactor-candidates           # Find complex code needing refactoring

# Testing
sdd test run tests/                   # Run tests with AI debugging

# Context Monitoring
sdd session-marker                    # Generate session marker (Step 1)
sdd context --session-marker <marker> # Check context using marker (Step 2)
sdd context --json                    # Get JSON output

# Development tools
sdd skills-dev setup-permissions -- update .   # Set up permissions
sdd skills-dev gendocs -- <skill-name>         # Generate skill docs
```

## Prerequisites

### Required
- **Claude Code** - Latest version
- **Python 3.9+** - For CLI tools
- **pip** - Python package manager

### Optional
- **Git** - For version control and spec collaboration
- **tree-sitter** libraries - For enhanced code documentation:
  - `tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`
  - `tree-sitter-go`, `tree-sitter-html`, `tree-sitter-css`
- **External AI CLIs** - For AI-enhanced features:
  - `gemini` - Fast structured analysis
  - `codex` - Code understanding
  - `cursor-agent` - Large codebase analysis (1M context with cheetah model)

## Getting Help

- **Issues**: Report bugs at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Docs**: Full Claude Code documentation at [Claude Code Docs](https://docs.claude.com/claude-code)

## What's Included

The plugin installs these components:

**In `~/.claude/`:**
- `skills/` - 8 specialized skills for Claude
- `commands/` - Slash commands like `/sdd-begin`
- `hooks/` - Automatic session detection
- `src/claude_skills/` - Python CLI tools

**In your PATH:**
- `sdd` - Unified CLI for all SDD, documentation, testing, and development commands

## Next Steps

Ready to get started?

1. ✅ Install the plugin (see above)
2. ✅ Verify installation works
3. 📝 Create your first spec: "Plan a feature for X"
4. 🚀 Implement with `/sdd-begin`
5. 🎉 Track progress and stay organized

**Questions?** Check [INSTALLATION.md](INSTALLATION.md) for detailed setup or [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) for development guidance.

---

**Version**: 0.4.0 | **License**: MIT | **Author**: Tyler Burleigh
