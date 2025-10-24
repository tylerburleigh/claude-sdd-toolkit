# Codebase Documentation - Quick Reference

## Supported Languages

The tool automatically detects and parses multiple programming languages:

- **Python** (.py)
- **JavaScript** (.js, .jsx, .mjs, .cjs)
- **TypeScript** (.ts, .tsx)
- **Go** (.go)
- **HTML** (.html, .htm)
- **CSS** (.css, .scss, .sass, .less)

Multi-language projects are fully supported with automatic detection and per-language statistics.

## CLI Commands

### Generate Documentation

```bash
# Basic usage
sdd doc generate <project_directory>

# Generate with custom name and version
sdd doc generate ./src --name MyProject --version 2.0.0

# Generate only Markdown
sdd doc generate ./src --format markdown

# Generate only JSON
sdd doc generate ./src --format json

# Specify output directory
sdd doc generate ./src --output-dir ./documentation

# Exclude patterns
sdd doc generate ./src --exclude test --exclude __pycache__

# Verbose output
sdd doc generate ./src --verbose

# Filter by language (python, javascript, typescript, go, html, css)
sdd doc generate ./src --language python

# Multi-language project (auto-detects all)
sdd doc generate ./fullstack-app --name "FullStack" --version "1.0.0"
```

### Analyze Codebase

```bash
# Analyze and show statistics only (no documentation generation)
sdd doc analyze <project_directory>

# With verbose output
sdd doc analyze ./src --verbose

# With exclusions
sdd doc analyze ./src --exclude test
```

### Validate Documentation

```bash
# Validate generated JSON against schema
sdd doc validate-json ./docs/documentation.json
```

## Common Workflows

### Quick Start - Single Directory

```bash
# Generate both Markdown and JSON for a project
cd /path/to/your/project
python /path/to/code-documentation/scripts/code_doc_tools.py generate . --name YourProject
```

### Multi-Project Documentation

```bash
# Generate docs for multiple projects
for project in project1 project2 project3; do
    sdd doc generate ./$project \
        --name $project \
        --output-dir ./docs/$project
done
```

### Pre-commit Hook Integration

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
sdd doc generate . --format json --output-dir ./docs
git add ./docs/documentation.json
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate Documentation
  run: |
    sdd doc generate ./src \
      --name ${{ github.event.repository.name }} \
      --version ${{ github.ref_name }} \
      --output-dir ./docs

- name: Validate Documentation
  run: |
    sdd doc validate-json ./docs/documentation.json
```

## Default Behaviors

| Option | Default Value | Description |
|--------|---------------|-------------|
| `--output-dir` | `./docs` | Output directory for generated files |
| `--format` | `both` | Generate both Markdown and JSON |
| `--version` | `1.0.0` | Project version |
| `--name` | Directory name | Project name |
| `--language` | Auto-detect all | Filter to specific language (python, javascript, typescript, go, html, css) |
| `--exclude` | Standard patterns | Exclude directories/files matching pattern |

## Output Files

### Generated Files

- **DOCUMENTATION.md** - Human-readable Markdown documentation
- **documentation.json** - Machine-readable JSON documentation

### File Locations

```
docs/
├── DOCUMENTATION.md       # Markdown output
└── documentation.json     # JSON output
```

## JSON Schema

The generated JSON follows the schema defined in `documentation-schema.json`:

```json
{
  "metadata": {
    "project_name": "string",
    "version": "string",
    "generated_at": "ISO 8601 datetime",
    "languages": ["python", "javascript", "typescript", "go", "html", "css"]
  },
  "statistics": {
    "total_files": 0,
    "total_lines": 0,
    "total_classes": 0,
    "total_functions": 0,
    "avg_complexity": 0,
    "by_language": {
      "python": { "files": 0, "lines": 0, "classes": 0, "functions": 0 },
      "javascript": { "files": 0, "lines": 0, "classes": 0, "functions": 0 }
    }
  },
  "modules": [ ... ],
  "classes": [ ... ],
  "functions": [ ... ],
  "dependencies": { ... }
}
```

## Exclusion Patterns

Default exclusions:
- `__pycache__`
- `.git`
- `venv`
- `.env`

Add custom exclusions:
```bash
sdd doc generate ./src \
    --exclude tests \
    --exclude build \
    --exclude dist
```

## Statistics Included

- Total files
- Total lines of code
- Total classes
- Total functions
- Average complexity
- Maximum complexity
- High complexity functions (complexity > 10)

## Tips

1. **Large codebases**: Use `--exclude` to skip non-essential directories like `node_modules`, `__pycache__`, `vendor`
2. **Version tracking**: Use `--version` to match your project version
3. **Automation**: Use the `analyze` subcommand for quick checks without generating docs
4. **Validation**: Always validate JSON output for machine processing
5. **Verbose mode**: Use `-v` for detailed progress during long-running operations
6. **Multi-language projects**: Tool auto-detects all supported languages; use `--language` to focus on specific stack
7. **Per-language stats**: Check `statistics.by_language` in JSON output for language-specific metrics
8. **Mixed codebases**: Exclude language-specific artifacts (e.g., `node_modules` for JS, `venv` for Python, `vendor` for Go)
