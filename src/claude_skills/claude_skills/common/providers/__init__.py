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
from .registry import (
    ProviderFactory,
    ProviderRegistration,
    register_provider,
    register_lazy_provider,
    available_providers,
    resolve_provider,
    get_provider_metadata,
    describe_providers,
    set_dependency_resolver,
    reset_registry,
)
from .gemini import (
    GeminiProvider,
    create_provider as create_gemini_provider,
    is_gemini_available as gemini_is_available,
    GEMINI_METADATA,
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
    "ProviderFactory",
    "ProviderRegistration",
    "register_provider",
    "register_lazy_provider",
    "available_providers",
    "resolve_provider",
    "get_provider_metadata",
    "describe_providers",
    "set_dependency_resolver",
    "reset_registry",
    "GeminiProvider",
    "create_gemini_provider",
    "gemini_is_available",
    "GEMINI_METADATA",
]
