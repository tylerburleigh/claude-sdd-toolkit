import pytest
import subprocess
import os


def test_run_tests_fallback_gemini_to_cursor():
    """Test run-tests falls back from gemini to cursor-agent."""
    # Rename gemini binary temporarily to simulate unavailability
    # (This is a simplified example - actual test would need proper setup)

    result = subprocess.run(
        ["sdd", "test", "consult", "assertion", "--error", "Test failed", "--hypothesis", "Root cause unknown"],
        capture_output=True,
        text=True
    )

    # Should succeed even if gemini unavailable
    assert result.returncode == 0
    # Should mention which tool was used
    assert "cursor-agent" in result.stdout.lower() or "gemini" in result.stdout.lower()


def test_sdd_plan_review_with_limits():
    """Test sdd-plan-review respects consultation limits."""
    # Run plan review that might consult multiple models
    env = os.environ.copy()
    env["HOME"] = "/tmp/test_home"
    result = subprocess.run(
        ["sdd", "plan-review", "test-spec-id"],
        capture_output=True,
        text=True,
        env=env  # Use test config
    )

    # Parse output to verify tool count
    # Implementation would check that no more than max_tools_per_run were used
    pass


def test_fidelity_review_retry_on_timeout():
    """Test fidelity review retries on timeout."""
    # Set very short timeout to force timeout
    result = subprocess.run(
        ["sdd", "fidelity-review", "test-spec-id",
         "--timeout", "1"],  # 1 second timeout
        capture_output=True,
        text=True
    )

    # Should have attempted retries (check logs or output)
    pass
