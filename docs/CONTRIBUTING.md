# Contributing to SDD Toolkit

Thank you for your interest in contributing to the Spec-Driven Development (SDD) Toolkit! This document provides guidelines and instructions for contributors.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style Guidelines](#code-style-guidelines)
- [Adding JSON Output to Commands](#adding-json-output-to-commands)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Common Patterns](#common-patterns)

## Development Setup

### Prerequisites

- **Python 3.9+** with pip
- **Git** for version control
- **Claude Code** (latest version) for testing CLI integration
- **pytest** for running tests

### Installation for Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tylerburleigh/claude-sdd-toolkit.git
   cd claude-sdd-toolkit
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

   This installs the package in editable mode, so changes to the source code are immediately reflected.

3. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov
   ```

4. **Verify installation:**
   ```bash
   sdd --version
   sdd verify-tools
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_skills --cov-report=html

# Run specific test file
pytest tests/test_json_output.py

# Run tests matching a pattern
pytest -k "test_json"
```

## Project Structure

```
claude-sdd-toolkit/
├── src/claude_skills/claude_skills/
│   ├── cli/                 # CLI entry points and unified interface
│   │   ├── sdd/            # Main SDD CLI
│   │   │   ├── __init__.py # CLI initialization and router
│   │   │   ├── options.py  # Shared argument groups
│   │   │   └── registry.py # Command registry
│   │   └── skills_dev/     # Skills development CLI
│   ├── common/             # Shared utilities
│   │   ├── json_output.py  # JSON formatting utilities
│   │   ├── sdd_config.py   # Configuration loading
│   │   ├── contracts.py    # Output contracts
│   │   └── ...
│   ├── sdd_next/           # sdd-next skill implementation
│   ├── sdd_plan/           # sdd-plan skill implementation
│   ├── sdd_update/         # sdd-update skill implementation
│   └── ...                 # Other skills
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
├── docs/                   # Documentation
└── skills/                 # Claude Code skill definitions
```

## Code Style Guidelines

### Python Code Style

- **Follow PEP 8** style guidelines
- **Use type hints** for function signatures
- **Write docstrings** for all public functions, classes, and modules
- **Keep functions focused** - each function should do one thing well
- **Limit line length** to 100 characters

### Example:

```python
def format_task_info(task_data: Dict[str, Any], include_metadata: bool = True) -> Dict[str, Any]:
    """
    Format task information for display or export.

    Args:
        task_data: Raw task data from spec file
        include_metadata: Whether to include metadata fields (default: True)

    Returns:
        Formatted task information dictionary

    Raises:
        ValueError: If task_data is missing required fields
    """
    # Implementation here
    pass
```

### Naming Conventions

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: Prefix with `_` (e.g., `_internal_helper`)

## Adding JSON Output to Commands

All SDD CLI commands should support JSON output for automation and agent consumption. This section explains how to add JSON output support to new or existing commands.

### Step 1: Import Required Utilities

Add these imports to your CLI module:

```python
from claude_skills.common.json_output import format_json_output, output_json
from claude_skills.common.sdd_config import load_sdd_config
```

### Step 2: Use Shared Argument Groups

When creating your command parser, use the global parent parser which provides `--json`, `--compact`, and `--no-compact` flags automatically:

```python
from claude_skills.cli.sdd.options import create_global_parent_parser

def create_parser():
    """Create the argument parser for this command."""
    # Load config for defaults
    config = load_sdd_config()

    # Create parent parser with global options
    parent_parser = create_global_parent_parser(config)

    # Create main parser
    parser = argparse.ArgumentParser(
        description="Your command description",
        parents=[parent_parser]  # Inherit global options
    )

    # Add command-specific arguments
    parser.add_argument('spec_id', help='Specification ID')
    # ... more arguments

    return parser
```

**What this gives you automatically:**
- `--json` / `--no-json` - Toggle JSON output
- `--compact` / `--no-compact` - Toggle compact formatting
- `--verbose`, `--debug`, `--quiet` - Logging control
- Respect for user configuration in `.claude/sdd_config.json`

### Step 3: Implement Conditional Output

In your command function, check `args.json` to determine output format:

```python
def cmd_my_command(args):
    """Execute my command."""
    # Your command logic here
    result_data = {
        "spec_id": args.spec_id,
        "status": "success",
        "data": some_processed_data
    }

    # Output formatting
    if args.json:
        # JSON output - respects --compact flag
        output_json(result_data, compact=args.compact)
    else:
        # Human-readable text output
        print(f"Spec: {result_data['spec_id']}")
        print(f"Status: {result_data['status']}")
        # ... format for human readability
```

### Step 4: Define Output Contract (Optional but Recommended)

For commands with complex output, define a contract extractor to ensure consistent, minimal JSON output:

**Create contract in `src/claude_skills/claude_skills/common/contracts.py`:**

```python
def extract_my_command_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract functional contract for my-command output.

    Includes only decision-enabling information, removes redundant fields.

    Args:
        data: Full command output data

    Returns:
        Contract-compliant dictionary with minimal required fields
    """
    return {
        "spec_id": data["spec_id"],
        "status": data["status"],
        # Include only fields needed for decision-making
        "required_field": data.get("required_field"),
        # Omit verbose metadata, descriptions, etc.
    }
```

**Then use it in your output:**

```python
from claude_skills.common.contracts import extract_my_command_contract

def cmd_my_command(args):
    result_data = {
        "spec_id": args.spec_id,
        "status": "success",
        "verbose_metadata": {...},  # Not needed for decisions
        "required_field": "value"
    }

    if args.json:
        if args.compact:
            # Apply contract extraction
            contract = extract_my_command_contract(result_data)
            output_json(contract, compact=True)
        else:
            # Full data, pretty-printed
            output_json(result_data, compact=False)
    else:
        # Human-readable output
        print(f"Spec: {result_data['spec_id']}")
```

### Configuration Integration

The global options automatically respect user configuration:

**User config (`.claude/sdd_config.json`):**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Behavior:**
- Without flags: Uses config defaults (JSON, compact in this example)
- With `--no-json`: Forces text output (overrides config)
- With `--no-compact`: Forces pretty-print (overrides config)

**Precedence (highest to lowest):**
1. CLI flags (`--json`, `--compact`, etc.)
2. Project config (`./.claude/sdd_config.json`)
3. Global config (`~/.claude/sdd_config.json`)
4. Built-in defaults

### Complete Example

Here's a complete minimal command with JSON output support:

```python
"""Example command with JSON output support."""
import argparse
from typing import Dict, Any
from claude_skills.common.json_output import output_json
from claude_skills.common.sdd_config import load_sdd_config
from claude_skills.cli.sdd.options import create_global_parent_parser


def cmd_example(args):
    """Execute example command."""
    # Command logic
    result = {
        "command": "example",
        "input": args.input_value,
        "status": "success",
        "output": "Processed data here"
    }

    # Output
    if args.json:
        output_json(result, compact=args.compact)
    else:
        print(f"Command: {result['command']}")
        print(f"Status: {result['status']}")
        print(f"Output: {result['output']}")


def create_parser():
    """Create argument parser."""
    config = load_sdd_config()
    parent_parser = create_global_parent_parser(config)

    parser = argparse.ArgumentParser(
        description="Example command",
        parents=[parent_parser]
    )
    parser.add_argument('input_value', help='Input value to process')
    parser.set_defaults(func=cmd_example)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
```

**Testing the command:**
```bash
# Text output (if config default is text)
sdd example "hello"

# JSON output (pretty-print)
sdd example "hello" --json

# JSON output (compact)
sdd example "hello" --json --compact

# Override config to force text
sdd example "hello" --no-json
```

### Best Practices for JSON Output

**DO:**
- ✅ Always support both JSON and text output modes
- ✅ Use `output_json()` helper for consistent formatting
- ✅ Respect `args.compact` flag in JSON mode
- ✅ Include all data needed for decision-making in JSON output
- ✅ Use type hints for JSON structures
- ✅ Document JSON output format in docstrings
- ✅ Test both compact and pretty-print modes

**DON'T:**
- ❌ Print debug messages when `args.json` is True (pollutes JSON output)
- ❌ Use `print()` for JSON output (use `output_json()` instead)
- ❌ Include unnecessary verbose metadata in compact mode
- ❌ Assume JSON is always enabled (check `args.json`)
- ❌ Hard-code JSON formatting (use shared utilities)
- ❌ Ignore the `--compact` flag (token optimization is important)

### Error Handling in JSON Mode

When outputting errors in JSON mode:

```python
def cmd_my_command(args):
    try:
        # Command logic
        result = perform_operation(args)

        if args.json:
            output_json({"status": "success", "data": result}, compact=args.compact)
        else:
            print(f"Success: {result}")

    except Exception as e:
        if args.json:
            # JSON error output
            output_json({
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }, compact=args.compact)
        else:
            # Human-readable error
            print(f"Error: {e}", file=sys.stderr)

        sys.exit(1)
```

## Testing Requirements

### Required Tests for JSON Output

When adding JSON output to a command, include these tests:

**1. Test JSON output mode:**
```python
def test_command_json_output(tmp_path, capsys):
    """Test command produces valid JSON output."""
    # Run command with --json
    result = subprocess.run(
        ['sdd', 'my-command', 'arg', '--json'],
        capture_output=True,
        text=True
    )

    # Verify exit code
    assert result.returncode == 0

    # Parse and validate JSON
    output = json.loads(result.stdout)
    assert output['status'] == 'success'
    assert 'required_field' in output
```

**2. Test compact mode:**
```python
def test_command_compact_output():
    """Test command produces compact JSON."""
    result = subprocess.run(
        ['sdd', 'my-command', 'arg', '--json', '--compact'],
        capture_output=True,
        text=True
    )

    # Verify it's single-line (no newlines except at end)
    assert result.stdout.count('\n') <= 1

    # Verify it's valid JSON
    output = json.loads(result.stdout)
    assert output is not None
```

**3. Test pretty-print mode:**
```python
def test_command_pretty_output():
    """Test command produces pretty-printed JSON."""
    result = subprocess.run(
        ['sdd', 'my-command', 'arg', '--json', '--no-compact'],
        capture_output=True,
        text=True
    )

    # Verify it's multi-line
    assert result.stdout.count('\n') > 2

    # Verify it's valid JSON
    output = json.loads(result.stdout)
    assert output is not None
```

**4. Test config integration:**
```python
def test_command_respects_config(tmp_path):
    """Test command respects sdd_config.json settings."""
    # Create config
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    config_file = config_dir / "sdd_config.json"
    config_file.write_text(json.dumps({
        "output": {
            "default_mode": "json",
            "json_compact": true
        }
    }))

    # Run from that directory
    result = subprocess.run(
        ['sdd', 'my-command', 'arg'],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )

    # Should output compact JSON (no --json flag needed)
    output = json.loads(result.stdout)
    assert result.stdout.count('\n') <= 1  # Compact format
```

### Test Coverage Requirements

- **Minimum coverage:** 80% for new code
- **Critical paths:** 100% coverage for JSON output formatting
- **Edge cases:** Test error conditions, empty results, large datasets

## Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Short one-line summary of function.

    More detailed description if needed, explaining what the function does,
    its purpose, and any important behavior.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)

    Returns:
        Description of return value and its structure

    Raises:
        ValueError: When input is invalid
        IOError: When file operations fail

    Examples:
        >>> result = function_name("test", 42)
        >>> print(result['status'])
        success
    """
    pass
```

### README Updates

When adding new features:
1. Update main README.md with feature description
2. Add usage examples
3. Update table of contents if adding new sections
4. Cross-link to related documentation

### Changelog

Add entries to CHANGELOG.md for:
- New features
- Bug fixes
- Breaking changes
- Deprecations

Format:
```markdown
## [Unreleased]

### Added
- JSON output support for `my-command` (#123)

### Fixed
- Bug in task dependency resolution (#124)

### Changed
- Improved performance of spec loading (#125)
```

## Pull Request Process

### Before Submitting

1. **Run tests:** Ensure all tests pass
   ```bash
   pytest
   ```

2. **Check code style:** Use flake8 or similar
   ```bash
   flake8 src/claude_skills/
   ```

3. **Update documentation:** Add/update relevant docs

4. **Add tests:** For any new functionality

5. **Update changelog:** Document your changes

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed? What problem does it solve?

## Changes
- List of specific changes made
- Use bullet points
- Be concise but complete

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] All tests pass locally
- [ ] Tested with real specs

## Documentation
- [ ] Updated relevant documentation
- [ ] Added code comments where needed
- [ ] Updated CHANGELOG.md

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests pass
- [ ] Documentation updated
```

### Review Process

1. **Automated checks:** CI must pass
2. **Code review:** At least one maintainer approval required
3. **Testing:** Reviewer tests the changes locally
4. **Documentation:** Reviewer checks docs are complete
5. **Merge:** Squash and merge into main branch

## Common Patterns

### Working with Spec Files

```python
from claude_skills.common.spec_utils import load_json_spec

# Load spec
spec_data = load_json_spec(spec_id, specs_dir)

# Access spec metadata
title = spec_data['metadata']['title']
phases = spec_data['hierarchy']
```

### Task Operations

```python
from claude_skills.common.task_utils import (
    find_task_by_id,
    get_task_dependencies,
    is_task_blocked
)

# Find task in hierarchy
task = find_task_by_id(hierarchy, task_id)

# Check dependencies
deps = get_task_dependencies(hierarchy, task_id)

# Check if task can start
can_start = not is_task_blocked(task, hierarchy)
```

### Configuration

```python
from claude_skills.common.sdd_config import load_sdd_config

# Load configuration
config = load_sdd_config()

# Access settings
json_enabled = config['output']['default_mode'] == 'json'
compact = config['output']['json_compact']
```

## Getting Help

- **Issues:** Report bugs at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- **Discussions:** Ask questions in [GitHub Discussions](https://github.com/tylerburleigh/claude-sdd-toolkit/discussions)
- **Documentation:** Read the full docs at [docs/](./docs/)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to the SDD Toolkit! 🎉
