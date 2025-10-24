# Installing SDD Toolkit Plugin

## Prerequisites

- **Claude Code** - Latest version installed
- **Python 3.9+** - For CLI tools
- **pip** - Python package manager
- **Terminal access** - For verification commands

## Installation Steps

### 1. Launch Claude Code

Open your terminal and launch Claude Code:

```bash
claude
```

### 2. Open Plugin Manager

In Claude Code, type:

```
/plugin
```

Press Enter.

### 3. Add from Marketplace

From the plugin menu, select **"Add from marketplace"** (or similar option).

### 4. Enter Repository

When prompted for the repository, enter:

```
tylerburleigh/claude-sdd-toolkit
```

### 5. Wait for Clone

Claude Code will clone the repository. This may take a moment.

### 6. Install Plugin

Once cloning is complete, click **"Install"** when prompted.

### 7. Exit Claude Code Completely

**Important**: Before installing Python dependencies, you must exit Claude Code completely. Close the application entirely (not just the window).

### 8. Install Python Dependencies

The plugin requires Python dependencies. Open a terminal and run:

```bash
# Navigate to the plugin directory
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills

# Install the package
pip install -e .
```

This installs the CLI tools (`sdd`, `doc`, `test`) that the skills use.

### 9. Restart Claude Code

Now restart Claude Code. The plugin and all its components will be active.

### 10. Configure Project Permissions

Open your project in Claude Code and run:

```
/sdd-setup
```

This will:
- Create `.claude/settings.json` in your project
- Add all required permissions for SDD skills and tools
- Prepare your project for spec-driven development

You should see a success message confirming the setup is complete.

**Note**: You only need to run this once per project.

## Verification

Verify the installation was successful:

### Check CLI Tools

```bash
# Check CLI commands are available
sdd --help
doc --help
test --help

# Check specific commands
sdd validate --help
doc generate --help
```

You should see help text for each command.

### Check Skills

```bash
# List installed skills
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
```

You should see these directories:
- `sdd-plan/`
- `sdd-next/`
- `sdd-update/`
- `sdd-validate/`
- `sdd-plan-review/`
- `code-doc/`
- `doc-query/`
- `run-tests/`

### Test in Claude Code

First, verify the setup command works:

```
/sdd-setup
```

This should configure your project permissions. If it completes successfully, everything is installed correctly!

Then try creating a spec:

```
Create a spec for adding a new feature
```

Claude should use the `sdd-plan` skill to create a specification.

Or try the workflow command:

```
/sdd-start
```

This should show the SDD workflow menu.

## Troubleshooting

### Skills Not Working

If skills aren't detected:

1. **Check plugin directory exists**:
   ```bash
   ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit
   ```

2. **Check skills are present**:
   ```bash
   ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
   ```

3. **Restart Claude Code** completely

### CLI Commands Not Found

If `sdd`, `doc`, or `test` commands aren't found:

1. **Reinstall Python package**:
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

3. **Add to shell profile** (make it permanent):
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Permission Errors

If you get permission errors when using SDD tools:

1. **Set up project permissions**:
   ```bash
   cd /path/to/your/project
   sdd skills-dev setup-permissions -- update .
   ```

2. **Or tell Claude**:
   ```
   Set up SDD permissions for this project
   ```

### Plugin Not Loading

If the plugin doesn't appear to load:

1. **Check plugin.json exists**:
   ```bash
   cat ~/.claude/plugins/marketplaces/claude-sdd-toolkit/.claude-plugin/plugin.json
   ```

2. **Check for errors** in Claude Code output

3. **Reinstall** (see Reinstallation section)

## Updating the Plugin

To update to the latest version:

```bash
# Pull latest changes
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit
git pull origin main

# Reinstall Python package
cd src/claude_skills
pip install -e .

# Restart Claude Code
```

## Reinstallation

If you need to completely reinstall the plugin:

### 1. Uninstall via Claude Code

1. In Claude Code, type `/plugin`
2. Select **"Manage and install plugins"**
3. Find `sdd-toolkit` in the list
4. Click **"Uninstall"**

### 2. Delete Plugin Cache

Exit Claude Code completely, then:

```bash
# Delete marketplace copy
rm -rf ~/.claude/plugins/marketplaces/claude-sdd-toolkit

# Delete plugin cache
rm -rf ~/.claude/plugins/cache/sdd-toolkit
```

### 3. Reinstall

1. Restart Claude Code
2. Follow the installation steps from the beginning

## What Gets Installed

After successful installation, you'll have:

### In `~/.claude/plugins/marketplaces/claude-sdd-toolkit/`

**Skills** (`skills/`):
- `sdd-plan/` - Create specifications
- `sdd-next/` - Find next task
- `sdd-update/` - Track progress
- `sdd-validate/` - Validate specs
- `sdd-plan-review/` - Multi-model review
- `code-doc/` - Generate documentation
- `doc-query/` - Query documentation
- `run-tests/` - Run and debug tests

**Commands** (`commands/`):
- `sdd-start.md` - `/sdd-start` command

**Hooks** (`hooks/`):
- `session-start` - Auto-detect active work
- `pre-tool-use` - Permission setup helper

**Source Code** (`src/claude_skills/`):
- Python package with CLI tools

### In your PATH
- `sdd` - SDD workflow CLI
- `doc` - Documentation CLI
- `test` - Testing CLI

## Next Steps

Once installed:

1. **Create your first spec**:
   ```
   Create a spec for [your feature]
   ```

2. **Try the workflow**:
   ```
   /sdd-start
   ```

3. **Read the docs**:
   - [README.md](README.md) - User guide
   - [DEVELOPER.md](DEVELOPER.md) - Extending the toolkit
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design

## Getting Help

- **Issues**: Report problems at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Documentation**: See [README.md](README.md) for complete documentation
- **Claude Code Docs**: Visit [Claude Code Documentation](https://docs.claude.com/claude-code)

---

**Version**: 2.0.0 | **Installation Guide** | Last updated: 2025-10-24
