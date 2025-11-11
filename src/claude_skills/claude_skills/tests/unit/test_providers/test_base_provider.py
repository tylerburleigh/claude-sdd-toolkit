"""
Unit tests for the provider abstraction scaffolding.

Focus areas:
    * ProviderContext hook orchestration and error normalization
    * Registry registration / resolution pathways
    * CLI runner happy-path execution against the abstraction
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from unittest.mock import Mock

import pytest

from claude_skills.common import PrettyPrinter
from claude_skills.common.providers import (
    GenerationRequest,
    GenerationResult,
    ModelDescriptor,
    ProviderCapability,
    ProviderContext,
    ProviderExecutionError,
    ProviderHooks,
    ProviderMetadata,
    ProviderStatus,
    ProviderUnavailableError,
    StreamChunk,
    available_providers,
    get_provider_metadata,
    register_provider,
    reset_registry,
    resolve_provider,
    set_dependency_resolver,
)
from claude_skills.cli.provider_runner import RunnerConfig, run_provider


def make_metadata(
    provider_name: str = "demo",
    capabilities: Optional[Set[ProviderCapability]] = None,
) -> ProviderMetadata:
    return ProviderMetadata(
        provider_name=provider_name,
        models=[
            ModelDescriptor(
                id=f"{provider_name}-model",
                display_name=f"{provider_name.title()} Model",
                capabilities=set(capabilities or {ProviderCapability.TEXT}),
            )
        ],
        default_model=f"{provider_name}-model",
    )


def make_result(
    *,
    content: str = "ok",
    model_fqn: str = "demo:demo-model",
    status: ProviderStatus = ProviderStatus.SUCCESS,
) -> GenerationResult:
    return GenerationResult(
        content=content,
        model_fqn=model_fqn,
        status=status,
    )


class DummyProvider(ProviderContext):
    """Simple ProviderContext implementation for exercising the base class."""

    def __init__(
        self,
        metadata: ProviderMetadata,
        hooks: ProviderHooks,
        *,
        result: Optional[GenerationResult] = None,
        stream_chunks: Optional[List[str]] = None,
        error: Optional[BaseException] = None,
    ) -> None:
        super().__init__(metadata, hooks)
        self._result = result or make_result()
        self._stream_chunks = stream_chunks or []
        self._error = error
        self.requests: List[GenerationRequest] = []

    def _execute(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        if self._error:
            raise self._error
        for idx, content in enumerate(self._stream_chunks):
            self._emit_stream_chunk(StreamChunk(content=content, index=idx))
        return self._result


@pytest.fixture(autouse=True)
def reset_registry_state() -> None:
    """Ensure registry isolation across tests."""
    reset_registry()
    yield
    reset_registry()


def test_provider_context_invokes_hooks_and_streams() -> None:
    before_hook = Mock()
    after_hook = Mock()
    captured_chunks: List[str] = []
    hooks = ProviderHooks(
        before_execute=before_hook,
        after_result=after_hook,
        on_stream_chunk=lambda chunk: captured_chunks.append(chunk.content),
    )
    metadata = make_metadata(
        capabilities={ProviderCapability.TEXT, ProviderCapability.STREAMING}
    )
    provider = DummyProvider(
        metadata,
        hooks,
        result=make_result(content="final"),
        stream_chunks=["foo", "bar"],
    )

    request = GenerationRequest(prompt="hello world", stream=True)
    result = provider.generate(request)

    assert result.content == "final"
    before_hook.assert_called_once_with(request, metadata)
    after_hook.assert_called_once_with(result)
    assert captured_chunks == ["foo", "bar"]
    assert provider.supports(ProviderCapability.TEXT) is True
    assert provider.supports(ProviderCapability.FUNCTION_CALLING) is False


def test_provider_context_wraps_unknown_exceptions() -> None:
    metadata = make_metadata()
    provider = DummyProvider(
        metadata,
        ProviderHooks(),
        error=RuntimeError("boom"),
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(GenerationRequest(prompt="broken"))

    assert "boom" in str(excinfo.value)


def test_provider_context_maps_file_not_found_to_unavailable() -> None:
    metadata = make_metadata()
    provider = DummyProvider(
        metadata,
        ProviderHooks(),
        error=FileNotFoundError("missing binary"),
    )

    with pytest.raises(ProviderUnavailableError) as excinfo:
        provider.generate(GenerationRequest(prompt="hey"))

    assert "missing binary" in str(excinfo.value)


def test_resolve_provider_passes_dependencies_and_returns_metadata() -> None:
    metadata = make_metadata()
    captured: Dict[str, object] = {}

    def factory(
        *,
        hooks: ProviderHooks,
        model: Optional[str],
        dependencies: Optional[Dict[str, object]],
        overrides: Optional[Dict[str, object]],
    ) -> DummyProvider:
        captured["hooks"] = hooks
        captured["model"] = model
        captured["dependencies"] = dependencies
        captured["overrides"] = overrides
        return DummyProvider(metadata, hooks)

    register_provider(
        "demo",
        factory=factory,
        metadata=metadata,
        priority=5,
        availability_check=lambda: True,
    )
    set_dependency_resolver(lambda provider_id: {"token": f"{provider_id}-dep"})
    hooks = ProviderHooks()

    resolved = resolve_provider(
        "demo",
        hooks=hooks,
        model="beta",
        overrides={"temperature": 0.2},
    )

    assert isinstance(resolved, DummyProvider)
    assert captured["hooks"] is hooks
    assert captured["model"] == "beta"
    assert captured["dependencies"] == {"token": "demo-dep"}
    assert captured["overrides"] == {"temperature": 0.2}
    assert available_providers() == ["demo"]
    assert get_provider_metadata("demo") == metadata


def test_available_providers_honors_priority_and_availability() -> None:
    # unavailable provider should still appear when requested, but filtered otherwise
    register_provider(
        "offline",
        factory=lambda **kwargs: DummyProvider(make_metadata("offline"), kwargs["hooks"]),
        availability_check=lambda: False,
        priority=10,
    )
    register_provider(
        "online",
        factory=lambda **kwargs: DummyProvider(make_metadata("online"), kwargs["hooks"]),
        availability_check=lambda: True,
        priority=1,
    )

    assert available_providers() == ["online"]
    assert available_providers(include_unavailable=True) == ["offline", "online"]


def test_run_provider_streaming_happy_path() -> None:
    metadata = make_metadata()
    result_payload = make_result(content="", model_fqn="demo:demo-model")

    def loader(
        provider: str,
        *,
        hooks: ProviderHooks,
        model: Optional[str] = None,
    ) -> DummyProvider:
        assert provider == "demo"
        assert model == "beta"
        return DummyProvider(
            metadata,
            hooks,
            result=result_payload,
            stream_chunks=["hello ", "world"],
        )

    config = RunnerConfig(
        provider="demo",
        prompt="Say hi",
        model="beta",
        stream=True,
        quiet_stream=True,
        json_output=True,
    )

    runner_result = run_provider(config, loader=loader, printer=PrettyPrinter())

    assert runner_result.status == ProviderStatus.SUCCESS
    assert runner_result.result is not None
    assert runner_result.result.content == "hello world"
    assert runner_result.result.model_fqn == "demo:demo-model"
