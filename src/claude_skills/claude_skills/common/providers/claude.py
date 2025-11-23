"""
Claude CLI provider implementation.

Bridges the `claude` command-line interface to the ProviderContext contract by
handling availability checks, safe command construction, response parsing, and
token usage normalization. Restricts to read-only operations for security.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Sequence, Protocol

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

DEFAULT_BINARY = "claude"
DEFAULT_TIMEOUT_SECONDS = 360
AVAILABILITY_OVERRIDE_ENV = "CLAUDE_CLI_AVAILABLE_OVERRIDE"
CUSTOM_BINARY_ENV = "CLAUDE_CLI_BINARY"

# Read-only tools allowed for Claude provider
# Core tools
ALLOWED_TOOLS = [
    # File operations (read-only)
    "Read",
    "Grep",
    "Glob",

    # Task delegation
    "Task",

    # Bash commands - file viewing
    "Bash(cat)",
    "Bash(head:*)",
    "Bash(tail:*)",
    "Bash(bat:*)",

    # Bash commands - directory listing/navigation
    "Bash(ls:*)",
    "Bash(tree:*)",
    "Bash(pwd)",
    "Bash(which:*)",
    "Bash(whereis:*)",

    # Bash commands - search/find
    "Bash(grep:*)",
    "Bash(rg:*)",
    "Bash(ag:*)",
    "Bash(find:*)",
    "Bash(fd:*)",

    # Bash commands - git operations (read-only)
    "Bash(git log:*)",
    "Bash(git show:*)",
    "Bash(git diff:*)",
    "Bash(git status:*)",
    "Bash(git grep:*)",
    "Bash(git blame:*)",
    "Bash(git branch:*)",
    "Bash(git rev-parse:*)",
    "Bash(git describe:*)",
    "Bash(git ls-tree:*)",

    # Bash commands - text processing
    "Bash(wc:*)",
    "Bash(cut:*)",
    "Bash(paste:*)",
    "Bash(column:*)",
    "Bash(sort:*)",
    "Bash(uniq:*)",

    # Bash commands - data formats
    "Bash(jq:*)",
    "Bash(yq:*)",

    # Bash commands - file analysis
    "Bash(file:*)",
    "Bash(stat:*)",
    "Bash(du:*)",
    "Bash(df:*)",

    # Bash commands - checksums/hashing
    "Bash(md5sum:*)",
    "Bash(shasum:*)",
    "Bash(sha256sum:*)",
    "Bash(sha512sum:*)",
]

# Tools that should be explicitly blocked
DISALLOWED_TOOLS = [
    "Write",
    "Edit",

    # Web operations (data exfiltration risk)
    "WebSearch",
    "WebFetch",

    # Dangerous file operations
    "Bash(rm:*)",
    "Bash(rmdir:*)",
    "Bash(dd:*)",
    "Bash(mkfs:*)",
    "Bash(fdisk:*)",

    # File modifications
    "Bash(touch:*)",
    "Bash(mkdir:*)",
    "Bash(mv:*)",
    "Bash(cp:*)",
    "Bash(chmod:*)",
    "Bash(chown:*)",
    "Bash(sed:*)",
    "Bash(awk:*)",

    # Git write operations
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git push:*)",
    "Bash(git pull:*)",
    "Bash(git merge:*)",
    "Bash(git rebase:*)",
    "Bash(git reset:*)",
    "Bash(git checkout:*)",

    # Package installations
    "Bash(npm install:*)",
    "Bash(pip install:*)",
    "Bash(apt install:*)",
    "Bash(brew install:*)",

    # System operations
    "Bash(sudo:*)",
    "Bash(halt:*)",
    "Bash(reboot:*)",
    "Bash(shutdown:*)",
]

# System prompt warning about shell command limitations
SHELL_COMMAND_WARNING = """
IMPORTANT SECURITY NOTE: When using shell commands, be aware of the following restrictions:
1. Only specific read-only commands are allowed (cat, grep, git log, etc.)
2. Write operations, file modifications, and destructive commands are blocked
3. Avoid using piped commands as they may bypass some security checks
4. Use sequential commands or alternative approaches when possible
"""


class RunnerProtocol(Protocol):
    """Callable signature used for executing Claude CLI commands."""

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
    """Invoke the Claude CLI via subprocess."""
    return subprocess.run(  # noqa: S603,S607 - intentional CLI invocation
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


CLAUDE_MODELS: List[ModelDescriptor] = [
    ModelDescriptor(
        id="sonnet",
        display_name="Sonnet 4.5",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
            ProviderCapability.VISION,
            ProviderCapability.THINKING,
        },
        routing_hints={"tier": "default", "description": "Smartest model for daily use"},
    ),
    ModelDescriptor(
        id="haiku",
        display_name="Haiku 4.5",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "fast", "description": "Fastest model for simple tasks"},
    ),
]

CLAUDE_METADATA = ProviderMetadata(
    provider_name="claude",
    models=tuple(CLAUDE_MODELS),
    default_model="sonnet",
    security_flags={"writes_allowed": False, "read_only": True},
    extra={"cli": "claude", "output_format": "json", "allowed_tools": ALLOWED_TOOLS},
)


class ClaudeProvider(ProviderContext):
    """ProviderContext implementation backed by the Claude CLI with read-only restrictions."""

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
                "Claude provider metadata is missing model descriptors.",
                provider=self.metadata.provider_name,
            )
        return self.metadata.models[0].id

    def _ensure_model(self, candidate: str) -> str:
        available = {descriptor.id for descriptor in self.metadata.models}
        if candidate not in available:
            raise ProviderExecutionError(
                f"Unsupported Claude model '{candidate}'. Available: {', '.join(sorted(available))}",
                provider=self.metadata.provider_name,
            )
        return candidate

    def _validate_request(self, request: GenerationRequest) -> None:
        unsupported: List[str] = []
        # Note: Claude CLI may not support these parameters via flags
        if request.temperature is not None:
            unsupported.append("temperature (use model defaults)")
        if request.max_tokens is not None:
            unsupported.append("max_tokens (use model defaults)")
        if request.continuation_id:
            unsupported.append("continuation_id")
        if request.attachments:
            unsupported.append("attachments")
        if unsupported:
            raise ProviderExecutionError(
                f"Claude CLI does not support: {', '.join(unsupported)}",
                provider=self.metadata.provider_name,
            )

    def _build_command(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> List[str]:
        """
        Build Claude CLI command with read-only tool restrictions.

        Command structure:
            claude --print [prompt] --output-format json --allowed-tools Read Grep ... --disallowed-tools Write Edit Bash
        """
        command = [self._binary, "--print", prompt, "--output-format", "json"]

        # Add read-only tool restrictions
        command.extend(["--allowed-tools"] + ALLOWED_TOOLS)
        command.extend(["--disallowed-tools"] + DISALLOWED_TOOLS)

        # Build system prompt with security warning
        full_system_prompt = system_prompt or ""
        if full_system_prompt:
            full_system_prompt = f"{full_system_prompt.strip()}\n\n{SHELL_COMMAND_WARNING.strip()}"
        else:
            full_system_prompt = SHELL_COMMAND_WARNING.strip()

        # Add system prompt
        command.extend(["--system-prompt", full_system_prompt])

        # Add model if specified and not default
        if model and model != self.metadata.default_model:
            command.extend(["--model", model])

        return command

    def _run(self, command: Sequence[str], timeout: Optional[int]) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(command, timeout=timeout, env=self._env)
        except FileNotFoundError as exc:
            raise ProviderUnavailableError(
                f"Claude CLI '{self._binary}' is not available on PATH.",
                provider=self.metadata.provider_name,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderTimeoutError(str(exc), provider=self.metadata.provider_name) from exc

    def _parse_output(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()
        if not text:
            raise ProviderExecutionError(
                "Claude CLI returned empty output.",
                provider=self.metadata.provider_name,
            )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError(
                f"Claude CLI returned invalid JSON: {exc}",
                provider=self.metadata.provider_name,
            ) from exc

    def _extract_usage(self, payload: Dict[str, Any]) -> TokenUsage:
        """
        Extract token usage from Claude CLI JSON response.

        Expected structure:
        {
            "usage": {"input_tokens": 10, "output_tokens": 50, ...},
            "modelUsage": {"claude-sonnet-4-5-20250929": {...}},
            ...
        }
        """
        usage = payload.get("usage") or {}
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            cached_input_tokens=int(usage.get("cached_input_tokens") or 0),
            total_tokens=int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0),
            metadata={
                "duration_ms": payload.get("duration_ms"),
                "total_cost_usd": payload.get("total_cost_usd"),
                "model_usage": payload.get("modelUsage"),
            },
        )

    def _resolve_model(self, request: GenerationRequest) -> str:
        model_override = request.metadata.get("model") if request.metadata else None
        if model_override:
            return self._ensure_model(str(model_override))
        return self._model

    def _emit_stream_if_requested(self, content: str, *, stream: bool) -> None:
        if not stream or not content:
            return
        self._emit_stream_chunk(StreamChunk(content=content, index=0))

    def _execute(self, request: GenerationRequest) -> GenerationResult:
        self._validate_request(request)
        model = self._resolve_model(request)
        command = self._build_command(
            model,
            request.prompt,
            system_prompt=request.system_prompt
        )
        timeout = request.timeout or self._timeout
        completed = self._run(command, timeout=timeout)

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise ProviderExecutionError(
                f"Claude CLI exited with code {completed.returncode}: {stderr or 'no stderr'}",
                provider=self.metadata.provider_name,
            )

        payload = self._parse_output(completed.stdout)

        # Extract content from "result" field (as per claude-model-chorus pattern)
        content = str(payload.get("result") or payload.get("content") or "").strip()

        # Extract model from modelUsage if available
        model_usage = payload.get("modelUsage") or {}
        reported_model = list(model_usage.keys())[0] if model_usage else model

        usage = self._extract_usage(payload)

        self._emit_stream_if_requested(content, stream=request.stream)

        return GenerationResult(
            content=content,
            model_fqn=f"{self.metadata.provider_name}:{reported_model}",
            status=ProviderStatus.SUCCESS,
            usage=usage,
            stderr=(completed.stderr or "").strip() or None,
            raw_payload=payload,
        )


def is_claude_available() -> bool:
    """Claude CLI availability check."""
    return detect_provider_availability("claude")


def create_provider(
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
    dependencies: Optional[Dict[str, object]] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> ClaudeProvider:
    """
    Factory used by the provider registry.

    dependencies/overrides allow callers (or tests) to inject runner/env/binary.
    """
    dependencies = dependencies or {}
    overrides = overrides or {}
    runner = dependencies.get("runner")
    env = dependencies.get("env")
    binary = overrides.get("binary") or dependencies.get("binary")
    timeout = overrides.get("timeout")
    selected_model = overrides.get("model") if overrides.get("model") else model

    return ClaudeProvider(
        metadata=CLAUDE_METADATA,
        hooks=hooks,
        model=selected_model,
        binary=binary,  # type: ignore[arg-type]
        runner=runner if runner is not None else None,  # type: ignore[arg-type]
        env=env if env is not None else None,  # type: ignore[arg-type]
        timeout=timeout if timeout is not None else None,
    )


# Register the provider immediately so consumers can resolve it by id.
register_provider(
    "claude",
    factory=create_provider,
    metadata=CLAUDE_METADATA,
    availability_check=is_claude_available,
    description="Anthropic Claude CLI adapter with read-only tool restrictions",
    tags=("cli", "text", "vision", "thinking", "read-only"),
    replace=True,
)


__all__ = [
    "ClaudeProvider",
    "create_provider",
    "is_claude_available",
    "CLAUDE_METADATA",
]
