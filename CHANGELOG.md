# Changelog

All notable changes to the SDD Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
