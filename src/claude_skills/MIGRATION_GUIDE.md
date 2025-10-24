# Unified CLI Migration Guide

## Overview

All developer tooling in `claude_skills` is consolidated into unified CLIs:
- **SDD (Spec-Driven Development)**: `sdd` - Single entry point for all spec-driven development workflows
- **Documentation**: `doc` - Codebase documentation generation and querying
- **Testing**: `test` - Test discovery, execution, and AI-assisted debugging
- **Skills Development**: `skills-dev` - Internal development utilities

This guide summarizes the transition from legacy standalone commands to the new unified CLIs.

## SDD CLI Migration (⚠️ DEPRECATED Commands)

The standalone SDD commands (`sdd-next`, `sdd-update`, `sdd-validate`) are **deprecated** and will be removed in v3.0.0. All functionality is now available through the unified `sdd` CLI.

### SDD Command Mapping

| Old Command | New Command(s) | Notes |
|-------------|----------------|-------|
| `sdd-next verify-tools` | `sdd verify-tools` | ✅ Direct replacement |
| `sdd-next find-specs` | `sdd find-specs` | ✅ Direct replacement |
| `sdd-next <spec-id>` | `sdd next-task <spec-id>` | ✅ Find next actionable task |
| `sdd-next list-tasks <spec-id>` | `sdd list-tasks <spec-id>` | ✅ Direct replacement |
| `sdd-next show-context <spec-id> <task-id>` | `sdd show-context <spec-id> <task-id>` | ✅ Direct replacement |
| `sdd-update status <spec-id> <task-id> <status>` | `sdd update-status <spec-id> <task-id> <status>` | ✅ Direct replacement |
| `sdd-update journal <spec-id> <task-id>` | `sdd add-journal <spec-id> <task-id>` | ✅ Direct replacement |
| `sdd-update blocked <spec-id> <task-id>` | `sdd mark-blocked <spec-id> <task-id>` | ✅ Direct replacement |
| `sdd-update unblock <spec-id> <task-id>` | `sdd unblock-task <spec-id> <task-id>` | ✅ Direct replacement |
| `sdd-update move <spec-id> <folder>` | `sdd move-spec <spec-id> <folder>` | ✅ Direct replacement |
| `sdd-update complete <spec-id>` | `sdd complete-spec <spec-id>` | ✅ Direct replacement |
| `sdd-update time <spec-id> <task-id>` | `sdd track-time <spec-id> <task-id>` | ✅ Direct replacement |
| `sdd-update report <spec-id>` | `sdd status-report <spec-id>` | ✅ Direct replacement |
| `sdd-update query <spec-id>` | `sdd query-tasks <spec-id>` | ✅ Direct replacement |
| `sdd-validate <spec-file>` | `sdd validate <spec-file>` | ✅ Direct replacement |
| `sdd-validate --fix <spec-file>` | `sdd fix <spec-file>` | ✅ Auto-fix issues |
| `sdd-validate --report <spec-file>` | `sdd report <spec-file>` | ✅ Validation report |

**View all SDD commands:**
```bash
sdd --help          # Core SDD commands
sdd doc --help      # Documentation commands (nested)
sdd test --help     # Testing commands (nested)
sdd skills-dev --help  # Development utilities (nested)
```

**Note**: The `sdd` CLI also provides nested access to `doc`, `test`, and `skills-dev` commands:
- `sdd doc generate` is equivalent to `doc generate`
- `sdd test run` is equivalent to `test run`
- `sdd skills-dev gendocs` is equivalent to `skills-dev gendocs`

You can use whichever style you prefer.

## Documentation, Testing, and Skills-Dev Migration

### Migration Summary

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `code-doc generate <dir>` | `doc generate <dir>` | ✅ Direct replacement |
| `code-doc analyze <dir>` | `doc analyze <dir>` | ✅ Direct replacement |
| `code-doc validate <file>` | `doc validate-json <file>` | ✅ Direct replacement |
| `doc-query find-class <name>` | `doc find-class <name>` | ✅ Direct replacement |
| `doc-query search <query>` | `doc search <query>` | ✅ Direct replacement |
| `doc-query stats` | `doc stats` | ✅ Direct replacement |
| `run-tests run --preset <name>` | `test run --preset <name>` | ✅ Direct replacement |
| `run-tests check-tools` | `test check-tools` | ✅ Direct replacement |
| `run-tests consult` | `test consult` | ✅ Direct replacement |
| `run-tests discover <path>` | `test discover <path>` | ✅ Direct replacement |
| `claude-skills-gendocs <skill>` | `skills-dev gendocs -- <skill>` | ✅ Pass arguments after `--` |
| `sdd-start-helper <cmd>` | `skills-dev start-helper -- <cmd>` | ✅ Pass arguments after `--` |
| `setup-project-permissions <cmd>` | `skills-dev setup-permissions -- <cmd>` | ✅ Pass arguments after `--` |

## Quick Start

### View all available commands
```bash
sdd --help        # SDD commands
doc --help        # Documentation commands
test --help       # Testing commands
skills-dev --help # Development utilities
```

### Get help for a specific command
```bash
sdd next-task --help
sdd update-status --help
doc generate --help
test run --help
skills-dev gendocs -- --help
```

## Key Benefits

1. **Fewer Entry Points**: Four unified CLIs (`sdd`, `doc`, `test`, `skills-dev`) replace 10+ separate commands.
2. **Consistent Interface**: Shared global flags (`--quiet`, `--json`, `--verbose`, `--no-color`, `--debug`).
3. **Flat Command Structure**: All subcommands are top-level for quick access.
4. **Graceful Transition**: Legacy entry points emit migration instructions.
5. **Clear Organization**: Commands grouped by domain (specs, docs, tests, development).

## Global Flags

All unified CLIs now support these global flags:

- `--quiet, -q`: Suppress non-essential output
- `--json`: Output in JSON format (when supported)
- `--verbose, -v`: Show detailed output
- `--no-color`: Disable colored output
- `--debug`: Enable debug mode with full stack traces

## Examples

### SDD Workflow
```bash
# Find next task to work on
sdd next-task my-feature-2025

# Update task status
sdd update-status my-feature-2025 task-1-1 completed

# Add journal entry for a task
sdd add-journal my-feature-2025 task-1-1 --entry "Implemented user authentication"

# Mark a task as blocked
sdd mark-blocked my-feature-2025 task-1-2 --reason "Waiting for API access"

# Validate a spec file
sdd validate specs/active/my-feature-2025.json

# Auto-fix spec issues
sdd fix specs/active/my-feature-2025.json

# Get status report
sdd status-report my-feature-2025

# Move spec to completed
sdd move-spec my-feature-2025 completed
```

### Documentation Workflow
```bash
# Generate documentation
doc generate ./src --output-dir ./docs

# Query documentation
doc find-class MyClass
doc stats --json
```

### Testing Workflow
```bash
# Run quick preset
test run --preset quick

# Check external tools
test check-tools --json

# Consult AI for failure triage
test consult assertion --error "Expected 1 == 2" --hypothesis "Off-by-one"
```

### Skills Development Utilities
```bash
# Generate CLI docs for skills
skills-dev gendocs -- sdd-validate --sections commands

# Check SDD start helper permissions
skills-dev start-helper -- check-permissions .

# Configure project permissions
skills-dev setup-permissions -- update .
```

## Legacy Commands

### Deprecated SDD Commands (⚠️ Remove by v3.0.0)

The following standalone SDD commands are **deprecated** and will be removed in v3.0.0:
- `sdd-next` → Use `sdd next-task`, `sdd verify-tools`, `sdd find-specs`, etc.
- `sdd-update` → Use `sdd update-status`, `sdd add-journal`, `sdd mark-blocked`, etc.
- `sdd-validate` → Use `sdd validate`, `sdd fix`, `sdd report`, etc.

### Other Deprecated Commands

The legacy tool commands (`code-doc`, `doc-query`, `run-tests`, `claude-skills-gendocs`, `sdd-start-helper`, `setup-project-permissions`) now exit with migration instructions and will be removed in the next major release.

**Migration recommended**: Update automation, scripts, and documentation to use the unified CLIs: `sdd`, `doc`, `test`, and `skills-dev`.

## Troubleshooting

### Command not found
If the new commands are not available, reinstall the package:
```bash
pip install -e .
```

### Getting help
All commands support `--help`:
```bash
sdd --help
doc --help
test --help
skills-dev --help
```

## What Changed Internally?

- **Architecture**: Refactored from multiple standalone CLIs to plugin-based unified CLIs (`sdd`, `doc`, `test`, `skills-dev`).
- **Code Organization**: New modules under `claude_skills/cli/sdd/` consolidate SDD commands; other CLIs follow the same pattern.
- **Registration System**: Commands register via `register_*()` functions for each domain.
- **Printer Pattern**: All handlers receive a `PrettyPrinter` instance instead of relying on module-level globals.
- **SDD Unification**: `sdd-next`, `sdd-update`, and `sdd-validate` commands merged into single `sdd` entry point.
- **Backward Compatibility**: Legacy commands now exit with migration guidance instead of running silently.

## Questions?

For issues or questions, please file an issue at the project repository.
