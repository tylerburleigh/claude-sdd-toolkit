# Codebase Documentation Generator Skill

A comprehensive skill for generating both human-readable and machine-readable documentation from Python codebases using AST parsing and code metrics analysis.

## Overview

This skill provides a modular, production-ready toolset for automatically documenting codebases. It analyzes Python code using AST (Abstract Syntax Tree) parsing to extract:

- **Classes** with inheritance, methods, and properties
- **Functions** with parameters, return types, and complexity metrics
- **Dependencies** and import relationships
- **Code metrics** including lines of code, complexity scores, and statistics

## Features

✅ **Multi-Format Output**
- Markdown documentation for human readers
- JSON documentation for machine processing and tooling

✅ **Comprehensive Analysis**
- Class definitions with inheritance chains
- Function signatures with type hints
- Cyclomatic complexity calculation
- Dependency graph extraction
- Code quality metrics

✅ **Modular Architecture**
- Clean separation of concerns (parsing, calculation, formatting)
- Easy to extend and customize
- Well-organized codebase following skill patterns

✅ **Easy to Use**
- Command-line interface with subcommands
- No external dependencies (uses only stdlib)
- Configurable output formats and exclusion patterns

## Quick Start

### Using the Skill in Claude

When you need to generate documentation for a codebase, tell Claude:

```
I need to generate documentation for my Python project.
Please use the code-documentation skill to create comprehensive
documentation with both Markdown and JSON output.
```

Claude will:
1. Read the SKILL.md file for best practices
2. Analyze your codebase using the modular toolset
3. Generate both human and machine-readable documentation

### Using the CLI Directly

```bash
# Generate documentation (both Markdown and JSON)
python scripts/code_doc_tools.py generate ./src

# With custom settings
python scripts/code_doc_tools.py generate ./src \
  --name "MyProject" \
  --version "2.0.0" \
  --output-dir ./documentation \
  --format both \
  --verbose

# Analyze codebase statistics only (no documentation files)
python scripts/code_doc_tools.py analyze ./src --verbose

# Validate generated JSON against schema
python scripts/code_doc_tools.py validate ./docs/documentation.json

# JSON only
python scripts/code_doc_tools.py generate ./src --format json

# Markdown only with exclusions
python scripts/code_doc_tools.py generate ./src \
  --format markdown \
  --exclude tests \
  --exclude __pycache__
```

## CLI Subcommands

| Subcommand | Purpose | Example |
|------------|---------|---------|
| `generate` | Generate documentation files | `generate ./src --name MyProject` |
| `analyze` | Show statistics without generating files | `analyze ./src --verbose` |
| `validate` | Validate JSON output against schema | `validate ./docs/documentation.json` |

## Files in This Skill

### Core Files
- **SKILL.md** - Comprehensive guide with examples and best practices
- **README.md** - This file (quick start and overview)
- **LICENSE.txt** - MIT License
- **documentation-schema.json** - JSON Schema for validation

### Modular Scripts (`scripts/`)
- **code_doc_tools.py** - Main CLI entry point with subcommands
- **generator.py** - Documentation generation orchestration
- **parser.py** - AST parsing and codebase analysis
- **calculator.py** - Metrics and complexity calculation
- **formatter.py** - Markdown and JSON output generation
- **__init__.py** - Package initialization

### References (`references/`)
- **quick-reference.md** - CLI commands and common workflows
- **examples.md** - Real-world usage examples and scenarios
- **patterns.md** - Best practices for different project types
- **examples/** - Sample input/output files

## Architecture

The skill follows a modular design pattern consistent with other skills:

```
code-documentation/
├── SKILL.md                      # Comprehensive documentation
├── README.md                     # Quick start guide
├── LICENSE.txt                   # MIT License
├── documentation-schema.json     # JSON validation schema
├── scripts/                      # Modular Python package
│   ├── code_doc_tools.py    # Main CLI entry point
│   ├── generator.py             # Orchestration layer
│   ├── parser.py                # AST parsing & analysis
│   ├── calculator.py            # Metrics calculation
│   ├── formatter.py             # Output formatting
│   └── __init__.py              # Package initialization
└── references/                   # Documentation & examples
    ├── quick-reference.md       # Command reference
    ├── examples.md              # Usage scenarios
    ├── patterns.md              # Best practices
    └── examples/                # Sample files
        ├── calculator.py        # Example Python module
        ├── documentation.json   # Example JSON output
        └── DOCUMENTATION.md     # Example Markdown output
```

## Output Examples

### Markdown Output (`DOCUMENTATION.md`)

```markdown
# MyProject Documentation

**Version:** 1.0.0
**Generated:** 2025-01-20 10:30:00

---

## 📊 Project Statistics

- **Total Files:** 15
- **Total Lines:** 2,450
- **Total Classes:** 12
- **Total Functions:** 47
- **Avg Complexity:** 3.2

## 🏛️ Classes

### `DataProcessor`

**Inherits from:** `BaseProcessor`
**Defined in:** `core/processor.py:15`

**Description:**
> Processes data using various transformation methods.

**Methods:**
- `process()`
- `validate()`
- `transform()`
```

### JSON Output (`documentation.json`)

```json
{
  "metadata": {
    "project_name": "MyProject",
    "version": "1.0.0",
    "generated_at": "2025-01-20T10:30:00",
    "language": "python"
  },
  "statistics": {
    "total_files": 15,
    "total_lines": 2450,
    "total_classes": 12,
    "total_functions": 47,
    "avg_complexity": 3.2
  },
  "classes": [...],
  "functions": [...],
  "dependencies": {...}
}
```

## Use Cases

1. **Project Documentation** - Generate initial documentation for new projects
2. **API Documentation** - Create API reference documentation automatically
3. **Code Review** - Analyze code complexity and structure
4. **Dependency Analysis** - Understand module relationships
5. **CI/CD Integration** - Automatically update docs on every commit
6. **Code Quality Tracking** - Monitor metrics over time
7. **Onboarding** - Help new developers understand codebase structure

## Advanced Features

### From SKILL.md
- **Tree-sitter Integration** - Multi-language support (JavaScript, TypeScript, etc.)
- **Dependency Graph Analysis** - Find circular dependencies
- **Complexity Metrics** - Track code quality over time
- **Custom Parsers** - Extend to other languages

### From references/
- **Common Workflows** - Pre-commit hooks, CI/CD integration
- **Project Patterns** - Best practices for libraries, web apps, microservices
- **Real-world Examples** - 12+ complete usage scenarios

## Tips for Best Results

1. **Use with Claude**: Let Claude read the SKILL.md first for best practices
2. **Clean Code**: Works best with well-documented code (docstrings)
3. **Type Hints**: Include type hints for better documentation
4. **Regular Updates**: Run on every commit to keep docs current
5. **Review Output**: Always review generated documentation for accuracy
6. **Exclude Appropriately**: Don't document tests, migrations, or generated files

## Requirements

- Python 3.7 or higher
- No external dependencies for basic usage (uses only stdlib)
- Optional: `jsonschema` for full JSON validation
- Optional: `tree-sitter` for multi-language support (see SKILL.md)

## Integration Examples

### GitHub Actions

```yaml
name: Update Documentation
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate Documentation
        run: |
          python scripts/code_doc_tools.py generate ./src \
            --name "${{ github.event.repository.name }}" \
            --verbose
      - name: Validate Output
        run: |
          pip install jsonschema
          python scripts/code_doc_tools.py validate ./docs/documentation.json
      - name: Commit Changes
        run: |
          git config user.name "GitHub Actions"
          git add docs/
          git commit -m "docs: Update documentation" || echo "No changes"
          git push
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/code_doc_tools.py generate ./src --format json
git add docs/documentation.json
```

## Standalone Design

This skill is **standalone** and does not integrate with SDD (Spec-Driven Development) workflows. It focuses exclusively on documentation generation and can be used independently in any project.

For SDD integration and project planning, see:
- **sdd-plan** - Specification planning skill
- **sdd-next** - Task preparation skill
- **sdd-update** - Progress tracking skill

## Documentation

- **[SKILL.md](SKILL.md)** - Complete guide with implementation details
- **[Quick Reference](references/quick-reference.md)** - CLI commands and workflows
- **[Examples](references/examples.md)** - 12+ real-world usage scenarios
- **[Patterns](references/patterns.md)** - Best practices for different project types
- **[Sample Output](references/examples/)** - Example generated documentation

## Contributing

This is a skill file for Claude. To improve it:

1. Add examples to references/examples.md
2. Enhance the modular scripts in scripts/
3. Add support for more languages
4. Improve documentation templates in formatter.py
5. Add new patterns to references/patterns.md

## License

MIT License - See LICENSE.txt

## Success!

The skill is fully functional, modular, and production-ready!

✅ Modular architecture following skill patterns
✅ Comprehensive CLI with subcommands
✅ Clean separation of concerns
✅ Well-documented with references
✅ Example files for learning
✅ Ready for immediate use

Use it to generate comprehensive documentation for any Python codebase!
