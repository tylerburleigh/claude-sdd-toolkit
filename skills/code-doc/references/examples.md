# Codebase Documentation - Examples

This document provides real-world examples and scenarios for using the multi-language codebase documentation generator.

## Example 1: Small Python Library

### Scenario
You have a small Python library with a few modules and want to generate documentation.

### Project Structure
```
my_library/
├── __init__.py
├── core.py
├── utils.py
└── helpers.py
```

### Command
```bash
sdd doc generate ./my_library --name "MyLibrary" --version "1.2.0" --output-dir ./docs
```

### Output
```
docs/
├── DOCUMENTATION.md       # Human-readable docs
└── documentation.json     # Machine-readable docs
```

---

## Example 1b: JavaScript/Node.js Project

### Scenario
You have a Node.js application and want to document its structure.

### Project Structure
```
my-app/
├── src/
│   ├── index.js
│   ├── routes/
│   ├── models/
│   └── utils/
├── package.json
└── README.md
```

### Command
```bash
sdd doc generate ./my-app/src --name "MyApp" --version "2.0.0" --language javascript --output-dir ./docs
```

### Output
Generates documentation for all JavaScript files including classes, functions, imports, and exports.

---

## Example 2: Large Application with Tests

### Scenario
You have a large application and want to exclude test files and virtual environment.

### Project Structure
```
my_app/
├── src/
│   ├── models/
│   ├── views/
│   └── controllers/
├── tests/
├── venv/
└── setup.py
```

### Command
```bash
sdd doc generate ./my_app/src --name "MyApp" --version "2.0.0" --exclude tests --exclude venv --verbose
```

### Why This Works
- Analyzes only the `src/` directory
- Skips `tests/` and `venv/` directories
- Provides verbose output for progress tracking

---

## Example 3: Quick Statistics Check

### Scenario
You want to quickly check codebase metrics without generating full documentation.

### Command
```bash
sdd doc analyze ./my_project --verbose
```

### Sample Output
```
🔍 Analyzing my_project...
📄 Found 45 Python files

✅ Analysis complete!
   📦 45 modules
   🏛️  23 classes
   ⚡ 156 functions

📊 Project Statistics:
   Total Files:      45
   Total Lines:      3,421
   Total Classes:    23
   Total Functions:  156
   Avg Complexity:   4.2
   Max Complexity:   15

⚠️  High Complexity Functions:
   - process_data (15)
   - validate_input (12)
```

---

## Example 4: CI/CD Integration (GitHub Actions)

### Scenario
Automatically generate documentation on every push to main branch.

### .github/workflows/docs.yml
```yaml
name: Generate Documentation

on:
  push:
    branches: [ main ]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Generate Documentation
        run: |
          sdd doc generate ./src --name "${{ github.event.repository.name }}" --version "${{ github.ref_name }}" --format both --output-dir ./docs

      - name: Validate JSON Output
        run: |
          pip install jsonschema
          sdd doc validate-json ./docs/documentation.json

      - name: Commit Documentation
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/
          git commit -m "docs: Update generated documentation" || echo "No changes"
          git push
```

---

## Example 5: Markdown-Only Documentation

### Scenario
You only need human-readable Markdown documentation for your README or wiki.

### Command
```bash
sdd doc generate ./src \
    --format markdown \
    --output-dir ./docs
```

### Use Case
- Publishing to GitHub wiki
- Embedding in project README
- Creating developer onboarding materials

---

## Example 6: JSON-Only for API Integration

### Scenario
You're building a tool that consumes codebase metadata programmatically.

### Command
```bash
sdd doc generate ./src \
    --format json \
    --output-dir ./api_data
```

### Python Integration Example
```python
import json

with open('./api_data/documentation.json', 'r') as f:
    docs = json.load(f)

# Access statistics
print(f"Total Functions: {docs['statistics']['total_functions']}")

# Find high-complexity functions
for func in docs['functions']:
    if func['complexity'] > 10:
        print(f"Complex: {func['name']} (complexity: {func['complexity']})")
```

---

## Example 7: Multi-Project Batch Documentation

### Scenario
You have multiple microservices and want to generate docs for all of them.

### Bash Script
```bash
#!/bin/bash

PROJECTS=("auth-service" "payment-service" "notification-service")
VERSION="1.5.0"

for project in "${PROJECTS[@]}"; do
    echo "Generating docs for $project..."

    sdd doc generate "./$project/src" \
        --name "$project" \
        --version "$VERSION" \
        --output-dir "./docs/$project" \
        --verbose

    echo "✅ Done: $project"
    echo ""
done

echo "🎉 All documentation generated!"
```

---

## Example 8: Pre-commit Hook

### Scenario
Automatically update JSON documentation before each commit to track code evolution.

### .git/hooks/pre-commit
```bash
#!/bin/bash

echo "Generating updated documentation..."

sdd doc generate ./src \
    --format json \
    --output-dir ./docs \
    --name "$(basename $(pwd))" 2>&1 | grep -E "(✅|❌)"

# Add documentation to staging
git add ./docs/documentation.json

echo "✅ Documentation updated"
```

### Make Hook Executable
```bash
chmod +x .git/hooks/pre-commit
```

---

## Example 9: Analyzing Only Changed Files

### Scenario
You want to analyze only specific directories after a major refactor.

### Command
```bash
# Analyze specific module
sdd doc analyze ./src/models --verbose

# Compare with full codebase
sdd doc analyze ./src --verbose
```

---

## Example 10: Custom Exclusions for Data Science Project

### Scenario
Data science project with notebooks, data files, and experiments to exclude.

### Project Structure
```
ml_project/
├── src/
├── notebooks/
├── data/
├── experiments/
└── models/
```

### Command
```bash
sdd doc generate ./ml_project \
    --exclude notebooks \
    --exclude data \
    --exclude experiments \
    --exclude "*.ipynb" \
    --exclude "checkpoint" \
    --name "ML Project" \
    --verbose
```

---

## Example 11: Validation in CI Pipeline

### Scenario
Ensure documentation stays valid and up-to-date in CI.

### GitLab CI (.gitlab-ci.yml)
```yaml
documentation:
  stage: test
  script:
    - sdd doc generate ./src --format json
    - pip install jsonschema
    - sdd doc validate-json ./docs/documentation.json
  artifacts:
    paths:
      - docs/
    expire_in: 1 week
```

---

## Example 12: Comparing Documentation Over Time

### Scenario
Track how your codebase metrics evolve across versions.

### Script: track_metrics.sh
```bash
#!/bin/bash

VERSION=$(git describe --tags)
OUTPUT_FILE="metrics_history.json"

# Generate current documentation
sdd doc generate ./src \
    --format json \
    --version "$VERSION" \
    --output-dir ./tmp_docs

# Extract and append statistics
python << EOF
import json
from datetime import datetime

with open('./tmp_docs/documentation.json', 'r') as f:
    docs = json.load(f)

entry = {
    'version': '$VERSION',
    'date': datetime.now().isoformat(),
    'statistics': docs['statistics']
}

# Append to history
try:
    with open('$OUTPUT_FILE', 'r') as f:
        history = json.load(f)
except FileNotFoundError:
    history = []

history.append(entry)

with open('$OUTPUT_FILE', 'w') as f:
    json.dump(history, f, indent=2)

print(f"✅ Metrics tracked for version {entry['version']}")
EOF

# Clean up
rm -rf ./tmp_docs
```

---

## Example 13: TypeScript React Application

### Scenario
Document a TypeScript React application with components, hooks, and utilities.

### Project Structure
```
react-app/
├── src/
│   ├── components/
│   │   ├── Button.tsx
│   │   └── Modal.tsx
│   ├── hooks/
│   │   └── useAuth.ts
│   └── utils/
│       └── api.ts
└── package.json
```

### Command
```bash
sdd doc generate ./react-app/src --name "ReactApp" --language typescript --output-dir ./docs --verbose
```

### Output Highlights
- Documents TypeScript interfaces and types
- Extracts React component props
- Captures async functions and hooks
- Shows import/export relationships

---

## Example 14: Go Microservice

### Scenario
Document a Go microservice with handlers, models, and services.

### Project Structure
```
go-service/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handlers/
│   ├── models/
│   └── services/
└── pkg/
```

### Command
```bash
sdd doc generate ./go-service --name "GoService" --language go --exclude vendor --output-dir ./docs
```

### What Gets Documented
- Package structure
- Function signatures with receivers
- Struct definitions
- Interface declarations
- Import dependencies

---

## Example 15: Multi-Language Full-Stack Application

### Scenario
Document a full-stack application with Python backend, TypeScript frontend, and HTML templates.

### Project Structure
```
fullstack-app/
├── backend/           # Python/FastAPI
│   ├── api/
│   ├── models/
│   └── services/
├── frontend/          # TypeScript/React
│   └── src/
│       ├── components/
│       └── pages/
└── templates/         # HTML
    └── emails/
```

### Command
```bash
sdd doc generate ./fullstack-app --name "FullStackApp" --version "3.0.0" --exclude node_modules --exclude __pycache__ --output-dir ./docs --verbose
```

### Benefits
- Automatically detects all languages (Python, TypeScript, HTML)
- Provides per-language statistics breakdown
- Shows cross-language dependencies
- Single unified documentation

---

## Example 16: Frontend-Only Project (HTML/CSS/JS)

### Scenario
Document a traditional web project with HTML, CSS, and vanilla JavaScript.

### Project Structure
```
website/
├── index.html
├── about.html
├── css/
│   ├── main.css
│   └── responsive.css
└── js/
    ├── app.js
    └── utils.js
```

### Command
```bash
sdd doc generate ./website --name "MyWebsite" --output-dir ./docs
```

### Output
- HTML structure and HTMX usage
- CSS selectors, variables, and media queries
- JavaScript functions and classes
- All in one comprehensive report

---

## Example 17: Language-Specific Documentation

### Scenario
Generate documentation only for JavaScript/TypeScript files in a mixed codebase.

### Command
```bash
sdd doc generate ./my-project --language javascript --name "JS Documentation" --output-dir ./docs/js-only
```

### Use Cases
- Focus on specific language layer
- Separate frontend from backend docs
- Language-specific code reviews
- Onboarding for specific tech stack

---

## Example 18: CI/CD Multi-Language Documentation

### Scenario
Automatically document a multi-language project in CI.

### .github/workflows/multi-lang-docs.yml
```yaml
name: Generate Multi-Language Documentation

on:
  push:
    branches: [ main ]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install code-doc
        run: pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-go tree-sitter-html tree-sitter-css

      - name: Generate Full Documentation
        run: sdd doc generate ./src --name "${{ github.event.repository.name }}" --version "${{ github.ref_name }}" --format both --output-dir ./docs

      - name: Upload Documentation
        uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: docs/
```

---

## Tips for Examples

1. **Start simple**: Begin with basic `generate` commands, add options as needed
2. **Test validation**: Always validate JSON if using programmatically
3. **Exclude smartly**: Use `--exclude` for faster processing on large codebases
4. **Version tracking**: Include `--version` to track documentation evolution
5. **Automate**: Integrate with CI/CD for continuous documentation updates

## See Also

- [Quick Reference](quick-reference.md) - Command reference and common workflows
- [Patterns](patterns.md) - Best practices for different project types
- [Example Output](examples/) - Sample generated documentation files
