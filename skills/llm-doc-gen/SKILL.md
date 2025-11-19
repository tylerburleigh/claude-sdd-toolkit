---
name: llm-doc-gen
description: LLM-powered documentation generation for narrative architecture docs, tutorials, and developer guides. Uses AI consultation to create contextual, human-readable documentation from code analysis and spec data.
---

# LLM-Based Documentation Generation Skill

## Overview

The `Skill(sdd-toolkit:llm-doc-gen)` skill generates narrative, contextual documentation using Large Language Model (LLM) consultation. Unlike programmatic documentation generators that extract structural information from code, this skill uses AI to create human-readable explanations, architectural insights, and developer-friendly guides.

**Core Capability:** Transform code structure and context into narrative documentation by consulting one or more LLMs in parallel, synthesizing their responses, and composing publication-ready documents.

**Use this skill when:**
- Creating architecture documentation that explains *why*, not just *what*
- Generating developer onboarding guides with contextual explanations
- Writing tutorials that synthesize multiple code concepts
- Producing design documentation from implementation details
- Creating narrative content that requires interpretation and synthesis

**Key features:**
- **Multi-agent consultation** - Parallel LLM queries for comprehensive insights
- **Context-aware prompting** - Uses code-doc output + spec data + source code
- **Research-then-synthesis** - LLMs provide research, main agent composes docs
- **Multiple output formats** - Architecture docs, tutorials, developer guides
- **Integration with SDD** - Generate docs from specs and task contexts

**Do NOT use for:**
- API reference documentation (use `Skill(sdd-toolkit:code-doc)` instead)
- Function/class catalogs (use code-doc for structural docs)
- Dependency graphs or metrics (use code-doc for programmatic analysis)
- Simple docstring extraction (code-doc handles this)

---

## LLM vs Programmatic Documentation

Understanding when to use LLM-based vs programmatic documentation generation is critical:

### When to Use LLM Documentation (llm-doc-gen)

**✅ Use llm-doc-gen when you need:**

1. **Narrative Explanations**
   - "Why does this architecture use microservices?"
   - "What problem does this design pattern solve here?"
   - Contextual interpretation, not just structure extraction

2. **Synthesis Across Sources**
   - Combining insights from code + specs + comments + tests
   - Identifying patterns and relationships
   - Creating coherent narratives from disparate information

3. **Human-Readable Guides**
   - Onboarding documentation for new developers
   - Architecture decision records with rationale
   - Tutorial content with explanations and examples

4. **Contextual Understanding**
   - Domain-specific terminology explained
   - Design trade-offs articulated
   - Implementation choices justified

### When to Use Programmatic Documentation (code-doc)

**✅ Use code-doc when you need:**

1. **Structural Information**
   - Complete list of all functions and classes
   - Accurate parameter types and return values
   - Inheritance hierarchies and class relationships

2. **Metrics and Analysis**
   - Cyclomatic complexity scores
   - Dependency graphs
   - Code coverage statistics

3. **API Reference**
   - Machine-readable function signatures
   - Exhaustive method documentation
   - Interface definitions

4. **Guaranteed Accuracy**
   - Programmatic extraction eliminates hallucination
   - AST parsing provides ground truth
   - No interpretation, just facts

### Best Practice: Combine Both

The most powerful documentation strategy uses both approaches:

```bash
# Step 1: Generate structural documentation with code-doc
sdd doc generate ./src --name MyProject --output-dir ./docs

# Step 2: Use that structural data as input for LLM narrative
sdd llm-doc architecture ./src \
    --use-code-doc ./docs/documentation.json \
    --output ./docs/ARCHITECTURE.md
```

**Why this works:**
- code-doc provides accurate structural data (functions, classes, dependencies)
- llm-doc-gen reads that data + source code to create narrative
- LLM has factual grounding from code-doc, reducing hallucination
- Result: Accurate structure + insightful narrative

---

## Core Workflow

### Research-Then-Synthesis Pattern

The llm-doc-gen skill uses a two-phase approach that separates AI research from document composition:

```
┌─────────────────────────────────────────┐
│ Phase 1: Research Gathering             │
│ ─────────────────────────────────────── │
│                                         │
│  1. Gather Context                      │
│     ├─ Code-doc structural data         │
│     ├─ SDD spec context (if available)  │
│     ├─ Source code files                │
│     └─ Existing documentation           │
│                                         │
│  2. Format LLM Prompts                  │
│     ├─ Include gathered context         │
│     ├─ Specify output requirements      │
│     └─ Add constraints and examples     │
│                                         │
│  3. Execute LLM Consultation            │
│     ├─ Multi-agent (parallel, default)  │
│     │  • cursor-agent                   │
│     │  • gemini                         │
│     │  • codex (if available)           │
│     └─ Single-agent (faster, optional)  │
│                                         │
│  4. Return Research Findings            │
│     └─ Separate responses per LLM       │
└─────────────────────────────────────────┘
                 │
                 │ Research findings (text)
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Phase 2: Synthesis & Composition        │
│ ─────────────────────────────────────── │
│                                         │
│  5. Synthesize Responses                │
│     ├─ Merge complementary insights     │
│     ├─ Resolve contradictions           │
│     ├─ Remove redundancy                │
│     └─ Identify consensus points        │
│                                         │
│  6. Compose Final Document              │
│     ├─ Apply document template          │
│     ├─ Format sections                  │
│     ├─ Add metadata                     │
│     └─ Validate output                  │
│                                         │
│  7. Write Output File                   │
│     └─ Save to specified location       │
└─────────────────────────────────────────┘
```

**Why This Pattern:**

1. **Separation of Concerns**
   - LLMs focus on analysis and research
   - Main agent controls file writing and composition
   - Clean boundary between AI analysis and output generation

2. **Safety**
   - LLMs never write files directly
   - Main agent validates and controls all file operations
   - No risk of AI accidentally modifying code

3. **Multi-Perspective Synthesis**
   - Consult multiple LLMs in parallel for diverse insights
   - Main agent intelligently merges perspectives
   - Richer, more comprehensive documentation

4. **Consistency**
   - Main agent ensures consistent formatting
   - Template-based output structure
   - Predictable document organization

---

## Tool Verification

**Before using this skill**, verify that LLM tools are available:

```bash
# Check for cursor-agent
cursor-agent --version

# Check for gemini
gemini --version

# Check for codex
codex --version
```

**Expected:** At least one LLM tool should respond with version information.

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
# Generate architecture documentation (multi-agent default)
sdd llm-doc architecture ./src --output ./docs/ARCHITECTURE.md

# Generate developer guide
sdd llm-doc guide ./src/auth --output ./docs/auth-guide.md

# Generate tutorial from feature implementation
sdd llm-doc tutorial ./src/scoring --output ./docs/scoring-tutorial.md
```

### With Code-Doc Integration

```bash
# Step 1: Generate structural docs first
sdd doc generate ./src --name MyProject

# Step 2: Generate narrative docs using structural data
sdd llm-doc architecture ./src \
    --use-code-doc ./docs/documentation.json \
    --output ./docs/ARCHITECTURE.md
```

### From SDD Spec

```bash
# Generate implementation guide from completed spec
sdd llm-doc from-spec my-spec-001 \
    --output ./docs/implementation-guide.md
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
   - Use `Skill(sdd-toolkit:code-doc)` for programmatic extraction
   - LLMs may miss edge cases or hallucinate details
   - Structural docs require 100% accuracy

2. **Simple API documentation**
   - code-doc handles function signatures better
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

1. **Always gather context first**
   - Run code-doc if structural data is needed
   - Read relevant spec files with `sdd` commands
   - Identify key source files to include

2. **Use multi-agent by default**
   - Parallel consultation provides richer insights
   - Synthesis of multiple perspectives improves quality
   - Only use single-agent for quick iterations

3. **Validate LLM outputs**
   - Check for hallucinated function names or features
   - Cross-reference with code-doc structural data
   - Don't blindly trust LLM responses

4. **Specify output format clearly**
   - Define document structure in prompt
   - Provide examples of desired format
   - Set length and tone constraints

5. **Report LLM failures transparently**
   - If an LLM tool fails, inform the user
   - Explain which models succeeded/failed
   - Provide fallback options

### MUST NOT DO:

1. **Never let LLMs write files directly**
   - Always use research-then-synthesis pattern
   - Main agent controls all file operations
   - LLMs return text only, never write

2. **Never skip context gathering**
   - LLMs need grounding in actual code structure
   - Without context, outputs are generic and unhelpful
   - Always provide code-doc data when available

3. **Never use for mission-critical accuracy**
   - LLMs can hallucinate details
   - Use code-doc for anything requiring 100% accuracy
   - Reserve llm-doc-gen for narrative and explanation

4. **Never ignore timeout/failure**
   - LLM calls can hang or fail
   - Always implement timeout handling
   - Provide graceful fallback to single-agent or manual

5. **Never batch without user awareness**
   - LLM consultation is expensive (time and API cost)
   - Always confirm before generating multiple docs
   - Show progress during multi-doc generation

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

---

*This skill documentation follows the standard pattern established by code-doc and doc-query skills.*
