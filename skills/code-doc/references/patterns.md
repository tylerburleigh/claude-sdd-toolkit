# Codebase Documentation - Patterns and Best Practices

This document outlines patterns, best practices, and recommendations for different project types and use cases.

## Table of Contents

1. [Project Type Patterns](#project-type-patterns)
2. [Language-Specific Patterns](#language-specific-patterns)
3. [Documentation Strategies](#documentation-strategies)
4. [Integration Patterns](#integration-patterns)
5. [Quality Metrics Patterns](#quality-metrics-patterns)

---

## Project Type Patterns

### Python Library

**Characteristics:**
- Focused API surface
- Emphasis on public functions/classes
- Version tracking critical

**Recommended Command:**
```bash
sdd doc generate ./src \
    --name "LibraryName" \
    --version "$(python setup.py --version)" \
    --format both \
    --exclude tests \
    --exclude examples
```

**Best Practices:**
- Update documentation on every release
- Include version in file name: `docs/v1.2.0/`
- Generate both Markdown (for humans) and JSON (for tooling)

---

### Web Application

**Characteristics:**
- Multiple layers (models, views, controllers)
- Large codebase
- Focus on architecture

**Recommended Command:**
```bash
sdd doc generate ./app \
    --name "AppName" \
    --exclude migrations \
    --exclude static \
    --exclude media \
    --exclude tests \
    --verbose
```

**Best Practices:**
- Generate per-module documentation
- Exclude non-code directories (static, media)
- Track complexity trends over time

---

### Data Science / ML Project

**Characteristics:**
- Notebooks mixed with modules
- Data processing pipelines
- Experiment code vs production code

**Recommended Command:**
```bash
sdd doc generate ./src \
    --exclude notebooks \
    --exclude data \
    --exclude experiments \
    --exclude checkpoints \
    --exclude "*.ipynb" \
    --name "MLProject"
```

**Best Practices:**
- Document only production code, not experiments
- Separate model code from data processing
- Track complexity of data pipelines

---

### Microservices Architecture

**Characteristics:**
- Multiple independent services
- Shared libraries
- Cross-service dependencies

**Pattern: Per-Service Documentation**
```bash
#!/bin/bash
for service in service-*; do
    sdd doc generate ./$service/src \
        --name "$service" \
        --output-dir ./docs/$service \
        --format both
done
```

**Pattern: Aggregated Documentation**
```bash
# Generate combined index
cat > docs/INDEX.md << EOF
# Microservices Documentation

$(for service in service-*; do
    echo "- [$service](${service}/DOCUMENTATION.md)"
done)
EOF
```

---

### Open Source Project

**Characteristics:**
- Public API documentation
- Contributor-friendly
- Multiple versions maintained

**Recommended Command:**
```bash
sdd doc generate ./src \
    --name "ProjectName" \
    --version "$(git describe --tags)" \
    --output-dir ./docs/api \
    --format both
```

**Best Practices:**
- Generate docs on release tags
- Maintain docs for multiple versions
- Include in GitHub Pages or wiki
- Link from main README

---

## Language-Specific Patterns

### Python

**Current Support:** ✅ Full support via AST parsing

**Patterns:**
```bash
# Standard Python project
sdd doc generate ./src --exclude venv --exclude .venv

# With Poetry
sdd doc generate ./package_name

# With setup.py
sdd doc generate ./src \
    --name "$(python setup.py --name)" \
    --version "$(python setup.py --version)"
```

**Metrics Focus:**
- Cyclomatic complexity
- Function/method count
- Class hierarchies
- Import dependencies

---

### JavaScript / TypeScript

**Current Support:** ✅ Full support via tree-sitter parsing

**Patterns:**
```bash
# JavaScript project
sdd doc generate ./src --language javascript --exclude node_modules

# TypeScript project
sdd doc generate ./src --language typescript --exclude node_modules --exclude dist

# React application
sdd doc generate ./src --name "ReactApp" --exclude node_modules --exclude build

# Full-stack (auto-detect all)
sdd doc generate ./project --exclude node_modules --exclude __pycache__
```

**Metrics Focus:**
- Async/await patterns
- Class and function exports
- Component hierarchies
- Import dependencies
- JSX component detection

---

### Go

**Current Support:** ✅ Full support via tree-sitter parsing

**Patterns:**
```bash
# Go project
sdd doc generate ./cmd ./pkg ./internal --language go --exclude vendor

# Microservice
sdd doc generate . --name "GoService" --exclude vendor --exclude testdata

# With versioning from git
sdd doc generate . --version "$(git describe --tags)" --exclude vendor
```

**Metrics Focus:**
- Package structure
- Function signatures with receivers (methods)
- Struct and interface definitions
- Import dependencies

---

### HTML / CSS

**Current Support:** ✅ Full support via tree-sitter parsing

**Patterns:**
```bash
# Static website
sdd doc generate . --name "Website"

# HTMX application
sdd doc generate ./templates --name "HTMXApp"

# CSS framework
sdd doc generate ./styles --language css --name "StyleFramework"
```

**Metrics Focus:**
- HTML: Element counts, HTMX attributes, custom data attributes
- CSS: Selectors, variables, media queries, keyframes

---

### Multi-Language Full-Stack

**Current Support:** ✅ Auto-detection of all languages

**Pattern:**
```bash
# Full-stack application (Python + TypeScript + HTML/CSS)
sdd doc generate . --name "FullStackApp" --exclude node_modules --exclude __pycache__ --exclude venv --exclude dist
```

**Benefits:**
- Unified documentation across languages
- Per-language statistics breakdown
- Cross-language dependency tracking
- Single source of truth

---

## Documentation Strategies

### Continuous Documentation

**Pattern:** Update docs automatically on every commit

```yaml
# GitHub Actions
name: Update Docs
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate Docs
        run: sdd doc generate ./src --format json
      - name: Commit
        run: |
          git add docs/
          git commit -m "docs: update" || true
          git push
```

**Use Cases:**
- Track code evolution
- Catch complexity increases early
- Maintain up-to-date API docs

---

### Release Documentation

**Pattern:** Generate docs only on releases

```yaml
# GitHub Actions
name: Release Docs
on:
  release:
    types: [published]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Release Docs
        run: |
          sdd doc generate ./src \
            --version ${{ github.event.release.tag_name }} \
            --output-dir ./docs/${{ github.event.release.tag_name }}
```

**Use Cases:**
- Version-specific documentation
- Stable API references
- Historical tracking

---

### Development Documentation

**Pattern:** Generate locally before code review

```bash
# Pre-commit hook
sdd doc analyze ./src --verbose

# Fail if complexity too high
COMPLEXITY=$(sdd doc analyze ./src | grep "Avg Complexity" | awk '{print $3}')
if (( $(echo "$COMPLEXITY > 10" | bc -l) )); then
    echo "❌ Average complexity too high: $COMPLEXITY"
    exit 1
fi
```

**Use Cases:**
- Code quality gates
- Pre-PR checks
- Developer awareness

---

## Integration Patterns

### Static Site Integration

**Pattern:** Embed generated Markdown in documentation sites

**MkDocs Example:**
```yaml
# mkdocs.yml
nav:
  - Home: index.md
  - API Reference: DOCUMENTATION.md  # Generated file

hooks:
  - scripts/generate_docs_hook.py
```

**Sphinx Example:**
```python
# conf.py
import subprocess

def generate_docs(app, config):
    subprocess.run([
        'python', 'scripts/code_doc_tools.py', 'generate', './src',
        '--format', 'markdown'
    ])

def setup(app):
    app.connect('config-inited', generate_docs)
```

---

### API Server Integration

**Pattern:** Serve documentation JSON via API

**Flask Example:**
```python
from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/docs')
def docs():
    with open('docs/documentation.json', 'r') as f:
        return jsonify(json.load(f))

@app.route('/api/docs/stats')
def stats():
    with open('docs/documentation.json', 'r') as f:
        data = json.load(f)
        return jsonify(data['statistics'])
```

---

### IDE Integration

**Pattern:** Generate and import in IDE for code navigation

**VS Code Example:**
```json
{
  "tasks": [
    {
      "label": "Generate Documentation",
      "type": "shell",
      "command": "sdd doc generate ./src",
      "problemMatcher": []
    }
  ]
}
```

---

## Quality Metrics Patterns

### Complexity Monitoring

**Pattern:** Track complexity over time and alert on increases

```bash
#!/bin/bash

# Generate current metrics
sdd doc generate ./src --format json --output-dir ./tmp

# Extract complexity
CURRENT=$(python -c "import json; print(json.load(open('./tmp/documentation.json'))['statistics']['avg_complexity'])")
PREVIOUS=$(python -c "import json; print(json.load(open('./docs/documentation.json'))['statistics']['avg_complexity'])")

echo "Previous: $PREVIOUS | Current: $CURRENT"

# Alert if increased significantly
if (( $(echo "$CURRENT > $PREVIOUS + 1" | bc -l) )); then
    echo "⚠️  Complexity increased significantly!"
    exit 1
fi
```

---

### High Complexity Alerts

**Pattern:** Identify and report functions exceeding complexity threshold

```python
import json

with open('docs/documentation.json', 'r') as f:
    docs = json.load(f)

THRESHOLD = 15
high_complexity = [
    f for f in docs['functions']
    if f['complexity'] > THRESHOLD
]

if high_complexity:
    print(f"⚠️  Found {len(high_complexity)} high-complexity functions:")
    for func in high_complexity:
        print(f"  - {func['name']} (complexity: {func['complexity']}) in {func['file']}")
```

---

### Code Growth Tracking

**Pattern:** Monitor codebase size and structure changes

```bash
#!/bin/bash

# Historical tracking
DATE=$(date +%Y-%m-%d)
sdd doc generate ./src --format json

python << EOF
import json
with open('docs/documentation.json', 'r') as f:
    stats = json.load(f)['statistics']

with open('metrics.csv', 'a') as f:
    f.write(f"$DATE,{stats['total_files']},{stats['total_lines']},{stats['total_functions']},{stats['avg_complexity']}\n")
EOF

echo "✅ Metrics logged for $DATE"
```

---

## Anti-Patterns (What to Avoid)

### ❌ Generating Docs for Everything

**Problem:** Including tests, migrations, generated files bloats documentation

**Solution:**
```bash
# Bad
sdd doc generate .

# Good
sdd doc generate ./src \
    --exclude tests --exclude migrations --exclude generated
```

---

### ❌ Ignoring Complexity Warnings

**Problem:** High complexity functions indicate maintainability issues

**Solution:** Set up CI gates:
```yaml
- name: Check Complexity
  run: |
    sdd doc analyze ./src
    # Fail if max complexity > 20
```

---

### ❌ Not Versioning Documentation

**Problem:** Can't track how API evolved over time

**Solution:**
```bash
# Version-specific output directories
sdd doc generate ./src \
    --version "$(git describe --tags)" \
    --output-dir "./docs/$(git describe --tags)"
```

---

## Best Practices Summary

1. **Exclude appropriately**: Don't document tests, migrations, or generated code
2. **Version tracking**: Always include version information
3. **Automate**: Integrate with CI/CD for consistent updates
4. **Monitor metrics**: Track complexity and size trends
5. **Format strategically**: JSON for machines, Markdown for humans
6. **Structure output**: Organize by version or module as needed
7. **Validate**: Always validate JSON output for programmatic use

---

## See Also

- [Examples](examples.md) - Real-world usage examples
- [Quick Reference](quick-reference.md) - Command reference
- [Example Output](examples/) - Sample generated files
