# Getting Started

Complete guide to installing and setting up the SDD Toolkit.

## Prerequisites

- **Claude Code** - Latest version installed
- **Python 3.9+** - For CLI tools
- **pip** - Python package manager
- **Node.js >= 18.x** - For OpenCode provider (optional)
- **Terminal access** - For verification commands

## Installation

### 1. Install the Plugin

Launch Claude Code and install the plugin from the marketplace:

```bash
claude  # Launch Claude Code
```

In Claude Code:
```
/plugins → Add from marketplace → tylerburleigh/claude-sdd-toolkit
```

Wait for the plugin to clone and click **Install** when prompted.

### 2. Exit Claude Code

**Important**: Exit Claude Code completely before installing dependencies.

### 3. Install Dependencies

The plugin requires both Python and Node.js dependencies. Choose one method:

#### Unified Installation (Recommended)

```bash
# Navigate to plugin directory
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills

# Install Python package
pip install -e .

# Install all dependencies (pip + npm)
sdd skills-dev install
```

This installs:
- Python package and CLI tools
- Node.js dependencies for OpenCode provider
- Verifies all installations

#### Manual Installation (Alternative)

**Python package only:**
```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**OpenCode provider** (optional, requires Node.js >= 18.x):
```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills/claude_skills/common/providers
npm install
```

See [providers/OPENCODE.md](providers/OPENCODE.md) for OpenCode setup details.

### 4. Verify Installation

```bash
# Check installation status
sdd skills-dev verify-install

# Or get JSON output
sdd skills-dev verify-install --json
```

This verifies:
- Python package installation
- `sdd` command availability
- OpenCode provider availability
- Node.js dependencies

### 5. Restart Claude Code

Restart Claude Code completely to load the plugin and skills.

### 6. Configure Your Project

Open your project in Claude Code and run:

```
/sdd-setup
```

This creates configuration files in your project:
- `.claude/settings.local.json` - Required permissions for SDD skills
- `.claude/sdd_config.json` - CLI output preferences
- `.claude/ai_config.yaml` - AI model defaults

**Note**: Run this once per project.

## Verification

### Test CLI Tools

```bash
# Check unified CLI
sdd --help

# Check subcommands
sdd doc --help
sdd test --help
sdd validate --help
```

You should see help text for each command.

### Test in Claude Code

Verify the setup:

```
/sdd-setup
```

This should configure project permissions successfully.

Then try creating a spec:

```
Let's create a spec for a chatbot feature
```

Claude should use the `sdd-plan` skill to create a specification.

## First Workflow

Once installed, try this workflow:

```
You: Create a spec for a CLI Pomodoro timer

Claude: [Analyzes codebase, creates specs/pending/pomodoro-timer-001.json]

You: /sdd-begin

Claude: Found pending spec "pomodoro-timer-001"
        Ready to activate and start implementing?

You: Yes

Claude: [Uses one-call prepare-task to get complete context]
        Task 1-1: Create Timer class with start/pause/stop methods

        Context from previous work:
        - No previous tasks (first in spec)
        - Phase: Foundation (0% complete)
        - Target file: src/timer.py

        [Implements task, updates status]

You: /sdd-begin

Claude: [prepare-task provides rich context in single call]
        Task 1-2: Add notification system...

        Context from previous work:
        - Previous: task-1-1 (Timer class created with basic structure)
        - Phase: Foundation (33% complete)
        - Related files: src/timer.py modified

        [Continues through tasks with automatic context loading]
```

**Key Features:**

- **One-Call Context**: `prepare-task` now provides all task info, dependencies, phase progress, and previous work in a single call
- **No Extra Commands**: No need for separate `task-info` or `check-deps` calls
- **Automatic Continuity**: Each task includes journal summaries from previous work
- **File Tracking**: See which files were modified by related tasks

See [workflows.md](workflows.md) for more workflow examples and [cli-reference.md](cli-reference.md) for detailed prepare-task documentation.

## Troubleshooting

### Skills Not Working

If skills aren't detected:

1. **Check plugin directory exists:**
   ```bash
   ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit
   ```

2. **Check skills are present:**
   ```bash
   ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
   ```

3. **Restart Claude Code** completely

### CLI Commands Not Found

If `sdd` commands aren't found:

1. **Reinstall Python package:**
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   ```

2. **Check your PATH** includes pip's bin directory:
   ```bash
   # For macOS
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"

   # For Linux
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Make it permanent** by adding to shell profile:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Permission Errors

If you get permission errors when using SDD tools:

1. **Run setup in Claude Code:**
   ```
   /sdd-setup
   ```

2. **Or ask Claude:**
   ```
   Set up SDD permissions for this project
   ```

See [troubleshooting.md](troubleshooting.md) for more help.

## Updating the Plugin

To update to the latest version:

### 1. Update Plugin Marketplace

In Claude Code:
```
/plugins → Manage marketplaces → claude-sdd-toolkit → Update marketplace
```

### 2. Update Installed Plugin

```
/plugins → Manage and uninstall → claude-sdd-toolkit → sdd-toolkit → Update now
```

### 3. Restart Claude Code

Exit completely and restart.

### 4. Reinstall Python Package

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**Why?** Marketplace update gets the latest code, plugin update installs it to Claude Code, restart loads new skills, and reinstall updates CLI commands.

## Next Steps

Now that you're set up:

1. **Learn core concepts**: See [core-concepts.md](core-concepts.md)
2. **Explore workflows**: Check [workflows.md](workflows.md)
3. **Configure settings**: Review [configuration.md](configuration.md)
4. **Try examples**: Start with simple specs and build up
5. **Generate documentation**: Run `sdd doc analyze-with-ai .` in your project

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Documentation**: [README.md](../README.md) for overview
- **Claude Code Docs**: [Claude Code Documentation](https://docs.claude.com/claude-code)
- **Architecture**: [architecture.md](architecture.md) for system design

---

*Last updated: 2025-11-22*
