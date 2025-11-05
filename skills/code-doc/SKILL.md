---
name: code-doc
description: Multi-language codebase documentation generation supporting Python, JavaScript/TypeScript, Go, HTML, CSS, and more. Creates both human-readable markdown documentation and machine-readable JSON output. Includes AST parsing, dependency analysis, code metrics, and automated documentation workflows.
---

# Codebase Documentation Generator Skill

## Overview

Multi-language codebase documentation generator that creates both human-readable markdown and machine-readable JSON output. Supports AST parsing, dependency analysis, code metrics, and AI-enhanced contextual documentation.

**Use this skill when:**
- Generate documentation for multi-language codebases (Python, JS/TS, Go, HTML, CSS)
- Create API documentation automatically
- Analyze code structure, complexity, and dependencies
- Generate machine-readable codebase metadata
- Create developer onboarding materials with architecture docs (AI-enhanced)
- Generate AI assistant context documentation (AI-enhanced)

**Key features:**
- **Structural documentation** - Classes, functions, dependencies, metrics
- **AI-enhanced documentation** - Multi-agent consultation for architecture and context docs
- **12 query commands** - Explore generated docs (stats, search, complexity, dependencies)
- **Read-only analysis** - Never modifies source code

**Do NOT use for:**
- Writing conceptual documentation (tutorials, guides)
- Generating docstrings (this extracts existing docstrings)
- Code generation or modification
- Testing or debugging (use `Skill(sdd-toolkit:run-tests)`)

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd doc CLI is installed and accessible
sdd doc --help
```

**Expected output**: Help text showing available commands (analyze, generate, validate-json, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd doc` CLI wrapper commands (e.g., `sdd doc analyze`, `sdd doc generate`, `sdd doc validate-json`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python src/claude_skills/code_doc/cli.py`, `bash python analyze.py`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

---

## Quick Start

**Basic 4-Step Workflow:**

1. **Analyze (Optional)** → Preview codebase structure
```bash
sdd doc analyze <directory> --verbose
```

2. **Generate** → Create documentation
```bash
# AI-enhanced (recommended if AI tools available)
sdd doc analyze-with-ai <directory> --name ProjectName --version X.Y.Z --verbose

# Structural only (no AI required)
sdd doc generate <directory> --name ProjectName --version X.Y.Z --verbose
```

3. **Validate** → Verify JSON output
```bash
sdd doc validate-json ./docs/documentation.json
```

4. **Query** → Explore generated documentation
```bash
sdd doc stats --docs-path ./docs/documentation.json
sdd doc search "MyClass" --docs-path ./docs/documentation.json
```

**AI-enhanced workflow outputs:**
- `DOCUMENTATION.md`, `documentation.json` (auto-written by skill)
- JSON research to stdout (main agent synthesizes → `ARCHITECTURE.md`, `AI_CONTEXT.md`)

**See sections below for:** Research-then-Synthesis Architecture, CLI Tools, Documentation Query Commands (all 12)

---

## AI-Enhanced Workflow (Research-then-Synthesis)

**Two-Phase Process:**

### Phase 1: Research Gathering (Skill)

The `analyze-with-ai` command:
- Generates structural docs (DOCUMENTATION.md, documentation.json) automatically
- Calls AI CLIs in parallel (cursor-agent + gemini by default)
- Collects separate research from each tool
- Returns JSON with research keyed by tool name to stdout
- **Does NOT write ARCHITECTURE.md/AI_CONTEXT.md** (main agent does this)

**JSON output format:**
```json
{
  "architecture_research": {"cursor-agent": "...", "gemini": "..."},
  "ai_context_research": {"cursor-agent": "...", "gemini": "..."}
}
```

### Phase 2: Synthesis (Main Agent)

**The main agent must:**
1. Parse JSON output between `RESEARCH_JSON_START` and `RESEARCH_JSON_END` markers
2. Synthesize ARCHITECTURE.md from multiple AI perspectives
   - Merge complementary insights, resolve contradictions, remove redundancy
   - Create unified architecture documentation
3. Synthesize AI_CONTEXT.md from multiple AI perspectives
   - Same process, optimized for AI assistant consumption
4. Write both files to output_dir

**Why this separation?** AI CLIs provide diverse perspectives without bias. Main agent (Claude Code) has user context and makes intelligent synthesis decisions.

**Multi-agent mode (default):** Consults 2 AI models in parallel for comprehensive analysis. Falls back to 1 if only 1 tool installed.

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

### Main CLI: `sdd doc`

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
- `DOCUMENTATION.md` - Structural reference (auto-written by skill)
- `documentation.json` - Machine-readable data (auto-written by skill)
- JSON to stdout - Research from all AI tools (for main agent synthesis)

**Main agent then writes:**
- `ARCHITECTURE.md` - Synthesized architecture docs
- `AI_CONTEXT.md` - Synthesized AI assistant quick reference

**AI Tools:**
- **cursor-agent with cheetah** (preferred) - 1M context, excellent for large codebases
- **gemini** - Fast, good for structured analysis
- **codex** - Good for code understanding

**Multi-Agent Mode (Default):**
- Consults 2 AI models in parallel for comprehensive analysis
- Uses priority order: cursor-agent → gemini → codex
- Automatically selects best 2 available models (or falls back to 1 if only 1 tool installed)
- Returns separate responses keyed by tool name (no merging/synthesis in skill)
- Main agent performs intelligent synthesis
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

### Documentation Query Commands

After generating documentation with `generate` or `analyze-with-ai`, you can query the generated `documentation.json` file using these commands.

```bash
sdd doc <command> --docs-path ./docs/documentation.json
```

If `--docs-path` is omitted, it auto-detects `./docs/documentation.json`.

---

#### 1. `stats` - Show Documentation Statistics

```bash
sdd doc stats --docs-path ./docs/documentation.json
```

**When to use:**
- Quick overview of documented codebase
- Get total counts (files, classes, functions, lines)
- Check complexity metrics

**Output:**
```
Documentation Statistics:
  Project: MyProject (version 1.0.0)
  Total Files: 85
  Total Classes: 38
  Total Functions: 424
  Total Lines: 25214
  Average Complexity: 6.82
  Max Complexity: 40
```

---

#### 2. `complexity` - Show High-Complexity Functions

```bash
sdd doc complexity --docs-path ./docs/documentation.json --threshold 10
```

**When to use:**
- Identify functions needing refactoring
- Code quality assessment
- Technical debt analysis

**Options:**
- `--threshold N`: Minimum complexity (default: 5)
- `--module PATH`: Filter by module

**Output:**
```
Found 42 result(s):

1. Function: generate_report
   File: src/validator.py
   Complexity: 40
   Parameters: result, options
```

---

#### 3. `find-class` - Find Class by Name or Pattern

```bash
sdd doc find-class PrettyPrinter --docs-path ./docs/documentation.json
sdd doc find-class ".*Printer" --pattern --docs-path ./docs/documentation.json
```

**When to use:**
- Locate a specific class
- Find classes matching a pattern
- Get class details (file, line, methods)

**Options:**
- `--pattern`: Treat name as regex pattern

**Output:**
```
Found 1 result(s):

1. Class: PrettyPrinter
   File: src/common/printer.py
   Line: 8
```

---

#### 4. `find-function` - Find Function by Name or Pattern

```bash
sdd doc find-function register_validate --docs-path ./docs/documentation.json
sdd doc find-function "register_.*" --pattern --docs-path ./docs/documentation.json
```

**When to use:**
- Locate a specific function
- Find functions matching a pattern
- Get function details (file, line, complexity, parameters)

**Options:**
- `--pattern`: Treat name as regex pattern

---

#### 5. `find-module` - Find Module by Name or Pattern

```bash
sdd doc find-module cli.py --docs-path ./docs/documentation.json
sdd doc find-module ".*validator.*" --pattern --docs-path ./docs/documentation.json
```

**When to use:**
- Locate a specific module
- Find modules matching a pattern

**Options:**
- `--pattern`: Treat name as regex pattern

---

#### 6. `search` - Search All Documented Entities

```bash
sdd doc search "validation" --docs-path ./docs/documentation.json
```

**When to use:**
- Search across classes, functions, and modules
- Find entities by keyword
- Broad exploration of codebase

**Output:**
```
Found 48 result(s):

1. Class: SpecValidationResult
   File: src/common/validation.py

2. Function: validate_hierarchy
   File: src/common/hierarchy_validation.py
   Complexity: 22
```

---

#### 7. `context` - Gather Context for Feature Area

```bash
sdd doc context "printer" --docs-path ./docs/documentation.json --limit 5
```

**When to use:**
- Understand a feature area
- Get related classes, modules, and dependencies
- Prepare for feature work

**Options:**
- `--limit N`: Limit results per entity type
- `--include-docstrings`: Include docstring excerpts
- `--include-stats`: Include module statistics

**Output:**
```
Found 3 total entities:

Classes (1):
  - PrettyPrinter (src/common/printer.py)

Modules (1):
  - src/common/printer.py

Dependencies (1):
  - sys
```

---

#### 8. `describe-module` - Describe a Module

```bash
sdd doc describe-module src/common/printer.py --docs-path ./docs/documentation.json
```

**When to use:**
- Get detailed module information
- See module's classes, functions, dependencies
- Understand module complexity

**Options:**
- `--top-functions N`: Limit to top N complex functions
- `--include-docstrings`: Include docstring excerpts
- `--skip-dependencies`: Skip dependency details

**Output:**
```
Module: src/common/printer.py
  Classes: 1 | Functions: 0 | Avg Complexity: 0
  Imports: sys
  Outgoing Dependencies: sys

  Classes (1):
    - PrettyPrinter
```

---

#### 9. `dependencies` - Show Module Dependencies

```bash
sdd doc dependencies src/cli/registry.py --docs-path ./docs/documentation.json
sdd doc dependencies src/common/printer.py --reverse --docs-path ./docs/documentation.json
```

**When to use:**
- Understand module dependencies
- Find reverse dependencies (who depends on this)
- Impact analysis before changes

**Options:**
- `--reverse`: Show reverse dependencies

**Output:**
```
Found 1 result(s):

1. Dependency: logging
   Depended by: src/cli/registry.py
```

---

#### 10. `list-classes` - List All Classes

```bash
sdd doc list-classes --docs-path ./docs/documentation.json
sdd doc list-classes --module src/common --docs-path ./docs/documentation.json
```

**When to use:**
- Browse all classes in codebase
- Filter classes by module
- Get class inventory

**Options:**
- `--module PATH`: Filter by module path

---

#### 11. `list-functions` - List All Functions

```bash
sdd doc list-functions --docs-path ./docs/documentation.json
sdd doc list-functions --module src/validator --docs-path ./docs/documentation.json
```

**When to use:**
- Browse all functions in codebase
- Filter functions by module
- Get function inventory

**Options:**
- `--module PATH`: Filter by module path

---

#### 12. `list-modules` - List All Modules

```bash
sdd doc list-modules --docs-path ./docs/documentation.json
```

**When to use:**
- See all documented modules
- Get module overview
- Navigate codebase structure

**Output:**
```
Found 85 result(s):

1. Module: scripts/extract_commands.py
   Classes: 1 | Functions: 8 | Avg Complexity: 3.75
   Imports: argparse, json, re, ...
```

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
- Consults exactly 2 AI models in parallel
- Uses priority order to select best 2: cursor-agent → gemini → codex
- Automatically adapts: if predefined pair unavailable, selects ANY 2 available tools
- Synthesizes responses for comprehensive coverage
- Best for production documentation
- Slower but more thorough

**Single-Agent (--single-agent flag)**
- Uses one AI model
- Faster
- Good for quick iterations

**Automatic Fallback:**
- If only 1 AI tool is installed system-wide → automatically uses single-agent mode
- If 2+ AI tools are installed → always uses 2 models in parallel (unless --single-agent flag is set)

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

6. **Always report AI model errors to the user** - If any AI models fail during `analyze-with-ai`, inform the user which models failed, which succeeded, and the impact on the generated documentation

### MUST NOT DO:

1. **Never document everything indiscriminately** - Exclude tests, generated code, migrations

2. **Never skip validation** - Always validate JSON before delivering

3. **Never guess file paths** - Use the actual output paths from the tool

4. **Never modify the JSON output manually** - Regenerate if changes needed

5. **Never ignore syntax errors** - Note them for the user (tool will skip and continue)

6. **Never hide AI model failures** - Always report which models failed during AI-enhanced documentation, even if the process succeeded with fallback models

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

**Report AI model errors transparently:**
```
"⚠️ AI model consultation encountered an error:
- cursor-agent failed (model 'cheetah' not available)
- gemini succeeded

Documentation was generated successfully using gemini's analysis.
For better coverage in the future, consider updating cursor-agent configuration
or using --single-agent with gemini."
```

**Or for complete AI failure:**
```
"⚠️ All AI models failed during consultation:
- cursor-agent: Model not available
- gemini: API rate limit exceeded

Falling back to structural documentation only.
DOCUMENTATION.md and documentation.json were generated successfully,
but ARCHITECTURE.md and AI_CONTEXT.md could not be created.

You can retry later with: sdd doc analyze-with-ai ..."
```

---

## Common Scenarios

### Scenario 1: Full Project Documentation with AI

**User:** "Document my entire Python project"

**Workflow:**
```bash
sdd doc analyze-with-ai ./my_project --name "MyProject" --version "1.0.0" --exclude tests --exclude migrations --verbose
# Skill returns JSON research → Main agent synthesizes → writes ARCHITECTURE.md, AI_CONTEXT.md
```

**Output:** DOCUMENTATION.md, documentation.json (skill) + ARCHITECTURE.md, AI_CONTEXT.md (main agent)

### Scenario 2: Structural Documentation Only

**User:** "Document my project" (no AI tools available)

**Workflow:**
```bash
sdd doc analyze ./my_project --verbose  # Preview
sdd doc generate ./my_project --name "MyProject" --version "1.0.0" --exclude tests --verbose
sdd doc validate-json ./docs/documentation.json
```

### Scenario 3: Quick Complexity Check

**User:** "What's the code complexity?"

**Workflow:**
```bash
sdd doc analyze ./src --verbose
```

Report: 45 files, 156 functions, avg complexity 4.2 (good), 2 high-complexity functions needing refactoring.

### Scenario 4: API Documentation

**User:** "Generate API docs for src/"

**Workflow:**
```bash
sdd doc generate ./src --name "MyProject API" --version "2.1.0" --verbose
```

### Scenario 5: Large Codebase with Exclusions

**User:** "Document Django project, skip tests/migrations/static"

**Workflow:**
```bash
sdd doc generate ./django_project --name "DjangoApp" --version "3.2.0" --exclude tests --exclude migrations --exclude static --exclude media --verbose
```

### Scenario 6: Querying Generated Documentation

**User:** "Find validation classes" or "Show high-complexity functions"

**Workflow:**
```bash
sdd doc search "validation" --docs-path ./docs/documentation.json
sdd doc complexity --threshold 15 --docs-path ./docs/documentation.json
sdd doc context "printer" --docs-path ./docs/documentation.json
sdd doc find-class PrettyPrinter --docs-path ./docs/documentation.json
```

**Use query commands for:** Exploring docs, finding classes/functions/modules, analyzing complexity/dependencies, quick lookups.

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

Using `sdd test check-tools`.

---

## Troubleshooting

### Common Issues

**ImportError: tree_sitter**
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-go
```

**No parser available for language**
- Tool skips unsupported files automatically
- Check output for warnings

**AI tool not found**
```bash
# Fallback to structural docs
sdd doc generate ./src --name MyProject --verbose
```

**Validation errors in JSON**
- Re-run with `--verbose` to see details
- Check for syntax errors in source files

**Schema validation fails**
```bash
pip install jsonschema  # For full schema validation
```

### AI Model Failures

**IMPORTANT: Always report model errors transparently to the user.**

**When AI-enhanced docs fail:**
1. Check tool output for ✓ (success) or ✗ (failure) per model
2. Report which models failed/succeeded and why
3. Explain impact on generated docs
4. Suggest fixes:
   - Verify installation: `cursor-agent --version`, `gemini --version`
   - Check API limits/authentication
   - Try `--single-agent` with working model
   - Fall back to structural docs: `sdd doc generate`

**Always report:**
- Which models were attempted
- Which succeeded/failed with reasons
- What docs were/weren't generated
- How to fix for future runs

---

## Technical Reference

### AI Tool Integration

This skill uses the standardized `ai_tools` module (`claude_skills.common.ai_tools`) for AI-enhanced documentation generation. The module provides:

- **Unified API** - Consistent interface for cursor-agent, gemini, and codex CLI tools
- **Type-safe responses** - Structured `ToolResponse` and `MultiToolResponse` dataclasses
- **Parallel execution** - Run multiple AI models concurrently for comprehensive analysis
- **Robust error handling** - Automatic timeout, retry, and fallback logic
- **Tool availability detection** - Check which AI CLIs are installed before analysis

**For detailed API documentation, see:** [AI Tools API Reference](../../docs/API_AI_TOOLS.md)

**Key functions used by this skill:**
- `execute_tools_parallel()` - Multi-agent consultation (runs 2 tools in parallel by default)
- `detect_available_tools()` - Check which AI CLIs are available on the system
- `check_tool_available()` - Verify a specific tool is installed
- `ToolResponse.success` - Check if consultation succeeded
- `MultiToolResponse.get_successful_responses()` - Filter successful consultations

The `sdd doc analyze-with-ai` command internally uses these functions to coordinate parallel AI consultations for architecture and context documentation, returning separate research from each tool for the main agent to synthesize.

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