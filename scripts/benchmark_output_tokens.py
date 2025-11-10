#!/usr/bin/env python3
"""
Benchmark script to measure token counts for different output formats.

Tests high-frequency SDD CLI commands (list-specs, progress, list-phases) across:
- Text format with Plain UI (simple text)
- JSON format (compact)
- JSON format (pretty-printed)

Uses config-driven testing: Creates temporary .claude/sdd_config.json files
with different default_mode/json_compact settings and uses --path to load them.

Note: Text output uses PlainUi because subprocess capture means stdout is not a TTY.

Usage:
    python scripts/benchmark_output_tokens.py [--spec-id SPEC_ID]

Example:
    python scripts/benchmark_output_tokens.py --spec-id my-spec-001
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed. Install with: pip install tiktoken")
    sys.exit(1)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Warning: Could not count tokens: {e}")
        return len(text.split())  # Fallback to word count


def create_temp_config(config_data: Dict, project_root: Path = None) -> Path:
    """
    Create a temporary .claude/sdd_config.json file.

    Args:
        config_data: Config dict to write (e.g., {"output": {"default_mode": "rich"}})
        project_root: Project root to symlink specs from (default: cwd)

    Returns:
        Path to temporary directory containing .claude/sdd_config.json
    """
    import os

    if project_root is None:
        project_root = Path.cwd()

    temp_dir = Path(tempfile.mkdtemp(prefix="sdd_benchmark_"))
    config_dir = temp_dir / ".claude"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "sdd_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    # Symlink specs directory so commands can find specs
    specs_source = project_root / "specs"
    if specs_source.exists():
        specs_link = temp_dir / "specs"
        os.symlink(specs_source, specs_link)

    return temp_dir


def run_command(cmd: List[str], env_vars: Dict[str, str] = None, config_dir: Path = None) -> Tuple[str, int, float]:
    """
    Run a command and capture output.

    Args:
        cmd: Command to run
        env_vars: Environment variables to set
        config_dir: If provided, add --path flag to use this directory for config

    Returns:
        Tuple of (output, return_code, execution_time)
    """
    import time
    import os

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    # Add --path flag to use temporary config directory
    full_cmd = cmd.copy()
    if config_dir:
        full_cmd.extend(['--path', str(config_dir)])

    start_time = time.time()
    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        env=env
    )
    elapsed = time.time() - start_time

    return result.stdout + result.stderr, result.returncode, elapsed


def benchmark_command(
    command: List[str],
    label: str,
    formats: Dict[str, Dict]
) -> Dict[str, Dict]:
    """
    Benchmark a command across different output formats using config files.

    Args:
        command: Base command to run (e.g., ['sdd', 'progress', 'spec-id'])
        label: Human-readable label for the command
        formats: Dict mapping format name to config data and env vars

    Returns:
        Dict mapping format name to metrics
    """
    results = {}

    print(f"\n{'='*60}")
    print(f"Benchmarking: {label}")
    print(f"{'='*60}")

    for format_name, config in formats.items():
        print(f"\n  Testing {format_name}...", end=" ", flush=True)

        # Create temporary config directory
        temp_dir = None
        try:
            if config.get("config_data"):
                temp_dir = create_temp_config(config["config_data"])

            # Run command (config drives format via --path)
            output, return_code, elapsed = run_command(
                command,
                env_vars=config.get("env_vars", {}),
                config_dir=temp_dir
            )

            if return_code != 0:
                print(f"❌ FAILED (exit code {return_code})")
                results[format_name] = {
                    "success": False,
                    "error": f"Command failed with exit code {return_code}"
                }
                continue

            # Measure output
            char_count = len(output)
            line_count = output.count('\n')
            token_count = count_tokens(output)

            print(f"✓ {token_count:,} tokens")

            results[format_name] = {
                "success": True,
                "output_length": char_count,
                "line_count": line_count,
                "token_count": token_count,
                "execution_time": elapsed,
                "sample_output": output[:200] + ("..." if len(output) > 200 else "")
            }

        finally:
            # Clean up temporary config
            if temp_dir and temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    return results


def generate_report(all_results: Dict[str, Dict], output_path: Path = None):
    """Generate markdown report from benchmark results."""

    report_lines = [
        "# SDD Output Format Token Benchmark Report",
        "",
        f"Generated: {Path(__file__).name}",
        "",
        "## Overview",
        "",
        "This report compares token counts across different output formats for high-frequency SDD CLI commands.",
        "",
        "**Testing Method**: Config-driven (creates temporary `.claude/sdd_config.json` with different `default_mode` settings)",
        "",
        "### Formats Tested",
        "",
        "- **Text (Plain)**: `default_mode: \"plain\"` - Simple text format (subprocess capture = non-TTY)",
        "- **JSON (Compact)**: `default_mode: \"json\"`, `json_compact: true` - Compact JSON",
        "- **JSON (Pretty)**: `default_mode: \"json\"`, `json_compact: false` - Pretty-printed JSON",
        "",
        "---",
        ""
    ]

    for command_name, results in all_results.items():
        report_lines.extend([
            f"## {command_name}",
            ""
        ])

        # Create comparison table
        report_lines.extend([
            "| Format | Tokens | Characters | Lines | Time (s) | Efficiency |",
            "|--------|--------|------------|-------|----------|------------|"
        ])

        # Find baseline (text rich) for comparison
        baseline_tokens = None
        for format_name, metrics in results.items():
            if metrics.get("success") and "text" in format_name.lower() and "rich" in format_name.lower():
                baseline_tokens = metrics["token_count"]
                break

        for format_name, metrics in results.items():
            if not metrics.get("success"):
                report_lines.append(f"| {format_name} | ❌ Failed | - | - | - | - |")
                continue

            tokens = metrics["token_count"]
            chars = metrics["output_length"]
            lines = metrics["line_count"]
            time_s = metrics["execution_time"]

            # Calculate efficiency vs baseline
            if baseline_tokens and baseline_tokens > 0:
                efficiency = f"{(baseline_tokens / tokens * 100):.1f}%"
                if tokens < baseline_tokens:
                    efficiency += " ⚡"
                elif tokens > baseline_tokens * 1.2:
                    efficiency += " 📈"
            else:
                efficiency = "Baseline"

            report_lines.append(
                f"| {format_name} | {tokens:,} | {chars:,} | {lines} | {time_s:.3f} | {efficiency} |"
            )

        report_lines.append("")

        # Add sample output for first successful format
        for format_name, metrics in results.items():
            if metrics.get("success"):
                report_lines.extend([
                    f"### Sample Output ({format_name})",
                    "",
                    "```",
                    metrics.get("sample_output", ""),
                    "```",
                    ""
                ])
                break

        report_lines.append("---")
        report_lines.append("")

    # Add summary
    report_lines.extend([
        "## Summary & Recommendations",
        "",
        "### Token Efficiency Ranking",
        ""
    ])

    # Calculate average efficiency across all commands
    format_avg_tokens = {}
    for command_name, results in all_results.items():
        for format_name, metrics in results.items():
            if metrics.get("success"):
                if format_name not in format_avg_tokens:
                    format_avg_tokens[format_name] = []
                format_avg_tokens[format_name].append(metrics["token_count"])

    # Sort by average token count
    format_rankings = sorted(
        [(fmt, sum(tokens) / len(tokens)) for fmt, tokens in format_avg_tokens.items()],
        key=lambda x: x[1]
    )

    for rank, (format_name, avg_tokens) in enumerate(format_rankings, 1):
        report_lines.append(f"{rank}. **{format_name}**: {avg_tokens:,.0f} tokens (average)")

    if format_rankings:
        report_lines.extend([
            "",
            "### Recommendations",
            "",
            "**For API/LLM Consumption:**",
            f"- Best format: **{format_rankings[0][0]}** ({format_rankings[0][1]:,.0f} tokens avg)",
            "- Most token-efficient for programmatic processing",
            "",
            "**For Human Reading:**",
            "- Use Rich TUI format for interactive terminals",
            "- Provides best readability with syntax highlighting",
            "",
            "**For CI/CD Pipelines:**",
            "- Use Plain text or compact JSON",
            "- Avoids ANSI codes and unnecessary formatting",
        ])
    else:
        report_lines.extend([
            "",
            "### Recommendations",
            "",
            "⚠️ **No successful test results** - all formats failed. Please check the errors above.",
        ])

    report_lines.extend([
        "",
        "---",
        "",
        f"*Report generated by {Path(__file__).name}*"
    ])

    report_content = "\n".join(report_lines)

    if output_path:
        output_path.write_text(report_content)
        print(f"\n\n✅ Report saved to: {output_path}")

    return report_content


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark SDD CLI output token counts"
    )
    parser.add_argument(
        "--spec-id",
        help="Spec ID to use for benchmarking (if not provided, will look for any active spec)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/OUTPUT_FORMAT_BENCHMARKS.md"),
        help="Output path for benchmark report"
    )

    args = parser.parse_args()

    # Find a spec to test with
    spec_id = args.spec_id
    if not spec_id:
        print("Finding active spec...")
        output, code, _ = run_command(["sdd", "list-specs", "--json"])
        if code == 0 and output:
            try:
                # Try to parse JSON output
                specs_data = json.loads(output)
                if isinstance(specs_data, list) and len(specs_data) > 0:
                    # Get first spec ID
                    spec_id = specs_data[0].get('spec_id')
                    if spec_id:
                        print(f"Using spec: {spec_id}")
            except json.JSONDecodeError:
                # Fallback: try to extract from text output
                lines = [l.strip() for l in output.split('\n') if l.strip()]
                for line in lines:
                    # Look for lines that look like spec IDs (contains date pattern)
                    if '-2025-' in line or '-2024-' in line:
                        # Extract the spec ID (first word on the line)
                        parts = line.split()
                        if parts:
                            spec_id = parts[0].strip('│').strip()
                            print(f"Using spec: {spec_id}")
                            break

    if not spec_id:
        print("Error: No spec ID provided and could not find active spec")
        print("Usage: python benchmark_output_tokens.py --spec-id YOUR_SPEC_ID")
        sys.exit(1)

    # Define output format configurations using config files
    # Note: Subprocess capture means stdout is not a TTY, so text output uses PlainUi automatically
    formats = {
        "Text (Plain)": {
            "config_data": {
                "output": {
                    "default_mode": "plain",
                    "json_compact": True
                }
            },
            "env_vars": {}
        },
        "JSON (Compact)": {
            "config_data": {
                "output": {
                    "default_mode": "json",
                    "json_compact": True
                }
            },
            "env_vars": {}
        },
        "JSON (Pretty)": {
            "config_data": {
                "output": {
                    "default_mode": "json",
                    "json_compact": False
                }
            },
            "env_vars": {}
        }
    }

    # Commands to benchmark
    commands = {
        "sdd list-specs": (
            ["sdd", "list-specs"],
            "List all specs with details"
        ),
        "sdd progress": (
            ["sdd", "progress", spec_id],
            f"Overall spec progress for {spec_id}"
        ),
        "sdd list-phases": (
            ["sdd", "list-phases", spec_id],
            f"List all phases for {spec_id}"
        )
    }

    # Run benchmarks
    all_results = {}
    for cmd_name, (cmd, label) in commands.items():
        try:
            results = benchmark_command(cmd, label, formats)
            all_results[cmd_name] = results
        except Exception as e:
            print(f"\n❌ Error benchmarking {cmd_name}: {e}")
            all_results[cmd_name] = {
                format_name: {"success": False, "error": str(e)}
                for format_name in formats.keys()
            }

    # Generate report
    report = generate_report(all_results, args.output)

    # Also print summary to stdout
    print("\n\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    print(f"\nFull report: {args.output}")


if __name__ == "__main__":
    main()
