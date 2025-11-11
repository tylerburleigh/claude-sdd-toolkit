"""
Provider abstraction primitives.

Re-exports the base request/response dataclasses, capability/status enums,
error hierarchy, and ProviderContext needed by higher-level registries
and skill integrations.
"""

from .base import (
    ProviderCapability,
    ProviderStatus,
    ProviderError,
    ProviderUnavailableError,
    ProviderExecutionError,
    ProviderTimeoutError,
    ModelDescriptor,
    ProviderMetadata,
    TokenUsage,
    StreamChunk,
    GenerationRequest,
    GenerationResult,
    ProviderHooks,
    ProviderContext,
    StreamCallback,
    BeforeExecuteHook,
    AfterResultHook,
)

__all__ = [
    "ProviderCapability",
    "ProviderStatus",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderExecutionError",
    "ProviderTimeoutError",
    "ModelDescriptor",
    "ProviderMetadata",
    "TokenUsage",
    "StreamChunk",
    "GenerationRequest",
    "GenerationResult",
    "ProviderHooks",
    "ProviderContext",
    "StreamCallback",
    "BeforeExecuteHook",
    "AfterResultHook",
]
