"""
Cursor Agent CLI provider implementation.

Adapts the `cursor-agent` command-line tool to the ProviderContext contract,
including availability checks, streaming normalization, and response parsing.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

from .base import (
    GenerationRequest,
    GenerationResult,
    ModelDescriptor,
    ProviderCapability,
    ProviderContext,
    ProviderExecutionError,
    ProviderHooks,
    ProviderMetadata,
    ProviderStatus,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StreamChunk,
    TokenUsage,
)
from .registry import register_provider
from .detectors import detect_provider_availability

DEFAULT_BINARY = "cursor-agent"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_TEMPERATURE = 0.3
AVAILABILITY_OVERRIDE_ENV = "CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE"
CUSTOM_BINARY_ENV = "CURSOR_AGENT_CLI_BINARY"


class RunnerProtocol(Protocol):
    """Callable signature used for executing cursor-agent CLI commands."""

    def __call__(
        self,
        command: Sequence[str],
        *,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess[str]:
        raise NotImplementedError


def _default_runner(
    command: Sequence[str],
    *,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the cursor-agent CLI via subprocess."""
    return subprocess.run(  # noqa: S603,S607 - intentional CLI invocation
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


CURSOR_MODELS: List[ModelDescriptor] = [
    ModelDescriptor(
        id="cursor-default",
        display_name="Cursor Agent Default",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "default"},
    ),
    ModelDescriptor(
        id="cursor-fast",
        display_name="Cursor Agent Fast",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "fast"},
    ),
    ModelDescriptor(
        id="cursor-premium",
        display_name="Cursor Agent Premium",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "premium"},
    ),
]

CURSOR_METADATA = ProviderMetadata(
    provider_name="cursor-agent",
    models=tuple(CURSOR_MODELS),
    default_model="cursor-default",
    security_flags={"writes_allowed": False},
    extra={"cli": "cursor-agent", "command": "cursor-agent chat"},
)

_JSON_FLAG = "--json"


class CursorAgentProvider(ProviderContext):
    """ProviderContext implementation backed by cursor-agent."""

    def __init__(
        self,
        metadata: ProviderMetadata,
        hooks: ProviderHooks,
        *,
        model: Optional[str] = None,
        binary: Optional[str] = None,
        runner: Optional[RunnerProtocol] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ):
        super().__init__(metadata, hooks)
        self._runner = runner or _default_runner
        self._binary = binary or os.environ.get(CUSTOM_BINARY_ENV, DEFAULT_BINARY)
        self._env = env
        self._timeout = timeout or DEFAULT_TIMEOUT_SECONDS
        self._model = self._ensure_model(model or metadata.default_model or self._first_model_id())

    def _first_model_id(self) -> str:
        if not self.metadata.models:
            raise ProviderUnavailableError(
                "Cursor Agent metadata is missing model descriptors.",
                provider=self.metadata.provider_name,
            )
        return self.metadata.models[0].id

    def _ensure_model(self, candidate: str) -> str:
        available = {descriptor.id for descriptor in self.metadata.models}
        if candidate not in available:
            raise ProviderExecutionError(
                f"Unsupported Cursor Agent model '{candidate}'. Available: {', '.join(sorted(available))}",
                provider=self.metadata.provider_name,
            )
        return candidate

    def _build_command(self, request: GenerationRequest, model: str) -> List[str]:
        command = [self._binary, "chat", _JSON_FLAG]

        working_dir = (request.metadata or {}).get("working_directory") if request.metadata else None
        if working_dir:
            command.extend(["--working-directory", str(working_dir)])

        temperature = request.temperature if request.temperature is not None else DEFAULT_TEMPERATURE
        command.extend(["--temperature", str(temperature)])

        if request.max_tokens is not None:
            command.extend(["--max-tokens", str(int(request.max_tokens))])

        if model:
            command.extend(["--model", model])

        if request.system_prompt:
            command.extend(["--system", request.system_prompt])

        extra_flags = (request.metadata or {}).get("cursor_agent_flags")
        if isinstance(extra_flags, list):
            for flag in extra_flags:
                if isinstance(flag, str) and flag.strip():
                    command.append(flag.strip())

        prompt = request.prompt
        command.extend(["--prompt", prompt])
        return command

    def _run(
        self,
        command: Sequence[str],
        *,
        timeout: Optional[int],
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(command, timeout=timeout, env=self._env)
        except FileNotFoundError as exc:
            raise ProviderUnavailableError(
                f"Cursor Agent CLI '{self._binary}' is not available on PATH.",
                provider=self.metadata.provider_name,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderTimeoutError(str(exc), provider=self.metadata.provider_name) from exc

    def _cursor_json_flag_error(self, result: subprocess.CompletedProcess[str]) -> bool:
        if result.returncode == 0:
            return False
        diagnostics = " ".join(
            part for part in [(result.stderr or ""), (result.stdout or "")]
        ).lower()
        if _JSON_FLAG not in diagnostics:
            return False
        indicators = [
            "unrecognized option",
            "unknown option",
            "unrecognized argument",
            "unknown argument",
            "no such option",
            "does not support",
            "not support",
            "flag provided but not defined",
            "invalid option",
        ]
        return any(indicator in diagnostics for indicator in indicators)

    def _remove_json_flag(self, command: Sequence[str]) -> List[str]:
        removed = False
        result: List[str] = []
        for token in command:
            if token == _JSON_FLAG and not removed:
                removed = True
                continue
            result.append(token)
        return result

    def _run_with_retry(
        self,
        command: Sequence[str],
        timeout: Optional[int],
    ) -> Tuple[subprocess.CompletedProcess[str], bool]:
        completed = self._run(command, timeout=timeout)
        if completed.returncode == 0:
            return completed, True
        if self._cursor_json_flag_error(completed):
            retried_command = self._remove_json_flag(command)
            retry_completed = self._run(retried_command, timeout=timeout)
            if retry_completed.returncode == 0:
                return retry_completed, False
            raise ProviderExecutionError(
                f"Cursor Agent CLI rejected {_JSON_FLAG} and retry failed: "
                f"{(retry_completed.stderr or '').strip() or 'unknown error'}",
                provider=self.metadata.provider_name,
            )
        raise ProviderExecutionError(
            f"Cursor Agent CLI exited with code {completed.returncode}: "
            f"{(completed.stderr or '').strip() or 'no stderr'}",
            provider=self.metadata.provider_name,
        )

    def _parse_json_payload(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()
        if not text:
            raise ProviderExecutionError(
                "Cursor Agent CLI returned empty output.",
                provider=self.metadata.provider_name,
            )
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError(
                f"Cursor Agent CLI returned invalid JSON: {exc}",
                provider=self.metadata.provider_name,
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderExecutionError(
                "Cursor Agent CLI returned an unexpected payload.",
                provider=self.metadata.provider_name,
            )
        return payload

    def _usage_from_payload(self, payload: Dict[str, Any]) -> TokenUsage:
        usage = payload.get("usage") or {}
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
            metadata={"raw_usage": usage} if usage else {},
        )

    def _emit_stream_if_requested(self, content: str, *, stream: bool) -> None:
        if not stream or not content:
            return
        self._emit_stream_chunk(StreamChunk(content=content, index=0))

    def _execute(self, request: GenerationRequest) -> GenerationResult:
        if request.attachments:
            raise ProviderExecutionError(
                "Cursor Agent CLI does not support attachments.",
                provider=self.metadata.provider_name,
            )

        model = self._ensure_model(
            str(request.metadata.get("model")) if request.metadata and "model" in request.metadata else self._model
        )

        command = self._build_command(request, model)
        timeout = request.timeout or self._timeout
        completed, json_mode = self._run_with_retry(command, timeout)

        if json_mode:
            payload = self._parse_json_payload(completed.stdout)
            content = str(payload.get("content") or "").strip()
            if not content and payload.get("messages"):
                content = " ".join(
                    str(message.get("content") or "")
                    for message in payload["messages"]
                    if isinstance(message, dict)
                ).strip()
            if not content:
                content = (payload.get("raw") or "").strip()
            usage = self._usage_from_payload(payload)
            self._emit_stream_if_requested(content, stream=request.stream)
            return GenerationResult(
                content=content,
                model_fqn=f"{self.metadata.provider_name}:{payload.get('model') or model}",
                status=ProviderStatus.SUCCESS,
                usage=usage,
                stderr=(completed.stderr or "").strip() or None,
                raw_payload=payload,
            )

        # Fallback mode (no JSON flag)
        content = completed.stdout.strip()
        self._emit_stream_if_requested(content, stream=request.stream)
        metadata = {
            "raw_text": content,
            "json_mode": False,
        }
        return GenerationResult(
            content=content,
            model_fqn=f"{self.metadata.provider_name}:{model}",
            status=ProviderStatus.SUCCESS,
            usage=TokenUsage(),
            stderr=(completed.stderr or "").strip() or None,
            raw_payload=metadata,
        )


def is_cursor_agent_available() -> bool:
    """Cursor Agent CLI availability check."""
    return detect_provider_availability("cursor-agent")


def create_provider(
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
    dependencies: Optional[Dict[str, object]] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> CursorAgentProvider:
    """
    Factory used by the provider registry.
    """
    dependencies = dependencies or {}
    overrides = overrides or {}
    runner = dependencies.get("runner")
    env = dependencies.get("env")
    binary = overrides.get("binary") or dependencies.get("binary")
    timeout = overrides.get("timeout")
    selected_model = overrides.get("model") if overrides.get("model") else model

    return CursorAgentProvider(
        metadata=CURSOR_METADATA,
        hooks=hooks,
        model=selected_model,
        binary=binary,  # type: ignore[arg-type]
        runner=runner if runner is not None else None,  # type: ignore[arg-type]
        env=env if env is not None else None,  # type: ignore[arg-type]
        timeout=timeout if timeout is not None else None,
    )


register_provider(
    "cursor-agent",
    factory=create_provider,
    metadata=CURSOR_METADATA,
    availability_check=is_cursor_agent_available,
    description="Cursor Agent CLI adapter",
    tags=("cli", "text", "function_calling"),
    replace=True,
)


__all__ = [
    "CursorAgentProvider",
    "create_provider",
    "is_cursor_agent_available",
    "CURSOR_METADATA",
]
