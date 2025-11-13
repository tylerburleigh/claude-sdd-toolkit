"""SDD Plan Review - Multi-model specification review tools."""

__version__ = "1.0.0"

from claude_skills.common.ai_tools import check_tool_available
from claude_skills.sdd_plan_review.reviewer import (
    review_with_tools,
)
from claude_skills.sdd_plan_review.prompts import (
    generate_review_prompt,
)
from claude_skills.sdd_plan_review.synthesis import (
    parse_response,
    build_consensus,
)
from claude_skills.sdd_plan_review.reporting import (
    generate_markdown_report,
    generate_json_report,
)

__all__ = [
    "check_tool_available",
    "review_with_tools",
    "generate_review_prompt",
    "parse_response",
    "build_consensus",
    "generate_markdown_report",
    "generate_json_report",
]
