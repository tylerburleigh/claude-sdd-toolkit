"""
Cursor Agent CLI provider implementation.

Adapts the `cursor-agent` command-line tool to the ProviderContext contract,
including availability checks, streaming normalization, and response parsing.
Enforces read-only restrictions via Cursor's permission configuration system.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
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
from .detectors import detect_provider_availability
from .registry import register_provider

DEFAULT_BINARY = "cursor-agent"
DEFAULT_TIMEOUT_SECONDS = 360
AVAILABILITY_OVERRIDE_ENV = "CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE"
CUSTOM_BINARY_ENV = "CURSOR_AGENT_CLI_BINARY"

# Read-only tools allowed for Cursor Agent
# Note: Cursor Agent uses config files for permissions, not command-line flags
# These lists serve as documentation and validation
ALLOWED_TOOLS = [
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

    # Shell commands - text processing
    "Shell(wc)",
    "Shell(cut)",
    "Shell(paste)",
    "Shell(column)",
    "Shell(sort)",
    "Shell(uniq)",

    # Shell commands - data formats
    "Shell(jq)",
    "Shell(yq)",

    # Shell commands - file analysis
    "Shell(file)",
    "Shell(stat)",
    "Shell(du)",
    "Shell(df)",

    # Shell commands - checksums/hashing
    "Shell(md5sum)",
    "Shell(shasum)",
    "Shell(sha256sum)",
    "Shell(sha512sum)",
]

# Tools that should be explicitly blocked
DISALLOWED_TOOLS = [
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

    # File modifications
    "Shell(touch)",
    "Shell(mkdir)",
    "Shell(mv)",
    "Shell(cp)",
    "Shell(chmod)",
    "Shell(chown)",
    "Shell(sed)",
    "Shell(awk)",

    # Git write operations
    "Shell(git add)",
    "Shell(git commit)",
    "Shell(git push)",
    "Shell(git pull)",
    "Shell(git merge)",
    "Shell(git rebase)",
    "Shell(git reset)",
    "Shell(git checkout)",

    # Package installations
    "Shell(npm install)",
    "Shell(pip install)",
    "Shell(apt install)",
    "Shell(brew install)",

    # System operations
    "Shell(sudo)",
    "Shell(halt)",
    "Shell(reboot)",
    "Shell(shutdown)",
]

# System prompt warning about Cursor Agent security limitations
SHELL_COMMAND_WARNING = """
IMPORTANT SECURITY NOTE: This session is running in read-only mode with the following restrictions:
1. File write operations (Write, Edit, Patch, Delete) are disabled via Cursor Agent config
2. Only approved read-only shell commands are permitted
3. Cursor Agent's security model is weaker than other CLIs - be cautious
4. Configuration is enforced via ~/.cursor/cli-config.json (original config backed up and restored automatically)
5. Note: This uses allowlist mode for maximum security - only explicitly allowed operations are permitted
"""


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
        id="composer-1",
        display_name="Composer-1",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "default"},
    ),
    ModelDescriptor(
        id="gpt-5.1-codex",
        display_name="GPT-5.1 Codex",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.STREAMING,
        },
        routing_hints={"tier": "codex"},
    ),
]

CURSOR_METADATA = ProviderMetadata(
    provider_name="cursor-agent",
    models=tuple(CURSOR_MODELS),
    default_model="composer-1",
    security_flags={"writes_allowed": False, "read_only": True},
    extra={
        "cli": "cursor-agent",
        "command": "cursor-agent --print --output-format json",
        "allowed_tools": ALLOWED_TOOLS,
        "config_based_permissions": True,
    },
)


class CursorAgentProvider(ProviderContext):
    """ProviderContext implementation backed by cursor-agent with read-only restrictions."""

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
        self._model = self._ensure_model(
            model or metadata.default_model or self._first_model_id()
        )
        self._config_backup_path: Optional[Path] = None
        self._original_config_existed: bool = False
        self._cleanup_done: bool = False

    def __del__(self) -> None:
        """Clean up temporary config directory on provider destruction."""
        self._cleanup_config_file()

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

    def _create_readonly_config(self) -> Path:
        """
        Backup and replace ~/.cursor/cli-config.json with read-only permissions.

        Cursor Agent uses a permission configuration system with the format:
        - {"allow": "Read(**)"}: Allow read access to all paths
        - {"allow": "Shell(command)"}: Allow specific shell commands
        - {"deny": "Write(**)"}: Deny write access

        Returns:
            Path to the HOME .cursor directory

        Note:
            This method backs up the original config to a unique timestamped file,
            then writes a read-only config. The backup is restored by _cleanup_config_file().
        """
        # Get HOME .cursor config path
        cursor_dir = Path.home() / ".cursor"
        config_path = cursor_dir / "cli-config.json"

        # Create unique backup path for thread-safety
        backup_suffix = f".sdd-backup.{os.getpid()}.{int(time.time())}"
        backup_path = Path(str(config_path) + backup_suffix)

        # Backup original config if it exists
        self._original_config_existed = config_path.exists()
        if self._original_config_existed:
            shutil.copy2(config_path, backup_path)
            self._config_backup_path = backup_path

        # Build permission list in new format
        permissions = []

        # Allow read access to all paths
        permissions.append({"allow": "Read(**)"})
        permissions.append({"allow": "Grep(**)"})
        permissions.append({"allow": "Glob(**)"})
        permissions.append({"allow": "List(**)"})

        # Add allowed shell commands (extract command names from ALLOWED_TOOLS)
        for tool in ALLOWED_TOOLS:
            if tool.startswith("Shell(") and tool.endswith(")"):
                # Extract command: "Shell(git log)" -> "git log"
                command = tool[6:-1]
                # Cursor Agent Shell permissions use first token only
                # "git log" becomes "git" in the config
                base_command = command.split()[0]
                permissions.append({"allow": f"Shell({base_command})"})

        # Create read-only config file
        cursor_dir.mkdir(parents=True, exist_ok=True)
        config_data = {
            "permissions": permissions,
            "description": "Read-only mode enforced by claude-sdd-toolkit",
            "approvalMode": "allowlist",  # Use allowlist mode for security
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        return cursor_dir

    def _cleanup_config_file(self) -> None:
        """Restore original ~/.cursor/cli-config.json from backup."""
        # Prevent double-cleanup (e.g., from finally block + __del__)
        if hasattr(self, '_cleanup_done') and self._cleanup_done:
            return

        cursor_dir = Path.home() / ".cursor"
        config_path = cursor_dir / "cli-config.json"

        try:
            # Restore original config from backup if it existed
            if (
                hasattr(self, '_config_backup_path')
                and self._config_backup_path is not None
                and self._config_backup_path.exists()
            ):
                shutil.move(self._config_backup_path, config_path)
            elif (
                hasattr(self, '_original_config_existed')
                and not self._original_config_existed
                and config_path.exists()
            ):
                # No original config existed - remove our temporary one
                config_path.unlink()

            # Clean up any leftover backup files
            if (
                hasattr(self, '_config_backup_path')
                and self._config_backup_path is not None
                and self._config_backup_path.exists()
            ):
                self._config_backup_path.unlink()

            # Clean up any .bad files created by cursor-agent CLI
            bad_config_path = Path(str(config_path) + ".bad")
            if bad_config_path.exists():
                bad_config_path.unlink()

        except (OSError, FileNotFoundError):
            # Files already removed or don't exist, ignore
            pass
        finally:
            # Mark cleanup as done to prevent double-cleanup
            if hasattr(self, '_cleanup_done'):
                self._cleanup_done = True
            if hasattr(self, '_config_backup_path'):
                self._config_backup_path = None
            if hasattr(self, '_original_config_existed'):
                self._original_config_existed = False

    def _build_command(
        self,
        request: GenerationRequest,
        model: str,
    ) -> List[str]:
        """
        Assemble the cursor-agent CLI invocation with read-only config.

        Args:
            request: Generation request
            model: Model ID to use

        Note:
            Config is read from ~/.cursor/cli-config.json (managed by _create_readonly_config).
            Uses --print mode for non-interactive execution with JSON output.
        """
        # cursor-agent in headless mode: --print --output-format json
        command = [self._binary, "--print", "--output-format", "json"]

        if model:
            command.extend(["--model", model])

        # Note: cursor-agent doesn't support --temperature or --max-tokens in --print mode
        # These flags are silently ignored if provided

        extra_flags = (request.metadata or {}).get("cursor_agent_flags")
        if isinstance(extra_flags, list):
            for flag in extra_flags:
                if isinstance(flag, str) and flag.strip():
                    command.append(flag.strip())

        # Prompt is passed as positional argument (not --prompt flag in --print mode)
        # Build full prompt with system context
        full_prompt = request.prompt
        if request.system_prompt:
            full_prompt = f"{request.system_prompt.strip()}\n\n{SHELL_COMMAND_WARNING.strip()}\n\n{request.prompt}"
        else:
            full_prompt = f"{SHELL_COMMAND_WARNING.strip()}\n\n{request.prompt}"

        command.append(full_prompt)
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
            raise ProviderTimeoutError(
                str(exc), provider=self.metadata.provider_name
            ) from exc

    def _run_with_retry(
        self,
        command: Sequence[str],
        timeout: Optional[int],
    ) -> Tuple[subprocess.CompletedProcess[str], bool]:
        """
        Execute the command and retry without --output-format json when the CLI lacks support.
        """
        completed = self._run(command, timeout=timeout)
        if completed.returncode == 0:
            return completed, True

        stderr_text = (completed.stderr or "").lower()
        # Check if --output-format flag is in command
        has_json_flag = "--output-format" in command
        if has_json_flag and any(
            phrase in stderr_text for phrase in ("unknown option", "unrecognized option")
        ):
            # Remove --output-format json from command for retry
            retry_command = []
            skip_next = False
            for i, part in enumerate(command):
                if skip_next:
                    skip_next = False
                    continue
                if part == "--output-format":
                    skip_next = True  # Skip next arg (the "json" value)
                    continue
                retry_command.append(part)

            retry_process = self._run(retry_command, timeout=timeout)
            if retry_process.returncode == 0:
                return retry_process, False

            stderr_text = (retry_process.stderr or stderr_text).strip()
            raise ProviderExecutionError(
                f"Cursor Agent CLI exited with code {retry_process.returncode}: "
                f"{stderr_text or 'no stderr'}",
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
            input_tokens=int(
                usage.get("input_tokens") or usage.get("prompt_tokens") or 0
            ),
            output_tokens=int(
                usage.get("output_tokens") or usage.get("completion_tokens") or 0
            ),
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
            str(request.metadata.get("model"))
            if request.metadata and "model" in request.metadata
            else self._model
        )

        # Backup and replace HOME config with read-only version
        self._create_readonly_config()

        try:
            # Build command (config is read from ~/.cursor/cli-config.json)
            command = self._build_command(request, model)
            timeout = request.timeout or self._timeout
            completed, json_mode = self._run_with_retry(command, timeout)
        finally:
            # Always restore original config, even if command fails
            self._cleanup_config_file()

        if json_mode:
            payload = self._parse_json_payload(completed.stdout)
            # cursor-agent returns content in "result" field
            content = str(payload.get("result") or payload.get("content") or "").strip()
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
    description="Cursor Agent CLI adapter with read-only restrictions via config files",
    tags=("cli", "text", "function_calling", "read-only"),
    replace=True,
)


__all__ = [
    "CursorAgentProvider",
    "create_provider",
    "is_cursor_agent_available",
    "CURSOR_METADATA",
]
