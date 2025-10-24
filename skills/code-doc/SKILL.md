---
name: code-doc
description: Multi-language codebase documentation generation supporting Python, JavaScript/TypeScript, Go, HTML, CSS, and more. Creates both human-readable markdown documentation and machine-readable JSON output. Includes AST parsing, dependency analysis, code metrics, and automated documentation workflows.
---

# Codebase Documentation Generator Skill

## Table of Contents

- [Quick Start](#quick-start)
- [When to Use This Skill](#when-to-use-this-skill)
- [Core Documentation Process](#core-documentation-process)
  - [Phase 1: Understand Requirements](#phase-1-understand-requirements)
  - [Phase 2: Analyze Codebase](#phase-2-analyze-codebase)
  - [Phase 3: Generate Documentation](#phase-3-generate-documentation)
  - [Phase 4: Validate & Deliver](#phase-4-validate--deliver)
- [CLI Tools](#cli-tools)
- [Critical Rules](#critical-rules)
- [Best Practices](#best-practices)
- [Common Scenarios](#common-scenarios)
- [Reference](#reference)

---

## Quick Start

### Option 1: AI-Enhanced Documentation (Recommended)

**Single-Step Workflow with AI Assistance:**

```bash
sdd doc analyze-with-ai <directory> --name ProjectName --version X.Y.Z --verbose
```

**This generates:**
- `DOCUMENTATION.md` - Structural reference (classes, functions, dependencies)
- `ARCHITECTURE.md` - Architecture and design docs (composed from AI research)
- `AI_CONTEXT.md` - Quick reference for AI assistants (composed from AI research)
- `documentation.json` - Machine-readable structural data

**Requirements:**
- At least one AI CLI tool installed: cursor-agent (with gpt-4.1), gemini, or codex
- Uses multi-agent consultation by default for comprehensive analysis

### Option 2: Structural Documentation Only

**Essential 4-Step Workflow (no AI required):**

1. **Understand** → Clarify scope and output requirements
- What needs documentation? (whole project, specific modules, public API only)
- What format? (markdown, JSON, or both)
- What to exclude? (tests, migrations, generated code)

2. **Analyze** → Run codebase analysis
```bash
sdd doc analyze <directory> --verbose
```

3. **Generate** → Create documentation files
```bash
sdd doc generate <directory> --name ProjectName --version X.Y.Z --format both --verbose
```

4. **Validate** → Verify output quality
```bash
sdd doc validate-json ./docs/documentation.json
```

---

## When to Use This Skill

**Use this skill when the user asks to:**
- Generate documentation for a multi-language codebase
- Create API documentation automatically
- Analyze code structure and complexity across multiple languages
- Document classes, functions, and dependencies
- Generate machine-readable codebase metadata (JSON)
- Create developer onboarding materials
- Track code quality metrics
- **Understand codebase architecture (AI-powered)**
- **Generate AI assistant context documentation (AI-powered)**
- **Create architecture diagrams and design docs (AI-powered)**

**Supported Languages:**
- **Python** - Full AST parsing, complexity metrics
- **JavaScript/TypeScript** - Classes, functions, exports, imports, JSX
- **Go** - Packages, structs, interfaces, methods
- **HTML** - Elements, HTMX attributes, custom components
- **CSS** - Selectors, rules, variables, @-rules

**AI-Enhanced Features:**
- **Multi-agent research** - Parallel consultation with multiple AI models for comprehensive analysis
- **Contextual analysis** - AI CLIs analyze code to understand "what" and "why", not just "how"
- **Architecture documentation** - Main agent composes docs from AI research findings
- **AI assistant quick reference** - Optimized context documentation for AI coding assistants

**Do NOT use for:**
- Writing conceptual documentation (tutorials, guides, explanations)
- Generating docstrings (this extracts existing docstrings)
- Code generation or modification
- Testing or debugging (use `Skill(run-tests)` instead)

---

## Research-then-Compose Architecture

**IMPORTANT: Understanding What Gets Generated Automatically vs Manually**

This skill uses a **research-then-compose pattern** for AI-enhanced documentation:

### What `analyze-with-ai` Command Does Automatically

When you run the `analyze-with-ai` command, it:
1. ✅ **Generates structural docs automatically** (DOCUMENTATION.md, documentation.json)
2. ✅ **Calls external AI CLIs** (cursor-agent, gemini, codex) for research
3. ✅ **Receives research findings** as text responses from AI CLIs
4. ⚠️ **Returns research to calling script** (does NOT write ARCHITECTURE.md/AI_CONTEXT.md itself)

### What the Main Agent Must Do After Research

**CRITICAL:** The main Claude Code agent must:
1. **Compose ARCHITECTURE.md** from AI research findings
   - Research is returned as plain text
   - Agent adds proper markdown headers
   - Agent adds project metadata (name, version, date)
   - Agent writes the final file to disk

2. **Compose AI_CONTEXT.md** from AI research findings
   - Same composition process
   - Format for AI assistant consumption
   - Write final file

### The Two-Phase Workflow

**Phase 1: Research (AI CLIs - Read-Only)**
- External AI CLIs analyze code files
- They identify patterns and architectural decisions
- They return research findings as text
- **They DO NOT write files** (read-only access only)

**Phase 2: Composition (Main Agent - Write Access)**
- Main agent receives research text
- Agent formats into documentation structure
- Agent writes ARCHITECTURE.md and AI_CONTEXT.md
- All file I/O happens in the main agent

**Why this separation?**
- External AI CLIs called via subprocess have read-only tools
- Main agent has full write access
- Ensures reliable operation across different AI CLI tools

---

## Core Documentation Process

### Phase 1: Understand Requirements

**1.1 Clarify Scope**

Ask the user to specify:
- **Target directory**: Which part of the codebase to document?
- **Project name**: How should the project be identified?
- **Version**: What version to document?
- **Output format**: Markdown, JSON, or both?
- **Exclusions**: What directories/patterns to skip?

**Common questions to ask:**
```
"Should I document the entire project or specific modules?"
"Do you need human-readable docs (Markdown), machine-readable (JSON), or both?"
"Should I exclude tests, migrations, or other directories?"
"What project name and version should I use?"
```

**1.2 Set Defaults**

If user doesn't specify:
- **Format**: Use `both` (Markdown + JSON)
- **Output directory**: Use `./docs`
- **Exclusions**: Add `tests`, `migrations`, `__pycache__`, `.git`, `venv`
- **Version**: Use `1.0.0` or derive from git tags

---

### Phase 2: Analyze Codebase

**2.1 Initial Analysis (Optional but Recommended)**

Run analyze command to preview statistics without generating files:

```bash
sdd doc analyze <directory> --exclude tests --exclude migrations --verbose
```

**Look for:**
- Total files, lines, classes, functions
- Average complexity (should be < 10 ideally)
- High complexity functions (> 15 indicates refactoring needs)
- Any syntax errors in files

**2.2 Report Findings**

Tell the user:
```
"I've analyzed the codebase:
- 45 Python files
- 23 classes
- 156 functions
- Average complexity: 4.2 (good)
- 2 high-complexity functions found

Ready to generate documentation. Proceeding with generation..."
```

---

### Phase 3: Generate Documentation

**3.1 Run Generation Command**

Use the generate subcommand with appropriate options:

```bash
sdd doc generate <directory> --name "ProjectName" --version "X.Y.Z" --output-dir ./docs --format both --exclude tests --exclude migrations --exclude __pycache__ --verbose
```

**Command breakdown:**
- `generate <directory>`: Target directory to document
- `--name`: Project name (required for good output)
- `--version`: Version string (defaults to 1.0.0)
- `--output-dir`: Where to save files (defaults to ./docs)
- `--format`: `markdown`, `json`, or `both` (default: both)
- `--exclude`: Pattern to exclude (can use multiple times)
- `--verbose`: Show progress (ALWAYS use this)

**3.2 Monitor Output**

Watch for:
- ✅ Successful file processing
- ⚠️ Syntax errors (will skip file and continue)
- ❌ Critical errors (will abort)

**3.3 Capture File Paths**

Note the output file locations reported by the tool:
```
✅ Markdown: /path/to/docs/DOCUMENTATION.md
✅ JSON: /path/to/docs/documentation.json
```

---

### Phase 4: Validate & Deliver

**4.1 Validate JSON Output**

If JSON was generated, ALWAYS validate:

```bash
sdd doc validate-json ./docs/documentation.json
```

Expected output:
```
✅ JSON documentation is valid
```

**4.2 Review Generated Content**

Read the generated files to verify quality:
- Check that major classes and functions are documented
- Verify complexity metrics seem reasonable
- Ensure dependencies are captured

**4.3 Provide Summary**

Tell the user what was created:

```
"Documentation generated successfully!

📄 Files created:
- docs/DOCUMENTATION.md (human-readable)
- docs/documentation.json (machine-readable)

📊 Coverage:
- 45 modules documented
- 23 classes with methods
- 156 functions with complexity scores
- Full dependency graph included

✅ JSON validation passed

The Markdown file provides a comprehensive overview for developers.
The JSON file can be used for tooling, analysis, or integration."
```

---

## CLI Tools

### Main CLI: `code_doc_tools.py`

Located at: `scripts/code_doc_tools.py`

**Four subcommands:**

#### 1. `analyze-with-ai` - Comprehensive Documentation with AI (NEW)

```bash
sdd doc analyze-with-ai <directory> [options]
```

**When to use:**
- User wants comprehensive documentation (structural + contextual)
- Building documentation for AI coding assistants
- Need architecture and design documentation
- Want multi-agent analysis for comprehensive coverage

**Options:**
- `--name NAME`: Project name (IMPORTANT - use this!)
- `--version VERSION`: Version string (default: 1.0.0)
- `--output-dir DIR`: Output location (default: ./docs)
- `--ai-tool {auto,cursor-agent,gemini,codex}`: Specific AI tool to use
- `--single-agent`: Use single agent instead of multi-agent (faster but less comprehensive)
- `--skip-architecture`: Skip ARCHITECTURE.md generation
- `--skip-ai-context`: Skip AI_CONTEXT.md generation
- `--dry-run`: Show what would be generated without running AI
- `--exclude PATTERN`: Exclude pattern (repeatable)
- `--verbose, -v`: Show progress (ALWAYS use)

**Output:**
- `DOCUMENTATION.md` - Structural reference
- `ARCHITECTURE.md` - Architecture docs (composed from AI research)
- `AI_CONTEXT.md` - AI assistant quick reference (composed from AI research)
- `documentation.json` - Machine-readable data

**AI Tools:**
- **cursor-agent with gpt-4.1** (preferred) - 1M context, excellent for large codebases
- **gemini** - Fast, good for structured analysis
- **codex** - Good for code understanding

**Multi-Agent Mode (Default):**
- Consults multiple AI models in parallel
- Synthesizes responses for comprehensive coverage
- Recommended for production documentation

#### 2. `analyze` - Preview Statistics Only

```bash
sdd doc analyze <directory> [options]
```

**When to use:**
- User wants to understand codebase metrics without generating docs
- Preview before full documentation generation
- Quick complexity check

**Options:**
- `--name`: Project name for display
- `--exclude PATTERN`: Exclude pattern (repeatable)
- `--verbose, -v`: Show progress

**Output:**
- Project statistics
- High complexity functions
- No files created

#### 3. `generate` - Create Documentation

```bash
sdd doc generate <directory> [options]
```

**When to use:**
- Main documentation generation task
- User wants docs created

**Options:**
- `--name NAME`: Project name (IMPORTANT - use this!)
- `--version VERSION`: Version string (default: 1.0.0)
- `--output-dir DIR`: Output location (default: ./docs)
- `--format FORMAT`: markdown, json, or both (default: both)
- `--exclude PATTERN`: Exclude pattern (repeatable)
- `--verbose, -v`: Show progress (ALWAYS use)

**Output:**
- DOCUMENTATION.md (if format includes markdown)
- documentation.json (if format includes json)

#### 4. `validate-json` - Check JSON Schema

```bash
sdd doc validate-json <json_file>
```

**When to use:**
- After generating JSON documentation
- Before delivering to user
- To verify JSON structure

**Output:**
- ✅ Validation success
- ❌ Validation errors with details

---

## AI Tool Setup (for analyze-with-ai)

### Checking Tool Availability

The skill will automatically detect which tools are installed and use the best one. You can check manually:

```bash
# Try running each tool
cursor-agent --version
gemini --version
codex --version
```

### Multi-Agent vs Single-Agent

**Multi-Agent (Default - Recommended)**
- Consults 2+ AI models in parallel
- Synthesizes responses for comprehensive coverage
- Best for production documentation
- Slower but more thorough

**Single-Agent (--single-agent flag)**
- Uses one AI model
- Faster
- Good for quick iterations or when only one tool is available

## Critical Rules

### MUST DO:

1. **Always use `--verbose`** - Provides progress visibility and helps debug issues

2. **Always specify `--name`** - Improves documentation quality significantly
```bash
# Good
--name "MyProject"

# Bad (will use directory name)
# (no --name)
```

3. **Always validate JSON output** if format includes JSON:
```bash
sdd doc validate-json ./docs/documentation.json
```

4. **Exclude non-code directories** by default:
- tests/
- migrations/
- __pycache__/
- .git/
- venv/, .venv/
- build/, dist/

5. **Run from skill directory** or provide absolute paths to scripts

### MUST NOT DO:

1. **Never document everything indiscriminately** - Exclude tests, generated code, migrations

2. **Never skip validation** - Always validate JSON before delivering

3. **Never guess file paths** - Use the actual output paths from the tool

4. **Never modify the JSON output manually** - Regenerate if changes needed

5. **Never ignore syntax errors** - Note them for the user (tool will skip and continue)

---

## Best Practices

### For Best Results:

1. **Preview First (Recommended)**
```bash
# Run analyze to preview
sdd doc analyze ./src --verbose

# Then generate if stats look good
sdd doc generate ./src --name Project --verbose
```

2. **Use Semantic Versioning**
```bash
# Good
--version "2.1.0"

# Less useful
--version "latest"
```

3. **Appropriate Exclusions**
```bash
# For Django projects
--exclude tests --exclude migrations --exclude static

# For data science projects
--exclude notebooks --exclude data --exclude experiments

# For microservices
--exclude tests --exclude deployment --exclude scripts
```

4. **Output Organization**
```bash
# Version-specific docs
--output-dir ./docs/v2.0.0

# Per-module docs
--output-dir ./docs/auth-module
```

### Communication Style:

**Be informative:**
```
"I'll generate documentation for your project.
Let me first analyze the codebase structure..."

[runs analyze command]

"Found 45 files with 156 functions. Average complexity is 4.2 which is good.
Now generating comprehensive documentation..."

[runs generate command]

"Documentation created successfully!
- DOCUMENTATION.md provides human-readable overview
- documentation.json contains structured data for tooling"
```

**Report issues clearly:**
```
"⚠️ Found 2 files with syntax errors that were skipped:
- old_module.py (line 45: invalid syntax)
- legacy_code.py (line 123: unexpected indent)

Documentation generated for the remaining 43 valid files."
```

---

## Common Scenarios

### Scenario 1: Full Project Documentation with AI (RECOMMENDED)

**User Request:** "Document my entire Python project" or "Generate comprehensive documentation"

**Your Response:**
1. Ask: "Should I exclude tests and migrations?"
2. Use `analyze-with-ai` command
3. Report what was generated
4. Highlight AI-generated architecture and AI context docs

**Example:**
```bash
# Single command generates everything
sdd doc analyze-with-ai ./my_project --name "MyProject" --version "1.0.0" --exclude tests --exclude migrations --verbose
```

**Output:**
```
docs/
├── DOCUMENTATION.md       # Structural (classes, functions, deps)
├── ARCHITECTURE.md        # Architecture docs (from AI research)
├── AI_CONTEXT.md         # AI quick reference (from AI research)
└── documentation.json    # Machine-readable structural
```

### Scenario 1b: Full Project Documentation (Structural Only)

**User Request:** "Document my Python project" (when no AI tools available)

**Your Response:**
1. Ask: "Should I exclude tests and migrations?"
2. Run: `analyze` command for preview
3. Report statistics
4. Run: `generate` with appropriate exclusions
5. Validate JSON output
6. Deliver summary with file paths

**Example:**
```bash
# Analyze
sdd doc analyze ./my_project --exclude tests --exclude migrations --verbose

# Generate
sdd doc generate ./my_project --name "MyProject" --version "1.0.0" --format both --exclude tests --exclude migrations --verbose

# Validate
sdd doc validate-json ./docs/documentation.json
```

---

### Scenario 2: API Documentation Only

**User Request:** "Generate API documentation for the src/ directory"

**Your Response:**
1. Focus on src/ directory
2. Use meaningful project name
3. Generate both formats
4. Validate

**Example:**
```bash
sdd doc generate ./src --name "MyProject API" --version "2.1.0" --format both --verbose
```

---

### Scenario 3: Quick Complexity Check

**User Request:** "What's the code complexity of my project?"

**Your Response:**
1. Use `analyze` subcommand
2. Report statistics
3. Highlight any concerns

**Example:**
```bash
sdd doc analyze ./src --verbose
```

**Report:**
```
"Your codebase analysis:
- 45 files, 3,421 lines
- 23 classes, 156 functions
- Average complexity: 4.2 (Good - below 10 is healthy)
- Maximum complexity: 15
- 2 high-complexity functions found:
  - process_data (complexity: 15)
  - validate_input (complexity: 12)

Consider refactoring these functions to improve maintainability."
```

---

### Scenario 4: JSON-Only for Tooling

**User Request:** "I need JSON output for my CI/CD pipeline"

**Your Response:**
1. Generate JSON only
2. Validate thoroughly
3. Provide path

**Example:**
```bash
# Generate JSON only
sdd doc generate ./src --name "MyProject" --format json --output-dir ./ci_artifacts --verbose

# Validate
sdd doc validate-json ./ci_artifacts/documentation.json
```

---

### Scenario 5: Large Codebase with Many Exclusions

**User Request:** "Document my Django monolith but skip tests, migrations, and static files"

**Your Response:**
1. Multiple `--exclude` flags
2. Use verbose to track progress
3. Expect longer processing time

**Example:**
```bash
sdd doc generate ./django_project --name "DjangoApp" --version "3.2.0" --exclude tests --exclude migrations --exclude static --exclude media --exclude venv --format both --verbose
```

---

## Reference

### Output File Structure

**Markdown (DOCUMENTATION.md):**
```markdown
# Project Documentation

**Version:** X.Y.Z
**Generated:** YYYY-MM-DD HH:MM:SS

## 📊 Project Statistics
- Total Files, Lines, Classes, Functions
- Complexity metrics

## 🏛️ Classes
[Each class with methods, properties, inheritance]

## ⚡ Functions
[Each function with parameters, return types, complexity]

## 📦 Dependencies
[Import relationships by module]
```

**JSON (documentation.json):**
```json
{
  "metadata": {
    "project_name": "string",
    "version": "string",
    "generated_at": "ISO datetime",
    "language": "python"
  },
  "statistics": { ... },
  "modules": [ ... ],
  "classes": [ ... ],
  "functions": [ ... ],
  "dependencies": { ... }
}
```

Full schema: `documentation-schema.json`

---

### Complexity Guidelines

**Cyclomatic Complexity Scores:**
- **1-5**: Simple, easy to test (Good ✅)
- **6-10**: Moderate, acceptable (OK ⚠️)
- **11-20**: Complex, needs attention (Warning ⚠️)
- **21+**: Very complex, refactor recommended (Critical ❌)

**Project Averages:**
- **< 5**: Excellent code quality
- **5-10**: Good, maintainable
- **10-15**: Concerning, review needed
- **> 15**: Serious technical debt

---

### Helper Scripts Location

All CLI tools are in `scripts/` directory:
- `scripts/code_doc_tools.py` - Main CLI (use this)
- `scripts/generator.py` - Orchestration (internal)
- `scripts/parser.py` - AST parsing (internal)
- `scripts/calculator.py` - Metrics (internal)
- `scripts/formatter.py` - Output formatting (internal)

**Only use `code_doc_tools.py`** - the other scripts are internal modules.

---

### Additional References

Located in `references/` directory:

1. **quick-reference.md** - CLI command reference and common workflows
2. **examples.md** - 12+ real-world usage scenarios
3. **patterns.md** - Best practices for different project types
4. **examples/** - Sample input/output files

Read these files for:
- Detailed command examples
- CI/CD integration patterns
- Project-type-specific recommendations
- Pre-commit hook setups

---

## Success Criteria

**Documentation generation is successful when:**

✅ All subcommands execute without errors
✅ Output files are created at expected locations
✅ JSON validation passes
✅ Statistics are reasonable (no anomalies)
✅ Markdown is well-formatted and readable
✅ Dependencies are captured correctly
✅ Syntax errors (if any) are noted for user

**Deliver to user:**
- File paths to generated documentation
- Summary of what was documented
- Any warnings or issues encountered
- Complexity insights if relevant
- Next steps (e.g., "Review DOCUMENTATION.md for overview")

---

## Prerequisites

**Before using this skill, check:**

**AI CLI tools** (optional, for AI-enhanced features):
   - cursor-agent (recommended for large codebases)
   - gemini CLI
   - codex CLI

Using `Skill(run-tests) check-tools`.

---

## Failure Handling & Troubleshooting

### Common Issues and Solutions

**1. ImportError: No module named 'tree_sitter'**
```bash
# Solution: Install tree-sitter dependencies
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-go tree-sitter-html tree-sitter-css
```

**2. No parser available for language**
- Some parsers require tree-sitter dependencies
- Falls back to skipping unsupported files
- Check output for "⚠️ No parser available" warnings

**3. AI tool not found (cursor-agent, gemini, codex)**
```bash
# Fallback: Use structural documentation only
sdd doc generate ./src --name MyProject

# Or install AI tools:
# cursor-agent: See cursor.com
# gemini: npm install -g @google/generative-ai-cli
# codex: npm install -g @anthropic/codex
```

**4. Validation errors in JSON**
- Re-run generation with `--verbose` to see details
- Check for syntax errors in source files
- Use `sdd doc validate-json` to identify issues

**5. Schema validation fails**
- Ensure jsonschema installed: `pip install jsonschema`
- Basic validation runs without it
- Install for full schema validation

### Retry Strategies

**If generation fails:**
1. Run with `--verbose` to see detailed errors
2. Add problematic files/directories to `--exclude`
3. Try with narrower scope (single language)
4. Check disk space and permissions

**If AI-enhanced docs fail:**
1. Verify AI tool installation
2. Check API rate limits
3. Try `--single-agent` instead of multi-agent
4. Fall back to structural docs only

---

## Key Reminders

1. **Standalone skill** - No SDD integration, works independently

2. **Multi-language support** - Supports Python, JS/TS, Go, HTML, CSS

3. **Read-only analysis** - Never modifies source code, only generates docs

4. **Use the CLI** - Don't implement manually; use `sdd doc` command

5. **Validate everything** - Always validate JSON output before delivering

6. **Verbose is your friend** - Always use `--verbose` flag for visibility

7. **Exclude intelligently** - Default exclusions for tests, migrations, venv, node_modules

8. **Project naming matters** - Always use `--name` for better documentation

---

## Final Notes

**This skill provides ready-to-use CLI tools for documentation generation. Your job is to:**
1. Understand user requirements
2. Execute the appropriate CLI commands
3. Validate output
4. Deliver results with helpful context

**You are NOT:**
- Writing documentation generators from scratch
- Implementing AST parsing
- Creating custom formatters

**The tools are already built - use them effectively!**

For detailed command examples, workflow patterns, and integration scenarios, refer to the `references/` directory.
