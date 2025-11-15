"""
Pretty printer utility for consistent console output across SDD tools.

This module provides the PrettyPrinter class - a backward-compatible wrapper
around the new Ui backend system. It maintains the original API while internally
delegating to RichUi or PlainUi based on environment detection.

Key Features:
- 100% backward compatible with existing code
- Automatically uses RichUi or PlainUi backend
- All original methods preserved with identical signatures
- No breaking changes to existing usage

Migration Path:
- Existing code continues to work unchanged
- New code can use Ui protocol directly via create_ui()
- PrettyPrinter wraps Ui for legacy compatibility
"""

import sys
from typing import Optional, TYPE_CHECKING

from .ui_factory import create_ui
from .ui_protocol import Ui, MessageLevel

if TYPE_CHECKING:
    from claude_skills.cli.sdd.verbosity import VerbosityLevel


class PrettyPrinter:
    """
    Utility for consistent, pretty console output optimized for Claude Code.

    This class maintains backward compatibility with the original PrettyPrinter
    implementation while internally delegating to the new Ui backend system.

    The Ui backend (RichUi or PlainUi) is automatically selected based on:
    - TTY availability (sys.stdout.isatty())
    - CI environment detection
    - Force flags or environment variables

    All original methods are preserved with identical signatures, ensuring
    100% backward compatibility with existing code.

    Verbosity Control:
    - Supports both legacy boolean flags (quiet, verbose) and new VerbosityLevel enum
    - VerbosityLevel.QUIET: Errors only, minimal output
    - VerbosityLevel.NORMAL: Standard output (default)
    - VerbosityLevel.VERBOSE: Detailed output including info messages

    Attributes:
        use_color: Whether to use ANSI color codes (auto-disabled if not TTY)
        verbose: Whether to show detailed info messages (legacy, use verbosity_level)
        quiet: Whether to suppress non-error output (legacy, use verbosity_level)
        verbosity_level: VerbosityLevel enum (QUIET, NORMAL, or VERBOSE)
        _ui: Internal Ui backend (RichUi or PlainUi)
    """

    def __init__(
        self,
        use_color: bool = True,
        verbose: bool = False,
        quiet: bool = False,
        verbosity_level: Optional['VerbosityLevel'] = None,
        _ui_backend: Optional[Ui] = None
    ):
        """
        Initialize the pretty printer.

        Args:
            use_color: Enable ANSI color codes (auto-disabled if not a TTY)
            verbose: Show detailed output including info messages (deprecated, use verbosity_level)
            quiet: Minimal output (errors only) (deprecated, use verbosity_level)
            verbosity_level: Optional VerbosityLevel enum (QUIET, NORMAL, VERBOSE).
                           If provided, overrides quiet/verbose flags.
            _ui_backend: Internal parameter for testing (not for public use)

        Example:
            # Standard usage (auto-detects environment)
            printer = PrettyPrinter()

            # Verbose mode (legacy)
            printer = PrettyPrinter(verbose=True)

            # Quiet mode (legacy)
            printer = PrettyPrinter(quiet=True)

            # New verbosity level API
            from claude_skills.cli.sdd.verbosity import VerbosityLevel
            printer = PrettyPrinter(verbosity_level=VerbosityLevel.QUIET)

            # Disable colors
            printer = PrettyPrinter(use_color=False)
        """
        self.use_color = use_color and sys.stdout.isatty()

        # Support both legacy boolean flags and new verbosity_level enum
        if verbosity_level is not None:
            # New API: use verbosity_level enum
            from claude_skills.cli.sdd.verbosity import VerbosityLevel
            self.verbosity_level = verbosity_level
            self.quiet = (verbosity_level == VerbosityLevel.QUIET)
            self.verbose = (verbosity_level == VerbosityLevel.VERBOSE)
        else:
            # Legacy API: use quiet/verbose booleans
            # Infer verbosity_level from boolean flags for internal consistency
            from claude_skills.cli.sdd.verbosity import VerbosityLevel
            self.quiet = quiet
            self.verbose = verbose
            if quiet:
                self.verbosity_level = VerbosityLevel.QUIET
            elif verbose:
                self.verbosity_level = VerbosityLevel.VERBOSE
            else:
                self.verbosity_level = VerbosityLevel.NORMAL

        # Create or use provided Ui backend
        if _ui_backend is not None:
            self._ui = _ui_backend
        else:
            # Automatically create appropriate backend
            # Force plain if colors are explicitly disabled
            force_plain = not self.use_color
            self._ui = create_ui(
                force_plain=force_plain,
                quiet=self.quiet
            )

    def _colorize(self, text: str, color_code: str) -> str:
        """
        Apply ANSI color code if colors are enabled.

        This method is preserved for backward compatibility but is no longer
        used internally. The Ui backend handles all styling.

        Args:
            text: Text to colorize
            color_code: ANSI color code (e.g., '34' for blue)

        Returns:
            Colorized text if use_color is True, otherwise plain text
        """
        if not self.use_color:
            return text
        return f"\033[{color_code}m{text}\033[0m"

    def action(self, msg: str) -> None:
        """
        Print an action message (what's being done now).

        Args:
            msg: Action message to display

        Example:
            printer.action("Processing task task-2-1...")
            printer.action("Validating dependencies...")
        """
        if not self.quiet:
            self._ui.print_status(msg, level=MessageLevel.ACTION)

    def success(self, msg: str) -> None:
        """
        Print a success message (completed action).

        Args:
            msg: Success message to display

        Example:
            printer.success("Task completed successfully")
            printer.success("Spec validation passed")
        """
        if not self.quiet:
            self._ui.print_status(msg, level=MessageLevel.SUCCESS)

    def info(self, msg: str) -> None:
        """
        Print an informational message (context/details).

        Only displays if verbose mode is enabled.

        Args:
            msg: Info message to display

        Example:
            printer.info("Checking 15 dependency files...")
            printer.info("Using default configuration")
        """
        if self.verbose and not self.quiet:
            self._ui.print_status(msg, level=MessageLevel.INFO)

    def warning(self, msg: str) -> None:
        """
        Print a warning message (non-blocking issue).

        Warnings always print regardless of verbosity level (QUIET, NORMAL, VERBOSE).
        This ensures important non-blocking issues are never silently suppressed.
        Printed to stderr.

        Args:
            msg: Warning message to display

        Example:
            printer.warning("Deprecated configuration format detected")
            printer.warning("Task has no estimated_hours metadata")
        """
        # Warnings always print (ignore quiet mode) - users need to see issues
        self._ui.print_status(msg, level=MessageLevel.WARNING)

    def error(self, msg: str) -> None:
        """
        Print an error message (blocking issue).

        Errors always print regardless of verbosity level (QUIET, NORMAL, VERBOSE).
        Critical issues must never be suppressed.
        Printed to stderr.

        Args:
            msg: Error message to display

        Example:
            printer.error("Spec file not found")
            printer.error("Invalid task ID format")
        """
        # Errors always print (ignore verbosity level) - critical issues must be visible
        self._ui.print_status(msg, level=MessageLevel.ERROR)

    def header(self, msg: str) -> None:
        """
        Print a section header.

        Args:
            msg: Header text to display

        Example:
            printer.header("Spec Validation Report")
            printer.header("Task Progress Summary")
        """
        if not self.quiet:
            self._ui.print_status(msg, level=MessageLevel.HEADER)

    def detail(self, msg: str, indent: int = 1) -> None:
        """
        Print an indented detail line.

        Args:
            msg: Detail message to display
            indent: Indentation level (number of 2-space indents)

        Example:
            printer.detail("Status: pending", indent=1)
            printer.detail("Dependencies: 3 tasks", indent=2)
        """
        if not self.quiet:
            # Apply indentation manually since Ui doesn't have indent parameter
            prefix = "  " * indent
            self._ui.print_status(f"{prefix}{msg}", level=MessageLevel.DETAIL)

    def result(self, key: str, value: str, indent: int = 0) -> None:
        """
        Print a key-value result.

        Args:
            key: Result key
            value: Result value
            indent: Indentation level (number of 2-space indents)

        Example:
            printer.result("Total Tasks", "23")
            printer.result("Completed", "15", indent=1)
        """
        if not self.quiet:
            # Apply indentation manually
            prefix = "  " * indent
            # Format as key: value
            text = f"{prefix}{key}: {value}"
            self._ui.print_status(text, level=MessageLevel.RESULT)

    def blank(self) -> None:
        """
        Print a blank line.

        Example:
            printer.action("Starting validation")
            printer.blank()
            printer.detail("Checking dependencies...")
        """
        if not self.quiet:
            self._ui.print_status("", level=MessageLevel.BLANK)

    def item(self, msg: str, indent: int = 0) -> None:
        """
        Print a list item.

        Args:
            msg: Item message to display
            indent: Indentation level (number of 2-space indents)

        Example:
            printer.item("Task 1: Create directory structure")
            printer.item("Subtask: Initialize config", indent=1)
        """
        if not self.quiet:
            # Apply indentation manually
            prefix = "  " * indent
            text = f"{prefix}• {msg}"
            self._ui.print_status(text, level=MessageLevel.ITEM)
