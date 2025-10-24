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

### Option 1: AI-Enhanced Documentation with Main Agent Synthesis (Recommended)

**Two-Phase Workflow with AI Research + Main Agent Synthesis:**

```bash
sdd doc analyze-with-ai <directory> --name ProjectName --version X.Y.Z --verbose
```

**Phase 1: Skill gathers research**
- Writes `DOCUMENTATION.md` - Structural reference (classes, functions, dependencies)
- Writes `documentation.json` - Machine-readable structural data
- Runs multi-agent AI consultation (cursor-agent + gemini in parallel)
- Returns JSON with separate responses from each AI tool to stdout

**Phase 2: Main agent synthesizes**
- Parses JSON output containing research from all AI tools
- Intelligently synthesizes findings from multiple perspectives
- Writes `ARCHITECTURE.md` - Unified architecture documentation
- Writes `AI_CONTEXT.md` - Unified AI assistant quick reference

**Requirements:**
- At least one AI CLI tool installed: cursor-agent (with cheetah), gemini, or codex
- Uses 2-model consultation by default for comprehensive analysis (falls back to single-model if only 1 tool available)
- Main agent (Claude Code) performs final synthesis

**After generation, you can query the documentation:**
```bash
sdd doc stats --docs-path ./docs/documentation.json
sdd doc find-class MyClass --docs-path ./docs/documentation.json
```
See "Documentation Query Commands" section for all 12 query commands.

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

5. **Query (Optional)** → Explore the generated documentation
```bash
# Get statistics
sdd doc stats --docs-path ./docs/documentation.json

# Find high-complexity functions
sdd doc complexity --threshold 10 --docs-path ./docs/documentation.json

# Search for specific entities
sdd doc search "MyClass" --docs-path ./docs/documentation.json
```

**Note:** All query commands support flexible argument order - put `--docs-path` before or after the subcommand.

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
- Testing or debugging (use `Skill(sdd-toolkit:run-tests)` instead)

---

## Research-then-Synthesis Architecture

**IMPORTANT: Understanding What Gets Generated Automatically vs By Main Agent**

This skill uses a **research gathering + main agent synthesis pattern** for AI-enhanced documentation:

### What `analyze-with-ai` Command Does Automatically

When you run the `analyze-with-ai` command, it:
1. ✅ **Generates structural docs automatically** (DOCUMENTATION.md, documentation.json)
2. ✅ **Calls external AI CLIs in parallel** (cursor-agent + gemini by default)
3. ✅ **Collects separate research responses** from each AI tool
4. ✅ **Returns JSON to stdout** with research keyed by tool name
5. ⚠️ **Does NOT write ARCHITECTURE.md/AI_CONTEXT.md** (main agent does this)

**JSON Output Format:**
```json
{
  "status": "success",
  "project_name": "MyProject",
  "version": "1.0.0",
  "output_dir": "docs",
  "architecture_research": {
    "cursor-agent": "raw architecture research from cursor-agent",
    "gemini": "raw architecture research from gemini"
  },
  "ai_context_research": {
    "cursor-agent": "raw AI context research from cursor-agent",
    "gemini": "raw AI context research from gemini"
  },
  "statistics": {...}
}
```

### What the Main Agent Must Do After Research

**CRITICAL:** The main Claude Code agent must:
1. **Parse JSON output** from skill's stdout
   - Extract between `RESEARCH_JSON_START` and `RESEARCH_JSON_END` markers
   - Parse as JSON object

2. **Synthesize ARCHITECTURE.md** from multiple AI perspectives
   - Read responses from cursor-agent and gemini separately
   - Intelligently merge insights and remove redundancy
   - Create unified, coherent architecture documentation
   - Add proper headers, project metadata, and formatting
   - Write final file to output_dir

3. **Synthesize AI_CONTEXT.md** from multiple AI perspectives
   - Same synthesis process
   - Format optimized for AI assistant consumption
   - Write final file to output_dir

### The Two-Phase Workflow

**Phase 1: Research Gathering (Skill)**
- Skill runs multi-agent consultation in parallel
- Each AI CLI analyzes code files independently
- Each provides their unique perspective
- Skill collects all responses without filtering or merging
- Returns raw responses as JSON to stdout
- **Does NOT synthesize or write AI docs**

**Phase 2: Synthesis (Main Agent)**
- Main agent receives separate responses from all AI tools
- Agent makes intelligent synthesis decisions:
  - Merges complementary insights
  - Resolves contradictions
  - Removes redundancy
  - Highlights unique perspectives where valuable
- Agent writes final ARCHITECTURE.md and AI_CONTEXT.md
- All synthesis and file writing happens in main agent

**Why this separation?**
- AI CLIs provide diverse perspectives without bias
- Main agent (Claude Code) has context about the user's needs
- Main agent can make intelligent synthesis decisions
- Cleaner separation of concerns: research vs. synthesis

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

### Scenario 1: Full Project Documentation with AI (RECOMMENDED)

**User Request:** "Document my entire Python project" or "Generate comprehensive documentation"

**Your Response:**
1. Ask: "Should I exclude tests and migrations?"
2. Run `analyze-with-ai` command (gathers research)
3. Parse JSON output from skill
4. Synthesize findings from multiple AI perspectives
5. Write ARCHITECTURE.md and AI_CONTEXT.md
6. Report what was generated

**Example:**
```bash
# Step 1: Run skill to gather research
sdd doc analyze-with-ai ./my_project --name "MyProject" --version "1.0.0" --exclude tests --exclude migrations --verbose

# Step 2: Skill writes structural docs and returns JSON
# Step 3: You (main agent) parse JSON with research from cursor-agent and gemini
# Step 4: You synthesize both perspectives into unified docs
# Step 5: You write final ARCHITECTURE.md and AI_CONTEXT.md
```

**Final Output:**
```
docs/
├── DOCUMENTATION.md       # Structural (auto-written by skill)
├── documentation.json     # Machine-readable (auto-written by skill)
├── ARCHITECTURE.md        # Synthesized by main agent from multi-AI research
└── AI_CONTEXT.md          # Synthesized by main agent from multi-AI research
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

### Scenario 6: Querying Generated Documentation

**User Request:** "Find all classes related to validation" or "Show me high-complexity functions" or "What modules handle printing?"

**Your Response:**
1. Verify documentation exists
2. Use appropriate query command
3. Present results clearly
4. Offer to dive deeper if needed

**Example:**
```bash
# Find validation-related entities
sdd doc search "validation" --docs-path ./docs/documentation.json

# Show high-complexity functions needing refactoring
sdd doc complexity --threshold 15 --docs-path ./docs/documentation.json

# Get context for printer-related code
sdd doc context "printer" --docs-path ./docs/documentation.json --limit 5

# Find a specific class
sdd doc find-class PrettyPrinter --docs-path ./docs/documentation.json

# List all classes in a module
sdd doc list-classes --module src/common --docs-path ./docs/documentation.json

# See module details
sdd doc describe-module src/common/printer.py --docs-path ./docs/documentation.json
```

**When to use query commands:**
- User wants to explore generated documentation
- Looking for specific classes, functions, or modules
- Analyzing code complexity or dependencies
- Understanding feature areas before making changes
- Quick lookups without reading full documentation

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

**IMPORTANT: Always report model errors to the user with specifics.**

1. **Check the tool output** - Look for ✓ (success) or ✗ (failure) symbols for each model
2. **Report which models failed and why** - Include the specific error (e.g., "model not available", "API error")
3. **Report which models succeeded** - Let user know if partial success occurred
4. **Explain the impact** - Was fallback successful? Which docs were/weren't generated?
5. **Provide next steps** - Suggest fixes or alternatives

**Actions to suggest:**
- Verify AI tool installation (`cursor-agent --version`, `gemini --version`, `codex --version`)
- Check API rate limits or authentication
- Try `--single-agent` with a working model instead of multi-agent
- Update model configuration if model name is invalid
- Fall back to structural docs only (`sdd doc generate`)

**Always be transparent about:**
- Which models were attempted
- Which succeeded/failed and why
- Whether documentation was still generated (with what limitations)
- How to fix the issue for future runs

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