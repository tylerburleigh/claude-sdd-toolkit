#!/usr/bin/env python3
"""
Comprehensive report generation for spec reviews.

Generates markdown and JSON reports from multi-model consensus data.
"""

from datetime import datetime, timezone
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
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "models_consulted": consensus["models"],
        "num_models": consensus["num_models"],
        # Category-based feedback fields
        "consensus_level": consensus.get("consensus_level"),
        "critical_blockers": consensus.get("critical_blockers", []),
        "major_suggestions": consensus.get("major_suggestions", []),
        "questions": consensus.get("questions", []),
        "design_strengths": consensus.get("design_strengths", []),
        "agreements": consensus.get("agreements", []),
        "disagreements": consensus.get("disagreements", []),
        "synthesis_notes": consensus.get("synthesis_notes", []),
    }
