"""Tests for sdd doc scope command."""

import json
import pytest
import argparse
from pathlib import Path
from claude_skills.doc_query.cli import cmd_scope
from claude_skills.common import PrettyPrinter


@pytest.fixture
def sample_scope_codebase(tmp_path):
    """Create a sample codebase.json for scope testing."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()

    codebase_path = docs_path / "codebase.json"
    codebase_data = {
        "metadata": {
            "project_name": "ScopeTestProject",
            "version": "1.0.0",
            "generated_at": "2025-11-21T10:00:00Z",
            "languages": ["python"],
            "schema_version": "2.0"
        },
        "statistics": {
            "total_files": 5,
            "total_lines": 500,
            "total_classes": 3,
            "total_functions": 12
        },
        "functions": [
            {
                "name": "process_auth",
                "file": "src/auth.py",
                "line": 20,
                "complexity": 12,
                "docstring": "Main authentication processing",
                "call_count": 45,
                "callers": ["login", "verify_token"],
                "calls": [{"name": "validate_credentials"}, {"name": "create_session"}]
            },
            {
                "name": "validate_credentials",
                "file": "src/auth.py",
                "line": 65,
                "complexity": 8,
                "docstring": "Credential validation logic",
                "call_count": 50,
                "callers": ["process_auth"],
                "calls": [{"name": "hash_password"}]
            },
            {
                "name": "create_session",
                "file": "src/auth.py",
                "line": 95,
                "complexity": 5,
                "docstring": "Session creation helper",
                "call_count": 45,
                "callers": ["process_auth"],
                "calls": []
            },
            {
                "name": "login",
                "file": "src/routes/auth.py",
                "line": 15,
                "complexity": 3,
                "docstring": "Login endpoint",
                "call_count": 100,
                "callers": [],
                "calls": [{"name": "process_auth"}]
            },
            {
                "name": "simple_helper",
                "file": "src/utils.py",
                "line": 10,
                "complexity": 2,
                "docstring": "Simple utility function",
                "call_count": 10,
                "callers": [],
                "calls": []
            }
        ],
        "classes": [
            {
                "name": "AuthService",
                "file": "src/auth.py",
                "line": 10,
                "docstring": "Authentication service class",
                "instantiation_count": 30
            },
            {
                "name": "SessionManager",
                "file": "src/auth.py",
                "line": 150,
                "docstring": "Session management",
                "instantiation_count": 25
            },
            {
                "name": "Utils",
                "file": "src/utils.py",
                "line": 5,
                "docstring": "Utility class",
                "instantiation_count": 5
            }
        ],
        "modules": [
            {
                "name": "auth",
                "file": "src/auth.py",
                "docstring": "Authentication module with login and session management",
                "functions": ["process_auth", "validate_credentials", "create_session"],
                "classes": ["AuthService", "SessionManager"],
                "complexity": {
                    "avg": 8.33,
                    "max": 12,
                    "total": 25
                },
                "dependencies": ["utils", "database"],
                "reverse_dependencies": ["routes.auth", "api"]
            },
            {
                "name": "utils",
                "file": "src/utils.py",
                "docstring": "Utility module",
                "functions": ["simple_helper"],
                "classes": ["Utils"],
                "complexity": {
                    "avg": 2.0,
                    "max": 2,
                    "total": 2
                },
                "dependencies": [],
                "reverse_dependencies": ["auth"]
            }
        ]
    }

    with open(codebase_path, 'w') as f:
        json.dump(codebase_data, f)

    return codebase_path


class TestScopePlanPreset:
    """Tests for scope command with --plan preset."""

    def test_scope_plan_basic_output(self, sample_scope_codebase, capsys):
        """Test basic --plan preset output contains module summary."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()
        output_text = captured.out + captured.err

        # Should contain module name
        assert 'auth' in output_text.lower() or 'src/auth.py' in output_text.lower()

        # Should contain complexity information (part of plan preset)
        assert 'complexity' in output_text.lower() or 'complex' in output_text.lower()

    def test_scope_plan_includes_complex_functions(self, sample_scope_codebase, capsys):
        """Test --plan preset includes complex functions analysis."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()
        output_text = captured.out + captured.err

        # Should identify complex functions (complexity > 5)
        # process_auth (12) and validate_credentials (8) should be mentioned
        assert 'process_auth' in output_text or 'validate_credentials' in output_text

    def test_scope_plan_json_output(self, sample_scope_codebase, capsys):
        """Test --plan preset with JSON output format."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=True,
            compact=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        # Capture stdout for JSON output
        captured = capsys.readouterr()

        # Should be valid JSON
        try:
            output_data = json.loads(captured.out)
            assert isinstance(output_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_scope_plan_missing_module_error(self, sample_scope_codebase, capsys):
        """Test --plan preset returns error when module is missing."""
        args = argparse.Namespace(
            preset='plan',
            module=None,
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'module' in output_text.lower() and 'required' in output_text.lower()

    def test_scope_plan_invalid_preset_error(self, sample_scope_codebase, capsys):
        """Test scope command returns error for invalid preset."""
        args = argparse.Namespace(
            preset='invalid',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'invalid' in output_text.lower() and 'preset' in output_text.lower()

    def test_scope_plan_missing_preset_error(self, sample_scope_codebase, capsys):
        """Test scope command returns error when preset is missing."""
        args = argparse.Namespace(
            preset=None,
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'preset' in output_text.lower() and 'required' in output_text.lower()

    def test_scope_plan_nonexistent_docs(self, tmp_path, capsys):
        """Test --plan preset returns error when docs don't exist."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(tmp_path / "nonexistent"),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'documentation not found' in output_text.lower()

    def test_scope_plan_with_dependencies(self, sample_scope_codebase, capsys):
        """Test --plan preset includes dependency information."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()
        output_text = captured.out + captured.err

        # Should include dependency information
        # auth module depends on utils and database
        assert 'depend' in output_text.lower()
