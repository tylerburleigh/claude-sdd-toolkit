"""
Pretty printer utility for consistent console output across SDD tools.
"""

import sys


class PrettyPrinter:
    """Utility for consistent, pretty console output optimized for Claude Code."""

    def __init__(self, use_color=True, verbose=False, quiet=False):
        """
        Initialize the pretty printer.

        Args:
            use_color: Enable ANSI color codes (auto-disabled if not a TTY)
            verbose: Show detailed output including info messages
            quiet: Minimal output (errors only)
        """
        self.use_color = use_color and sys.stdout.isatty()
        self.verbose = verbose
        self.quiet = quiet

    def _colorize(self, text, color_code):
        """Apply ANSI color code if colors are enabled."""
        if not self.use_color:
            return text
        return f"\033[{color_code}m{text}\033[0m"

    def action(self, msg):
        """Print an action message (what's being done now)."""
        if not self.quiet:
            print(f"🔵 {self._colorize('Action:', '34')} {msg}")

    def success(self, msg):
        """Print a success message (completed action)."""
        if not self.quiet:
            print(f"✅ {self._colorize('Success:', '32')} {msg}")

    def info(self, msg):
        """Print an informational message (context/details)."""
        if self.verbose and not self.quiet:
            print(f"ℹ️  {self._colorize('Info:', '36')} {msg}")

    def warning(self, msg):
        """Print a warning message (non-blocking issue)."""
        if not self.quiet:
            print(f"⚠️  {self._colorize('Warning:', '33')} {msg}", file=sys.stderr)

    def error(self, msg):
        """Print an error message (blocking issue)."""
        print(f"❌ {self._colorize('Error:', '31')} {msg}", file=sys.stderr)

    def header(self, msg):
        """Print a section header."""
        if not self.quiet:
            line = "═" * 60
            print(f"\n{self._colorize(line, '35')}")
            print(f"{self._colorize(msg.center(60), '35;1')}")
            print(f"{self._colorize(line, '35')}\n")

    def detail(self, msg, indent=1):
        """Print an indented detail line."""
        if not self.quiet:
            prefix = "  " * indent
            print(f"{prefix}{msg}")

    def result(self, key, value, indent=0):
        """Print a key-value result."""
        if not self.quiet:
            prefix = "  " * indent
            print(f"{prefix}{self._colorize(key + ':', '36')} {value}")

    def blank(self):
        """Print a blank line."""
        if not self.quiet:
            print()

    def item(self, msg, indent=0):
        """Print a list item."""
        if not self.quiet:
            prefix = "  " * indent
            print(f"{prefix}• {msg}")

