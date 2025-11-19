"""Parse Claude Code transcript files to extract token usage metrics."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TokenMetrics:
    """Token usage metrics extracted from a transcript."""

    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    context_length: int

    @property
    def context_percentage(self, max_context: int = 155000) -> float:
        """Calculate context usage percentage."""
        return (self.context_length / max_context) * 100 if max_context > 0 else 0.0


def is_clear_command(entry: dict) -> bool:
    """
    Check if a transcript entry is a /clear command.

    The /clear command resets the conversation context, so we should
    reset token counters when we encounter it.

    Args:
        entry: A parsed JSONL entry from the transcript

    Returns:
        True if this entry represents a /clear command
    """
    if entry.get("type") != "user":
        return False

    message = entry.get("message", {})
    content = message.get("content", [])

    if not content or not isinstance(content, list):
        return False

    for item in content:
        if isinstance(item, dict):
            text = item.get("text", "")
            if "<command-name>/clear</command-name>" in text:
                return True

    return False


def parse_transcript(transcript_path: str | Path) -> Optional[TokenMetrics]:
    """
    Parse a Claude Code transcript JSONL file and extract token metrics.

    Args:
        transcript_path: Path to the transcript JSONL file

    Returns:
        TokenMetrics object with aggregated token data, or None if parsing fails
    """
    transcript_path = Path(transcript_path)

    if not transcript_path.exists():
        return None

    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0
    context_length = 0

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Check for /clear command - reset all counters
                if is_clear_command(entry):
                    input_tokens = 0
                    output_tokens = 0
                    cached_tokens = 0
                    context_length = 0
                    continue  # Don't process /clear entry itself

                # Skip sidechain and error messages
                if entry.get("isSidechain") or entry.get("isApiErrorMessage"):
                    continue

                # Extract usage data
                message = entry.get("message", {})
                usage = message.get("usage", {})

                if usage:
                    # Accumulate token counts
                    input_tokens += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)

                    # Cached tokens come from both read and creation
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    cache_creation = usage.get("cache_creation_input_tokens", 0)
                    cached_tokens += cache_read + cache_creation

                    # Context length is from the most recent valid entry
                    # (input tokens + cached tokens, excluding output)
                    context_length = (
                        usage.get("input_tokens", 0)
                        + usage.get("cache_read_input_tokens", 0)
                        + usage.get("cache_creation_input_tokens", 0)
                    )

    except Exception:
        return None

    total_tokens = input_tokens + output_tokens + cached_tokens

    return TokenMetrics(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
        context_length=context_length,
    )
