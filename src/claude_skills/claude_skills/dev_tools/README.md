# Development Tools

This package contains development utilities for maintaining the `claude_skills` package.

## Documentation Generation (gendocs)

Generates markdown documentation from CLI argparse definitions.

### Purpose

Maintains consistency across SKILL.md files by auto-generating command reference sections from the actual CLI code. This ensures documentation never drifts from the implementation.

### Installation

After installing `claude-skills` package:

```bash
# Development installation
cd /path/to/claude_skills
pip install -e .

# The unified SDD CLI is now available
sdd --help
```

### Usage

The legacy `claude-skills-gendocs` command has been removed. Documentation generation is now accessed through the unified CLI:

```bash
# Generate documentation for a skill (outputs to stdout)
sdd skills-dev gendocs -- sdd-validate

# Save to file
sdd skills-dev gendocs -- sdd-validate --output-file docs/commands.md

# Generate only specific sections
sdd skills-dev gendocs -- doc-query --sections global commands

# See help
sdd skills-dev --help
```

### Supported Skills

Note: The tool uses internal module names. User-facing commands are shown in parentheses.

- `sdd-validate` (→ `sdd validate`) - Spec validation and auto-fix
- `sdd-next` (→ `sdd next`) - Task discovery and execution plans
- `sdd-update` (→ `sdd update`) - Progress tracking and status updates
- `doc-query` (→ `sdd doc find-*`) - Codebase documentation queries
- `run-tests` (→ `sdd test run`) - Test discovery and execution
- `llm-doc-gen` (→ `sdd llm-doc-gen generate`) - LLM-based documentation
- Documentation generation (formerly `code-doc`) now integrated via `sdd doc generate`
- `sdd-integration` - SDD/doc-query integration

### Output Sections

The generated documentation includes:

1. **Global Options** - Options available on all commands
2. **Command Reference** - Individual command documentation with:
   - Usage syntax
   - Positional arguments
   - Optional flags
   - Default values

### Updating SKILL.md Files

Workflow for updating skill documentation:

```bash
# 1. Generate the command reference
sdd skills-dev gendocs -- sdd-validate > /tmp/commands.md

# 2. Copy the relevant sections into SKILL.md
# 3. Keep the hand-written sections (Overview, When to Use, Examples)
# 4. Replace only the auto-generated sections
```

**Recommended structure for SKILL.md:**

```markdown
---
name: skill-name
description: Short description
---

# Skill Name

## Overview
[Hand-written overview]

## When to Use This Skill
[Hand-written guidance]

## Quick Start
[Hand-written examples]

<!-- AUTO-GENERATED SECTION STARTS HERE -->
## Global Options
[Auto-generated from CLI]

## Command Reference
[Auto-generated from CLI]

## Exit Codes
[Hand-written or auto-generated]
<!-- AUTO-GENERATED SECTION ENDS HERE -->

## Advanced Usage
[Hand-written examples]
```

### Adding Support for New Skills

To add support for a new skill:

1. Add mapping in `generate_docs.py`:

```python
SKILL_MODULE_MAP = {
    'my-new-skill': 'claude_skills.my_skill.cli',
    # ...
}
```

2. Ensure the CLI module exposes the parser:

**Option A** - Add a `get_parser()` function:
```python
def get_parser():
    parser = argparse.ArgumentParser(...)
    # configure parser
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    # ...
```

**Option B** - The parser will be auto-detected from `main()` via introspection

3. Test:
```bash
sdd skills-dev gendocs -- my-new-skill
```

### Design Notes

**Why not fully automatic?**
- Skills need context, examples, and guidance that can't be auto-generated
- Hand-written documentation provides "when" and "why" - code only provides "what"
- Combines human insight with machine-verified accuracy

**Parser extraction methods:**
1. Looks for `get_parser()` or `create_parser()` functions
2. Monkey-patches `ArgumentParser.__init__` to capture parser during `main()` call
3. Checks for global `parser` variable

**Limitations:**
- Doesn't capture dynamic behavior (e.g., conditionally added arguments)
- Doesn't extract command descriptions beyond what's in argparse
- May not work with highly customized argparse usage

### Examples

#### Basic usage
```bash
$ sdd skills-dev gendocs -- sdd-validate
# sdd-validate Command Reference

*This section is auto-generated from CLI definitions.*

## Global Options
...
```

#### Selective sections
```bash
$ sdd skills-dev gendocs -- doc-query --sections commands
## Command Reference

### find-class
...
```

#### Integration with CI/CD
```bash
# Verify documentation is up-to-date
sdd skills-dev gendocs -- sdd-validate > /tmp/current.md
diff /tmp/current.md skills/sdd-validate/COMMANDS.md || {
  echo "Documentation is out of date!"
  exit 1
}
```

### Troubleshooting

**"Could not extract ArgumentParser"**
- The CLI module doesn't expose a `get_parser()` function
- The parser creation happens in an unusual way
- Solution: Add a `get_parser()` function to the CLI module

**"Unknown skill: xyz"**
- Skill not in `SKILL_MODULE_MAP`
- Solution: Add mapping in `generate_docs.py`

**Output missing commands**
- Parser uses non-standard subparser setup
- Solution: Check the parser structure and update extraction logic
