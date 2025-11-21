# Claude Skills - Python Package

Professional Python package implementing Spec-Driven Development (SDD) workflows and developer tools for Claude Code.

## 📚 Documentation

- **[Complete Installation Guide](../../INSTALLATION.md)** - Setup for both Python package and Claude Code integration
- **[Architecture Documentation](../../docs/architecture.md)** - System design and implementation details
- **[Best Practices](../../docs/BEST_PRACTICES.md)** - Development guidelines and patterns

**New user?** Start with [../../INSTALLATION.md](../../INSTALLATION.md) for complete setup instructions.

## Quick Installation

```bash
# From the package directory
cd ~/.claude/src/claude_skills
pip install -e .

# Verify installation
sdd --help
sdd doc --help
sdd test --help
sdd skills-dev --help
```

This installs the unified `sdd` CLI with subcommands:
- `sdd` – Core spec-driven development workflows
- `sdd doc` – Documentation generation and querying
- `sdd test` – Test execution, consultation, and discovery
- `sdd skills-dev` – Internal development utilities

## Available Commands

### Unified SDD CLI (`sdd`)

The unified SDD CLI consolidates all spec-driven development commands into a single interface:

```bash
# Spec Creation & Planning
sdd create "Feature Name" --template medium     # Create new specification
sdd analyze ./src                                # Analyze codebase for planning
sdd template list                                # List available templates

# Multi-Model Review
sdd review my-spec-001                           # Review spec with AI models
sdd list-review-tools                            # Check available AI CLI tools

# Spec Rendering
sdd render my-spec-001 --mode enhanced           # Render with AI enhancements
sdd render my-spec-001 --enhancement-level full  # Maximum detail rendering

# Task Discovery & Preparation
sdd next-task my-spec-001                        # Find next actionable task
sdd prepare-task my-spec-001 task-1-1            # Get full task context
sdd task-info my-spec-001 task-1-1               # Get task details
sdd check-deps my-spec-001 task-1-1              # Check task dependencies
sdd detect-project                               # Detect project type
sdd find-tests                                   # Find test files

# Progress Tracking
sdd update-status my-spec-001 task-1-1 completed # Update task status
sdd complete-task my-spec-001 task-1-1           # Complete with auto-journaling
sdd add-journal my-spec-001 --title "Decision"   # Add journal entry
sdd mark-blocked my-spec-001 task-1-2 "Reason"   # Mark task as blocked
sdd activate-spec my-spec-001                    # Move from pending to active
sdd complete-spec my-spec-001                    # Move to completed
sdd status-report my-spec-001                    # Generate status report
sdd list-specs --status active                   # List specs by status

# Validation & Fixing
sdd validate my-spec-001                         # Validate spec (accepts spec-id or .json path)
sdd fix my-spec-001                              # Auto-fix validation issues
sdd report my-spec-001 --output report.md        # Generate validation report
sdd stats my-spec-001                            # Show spec statistics
sdd analyze-deps my-spec-001                     # Analyze dependencies

# Context Monitoring
sdd context                                      # Show current session token usage
sdd session-marker start                         # Mark session start

# View all commands
sdd --help                                       # Complete command reference
```


**Key Benefits**:
- ✅ Single unified command (`sdd`) with comprehensive subcommands
- ✅ Consistent interface and flags across all operations
- ✅ Better command discovery via `sdd --help`
- ✅ Faster workflow with shorter command names

**Note:** The CLI is actively evolving. Run `sdd --help` for the complete, up-to-date command list. The examples above show the most commonly used commands.

### Documentation CLI (`sdd doc`)
```bash
sdd doc generate ./src --output-dir ./docs
sdd doc find-class ClassName
sdd doc stats --json
sdd doc callers "function_name"
sdd doc call-graph "entry_point"
```

### Testing CLI (`sdd test`)
```bash
sdd test run --preset quick
sdd test check-tools --json
sdd test consult assertion --error "Expected 1 == 2" --hypothesis "off-by-one"
```

### Skills Development CLI (`sdd skills-dev`)
```bash
sdd skills-dev gendocs -- sdd-validate --sections commands
sdd skills-dev start-helper -- check-permissions .
sdd skills-dev setup-permissions -- update .
```

## Development

### Running Tests

```bash
# From the package directory
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
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
├── llm_doc_gen/        # LLM documentation generation
│   └── analysis/       # Code analysis module (formerly code_doc)
└── tests/              # Test suite
```

## Integration with Claude Code

This package is part of the larger Claude Skills ecosystem located at `~/.claude/`:

```
~/.claude/
├── skills/           # Claude Code skills (auto-detected)
├── commands/         # Slash commands (/sdd-begin)
├── hooks/            # Event hooks (session-start, pre-tool-use)
└── src/
    └── claude_skills/  ← This package
```

**Skills** use these CLI tools to:
- Create specifications (sdd-plan skill)
- Find next tasks (sdd next)
- Track progress (sdd update)
- Validate specs (sdd validate)
- Generate and query documentation (llm-doc-gen, doc-query)
- Run and debug tests (run-tests)

See [../../README.md](../../README.md) for how everything works together.

## Benefits

✅ **Professional Package** - Standard Python package structure
✅ **IDE Support** - Full autocomplete, go-to-definition, type checking
✅ **Unified CLI** - Use `sdd next` instead of `sdd-next` (simpler, consistent)
✅ **Testable** - Proper test structure and imports
✅ **Extensible** - Easy to add new commands and tools
✅ **Well-Documented** - Comprehensive guides and examples
