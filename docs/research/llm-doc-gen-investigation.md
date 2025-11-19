# LLM-Based Documentation Generation - Investigation Findings

**Date:** 2025-11-19
**Spec:** llm-doc-gen-2025-11-19-001
**Phase:** Investigation & Planning (Completed)

---

## Executive Summary

This document captures research findings from investigating existing skill patterns and AI provider integration approaches. These findings will guide the implementation of the `llm-doc-gen` skill for LLM-based documentation generation.

---

## Task 1-1: Skill Structure Patterns Analysis

### Analyzed Skills

- `skills/code-doc/SKILL.md` (1,081 lines)
- `skills/doc-query/SKILL.md` (1,106 lines)
- `skills/sdd-plan/SKILL.md` (200+ lines sampled)

### Common Structure Pattern

All skills follow a consistent documentation structure:

#### 1. YAML Frontmatter
```yaml
---
name: skill-name
description: One-line description for skill listing
---
```

#### 2. Core Sections (in order)

1. **Overview** - Brief explanation of skill purpose
2. **When to Use This Skill** - ✅ Use cases and ❌ Anti-patterns
3. **Tool Verification** - How to check CLI availability
4. **Quick Start** - Common workflows with bash examples
5. **Detailed Documentation** - Organized by use case/workflow
6. **Best Practices & Critical Rules** - MUST DO / MUST NOT DO sections
7. **Troubleshooting** - Common issues and solutions

### Documentation Approach

**Code Examples:**
- Heavy use of bash code blocks with proper quoting
- Show actual commands, not pseudo-code
- Include expected output examples

**Structure:**
- Clear markdown header hierarchy (##, ###, ####)
- Tables for reference material (commands, options, workflows)
- Decision trees for choosing workflows
- Explicit warnings with ⚠️ or **CRITICAL** callouts

**Emphasis:**
- CLI commands over direct script execution
- "Always use `sdd doc` not `python doc.py`"
- Tool verification before usage
- Anti-patterns to prevent misuse

### Key Patterns for LLM-Doc

Based on analysis, the llm-doc-gen skill should:

1. **Follow established structure** - Users expect consistency
2. **Provide multi-tiered workflows** - Automated + manual patterns
3. **Explicit anti-patterns** - When NOT to use LLM generation
4. **Integration examples** - Show how to use with sdd CLI
5. **Decision guides** - Help users choose LLM vs programmatic approach

---

## Task 1-2: AI Provider Integration Patterns Analysis

### Analyzed Files

- `src/claude_skills/claude_skills/code_doc/ai_consultation.py` (810 lines)
- BMAD `workflow.yaml`, `agent.yaml`, `activation.xml`, `instructions.md`

### Code-Doc AI Provider Pattern

#### Provider Abstraction Layer

**Location:** `claude_skills.common.ai_tools`

**Key Functions:**
```python
# Tool detection
get_enabled_and_available_tools(skill_name: str) -> List[str]

# Single-tool execution with fallback
execute_tool_with_fallback(
    skill_name: str,
    tool: str,
    prompt: str,
    model: Optional[str],
    timeout: int,
    context: Optional[Dict],
    tracker: Optional[ConsultationTracker]
) -> ToolResponse

# Parallel multi-tool execution
execute_tools_parallel(
    tools: Sequence[str],
    prompt: str,
    models: Dict[str, Optional[str]]
) -> MultiToolResponse
```

**Response Envelope:**
```python
class ToolResponse:
    success: bool
    output: str
    status: ToolStatus  # SUCCESS, TIMEOUT, NOT_FOUND, FAILED
    tool: str
    duration: float
    error: Optional[str]
```

#### Model Resolution

**Location:** `claude_skills.common.ai_config`

```python
# Resolve model for specific tool
resolve_tool_model(
    skill_name: str,
    tool: str,
    override: Any = None,
    context: Optional[Dict] = None
) -> Optional[str]

# Resolve models for multiple tools
resolve_models_for_tools(
    skill_name: str,
    tools: Sequence[str],
    override: Any = None,
    context: Optional[Dict] = None
) -> List[Tuple[str, Optional[str]]]
```

**Context-based routing:**
```python
DOC_TYPE_ROUTING = {
    "architecture": ("cursor-agent", "gemini"),
    "ai_context": ("gemini", "cursor-agent"),
    "developer_guide": ("codex", "gemini"),
}
```

#### Multi-Agent Consultation

**Function:** `consult_multi_agent()`

**Features:**
- Parallel execution of 2+ AI tools
- Configurable agent selection via config
- Automatic fallback to available tools
- Returns `responses_by_tool` dict for synthesis

**Pattern:**
1. Detect available tools
2. Select agents (configured or auto)
3. Resolve models per agent
4. Execute in parallel
5. Return separate responses (no synthesis in skill)

### Content Generation Strategy

**Research-Then-Synthesis Pattern:**

```
┌─────────────────┐
│ LLM Tools       │
│ (Read-Only)     │
│                 │
│ • Analyze code  │
│ • Provide       │
│   research      │
│   findings      │
│ • Return text   │
│   output        │
└────────┬────────┘
         │
         │ Research findings (text)
         │
         ▼
┌─────────────────┐
│ Main Agent      │
│ (Orchestrator)  │
│                 │
│ • Receive       │
│   research      │
│ • Synthesize    │
│   findings      │
│ • Write files   │
└─────────────────┘
```

**Why This Pattern:**
1. **Separation of Concerns** - LLMs analyze, orchestrator writes
2. **No File Access** - LLM tools can't accidentally modify code
3. **Synthesis Control** - Main agent makes final decisions
4. **Multi-Perspective** - Combine insights from multiple LLMs

**Implementation in code-doc:**

```python
# 1. Format prompt for research
prompt = format_architecture_research_prompt(
    context_summary,
    key_files,
    project_root
)

# 2. Get research from LLM(s)
success, result = generate_architecture_docs(
    context_summary,
    key_files,
    project_root,
    use_multi_agent=True
)

# 3. Main agent synthesizes and writes
if success:
    responses_by_tool = result["responses_by_tool"]
    # Synthesize multiple perspectives
    final_doc = synthesize_responses(responses_by_tool)
    # Write file
    write_file("ARCHITECTURE.md", final_doc)
```

### BMAD Patterns

**Workflow Configuration (YAML):**
- Metadata: name, version, description, author
- Variables: config_source, output_folder, paths
- Component files: instructions, validation, templates
- Boolean flags: standalone, web_bundle

**Agent Definition (YAML):**
- metadata: id, name, title, icon
- persona: role, identity, communication_style, principles
- critical_actions: runtime initialization steps
- menu: user-facing commands with triggers
- prompts: reusable prompt templates (optional)

**Activation Protocol (XML):**
- `<activation>` block with initialization steps
- Command handlers for different action types
- Rules for agent behavior
- File loading only when executing (not pre-loading)

**Instruction Files (Markdown with XML):**
- `<critical>` blocks for mandatory steps
- `<workflow>` structure with numbered steps
- `<check if="condition">` for conditional logic
- `<action>` and `<invoke-workflow>` directives
- State file for resumable workflows

**Smart Loading Strategy:**
- Check state file FIRST before loading data
- Resume from checkpoint if available
- Only load necessary CSV/data files on resume
- Archive old state files instead of overwriting

---

## Integration Points for LLM-Doc-Gen

### 1. Provider Abstraction

**Use existing infrastructure:**
- `claude_skills.common.ai_tools` for provider calls
- `claude_skills.common.ai_config` for model resolution
- Standard ToolResponse envelope for consistency

**Add llm-doc-gen specific:**
- Doc type routing (if needed for different content types)
- Prompt formatters for various doc types
- Document composers for final output

### 2. Content Generation Workflow

```
1. Gather Context
   ├─ Read spec file (sdd get-task, sdd progress)
   ├─ Query codebase docs (sdd doc commands)
   └─ Extract relevant files/modules

2. Format LLM Prompt
   ├─ Include context summary
   ├─ Specify output format
   ├─ Add constraints (tone, length, structure)
   └─ Provide examples if needed

3. Execute LLM Consultation
   ├─ Single-agent OR multi-agent
   ├─ Parallel execution for speed
   ├─ Timeout handling
   └─ Error recovery

4. Synthesize Results
   ├─ Merge multi-agent responses (if applicable)
   ├─ Format per output type
   ├─ Validate against requirements
   └─ Compose final document

5. Write Output
   ├─ Save to specified location
   ├─ Update metadata
   └─ Report to user
```

### 3. LLM vs Programmatic Choice

**When to use LLM generation (llm-doc-gen):**
- Narrative documentation (architecture, design docs)
- Contextual explanations (why, not just what)
- Synthesized insights from multiple sources
- Human-readable guides and tutorials
- Nuanced interpretation of code patterns

**When to use programmatic generation (code-doc):**
- API reference documentation
- Function/class catalogs
- Dependency graphs
- Complexity metrics
- Structural analysis (AST-based)

**Can combine both:**
1. code-doc generates structural data (documentation.json)
2. llm-doc-gen reads that data + source code
3. LLM produces narrative documentation using structural context

---

## Recommended Architecture for LLM-Doc-Gen

### Module Structure

```
skills/llm-doc-gen/
├── SKILL.md              # User-facing documentation
├── cli.py                # CLI entry point (sdd llm-doc commands)
├── prompts/              # Prompt templates
│   ├── architecture.py
│   ├── tutorial.py
│   └── guide.py
├── synthesis.py          # Multi-agent response synthesis
└── workflow_engine.py    # Orchestration logic
```

### CLI Commands (Proposed)

```bash
# Generate narrative architecture doc
sdd llm-doc architecture <directory> --output ARCHITECTURE.md

# Generate tutorial from code
sdd llm-doc tutorial <feature> --output tutorial.md

# Generate developer guide
sdd llm-doc guide <module> --output guide.md

# Multi-agent mode (default)
sdd llm-doc architecture <dir> --multi-agent

# Single-agent mode
sdd llm-doc architecture <dir> --single-agent --tool cursor-agent
```

### Integration with Existing Tools

**Read code-doc output:**
```bash
# 1. Generate structural docs first
sdd doc generate ./src --name MyProject

# 2. Use that as input for LLM narrative
sdd llm-doc architecture ./src --use-code-doc ./docs/documentation.json
```

**Read SDD specs:**
```bash
# Generate docs from spec
sdd llm-doc from-spec <spec-id> --task <task-id> --output implementation-guide.md
```

---

## Next Steps

### Phase 2: Implementation Planning

1. **Define CLI interface** - Decide on command structure
2. **Design prompt templates** - Create effective prompts for each doc type
3. **Implement synthesis logic** - How to merge multi-agent responses
4. **Add error handling** - Timeouts, fallbacks, retries
5. **Write SKILL.md** - Following patterns identified in task-1-1

### Phase 3: Core Implementation

1. **Create CLI wrapper** - `sdd llm-doc` command structure
2. **Implement prompt formatters** - Per doc type
3. **Build workflow engine** - Orchestrate LLM calls
4. **Add synthesis layer** - Merge responses intelligently
5. **Write tests** - Unit + integration tests

### Phase 4: Integration & Documentation

1. **Integrate with code-doc** - Use structural data as input
2. **Integrate with SDD** - Generate docs from specs
3. **Write comprehensive SKILL.md** - Complete user guide
4. **Add examples** - Real-world usage scenarios
5. **Performance testing** - Optimize prompts and workflows

---

## References

### Code Files Analyzed

- `src/claude_skills/claude_skills/code_doc/ai_consultation.py`
- `src/claude_skills/common/ai_tools.py` (imported)
- `src/claude_skills/common/ai_config.py` (imported)

### BMAD Files Analyzed

- `src/modules/bmm/workflows/document-project/workflow.yaml`
- `src/core/agents/bmad-master.agent.yaml`
- `src/utility/models/agent-activation-ide.xml`
- `src/modules/bmm/workflows/document-project/instructions.md`

### Skills Analyzed

- `skills/code-doc/SKILL.md`
- `skills/doc-query/SKILL.md`
- `skills/sdd-plan/SKILL.md`

---

*This research document was created during the investigation phase of spec llm-doc-gen-2025-11-19-001 to capture findings for future implementation.*
