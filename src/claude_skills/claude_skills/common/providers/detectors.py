"""
Provider availability detection utilities.

Centralizes CLI discovery strategies (PATH resolution, environment overrides,
and health probes) so provider modules and higher-level tooling can share
consistent logic.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Sequence

logger = logging.getLogger(__name__)

_TOOL_PATH_ENV = "CLAUDE_SKILLS_TOOL_PATH"


def _coerce_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


def _resolve_executable(binary: str) -> Optional[str]:
    configured_path = os.environ.get(_TOOL_PATH_ENV)
    if configured_path:
        return shutil.which(binary, path=configured_path)
    return shutil.which(binary)


@dataclass(frozen=True)
class ProviderDetector:
    """Configuration describing how to detect a provider CLI."""

    provider_id: str
    default_binary: str
    override_env: Optional[str] = None
    binary_env: Optional[str] = None
    probe_args: Sequence[str] = field(default_factory=lambda: ("--version",))
    probe_timeout: int = 5

    def _resolve_binary(self) -> Optional[str]:
        binary = self.default_binary
        if self.binary_env and os.environ.get(self.binary_env):
            binary = os.environ[self.binary_env]  # explicit override path/name
        return _resolve_executable(binary)

    def _run_probe(self, executable: str) -> bool:
        if not self.probe_args:
            return True
        try:
            subprocess.run(
                [executable, *self.probe_args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.probe_timeout,
                check=True,
            )
            return True
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug(
                "Probe for provider '%s' failed via %s: %s",
                self.provider_id,
                executable,
                exc,
            )
            return False

    def is_available(self, *, use_probe: bool = True) -> bool:
        override = _coerce_bool(os.environ.get(self.override_env)) if self.override_env else None
        if override is not None:
            return override

        executable = self._resolve_binary()
        if not executable:
            return False

        if not use_probe:
            return True

        return self._run_probe(executable)


_DEFAULT_DETECTORS: tuple[ProviderDetector, ...] = (
    ProviderDetector(
        provider_id="gemini",
        default_binary="gemini",
        override_env="GEMINI_CLI_AVAILABLE_OVERRIDE",
        binary_env="GEMINI_CLI_BINARY",
        probe_args=("--help",),
    ),
    ProviderDetector(
        provider_id="codex",
        default_binary="codex",
        override_env="CODEX_CLI_AVAILABLE_OVERRIDE",
        binary_env="CODEX_CLI_BINARY",
        probe_args=("--version",),
    ),
    ProviderDetector(
        provider_id="cursor-agent",
        default_binary="cursor-agent",
        override_env="CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE",
        binary_env="CURSOR_AGENT_CLI_BINARY",
        probe_args=("--version",),
    ),
    ProviderDetector(
        provider_id="claude",
        default_binary="claude",
        override_env="CLAUDE_CLI_AVAILABLE_OVERRIDE",
        binary_env="CLAUDE_CLI_BINARY",
        probe_args=("--version",),
    ),
    ProviderDetector(
        provider_id="opencode",
        default_binary="node",
        override_env="OPENCODE_AVAILABLE_OVERRIDE",
        binary_env="OPENCODE_BINARY",
        probe_args=("--version",),
    ),
)

_DETECTORS: Dict[str, ProviderDetector] = {}


def _reset_default_detectors() -> None:
    _DETECTORS.clear()
    for detector in _DEFAULT_DETECTORS:
        _DETECTORS[detector.provider_id] = detector


def register_detector(detector: ProviderDetector, *, replace: bool = False) -> None:
    """
    Register a detector configuration.
    """
    if detector.provider_id in _DETECTORS and not replace:
        raise ValueError(f"Detector for '{detector.provider_id}' already exists")
    _DETECTORS[detector.provider_id] = detector


def get_detector(provider_id: str) -> Optional[ProviderDetector]:
    """Return the detector for a provider id."""
    return _DETECTORS.get(provider_id)


def detect_provider_availability(provider_id: str, *, use_probe: bool = True) -> bool:
    """
    Check whether a provider is available.

    Args:
        provider_id: Identifier ("gemini", "codex", "cursor-agent", "claude")
        use_probe: When False, only perform PATH resolution / overrides.
    """
    detector = get_detector(provider_id)
    if detector is None:
        raise KeyError(f"No detector registered for provider '{provider_id}'")
    return detector.is_available(use_probe=use_probe)


def iter_detector_statuses(*, use_probe: bool = True) -> Dict[str, bool]:
    """Return availability map for all registered detectors."""
    return {
        provider_id: detector.is_available(use_probe=use_probe)
        for provider_id, detector in _DETECTORS.items()
    }


def reset_detectors() -> None:
    """Reset detectors to the default set (used by tests)."""
    _reset_default_detectors()


def list_detectors() -> Iterable[ProviderDetector]:
    """Expose registered detector configs."""
    return tuple(_DETECTORS.values())


_reset_default_detectors()

__all__ = [
    "ProviderDetector",
    "register_detector",
    "get_detector",
    "detect_provider_availability",
    "iter_detector_statuses",
    "reset_detectors",
    "list_detectors",
]
