"""
Tests for provider availability detectors.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from claude_skills.common.providers import (
    ProviderDetector,
    detect_provider_availability,
    get_provider_detector,
    register_provider_detector,
    reset_provider_detectors,
)


@pytest.fixture(autouse=True)
def reset_detectors() -> None:
    reset_provider_detectors()
    yield
    reset_provider_detectors()


def test_detect_provider_availability_runs_probe(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_CLI_AVAILABLE_OVERRIDE", "")

    with patch(
        "claude_skills.common.providers.detectors._resolve_executable",
        return_value="/tmp/gemini",
    ), patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=["gemini"], returncode=0)
        assert detect_provider_availability("gemini") is True
        mock_run.assert_called_once()


def test_detect_provider_availability_missing_binary_returns_false(monkeypatch) -> None:
    with patch(
        "claude_skills.common.providers.detectors._resolve_executable",
        return_value=None,
    ):
        assert detect_provider_availability("codex") is False


def test_detect_provider_availability_respects_override(monkeypatch) -> None:
    monkeypatch.setenv("CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE", "0")
    assert detect_provider_availability("cursor-agent") is False

    monkeypatch.setenv("CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE", "1")
    assert detect_provider_availability("cursor-agent") is True


def test_register_custom_detector(monkeypatch) -> None:
    custom = ProviderDetector(
        provider_id="custom-tool",
        default_binary="custom-tool",
        override_env="CUSTOM_TOOL_AVAILABLE",
        probe_args=(),
    )
    register_provider_detector(custom, replace=True)
    detector = get_provider_detector("custom-tool")
    assert detector is custom

    monkeypatch.setenv("CUSTOM_TOOL_AVAILABLE", "1")
    assert detect_provider_availability("custom-tool") is True
