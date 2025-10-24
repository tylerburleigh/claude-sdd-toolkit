# Claude Skills - Python Package

Professional Python package implementing Spec-Driven Development (SDD) workflows and developer tools for Claude Code.

## 📚 Documentation

- **[Complete Installation Guide](../../INSTALLATION.md)** - Setup for both Python package and Claude Code integration
- **[Getting Started](GETTING_STARTED.md)** - Quick start guide and first workflows
- **[Workflows](docs/workflows.md)** - Step-by-step guides for common tasks
- **[CLI Reference](docs/cli-reference.md)** - All CLI commands (if exists)

**New user?** Start with [../../INSTALLATION.md](../../INSTALLATION.md) for complete setup instructions.

## Quick Installation

```bash
# From the package directory
cd ~/.claude/src/claude_skills
pip install -e .

# Verify installation
sdd --help
doc --help
test --help
skills-dev --help
```

This installs the unified CLIs:
- `sdd` – Spec-driven development workflows
- `doc` – Documentation generation and querying
- `test` – Test execution, consultation, and discovery
- `skills-dev` – Internal development utilities (wrapping legacy tools)

## Available Commands

### Unified SDD CLI (`sdd`)

**⭐ All 60 SDD commands now use a single CLI: `sdd`**

The unified SDD CLI consolidates all spec-driven development commands:

```bash
# Spec Creation & Planning (sdd-plan: 3 commands)
sdd create "Feature Name" --template medium     # Create new specification
sdd analyze ./src                                # Analyze codebase for planning
sdd template list                                # List available templates

# Multi-Model Review (sdd-plan-review: 2 commands)
sdd review specs/active/my-spec.json             # Review spec with AI models
sdd list-review-tools                            # Check available AI CLI tools

# Task Discovery (sdd-next: 19 commands)
sdd next-task SPEC_ID                            # Find next actionable task
sdd prepare-task SPEC_ID TASK_ID                 # Prepare task for execution
sdd task-info SPEC_ID TASK_ID                    # Get task details
sdd check-deps SPEC_ID TASK_ID                   # Check task dependencies
sdd detect-project                               # Detect project type
sdd find-tests                                   # Find test files

# Progress Tracking (sdd-update: 31 commands)
sdd update-status SPEC_ID TASK_ID completed      # Update task status
sdd add-journal SPEC_FILE --title "Note"         # Add journal entry
sdd mark-blocked SPEC_ID TASK_ID "Reason"        # Mark task as blocked
sdd complete-spec SPEC_ID                        # Mark spec as complete
sdd status-report SPEC_ID                        # Generate status report
sdd query-tasks SPEC_ID --status pending         # Query tasks
sdd list-phases SPEC_ID                          # List all phases

# Validation & Fixing (sdd-validate: 5 commands)
sdd validate SPEC_FILE                           # Validate JSON spec
sdd fix SPEC_FILE                                # Auto-fix validation issues
sdd report SPEC_FILE --output report.md          # Generate validation report
sdd stats SPEC_FILE                              # Show spec statistics
sdd analyze-deps SPEC_FILE                       # Analyze dependencies

# View all commands
sdd --help
```

**📖 Migration Guide**: See [SDD_MIGRATION.md](./SDD_MIGRATION.md) for detailed migration instructions from old CLIs (`sdd-next`, `sdd-update`, etc.) to the unified `sdd` command.

**Key Benefits**:
- ✅ Single command to remember (`sdd`)
- ✅ 60 commands across 5 modules
- ✅ Consistent interface and flags
- ✅ Better command discovery
- ✅ Faster workflow

### Documentation CLI (`doc`)
```bash
doc generate ./src --output-dir ./docs
doc find-class ClassName
doc stats --json
```

### Testing CLI (`test`)
```bash
test run --preset quick
test check-tools --json
test consult assertion --error "Expected 1 == 2" --hypothesis "off-by-one"
```

### Skills Development CLI (`skills-dev`)
```bash
skills-dev gendocs -- sdd-validate --sections commands
skills-dev start-helper -- check-permissions .
skills-dev setup-permissions -- update .
```

## Development

### Running Tests

```bash
cd /Users/tylerburleigh/Documents/private/.claude/src/claude_skills
pytest tests/ -v
```

### Project Structure

```
claude_skills/
├── common/              # Shared utilities (formerly sdd_common)
│   ├── paths.py        # Path discovery and validation
│   ├── state.py        # State file operations
│   ├── spec.py         # Spec parsing utilities
│   └── ...
├── sdd_next/           # Next task discovery
│   ├── cli.py          # Command-line interface
│   ├── discovery.py    # Task discovery logic
│   └── ...
├── sdd_plan/           # Specification creation
├── sdd_update/         # Progress tracking
├── sdd_validate/       # Validation tools
├── doc_query/          # Documentation queries
├── run_tests/          # Test execution
├── code_doc/           # Documentation generation
└── tests/              # Test suite
```

## Integration with Claude Code

This package is part of the larger Claude Skills ecosystem located at `~/.claude/`:

```
~/.claude/
├── skills/           # Claude Code skills (auto-detected)
├── commands/         # Slash commands (/sdd-start)
├── hooks/            # Event hooks (session-start, pre-tool-use)
└── src/
    └── claude_skills/  ← This package
```

**Skills** use these CLI tools to:
- Create specifications (sdd-plan skill)
- Find next tasks (sdd next)
- Track progress (sdd update)
- Validate specs (sdd validate)
- Generate and query documentation (code-doc, doc-query)
- Run and debug tests (run-tests)

See [../../README.md](../../README.md) for how everything works together.

## Benefits

✅ **Professional Package** - Standard Python package structure
✅ **IDE Support** - Full autocomplete, go-to-definition, type checking
✅ **Unified CLI** - Use `sdd next` instead of `sdd-next` (simpler, consistent)
✅ **Testable** - Proper test structure and imports
✅ **Extensible** - Easy to add new commands and tools
✅ **Well-Documented** - Comprehensive guides and examples
