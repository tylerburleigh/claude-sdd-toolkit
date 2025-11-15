# SDD Verbosity System Documentation

## Overview

The SDD toolkit implements a comprehensive verbosity system that controls the level of detail in command output. This system is particularly valuable for AI agents and automation workflows that need to minimize token usage while maintaining essential information.

## Verbosity Levels

### QUIET Mode (`--quiet`)
- **Purpose**: Minimal output for automation and AI workflows
- **Fields**: Only essential fields required for downstream processing
- **Behavior**:
  - Omits empty values (empty lists, dicts, null values)
  - Filters out non-essential metadata
  - Reduces output by 20-60% depending on command
- **Use Cases**: CI/CD pipelines, AI agents, scripts

### NORMAL Mode (default)
- **Purpose**: Balanced output for human and automated use
- **Fields**: Essential + standard fields
- **Behavior**:
  - Includes commonly needed fields
  - Omits debug/verbose-only information
  - Default when no flags specified
- **Use Cases**: Interactive CLI usage, general scripting

### VERBOSE Mode (`--verbose`)
- **Purpose**: Complete output for debugging and inspection
- **Fields**: All available fields including empty values
- **Behavior**:
  - Includes all metadata and debug information
  - Preserves empty fields for completeness
  - Maximum information density
- **Use Cases**: Debugging, development, troubleshooting

## Command Coverage

The verbosity system is implemented across all major SDD command categories:

### Core Workflow Commands (sdd_core)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `progress` | spec_id, total_tasks, completed_tasks, percentage, current_phase | + title, status, remaining_tasks, node_id, type | Progress tracking |
| `prepare-task` | success, task_id, task_data, dependencies | + repo_root, needs_branch_creation, dirty_tree_status, needs_commit_cadence, spec_complete | Task preparation |
| `query-tasks` | id, title, type, status, parent | + completed_tasks, total_tasks, metadata | Task querying |
| `list-specs` | spec_id, status, title, progress_percentage | + total_tasks, completed_tasks, current_phase, version, created_at, updated_at | Spec listing |
| `validate` | status | + spec_id, errors, warnings, auto_fixable_issues, schema | Validation |

### Documentation Commands (doc_query)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `search` | matches, total_matches | + query, search_time_ms | Code search |
| `get-function` | name, signature, file_path | + docstring, line_number, complexity | Function lookup |
| `get-class` | name, file_path | + docstring, methods, base_classes | Class lookup |
| `list-modules` | modules, total_modules | + filter_applied, scan_time_ms | Module listing |
| `stats` | total_functions, total_classes, total_modules | + language_breakdown, complexity_stats | Statistics |
| `analyze-imports` | imports, external_imports | + import_graph, circular_dependencies, unused_imports | Import analysis |

### Update Commands (sdd_update)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `update-status` | success, task_id, new_status | + old_status, updated_at, spec_id, status_note | Status updates |
| `mark-blocked` | success, task_id, blocker_id | + blocker_description, updated_at | Block tracking |
| `unblock-task` | success, task_id | + removed_blockers, updated_at | Unblocking |
| `add-journal` | success, entry_id | + spec_id, timestamp, entry_type, title, content | Journaling |
| `add-revision` | success, revision_id | + spec_id, timestamp, content | Revisions |

### Code Documentation (code_doc)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `generate` | status, project, output_dir | + format | Doc generation |
| `validate` | status, message | + schema | Schema validation |
| `analyze` | status, project, statistics | + statistics | Code analysis |

### Testing Commands (run_tests)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `check-tools` | available_count, available_tools | + tools | Tool availability |
| `consult` | status, message | + message | Error responses |
| `run` | status, message | + message | Error responses |

### Context Tracking (context_tracker)
| Command | Essential Fields | Standard Fields | Notes |
|---------|-----------------|-----------------|-------|
| `context` | context_percentage_used | + context_length, context_percentage, max_context, input_tokens, output_tokens, cached_tokens, total_tokens, transcript_path | Context metrics |

## Usage Examples

### Basic Usage

```bash
# QUIET mode - minimal output
sdd progress my-spec --json --quiet

# NORMAL mode - default
sdd progress my-spec --json

# VERBOSE mode - complete output
sdd progress my-spec --json --verbose
```

### Output Comparison

```json
// QUIET mode
{
  "spec_id": "my-spec",
  "total_tasks": 23,
  "completed_tasks": 15,
  "percentage": 65,
  "current_phase": "phase-2"
}

// NORMAL mode
{
  "spec_id": "my-spec",
  "title": "My Specification",
  "status": "in_progress",
  "total_tasks": 23,
  "completed_tasks": 15,
  "percentage": 65,
  "remaining_tasks": 8,
  "current_phase": "phase-2",
  "node_id": "spec-root",
  "type": "spec"
}

// VERBOSE mode
{
  "spec_id": "my-spec",
  "title": "My Specification",
  "status": "in_progress",
  "total_tasks": 23,
  "completed_tasks": 15,
  "percentage": 65,
  "remaining_tasks": 8,
  "current_phase": "phase-2",
  "node_id": "spec-root",
  "type": "spec",
  "phases": [],
  "metadata": {},
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-15T21:00:00Z"
}
```

## AI Agent Integration

### Recommended Patterns

For AI agents and automation workflows, use QUIET mode to minimize token consumption:

```bash
# Query next task with minimal output
sdd prepare-task my-spec --json --quiet

# Check progress with essential fields only
sdd progress my-spec --json --quiet

# Search with minimal metadata
sdd doc-query search "function_name" --json --quiet
```

### Token Savings

Typical token reduction in QUIET mode:
- **doc_query commands**: 40-60% reduction
- **sdd_core commands**: 25-40% reduction
- **sdd_update commands**: 20-35% reduction

Example: A `prepare-task` response that uses 500 tokens in VERBOSE mode typically uses only 300-350 tokens in QUIET mode.

## Best Practices

### For AI Agents

1. **Always use `--quiet` with `--json`** for automated workflows
2. **Use NORMAL mode** when human review is expected
3. **Use VERBOSE mode** only for debugging or when complete context is needed

### For Scripts

```bash
# Good: Minimal output for script processing
result=$(sdd query-tasks my-spec --status pending --json --quiet)

# Good: Parse essential fields only
spec_id=$(echo "$result" | jq -r '.spec_id')
tasks=$(echo "$result" | jq -r '.total_tasks')

# Avoid: Verbose output in automation
# sdd query-tasks my-spec --status pending --json --verbose
```

### For Interactive Use

```bash
# Good: Use defaults (NORMAL mode) for human-readable output
sdd progress my-spec

# Good: Use VERBOSE when troubleshooting
sdd progress my-spec --verbose

# Good: Use QUIET when piping to other commands
sdd list-specs --json --quiet | jq '.[] | select(.status == "in_progress")'
```

## Field Set Design

All commands follow consistent patterns for field classification:

### Essential Fields
- Required for downstream processing
- Never empty/null in valid responses
- Core identification and status information
- Examples: `spec_id`, `task_id`, `status`, `success`

### Standard Fields
- Commonly needed for typical use cases
- May be empty but provide useful context
- Includes timestamps, counts, and basic metadata
- Examples: `title`, `updated_at`, `total_tasks`, `percentage`

### Verbose-Only Fields
- Debug information and complete metadata
- Often empty in normal operation
- Detailed internal state
- Examples: `metadata`, `debug_info`, `cache_stats`

## Configuration

### Global Settings

Verbosity can be configured in `.claude/settings.json`:

```json
{
  "sdd": {
    "verbosity": "quiet"
  }
}
```

Command-line flags override configuration:

```bash
# Override quiet default with verbose
sdd progress my-spec --verbose
```

### Environment Variables

```bash
# Set default verbosity level
export SDD_VERBOSITY=quiet

# Run command
sdd progress my-spec --json
```

## Implementation Details

### Architecture

The verbosity system is implemented through:

1. **Field Sets**: Pre-defined sets in `output_utils.py`
   - `COMMAND_NAME_ESSENTIAL`: Minimal fields
   - `COMMAND_NAME_STANDARD`: Essential + common fields

2. **Filtering Function**: `prepare_output()` in `output_utils.py`
   - Applies field sets based on verbosity level
   - Handles empty value omission in QUIET mode

3. **CLI Integration**: Global `--quiet`/`--verbose` flags
   - Parsed by `VerbosityLevel.from_args()`
   - Stored in `args.verbosity_level`

### Adding Verbosity to New Commands

```python
from claude_skills.cli.sdd.output_utils import prepare_output

# Define field sets
MY_COMMAND_ESSENTIAL = {'id', 'status', 'result'}
MY_COMMAND_STANDARD = {'id', 'status', 'result', 'timestamp', 'metadata'}

# In command handler
def cmd_my_command(args, printer):
    # ... command logic ...

    if args.json:
        output = prepare_output(
            data,
            args,
            MY_COMMAND_ESSENTIAL,
            MY_COMMAND_STANDARD
        )
        print(json.dumps(output, indent=2))
```

## Testing

Comprehensive test suites verify:

1. **Field Filtering**: `tests/test_cli_verbosity.py`
2. **Doc Query Integration**: `tests/test_doc_query_verbosity.py`
3. **Output Reduction**: `tests/test_verbosity_output_reduction.py`

Run tests:

```bash
# All verbosity tests
pytest tests/test_*verbosity*.py -v

# Measure output reduction
pytest tests/test_verbosity_output_reduction.py -v -s
```

## Troubleshooting

### Command not respecting verbosity

Check if command implements JSON output:
```bash
sdd my-command --help | grep -i json
```

Some commands (document generators, action commands) may not support JSON output.

### Unexpected fields in QUIET mode

Verify field sets are correctly defined in `output_utils.py`. Essential fields should be a subset of standard fields:

```python
assert MY_COMMAND_ESSENTIAL.issubset(MY_COMMAND_STANDARD)
```

### Empty output in QUIET mode

QUIET mode omits empty values. If all non-essential fields are empty, output may be minimal. This is expected behavior.

## Migration Guide

### Upgrading from Pre-Verbosity Versions

Old behavior (pre-verbosity):
```bash
sdd progress my-spec --json
# Returns all fields always
```

New behavior (with verbosity):
```bash
# Same command, same default output (NORMAL mode)
sdd progress my-spec --json

# Opt into minimal output
sdd progress my-spec --json --quiet

# Opt into complete output
sdd progress my-spec --json --verbose
```

**Breaking Changes**: None. Default behavior matches pre-verbosity output.

## Related Documentation

- [CLI Options](./cli-options.md) - Global CLI flags
- [JSON Output](./json-output.md) - JSON output format specifications
- [AI Agent Guide](./ai-agents.md) - Best practices for AI integration
- [API Reference](./api-reference.md) - Complete command reference

## Contributing

When adding new commands:

1. Define field sets in `output_utils.py`
2. Use `prepare_output()` in command handler
3. Add tests in `tests/test_*_verbosity.py`
4. Document field sets in this file
5. Verify output reduction targets (20-60%)

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.
