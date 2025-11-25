# Changelog

All notable changes to the SDD Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and aspires to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (but probably doesn't).

# Unreleased

## [0.7.7] - 2025-11-25

### Added
- **Automatic documentation context in prepare-task**: `sdd prepare-task` now automatically populates `context.file_docs` with file-focused documentation when doc-query is available
  - Includes relevant files, dependencies, and provenance metadata (source, timestamp, git SHA, freshness)
  - Eliminates need to manually call doc-query helpers after running prepare-task
  - Falls back gracefully when documentation is unavailable or stale
  - Integration leverages `file_path` from task metadata for focused context
- **Call context integration**: New `get_call_context()` convenience function for retrieving callers/callees at module level
  - Simplifies documentation queries with direct access to call graph relationships
  - Integrated into doc helper for richer task context
- **Test coverage enhancements**:
  - Added comprehensive unit tests for `get_call_context()` and `get_test_context()`
  - Test function list extraction with coverage hint generation based on function coverage analysis
  - Enhanced test coverage for default context fields and doc integration
- **Git-based staleness detection**: Documentation freshness tracking using git commit SHAs
  - Automatic detection of stale documentation based on file modifications
  - Provenance metadata includes source, timestamp, and git SHA for auditing

### Changed
- Enhanced doc helper (`get_task_context_from_docs()`) to accept `file_path` and `spec_id` parameters for targeted documentation queries
- Updated `prepare_task()` to pass task metadata through to doc helper for richer context gathering
- Enhanced `doc_integration.py` with improved error handling and fallback mechanisms
- Added `doc_context` configuration settings to `sdd_config.json` template for fine-grained control

### Documentation
- Updated `analysis/prepare-task-default-context.md` with `context.file_docs` field documentation
- Updated `skills/sdd-next/SKILL.md` to document automatic file_docs inclusion in default workflow
- Added `context.file_docs` to Command Value Matrix in sdd-next skill documentation
- Added comprehensive test documentation for doc helper and integration

## [0.7.6] - 2025-11-23

### Changed

**Prepare-Task Default Context Enhancement:**
- Enhanced `sdd prepare-task` to provide comprehensive context in default output without requiring additional flags
  - Default output now includes: `context.previous_sibling`, `context.parent_task`, `context.phase`, `context.sibling_files`, `context.task_journal`, and `context.dependencies`
  - Eliminates need for separate `task-info` or `check-deps` calls in standard workflow
  - One-call workflow provides all information needed for task execution
  - Performance: <100ms median latency, <30ms overhead vs minimal context

### Added
- New test coverage for default context fields and JSON output formats
  - Added `test_prepare_task_context_includes_dependencies` to validate dependency structure
  - Added `test_prepare_task_json_output_pretty` and `test_prepare_task_json_output_compact` for serialization testing
  - Added `test_prepare_task_latency_budget_100ms` to enforce performance requirements

### Documentation
- Updated `docs/cli-reference.md` with one-call workflow documentation and enhanced default output examples
- Updated `docs/workflows.md` to demonstrate automatic context retrieval without additional commands
- Updated `skills/sdd-next/SKILL.md` with Command Value Matrix and anti-patterns for redundant command usage
- Added guidance on when to use `task-info`/`check-deps` (only for explicit overrides or special cases)

### Impact
- **Agent workflow simplification**: Reduces command calls per task from 3-4 to 1 (prepare-task only)
- **Token efficiency**: Eliminates redundant context gathering reducing token usage by ~30%
- **Faster execution**: Single command reduces round-trip latency by 60-200ms per task
- **Better defaults**: Context fields that were previously optional are now standard, improving agent decision-making

## [0.7.5] - 2025-11-23

### Added
- Provider security documentation set: `docs/security/PROVIDER_SECURITY.md`, `docs/security/THREAT_MODEL.md`, and `docs/security/TESTING.md`

### Changed
- Enforced read-only/tool-restriction policies across Claude, Gemini, Codex, Cursor Agent, and OpenCode providers with corresponding unit tests and CLI flag updates
- Hardened `ai_tools` integration tests by switching the mock binaries to JSON outputs and supporting float timeouts to better mirror real provider CLIs

## [0.7.1] - 2025-11-22

### Added

**Journal Accessibility Improvements:**
- Enhanced `get-journal` command with ergonomic positional syntax
  - New syntax: `sdd get-journal SPEC_ID [TASK_ID]` for cleaner command-line usage
  - Legacy `--task-id` flag still supported for backward compatibility
  - Improved help text with usage examples
- Journal data now included in `prepare-task` output at all verbosity levels
  - `context.task_journal` field added to both ESSENTIAL and STANDARD field sets
  - Accessible via `--quiet`, default, and `--verbose` modes
  - Provides integrated access to task journal without requiring separate `get-journal` calls

### Changed
- `prepare-task` context now includes task journal entries by default
  - Previously required verbose mode to access journal data
  - Now available at all verbosity levels for better workflow integration

### Documentation
- Added `docs/journal-accessibility-improvements.md` with usage examples and migration guide
- Documented positional vs flag-based syntax patterns
- Clarified when to use `get-journal` vs `prepare-task` for journal access

### Notes
- All changes maintain full backward compatibility
- Existing scripts using `--task-id` flag continue to work unchanged
- Output structure remains consistent across all verbosity levels

## [0.7.0] - 2025-11-21

### Added

**Doc Query Scope Command (PR #34):**
- New `sdd doc scope` command with preset-based workflows for planning and implementation
  - `--plan` preset: Module summary, complexity analysis, and architectural overview
  - `--implement` preset: Call graphs, callers, instantiated classes for implementation work
  - Optional `--function` parameter for targeted analysis in implement preset
  - JSON and Markdown output formats with verbosity filtering
- **Comprehensive Test Suite**: 25 passing tests (8 plan + 8 implement + 9 validation)
  - Basic output validation for both presets
  - JSON and markdown format testing
  - Error handling (missing module, invalid preset, nonexistent docs)
  - Edge cases (empty paths, whitespace, case sensitivity)
- **Documentation & Examples**:
  - 5 example files (plan/implement in JSON/Markdown + README)
  - Deterministic examples with commit hashes for reproducibility
  - Updated 3 skill documents (doc-query, sdd-plan, sdd-next)
  - Decision matrix for command selection guidance

**Analysis Integration in LLM Doc Gen (PR #33):**
- Integrated codebase analysis insights into LLM documentation generation
  - Automatic extraction of metrics from `documentation.json` (generated by doc-query)
  - Priority 1 metrics: Most-called functions, entry points, high-complexity functions, cross-module dependencies
  - Priority 2 metrics: Most-instantiated classes, fan-out analysis, integration points
- **Performance Features**:
  - Aggressive caching with freshness tracking (50-1000x speedup on warm cache)
  - Adaptive scaling based on codebase size (<100/100-500/>500 files)
  - Token budget management (250-450 tokens per generator type)
  - <2s total overhead with caching
- **Quality Improvements**:
  - A/B testing framework for measuring documentation quality (10-metric evaluation)
  - Typical improvement: 50-100% better accuracy and completeness
  - Reduced LLM hallucinations with data-driven context
  - Factual dependency mapping with reference counts
- **New Modules**:
  - `analysis_insights.py` (754 lines): Extraction and formatting logic
  - `performance_benchmark.py` (505 lines): Performance validation
  - `ab_testing.py` (637 lines): Quality measurement framework
- **Documentation**:
  - `docs/llm-doc-gen/ANALYSIS_INTEGRATION.md` (566 lines)
  - `docs/llm-doc-gen/BEST_PRACTICES.md` (795 lines)

### Changed

**Performance Optimizations for LLM-Doc-Gen (PR #32):**
- **49x speedup** in cross-reference resolution with indexed lookups (O(n²) → O(1))
- **3-4x faster** large codebase processing with parallel execution
- **10-20x faster** repeated runs with persistent caching
- **40% memory reduction** with streaming output and `__slots__`
- **Smart Filtering**: Three predefined profiles (FAST, BALANCED, COMPLETE)
  - `FileSizeFilter`, `FileCountLimiter`, `SamplingStrategy` classes
  - CLI flags: `--filter-mode`, `--max-file-size`, `--max-files-per-dir`, `--sample-rate`
- **Indexed Resolution**:
  - `SymbolIndex`: O(1) hash-based lookups for functions/classes/methods
  - `ImportIndex`: Bidirectional import tracking with transitive dependencies
  - `FastResolver`: Replaces nested loops with indexed lookups
- **Parallel Processing**:
  - `ParallelParser`: Multiprocessing.Pool-based concurrent AST parsing
  - Per-worker TreeCache to prevent conflicts
  - Auto-detection of CPU cores, CLI flags: `--parallel`, `--workers N`
- **Streaming & Caching**:
  - `StreamingJSONWriter`: Memory-efficient output for large codebases
  - NDJSON support with optional gzip compression
  - `PersistentCache`: SQLite-backed cache with SHA256-based keys
  - Automatic invalidation based on file modifications
- **Two-Tier Output**:
  - `SummaryGenerator`: Concise overviews (60-80% smaller)
  - `DetailWriter`: Comprehensive documentation
  - Backward compatible single-output mode preserved

**Code Organization (PR #31):**
- Integrated code-doc functionality as `llm_doc_gen.analysis` module
  - Moved `code_doc/` → `llm_doc_gen/analysis/` (14 files)
  - Net reduction of 442 lines across 68 files
- Enhanced documentation with real codebase statistics
  - Overview prompts include module complexity and language breakdown
  - Index pages display "Project Vital Signs" (LOC, file count, languages)
- Simplified default output directory from `./docs/llm-generated` to `./docs`
- Migrated tests to `tests/unit/llm_doc_gen/analysis/` (14 test files)
- Removed standalone code-doc agent and skill documentation

### Performance

**LLM-Doc-Gen Benchmarks (PR #32):**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cross-reference resolution | O(n²) nested loops | O(1) indexed lookups | **49x speedup** |
| Large codebase processing | Sequential, high memory | Parallel + streaming | **3-4x faster, 40% less memory** |
| Repeated runs (unchanged files) | Full re-parse | Cached results | **10-20x faster** |
| Output file size | Single large file | Two-tier or streaming | **60-80% smaller summaries** |

**Analysis Integration (PR #33):**
| Codebase Size | Cold Cache | Warm Cache | Total Overhead |
|--------------|-----------|-----------|----------------|
| Small (<100 files) | 0.3-0.5s | 0.001s | <0.6s |
| Medium (100-500) | 0.8-1.2s | 0.001s | <1.3s |
| Large (>500) | 1.5-2.0s | 0.001s | <2.1s |

### Notes
- Version 0.7.0 represents major feature additions and performance improvements
- All changes maintain backward compatibility
- Comprehensive test coverage: 100+ new tests across all features
- Four PRs merged: #31 (integration), #32 (performance), #33 (analysis), #34 (scope command)

## [0.6.8] - 2025-11-20

### Added

**LLM-Doc-Gen Skill (PR #30):**
- New `llm-doc-gen` skill for LLM-powered documentation generation
  - [BMAD](https://github.com/bmad-code-org/BMAD-METHOD)-style workflow orchestration with conditional execution and resumability
  - Multi-language codebase analysis (Python, JavaScript/TypeScript, Go, HTML, CSS)
  - AI-powered narrative documentation generation with contextual explanations
  - 7-section sharded documentation structure with auto-linking
  - Monorepo/monolith detection with project type classification
  - Resumable workflows with atomic state persistence
- **AI Integration:**
  - Multi-agent LLM consultation framework with parallel analysis
  - Sophisticated prompts for project overview, architecture, and component documentation
  - Support for Claude, GPT, Gemini, and other LLM providers
- **CLI Command**: `sdd llm-doc-gen` with `--resume` flag for workflow recovery
- **Documentation**:
  - Overview, Architecture, Components, Setup, Usage, Testing, and API sections
  - Index generation with automatic cross-linking
  - Project Vital Signs (LOC, file count, languages)
- **Testing**: 60+ unit tests, integration tests, end-to-end workflows, fidelity reviews

### Changed

**LLM-Doc-Gen Architecture Enhancement (PR #31):**
- Integrated code-doc functionality as `llm_doc_gen.analysis` module for better cohesion
  - Moved `code_doc/` → `llm_doc_gen/analysis/` (14 files including parsers)
  - Eliminated architectural duplication between standalone and integrated analysis
  - Net reduction of 442 lines across 68 files
- Enhanced documentation generation with real codebase statistics
  - Overview prompts now include module complexity and language breakdown
  - Index pages display "Project Vital Signs" (LOC, file count, primary languages)
  - Statistics flow: DocumentationGenerator → ProjectData → enhanced output
- Simplified default output directory from `./docs/llm-generated` to `./docs`

**Code Organization (PR #31):**
- Migrated all code-doc tests to `tests/unit/llm_doc_gen/analysis/` (14 test files)
- Updated imports across CLI, parsers, and test fixtures
- Removed standalone code-doc agent (`agents/code-doc.md`)
- Removed standalone code-doc skill documentation (`skills/code-doc/SKILL.md`, 28KB)

### Fixed
- Parameter naming corrections in DocumentationGenerator integration (PR #31)
  - Corrected `root_path` → `project_dir`
  - Corrected `project_version` → `version`
  - Fixed `save_json()` parameter passing

### Notes
- LLM-doc-gen provides narrative, contextual documentation vs code-doc's structural documentation
- All functionality preserved - code-doc reorganized for better architecture
- No breaking changes to CLI or skill interfaces
- Analysis capabilities now first-class component of llm-doc-gen
- Combined PRs add ~22k lines (llm-doc-gen) while removing ~2k lines (code-doc integration)

## [0.6.5] - 2025-11-19

### Added

**OpenCode AI Provider:**
- New AI provider for OpenCode AI models with Node.js wrapper integration
  - Full provider implementation supporting OpenCode AI's latest models
  - Node.js wrapper (`opencode_wrapper.js`) for SDK communication
  - Read-only security mode (blocks Write, Edit, Bash tools)
  - Allows Read, Grep, Glob, WebSearch, WebFetch, Task, Explore tools only
  - 360-second default timeout for extended reasoning tasks
  - Comprehensive unit test coverage (696 lines across all test scenarios)
  - Provider detection with Node.js runtime checks
  - Automatic npm dependency installation verification
- **Provider Documentation** - Complete guide at `docs/providers/OPENCODE.md`
  - Installation instructions with Node.js setup requirements
  - Configuration examples with API key management
  - Troubleshooting guide for common issues
  - Architecture overview and design patterns
- **Integration Features**:
  - Provider registry integration with lazy-loading
  - Availability checks with helpful error messages
  - Updated AI config templates with OpenCode defaults
  - CLI runner support: `python -m claude_skills.cli.provider_runner --provider opencode`

### Changed
- **AI Configuration Templates** - Updated default templates to include OpenCode provider configuration
- **Provider System** - Enhanced provider detection to support Node.js-based providers

### Notes
- Requires Node.js >= 18.x for OpenCode provider
- npm dependencies must be installed separately in the providers directory
- OpenCode CLI binary (`@opencode-ai/sdk`) should be installed globally
- Provider follows same security model as Claude provider (read-only tools only)

## [0.6.0] - 2025-11-18

### Added

**Three-Tier Verbosity System (#25):**
- New verbosity levels: QUIET, NORMAL, VERBOSE for controlling CLI output detail
  - QUIET: Minimal output with ~50% reduction, essential fields only
  - NORMAL: Balanced output (current default, backward compatible)
  - VERBOSE: Maximum output with debug information
- Field-level filtering with essential/standard field sets
- Applied across 100+ CLI commands
- CLI flags: `--quiet` and `--verbose`
- Configuration: `output.default_verbosity` in `.claude/sdd_config.json`

**AI Consultation Enhancements (#24):**
- Fallback and retry logic for AI tool consultations
- Per-invocation consultation limits via `consultation_limits.max_tools_per_run`
- ConsultationTracker for thread-safe tracking across parallel consultations
- Configurable retry/skip behavior based on error types (timeout, error, not_found, invalid_output)
- Skill-level default model configuration for all AI providers
- Tool priority and fallback order resolution
- Hybrid retry strategy (transient errors retry, permanent errors skip to next tool)

**Work Mode Configuration:**
- New `work_mode` field in `.claude/sdd_config.json`
  - "single": Plan and execute one task at a time with explicit approval (default)
  - "autonomous": Complete all tasks in current phase automatically within context limits
- Eliminates interruptions for mode selection
- Persistent preference across sessions
- New CLI command: `sdd get-work-mode`

**High-Level Task Operations:**
- Convenience operations in sdd-modify: update_task, update_metadata, add_verification, batch_update
- Eliminates need for custom Python scripts for bulk spec modifications
- Matches documented API for task-centric operations

### Changed

**Context Optimization (#26):**
- Enhanced context_utils.py with deduplication and file grouping
- Optimized sdd-next context gathering to reduce redundant CLI calls
- Improved dependency analysis in discovery.py
- Better performance for task preparation workflows

**User Guidance:**
- Enhanced error messages for blocked operations
- Improved hook feedback with modification workflow examples
- Better guidance when agents encounter CLI errors

**Documentation:**
- Added Journal vs Git History guidance
- Updated Deep Dive & Plan Approval section
- Multiple fidelity reviews and improvements
- Output field parity verification across commands

### Fixed
- Transcript path resolution issues
- Various small bugs and edge cases

### Performance
- ~50% output reduction in QUIET mode for token optimization
- Reduced redundant CLI calls in sdd-next context gathering
- Improved context preparation performance

### Notes
- Verbosity NORMAL mode maintains backward compatibility with previous output
- All existing tests passing
- Configuration changes are backward compatible
- AI consultation fallback respects tool availability and configuration

## [0.5.1] - 2025-11-11

### Added
- **Claude Provider** - New AI provider for Anthropic Claude models with read-only tool restrictions
  - Supports Sonnet 4.5 and Haiku 4.5 models
  - Read-only security mode (blocks Write, Edit, Bash tools)
  - Allows Read, Grep, Glob, WebSearch, WebFetch, Task, Explore tools only
  - Default 360-second timeout for extended reasoning
  - Comprehensive unit and integration test coverage (19 unit tests)
  - Provider detection with environment variable overrides
  - CLI runner support for testing: `python -m claude_skills.cli.provider_runner --provider claude`
- **Provider Abstraction Layer** - Unified interface for AI tool orchestration
  - Base module with clear contracts for tool orchestration
  - Provider registry with lazy-loading and availability checks
  - CLI runner with streaming support and error handling
  - Four provider implementations: Gemini, Codex, Cursor Agent, Claude
- `ai_config_setup.ensure_ai_config()` helper shared by setup workflows to seed `.claude/ai_config.yaml` with packaged defaults.
- `sdd fidelity-review` now auto-saves JSON reports when no output path is provided, making it easier to reuse results across tooling.
- Centralized setup templates bundled under `claude_skills.common.templates.setup` with a public `setup_templates` helper module for loading or copying packaged defaults.
- Unit and integration coverage that exercises the new setup templates, including `tests/unit/test_common/test_setup_templates.py` and the updated `skills-dev setup-permissions` integration flow.
- Provider abstraction documentation that explains the `ProviderContext` contract, registry/detector workflow, and how to exercise providers via the `provider_runner` CLI.

### Fixed
- **Corrected Model Names** - All provider implementations now use only real, CLI-supported models:
  - Gemini: gemini-2.5-pro, gemini-2.5-flash
  - Codex: gpt-5-codex, gpt-5-codex-mini, gpt-5
  - Cursor Agent: composer-1, gpt-5-codex
  - Claude: sonnet (Sonnet 4.5), haiku (Haiku 4.5)
- Updated CLI integration tests to opt into text output (`--no-json`) so completion prompts and human-facing messaging continue to be covered after switching to JSON-first defaults.
- Restored the packaged `.claude/settings.local.json` template so setup tooling and tests can copy the default permission manifest without errors.

### Changed
- **Provider Timeout Increased** - All AI provider default timeouts increased from 120s to 360s to support extended reasoning and complex tasks across Gemini, Codex, Cursor Agent, and Claude providers
- **Refactored ai_tools** - Now delegates to provider registry instead of direct tool invocation
- **Normalized ai_config** - Provider-centric configuration with standardized settings format
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
For architecture details, see [docs/architecture.md](docs/architecture.md).
