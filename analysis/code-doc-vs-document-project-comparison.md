# Code-Doc vs Document-Project: Comparison and Contrast

## Executive Summary

Both systems generate codebase documentation for AI-assisted development, but they take fundamentally different approaches:

- **code-doc** (claude-sdd-toolkit): AST-based, language-aware parser that generates structured JSON + Markdown documentation with cross-references
- **document-project** (BMAD-METHOD): Workflow-driven, project-type-aware system that generates comprehensive brownfield documentation optimized for AI agent context

---

## Architecture Comparison

### code-doc Architecture

**Approach:** Language parser-based with AST analysis
- **Core Components:**
  - Language-specific parsers (Python, JavaScript, Go, HTML, CSS)
  - AST analysis for cross-references (function calls, class instantiations, imports)
  - Schema-based JSON output with versioning
  - Markdown formatter for human-readable output
  - AI consultation module for generating architecture docs

**Data Flow:**
```
Project Root → ParserFactory → Language Parsers → AST Analysis → 
Cross-Reference Graph → Schema Enhancement → JSON/Markdown Output
```

**Key Files:**
- `code_doc/parsers/` - Language-specific parsers
- `code_doc/ast_analysis.py` - Cross-reference tracking
- `code_doc/schema.py` - Structured data schema
- `code_doc/generator.py` - Orchestration
- `code_doc/formatter.py` - Output generation
- `code_doc/ai_consultation.py` - AI-assisted documentation

### document-project Architecture

**Approach:** Workflow-driven with project type detection
- **Core Components:**
  - Project type detection (12 types: web, mobile, backend, CLI, etc.)
  - CSV-driven documentation requirements (`documentation-requirements.csv`)
  - Multi-part project detection (client/server monorepos)
  - Scan level selection (Quick/Deep/Exhaustive)
  - Resumability with state tracking
  - Write-as-you-go pattern to prevent context exhaustion

**Data Flow:**
```
Project Root → Project Type Detection → Documentation Requirements CSV → 
Scan Level Selection → Targeted Scanning → Multi-file Documentation Output
```

**Key Files:**
- `workflow.yaml` - Workflow configuration
- `instructions.md` - Step-by-step workflow logic
- `documentation-requirements.csv` - Project type scanning patterns
- `workflows/full-scan-instructions.md` - Full scan implementation
- `workflows/deep-dive-instructions.md` - Deep-dive mode

---

## Feature Comparison

### 1. Project Type Awareness

**code-doc:**
- ❌ No explicit project type detection
- ✅ Language detection (Python, JavaScript, Go, etc.)
- ✅ Framework detection (FastAPI, Django, Flask, etc.)
- ✅ Generic approach works for any project structure

**document-project:**
- ✅ 12 project types with specific detection patterns
- ✅ Project type-specific scanning requirements
- ✅ Architecture template matching (170+ templates)
- ✅ Multi-part project detection (client/server separation)
- ✅ Conditional scanning based on project type (API scan, UI components, data models, etc.)

**Winner:** document-project for brownfield projects needing contextual understanding

---

### 2. Scanning Depth and Control

**code-doc:**
- ✅ Scans all files matching language parsers
- ✅ Configurable exclude patterns
- ✅ Language filtering support
- ❌ No scan depth levels
- ❌ No resumability

**document-project:**
- ✅ Three scan levels:
  - **Quick** (2-5 min): Pattern-based, no source file reading
  - **Deep** (10-30 min): Critical directories only
  - **Exhaustive** (30-120 min): All source files
- ✅ Resumability with state tracking (`project-scan-report.json`)
- ✅ Write-as-you-go pattern prevents context exhaustion
- ✅ Deep-dive mode for specific areas
- ✅ Batching strategy for large projects

**Winner:** document-project for large projects and context management

---

### 3. Output Format and Structure

**code-doc:**
- ✅ **JSON output:** Structured schema with versioning
  - Modules, classes, functions with metadata
  - Cross-references (callers, callees, instantiations)
  - Dependencies and imports
  - Complexity metrics
- ✅ **Markdown output:** Human-readable documentation
  - Statistics, language breakdown
  - Classes and functions with signatures
  - Dependencies list
- ✅ Single comprehensive file per format
- ✅ Machine-readable JSON enables doc-query integration

**document-project:**
- ✅ **Multi-file Markdown output:**
  - `index.md` - Master index (primary AI retrieval source)
  - `project-overview.md` - Executive summary
  - `architecture.md` - Detailed architecture
  - `source-tree-analysis.md` - Annotated directory tree
  - `component-inventory.md` - Component catalog
  - `development-guide.md` - Local dev instructions
  - `api-contracts.md` - API documentation (conditional)
  - `data-models.md` - Database schema (conditional)
  - `deep-dive-{area}.md` - Area-specific deep dives
- ✅ Multi-part projects get per-part documentation
- ✅ `project-parts.json` for machine-readable metadata
- ❌ No structured JSON schema (Markdown-focused)

**Winner:** Tie - code-doc for structured data, document-project for comprehensive narrative docs

---

### 4. Cross-Reference Analysis

**code-doc:**
- ✅ **Advanced AST-based cross-references:**
  - Function call tracking (who calls what)
  - Class instantiation tracking
  - Import dependency graph
  - Dynamic pattern detection (decorators, dynamic calls)
- ✅ `CrossReferenceGraph` data structure
- ✅ Schema enhancement with `CallReference`, `InstantiationReference`, `ImportReference`
- ✅ Enables "where is this used" queries

**document-project:**
- ❌ No explicit cross-reference tracking
- ✅ Dependency analysis through pattern matching
- ✅ Integration point identification
- ✅ Architecture-level relationships

**Winner:** code-doc for detailed code-level cross-references

---

### 5. AI Integration

**code-doc:**
- ✅ **AI consultation module** (`ai_consultation.py`):
  - Architecture documentation generation
  - AI context documentation
  - Developer guide generation
  - Multi-tool support (cursor-agent, gemini, codex)
  - Tool routing based on doc type
  - Consensus agent support
- ✅ AI-generated docs supplement structural analysis
- ✅ Configurable model selection per tool

**document-project:**
- ✅ Workflow designed for AI agent consumption
- ✅ `index.md` optimized for AI retrieval
- ✅ Context variables (`{document_project_content}`) for other workflows
- ❌ No explicit AI tool integration in workflow
- ✅ Designed to feed into PRD/architecture workflows

**Winner:** code-doc for explicit AI tool integration, document-project for workflow integration

---

### 6. Language Support

**code-doc:**
- ✅ **Explicit parser support:**
  - Python (full AST analysis)
  - JavaScript/TypeScript
  - Go
  - HTML
  - CSS
- ✅ Extensible parser factory pattern
- ✅ Language-specific parsing logic
- ✅ Multi-language projects supported

**document-project:**
- ✅ Language-agnostic approach
- ✅ Pattern-based detection (file extensions, config files)
- ✅ Works with any language through pattern matching
- ❌ No language-specific AST parsing

**Winner:** code-doc for deep language understanding, document-project for broad coverage

---

### 7. Integration with Development Workflows

**code-doc:**
- ✅ Integrated into SDD toolkit workflow
- ✅ Invoked via `sdd doc generate`
- ✅ Used by `doc-query` skill for context retrieval
- ✅ Suggested after spec completion
- ✅ Agent wrapper (`code-doc-subagent`) for Claude Desktop

**document-project:**
- ✅ **Deep workflow integration:**
  - Prerequisite for brownfield PRD creation
  - Used by multiple workflows (PRD, architecture, epics, stories)
  - Context variable system (`{document_project_content}`)
  - Workflow sequencing validation
  - Status tracking integration
- ✅ "When in doubt, run document-project" philosophy
- ✅ Mandatory for brownfield projects

**Winner:** document-project for comprehensive workflow integration

---

### 8. Context Management

**code-doc:**
- ❌ No explicit context management
- ✅ Processes entire codebase in memory
- ❌ No resumability
- ❌ No batching strategy

**document-project:**
- ✅ **Context-safe architecture:**
  - Write-as-you-go pattern
  - Documents written immediately to disk
  - Detailed findings purged after writing
  - State tracking for resumability
  - Batching strategy (one subfolder at a time)
  - Prevents context exhaustion on large projects

**Winner:** document-project for large codebase handling

---

### 9. Use Cases

**code-doc:**
- ✅ **Best for:**
  - Generating structured code documentation
  - Cross-reference analysis
  - Code understanding and navigation
  - Integration with doc-query for semantic search
  - Language-specific deep analysis
  - Machine-readable documentation (JSON)

**document-project:**
- ✅ **Best for:**
  - Brownfield project onboarding
  - AI agent context preparation
  - Comprehensive project documentation
  - Multi-part project analysis
  - Architecture documentation
  - PRD creation prerequisites
  - Large codebase analysis with context management

---

## Key Differences Summary

| Aspect | code-doc | document-project |
|--------|----------|------------------|
| **Primary Focus** | Code structure & cross-references | Project context & architecture |
| **Output Format** | JSON + Markdown (structured) | Multi-file Markdown (narrative) |
| **Project Awareness** | Language/framework detection | Project type detection (12 types) |
| **Scanning Control** | All files, configurable excludes | 3 scan levels (Quick/Deep/Exhaustive) |
| **Resumability** | ❌ No | ✅ Yes (state tracking) |
| **Context Management** | ❌ In-memory processing | ✅ Write-as-you-go, batching |
| **Cross-References** | ✅ AST-based detailed tracking | ❌ Pattern-based only |
| **AI Integration** | ✅ Explicit AI tool calls | ✅ Workflow integration |
| **Multi-part Projects** | ❌ No | ✅ Yes (client/server) |
| **Workflow Integration** | ✅ SDD toolkit integration | ✅ Deep BMAD workflow integration |
| **Language Support** | ✅ Deep parsers (5 languages) | ✅ Pattern-based (any language) |
| **Use Case** | Code documentation & analysis | Brownfield project documentation |

---

## Complementary Strengths

These systems are **complementary** rather than competing:

1. **code-doc** excels at:
   - Detailed code-level analysis
   - Cross-reference tracking
   - Structured data generation
   - Language-specific parsing

2. **document-project** excels at:
   - High-level project understanding
   - Context management for large projects
   - Workflow integration
   - Brownfield project documentation

## Potential Integration Opportunities

1. **Use code-doc's AST analysis** within document-project's deep-dive mode for detailed code analysis
2. **Use document-project's project type detection** to inform code-doc's scanning strategy
3. **Combine outputs:** Use code-doc's JSON for machine queries, document-project's Markdown for AI context
4. **Cross-reference enhancement:** Add code-doc's cross-reference data to document-project's architecture docs

---

## Recommendations

### When to Use code-doc:
- Need structured JSON documentation for programmatic access
- Want detailed cross-reference analysis
- Working with specific languages (Python, JavaScript, Go)
- Need integration with doc-query for semantic search
- Generating developer-focused code documentation

### When to Use document-project:
- Brownfield project analysis
- Need comprehensive project context for AI agents
- Large codebases requiring context management
- Multi-part projects (client/server)
- Preparing context for PRD/architecture workflows
- Need resumable documentation generation

### When to Use Both:
- Comprehensive documentation strategy:
  - document-project for high-level context
  - code-doc for detailed code analysis
  - Both outputs feed into different workflows

---

## Conclusion

**code-doc** is a **code-focused documentation tool** that excels at structural analysis and cross-references, while **document-project** is a **project-focused documentation workflow** optimized for AI agent context and brownfield project understanding.

The choice depends on:
- **Scope:** Code-level detail (code-doc) vs. project-level context (document-project)
- **Output needs:** Structured JSON (code-doc) vs. narrative Markdown (document-project)
- **Project size:** Small-medium (code-doc) vs. large with context management (document-project)
- **Workflow:** SDD toolkit (code-doc) vs. BMAD method (document-project)

Both systems serve important roles in AI-assisted development workflows, and their strengths complement each other well.
