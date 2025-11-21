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


class TestScopeImplementPreset:
    """Tests for scope command with --implement preset."""

    def test_scope_implement_with_function(self, sample_scope_codebase, capsys):
        """Test --implement preset with function parameter."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='process_auth',
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()
        output_text = captured.out + captured.err

        # Should contain function information
        assert 'process_auth' in output_text

        # Should include caller information
        assert 'caller' in output_text.lower() or 'login' in output_text or 'verify_token' in output_text

        # Should include call graph
        assert 'call' in output_text.lower()

    def test_scope_implement_without_function(self, sample_scope_codebase, capsys):
        """Test --implement preset without function shows tip."""
        args = argparse.Namespace(
            preset='implement',
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

        # Should still show instantiated classes
        assert 'authservice' in output_text.lower() or 'sessionmanager' in output_text.lower() or 'class' in output_text.lower()

        # Should show tip about using --function
        assert 'tip' in output_text.lower() or 'function' in output_text.lower()

    def test_scope_implement_json_output(self, sample_scope_codebase, capsys):
        """Test --implement preset with JSON output."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='process_auth',
            docs_path=str(sample_scope_codebase.parent),
            json=True,
            compact=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()

        # Should be valid JSON
        try:
            output_data = json.loads(captured.out)
            assert isinstance(output_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_scope_implement_shows_callers(self, sample_scope_codebase, capsys):
        """Test --implement preset includes caller analysis."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='process_auth',
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()
        output_text = captured.out + captured.err

        # Should identify callers (login and verify_token call process_auth)
        # At minimum should show caller-related information
        assert 'caller' in output_text.lower() or 'login' in output_text

    def test_scope_implement_shows_instantiated_classes(self, sample_scope_codebase, capsys):
        """Test --implement preset includes instantiated classes."""
        args = argparse.Namespace(
            preset='implement',
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

        # Should show instantiated classes from auth module
        # AuthService and SessionManager are in src/auth.py
        assert 'authservice' in output_text.lower() or 'sessionmanager' in output_text.lower() or 'instantiat' in output_text.lower()

    def test_scope_implement_missing_function_still_works(self, sample_scope_codebase, capsys):
        """Test --implement preset works without function parameter."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Should succeed even without function
        assert result == 0

    def test_scope_implement_nonexistent_docs(self, tmp_path, capsys):
        """Test --implement preset returns error when docs don't exist."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='process_auth',
            docs_path=str(tmp_path / "nonexistent"),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'documentation not found' in output_text.lower()

    def test_scope_implement_compact_json(self, sample_scope_codebase, capsys):
        """Test --implement preset with compact JSON output."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='process_auth',
            docs_path=str(sample_scope_codebase.parent),
            json=True,
            compact=True
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()

        # Compact JSON should be single-line
        lines = captured.out.strip().splitlines()
        assert len(lines) == 1

        # Should still be valid JSON
        try:
            output_data = json.loads(captured.out)
            assert isinstance(output_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Compact output is not valid JSON")


class TestScopeValidationAndErrors:
    """Tests for scope command validation and error handling."""

    def test_scope_missing_both_module_and_preset(self, sample_scope_codebase, capsys):
        """Test error when both module and preset are missing."""
        args = argparse.Namespace(
            preset=None,
            module=None,
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Should fail - preset is required
        assert result == 1

        captured = capsys.readouterr()
        output_text = captured.out + captured.err
        assert 'preset' in output_text.lower() and 'required' in output_text.lower()

    def test_scope_json_error_format(self, sample_scope_codebase, capsys):
        """Test that errors are properly formatted in JSON mode."""
        args = argparse.Namespace(
            preset=None,  # Missing preset should cause error
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=True,
            compact=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 1

        captured = capsys.readouterr()

        # Should output valid JSON with error information
        try:
            error_data = json.loads(captured.out)
            assert error_data.get('status') == 'error'
            assert 'message' in error_data
        except json.JSONDecodeError:
            pytest.fail("Error output is not valid JSON")

    def test_scope_plan_with_nonexistent_module(self, sample_scope_codebase, capsys):
        """Test --plan preset with module that doesn't exist in docs."""
        args = argparse.Namespace(
            preset='plan',
            module='src/nonexistent.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Implementation may return error or handle gracefully
        # Just verify it doesn't crash
        assert result in [0, 1]

    def test_scope_implement_with_nonexistent_function(self, sample_scope_codebase, capsys):
        """Test --implement preset with function that doesn't exist."""
        args = argparse.Namespace(
            preset='implement',
            module='src/auth.py',
            function='nonexistent_function',
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Implementation may return error or handle gracefully
        # Just verify it doesn't crash
        assert result in [0, 1]

    def test_scope_compact_json_single_line(self, sample_scope_codebase, capsys):
        """Test that compact JSON is truly single-line."""
        args = argparse.Namespace(
            preset='plan',
            module='src/auth.py',
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=True,
            compact=True
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        assert result == 0

        captured = capsys.readouterr()

        # Compact mode should produce single line
        lines = [l for l in captured.out.strip().splitlines() if l.strip()]
        assert len(lines) == 1

    def test_scope_both_presets_invalid(self, sample_scope_codebase, capsys):
        """Test that only one preset can be used at a time."""
        # This test verifies the preset validation logic
        # The actual CLI parser might prevent this, but we test the command logic

        for invalid_preset in ['both', 'planimplement', 'all']:
            args = argparse.Namespace(
                preset=invalid_preset,
                module='src/auth.py',
                function=None,
                docs_path=str(sample_scope_codebase.parent),
                json=False
            )

            printer = PrettyPrinter(verbose=True)

            result = cmd_scope(args, printer)

            # Should reject invalid preset names
            assert result == 1

    def test_scope_empty_module_path(self, sample_scope_codebase, capsys):
        """Test error handling for empty module path."""
        args = argparse.Namespace(
            preset='plan',
            module='',  # Empty string
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Should handle empty module gracefully
        assert result in [0, 1]

    def test_scope_whitespace_module_path(self, sample_scope_codebase, capsys):
        """Test error handling for whitespace-only module path."""
        args = argparse.Namespace(
            preset='plan',
            module='   ',  # Whitespace only
            function=None,
            docs_path=str(sample_scope_codebase.parent),
            json=False
        )

        printer = PrettyPrinter(verbose=True)

        result = cmd_scope(args, printer)

        # Should handle whitespace-only module gracefully
        assert result in [0, 1]

    def test_scope_case_sensitive_preset(self, sample_scope_codebase, capsys):
        """Test that preset names are case-sensitive."""
        for invalid_preset in ['Plan', 'PLAN', 'Implement', 'IMPLEMENT']:
            args = argparse.Namespace(
                preset=invalid_preset,
                module='src/auth.py',
                function=None,
                docs_path=str(sample_scope_codebase.parent),
                json=False
            )

            printer = PrettyPrinter(verbose=True)

            result = cmd_scope(args, printer)

            # Should reject non-lowercase preset names
            assert result == 1

            captured = capsys.readouterr()
            output_text = captured.out + captured.err
            assert 'invalid' in output_text.lower() or 'preset' in output_text.lower()
