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

### 9. (Optional) Install OpenCode Provider Dependencies

If you plan to use the OpenCode AI provider, install Node.js dependencies:

```bash
# Navigate to the providers directory
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills/claude_skills/common/providers

# Install Node.js dependencies
npm install
```

**Prerequisites for OpenCode**:
- Node.js >= 18.x
- OpenCode API key

See [docs/providers/OPENCODE.md](docs/providers/OPENCODE.md) for complete setup instructions.

### 10. Restart Claude Code

Now restart Claude Code. The plugin and all its components will be active.

### 11. Configure Project Permissions

Open your project in Claude Code and run:

```
/sdd-setup
```

This will create in your project:
- `.claude/settings.local.json` - Required permissions for SDD skills and tools
- `.claude/sdd_config.json` - CLI output preferences
- `.claude/ai_config.yaml` - AI model defaults

You should see a success message confirming the setup is complete.

**Note**: You only need to run this once per project.

## Verification

Verify the installation was successful:

### Check CLI Tools

```bash
# Check unified CLI is available
sdd --help

# Check subcommands
sdd doc --help
sdd test --help
sdd validate --help
```

You should see help text for each command.

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

If `sdd` commands aren't found:

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

1. **Run setup command** in Claude Code:
   ```
   /sdd-setup
   ```

2. **Or ask Claude**:
   ```
   Set up SDD permissions for this project
   ```

## Updating the Plugin

To update to the latest version:

### Step 1: Update the Plugin Marketplace

In Claude Code, type:

```
/plugins
```

1. Select **"Manage marketplaces"**
2. Select **`claude-sdd-toolkit`**
3. Select **"Update marketplace"**
4. Wait for the update to complete

### Step 2: Update the Installed Plugin

Type `/plugins` again:

1. Select **"Manage and uninstall plugins"**
2. Select **`claude-sdd-toolkit`**
3. Select **`sdd-toolkit`**
4. Select **"Update now"**
5. Wait for the update to complete

### Step 3: Restart Claude Code

Exit Claude Code completely and restart it.

### Step 4: Reinstall Python Package

The plugin files are now updated, but you must reinstall the Python CLI tools:

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**Why?** The marketplace update gets the latest code, the plugin update installs it to Claude Code, the restart loads the new skills, and the reinstall updates the CLI commands.

## Getting Help

- **Issues**: Report problems at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Documentation**: See [README.md](README.md) for complete documentation
- **Claude Code Docs**: Visit [Claude Code Documentation](https://docs.claude.com/claude-code)

---

**Version**: 0.5.1 | **Installation Guide** | Last updated: 2024-11-18
