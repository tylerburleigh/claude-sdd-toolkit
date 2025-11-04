#!/usr/bin/env python3
"""
Token Efficiency Measurement Script

Measures token savings achieved by --compact flag across SDD commands.
Runs each command with and without --compact, counts tokens using tiktoken,
and calculates savings percentages.

Usage:
    python scripts/measure_token_efficiency.py <spec-id> <task-id>

Example:
    python scripts/measure_token_efficiency.py compact-json-output-2025-11-03-001 task-3-1

Requirements:
    - tiktoken: pip install tiktoken
    - SDD toolkit installed and accessible via 'sdd' command

Targets:
    - prepare-task: 65-70% token savings
    - task-info: 85-90% token savings
    - Overall minimum: 55% token savings for all commands
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Tuple

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken is not installed.")
    print("Please install it with: pip install tiktoken")
    sys.exit(1)


class TokenMeasurement:
    """Measures and compares token counts for SDD command outputs."""

    # Token savings targets for each command
    TARGETS = {
        "prepare-task": {"min": 65, "max": 70},
        "task-info": {"min": 85, "max": 90},
        "check-deps": {"min": 55, "max": 100},  # Overall minimum
        "progress": {"min": 55, "max": 100},
        "next-task": {"min": 55, "max": 100},
    }

    def __init__(self, spec_id: str, task_id: str):
        """Initialize with spec and task IDs."""
        self.spec_id = spec_id
        self.task_id = task_id
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.results: List[Dict] = []

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def run_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Run a command and return (success, output).

        Args:
            command: Command and arguments as list

        Returns:
            Tuple of (success boolean, output string)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds"
        except Exception as e:
            return False, f"Error running command: {e}"

    def measure_command(self, command_name: str, args: List[str]) -> Dict:
        """
        Measure token counts for a command with and without --compact.

        Args:
            command_name: Name of the SDD command (e.g., "prepare-task")
            args: Additional arguments for the command

        Returns:
            Dictionary with measurement results
        """
        print(f"\n🔵 Measuring: {command_name}")

        # Run without --compact
        cmd_normal = ["sdd", command_name] + args + ["--json"]
        success_normal, output_normal = self.run_command(cmd_normal)

        if not success_normal:
            print(f"  ❌ Normal command failed: {output_normal[:100]}")
            return {
                "command": command_name,
                "error": output_normal,
                "success": False,
            }

        # Run with --compact
        cmd_compact = ["sdd", command_name] + args + ["--compact", "--json"]
        success_compact, output_compact = self.run_command(cmd_compact)

        if not success_compact:
            print(f"  ❌ Compact command failed: {output_compact[:100]}")
            return {
                "command": command_name,
                "error": output_compact,
                "success": False,
            }

        # Count tokens
        tokens_normal = self.count_tokens(output_normal)
        tokens_compact = self.count_tokens(output_compact)

        # Calculate savings
        if tokens_normal == 0:
            savings_pct = 0.0
        else:
            savings_pct = ((tokens_normal - tokens_compact) / tokens_normal) * 100

        # Check if meets target
        target = self.TARGETS.get(command_name, {"min": 55, "max": 100})
        meets_target = target["min"] <= savings_pct <= target["max"]

        result = {
            "command": command_name,
            "tokens_normal": tokens_normal,
            "tokens_compact": tokens_compact,
            "savings_tokens": tokens_normal - tokens_compact,
            "savings_pct": round(savings_pct, 2),
            "target_min": target["min"],
            "target_max": target["max"],
            "meets_target": meets_target,
            "success": True,
        }

        # Print result
        status = "✅" if meets_target else "❌"
        print(f"  {status} Normal: {tokens_normal} tokens | Compact: {tokens_compact} tokens")
        print(f"     Savings: {result['savings_pct']}% (target: {target['min']}-{target['max']}%)")

        return result

    def run_all_measurements(self) -> bool:
        """
        Run measurements for all 5 commands.

        Returns:
            True if all commands meet their targets, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Token Efficiency Measurement")
        print(f"{'='*70}")
        print(f"Spec ID: {self.spec_id}")
        print(f"Task ID: {self.task_id}")
        print(f"Encoding: cl100k_base (Claude tokenizer)")

        # Measure each command
        commands = [
            ("prepare-task", [self.spec_id]),
            ("task-info", [self.spec_id, self.task_id]),
            ("check-deps", [self.spec_id, self.task_id]),
            ("progress", [self.spec_id]),
            ("next-task", [self.spec_id]),
        ]

        for command_name, args in commands:
            result = self.measure_command(command_name, args)
            self.results.append(result)

        return self.print_summary()

    def print_summary(self) -> bool:
        """
        Print summary report and return overall pass/fail.

        Returns:
            True if all commands passed, False otherwise
        """
        print(f"\n{'='*70}")
        print("Summary Report")
        print(f"{'='*70}\n")

        # Print table header
        print(f"{'Command':<15} {'Normal':>10} {'Compact':>10} {'Saved':>10} {'Savings %':>12} {'Target':>15} {'Status':>8}")
        print("-" * 90)

        all_passed = True
        total_normal = 0
        total_compact = 0

        for result in self.results:
            if not result["success"]:
                print(f"{result['command']:<15} {'ERROR':<45} ❌")
                all_passed = False
                continue

            cmd = result["command"]
            tokens_n = result["tokens_normal"]
            tokens_c = result["tokens_compact"]
            saved = result["savings_tokens"]
            savings_pct = result["savings_pct"]
            target = f"{result['target_min']}-{result['target_max']}%"
            status = "✅" if result["meets_target"] else "❌"

            print(f"{cmd:<15} {tokens_n:>10} {tokens_c:>10} {saved:>10} {savings_pct:>11.2f}% {target:>15} {status:>8}")

            total_normal += tokens_n
            total_compact += tokens_c

            if not result["meets_target"]:
                all_passed = False

        # Print totals
        print("-" * 90)
        total_saved = total_normal - total_compact
        total_savings_pct = ((total_normal - total_compact) / total_normal * 100) if total_normal > 0 else 0

        print(f"{'TOTALS':<15} {total_normal:>10} {total_compact:>10} {total_saved:>10} {total_savings_pct:>11.2f}%")

        # Print overall status
        print(f"\n{'='*70}")
        if all_passed:
            print("✅ SUCCESS: All commands meet their token savings targets!")
        else:
            print("❌ FAILURE: Some commands did not meet their targets.")
            print("\nFailed commands:")
            for result in self.results:
                if result["success"] and not result["meets_target"]:
                    print(f"  - {result['command']}: {result['savings_pct']}% (target: {result['target_min']}-{result['target_max']}%)")

        print(f"{'='*70}\n")

        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Measure token efficiency of SDD commands with --compact flag"
    )
    parser.add_argument("spec_id", help="Specification ID to test with")
    parser.add_argument("task_id", help="Task ID to test with")

    args = parser.parse_args()

    # Run measurements
    measurer = TokenMeasurement(args.spec_id, args.task_id)
    success = measurer.run_all_measurements()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
