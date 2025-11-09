# Plain Mode Support Investigation - Findings

## Problem Statement
When `default_mode: plain` is set in SDD config, visualization commands like `sdd list-specs` produce errors or revert to Rich formatting instead of plain text.

## Root Cause Analysis

### Issue 1: Deprecated Config Fields (FIXED ✅)
**Fixed by:** Updated CLI config loading to use `default_mode` and `json_compact` instead of deprecated `json` and `compact` fields.

Files changed:
- `cli/sdd/__init__.py` - Updated config field references
- `tests/unit/test_common/test_sdd_config.py` - Updated tests for new fields
- `tests/integration/test_sdd_config_integration.py` - Updated integration tests

### Issue 2: Architectural Incompatibility (UNRESOLVED ❌)
**Core Problem:** Visualization commands have a fundamental architectural issue with plain mode support.

#### Commands Affected (7 files):
1. `sdd_update/list_specs.py` - Creates Rich Table with complex styling
2. `sdd_update/query_tasks.py` - Creates Rich Table with complex styling
3. `sdd_update/list_phases.py` - Creates Rich Table with complex styling
4. `sdd_update/status_report.py` - Creates Rich Layout/Panels
5. `sdd_next/cli.py` - Creates Rich Tree for dependency visualization
6. `sdd_validate/diff.py` - Creates Rich Columns/Panels for diff visualization
7. `sdd_fidelity_review/report.py` - Creates Rich Panel for fidelity reports

#### Why It's Incompatible:
- These commands create **Rich-specific objects** (Table, Tree, Panel, Columns)
- Rich objects require a **Rich Console** to render
- PlainUi does NOT have a Rich Console (`.console` returns `None`)
- Rich objects cannot be rendered as plain text

#### What We've Tried:

1. **Attempt 1: Use RichUi.print_table() protocol method**
   - ❌ FAILED: RichUi.print_table() doesn't support advanced features:
     - Per-column styling (colors, alignment, widths)
     - Custom borders and padding
     - Dynamic columns
     - Custom headers
   - Would lose significant visual quality for Rich mode

2. **Attempt 2: Check for PlainUi and skip visualization**
   ```python
   if ui and ui.console is None:
       printer.info("Use --json for output")
       return
   ```
   - ❌ FAILED: When `ui=None`, calling `create_ui()` respects the config and returns PlainUi
   - Leads to NoneType errors when trying to `console.print()`

3. **Attempt 3: Force Rich console for fallback**
   ```python
   console = ui.console if ui else create_ui(force_rich=True).console
   ```
   - ❌ FAILED: Ignores user's `default_mode: plain` setting
   - Commands always produce Rich output, defeating the purpose of plain mode config

## Key Architectural Findings

### 1. CLI Design Issue
- Main CLI entry point (`cli/sdd/__init__.py`) creates only a `PrettyPrinter`
- **Does NOT create or pass UI instances** to command handlers
- Commands receive `ui=None` by default
- This means the `ui` parameter is essentially non-functional in the current design

### 2. UI Factory Design
- `create_ui()` automatically selects backend based on:
  - `force_rich` / `force_plain` flags
  - Config setting `output.default_mode`
  - TTY detection (is output a terminal?)
  - CI environment detection
- When called without flags, respects user's config setting

### 3. PlainUi Implementation
- Has `.console` property that returns `None` (for compatibility)
- Has `print_table()`, `print_tree()`, `print_panel()` methods that work with plain text
- These methods ARE compatible with plain mode
- BUT visualization commands don't use these methods - they create Rich objects directly

## What Needs to Change

### Option A: Redesign Visualization Commands (Recommended)
- Convert Rich Table/Tree/Panel objects to plain data structures
- Use UI protocol methods: `ui.print_table()`, `ui.print_tree()`, `ui.print_panel()`
- Both RichUi and PlainUi implement these methods
- This is the "right" architectural pattern

### Option B: Enhance RichUi.print_table()
- Add support for advanced features currently used
- Add `column_config` parameter for per-column styling
- Add support for all Rich Table options
- Make it a true feature-parity wrapper

### Option C: Always Use Rich
- Explicitly force Rich mode for visualization commands
- Accept that plain mode can't support visual tables
- Only use plain mode for text-based commands

## Current State of Fixes

### Status: PARTIAL ✅❌

**Working:**
- Deprecated config fields are fixed
- All config tests pass (29/29)
- No NoneType errors from missing console attribute

**Not Working:**
- Plain mode config setting is not respected by visualization commands
- Commands either crash or force Rich output
- No clean fallback for plain mode

## Recommended Next Steps

1. **Investigate Option A (Preferred):**
   - Check how `sdd_next/discovery.py` returns data structures vs Rich objects
   - Look for examples of commands using `ui.print_table()` successfully
   - Determine migration path for 7 affected files

2. **Document Current Behavior:**
   - Plain mode works for `--json` output flag
   - Plain mode works for text-only commands
   - Plain mode DOES NOT work for table/tree/panel visualizations

3. **Decide on Philosophy:**
   - Is plain mode for "no colors" or for "no fancy formatting"?
   - Can visual tables exist in plain mode (as ASCII art)?
   - Or should plain mode skip complex visualizations entirely?

## References

- Plain UI implementation: `src/claude_skills/common/plain_ui.py`
- Rich UI implementation: `src/claude_skills/common/rich_ui.py`
- UI Protocol: `src/claude_skills/common/ui_protocol.py`
- UI Factory: `src/claude_skills/common/ui_factory.py`
- CLI Entry Point: `src/claude_skills/cli/sdd/__init__.py`
