# Installing SDD Toolkit Plugin

## Prerequisites

- Claude Code (latest version)
- Python 3.9 or higher
- pip package manager
- Git (for cloning repository)

## Quick Install

### Option 1: Install from Git Repository (Recommended)

1. **Add marketplace configuration**:
   ```bash
   # Create or edit ~/.claude/marketplace.json
   cat > ~/.claude/marketplace.json << 'EOF'
   {
     "marketplaces": [
       {
         "name": "Team Plugins",
         "plugins": [
           {
             "name": "sdd-toolkit",
             "source": "git",
             "url": "https://github.com/tylerburleigh/claude-sdd-toolkit",
             "branch": "main"
           }
         ]
       }
     ]
   }
   EOF
   ```

2. **Install the plugin**:
   ```bash
   # In Claude Code
   /plugin install sdd-toolkit
   ```

3. **Install Python dependencies**:
   ```bash
   cd ~/.claude/plugins/sdd-toolkit/src/claude_skills
   pip install -e .
   ```

4. **Restart Claude Code**

### Option 2: Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tylerburleigh/claude-sdd-toolkit ~/.claude/plugins/sdd-toolkit
   ```

2. **Install Python dependencies**:
   ```bash
   cd ~/.claude/plugins/sdd-toolkit/src/claude_skills
   pip install -e .
   ```

3. **Restart Claude Code**

## Verification

After installation, verify everything works:

```bash
# Check CLI tools
sdd --help

# Check skills in Claude Code
# Ask Claude: "List available skills"
# You should see: sdd-plan, sdd-next, sdd-update, etc.

# Test a command
# In Claude Code, type: /sdd-start
```

## Troubleshooting

### Plugin not detected
- Ensure the plugin is in `~/.claude/plugins/sdd-toolkit/`
- Check that `.claude-plugin/plugin.json` exists
- Restart Claude Code

### Python package not found
```bash
# Reinstall the package
cd ~/.claude/plugins/sdd-toolkit/src/claude_skills
pip install -e .
```

### Commands not working
```bash
# Check PATH includes pip's bin directory
which sdd

# If not found, add to PATH or reinstall
pip install -e ~/.claude/plugins/sdd-toolkit/src/claude_skills
```

## Updating

```bash
# Pull latest changes
cd ~/.claude/plugins/sdd-toolkit
git pull

# Reinstall Python package if updated
cd src/claude_skills
pip install -e .
```

## Uninstalling

```bash
# Remove plugin
rm -rf ~/.claude/plugins/sdd-toolkit

# Uninstall Python package
pip uninstall claude-skills
```
