---
name: llm-doc-gen
description: LLM-powered documentation generation for narrative architecture docs, tutorials, and developer guides. Uses AI consultation to create contextual, human-readable documentation from code analysis and spec data.
---

# LLM-Based Documentation Generation Skill

## Overview

This skill generates comprehensive, navigable documentation using Large Language Model (LLM) consultation. It creates sharded documentation (organized topic files) by having LLMs read and analyze source code directly, then synthesizing their insights into structured, human-readable guides.

**Core Capability:** Transform codebases into sharded documentation by orchestrating LLM analysis through workflow-driven steps, managing state for resumability, and producing organized topic files instead of monolithic documents.

**Use this skill when:**
- Creating architecture documentation that explains *why*, not just *what*
- Generating developer onboarding guides with contextual explanations
- Writing tutorials that synthesize multiple code concepts
- Producing design documentation from implementation details
- Creating narrative content that requires interpretation and synthesis

**Key features:**
- **Sharded documentation** - Organized topic files (architecture/, guides/, reference/) instead of monolithic docs
- **State-based resumability** - Resume interrupted scans from last checkpoint
- **Multi-agent consultation** - Parallel LLM queries for comprehensive insights
- **Workflow orchestration** - Step-by-step analysis guided by workflow engine
- **Direct source reading** - LLMs read code directly (no AST parsing required)
- **Research-then-synthesis** - LLMs provide research, main agent composes organized docs

**Do NOT use for:**
- Quick prototyping or throwaway code
- Projects under 100 lines
- Code that changes daily (docs become stale quickly)
- When simple README.md is sufficient

## ⚠️ Long-Running Operations

**This skill may run operations that take up to 5 minutes. Be patient and wait for completion.**

### CRITICAL: Avoid BashOutput Spam
- **ALWAYS use foreground execution with 5-minute timeout:** `Bash(command="...", timeout=300000)`
- **WAIT for the command to complete** - this may take the full 5 minutes
- **NEVER use `run_in_background=True` for test suites, builds, or analysis**
- If you must use background (rare), **wait at least 60 seconds** between BashOutput checks
- **Maximum 3 BashOutput calls per background process** - then kill it or let it finish

### Why?
Polling BashOutput repeatedly creates spam and degrades user experience. Long operations should run in foreground with appropriate timeout, not in background with frequent polling.

### Example (CORRECT):
```
# Test suite that might take 5 minutes (timeout in milliseconds)
result = Bash(command="pytest src/", timeout=300000)  # Wait up to 5 minutes
# The command will block here until completion - this is correct behavior
```

### Example (WRONG):
```
# Don't use background + polling
bash_id = Bash(command="pytest", run_in_background=True)
output = BashOutput(bash_id)  # Creates spam!
```

---

## Sharded Documentation Output

Unlike monolithic documentation files, llm-doc-gen produces organized, navigable documentation sharded by topic:

**Example Output Structure:**
```
docs/
├── index.md                    # Main navigation and project overview
├── architecture/
│   ├── overview.md             # System architecture and design
│   ├── components.md           # Component descriptions
│   └── data-flow.md            # Data flow and interactions
├── guides/
│   ├── getting-started.md      # Developer onboarding
│   ├── development.md          # Development workflows
│   └── deployment.md           # Deployment procedures
└── reference/
    ├── api.md                  # API reference
    ├── configuration.md        # Configuration options
    └── troubleshooting.md      # Common issues and solutions
```

**Benefits:**
- **Navigable** - Find specific topics easily
- **Maintainable** - Update individual sections without touching others
- **Scalable** - Grows organically with project complexity
- **Readable** - Focused docs instead of overwhelming single file

**State File for Resumability:**

The skill maintains a `project-doc-state.json` file to enable resuming interrupted scans:

```json
{
  "version": "1.0",
  "project_name": "MyProject",
  "last_updated": "2025-11-19T20:00:00Z",
  "current_step": "generate-guides",
  "completed_steps": ["scan-structure", "analyze-architecture", "generate-architecture-docs"],
  "files_analyzed": ["src/main.py", "src/auth.py", "src/db.py"],
  "sections_generated": [
    "docs/index.md",
    "docs/architecture/overview.md",
    "docs/architecture/components.md"
  ],
  "workflow_mode": "full_scan"
}
```

If the scan is interrupted, simply run `sdd llm-doc-gen resume ./docs` to continue from the last checkpoint.

---

## Core Workflow

### Workflow-Driven Documentation Generation

The llm-doc-gen skill uses a workflow engine that orchestrates LLM analysis through systematic steps:

```
┌─────────────────────────────────────────┐
│ Step 1: Initialize                      │
│ ─────────────────────────────────────── │
│                                         │
│  • Scan project structure               │
│  • Create state file (project-doc-state.json) │
│  • Detect project type                  │
│  • Plan documentation sections          │
│  • Check for existing docs/resume       │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Step 2: Analyze Architecture            │
│ ─────────────────────────────────────── │
│                                         │
│  • LLMs read source files directly      │
│  • Identify components and patterns     │
│  • Analyze data flow and interactions   │
│  • Multi-agent consultation (parallel)  │
│  • Update state: architecture analyzed  │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Step 3: Generate Architecture Docs      │
│ ─────────────────────────────────────── │
│                                         │
│  • Synthesize LLM research findings     │
│  • Create docs/architecture/overview.md │
│  • Create docs/architecture/components.md │
│  • Create docs/architecture/data-flow.md │
│  • Update state: architecture docs done │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Step 4: Generate Guides                 │
│ ─────────────────────────────────────── │
│                                         │
│  • Analyze developer workflows          │
│  • Create docs/guides/getting-started.md │
│  • Create docs/guides/development.md    │
│  • Create docs/guides/deployment.md     │
│  • Update state: guides done            │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Step 5: Generate Reference              │
│ ─────────────────────────────────────── │
│                                         │
│  • Extract API patterns                 │
│  • Create docs/reference/api.md         │
│  • Create docs/reference/configuration.md │
│  • Create docs/reference/troubleshooting.md │
│  • Update state: reference done         │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Step 6: Finalize                        │
│ ─────────────────────────────────────── │
│                                         │
│  • Generate docs/index.md with navigation │
│  • Validate all sections created        │
│  • Update state: complete                │
│  • Archive state file                   │
└─────────────────────────────────────────┘
```

**Resumability:**

If interrupted at any step, the workflow can resume from the last completed step using the state file:

```bash
# Workflow interrupted after Step 3
sdd llm-doc-gen resume ./docs
# Resumes from Step 4: Generate Guides
```

**Key Workflow Principles:**

1. **Stateful Execution**
   - Each step updates project-doc-state.json
   - Resume from any checkpoint
   - No duplicate work

2. **LLMs Read Code Directly**
   - No AST parsing or pre-processing
   - LLMs analyze source files natively
   - Simpler, more maintainable

3. **Sharded Output**
   - Each step produces focused docs
   - Organized by topic (architecture/, guides/, reference/)
   - Easy to navigate and maintain

4. **Multi-Agent Research**
   - Parallel LLM consultation at each step
   - Synthesis of multiple perspectives
   - Richer, more comprehensive insights

---

## Codebase Analysis Integration

**NEW:** llm-doc-gen now integrates with codebase analysis insights to enhance documentation quality with factual, data-driven context.

### What It Does

The analysis integration automatically extracts and formats metrics from `documentation.json` (generated by `sdd doc generate`) and includes them in LLM prompts. This provides:

- **Factual Grounding**: Real metrics from codebase analysis (call counts, complexity, dependencies)
- **Better Accuracy**: AI identifies architectural patterns based on actual code structure
- **Specific Insights**: Quantifiable metrics instead of generic observations
- **Reduced Hallucinations**: Data-driven context reduces AI speculation

### Key Features

**Automatic Integration:**
- Detects `documentation.json` in project root
- Extracts high-value metrics (most-called functions, entry points, complexity)
- Formats insights within token budgets (250-450 tokens depending on generator)
- Gracefully degrades if analysis data unavailable

**Performance:**
- <2s overhead for insight extraction (with caching)
- 50-1000x speedup on repeated extractions (warm cache)
- Adaptive scaling based on codebase size

**Quality Validation:**
- A/B testing framework to measure documentation improvements
- Typical improvement: 50-100% better accuracy and completeness
- Comprehensive evaluation rubrics across 10+ metrics

### Quick Example

```bash
# Generate analysis data first
sdd doc generate --output documentation.json

# Generate documentation (automatically uses analysis insights)
sdd llm-doc-gen scan ./src --project-name MyProject --output-dir ./docs

# Documentation now includes factual metrics like:
# - "process_request() called 127 times (most critical function)"
# - "5 entry points identified: main(), handle_api_request(), ..."
# - "Core module dependencies: api → core (23 refs), core → utils (18 refs)"
```

### When Analysis Insights Are Used

Analysis integration is **automatic** but **optional**:

1. **With insights** (if `documentation.json` exists):
   - Extracts Priority 1 metrics: Most-called functions, entry points, cross-module deps
   - Extracts Priority 2 metrics: Most-instantiated classes, high-complexity functions
   - Formats for token budget and includes in prompts
   - Result: More accurate, specific, factually-grounded documentation

2. **Without insights** (if `documentation.json` missing):
   - Generates documentation using AI reasoning alone
   - Still produces quality documentation
   - May be more generic and less specific to codebase

### Documentation

For detailed information about analysis integration:

- **Integration Guide**: `docs/llm-doc-gen/ANALYSIS_INTEGRATION.md` - How it works, architecture, caching
- **Best Practices**: `docs/llm-doc-gen/BEST_PRACTICES.md` - Guidelines for effective use
- **A/B Testing**: `src/claude_skills/claude_skills/llm_doc_gen/AB_TESTING_README.md` - Measuring impact

### Performance Characteristics

| Codebase Size | Cold Cache | Warm Cache | Typical Overhead |
| --- | --- | --- | --- |
| Small (<100 files) | 0.3-0.5s | 0.001s | <0.6s |
| Medium (100-500) | 0.8-1.2s | 0.001s | <1.3s |
| Large (>500) | 1.5-2.0s | 0.001s | <2.1s |

**Note:** Overhead is only incurred once per documentation generation session due to aggressive caching.

---

## Tool Verification

**Before using this skill**, verify that LLM tools are available:

```bash
# Check which tools are available for llm-doc-gen
sdd test check-tools --skill llm-doc-gen

# For JSON output
sdd test check-tools --skill llm-doc-gen --json
```

**Expected:** At least one LLM tool should be detected as available.

**IMPORTANT - How This Skill Works:**
- ✅ **Skill invokes LLM tools** - Uses `execute_tool_with_fallback()` and `execute_tools_parallel()`
- ✅ **Provider abstraction** - Shared `claude_skills.common.ai_tools` infrastructure
- ✅ **Multi-agent support** - Parallel consultation of 2+ LLMs for comprehensive insights
- ❌ **No direct LLM calls** - Does not invoke OpenAI/Anthropic APIs directly

The skill shells out to installed CLI tools (cursor-agent, gemini, codex) which handle the actual LLM API communication.

If no LLM tools are installed, this skill cannot function. Install at least one of the supported tools before using llm-doc-gen.

---

## Quick Start

### Basic Usage

```bash
# Generate complete sharded documentation
sdd llm-doc-gen scan ./src --project-name MyProject --output-dir ./docs

# Resume interrupted scan
sdd llm-doc-gen resume ./docs

# Generate specific section only
sdd llm-doc-gen section architecture --source ./src --output ./docs/architecture/

# Single-agent mode (faster, less comprehensive)
sdd llm-doc-gen scan ./src --single-agent --tool cursor-agent
```

### Output

After running `sdd llm-doc-gen scan`, you'll get organized documentation:

```
docs/
├── index.md                    # Navigation and overview
├── architecture/               # System design docs
│   ├── overview.md
│   ├── components.md
│   └── data-flow.md
├── guides/                     # Developer guides
│   ├── getting-started.md
│   ├── development.md
│   └── deployment.md
└── reference/                  # Reference docs
    ├── api.md
    ├── configuration.md
    └── troubleshooting.md
```

---

## When to Use This Skill

### ✅ Use `Skill(sdd-toolkit:llm-doc-gen)` when:

1. **Architecture Documentation**
   - Explaining system design and component relationships
   - Documenting architectural decisions and trade-offs
   - Creating high-level overviews for stakeholders

2. **Developer Onboarding**
   - Writing guides that explain "how things work here"
   - Creating contextual documentation for new team members
   - Synthesizing knowledge across multiple modules

3. **Tutorial Creation**
   - Generating step-by-step guides from code examples
   - Explaining complex features with narrative flow
   - Creating learning materials from implementation

4. **Design Documentation**
   - Documenting design patterns and their rationale
   - Explaining implementation choices
   - Creating architecture decision records (ADRs)

5. **Specification-Based Docs**
   - Generating implementation guides from SDD specs
   - Creating post-implementation documentation
   - Synthesizing spec intent with actual code

### ❌ Don't use `Skill(sdd-toolkit:llm-doc-gen)` when:

1. **You need structural accuracy**
   - Use `sdd doc generate` for programmatic extraction
   - LLMs may miss edge cases or hallucinate details
   - Structural docs require 100% accuracy

2. **Simple API documentation**
   - `sdd doc generate` handles function signatures better
   - No need for narrative in pure API reference
   - Programmatic extraction is faster and more accurate

3. **Quick prototyping or spikes**
   - LLM consultation adds overhead (30-60s per doc)
   - Not worth it for throwaway code
   - Save for production documentation

4. **Documentation already exists**
   - Don't regenerate if existing docs are current
   - LLM costs add up quickly
   - Update manually for small changes

---

## Critical Rules

### MUST DO:

1. **Always use the workflow engine**
   - Don't skip initialization step
   - Let the workflow manage state and checkpoints
   - Enable resumability by maintaining state file

2. **Use multi-agent by default**
   - Parallel consultation provides richer insights
   - Synthesis of multiple perspectives improves quality
   - Only use single-agent for quick iterations or cost constraints

3. **Let LLMs read code directly**
   - Provide source file paths to LLMs
   - No pre-processing or parsing required
   - Trust LLMs to understand code structure

4. **Maintain state file integrity**
   - Don't manually edit project-doc-state.json
   - Use `sdd llm-doc-gen resume` to continue interrupted scans
   - State file enables checkpointing and progress tracking

5. **Report LLM failures transparently**
   - If an LLM tool fails, inform the user
   - Explain which models succeeded/failed
   - Provide fallback options

### MUST NOT DO:

1. **Never let LLMs write files directly**
   - Always use research-then-synthesis pattern
   - Workflow engine controls all file operations
   - LLMs return analysis text only

2. **Never skip the initialization step**
   - State file setup is critical for resumability
   - Project structure scan informs documentation organization
   - Skipping initialization breaks checkpoint recovery

3. **Never mix monolithic and sharded output**
   - Stick to sharded documentation structure
   - Don't create single DOCUMENTATION.md files
   - Organized topics are more maintainable

4. **Never ignore timeout/failure**
   - LLM calls can hang or fail
   - Always implement timeout handling
   - Provide graceful fallback to single-agent or manual

5. **Never batch without state tracking**
   - LLM consultation is expensive (time and API cost)
   - State file tracks progress through sections
   - Always show progress during generation

---

## Detailed Workflow Steps

### Step-by-Step Execution

When you run `sdd llm-doc-gen scan ./src --project-name MyProject`, the workflow engine executes these steps:

#### Step 1: Initialize (5-10 seconds)

**Actions:**
- Scan project directory structure
- Detect project type (web app, library, CLI tool, etc.)
- Create `docs/project-doc-state.json` file
- Plan documentation sections based on project type
- Check for existing documentation to resume

**Output:**
```
🔍 Scanning project structure...
✅ Detected: Python web application (Flask)
📋 Planned sections: architecture, guides, reference
💾 State file created: docs/project-doc-state.json
```

**Resume Check:**
If state file exists, you'll be prompted:
```
Found existing documentation state (last updated 2 hours ago).

Resume from where you left off? [Y/n]
```

---

#### Step 2: Analyze Architecture (30-60 seconds)

**Actions:**
- LLMs read main source files (entry points, core modules)
- Identify system components and their relationships
- Analyze data flow and interaction patterns
- Multi-agent consultation (2+ LLMs in parallel)
- Synthesize findings from multiple perspectives

**Expected Output:**
```
🤖 Consulting 2 AI models for architecture analysis...
   Tools: cursor-agent, gemini

✅ cursor-agent completed (28.3s)
✅ gemini completed (24.1s)

📊 Analysis complete:
   - 5 core components identified
   - 3 data flow patterns documented
   - 12 source files analyzed
```

**State Update:**
`current_step: "generate-architecture-docs"`, `completed_steps: ["initialize", "analyze-architecture"]`

---

#### Step 3: Generate Architecture Docs (20-40 seconds)

**Actions:**
- Synthesize LLM research findings
- Create `docs/architecture/overview.md`
- Create `docs/architecture/components.md`
- Create `docs/architecture/data-flow.md`
- Update state file

**Expected Output:**
```
📝 Generating architecture documentation...

✅ Created: docs/architecture/overview.md (2.1 KB)
✅ Created: docs/architecture/components.md (3.4 KB)
✅ Created: docs/architecture/data-flow.md (1.8 KB)

💾 State updated: 3 architecture docs complete
```

---

#### Step 4: Generate Guides (40-80 seconds)

**Actions:**
- Analyze developer workflows and setup procedures
- Create `docs/guides/getting-started.md`
- Create `docs/guides/development.md`
- Create `docs/guides/deployment.md`
- Update state file

**Expected Output:**
```
📝 Generating developer guides...

🤖 Analyzing: Setup procedures, development workflows, deployment...

✅ Created: docs/guides/getting-started.md (4.2 KB)
✅ Created: docs/guides/development.md (3.1 KB)
✅ Created: docs/guides/deployment.md (2.5 KB)

💾 State updated: 3 guide docs complete
```

---

#### Step 5: Generate Reference (30-50 seconds)

**Actions:**
- Extract API patterns and endpoints
- Document configuration options
- Identify common issues and solutions
- Create reference documentation
- Update state file

**Expected Output:**
```
📝 Generating reference documentation...

✅ Created: docs/reference/api.md (5.3 KB)
✅ Created: docs/reference/configuration.md (2.8 KB)
✅ Created: docs/reference/troubleshooting.md (1.9 KB)

💾 State updated: 3 reference docs complete
```

---

#### Step 6: Finalize (10-15 seconds)

**Actions:**
- Generate `docs/index.md` with navigation
- Validate all sections created
- Mark state as complete
- Archive state file

**Expected Output:**
```
✨ Finalizing documentation...

✅ Created: docs/index.md (navigation index)
✅ Validated: All 9 documentation files present

📊 Documentation Complete:
   Total sections: 9 files
   Total size: 27.1 KB
   Time elapsed: 2m 45s

📁 Output directory: ./docs
```

---

### Resumability

If the workflow is interrupted at any step, the state file preserves progress:

```json
{
  "current_step": "generate-guides",
  "completed_steps": ["initialize", "analyze-architecture", "generate-architecture-docs"],
  "sections_generated": [
    "docs/architecture/overview.md",
    "docs/architecture/components.md",
    "docs/architecture/data-flow.md"
  ]
}
```

**To resume:**
```bash
sdd llm-doc-gen resume ./docs
```

**Resume output:**
```
🔄 Resuming documentation generation...
✅ Found state file (last updated 1 hour ago)
📋 Progress: 3/9 sections complete (33%)
▶️  Resuming from: Step 4 (Generate Guides)
```

The workflow continues from Step 4, skipping already-completed sections.

---

### User Interaction Points

The workflow prompts for user input at key decision points:

**1. Resume Check** (if state file exists)
```
Found existing documentation state.

Resume from where you left off? [Y/n]
```

**2. Project Type Confirmation** (if auto-detection uncertain)
```
Detected project type: Web Application

Is this correct? [Y/n]
> If no: What type of project is this? [library/cli/api/other]
```

**3. Section Selection** (optional)
```
Generate all sections or specific sections only?

1. All sections (recommended)
2. Architecture only
3. Guides only
4. Reference only
5. Custom selection

Choice [1]:
```

**4. LLM Tool Failure**
```
⚠️  Warning: cursor-agent failed (timeout)

Continue with remaining tools? [Y/n]
Available: gemini
```

---

## Next Steps

This skill is currently under development. The sections above define the core purpose and workflow. Implementation details, CLI commands, and examples will be added in subsequent phases.

**Current Status:** Phase 1 - Documentation & Planning (IN PROGRESS)

**Remaining Work:**
- CLI command structure definition
- Prompt template development
- Synthesis logic implementation
- Integration with code-doc and SDD
- Comprehensive examples and use cases
