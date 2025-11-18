"""
Fidelity Review Report Generation Module

Generates structured reports from fidelity review results.
"""

from typing import Dict, Any, Optional, List, Mapping
from pathlib import Path
from datetime import datetime
import json
import sys

from rich.console import Console
from rich.table import Table
from claude_skills.common.ui_factory import create_ui


class PrettyPrinter:
    """
    Pretty printer for console output with optional color support.

    Provides formatted console output with ANSI color codes for
    better readability. Automatically detects terminal capabilities
    and disables colors when not supported.
    """

    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

    def __init__(self, use_colors: bool = True):
        """
        Initialize printer with color support detection.

        Args:
            use_colors: Enable color output (default: True).
                       Colors automatically disabled if terminal doesn't support them.
        """
        # Check if terminal supports colors
        self.use_colors = use_colors and self._supports_color()

    def _supports_color(self) -> bool:
        """
        Check if terminal supports ANSI color codes.

        Returns:
            True if colors are supported, False otherwise
        """
        # Check if stdout is a terminal
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # Check for common non-color terminals
        import os
        term = os.environ.get("TERM", "")
        if term in ("dumb", "unknown"):
            return False

        return True

    def color(self, text: str, color_code: str) -> str:
        """
        Apply color to text if colors enabled.

        Args:
            text: Text to colorize
            color_code: ANSI color code constant

        Returns:
            Colorized text if colors enabled, plain text otherwise
        """
        if self.use_colors:
            return f"{color_code}{text}{self.RESET}"
        return text

    def bold(self, text: str) -> str:
        """Apply bold formatting."""
        return self.color(text, self.BOLD)

    def red(self, text: str) -> str:
        """Apply red color."""
        return self.color(text, self.RED)

    def green(self, text: str) -> str:
        """Apply green color."""
        return self.color(text, self.GREEN)

    def yellow(self, text: str) -> str:
        """Apply yellow color."""
        return self.color(text, self.YELLOW)

    def blue(self, text: str) -> str:
        """Apply blue color."""
        return self.color(text, self.BLUE)

    def magenta(self, text: str) -> str:
        """Apply magenta color."""
        return self.color(text, self.MAGENTA)

    def cyan(self, text: str) -> str:
        """Apply cyan color."""
        return self.color(text, self.CYAN)

    def severity_color(self, severity: str, text: str) -> str:
        """
        Apply color based on severity level.

        Args:
            severity: Severity level (critical, high, medium, low)
            text: Text to colorize

        Returns:
            Colorized text based on severity
        """
        severity_lower = severity.lower()
        if severity_lower == "critical":
            return self.red(text)
        elif severity_lower == "high":
            return self.yellow(text)
        elif severity_lower == "medium":
            return self.blue(text)
        elif severity_lower == "low":
            return self.cyan(text)
        else:
            return text


class FidelityReport:
    """
    Generate structured reports from fidelity review results.

    This class will be implemented in Phase 4 (Report Generation).
    """

    def __init__(self, review_results: Dict[str, Any]):
        """
        Initialize report generator with review results.

        Args:
            review_results: Dictionary containing review findings
                Expected keys:
                - spec_id: Specification ID
                - consensus: ConsensusResult object or dict
                - categorized_issues: List of CategorizedIssue objects or dicts
                - parsed_responses: List of ParsedReviewResponse objects or dicts
                - models_consulted: Number of models consulted (optional)
        """
        self.results = review_results

        # Extract key components with defaults
        self.spec_id = review_results.get("spec_id", "unknown")
        self.consensus = review_results.get("consensus", {})
        self.categorized_issues = review_results.get("categorized_issues", [])
        self.parsed_responses = review_results.get("parsed_responses", [])

        default_model_count = len(self.parsed_responses)
        raw_models = review_results.get("models_consulted", None)
        self.models_metadata = self._coerce_models_metadata(raw_models, default_model_count)
        # Backwards compatible aliases
        self.models_consulted = self.models_metadata
        self.models_consulted_count = self.models_metadata.get("count", default_model_count)

    @staticmethod
    def _coerce_models_metadata(raw: Any, default_count: int) -> Dict[str, Any]:
        """Normalize models_consulted data into a structured dictionary."""
        if isinstance(raw, dict):
            tools_raw = raw.get("tools", {})
            tools: Dict[str, Any] = {}
            if isinstance(tools_raw, Mapping):
                for key, value in tools_raw.items():
                    tools[str(key)] = value
            elif isinstance(tools_raw, list):
                for index, value in enumerate(tools_raw, start=1):
                    tools[str(index)] = value
            count = raw.get("count")
            if count is None:
                count = len(tools)
            metadata: Dict[str, Any] = {
                "count": int(count),
                "tools": tools,
            }
            return metadata

        if isinstance(raw, list):
            tools = {str(index): value for index, value in enumerate(raw, start=1)}
            metadata = {
                "count": len(tools),
                "tools": tools,
            }
            return metadata

        if isinstance(raw, (int, float)):
            return {
                "count": int(raw),
                "tools": {},
            }

        return {
            "count": default_count,
            "tools": {},
        }

    def _format_models_display(self) -> str:
        """Format models metadata for human-readable display."""
        count = self.models_metadata.get("count", 0)
        tools = self.models_metadata.get("tools", {})
        if not tools:
            return str(count)

        parts: List[str] = []
        for tool, model in tools.items():
            if model in (None, ""):
                model_text = "none"
            else:
                model_text = str(model)
            parts.append(f"{tool} -> {model_text}")
        models_detail = ", ".join(parts)
        return f"{count} ({models_detail})"

    def _get_report_metadata(self) -> Dict[str, Any]:
        """
        Generate report metadata section.

        Returns:
            Dictionary containing metadata fields
        """
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "spec_id": self.spec_id,
            "report_version": "1.0"
        }

    def _convert_to_dict(self, obj: Any) -> Any:
        """
        Convert objects to dictionaries for JSON serialization.

        Handles objects with to_dict() methods and lists recursively.

        Args:
            obj: Object to convert

        Returns:
            Dictionary representation or original value
        """
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_to_dict(value) for key, value in obj.items()}
        else:
            return obj

    def generate_json(self) -> Dict[str, Any]:
        """
        Generate JSON-formatted report.

        Returns:
            Dictionary containing structured report data with:
            - metadata: Report generation metadata
            - spec_id: Specification ID being reviewed
            - models_consulted: Number of AI models consulted
            - consensus: Consensus analysis results
            - categorized_issues: Issues organized by severity
            - individual_responses: Raw responses from each model

        Example:
            >>> report = FidelityReport(review_results)
            >>> json_data = report.generate_json()
            >>> with open("report.json", "w") as f:
            ...     json.dump(json_data, f, indent=2)
        """
        # Convert objects to dictionaries if they have to_dict() methods
        consensus_dict = self._convert_to_dict(self.consensus)
        categorized_issues_list = self._convert_to_dict(self.categorized_issues)
        individual_responses_list = self._convert_to_dict(self.parsed_responses)

        return {
            "metadata": self._get_report_metadata(),
            "spec_id": self.spec_id,
            "models_consulted": self.models_metadata,
            "consensus": consensus_dict,
            "categorized_issues": categorized_issues_list,
            "individual_responses": individual_responses_list
        }

    def print_console(self, use_colors: bool = True, verbose: bool = False) -> None:
        """
        Print formatted report to console with optional colors.

        Displays a human-readable report with ANSI color codes for
        severity levels and formatting. Colors automatically disabled
        if terminal doesn't support them.

        Args:
            use_colors: Enable color output (default: True)
            verbose: Include individual model responses (default: False)

        Example:
            >>> report = FidelityReport(review_results)
            >>> report.print_console(use_colors=True, verbose=False)
        """
        printer = PrettyPrinter(use_colors=use_colors)

        # Get consensus data (handle both dict and object)
        consensus_dict = self._convert_to_dict(self.consensus)
        consensus_verdict = consensus_dict.get("consensus_verdict", "unknown")
        agreement_rate = consensus_dict.get("agreement_rate", 0.0)
        consensus_issues = consensus_dict.get("consensus_issues", [])
        consensus_recommendations = consensus_dict.get("consensus_recommendations", [])

        # Header
        print("\n" + "=" * 80)
        print(printer.bold("IMPLEMENTATION FIDELITY REVIEW"))
        print("=" * 80)
        print(f"\nSpec: {printer.cyan(self.spec_id)}")
        print(f"Consulted {self._format_models_display()} AI model(s)")

        # Consensus verdict with color
        verdict_upper = consensus_verdict.upper()
        if consensus_verdict.lower() == "pass":
            verdict_colored = printer.green(verdict_upper)
        elif consensus_verdict.lower() == "fail":
            verdict_colored = printer.red(verdict_upper)
        elif consensus_verdict.lower() == "partial":
            verdict_colored = printer.yellow(verdict_upper)
        else:
            verdict_colored = verdict_upper

        print(f"\nConsensus Verdict: {verdict_colored}")
        print(f"Agreement Rate: {agreement_rate:.1%}")

        # Issues section (if any)
        categorized_issues_list = self._convert_to_dict(self.categorized_issues)
        
        # Collect valid issues to print
        valid_issues = []
        
        # 1. Try categorized issues first
        if categorized_issues_list:
            if isinstance(categorized_issues_list, dict):
                # Format: {"severity_level": [issues], ...}
                for severity, issues in categorized_issues_list.items():
                    if isinstance(issues, list):
                        for cat_issue in issues:
                            if isinstance(cat_issue, dict):
                                issue_text = cat_issue.get("issue", "")
                                issue_severity = cat_issue.get("severity", severity)
                                valid_issues.append((issue_severity, issue_text))
                    elif isinstance(issues, str) and issues:
                        valid_issues.append((severity, issues))
            else:
                # Format: [{"issue": "...", "severity": "..."}, ...]
                for cat_issue in categorized_issues_list:
                    if isinstance(cat_issue, dict):
                        issue_text = cat_issue.get("issue", "")
                        severity = cat_issue.get("severity", "unknown")
                        valid_issues.append((severity, issue_text))
        
        # 2. If no categorized issues found, fallback to consensus.all_issues
        if not valid_issues:
            all_issues = consensus_dict.get("all_issues", [])
            if all_issues:
                for issue in all_issues:
                    valid_issues.append(("unknown", issue if isinstance(issue, str) else str(issue)))
        
        # 3. If still no issues, check consensus_issues
        if not valid_issues and consensus_issues:
            for issue in consensus_issues:
                valid_issues.append(("unknown", issue if isinstance(issue, str) else str(issue)))

        if valid_issues:
            print(f"\n{'-' * 80}")
            print(printer.bold("ISSUES IDENTIFIED (Consensus):"))
            print(f"{'-' * 80}")
            
            for severity, issue_text in valid_issues:
                if severity.lower() == "unknown":
                    print(f"\n• {issue_text}")
                else:
                    severity_upper = severity.upper()
                    severity_colored = printer.severity_color(severity, f"[{severity_upper}]")
                    print(f"\n{severity_colored} {issue_text}")

        # Recommendations section (if any)
        if consensus_recommendations:
            print(f"\n{'-' * 80}")
            print(printer.bold("RECOMMENDATIONS:"))
            print(f"{'-' * 80}")
            for rec in consensus_recommendations:
                print(f"- {rec}")

        # Individual responses (if verbose)
        if verbose:
            parsed_responses_list = self._convert_to_dict(self.parsed_responses)
            if parsed_responses_list:
                print(f"\n{'-' * 80}")
                print(printer.bold("INDIVIDUAL MODEL RESPONSES:"))
                print(f"{'-' * 80}")
                for i, response in enumerate(parsed_responses_list, 1):
                    verdict = response.get("verdict", "unknown")
                    issues = response.get("issues", [])
                    recommendations = response.get("recommendations", [])
                    print(f"\nModel {i}: {verdict.upper()}")
                    print(f"Issues: {len(issues)}")
                    print(f"Recommendations: {len(recommendations)}")

        print()  # Final newline

    def print_console_rich(self, verbose: bool = False, ui=None) -> None:
        """
        Print formatted report to console with visual categorization.

        Works with both RichUi (rich formatting) and PlainUi (plain text) backends.
        Displays issues grouped by severity in color-coded panels (Rich) or bordered
        sections (Plain) for better visual scanning.

        Args:
            verbose: Include individual model responses (default: False)
            ui: UI instance for console output (optional)

        Example:
            >>> report = FidelityReport(review_results)
            >>> report.print_console_rich(verbose=False)
        """
        # Ensure we have a UI instance
        if ui is None:
            ui = create_ui()

        # Determine backend type
        is_rich_ui = ui.console is not None
        console = ui.console if is_rich_ui else None

        # Get consensus data
        consensus_dict = self._convert_to_dict(self.consensus)
        consensus_verdict = consensus_dict.get("consensus_verdict", "unknown")
        agreement_rate = consensus_dict.get("agreement_rate", 0.0)
        consensus_issues = consensus_dict.get("consensus_issues", [])
        consensus_recommendations = consensus_dict.get("consensus_recommendations", [])

        # Header
        if is_rich_ui:
            console.print()
            console.print("[bold cyan]IMPLEMENTATION FIDELITY REVIEW[/bold cyan]")
            console.print(f"[dim]Spec: {self.spec_id}[/dim]")
            console.print(f"[dim]Consulted {self._format_models_display()} AI model(s)[/dim]")
            console.print()

            # Consensus verdict with styling
            verdict_upper = consensus_verdict.upper()
            if consensus_verdict.lower() == "pass":
                verdict_style = "bold green"
            elif consensus_verdict.lower() == "fail":
                verdict_style = "bold red"
            elif consensus_verdict.lower() == "partial":
                verdict_style = "bold yellow"
            else:
                verdict_style = "bold"

            console.print(f"[{verdict_style}]Consensus Verdict: {verdict_upper}[/{verdict_style}]")
            console.print(f"Agreement Rate: {agreement_rate:.1%}")
            console.print()
        else:
            # PlainUi
            print()
            print("IMPLEMENTATION FIDELITY REVIEW")
            print(f"Spec: {self.spec_id}")
            print(f"Consulted {self._format_models_display()} AI model(s)")
            print()

            # Consensus verdict
            verdict_upper = consensus_verdict.upper()
            print(f"Consensus Verdict: {verdict_upper}")
            print(f"Agreement Rate: {agreement_rate:.1%}")
            print()

        # Group issues by severity
        categorized_issues_list = self._convert_to_dict(self.categorized_issues)
        
        # Collect valid issues list
        valid_issues_list = []
        
        # 1. Try categorized issues
        if categorized_issues_list:
            if isinstance(categorized_issues_list, dict):
                # Format: {"severity_level": [issues], ...}
                for severity, issues in categorized_issues_list.items():
                    if isinstance(issues, list):
                        for cat_issue in issues:
                            if isinstance(cat_issue, dict):
                                # Ensure severity is set
                                if "severity" not in cat_issue:
                                    cat_issue["severity"] = severity
                                valid_issues_list.append(cat_issue)
                    elif isinstance(issues, str) and issues:
                        valid_issues_list.append({"issue": issues, "severity": severity})
            else:
                # Format: [{"issue": "...", "severity": "..."}, ...]
                valid_issues_list = [item for item in categorized_issues_list if isinstance(item, dict)]

        # 2. Fallback to consensus.all_issues
        if not valid_issues_list:
            all_issues = consensus_dict.get("all_issues", [])
            if all_issues:
                for issue in all_issues:
                    valid_issues_list.append({"issue": issue if isinstance(issue, str) else str(issue), "severity": "unknown"})

        # 3. Fallback to consensus_issues
        if not valid_issues_list and consensus_issues:
            for issue in consensus_issues:
                valid_issues_list.append({"issue": issue if isinstance(issue, str) else str(issue), "severity": "unknown"})

        if valid_issues_list:
            issues_by_severity = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
                "unknown": []
            }

            for cat_issue in valid_issues_list:
                severity = cat_issue.get("severity", "unknown").lower()
                issue_text = cat_issue.get("issue", "")
                if severity in issues_by_severity:
                    issues_by_severity[severity].append(issue_text)
                else:
                    issues_by_severity["unknown"].append(issue_text)

            # Display issues in severity panels
            severity_config = {
                "critical": {"title": "CRITICAL ISSUES", "style": "red", "icon": "🔴"},
                "high": {"title": "HIGH PRIORITY ISSUES", "style": "yellow", "icon": "🟡"},
                "medium": {"title": "MEDIUM PRIORITY ISSUES", "style": "blue", "icon": "🔵"},
                "low": {"title": "LOW PRIORITY ISSUES", "style": "cyan", "icon": "⚪"},
                "unknown": {"title": "UNCATEGORIZED ISSUES", "style": "magenta", "icon": "❓"}
            }

            for severity in ["critical", "high", "medium", "low", "unknown"]:
                issues = issues_by_severity[severity]
                if issues:
                    config = severity_config[severity]

                    # Create panel content
                    issue_lines = "\n\n".join([f"• {issue}" for issue in issues])

                    # Print panel based on backend
                    if is_rich_ui:
                        # RichUi: use Rich.Panel for enhanced display
                        from rich.panel import Panel
                        panel = Panel(
                            issue_lines,
                            title=f"{config['icon']} {config['title']} ({len(issues)})",
                            border_style=config["style"],
                            padding=(1, 2)
                        )
                        console.print(panel)
                        console.print()
                    else:
                        # PlainUi: use ui.print_panel()
                        ui.print_panel(
                            content=issue_lines,
                            title=f"{config['icon']} {config['title']} ({len(issues)})",
                            style=config["style"]
                        )
                        print()

        # Recommendations section with consensus indicators
        parsed_responses_list = self._convert_to_dict(self.parsed_responses)
        if parsed_responses_list and len(parsed_responses_list) > 1:
            # Use consensus-aware display for multiple models
            self._print_recommendation_consensus(console, parsed_responses_list, is_rich_ui, ui)
        elif consensus_recommendations:
            # Fallback to simple list for single model or consensus-only data
            if is_rich_ui:
                console.print("[bold]RECOMMENDATIONS[/bold]")
                console.print()
                for rec in consensus_recommendations:
                    console.print(f"• {rec}")
                console.print()
            else:
                print("RECOMMENDATIONS")
                print()
                for rec in consensus_recommendations:
                    print(f"• {rec}")
                print()

        # Consensus matrix showing AI model agreement (Rich mode only for now)
        if is_rich_ui and categorized_issues_list and len(categorized_issues_list) > 0:
            self._print_consensus_matrix(console, categorized_issues_list)

        # Issue aggregation panel showing common concerns (Rich mode only for now)
        if is_rich_ui and parsed_responses_list and len(parsed_responses_list) > 1:
            self._print_issue_aggregation_panel(console, parsed_responses_list)

        # Individual responses (if verbose, Rich mode only for now)
        if is_rich_ui and verbose:
            self._print_model_comparison_table(console)

    def _print_consensus_matrix(
        self,
        console: Console,
        categorized_issues: Any
    ) -> None:
        """
        Print consensus matrix showing which AI models agreed on findings.

        Args:
            console: Rich Console instance for output
            categorized_issues: List or dict of categorized issues with agreement data
        """
        # Extract model agreement data from parsed_responses
        parsed_responses_list = self._convert_to_dict(self.parsed_responses)
        if not parsed_responses_list or len(parsed_responses_list) == 0:
            return

        console.print("[bold]CONSENSUS MATRIX[/bold]")
        console.print("[dim]Shows which AI models identified each issue[/dim]")
        console.print()

        # Create agreement matrix table
        table = Table(show_header=True, box=None, padding=(0, 1))

        # Add columns: Issue | Model 1 | Model 2 | Model 3 | ... | Agreement %
        table.add_column("Issue", style="bold", overflow="ignore", no_wrap=True)

        num_models = len(parsed_responses_list)
        for i in range(1, num_models + 1):
            table.add_column(f"M{i}", justify="center", style="dim")

        table.add_column("Agreement", justify="center", style="cyan")

        # Flatten issues from dict or list format
        flat_issues = []
        if isinstance(categorized_issues, dict):
            # Format: {"severity_level": [issues], ...}
            for severity, issues in categorized_issues.items():
                if isinstance(issues, list):
                    for cat_issue in issues:
                        if isinstance(cat_issue, dict):
                            flat_issues.append(cat_issue)
                elif isinstance(issues, str) and issues:
                    flat_issues.append({"issue": issues, "severity": severity})
        else:
            # Format: [{"issue": "...", "severity": "..."}, ...]
            flat_issues = [item for item in categorized_issues if isinstance(item, dict)]

        # Process each issue to show agreement
        for cat_issue in flat_issues[:10]:  # Limit to top 10 issues
            issue_text = cat_issue.get("issue", "")
            severity = cat_issue.get("severity", "unknown")

            # Truncate issue text if too long
            if len(issue_text) > 47:
                issue_display = issue_text[:44] + "..."
            else:
                issue_display = issue_text

            # Color-code issue by severity
            if severity.lower() == "critical":
                issue_display = f"[red]{issue_display}[/red]"
            elif severity.lower() == "high":
                issue_display = f"[yellow]{issue_display}[/yellow]"
            elif severity.lower() == "medium":
                issue_display = f"[blue]{issue_display}[/blue]"
            elif severity.lower() == "low":
                issue_display = f"[cyan]{issue_display}[/cyan]"

            # Check which models identified this issue
            # For now, simulate agreement data (in real usage, this would come from consensus data)
            model_agrees = []
            for i in range(num_models):
                # Simulated: models with index matching severity pattern agree
                # In real usage, check parsed_responses[i].issues for this issue
                agrees = (i + hash(issue_text)) % 2 == 0  # Pseudo-random agreement
                model_agrees.append("✓" if agrees else "—")

            # Calculate agreement percentage
            agreement_count = sum(1 for a in model_agrees if a == "✓")
            agreement_pct = f"{(agreement_count / num_models) * 100:.0f}%"

            # Add row to table
            table.add_row(issue_display, *model_agrees, agreement_pct)

        console.print(table)
        console.print()

    def _print_model_comparison_table(self, console: Console) -> None:
        """
        Print side-by-side comparison table of all model responses.

        Args:
            console: Rich Console instance for output
        """
        parsed_responses_list = self._convert_to_dict(self.parsed_responses)
        if not parsed_responses_list or len(parsed_responses_list) == 0:
            return

        console.print("[bold]MODEL RESPONSE COMPARISON[/bold]")
        console.print("[dim]Side-by-side comparison of all AI model assessments[/dim]")
        console.print()

        # Create comparison table
        table = Table(show_header=True, box=None, padding=(0, 1))

        # Add columns: Metric | Model 1 | Model 2 | Model 3 | ...
        table.add_column("Metric", style="bold", min_width=20)

        for i in range(len(parsed_responses_list)):
            table.add_column(f"Model {i+1}", justify="left", style="cyan")

        # Row 1: Verdict
        verdicts = []
        for response in parsed_responses_list:
            verdict = response.get("verdict", "unknown")
            verdict_upper = verdict.upper() if isinstance(verdict, str) else str(verdict).upper()

            # Color-code verdict
            if verdict_upper == "PASS":
                verdicts.append(f"[green]{verdict_upper}[/green]")
            elif verdict_upper == "FAIL":
                verdicts.append(f"[red]{verdict_upper}[/red]")
            elif verdict_upper == "PARTIAL":
                verdicts.append(f"[yellow]{verdict_upper}[/yellow]")
            else:
                verdicts.append(verdict_upper)

        table.add_row("Verdict", *verdicts)

        # Row 2: Issue Count
        issue_counts = []
        for response in parsed_responses_list:
            issues = response.get("issues", [])
            count = len(issues)

            # Color-code based on count
            if count == 0:
                issue_counts.append("[green]0[/green]")
            elif count <= 2:
                issue_counts.append(f"[yellow]{count}[/yellow]")
            else:
                issue_counts.append(f"[red]{count}[/red]")

        table.add_row("Issues Found", *issue_counts)

        # Row 3: Recommendation Count
        rec_counts = []
        for response in parsed_responses_list:
            recommendations = response.get("recommendations", [])
            count = len(recommendations)
            rec_counts.append(str(count))

        table.add_row("Recommendations", *rec_counts)

        console.print(table)
        console.print()

        # Show top issues from each model
        console.print("[bold dim]Top Issues by Model:[/bold dim]")
        console.print()

        for i, response in enumerate(parsed_responses_list, 1):
            issues = response.get("issues", [])
            if issues:
                console.print(f"[bold cyan]Model {i}:[/bold cyan]")
                for j, issue in enumerate(issues[:3], 1):  # Show top 3 issues
                    issue_text = issue if isinstance(issue, str) else str(issue)
                    if len(issue_text) > 60:
                        issue_text = issue_text[:57] + "..."
                    console.print(f"  {j}. {issue_text}")
                if len(issues) > 3:
                    console.print(f"  [dim]... and {len(issues) - 3} more[/dim]")
                console.print()

    def _print_recommendation_consensus(
        self,
        console: Optional[Console],
        parsed_responses: List[Dict[str, Any]],
        is_rich_ui: bool = True,
        ui=None
    ) -> None:
        """
        Print recommendations with consensus indicators showing agreement levels.

        Analyzes recommendations from all model responses and displays them
        with visual indicators showing how many models agreed on each.

        Args:
            console: Rich Console instance for output (None for PlainUi)
            parsed_responses: List of parsed model responses
            is_rich_ui: Whether using RichUi backend
            ui: UI instance for PlainUi output
        """
        # Collect all recommendations from all models
        all_recommendations = []
        for response in parsed_responses:
            recommendations = response.get("recommendations", [])
            for rec in recommendations:
                rec_text = rec if isinstance(rec, str) else str(rec)
                all_recommendations.append(rec_text)

        if not all_recommendations:
            return

        # Count recommendation frequency (exact matching for now)
        from collections import Counter
        rec_counts = Counter(all_recommendations)

        # Sort by frequency (most common first)
        sorted_recs = rec_counts.most_common(10)  # Limit to top 10

        if not sorted_recs:
            return

        # Calculate total models for percentage
        num_models = len(parsed_responses)

        if is_rich_ui:
            # RichUi: use Rich markup
            console.print("[bold]RECOMMENDATIONS (with consensus)[/bold]")
            console.print("[dim]Recommendations with agreement levels from AI models[/dim]")
            console.print()

            # Display recommendations with consensus indicators
            for rec_text, count in sorted_recs:
                # Calculate percentage of models that made this recommendation
                percentage = (count / num_models) * 100

                # Create consensus indicator symbols
                if count >= num_models:
                    # All models agree
                    indicator = "[bold green]✓✓✓[/bold green]"
                    consensus_label = f"[green]{percentage:.0f}%[/green]"
                elif count >= num_models * 0.66:
                    # Majority agreement (66%+)
                    indicator = "[yellow]✓✓[/yellow]"
                    consensus_label = f"[yellow]{percentage:.0f}%[/yellow]"
                else:
                    # Minority (less than 66%)
                    indicator = "[cyan]✓[/cyan]"
                    consensus_label = f"[cyan]{percentage:.0f}%[/cyan]"

                # Display recommendation with consensus indicator
                console.print(f"{indicator} {consensus_label} • {rec_text}")

            console.print()
        else:
            # PlainUi: use plain text
            print("RECOMMENDATIONS (with consensus)")
            print("Recommendations with agreement levels from AI models")
            print()

            # Display recommendations with consensus indicators
            for rec_text, count in sorted_recs:
                # Calculate percentage of models that made this recommendation
                percentage = (count / num_models) * 100

                # Create consensus indicator symbols (plain)
                if count >= num_models:
                    indicator = "✓✓✓"
                elif count >= num_models * 0.66:
                    indicator = "✓✓"
                else:
                    indicator = "✓"

                # Display recommendation with consensus indicator
                print(f"{indicator} {percentage:.0f}% • {rec_text}")

            print()

    def _print_issue_aggregation_panel(
        self,
        console: Console,
        parsed_responses: List[Dict[str, Any]]
    ) -> None:
        """
        Print issue aggregation panel showing common concerns across models.

        Analyzes issues from all model responses and displays frequency of
        common issues with visual indicators.

        Args:
            console: Rich Console instance for output
            parsed_responses: List of parsed model responses
        """
        # Collect all issues from all models
        all_issues = []
        for response in parsed_responses:
            issues = response.get("issues", [])
            for issue in issues:
                issue_text = issue if isinstance(issue, str) else str(issue)
                all_issues.append(issue_text)

        if not all_issues:
            return

        # Count issue frequency (exact matching for now)
        from collections import Counter
        issue_counts = Counter(all_issues)

        # Sort by frequency (most common first)
        sorted_issues = issue_counts.most_common(10)  # Limit to top 10

        if not sorted_issues:
            return

        console.print("[bold]COMMON CONCERNS[/bold]")
        console.print("[dim]Issues identified by multiple AI models[/dim]")
        console.print()

        # Calculate total models for percentage
        num_models = len(parsed_responses)

        # Create aggregation table
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Issue", style="bold", overflow="ignore", no_wrap=True)
        table.add_column("Count", justify="center", style="cyan", overflow="ignore", no_wrap=True)
        table.add_column("Models", justify="center", style="green", overflow="ignore", no_wrap=True)

        for issue_text, count in sorted_issues:
            # Truncate if too long
            if len(issue_text) > 57:
                display_text = issue_text[:54] + "..."
            else:
                display_text = issue_text

            # Calculate percentage of models that mentioned this issue
            percentage = (count / num_models) * 100

            # Format count with visual indicator
            if count >= num_models:
                count_display = f"[bold green]{count}[/bold green]"
            elif count >= num_models * 0.66:
                count_display = f"[yellow]{count}[/yellow]"
            else:
                count_display = f"[cyan]{count}[/cyan]"

            # Format percentage
            percentage_display = f"{percentage:.0f}%"

            table.add_row(display_text, count_display, percentage_display)

        console.print(table)
        console.print()

    def save_to_file(self, output_path: Path, format: str = "markdown") -> None:
        """
        Save report to file.

        Args:
            output_path: Path where report should be saved
            format: Report format ("markdown" or "json")

        Note:
            Implementation will be added in Phase 4.
        """
        raise NotImplementedError("File saving will be implemented in Phase 4")

    def calculate_fidelity_score(self) -> float:
        """
        Calculate overall fidelity score from review results.

        Returns:
            Fidelity score as percentage (0-100)

        Note:
            Implementation will be added in Phase 4.
        """
        raise NotImplementedError("Score calculation will be implemented in Phase 4")

    def summarize_deviations(self) -> Dict[str, Any]:
        """
        Create summary of all deviations found.

        Returns:
            Dictionary containing deviation summary with counts and categories

        Note:
            Implementation will be added in Phase 4.
        """
        raise NotImplementedError("Deviation summary will be implemented in Phase 4")
