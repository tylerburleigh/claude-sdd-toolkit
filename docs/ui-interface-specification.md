# Ui Interface Specification

**Date:** 2025-11-06 (Updated: 2025-11-06)
**Task:** task-1-2-1 - Define Ui interface methods based on usage analysis
**Spec:** AI-Agent-First TUI Upgrade (tui-upgrade-2025-11-06-001)
**Related Documents:**
- [TUI Implementation Decision Record](./tui-implementation-decision.md)
- [PrettyPrinter Audit Results](./prettyprinter-audit-results.md) (Background Research)
- [PrettyPrinter Interface Requirements](./prettyprinter-interface-requirements.md) (Background Research)

---

## Executive Summary

This document defines the **Ui interface** - a unified, agent-first abstraction for terminal user interface operations in the SDD toolkit, powered by the [Rich library](https://github.com/Textualize/rich).

**Key Decisions:**
1. **Rich-Powered** - Uses Rich library for tables, trees, progress bars, panels, and styled output
2. **Agent-First** - Supports both immediate and deferred rendering for AI workflows
3. **Dual Backend** - RichUi for rich terminals, PlainUi for non-TTY fallback
4. **Protocol-Based** - Type-safe interface using Python Protocol (PEP 544)
5. **Backward Compatible** - Existing PrettyPrinter remains unchanged

---

## Table of Contents

1. [Design Rationale](#design-rationale)
2. [Interface Definition](#interface-definition)
3. [Rich-Powered Methods](#rich-powered-methods)
4. [Implementation Strategy](#implementation-strategy)
5. [Usage Examples](#usage-examples)
6. [Testing Requirements](#testing-requirements)

---

## Design Rationale

### Why Rich?

**Background:** Phase 1 investigation (tasks 1-1-1, 1-1-2) analyzed the existing custom `PrettyPrinter` class used across 49 files. The audit revealed:
- No existing Rich dependency
- Simple text-based output (10 methods: action, success, info, warning, error, etc.)
- Missing advanced TUI features (tables, trees, progress bars)

**Decision:** Adopt Rich library instead of enhancing PrettyPrinter.

**Rationale:**
- ✅ **Rich Feature Set** - Tables, trees, progress bars, panels, syntax highlighting
- ✅ **Battle-Tested** - 47K+ GitHub stars, used by pandas, pytest, poetry
- ✅ **Agent-Friendly** - Console API perfect for conditional/captured rendering
- ✅ **Minimal Migration** - PrettyPrinter stays unchanged (no breaking changes)
- ✅ **Extensible** - Many additional features available (live displays, logging, etc.)

See [TUI Implementation Decision Record](./tui-implementation-decision.md) for full details.

---

## Interface Definition

### Design Principles

1. **Rich-First** - Leverage Rich's capabilities for modern TUI
2. **Agent-Centric** - Support immediate and deferred rendering modes
3. **Simple API** - Easy to use for common cases
4. **Type-Safe** - Full type hints for IDE support
5. **Testable** - Clean abstraction for mocking and testing

### Protocol Definition

**Implementation:** Use `typing.Protocol` (PEP 544) for structural subtyping.

**Benefits:**
- ✅ No explicit inheritance required
- ✅ RichUi and PlainUi can have different implementations
- ✅ Duck typing compatibility
- ✅ Type checking without runtime overhead

```python
from typing import Protocol, Optional, List, Dict, Any, runtime_checkable

@runtime_checkable
class Ui(Protocol):
    """
    Agent-first terminal user interface protocol using Rich.

    Provides Rich-powered TUI features for modern terminal output.
    """

    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Display data as a formatted table."""
        ...

    def print_tree(
        self,
        data: Dict[str, Any],
        label: str = "Root",
        **kwargs: Any
    ) -> None:
        """Display hierarchical data as a tree."""
        ...

    def print_diff(
        self,
        old_text: str,
        new_text: str,
        old_label: str = "Original",
        new_label: str = "Modified",
        **kwargs: Any
    ) -> None:
        """Display text differences with syntax highlighting."""
        ...

    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Create progress context manager."""
        ...

    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "default",
        **kwargs: Any
    ) -> None:
        """Display content in a bordered panel."""
        ...

    def print_status(
        self,
        message: str,
        level: MessageLevel = MessageLevel.INFO,
        **kwargs: Any
    ) -> None:
        """Print a styled status message."""
        ...
```

**Full protocol definition:** `src/claude_skills/claude_skills/common/ui_protocol.py`

---

## Rich-Powered Methods

### 1. print_table()

**Purpose:** Display tabular data with automatic formatting.

**Rich Component:** `rich.table.Table`

**Example:**
```python
ui.print_table(
    [
        {"task": "task-1-1", "status": "completed", "progress": "100%"},
        {"task": "task-1-2", "status": "in_progress", "progress": "50%"},
        {"task": "task-1-3", "status": "pending", "progress": "0%"}
    ],
    title="Task Status",
    columns=["task", "status", "progress"]
)
```

**Output:**
```
┏━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Task     ┃ Status      ┃ Progress ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ task-1-1 │ completed   │ 100%     │
│ task-1-2 │ in_progress │ 50%      │
│ task-1-3 │ pending     │ 0%       │
└──────────┴─────────────┴──────────┘
```

**Use Cases:**
- Task progress summaries
- Dependency status tables
- Test result matrices
- File/path listings

---

### 2. print_tree()

**Purpose:** Display hierarchical data structures with visual branching.

**Rich Component:** `rich.tree.Tree`

**Example:**
```python
ui.print_tree(
    {
        "phase-1": {
            "task-1-1": {},
            "task-1-2": {
                "task-1-2-1": {},
                "task-1-2-2": {}
            }
        },
        "phase-2": {
            "task-2-1": {}
        }
    },
    label="Spec Hierarchy"
)
```

**Output:**
```
Spec Hierarchy
├── phase-1
│   ├── task-1-1
│   └── task-1-2
│       ├── task-1-2-1
│       └── task-1-2-2
└── phase-2
    └── task-2-1
```

**Use Cases:**
- Spec hierarchy visualization
- Dependency graphs
- File system structures
- Task breakdown displays

---

### 3. print_diff()

**Purpose:** Display text differences with syntax highlighting.

**Rich Component:** `rich.syntax.Syntax` + diff algorithms

**Example:**
```python
ui.print_diff(
    old_text='status: "pending"',
    new_text='status: "completed"',
    old_label="Before",
    new_label="After"
)
```

**Output:**
```
━━━ Before ━━━
status: "pending"

━━━ After ━━━
status: "completed"
       ^^^^^^^^^^
```

**Use Cases:**
- Spec modifications review
- Task status changes
- Configuration updates
- Journal entry comparisons

---

### 4. progress()

**Purpose:** Show progress bars and spinners for long operations.

**Rich Component:** `rich.progress.Progress`

**Example:**
```python
with ui.progress("Processing tasks...", total=10) as prog:
    for i in range(10):
        process_task(i)
        prog.update(1)

# Indeterminate spinner
with ui.progress("Validating spec...") as prog:
    validate()
```

**Output:**
```
Processing tasks... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 70% 7/10
```

**Use Cases:**
- File processing loops
- Batch operations
- Long-running validations
- Multi-step workflows

---

### 5. print_panel()

**Purpose:** Display content in bordered panels with optional styling.

**Rich Component:** `rich.panel.Panel`

**Example:**
```python
ui.print_panel(
    "Task completed successfully!",
    title="Success",
    style="success"
)

ui.print_panel(
    "Missing dependency: task-2-1 must complete first",
    title="Blocked",
    style="warning"
)
```

**Output:**
```
╭─────────── Success ───────────╮
│ Task completed successfully!  │
╰───────────────────────────────╯

╭─────────── Blocked ───────────╮
│ Missing dependency: task-2-1  │
│ must complete first           │
╰───────────────────────────────╯
```

**Use Cases:**
- Success/error notifications
- Warnings and alerts
- Highlighted information
- Call-out boxes

---

### 6. print_status()

**Purpose:** Print styled status messages with severity levels.

**Rich Component:** `rich.console.Console` with styling

**Example:**
```python
ui.print_status("Validating spec...", level=MessageLevel.ACTION)
ui.print_status("Validation passed!", level=MessageLevel.SUCCESS)
ui.print_status("Warning: Missing metadata", level=MessageLevel.WARNING)
ui.print_status("Error: Invalid task ID", level=MessageLevel.ERROR)
```

**Output:**
```
🔵 Validating spec...
✅ Validation passed!
⚠️  Warning: Missing metadata
❌ Error: Invalid task ID
```

**Use Cases:**
- Operation progress updates
- Status notifications
- Error/warning reporting
- Agent feedback messages

---

## Implementation Strategy

### Dual Backend Architecture

```
┌─────────────────────────────────────────┐
│          Ui Protocol                     │
│  (defines interface, no implementation)  │
└─────────────────────────────────────────┘
                  ▲
                  │ implements
        ┌─────────┴─────────┐
        │                   │
┌───────┴─────────┐  ┌──────┴────────┐
│     RichUi      │  │   PlainUi     │
│                 │  │               │
│ • Rich Console  │  │ • Plain text  │
│ • Rich Table    │  │ • ASCII boxes │
│ • Rich Tree     │  │ • Simple      │
│ • Rich Progress │  │   progress    │
│ • Rich Panel    │  │ • Basic fmt   │
└─────────────────┘  └───────────────┘
```

### RichUi Implementation

**Purpose:** Full-featured Rich-powered backend for interactive terminals.

**Dependencies:**
- `rich.console.Console`
- `rich.table.Table`
- `rich.tree.Tree`
- `rich.progress.Progress`
- `rich.panel.Panel`

**Location:** `src/claude_skills/claude_skills/common/rich_ui.py`

**Key Features:**
- Auto-detects TTY for color/formatting
- Supports Rich's full feature set
- Handles Unicode and emoji
- Live displays and updates

---

### PlainUi Implementation

**Purpose:** Fallback backend for non-TTY environments (tests, CI, piped output).

**Dependencies:** None (stdlib only)

**Location:** `src/claude_skills/claude_skills/common/plain_ui.py`

**Key Features:**
- ASCII-only output (no Unicode)
- Simple box drawing (|, -, +)
- Text-based progress indicators
- No color codes
- Deterministic output for testing

---

### Factory Pattern

**Purpose:** Auto-select backend based on environment.

```python
from claude_skills.common import create_ui

# Auto-detect best backend
ui = create_ui()  # Returns RichUi if TTY, else PlainUi

# Explicit backend
ui = create_ui(backend="rich")  # Force RichUi
ui = create_ui(backend="plain")  # Force PlainUi
```

**Implementation:** `src/claude_skills/claude_skills/common/ui_factory.py`

---

## Usage Examples

### Example 1: CLI Command with Progress

```python
from claude_skills.common import create_ui

def validate_spec_command(spec_path: str) -> int:
    ui = create_ui()

    ui.print_status("Starting validation...", level=MessageLevel.ACTION)

    tasks = load_tasks(spec_path)

    with ui.progress("Validating tasks...", total=len(tasks)) as prog:
        errors = []
        for task in tasks:
            result = validate_task(task)
            if not result.valid:
                errors.append(result.error)
            prog.update(1)

    if errors:
        ui.print_panel(
            "\n".join(errors),
            title="Validation Errors",
            style="error"
        )
        return 1

    ui.print_status("Validation passed!", level=MessageLevel.SUCCESS)
    return 0
```

---

### Example 2: Hierarchical Display

```python
from claude_skills.common import create_ui

def show_spec_hierarchy(spec_path: str):
    ui = create_ui()
    spec = load_spec(spec_path)

    # Build hierarchy
    hierarchy = {}
    for phase in spec.phases:
        hierarchy[phase.id] = {
            task.id: {} for task in phase.tasks
        }

    ui.print_tree(hierarchy, label=f"Spec: {spec.title}")
```

---

### Example 3: Progress Summary Table

```python
from claude_skills.common import create_ui

def show_progress_summary(spec_path: str):
    ui = create_ui()
    spec = load_spec(spec_path)

    data = [
        {
            "phase": phase.id,
            "completed": phase.completed_tasks,
            "total": phase.total_tasks,
            "percentage": f"{phase.completion_percentage}%"
        }
        for phase in spec.phases
    ]

    ui.print_table(
        data,
        title=f"Progress: {spec.title}",
        columns=["phase", "completed", "total", "percentage"]
    )
```

---

## Testing Requirements

### Protocol Compliance Tests

**Verify both implementations satisfy Ui protocol:**

```python
def test_richui_implements_protocol():
    from claude_skills.common import RichUi, Ui
    ui = RichUi()
    assert isinstance(ui, Ui)

def test_plainui_implements_protocol():
    from claude_skills.common import PlainUi, Ui
    ui = PlainUi()
    assert isinstance(ui, Ui)
```

---

### Rich Output Tests

**Test RichUi produces Rich-formatted output:**

```python
def test_richui_print_table(capsys):
    ui = RichUi()
    ui.print_table([{"a": "1", "b": "2"}])

    output = capsys.readouterr().out
    assert "┃" in output  # Rich box characters
    assert "━" in output

def test_richui_print_tree(capsys):
    ui = RichUi()
    ui.print_tree({"child": {}}, label="Root")

    output = capsys.readouterr().out
    assert "Root" in output
    assert "child" in output
```

---

### Plain Output Tests

**Test PlainUi produces ASCII-only output:**

```python
def test_plainui_print_table(capsys):
    ui = PlainUi()
    ui.print_table([{"a": "1", "b": "2"}])

    output = capsys.readouterr().out
    assert "|" in output  # ASCII pipes
    assert "-" in output
    assert "┃" not in output  # No Unicode

def test_plainui_print_tree(capsys):
    ui = PlainUi()
    ui.print_tree({"child": {}}, label="Root")

    output = capsys.readouterr().out
    assert "Root" in output
    assert "child" in output
    assert all(ord(c) < 128 for c in output)  # ASCII only
```

---

### Factory Tests

**Test auto-detection:**

```python
def test_factory_detects_tty(monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = create_ui()
    assert isinstance(ui, RichUi)

def test_factory_fallback_no_tty(monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    ui = create_ui()
    assert isinstance(ui, PlainUi)

def test_factory_explicit_backend():
    ui = create_ui(backend="rich")
    assert isinstance(ui, RichUi)

    ui = create_ui(backend="plain")
    assert isinstance(ui, PlainUi)
```

---

## Migration Notes

### Relationship with PrettyPrinter

**PrettyPrinter Status:** The existing custom `PrettyPrinter` class (used in 49 files) remains **unchanged** and fully supported.

**Migration Strategy:**
- **No forced migration** - PrettyPrinter continues working
- **New code** - Use `Ui` interface (via `create_ui()`)
- **High-value modules** - Selectively migrate to leverage Rich features
- **Gradual transition** - Both systems coexist indefinitely

**When to use each:**
- **PrettyPrinter** - Existing code, simple text output, backward compatibility
- **Ui (Rich)** - New code, tables/trees/progress needed, modern TUI desired

---

## References

- [Rich Library Documentation](https://rich.readthedocs.io/)
- [TUI Implementation Decision Record](./tui-implementation-decision.md)
- [PrettyPrinter Audit Results](./prettyprinter-audit-results.md)
- [PrettyPrinter Interface Requirements](./prettyprinter-interface-requirements.md)

---

**Document Status:** Revised to reflect Rich-based implementation (2025-11-06)
