# sdd-common: Shared Utilities for Spec-Driven Development

Shared Python utilities used by all SDD skills (sdd plan, sdd next, sdd update).

## Purpose

Provides a single source of truth for common operations across the SDD skill family:
- JSON spec loading, saving, and validation
- Spec file parsing and frontmatter extraction
- Progress calculation and status updates
- Path discovery and validation
- Pretty console output formatting

## Modules

### `spec.py` - JSON Spec File Operations
- `load_json_spec(spec_id, specs_dir)` - Load JSON spec with error handling
- `save_json_spec(spec_id, specs_dir, spec_data)` - Atomic write with backup
- `backup_json_spec(spec_id, specs_dir)` - Create JSON spec backup
- `get_node(spec_data, node_id)` - Get specific node from hierarchy
- `update_node(spec_data, node_id, updates)` - Update node fields

**Features:**
- Atomic writes (temp file → rename)
- Automatic backups before save
- JSON schema validation
- Auto-updates `last_updated` timestamp

### `spec.py` - Additional Spec Operations
- `extract_frontmatter(spec_file)` - Extract metadata from JSON or Markdown specs

**Features:**
- JSON-first metadata extraction with Markdown fallback (legacy support)
- Automatic `spec_id` inference from filename when missing
- Graceful error reporting for missing/invalid specs
- Reusable helpers for JSON spec management

### `progress.py` - Progress Calculation
- `recalculate_progress(spec_data, node_id)` - Recursive progress update
- `update_parent_status(spec_data, node_id)` - Update parent chain
- `update_node_status(node)` - Set status based on children
- `get_progress_summary(spec_data, node_id)` - Get progress info
- `list_phases(spec_data)` - List all phases with progress
- `get_task_counts_by_status(spec_data)` - Count tasks by status

**Features:**
- Bottom-up recursive calculation
- Automatic status derivation (pending/in_progress/completed)
- Respects manually set statuses (blocked, etc.)
- Efficient parent chain updates

### `paths.py` - Path Discovery
- `find_specs_directory(provided_path)` - Discover specs directory
- `find_spec_file(spec_id, specs_dir)` - Find JSON spec file path
- `validate_path(path)` - Validate and normalize path
- `ensure_directory(path)` - Create directory if needed

**Features:**
- Multi-location search (cwd, ~/Documents/Sandbox, .claude/)
- Absolute path resolution
- Handles both files and directories
- Warns on multiple matches

### `printer.py` - Pretty Output
- `PrettyPrinter` class for consistent console output
- Methods: `action()`, `success()`, `info()`, `warning()`, `error()`, `header()`, `detail()`, `result()`

**Features:**
- ANSI color support (auto-disabled for non-TTY)
- Emoji indicators for quick scanning
- Verbose/quiet modes
- Indented detail output

## Usage Example

```python
# Import from claude_skills.common
from claude_skills.common import (
    load_json_spec,
    save_json_spec,
    recalculate_progress,
    find_specs_directory,
    PrettyPrinter
)

# Setup
printer = PrettyPrinter(verbose=True)
specs_dir = find_specs_directory()

# Load JSON spec
spec_data = load_json_spec("my-spec-2025", specs_dir)

# Update a task
from claude_skills.common.spec import update_node
update_node(spec_data, "task-1-1", {"status": "completed"})

# Recalculate progress
recalculate_progress(spec_data, "task-1-1")

# Save with backup
save_json_spec("my-spec-2025", specs_dir, spec_data, backup=True)

printer.success("Task updated and progress recalculated")
```

### `spec_validation.py` - Spec Document Validation
- `validate_spec_document(spec_file, check_state)` - Comprehensive spec validation
- `validate_anchor_placement(spec_content)` - Check task anchor placement
- `validate_task_details(spec_content)` - Validate task Changes/Reasoning sections
- `validate_required_sections(spec_content)` - Check for required spec sections
- `validate_phase_format(spec_content)` - Validate phase structure
- `parse_specification(spec_content)` - Parse spec into structured data
- `FileModification` - Data class for file modification info
- `VerificationStep` - Data class for verification steps

**Features:**
- Validates anchor placement in detailed sections (critical for `sdd next-task`)
- Checks for Changes and Reasoning in each task
- Verifies phase numbering and structure
- Validates frontmatter format
- Returns structured SpecValidationResult

### `hierarchy_validation.py` - JSON Spec Hierarchy Validation
- `validate_spec_hierarchy(spec_data)` - Comprehensive hierarchy validation
- `validate_structure(spec_data)` - Check JSON structure
- `validate_hierarchy(hierarchy)` - Validate hierarchy integrity
- `validate_nodes(hierarchy)` - Check node structure
- `validate_task_counts(hierarchy)` - Verify task counts
- `validate_dependencies(hierarchy)` - Check dependency references
- `validate_metadata(hierarchy)` - Validate node metadata

**Features:**
- Validates hierarchy parent/child relationships
- Checks task count accuracy
- Validates dependency references
- Ensures required fields present
- Returns structured JsonSpecValidationResult

### Auto-fix Functionality
Auto-fix functionality is available through the sdd CLI.
Use `sdd fix` to automatically repair common issues in JSON spec files.

### `reporting.py` - Validation Reports
- `generate_validation_report(result)` - Generate validation report
- `generate_combined_report(spec_result, json_result)` - Combined report

**Features:**
- Markdown-formatted reports
- Categorized issues by severity
- Actionable recommendations
- Summary statistics

## Dependencies

- **Python 3.6+** (no external packages required)
- Standard library only: `json`, `re`, `pathlib`, `datetime`, `shutil`

## Used By

- **sdd-plan commands** (`sdd create`, etc.) - Spec creation, state generation, and validation
- **sdd-plan-review commands** - Pre-review spec validation
- **sdd-next commands** (`sdd next-task`, `sdd verify-tools`, `sdd find-specs`, etc.) - Task discovery and execution planning
- **sdd-update commands** (`sdd update-status`, `sdd add-journal`, `sdd mark-blocked`, etc.) - Progress tracking and status updates

## Design Principles

1. **No external dependencies** - Uses Python standard library only
2. **Defensive coding** - Validates inputs, handles errors gracefully
3. **Atomic operations** - JSON spec updates are all-or-nothing
4. **Type hints** - All functions have proper type annotations
5. **Single responsibility** - Each module has one clear purpose

## Version

Current version: 1.0.0

## License

Same as parent project.
