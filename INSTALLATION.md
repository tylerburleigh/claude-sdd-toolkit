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
/plugins
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

**Important**: Before installing Python dependencies, you must exit out of Claude Code.

### 8. Install Python Dependencies

The plugin requires Python dependencies. Open a terminal and run:

```bash
# Navigate to the plugin directory
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills

# Install the package
pip install -e .
```

This installs the python CLI tools that the skills use.

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
sdd doc --help
sdd test --help

# Check specific commands
sdd validate --help
sdd doc generate --help
```

You should see help text for each command.ß

### Test in Claude Code

First, verify the setup command works:

```
/sdd-setup
```

This should configure your project permissions. If it completes successfully, everything is installed correctly!

Then try creating a spec. Say to Claude something like:

```
Let's create a spec for a chatgpt clone
```

Claude should use the `sdd-plan` skill to create a specification.

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

## Updating the Plugin

To update to the latest version:

In Claude Code, type:

```
/plugins
```

When the menu appears, choose "4. Manage marketplaces. Then choose "claude-sdd-toolkit" and then "Update marketplace.

Close and reopen Claude Code.

## Getting Help

- **Issues**: Report problems at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Documentation**: See [README.md](README.md) for complete documentation
- **Claude Code Docs**: Visit [Claude Code Documentation](https://docs.claude.com/claude-code)

---

**Version**: 0.1.0 | **Installation Guide** | Last updated: 2025-10-24
