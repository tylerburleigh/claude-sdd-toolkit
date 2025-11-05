"""
Fidelity Review Report Generation Module

Generates structured reports from fidelity review results.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json


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
