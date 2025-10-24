# Installation Guide

## Choose Your Installation Type

### 🔌 Plugin Installation (Team Members)
**Use this if**: You want to use the SDD toolkit in your projects

👉 **See [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md)**

### 🛠️ Development Installation (Contributors)
**Use this if**: You want to modify or contribute to the toolkit

👉 **Continue reading this document**

---

# Development Installation Guide

This guide covers the complete development installation of the SDD Toolkit, including both the Python package and the Claude Code integration.

## Overview

The Claude Skills system consists of two parts:

1. **Python Package** (`claude-skills`) - CLI tools at `~/.claude/src/claude_skills/`
2. **Claude Code Integration** - Skills, hooks, and commands in `~/.claude/`

Both work together to provide Spec-Driven Development and tooling for Claude Code.

## Directory Structure

After complete installation, your `~/.claude/` directory will contain:

```
~/.claude/
├── settings.json              # Global Claude Code settings
├── skills/                    # Claude Code skills (auto-detected)
│   ├── sdd-plan/             # Spec creation skill
│   ├── sdd-next/             # Task discovery skill
│   ├── sdd-update/           # Progress tracking skill
│   ├── sdd-validate/         # Validation skill
│   ├── sdd-plan-review/      # Multi-model review skill
│   ├── doc-query/            # Documentation query skill
│   ├── run-tests/            # Test execution skill
│   └── code-doc/             # Doc generation skill
├── commands/                  # Slash commands
│   └── sdd-start.md          # /sdd-start command
├── hooks/                     # Event hooks
│   ├── session-start         # Runs on session start
│   └── pre-tool-use          # Runs before tool execution
├── src/                       # Source code
│   └── claude_skills/        # Python package
└── INSTALLATION.md            # This file
```

## Part 1: Python Package Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (recommended)

### Step 1: Install the Package

```bash
# Navigate to the package directory
cd ~/.claude/src/claude_skills

# Install in editable mode (recommended)
pip install -e .
```

**What this does**:
- Installs Python dependencies (tree-sitter, parsers, etc.)
- Creates CLI commands in your PATH
- Enables immediate code changes without reinstall

### Step 2: Verify CLI Installation

```bash
# Check unified CLI commands are available
sdd --help
sdd doc --help
sdd test --help
sdd skills-dev --help

# Test specific commands
sdd validate --help
sdd doc generate --help
sdd test run --help
```

**Expected output**: Help text for each command

**Note**: The package now uses unified CLIs (`sdd`, `doc`, `test`, `skills-dev`) instead of separate commands. See [MIGRATION_GUIDE.md](src/claude_skills/MIGRATION_GUIDE.md) for details.

### Step 3: Handle PATH Issues (if needed)

If commands are not found:

```bash
# Find where pip installed scripts
python3 -m site --user-base

# Add to your shell profile (~/.bashrc or ~/.zshrc)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"  # macOS
export PATH="$HOME/.local/bin:$PATH"              # Linux

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

## Part 2: Claude Code Integration

### Skills Directory

Skills in `~/.claude/skills/` are automatically detected by Claude Code.

**Current skills**:

| Skill | Purpose | Files |
|-------|---------|-------|
| `sdd-plan` | Create specifications | SKILL.md, skill_system_v2.txt |
| `sdd-next` | Find next task | SKILL.md, execution_template_v1.txt |
| `sdd-update` | Track progress | SKILL.md |
| `sdd-validate` | Validate specs | SKILL.md |
| `sdd-plan-review` | Multi-model review | SKILL.md |
| `doc-query` | Query documentation | SKILL.md, scripts/ |
| `run-tests` | Run tests with AI | SKILL.md, scripts/ |
| `code-doc` | Generate docs | SKILL.md, scripts/ |

Each skill directory contains:
- `SKILL.md` - Instructions for Claude
- `README.md` - Human documentation
- `scripts/` (optional) - Python helper scripts

### Commands Directory

Slash commands in `~/.claude/commands/` are invoked with `/command-name`.

**Current commands**:

| Command | File | Purpose |
|---------|------|---------|
| `/sdd-start` | `sdd-start.md` | Resume or start SDD work interactively |

To create a new slash command:

```bash
# Create a markdown file
cat > ~/.claude/commands/my-command.md << 'EOF'
---
name: my-command
description: Description of what this command does
---

# Instructions for Claude

When the user runs /my-command, you should:
1. Do this
2. Then do that
3. Return results
EOF
```

### Hooks Directory

Hooks in `~/.claude/hooks/` run automatically on events.

**Current hooks**:

| Hook | Event | Purpose |
|------|-------|---------|
| `session-start` | Session begins | Detect SDD projects, show active specs |
| `pre-tool-use` | Before tool use | Offer permission setup for SDD tools |

**Hook script requirements**:
- Must be executable: `chmod +x ~/.claude/hooks/my-hook`
- Must output JSON (optional)
- Must exit with code 0 (non-blocking)
- Can read from stdin (for pre-tool-use)

### Settings File

`~/.claude/settings.json` contains global Claude Code configuration.

**Key sections**:

```json
{
  "permissions": {
    "allow": [
      "Skill(sdd-toolkit:sdd-plan)",
      "Skill(sdd-toolkit:sdd-next)",
      "Bash(sdd:*)",
      "Read(//**/specs/**)",
      "Write(//**/specs/active/**)"
    ]
  },
  "sdd": {
    "auto_suggest_resume": true,
    "recent_activity_days": 7,
    "session_timeout_hours": 1,
    "auto_offer_permissions": true
  },
  "hooks": {}
}
```

**To add permissions manually**:

```bash
# Edit settings.json
vim ~/.claude/settings.json

# Or use the helper command
sdd skills-dev setup-permissions -- update ~/.claude
```

## Part 3: Project-Level Setup

When you use Claude Skills in a project, some project-specific setup is needed.

### Step 1: Create Specs Directory

```bash
# In your project root
mkdir -p specs/{active,completed,archived}
```

**Directory purposes**:
- `active/` - Currently working JSON specifications
- `completed/` - Finished JSON specifications
- `archived/` - Old or abandoned JSON specifications

### Step 2: Configure Project Permissions

Option 1: Let Claude Code prompt you (recommended):

```
# In Claude Code, use any SDD skill
/sdd-start

# Claude will prompt:
# "Would you like to add SDD permissions to .claude/settings.json?"
# → Choose "Yes"
```

Option 2: Configure manually:

```bash
# In your project root
sdd skills-dev setup-permissions -- update .

# This creates/updates:
# ./claude/settings.json
```

### Step 3: Verify Setup

```bash
# Check permissions are configured
sdd skills-dev setup-permissions -- check .

# Expected output:
# {
#   "configured": true,
#   "settings_file": "/path/to/project/.claude/settings.json"
# }
```

## Part 4: First Time Usage

### Try /sdd-start

```
# In Claude Code
/sdd-start
```

**If no active specs**:
```
📋 No active SDD work found.

What would you like to do?
1. Write new spec
2. Something else
```

**If active specs exist**:
```
📋 Found 1 active specification:

1. ⚡ Add User Authentication
   ID: user-auth-2025-10-23-001
   Progress: 3/8 tasks (37%)

What would you like to do?
1. Continue with next task
2. Write new spec
3. Something else
```

### Create Your First Spec

```
I want to create a feature: Add rate limiting to API endpoints
```

Claude will:
1. Invoke `sdd-plan` skill
2. Explore your codebase
3. Create detailed specification
4. Save to `specs/active/`

### Execute Tasks

```
/sdd-start
```

Choose "Continue with next task"

Claude will:
1. Invoke `sdd-next` skill
2. Find next pending task
3. Provide implementation context
4. Help you implement it

### Mark Complete

```
Mark task as complete
```

Claude will:
1. Invoke `sdd-update` skill
2. Update task status
3. Increment progress counters
4. Journal completion

## Part 5: Advanced Configuration

### Custom Permissions

Edit `.claude/settings.json` or `project/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(my-custom-command:*)",
      "Read(//path/to/custom/**)",
      "Write(//path/to/output/**)"
    ],
    "deny": [
      "Bash(rm:*)",
      "Write(//etc/**)"
    ]
  }
}
```

### Custom Skills

Create a new skill:

```bash
# Create skill directory
mkdir ~/.claude/skills/my-skill

# Create SKILL.md
cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: What this skill does
---

# My Skill Instructions

When invoked, you should:
1. Do this
2. Then that
EOF

# Claude Code will auto-detect it
# Invoke with: Skill(my-skill)
```

### Custom Hooks

Create a new hook:

```bash
# Create hook script
cat > ~/.claude/hooks/post-task-complete << 'EOF'
#!/bin/bash
# Runs after a task is marked complete

# Read task info from stdin
task_info=$(cat)

# Do something useful
echo "$task_info" | jq .task_id >> ~/.claude/task-log.txt

exit 0
EOF

# Make executable
chmod +x ~/.claude/hooks/post-task-complete
```

## Part 6: Troubleshooting

### Issue: Skills not detected

**Symptom**: `/sdd-start` or skill invocations fail

**Solution**:
```bash
# Check skills directory exists
ls ~/.claude/skills/

# Check each skill has SKILL.md
ls ~/.claude/skills/*/SKILL.md

# Restart Claude Code
```

### Issue: CLI commands not found

**Symptom**: `bash: sdd-next: command not found`

**Solution**:
```bash
# Reinstall package
cd ~/.claude/src/claude_skills
pip install -e .

# Check PATH
echo $PATH

# Add to PATH if needed
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

### Issue: Permission denied

**Symptom**: Claude Code says "Permission denied for Bash(sdd:*)"

**Solution**:
```bash
# Check permissions in settings
cat ~/.claude/settings.json | grep "Bash(sdd:"

# If missing, add with helper
sdd skills-dev setup-permissions -- update ~/.claude

# Or edit manually
```

### Issue: Hooks not running

**Symptom**: Session-start hook doesn't detect specs

**Solution**:
```bash
# Check hooks are executable
ls -l ~/.claude/hooks/

# Make executable if needed
chmod +x ~/.claude/hooks/*

# Check hook output manually
~/.claude/hooks/session-start
```

### Issue: Specs directory not found

**Symptom**: "No specs/active directory found"

**Solution**:
```bash
# Create specs structure
mkdir -p specs/{active,completed,archived}

# Or let sdd-plan create it automatically
```

## Part 7: Updating

### Update Python Package

```bash
cd ~/.claude/src/claude_skills
git pull origin main
pip install -e .
```

### Update Skills

```bash
cd ~/.claude/skills/sdd-plan
git pull origin main

# Or update all skills
cd ~/.claude
git pull origin main
```

### Update Hooks

```bash
cd ~/.claude/hooks
# Edit hook files as needed
# Hooks are bash scripts - just edit and save
```

## Part 8: Uninstallation

### Remove Python Package

```bash
pip uninstall claude-skills
```

### Remove Skills (optional)

```bash
# Remove specific skill
rm -rf ~/.claude/skills/sdd-plan

# Or remove all
rm -rf ~/.claude/skills/*
```

### Remove Hooks (optional)

```bash
rm -rf ~/.claude/hooks/*
```

### Clean Project Files

```bash
# In each project
rm -rf specs/
rm -rf .claude/settings.json
```

## Next Steps

- **Quick Start**: See [GETTING_STARTED.md](src/claude_skills/GETTING_STARTED.md)
- **Workflows**: See examples in action
- **CLI Reference**: Learn all commands
- **Customize**: Create your own skills and hooks

---

**Need help?** Check the troubleshooting section or open an issue on GitHub.
