"""
Agent-first terminal user interface protocol using Rich library.

This module defines the Ui protocol - a unified, agent-first abstraction
for terminal user interface operations in the SDD toolkit, built on Rich.

Key Features:
- Rich-powered TUI with tables, trees, panels, and progress indicators
- Support for both immediate and deferred rendering modes
- Structured message collection with metadata
- Context management for message tagging
- Type-safe protocol for multiple implementations
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from abc import abstractmethod


class MessageLevel(Enum):
    """
    Message severity/type levels.
    """

    ACTION = "action"  # In-progress operation
    SUCCESS = "success"  # Completed successfully
    INFO = "info"  # Informational detail
    WARNING = "warning"  # Non-blocking issue
    ERROR = "error"  # Blocking issue
    DETAIL = "detail"  # Additional context
    RESULT = "result"  # Key-value output
    ITEM = "item"  # List item
    HEADER = "header"  # Section header
    BLANK = "blank"  # Spacing


@dataclass
class Message:
    """
    Structured message with metadata for agent analysis.

    Supports filtering, querying, and deferred rendering.

    Attributes:
        level: Message severity/type
        text: Message content
        timestamp: When message was created
        context: Task ID, phase, operation, etc.
        metadata: Custom data (indent, key, etc.)
        rendered: Whether message has been displayed
    """

    level: MessageLevel
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    rendered: bool = False


@runtime_checkable
class Ui(Protocol):
    """
    Agent-first terminal user interface protocol using Rich.

    Provides Rich-powered TUI features including tables, trees, panels,
    progress indicators, and diff display. Supports both immediate and
    deferred rendering modes for AI-agent workflows.

    Core Rich Features:
    - print_table: Display data in formatted tables
    - print_tree: Show hierarchical data structures
    - print_diff: Display code/text differences
    - progress: Show progress bars and spinners
    - print_panel: Display content in bordered panels
    - print_status: Show status messages with styling

    All implementations must support:
    1. Rich-powered output methods
    2. Message collection in deferred mode
    3. Context management for message tagging

    Usage:
        # Rich-powered interface
        ui = RichUi()
        ui.print_table(data, title="Task Progress")
        ui.print_tree(hierarchy)

        # With progress tracking
        with ui.progress("Processing tasks...") as progress:
            for task in tasks:
                process(task)
                progress.update()
    """

    # ================================================================
    # Rich-Powered Output Methods
    # ================================================================

    @abstractmethod
    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Print data as a formatted table using Rich Table.

        Args:
            data: List of dictionaries representing rows
            columns: Column names to display (default: all keys from first row)
            title: Optional table title
            **kwargs: Additional Rich Table options (show_header, show_lines, etc.)

        Example:
            ui.print_table(
                [
                    {"task": "task-1-1", "status": "completed", "progress": "100%"},
                    {"task": "task-1-2", "status": "in_progress", "progress": "50%"}
                ],
                title="Task Status"
            )
        """
        ...

    @abstractmethod
    def print_tree(
        self,
        data: Dict[str, Any],
        label: str = "Root",
        **kwargs: Any
    ) -> None:
        """
        Print hierarchical data as a tree using Rich Tree.

        Args:
            data: Nested dictionary representing tree structure
            label: Root node label
            **kwargs: Additional Rich Tree options

        Example:
            ui.print_tree(
                {
                    "phase-1": {
                        "task-1-1": {},
                        "task-1-2": {
                            "task-1-2-1": {},
                            "task-1-2-2": {}
                        }
                    }
                },
                label="Spec Hierarchy"
            )
        """
        ...

    @abstractmethod
    def print_diff(
        self,
        old_text: str,
        new_text: str,
        old_label: str = "Original",
        new_label: str = "Modified",
        **kwargs: Any
    ) -> None:
        """
        Print text difference using syntax highlighting.

        Args:
            old_text: Original text
            new_text: Modified text
            old_label: Label for original text
            new_label: Label for modified text
            **kwargs: Additional formatting options

        Example:
            ui.print_diff(
                old_text="status: pending",
                new_text="status: completed",
                old_label="Before",
                new_label="After"
            )
        """
        ...

    @abstractmethod
    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """
        Create and return a progress context manager.

        Args:
            description: Progress description
            total: Total steps (None for indeterminate spinner)
            **kwargs: Additional Rich Progress options

        Returns:
            Context manager for progress tracking

        Example:
            with ui.progress("Processing files...", total=100) as progress:
                for i in range(100):
                    process_file(i)
                    progress.update(1)
        """
        ...

    @abstractmethod
    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "default",
        **kwargs: Any
    ) -> None:
        """
        Print content in a bordered panel using Rich Panel.

        Args:
            content: Content to display
            title: Optional panel title
            style: Panel style (default, success, warning, error)
            **kwargs: Additional Rich Panel options

        Example:
            ui.print_panel(
                "Task completed successfully!",
                title="Success",
                style="success"
            )
        """
        ...

    @abstractmethod
    def print_status(
        self,
        message: str,
        level: MessageLevel = MessageLevel.INFO,
        **kwargs: Any
    ) -> None:
        """
        Print a styled status message.

        Args:
            message: Status message
            level: Message severity level
            **kwargs: Additional styling options

        Example:
            ui.print_status("Validating spec...", level=MessageLevel.ACTION)
            ui.print_status("Validation passed!", level=MessageLevel.SUCCESS)
        """
        ...
