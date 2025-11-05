"""
AI Consultation Wrapper for Fidelity Review

Lightweight wrapper around common/ai_tools.py specifically tailored for
implementation fidelity review use cases. Provides simplified API with
fidelity-review-specific defaults and error handling.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

from claude_skills.common.ai_tools import (
    ToolResponse,
    ToolStatus,
    execute_tool,
    execute_tools_parallel,
    detect_available_tools,
    check_tool_available
)

logger = logging.getLogger(__name__)


class FidelityVerdict(Enum):
    """Overall fidelity verdict from AI review."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class ParsedReviewResponse:
    """
    Structured representation of AI review response.

    Extracted from free-form AI tool output to provide
    structured access to review findings.

    Attributes:
        verdict: Overall pass/fail/partial verdict
        issues: List of identified issues
        recommendations: List of suggested improvements
        summary: Brief summary of findings
        raw_response: Original AI response text
        confidence: Confidence level if extractable (0.0-1.0)
    """
    verdict: FidelityVerdict
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "verdict": self.verdict.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "summary": self.summary,
            "raw_response": self.raw_response,
            "confidence": self.confidence
        }


class ConsultationError(Exception):
    """Base exception for consultation errors."""
    pass


class NoToolsAvailableError(ConsultationError):
    """Raised when no AI tools are available for consultation."""
    pass


class ConsultationTimeoutError(ConsultationError):
    """Raised when consultation times out."""
    pass


def consult_ai_on_fidelity(
    prompt: str,
    tool: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 120
) -> ToolResponse:
    """
    Consult an AI tool for implementation fidelity review.

    Simplified wrapper around execute_tool() with fidelity-review defaults
    and comprehensive error handling.

    Args:
        prompt: The review prompt to send to the AI tool
        tool: Specific tool to use (gemini, codex, cursor-agent).
              If None, uses first available tool.
        model: Model to request (optional, tool-specific)
        timeout: Timeout in seconds (default: 120)

    Returns:
        ToolResponse object with consultation results

    Raises:
        NoToolsAvailableError: If no AI tools are available
        ConsultationTimeoutError: If consultation times out
        ConsultationError: For other consultation failures

    Example:
        >>> response = consult_ai_on_fidelity(
        ...     prompt="Review this implementation...",
        ...     tool="gemini"
        ... )
        >>> if response.success:
        ...     print(response.output)
    """
    try:
        # If no tool specified, detect available tools
        if tool is None:
            available_tools = detect_available_tools()
            if not available_tools:
                raise NoToolsAvailableError(
                    "No AI consultation tools available. "
                    "Please install: gemini, codex, or cursor-agent"
                )
            tool = available_tools[0]
            logger.info(f"Using detected tool: {tool}")

        # Check if specified tool is available
        if not check_tool_available(tool):
            raise NoToolsAvailableError(
                f"Tool '{tool}' not found. "
                "Please install it or choose a different tool."
            )

        # Execute consultation
        response = execute_tool(
            tool=tool,
            prompt=prompt,
            model=model,
            timeout=timeout
        )

        # Handle timeout status
        if response.status == ToolStatus.TIMEOUT:
            raise ConsultationTimeoutError(
                f"Consultation with {tool} timed out after {timeout}s"
            )

        # Log warnings for non-success but non-timeout statuses
        if not response.success:
            logger.warning(
                f"Consultation with {tool} failed: {response.status.value} - {response.error}"
            )

        return response

    except (NoToolsAvailableError, ConsultationTimeoutError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        logger.error(f"Unexpected error during consultation: {e}")
        raise ConsultationError(f"Consultation failed: {e}") from e


def consult_multiple_ai_on_fidelity(
    prompt: str,
    tools: Optional[List[str]] = None,
    model: Optional[str] = None,
    timeout: int = 120,
    require_all_success: bool = False
) -> List[ToolResponse]:
    """
    Consult multiple AI tools in parallel for fidelity review.

    Wrapper around execute_tools_parallel() with fidelity-review defaults
    and comprehensive error handling.

    Args:
        prompt: The review prompt to send to all AI tools
        tools: List of tools to consult (gemini, codex, cursor-agent).
               If None, uses all available tools.
        model: Model to request (optional, tool-specific)
        timeout: Timeout in seconds per tool (default: 120)
        require_all_success: If True, raise exception if any tool fails

    Returns:
        List of ToolResponse objects, one per tool

    Raises:
        NoToolsAvailableError: If no AI tools are available
        ConsultationError: If require_all_success=True and any tool fails

    Example:
        >>> responses = consult_multiple_ai_on_fidelity(
        ...     prompt="Review this implementation...",
        ...     tools=["gemini", "codex"]
        ... )
        >>> for response in responses:
        ...     print(f"{response.tool}: {response.status.value}")
    """
    try:
        # If no tools specified, detect all available tools
        if tools is None:
            tools = detect_available_tools()
            if not tools:
                raise NoToolsAvailableError(
                    "No AI consultation tools available. "
                    "Please install: gemini, codex, or cursor-agent"
                )
            logger.info(f"Using detected tools: {', '.join(tools)}")

        # Filter to only available tools
        available_tools = [t for t in tools if check_tool_available(t)]
        if not available_tools:
            raise NoToolsAvailableError(
                f"None of the specified tools are available: {', '.join(tools)}"
            )

        if len(available_tools) < len(tools):
            unavailable = set(tools) - set(available_tools)
            logger.warning(f"Some tools unavailable: {', '.join(unavailable)}")

        # Execute consultations in parallel
        responses = execute_tools_parallel(
            tools=available_tools,
            prompt=prompt,
            model=model,
            timeout=timeout
        )

        # Check for failures if required
        if require_all_success:
            failures = [r for r in responses if not r.success]
            if failures:
                failed_tools = [r.tool for r in failures]
                raise ConsultationError(
                    f"Consultation failed for tools: {', '.join(failed_tools)}"
                )

        return responses

    except (NoToolsAvailableError, ConsultationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        logger.error(f"Unexpected error during parallel consultation: {e}")
        raise ConsultationError(f"Parallel consultation failed: {e}") from e


def get_consultation_summary(responses: List[ToolResponse]) -> Dict[str, Any]:
    """
    Generate summary statistics for multiple consultation responses.

    Useful for understanding overall consultation health and results.

    Args:
        responses: List of ToolResponse objects

    Returns:
        Dictionary with summary statistics:
        {
            "total": int,
            "successful": int,
            "failed": int,
            "timed_out": int,
            "total_duration": float,
            "average_duration": float,
            "tools_used": List[str],
            "success_rate": float
        }

    Example:
        >>> summary = get_consultation_summary(responses)
        >>> print(f"Success rate: {summary['success_rate']:.1%}")
    """
    total = len(responses)
    if total == 0:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "timed_out": 0,
            "total_duration": 0.0,
            "average_duration": 0.0,
            "tools_used": [],
            "success_rate": 0.0
        }

    successful = sum(1 for r in responses if r.success)
    failed = sum(1 for r in responses if r.failed and r.status != ToolStatus.TIMEOUT)
    timed_out = sum(1 for r in responses if r.status == ToolStatus.TIMEOUT)
    total_duration = sum(r.duration for r in responses)
    average_duration = total_duration / total if total > 0 else 0.0
    tools_used = [r.tool for r in responses]
    success_rate = successful / total if total > 0 else 0.0

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "timed_out": timed_out,
        "total_duration": total_duration,
        "average_duration": average_duration,
        "tools_used": tools_used,
        "success_rate": success_rate
    }


def parse_review_response(response: ToolResponse) -> ParsedReviewResponse:
    """
    Parse AI tool response to extract structured review information.

    Extracts verdict, issues, recommendations from free-form AI response.
    Uses pattern matching and heuristics to identify key information.

    Args:
        response: ToolResponse from AI consultation

    Returns:
        ParsedReviewResponse with extracted information

    Example:
        >>> tool_response = consult_ai_on_fidelity(prompt)
        >>> parsed = parse_review_response(tool_response)
        >>> print(f"Verdict: {parsed.verdict.value}")
        >>> for issue in parsed.issues:
        ...     print(f"- {issue}")
    """
    output = response.output.strip()

    # Initialize with defaults
    verdict = FidelityVerdict.UNKNOWN
    issues = []
    recommendations = []
    summary = ""
    confidence = None

    # If response failed, return early with UNKNOWN verdict
    if not response.success:
        return ParsedReviewResponse(
            verdict=FidelityVerdict.UNKNOWN,
            issues=[f"Tool execution failed: {response.error}"],
            recommendations=[],
            summary="Unable to complete review due to tool failure",
            raw_response=output,
            confidence=0.0
        )

    # Extract verdict using pattern matching
    verdict_patterns = [
        (r'\b(PASS|PASSED|PASSES)\b', FidelityVerdict.PASS),
        (r'\b(FAIL|FAILED|FAILS|FAILURE)\b', FidelityVerdict.FAIL),
        (r'\b(PARTIAL|PARTIALLY)\b', FidelityVerdict.PARTIAL),
    ]

    for pattern, verdict_value in verdict_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            verdict = verdict_value
            break

    # Heuristic: If "PASS" appears but also mentions issues/concerns, mark as PARTIAL
    if verdict == FidelityVerdict.PASS:
        concern_keywords = ['issue', 'problem', 'concern', 'warning', 'error']
        if any(keyword in output.lower() for keyword in concern_keywords):
            verdict = FidelityVerdict.PARTIAL

    # Extract issues (look for common patterns)
    issue_patterns = [
        r'(?:Issue|Problem|Concern|Error)(?:s)?:\s*\n?[-•*]?\s*(.+?)(?:\n\n|\n[-•*]|$)',
        r'(?:Found|Identified)\s+(?:the following\s+)?(?:issue|problem)(?:s)?:\s*\n?(.+?)(?:\n\n|$)',
        r'[-•*]\s*Issue:\s*(.+?)(?:\n|$)',
    ]

    for pattern in issue_patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE | re.DOTALL)
        for match in matches:
            issue_text = match.group(1).strip()
            # Split on bullet points if multiple issues in one match
            sub_issues = re.split(r'\n[-•*]\s*', issue_text)
            issues.extend([i.strip() for i in sub_issues if i.strip()])

    # Extract recommendations (look for common patterns)
    rec_patterns = [
        r'(?:Recommendation|Suggest|Should)(?:s)?:\s*\n?[-•*]?\s*(.+?)(?:\n\n|\n[-•*]|$)',
        r'(?:I recommend|It is recommended|Consider)\s+(.+?)(?:\n|$)',
        r'[-•*]\s*Recommendation:\s*(.+?)(?:\n|$)',
    ]

    for pattern in rec_patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE | re.DOTALL)
        for match in matches:
            rec_text = match.group(1).strip()
            # Split on bullet points if multiple recommendations in one match
            sub_recs = re.split(r'\n[-•*]\s*', rec_text)
            recommendations.extend([r.strip() for r in sub_recs if r.strip()])

    # Extract summary (first paragraph or first 200 chars)
    summary_match = re.match(r'^(.+?)(?:\n\n|\n#|$)', output, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
        if len(summary) > 200:
            summary = summary[:197] + "..."
    else:
        summary = output[:200] + "..." if len(output) > 200 else output

    # Extract confidence if mentioned (0-100% or 0.0-1.0)
    confidence_match = re.search(
        r'(?:confidence|certainty):\s*(\d+(?:\.\d+)?)\s*%?',
        output,
        re.IGNORECASE
    )
    if confidence_match:
        conf_value = float(confidence_match.group(1))
        # Normalize to 0.0-1.0 range
        if conf_value > 1.0:
            confidence = conf_value / 100.0
        else:
            confidence = conf_value

    return ParsedReviewResponse(
        verdict=verdict,
        issues=issues,
        recommendations=recommendations,
        summary=summary,
        raw_response=output,
        confidence=confidence
    )


def parse_multiple_responses(
    responses: List[ToolResponse]
) -> List[ParsedReviewResponse]:
    """
    Parse multiple AI tool responses.

    Convenience function to parse a list of ToolResponse objects.

    Args:
        responses: List of ToolResponse objects

    Returns:
        List of ParsedReviewResponse objects

    Example:
        >>> responses = consult_multiple_ai_on_fidelity(prompt)
        >>> parsed_list = parse_multiple_responses(responses)
        >>> for parsed in parsed_list:
        ...     print(f"{parsed.verdict.value}: {len(parsed.issues)} issues")
    """
    return [parse_review_response(response) for response in responses]
