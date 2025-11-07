#!/usr/bin/env python3
"""
Demo script showing TUI progress feedback in action.

This demonstrates the progress context managers with a simple
print-based callback implementation.
"""

import time
import sys
from datetime import datetime

# Add src to path for import
sys.path.insert(0, '/home/tyler/Documents/GitHub/claude-sdd-toolkit/src/claude_skills')

from claude_skills.common.tui_progress import (
    ai_consultation_progress,
    batch_consultation_progress,
    ProgressCallback
)
from claude_skills.common.ai_tools import ToolStatus, ToolResponse


class PrintProgressCallback:
    """Simple print-based progress callback for demonstration."""

    def on_start(self, tool: str, timeout: int, **context) -> None:
        """Print when tool starts."""
        model = context.get('model', 'default')
        print(f"\n🚀 Starting {tool} (model: {model}, timeout: {timeout}s)")
        print(f"   {'─' * 60}")

    def on_update(self, tool: str, elapsed: float, timeout: int, **context) -> None:
        """Print periodic updates (not yet implemented in subprocess)."""
        remaining = timeout - elapsed
        percent = (elapsed / timeout) * 100
        print(f"   ⏱️  {elapsed:.1f}s elapsed, {remaining:.1f}s remaining ({percent:.0f}%)")

    def on_complete(self, tool: str, status: ToolStatus, duration: float, **context) -> None:
        """Print completion status."""
        if status == ToolStatus.SUCCESS:
            output_length = context.get('output_length', 0)
            print(f"   ✅ {tool} completed ({duration:.2f}s)")
            print(f"   📊 Output: {output_length} characters")
        elif status == ToolStatus.TIMEOUT:
            print(f"   ⏰ {tool} timed out after {duration:.2f}s")
        elif status == ToolStatus.ERROR:
            error = context.get('error', 'Unknown error')
            print(f"   ❌ {tool} failed ({duration:.2f}s)")
            print(f"   💥 Error: {error}")
        elif status == ToolStatus.NOT_FOUND:
            print(f"   🔍 {tool} not found in PATH")
        print(f"   {'─' * 60}\n")

    def on_batch_start(self, tools: list[str], count: int, timeout: int, **context) -> None:
        """Print when batch starts."""
        print(f"\n🚀 Starting batch execution of {count} tools")
        print(f"   Tools: {', '.join(tools)}")
        print(f"   Per-tool timeout: {timeout}s")
        print(f"   {'═' * 60}")

    def on_tool_complete(self, tool: str, response: ToolResponse, completed_count: int, total_count: int) -> None:
        """Print when individual tool completes in batch."""
        status_emoji = "✅" if response.success else "❌"
        print(f"   {status_emoji} {tool} finished ({response.duration:.2f}s) - Progress: {completed_count}/{total_count}")

    def on_batch_complete(self, total_count: int, success_count: int, failure_count: int,
                         total_duration: float, max_duration: float) -> None:
        """Print batch summary."""
        print(f"   {'═' * 60}")
        print(f"   📊 Batch Summary:")
        print(f"      • Total tools: {total_count}")
        print(f"      • Successes: {success_count}")
        print(f"      • Failures: {failure_count}")
        print(f"      • Total time: {total_duration:.2f}s (wall clock)")
        print(f"      • Longest tool: {max_duration:.2f}s")
        print(f"   {'═' * 60}\n")


def demo_single_tool_success():
    """Demo 1: Single tool execution (success)."""
    print("\n" + "=" * 80)
    print("DEMO 1: Single Tool Execution (Success)")
    print("=" * 80)

    callback = PrintProgressCallback()

    with ai_consultation_progress(
        "gemini",
        timeout=90,
        callback=callback,
        model="gemini-2.5-pro",
        prompt_length=512
    ) as progress:
        # Simulate tool execution
        time.sleep(1.5)

        # Create successful response
        response = ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="This is a sample response from the AI model with comprehensive analysis...",
            error=None,
            duration=1.5,
            timestamp=datetime.now().isoformat(),
            model="gemini-2.5-pro",
            prompt="Sample prompt"
        )

        progress.complete(response)


def demo_single_tool_timeout():
    """Demo 2: Single tool execution (timeout)."""
    print("\n" + "=" * 80)
    print("DEMO 2: Single Tool Execution (Timeout)")
    print("=" * 80)

    callback = PrintProgressCallback()

    with ai_consultation_progress(
        "codex",
        timeout=30,
        callback=callback,
        model="gpt-5-codex"
    ) as progress:
        # Simulate longer execution
        time.sleep(1.0)

        # Create timeout response
        response = ToolResponse(
            tool="codex",
            status=ToolStatus.TIMEOUT,
            output="",
            error="Tool timed out after 30s",
            duration=30.0,
            timestamp=datetime.now().isoformat(),
            model="gpt-5-codex",
            prompt="Sample prompt"
        )

        progress.complete(response)


def demo_single_tool_error():
    """Demo 3: Single tool execution (error)."""
    print("\n" + "=" * 80)
    print("DEMO 3: Single Tool Execution (Error)")
    print("=" * 80)

    callback = PrintProgressCallback()

    with ai_consultation_progress(
        "cursor-agent",
        timeout=60,
        callback=callback,
        model="cheetah"
    ) as progress:
        # Simulate execution with error
        time.sleep(0.5)

        # Create error response
        response = ToolResponse(
            tool="cursor-agent",
            status=ToolStatus.ERROR,
            output="",
            error="Connection refused: Unable to reach cursor-agent service",
            duration=0.5,
            timestamp=datetime.now().isoformat(),
            model="cheetah",
            prompt="Sample prompt"
        )

        progress.complete(response)


def demo_batch_execution():
    """Demo 4: Parallel batch execution."""
    print("\n" + "=" * 80)
    print("DEMO 4: Parallel Batch Execution (3 tools)")
    print("=" * 80)

    callback = PrintProgressCallback()

    tools = ["gemini", "codex", "cursor-agent"]

    with batch_consultation_progress(
        tools,
        timeout=120,
        callback=callback,
        models={"gemini": "gemini-2.5-pro", "codex": "gpt-5-codex", "cursor-agent": "cheetah"}
    ) as progress:
        # Simulate parallel execution with staggered completion

        # First tool completes quickly
        time.sleep(0.8)
        response1 = ToolResponse(
            tool="cursor-agent",
            status=ToolStatus.SUCCESS,
            output="Quick response",
            error=None,
            duration=0.8,
            timestamp=datetime.now().isoformat(),
            model="cheetah",
            prompt="Sample prompt"
        )
        progress.mark_complete("cursor-agent", response1)

        # Second tool completes
        time.sleep(0.5)
        response2 = ToolResponse(
            tool="codex",
            status=ToolStatus.SUCCESS,
            output="Detailed analysis with code examples...",
            error=None,
            duration=1.3,
            timestamp=datetime.now().isoformat(),
            model="gpt-5-codex",
            prompt="Sample prompt"
        )
        progress.mark_complete("codex", response2)

        # Third tool times out
        time.sleep(0.4)
        response3 = ToolResponse(
            tool="gemini",
            status=ToolStatus.TIMEOUT,
            output="",
            error="Timeout after 120s",
            duration=120.0,
            timestamp=datetime.now().isoformat(),
            model="gemini-2.5-pro",
            prompt="Sample prompt"
        )
        progress.mark_complete("gemini", response3)


def demo_auto_completion():
    """Demo 5: Auto-completion when user forgets to call complete()."""
    print("\n" + "=" * 80)
    print("DEMO 5: Auto-Completion (user forgot to call complete)")
    print("=" * 80)

    callback = PrintProgressCallback()

    with ai_consultation_progress(
        "gemini",
        timeout=90,
        callback=callback,
        model="gemini-2.5-pro"
    ) as progress:
        # Simulate work but forget to call progress.complete()
        time.sleep(1.0)
        # Context manager will auto-complete on exit

    print("   ℹ️  Note: The context manager auto-completed because complete() wasn't called")


def demo_exception_handling():
    """Demo 6: Exception during execution."""
    print("\n" + "=" * 80)
    print("DEMO 6: Exception Handling")
    print("=" * 80)

    callback = PrintProgressCallback()

    try:
        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=callback
        ) as progress:
            # Simulate work that fails
            time.sleep(0.5)
            raise ValueError("Simulated error during AI consultation")
    except ValueError as e:
        print(f"   ℹ️  Exception caught: {e}")
        print(f"   ℹ️  Progress callback was still invoked with ERROR status")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "TUI PROGRESS FEEDBACK DEMONSTRATION" + " " * 23 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  This demo shows the progress context managers in action with a" + " " * 11 + "║")
    print("║" + "  simple print-based callback. In production, these same callbacks" + " " * 8 + "║")
    print("║" + "  will drive Rich TUI progress bars, spinners, and status displays." + " " * 8 + "║")
    print("╚" + "═" * 78 + "╝")

    # Run demos
    demo_single_tool_success()
    time.sleep(0.5)

    demo_single_tool_timeout()
    time.sleep(0.5)

    demo_single_tool_error()
    time.sleep(0.5)

    demo_batch_execution()
    time.sleep(0.5)

    demo_auto_completion()
    time.sleep(0.5)

    demo_exception_handling()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("  • These context managers will be integrated with execute_tool() in Phase 4")
    print("  • Rich library will provide actual TUI elements (progress bars, spinners)")
    print("  • The callback interface remains the same - just swap PrintProgressCallback")
    print("    for RichProgressCallback")
    print("\n")


if __name__ == "__main__":
    main()
