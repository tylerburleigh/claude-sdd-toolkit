"""Tests for doc_query CLI JSON formatting helpers."""

import argparse
from typing import Dict, Any

from claude_skills.doc_query.cli import _maybe_json


def _run_maybe_json(payload: Dict[str, Any], compact: bool, capsys):
    args = argparse.Namespace(json=True, compact=compact)
    emitted = _maybe_json(args, payload)
    captured = capsys.readouterr().out.strip().splitlines()
    return emitted, captured


def test_doc_query_maybe_json_compact_single_line(capsys):
    payload = {"status": "ok", "count": 2}
    emitted, lines = _run_maybe_json(payload, True, capsys)

    assert emitted is True
    assert len(lines) == 1
    assert lines[0].startswith('{"status":"ok"')


def test_doc_query_maybe_json_pretty_multiline(capsys):
    payload = {"status": "ok", "count": 2}
    emitted, lines = _run_maybe_json(payload, False, capsys)

    assert emitted is True
    assert len(lines) > 1  # pretty output spans multiple lines
    assert lines[0] == "{"


def test_doc_query_maybe_json_respects_json_flag(capsys):
    payload = {"status": "ok"}
    args = argparse.Namespace(json=False, compact=True)

    emitted = _maybe_json(args, payload)
    captured = capsys.readouterr().out

    assert emitted is False
    assert captured == ""
