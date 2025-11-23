"""
Base provider abstractions for the SDD toolkit.

This module mirrors the ModelChorus provider contracts while adapting them
to the claude-skills codebase. It defines the canonical capability/status
enums, request/response dataclasses, error surface, and the `ProviderContext`
abstract base class invoked by higher-level registries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Set


class ProviderCapability(Enum):
    """
    Declares the feature flags a provider can expose to routing heuristics.

    These values intentionally align with the audited ModelChorus capabilities
    so that metadata can be shared between ecosystems.
    """

    TEXT = "text_generation"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    THINKING = "thinking"


class ProviderStatus(Enum):
    """
    Normalized execution outcomes emitted by providers.

    This mirrors the legacy ToolStatus enum so existing callers can map the
    new abstraction back to their current success/error handling paths.
    """

    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_OUTPUT = "invalid_output"
    ERROR = "error"
    CANCELED = "canceled"

    def is_retryable(self) -> bool:
        """
        Check if this status represents a transient failure that may succeed on retry.

        Retryable statuses:
            - TIMEOUT: May succeed with more time or if temporary resource contention resolves
            - ERROR: Generic errors may be transient (network issues, rate limits, etc.)

        Non-retryable statuses:
            - SUCCESS: Already succeeded
            - NOT_FOUND: Provider/tool not available (won't change on retry)
            - INVALID_OUTPUT: Provider responded but output was malformed (unlikely to fix on retry)
            - CANCELED: Explicitly canceled (shouldn't retry)

        Returns:
            True if the status is retryable, False otherwise
        """
        return self in (ProviderStatus.TIMEOUT, ProviderStatus.ERROR)


class ProviderError(RuntimeError):
    """Base exception for provider orchestration."""

    def __init__(self, message: str, *, provider: Optional[str] = None):
        self.provider = provider
        super().__init__(message)


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot be instantiated (binary missing, auth issues)."""


class ProviderExecutionError(ProviderError):
    """Raised when a provider command returns a non-retryable error."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider exceeds its allotted execution time."""


@dataclass(frozen=True)
class TokenUsage:
    """Token accounting information reported by providers."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    total_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelDescriptor:
    """
    Describes a model supported by a provider.

    Attributes:
        id: Provider-specific identifier (e.g., "pro").
        display_name: Friendly name for UIs/logs.
        capabilities: Capability flags supported by the model.
        routing_hints: Optional metadata used by registries (cost, latency, etc.).
    """

    id: str
    display_name: Optional[str] = None
    capabilities: Set[ProviderCapability] = field(default_factory=set)
    routing_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderMetadata:
    """
    Provider-level metadata shared with registries and consumers.

    Attributes:
        provider_name: Canonical provider identifier ("gemini", "codex", etc.).
        models: Supported model descriptors.
        default_model: Optional default model id used when no override supplied.
        security_flags: Provider-specific sandbox/safety configuration.
        extra: Arbitrary metadata (version info, auth requirements, etc.).
    """

    provider_name: str
    models: Sequence[ModelDescriptor]
    default_model: Optional[str] = None
    security_flags: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationRequest:
    """
    Normalized request payload for provider execution.

    Attributes closely follow the ModelChorus GenerationRequest contract to
    simplify migration between ecosystems.
    """

    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    continuation_id: Optional[str] = None
    attachments: Sequence[str] = field(default_factory=list)
    timeout: Optional[float] = None
    stream: bool = False


@dataclass(frozen=True)
class StreamChunk:
    """Represents a streamed fragment emitted by the provider."""

    content: str
    index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    """
    Normalized provider response.

    Attributes:
        content: Final text output (aggregated if streaming was used).
        model_fqn: Fully-qualified model identifier `<provider>:<model>`.
        status: ProviderStatus describing execution outcome.
        usage: Optional token usage data.
        stderr: Captured stderr/log output for debugging.
        raw_payload: Provider-specific metadata (JSON blobs, traces, etc.).
    """

    content: str
    model_fqn: str
    status: ProviderStatus
    usage: TokenUsage = field(default_factory=TokenUsage)
    stderr: Optional[str] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)


StreamCallback = Callable[[StreamChunk], None]
BeforeExecuteHook = Callable[[GenerationRequest, ProviderMetadata], None]
AfterResultHook = Callable[[GenerationResult], None]


@dataclass
class ProviderHooks:
    """
    Optional lifecycle hooks wired by the registry.

    Hooks default to no-ops so providers can invoke them unconditionally.
    """

    before_execute: Optional[BeforeExecuteHook] = None
    on_stream_chunk: Optional[StreamCallback] = None
    after_result: Optional[AfterResultHook] = None

    def emit_before(self, request: GenerationRequest, metadata: ProviderMetadata) -> None:
        if self.before_execute:
            self.before_execute(request, metadata)

    def emit_stream(self, chunk: StreamChunk) -> None:
        if self.on_stream_chunk:
            self.on_stream_chunk(chunk)

    def emit_after(self, result: GenerationResult) -> None:
        if self.after_result:
            self.after_result(result)


class ProviderContext(ABC):
    """
    Base class for provider implementations.

    Subclasses should:
        * Resolve CLI/environment dependencies during initialization.
        * Implement `_execute()` to run the underlying provider and return a
          populated `GenerationResult`.
        * Emit streaming chunks via `self._hooks.emit_stream()` when `request.stream`
          is True and the provider supports streaming output.
    """

    def __init__(self, metadata: ProviderMetadata, hooks: Optional[ProviderHooks] = None):
        self._metadata = metadata
        self._hooks = hooks or ProviderHooks()

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def supports(self, capability: ProviderCapability) -> bool:
        """Return True if any registered model advertises the capability."""
        return any(capability in model.capabilities for model in self._metadata.models)

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """
        Execute the provider with the supplied request.

        Applies lifecycle hooks, normalizes errors, and ensures ProviderStatus
        is consistent across implementations.
        """
        normalized_request = self._prepare_request(request)
        self._hooks.emit_before(normalized_request, self._metadata)

        try:
            result = self._execute(normalized_request)
        except ProviderTimeoutError:
            raise
        except ProviderUnavailableError:
            raise
        except ProviderError:
            raise
        except FileNotFoundError as exc:
            raise ProviderUnavailableError(str(exc), provider=self._metadata.provider_name) from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc), provider=self._metadata.provider_name) from exc
        except Exception as exc:  # noqa: BLE001 - we intentionally wrap all provider exceptions
            raise ProviderExecutionError(str(exc), provider=self._metadata.provider_name) from exc

        self._hooks.emit_after(result)
        return result

    def _prepare_request(self, request: GenerationRequest) -> GenerationRequest:
        """
        Allow subclasses to adjust request metadata before execution.

        The default implementation simply returns the request to keep hooks
        centralized inside ProviderContext.
        """
        return request

    def _emit_stream_chunk(self, chunk: StreamChunk) -> None:
        """
        Helper for subclasses to publish streaming output through hooks.
        """
        self._hooks.emit_stream(chunk)

    @abstractmethod
    def _execute(self, request: GenerationRequest) -> GenerationResult:
        """
        Subclasses must implement the actual provider invocation.
        """
        raise NotImplementedError


__all__ = [
    "ProviderCapability",
    "ProviderStatus",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderExecutionError",
    "ProviderTimeoutError",
    "TokenUsage",
    "ModelDescriptor",
    "ProviderMetadata",
    "GenerationRequest",
    "GenerationResult",
    "StreamChunk",
    "StreamCallback",
    "BeforeExecuteHook",
    "AfterResultHook",
    "ProviderHooks",
    "ProviderContext",
]
