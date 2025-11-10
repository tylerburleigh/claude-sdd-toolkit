#!/usr/bin/env python3
"""
Rich TUI preview - shows what the progress feedback will look like
with actual Rich library components (progress bars, spinners, etc.)

This requires the rich library to be installed:
    pip install rich
"""

import time
import sys
from datetime import datetime

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich import box
except ImportError:
    print("❌ This demo requires the 'rich' library.")
    print("   Install with: pip install rich")
    sys.exit(1)

# Add src to path
sys.path.insert(0, '/home/tyler/Documents/GitHub/claude-sdd-toolkit/src/claude_skills')

from claude_skills.common.tui_progress import (
    ai_consultation_progress,
    batch_consultation_progress,
    ProgressCallback
)
from claude_skills.common.ai_tools import ToolStatus, ToolResponse


console = Console()


class RichProgressCallback:
    """Rich TUI progress callback implementation."""

    def __init__(self, progress: Progress):
        self.progress = progress
        self.task_id = None

    def on_start(self, tool: str, timeout: int, **context) -> None:
        """Create progress bar when tool starts."""
        model = context.get('model', 'default')
        description = f"[cyan]{tool}[/cyan] ({model})"
        self.task_id = self.progress.add_task(
            description,
            total=timeout,
            start=True
        )

    def on_update(self, tool: str, elapsed: float, timeout: int, **context) -> None:
        """Update progress bar (periodic updates)."""
        if self.task_id is not None:
            self.progress.update(self.task_id, completed=elapsed)

    def on_complete(self, tool: str, status: ToolStatus, duration: float, **context) -> None:
        """Complete progress bar with status."""
        if self.task_id is not None:
            if status == ToolStatus.SUCCESS:
                description = f"[green]✓[/green] [cyan]{tool}[/cyan]"
            elif status == ToolStatus.TIMEOUT:
                description = f"[yellow]⏰[/yellow] [cyan]{tool}[/cyan] (timeout)"
            elif status == ToolStatus.ERROR:
                description = f"[red]✗[/red] [cyan]{tool}[/cyan] (error)"
            else:
                description = f"[red]✗[/red] [cyan]{tool}[/cyan] (not found)"

            self.progress.update(
                self.task_id,
                description=description,
                completed=duration if status == ToolStatus.TIMEOUT else duration,
                total=duration
            )


class RichBatchProgressCallback:
    """Rich TUI batch progress callback."""

    def __init__(self, progress: Progress):
        self.progress = progress
        self.task_ids = {}
        self.aggregate_task_id = None

    def on_batch_start(self, tools: list[str], count: int, timeout: int, **context) -> None:
        """Create progress bars for all tools."""
        # Create aggregate progress
        self.aggregate_task_id = self.progress.add_task(
            "[bold blue]Overall Progress[/bold blue]",
            total=count,
            start=True
        )

        # Create per-tool progress bars
        for tool in tools:
            task_id = self.progress.add_task(
                f"[dim]{tool}[/dim]",
                total=timeout,
                start=False
            )
            self.task_ids[tool] = task_id

    def on_tool_complete(self, tool: str, response: ToolResponse, completed_count: int, total_count: int) -> None:
        """Mark tool as complete."""
        task_id = self.task_ids.get(tool)
        if task_id is not None:
            if response.success:
                description = f"[green]✓[/green] [cyan]{tool}[/cyan]"
            else:
                description = f"[red]✗[/red] [cyan]{tool}[/cyan]"

            self.progress.update(
                task_id,
                description=description,
                completed=response.duration,
                total=response.duration,
                visible=True
            )

        # Update aggregate
        if self.aggregate_task_id is not None:
            self.progress.update(self.aggregate_task_id, completed=completed_count)

    def on_batch_complete(self, total_count: int, success_count: int, failure_count: int,
                         total_duration: float, max_duration: float) -> None:
        """Finalize aggregate progress."""
        if self.aggregate_task_id is not None:
            description = f"[bold green]Complete[/bold green] ({success_count}/{total_count} succeeded)"
            self.progress.update(
                self.aggregate_task_id,
                description=description,
                completed=total_count
            )


def demo_single_tool_rich():
    """Demo single tool with Rich progress bar."""
    console.print("\n[bold cyan]═══ Demo 1: Single Tool Execution ═══[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        callback = RichProgressCallback(progress)

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=callback,
            model="gemini-2.5-pro"
        ) as prog:
            # Simulate work
            time.sleep(2.0)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Sample response",
                error=None,
                duration=2.0,
                timestamp=datetime.now().isoformat(),
                model="gemini-2.5-pro",
                prompt="Sample"
            )
            prog.complete(response)

    console.print()


def demo_batch_execution_rich():
    """Demo parallel batch with Rich multi-progress."""
    console.print("\n[bold cyan]═══ Demo 2: Parallel Batch Execution ═══[/bold cyan]\n")

    tools = ["gemini", "codex", "cursor-agent"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        callback = RichBatchProgressCallback(progress)

        with batch_consultation_progress(
            tools,
            timeout=120,
            callback=callback
        ) as prog:
            # Simulate staggered completion

            time.sleep(0.8)
            prog.mark_complete("cursor-agent", ToolResponse(
                tool="cursor-agent",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=0.8,
                timestamp=datetime.now().isoformat(),
                model="composer-1",
                prompt="Sample"
            ))

            time.sleep(0.7)
            prog.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=1.5,
                timestamp=datetime.now().isoformat(),
                model="gpt-5-codex",
                prompt="Sample"
            ))

            time.sleep(0.5)
            prog.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.ERROR,
                output="",
                error="Connection error",
                duration=2.0,
                timestamp=datetime.now().isoformat(),
                model="gemini-2.5-pro",
                prompt="Sample"
            ))

    console.print()


def demo_status_display():
    """Show status display examples."""
    console.print("\n[bold cyan]═══ Demo 3: Status Display Examples ═══[/bold cyan]\n")

    # Success status
    table = Table(title="Tool Execution Results", box=box.ROUNDED)
    table.add_column("Status", style="bold")
    table.add_column("Tool")
    table.add_column("Duration")
    table.add_column("Details")

    table.add_row(
        "[green]✓ SUCCESS[/green]",
        "[cyan]gemini[/cyan]",
        "45.2s",
        "Model: gemini-2.5-pro | Output: 2,048 chars"
    )
    table.add_row(
        "[yellow]⏰ TIMEOUT[/yellow]",
        "[cyan]codex[/cyan]",
        "90.0s",
        "Model: gpt-5-codex | Exceeded timeout"
    )
    table.add_row(
        "[red]✗ ERROR[/red]",
        "[cyan]cursor-agent[/cyan]",
        "5.1s",
        "Connection refused"
    )
    table.add_row(
        "[green]✓ SUCCESS[/green]",
        "[cyan]gemini[/cyan]",
        "38.7s",
        "Model: gemini-exp-1114 | Output: 1,536 chars"
    )

    console.print(table)
    console.print()


def demo_panel_display():
    """Show panel-based progress display."""
    console.print("\n[bold cyan]═══ Demo 4: Panel Display ═══[/bold cyan]\n")

    panel = Panel(
        "[cyan]gemini[/cyan]\n\n"
        "[dim]Model:[/dim] gemini-2.5-pro\n"
        "[dim]Status:[/dim] [yellow]⏳ Running[/yellow]\n"
        "[dim]Elapsed:[/dim] 32.4s / 90s\n"
        "[dim]Progress:[/dim] [yellow]36%[/yellow]\n\n"
        "Waiting for response...",
        title="[bold]AI Tool Consultation[/bold]",
        border_style="cyan",
        box=box.DOUBLE
    )
    console.print(panel)

    time.sleep(1)

    panel = Panel(
        "[cyan]gemini[/cyan]\n\n"
        "[dim]Model:[/dim] gemini-2.5-pro\n"
        "[dim]Status:[/dim] [green]✓ Completed[/green]\n"
        "[dim]Duration:[/dim] 45.2s\n"
        "[dim]Output:[/dim] 2,048 characters\n\n"
        "[green]Response received successfully[/green]",
        title="[bold]AI Tool Consultation[/bold]",
        border_style="green",
        box=box.DOUBLE
    )
    console.print(panel)
    console.print()


def main():
    """Run Rich TUI preview."""
    console.clear()
    console.print()
    console.rule("[bold cyan]Rich TUI Progress Feedback Preview[/bold cyan]")
    console.print()
    console.print(
        "[dim]This preview shows what the progress feedback will look like with\n"
        "the Rich library providing actual TUI elements (progress bars, spinners,\n"
        "status displays, and panels).[/dim]"
    )

    # Run demos
    demo_single_tool_rich()
    time.sleep(1)

    demo_batch_execution_rich()
    time.sleep(1)

    demo_status_display()
    time.sleep(1)

    demo_panel_display()

    console.rule("[bold green]Preview Complete[/bold green]")
    console.print()
    console.print("[bold]Next Steps:[/bold]")
    console.print("  • Integrate context managers with execute_tool() and execute_tools_parallel()")
    console.print("  • Implement RichProgressCallback for production use")
    console.print("  • Add real-time updates during subprocess execution (Phase 5)")
    console.print("  • Add cancellation support with user feedback")
    console.print()


if __name__ == "__main__":
    main()
