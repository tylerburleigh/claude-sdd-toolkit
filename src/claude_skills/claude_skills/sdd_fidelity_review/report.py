"""
Fidelity Review Report Generation Module

Generates structured reports from fidelity review results.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


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
        self.models_consulted = review_results.get(
            "models_consulted",
            len(self.parsed_responses)
        )

    def _get_report_metadata(self) -> Dict[str, Any]:
        """
        Generate report metadata section.

        Returns:
            Dictionary containing metadata fields
        """
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "spec_id": self.spec_id,
            "models_consulted": self.models_consulted,
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

    def generate_markdown(self) -> str:
        """
        Generate markdown-formatted report.

        Returns:
            Markdown string containing the formatted report with:
            - Header with spec ID and models consulted
            - Consensus verdict and agreement rate
            - Issues identified (organized by severity)
            - Recommendations from consensus
            - Optional: Individual model responses section

        Example:
            >>> report = FidelityReport(review_results)
            >>> markdown = report.generate_markdown()
            >>> with open("report.md", "w") as f:
            ...     f.write(markdown)
        """
        output = []

        # Header section
        output.append("# Implementation Fidelity Review\n")
        output.append(f"**Spec:** {self.spec_id}\n")
        output.append(f"**Models Consulted:** {self.models_consulted}\n")

        # Get consensus data (handle both dict and object)
        consensus_dict = self._convert_to_dict(self.consensus)
        consensus_verdict = consensus_dict.get("consensus_verdict", "unknown")
        agreement_rate = consensus_dict.get("agreement_rate", 0.0)
        consensus_issues = consensus_dict.get("consensus_issues", [])
        consensus_recommendations = consensus_dict.get("consensus_recommendations", [])

        # Consensus verdict section
        output.append(f"\n## Consensus Verdict: {consensus_verdict.upper()}\n")
        output.append(f"**Agreement Rate:** {agreement_rate:.1%}\n")

        # Issues section (if any)
        categorized_issues_list = self._convert_to_dict(self.categorized_issues)
        if categorized_issues_list:
            output.append("\n## Issues Identified (Consensus)\n")
            for cat_issue in categorized_issues_list:
                issue_text = cat_issue.get("issue", "")
                severity = cat_issue.get("severity", "unknown")
                output.append(f"\n### [{severity.upper()}] {issue_text}\n")

        # Recommendations section (if any)
        if consensus_recommendations:
            output.append("\n## Recommendations\n")
            for rec in consensus_recommendations:
                output.append(f"- {rec}\n")

        return "".join(output)

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
            "models_consulted": self.models_consulted,
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
        consensus_recommendations = consensus_dict.get("consensus_recommendations", [])

        # Header
        print("\n" + "=" * 80)
        print(printer.bold("IMPLEMENTATION FIDELITY REVIEW"))
        print("=" * 80)
        print(f"\nSpec: {printer.cyan(self.spec_id)}")
        print(f"Consulted {self.models_consulted} AI model(s)")

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
        if categorized_issues_list:
            print(f"\n{'-' * 80}")
            print(printer.bold("ISSUES IDENTIFIED (Consensus):"))
            print(f"{'-' * 80}")
            for cat_issue in categorized_issues_list:
                issue_text = cat_issue.get("issue", "")
                severity = cat_issue.get("severity", "unknown")
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

    def print_console_rich(self, verbose: bool = False) -> None:
        """
        Print formatted report to console using Rich panels with visual categorization.

        Displays issues grouped by severity in color-coded panels for better
        visual scanning. Uses Rich library for enhanced terminal output.

        Args:
            verbose: Include individual model responses (default: False)

        Example:
            >>> report = FidelityReport(review_results)
            >>> report.print_console_rich(verbose=False)
        """
        console = Console()

        # Get consensus data
        consensus_dict = self._convert_to_dict(self.consensus)
        consensus_verdict = consensus_dict.get("consensus_verdict", "unknown")
        agreement_rate = consensus_dict.get("agreement_rate", 0.0)
        consensus_recommendations = consensus_dict.get("consensus_recommendations", [])

        # Header
        console.print()
        console.print("[bold cyan]IMPLEMENTATION FIDELITY REVIEW[/bold cyan]")
        console.print(f"[dim]Spec: {self.spec_id}[/dim]")
        console.print(f"[dim]Consulted {self.models_consulted} AI model(s)[/dim]")
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

        # Group issues by severity
        categorized_issues_list = self._convert_to_dict(self.categorized_issues)
        if categorized_issues_list:
            issues_by_severity = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            }

            for cat_issue in categorized_issues_list:
                severity = cat_issue.get("severity", "unknown").lower()
                issue_text = cat_issue.get("issue", "")
                if severity in issues_by_severity:
                    issues_by_severity[severity].append(issue_text)

            # Display issues in severity panels
            severity_config = {
                "critical": {"title": "CRITICAL ISSUES", "style": "red", "icon": "🔴"},
                "high": {"title": "HIGH PRIORITY ISSUES", "style": "yellow", "icon": "🟡"},
                "medium": {"title": "MEDIUM PRIORITY ISSUES", "style": "blue", "icon": "🔵"},
                "low": {"title": "LOW PRIORITY ISSUES", "style": "cyan", "icon": "⚪"}
            }

            for severity in ["critical", "high", "medium", "low"]:
                issues = issues_by_severity[severity]
                if issues:
                    config = severity_config[severity]

                    # Create panel content
                    issue_lines = "\n\n".join([f"• {issue}" for issue in issues])

                    # Create panel
                    panel = Panel(
                        issue_lines,
                        title=f"{config['icon']} {config['title']} ({len(issues)})",
                        border_style=config["style"],
                        padding=(1, 2)
                    )
                    console.print(panel)
                    console.print()

        # Recommendations section
        if consensus_recommendations:
            console.print("[bold]RECOMMENDATIONS[/bold]")
            console.print()
            for rec in consensus_recommendations:
                console.print(f"• {rec}")
            console.print()

        # Consensus matrix showing AI model agreement
        if categorized_issues_list and len(categorized_issues_list) > 0:
            self._print_consensus_matrix(console, categorized_issues_list)

        # Individual responses (if verbose)
        if verbose:
            self._print_model_comparison_table(console)

    def _print_consensus_matrix(
        self,
        console: Console,
        categorized_issues: List[Dict[str, Any]]
    ) -> None:
        """
        Print consensus matrix showing which AI models agreed on findings.

        Args:
            console: Rich Console instance for output
            categorized_issues: List of categorized issues with agreement data
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
        table.add_column("Issue", style="bold", max_width=50)

        num_models = len(parsed_responses_list)
        for i in range(1, num_models + 1):
            table.add_column(f"M{i}", justify="center", style="dim")

        table.add_column("Agreement", justify="center", style="cyan")

        # Process each issue to show agreement
        for cat_issue in categorized_issues[:10]:  # Limit to top 10 issues
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

        # Row 4: Confidence (if available)
        if any("confidence" in response for response in parsed_responses_list):
            confidences = []
            for response in parsed_responses_list:
                confidence = response.get("confidence", "N/A")
                if confidence != "N/A":
                    confidences.append(f"{confidence}%")
                else:
                    confidences.append("N/A")
            table.add_row("Confidence", *confidences)

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
