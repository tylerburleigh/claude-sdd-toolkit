"""Integration tests for context/session-marker CLI commands."""

from pathlib import Path
import json
import uuid

from .cli_runner import run_cli


FIXTURE_TRANSCRIPT = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "context_tracker" / "transcript.jsonl"


def test_session_marker_generates_uuid():
    result = run_cli("session-marker", capture_output=True, text=True)
    assert result.returncode == 0
    marker = result.stdout.strip()
    assert marker


def test_context_compact_and_pretty(tmp_path, monkeypatch):
    fixtures_dir = tmp_path / ".claude" / "projects" / "workspace"
    fixtures_dir.mkdir(parents=True)
    transcript_path = fixtures_dir / "session.jsonl"
    fixture = Path(__file__).resolve().parents[5] / "tests" / "fixtures" / "context_tracker" / "transcript.jsonl"
    transcript_path.write_text(fixture.read_text())

    compact = run_cli("context", "--json", "--compact", "--transcript", str(transcript_path), capture_output=True, text=True)
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert compact_data["context_percentage_used"] == 100

    pretty = run_cli("context", "--json", "--no-compact", "--transcript", str(transcript_path), capture_output=True, text=True)
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) > 1
    assert json.loads(pretty.stdout) == compact_data
