"""
Codex CLI provider implementation.

Wraps the `codex exec` command to satisfy the ProviderContext contract,
including availability checks, request validation, JSONL parsing, and
token usage normalization. Enforces read-only restrictions via native
OS-level sandboxing (--sandbox read-only flag).
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

DEFAULT_BINARY = "codex"
DEFAULT_TIMEOUT_SECONDS = 360
AVAILABILITY_OVERRIDE_ENV = "CODEX_CLI_AVAILABLE_OVERRIDE"
CUSTOM_BINARY_ENV = "CODEX_CLI_BINARY"

# Read-only operations allowed by Codex --sandbox read-only mode
# Note: These are enforced natively by OS-level sandboxing, not by this wrapper
# macOS: Seatbelt | Linux: Landlock + seccomp | Windows: Restricted Token
SANDBOX_ALLOWED_OPERATIONS = [
    # File operations (read-only)
    "Read",
    "Grep",
    "Glob",
    "List",

    # Task delegation
    "Task",

    # Shell commands - file viewing
    "Shell(cat)",
    "Shell(head)",
    "Shell(tail)",
    "Shell(bat)",
    "Shell(less)",
    "Shell(more)",

    # Shell commands - directory listing/navigation
    "Shell(ls)",
    "Shell(tree)",
    "Shell(pwd)",
    "Shell(which)",
    "Shell(whereis)",

    # Shell commands - search/find
    "Shell(grep)",
    "Shell(rg)",
    "Shell(ag)",
    "Shell(find)",
    "Shell(fd)",
    "Shell(locate)",

    # Shell commands - git operations (read-only)
    "Shell(git log)",
    "Shell(git show)",
    "Shell(git diff)",
    "Shell(git status)",
    "Shell(git grep)",
    "Shell(git blame)",
    "Shell(git branch)",
    "Shell(git rev-parse)",
    "Shell(git describe)",
    "Shell(git ls-tree)",
    "Shell(git ls-files)",

    # Shell commands - text processing
    "Shell(wc)",
    "Shell(cut)",
    "Shell(paste)",
    "Shell(column)",
    "Shell(sort)",
    "Shell(uniq)",
    "Shell(diff)",

    # Shell commands - data formats
    "Shell(jq)",
    "Shell(yq)",
    "Shell(xmllint)",

    # Shell commands - file analysis
    "Shell(file)",
    "Shell(stat)",
    "Shell(du)",
    "Shell(df)",
    "Shell(lsof)",

    # Shell commands - checksums/hashing
    "Shell(md5sum)",
    "Shell(shasum)",
    "Shell(sha256sum)",
    "Shell(sha512sum)",
    "Shell(cksum)",

    # Shell commands - process inspection
    "Shell(ps)",
    "Shell(top)",
    "Shell(htop)",

    # Shell commands - system information
    "Shell(uname)",
    "Shell(hostname)",
    "Shell(whoami)",
    "Shell(id)",
    "Shell(date)",
    "Shell(uptime)",
]

# Operations blocked by Codex --sandbox read-only mode
SANDBOX_BLOCKED_OPERATIONS = [
    "Write",
    "Edit",
    "Patch",
    "Delete",

    # Web operations (data exfiltration risk)
    "WebFetch",

    # Dangerous file operations
    "Shell(rm)",
    "Shell(rmdir)",
    "Shell(dd)",
    "Shell(mkfs)",
    "Shell(fdisk)",
    "Shell(shred)",

    # File modifications
    "Shell(touch)",
    "Shell(mkdir)",
    "Shell(mv)",
    "Shell(cp)",
    "Shell(chmod)",
    "Shell(chown)",
    "Shell(chgrp)",
    "Shell(sed)",
    "Shell(awk)",
    "Shell(tee)",

    # Git write operations
    "Shell(git add)",
    "Shell(git commit)",
    "Shell(git push)",
    "Shell(git pull)",
    "Shell(git merge)",
    "Shell(git rebase)",
    "Shell(git reset)",
    "Shell(git checkout)",
    "Shell(git stash)",
    "Shell(git cherry-pick)",

    # Package installations
    "Shell(npm install)",
    "Shell(pip install)",
    "Shell(apt install)",
    "Shell(apt-get install)",
    "Shell(brew install)",
    "Shell(yum install)",
    "Shell(dnf install)",
    "Shell(cargo install)",

    # System operations
    "Shell(sudo)",
    "Shell(su)",
    "Shell(halt)",
    "Shell(reboot)",
    "Shell(shutdown)",
    "Shell(systemctl)",
    "Shell(service)",

    # Network write operations
    "Shell(curl -X POST)",
    "Shell(curl -X PUT)",
    "Shell(curl -X DELETE)",
    "Shell(wget)",
    "Shell(scp)",
    "Shell(rsync)",
]

# System prompt warning about Codex sandbox restrictions
SANDBOX_WARNING = """
IMPORTANT SECURITY NOTE: This session runs with Codex CLI's native --sandbox read-only mode:
1. Native OS-level sandboxing enforced by the operating system:
   - macOS: Seatbelt sandbox policy
   - Linux: Landlock LSM + seccomp filters
   - Windows: Restricted token + job objects
2. Only read operations are permitted - writes are blocked at the OS level
3. Shell commands are restricted to read-only operations by the sandbox
4. The sandbox is enforced by the Codex CLI itself, not just tool filtering
5. This is the most robust security model - cannot be bypassed by piped commands or escapes
6. Attempts to write files or modify system state will be blocked by the OS
"""


class RunnerProtocol(Protocol):
    """Callable signature used for executing Codex CLI commands."""

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
    """Invoke the Codex CLI via subprocess."""
    return subprocess.run(  # noqa: S603,S607 - intentional CLI invocation
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


CODEX_MODELS: List[ModelDescriptor] = [
    ModelDescriptor(
        id="gpt-5.1-codex",
        display_name="GPT-5.1 Codex",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        },
        routing_hints={"tier": "primary", "optimized_for": "codex"},
    ),
    ModelDescriptor(
        id="gpt-5.1-codex-mini",
        display_name="GPT-5.1 Codex Mini",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        },
        routing_hints={"tier": "fast", "optimized_for": "codex"},
    ),
    ModelDescriptor(
        id="gpt-5.1",
        display_name="GPT-5.1",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
            ProviderCapability.FUNCTION_CALLING,
        },
        routing_hints={"tier": "general"},
    ),
]

CODEX_METADATA = ProviderMetadata(
    provider_name="codex",
    models=tuple(CODEX_MODELS),
    default_model="gpt-5.1-codex",
    security_flags={"writes_allowed": False, "read_only": True, "sandbox": "read-only"},
    extra={
        "cli": "codex",
        "command": "codex exec",
        "allowed_operations": SANDBOX_ALLOWED_OPERATIONS,
        "blocked_operations": SANDBOX_BLOCKED_OPERATIONS,
        "os_level_sandboxing": True,
    },
)


class CodexProvider(ProviderContext):
    """ProviderContext implementation backed by the Codex CLI with OS-level read-only sandboxing."""

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
                "Codex provider metadata is missing model descriptors.",
                provider=self.metadata.provider_name,
            )
        return self.metadata.models[0].id

    def _ensure_model(self, candidate: str) -> str:
        available = {descriptor.id for descriptor in self.metadata.models}
        if candidate not in available:
            raise ProviderExecutionError(
                f"Unsupported Codex model '{candidate}'. Available: {', '.join(sorted(available))}",
                provider=self.metadata.provider_name,
            )
        return candidate

    def _validate_request(self, request: GenerationRequest) -> None:
        unsupported: List[str] = []
        if request.temperature is not None:
            unsupported.append("temperature")
        if request.max_tokens is not None:
            unsupported.append("max_tokens")
        if request.continuation_id:
            unsupported.append("continuation_id")
        if unsupported:
            raise ProviderExecutionError(
                f"Codex CLI does not support: {', '.join(unsupported)}",
                provider=self.metadata.provider_name,
            )

    def _build_prompt(self, request: GenerationRequest) -> str:
        """
        Build prompt with sandbox security warning injected.

        Combines user system prompt + SANDBOX_WARNING + user prompt to ensure
        the AI is aware of the read-only sandbox restrictions.
        """
        parts = []

        # Add user system prompt if provided
        if request.system_prompt:
            parts.append(request.system_prompt.strip())

        # Add sandbox warning (always)
        parts.append(SANDBOX_WARNING.strip())

        # Add user prompt
        parts.append(request.prompt)

        return "\n\n".join(parts)

    def _normalize_attachment_paths(self, request: GenerationRequest) -> List[str]:
        attachments = []
        for entry in request.attachments:
            if isinstance(entry, str) and entry.strip():
                attachments.append(entry.strip())
        return attachments

    def _build_command(self, model: str, prompt: str, attachments: List[str]) -> List[str]:
        # Note: codex CLI requires --json flag for JSONL output (non-interactive mode)
        command = [self._binary, "exec", "--sandbox", "read-only", "--json"]
        if model:
            command.extend(["-m", model])
        for path in attachments:
            command.extend(["--image", path])
        command.append(prompt)
        return command

    def _run(self, command: Sequence[str], timeout: Optional[int]) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(command, timeout=timeout, env=self._env)
        except FileNotFoundError as exc:
            raise ProviderUnavailableError(
                f"Codex CLI '{self._binary}' is not available on PATH.",
                provider=self.metadata.provider_name,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderTimeoutError(str(exc), provider=self.metadata.provider_name) from exc

    def _flatten_text(self, payload: Any) -> str:
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            pieces: List[str] = []
            for key in ("text", "content", "value"):
                value = payload.get(key)
                if value:
                    pieces.append(self._flatten_text(value))
            if "parts" in payload and isinstance(payload["parts"], list):
                pieces.extend(self._flatten_text(part) for part in payload["parts"])
            if "messages" in payload and isinstance(payload["messages"], list):
                pieces.extend(self._flatten_text(message) for message in payload["messages"])
            return "".join(pieces)
        if isinstance(payload, list):
            return "".join(self._flatten_text(item) for item in payload)
        return ""

    def _extract_agent_text(self, payload: Dict[str, Any]) -> str:
        # Check if this is an item with type="agent_message" or type="reasoning"
        item_type = payload.get("type")
        if item_type in ("agent_message", "reasoning"):
            text = self._flatten_text(payload)
            if text:
                return text

        # Check for specific message keys
        for key in ("agent_message", "message", "delta", "content"):
            if key in payload:
                text = self._flatten_text(payload[key])
                if text:
                    return text

        # Recurse into nested item
        item = payload.get("item")
        if isinstance(item, dict):
            return self._extract_agent_text(item)
        return ""

    def _token_usage_from_payload(self, payload: Dict[str, Any]) -> TokenUsage:
        usage = payload.get("usage") or payload.get("token_usage") or {}
        cached = usage.get("cached_input_tokens") or usage.get("cached_tokens") or 0
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
            cached_input_tokens=int(cached),
            total_tokens=int(usage.get("total_tokens") or 0),
            metadata={"usage_event": payload},
        )

    def _process_events(
        self,
        stdout: str,
        *,
        stream: bool,
    ) -> tuple[str, TokenUsage, Dict[str, Any], Optional[str]]:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if not lines:
            raise ProviderExecutionError(
                "Codex CLI returned empty output.",
                provider=self.metadata.provider_name,
            )

        events: List[Dict[str, Any]] = []
        final_content = ""
        usage = TokenUsage()
        thread_id: Optional[str] = None
        reported_model: Optional[str] = None
        stream_index = 0
        streamed_chunks: List[str] = []

        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProviderExecutionError(
                    f"Codex CLI emitted invalid JSON: {exc}",
                    provider=self.metadata.provider_name,
                ) from exc

            events.append(event)
            event_type = str(event.get("type") or event.get("event") or "").lower()

            if event_type == "thread.started":
                thread_id = (
                    event.get("thread_id")
                    or (event.get("thread") or {}).get("id")
                    or event.get("id")
                )
            elif event_type in {"item.delta", "response.delta"}:
                delta_text = self._extract_agent_text(event)
                if delta_text:
                    streamed_chunks.append(delta_text)
                    if stream:
                        self._emit_stream_chunk(
                            StreamChunk(content=delta_text, index=stream_index)
                        )
                        stream_index += 1
            elif event_type in {"item.completed", "response.completed"}:
                completed_text = self._extract_agent_text(event)
                if completed_text:
                    final_content = completed_text
            elif event_type in {"turn.completed", "usage"}:
                usage = self._token_usage_from_payload(event)
            if reported_model is None:
                reported_model = (
                    event.get("model")
                    or (event.get("item") or {}).get("model")
                    or (event.get("agent_message") or {}).get("model")
                )

        if not final_content:
            if streamed_chunks:
                final_content = "".join(streamed_chunks)
            else:
                raise ProviderExecutionError(
                    "Codex CLI did not emit a completion event.",
                    provider=self.metadata.provider_name,
                )

        metadata: Dict[str, Any] = {}
        if thread_id:
            metadata["thread_id"] = thread_id
        metadata["events"] = events

        return final_content, usage, metadata, reported_model

    def _execute(self, request: GenerationRequest) -> GenerationResult:
        self._validate_request(request)
        model = self._ensure_model(
            str(request.metadata.get("model")) if request.metadata and "model" in request.metadata else self._model
        )
        prompt = self._build_prompt(request)
        attachments = self._normalize_attachment_paths(request)
        command = self._build_command(model, prompt, attachments)
        timeout = request.timeout or self._timeout
        completed = self._run(command, timeout=timeout)

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise ProviderExecutionError(
                f"Codex CLI exited with code {completed.returncode}: {stderr or 'no stderr'}",
                provider=self.metadata.provider_name,
            )

        content, usage, metadata, reported_model = self._process_events(
            completed.stdout,
            stream=request.stream,
        )

        return GenerationResult(
            content=content,
            model_fqn=f"{self.metadata.provider_name}:{reported_model or model}",
            status=ProviderStatus.SUCCESS,
            usage=usage,
            stderr=(completed.stderr or "").strip() or None,
            raw_payload=metadata,
        )


def is_codex_available() -> bool:
    """Codex CLI availability check."""
    return detect_provider_availability("codex")


def create_provider(
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
    dependencies: Optional[Dict[str, object]] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> CodexProvider:
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

    return CodexProvider(
        metadata=CODEX_METADATA,
        hooks=hooks,
        model=selected_model,
        binary=binary,  # type: ignore[arg-type]
        runner=runner if runner is not None else None,  # type: ignore[arg-type]
        env=env if env is not None else None,  # type: ignore[arg-type]
        timeout=timeout if timeout is not None else None,
    )


register_provider(
    "codex",
    factory=create_provider,
    metadata=CODEX_METADATA,
    availability_check=is_codex_available,
    description="OpenAI Codex CLI adapter with native OS-level read-only sandboxing",
    tags=("cli", "text", "function_calling", "read-only", "sandboxed"),
    replace=True,
)


__all__ = [
    "CodexProvider",
    "create_provider",
    "is_codex_available",
    "CODEX_METADATA",
]
