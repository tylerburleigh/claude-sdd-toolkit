"""
Standalone CLI helpers for invoking ProviderContext implementations.

Exposes:
    * `build_parser()` - reusable argparse parser for provider invocations.
    * `run_cli()`      - entrypoint for `python -m claude_skills.cli.provider_runner`.
    * `run_provider()` - programmatic API used by future registries/skills.

The runner focuses on consistent logging, timeout handling, optional streaming
display, and machine-readable JSON output so provider implementations can be
tested or exercised in isolation from higher-level skills.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

from claude_skills.common import PrettyPrinter
from claude_skills.common.providers import (
    GenerationRequest,
    GenerationResult,
    ProviderContext,
    ProviderError,
    ProviderHooks,
    ProviderStatus,
    ProviderUnavailableError,
    ProviderExecutionError,
    ProviderTimeoutError,
    StreamChunk,
    TokenUsage,
)

logger = logging.getLogger(__name__)

try:
    from claude_skills.common.providers import resolve_provider as _resolve_provider
except Exception:  # pragma: no cover - best effort optional dependency
    _resolve_provider = None  # type: ignore


class ProviderLoader(Protocol):
    """Callable used by the runner to obtain ProviderContext instances."""

    def __call__(
        self,
        provider: str,
        *,
        hooks: ProviderHooks,
        model: Optional[str] = None,
    ) -> ProviderContext: ...


@dataclass
class RunnerConfig:
    """Configuration parsed from CLI flags or programmatic callers."""

    provider: str
    prompt: str
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    timeout: Optional[int] = None
    stream: bool = False
    json_output: bool = False
    quiet_stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunnerResult:
    """Return payload for scripted consumers."""

    status: ProviderStatus
    provider: str
    model: Optional[str]
    duration: float
    result: Optional[GenerationResult] = None
    error_message: Optional[str] = None


def build_parser() -> argparse.ArgumentParser:
    """Create an ArgumentParser for provider invocations."""
    parser = argparse.ArgumentParser(
        prog="provider-runner",
        description="Execute provider abstraction implementations with consistent output formatting.",
    )
    parser.add_argument(
        "-p",
        "--provider",
        required=True,
        help="Provider identifier (e.g., gemini, codex, cursor-agent).",
    )
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument(
        "--prompt",
        help="Prompt text to send to the provider.",
    )
    prompt_group.add_argument(
        "--prompt-file",
        help="Path to file containing the prompt (use '-' for stdin).",
    )
    parser.add_argument(
        "--system-prompt",
        help="Optional system prompt / instructions.",
    )
    parser.add_argument(
        "--model",
        help="Model identifier override (provider specific).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in seconds for provider execution.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Request streaming output (if provider supports it).",
    )
    parser.add_argument(
        "--quiet-stream",
        action="store_true",
        help="Do not echo streamed chunks to stdout (still captured in final output).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of PrettyPrinter output.",
    )
    parser.add_argument(
        "--metadata",
        action="append",
        metavar="KEY=VALUE",
        help="Additional metadata to pass with the request (repeatable).",
    )
    parser.add_argument(
        "--metadata-json",
        help="JSON string containing additional metadata to merge into the request.",
    )
    return parser


def _default_provider_loader(
    provider: str,
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
) -> ProviderContext:
    """
    Lazy loader that defers to the provider registry once it exists.

    Until the registry module lands, this helper raises a clear error so
    callers understand that provider execution is not yet wired up.
    """
    if _resolve_provider is None:
        raise ProviderUnavailableError(
            "Provider registry is not available yet.",
            provider=provider,
        )
    return _resolve_provider(provider, hooks=hooks, model=model)


def run_provider(
    config: RunnerConfig,
    *,
    printer: Optional[PrettyPrinter] = None,
    loader: Optional[ProviderLoader] = None,
) -> RunnerResult:
    """
    Execute a provider with the supplied configuration.

    Returns a RunnerResult containing execution metadata so automated callers
    can inspect status, timing, and outputs.
    """
    printer = printer or PrettyPrinter()
    loader = loader or _default_provider_loader

    stream_buffer: List[str] = []

    def _handle_stream(chunk: StreamChunk) -> None:
        stream_buffer.append(chunk.content)
        if config.quiet_stream or config.json_output:
            return
        sys.stdout.write(chunk.content)
        sys.stdout.flush()

    hooks = ProviderHooks(on_stream_chunk=_handle_stream)
    started_at = time.perf_counter()

    try:
        context = loader(config.provider, hooks=hooks, model=config.model)
    except ProviderUnavailableError as exc:
        logger.error("Provider '%s' unavailable: %s", config.provider, exc)
        return RunnerResult(
            status=ProviderStatus.NOT_FOUND,
            provider=config.provider,
            model=config.model,
            duration=0.0,
            error_message=str(exc),
        )

    request = GenerationRequest(
        prompt=config.prompt,
        system_prompt=config.system_prompt,
        temperature=None,
        max_tokens=None,
        metadata=config.metadata,
        timeout=config.timeout,
        stream=config.stream,
    )

    try:
        result = context.generate(request)
        duration = time.perf_counter() - started_at
        if stream_buffer and not result.content:
            result = replace(result, content="".join(stream_buffer))
        return RunnerResult(
            status=result.status,
            provider=config.provider,
            model=result.model_fqn,
            duration=duration,
            result=result,
        )
    except ProviderTimeoutError as exc:
        duration = time.perf_counter() - started_at
        logger.warning("Provider '%s' timed out: %s", config.provider, exc)
        return RunnerResult(
            status=ProviderStatus.TIMEOUT,
            provider=config.provider,
            model=config.model,
            duration=duration,
            error_message=str(exc),
        )
    except ProviderExecutionError as exc:
        duration = time.perf_counter() - started_at
        logger.error("Provider '%s' execution error: %s", config.provider, exc)
        return RunnerResult(
            status=ProviderStatus.ERROR,
            provider=config.provider,
            model=config.model,
            duration=duration,
            error_message=str(exc),
        )
    except ProviderError as exc:
        duration = time.perf_counter() - started_at
        logger.error("Provider '%s' failed: %s", config.provider, exc)
        return RunnerResult(
            status=ProviderStatus.ERROR,
            provider=config.provider,
            model=config.model,
            duration=duration,
            error_message=str(exc),
        )


def _load_prompt(args: argparse.Namespace) -> str:
    """Resolve prompt from inline text or file/stdin."""
    if args.prompt is not None:
        return args.prompt

    path = args.prompt_file
    if path == "-":
        return sys.stdin.read()
    file_path = Path(path).expanduser()
    return file_path.read_text(encoding="utf-8")


def _parse_metadata(args: argparse.Namespace) -> Dict[str, Any]:
    """Combine key=value pairs and JSON metadata flags."""
    metadata: Dict[str, Any] = {}

    if args.metadata_json:
        try:
            parsed = json.loads(args.metadata_json)
            if isinstance(parsed, dict):
                metadata.update(parsed)
            else:
                raise ValueError("metadata JSON must be an object")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid metadata JSON: {exc}") from exc

    for entry in args.metadata or []:
        if "=" not in entry:
            raise ValueError(f"Metadata entry must be KEY=VALUE, got '{entry}'")
        key, value = entry.split("=", 1)
        metadata[key.strip()] = value.strip()

    return metadata


def _print_result(result: RunnerResult, config: RunnerConfig, printer: PrettyPrinter) -> None:
    """Pretty-print execution results."""
    printer.header("Provider Result")
    printer.result("Provider", config.provider)
    printer.result("Status", result.status.value)
    printer.result("Duration", f"{result.duration:.2f}s")

    if result.error_message:
        printer.warning(result.error_message)
        return

    if not result.result:
        printer.warning("No result payload returned.")
        return

    printer.result("Model", result.result.model_fqn or "(unknown)")

    usage = result.result.usage
    if any(
        [
            usage.input_tokens,
            usage.output_tokens,
            usage.cached_input_tokens,
            usage.total_tokens,
        ]
    ):
        printer.result("Token Usage", "", indent=0)
        printer.result("Input", str(usage.input_tokens), indent=1)
        printer.result("Output", str(usage.output_tokens), indent=1)
        printer.result(
            "Total",
            str(usage.total_tokens or (usage.input_tokens + usage.output_tokens)),
            indent=1,
        )

    printer.blank()
    printer.header("Output")
    sys.stdout.write(result.result.content or "(empty)")
    if not result.result.content.endswith("\n"):
        sys.stdout.write("\n")


def _dump_json_result(result: RunnerResult) -> None:
    """Emit JSON payload for automation."""
    payload: Dict[str, Any] = {
        "status": result.status.value,
        "provider": result.provider,
        "model": result.model,
        "duration": result.duration,
    }
    if result.error_message:
        payload["error"] = result.error_message
    if result.result:
        payload["content"] = result.result.content
        payload["usage"] = {
            "input_tokens": result.result.usage.input_tokens,
            "output_tokens": result.result.usage.output_tokens,
            "cached_input_tokens": result.result.usage.cached_input_tokens,
            "total_tokens": result.result.usage.total_tokens,
            "metadata": result.result.usage.metadata,
        }
        payload["raw_payload"] = result.result.raw_payload
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def run_cli(argv: Optional[List[str]] = None) -> int:
    """
    Command-line entrypoint used by python -m claude_skills.cli.provider_runner.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        prompt = _load_prompt(args)
        metadata = _parse_metadata(args)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2

    config = RunnerConfig(
        provider=args.provider,
        prompt=prompt,
        system_prompt=args.system_prompt,
        model=args.model,
        timeout=args.timeout,
        stream=args.stream,
        quiet_stream=args.quiet_stream,
        json_output=args.json,
        metadata=metadata,
    )

    printer = PrettyPrinter()
    result = run_provider(config, printer=printer)

    if args.json:
        _dump_json_result(result)
    else:
        _print_result(result, config, printer)

    return 0 if result.status == ProviderStatus.SUCCESS else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_cli())
