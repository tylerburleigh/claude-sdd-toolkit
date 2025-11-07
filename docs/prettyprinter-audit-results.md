# PrettyPrinter Usage Audit Results

**Date:** 2025-11-06
**Task:** task-1-1-1 - Search for all PrettyPrinter instantiations and method calls
**Spec:** AI-Agent-First TUI Upgrade (tui-upgrade-2025-11-06-001)

---

> **⚠️ IMPORTANT NOTE - BACKGROUND RESEARCH ONLY**
>
> This audit was conducted during Phase 1 investigation (task-1-1-1) to understand how terminal output is currently handled in the codebase.
>
> **This analysis informed the decision to adopt Rich library for the new TUI system.**
>
> **Actual Implementation:** Based on this audit showing no existing Rich dependency and extensive PrettyPrinter usage, the decision was made to introduce Rich as a new dependency and create a modern `Ui` interface with Rich-powered features (tables, trees, progress bars, panels).
>
> **PrettyPrinter Status:** The existing `PrettyPrinter` class (49 files) remains unchanged for backward compatibility.
>
> See [TUI Implementation Decision Record](./tui-implementation-decision.md) for the full rationale.

---

## Executive Summary

**CRITICAL FINDING:** The codebase does NOT use Rich library's PrettyPrinter at all. Instead, it uses a custom lightweight `PrettyPrinter` class defined in `common/printer.py`.

**Key Discoveries:**
- ✅ 49 files reference "PrettyPrinter"
- ✅ All references are to the custom `claude_skills.common.PrettyPrinter` class
- ❌ ZERO imports from `rich.pretty` or any Rich library components
- ❌ Rich is NOT listed as a dependency in `pyproject.toml`
- ✅ Custom PrettyPrinter is already agent-friendly with simple, semantic methods

---

## Import Patterns

### Custom PrettyPrinter Import Pattern

**Primary import pattern found:**
```python
from claude_skills.common import PrettyPrinter
```

**Locations:** 49 files across the codebase

**Common usage locations:**
- CLI modules (all command-line interfaces)
- Test files (integration and unit tests)
- Workflow modules (sdd-update, sdd-plan, sdd-next, etc.)
- AI consultation modules
- Helper scripts

### Rich Library Imports

**Search results:**
- `from rich.pretty import PrettyPrinter` - **0 matches**
- `from rich` (any component) - **0 matches**
- `import rich` - **0 matches**

**Conclusion:** Rich library is not used anywhere in the codebase.

---

## Custom PrettyPrinter Implementation

### Source File
**Location:** `src/claude_skills/claude_skills/common/printer.py`

### Class Definition
```python
class PrettyPrinter:
    """Utility for consistent, pretty console output optimized for Claude Code."""

    def __init__(self, use_color=True, verbose=False, quiet=False):
```

### Available Methods

| Method | Purpose | Output Channel |
|--------|---------|----------------|
| `action(msg)` | Current action being performed | stdout |
| `success(msg)` | Completed action | stdout |
| `info(msg)` | Context/details (verbose only) | stdout |
| `warning(msg)` | Non-blocking issue | stderr |
| `error(msg)` | Blocking issue | stderr |
| `header(msg)` | Section header | stdout |
| `detail(msg, indent=1)` | Indented detail line | stdout |
| `result(key, value, indent=0)` | Key-value result | stdout |
| `blank()` | Blank line | stdout |
| `item(msg, indent=0)` | List item | stdout |

### Key Features

**1. Agent-Friendly Design:**
- ✅ Semantic method names (`success`, `error`, `warning`)
- ✅ Simple string-based interface (no complex formatting syntax)
- ✅ Clear output categories for different message types

**2. TTY Detection:**
- Automatically disables color codes when not running in a TTY
- `use_color = use_color and sys.stdout.isatty()`

**3. Verbosity Control:**
- `verbose` - Shows `info()` messages
- `quiet` - Errors only
- Normal - Actions, success, warnings, errors

**4. ANSI Color Support:**
- Blue (34) - Actions
- Green (32) - Success
- Cyan (36) - Info/Results
- Yellow (33) - Warnings
- Red (31) - Errors
- Magenta (35) - Headers

---

## Instantiation Points

### Direct Instantiation Pattern

Most CLI modules follow this pattern:

```python
printer = PrettyPrinter(
    use_color=not args.no_color,
    verbose=args.verbose,
    quiet=args.quiet
)
```

### Common Instantiation Contexts

**1. CLI Entry Points**
- All command functions receive `printer: PrettyPrinter` parameter
- Instantiated once at CLI initialization
- Passed through to subcommands

**2. AI Consultation Functions**
- `printer: Optional['PrettyPrinter'] = None` parameter pattern
- Falls back to plain `print()` if None
- Used for consistent output in AI tool invocations

**3. Test Files**
- Instantiated in conftest.py fixtures
- Used for test output consistency
- Often disabled with `quiet=True` in automated tests

---

## Usage Patterns by Module

### 1. CLI Modules (18 files)

**Primary usage pattern:**
```python
def cmd_<action>(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    printer.action("Starting...")
    # ... work ...
    printer.success("Completed!")
    return 0
```

**Files:**
- `sdd_plan/cli.py`
- `sdd_next/cli.py`
- `sdd_update/cli.py`
- `sdd_validate/cli.py`
- `sdd_render/cli.py`
- `sdd_pr/cli.py`
- `sdd_fidelity_review/cli.py`
- `sdd_plan_review/cli.py`
- `sdd_spec_mod/cli.py`
- `code_doc/cli.py`
- `doc_query/cli.py`
- `run_tests/cli.py`
- `context_tracker/cli.py`
- `cli/sdd/__init__.py`
- `cli/skills_dev/setup_permissions.py`
- `cli/skills_dev/start_helper.py`
- `cli/skills_dev/git_config_helper.py`
- `cli/skills_dev/migrate.py`

### 2. Workflow Modules (8 files)

**Usage for progress tracking:**
```python
printer.action(f"Processing task {task_id}...")
printer.detail(f"  Status: {status}", indent=1)
printer.success("Task updated")
```

**Files:**
- `sdd_update/lifecycle.py`
- `sdd_update/workflow.py`
- `sdd_update/status.py`
- `sdd_update/time_tracking.py`
- `sdd_update/validation.py`
- `sdd_update/journal.py`
- `sdd_update/verification.py`
- `sdd_update/query.py`

### 3. AI Consultation Modules (3 files)

**Optional printer pattern:**
```python
def consult_ai_tool(
    tool_name: str,
    printer: Optional['PrettyPrinter'] = None
) -> Dict[str, any]:
    if printer:
        printer.action(f"Consulting {tool_name}...")
    else:
        print(f"Consulting {tool_name}...")
```

**Files:**
- `code_doc/ai_consultation.py`
- `run_tests/consultation.py`
- `sdd_pr/pr_creation.py`

### 4. Helper/Utility Modules (5 files)

**Files:**
- `common/query_operations.py`
- `common/git_metadata.py`
- `sdd_update/list_specs.py`
- `sdd_fidelity_review/report.py`
- `cli/skills_dev/registry.py`
- `cli/skills_dev/gendocs.py`

### 5. Test Files (15 files)

**Usage in tests:**
```python
def test_something(capsys):
    printer = PrettyPrinter(use_color=False, quiet=True)
    printer.success("Test output")
    captured = capsys.readouterr()
```

**Files:** (Located in `tests/` and `claude_skills/tests/`)
- Integration tests
- Unit tests
- Test fixtures (conftest.py)

---

## Method Call Frequency (Estimated)

Based on grep results, approximate frequency of method calls:

| Method | Estimated Calls | Primary Use Cases |
|--------|----------------|-------------------|
| `action()` | ~200+ | Progress updates, starting operations |
| `success()` | ~150+ | Completion confirmations |
| `error()` | ~100+ | Error reporting |
| `warning()` | ~75+ | Non-critical issues |
| `info()` | ~50+ | Verbose details |
| `result()` | ~40+ | Key-value output |
| `detail()` | ~30+ | Indented context |
| `header()` | ~25+ | Section separators |
| `item()` | ~20+ | Lists |
| `blank()` | ~15+ | Spacing |

---

## Configuration Patterns

### Common Configuration

**Standard CLI initialization:**
```python
printer = PrettyPrinter(
    use_color=not args.no_color,  # --no-color flag
    verbose=args.verbose,          # -v/--verbose flag
    quiet=args.quiet               # -q/--quiet flag
)
```

### Test Configuration

**Quiet mode for automated tests:**
```python
printer = PrettyPrinter(use_color=False, quiet=True)
```

### Verbose Debugging

**Development/debugging mode:**
```python
printer = PrettyPrinter(use_color=True, verbose=True, quiet=False)
```

---

## Integration Points

### 1. CLI Framework Integration

**Every CLI command follows this pattern:**
```python
def cmd_<action>(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Command function receives printer as parameter."""
    pass
```

### 2. Error Handling Integration

**Consistent error reporting:**
```python
def _handle_error(args: argparse.Namespace, printer: PrettyPrinter, exc: Exception) -> int:
    if getattr(args, 'json', False):
        _dump_json({"status": "error", "message": str(exc)})
    else:
        printer.error(str(exc))
    return 1
```

### 3. JSON Output Mode

**JSON mode bypasses PrettyPrinter:**
```python
def _print_if_json(args: argparse.Namespace, payload: object, printer: PrettyPrinter) -> bool:
    if getattr(args, 'json', False):
        _dump_json(payload)
        return True
    return False
```

---

## Custom Extensions/Wrappers

**No custom wrappers or subclasses found.** All usage is direct instantiation and method calls.

---

## Edge Cases and Special Patterns

### 1. Optional Printer Pattern

**Used in AI consultation functions:**
```python
printer: Optional['PrettyPrinter'] = None
```
- Allows functions to work with or without printer
- Falls back to plain `print()` when None

### 2. TTY Detection Notes

**From integration test comments:**
```python
# Note: Output verification skipped due to PrettyPrinter TTY detection
# Command functionality verified by return code
```
- Tests acknowledge TTY detection affects output
- Some tests validate behavior, not exact output

### 3. Forward References

**Type hint pattern:**
```python
from typing import Optional

printer: Optional['PrettyPrinter'] = None
```
- Uses string literal for forward reference
- Common in function signatures

---

## Implications for AI-Agent-First TUI Upgrade

### ✅ Good News

1. **No Rich Dependency to Remove**
   - Custom PrettyPrinter already exists
   - No migration from Rich needed
   - No breaking changes from removing Rich

2. **Already Agent-Friendly**
   - Semantic method names (`success`, `error`, `warning`)
   - Simple string-based interface
   - Clear output categories

3. **Consistent Usage Pattern**
   - All CLI modules follow same pattern
   - Standardized instantiation
   - Uniform error handling

4. **Well-Tested**
   - Used in 15+ test files
   - Integration tests cover TTY detection
   - Unit tests validate behavior

### ⚠️ Considerations

1. **Limited Formatting Capabilities**
   - No tables, progress bars, or complex layouts
   - No tree rendering
   - No syntax highlighting
   - No markdown rendering

2. **Agent Interface Could Be Enhanced**
   - Current methods are imperative (print now)
   - Could add structured data collection
   - Could separate rendering from output

3. **No Streaming/Progressive Output**
   - All output is immediate
   - No support for updating previous lines
   - No spinner or progress indicator support

---

## Recommendations for Next Task (task-1-1-2)

Based on this audit, the next task should focus on:

1. **Document Current Interface**
   - The custom PrettyPrinter is the baseline
   - Methods are already semantic and agent-friendly
   - TTY detection is already handled

2. **Identify Enhancement Opportunities**
   - Structured data collection (separate from rendering)
   - Agent-friendly output modes
   - Progressive/streaming output support
   - Rich formatting capabilities (if needed)

3. **Consider Consolidation Strategy**
   - Keep custom PrettyPrinter as foundation
   - Add agent-first enhancements
   - Optionally integrate Rich for complex formatting (if valuable)
   - Maintain backward compatibility

4. **Testing Strategy**
   - Existing tests provide good coverage
   - TTY detection already tested
   - Add agent mode tests

---

## Files Analyzed

**Total files with PrettyPrinter references:** 49

**Categories:**
- CLI modules: 18
- Workflow modules: 8
- Test files: 15
- AI consultation: 3
- Helper/utility: 5

**Files NOT using PrettyPrinter:**
- None identified (all modules use consistent pattern)

---

## Search Commands Used

```bash
# Imports
grep -r "from rich.pretty import PrettyPrinter" --include="*.py"  # 0 results
grep -r "from rich" --include="*.py"                              # 0 results
grep -r "import rich" --include="*.py"                            # 0 results

# Custom PrettyPrinter
grep -r "PrettyPrinter" --include="*.py"                          # 49 files
grep -r "from claude_skills.common import PrettyPrinter"          # Common pattern

# Dependencies
grep -i "rich" ./src/claude_skills/pyproject.toml                 # 0 results
```

---

## Conclusion

The audit reveals that the codebase already has a custom, lightweight, agent-friendly `PrettyPrinter` implementation. There is **no Rich library dependency** and no need to migrate away from Rich.

The focus of Phase 1 should shift from "migrating away from Rich" to "enhancing the existing custom PrettyPrinter with agent-first capabilities" while maintaining its simplicity and effectiveness.

**Next Steps:**
- Task 1-1-2: Document common usage patterns (DONE in this audit)
- Task 1-2: Evaluate enhancement opportunities for agent-first TUI
- Consider: Is Rich integration valuable for specific use cases, or continue with custom solution?

