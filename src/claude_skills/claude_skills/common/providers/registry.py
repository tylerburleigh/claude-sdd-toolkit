"""
Provider registry utilities.

Encapsulates registration, lazy loading, availability checks, and dependency
injection hooks for ProviderContext implementations. This module backs the
CLI provider runner plus future skill integrations, providing a single source
of truth for discovering available providers.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence

from .base import (
    ProviderContext,
    ProviderHooks,
    ProviderMetadata,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class ProviderFactory(Protocol):
    """
    Callable that instantiates a ProviderContext.

    Implementations should accept keyword-only arguments for hooks, model,
    dependencies, and overrides so the registry can pass future options
    without breaking signatures.
    """

    def __call__(
        self,
        *,
        hooks: ProviderHooks,
        model: Optional[str] = None,
        dependencies: Optional[Dict[str, object]] = None,
        overrides: Optional[Dict[str, object]] = None,
    ) -> ProviderContext:
        ...


AvailabilityCheck = Callable[[], bool]
MetadataResolver = Callable[[], ProviderMetadata]
LazyFactoryLoader = Callable[[], ProviderFactory]
DependencyResolver = Callable[[str], Dict[str, object]]


@dataclass
class ProviderRegistration:
    """Internal record for a registered provider."""

    provider_id: str
    factory: Optional[ProviderFactory] = None
    lazy_loader: Optional[LazyFactoryLoader] = None
    metadata: Optional[ProviderMetadata] = None
    metadata_resolver: Optional[MetadataResolver] = None
    availability_check: Optional[AvailabilityCheck] = None
    priority: int = 0
    description: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)

    def load_factory(self) -> ProviderFactory:
        """Return the provider factory, performing lazy import if needed."""
        if self.factory is not None:
            return self.factory

        if self.lazy_loader is None:
            raise ProviderUnavailableError(
                f"Provider '{self.provider_id}' is missing a factory.",
                provider=self.provider_id,
            )

        factory = self.lazy_loader()
        if factory is None:
            raise ProviderUnavailableError(
                f"Lazy loader for '{self.provider_id}' returned None.",
                provider=self.provider_id,
            )

        self.factory = factory
        self.lazy_loader = None
        return factory

    def is_available(self) -> bool:
        """Return True if the provider passes its availability check."""
        if self.availability_check is None:
            return True
        try:
            return bool(self.availability_check())
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Availability check for provider '%s' failed: %s",
                self.provider_id,
                exc,
            )
            return False

    def resolve_metadata(self) -> Optional[ProviderMetadata]:
        """Return cached metadata, resolving lazily when necessary."""
        if self.metadata is not None:
            return self.metadata

        if self.metadata_resolver is None:
            return None

        try:
            self.metadata = self.metadata_resolver()
            return self.metadata
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Metadata resolver for provider '%s' failed: %s",
                self.provider_id,
                exc,
            )
            return None


_REGISTRY: Dict[str, ProviderRegistration] = {}
_dependency_resolver: Optional[DependencyResolver] = None


def register_provider(
    provider_id: str,
    *,
    factory: Optional[ProviderFactory] = None,
    lazy_loader: Optional[LazyFactoryLoader] = None,
    metadata: Optional[ProviderMetadata] = None,
    metadata_resolver: Optional[MetadataResolver] = None,
    availability_check: Optional[AvailabilityCheck] = None,
    priority: int = 0,
    description: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    replace: bool = False,
) -> None:
    """
    Register a provider factory with the global registry.

    Args:
        provider_id: Canonical provider identifier (e.g., "gemini").
        factory: Callable that instantiates ProviderContext instances.
        lazy_loader: Callable that returns a factory when invoked (lazy import).
        metadata: Optional ProviderMetadata object (cached).
        metadata_resolver: Callable that returns ProviderMetadata on demand.
        availability_check: Callable returning bool to gate resolution.
        priority: Sorting priority for available_providers (higher first).
        description: Human-readable description for diagnostics.
        tags: Optional labels describing the provider (e.g., ["cli", "modelchorus"]).
        replace: Overwrite existing registration if True.
    """
    if provider_id in _REGISTRY and not replace:
        raise ValueError(f"Provider '{provider_id}' is already registered")

    if factory is None and lazy_loader is None:
        raise ValueError("Either 'factory' or 'lazy_loader' must be provided")

    registration = ProviderRegistration(
        provider_id=provider_id,
        factory=factory,
        lazy_loader=lazy_loader,
        metadata=metadata,
        metadata_resolver=metadata_resolver,
        availability_check=availability_check,
        priority=priority,
        description=description,
        tags=tuple(tags or ()),
    )
    _REGISTRY[provider_id] = registration
    logger.debug("Provider '%s' registered (priority=%s)", provider_id, priority)


def register_lazy_provider(
    provider_id: str,
    module_path: str,
    *,
    factory_attr: str = "create_provider",
    metadata_attr: Optional[str] = None,
    availability_attr: Optional[str] = None,
    priority: int = 0,
    description: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    replace: bool = False,
) -> None:
    """
    Helper for registering providers by module path without importing upfront.
    """

    def _lazy_loader() -> ProviderFactory:
        module = importlib.import_module(module_path)
        factory_obj = getattr(module, factory_attr, None)
        if factory_obj is None:
            raise ProviderUnavailableError(
                f"Module '{module_path}' is missing '{factory_attr}'.",
                provider=provider_id,
            )
        return factory_obj

    metadata_resolver: Optional[MetadataResolver] = None
    if metadata_attr:
        metadata_resolver = _build_attr_resolver(
            module_path, metadata_attr, provider_id
        )

    availability_check: Optional[AvailabilityCheck] = None
    if availability_attr:
        availability_check = _build_attr_resolver(
            module_path, availability_attr, provider_id
        )

    register_provider(
        provider_id,
        lazy_loader=_lazy_loader,
        metadata_resolver=metadata_resolver,
        availability_check=availability_check,
        priority=priority,
        description=description,
        tags=tags,
        replace=replace,
    )


def _build_attr_resolver(
    module_path: str, attr: str, provider_id: str
) -> Callable[[], Any]:
    def _resolver() -> Any:
        module = importlib.import_module(module_path)
        target = getattr(module, attr, None)
        if callable(target):
            return target()
        return target

    return _resolver


def available_providers(*, include_unavailable: bool = False) -> List[str]:
    """
    Return provider identifiers sorted by priority (desc) then name.
    """
    providers: List[ProviderRegistration] = list(_REGISTRY.values())
    providers.sort(key=lambda reg: (-reg.priority, reg.provider_id))

    if include_unavailable:
        return [reg.provider_id for reg in providers]

    return [reg.provider_id for reg in providers if reg.is_available()]


def check_provider_available(provider_id: str) -> bool:
    """
    Check if a provider is available using its registered availability check.

    Args:
        provider_id: Provider identifier (e.g., "opencode", "gemini")

    Returns:
        True if provider is registered and passes its availability check

    Example:
        >>> check_provider_available("opencode")
        True
    """
    registration = _REGISTRY.get(provider_id)
    if registration is None:
        return False
    return registration.is_available()


def resolve_provider(
    provider_id: str,
    *,
    hooks: ProviderHooks,
    model: Optional[str] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> ProviderContext:
    """
    Instantiate a provider by id using the registered factory.
    """
    registration = _REGISTRY.get(provider_id)
    if registration is None:
        raise ProviderUnavailableError(
            f"Provider '{provider_id}' is not registered.", provider=provider_id
        )

    if not registration.is_available():
        raise ProviderUnavailableError(
            f"Provider '{provider_id}' is currently unavailable.",
            provider=provider_id,
        )

    factory = registration.load_factory()
    dependencies = _resolve_dependencies(provider_id)
    return factory(
        hooks=hooks,
        model=model,
        dependencies=dependencies,
        overrides=overrides,
    )


def get_provider_metadata(provider_id: str) -> Optional[ProviderMetadata]:
    """Return ProviderMetadata if available."""
    registration = _REGISTRY.get(provider_id)
    if registration is None:
        return None
    return registration.resolve_metadata()


def describe_providers() -> List[Dict[str, object]]:
    """
    Return descriptive information for all registered providers.
    """
    summary: List[Dict[str, object]] = []
    for reg in _REGISTRY.values():
        summary.append(
            {
                "id": reg.provider_id,
                "description": reg.description,
                "priority": reg.priority,
                "tags": list(reg.tags),
                "available": reg.is_available(),
            }
        )
    return summary


def set_dependency_resolver(resolver: Optional[DependencyResolver]) -> None:
    """
    Register a callable that supplies dependency dictionaries per provider id.

    The resolver is invoked during `resolve_provider` and should return a dict
    that will be passed to the provider factory via the `dependencies` keyword.
    """
    global _dependency_resolver
    _dependency_resolver = resolver


def reset_registry() -> None:
    """Utility for tests to clear registry state."""
    _REGISTRY.clear()
    set_dependency_resolver(None)


def _resolve_dependencies(provider_id: str) -> Dict[str, object]:
    if _dependency_resolver is None:
        return {}
    try:
        dependencies = _dependency_resolver(provider_id)
        return dependencies or {}
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning(
            "Dependency resolver failed for provider '%s': %s",
            provider_id,
            exc,
        )
        return {}


__all__ = [
    "ProviderFactory",
    "ProviderRegistration",
    "register_provider",
    "register_lazy_provider",
    "available_providers",
    "check_provider_available",
    "resolve_provider",
    "get_provider_metadata",
    "describe_providers",
    "set_dependency_resolver",
    "reset_registry",
]
