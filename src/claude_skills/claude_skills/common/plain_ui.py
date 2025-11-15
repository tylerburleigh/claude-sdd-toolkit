"""
Plain text terminal user interface backend.

This module implements the PlainUi backend - a simple text-based fallback
for non-TTY environments (CI, pipes, non-interactive contexts).

Key Features:
- Simple text output without ANSI codes
- No Rich library required for output
- Safe for CI/CD pipelines and log files
- Maintains compatibility with Ui protocol
- Optional message collection for deferred rendering

Usage:
    from claude_skills.common.plain_ui import PlainUi
    from claude_skills.common.ui_protocol import MessageLevel

    ui = PlainUi()
    ui.print_table([{"task": "task-1-1", "status": "completed"}], title="Tasks")
    ui.print_status("Processing...", level=MessageLevel.ACTION)

    # Collection mode still works
    ui_collect = PlainUi(collect_messages=True)
    ui_collect.print_status("Message", MessageLevel.INFO)
    messages = ui_collect.get_messages()
"""

from typing import Optional, List, Dict, Any, Iterator
from contextlib import contextmanager
from io import StringIO
import difflib
import sys

from .ui_protocol import Ui, MessageLevel, Message


class PlainUi:
    """
    Plain text TUI backend for non-TTY environments.

    Provides simple text output without ANSI codes or Rich formatting.
    Designed for CI/CD, pipes, logs, and other non-interactive contexts
    where fancy formatting is not desired or not supported.

    All Ui protocol methods are implemented with plain text equivalents:
    - Tables rendered as ASCII text
    - Trees rendered with ASCII box characters
    - Panels rendered with simple borders
    - Progress shown as text updates
    - Diffs shown as unified diff format

    Attributes:
        collect_messages: Whether to collect messages for deferred rendering
        _messages: Collection of structured messages
        _context_stack: Stack of context dictionaries for message tagging
        quiet: Whether to suppress non-critical output (errors and warnings always print)
        file: Output file object (default stdout)
    """

    def __init__(
        self,
        collect_messages: bool = False,
        quiet: bool = False,
        file: Optional[Any] = None
    ) -> None:
        """
        Initialize PlainUi backend.

        Args:
            collect_messages: Whether to collect messages for deferred rendering
            quiet: Suppress non-critical output (errors and warnings always print)
            file: Output file object (default sys.stdout)

        Example:
            # Standard output
            ui = PlainUi()

            # Quiet mode (errors and warnings only)
            ui = PlainUi(quiet=True)

            # Collection mode
            ui = PlainUi(collect_messages=True)

            # Custom output file
            with open("output.txt", "w") as f:
                ui = PlainUi(file=f)
        """
        self.collect_messages = collect_messages
        self.quiet = quiet
        self.file = file or sys.stdout
        self._messages: List[Message] = []
        self._context_stack: List[Dict[str, Any]] = []

    @property
    def console(self) -> None:
        """
        Compatibility property for code that accesses ui.console.

        PlainUi does not use Rich Console - it outputs plain text directly.
        This property returns None to maintain interface compatibility with RichUi.

        Returns:
            None (PlainUi does not use Rich Console)
        """
        return None

    # ================================================================
    # Output Methods (Ui Protocol Implementation)
    # ================================================================

    def print_table(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Print data as a formatted ASCII table.

        Creates a simple ASCII table with borders and column alignment.
        No ANSI codes or fancy formatting.

        Args:
            data: List of dictionaries representing rows
            columns: Column names to display (default: all keys from first row)
            title: Optional table title
            **kwargs: Ignored (for API compatibility)

        Example:
            ui.print_table(
                [
                    {"task": "task-1-1", "status": "completed"},
                    {"task": "task-1-2", "status": "pending"}
                ],
                title="Task Status"
            )

            Output:
            ===== Task Status =====
            | task     | status    |
            |----------|-----------|
            | task-1-1 | completed |
            | task-1-2 | pending   |
        """
        if not data:
            self.print_status("No data to display", level=MessageLevel.WARNING)
            return

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Calculate column widths
        col_widths = {}
        for col in columns:
            # Max of column name length and all values in that column
            col_widths[col] = max(
                len(col),
                max(len(str(row.get(col, ""))) for row in data)
            )

        # Build output
        lines = []

        # Title
        if title:
            lines.append(f"===== {title} =====")
            lines.append("")

        # Header
        header = "| " + " | ".join(col.ljust(col_widths[col]) for col in columns) + " |"
        lines.append(header)

        # Separator
        separator = "|-" + "-|-".join("-" * col_widths[col] for col in columns) + "-|"
        lines.append(separator)

        # Rows
        for row in data:
            row_str = "| " + " | ".join(
                str(row.get(col, "")).ljust(col_widths[col]) for col in columns
            ) + " |"
            lines.append(row_str)

        output = "\n".join(lines)
        self._output(output, MessageLevel.RESULT, metadata={"type": "table"})

    def print_tree(
        self,
        data: Dict[str, Any],
        label: str = "Root",
        **kwargs: Any
    ) -> None:
        """
        Print hierarchical data as an ASCII tree.

        Uses simple ASCII characters to show tree structure.
        No box-drawing Unicode characters.

        Args:
            data: Nested dictionary representing tree structure
            label: Root node label
            **kwargs: Ignored (for API compatibility)

        Example:
            ui.print_tree(
                {
                    "phase-1": {
                        "task-1-1": {},
                        "task-1-2": {"task-1-2-1": {}}
                    }
                },
                label="Spec"
            )

            Output:
            Spec
            +- phase-1
               +- task-1-1
               +- task-1-2
                  +- task-1-2-1
        """
        lines = [label]

        def _build_tree(node_data: Dict[str, Any], prefix: str = "", is_last: bool = True) -> None:
            """Recursively build tree lines."""
            items = list(node_data.items())
            for i, (key, value) in enumerate(items):
                is_last_item = (i == len(items) - 1)

                # Branch characters
                if is_last_item:
                    branch = "+- "
                    extension = "   "
                else:
                    branch = "+- "
                    extension = "|  "

                lines.append(prefix + branch + key)

                if isinstance(value, dict) and value:
                    _build_tree(value, prefix + extension, is_last_item)

        _build_tree(data)
        output = "\n".join(lines)
        self._output(output, MessageLevel.RESULT, metadata={"type": "tree"})

    def print_diff(
        self,
        old_text: str,
        new_text: str,
        old_label: str = "Original",
        new_label: str = "Modified",
        **kwargs: Any
    ) -> None:
        """
        Print text difference as unified diff.

        Uses Python's difflib to generate standard unified diff format.
        No syntax highlighting or colors.

        Args:
            old_text: Original text
            new_text: Modified text
            old_label: Label for original text
            new_label: Label for modified text
            **kwargs: Additional formatting options (context_lines)

        Example:
            ui.print_diff(
                old_text="status: pending",
                new_text="status: completed"
            )

            Output:
            --- Original
            +++ Modified
            @@ -1 +1 @@
            -status: pending
            +status: completed
        """
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

        self._output(diff_text, MessageLevel.RESULT, metadata={"type": "diff"})

    @contextmanager
    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        **kwargs: Any
    ) -> Iterator['PlainProgressTask']:
        """
        Create a progress context manager.

        In PlainUi, progress is shown as simple text updates.
        No progress bars or spinners - just text messages.

        Args:
            description: Progress description
            total: Total steps (used for percentage calculation)
            **kwargs: Ignored (for API compatibility)

        Returns:
            Context manager for progress tracking

        Example:
            # With total (shows percentage)
            with ui.progress("Processing files...", total=100) as progress:
                for i in range(100):
                    process_file(i)
                    progress.update(1)

            # Without total (just shows updates)
            with ui.progress("Loading...") as progress:
                long_operation()
        """
        # Show start message
        if not self.quiet:
            start_msg = f"[Progress] {description}"
            if total is not None:
                start_msg += f" (0/{total}, 0%)"
            self._write(start_msg)

        task = PlainProgressTask(self, description, total)
        try:
            yield task
        finally:
            # Show completion message
            if not self.quiet:
                end_msg = f"[Progress] {description} - Complete"
                if total is not None:
                    end_msg += f" ({total}/{total}, 100%)"
                self._write(end_msg)

    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "default",
        **kwargs: Any
    ) -> None:
        """
        Print content in a simple ASCII bordered panel.

        Uses basic ASCII characters for borders.
        Style parameter is ignored (no colors in plain mode).

        Args:
            content: Content to display
            title: Optional panel title
            style: Ignored (for API compatibility)
            **kwargs: Ignored (for API compatibility)

        Example:
            ui.print_panel("Task completed!", title="Success")

            Output:
            +---------- Success ----------+
            | Task completed!             |
            +-----------------------------+
        """
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0

        if title:
            max_width = max(max_width, len(title) + 4)

        # Build panel
        output_lines = []

        # Top border with title
        if title:
            title_part = f" {title} "
            padding = max_width - len(title_part)
            left_pad = padding // 2
            right_pad = padding - left_pad
            output_lines.append(f"+{'-' * left_pad}{title_part}{'-' * right_pad}+")
        else:
            output_lines.append(f"+{'-' * max_width}+")

        # Content lines
        for line in lines:
            padded = line.ljust(max_width)
            output_lines.append(f"| {padded} |")

        # Bottom border
        output_lines.append(f"+{'-' * max_width}+")

        output = "\n".join(output_lines)
        self._output(output, MessageLevel.RESULT, metadata={"type": "panel"})

    def print_status(
        self,
        message: str,
        level: MessageLevel = MessageLevel.INFO,
        **kwargs: Any
    ) -> None:
        """
        Print a status message with level indicator.

        Uses simple text prefixes for different levels.
        No emojis or colors in plain mode.

        Args:
            message: Status message
            level: Message severity level
            **kwargs: Ignored (for API compatibility)

        Example:
            ui.print_status("Starting task", level=MessageLevel.ACTION)
            # Output: [ACTION] Starting task

            ui.print_status("Task done", level=MessageLevel.SUCCESS)
            # Output: [SUCCESS] Task done
        """
        # Level prefixes (plain text, no emojis)
        level_map = {
            MessageLevel.ACTION: "[ACTION]",
            MessageLevel.SUCCESS: "[SUCCESS]",
            MessageLevel.INFO: "[INFO]",
            MessageLevel.WARNING: "[WARNING]",
            MessageLevel.ERROR: "[ERROR]",
            MessageLevel.DETAIL: "",
            MessageLevel.RESULT: "[RESULT]",
            MessageLevel.ITEM: "-",
            MessageLevel.HEADER: "=====",
            MessageLevel.BLANK: ""
        }

        prefix = level_map.get(level, "")

        if level == MessageLevel.HEADER:
            # Special formatting for headers
            text = f"\n{prefix} {message} {prefix}\n"
        elif level == MessageLevel.BLANK:
            text = ""
        elif prefix:
            text = f"{prefix} {message}"
        else:
            text = message

        self._output(text, level)

    # ================================================================
    # Internal Methods
    # ================================================================

    def _output(
        self,
        text: str,
        level: MessageLevel,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Output text to file or collect as message.

        Respects quiet mode (errors and warnings always print).

        Args:
            text: Text to output
            level: Message level
            metadata: Optional metadata
        """
        if self.collect_messages:
            self._add_message(level, text, metadata)
        else:
            # Check quiet mode - always allow errors and warnings through
            if self.quiet and level not in (MessageLevel.ERROR, MessageLevel.WARNING):
                return

            self._write(text)

    def _write(self, text: str) -> None:
        """Write text to output file."""
        print(text, file=self.file)
        if hasattr(self.file, 'flush'):
            self.file.flush()

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
        Add a message to the collection.

        Args:
            level: Message level
            text: Message text
            metadata: Optional metadata dictionary
        """
        context = {}
        if self._context_stack:
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
            messages = ui.get_messages()
            errors = ui.get_messages(level=MessageLevel.ERROR)
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

        Displays all collected messages to output file.

        Example:
            ui = PlainUi(collect_messages=True)
            ui.print_status("Message 1", MessageLevel.INFO)
            ui.print_status("Message 2", MessageLevel.INFO)
            ui.render_all()  # Now display them
        """
        for msg in self._messages:
            if not msg.rendered:
                # Write message text directly
                if not self.quiet or msg.level == MessageLevel.ERROR:
                    self._write(msg.text)
                msg.rendered = True

    def clear_messages(self) -> None:
        """Clear all collected messages."""
        self._messages.clear()

    @contextmanager
    def context(self, **context_kwargs: Any) -> Iterator[None]:
        """
        Context manager for message tagging.

        All messages within the context block are tagged with
        the provided context keys.

        Args:
            **context_kwargs: Context key-value pairs

        Example:
            with ui.context(task_id="task-1-1"):
                ui.print_status("Working", MessageLevel.ACTION)
                # Message tagged with task_id
        """
        self._context_stack.append(context_kwargs)
        try:
            yield
        finally:
            self._context_stack.pop()


class PlainProgressTask:
    """
    Progress task wrapper for PlainUi.

    Tracks progress and displays text updates.
    No visual progress bars - just percentage updates.
    """

    def __init__(
        self,
        ui: PlainUi,
        description: str,
        total: Optional[int]
    ) -> None:
        """
        Initialize progress task.

        Args:
            ui: PlainUi instance
            description: Progress description
            total: Total steps (None for indeterminate)
        """
        self._ui = ui
        self._description = description
        self._total = total
        self._current = 0

    def update(self, advance: float = 1.0) -> None:
        """
        Update progress.

        In PlainUi, this optionally prints progress updates.

        Args:
            advance: Amount to advance
        """
        self._current += advance

        # Only show updates if not quiet and we have a total
        if not self._ui.quiet and self._total is not None:
            percentage = int((self._current / self._total) * 100)
            msg = f"[Progress] {self._description} ({int(self._current)}/{self._total}, {percentage}%)"
            self._ui._write(msg)

    def set_description(self, description: str) -> None:
        """
        Update progress description.

        Args:
            description: New description
        """
        self._description = description
