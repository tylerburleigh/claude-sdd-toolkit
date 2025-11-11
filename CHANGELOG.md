# Changelog

All notable changes to the SDD Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and aspires to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (but probably doesn't).

# Unreleased

### Added
- **Claude Provider** - New AI provider for Anthropic Claude models with read-only tool restrictions
  - Supports Sonnet 4.5 and Haiku 3.5 models
  - Read-only security mode (blocks Write, Edit, Bash tools)
  - Allows Read, Grep, Glob, WebSearch, WebFetch, Task, Explore tools only
  - Default 360-second timeout for extended reasoning
  - Comprehensive unit and integration test coverage (19 unit tests)
  - Provider detection with environment variable overrides
  - CLI runner support for testing: `python -m claude_skills.cli.provider_runner --provider claude`
- `ai_config_setup.ensure_ai_config()` helper shared by setup workflows to seed `.claude/ai_config.yaml` with packaged defaults.
- `sdd fidelity-review` now auto-saves both Markdown and JSON reports when no output path is provided, making it easier to reuse results across tooling.
- Centralized setup templates bundled under `claude_skills.common.templates.setup` with a public `setup_templates` helper module for loading or copying packaged defaults.
- Unit and integration coverage that exercises the new setup templates, including `tests/unit/test_common/test_setup_templates.py` and the updated `skills-dev setup-permissions` integration flow.
- Provider abstraction documentation that explains the `ProviderContext` contract, registry/detector workflow, and how to exercise providers via the `provider_runner` CLI.

### Fixed
- Updated CLI integration tests to opt into text output (`--no-json`) so completion prompts and human-facing messaging continue to be covered after switching to JSON-first defaults.
- Restored the packaged `.claude/settings.local.json` template so setup tooling and tests can copy the default permission manifest without errors.

### Changed
- **Provider Timeout Increased** - All AI provider default timeouts increased from 120s to 360s to support extended reasoning and complex tasks across Gemini, Codex, Cursor Agent, and Claude providers
- Consolidated AI model resolution across `run-tests`, `sdd doc analyze-with-ai`, `sdd plan-review`, and `sdd render --mode enhanced`. These flows now delegate to `ai_config.resolve_tool_model`, accept `--model` CLI overrides (global or per-tool), surface the resolved map in progress output, and ship unit tests documenting the shared helper contract.
- Run-tests, code-doc, and sdd-render runtimes now invoke AI providers via the shared registry/`execute_tool` helpers, so dry runs, timeouts, and error reporting use the new normalized response envelope.

## [0.5.0] - 2025-11-09

### Added
- **Plain UI Mode** - Terminal-agnostic plain text output mode alongside Rich mode
  - `default_mode` config option: `rich`, `plain`, or `json`
  - Automatic CI/CD environment detection (`FORCE_PLAIN_UI`)
  - Consistent rendering across all CLI commands
- **Centralized JSON Output** - `json_output.py` helper module with config-aware formatting
  - Unified JSON printing across all commands
  - Respects `default_mode` and `json_compact` configuration
- **Schema Validation Infrastructure** - Optional JSON Schema validation with Draft 07 support
  - Cached schema loader with environment variable overrides
  - Optional `validation` dependency group (`jsonschema>=4.0.0`)
  - Schema errors surfaced in `sdd validate` CLI output
- **Workflow Guardrails** - Security and workflow enforcement
  - Pre-tool hook (`hooks/block-json-specs`) blocks direct spec JSON reads
  - Tool invocations enforce read-only sandbox mode
  - Forces usage of structured `sdd` CLI commands
- **Directory Scaffolding** - `.fidelity-reviews/` directory with README template
- **Documentation** - `docs/OUTPUT_FORMAT_BENCHMARKS.md` with token savings analysis
- **Testing Infrastructure** - Comprehensive integration and unit test coverage
  - New CLI runner helpers (`tests/integration/cli_runner.py`)
  - Cache operation tests covering CRUD, TTL, statistics, key generation
  - All tests relocated to `src/claude_skills/claude_skills/tests`

### Changed
- **Configuration System Modernization**
  - Replaced `output.json` boolean with `output.default_mode` enum (rich/plain/json)
  - Replaced `output.compact` with `output.json_compact` for clarity
  - Legacy format still supported for backward compatibility
- **AI Configuration Consolidation**
  - Skills load AI settings from `.claude/ai_config.yaml` (centralized)
  - Removed per-skill `config.yaml` files
  - Added merge helpers and safe defaults for tool invocation
  - Added `CLAUDE_SKILLS_TOOL_PATH` environment override for PATH resolution
- **CLI Registry Improvements**
  - `_try_register_optional()` ensures graceful degradation when optional modules missing
  - Prevents CLI startup crashes when `sdd_render` or `sdd_fidelity_review` unavailable
  - Enhanced logging for module registration
- **Validation Workflow Enhancement**
  - `sdd validate` runs schema validation before structural analysis
  - Schema messages routed through CLI output system
  - Diff views respect UI abstraction (Rich/Plain parity)
- **UI Abstraction Layer**
  - `ui_factory.py` creates appropriate UI based on mode
  - Status dashboard refactored for Plain/Rich parity
  - Path utilities moved to `paths.py`
- **Test Suite Organization**
  - All tests migrated from top-level `tests/` to `src/claude_skills/claude_skills/tests`
  - pytest discovery configured for package namespace
  - Removed duplicate legacy test files

### Removed
- **Legacy Documentation** - ~50,000 lines of research artifacts and design docs removed
- **Per-Skill Configuration** - Individual `skills/*/config.yaml` files (replaced by centralized AI config)
- **Top-Level Tests** - Removed `tests/` directory after migration to package namespace
- **Duplicate Test Files** - Cleaned up obsolete test artifacts

### Security
- Tool invocations enforce read-only sandbox mode and JSON output
- Pre-tool hooks prevent direct spec JSON access (forces CLI workflow)
- Environment-based retries with PATH override capability

### Breaking Changes
- **Schema Validation** - Specs missing required metadata will now fail validation
- **Hook Enforcement** - Direct reads of `specs/*.json` files exit with failure; scripts must use CLI commands (`sdd next-task`, `sdd query-tasks`, etc.)
- **Config Migration** - Projects using `output.json`/`output.compact` should migrate to `output.default_mode`/`output.json_compact` (legacy format still supported)
- **Optional Dependencies** - Schema validation requires `pip install ".[validation]"`; warnings shown when unavailable

### Notes
- All 36 cache tests passing
- Plain mode verified in CI/CD environments
- Config precedence: CLI flags → project config → global config → defaults

## [0.4.5] - 2025-11-05

### Added
- **AI Tools Infrastructure** - Unified `ai_tools` module for consistent AI CLI interactions
  - `execute_tool()` - Single AI tool consultation with structured responses
  - `execute_tools_parallel()` - Multi-agent parallel execution using ThreadPoolExecutor
  - `check_tool_available()` / `detect_available_tools()` - Tool availability detection
  - `build_tool_command()` - Tool-specific command construction
  - `ToolResponse` / `MultiToolResponse` - Immutable response dataclasses with type safety
- **AI Configuration Module** - Centralized `ai_config` module for tool detection and configuration
- **Comprehensive API Documentation** - `docs/API_AI_TOOLS.md` (1,038 lines) with complete API reference
- **Integration Tests** - 44 new tests for AI tools with mock CLI tools
- **Unit Tests** - 27 new tests for core AI tools functions
- **End-to-End Tests** - 21 tests for run-tests AI consultation workflow
- **sdd-plan-review Tests** - 15 integration tests for multi-model review

### Changed
- **run-tests skill** - Migrated to use shared `ai_tools` infrastructure
  - Replaced custom tool checking with `check_tool_available()`
  - Migrated `run_consultation()` to `execute_tool()`
  - Migrated `consult_multi_agent()` to `execute_tools_parallel()`
- **sdd-plan-review skill** - Refactored to use `execute_tools_parallel()` for parallel reviews
- **code-doc skill** - Updated AI consultation to use shared infrastructure

### Removed
- **tool_checking.py** - Removed 396 lines of duplicated tool checking code from run-tests
- **Obsolete test files** - Removed 4 outdated test files (422 lines) for old module structures

### Fixed
- **Test isolation** - Fixed shallow copy bug in `sdd_config.py` causing test pollution
- **Test mocking** - Fixed incorrect patch decorators in `test_sdd_config.py`

### Performance
- **Parallel execution** - Tools run concurrently (time = slowest tool, not sum)
- **Proper timeout handling** - 90s default with configurable timeouts
- **Efficient resource management** - ThreadPoolExecutor with proper cleanup

### Documentation
- Created comprehensive API documentation at `docs/API_AI_TOOLS.md`
- Documented all functions, dataclasses, and usage patterns
- Included error handling guidance and best practices

### Notes
- All 139 tests passing (5 skipped)
- No performance regressions detected
- Backwards compatible - no breaking changes to existing skill CLIs
- Net change: +6,154 insertions, -4,173 deletions across 24 files

## [0.4.2] - 2025-11-04

### Added

**Configurable JSON Output System:**
- **Compact Mode**: Reduces output from `sdd` commands by an estimated 30%
  - Single-line output eliminates unnecessary whitespace and newlines
  - Ideal for machine-to-machine communication and token optimization
- **Configuration File**: New `.claude/sdd_config.json` for persistent preferences
  - Configure `json` and `compact` output modes globally
  - Interactive setup prompts during `sdd setup-permissions`
  - Config hierarchy: project-local > global > built-in defaults
- **CLI Flags**: `--json`/`--no-json` and `--compact`/`--no-compact`
  - Runtime override of config file settings
  - Full argparse integration with mutually exclusive groups

### Fixed
- Fixed `--no-compact` flag not being recognized (argument reordering bug)
- Fixed argument reconstruction for boolean False values (now properly uses `--no-` prefix)

### Documentation
- Added SDD_CONFIG_README.md with comprehensive configuration guide
- Updated README.md with configuration section
- Updated setup scripts with interactive prompts

## [0.4.1] - 2025-11-03

### Added

**Git Integration Features (PR #13):**
- **Agent-Controlled File Staging**: Two-step commit workflow with preview-and-select pattern
  - New functions for selective file staging with granular control
  - Prevents unrelated files from being included in commits
  - Opt-in via `file_staging.show_before_commit` config (backward compatible)
  - CLI command: `sdd create-task-commit`

- **AI-Powered PR Creation (sdd-pr skill)**: Automated comprehensive PR descriptions
  - Analyzes spec metadata, git diffs, commit history, and journal entries
  - Two-step workflow: draft review → user approval → PR creation
  - Automatic handoff from `sdd-next` after spec completion
  - Configurable via `.claude/git_config.json` (`ai_pr` section)

### Changed
- Reorganized README.md for improved readability and user onboarding flow

### Notes
- Run `sdd setup-permissions update .` to add sdd-pr permissions
- Enable features in `.claude/git_config.json` as needed

## [0.4.0] - 2025-11-02

### Added

**Code Documentation & Integration:**
- Code-doc integration for SDD skills - sdd-plan, sdd-next, and run-tests now leverage generated codebase documentation for richer context (PR #11)
- AI-enhanced spec rendering with three enhancement levels (summary/standard/full) (PR #11)
- `sdd render` command with basic and AI-enhanced modes (PR #11)
- Cross-reference tracking in doc-query: callers, callees, call graphs (PR #3)
- Workflow automation commands: trace-entry, trace-data, impact analysis, refactor-candidates (PR #3)
- Bidirectional relationship tracking in documentation schema v2.0 (PR #3)

**Context & Time Management:**
- Context tracking system to monitor Claude token usage and prevent hitting 160k limit (PR #8, PR #9)
- `sdd context` command for viewing current session usage
- `sdd session-marker` for transcript identification
- Automatic time tracking via timestamps - no manual entry needed (PR #7)
  - `started_at` and `completed_at` timestamps recorded automatically
  - `actual_hours` calculated from duration

**Workflow Enhancements:**
- Pending folder workflow - specs created in `specs/pending/` by default (PR #8)
- `sdd activate-spec` command to move specs from pending to active
- Automatic spec completion detection with prompts (PR #6)
- Task category metadata: investigation, implementation, refactoring, decision, research (PR #5)
- `sdd complete-task` command with automatic journaling (PR #6)
- `sdd list-specs` command with status filtering (PR #8)
- `sdd update-task-metadata` command for field updates (PR #11)

**Project Organization:**
- Centralized spec metadata in hidden directories (PR #1):
  - `.reports/` - Validation reports (gitignored)
  - `.reviews/` - Multi-model reviews (gitignored)
  - `.backups/` - Spec backups (gitignored)
  - `.human-readable/` - Rendered markdown (gitignored)

**Enhanced Validation:**
- Improved auto-fix capabilities with iterative workflow (PR #4)
- Better error messaging and UX (PR #4)
- Enhanced validation documentation (PR #4)

### Changed
- Refactored to subagent architecture for cleaner skill execution (PR #9)
  - sdd-validate, sdd-plan-review, sdd-update, run-tests, code-doc use specialized subagents
  - Autonomous task execution with parallel support
- Moved `DEVELOPER.md` to `docs/BEST_PRACTICES.md` (PR #5)
- Enhanced SKILL.md documentation with comprehensive examples (PR #11)
- Improved `/sdd-begin` to show both pending and active specs (PR #8)
- Better session start hooks with context tracking (PR #9)
- Improved spec lifecycle management (PR #8)

### Removed
- Manual time entry (`--actual-hours` flag) - replaced by automatic timestamp tracking (PR #7)
- Pre-approved Read permissions for spec files to enable proper hook interception (PR #10)

### Fixed
- JSON spec corruption issues (PR #1)
- Various bugs in reviewer and code-doc skills
- Test coverage improvements across multiple PRs

## [0.1.0] - 2024-10-24

### Added

**Initial public release with core SDD capabilities:**

**Core Workflow Skills:**
- `sdd-plan` - Specification creation from templates (simple/medium/complex/security)
- `sdd-next` - Task discovery and execution planning
- `sdd-update` - Progress tracking and journaling
- `sdd-validate` - Spec integrity validation with dependency checking
- `sdd-plan-review` - Multi-model spec review with external AI tools

**Documentation System:**
- `code-doc` - Multi-language codebase documentation generation
  - Support for Python, JavaScript/TypeScript, Go, HTML, CSS
  - AST-based analysis using tree-sitter
- `doc-query` - Documentation querying and search

**Testing Infrastructure:**
- `run-tests` - pytest integration with AI-assisted debugging

**CLI & Integration:**
- Unified `sdd` CLI consolidating all commands
- Claude Code plugin integration
- `/sdd-begin` command for resuming work
- `/sdd-setup` command for project configuration
- Session hooks for automatic workflow detection

**Spec Management:**
- JSON-based spec format with tasks, dependencies, and phases
- Spec folder structure (pending/active/completed/archived)
- Dependency graph visualization
- Task dependency tracking and validation
- Journal entries for decision tracking
- Verification task execution

**Features:**
- Template-based spec creation
- Basic spec rendering to markdown
- Telemetry and metrics collection
- Atomic task design principle

---

## Summary

**0.4.0** brings major workflow automation, AI integration, and developer experience improvements built on the solid foundation of 0.1.0. Key highlights include automatic time tracking, context monitoring, AI-enhanced rendering, code-doc integration, and the pending folder workflow for better spec organization.

**0.1.0** established the core spec-driven development methodology with comprehensive task management, documentation generation, and Claude Code integration.

---

For installation instructions, see [INSTALLATION.md](INSTALLATION.md).
For usage guide, see [README.md](README.md).
For architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
