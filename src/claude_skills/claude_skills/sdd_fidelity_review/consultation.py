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

# Import cache modules with fallback
try:
    from claude_skills.common.cache import CacheManager, generate_fidelity_review_key
    from claude_skills.common.config import is_cache_enabled
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FidelityVerdict(Enum):
    """Overall fidelity verdict from AI review."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """Severity level for identified issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
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
    require_all_success: bool = False,
    cache_key_params: Optional[Dict[str, Any]] = None,
    use_cache: Optional[bool] = None
) -> List[ToolResponse]:
    """
    Consult multiple AI tools in parallel for fidelity review.

    Wrapper around execute_tools_parallel() with fidelity-review defaults,
    comprehensive error handling, and optional caching support.

    Args:
        prompt: The review prompt to send to all AI tools
        tools: List of tools to consult (gemini, codex, cursor-agent).
               If None, uses all available tools.
        model: Model to request (optional, tool-specific)
        timeout: Timeout in seconds per tool (default: 120)
        require_all_success: If True, raise exception if any tool fails
        cache_key_params: Parameters for cache key generation (spec_id, scope, target, file_paths)
        use_cache: Enable caching (overrides config, defaults to config setting)

    Returns:
        List of ToolResponse objects, one per tool

    Raises:
        NoToolsAvailableError: If no AI tools are available
        ConsultationError: If require_all_success=True and any tool fails

    Example:
        >>> responses = consult_multiple_ai_on_fidelity(
        ...     prompt="Review this implementation...",
        ...     tools=["gemini", "codex"],
        ...     cache_key_params={"spec_id": "my-spec-001", "scope": "phase", "target": "phase-1"}
        ... )
        >>> for response in responses:
        ...     print(f"{response.tool}: {response.status.value}")
    """
    # Check cache if enabled and cache_key_params provided
    cache_enabled = use_cache if use_cache is not None else (_CACHE_AVAILABLE and is_cache_enabled())
    cached_responses = None

    if cache_enabled and cache_key_params and _CACHE_AVAILABLE:
        try:
            cache = CacheManager()
            cache_key = generate_fidelity_review_key(
                spec_id=cache_key_params.get("spec_id", ""),
                scope=cache_key_params.get("scope", ""),
                target=cache_key_params.get("target", ""),
                file_paths=cache_key_params.get("file_paths"),
                model=model
            )

            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info("Cache hit: Using cached AI consultation results")
                # Reconstruct ToolResponse objects from cached data
                cached_responses = []
                for resp_data in cached_data:
                    cached_responses.append(ToolResponse(
                        tool=resp_data["tool"],
                        status=ToolStatus(resp_data["status"]),
                        output=resp_data["output"],
                        error=resp_data.get("error"),
                        exit_code=resp_data.get("exit_code"),
                        model=resp_data.get("model"),
                        metadata=resp_data.get("metadata", {})
                    ))
                return cached_responses
            else:
                logger.debug("Cache miss: Will consult AI tools and cache results")
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}. Proceeding with AI consultation.")

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
        # Convert single model string to models dict if provided
        models_dict = {tool: model for tool in available_tools} if model else None
        responses = execute_tools_parallel(
            tools=available_tools,
            prompt=prompt,
            models=models_dict,
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
    # Handle both string input and ToolResponse objects
    if isinstance(response, str):
        output = response.strip()
        success = True
        error = None
    else:
        output = response.output.strip() if response.output else ""
        success = response.success
        error = response.error

    # Initialize with defaults
    verdict = FidelityVerdict.UNKNOWN
    issues = []
    recommendations = []
    summary = ""
    confidence = None

    # If response failed, return early with UNKNOWN verdict
    if not success:
        return ParsedReviewResponse(
            verdict=FidelityVerdict.UNKNOWN,
            issues=[f"Tool execution failed: {error}"],
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
    # But exclude phrases like "no issues", "no problems", etc.
    if verdict == FidelityVerdict.PASS:
        output_lower = output.lower()
        # Check for negative patterns first (no issues, no problems, etc.)
        negative_patterns = [
            r'no\s+issue', r'no\s+problem', r'no\s+concern',
            r'no\s+warning', r'no\s+error', r'0\s+issue', r'0\s+problem'
        ]
        has_negatives = any(re.search(pattern, output_lower) for pattern in negative_patterns)

        # Only downgrade to PARTIAL if we find concerns AND don't have negatives
        if not has_negatives:
            concern_keywords = ['issue', 'problem', 'concern', 'warning', 'error']
            if any(keyword in output_lower for keyword in concern_keywords):
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


@dataclass
class ConsensusResult:
    """
    Consensus analysis across multiple AI review responses.

    Identifies issues and recommendations where multiple models agree,
    providing higher confidence in findings.

    Attributes:
        consensus_verdict: Majority verdict across all responses
        consensus_issues: Issues mentioned by 2+ models
        consensus_recommendations: Recommendations mentioned by 2+ models
        all_issues: All unique issues across all models
        all_recommendations: All unique recommendations across all models
        verdict_distribution: Count of each verdict type
        agreement_rate: Percentage of models agreeing on verdict (0.0-1.0)
        model_count: Total number of models consulted
    """
    consensus_verdict: FidelityVerdict
    consensus_issues: List[str] = field(default_factory=list)
    consensus_recommendations: List[str] = field(default_factory=list)
    all_issues: List[str] = field(default_factory=list)
    all_recommendations: List[str] = field(default_factory=list)
    verdict_distribution: Dict[str, int] = field(default_factory=dict)
    agreement_rate: float = 0.0
    model_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "consensus_verdict": self.consensus_verdict.value,
            "consensus_issues": self.consensus_issues,
            "consensus_recommendations": self.consensus_recommendations,
            "all_issues": self.all_issues,
            "all_recommendations": self.all_recommendations,
            "verdict_distribution": self.verdict_distribution,
            "agreement_rate": self.agreement_rate,
            "model_count": self.model_count
        }


def detect_consensus(
    parsed_responses: List[ParsedReviewResponse],
    min_agreement: int = 2,
    similarity_threshold: float = 0.7
) -> ConsensusResult:
    """
    Detect consensus across multiple AI review responses.

    Identifies issues and recommendations where multiple models agree,
    providing higher confidence findings.

    Args:
        parsed_responses: List of ParsedReviewResponse objects
        min_agreement: Minimum number of models that must agree (default: 2)
        similarity_threshold: Similarity threshold for fuzzy matching (0.0-1.0)
                            Not implemented in v1, uses exact matching

    Returns:
        ConsensusResult with consensus analysis

    Algorithm:
        1. Count verdict distribution and find majority verdict
        2. Collect all issues/recommendations across models
        3. Identify items mentioned by >= min_agreement models
        4. Calculate agreement rate for verdict

    Example:
        >>> parsed = parse_multiple_responses(responses)
        >>> consensus = detect_consensus(parsed, min_agreement=2)
        >>> print(f"Consensus: {consensus.consensus_verdict.value}")
        >>> print(f"Agreement: {consensus.agreement_rate:.1%}")
        >>> for issue in consensus.consensus_issues:
        ...     print(f"- {issue}")
    """
    if not parsed_responses:
        return ConsensusResult(
            consensus_verdict=FidelityVerdict.UNKNOWN,
            model_count=0
        )

    model_count = len(parsed_responses)

    # 1. Count verdict distribution
    verdict_counts: Dict[FidelityVerdict, int] = {}
    for response in parsed_responses:
        verdict_counts[response.verdict] = verdict_counts.get(response.verdict, 0) + 1

    # Find majority verdict
    consensus_verdict = FidelityVerdict.UNKNOWN
    max_count = 0
    for verdict, count in verdict_counts.items():
        if count > max_count:
            max_count = count
            consensus_verdict = verdict

    # Calculate agreement rate (percentage agreeing on consensus verdict)
    agreement_rate = max_count / model_count if model_count > 0 else 0.0

    # Convert to string keys for JSON serialization
    verdict_distribution = {v.value: c for v, c in verdict_counts.items()}

    # 2. Collect all issues and count occurrences
    issue_counts: Dict[str, int] = {}
    for response in parsed_responses:
        for issue in response.issues:
            # Normalize: lowercase and strip whitespace
            normalized_issue = issue.lower().strip()
            issue_counts[normalized_issue] = issue_counts.get(normalized_issue, 0) + 1

    # 3. Identify consensus issues (mentioned by >= min_agreement models)
    consensus_issues = []
    all_issues = []
    for issue, count in issue_counts.items():
        if count >= min_agreement:
            consensus_issues.append(issue)
        all_issues.append(issue)

    # 4. Collect all recommendations and count occurrences
    rec_counts: Dict[str, int] = {}
    for response in parsed_responses:
        for rec in response.recommendations:
            # Normalize: lowercase and strip whitespace
            normalized_rec = rec.lower().strip()
            rec_counts[normalized_rec] = rec_counts.get(normalized_rec, 0) + 1

    # 5. Identify consensus recommendations (mentioned by >= min_agreement models)
    consensus_recommendations = []
    all_recommendations = []
    for rec, count in rec_counts.items():
        if count >= min_agreement:
            consensus_recommendations.append(rec)
        all_recommendations.append(rec)

    return ConsensusResult(
        consensus_verdict=consensus_verdict,
        consensus_issues=consensus_issues,
        consensus_recommendations=consensus_recommendations,
        all_issues=all_issues,
        all_recommendations=all_recommendations,
        verdict_distribution=verdict_distribution,
        agreement_rate=agreement_rate,
        model_count=model_count
    )


@dataclass
class CategorizedIssue:
    """
    Issue with assigned severity category.

    Attributes:
        issue: The issue description
        severity: Assigned severity level
        keywords_matched: Keywords that triggered this severity
    """
    issue: str
    severity: IssueSeverity
    keywords_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issue": self.issue,
            "severity": self.severity.value,
            "keywords_matched": self.keywords_matched
        }


def categorize_issue_severity(issue: str) -> CategorizedIssue:
    """
    Categorize issue severity based on keywords and patterns.

    Uses keyword matching to assign severity levels:
    - CRITICAL: Security vulnerabilities, data loss, crashes
    - HIGH: Incorrect behavior, spec violations, broken functionality
    - MEDIUM: Performance issues, missing tests, code quality
    - LOW: Style issues, documentation, minor improvements

    Args:
        issue: Issue description text

    Returns:
        CategorizedIssue with assigned severity

    Example:
        >>> issue = "SQL injection vulnerability in login form"
        >>> categorized = categorize_issue_severity(issue)
        >>> categorized.severity
        <IssueSeverity.CRITICAL: 'critical'>
        >>> categorized.keywords_matched
        ['sql injection', 'vulnerability']
    """
    issue_lower = issue.lower()

    # CRITICAL severity keywords
    critical_keywords = [
        'security', 'vulnerability', 'injection', 'xss', 'csrf',
        'authentication bypass', 'unauthorized access', 'data loss',
        'crash', 'segfault', 'memory leak', 'remote code execution',
        'privilege escalation', 'buffer overflow'
    ]

    # HIGH severity keywords
    high_keywords = [
        'incorrect', 'wrong', 'broken', 'fails', 'failure',
        'spec violation', 'requirement not met', 'does not match',
        'missing required', 'critical bug', 'data corruption',
        'logic error', 'incorrect behavior'
    ]

    # MEDIUM severity keywords
    medium_keywords = [
        'performance', 'slow', 'inefficient', 'optimization',
        'missing test', 'no tests', 'untested', 'test coverage',
        'code quality', 'maintainability', 'complexity',
        'duplication', 'refactor', 'improvement needed'
    ]

    # LOW severity keywords
    low_keywords = [
        'style', 'formatting', 'naming', 'documentation',
        'comment', 'typo', 'whitespace', 'minor',
        'suggestion', 'consider', 'could be better'
    ]

    # Check keywords in order of severity (highest first)
    matched_keywords = []

    for keyword in critical_keywords:
        if keyword in issue_lower:
            matched_keywords.append(keyword)
    if matched_keywords:
        return CategorizedIssue(
            issue=issue,
            severity=IssueSeverity.CRITICAL,
            keywords_matched=matched_keywords
        )

    for keyword in high_keywords:
        if keyword in issue_lower:
            matched_keywords.append(keyword)
    if matched_keywords:
        return CategorizedIssue(
            issue=issue,
            severity=IssueSeverity.HIGH,
            keywords_matched=matched_keywords
        )

    for keyword in medium_keywords:
        if keyword in issue_lower:
            matched_keywords.append(keyword)
    if matched_keywords:
        return CategorizedIssue(
            issue=issue,
            severity=IssueSeverity.MEDIUM,
            keywords_matched=matched_keywords
        )

    for keyword in low_keywords:
        if keyword in issue_lower:
            matched_keywords.append(keyword)
    if matched_keywords:
        return CategorizedIssue(
            issue=issue,
            severity=IssueSeverity.LOW,
            keywords_matched=matched_keywords
        )

    # Default to MEDIUM if no keywords matched
    return CategorizedIssue(
        issue=issue,
        severity=IssueSeverity.MEDIUM,
        keywords_matched=[]
    )


def categorize_issues(issues: List[str]) -> List[CategorizedIssue]:
    """
    Categorize severity for multiple issues.

    Convenience function to categorize a list of issues.

    Args:
        issues: List of issue descriptions

    Returns:
        List of CategorizedIssue objects, sorted by severity (critical first)

    Example:
        >>> issues = [
        ...     "SQL injection in login",
        ...     "Missing tests for auth module",
        ...     "Typo in README"
        ... ]
        >>> categorized = categorize_issues(issues)
        >>> for cat in categorized:
        ...     print(f"{cat.severity.value}: {cat.issue}")
        critical: SQL injection in login
        medium: Missing tests for auth module
        low: Typo in README
    """
    categorized = [categorize_issue_severity(issue) for issue in issues]

    # Sort by severity (critical -> high -> medium -> low -> unknown)
    severity_order = {
        IssueSeverity.CRITICAL: 0,
        IssueSeverity.HIGH: 1,
        IssueSeverity.MEDIUM: 2,
        IssueSeverity.LOW: 3,
        IssueSeverity.UNKNOWN: 4
    }

    categorized.sort(key=lambda x: severity_order.get(x.severity, 99))

    return categorized
