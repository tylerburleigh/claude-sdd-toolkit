"""
AI Consultation Wrapper for Fidelity Review

Lightweight wrapper around common/ai_tools.py specifically tailored for
implementation fidelity review use cases. Provides simplified API with
fidelity-review-specific defaults and error handling.
"""

from typing import List, Optional, Dict, Any, Tuple, Set, Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import re
from copy import deepcopy

from claude_skills.common import ai_tools
from claude_skills.common.ai_tools import ToolResponse, ToolStatus
from claude_skills.common.progress import ProgressEmitter
from claude_skills.common import ai_config
from claude_skills.common.ai_config import ALL_SUPPORTED_TOOLS
from claude_skills.common import consultation_limits

# Import cache modules with fallback
try:
    from claude_skills.common.cache import CacheManager, generate_fidelity_review_key
    from claude_skills.common.config import is_cache_enabled
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

FIDELITY_SKILL_NAME = "sdd-fidelity-review"


def _summarize_models_map(models_map: Mapping[str, Optional[str]]) -> Optional[str]:
    """Convert a per-tool model map into a deterministic summary string."""
    if not models_map:
        return None
    summary_parts = [
        f"{tool}:{model if model is not None else 'none'}"
        for tool, model in models_map.items()
    ]
    return "|".join(summary_parts) if summary_parts else None


# Helper functions for config-driven behavior
def get_fidelity_review_timeout() -> int:
    """
    Get consultation timeout from config.

    Returns timeout in seconds from config file (defaults to 600).
    """
    return ai_config.get_timeout(FIDELITY_SKILL_NAME, 'consultation')


def get_enabled_fidelity_tools() -> Dict[str, Dict]:
    """
    Get enabled tools from config.

    Returns dictionary of tools where enabled: true in config.
    """
    return ai_config.get_enabled_tools(FIDELITY_SKILL_NAME)


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
        raw_response: Original AI response text when structured parsing fails
        structured_response: Parsed JSON payload when available
        provider: Tool/provider that produced the response
        model: Model identifier if provided by the tool
    """
    verdict: FidelityVerdict
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""
    raw_response: Optional[str] = None
    structured_response: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data: Dict[str, Any] = {
            "verdict": self.verdict.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "summary": self.summary,
        }
        if self.raw_response is not None:
            data["raw_response"] = self.raw_response
        if self.structured_response is not None:
            data["structured_response"] = self.structured_response
        if self.provider is not None:
            data["provider"] = self.provider
        if self.model is not None:
            data["model"] = self.model
        return data


class ConsultationError(Exception):
    """Base exception for consultation errors."""
    pass


class NoToolsAvailableError(ConsultationError):
    """Raised when no AI tools are available for consultation."""
    pass


class ConsultationTimeoutError(ConsultationError):
    """Raised when consultation times out."""
    pass


SECTION_HEADING_ISSUE_KEYWORDS = (
    "issue",
    "finding",
    "concern",
    "deviation",
    "blocker",
    "blocking",
    "risk",
    "problem",
    "failure",
)
SECTION_HEADING_RECOMMENDATION_KEYWORDS = (
    "recommendation",
    "suggestion",
    "next step",
    "action",
    "follow-up",
    "remediation",
    "mitigation",
    "todo",
    "fix",
)
ISSUE_KEYWORDS = (
    "issue",
    "problem",
    "concern",
    "bug",
    "error",
    "fail",
    "failure",
    "missing",
    "absent",
    "does not",
    "not met",
    "not satisfied",
    "deviation",
    "deviate",
    "deviates",
    "blocker",
    "blocking",
    "incomplete",
    "incorrect",
    "mismatch",
    "violation",
    "prevent",
    "broken",
    "lack",
    "lacking",
)
RECOMMENDATION_KEYWORDS = (
    "recommend",
    "should",
    "consider",
    "suggest",
    "ensure",
    "add",
    "implement",
    "address",
    "fix",
    "resolve",
    "mitigate",
    "need to",
    "must",
    "propose",
    "update",
    "restore",
    "provide",
)
ISSUE_PREFIXES = (
    "blocking",
    "critical",
    "major",
    "minor",
    "deviation",
    "issue",
    "concern",
    "failing",
    "fails",
    "failed",
    "missing",
    "broken",
)
RECOMMENDATION_PREFIXES = (
    "recommend",
    "recommendation",
    "suggest",
    "should",
    "must",
    "need to",
    "consider",
    "ensure",
    "action",
    "next step",
)
SHORT_RESPONSE_DENYLIST = {"yes", "no", "n/a", "none", "ok", "pass"}
LIST_ITEM_PATTERN = re.compile(r'^\s*(?:[-*•‣▪◦]|\d+[.)])\s+(.*)$')
HEADING_PATTERN = re.compile(r'^\s*(#{2,6})\s+(.+)$', re.MULTILINE)
NEGATIVE_STATUS_TOKENS = (
    "no",
    "not",
    "fail",
    "failed",
    "failure",
    "missing",
    "insufficient",
    "inadequate",
    "partial",
    "block",
    "blocked",
    "deviation",
    "deviates",
    "doesn't",
    "does not",
    "did not",
    "unable",
)
POSITIVE_STATUS_TOKENS = (
    "yes",
    "pass",
    "passes",
    "passed",
    "met",
    "complete",
    "completed",
    "sufficient",
    "adequate",
    "true",
    "aligned",
)


def _strip_markdown_emphasis(text: str) -> str:
    """Remove common markdown emphasis markers without altering content casing."""
    if not text:
        return ""
    cleaned = text.strip()
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    cleaned = re.sub(r'\[(.+?)\]\((.*?)\)', r'\1', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def _normalize_for_matching(text: str) -> str:
    """Normalize text for deduplication and fuzzy matching."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip().lower()


def _classify_heading(heading: Optional[str]) -> Optional[str]:
    """Classify section heading as issue or recommendation oriented."""
    if not heading:
        return None
    heading_lower = heading.lower()
    if any(keyword in heading_lower for keyword in SECTION_HEADING_ISSUE_KEYWORDS):
        return "issue"
    if any(keyword in heading_lower for keyword in SECTION_HEADING_RECOMMENDATION_KEYWORDS):
        return "recommendation"
    return None


def _split_sections_by_heading(text: str) -> List[Tuple[Optional[str], str]]:
    """
    Split text into sections using markdown headings.

    Returns list of (heading, section_text) pairs. Sections prior to the first
    heading are returned with heading=None.
    """
    if not text.strip():
        return []

    sections: List[Tuple[Optional[str], str]] = []
    matches = list(HEADING_PATTERN.finditer(text))

    if not matches:
        return [(None, text.strip())]

    first_start = matches[0].start()
    if first_start > 0:
        preamble = text[:first_start].strip()
        if preamble:
            sections.append((None, preamble))

    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[section_start:section_end].strip()
        sections.append((heading, section_text))

    return sections


def _extract_list_items(section_text: str) -> List[str]:
    """
    Extract bullet or numbered list items from section text.

    Preserves multi-line items by joining continuation lines with spaces.
    """
    if not section_text:
        return []

    items: List[str] = []
    current_parts: List[str] = []

    for line in section_text.splitlines():
        if not line.strip():
            if current_parts:
                items.append(" ".join(current_parts).strip())
                current_parts = []
            continue

        match = LIST_ITEM_PATTERN.match(line)
        if match:
            if current_parts:
                items.append(" ".join(current_parts).strip())
            current_parts = [match.group(1).strip()]
            continue

        if current_parts and line.startswith((" ", "\t")):
            current_parts.append(line.strip())
        elif current_parts:
            current_parts.append(line.strip())

    if current_parts:
        items.append(" ".join(current_parts).strip())

    return [item for item in items if item]


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    deduped: List[str] = []
    for item in items:
        normalized = _normalize_for_matching(item)
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(item)
    return deduped


def _strip_code_fences(text: str) -> str:
    """Remove Markdown code fences if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    newline_index = stripped.find("\n")
    if newline_index == -1:
        return stripped.strip("`").strip()

    content = stripped[newline_index + 1 :]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _load_json_from_text(text: str) -> Optional[Any]:
    """Attempt to parse JSON from the provided text or embedded code block."""
    candidate = _strip_code_fences(text)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Attempt to parse first JSON object in text
    start_obj = candidate.find("{")
    end_obj = candidate.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        try:
            return json.loads(candidate[start_obj:end_obj + 1])
        except json.JSONDecodeError:
            pass

    # Attempt to parse first JSON array
    start_array = candidate.find("[")
    end_array = candidate.rfind("]")
    if start_array != -1 and end_array != -1 and end_array > start_array:
        try:
            return json.loads(candidate[start_array:end_array + 1])
        except json.JSONDecodeError:
            pass

    return None


def _coerce_verdict(value: Optional[str]) -> Optional[FidelityVerdict]:
    """Convert a string verdict to the matching FidelityVerdict."""
    if not value or not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    mapping = {
        "pass": FidelityVerdict.PASS,
        "fail": FidelityVerdict.FAIL,
        "failed": FidelityVerdict.FAIL,
        "failure": FidelityVerdict.FAIL,
        "partial": FidelityVerdict.PARTIAL,
        "unknown": FidelityVerdict.UNKNOWN,
    }
    return mapping.get(normalized)


def _coerce_issue_entry(entry: Any) -> Optional[str]:
    """Normalize issue entries from structured JSON responses."""
    if isinstance(entry, str):
        return entry.strip() or None

    if isinstance(entry, dict):
        candidate_fields = ["description", "detail", "text", "summary", "issue"]
        text_value = None
        for field in candidate_fields:
            value = entry.get(field)
            if isinstance(value, str) and value.strip():
                text_value = value.strip()
                break
        if not text_value:
            return None

        severity = entry.get("severity")
        if isinstance(severity, str) and severity.strip():
            sev = severity.strip()
            if not text_value.lower().startswith(sev.lower()):
                text_value = f"{sev}: {text_value}"
        return text_value

    return None


def _coerce_recommendation_entry(entry: Any) -> Optional[str]:
    """Normalize recommendation entries from structured JSON responses."""
    if isinstance(entry, str):
        return entry.strip() or None

    if isinstance(entry, dict):
        candidate_fields = ["description", "detail", "text", "recommendation", "summary"]
        for field in candidate_fields:
            value = entry.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _score_keywords(text: str, keywords: tuple[str, ...]) -> int:
    """Count keyword matches within text for heuristic scoring."""
    return sum(1 for keyword in keywords if keyword in text)


def _is_negative_status(text: Optional[str]) -> bool:
    if not text or not isinstance(text, str):
        return False
    lowered = text.strip().lower()
    if any(token in lowered for token in NEGATIVE_STATUS_TOKENS):
        return True
    if any(token == lowered for token in POSITIVE_STATUS_TOKENS):
        return False
    return False


def _is_positive_status(text: Optional[str]) -> bool:
    if not text or not isinstance(text, str):
        return False
    lowered = text.strip().lower()
    return any(token == lowered for token in POSITIVE_STATUS_TOKENS)


def _extract_structured_json_insights(
    payload: Dict[str, Any],
    add_issue: Callable[[str], None],
    add_recommendation: Callable[[str], None],
) -> None:
    def _combine_message(label: str, answer: Optional[str], details: Optional[str]) -> str:
        parts = [label]
        if isinstance(answer, str) and answer.strip():
            parts.append(answer.strip())
        if isinstance(details, str) and details.strip():
            parts.append(details.strip())
        return ": ".join(parts) if len(parts) > 1 else parts[0]

    def _handle_section(label: str, section: Any, status_keys: Tuple[str, ...] = ("answer", "status", "met", "result")) -> None:
        if not isinstance(section, dict):
            return
        answer = None
        for key in status_keys:
            if key in section:
                candidate = section[key]
                if isinstance(candidate, str) and candidate.strip():
                    answer = candidate
                    break
        details = None
        for key in ("details", "comment", "note", "explanation", "reason"):
            if key in section and isinstance(section[key], str) and section[key].strip():
                details = section[key]
                break

        if answer and _is_positive_status(answer):
            return

        candidate_texts = []
        candidate_texts.append(_combine_message(label, answer, details))

        if answer and _is_negative_status(answer):
            add_issue(candidate_texts[-1])
        elif details and _is_negative_status(details):
            add_issue(candidate_texts[-1])

    _handle_section("Requirement alignment", payload.get("requirement_alignment"))
    _handle_section("Success criteria", payload.get("success_criteria"))
    _handle_section("Test coverage", payload.get("test_coverage"))
    _handle_section("Documentation", payload.get("documentation"))

    code_quality = payload.get("code_quality")
    if isinstance(code_quality, dict):
        issues_list = code_quality.get("issues")
        if isinstance(issues_list, list):
            for entry in issues_list:
                issue_text = _coerce_issue_entry(entry)
                if issue_text:
                    add_issue(issue_text)
        cq_details = code_quality.get("details")
        if isinstance(cq_details, str) and cq_details.strip() and _is_negative_status(cq_details):
            add_issue(f"Code quality: {cq_details.strip()}")

    deviations = payload.get("deviations")
    if isinstance(deviations, list):
        for entry in deviations:
            issue_text = _coerce_issue_entry(entry)
            if issue_text:
                add_issue(issue_text)

    follow_up_keys = ("next_steps", "actions", "follow_ups", "follow_up_actions", "remediations")
    for key in follow_up_keys:
        value = payload.get(key)
        if isinstance(value, list):
            for entry in value:
                rec_text = _coerce_recommendation_entry(entry)
                if rec_text:
                    add_recommendation(rec_text)
        elif isinstance(value, str) and value.strip():
            add_recommendation(value.strip())


def _classify_list_item(text: str, section_hint: Optional[str]) -> Optional[str]:
    """
    Classify list item as issue or recommendation using heuristics.

    Considers section headings, severity prefixes, and keyword presence while
    avoiding overly short benign responses.
    """
    normalized = _normalize_for_matching(text)
    if not normalized:
        return None
    if len(normalized.replace(" ", "")) < 6:
        return None
    if normalized in SHORT_RESPONSE_DENYLIST:
        return None

    section_type = section_hint
    issue_score = 0
    recommendation_score = 0

    if section_type == "issue":
        issue_score += 2
    elif section_type == "recommendation":
        recommendation_score += 2

    if any(normalized.startswith(prefix) for prefix in ISSUE_PREFIXES):
        issue_score += 2
    if any(normalized.startswith(prefix) for prefix in RECOMMENDATION_PREFIXES):
        recommendation_score += 2

    issue_score += _score_keywords(normalized, ISSUE_KEYWORDS)
    recommendation_score += _score_keywords(normalized, RECOMMENDATION_KEYWORDS)

    if issue_score == recommendation_score == 0:
        if section_type and len(normalized.split()) >= 5:
            return section_type
        return None

    if issue_score > recommendation_score:
        return "issue"
    if recommendation_score > issue_score:
        return "recommendation"

    return section_type or ("issue" if issue_score > 0 else None)


def consult_ai_on_fidelity(
    prompt: str,
    tool: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 600,
    tracker: Optional[consultation_limits.ConsultationTracker] = None,
) -> ToolResponse:
    """
    Consult an AI tool for implementation fidelity review.

    Simplified wrapper around ai_tools.execute_tool_with_fallback() with fidelity-review defaults
    and comprehensive error handling.

    Args:
        prompt: The review prompt to send to the AI tool
        tool: Specific tool to use (gemini, codex, cursor-agent).
              If None, uses first available tool.
        model: Model to request (optional, tool-specific)
        timeout: Timeout in seconds (default: 600)
        tracker: Optional ConsultationTracker instance for limiting tool usage

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
            available_tools = ai_tools.get_enabled_and_available_tools(FIDELITY_SKILL_NAME)
            if not available_tools:
                raise NoToolsAvailableError(
                    "No AI consultation tools available. "
                    f"Please install: {', '.join(ALL_SUPPORTED_TOOLS)}"
                )
            tool = available_tools[0]
            logger.info(f"Using detected tool: {tool}")

        # Check if specified tool is available
        if not ai_tools.check_tool_available(tool):
            raise NoToolsAvailableError(
                f"Tool '{tool}' not found. "
                "Please install it or choose a different tool."
            )

        # Resolve model configuration (explicit CLI arg wins over config)
        resolved_model = ai_config.resolve_tool_model(
            FIDELITY_SKILL_NAME,
            tool,
            override=model,
        )

        # Execute consultation with fallback
        response = ai_tools.execute_tool_with_fallback(
            skill_name=FIDELITY_SKILL_NAME,
            tool=tool,
            prompt=prompt,
            model=resolved_model,
            timeout=timeout,
            tracker=tracker,
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
    timeout: int = 600,
    require_all_success: bool = False,
    cache_key_params: Optional[Dict[str, Any]] = None,
    use_cache: Optional[bool] = None,
    progress_emitter: Optional[ProgressEmitter] = None
) -> List[ToolResponse]:
    """
    Consult multiple AI tools in parallel for fidelity review.

    Wrapper around ai_tools.execute_tools_parallel() with fidelity-review defaults,
    comprehensive error handling, and optional caching support.

    Caching Behavior:
        - First checks cache for existing results (cache hit = instant return)
        - On cache miss, consults AI tools via ai_tools.execute_tools_parallel()
        - Saves fresh consultation results to cache for future use
        - Cache save failures are non-fatal (logged as warnings)
        - Serialization format preserves tool, status, output, error, model, metadata

    Args:
        prompt: The review prompt to send to all AI tools
        tools: List of tools to consult (gemini, codex, cursor-agent).
               If None, uses all available tools.
        model: Model to request (optional, tool-specific)
        timeout: Timeout in seconds per tool (default: 120)
        require_all_success: If True, raise exception if any tool fails
        cache_key_params: Parameters for cache key generation (spec_id, scope, target, file_paths)
        use_cache: Enable caching (overrides config, defaults to config setting)
        progress_emitter: Optional ProgressEmitter for emitting structured events (cache_check,
                          ai_consultation, model_response, cache_save, complete)

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
    cache_key = None
    cache = None

    try:
        # Track any tool availability errors to defer until after cache check
        tool_availability_error: Optional[NoToolsAvailableError] = None
        final_tools_to_consult: List[str] = []
        resolved_models_map: Dict[str, Optional[str]] = {}
        models_summary = ""
        models_payload: Dict[str, Optional[str]] = {}

        # If no tools specified, detect available tools and filter by config
        # We do this without raising errors yet, to allow cache check to happen first
        if tools is None:
            # Get enabled tools from config
            enabled_tools_config = get_enabled_fidelity_tools()
            enabled_tool_names = list(enabled_tools_config.keys())

            # Detect all available tools
            all_available_tools = ai_tools.get_enabled_and_available_tools(FIDELITY_SKILL_NAME)
            if not all_available_tools:
                tool_availability_error = NoToolsAvailableError(
                    "No AI consultation tools available. "
                    f"Please install: {', '.join(ALL_SUPPORTED_TOOLS)}"
                )
            else:
                # Filter to only tools that are BOTH available AND enabled
                tools = [t for t in all_available_tools if t in enabled_tool_names]

                if not tools:
                    # Fallback to all available if none match enabled filter
                    logger.warning(
                        f"No tools matched enabled config ({enabled_tool_names}). "
                        f"Using all available tools: {', '.join(all_available_tools)}"
                    )
                    tools = all_available_tools
                else:
                    logger.info(f"Using enabled tools from config: {', '.join(tools)}")

        # Filter to only available tools (if we have tools to check)
        if tools is not None and not tool_availability_error:
            available_tools = [t for t in tools if ai_tools.check_tool_available(t)]
            if not available_tools:
                tool_availability_error = NoToolsAvailableError(
                    f"None of the specified tools are available: {', '.join(tools)}"
                )
            else:
                if len(available_tools) < len(tools):
                    unavailable = set(tools) - set(available_tools)
                    logger.warning(f"Some tools unavailable: {', '.join(unavailable)}")

                enabled_tools_map = get_enabled_fidelity_tools()
                final_tools_to_consult = [
                    tool for tool in available_tools if tool in enabled_tools_map
                ]
                if not final_tools_to_consult:
                    tool_availability_error = NoToolsAvailableError(
                        f"All available tools ({', '.join(available_tools)}) are disabled in the configuration."
                    )

        # Resolve models if we have tools
        if final_tools_to_consult and not tool_availability_error:
            resolved_models_map = ai_config.resolve_models_for_tools(
                FIDELITY_SKILL_NAME,
                final_tools_to_consult,
                override=model,
            )
            models_summary = _summarize_models_map(resolved_models_map)
            models_payload = dict(resolved_models_map)

        # Check cache before raising any tool availability errors
        # This allows cache hits to short-circuit even when no tools are available
        if cache_enabled and cache_key_params and _CACHE_AVAILABLE:
            try:
                cache = cache or CacheManager()
                cache_key = generate_fidelity_review_key(
                    spec_id=cache_key_params.get("spec_id", ""),
                    scope=cache_key_params.get("scope", ""),
                    target=cache_key_params.get("target", ""),
                    file_paths=cache_key_params.get("file_paths"),
                    models=resolved_models_map,
                    model=model,
                )

                cached_data = cache.get(cache_key)
                if cached_data:
                    logger.info("Cache hit: Using cached AI consultation results")
                    if progress_emitter:
                        progress_emitter.emit("cache_check", {
                            "cache_hit": True,
                            "cache_key": cache_key[:32] + "...",
                            "num_responses": len(cached_data),
                            "models": models_payload,
                            "models_summary": models_summary,
                        })
                    cached_responses = [
                        ToolResponse(
                            tool=resp_data["tool"],
                            status=ToolStatus(resp_data["status"]),
                            output=resp_data["output"],
                            error=resp_data.get("error"),
                            exit_code=resp_data.get("exit_code"),
                            model=resp_data.get("model"),
                            metadata=resp_data.get("metadata", {})
                        )
                        for resp_data in cached_data
                    ]
                    return cached_responses
                else:
                    logger.debug("Cache miss: Will consult AI tools and cache results")
                    if progress_emitter:
                        progress_emitter.emit("cache_check", {
                            "cache_hit": False,
                            "cache_key": cache_key[:32] + "...",
                            "models": models_payload,
                            "models_summary": models_summary,
                        })
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}. Proceeding with AI consultation.")

        # If we deferred a tool availability error and didn't get a cache hit, raise it now
        if tool_availability_error:
            raise tool_availability_error

        # Emit ai_consultation event before calling AI tools
        if progress_emitter:
            progress_emitter.emit("ai_consultation", {
                "tools": final_tools_to_consult,
                "model": models_summary,
                "models_summary": models_summary,
                "models": models_payload,
                "timeout": timeout
            })

        # Execute consultations in parallel
        models_dict_raw = {
            tool: resolved_model
            for tool, resolved_model in resolved_models_map.items()
            if resolved_model
        }
        models_dict = models_dict_raw if models_dict_raw else None
        multi_response = ai_tools.execute_tools_parallel(
            tools=final_tools_to_consult,
            prompt=prompt,
            models=models_dict,
            timeout=timeout
        )
        # Extract list of responses from MultiToolResponse dataclass
        responses = list(multi_response.responses.values())

        # Emit model_response events for each response
        if progress_emitter:
            for resp in responses:
                progress_emitter.emit("model_response", {
                    "tool": resp.tool,
                    "status": resp.status.value,
                    "model": resp.model,
                    "models_summary": models_summary,
                    "models": models_payload,
                    "has_error": resp.error is not None,
                    "output_length": len(resp.output) if resp.output else 0
                })

        # Save responses to cache if caching enabled
        if cache_enabled and cache_key and cache and _CACHE_AVAILABLE:
            try:
                # Serialize ToolResponse objects to cache-friendly format
                serialized_responses = []
                for resp in responses:
                    serialized_responses.append({
                        "tool": resp.tool,
                        "status": resp.status.value,
                        "output": resp.output,
                        "error": resp.error,
                        "exit_code": resp.exit_code,
                        "model": resp.model,
                        "metadata": resp.metadata
                    })

                # Save to cache (CacheManager handles TTL from config)
                success = cache.set(cache_key, serialized_responses)
                if success:
                    logger.info(f"Saved AI consultation results to cache (key: {cache_key[:32]}...)")
                    # Emit cache_save event
                    if progress_emitter:
                        progress_emitter.emit("cache_save", {
                            "success": True,
                            "cache_key": cache_key[:32] + "...",
                            "num_responses": len(serialized_responses),
                            "models_summary": models_summary,
                            "models": models_payload,
                        })
                else:
                    logger.warning("Failed to save consultation results to cache")
                    if progress_emitter:
                        progress_emitter.emit("cache_save", {
                            "success": False,
                            "cache_key": cache_key[:32] + "...",
                            "models_summary": models_summary,
                            "models": models_payload,
                        })
            except Exception as e:
                logger.warning(f"Failed to save consultation results to cache: {e}")
                # Emit cache_save failure event
                if progress_emitter:
                    progress_emitter.emit("cache_save", {
                        "success": False,
                        "error": str(e),
                        "models_summary": models_summary,
                        "models": models_payload,
                    })
                # Continue without caching - non-fatal error

        # Check for failures if required
        if require_all_success:
            failures = [r for r in responses if not r.success]
            if failures:
                failed_tools = [r.tool for r in failures]
                raise ConsultationError(
                    f"Consultation failed for tools: {', '.join(failed_tools)}"
                )

        # Emit complete event
        if progress_emitter:
            successful = len([r for r in responses if r.success])
            progress_emitter.emit("complete", {
                "total_responses": len(responses),
                "successful": successful,
                "failed": len(responses) - successful,
                "models_summary": models_summary,
                "models": models_payload,
            })

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
    provider_name: Optional[str] = None
    model_name: Optional[str] = None

    if isinstance(response, str):
        output = response.strip()
        success = True
        error = None
    else:
        output = response.output.strip() if response.output else ""
        success = response.success
        error = response.error
        provider_name = response.tool
        model_name = response.model

    # Initialize with defaults
    verdict = FidelityVerdict.UNKNOWN
    issues: List[str] = []
    recommendations: List[str] = []
    summary = ""

    issue_seen: Set[str] = set()
    recommendation_seen: Set[str] = set()

    def add_issue(candidate: str) -> None:
        cleaned_candidate = _strip_markdown_emphasis(candidate)
        normalized_candidate = _normalize_for_matching(cleaned_candidate)
        if not normalized_candidate or normalized_candidate in issue_seen:
            return
        issue_seen.add(normalized_candidate)
        issues.append(cleaned_candidate)

    def add_recommendation(candidate: str) -> None:
        cleaned_candidate = _strip_markdown_emphasis(candidate)
        normalized_candidate = _normalize_for_matching(cleaned_candidate)
        if not normalized_candidate or normalized_candidate in recommendation_seen:
            return
        recommendation_seen.add(normalized_candidate)
        recommendations.append(cleaned_candidate)

    # If response failed, return early with UNKNOWN verdict
    if not success:
        return ParsedReviewResponse(
            verdict=FidelityVerdict.UNKNOWN,
            issues=[f"Tool execution failed: {error}"],
            recommendations=[],
            summary="Unable to complete review due to tool failure",
            raw_response=output,
            provider=provider_name,
            model=model_name
        )

    json_payload = _load_json_from_text(output)
    structured_payload: Optional[Dict[str, Any]] = None
    summary_provided = False

    if isinstance(json_payload, dict):
        if (
            "response" in json_payload
            and isinstance(json_payload["response"], str)
        ):
            nested_payload = _load_json_from_text(json_payload["response"])
            if isinstance(nested_payload, dict):
                json_payload = nested_payload

        verdict_from_json = _coerce_verdict(json_payload.get("verdict"))
        if verdict_from_json is not None:
            verdict = verdict_from_json

        json_summary = json_payload.get("summary")
        if isinstance(json_summary, str) and json_summary.strip():
            summary = json_summary.strip()
            summary_provided = True

        json_issues = json_payload.get("issues")
        if isinstance(json_issues, list):
            for entry in json_issues:
                issue_text = _coerce_issue_entry(entry)
                if issue_text:
                    add_issue(issue_text)

        json_recommendations = json_payload.get("recommendations")
        if isinstance(json_recommendations, list):
            for entry in json_recommendations:
                rec_text = _coerce_recommendation_entry(entry)
                if rec_text:
                    add_recommendation(rec_text)

        _extract_structured_json_insights(json_payload, add_issue, add_recommendation)

        structured_payload = deepcopy(json_payload)

    # Extract verdict using pattern matching
    if verdict is FidelityVerdict.UNKNOWN:
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

    normalized_output = output.replace("\r\n", "\n")

    # Extract structured sections using headings and list heuristics
    sections = _split_sections_by_heading(normalized_output)
    allow_issue_extraction = not issues
    allow_recommendation_extraction = not recommendations
    if allow_issue_extraction or allow_recommendation_extraction:
        for heading, section_text in sections:
            section_hint = _classify_heading(heading)
            items = _extract_list_items(section_text)

            if not items and section_hint in {"issue", "recommendation"}:
                # Split paragraph text into meaningful chunks when no explicit list exists
                items = [
                    chunk.strip()
                    for chunk in re.split(r'\n\s*\n', section_text)
                    if chunk and chunk.strip()
                ]

            for item in items:
                classification = _classify_list_item(item, section_hint)
                if allow_issue_extraction and classification == "issue":
                    add_issue(item)
                elif allow_recommendation_extraction and classification == "recommendation":
                    add_recommendation(item)

    # Fallback to legacy regex extraction for backward compatibility
    if not issues:
        issue_patterns = [
            r'(?:Issue|Problem|Concern|Error)(?:s)?:\s*\n?[-•*]?\s*(.+?)(?:\n\n|\n[-•*]|\Z)',
            r'(?:Found|Identified)\s+(?:the following\s+)?(?:issue|problem)(?:s)?:\s*\n?(.+?)(?:\n\n|\Z)',
            r'[-•*]\s*Issue:\s*(.+?)(?:\n|\Z)',
        ]

        for pattern in issue_patterns:
            matches = re.finditer(pattern, normalized_output, re.IGNORECASE | re.DOTALL)
            for match in matches:
                issue_text = match.group(1).strip()
                sub_issues = re.split(r'\n[-•*]\s*', issue_text)
                for sub_issue in sub_issues:
                    if sub_issue.strip():
                        add_issue(sub_issue)

    if not recommendations:
        rec_patterns = [
            r'(?:Recommendation|Suggest|Should)(?:s)?:\s*\n?[-•*]?\s*(.+?)(?:\n\n|\n[-•*]|\Z)',
            r'(?:I recommend|It is recommended|Consider)\s+(.+?)(?:\n|\Z)',
            r'[-•*]\s*Recommendation:\s*(.+?)(?:\n|\Z)',
        ]

        for pattern in rec_patterns:
            matches = re.finditer(pattern, normalized_output, re.IGNORECASE | re.DOTALL)
            for match in matches:
                rec_text = match.group(1).strip()
                sub_recs = re.split(r'\n[-•*]\s*', rec_text)
                for sub_rec in sub_recs:
                    if sub_rec.strip():
                        add_recommendation(sub_rec)

    # Extract summary (first paragraph with generous cap)
    if not summary_provided:
        summary_segments = [
            segment.strip()
            for segment in re.split(r'\n\s*\n', normalized_output, maxsplit=1)
            if segment and segment.strip()
        ]
        if summary_segments:
            summary = summary_segments[0]
        else:
            summary = normalized_output.strip()

    final_raw_response = None if structured_payload is not None else (output if output else None)

    return ParsedReviewResponse(
        verdict=verdict,
        issues=issues,
        recommendations=recommendations,
        summary=summary,
        raw_response=final_raw_response,
        structured_response=structured_payload,
        provider=provider_name,
        model=model_name
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
    issue_order: List[str] = []
    issue_originals: Dict[str, str] = {}
    for response in parsed_responses:
        for issue in response.issues:
            cleaned_issue = issue.strip()
            normalized_issue = _normalize_for_matching(cleaned_issue)
            if not normalized_issue:
                continue
            if normalized_issue not in issue_counts:
                issue_counts[normalized_issue] = 0
                issue_originals[normalized_issue] = cleaned_issue
                issue_order.append(normalized_issue)
            issue_counts[normalized_issue] += 1

    # 3. Identify consensus issues (mentioned by >= min_agreement models)
    consensus_issues = _dedupe_preserve_order([
        issue_originals[norm]
        for norm in issue_order
        if issue_counts.get(norm, 0) >= min_agreement
    ])
    all_issues = _dedupe_preserve_order([issue_originals[norm] for norm in issue_order])

    # 4. Collect all recommendations and count occurrences
    rec_counts: Dict[str, int] = {}
    rec_order: List[str] = []
    rec_originals: Dict[str, str] = {}
    for response in parsed_responses:
        for rec in response.recommendations:
            cleaned_rec = rec.strip()
            normalized_rec = _normalize_for_matching(cleaned_rec)
            if not normalized_rec:
                continue
            if normalized_rec not in rec_counts:
                rec_counts[normalized_rec] = 0
                rec_originals[normalized_rec] = cleaned_rec
                rec_order.append(normalized_rec)
            rec_counts[normalized_rec] += 1

    # 5. Identify consensus recommendations (mentioned by >= min_agreement models)
    consensus_recommendations = _dedupe_preserve_order([
        rec_originals[norm]
        for norm in rec_order
        if rec_counts.get(norm, 0) >= min_agreement
    ])
    all_recommendations = _dedupe_preserve_order([rec_originals[norm] for norm in rec_order])

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
