# Ui Interface Specification

**Date:** 2025-11-06
**Task:** task-1-2-1 - Define Ui interface methods based on usage analysis
**Spec:** AI-Agent-First TUI Upgrade (tui-upgrade-2025-11-06-001)
**Related Documents:**
- [PrettyPrinter Audit Results](./prettyprinter-audit-results.md)
- [PrettyPrinter Interface Requirements](./prettyprinter-interface-requirements.md)

---

## Executive Summary

This document defines the **Ui interface** - a unified, agent-first abstraction for terminal user interface operations in the SDD toolkit. The Ui interface:

1. **Preserves** all existing PrettyPrinter functionality (100% backward compatible)
2. **Adds** agent-first capabilities (deferred rendering, structured data, context management)
3. **Provides** a clean abstraction for future TUI enhancements
4. **Enables** gradual migration without breaking existing code

**Key Design Decision:** Use Python Protocol for maximum flexibility, with PrettyPrinter implementing Ui via an adapter pattern.

---

## Table of Contents

1. [Interface Design](#interface-design)
2. [Core Methods (PrettyPrinter Compatibility)](#core-methods-prettyprinter-compatibility)
3. [Agent-First Extensions](#agent-first-extensions)
4. [Implementation Strategy](#implementation-strategy)
5. [Usage Examples](#usage-examples)
6. [Migration Plan](#migration-plan)
7. [Testing Requirements](#testing-requirements)

---

## Interface Design

### Design Principles

1. **Backward Compatibility First** - Existing code must work unchanged
2. **Agent-Centric** - Support both immediate and deferred rendering
3. **Simple by Default** - Easy to use for common cases
4. **Extensible** - Support advanced use cases without complexity
5. **Type-Safe** - Full type hints for IDE support

### Interface Type: Protocol

**Decision:** Use `typing.Protocol` (PEP 544) for structural subtyping.

**Rationale:**
- ✅ Flexible - Classes can implement Ui without explicit inheritance
- ✅ Gradual typing - PrettyPrinter already implements most methods
- ✅ Duck typing - Works with existing code patterns
- ✅ No runtime overhead - Pure type checking

**Alternative Considered:** Abstract Base Class (abc.ABC)
- ❌ Requires explicit inheritance
- ❌ Less flexible for existing code
- ✅ Runtime type checking (but not needed)

---

## Core Methods (PrettyPrinter Compatibility)

### Protocol Definition

```python
from typing import Protocol, Optional, Any, Dict, List
from datetime import datetime
from enum import Enum

class MessageLevel(Enum):
    """Message severity/type levels."""
    ACTION = "action"      # In-progress operation
    SUCCESS = "success"    # Completed successfully
    INFO = "info"          # Informational detail
    WARNING = "warning"    # Non-blocking issue
    ERROR = "error"        # Blocking issue
    DETAIL = "detail"      # Additional context
    RESULT = "result"      # Key-value output
    ITEM = "item"          # List item
    HEADER = "header"      # Section header
    BLANK = "blank"        # Spacing


class Ui(Protocol):
    """
    Agent-first terminal user interface protocol.

    Provides immediate and deferred rendering modes, structured message
    collection, and context management for AI-agent workflows.

    All implementations must support:
    1. 10 core output methods (PrettyPrinter compatibility)
    2. Message collection in deferred mode
    3. Context management for message tagging
    """

    # ================================================================
    # Core Output Methods (PrettyPrinter Compatibility)
    # ================================================================

    def action(self, msg: str) -> None:
        """
        Print an action message (what's being done now).

        Args:
            msg: Action description

        Example:
            ui.action("Processing task task-2-1...")
        """
        ...

    def success(self, msg: str) -> None:
        """
        Print a success message (completed action).

        Args:
            msg: Success description

        Example:
            ui.success("Task completed successfully")
        """
        ...

    def info(self, msg: str) -> None:
        """
        Print an informational message (context/details).

        Only prints in verbose mode.

        Args:
            msg: Information to display

        Example:
            ui.info("Checking 15 dependency files...")
        """
        ...

    def warning(self, msg: str) -> None:
        """
        Print a warning message (non-blocking issue).

        Prints to stderr.

        Args:
            msg: Warning description

        Example:
            ui.warning("Deprecated configuration format detected")
        """
        ...

    def error(self, msg: str) -> None:
        """
        Print an error message (blocking issue).

        Prints to stderr. Always prints (ignores quiet mode).

        Args:
            msg: Error description

        Example:
            ui.error("Spec file not found")
        """
        ...

    def header(self, msg: str) -> None:
        """
        Print a section header.

        Args:
            msg: Header text

        Example:
            ui.header("Spec Validation Report")
        """
        ...

    def detail(self, msg: str, indent: int = 1) -> None:
        """
        Print an indented detail line.

        Args:
            msg: Detail text
            indent: Indentation level (default: 1)

        Example:
            ui.detail("Status: pending", indent=1)
        """
        ...

    def result(self, key: str, value: str, indent: int = 0) -> None:
        """
        Print a key-value result.

        Args:
            key: Result key
            value: Result value
            indent: Indentation level (default: 0)

        Example:
            ui.result("Total Tasks", "23")
        """
        ...

    def blank(self) -> None:
        """
        Print a blank line.

        Example:
            ui.blank()
        """
        ...

    def item(self, msg: str, indent: int = 0) -> None:
        """
        Print a list item with bullet point.

        Args:
            msg: Item text
            indent: Indentation level (default: 0)

        Example:
            ui.item("Task 1: Create directory structure")
        """
        ...
```

### Method Mapping from PrettyPrinter

| PrettyPrinter Method | Ui Method | Signature Match | Behavior Match |
|---------------------|-----------|-----------------|----------------|
| `action(msg)` | `action(msg)` | ✅ Exact | ✅ Exact |
| `success(msg)` | `success(msg)` | ✅ Exact | ✅ Exact |
| `info(msg)` | `info(msg)` | ✅ Exact | ✅ Exact |
| `warning(msg)` | `warning(msg)` | ✅ Exact | ✅ Exact |
| `error(msg)` | `error(msg)` | ✅ Exact | ✅ Exact |
| `header(msg)` | `header(msg)` | ✅ Exact | ✅ Exact |
| `detail(msg, indent=1)` | `detail(msg, indent=1)` | ✅ Exact | ✅ Exact |
| `result(key, value, indent=0)` | `result(key, value, indent=0)` | ✅ Exact | ✅ Exact |
| `blank()` | `blank()` | ✅ Exact | ✅ Exact |
| `item(msg, indent=0)` | `item(msg, indent=0)` | ✅ Exact | ✅ Exact |

**Result:** 100% signature compatibility. PrettyPrinter already implements the core Ui interface.

---

## Agent-First Extensions

### Message Data Structure

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Message:
    """
    Structured message with metadata for agent analysis.

    Supports filtering, querying, and deferred rendering.
    """
    level: MessageLevel
    text: str
    timestamp: datetime
    context: Dict[str, Any]  # task_id, phase, operation, etc.
    metadata: Dict[str, Any]  # Custom data
    rendered: bool = False   # Track if message has been displayed

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

### Extended Protocol Methods

```python
class Ui(Protocol):
    """Extended with agent-first capabilities."""

    # ... (core methods above) ...

    # ================================================================
    # Agent-First Extensions
    # ================================================================

    # ----------------------------------------------------------------
    # Rendering Mode Control
    # ----------------------------------------------------------------

    @property
    def mode(self) -> str:
        """
        Get current rendering mode.

        Returns:
            "immediate" - Messages print immediately (default)
            "collect" - Messages are collected for later rendering
        """
        ...

    def set_mode(self, mode: str) -> None:
        """
        Set rendering mode.

        Args:
            mode: "immediate" or "collect"

        Example:
            ui.set_mode("collect")
            ui.action("Step 1")
            ui.action("Step 2")
            messages = ui.get_messages()
            ui.render()  # Render all collected messages
        """
        ...

    # ----------------------------------------------------------------
    # Message Collection & Query
    # ----------------------------------------------------------------

    def get_messages(
        self,
        level: Optional[MessageLevel] = None,
        context: Optional[Dict[str, Any]] = None,
        since: Optional[datetime] = None,
        unrendered_only: bool = False
    ) -> List[Message]:
        """
        Query collected messages.

        Args:
            level: Filter by message level
            context: Filter by context fields (partial match)
            since: Filter by timestamp (messages after this time)
            unrendered_only: Only return messages not yet rendered

        Returns:
            List of matching messages

        Example:
            # Get all errors
            errors = ui.get_messages(level=MessageLevel.ERROR)

            # Get messages for specific task
            task_msgs = ui.get_messages(context={"task_id": "task-2-1"})

            # Get recent messages
            recent = ui.get_messages(since=datetime.now() - timedelta(minutes=5))
        """
        ...

    def clear_messages(self) -> None:
        """
        Clear all collected messages.

        Example:
            ui.clear_messages()
        """
        ...

    def message_count(self, level: Optional[MessageLevel] = None) -> int:
        """
        Count collected messages, optionally filtered by level.

        Args:
            level: Optional level filter

        Returns:
            Message count

        Example:
            error_count = ui.message_count(MessageLevel.ERROR)
        """
        ...

    # ----------------------------------------------------------------
    # Context Management
    # ----------------------------------------------------------------

    def set_context(self, **kwargs: Any) -> None:
        """
        Set context for subsequent messages.

        All messages will be tagged with these context fields
        until context is cleared or changed.

        Args:
            **kwargs: Context key-value pairs

        Example:
            ui.set_context(task_id="task-2-1", phase="implementation")
            ui.action("Starting work")  # Tagged with task_id and phase
        """
        ...

    def update_context(self, **kwargs: Any) -> None:
        """
        Update existing context (merge with current).

        Args:
            **kwargs: Context key-value pairs to add/update

        Example:
            ui.set_context(task_id="task-2-1")
            ui.update_context(phase="testing")  # Keeps task_id, adds phase
        """
        ...

    def clear_context(self) -> None:
        """
        Clear current context.

        Example:
            ui.clear_context()
        """
        ...

    def get_context(self) -> Dict[str, Any]:
        """
        Get current context.

        Returns:
            Current context dictionary
        """
        ...

    def context_manager(self, **kwargs: Any):
        """
        Context manager for temporary context.

        Args:
            **kwargs: Context key-value pairs

        Example:
            with ui.context_manager(task_id="task-2-1"):
                ui.action("Working")  # Tagged with task_id
            # Context automatically cleared
        """
        ...

    # ----------------------------------------------------------------
    # Rendering Control
    # ----------------------------------------------------------------

    def render(
        self,
        messages: Optional[List[Message]] = None,
        clear_after: bool = True
    ) -> None:
        """
        Render collected messages to output.

        Args:
            messages: Specific messages to render (default: all unrendered)
            clear_after: Clear messages after rendering (default: True)

        Example:
            ui.set_mode("collect")
            ui.action("Step 1")
            ui.success("Done")
            ui.render()  # Now prints both messages
        """
        ...

    def render_to_string(
        self,
        messages: Optional[List[Message]] = None
    ) -> str:
        """
        Render messages to string instead of output.

        Args:
            messages: Messages to render (default: all unrendered)

        Returns:
            Rendered output as string

        Example:
            output = ui.render_to_string()
        """
        ...

    # ----------------------------------------------------------------
    # Output Configuration
    # ----------------------------------------------------------------

    def set_output_mode(self, mode: str) -> None:
        """
        Set output formatting mode.

        Args:
            mode: "auto" (default), "color", "plain", or "structured"

        Example:
            ui.set_output_mode("plain")  # Disable colors
        """
        ...
```

---

## Implementation Strategy

### Chosen Approach: Adapter Pattern

**Strategy:** Create a `UiAdapter` that wraps `PrettyPrinter` and implements the full Ui protocol.

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                     Ui Protocol                          │
│  (defines interface, no implementation)                  │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ implements
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────┴─────────┐               ┌────────┴────────┐
│  PrettyPrinter  │               │   UiAdapter     │
│  (legacy impl)  │               │   (full impl)   │
│                 │               │                 │
│ • 10 core       │               │ • Wraps         │
│   methods       │               │   PrettyPrinter │
│ • No extensions │               │ • Adds agent    │
│                 │               │   extensions    │
└─────────────────┘               └─────────────────┘
```

**Benefits:**
- ✅ Zero changes to existing PrettyPrinter
- ✅ Existing code continues working unchanged
- ✅ New code can use UiAdapter for agent features
- ✅ Gradual migration path
- ✅ Both can coexist

**Implementation Files:**

1. **`common/ui_protocol.py`** - Protocol definition, Message class
2. **`common/ui_adapter.py`** - UiAdapter implementation
3. **`common/printer.py`** - PrettyPrinter (unchanged)
4. **`common/__init__.py`** - Export both PrettyPrinter and UiAdapter

---

### UiAdapter Implementation Outline

```python
# common/ui_adapter.py

from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from .ui_protocol import Ui, Message, MessageLevel
from .printer import PrettyPrinter

class UiAdapter:
    """
    Agent-first Ui implementation wrapping PrettyPrinter.

    Provides backward-compatible interface with agent extensions.
    """

    def __init__(
        self,
        use_color: bool = True,
        verbose: bool = False,
        quiet: bool = False,
        mode: str = "immediate"
    ):
        """
        Initialize UiAdapter.

        Args:
            use_color: Enable ANSI colors (auto-disabled if not TTY)
            verbose: Show info messages
            quiet: Minimal output (errors only)
            mode: "immediate" or "collect"
        """
        self._printer = PrettyPrinter(use_color, verbose, quiet)
        self._mode = mode
        self._messages: List[Message] = []
        self._context: Dict[str, Any] = {}
        self._output_mode = "auto"

    # ================================================================
    # Core Methods (delegate to PrettyPrinter)
    # ================================================================

    def action(self, msg: str) -> None:
        """Print action message."""
        self._record_message(MessageLevel.ACTION, msg)
        if self._mode == "immediate":
            self._printer.action(msg)

    def success(self, msg: str) -> None:
        """Print success message."""
        self._record_message(MessageLevel.SUCCESS, msg)
        if self._mode == "immediate":
            self._printer.success(msg)

    # ... (similar for all 10 core methods) ...

    # ================================================================
    # Agent-First Extensions
    # ================================================================

    def _record_message(self, level: MessageLevel, text: str, **metadata):
        """Record message for collection."""
        msg = Message(
            level=level,
            text=text,
            timestamp=datetime.now(),
            context=self._context.copy(),
            metadata=metadata,
            rendered=(self._mode == "immediate")
        )
        self._messages.append(msg)

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in ("immediate", "collect"):
            raise ValueError(f"Invalid mode: {mode}")
        self._mode = mode

    def get_messages(
        self,
        level: Optional[MessageLevel] = None,
        context: Optional[Dict[str, Any]] = None,
        since: Optional[datetime] = None,
        unrendered_only: bool = False
    ) -> List[Message]:
        """Query collected messages."""
        results = self._messages

        if level:
            results = [m for m in results if m.level == level]

        if context:
            results = [
                m for m in results
                if all(m.context.get(k) == v for k, v in context.items())
            ]

        if since:
            results = [m for m in results if m.timestamp >= since]

        if unrendered_only:
            results = [m for m in results if not m.rendered]

        return results

    def set_context(self, **kwargs: Any) -> None:
        """Set context for messages."""
        self._context = kwargs

    def update_context(self, **kwargs: Any) -> None:
        """Update context."""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear context."""
        self._context = {}

    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self._context.copy()

    @contextmanager
    def context_manager(self, **kwargs: Any):
        """Temporary context."""
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context

    def render(
        self,
        messages: Optional[List[Message]] = None,
        clear_after: bool = True
    ) -> None:
        """Render collected messages."""
        if messages is None:
            messages = self.get_messages(unrendered_only=True)

        for msg in messages:
            # Delegate to appropriate printer method
            method = getattr(self._printer, msg.level.value)
            if msg.level in (MessageLevel.DETAIL, MessageLevel.ITEM):
                # Methods with indent parameter
                indent = msg.metadata.get("indent", 0)
                method(msg.text, indent=indent)
            elif msg.level == MessageLevel.RESULT:
                # result() has key/value/indent
                key = msg.metadata.get("key", "")
                indent = msg.metadata.get("indent", 0)
                method(key, msg.text, indent=indent)
            else:
                method(msg.text)

            msg.rendered = True

        if clear_after:
            self._messages = [m for m in self._messages if not m.rendered]

    # ... (other extension methods) ...
```

---

## Usage Examples

### Example 1: Backward Compatible (Existing Code)

```python
# Existing code works unchanged
from claude_skills.common import PrettyPrinter

printer = PrettyPrinter(use_color=True, verbose=False, quiet=False)
printer.action("Starting validation...")
printer.success("Validation passed")
printer.result("Tasks", "23")
```

**Result:** Works exactly as before, no changes needed.

---

### Example 2: Agent-First with UiAdapter

```python
from claude_skills.common import UiAdapter

# Use UiAdapter for agent-first features
ui = UiAdapter(mode="collect", use_color=True)

# Set context for task
with ui.context_manager(task_id="task-2-1", phase="implementation"):
    ui.action("Starting implementation")
    ui.info("Checking dependencies")
    ui.success("Implementation complete")

# Get messages for analysis
messages = ui.get_messages()
error_count = ui.message_count(MessageLevel.ERROR)

# Render when ready
if error_count == 0:
    ui.render()  # Show all messages
else:
    # Show errors immediately
    ui.render(ui.get_messages(level=MessageLevel.ERROR))
```

---

### Example 3: Mixed Mode (Immediate + Collection)

```python
ui = UiAdapter(mode="immediate")

# Immediate output for user feedback
ui.action("Running tests...")

# Collect detailed progress
ui.set_mode("collect")
for test in tests:
    ui.info(f"Running {test.name}")
    result = test.run()
    if result.failed:
        ui.error(f"Test failed: {test.name}")

# Switch back to immediate
ui.set_mode("immediate")

# Final summary (immediate)
ui.success("Test suite completed")

# Analyze collected details
failures = ui.get_messages(level=MessageLevel.ERROR)
ui.result("Failures", str(len(failures)))
```

---

### Example 4: Gradual Migration

```python
# Phase 1: Keep PrettyPrinter, add UiAdapter selectively
def existing_function(printer: PrettyPrinter):
    """Existing code, uses PrettyPrinter."""
    printer.action("Working")
    printer.success("Done")

def new_function(ui: UiAdapter):
    """New code, uses UiAdapter with agent features."""
    with ui.context_manager(operation="new_function"):
        ui.action("Working with context")
        ui.success("Done with metadata")

# Phase 2: Introduce Ui type hint (works with both)
from claude_skills.common import Ui

def flexible_function(ui: Ui):
    """Works with PrettyPrinter OR UiAdapter."""
    ui.action("Working")
    ui.success("Done")
    # Can't use agent extensions (not in PrettyPrinter)

# Phase 3: Type check for extensions
from claude_skills.common import UiAdapter

def smart_function(ui: Ui):
    """Adapts based on capabilities."""
    ui.action("Starting")

    if isinstance(ui, UiAdapter):
        # Use agent features
        ui.set_context(operation="smart_function")
        messages = ui.get_messages()

    ui.success("Done")
```

---

## Migration Plan

### Phase 1: Introduction (Current)

**Goal:** Introduce Ui protocol and UiAdapter without breaking existing code.

**Actions:**
1. ✅ Create `common/ui_protocol.py` (Protocol, Message, MessageLevel)
2. ✅ Create `common/ui_adapter.py` (UiAdapter implementation)
3. ✅ Export from `common/__init__.py`
4. ✅ Keep PrettyPrinter unchanged
5. ✅ Add comprehensive tests for UiAdapter

**Timeline:** Phase 1 of spec (current work)

**Result:** Both PrettyPrinter and UiAdapter available, coexist peacefully.

---

### Phase 2: Selective Adoption (Future)

**Goal:** Use UiAdapter in new code and high-value migrations.

**Candidates for early adoption:**
- AI consultation modules (already use Optional[PrettyPrinter])
- New features developed during Phase 2+
- Modules that would benefit from context (task tracking)

**Actions:**
1. Update AI consultation functions to use UiAdapter
2. Add UiAdapter to new CLI commands
3. Migrate sdd-update workflow (benefits from context)

**Timeline:** Phase 2-3 of spec

**Result:** New code uses UiAdapter, old code continues with PrettyPrinter.

---

### Phase 3: Gradual Migration (Optional, Future)

**Goal:** Migrate remaining PrettyPrinter usage to UiAdapter.

**Priority order:**
1. High-value: Modules with complex output (CLI commands)
2. Medium-value: Workflow modules (sdd-update, sdd-next)
3. Low-value: Simple utility scripts

**Actions:**
1. Change type hints: `PrettyPrinter` → `Ui`
2. Update instantiation: `PrettyPrinter()` → `UiAdapter()`
3. Optionally add agent features (context, collection)
4. Test thoroughly

**Timeline:** Post Phase 3, ongoing

**Result:** Most code uses UiAdapter, PrettyPrinter only for legacy.

---

### Phase 4: Deprecation (Optional, Far Future)

**Goal:** Potentially deprecate PrettyPrinter if fully migrated.

**Considerations:**
- Is PrettyPrinter still used externally?
- Is the migration complete and stable?
- Is the maintenance burden significant?

**Actions:**
1. Add deprecation warnings to PrettyPrinter
2. Update documentation to recommend UiAdapter
3. Eventually remove PrettyPrinter (breaking change)

**Timeline:** TBD (only if needed)

**Result:** Single Ui implementation (UiAdapter).

---

## Testing Requirements

### Test Categories

#### 1. Protocol Compliance Tests

**Verify PrettyPrinter implements Ui protocol:**

```python
def test_prettyprinter_implements_ui_protocol():
    """PrettyPrinter should satisfy Ui protocol."""
    from claude_skills.common import PrettyPrinter, Ui

    printer = PrettyPrinter()
    # Type checker should pass
    _ui: Ui = printer

    # Has all required methods
    assert hasattr(printer, 'action')
    assert hasattr(printer, 'success')
    # ... (all 10 methods)
```

#### 2. UiAdapter Core Method Tests

**Verify delegation to PrettyPrinter:**

```python
def test_uiadapter_action_immediate_mode(capsys):
    """action() in immediate mode should print immediately."""
    ui = UiAdapter(use_color=False, mode="immediate")
    ui.action("Test message")

    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert "Action:" in captured.out

def test_uiadapter_action_collect_mode(capsys):
    """action() in collect mode should not print immediately."""
    ui = UiAdapter(use_color=False, mode="collect")
    ui.action("Test message")

    captured = capsys.readouterr()
    assert captured.out == ""  # Nothing printed yet

    messages = ui.get_messages()
    assert len(messages) == 1
    assert messages[0].level == MessageLevel.ACTION
```

#### 3. Message Collection Tests

```python
def test_message_collection():
    """Messages should be collected with metadata."""
    ui = UiAdapter(mode="collect")

    ui.action("Step 1")
    ui.success("Step 2")
    ui.error("Step 3")

    messages = ui.get_messages()
    assert len(messages) == 3
    assert messages[0].level == MessageLevel.ACTION
    assert messages[1].level == MessageLevel.SUCCESS
    assert messages[2].level == MessageLevel.ERROR

def test_message_filtering_by_level():
    """get_messages() should filter by level."""
    ui = UiAdapter(mode="collect")

    ui.action("A")
    ui.error("E1")
    ui.success("S")
    ui.error("E2")

    errors = ui.get_messages(level=MessageLevel.ERROR)
    assert len(errors) == 2
    assert all(m.level == MessageLevel.ERROR for m in errors)
```

#### 4. Context Management Tests

```python
def test_context_tagging():
    """Messages should be tagged with context."""
    ui = UiAdapter(mode="collect")

    ui.set_context(task_id="task-1", phase="test")
    ui.action("Message 1")
    ui.success("Message 2")

    messages = ui.get_messages()
    assert all(m.context["task_id"] == "task-1" for m in messages)
    assert all(m.context["phase"] == "test" for m in messages)

def test_context_manager():
    """Context manager should temporarily set context."""
    ui = UiAdapter(mode="collect")

    with ui.context_manager(task_id="task-1"):
        ui.action("Inside")

    ui.action("Outside")

    messages = ui.get_messages()
    assert messages[0].context.get("task_id") == "task-1"
    assert messages[1].context.get("task_id") is None
```

#### 5. Rendering Tests

```python
def test_render_collected_messages(capsys):
    """render() should output collected messages."""
    ui = UiAdapter(use_color=False, mode="collect")

    ui.action("Step 1")
    ui.success("Step 2")

    # Nothing printed yet
    captured = capsys.readouterr()
    assert captured.out == ""

    # Render
    ui.render()

    captured = capsys.readouterr()
    assert "Step 1" in captured.out
    assert "Step 2" in captured.out
```

#### 6. Backward Compatibility Tests

```python
def test_backward_compatibility_signatures():
    """All PrettyPrinter methods should have same signature in UiAdapter."""
    from inspect import signature
    from claude_skills.common import PrettyPrinter, UiAdapter

    printer = PrettyPrinter()
    ui = UiAdapter()

    methods = ['action', 'success', 'info', 'warning', 'error',
               'header', 'detail', 'result', 'blank', 'item']

    for method_name in methods:
        printer_sig = signature(getattr(printer, method_name))
        ui_sig = signature(getattr(ui, method_name))
        assert printer_sig == ui_sig, f"Signature mismatch for {method_name}"

def test_backward_compatibility_output(capsys):
    """UiAdapter immediate mode should produce same output as PrettyPrinter."""
    from claude_skills.common import PrettyPrinter, UiAdapter

    # PrettyPrinter output
    printer = PrettyPrinter(use_color=False)
    printer.action("Test")
    printer_output = capsys.readouterr().out

    # UiAdapter output
    ui = UiAdapter(use_color=False, mode="immediate")
    ui.action("Test")
    ui_output = capsys.readouterr().out

    assert printer_output == ui_output
```

---

## Summary

### Key Decisions

1. **Interface Type:** Python Protocol (structural subtyping)
2. **Core Methods:** 10 methods, 100% backward compatible with PrettyPrinter
3. **Agent Extensions:** Message collection, context management, deferred rendering
4. **Implementation:** Adapter pattern wrapping PrettyPrinter
5. **Migration:** Gradual, both systems coexist

### Benefits

✅ **Backward Compatible** - Existing code works unchanged
✅ **Agent-First** - Supports deferred rendering and structured data
✅ **Flexible** - Protocol allows multiple implementations
✅ **Gradual Migration** - No big-bang rewrites required
✅ **Type-Safe** - Full type hints for IDE support

### Next Steps

**Immediate (Phase 1):**
1. Implement `common/ui_protocol.py` (Protocol, Message, MessageLevel)
2. Implement `common/ui_adapter.py` (UiAdapter class)
3. Write comprehensive test suite
4. Update `common/__init__.py` exports
5. Document usage patterns

**Future (Phase 2+):**
1. Adopt UiAdapter in AI consultation modules
2. Use UiAdapter for new CLI commands
3. Migrate high-value modules selectively
4. Consider progress indicators (may need Rich integration)

---

## Appendix: Design Alternatives Considered

### Alternative 1: Make PrettyPrinter Implement Ui Directly

**Approach:** Add agent extensions directly to PrettyPrinter class.

**Pros:**
- Single implementation
- No adapter overhead

**Cons:**
- ❌ Changes existing class (riskier)
- ❌ Mixes concerns (legacy + agent-first)
- ❌ Harder to test in isolation

**Decision:** Rejected - adapter pattern is safer

---

### Alternative 2: Replace PrettyPrinter Entirely

**Approach:** Create new Ui class, deprecate PrettyPrinter.

**Pros:**
- Clean slate
- No legacy baggage

**Cons:**
- ❌ Breaking change for 49 files
- ❌ High migration cost
- ❌ Risk of bugs in all modules

**Decision:** Rejected - too risky, adapter is safer

---

### Alternative 3: Use Rich Library

**Approach:** Adopt Rich library for formatting, wrap in Ui interface.

**Pros:**
- Rich formatting capabilities
- Progress bars, tables, syntax highlighting

**Cons:**
- ❌ New dependency (audit found none currently)
- ❌ Larger footprint
- ❌ Less control over behavior
- ❌ May have TTY detection issues

**Decision:** Deferred - can add later if needed, start with custom

---

**End of Specification**

