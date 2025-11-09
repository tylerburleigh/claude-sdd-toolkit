# Design: Data Structure to UI Protocol Mapping

## Overview

This document specifies how to convert Rich Table visualizations in visualization commands (like `list_specs`) to a unified data structure that works with both RichUi and PlainUi backends.

## Current Rich Table Example: list_specs.py

```python
# Current Rich-only approach
table = Table(
    title="📋 Specifications",
    show_header=True,
    header_style="bold cyan",
    border_style="blue",
    title_style="bold magenta",
)

table.add_column("ID", style="cyan", no_wrap=True, min_width=30)
table.add_column("Title", style="white", no_wrap=True, min_width=25)
table.add_column("Progress", justify="right", style="yellow", min_width=12)
table.add_column("Status", justify="center", style="green", min_width=10)
table.add_column("Phase", style="blue", min_width=10)
table.add_column("Updated", style="dim", min_width=10)

# Add rows...
table.add_row(...)

# Print only in Rich mode
console.print(table)
```

## Unified UI Protocol Mapping

### 1. Data Structure Format

Replace Rich Table construction with plain data structures:

```python
# Instead of Rich Table, prepare data as List[Dict]
table_data = [
    {
        "ID": "spec-id-001",
        "Title": "User Authentication System",
        "Progress": "████░░░░░░ 50%\n5/10 tasks",
        "Status": "⚡ Active",
        "Phase": "phase-2",
        "Updated": "2025-11-08"
    },
    {
        "ID": "spec-id-002",
        "Title": "API Versioning",
        "Progress": "██████░░░░ 60%\n6/10 tasks",
        "Status": "✅ Complete",
        "Phase": "phase-3",
        "Updated": "2025-11-07"
    }
]

# Define visible columns
columns = ["ID", "Title", "Progress", "Status", "Phase", "Updated"]

# Optional title
title = "📋 Specifications"
```

### 2. RichUi Backend Handling

For RichUi, convert the unified data structure back to Rich Table:

```python
def render_table_rich(ui, table_data, columns, title):
    """Convert unified data to Rich Table for RichUi backend."""

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold magenta",
    )

    # Add columns with styling
    column_styles = {
        "ID": "cyan",
        "Title": "white",
        "Progress": "yellow",
        "Status": "green",
        "Phase": "blue",
        "Updated": "dim"
    }

    for col in columns:
        style = column_styles.get(col, "white")
        justify = "right" if col == "Progress" else ("center" if col == "Status" else "left")

        table.add_column(col, style=style, no_wrap=True, justify=justify)

    # Add rows
    for row in table_data:
        table.add_row(*[row.get(col, "") for col in columns])

    # Render via RichUi console
    ui.console.print(table)
```

### 3. PlainUi Backend Handling

PlainUi already has `print_table()` method that handles ASCII rendering:

```python
def render_table_plain(ui, table_data, columns, title):
    """Use PlainUi's native print_table() for ASCII rendering."""

    ui.print_table(
        data=table_data,
        columns=columns,
        title=title
    )

    # PlainUi print_table() automatically:
    # 1. Calculates optimal column widths
    # 2. Creates ASCII borders with |, -, +
    # 3. Renders headers and separators
    # 4. Handles multi-line cell content (Progress field)
    # 5. Strips Rich markup if present
```

### 4. Unified Rendering Function

Create a wrapper function that handles both backends:

```python
def print_specs_table(ui, specs_info, verbose=False):
    """
    Print specifications using unified UI protocol.

    Works with both RichUi and PlainUi backends.
    """

    if not specs_info:
        ui.print_status("No specifications found.", level=MessageLevel.INFO)
        return

    # 1. Prepare table data (List[Dict])
    table_data = []
    for spec in specs_info:
        # Create progress display
        if spec['total_tasks'] > 0:
            progress_bar = _create_progress_bar_plain(spec['progress_percentage'])
            progress = f"{progress_bar} {spec['progress_percentage']}%\n{spec['completed_tasks']}/{spec['total_tasks']} tasks"
        else:
            progress = "No tasks"

        # Create status display
        status_map = {
            "active": "⚡ Active",
            "completed": "✅ Complete",
            "pending": "⏸️  Pending",
            "archived": "📦 Archived"
        }
        status = status_map.get(spec['status'], spec['status'].title())

        # Build row
        row = {
            "ID": spec['spec_id'],
            "Title": spec['title'],
            "Progress": progress,
            "Status": status,
            "Phase": spec.get('current_phase', '-'),
            "Updated": spec.get('updated_at', '-').split('T')[0] if spec.get('updated_at') else '-'
        }

        table_data.append(row)

    # 2. Define columns
    columns = ["ID", "Title", "Progress", "Status", "Phase", "Updated"]

    # 3. Render based on UI backend
    if ui.console is None:
        # PlainUi - uses native print_table()
        ui.print_table(data=table_data, columns=columns, title="📋 Specifications")
    else:
        # RichUi - convert to Rich Table
        from rich.table import Table

        table = Table(
            title="📋 Specifications",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta",
        )

        column_config = {
            "ID": {"style": "cyan", "no_wrap": True, "overflow": "ignore", "min_width": 30},
            "Title": {"style": "white", "no_wrap": True, "overflow": "ignore", "min_width": 25},
            "Progress": {"style": "yellow", "no_wrap": True, "overflow": "ignore", "min_width": 12, "justify": "right"},
            "Status": {"style": "green", "no_wrap": True, "overflow": "ignore", "min_width": 10, "justify": "center"},
            "Phase": {"style": "blue", "no_wrap": True, "overflow": "ignore", "min_width": 10},
            "Updated": {"style": "dim", "no_wrap": True, "overflow": "ignore", "min_width": 10}
        }

        for col in columns:
            config = column_config.get(col, {})
            table.add_column(col, **config)

        for row_data in table_data:
            table.add_row(*[row_data.get(col, "") for col in columns])

        ui.console.print(table)

    # 4. Print verbose details if requested
    if verbose:
        ui.print_status("Verbose Details:", level=MessageLevel.HEADER)
        for spec in specs_info:
            # Print spec details
            pass
```

## Key Design Decisions

### 1. Progress Bar Representation

**Rich Mode:**
```
[green]██████░░░░[/green] 60%
6/10 tasks
```

**Plain Mode:**
```
████░░░░░░ 60%
6/10 tasks
```

**Implementation:**
- Create `_create_progress_bar_plain()` function
- Returns simple ASCII: `█` for filled, `░` for empty
- No color codes needed
- Multi-line text supported (newline in dict value)

### 2. Status Emoji Handling

**Both Modes:**
- Keep emojis (✅, ⚡, ⏸️, 📦) - they are pure ASCII/Unicode
- Work in both Rich and plain terminals
- No styling applied
- Easy to replace with text if needed: (✅→[OK], ⚡→[ACTIVE])

### 3. Column Width Management

**Rich Mode:**
- Uses `min_width` and Rich's auto-layout
- Rich handles truncation and wrapping
- `no_wrap=True` prevents wrapping
- `overflow="ignore"` truncates if too wide

**Plain Mode:**
- PlainUi calculates width: `max(len(header), max(len(value) for value in column))`
- Padding with spaces for alignment
- Handles multi-line values by breaking on `\n`
- Fixed-width ASCII rendering

### 4. Multi-line Cell Content

**Progress Field Example:**
```
████░░░░░░ 60%
6/10 tasks
```

**Plain Mode Handling:**
- PlainUi's `print_table()` supports newlines in values
- Splits on `\n` and renders as stacked lines
- Aligns with column width
- No special handling needed

**Rich Mode Handling:**
- Rich Table automatically handles `\n` in cells
- Renders multi-line cells with proper spacing
- Maintains alignment

## Implementation Strategy

### Phase 1: Investigation (Current)
- [x] Analyze current Rich usage in list_specs.py
- [x] Design unified data structure protocol
- [ ] Create wrapper functions for rendering

### Phase 2: Implementation
- Create `print_specs_table()` function
- Implement progress bar plain mode version
- Update list_specs.py to use unified approach
- Test with both UI backends

### Phase 3: Verification
- Integration tests with RichUi
- Integration tests with PlainUi
- Verify output format matches original
- Test verbose mode in both backends

### Phase 4: Refactoring
- Apply pattern to other visualization commands
- Update status_report.py if needed
- Update list_phases.py if needed
- Consolidate common patterns

## Data Flow Diagram

```
list_specs() - Get spec information
       ↓
Build table_data: List[Dict]
       ↓
       ├──→ RichUi? ──→ Convert to Rich Table ──→ console.print()
       │
       └──→ PlainUi? ──→ ui.print_table() ──→ ASCII output
```

## API Contract

### Input
```python
# Unified data structure
table_data: List[Dict[str, Any]] = [
    {"ID": str, "Title": str, "Progress": str, "Status": str, "Phase": str, "Updated": str},
    ...
]

columns: List[str]  # Column names to display
title: Optional[str]  # Table title
```

### Output
**RichUi:** Formatted Rich Table with colors and styling
**PlainUi:** ASCII table with borders and fixed widths

### Backend Detection
```python
if ui.console is None:
    # PlainUi backend
else:
    # RichUi backend
```

## Testing Strategy

### Test Cases

1. **Empty Data**
   - Test: Empty list → Info message
   - Both backends

2. **Single Row**
   - Test: One spec displayed correctly
   - Verify column widths
   - Check status emoji renders

3. **Multiple Rows**
   - Test: 5+ specs displayed
   - Headers visible and aligned
   - Progress bars render correctly

4. **Progress Bar Styles**
   - Test: Different completion percentages
   - Color rendering in RichUi
   - ASCII rendering in PlainUi

5. **Multi-line Cells**
   - Test: Progress field with 2 lines
   - Alignment in both backends
   - Width calculation includes newlines

6. **Verbose Mode**
   - Test: Additional details displayed
   - Proper formatting in both backends

7. **Edge Cases**
   - Very long titles (truncation)
   - Missing values (empty string)
   - Special characters in names

## Success Criteria

- [x] Design document complete
- [ ] Both PlainUi and RichUi produce valid output
- [ ] Visual appearance is comparable to original Rich output
- [ ] Progress bars render correctly in both modes
- [ ] No Rich dependencies required in plain mode
- [ ] Extensible for other visualization commands
- [ ] Integration tests pass
- [ ] Performance is acceptable (< 1 second render)

## Files Affected

1. `/src/claude_skills/claude_skills/sdd_update/list_specs.py`
   - Replace Rich Table construction with unified approach
   - Keep data preparation logic (counts, percentages)
   - Add progress bar plain text version

2. `/src/claude_skills/claude_skills/common/plain_ui.py`
   - No changes (print_table() already exists)
   - May need to verify multi-line cell handling

3. `/src/claude_skills/claude_skills/common/rich_ui.py`
   - Potentially no changes
   - Verify print_table() works with styled data

## References

- PlainUi implementation: `/src/claude_skills/claude_skills/common/plain_ui.py` (lines 111-187)
- RichUi implementation: `/src/claude_skills/claude_skills/common/rich_ui.py` (lines 98-169)
- Current list_specs: `/src/claude_skills/claude_skills/sdd_update/list_specs.py`
- Analysis document: `ANALYSIS_RICH_USAGE.md`
