"""
Rich-powered terminal user interface backend.

This module implements the RichUi backend - a full-featured TUI implementation
using the Rich library for interactive terminal environments (TTY).

Key Features:
- Rich Table for formatted data display
- Rich Tree for hierarchical structures
- Rich Progress for progress bars and spinners
- Rich Panel for bordered content
- Rich Console for styled output
- Syntax highlighting for diffs

Usage:
    from claude_skills.common.rich_ui import RichUi
    from claude_skills.common.ui_protocol import MessageLevel

    ui = RichUi()
    ui.print_table([{"task": "task-1-1", "status": "completed"}], title="Tasks")
    ui.print_status("Processing...", level=MessageLevel.ACTION)

    with ui.progress("Loading files...", total=100) as progress:
        for i in range(100):
            process_file(i)
            progress.update(1)
"""

from typing import Optional, List, Dict, Any, Iterator
from contextlib import contextmanager
from io import StringIO
import difflib

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.text import Text

from .ui_protocol import Ui, MessageLevel, Message


class RichUi:
    """
    Rich-powered TUI backend for interactive terminals.

    Provides full Rich functionality including tables, trees, progress bars,
    panels, and styled output. Designed for TTY environments where rich
    formatting is available and beneficial.

    This implementation uses Rich Console as the core output mechanism,
    providing advanced formatting capabilities for AI-agent workflows.

    Attributes:
        console: Rich Console instance for output
        _messages: Collection of structured messages (when collecting)
        _collecting: Whether to collect messages instead of immediate rendering
        _context_stack: Stack of context dictionaries for message tagging
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        collect_messages: bool = False
    ) -> None:
        """
        Initialize RichUi backend.

        Args:
            console: Optional Rich Console instance (creates default if None)
            collect_messages: Whether to collect messages for deferred rendering

        Example:
            # Default console (auto-detects TTY)
            ui = RichUi()

            # Custom console with specific settings
            custom_console = Console(force_terminal=True, width=120)
            ui = RichUi(console=custom_console)

            # Collection mode for deferred rendering
            ui = RichUi(collect_messages=True)
            ui.print_status("Processing...")
            messages = ui.get_messages()
            ui.render_all()
        """
        self.console = console or Console()
        self._collecting = collect_messages
        self._messages: List[Message] = []
        self._context_stack: List[Dict[str, Any]] = []

    # ================================================================
    # Rich-Powered Output Methods
    # ================================================================

    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Print data as a formatted table using Rich Table.

        Creates a Rich Table with automatic column detection, formatting,
        and borders. Supports extensive customization via kwargs.

        Args:
            data: List of dictionaries representing rows
            columns: Column names to display (default: all keys from first row)
            title: Optional table title
            **kwargs: Additional Rich Table options:
                - show_header: bool (default True)
                - show_lines: bool (default False)
                - show_edge: bool (default True)
                - header_style: str (default "bold magenta")
                - border_style: str (default "bright_blue")
                - row_styles: List[str] (alternating row colors)

        Example:
            ui.print_table(
                [
                    {"task": "task-1-1", "status": "completed", "progress": "100%"},
                    {"task": "task-1-2", "status": "in_progress", "progress": "50%"}
                ],
                title="Task Status",
                show_lines=True
            )
        """
        if not data:
            self.print_status("No data to display", level=MessageLevel.WARNING)
            return

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Create table
        table = Table(
            title=title,
            show_header=kwargs.get("show_header", True),
            show_lines=kwargs.get("show_lines", False),
            show_edge=kwargs.get("show_edge", True),
            header_style=kwargs.get("header_style", "bold magenta"),
            border_style=kwargs.get("border_style", "bright_blue")
        )

        # Add columns
        for col in columns:
            table.add_column(col, overflow="ignore", no_wrap=True)

        # Add rows
        for row_data in data:
            row_values = [str(row_data.get(col, "")) for col in columns]
            table.add_row(*row_values)

        # Render
        if self._collecting:
            # Capture table output to string
            string_io = StringIO()
            temp_console = Console(file=string_io, force_terminal=False)
            temp_console.print(table)
            content = string_io.getvalue()
            self._add_message(MessageLevel.RESULT, content, metadata={"type": "table"})
        else:
            self.console.print(table)

    def print_tree(
        self,
        data: Dict[str, Any],
        label: str = "Root",
        **kwargs: Any
    ) -> None:
        """
        Print hierarchical data as a tree using Rich Tree.

        Recursively builds a Rich Tree from nested dictionaries,
        displaying hierarchical relationships with visual branching.

        Args:
            data: Nested dictionary representing tree structure
            label: Root node label
            **kwargs: Additional Rich Tree options:
                - guide_style: str (default "bright_blue")
                - expanded: bool (default True)

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
        tree = Tree(
            label,
            guide_style=kwargs.get("guide_style", "bright_blue"),
            expanded=kwargs.get("expanded", True)
        )

        def _build_tree(node: Tree, data_dict: Dict[str, Any]) -> None:
            """Recursively build tree from nested dict."""
            for key, value in data_dict.items():
                if isinstance(value, dict):
                    branch = node.add(key)
                    _build_tree(branch, value)
                else:
                    node.add(f"{key}: {value}")

        _build_tree(tree, data)

        # Render
        if self._collecting:
            string_io = StringIO()
            temp_console = Console(file=string_io, force_terminal=False)
            temp_console.print(tree)
            content = string_io.getvalue()
            self._add_message(MessageLevel.RESULT, content, metadata={"type": "tree"})
        else:
            self.console.print(tree)

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

        Uses Python's difflib to generate unified diff, then displays
        with syntax highlighting for added/removed lines.

        Args:
            old_text: Original text
            new_text: Modified text
            old_label: Label for original text
            new_label: Label for modified text
            **kwargs: Additional formatting options:
                - context_lines: int (default 3)
                - lexer: str (default "diff")

        Example:
            ui.print_diff(
                old_text="status: pending",
                new_text="status: completed",
                old_label="Before",
                new_label="After"
            )
        """
        # Generate unified diff
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            lineterm='',
            n=kwargs.get("context_lines", 3)
        )

        diff_text = '\n'.join(diff_lines)

        if not diff_text:
            self.print_status("No differences found", level=MessageLevel.INFO)
            return

        # Render with syntax highlighting
        syntax = Syntax(
            diff_text,
            kwargs.get("lexer", "diff"),
            theme="monokai",
            line_numbers=False
        )

        if self._collecting:
            string_io = StringIO()
            temp_console = Console(file=string_io, force_terminal=False)
            temp_console.print(syntax)
            content = string_io.getvalue()
            self._add_message(MessageLevel.RESULT, content, metadata={"type": "diff"})
        else:
            self.console.print(syntax)

    @contextmanager
    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        **kwargs: Any
    ) -> Iterator['ProgressTask']:
        """
        Create and return a progress context manager.

        Displays Rich Progress bar with spinner, description, and percentage.
        If total is None, shows indeterminate spinner. Otherwise shows
        progress bar with completion percentage.

        Args:
            description: Progress description
            total: Total steps (None for indeterminate spinner)
            **kwargs: Additional Rich Progress options:
                - transient: bool (default True) - Remove after completion
                - refresh_per_second: int (default 10)

        Returns:
            Context manager for progress tracking with update() method

        Example:
            # Determinate progress (known total)
            with ui.progress("Processing files...", total=100) as progress:
                for i in range(100):
                    process_file(i)
                    progress.update(1)

            # Indeterminate progress (unknown total)
            with ui.progress("Loading...") as progress:
                long_running_operation()
        """
        progress_obj = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn() if total is not None else TextColumn(""),
            TaskProgressColumn() if total is not None else TextColumn(""),
            console=self.console,
            transient=kwargs.get("transient", True),
            refresh_per_second=kwargs.get("refresh_per_second", 10)
        )

        with progress_obj:
            task_id = progress_obj.add_task(description, total=total or 100)
            yield ProgressTask(progress_obj, task_id)

    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "default",
        **kwargs: Any
    ) -> None:
        """
        Print content in a bordered panel using Rich Panel.

        Creates a Rich Panel with borders, optional title, and styling.
        Useful for highlighting important information or sections.

        Args:
            content: Content to display
            title: Optional panel title
            style: Panel style (default, success, warning, error, info)
            **kwargs: Additional Rich Panel options:
                - border_style: str (overrides style presets)
                - padding: int or tuple (default (0, 1))
                - expand: bool (default False)

        Example:
            ui.print_panel(
                "Task completed successfully!",
                title="Success",
                style="success"
            )

            ui.print_panel(
                "Configuration error detected",
                title="Error",
                style="error",
                expand=True
            )
        """
        # Style presets
        style_map = {
            "default": "bright_blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "cyan"
        }

        border_style = kwargs.get("border_style", style_map.get(style, "bright_blue"))

        panel = Panel(
            content,
            title=title,
            border_style=border_style,
            padding=kwargs.get("padding", (0, 1)),
            expand=kwargs.get("expand", False)
        )

        if self._collecting:
            string_io = StringIO()
            temp_console = Console(file=string_io, force_terminal=False)
            temp_console.print(panel)
            content_str = string_io.getvalue()
            self._add_message(MessageLevel.RESULT, content_str, metadata={"type": "panel"})
        else:
            self.console.print(panel)

    def print_status(
        self,
        message: str,
        level: MessageLevel = MessageLevel.INFO,
        **kwargs: Any
    ) -> None:
        """
        Print a styled status message.

        Displays a message with level-appropriate styling (color, emoji).
        Supports different severity levels with distinct visual indicators.

        Args:
            message: Status message
            level: Message severity level
            **kwargs: Additional styling options:
                - emoji: bool (default True) - Show emoji prefix
                - style: str (override default level style)

        Example:
            ui.print_status("Validating spec...", level=MessageLevel.ACTION)
            ui.print_status("Validation passed!", level=MessageLevel.SUCCESS)
            ui.print_status("Missing metadata", level=MessageLevel.WARNING)
            ui.print_status("File not found", level=MessageLevel.ERROR)
        """
        # Level styling
        level_config = {
            MessageLevel.ACTION: ("🔵", "Action:", "blue"),
            MessageLevel.SUCCESS: ("✅", "Success:", "green"),
            MessageLevel.INFO: ("ℹ️", "Info:", "cyan"),
            MessageLevel.WARNING: ("⚠️", "Warning:", "yellow"),
            MessageLevel.ERROR: ("❌", "Error:", "red"),
            MessageLevel.DETAIL: ("", "", "white"),
            MessageLevel.RESULT: ("", "", "cyan"),
            MessageLevel.ITEM: ("•", "", "white"),
            MessageLevel.HEADER: ("", "", "bold magenta"),
            MessageLevel.BLANK: ("", "", "white")
        }

        emoji, label, style = level_config.get(level, ("", "", "white"))

        # Build message with styling
        show_emoji = kwargs.get("emoji", True)
        custom_style = kwargs.get("style", style)

        parts = []
        if show_emoji and emoji:
            parts.append(emoji)
        if label:
            parts.append(Text(label, style=custom_style))
        parts.append(message)

        text = Text(" ").join([Text(p) if isinstance(p, str) else p for p in parts])

        if self._collecting:
            self._add_message(level, message, metadata={"emoji": emoji, "label": label})
        else:
            self.console.print(text)

    # ================================================================
    # Message Collection & Management
    # ================================================================

    def _add_message(
        self,
        level: MessageLevel,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the collection (internal).

        Args:
            level: Message level
            text: Message text
            metadata: Optional metadata dictionary
        """
        context = {}
        if self._context_stack:
            # Merge all contexts in stack
            for ctx in self._context_stack:
                context.update(ctx)

        msg = Message(
            level=level,
            text=text,
            context=context,
            metadata=metadata or {}
        )
        self._messages.append(msg)

    def get_messages(
        self,
        level: Optional[MessageLevel] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Message]:
        """
        Get collected messages, optionally filtered.

        Args:
            level: Filter by message level
            context: Filter by context keys

        Returns:
            List of matching messages

        Example:
            # Get all messages
            all_messages = ui.get_messages()

            # Get only errors
            errors = ui.get_messages(level=MessageLevel.ERROR)

            # Get messages from specific task
            task_messages = ui.get_messages(context={"task_id": "task-1-1"})
        """
        messages = self._messages

        if level is not None:
            messages = [m for m in messages if m.level == level]

        if context is not None:
            messages = [
                m for m in messages
                if all(m.context.get(k) == v for k, v in context.items())
            ]

        return messages

    def render_all(self) -> None:
        """
        Render all collected messages immediately.

        Useful in collection mode to display all collected messages
        at once after they've been collected and analyzed.

        Example:
            ui = RichUi(collect_messages=True)
            ui.print_status("Step 1", MessageLevel.ACTION)
            ui.print_status("Step 2", MessageLevel.ACTION)
            # Analyze messages...
            ui.render_all()  # Now display them
        """
        for msg in self._messages:
            if not msg.rendered:
                # Re-render message using print_status
                if "type" in msg.metadata:
                    # Complex types (table, tree, etc.) - just print raw
                    self.console.print(msg.text)
                else:
                    # Status messages - render with styling
                    self.print_status(msg.text, msg.level)
                msg.rendered = True

    def clear_messages(self) -> None:
        """Clear all collected messages."""
        self._messages.clear()

    @contextmanager
    def context(self, **context_kwargs: Any) -> Iterator[None]:
        """
        Context manager for message tagging.

        All messages printed within the context block will be tagged
        with the provided context keys.

        Args:
            **context_kwargs: Context key-value pairs

        Example:
            with ui.context(task_id="task-1-1", phase="implementation"):
                ui.print_status("Starting work", MessageLevel.ACTION)
                # Message tagged with task_id and phase
        """
        self._context_stack.append(context_kwargs)
        try:
            yield
        finally:
            self._context_stack.pop()


class ProgressTask:
    """
    Wrapper for Rich Progress task with simplified API.

    Provides a simple update() method for advancing progress.
    """

    def __init__(self, progress: Progress, task_id: int) -> None:
        """
        Initialize progress task wrapper.

        Args:
            progress: Rich Progress instance
            task_id: Task ID from Progress
        """
        self._progress = progress
        self._task_id = task_id

    def update(self, advance: float = 1.0) -> None:
        """
        Update progress by advancing specified amount.

        Args:
            advance: Amount to advance (default 1.0)
        """
        self._progress.update(self._task_id, advance=advance)

    def set_description(self, description: str) -> None:
        """
        Update the progress description.

        Args:
            description: New description text
        """
        self._progress.update(self._task_id, description=description)
