# Developer Guide - SDD Toolkit

> Extending and customizing the SDD Toolkit

This guide is for developers who want to extend the SDD Toolkit with custom skills, commands, hooks, and CLI tools.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Adding Custom Skills](#adding-custom-skills)
- [Adding Custom Commands](#adding-custom-commands)
- [Adding Custom Hooks](#adding-custom-hooks)
- [Adding Custom CLI Tools](#adding-custom-cli-tools)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Contributing](#contributing)

## Architecture Overview

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

The SDD Toolkit consists of four main components:

1. **Skills** (`~/.claude/skills/`) - Claude Code skill extensions
2. **Commands** (`~/.claude/commands/`) - User-invoked slash commands
3. **Hooks** (`~/.claude/hooks/`) - Event-triggered automation
4. **CLI Tools** (`~/.claude/src/claude_skills/`) - Python package with CLI commands

## Adding Custom Skills

Skills extend Claude's capabilities with specialized workflows.

### Creating a Skill

```bash
# 1. Create skill directory
mkdir ~/.claude/skills/my-skill

# 2. Create SKILL.md with instructions for Claude
cat > ~/.claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Brief description of what this skill does
---

# My Skill

## Purpose

Explain what this skill is for and when Claude should use it.

## Instructions

When invoked, you should:

1. **First step**: Describe what to do first
2. **Second step**: Describe what to do next
3. **Return results**: Explain what to return to the user

## Usage Examples

Show examples of how users might invoke this skill:
- "Use my-skill to analyze the codebase"
- "Run my-skill on this file"

## CLI Tools

If this skill uses CLI tools, document them here:

```bash
# Example CLI command
my-tool --option value
```

## Output Format

Describe the expected output format for the user.
EOF

# 3. Test the skill
# In Claude Code: "Use my-skill to do something"
```

### Skill Best Practices

1. **Clear instructions**: Write instructions as if Claude is a new team member
2. **Use CLI tools**: Leverage the Python package for complex operations
3. **Error handling**: Include instructions for handling common errors
4. **Examples**: Provide concrete usage examples
5. **Permissions**: Document required permissions in the skill description

### Skill Examples

See existing skills for reference:
- `~/.claude/skills/sdd-plan/` - Complex workflow with multiple steps
- `~/.claude/skills/doc-query/` - Simple CLI wrapper
- `~/.claude/skills/run-tests/` - Interactive workflow with error handling

## Adding Custom Commands

Commands are user-invoked workflows that start with `/`.

### Creating a Command

```bash
# 1. Create command file
cat > ~/.claude/commands/my-command.md << 'EOF'
---
name: my-command
description: Brief description shown in command list
---

# My Command

## Purpose

Explain what this command does and when to use it.

## Workflow

Guide the user through an interactive workflow:

1. **Gather information**: Ask the user for input
2. **Process**: Use skills or CLI tools to process
3. **Present results**: Show results and next steps

## Example

Show an example interaction:

```
User: /my-command
Claude: What would you like to accomplish?
User: I want to analyze my code
Claude: [Uses appropriate skills and tools]
```
EOF

# 2. Test the command
# In Claude Code: /my-command
```

### Command Best Practices

1. **Interactive**: Commands should guide the user through steps
2. **Clear prompts**: Ask clear questions to gather input
3. **Use skills**: Leverage existing skills rather than reimplementing logic
4. **Feedback**: Provide clear feedback at each step
5. **Exit paths**: Provide ways to cancel or go back

## Adding Custom Hooks

Hooks run automatically in response to events.

### Creating a Hook

```bash
# 1. Create hook script
cat > ~/.claude/hooks/my-hook << 'EOF'
#!/bin/bash

# Hook: my-hook
# Event: session-start, session-end, pre-tool-use, post-tool-use, user-prompt-submit
# Purpose: What this hook does

# Hooks receive event data via stdin
event_data=$(cat)

# Perform your logic here
# Example: Log the event
echo "$event_data" >> ~/.claude/logs/hook-log.txt

# Optionally output JSON for Claude to read
echo '{
  "status": "success",
  "message": "Hook executed successfully",
  "data": {
    "key": "value"
  }
}'

# Always exit 0 to avoid blocking
exit 0
EOF

# 2. Make executable
chmod +x ~/.claude/hooks/my-hook

# 3. Test manually
echo '{"test": "data"}' | ~/.claude/hooks/my-hook
```

### Available Hook Events

| Event | When It Fires | Input Data |
|-------|---------------|------------|
| `session-start` | When Claude Code session begins | Session info, working directory |
| `session-end` | When session ends | Session summary |
| `pre-tool-use` | Before any tool is used | Tool name, parameters |
| `post-tool-use` | After any tool is used | Tool name, parameters, result |
| `user-prompt-submit` | When user submits a message | User message text |

### Hook Best Practices

1. **Fast execution**: Hooks should complete quickly (< 1 second)
2. **Non-blocking**: Always exit 0, even on errors
3. **Error handling**: Handle errors gracefully and log them
4. **JSON output**: Use JSON format for structured data
5. **Permissions**: Ensure hook has necessary file permissions
6. **Logging**: Log important events for debugging

### Hook Examples

```bash
# Example: Notify on test failures
cat > ~/.claude/hooks/post-tool-use << 'EOF'
#!/bin/bash
data=$(cat)
tool=$(echo "$data" | jq -r '.tool')

if [[ "$tool" == "Bash" ]]; then
  command=$(echo "$data" | jq -r '.parameters.command')
  if [[ "$command" =~ pytest ]]; then
    result=$(echo "$data" | jq -r '.result')
    if [[ "$result" =~ FAILED ]]; then
      echo '{"status": "alert", "message": "Tests failed!"}'
    fi
  fi
fi

exit 0
EOF
chmod +x ~/.claude/hooks/post-tool-use
```

## Adding Custom CLI Tools

CLI tools provide reusable functionality for skills and hooks.

### Creating a CLI Tool Module

```bash
# 1. Create module directory
cd ~/.claude/src/claude_skills/claude_skills
mkdir my_tool

# 2. Create module files
# my_tool/__init__.py
cat > my_tool/__init__.py << 'EOF'
"""My custom tool module."""
__version__ = "1.0.0"
EOF

# my_tool/cli.py
cat > my_tool/cli.py << 'EOF'
#!/usr/bin/env python3
"""
My Tool CLI

Description of what this tool does.
"""

import click
from ..common.logging import get_logger

logger = get_logger(__name__)

@click.group()
@click.version_option()
def cli():
    """My tool CLI commands."""
    pass

@cli.command()
@click.argument('input_value')
@click.option('--option', '-o', help='Optional parameter')
def process(input_value, option):
    """Process something with the input value."""
    try:
        logger.info(f"Processing: {input_value}")
        # Your logic here
        result = f"Processed: {input_value}"
        print(result)
    except Exception as e:
        logger.error(f"Error processing: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()
EOF

# 3. Add entry point to pyproject.toml
cat >> ~/.claude/src/claude_skills/pyproject.toml << 'EOF'
my-tool = "claude_skills.my_tool.cli:cli"
EOF

# 4. Reinstall package
cd ~/.claude/src/claude_skills
pip install -e .

# 5. Test
my-tool --help
my-tool process test-value --option foo
```

### CLI Tool Best Practices

1. **Use Click**: Follow the Click framework for consistency
2. **Logging**: Use the shared logging utilities from `common.logging`
3. **Error handling**: Provide clear error messages
4. **Documentation**: Include docstrings and help text
5. **Testing**: Write unit tests in `tests/` directory
6. **Configuration**: Use shared config from `common.config`

### Unified CLI Architecture

The toolkit uses a unified CLI architecture with subcommands:

- `sdd` - SDD workflows (next-task, update-status, validate)
- `doc` - Documentation (generate, query, search)
- `test` - Test execution (run, debug)
- `skills-dev` - Development tools (setup-permissions, gendocs, start-helper)

When adding new functionality, consider adding it as a subcommand to an existing CLI rather than creating a new top-level command.

Example:
```python
# Add to sdd CLI
@sdd.command('my-command')
def my_command():
    """My new SDD command."""
    pass
```

## Development Setup

See [INSTALLATION.md](INSTALLATION.md) for complete development setup instructions.

### Quick Setup

```bash
# 1. Clone or download the toolkit
cd ~/.claude

# 2. Install in development mode
cd src/claude_skills
pip install -e .

# 3. Verify installation
sdd --help
doc --help
test --help

# 4. Run tests
python -m pytest tests/
```

### Project Permissions

When developing, you may need to set up project-level permissions:

```bash
# Set up permissions for current project
cd /path/to/your/project
sdd skills-dev setup-permissions -- update .

# Check permissions
cat .claude/settings.json
```

## Testing

### Running Tests

```bash
# Run all tests
cd ~/.claude/src/claude_skills
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_sdd_next.py

# Run with coverage
python -m pytest tests/ --cov=claude_skills
```

### Writing Tests

```python
# tests/test_my_tool.py
import pytest
from claude_skills.my_tool.cli import process

def test_process_basic():
    """Test basic processing."""
    result = process("test-input", None)
    assert result == "Processed: test-input"

def test_process_with_option():
    """Test processing with option."""
    result = process("test-input", "option-value")
    assert "option-value" in result
```

## Contributing

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all public functions
- Keep functions small and focused
- Use meaningful variable names

### Documentation

- Update README.md if adding user-facing features
- Update this DEVELOPER.md if adding developer-facing features
- Add docstrings to all modules, classes, and functions
- Include usage examples in CLI help text

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Update documentation
6. Submit pull request

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push and create PR
git push origin feature/my-feature
```

## Common Patterns

### Accessing Spec Files

```python
from claude_skills.common.spec_utils import find_active_specs, load_spec

# Find all active specs
specs = find_active_specs("/path/to/project")

# Load a specific spec
spec = load_spec("/path/to/spec.json")
```

### Using the Logger

```python
from claude_skills.common.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Working with Git

```python
from claude_skills.common.git_utils import get_git_root, is_git_repo

if is_git_repo("/path/to/project"):
    git_root = get_git_root("/path/to/project")
    print(f"Git root: {git_root}")
```

## Resources

- **Claude Code Documentation**: https://docs.claude.com/claude-code
- **Click Documentation**: https://click.palletsprojects.com/
- **pytest Documentation**: https://docs.pytest.org/

## Getting Help

- Create an issue on GitHub
- Check existing skills for examples
- Review the common utilities in `claude_skills/common/`

---

**Ready to contribute?** Start by exploring the existing codebase and identifying areas for improvement.
