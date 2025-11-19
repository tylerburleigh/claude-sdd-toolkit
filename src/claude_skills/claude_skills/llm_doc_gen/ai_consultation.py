"""
AI Consultation Integration for LLM Documentation Generation.

Bridges documentation generators with AI provider abstraction.
Handles LLM consultation with graceful error handling.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, Any, Dict
from dataclasses import dataclass


@dataclass
class ConsultationResult:
    """Result from AI consultation."""

    success: bool
    output: str
    error: Optional[str] = None
    tool_used: Optional[str] = None
    duration: Optional[float] = None


class AIConsultationError(Exception):
    """Raised when AI consultation fails."""

    pass


def get_available_providers() -> list[str]:
    """
    Get list of available AI providers.

    Checks for external AI CLI tools that can be used for consultation.
    Falls back to empty list if no providers available.

    Returns:
        List of available provider names
    """
    # Try to import from existing code-doc AI tools
    try:
        from claude_skills.common.ai_tools import get_enabled_and_available_tools

        return get_enabled_and_available_tools("llm-doc-gen")
    except ImportError:
        # Fallback: check common providers manually
        import shutil

        available = []
        common_providers = ["cursor-agent", "gemini", "codex", "opencode"]

        for provider in common_providers:
            if shutil.which(provider):
                available.append(provider)

        return available


def consult_llm(
    prompt: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 120,
    verbose: bool = False,
) -> ConsultationResult:
    """
    Consult an LLM with the given prompt.

    Integrates with existing AI provider abstraction with graceful error handling.

    Args:
        prompt: Formatted prompt for LLM
        provider: Specific provider to use (auto-selected if None)
        model: Specific model to use (uses provider default if None)
        timeout: Timeout in seconds
        verbose: Enable verbose output

    Returns:
        ConsultationResult with success status and output/error

    Raises:
        AIConsultationError: If consultation fails critically
    """
    import time

    start_time = time.time()

    # Try to use existing provider abstraction
    try:
        from claude_skills.common.ai_tools import execute_tool_with_fallback

        # Auto-select provider if not specified
        if provider is None:
            available = get_available_providers()
            if not available:
                return ConsultationResult(
                    success=False,
                    output="",
                    error="No AI providers available. Install cursor-agent, gemini, codex, or opencode.",
                )
            provider = available[0]

        if verbose:
            print(f"Consulting {provider} for documentation generation...")
            sys.stdout.flush()

        # Use existing provider abstraction
        response = execute_tool_with_fallback(
            skill_name="llm-doc-gen",
            tool=provider,
            prompt=prompt,
            model=model,
            timeout=timeout,
            context={"doc_type": "overview"},
        )

        duration = time.time() - start_time

        if response.success:
            return ConsultationResult(
                success=True,
                output=response.output,
                tool_used=provider,
                duration=duration,
            )
        else:
            error_msg = response.error or f"{provider} consultation failed"
            return ConsultationResult(
                success=False, output="", error=error_msg, tool_used=provider, duration=duration
            )

    except ImportError:
        # Fallback: direct CLI execution
        return _consult_llm_direct(prompt, provider, model, timeout, verbose, start_time)


def _consult_llm_direct(
    prompt: str,
    provider: Optional[str],
    model: Optional[str],
    timeout: int,
    verbose: bool,
    start_time: float,
) -> ConsultationResult:
    """
    Direct CLI consultation fallback when provider abstraction unavailable.

    Args:
        prompt: Formatted prompt
        provider: Provider name
        model: Model name
        timeout: Timeout in seconds
        verbose: Verbose output
        start_time: Start time for duration tracking

    Returns:
        ConsultationResult
    """
    import subprocess
    import time
    import shutil

    # Auto-select provider
    if provider is None:
        available = get_available_providers()
        if not available:
            return ConsultationResult(
                success=False, output="", error="No AI providers available"
            )
        provider = available[0]

    # Check provider exists
    if not shutil.which(provider):
        return ConsultationResult(
            success=False, output="", error=f"Provider {provider} not found in PATH"
        )

    if verbose:
        print(f"Consulting {provider} (direct CLI)...")
        sys.stdout.flush()

    # Build command
    cmd = [provider]
    if model:
        cmd.extend(["--model", model])

    try:
        # Run with timeout
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            return ConsultationResult(
                success=True,
                output=result.stdout,
                tool_used=provider,
                duration=duration,
            )
        else:
            return ConsultationResult(
                success=False,
                output="",
                error=f"{provider} exited with code {result.returncode}: {result.stderr}",
                tool_used=provider,
                duration=duration,
            )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ConsultationResult(
            success=False,
            output="",
            error=f"{provider} timed out after {timeout}s",
            tool_used=provider,
            duration=duration,
        )
    except Exception as e:
        duration = time.time() - start_time
        return ConsultationResult(
            success=False,
            output="",
            error=f"{provider} execution failed: {str(e)}",
            tool_used=provider,
            duration=duration,
        )


def consult_multi_agent(
    prompt: str,
    providers: Optional[list[str]] = None,
    timeout: int = 120,
    verbose: bool = False,
) -> Dict[str, ConsultationResult]:
    """
    Consult multiple AI providers in parallel.

    Args:
        prompt: Formatted prompt for LLMs
        providers: List of providers to use (auto-selected if None)
        timeout: Timeout in seconds per provider
        verbose: Enable verbose output

    Returns:
        Dictionary mapping provider names to ConsultationResults
    """
    # Try to use existing multi-agent consultation
    try:
        from claude_skills.common.ai_tools import execute_tools_parallel

        # Auto-select providers if not specified
        if providers is None:
            available = get_available_providers()
            if len(available) < 2:
                # Fall back to single consultation
                result = consult_llm(prompt, timeout=timeout, verbose=verbose)
                return {result.tool_used or "unknown": result}

            providers = available[:3]  # Use top 3 available

        if verbose:
            print(f"Consulting {len(providers)} providers in parallel...")
            sys.stdout.flush()

        # Use existing parallel execution
        multi_response = execute_tools_parallel(
            tools=providers,
            prompt=prompt,
            models={},  # Use defaults
        )

        # Convert to our result format
        results = {}
        for tool, response in multi_response.responses.items():
            results[tool] = ConsultationResult(
                success=response.success,
                output=response.output if response.success else "",
                error=None if response.success else response.error,
                tool_used=tool,
                duration=response.duration,
            )

        return results

    except ImportError:
        # Fallback: sequential consultation
        results = {}
        for provider in providers or get_available_providers()[:3]:
            result = consult_llm(prompt, provider=provider, timeout=timeout, verbose=verbose)
            results[provider] = result

        return results


def test_consultation() -> bool:
    """
    Test AI consultation with a simple prompt.

    Returns:
        True if consultation works, False otherwise
    """
    test_prompt = "# Test\n\nRespond with 'OK' if you can read this."

    result = consult_llm(test_prompt, timeout=30, verbose=False)

    return result.success
