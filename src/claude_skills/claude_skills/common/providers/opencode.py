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


OPENCODE_MODELS: List[ModelDescriptor] = [
    ModelDescriptor(
        id="default",
        display_name="OpenCode AI Default",
        capabilities={
            ProviderCapability.TEXT,
            ProviderCapability.STREAMING,
        },
        routing_hints={"configurable": True, "source": "ai_config.yaml"},
    ),
]

OPENCODE_METADATA = ProviderMetadata(
    provider_name="opencode",
    models=tuple(OPENCODE_MODELS),
    default_model="default",
    security_flags={"writes_allowed": False},
    extra={
        "wrapper": "opencode_wrapper.js",
        "server_url": DEFAULT_SERVER_URL,
        "configurable": True,
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
        self._env = env
        self._timeout = timeout or DEFAULT_TIMEOUT_SECONDS
        self._model = self._ensure_model(model or metadata.default_model or self._first_model_id())
        self._server_process: Optional[subprocess.Popen] = None

    def _first_model_id(self) -> str:
        if not self.metadata.models:
            raise ProviderUnavailableError(
                "OpenCode provider metadata is missing model descriptors.",
                provider=self.metadata.provider_name,
            )
        return self.metadata.models[0].id

    def _ensure_model(self, candidate: str) -> str:
        available = {descriptor.id for descriptor in self.metadata.models}
        if candidate not in available:
            raise ProviderExecutionError(
                f"Unsupported OpenCode model '{candidate}'. Available: {', '.join(sorted(available))}",
                provider=self.metadata.provider_name,
            )
        return candidate
