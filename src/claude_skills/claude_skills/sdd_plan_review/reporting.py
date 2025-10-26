#!/usr/bin/env python3
"""
Comprehensive report generation for spec reviews.

Generates markdown and JSON reports from multi-model consensus data.
"""

from datetime import datetime
from typing import Dict, Any, List


def generate_markdown_report(
    consensus: Dict[str, Any],
    spec_id: str,
    spec_title: str,
    review_type: str,
    parsed_responses: List[Dict[str, Any]] = None
) -> str:
    """
    Generate comprehensive markdown review report.

    With AI synthesis, the consensus already contains structured markdown.
    This function wraps it with header and model details.

    Args:
        consensus: Consensus data from AI synthesis
        spec_id: Specification ID
        spec_title: Specification title
        review_type: Type of review performed
        parsed_responses: Individual model responses (optional)

    Returns:
        Formatted markdown report
    """
    lines = []

    # Header
    lines.append(f"# Specification Review Report")
    lines.append("")
    lines.append(f"**Spec**: {spec_title} (`{spec_id}`)")
    lines.append(f"**Review Type**: {review_type.capitalize()}")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Models Consulted**: {consensus.get('num_models', 0)} ({', '.join(consensus.get('models', []))})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # AI Synthesis (this is the main content now)
    synthesis_text = consensus.get("synthesis_text", "")
    if synthesis_text:
        lines.append(synthesis_text)
    else:
        lines.append("## Error")
        lines.append("")
        lines.append("AI synthesis failed or produced no output.")
        lines.append("")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Model-by-Model Raw Reviews
    lines.append("## 📝 Individual Model Reviews")
    lines.append("")

    if parsed_responses:
        for model_data in parsed_responses:
            model_name = model_data.get("tool", "Unknown Model")
            raw_review = model_data.get("raw_review", "")

            lines.append(f"### {model_name}")
            lines.append("")
            if raw_review:
                lines.append(raw_review)
            else:
                lines.append("*(No response)*")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def _get_recommendation_summary(consensus: Dict[str, Any], recommendation: str) -> str:
    """Get summary text for recommendation."""
    score = consensus.get("overall_score", 0)

    if recommendation == "APPROVE":
        return (
            f"This specification scores {score}/10 and is ready for implementation. "
            "Address any remaining issues during development."
        )
    elif recommendation == "REVISE":
        return (
            f"This specification scores {score}/10 and needs revision before implementation. "
            "Focus on critical and high-priority issues identified below."
        )
    else:  # REJECT
        return (
            f"This specification scores {score}/10 and has fundamental issues requiring redesign. "
            "Consider alternative approaches before proceeding."
        )


def _get_score_assessment(score: float) -> str:
    """Get qualitative assessment for a score."""
    if score >= 9:
        return "Excellent"
    elif score >= 7:
        return "Good"
    elif score >= 5:
        return "Needs Work"
    elif score >= 3:
        return "Poor"
    else:
        return "Critical"


def _format_issue(number: int, issue: Dict[str, Any], brief: bool = False) -> List[str]:
    """Format an issue for display."""
    lines = []

    flagged_by = ", ".join(issue.get("flagged_by", []))

    lines.append(f"#### {number}. {issue['title']}")
    lines.append(f"**Severity**: {issue['severity']} | **Flagged by**: {flagged_by}")
    lines.append("")

    if not brief:
        if issue.get("description"):
            lines.append(f"**Description**: {issue['description']}")
            lines.append("")

        if issue.get("impact"):
            lines.append(f"**Impact**: {issue['impact']}")
            lines.append("")

        if issue.get("recommendation"):
            lines.append(f"**Recommendation**: {issue['recommendation']}")
            lines.append("")

    return lines


def _format_model_summary(model_data: Dict[str, Any]) -> List[str]:
    """
    Format individual model response for display.

    Args:
        model_data: Normalized model response data

    Returns:
        List of formatted lines
    """
    lines = []

    # Check if response is completely empty
    has_content = (
        model_data.get("overall_score") is not None or
        model_data.get("dimensions") or
        model_data.get("issues") or
        model_data.get("strengths") or
        model_data.get("recommendations")
    )

    if not has_content:
        lines.append("**Response could not be parsed**")
        lines.append("")
        lines.append("The model's response did not contain structured feedback in the expected format.")
        lines.append("")
        return lines

    # Overall assessment
    if model_data.get("overall_score") is not None:
        lines.append(f"**Overall Score**: {model_data['overall_score']}/10")

    if model_data.get("recommendation"):
        rec_emoji = {"APPROVE": "✅", "REVISE": "⚠️", "REJECT": "❌"}.get(
            model_data["recommendation"], "❓"
        )
        lines.append(f"**Recommendation**: {rec_emoji} {model_data['recommendation']}")

    lines.append("")

    # Dimension scores
    if model_data.get("dimensions"):
        lines.append("**Dimension Scores**:")
        for dim_name, dim_data in model_data["dimensions"].items():
            score = dim_data.get("score", "N/A")
            dim_display = dim_name.replace("_", " ").title()
            lines.append(f"- {dim_display}: {score}/10")
            if dim_data.get("notes"):
                lines.append(f"  - *{dim_data['notes']}*")
        lines.append("")

    # Key issues
    if model_data.get("issues"):
        lines.append("**Key Issues Identified**:")
        # Show all issues sorted by severity
        sorted_issues = sorted(
            model_data["issues"],
            key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.get("severity", "MEDIUM"), 4)
        )
        for issue in sorted_issues:
            severity = issue.get("severity", "MEDIUM")
            title = issue.get("title", "Untitled")
            lines.append(f"- [{severity}] {title}")
        lines.append("")

    # Key strengths
    if model_data.get("strengths"):
        lines.append("**Strengths Noted**:")
        # Show all strengths
        for strength in model_data["strengths"]:
            lines.append(f"- {strength}")
        lines.append("")

    return lines


def generate_json_report(
    consensus: Dict[str, Any],
    spec_id: str,
    spec_title: str,
    review_type: str
) -> Dict[str, Any]:
    """
    Generate JSON format review report.

    Args:
        consensus: Consensus data
        spec_id: Specification ID
        spec_title: Specification title
        review_type: Review type

    Returns:
        JSON-serializable report dictionary
    """
    return {
        "spec_id": spec_id,
        "spec_title": spec_title,
        "review_type": review_type,
        "timestamp": datetime.now().isoformat(),
        "models_consulted": consensus["models"],
        "num_models": consensus["num_models"],
        "recommendation": consensus.get("final_recommendation"),
        "consensus_level": consensus.get("consensus_level"),
        "overall_score": consensus.get("overall_score"),
        "dimension_scores": consensus.get("dimension_scores", {}),
        "issues": consensus.get("all_issues", []),
        "strengths": consensus.get("all_strengths", []),
        "recommendations": consensus.get("all_recommendations", []),
        "agreements": consensus.get("agreements", []),
        "disagreements": consensus.get("disagreements", []),
    }
