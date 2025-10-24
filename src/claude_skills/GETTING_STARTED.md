# Getting Started with Claude Skills

Welcome! This guide will help you set up and start using the Spec-Driven Development (SDD) toolkit for Claude Code.

## What is This?

**claude-skills** is a Python package that provides:
- 📋 **Spec-Driven Development** - Plan-first methodology for reliable AI-assisted coding
- 🔍 **Code Documentation** - Generate and query searchable codebase documentation
- 🧪 **Test Management** - Run and debug tests with AI assistance
- 🛠️ **Development Tools** - CLI utilities for workflow automation

## Prerequisites

- **Python 3.9+** (check with `python3 --version`)
- **pip** (Python package manager)
- **Claude Code** (the AI-powered IDE)
- **Git** (recommended, for version control)

## Quick Installation

### Step 1: Install the Package

```bash
# Clone or navigate to the repository
cd /path/to/claude_skills

# Install in editable mode (recommended for development)
pip install -e .

# OR: Install from a specific path
pip install -e ~/Documents/private/.claude/src/claude_skills
```

### Step 2: Verify Installation

```bash
# Check that unified CLI commands are available
sdd --help
doc --help
test --help
skills-dev --help

# You should see help text for each command
```

**Note**: The package now uses unified CLIs (`sdd`, `doc`, `test`, `skills-dev`). See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details.

### Step 3: Verify Claude Code Integration

The skills in `~/.claude/skills/` are automatically detected by Claude Code. Verify:

```bash
# In Claude Code, type:
/help

# You should see:
# - /sdd-start - Resume or start spec-driven development
```

## First Time Setup

### Configure Permissions (Optional but Recommended)

When you first use SDD tools in a project, Claude Code will offer to configure permissions automatically. This allows seamless use of SDD commands without repeated prompts.

**Option 1: Let Claude Code handle it**
- Just use `/sdd-start` or invoke any SDD skill
- Claude Code will prompt you to add permissions
- Accept the prompt (one-time per project)

**Option 2: Configure manually**
```bash
# In your project directory
skills-dev setup-permissions -- update .

# This adds SDD permissions to .claude/settings.json
```

### Verify Setup

```bash
# Check if permissions are configured
skills-dev setup-permissions -- check .

# Expected output:
# {
#   "configured": true,
#   "settings_file": "/path/to/project/.claude/settings.json"
# }
```

## Your First Workflow

### Scenario: Create a New Feature

Let's create a simple feature specification and work through it.

#### 1. Start a New Spec

In Claude Code, say:
```
I want to create a new feature: Add user authentication to the API
```

Claude will invoke the `sdd-plan` skill to:
- Understand your intent
- Explore your codebase
- Create a detailed specification with phases and tasks
- Save it to `specs/active/`

#### 2. Resume Work

Later, when you return to the project:

```
/sdd-start
```

Claude will:
- Detect active specifications
- Show your progress
- Offer to continue with the next task

#### 3. Execute Tasks

When ready to work on a task:

```
Use sdd-next to find and prepare the next task
```

Or directly in the CLI:
```bash
sdd-next next-task <spec-id>
sdd-next prepare-task <spec-id>
```

#### 4. Track Progress

After completing work:

```
Use sdd-update to mark task as complete
```

Or directly:
```bash
sdd-update complete <spec-id> <task-id>
sdd-update journal <spec-id> "Implemented authentication endpoints"
```

## Available Tools

### Claude Code Skills

These are invoked by Claude automatically or via explicit requests:

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| **sdd-plan** | Create specifications | Starting new features or refactoring |
| **sdd-next** | Find next task | Continuing work on active specs |
| **sdd-update** | Track progress | Marking tasks complete, journaling |
| **sdd-validate** | Validate specs | Checking spec file integrity |
| **sdd-plan-review** | Multi-model review | Getting feedback on specs |
| **code-doc** | Generate docs | First time in codebase, after major changes |
| **doc-query** | Query docs | Understanding code structure |
| **run-tests** | Run tests with AI | Debugging test failures |

### CLI Commands

These can be run directly in your terminal:

| Command | Purpose | Example |
|---------|---------|---------|
| `sdd-next` | Task discovery | `sdd-next next-task my-spec-001` |
| `sdd-update` | Progress tracking | `sdd-update complete my-spec-001 task-1` |
| `sdd-validate` | Spec validation | `sdd-validate validate specs/active/my-spec.json` |
| `doc-query` | Documentation queries | `doc-query search "authentication"` |
| `run-tests` | Test execution | `run-tests run tests/` |
| `code-doc` | Generate documentation | `code-doc generate .` |
| `sdd-start-helper` | Session management | `sdd-start-helper format-output` |
| `setup-project-permissions` | Permission setup | `setup-project-permissions update .` |
| `claude-skills-gendocs` | Generate skill docs | `claude-skills-gendocs sdd-validate` |

### Slash Commands

Available in Claude Code:

| Command | Purpose |
|---------|---------|
| `/sdd-start` | Resume or start SDD work with interactive options |

## Common Workflows

### Workflow 1: Create and Execute a Feature

```bash
# 1. In Claude Code, request feature
"Create a spec for adding rate limiting to the API"

# 2. Claude invokes sdd-plan skill automatically
# Result: specs/active/rate-limiting-2025-10-23-001.json

# 3. Later, resume work
/sdd-start

# 4. Claude shows options, you choose "Continue with next task"
# Claude invokes sdd-next skill automatically

# 5. Complete the task
# Claude invokes sdd-update skill when done

# 6. Repeat steps 3-5 until spec complete
```

### Workflow 2: Generate and Query Documentation

```bash
# 1. Generate documentation for your codebase
"Use code-doc skill to document this project"

# Result: docs/documentation.json created

# 2. Query the documentation
"What classes handle authentication?"

# Claude uses doc-query skill to search documentation

# 3. Find specific code
doc-query find-class AuthService
doc-query search "JWT token"
doc-query dependencies app/services/auth.py
```

### Workflow 3: Run and Debug Tests

```bash
# 1. Run tests
"Use run-tests skill to run all tests"

# 2. If failures occur, Claude uses AI consultation
# Claude analyzes failures and suggests fixes

# 3. Manual test run
run-tests run tests/unit/
run-tests consult "AuthService test failing with 401 error"
```

### Workflow 4: Validate Specifications

```bash
# 1. Check spec integrity
sdd-validate validate specs/active/my-spec.json

# 2. Preview auto-fixable issues
sdd-validate fix specs/active/my-spec.json --preview

# 3. Apply fixes
sdd-validate fix specs/active/my-spec.json

# 4. Generate detailed report
sdd-validate report specs/active/my-spec.json --output report.md
```

## Directory Structure

After installation and first use, your project will have:

```
your-project/
├── .claude/
│   ├── settings.json          # Project permissions (auto-created)
│   └── settings.local.json    # Local overrides
├── specs/
│   ├── active/                # Currently working specifications (.json files)
│   ├── completed/             # Finished specifications
│   └── archived/              # Old or abandoned specs
├── docs/                      # Generated documentation (optional)
│   └── documentation.json
└── your code...
```

## Configuration

### Global Settings

Located at `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Skill(sdd-plan)",
      "Skill(sdd-next)",
      "Bash(sdd-next:*)",
      "Read(//**/specs/**)",
      "Write(//**/specs/active/**)"
    ]
  },
  "sdd": {
    "auto_suggest_resume": true,
    "recent_activity_days": 7,
    "session_timeout_hours": 1,
    "auto_offer_permissions": true
  }
}
```

### Project Settings

Located at `your-project/.claude/settings.json` (created automatically):

```json
{
  "permissions": {
    "allow": [
      "Read(//**/specs/**)",
      "Write(//**/specs/active/**)",
      "Edit(//**/specs/active/**)"
    ]
  }
}
```

## Troubleshooting

### Issue: Command not found

```bash
$ sdd-next --help
bash: sdd-next: command not found
```

**Solution**: Reinstall the package and check your PATH

```bash
pip install -e /path/to/claude_skills

# Check if installed
pip show claude-skills

# Find where commands are installed
which sdd-next

# If not in PATH, add to your shell profile
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

### Issue: Permission denied errors in Claude Code

```
Error: Permission denied for Bash(sdd-next:*)
```

**Solution**: Configure project permissions

```bash
setup-project-permissions update .
```

Or accept the permission prompt when Claude Code asks.

### Issue: Specs directory not found

```
Error: No specs/active directory found
```

**Solution**: Create the directory structure

```bash
mkdir -p specs/{active,completed,archived}
```

Or let `sdd-plan` create it automatically when you create your first spec.

### Issue: Documentation not found (doc-query)

```
Error: Documentation not found
```

**Solution**: Generate documentation first

In Claude Code:
```
Use code-doc skill to generate documentation for this project
```

Or via CLI:
```bash
code-doc generate .
```

### Issue: Hooks not triggering

If the session-start hook doesn't detect SDD projects:

```bash
# Check hook execution permissions
chmod +x ~/.claude/hooks/*

# Check hook files exist
ls -la ~/.claude/hooks/

# Verify auto-offer is enabled
cat ~/.claude/settings.json | grep auto_offer_permissions
```

## Next Steps

- **Read the docs**: Check `/docs` for detailed reference documentation
- **Explore examples**: See `/examples` for complete workflow guides
- **Join the community**: Share feedback and contribute improvements
- **Customize**: Adjust settings and workflows to your needs

## Getting Help

- **CLI help**: Run any command with `--help` flag
- **Skill documentation**: Check `~/.claude/skills/*/SKILL.md`
- **Issue tracker**: Report bugs or request features on GitHub
- **Claude Code docs**: Visit https://docs.claude.com/claude-code

---

**Happy coding with Claude Skills! 🚀**
