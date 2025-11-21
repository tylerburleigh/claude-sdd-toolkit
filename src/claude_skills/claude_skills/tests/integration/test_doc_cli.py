"""Integration tests for the unified doc CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SDD_ENTRY = REPO_ROOT / "claude_skills" / "cli" / "sdd" / "__init__.py"


def run_doc_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run doc CLI via sdd."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [sys.executable, str(SDD_ENTRY), "doc", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def _write_sample_docs(tmp_path: Path) -> Path:
    """Create a minimal codebase.json payload for doc CLI tests."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "project_name": "sample",
            "version": "1.0.0",
            "language": "python"
        },
        "modules": [
            {
                "name": "calculator",
                "file": "calculator.py",
                "classes": ["Calculator"],
                "functions": ["add", "format_result"],
                "docstring": "Calculator helpers"
            }
        ],
        "classes": [
            {
                "name": "Calculator",
                "entity_type": "class",
                "file": "calculator.py",
                "line": 10,
                "docstring": "Performs addition.",
                "methods": ["add"],
                "properties": []
            }
        ],
        "functions": [
            {
                "name": "add",
                "entity_type": "function",
                "file": "calculator.py",
                "line": 20,
                "docstring": "Add two numbers.",
                "parameters": [
                    {"name": "a", "type": "float"},
                    {"name": "b", "type": "float"}
                ],
                "return_type": "float",
                "decorators": [],
                "complexity": 2,
                "is_async": False,
                "calls": [
                    {"name": "format_result", "call_type": "function_call"}
                ]
            },
            {
                "name": "format_result",
                "entity_type": "function",
                "file": "calculator.py",
                "line": 60,
                "docstring": "Format result for display.",
                "parameters": [
                    {"name": "value", "type": "float"}
                ],
                "return_type": "str",
                "decorators": [],
                "complexity": 1,
                "is_async": False,
                "callers": [
                    {"name": "add", "call_type": "function_call"}
                ]
            }
        ],
        "dependencies": {
            "calculator.py": ["external.math"]
        }
    }
    (docs_dir / "codebase.json").write_text(json.dumps(payload, indent=2))
    return docs_dir


def test_doc_help_lists_key_subcommands() -> None:
    result = run_doc_cli("--help")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    for subcommand in [
        "generate",
        "validate-json",
        "analyze",
        "find-class",
        "find-function",
        "list-modules",
    ]:
        assert subcommand in stdout


def test_doc_requires_subcommand() -> None:
    result = run_doc_cli()
    assert result.returncode != 0
    combined = (result.stderr or result.stdout).lower()
    assert "usage:" in combined


def test_doc_search_compact_and_pretty(tmp_path: Path) -> None:
    """doc search should honor compact JSON flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "search",
        "Calculator",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    compact_lines = compact.stdout.strip().splitlines()
    assert len(compact_lines) == 1
    compact_data = json.loads(compact.stdout)
    assert any(entry.get("name") == "Calculator" for entry in compact_data)

    pretty = run_doc_cli(
        "search",
        "Calculator",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_find_class_compact_and_pretty(tmp_path: Path) -> None:
    """doc find-class should also honor compact formatting."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "find-class",
        "Calculator",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, list)
    assert compact_data[0]["name"] == "Calculator"

    pretty = run_doc_cli(
        "find-class",
        "Calculator",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_find_function_compact_and_pretty(tmp_path: Path) -> None:
    """doc find-function should honor compact formatting."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "find-function",
        "add",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, list)
    assert compact_data[0]["name"] == "add"

    pretty = run_doc_cli(
        "find-function",
        "add",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_callers_compact_and_pretty(tmp_path: Path) -> None:
    """doc callers output should follow compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "callers",
        "add",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, list)

    pretty = run_doc_cli(
        "callers",
        "add",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_trace_entry_compact_and_pretty(tmp_path: Path) -> None:
    """trace-entry output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "trace-entry",
        "add",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, dict)

    pretty = run_doc_cli(
        "trace-entry",
        "add",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_trace_data_compact_and_pretty(tmp_path: Path) -> None:
    """trace-data output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "trace-data",
        "Calculator",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, dict)

    pretty = run_doc_cli(
        "trace-data",
        "Calculator",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_impact_compact_and_pretty(tmp_path: Path) -> None:
    """impact analysis output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "impact",
        "add",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    assert len(compact.stdout.strip().splitlines()) == 1
    compact_data = json.loads(compact.stdout)
    assert isinstance(compact_data, dict)

    pretty = run_doc_cli(
        "impact",
        "add",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert len(pretty.stdout.strip().splitlines()) >= 1
    assert json.loads(pretty.stdout) == compact_data


def test_doc_call_graph_compact_and_pretty(tmp_path: Path) -> None:
    """call-graph output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "call-graph",
        "add",
        "--json",
        "--compact",
        "--format", "json",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    compact_data = json.loads(compact.stdout or "{}")

    pretty = run_doc_cli(
        "call-graph",
        "add",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert json.loads(pretty.stdout or "{}") == compact_data


def test_doc_refactor_candidates_compact_and_pretty(tmp_path: Path) -> None:
    """refactor-candidates output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "refactor-candidates",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    compact_data = json.loads(compact.stdout or "{}")

    pretty = run_doc_cli(
        "refactor-candidates",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert json.loads(pretty.stdout or "{}") == compact_data


def test_doc_dependencies_compact_and_pretty(tmp_path: Path) -> None:
    """dependencies output should respect compact flags."""
    docs_dir = _write_sample_docs(tmp_path)

    compact = run_doc_cli(
        "dependencies",
        "calculator.py",
        "--json",
        "--compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert compact.returncode == 0
    compact_data = json.loads(compact.stdout or "[]")

    pretty = run_doc_cli(
        "dependencies",
        "calculator.py",
        "--json",
        "--no-compact",
        "--docs-path", str(docs_dir),
        "--no-staleness-check",
    )
    assert pretty.returncode == 0
    assert json.loads(pretty.stdout or "[]") == compact_data
