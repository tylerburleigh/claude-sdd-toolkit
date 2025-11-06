# PrettyPrinter Interface Requirements

**Date:** 2025-11-06
**Task:** task-1-1-2 - Document common usage patterns and interface requirements
**Spec:** AI-Agent-First TUI Upgrade (tui-upgrade-2025-11-06-001)
**Related:** [PrettyPrinter Audit Results](./prettyprinter-audit-results.md)

---

> **⚠️ IMPORTANT NOTE - BACKGROUND RESEARCH ONLY**
>
> This document was created during Phase 1 investigation (task-1-1-2) to understand the existing `PrettyPrinter` class and its usage patterns across the codebase.
>
> **This analysis informed the decision to use Rich library instead of enhancing PrettyPrinter.**
>
> **Actual Implementation:** The TUI upgrade uses the [Rich library](https://github.com/Textualize/rich) with a new `Ui` protocol that defines methods like `print_table()`, `print_tree()`, `print_diff()`, `progress()`, `print_panel()`, and `print_status()`.
>
> **PrettyPrinter Status:** The existing `PrettyPrinter` class remains unchanged and continues to work for backward compatibility. New code should use the Rich-based `Ui` implementations (RichUi, PlainUi).
>
> See [TUI Implementation Decision Record](./tui-implementation-decision.md) for details on why Rich was chosen.

---

## Executive Summary

This document defines the interface requirements for the custom `PrettyPrinter` class, based on analysis of 49 files across the codebase. It specifies:

1. **Core API Contract** - Methods that must be preserved for backward compatibility
2. **Usage Patterns** - How the interface is used across different contexts
3. **Interface Gaps** - Agent-first capabilities missing from current design
4. **Enhancement Opportunities** - Specific improvements for AI-agent workflows

**Key Requirement:** Any enhancements must maintain 100% backward compatibility with existing usage.

---

## Table of Contents

1. [Core API Contract](#core-api-contract)
2. [Initialization Contract](#initialization-contract)
3. [Usage Pattern Catalog](#usage-pattern-catalog)
4. [Interface Gaps Analysis](#interface-gaps-analysis)
5. [Enhancement Requirements](#enhancement-requirements)
6. [Backward Compatibility Requirements](#backward-compatibility-requirements)
7. [Test Coverage Requirements](#test-coverage-requirements)

---

## Core API Contract

### Current Implementation

**Source:** `src/claude_skills/claude_skills/common/printer.py`

**Class:** `PrettyPrinter`

### Required Methods (MUST Preserve)

These methods are used extensively and MUST remain unchanged:

#### 1. `action(msg: str) -> None`

**Purpose:** Print an action message (what's being done now)

**Contract:**
```python
def action(self, msg: str) -> None:
    """Print an action message (what's being done now)."""
```

**Behavior:**
- Prints to stdout
- Prepends 🔵 emoji and "Action:" label (if color enabled)
- Respects `quiet` flag (suppressed if quiet=True)
- Uses blue color code (34) for "Action:" label

**Usage Frequency:** ~200+ calls across codebase

**Example:**
```python
printer.action("Processing task task-2-1...")
printer.action("Validating dependencies...")
```

---

#### 2. `success(msg: str) -> None`

**Purpose:** Print a success message (completed action)

**Contract:**
```python
def success(self, msg: str) -> None:
    """Print a success message (completed action)."""
```

**Behavior:**
- Prints to stdout
- Prepends ✅ emoji and "Success:" label (if color enabled)
- Respects `quiet` flag (suppressed if quiet=True)
- Uses green color code (32) for "Success:" label

**Usage Frequency:** ~150+ calls

**Example:**
```python
printer.success("Task completed successfully")
printer.success("Spec validation passed")
```

---

#### 3. `info(msg: str) -> None`

**Purpose:** Print an informational message (context/details)

**Contract:**
```python
def info(self, msg: str) -> None:
    """Print an informational message (context/details)."""
```

**Behavior:**
- Prints to stdout
- Prepends ℹ️ emoji and "Info:" label (if color enabled)
- **Only prints if `verbose=True`**
- Also respects `quiet` flag
- Uses cyan color code (36) for "Info:" label

**Usage Frequency:** ~50+ calls

**Example:**
```python
printer.info("Checking 15 dependency files...")
printer.info("Using default configuration")
```

---

#### 4. `warning(msg: str) -> None`

**Purpose:** Print a warning message (non-blocking issue)

**Contract:**
```python
def warning(self, msg: str) -> None:
    """Print a warning message (non-blocking issue)."""
```

**Behavior:**
- **Prints to stderr** (not stdout)
- Prepends ⚠️ emoji and "Warning:" label (if color enabled)
- Respects `quiet` flag
- Uses yellow color code (33) for "Warning:" label

**Usage Frequency:** ~75+ calls

**Example:**
```python
printer.warning("Deprecated configuration format detected")
printer.warning("Task has no estimated_hours metadata")
```

---

#### 5. `error(msg: str) -> None`

**Purpose:** Print an error message (blocking issue)

**Contract:**
```python
def error(self, msg: str) -> None:
    """Print an error message (blocking issue)."""
```

**Behavior:**
- **Prints to stderr** (not stdout)
- Prepends ❌ emoji and "Error:" label (if color enabled)
- **ALWAYS prints** (ignores quiet flag)
- Uses red color code (31) for "Error:" label

**Usage Frequency:** ~100+ calls

**Example:**
```python
printer.error("Spec file not found")
printer.error("Invalid task ID format")
```

---

#### 6. `header(msg: str) -> None`

**Purpose:** Print a section header

**Contract:**
```python
def header(self, msg: str) -> None:
    """Print a section header."""
```

**Behavior:**
- Prints to stdout
- Surrounds message with "═" line (60 chars)
- Centers message text (60 chars width)
- Respects `quiet` flag
- Uses magenta color code (35) with bold (35;1)
- Adds blank line before and after

**Usage Frequency:** ~25+ calls

**Example Output:**
```
════════════════════════════════════════════════════════════
                    Spec Validation Report
════════════════════════════════════════════════════════════
```

---

#### 7. `detail(msg: str, indent: int = 1) -> None`

**Purpose:** Print an indented detail line

**Contract:**
```python
def detail(self, msg: str, indent: int = 1) -> None:
    """Print an indented detail line."""
```

**Behavior:**
- Prints to stdout
- Indents with 2 spaces per indent level
- Respects `quiet` flag
- No color or emoji (plain text)

**Usage Frequency:** ~30+ calls

**Example:**
```python
printer.detail("Status: pending", indent=1)
printer.detail("Dependencies: 3 tasks", indent=2)
```

---

#### 8. `result(key: str, value: str, indent: int = 0) -> None`

**Purpose:** Print a key-value result

**Contract:**
```python
def result(self, key: str, value: str, indent: int = 0) -> None:
    """Print a key-value result."""
```

**Behavior:**
- Prints to stdout
- Format: `{indent}{key}: {value}`
- Key is colored cyan (36) if colors enabled
- Respects `quiet` flag

**Usage Frequency:** ~40+ calls

**Example:**
```python
printer.result("Total Tasks", "23")
printer.result("Completed", "15", indent=1)
```

---

#### 9. `blank() -> None`

**Purpose:** Print a blank line

**Contract:**
```python
def blank(self) -> None:
    """Print a blank line."""
```

**Behavior:**
- Prints single newline to stdout
- Respects `quiet` flag

**Usage Frequency:** ~15+ calls

**Example:**
```python
printer.action("Starting validation")
printer.blank()
printer.detail("Checking dependencies...")
```

---

#### 10. `item(msg: str, indent: int = 0) -> None`

**Purpose:** Print a list item

**Contract:**
```python
def item(self, msg: str, indent: int = 0) -> None:
    """Print a list item."""
```

**Behavior:**
- Prints to stdout
- Format: `{indent}• {msg}`
- Uses bullet point (•) character
- Respects `quiet` flag

**Usage Frequency:** ~20+ calls

**Example:**
```python
printer.item("Task 1: Create directory structure")
printer.item("Subtask: Initialize config", indent=1)
```

---

## Initialization Contract

### Constructor Signature

```python
def __init__(self, use_color: bool = True, verbose: bool = False, quiet: bool = False)
```

### Parameters

**`use_color: bool = True`**
- Controls ANSI color code output
- **Automatically disabled if not TTY:** `use_color and sys.stdout.isatty()`
- Affects: All color codes in labels

**`verbose: bool = False`**
- Controls `info()` message visibility
- When False: `info()` messages are suppressed
- When True: All messages print (except if quiet)

**`quiet: bool = False`**
- Minimal output mode (errors only)
- When True: Only `error()` messages print
- Suppresses: action, success, info, warning, header, detail, result, blank, item

### Typical CLI Initialization

```python
printer = PrettyPrinter(
    use_color=not args.no_color,  # From --no-color flag
    verbose=args.verbose,          # From -v/--verbose flag
    quiet=args.quiet               # From -q/--quiet flag
)
```

---

## Usage Pattern Catalog

### Pattern 1: CLI Progress Reporting

**Frequency:** 18 CLI modules

**Pattern:**
```python
def cmd_generate(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    printer.action("Starting code documentation generation...")

    # Work happens here
    generator = DocumentationGenerator()
    result = generator.generate(args.directory)

    printer.success("Documentation generated successfully")
    printer.result("Files Processed", str(result.file_count))
    printer.result("Output Path", str(result.output_path))

    return 0
```

**Characteristics:**
- action() at start
- success() at completion
- result() for key metrics
- Return code based on success/failure

---

### Pattern 2: Error Handling

**Frequency:** All CLI modules

**Pattern:**
```python
def _handle_error(args: argparse.Namespace, printer: PrettyPrinter, exc: Exception) -> int:
    if getattr(args, 'json', False):
        # JSON mode bypasses printer
        _dump_json({"status": "error", "message": str(exc)})
    else:
        # Human-readable mode uses printer
        printer.error(str(exc))
    return 1
```

**Characteristics:**
- Check for JSON mode first
- Use error() for human output
- Always return non-zero exit code

---

### Pattern 3: Verbose Details

**Frequency:** ~50+ uses

**Pattern:**
```python
printer.action("Analyzing dependencies...")
printer.info(f"Scanning {len(files)} files")  # Only if --verbose
printer.info(f"Found {dep_count} dependencies")
printer.success("Analysis complete")
```

**Characteristics:**
- info() for intermediate progress
- Only visible with --verbose flag
- Provides transparency without overwhelming output

---

### Pattern 4: Structured Hierarchical Output

**Frequency:** Progress reports, summaries

**Pattern:**
```python
printer.header("Spec Progress Report")
printer.blank()

printer.result("Total Tasks", str(total))
printer.result("Completed", str(completed), indent=1)
printer.result("In Progress", str(in_progress), indent=1)
printer.result("Pending", str(pending), indent=1)

printer.blank()
printer.detail("Current Phase: Authentication Service")
printer.detail("Next Task: task-2-3", indent=1)
```

**Characteristics:**
- header() for sections
- blank() for spacing
- result() for metrics
- detail() for context
- indent parameter for hierarchy

---

### Pattern 5: List Presentation

**Frequency:** Task lists, file lists

**Pattern:**
```python
printer.header("Blocked Tasks")
printer.blank()

for task in blocked_tasks:
    printer.item(f"task-{task.id}: {task.title}")
    printer.detail(f"Blocked by: {task.blocker}", indent=2)
    printer.blank()
```

**Characteristics:**
- item() for list entries
- detail() for additional context
- blank() between entries

---

### Pattern 6: Optional Printer (AI Consultation)

**Frequency:** 3 AI consultation modules

**Pattern:**
```python
def consult_tool(
    tool_name: str,
    printer: Optional['PrettyPrinter'] = None
) -> Dict[str, any]:
    if printer:
        printer.action(f"Consulting {tool_name}...")
    else:
        print(f"Consulting {tool_name}...")

    # ... tool invocation ...

    if printer:
        printer.success("Consultation complete")
```

**Characteristics:**
- Optional printer parameter
- Fallback to print() if None
- Used in functions called from different contexts

---

### Pattern 7: JSON Mode Bypass

**Frequency:** All CLI modules with --json flag

**Pattern:**
```python
def _print_if_json(args: argparse.Namespace, payload: object, printer: PrettyPrinter) -> bool:
    if getattr(args, 'json', False):
        _dump_json(payload)
        return True  # Skip further output
    return False  # Continue with printer output

# Usage:
if not _print_if_json(args, result_data, printer):
    printer.success("Operation completed")
    printer.result("Key", "Value")
```

**Characteristics:**
- Check JSON mode first
- Dump structured data if JSON
- Use printer only if human-readable mode
- Return bool to control flow

---

## Interface Gaps Analysis

### Gap 1: Imperative-Only Model

**Current Limitation:**
All methods immediately print to stdout/stderr. No way to collect messages for later rendering.

**Impact:**
- Agent can't preview output before showing user
- No way to suppress output temporarily
- Can't collect messages for structured analysis
- No batching or aggregation support

**Example Scenario:**
```python
# Current: Messages print immediately
printer.action("Step 1")
printer.action("Step 2")
printer.action("Step 3")

# Agent Need: Collect messages, then decide what to show
messages = printer.collect([
    ("action", "Step 1"),
    ("action", "Step 2"),
    ("action", "Step 3")
])
# Analyze messages, filter, then render
```

---

### Gap 2: No Structured Data Capture

**Current Limitation:**
Messages are formatted strings with no associated metadata.

**Impact:**
- Can't extract structured data from output
- No timestamp or context tracking
- Can't filter or search messages
- No support for machine-readable logs

**Example Scenario:**
```python
# Current: String-only
printer.result("Status", "completed")

# Agent Need: Structured data
printer.result("Status", "completed", metadata={
    "timestamp": datetime.now(),
    "task_id": "task-2-1",
    "duration": 120.5
})
```

---

### Gap 3: No Progress/Streaming Support

**Current Limitation:**
No support for updating previous lines or showing progress.

**Impact:**
- Can't show spinners or progress bars
- Can't update status in-place
- Verbose output clutters terminal
- No visual feedback for long operations

**Example Need:**
```python
# Spinner for long operation
with printer.spinner("Analyzing 1000 files..."):
    analyze()

# Progress bar
for file in files:
    printer.progress(current=i, total=len(files))
```

---

### Gap 4: Limited Contextual Information

**Current Limitation:**
No way to associate messages with context (task ID, phase, operation).

**Impact:**
- Hard to filter messages by context
- Can't group related messages
- No support for nested operations
- Can't trace message flow

**Example Need:**
```python
# Context manager for operations
with printer.context(task_id="task-2-1", phase="implementation"):
    printer.action("Starting work")
    # All messages auto-tagged with context
    printer.success("Completed")
```

---

### Gap 5: No Agent Decision Support

**Current Limitation:**
No way to mark messages for agent attention or decision points.

**Impact:**
- Agent can't distinguish routine vs important messages
- No way to flag messages requiring action
- Can't prioritize message review
- No support for agent workflows

**Example Need:**
```python
# Mark important messages
printer.action("Proceeding with refactor", priority="high")
printer.warning("Breaking change detected", requires_decision=True)

# Agent can query: "Show me all messages requiring decisions"
decisions = printer.get_messages(requires_decision=True)
```

---

### Gap 6: TTY Detection Limitations

**Current Issue:**
TTY detection disables colors in non-interactive contexts (tests, CI, agents).

**Impact:**
- Tests can't verify exact output format
- CI logs lose semantic information
- Agents may get unexpected output
- Integration tests skip output verification

**From Code Comments:**
```python
# tests/integration/test_sdd_plan_review_integration.py:127
# Note: Output verification skipped due to PrettyPrinter TTY detection
```

**Need:**
- Explicit output mode control (force color, force plain, force structured)
- Separate TTY detection from formatting decisions

---

## Enhancement Requirements

Based on gap analysis, here are the required enhancements for agent-first TUI:

### Enhancement 1: Deferred Rendering Mode

**Requirement:**
Support collecting messages without immediate output, then rendering later.

**API Proposal:**
```python
# Enable collection mode
printer = PrettyPrinter(mode="collect")  # vs "immediate" (default)

# Messages are collected, not printed
printer.action("Step 1")
printer.success("Done")

# Get collected messages
messages = printer.get_messages()  # List[Message]

# Render explicitly
printer.render()  # Now prints

# Clear buffer
printer.clear()
```

**Backward Compatibility:**
- Default mode="immediate" preserves current behavior
- Existing code works without changes

---

### Enhancement 2: Structured Message Objects

**Requirement:**
Each message should have metadata for analysis and filtering.

**API Proposal:**
```python
@dataclass
class Message:
    level: str  # "action", "success", "error", etc.
    text: str
    timestamp: datetime
    context: Dict[str, Any]  # task_id, phase, etc.
    metadata: Dict[str, Any]  # custom data

# Access messages as structured data
for msg in printer.get_messages():
    if msg.level == "error":
        # Handle error
        pass
```

**Backward Compatibility:**
- Internal change only
- Existing methods continue to work

---

### Enhancement 3: Context Management

**Requirement:**
Support associating messages with context (task, phase, operation).

**API Proposal:**
```python
# Context manager
with printer.context(task_id="task-2-1", phase="implementation"):
    printer.action("Starting")  # Auto-tagged with context
    printer.success("Done")     # Auto-tagged with context

# Or explicit
printer.set_context(task_id="task-2-1")
printer.action("Working")
printer.clear_context()
```

**Backward Compatibility:**
- Optional feature
- Works alongside existing code

---

### Enhancement 4: Message Filtering & Query

**Requirement:**
Agent needs to query messages by criteria.

**API Proposal:**
```python
# Get messages by level
errors = printer.get_messages(level="error")

# Get messages by context
task_messages = printer.get_messages(context={"task_id": "task-2-1"})

# Get messages requiring decisions
decisions = printer.get_messages(requires_decision=True)

# Time-based queries
recent = printer.get_messages(since=datetime.now() - timedelta(minutes=5))
```

**Backward Compatibility:**
- New methods, don't affect existing

---

### Enhancement 5: Output Mode Control

**Requirement:**
Explicit control over output format, separate from TTY detection.

**API Proposal:**
```python
printer = PrettyPrinter(
    output_mode="auto",     # Auto-detect (current behavior)
    # OR
    output_mode="color",    # Force color codes
    # OR
    output_mode="plain",    # Force plain text
    # OR
    output_mode="structured"  # JSON-like structured output
)
```

**Backward Compatibility:**
- Default "auto" preserves current behavior
- Explicit modes for tests and agents

---

### Enhancement 6: Progress Indicators (Future)

**Requirement:**
Support for spinners and progress bars (Phase 2 consideration).

**API Proposal:**
```python
# Spinner
with printer.spinner("Processing..."):
    do_work()

# Progress bar
for i, item in enumerate(items):
    printer.progress(current=i+1, total=len(items), label=f"Processing {item}")
```

**Note:** This may require Rich integration or custom implementation.

---

## Backward Compatibility Requirements

### Critical Constraints

1. **All 10 methods must remain unchanged**
   - Signatures must not change
   - Behavior must be identical in default mode
   - Return types must match (currently all `None`)

2. **Initialization parameters must be backward compatible**
   - Existing `use_color`, `verbose`, `quiet` must work
   - New parameters must be optional with safe defaults

3. **Output must be identical in default mode**
   - Same emoji, same colors, same formatting
   - Same stdout vs stderr routing
   - Same TTY detection behavior

4. **Import path must remain the same**
   - `from claude_skills.common import PrettyPrinter`
   - No namespace changes

### Testing for Backward Compatibility

**Required tests:**
```python
def test_backward_compatibility_action():
    """Verify action() output unchanged."""
    printer = PrettyPrinter(use_color=False)
    # Capture output
    # Assert exact match with current behavior

def test_backward_compatibility_all_methods():
    """Verify all 10 methods produce expected output."""
    # Test each method
```

---

## Test Coverage Requirements

### Current Test Coverage

**Existing tests:** 15 test files reference PrettyPrinter

**Test categories:**
1. Unit tests for PrettyPrinter class
2. CLI integration tests using PrettyPrinter
3. Workflow tests with output validation

**Known limitations:**
- TTY detection makes output verification difficult
- Some tests skip output validation (comments indicate this)
- Tests often use `quiet=True` to suppress output

### Required New Tests

**For enhancements:**

1. **Collection Mode Tests**
   ```python
   def test_collection_mode():
       printer = PrettyPrinter(mode="collect")
       printer.action("test")
       messages = printer.get_messages()
       assert len(messages) == 1
       assert messages[0].level == "action"
   ```

2. **Context Management Tests**
   ```python
   def test_context_manager():
       printer = PrettyPrinter(mode="collect")
       with printer.context(task_id="task-1"):
           printer.action("work")
       messages = printer.get_messages()
       assert messages[0].context["task_id"] == "task-1"
   ```

3. **Message Query Tests**
   ```python
   def test_message_filtering():
       printer = PrettyPrinter(mode="collect")
       printer.action("a")
       printer.error("b")
       errors = printer.get_messages(level="error")
       assert len(errors) == 1
   ```

4. **Output Mode Tests**
   ```python
   def test_output_mode_plain():
       printer = PrettyPrinter(output_mode="plain")
       # Verify no ANSI codes in output
   ```

5. **Backward Compatibility Suite**
   ```python
   def test_default_behavior_unchanged():
       # Verify default mode matches current behavior
       # Test all 10 methods
   ```

---

## Implementation Priorities

### Phase 1: Foundation (Current Phase)

1. ✅ Audit current usage (task-1-1-1)
2. ✅ Document interface requirements (task-1-1-2)
3. ⏳ Decide on enhancement approach (task-1-2)

### Phase 2: Agent-First Enhancements

**High Priority:**
- Collection mode (deferred rendering)
- Structured message objects
- Output mode control (fix TTY issues)

**Medium Priority:**
- Context management
- Message filtering/query

**Low Priority (Future):**
- Progress indicators (may need Rich or custom)
- Advanced formatting

---

## Summary

### Core Requirements

**MUST Preserve:**
- All 10 public methods with exact signatures
- Current output format in default mode
- stdout/stderr routing
- TTY detection behavior
- Import path: `claude_skills.common.PrettyPrinter`

**MUST Add (Agent-First):**
- Collection mode for deferred rendering
- Structured message objects with metadata
- Message query and filtering
- Explicit output mode control

**SHOULD Add (Nice to Have):**
- Context management
- Progress indicators
- Enhanced formatting options

**Backward Compatibility:**
- 100% compatibility in default mode
- New features are opt-in
- Existing code works without changes

---

## Next Steps

This requirements document informs **task-1-2** (decision point):

**Decision:** How to enhance PrettyPrinter for agent-first TUI?

**Options:**
1. Enhance custom PrettyPrinter with agent-first features (recommended based on audit)
2. Integrate Rich library for advanced features
3. Hybrid approach (custom + Rich for specific needs)

**Recommendation:** Option 1 (enhance custom) based on:
- No existing Rich dependency
- Custom class already agent-friendly
- Full control over behavior
- Smaller dependency footprint
- Simpler testing

