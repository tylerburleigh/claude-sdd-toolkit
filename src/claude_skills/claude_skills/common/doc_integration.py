"""
Doc Integration Utilities for SDD Skills

Provides unified utilities for checking documentation availability,
prompting for generation, and handling user responses.

This module serves as a shared contract between SDD skills (sdd-plan,
sdd-next, sdd-update) and the documentation system (llm-doc-gen, doc-query).
"""

from enum import Enum
import logging
import subprocess
import json
import os
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Import git helpers for commit-based staleness detection
try:
    from .doc_helper import get_current_git_commit, count_commits_between
except ImportError:
    # Fallback if doc_helper not available
    def get_current_git_commit(project_root: str = ".") -> Optional[str]:
        return None
    def count_commits_between(commit_a: str, commit_b: str, project_root: str = ".") -> int:
        return 0


class DocStatus(Enum):
    """Documentation availability status."""
    AVAILABLE = "available"     # Docs exist and are current
    MISSING = "missing"          # No docs found
    STALE = "stale"             # Docs exist but outdated
    ERROR = "error"              # Error checking status


# Module-level cache for documentation status (per-session)
_doc_status_cache: Optional[DocStatus] = None


def check_doc_availability(force_refresh: bool = False) -> DocStatus:
    """
    Check if codebase documentation is available via 'sdd doc stats'.

    This function calls the unified CLI command 'sdd doc stats --json' to
    determine if documentation exists and is current. Results are cached
    per session to avoid repeated subprocess calls.

    Args:
        force_refresh: If True, bypass cache and check again

    Returns:
        DocStatus: Current documentation status
            - AVAILABLE: Docs exist and are current
            - MISSING: No documentation found
            - STALE: Docs exist but are outdated
            - ERROR: Error occurred while checking

    Examples:
        >>> status = check_doc_availability()
        >>> if status == DocStatus.AVAILABLE:
        ...     print("Documentation is ready to use")
        >>> elif status == DocStatus.MISSING:
        ...     print("Need to generate documentation")
    """
    global _doc_status_cache

    # Return cached result if available and not forcing refresh
    if not force_refresh and _doc_status_cache is not None:
        logger.debug(f"check_doc_availability: returning cached status {_doc_status_cache.value}")
        return _doc_status_cache

    try:
        # Call sdd doc stats to check documentation status
        result = subprocess.run(
            ["sdd", "doc", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Handle different exit codes
        if result.returncode == 0:
            # Command succeeded - parse JSON to check staleness
            try:
                stats = json.loads(result.stdout)
                status = _determine_status_from_stats(stats)
                _doc_status_cache = status
                logger.debug(f"check_doc_availability: status={status.value} (fresh check)")
                return status
            except json.JSONDecodeError:
                # Invalid JSON output
                _doc_status_cache = DocStatus.ERROR
                return DocStatus.ERROR

        elif result.returncode == 1:
            # Documentation not found
            _doc_status_cache = DocStatus.MISSING
            return DocStatus.MISSING
        else:
            # Other error codes
            _doc_status_cache = DocStatus.ERROR
            return DocStatus.ERROR

    except FileNotFoundError:
        # sdd command not found in PATH
        _doc_status_cache = DocStatus.ERROR
        return DocStatus.ERROR
    except subprocess.TimeoutExpired:
        # Command timed out
        _doc_status_cache = DocStatus.ERROR
        return DocStatus.ERROR
    except Exception:
        # Catch-all for any other errors
        _doc_status_cache = DocStatus.ERROR
        return DocStatus.ERROR


def get_staleness_threshold() -> int:
    """
    Get the commit-based staleness threshold from environment variable.

    Returns:
        int: Number of commits after which docs are considered stale (default: 10)
    """
    try:
        threshold = os.environ.get('SDD_STALENESS_COMMIT_THRESHOLD', '10')
        return int(threshold)
    except (ValueError, TypeError):
        return 10


def _determine_status_from_stats(stats: dict) -> DocStatus:
    """
    Determine documentation status from parsed stats JSON.

    Uses commit-based staleness detection when git metadata is available,
    falls back to time-based detection (7 days) otherwise.

    Args:
        stats: Parsed JSON from 'sdd doc stats --json'

    Returns:
        DocStatus: AVAILABLE or STALE based on analysis
    """
    # Check if staleness information is provided
    if 'staleness' in stats:
        is_stale = stats['staleness'].get('is_stale', False)
        if is_stale:
            return DocStatus.STALE
        return DocStatus.AVAILABLE

    # Primary: Git-based staleness detection (commit count)
    metadata = stats.get('metadata', {})
    generated_at_commit = metadata.get('generated_at_commit')

    if generated_at_commit:
        # We have git metadata - use commit-based staleness
        current_commit = get_current_git_commit()

        if current_commit and current_commit != generated_at_commit:
            # Commits have changed - check how many
            commits_since = count_commits_between(generated_at_commit, current_commit)
            threshold = get_staleness_threshold()
            logger.debug(f"Staleness check: {commits_since} commits since generation (threshold: {threshold})")

            if commits_since >= threshold:
                return DocStatus.STALE
            # Within threshold - docs are current
            return DocStatus.AVAILABLE

        # Same commit or can't get current commit - docs are current
        return DocStatus.AVAILABLE

    # Fallback: Time-based staleness detection (7 days)
    generated_at = stats.get('generated_at') or metadata.get('generated_at')
    if not generated_at:
        # No timestamp - assume available but can't verify staleness
        return DocStatus.AVAILABLE

    try:
        # Parse the timestamp
        if isinstance(generated_at, str):
            # Handle ISO format timestamps
            gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        else:
            # Already a datetime or number
            return DocStatus.AVAILABLE

        # Check if docs are older than 7 days (conservative staleness threshold)
        now = datetime.now(timezone.utc)
        age_days = (now - gen_time).days

        if age_days > 7:
            return DocStatus.STALE
        return DocStatus.AVAILABLE

    except (ValueError, AttributeError):
        # Can't parse timestamp - assume available
        return DocStatus.AVAILABLE


def clear_doc_status_cache() -> None:
    """
    Clear the cached documentation status.

    Use this when documentation has been generated or modified and you
    want subsequent checks to reflect the new state.

    Example:
        >>> # After generating documentation
        >>> clear_doc_status_cache()
        >>> status = check_doc_availability()  # Will check again
    """
    global _doc_status_cache
    _doc_status_cache = None


def prompt_for_generation(
    skill_name: Optional[str] = None,
    context: Optional[str] = None,
    timeout_seconds: Optional[int] = None
) -> bool:
    """
    Prompt user to generate documentation with skill-specific messaging.

    Displays an interactive prompt asking if the user wants to generate
    codebase documentation. The prompt includes skill-specific value
    propositions explaining why documentation would be beneficial.

    Args:
        skill_name: Name of skill requesting generation (e.g., "sdd-plan",
                   "sdd-next", "sdd-update"). Used to customize the message
                   with skill-specific benefits.
        context: Additional context about why generation would help in this
                specific situation. Displayed to provide more detail.
        timeout_seconds: Timeout for user input in seconds. Currently not
                        implemented (Python's input() doesn't support timeout
                        natively). Reserved for future use.

    Returns:
        bool: True if user wants to generate documentation, False otherwise.
              Empty input (just pressing Enter) returns True (Y is default).

    Examples:
        >>> # Simple prompt with no context
        >>> if prompt_for_generation():
        ...     print("User wants to generate docs")

        >>> # Skill-specific prompt
        >>> if prompt_for_generation(skill_name="sdd-plan"):
        ...     # Shows sdd-plan specific benefits
        ...     print("Generating documentation...")

        >>> # With additional context
        >>> if prompt_for_generation(
        ...     skill_name="sdd-next",
        ...     context="Task requires understanding 15 related files"
        ... ):
        ...     print("Context helps user make informed decision")
    """
    # Build the prompt message with skill-specific value proposition
    message = _build_generation_prompt(skill_name, context)

    # Display prompt and get user input
    try:
        response = input(message).strip().lower()

        # Parse response using Y/n pattern (Y is default)
        if response in ('', 'y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            # Invalid input - default to No (safer choice)
            print("Invalid input. Treating as 'no'.")
            return False

    except KeyboardInterrupt:
        # User pressed Ctrl+C - treat as No
        print("\nPrompt cancelled.")
        return False
    except EOFError:
        # End of file reached (Ctrl+D or redirected input) - treat as No
        print("\nEnd of input reached. Treating as 'no'.")
        return False


def _build_generation_prompt(
    skill_name: Optional[str],
    context: Optional[str]
) -> str:
    """
    Build skill-specific documentation generation prompt.

    Creates a formatted prompt message that includes:
    1. A header indicating documentation is recommended
    2. Skill-specific value proposition explaining benefits
    3. Optional context about the current situation
    4. Y/n input request (with Y as default)

    Args:
        skill_name: Name of skill requesting generation. Used to select
                   appropriate value proposition message.
        context: Additional context to include in the prompt.

    Returns:
        str: Formatted prompt message ready to display to user

    Example output:
        📚 Documentation Generation Recommended

        Generating codebase documentation enables automated analysis of
        existing code patterns and architecture.

        Context: Task requires understanding auth system patterns

        Would you like to generate documentation now? [Y/n]:
    """
    # Map skill names to value propositions
    # Each skill has specific benefits that documentation provides
    value_props = {
        "sdd-plan": "automated analysis of existing code patterns and architecture",
        "sdd-next": "automatic file suggestions and dependency analysis for tasks",
        "sdd-update": "automatic verification of implementation completeness",
    }

    # Get skill-specific value proposition, or use default
    value_prop = value_props.get(
        skill_name,
        "faster codebase analysis and intelligent suggestions"
    )

    # Build prompt message
    lines = [
        "\n📚 Documentation Generation Recommended",
        "",
        f"Generating codebase documentation enables {value_prop}.",
    ]

    # Add optional context if provided
    if context:
        lines.append("")
        lines.append(f"Context: {context}")

    # Add input prompt
    lines.append("")
    lines.append("Would you like to generate documentation now? [Y/n]: ")

    return "\n".join(lines)
