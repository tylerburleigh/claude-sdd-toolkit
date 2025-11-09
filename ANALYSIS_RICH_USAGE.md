# Rich Usage Analysis: list_specs.py

## Current Rich Implementation

### Imports
- `from rich.table import Table`
- `from rich.console import Console`

### Rich Components Used

#### 1. Rich Table (Primary Feature)
**Location:** `_print_specs_text()` function (lines 167-227)

**Table Configuration:**
```python
table = Table(
    title="📋 Specifications",
    show_header=True,
    header_style="bold cyan",
    border_style="blue",
    title_style="bold magenta",
)
```

**Styling Options Applied:**
- `title`: "📋 Specifications" (includes emoji)
- `show_header`: True (displays column headers)
- `header_style`: "bold cyan" (bold blue header text)
- `border_style`: "blue" (blue colored borders)
- `title_style`: "bold magenta" (bold magenta title text)

**Columns (6 total):**
1. **ID** - cyan color, no_wrap=True, min_width=30
2. **Title** - white color, no_wrap=True, min_width=25
3. **Progress** - yellow color, right-justified, no_wrap=True, min_width=12
4. **Status** - green color, center-justified, no_wrap=True, min_width=10
5. **Phase** - blue color, no_wrap=True, min_width=10
6. **Updated** - dim color, no_wrap=True, min_width=10

**Column Styling Attributes:**
- `style`: Color specification per column (cyan, white, yellow, green, blue, dim)
- `justify`: Text alignment (right, center, default=left)
- `no_wrap`: Prevents text wrapping (True for all columns)
- `overflow`: Truncation behavior (set to "ignore" for all)
- `min_width`: Minimum column width in characters

#### 2. Rich Markup & Styling

**Progress Bar Visualization:**
- Uses Unicode block characters: `█` (filled) and `░` (empty)
- Dynamic color coding based on percentage:
  - Red: 0-24%
  - Orange: 25-49%
  - Yellow: 50-74%
  - Green: 75-100%
- Syntax: `[{color}]█[/{color}]░` (Rich markup syntax)
- Width: 10 characters (configurable in `_create_progress_bar()`)
- Combined with text: `{progress_bar} {percentage}%\n{completed}/{total} tasks`

**Text Markup:**
- `[bold cyan]` - Bold cyan text
- `[cyan]` - Cyan text
- `[/color]` - Closing tag
- Emojis in text: ⚡, ✅, ⏸️, 📦

**Status Display with Emojis:**
- Active: "⚡ Active"
- Completed: "✅ Complete"
- Pending: "⏸️  Pending"
- Archived: "📦 Archived"

**Verbose Output (lines 230-243):**
- Uses `console.print()` with Rich markup
- Multi-line formatting with headers and indented details

#### 3. Console Output
- Creates Rich Console via `create_ui(force_rich=True).console`
- Uses `console.print(table)` to render the table
- Supports printing Rich markup strings with inline formatting

### Plain Mode Handling

**Current Implementation (lines 158-161):**
```python
if ui and ui.console is None:
    printer.info("Rich table visualization not available in plain mode. Use --json for structured output.")
    return
```

**Current Behavior:**
- Detects PlainUi (console is None)
- Prints informational message
- Returns without rendering table
- Suggests using --json format

### Data Flow

1. **Input:** List of spec dictionaries with metadata
2. **Processing:**
   - Calculates progress percentage
   - Formats status display with emojis
   - Creates visual progress bar
   - Applies Rich styling
3. **Output:** Rich Table rendered via console
4. **Fallback:** PlainUi returns message directing to --json format

## Key Observations

### Rich Features for Plain Mode Conversion

**Rich-Specific Features that Need Plain Text Alternatives:**
1. **Table Borders & Headers** - ASCII table needed
2. **Color Codes** - Remove or make optional
3. **Bold/Dim Text** - Not possible in plain text (remove styling)
4. **Progress Bar Colors** - Use ASCII characters without color codes
5. **Emojis** - Can keep (pure ASCII) or replace with text indicators
6. **Column Widths & Alignment** - Use fixed-width formatting with padding
7. **Multi-line Cells** - Convert to single-line or use separators

### Current Architecture

- **UI Factory Pattern:** `create_ui()` creates Rich or Plain UI
- **UI Abstraction:** PlainUi has `console = None`
- **Format Routing:** Text format uses Rich, JSON format is plain
- **Detection Logic:** Checks `ui.console is None` to detect plain mode

### Dependencies

- **Rich Library:** Required for table rendering
- **PrettyPrinter:** Used for plain text info messages
- **UI Factory:** Provides Console or PlainUi based on configuration
- **JSON Output:** Handles structured JSON format

## Recommendations for Plain Mode Support

1. **Create PlainUi Table Renderer:** Implement ASCII-based table in `plain_ui.py`
2. **Color Stripping:** Remove Rich markup before printing
3. **Progress Bar Simplification:** Use ASCII characters (e.g., `[=====>-----]` or `████░░░░░░`)
4. **Column Alignment:** Use padding and fixed widths for alignment
5. **Emoji Handling:** Can keep emojis or replace with text
6. **Error Handling:** Graceful fallback if table rendering fails

## File References

- **Source File:** `src/claude_skills/claude_skills/sdd_update/list_specs.py`
- **Lines with Rich Usage:**
  - Progress bar: lines 15-43 (standalone function)
  - Table creation: lines 167-173
  - Column definition: lines 175-181
  - Row generation: lines 184-224
  - Plain mode detection: lines 158-161
  - Verbose output: lines 230-243
