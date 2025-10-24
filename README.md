# SDD Toolkit - Claude Code Plugin

> Professional spec-driven development tools for Claude Code

[![Plugin Version](https://img.shields.io/badge/version-2.0.0-blue.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)]()
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()

## What is This?

A comprehensive Claude Code plugin that brings professional, plan-first development workflows to your AI-assisted coding sessions.

**Installation**: See [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md)

**For Development Setup**: See [INSTALLATION.md](INSTALLATION.md)

## Quick Start

1. Install the plugin (see [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md))
2. In Claude Code, say: "Create a spec for adding user authentication"
3. Claude uses the SDD toolkit to create a detailed specification
4. Resume anytime with `/sdd-start`

## About This Directory

This is your `~/.claude/` directory (or the plugin installation at `~/.claude/plugins/sdd-toolkit/`) - the home for Claude Code configuration, skills, and automation. It contains:

✅ **SDD Toolkit** - Spec-Driven Development workflow
✅ **Documentation Tools** - Generate and query codebase docs
✅ **Test Management** - AI-assisted test execution and debugging
✅ **Automation** - Hooks, commands, and CLI utilities

## Directory Structure

```
~/.claude/
├── INSTALLATION.md           # Complete installation guide ← START HERE
├── README.md                 # This file
├── settings.json             # Global Claude Code settings
│
├── skills/                   # Claude Code skills (auto-detected)
│   ├── sdd-plan/            # Create specifications
│   ├── sdd-next/            # Find next task
│   ├── sdd-update/          # Track progress
│   ├── sdd-validate/        # Validate specs
│   ├── sdd-plan-review/     # Multi-model review
│   ├── doc-query/           # Query documentation
│   ├── run-tests/           # Execute tests
│   └── code-doc/            # Generate docs
│
├── commands/                 # Slash commands
│   └── sdd-start.md         # /sdd-start - Resume work
│
├── hooks/                    # Event hooks (auto-run)
│   ├── session-start        # Detect active work on session start
│   └── pre-tool-use         # Offer permission setup
│
└── src/                      # Source code
    └── claude_skills/       # Python package (CLI tools)
        ├── sdd_next/        # Task discovery
        ├── sdd_update/      # Progress tracking
        ├── sdd_validate/    # Validation
        ├── doc_query/       # Doc queries
        ├── run_tests/       # Test execution
        ├── code_doc/        # Doc generation
        ├── dev_tools/       # Development utilities
        └── common/          # Shared utilities
```

## Quick Start

### 1. Installation

```bash
# See complete guide
cat INSTALLATION.md

# Or quick install
cd ~/.claude/src/claude_skills
pip install -e .
```

### 2. Verify Setup

```bash
# Check unified CLI commands
sdd --help
doc --help
test --help
skills-dev --help

# Check Claude Code integration
ls ~/.claude/skills/
```

### 3. First Workflow

In Claude Code:

```
I want to create a feature: Add user authentication
```

Claude invokes `sdd-plan` skill automatically to create a specification.

Then resume work anytime with:

```
/sdd-start
```

## What's in Each Directory

### `/skills` - Claude Code Skills

**Purpose**: Extend Claude's capabilities with specialized workflows

**How they work**:
- Claude Code auto-detects skills in this directory
- Each skill has `SKILL.md` with instructions for Claude
- Invoke via: `Skill(skill-name)` or through natural conversation
- Claude decides when to use based on context

**Available skills**:

| Skill | Use Case | Example |
|-------|----------|---------|
| `sdd-plan` | Create specs | "Plan a new feature for rate limiting" |
| `sdd-next` | Find next task | "What should I work on next?" |
| `sdd-update` | Track progress | "Mark task as complete" |
| `sdd-validate` | Validate specs | "Check if my spec is valid" |
| `sdd-plan-review` | Multi-model review | "Get feedback on this spec" |
| `doc-query` | Query docs | "What classes handle auth?" |
| `run-tests` | Run tests | "Run all tests and help debug failures" |
| `code-doc` | Generate docs | "Document this codebase" |

### `/commands` - Slash Commands

**Purpose**: User-invoked commands in Claude Code

**How they work**:
- Type `/command-name` in Claude Code
- Claude reads the `.md` file and follows instructions
- Great for interactive, step-by-step workflows

**Available commands**:

| Command | Purpose |
|---------|---------|
| `/sdd-start` | Resume or start SDD work with interactive menu |

**Create your own**:

```bash
cat > ~/.claude/commands/my-command.md << 'EOF'
---
name: my-command
description: What it does
---

Instructions for Claude...
EOF
```

### `/hooks` - Event Hooks

**Purpose**: Automatic actions triggered by events

**How they work**:
- Bash scripts that run on specific events
- Must be executable (`chmod +x`)
- Output JSON (optional)
- Always exit 0 (non-blocking)

**Available hooks**:

| Hook | Event | Purpose |
|------|-------|---------|
| `session-start` | New session | Detect SDD projects, show active specs |
| `pre-tool-use` | Before tool | Offer permission setup |

**Hook events**:
- `session-start` - When Claude Code session begins
- `session-end` - When session ends
- `pre-tool-use` - Before any tool is used
- `post-tool-use` - After any tool is used
- `user-prompt-submit` - When user submits a message

**Create your own**:

```bash
cat > ~/.claude/hooks/my-hook << 'EOF'
#!/bin/bash
# Do something useful
echo '{"status": "success"}'
exit 0
EOF
chmod +x ~/.claude/hooks/my-hook
```

### `/src/claude_skills` - Python Package

**Purpose**: CLI tools and shared libraries

**How it works**:
- Installed via `pip install -e .`
- Creates CLI commands in your PATH
- Used by skills and hooks
- Shared utilities for all tools

**CLI commands provided** (unified architecture):

| Command | Purpose | Example |
|---------|---------|---------|
| `sdd` | SDD workflows | `sdd next-task my-spec-001` |
| `sdd` | Progress tracking | `sdd update-status my-spec-001 task-1 completed` |
| `sdd` | Spec validation | `sdd validate specs/active/my-spec.json` |
| `doc` | Doc queries | `doc search "authentication"` |
| `doc` | Doc generation | `doc generate .` |
| `test` | Test execution | `test run tests/` |
| `skills-dev` | Session management | `skills-dev start-helper -- format-output` |
| `skills-dev` | Permission setup | `skills-dev setup-permissions -- update .` |
| `skills-dev` | Generate skill docs | `skills-dev gendocs -- sdd-validate` |

**Note**: See [MIGRATION_GUIDE.md](src/claude_skills/MIGRATION_GUIDE.md) for details on the unified CLI architecture.

**Package structure**:

```
claude_skills/
├── sdd_next/           # Task discovery module
├── sdd_update/         # Progress tracking module
├── sdd_validate/       # Validation module
├── doc_query/          # Documentation queries
├── run_tests/          # Test execution
├── code_doc/           # Doc generation
├── dev_tools/          # Development utilities
├── common/             # Shared utilities
└── tests/              # Test suite
```

## Configuration

### Global Settings

`~/.claude/settings.json` contains your Claude Code configuration:

```json
{
  "permissions": {
    "allow": [
      "Skill(sdd-plan)",
      "Bash(sdd:*)",
      "Bash(doc:*)",
      "Bash(test:*)",
      "Read(//**/specs/**)"
    ]
  },
  "sdd": {
    "auto_suggest_resume": true,
    "recent_activity_days": 7
  }
}
```

**Key sections**:
- `permissions.allow` - Pre-approved operations
- `permissions.deny` - Blocked operations
- `permissions.ask` - Prompt before use
- `sdd` - SDD-specific settings
- `hooks` - Hook configuration

### Project Settings

Each project can have `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read(//**/specs/**)",
      "Write(//**/specs/active/**)"
    ]
  }
}
```

**Setup automatically**:
```bash
skills-dev setup-permissions -- update .
```

Or let Claude Code prompt you when first using SDD tools.

## Common Workflows

### Create a New Feature

```
1. In Claude Code: "Create a spec for adding rate limiting"
2. Claude uses sdd-plan skill automatically
3. Result: specs/active/rate-limiting-2025-10-23-001.json
4. Later: /sdd-start to resume
5. Complete tasks iteratively
```

### Resume Work

```
1. Open Claude Code in project
2. Type: /sdd-start
3. Claude shows active specs and progress
4. Choose "Continue with next task"
5. Claude uses sdd-next skill
6. Implement, complete, repeat
```

### Generate Documentation

```
1. "Use code-doc skill to document this project"
2. Claude generates docs/documentation.json
3. Query with: "What classes handle authentication?"
4. Claude uses doc-query skill to search
```

### Run and Debug Tests

```
1. "Use run-tests skill to run all tests"
2. Claude executes tests
3. If failures: Claude analyzes and suggests fixes
4. Implement fixes
5. Re-run tests
```

## How Everything Works Together

### The Flow

```
User Request
    ↓
Claude Code (reads CLAUDE.md, skills, commands)
    ↓
Skills (invoke CLI tools)
    ↓
CLI Tools (from claude_skills package)
    ↓
Project Files (specs/, code, tests)
    ↓
Results back to Claude
    ↓
Response to User
```

### Example: Creating a Spec

```
User: "Create a spec for user authentication"
    ↓
Claude detects intent, invokes Skill(sdd-plan)
    ↓
sdd-plan skill reads SKILL.md instructions
    ↓
sdd-plan uses doc-query CLI to explore codebase
    ↓
sdd-plan generates specification
    ↓
Spec saved to specs/active/user-auth-2025-10-23-001.json
    ↓
Claude shows spec summary to user
```

### Example: Resuming Work

```
User: /sdd-start
    ↓
SlashCommand triggers commands/sdd-start.md
    ↓
Claude runs skills-dev start-helper CLI to find active specs
    ↓
Claude presents options to user
    ↓
User chooses "Continue with next task"
    ↓
Claude invokes Skill(sdd-next)
    ↓
sdd-next CLI finds next task in spec
    ↓
Claude shows task details and helps implement
```

### Example: Session Hook

```
User opens Claude Code
    ↓
session-start hook runs automatically
    ↓
Hook checks for specs/active/ directory
    ↓
Hook finds active specifications
    ↓
Hook creates marker file with spec info
    ↓
Claude reads marker proactively
    ↓
Claude greets: "I found active specs. Run /sdd-start to resume?"
```

## Extending the System

### Add a New Skill

```bash
# 1. Create directory
mkdir ~/.claude/skills/my-skill

# 2. Create SKILL.md
cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: What this skill does
---

# My Skill

When invoked, you should:
1. Do this
2. Then that
3. Return results
EOF

# 3. Use it
# In Claude Code: "Use my-skill to do something"
```

### Add a New Command

```bash
# 1. Create command file
cat > ~/.claude/commands/my-command.md << 'EOF'
---
name: my-command
description: Interactive command
---

# My Command

Guide the user through:
1. Step one
2. Step two
3. Step three
EOF

# 2. Use it
# In Claude Code: /my-command
```

### Add a New Hook

```bash
# 1. Create hook script
cat > ~/.claude/hooks/post-task-complete << 'EOF'
#!/bin/bash
task_data=$(cat)  # Read from stdin
echo "$task_data" >> ~/task-log.txt
exit 0
EOF

# 2. Make executable
chmod +x ~/.claude/hooks/post-task-complete
```

### Add a New CLI Tool

```bash
# 1. Add to claude_skills package
cd ~/.claude/src/claude_skills/claude_skills
mkdir my_tool
# ... implement your tool ...

# 2. Add entry point to pyproject.toml
[project.scripts]
my-tool = "claude_skills.my_tool.cli:main"

# 3. Reinstall
cd ~/.claude/src/claude_skills
pip install -e .

# 4. Use it
my-tool --help
```

## Troubleshooting

### Skills not working

```bash
# Check skills directory
ls ~/.claude/skills/*/SKILL.md

# Check permissions
cat ~/.claude/settings.json | grep Skill

# Restart Claude Code
```

### CLI commands not found

```bash
# Reinstall package
cd ~/.claude/src/claude_skills
pip install -e .

# Check unified CLIs
sdd --help
doc --help
test --help
```

### Hooks not running

```bash
# Check executable
ls -l ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/*

# Test manually
~/.claude/hooks/session-start
```

## Documentation

- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md) - Complete setup
- **Quick Start**: [src/claude_skills/GETTING_STARTED.md](src/claude_skills/GETTING_STARTED.md)
- **Workflows**: [src/claude_skills/docs/workflows.md](src/claude_skills/docs/workflows.md)
- **CLI Reference**: [src/claude_skills/docs/cli-reference.md](src/claude_skills/docs/cli-reference.md)
- **Skills Reference**: Each skill has README.md in its directory

## Getting Help

- **Claude Code Docs**: https://docs.claude.com/claude-code
- **GitHub Issues**: Report bugs or request features
- **Community**: Share workflows and customizations

---

**Ready to get started?** See [INSTALLATION.md](INSTALLATION.md) for step-by-step setup instructions.
