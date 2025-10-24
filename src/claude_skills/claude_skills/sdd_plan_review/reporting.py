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
    review_type: str
) -> str:
    """
    Generate comprehensive markdown review report.

    Args:
        consensus: Consensus data from synthesis
        spec_id: Specification ID
        spec_title: Specification title
        review_type: Type of review performed

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
    lines.append(f"**Models Consulted**: {consensus['num_models']} ({', '.join(consensus['models'])})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overall Recommendation
    recommendation = consensus.get("final_recommendation", "UNKNOWN")
    rec_emoji = {"APPROVE": "✅", "REVISE": "⚠️", "REJECT": "❌"}.get(recommendation, "❓")

    lines.append(f"## {rec_emoji} Overall Recommendation: **{recommendation}**")
    lines.append("")
    lines.append(_get_recommendation_summary(consensus, recommendation))
    lines.append("")
    lines.append(f"**Consensus Level**: {consensus['consensus_level'].replace('_', ' ').title()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Scores Summary
    lines.append("## 📊 Scores Summary")
    lines.append("")
    if consensus.get("overall_score"):
        lines.append(f"**Overall Score**: {consensus['overall_score']}/10")
        lines.append(f"- Average: {consensus['overall_score_avg']}/10")
        lines.append(f"- Median: {consensus['overall_score_median']}/10")
        lines.append("")

    # Dimension scores table
    if consensus.get("dimension_scores"):
        lines.append("| Dimension        | Score | Range | Assessment |")
        lines.append("|------------------|-------|-------|------------|")

        dim_order = ["completeness", "clarity", "feasibility", "architecture", "risk_management", "verification"]
        for dim in dim_order:
            if dim in consensus["dimension_scores"]:
                scores = consensus["dimension_scores"][dim]
                avg = scores["avg"]
                score_range = f"{scores['min']}-{scores['max']}"
                assessment = _get_score_assessment(avg)

                dim_display = dim.replace("_", " ").title()
                lines.append(f"| {dim_display:16} | {avg}/10 | {score_range} | {assessment} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Strengths
    if consensus.get("all_strengths"):
        lines.append("## ✅ Strengths")
        lines.append("")
        for strength in consensus["all_strengths"][:10]:  # Top 10
            lines.append(f"- {strength}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Issues Found
    if consensus.get("all_issues"):
        lines.append("## 🚨 Issues Found")
        lines.append("")

        # Group by severity
        by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
        }
        for issue in consensus["all_issues"]:
            severity = issue.get("severity", "MEDIUM")
            by_severity[severity].append(issue)

        # Critical issues
        if by_severity["CRITICAL"]:
            lines.append("### 🔴 Critical Issues (Must Fix)")
            lines.append("")
            for i, issue in enumerate(by_severity["CRITICAL"], 1):
                lines.extend(_format_issue(i, issue))
            lines.append("")

        # High priority
        if by_severity["HIGH"]:
            lines.append("### 🟠 High Priority Issues (Should Fix)")
            lines.append("")
            for i, issue in enumerate(by_severity["HIGH"], 1):
                lines.extend(_format_issue(i, issue))
            lines.append("")

        # Medium priority
        if by_severity["MEDIUM"]:
            lines.append("### 🟡 Medium Priority Issues")
            lines.append("")
            # Only show first 5 medium issues
            for i, issue in enumerate(by_severity["MEDIUM"][:5], 1):
                lines.extend(_format_issue(i, issue, brief=True))
            if len(by_severity["MEDIUM"]) > 5:
                lines.append(f"*...and {len(by_severity['MEDIUM']) - 5} more medium priority issues*")
            lines.append("")

        # Low priority (summarize)
        if by_severity["LOW"]:
            lines.append(f"### 🟢 Low Priority Issues ({len(by_severity['LOW'])} total)")
            lines.append("")
            lines.append("*(Minor improvements and enhancements)*")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Recommendations
    if consensus.get("all_recommendations"):
        lines.append("## 💡 Recommendations")
        lines.append("")
        for i, rec in enumerate(consensus["all_recommendations"][:10], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Agreements & Disagreements
    if consensus.get("agreements") or consensus.get("disagreements"):
        lines.append("## 🤝 Consensus Analysis")
        lines.append("")

        if consensus.get("agreements"):
            lines.append("### Points of Agreement")
            lines.append("")
            for agreement in consensus["agreements"]:
                lines.append(f"- ✓ {agreement}")
            lines.append("")

        if consensus.get("disagreements"):
            lines.append("### ⚠️ Points of Disagreement")
            lines.append("")
            for disagreement in consensus["disagreements"]:
                lines.append(f"**{disagreement['topic']}**:")
                lines.append("")
                if isinstance(disagreement.get("positions"), dict):
                    for model, position in disagreement["positions"].items():
                        lines.append(f"- {model}: {position}")
                lines.append("")
                if disagreement.get("description"):
                    lines.append(f"*{disagreement['description']}*")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Model-by-Model Summary
    lines.append("## 📝 Model-by-Model Summary")
    lines.append("")
    # This would include individual model breakdowns
    # For now, just show models consulted
    for model in consensus["models"]:
        lines.append(f"### {model}")
        lines.append("")
        lines.append("*(Individual model details would appear here)*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Action Items
    lines.append("## 📋 Action Items")
    lines.append("")

    if recommendation == "APPROVE":
        lines.append("**To Proceed**:")
        lines.append("- [ ] Address any critical/high issues identified")
        lines.append("- [ ] Begin implementation with `sdd next-task`")
    elif recommendation == "REVISE":
        critical_count = len(by_severity.get("CRITICAL", []))
        high_count = len(by_severity.get("HIGH", []))

        lines.append("**To Approve Spec**:")
        if critical_count > 0:
            lines.append(f"- [ ] Fix {critical_count} critical issue(s)")
        if high_count > 0:
            lines.append(f"- [ ] Address {high_count} high priority issue(s)")
        lines.append("- [ ] Update spec file")
        lines.append("- [ ] Re-review (optional: `sdd review --type quick`)")
    else:  # REJECT
        lines.append("**Recommended Actions**:")
        lines.append("- [ ] Review fundamental design decisions")
        lines.append("- [ ] Consider alternative approaches")
        lines.append("- [ ] Consult with team/stakeholders")
        lines.append("- [ ] Create new spec addressing core issues")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Next Steps
    lines.append("## 🎯 Next Steps")
    lines.append("")
    lines.append("1. Review this report with your team")
    lines.append("2. Address critical and high priority issues")
    lines.append("3. Update the spec file")
    if recommendation != "APPROVE":
        lines.append("4. Consider re-review after changes")
    lines.append(f"{4 if recommendation != 'APPROVE' else '4'}. Proceed with implementation when ready")
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
