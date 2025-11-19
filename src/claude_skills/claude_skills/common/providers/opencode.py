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
