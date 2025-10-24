# SDD Toolkit - Claude Code Plugin

> Plan-first development with Claude - systematic, trackable, and organized

[![Plugin Version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()
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
- Breaking execution into one task at a time with approval gates
- Tracking progress automatically so you can resume anytime
- Journaling decisions and changes for a complete project record

Specs live in your project as JSON files, giving you a machine-readable history of what was planned and what was actually done.

## Quick Start

### Installation

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

### Verify Installation

```bash
# Check that CLI tools are available (examples)
sdd --help
sdd doc --help
sdd test --help

# Check that skills are installed
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
```

You should see: `sdd-plan`, `sdd-next`, `sdd-update`, and other skills.

**Test in Claude Code**: Navigate to a project and run `/sdd-setup`. If it completes successfully, everything is working!

### Your First Workflow

In Claude Code, try this:

```
Create a spec for adding user authentication with email and password
```

Claude will:
1. Explore your codebase
2. Create a detailed specification
3. Break it into actionable tasks
4. Save it as `specs/active/user-auth-YYYY-MM-DD-001.json`

Resume anytime with:

```
/sdd-start
```

### See It In Action

Want to see a complete workflow from start to finish? Check out [docs/examples/complete_task_workflow.md](docs/examples/complete_task_workflow.md) for a real-world demonstration. It shows the full interaction between a user and Claude after the user runs `/sdd-start` until the first task is completed and journaled. This example gives you a sense of what you can expect using this tool.

## Core Concepts

### Specifications (Specs)

A **spec** is a JSON file containing:
- Feature overview and goals
- File-by-file implementation plan
- Task breakdown with dependencies
- Verification steps
- Edge cases and considerations

Specs live in your project's `specs/` directory:
- `specs/active/` - Current work
- `specs/completed/` - Finished features
- `specs/archived/` - Old/cancelled work

### Skills

**Skills** extend Claude's capabilities. The toolkit provides:

| Skill | What It Does | When To Use |
|-------|-------------|-------------|
| `sdd-plan` | Create specifications | "Plan a feature for rate limiting" |
| `sdd-next` | Find next task | "What should I work on next?" |
| `sdd-update` | Track progress | Automatic when tasks complete |
| `sdd-validate` | Check spec validity | "Is my spec valid?" |
| `sdd-render` | Render specs to markdown | Generate human-readable documentation |
| `sdd-plan-review` | Multi-model review | "Review my spec" |
| `code-doc` | Generate docs | "Document this codebase" |
| `doc-query` | Query docs | "What handles authentication?" |
| `run-tests` | Run & debug tests | "Run tests and fix failures" |

Claude uses skills automatically based on your requests.

### Commands

**Commands** are interactive workflows you invoke with `/`:

- `/sdd-start` - Resume work on active specs

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
   /sdd-start → pick next task
   ↓
4. Track Progress
   Tasks auto-marked as complete
   ↓
5. Resume Anytime
   /sdd-start shows progress
```

## Common Workflows

### Create and Implement a Feature

```
You: Create a spec for adding rate limiting to the API

Claude: [Creates detailed spec at specs/active/rate-limiting-001.json]

You: /sdd-start

Claude: Found active spec "rate-limiting-001". Continue with next task?

You: Yes

Claude: Task 1: Create RateLimiter middleware class
        [Implements the task]

You: /sdd-start

Claude: Task 2: Add rate limit configuration...
        [Continues through all tasks]
```

### Resume Work After a Break

```
You: /sdd-start

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

## Project Structure

After using the toolkit, your project will have:

```
your-project/
├── specs/                    # Specifications
│   ├── active/              # Current work
│   │   └── feature-001.json
│   ├── completed/           # Finished
│   └── archived/            # Old/cancelled
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
      "Skill(sdd-plan)",
      "Skill(sdd-next)",
      "Read(//**/specs/**)",
      "Write(//**/specs/active/**)"
    ]
  }
}
```

### Advanced: Manual Setup

If you prefer to configure manually via CLI:

```bash
# In your project directory
sdd skills-dev setup-permissions -- update .
```

This does the same thing as `/sdd-setup` but from the command line.

### Global Settings

Your global settings at `~/.claude/settings.json` control default behavior:

```json
{
  "sdd": {
    "auto_suggest_resume": true,
    "recent_activity_days": 7
  }
}
```

## Troubleshooting

### Skills Not Working

```bash
# Verify skills are installed
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/

# Should show: sdd-plan, sdd-next, sdd-update, etc.

# If missing, reinstall the plugin
# See "Reinstallation" section
```

### CLI Commands Not Found

```bash
# Reinstall the Python package
cd ~/.claude/src/claude_skills
pip install -e .

# Verify
sdd --help
doc --help
test --help
```

### Permission Errors

```bash
# Set up project permissions
cd /path/to/your/project
sdd skills-dev setup-permissions -- update .

# Or tell Claude: "Set up SDD permissions for this project"
```

### Hooks Not Running

```bash
# Check if hooks are executable
ls -l ~/.claude/hooks/

# Make them executable
chmod +x ~/.claude/hooks/*
```

## Reinstallation

If you need to reinstall the plugin:

1. In Claude Code, type `/plugin`
2. Select **"Manage and install plugins"**
3. Find `sdd-toolkit` and click **"Uninstall"**
4. Exit Claude Code
5. Delete plugin cache:
   ```bash
   rm -rf ~/.claude/plugins/marketplaces/claude-sdd-toolkit
   rm -rf ~/.claude/plugins/cache/sdd-toolkit
   ```
6. Restart Claude Code
7. Follow the installation steps again

## Advanced Usage

### For Developers

Want to extend the toolkit or contribute?
- **[DEVELOPER.md](DEVELOPER.md)** - Add custom skills, commands, hooks
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and data flow

### For Teams

Want to use this with your team?
- Commit `specs/` directory to git for collaboration
- Share `.claude/settings.json` for consistent permissions
- Use spec templates for common patterns

### CLI Reference

The toolkit provides unified CLI commands:

```bash
# SDD workflows
sdd next-task <spec-id>           # Find next task
sdd update-status <spec> <task>   # Update progress
sdd validate <spec.json>          # Validate spec
sdd render <spec-id|spec.json>    # Render spec to markdown

# Documentation
sdd doc generate .                    # Generate docs
sdd doc query "search term"           # Search docs
sdd doc search "pattern"              # Pattern search

# Testing
sdd test run tests/                   # Run tests with AI debugging

# Development tools
sdd skills-dev setup-permissions -- update .   # Set up permissions
sdd skills-dev gendocs -- <skill-name>         # Generate skill docs
```

## Prerequisites

- **Claude Code** - Latest version
- **Python 3.9+** - For CLI tools
- **pip** - Python package manager
- **Git** (optional) - For version control

## Getting Help

- **Issues**: Report bugs at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Docs**: Full documentation at [Claude Code Docs](https://docs.claude.com/claude-code)
- **Examples**: Check `examples/` directory for sample workflows

## What's Included

The plugin installs these components:

**In `~/.claude/`:**
- `skills/` - 8 specialized skills for Claude
- `commands/` - Slash commands like `/sdd-start`
- `hooks/` - Automatic session detection
- `src/claude_skills/` - Python CLI tools

**In your PATH:**
- `sdd` - Unified CLI for all SDD, documentation, testing, and development commands
- `sdd-integration` - Integration utilities

## Tips for Success

1. **Start with a spec** - Always create a spec before major work
2. **Use /sdd-start often** - It keeps you on track
3. **Review specs** - Use multi-model review for important features
4. **Keep specs active** - Move completed specs to `completed/`
5. **Document as you go** - Run `code-doc` periodically
6. **Trust the process** - The workflow prevents forgotten requirements

## Next Steps

Ready to get started?

1. ✅ Install the plugin (see above)
2. ✅ Verify installation works
3. 📝 Create your first spec: "Plan a feature for X"
4. 🚀 Implement with `/sdd-start`
5. 🎉 Track progress and stay organized

**Questions?** Check [INSTALLATION.md](INSTALLATION.md) for detailed setup or [DEVELOPER.md](DEVELOPER.md) for customization.

---

**Version**: 0.1.0 | **License**: MIT | **Author**: Tyler Burleigh
