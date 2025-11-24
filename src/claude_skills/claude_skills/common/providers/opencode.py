"""
OpenCode AI provider implementation.

Bridges the OpenCode AI Node.js SDK wrapper to the ProviderContext contract by
handling availability checks, server management, wrapper script execution,
response parsing, and token usage normalization.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
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

DEFAULT_BINARY = "node"
DEFAULT_WRAPPER_SCRIPT = Path(__file__).parent / "opencode_wrapper.js"
DEFAULT_TIMEOUT_SECONDS = 360
DEFAULT_SERVER_URL = "http://localhost:4096"
SERVER_STARTUP_TIMEOUT = 30
AVAILABILITY_OVERRIDE_ENV = "OPENCODE_AVAILABLE_OVERRIDE"
CUSTOM_BINARY_ENV = "OPENCODE_BINARY"
CUSTOM_WRAPPER_ENV = "OPENCODE_WRAPPER_SCRIPT"

# Read-only tools configuration for OpenCode server
# Uses dual-layer protection: tool disabling + permission denial
READONLY_TOOLS_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "tools": {
        # Disable write operations
        "write": False,
        "edit": False,
        "patch": False,
        "todowrite": False,

        # Disable shell execution
        "bash": False,

        # Enable read operations
        "read": True,
        "grep": True,
        "glob": True,
        "list": True,
        "todoread": True,
        "task": True,

        # Disable web operations (data exfiltration risk)
        "webfetch": False,
    },
    "permission": {
        # Double-guard with permission denials
        "edit": "deny",
        "bash": "deny",
        "webfetch": "deny",
        "external_directory": "deny",
    },
}

# System prompt warning about tool limitations
SHELL_COMMAND_WARNING = """
IMPORTANT SECURITY NOTE: This session is running in read-only mode with the following restrictions:
1. File write operations (write, edit, patch) are disabled
2. Shell command execution (bash) is disabled
3. Web operations (webfetch) are disabled to prevent data exfiltration
4. Only read operations are available (read, grep, glob, list)
5. Attempts to modify files, execute commands, or access the web will be blocked by the server
"""


OPENCODE_MODELS: List[ModelDescriptor] = [
    ModelDescriptor(
        id="default",
        display_name="OpenCode AI (configurable via OpenCode settings)",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
        },
        routing_hints={
            "configurable": True,
            "source": "opencode config",
            "note": "Accepts any model ID - validated by opencode CLI",
        },
    ),
]

OPENCODE_METADATA = ProviderMetadata(
    provider_name="opencode",
    models=tuple(OPENCODE_MODELS),
    default_model="default",
    security_flags={"writes_allowed": False, "read_only": True},
    extra={
        "wrapper": "opencode_wrapper.js",
        "server_url": DEFAULT_SERVER_URL,
        "configurable": True,
        "readonly_config": READONLY_TOOLS_CONFIG,
    },
)


class RunnerProtocol(Protocol):
    """Callable signature used for executing Node.js wrapper commands."""

    def __call__(
        self,
        command: Sequence[str],
        *,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[str] = None,
    ) -> subprocess.CompletedProcess[str]:
        raise NotImplementedError


def _default_runner(
    command: Sequence[str],
    *,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    input_data: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the OpenCode wrapper via subprocess."""
    return subprocess.run(  # noqa: S603,S607 - intentional wrapper invocation
        list(command),
        capture_output=True,
        text=True,
        input=input_data,
        timeout=timeout,
        env=env,
        check=False,
    )


class OpenCodeProvider(ProviderContext):
    """ProviderContext implementation backed by the OpenCode AI wrapper."""

    def __init__(
        self,
        metadata: ProviderMetadata,
        hooks: ProviderHooks,
        *,
        model: Optional[str] = None,
        binary: Optional[str] = None,
        wrapper_path: Optional[Path] = None,
        runner: Optional[RunnerProtocol] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ):
        super().__init__(metadata, hooks)
        self._runner = runner or _default_runner
        self._binary = binary or os.environ.get(CUSTOM_BINARY_ENV, DEFAULT_BINARY)
        self._wrapper_path = wrapper_path or Path(
            os.environ.get(CUSTOM_WRAPPER_ENV, str(DEFAULT_WRAPPER_SCRIPT))
        )

        # Prepare environment for subprocess with secure API key handling
        self._env = self._prepare_subprocess_env(env)

        self._timeout = timeout or DEFAULT_TIMEOUT_SECONDS
        self._model = self._ensure_model(model or metadata.default_model or self._first_model_id())
        self._server_process: Optional[subprocess.Popen] = None
        self._config_file_path: Optional[Path] = None

    def __del__(self) -> None:
        """Clean up server process and config file on provider destruction."""
        # Clean up server process
        if hasattr(self, '_server_process') and self._server_process is not None:
            try:
                self._server_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self._server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self._server_process.kill()
            except (OSError, ProcessLookupError):
                # Process already terminated, ignore
                pass
            finally:
                self._server_process = None

        # Clean up config file
        self._cleanup_config_file()

    def _prepare_subprocess_env(self, custom_env: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Prepare environment variables for subprocess execution.

        Merges current process environment with custom overrides and ensures
        required OpenCode variables are present.
        """
        # Start with a copy of the current environment
        subprocess_env = os.environ.copy()

        # Merge custom environment if provided
        if custom_env:
            subprocess_env.update(custom_env)

        # Ensure OPENCODE_SERVER_URL is set (use default if not provided)
        if "OPENCODE_SERVER_URL" not in subprocess_env:
            subprocess_env["OPENCODE_SERVER_URL"] = DEFAULT_SERVER_URL

        # Note: OPENCODE_API_KEY should be provided via environment or custom_env
        # We don't set a default value for security reasons

        return subprocess_env

    def _create_readonly_config(self) -> Path:
        """
        Create temporary opencode.json with read-only tool restrictions.

        Returns:
            Path to the temporary config file

        Note:
            - Tool blocking may not work for MCP tools (OpenCode issue #3756)
            - Config is server-wide, affecting all sessions on this server instance
        """
        # Create temp directory for config
        temp_dir = Path(tempfile.mkdtemp(prefix="opencode_readonly_"))

        # Create config file
        config_path = temp_dir / "opencode.json"
        with open(config_path, 'w') as f:
            json.dump(READONLY_TOOLS_CONFIG, f, indent=2)

        return config_path

    def _cleanup_config_file(self) -> None:
        """Remove temporary config file and directory."""
        if hasattr(self, '_config_file_path') and self._config_file_path is not None:
            try:
                # Remove config file
                if self._config_file_path.exists():
                    self._config_file_path.unlink()

                # Remove temp directory
                temp_dir = self._config_file_path.parent
                if temp_dir.exists():
                    temp_dir.rmdir()
            except (OSError, FileNotFoundError):
                # File already removed or doesn't exist, ignore
                pass
            finally:
                self._config_file_path = None

    def _first_model_id(self) -> str:
        if not self.metadata.models:
            raise ProviderUnavailableError(
                "OpenCode provider metadata is missing model descriptors.",
                provider=self.metadata.provider_name,
            )
        return self.metadata.models[0].id

    def _ensure_model(self, candidate: str) -> str:
        # Validate that the model is not empty
        if not candidate or not candidate.strip():
            raise ProviderExecutionError(
                "Model identifier cannot be empty",
                provider=self.metadata.provider_name,
            )

        # For opencode, we accept any model ID and let opencode CLI validate it
        # This avoids maintaining a hardcoded list that would become stale
        # opencode CLI supports many models across providers (OpenAI, Anthropic, etc.)
        return candidate

    def _is_port_open(self, port: int, host: str = "localhost") -> bool:
        """Check if a TCP port is open and accepting connections."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except (socket.error, OSError):
            return False

    def _ensure_server_running(self) -> None:
        """Ensure OpenCode server is running, start if necessary."""
        # Extract port from server URL (default: 4096)
        server_url = self._env.get("OPENCODE_SERVER_URL", DEFAULT_SERVER_URL) if self._env else DEFAULT_SERVER_URL
        try:
            # Parse port from URL (e.g., "http://localhost:4096" -> 4096)
            port = int(server_url.split(":")[-1].rstrip("/"))
        except (ValueError, IndexError):
            port = 4096

        # Check if server is already running
        if self._is_port_open(port):
            return

        # Server not running - need to start it
        # Look for opencode binary in node_modules/.bin first
        opencode_binary = None
        node_modules_bin = Path("node_modules/.bin/opencode")

        if node_modules_bin.exists():
            opencode_binary = str(node_modules_bin)
        else:
            # Fall back to global opencode if available
            try:
                result = subprocess.run(
                    ["which", "opencode"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    opencode_binary = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        if not opencode_binary:
            raise ProviderUnavailableError(
                "OpenCode server not running and 'opencode' binary not found in node_modules/.bin or PATH",
                provider=self.metadata.provider_name,
            )

        # Create read-only configuration file
        self._config_file_path = self._create_readonly_config()

        # Start server in background
        # Prepare environment with API keys and configuration
        server_env = self._prepare_subprocess_env(self._env)
        # Set OPENCODE_CONFIG to point to our readonly config
        server_env["OPENCODE_CONFIG"] = str(self._config_file_path)

        try:
            self._server_process = subprocess.Popen(
                [opencode_binary, "serve", f"--hostname=127.0.0.1", f"--port={port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=server_env,  # Pass environment variables to server
                start_new_session=True,  # Detach from parent
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise ProviderExecutionError(
                f"Failed to start OpenCode server: {e}",
                provider=self.metadata.provider_name,
            ) from e

        # Wait for server to become available
        start_time = time.time()
        while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
            if self._is_port_open(port):
                return
            time.sleep(0.5)

        # Timeout - server didn't start
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None

        raise ProviderTimeoutError(
            f"OpenCode server failed to start within {SERVER_STARTUP_TIMEOUT} seconds",
            provider=self.metadata.provider_name,
        )

    def _execute(self, request: GenerationRequest) -> GenerationResult:
        """Execute generation request via OpenCode wrapper."""
        # Ensure server is running before making request
        self._ensure_server_running()

        # Build JSON payload for wrapper stdin
        payload = {
            "prompt": request.prompt,
            "system_prompt": request.system_prompt if hasattr(request, "system_prompt") else None,
            "config": {
                "model": self._model,
                "temperature": request.temperature if hasattr(request, "temperature") else None,
                "max_tokens": request.max_tokens if hasattr(request, "max_tokens") else None,
            },
        }

        # Build command to invoke wrapper
        command = [self._binary, str(self._wrapper_path)]
        if request.stream:
            command.append("--stream")

        # Execute wrapper with JSON payload via stdin
        timeout = request.timeout or self._timeout
        try:
            completed = self._runner(
                command,
                timeout=timeout,
                env=self._env,
                input_data=json.dumps(payload),
            )
        except FileNotFoundError as exc:
            raise ProviderUnavailableError(
                f"Node.js binary '{self._binary}' not found",
                provider=self.metadata.provider_name,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderTimeoutError(
                f"OpenCode wrapper timed out after {timeout}s",
                provider=self.metadata.provider_name,
            ) from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise ProviderExecutionError(
                f"OpenCode wrapper exited with code {completed.returncode}: {stderr or 'no stderr'}",
                provider=self.metadata.provider_name,
            )

        # Parse line-delimited JSON output
        content_parts = []
        final_usage: Optional[TokenUsage] = None
        raw_payload: Dict[str, Any] = {}

        for line in completed.stdout.strip().split("\n"):
            if not line.strip():
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProviderExecutionError(
                    f"Invalid JSON from wrapper: {line[:100]}",
                    provider=self.metadata.provider_name,
                ) from exc

            msg_type = msg.get("type")

            if msg_type == "chunk":
                # Streaming chunk
                chunk_content = msg.get("content", "")
                content_parts.append(chunk_content)
                if request.stream:
                    self._emit_stream_chunk(StreamChunk(content=chunk_content, index=len(content_parts) - 1))

            elif msg_type == "done":
                # Final response with metadata
                response_data = msg.get("response", {})
                final_text = response_data.get("text", "")
                if final_text and not content_parts:
                    content_parts.append(final_text)

                # Extract token usage
                usage_data = response_data.get("usage", {})
                final_usage = TokenUsage(
                    input_tokens=usage_data.get("prompt_tokens", 0),
                    output_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                    metadata={"model": response_data.get("model")},
                )
                raw_payload = response_data

            elif msg_type == "error":
                # Error from wrapper
                error_msg = msg.get("message", "Unknown error")
                raise ProviderExecutionError(
                    f"OpenCode wrapper error: {error_msg}",
                    provider=self.metadata.provider_name,
                )

        # Combine all content parts
        final_content = "".join(content_parts)

        # Use default usage if not provided
        if final_usage is None:
            final_usage = TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)

        return GenerationResult(
            content=final_content,
            model_fqn=f"{self.metadata.provider_name}:{self._model}",
            status=ProviderStatus.SUCCESS,
            usage=final_usage,
            stderr=(completed.stderr or "").strip() or None,
            raw_payload=raw_payload,
        )


def is_opencode_available() -> bool:
    """
    Check if OpenCode provider dependencies are available.

    Verifies:
    1. Node.js runtime is available
    2. Wrapper script exists
    3. node_modules exists with @opencode-ai/sdk
    4. opencode binary exists (for server management)
    """
    # Check Node.js runtime
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

    # Check wrapper script exists
    if not DEFAULT_WRAPPER_SCRIPT.exists():
        return False

    # Check node_modules with @opencode-ai/sdk
    sdk_path = DEFAULT_WRAPPER_SCRIPT.parent / "node_modules" / "@opencode-ai" / "sdk"
    if not sdk_path.exists():
        return False

    # Check opencode binary (in node_modules/.bin or global PATH)
    node_modules_bin = Path("node_modules/.bin/opencode")
    if node_modules_bin.exists():
        return True

    # Check global PATH
    try:
        result = subprocess.run(
            ["which", "opencode"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False


def create_provider(
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
    dependencies: Optional[Dict[str, object]] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> OpenCodeProvider:
    """
    Factory function for creating OpenCodeProvider instances.

    Args:
        hooks: Provider hooks for callbacks
        model: Optional model ID override
        dependencies: Optional dependencies (runner, env, binary)
        overrides: Optional parameter overrides

    Returns:
        Configured OpenCodeProvider instance
    """
    dependencies = dependencies or {}
    overrides = overrides or {}

    runner = dependencies.get("runner")
    env = dependencies.get("env")
    binary = overrides.get("binary") or dependencies.get("binary")
    wrapper_path = overrides.get("wrapper_path") or dependencies.get("wrapper_path")
    timeout = overrides.get("timeout") or dependencies.get("timeout")

    return OpenCodeProvider(
        metadata=OPENCODE_METADATA,
        hooks=hooks,
        model=model,
        binary=binary,
        wrapper_path=wrapper_path,
        runner=runner,
        env=env,
        timeout=timeout,
    )


# Register the provider immediately so consumers can resolve it by id.
register_provider(
    "opencode",
    factory=create_provider,
    metadata=OPENCODE_METADATA,
    availability_check=is_opencode_available,
    description="OpenCode AI SDK adapter with Node.js wrapper",
    tags=("sdk", "text", "streaming"),
    replace=True,
)
