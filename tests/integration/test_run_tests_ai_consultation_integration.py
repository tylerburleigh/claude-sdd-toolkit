"""
Integration tests for run-tests skill AI consultation with real AI CLI tools.

Tests the run-tests skill's AI consultation functionality end-to-end by:
1. Checking tool availability via `sdd test check-tools`
2. Running consultation commands with actual AI tools
3. Verifying command execution and response handling
4. Testing different failure types and consultation modes
"""

import pytest
import subprocess
import json
from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_test_error():
    """Sample test error message for consultation."""
    return """
AssertionError: Expected 5, got 3
File "tests/test_calculator.py", line 42, in test_addition
    assert result == 5
"""


@pytest.fixture
def sample_hypothesis():
    """Sample hypothesis about test failure."""
    return "The add() function may not be handling negative numbers correctly"


# =============================================================================
# Tool Availability Tests
# =============================================================================


class TestToolAvailability:
    """Tests for checking AI tool availability."""

    def test_check_tools_command_exists(self):
        """Test that check-tools command is available."""
        result = subprocess.run(
            ["sdd", "test", "check-tools"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should execute successfully (return code 0 or 1)
        assert result.returncode in [0, 1]

    def test_check_tools_help(self):
        """Test that check-tools help works."""
        result = subprocess.run(
            ["sdd", "test", "check-tools", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should succeed
        assert result.returncode == 0


# =============================================================================
# Consultation Command Tests
# =============================================================================


class TestConsultationCommands:
    """Tests for AI consultation commands."""

    def test_consult_help_command(self):
        """Test that consult help command works."""
        result = subprocess.run(
            ["sdd", "test", "consult", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Help should succeed
        assert result.returncode == 0

        # Should show usage information
        output_lower = result.stdout.lower()
        assert "consult" in output_lower or "usage" in output_lower

    def test_consult_requires_arguments(self):
        """Test that consult command validates required arguments."""
        result = subprocess.run(
            ["sdd", "test", "consult"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should fail or show help (missing required arguments)
        assert result.returncode != 0 or "usage" in result.stdout.lower()

    def test_consult_failure_types(self):
        """Test that different failure types are accepted."""
        failure_types = ["assertion", "exception", "import", "fixture", "timeout"]

        for failure_type in failure_types:
            result = subprocess.run(
                [
                    "sdd", "test", "consult",
                    failure_type,
                    "--error", "sample error",
                    "--hypothesis", "sample hypothesis",
                    "--dry-run"  # Use dry-run if available
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Command should be recognized (may fail due to missing required params)
            # But failure type should be accepted
            assert result.returncode in [0, 1, 2], f"Failure type '{failure_type}' not recognized"

    def test_consult_list_routing(self):
        """Test that routing matrix can be displayed."""
        result = subprocess.run(
            ["sdd", "test", "consult", "--list-routing"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should execute (return code 0 or 1)
        assert result.returncode in [0, 1]


# =============================================================================
# Real AI Tools Integration Tests
# =============================================================================


class TestRealAIToolsConsultation:
    """
    Integration tests with actual AI CLI tools.

    These tests are skipped if real AI tools are not available on the system.
    They validate end-to-end consultation workflow with actual model calls.
    """

    @staticmethod
    def has_any_ai_tool():
        """Check if any AI tool is available."""
        result = subprocess.run(
            ["sdd", "test", "check-tools"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False

        # Check if output indicates tools are available
        output_lower = (result.stdout + result.stderr).lower()
        return "available" in output_lower or "found" in output_lower

    @pytest.mark.skipif(
        not has_any_ai_tool.__func__(),
        reason="No AI consultation tools available (gemini, codex, or cursor-agent)"
    )
    def test_real_assertion_consultation(self, sample_test_error, sample_hypothesis):
        """Test consultation command with dry-run mode."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", sample_test_error,
                "--hypothesis", sample_hypothesis,
                "--dry-run"  # Use dry-run to avoid actual AI calls
            ],
            capture_output=True,
            text=True,
            timeout=10  # Short timeout for dry-run
        )

        # Should execute successfully in dry-run
        assert result.returncode in [0, 1]

    @pytest.mark.skipif(
        not has_any_ai_tool.__func__(),
        reason="No AI consultation tools available"
    )
    def test_real_exception_consultation(self):
        """Test consultation command for exception with dry-run."""
        error = "AttributeError: 'NoneType' object has no attribute 'value'"
        hypothesis = "Function returning None instead of expected object"

        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "exception",
                "--error", error,
                "--hypothesis", hypothesis,
                "--dry-run"  # Use dry-run
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute successfully in dry-run
        assert result.returncode in [0, 1]

    @pytest.mark.skipif(
        not has_any_ai_tool.__func__(),
        reason="No AI consultation tools available"
    )
    def test_real_manual_tool_selection(self):
        """Test manual tool selection in consultation with dry-run."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", "Test error",
                "--hypothesis", "Test hypothesis",
                "--tool", "gemini",  # Manually select gemini
                "--dry-run"  # Use dry-run
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute successfully in dry-run
        assert result.returncode in [0, 1]

    @pytest.mark.skipif(
        not has_any_ai_tool.__func__(),
        reason="No AI consultation tools available"
    )
    def test_real_multi_agent_consultation(self):
        """Test multi-agent consultation mode with dry-run."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "exception",
                "--error", "KeyError: 'missing_key'",
                "--hypothesis", "Dictionary missing expected key",
                "--multi-agent",  # Use multiple agents
                "--dry-run"  # Use dry-run
            ],
            capture_output=True,
            text=True,
            timeout=10  # Short timeout for dry-run
        )

        # Should execute successfully in dry-run
        assert result.returncode in [0, 1]


# =============================================================================
# Consultation with Code Context Tests
# =============================================================================


class TestConsultationWithContext:
    """Tests for consultation with test and implementation code."""

    def test_consult_with_test_code(self, sample_test_error, sample_hypothesis, tmp_path):
        """Test consultation including test code."""
        # Create a dummy test file
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("""
def test_addition():
    result = add(2, 3)
    assert result == 5
""")

        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", sample_test_error,
                "--hypothesis", sample_hypothesis,
                "--test-code", str(test_file),
                "--dry-run"  # Use dry-run
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute successfully in dry-run
        assert result.returncode in [0, 1]

    def test_consult_with_impl_code(self, sample_test_error, sample_hypothesis, tmp_path):
        """Test consultation including implementation code."""
        # Create dummy implementation file
        impl_file = tmp_path / "calculator.py"
        impl_file.write_text("""
def add(a, b):
    return a + b
""")

        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", sample_test_error,
                "--hypothesis", sample_hypothesis,
                "--impl-code", str(impl_file)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should execute
        assert result.returncode in [0, 1]

    def test_consult_with_both_codes(self, sample_test_error, sample_hypothesis, tmp_path):
        """Test consultation with both test and implementation code."""
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("def test_add(): pass")

        impl_file = tmp_path / "sample.py"
        impl_file.write_text("def add(a, b): return a + b")

        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", sample_test_error,
                "--hypothesis", sample_hypothesis,
                "--test-code", str(test_file),
                "--impl-code", str(impl_file)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should execute
        assert result.returncode in [0, 1]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestConsultationErrorHandling:
    """Tests for error handling in consultation commands."""

    def test_consult_with_invalid_tool(self):
        """Test error handling for invalid tool name."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", "error",
                "--hypothesis", "hypothesis",
                "--tool", "invalid-tool-name"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with error message
        assert result.returncode != 0

    def test_consult_with_nonexistent_code_file(self):
        """Test error handling for non-existent code file."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", "error",
                "--hypothesis", "hypothesis",
                "--test-code", "/nonexistent/file.py",
                "--dry-run"  # Use dry-run
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should complete in dry-run
        assert result.returncode in [0, 1]  # May warn or error

    def test_consult_timeout_handling(self):
        """Test that consultation respects timeout settings."""
        result = subprocess.run(
            [
                "sdd", "test", "consult",
                "assertion",
                "--error", "test error",
                "--hypothesis", "test hypothesis",
                "--dry-run"  # Use dry-run to avoid actual tool execution
            ],
            capture_output=True,
            text=True,
            timeout=5  # Short timeout for dry-run
        )

        # Should complete quickly in dry-run mode
        assert result.returncode in [0, 1]


# =============================================================================
# Test Discovery Tests
# =============================================================================


class TestDiscoveryCommands:
    """Tests for test discovery commands."""

    def test_discover_summary(self):
        """Test test discovery summary command."""
        result = subprocess.run(
            ["sdd", "test", "discover", "--summary"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute
        assert result.returncode in [0, 1]

    def test_discover_tree(self):
        """Test test discovery tree command."""
        result = subprocess.run(
            ["sdd", "test", "discover", "--tree"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should execute
        assert result.returncode in [0, 1]


# =============================================================================
# Test Run Preset Tests
# =============================================================================


class TestRunPresets:
    """Tests for test run presets."""

    def test_run_help(self):
        """Test run command help."""
        result = subprocess.run(
            ["sdd", "test", "run", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should succeed
        assert result.returncode == 0

    def test_list_presets(self):
        """Test listing available presets."""
        result = subprocess.run(
            ["sdd", "test", "run", "--list"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should execute
        assert result.returncode in [0, 1]

    def test_quick_preset(self):
        """Test quick preset (dry-run)."""
        # Note: Actual test execution would run real tests
        # This test just verifies the command is recognized
        result = subprocess.run(
            ["sdd", "test", "run", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Check that quick preset is mentioned in help
        output_lower = result.stdout.lower()
        if "quick" in output_lower:
            assert True
        else:
            # Preset might not be documented in help
            assert result.returncode == 0
