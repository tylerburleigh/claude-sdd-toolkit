# AI Context - Quick Reference Guide

**Project**: claude-sdd-toolkit
**Version**: 1.0.0
**Generated**: 2025-11-18

> This AI context guide was generated for AI assistants working with the SDD Toolkit codebase.
> Generated using `sdd doc analyze-with-ai` with cursor-agent AI consultation.

This document provides a concise, actionable reference for AI assistants (like Claude Code, Cursor, GitHub Copilot) working with the claude-sdd-toolkit codebase.

---

## 1. Project Overview

### What is the SDD Toolkit?

A **Python-based CLI toolkit** implementing Spec-Driven Development (SDD) - a systematic "plan-first" approach that keeps AI models "on guardrails" through machine-readable JSON specifications.

### Core Purpose

Enable structured, trackable, AI-assisted development by:
- Creating development specifications before coding
- Tracking progress through defined phases and tasks
- Reviewing implementation fidelity against specs
- Generating comprehensive documentation
- Integrating with multiple AI tools for enhanced assistance

### Target Users

Software developers and teams who want to:
- Leverage AI assistance systematically
- Maintain clear development plans and audit trails
- Ensure implementation matches specifications
- Track progress transparently

### Key Value Proposition

Puts AI "on guardrails" - provides structure and boundaries for AI-assisted development while maintaining flexibility and power.

---

## 2. Essential Domain Concepts

### 1. Spec (Specification) - The Heart of SDD

**Definition**: A machine-readable JSON file defining a development task end-to-end.

**Location**: `specs/{pending,active,completed,archived}/*.json`

**Structure**:
- **Metadata**: Name, description, version, complexity rating
- **Phases**: Logical groupings of related tasks
- **Tasks**: Atomic work units with IDs, descriptions, dependencies, verification steps
- **Dependencies**: Task relationships (which tasks must complete first)
- **Journal**: Decision log and notes during development
- **Status tracking**: Per-task and overall progress

**Lifecycle**:
```
pending/ → active/ → completed/ → archived/
```

**Why Critical**: Single source of truth for all development work; all CLI tools operate on specs.

**Schema**: Validated against `src/claude_skills/schemas/specification-schema.json`

---

### 2. Skills - Modular Capabilities

**Definition**: A command or set of related commands providing specific functionality.

**Core Skills**:

**Documentation**:
- `code_doc` - Generate codebase documentation (Markdown + JSON)
- `doc_query` - Query generated documentation, analyze dependencies

**SDD Workflow**:
- `sdd_plan` - Create new specifications
- `sdd_next` - Get next actionable task (core orchestration)
- `sdd_update` - Update task status and journal
- `sdd_validate` - Validate spec structure and dependencies
- `sdd_render` - Render specs to human-readable markdown

**Quality Assurance**:
- `sdd_fidelity_review` - Review implementation vs spec
- `sdd_plan_review` - Review specs before implementation
- `run_tests` - Test execution with AI debugging

**Workflow Support**:
- `sdd_pr` - Generate pull requests with AI
- `sdd_spec_mod` - Systematically modify specs
- `context_tracker` - Monitor Claude Code token usage

**Architecture**: Each skill is a Python package in `src/claude_skills/` with:
- `cli.py` - Command-line interface
- Business logic modules
- Integration with `common` utilities

**Independence**: Skills are modular and can be used standalone or in workflows.

---

### 3. Tasks - Atomic Work Units

**Definition**: Individual units of work within a spec.

**Structure**:
```json
{
  "id": "task-1-1",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication...",
  "phase_id": "phase-1",
  "dependencies": ["task-1-0"],
  "verification": ["Verify login works", "Test token expiration"],
  "status": "pending" | "in-progress" | "completed" | "verified"
}
```

**Key Fields**:
- `id` - Unique identifier (e.g., `task-1-1`, `task-2-3`)
- `dependencies` - Array of task IDs that must complete first
- `verification` - Steps to verify task completion
- `status` - Current task state

**Task States**:
- `pending` - Not yet started
- `in-progress` - Currently being worked on
- `completed` - Implementation done, awaiting verification
- `verified` - Verification steps completed

---

### 4. Dependencies - Task Relationships

**Definition**: Directed edges between tasks defining execution order.

**Format**: Task ID references in `dependencies` array

**Example**:
```json
{
  "id": "task-2-1",
  "dependencies": ["task-1-1", "task-1-2"]
}
```
*Task 2-1 can only start after tasks 1-1 AND 1-2 are completed.*

**Validation**: `sdd_validate` detects circular dependencies

**Impact**: `sdd_next` uses dependencies to determine which tasks are ready vs blocked

---

### 5. Phases - Logical Grouping

**Definition**: High-level organizational units grouping related tasks.

**Structure**:
```json
{
  "id": "phase-1",
  "title": "Foundation Setup",
  "description": "Core infrastructure and setup",
  "dependencies": []
}
```

**Purpose**:
- Organize large projects into manageable chunks
- Enable phase-level reviews and reporting
- Support incremental delivery

**Dependencies**: Phases can depend on other phases completing first

---

### 6. Provider - AI Tool Abstraction

**Definition**: Standardized interface for external AI CLI tools.

**Supported Providers**:
- **Gemini** - Google Gemini CLI (`gemini`)
- **Codex** - Anthropic Codex CLI (`codex`)
- **Cursor Agent** - Cursor IDE AI agent (`cursor-agent`)
- **Claude** - Claude CLI (`claude`, read-only restrictions)
- **OpenCode** - OpenCode AI SDK via Node.js wrapper (`opencode`)

**Provider Context**: Base class `ProviderContext` in `src/claude_skills/common/providers/base.py`

**Why Important**: Enables "bring your own AI" model - users choose their preferred tools

**Configuration**: Managed via `ai_config.json` and environment

---

### 7. Documentation JSON - Machine-Readable Codebase

**Location**: `docs/documentation.json`

**Generated By**: `sdd doc generate` or `sdd doc analyze-with-ai`

**Content**:
- All modules, classes, functions with full details
- Complexity metrics (cyclomatic complexity)
- Dependency graphs (imports, relationships)
- Code statistics (lines, files, averages)
- Framework and pattern detection

**Consumed By**:
- `doc_query` - For all query operations
- `sdd_next` - For task context preparation
- Analysis tools - For code insights

**Schema**: Defined in `src/claude_skills/schemas/documentation-schema.json`

---

### 8. Cache - AI Consultation Results

**Location**: Project-local cache directory (`.sdd_cache/` or similar)

**Purpose**: Store AI consultation results to reduce cost and latency

**Features**:
- TTL-based expiration (configurable, default varies by use case)
- Deterministic key generation (prompt + model + version)
- Automatic cleanup of expired entries

**Management**: `sdd cache clear`, `sdd cache inspect`

**Why Important**: Multi-model consultation can be expensive; caching prevents redundant calls

---

## 3. Critical Files for AI Assistants

### Must-Know Files (Read These First)

#### 1. **Specification Schema**
- **Path**: `src/claude_skills/schemas/specification-schema.json`
- **Why**: Defines valid spec structure, all required/optional fields
- **When**: Creating/modifying specs, validating structure

#### 2. **Documentation Schema**
- **Path**: `src/claude_skills/schemas/documentation-schema.json`
- **Why**: Defines structure of generated documentation
- **When**: Parsing documentation.json, generating docs

#### 3. **Common Utilities**
- **Path**: `src/claude_skills/common/`
- **Why**: Shared utilities ALL skills depend on
- **Key Modules**:
  - `printer.py` - Output formatting (PrettyPrinter)
  - `spec.py` - Spec loading/saving
  - `validation.py` - Spec validation
  - `paths.py` - Path resolution
  - `providers/` - AI tool integration

#### 4. **CLI Registry**
- **Path**: `src/claude_skills/cli/registry.py`
- **Why**: Central command registration - how CLI routes to skills
- **When**: Understanding command flow, adding new commands

#### 5. **README and Documentation**
- **Paths**: `README.md`, `docs/ARCHITECTURE.md`, `docs/DOCUMENTATION.md`
- **Why**: High-level understanding, usage examples
- **When**: First-time orientation, understanding workflows

### File Naming Conventions

#### Spec Files
- **Format**: `<descriptive-name>-<YYYY-MM-DD>-<NNN>.json`
- **Example**: `user-auth-feature-2025-11-18-001.json`
- **Location**: `specs/{pending,active,completed,archived}/`

#### Skill Structure
- **Pattern**: `src/claude_skills/<skill_name>/`
  - `cli.py` - CLI interface (required)
  - `<feature>.py` - Business logic modules
  - `__init__.py` - Package initialization

#### Schema Files
- **Location**: `src/claude_skills/schemas/`
- **Pattern**: `<name>-schema.json`

#### Generated Documentation
- **Location**: `docs/`
- **Files**:
  - `DOCUMENTATION.md` - Human-readable structural docs
  - `documentation.json` - Machine-readable structural data
  - `ARCHITECTURE.md` - AI-enhanced architecture overview
  - `AI_CONTEXT.md` - This file - AI assistant quick reference

---

## 4. Common Workflows

### Workflow 1: Create and Execute a Spec

**Goal**: Plan a feature, execute tasks systematically

**Steps**:
```bash
# 1. Create new spec
sdd plan create --name "Add Authentication" --output specs/active/

# 2. Edit spec JSON to define phases, tasks, dependencies

# 3. Validate spec
sdd validate specs/active/auth-feature-2025-11-18-001.json

# 4. Get next actionable task
sdd next-task auth-feature-2025-11-18-001

# 5. Implement the task

# 6. Update task status
sdd update auth-feature-2025-11-18-001 --task task-1-1 --status completed

# 7. Add journal entry
sdd journal auth-feature-2025-11-18-001 "Implemented JWT auth with bcrypt"

# 8. Repeat steps 4-7 until all tasks done

# 9. Review implementation fidelity
sdd fidelity-review auth-feature-2025-11-18-001

# 10. Create pull request
sdd pr create auth-feature-2025-11-18-001
```

---

### Workflow 2: Generate and Query Documentation

**Goal**: Document codebase, analyze code structure

**Steps**:
```bash
# 1. Generate comprehensive docs with AI enhancement
sdd doc analyze-with-ai . --name "MyProject" --version "1.0.0"

# 2. Query documentation
sdd doc stats                          # Show statistics
sdd doc complexity --threshold 10      # High-complexity functions
sdd doc search "authentication"        # Find auth-related code
sdd doc dependencies src/auth.py       # Show dependencies

# 3. Analyze call graphs
sdd doc callers authenticate_user      # Who calls this?
sdd doc callees authenticate_user      # What does this call?

# 4. Impact analysis
sdd doc impact authenticate_user       # Impact of changing this function
```

---

### Workflow 3: Review Spec Before Implementation

**Goal**: Validate spec quality before starting work

**Steps**:
```bash
# 1. Create spec (manually or via sdd plan create)

# 2. Run multi-model spec review
sdd plan-review specs/active/new-feature-2025-11-18-001.json

# 3. Review generated report (identifies ambiguities, missing details)

# 4. Modify spec based on feedback
sdd spec-mod specs/active/new-feature-2025-11-18-001.json --apply-review

# 5. Re-validate
sdd validate specs/active/new-feature-2025-11-18-001.json

# 6. Proceed with implementation (Workflow 1)
```

---

### Workflow 4: Debug Test Failures with AI

**Goal**: Use AI to help debug failing tests

**Steps**:
```bash
# 1. Run tests
sdd test run --preset all

# 2. If failures, consult AI for debugging help
sdd test debug --test test_authentication --ai gemini

# 3. Review AI suggestions

# 4. Fix code based on suggestions

# 5. Re-run tests
sdd test run --preset all
```

---

### Workflow 5: Monitor Context Usage (Claude Code)

**Goal**: Track token/context consumption in Claude Code

**Steps**:
```bash
# 1. Find Claude Code transcript file
# Usually in ~/.claude_code/transcripts/ or similar

# 2. Monitor usage
sdd context-tracker <transcript-file>

# 3. View real-time metrics
# - Tokens used
# - Context window percentage
# - Tool usage breakdown
```

---

## 5. Potential Gotchas

### 1. Spec Validation is Strict

**Issue**: Specs must pass JSON schema validation

**Gotcha**: Missing required fields, incorrect field types, circular dependencies will cause failures

**Fix**:
- Always run `sdd validate <spec>` before using a spec
- Use `sdd validate --fix` for auto-fixable issues
- Check schema at `src/claude_skills/schemas/specification-schema.json`

**Example Error**:
```
ValidationError: 'phase_id' is required for task task-1-1
```

---

### 2. Documentation Staleness

**Issue**: Code changes after documentation generation make docs stale

**Gotcha**: `doc_query` may prompt to regenerate if docs are stale

**Fix**:
- Regenerate docs when code changes significantly: `sdd doc generate .`
- Use `--skip-refresh` flag to bypass staleness check (not recommended)
- Set up pre-commit hooks to auto-regenerate

**Staleness Detection**: Compares doc generation timestamp vs file modification times

---

### 3. AI Tool Availability

**Issue**: Skills requiring AI tools fail if tools not installed

**Gotcha**: Multi-agent consultation needs at least 2 AI tools installed

**Fix**:
- Check available tools: `sdd test check-tools`
- Install missing tools (gemini, cursor-agent, codex)
- Use `--single-agent` flag for single-tool consultation
- Fall back to non-AI commands (e.g., `sdd doc generate` instead of `analyze-with-ai`)

**Detection**: Provider registry auto-detects installed tools

---

### 4. Dependency Resolution

**Issue**: Complex dependency graphs can block progress

**Gotcha**: `sdd next-task` may report "no ready tasks" if all tasks are blocked

**Fix**:
- Visualize dependencies: `sdd validate <spec> --show-graph`
- Check for circular dependencies: `sdd validate <spec>`
- Review dependency logic - ensure at least one task has no dependencies
- Consider breaking large specs into smaller ones

**Common Pattern**: Start with one "setup" task with no dependencies

---

### 5. Provider-Specific Restrictions

**Issue**: Claude provider has read-only restrictions

**Gotcha**: Some operations fail with Claude provider due to security restrictions

**Fix**:
- Use gemini, cursor-agent, or codex for write operations
- Check provider capabilities in `common/providers/<provider>.py`
- Provider selection order: cursor-agent → gemini → codex → claude

**Read-Only Operations**: Claude provider can read but not write/modify code

---

### 6. JSON vs Rich Output Modes

**Issue**: CLI output format varies by flags

**Gotcha**: Mixing `--json` with Rich formatting flags causes issues

**Fix**:
- Use `--json` for programmatic consumption (scripts, agents)
- Use Rich output (default) for human readability
- Use `--no-json` to explicitly disable JSON output
- Check config: `sdd_config.json` may set defaults

**Example**:
```bash
# For scripts/agents
sdd next-task <spec> --json

# For humans
sdd next-task <spec> --verbose
```

---

### 7. Work Mode Confusion

**Issue**: `sdd-next` behavior changes based on work mode

**Gotcha**: Auto mode doesn't prompt, interactive mode does

**Fix**:
- Understand modes:
  - `auto` - No prompts, fail fast (for AI agents)
  - `manual` - Explicit task selection required
  - `interactive` - Prompts for user decisions
- Set via: `--work-mode <mode>` flag or `work_mode` in config
- Check current mode: `sdd config show`

**Default**: Usually `interactive` for humans, `auto` for agents

---

### 8. Cache Invalidation

**Issue**: Cached AI results may be stale

**Gotcha**: Code changes don't auto-invalidate cache

**Fix**:
- Clear cache: `sdd cache clear`
- Inspect cache: `sdd cache inspect`
- TTL handles most cases automatically
- Force refresh: bypass cache in consultation calls (varies by skill)

**When to Clear**: After significant code changes, before important reviews

---

## 6. Extension Patterns

### Adding a New Skill

**Goal**: Extend toolkit with custom functionality

**Steps**:

1. **Create Skill Package**:
   ```bash
   mkdir -p src/claude_skills/<skill_name>
   touch src/claude_skills/<skill_name>/__init__.py
   touch src/claude_skills/<skill_name>/cli.py
   ```

2. **Implement CLI Interface** (`cli.py`):
   ```python
   import argparse
   from claude_skills.common.printer import PrettyPrinter

   def register_commands(subparsers):
       parser = subparsers.add_parser('my-command')
       parser.add_argument('--option', help='...')
       parser.set_defaults(func=cmd_my_command)

   def cmd_my_command(args, printer: PrettyPrinter):
       # Implementation
       printer.success("Done!")
   ```

3. **Register in Main CLI**:
   - Add to `src/claude_skills/cli/registry.py`
   - Import and call `register_commands()`

4. **Use Common Utilities**:
   ```python
   from claude_skills.common.printer import PrettyPrinter
   from claude_skills.common.spec import load_json_spec
   from claude_skills.common.validation import validate_spec
   ```

5. **Add Tests**:
   - Create `tests/<skill_name>/` directory
   - Write unit and integration tests

6. **Document**:
   - Update README.md
   - Add skill documentation

---

### Adding a New Language Parser (code_doc)

**Goal**: Support additional programming languages

**Steps**:

1. **Install Tree-Sitter Grammar**:
   ```bash
   pip install tree-sitter-<language>
   ```

2. **Create Parser Module**:
   ```python
   # src/claude_skills/code_doc/parsers/<language>.py
   from .base import BaseParser

   class LanguageParser(BaseParser):
       def __init__(self):
           super().__init__(language='<language>')

       def parse_file(self, file_path):
           # Implementation
           return parsed_data
   ```

3. **Update Parser Factory**:
   ```python
   # src/claude_skills/code_doc/parsers/factory.py
   from .<language> import LanguageParser

   def create_parser_factory():
       return {
           '<language>': LanguageParser,
           # ...
       }
   ```

4. **Add Language Detection**:
   ```python
   # src/claude_skills/code_doc/detectors.py
   LANGUAGE_EXTENSIONS = {
       '<language>': ['.ext1', '.ext2'],
       # ...
   }
   ```

5. **Test**:
   - Create test files in new language
   - Verify parsing and documentation generation

---

### Adding a New AI Provider

**Goal**: Integrate a new AI CLI tool

**Steps**:

1. **Create Provider Class**:
   ```python
   # src/claude_skills/common/providers/<provider>.py
   from .base import ProviderContext

   class NewProvider(ProviderContext):
       def __init__(self, model=None):
           super().__init__(name='<provider>', model=model)

       def _run_prompt_impl(self, prompt, **kwargs):
           # Call external CLI tool
           result = subprocess.run(['<cli>', 'prompt', prompt], ...)
           return result.stdout

       def supports_write_operations(self):
           return True  # or False if read-only
   ```

2. **Register Provider**:
   ```python
   # src/claude_skills/common/providers/registry.py
   from .<provider> import NewProvider

   def get_all_providers():
       return {
           '<provider>': NewProvider,
           # ...
       }
   ```

3. **Add Detection Logic**:
   ```python
   # src/claude_skills/common/providers/detectors.py
   def detect_<provider>():
       try:
           subprocess.run(['<cli>', '--version'], ...)
           return True
       except FileNotFoundError:
           return False
   ```

4. **Update Configuration**:
   - Add to `ai_config.json` template
   - Document provider-specific settings

5. **Test**:
   - Test with mock provider
   - Test with actual CLI tool
   - Verify read/write restrictions

---

## 7. Performance Tips

### 1. Use JSON Output for Programmatic Access

**Why**: JSON parsing is faster than Rich terminal output parsing

**How**:
```bash
sdd next-task <spec> --json | jq '.next_task.id'
```

**Benefit**: Enables scripting, automation, integration with other tools

---

### 2. Skip Staleness Checks When Appropriate

**Why**: Documentation regeneration can be slow on large codebases

**How**:
```bash
sdd doc search "pattern" --skip-refresh
```

**Caution**: Results may be based on stale data

**Best Practice**: Use during iterative queries, regenerate when code changes

---

### 3. Use Single-Agent Mode for Faster Consultation

**Why**: Multi-agent consultation consults 2+ AI models (slower but higher quality)

**How**:
```bash
sdd plan-review <spec> --single-agent --ai gemini
```

**Trade-off**: Faster but less comprehensive review

**When**: Quick iterations, low-stakes reviews

---

### 4. Leverage Caching

**Why**: AI consultation is slow and expensive

**How**: Let the toolkit handle it automatically (caching is default)

**Manual Control**:
```bash
sdd cache inspect   # View cache contents
sdd cache clear     # Clear all cache (forces fresh consultation)
```

**Best Practice**: Clear cache only when necessary (significant code changes)

---

### 5. Use Verbosity Levels Wisely

**Why**: Verbose output can be overwhelming, quiet output saves tokens

**How**:
```bash
sdd next-task <spec> --quiet      # Minimal output, essential only
sdd next-task <spec>              # Standard output
sdd next-task <spec> --verbose    # Detailed debugging output
```

**For AI Agents**: Use `--quiet --json` for minimal token usage

**For Humans**: Use `--verbose` for debugging

---

### 6. Batch Operations When Possible

**Why**: Reduces overhead of loading specs/docs multiple times

**How**: Use commands that operate on multiple entities

**Example**:
```bash
# Good - batch validation
sdd validate specs/active/*.json

# Less efficient - one at a time
for spec in specs/active/*.json; do sdd validate $spec; done
```

---

## 8. Common Error Messages & Solutions

### Error: "Spec validation failed: Circular dependency detected"

**Cause**: Task dependencies form a cycle (A → B → C → A)

**Solution**:
1. Run `sdd validate <spec> --show-graph` to visualize
2. Identify the cycle
3. Remove one dependency to break the cycle
4. Re-validate

---

### Error: "No ready tasks found"

**Cause**: All tasks are blocked by dependencies

**Solution**:
1. Check dependency graph: `sdd validate <spec> --show-graph`
2. Ensure at least one task has no dependencies (entry point)
3. Mark blocking tasks as completed if they're done
4. Consider if some dependencies are unnecessary

---

### Error: "Documentation is stale or missing"

**Cause**: `docs/documentation.json` doesn't exist or is older than code

**Solution**:
1. Regenerate documentation: `sdd doc generate .`
2. Or with AI enhancement: `sdd doc analyze-with-ai .`
3. Or skip staleness check: `sdd doc <command> --skip-refresh`

---

### Error: "AI tool 'gemini' not found"

**Cause**: Required AI CLI tool is not installed or not in PATH

**Solution**:
1. Check available tools: `sdd test check-tools`
2. Install missing tool (e.g., `pip install gemini-cli`)
3. Or use different provider: `--ai cursor-agent`
4. Or use single-agent mode: `--single-agent`
5. Or fall back to non-AI command

---

### Error: "Provider 'claude' does not support write operations"

**Cause**: Attempting write operation with read-only Claude provider

**Solution**:
1. Use different provider: `--ai gemini` or `--ai cursor-agent`
2. Check provider capabilities in docs
3. Understand which operations require write access

---

### Error: "Task 'task-1-1' not found in spec"

**Cause**: Referenced task ID doesn't exist in spec

**Solution**:
1. Check task IDs in spec: `sdd list-tasks <spec>`
2. Fix typo in task ID
3. Ensure task exists before referencing in dependencies or commands

---

## 9. Key Takeaways for AI Assistants

### 1. Specs Are Central
- Everything in SDD revolves around JSON specification files
- Always validate specs before and after modifications
- Specs live in `specs/{pending,active,completed,archived}/`

### 2. Use Common Utilities
- Don't reinvent utilities - use `common/` package
- `PrettyPrinter` for all output
- `load_json_spec()` / `save_json_spec()` for spec operations
- `validate_spec()` before saving specs

### 3. Follow Naming Conventions
- Spec files: `<name>-<YYYY-MM-DD>-<NNN>.json`
- Task IDs: `task-<phase>-<number>` (e.g., `task-1-1`)
- Phase IDs: `phase-<number>` (e.g., `phase-1`)

### 4. Respect Dependencies
- Always check task dependencies before marking as ready
- Circular dependencies are invalid and will fail validation
- Use `sdd next-task` to find ready tasks (respects dependencies)

### 5. Provider Awareness
- Different AI providers have different capabilities
- Claude provider is read-only
- Multi-agent mode requires 2+ providers installed
- Check availability with `sdd test check-tools`

### 6. Documentation is Queryable
- Generate docs with `sdd doc generate` or `analyze-with-ai`
- Query with `doc_query` commands (search, complexity, dependencies, etc.)
- `documentation.json` is machine-readable - use it for code analysis

### 7. Verbosity Matters
- `--json` for programmatic access (agents, scripts)
- `--verbose` for debugging
- `--quiet` for minimal output (token efficiency)

### 8. Caching Improves Performance
- AI consultation results are cached with TTL
- Clear cache after significant changes: `sdd cache clear`
- Cache is transparent - no manual management needed usually

### 9. Work Modes Affect Behavior
- `auto` - No prompts, fail fast (for AI agents)
- `manual` - Explicit task selection
- `interactive` - Prompts for decisions
- Set appropriately based on context

### 10. Validation is Your Friend
- Always validate specs: `sdd validate <spec>`
- Use `--fix` for auto-fixable issues
- Validation catches circular dependencies, missing fields, schema violations

---

## 10. Quick Reference Commands

### Spec Operations
```bash
sdd plan create --name "Feature"           # Create new spec
sdd validate <spec>                        # Validate spec
sdd validate <spec> --fix                  # Auto-fix issues
sdd next-task <spec>                       # Get next ready task
sdd update <spec> --task <id> --status <s> # Update task status
sdd journal <spec> "Decision note"         # Add journal entry
sdd progress <spec>                        # Show progress
```

### Documentation
```bash
sdd doc generate .                         # Generate structural docs
sdd doc analyze-with-ai .                  # Generate AI-enhanced docs
sdd doc stats                              # Show statistics
sdd doc search "pattern"                   # Search entities
sdd doc complexity --threshold 10          # High-complexity functions
sdd doc dependencies <module>              # Show dependencies
sdd doc callers <function>                 # Show callers
sdd doc impact <function>                  # Impact analysis
```

### Reviews
```bash
sdd plan-review <spec>                     # Review spec before implementation
sdd fidelity-review <spec>                 # Review implementation vs spec
```

### Testing
```bash
sdd test run --preset all                  # Run tests
sdd test debug --test <name> --ai gemini   # Debug with AI
sdd test check-tools                       # Check AI tool availability
```

### PR Creation
```bash
sdd pr create <spec>                       # Create PR from spec
```

### Cache Management
```bash
sdd cache clear                            # Clear all cache
sdd cache inspect                          # View cache contents
```

---

## Summary

The claude-sdd-toolkit enables **systematic, trackable, AI-assisted development** through:

1. **Machine-readable JSON specifications** that define work upfront
2. **Modular skills** for documentation, planning, execution, review, and PR creation
3. **Multi-AI integration** via provider abstraction (gemini, cursor-agent, codex, claude)
4. **Comprehensive documentation** generation and querying
5. **Quality assurance** through fidelity reviews and plan reviews
6. **Progress tracking** with status updates and journaling

**For AI assistants working with this codebase**:
- Start with specs - they're the source of truth
- Use `common` utilities for consistency
- Validate early and often
- Leverage documentation for code understanding
- Respect dependencies and provider capabilities
- Choose appropriate verbosity and work modes

This structured approach keeps AI assistance systematic and on-track while maintaining developer control and visibility.
