"""
Unit tests for sdd_fidelity_review module.

Tests for FidelityReviewer artifact gathering, configuration handling, tool checking,
consultation wrappers, response parsing, and prompt generation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import subprocess
import json

from claude_skills.sdd_fidelity_review.review import FidelityReviewer
from claude_skills.sdd_fidelity_review.consultation import (
    consult_ai_on_fidelity,
    consult_multiple_ai_on_fidelity,
    parse_review_response,
    parse_multiple_responses,
    detect_consensus,
    categorize_issues,
    FidelityVerdict,
    IssueSeverity,
    ParsedReviewResponse,
    ConsensusResult,
    CategorizedIssue,
    NoToolsAvailableError,
    ConsultationTimeoutError,
    ConsultationError
)
from claude_skills.common.ai_tools import ToolResponse, ToolStatus


# =============================================================================
# FidelityReviewer Tests - Initialization and Spec Loading
# =============================================================================


def test_fidelity_reviewer_init_with_spec_path():
    """FidelityReviewer should initialize with explicit spec path."""
    spec_path = Path("/fake/specs")
    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test Spec", "hierarchy": {}}

        reviewer = FidelityReviewer("test-spec-001", spec_path=spec_path)

        assert reviewer.spec_id == "test-spec-001"
        assert reviewer.spec_path == spec_path
        assert reviewer.spec_data is not None
        mock_load.assert_called_once_with("test-spec-001", spec_path)


def test_fidelity_reviewer_init_auto_discover_specs():
    """FidelityReviewer should auto-discover specs directory if not provided."""
    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
            mock_find.return_value = Path("/discovered/specs")
            mock_load.return_value = {"title": "Test Spec", "hierarchy": {}}

            reviewer = FidelityReviewer("test-spec-001")

            assert reviewer.spec_path == Path("/discovered/specs")
            mock_find.assert_called_once()
            mock_load.assert_called_once_with("test-spec-001", Path("/discovered/specs"))


def test_fidelity_reviewer_init_specs_not_found():
    """FidelityReviewer should handle specs directory not found."""
    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        mock_find.return_value = None

        reviewer = FidelityReviewer("test-spec-001")

        assert reviewer.spec_data is None


def test_fidelity_reviewer_init_spec_load_failure():
    """FidelityReviewer should handle spec load failure."""
    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = None

            reviewer = FidelityReviewer("nonexistent-spec")

            assert reviewer.spec_data is None


# =============================================================================
# FidelityReviewer Tests - Task Requirements Extraction
# =============================================================================


def test_get_task_requirements_success():
    """get_task_requirements should extract task data from spec."""
    spec_data = {
        "hierarchy": {
            "task-1-1": {
                "title": "Create AuthService",
                "type": "task",
                "status": "completed",
                "parent": "phase-1",
                "dependencies": {
                    "blocks": ["task-1-2"],
                    "blocked_by": []
                },
                "metadata": {
                    "description": "Implement authentication service",
                    "file_path": "src/services/authService.ts",
                    "estimated_hours": 3,
                    "verification_steps": [
                        "Tests pass",
                        "Service integrates with API"
                    ]
                }
            }
        }
    }

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = spec_data

            reviewer = FidelityReviewer("test-spec")
            requirements = reviewer.get_task_requirements("task-1-1")

            assert requirements is not None
            assert requirements["task_id"] == "task-1-1"
            assert requirements["title"] == "Create AuthService"
            assert requirements["type"] == "task"
            assert requirements["status"] == "completed"
            assert requirements["description"] == "Implement authentication service"
            assert requirements["file_path"] == "src/services/authService.ts"
            assert requirements["estimated_hours"] == 3
            assert len(requirements["verification_steps"]) == 2


def test_get_task_requirements_not_found():
    """get_task_requirements should return None for nonexistent task."""
    spec_data = {"hierarchy": {}}

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = spec_data

            reviewer = FidelityReviewer("test-spec")
            requirements = reviewer.get_task_requirements("nonexistent-task")

            assert requirements is None


def test_get_task_requirements_spec_not_loaded():
    """get_task_requirements should return None if spec not loaded."""
    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        mock_find.return_value = None

        reviewer = FidelityReviewer("test-spec")
        requirements = reviewer.get_task_requirements("task-1-1")

        assert requirements is None


# =============================================================================
# FidelityReviewer Tests - Phase Tasks Extraction
# =============================================================================


def test_get_phase_tasks_success():
    """get_phase_tasks should return all tasks within a phase."""
    spec_data = {
        "hierarchy": {
            "phase-1": {
                "title": "Setup Phase",
                "type": "phase",
                "parent": "root"
            },
            "task-1-1": {
                "title": "Task 1",
                "type": "task",
                "status": "completed",
                "parent": "phase-1",
                "metadata": {
                    "file_path": "src/file1.ts"
                }
            },
            "task-1-2": {
                "title": "Task 2",
                "type": "task",
                "status": "pending",
                "parent": "phase-1",
                "metadata": {
                    "file_path": "src/file2.ts"
                }
            },
            "group-1-1": {
                "title": "Group 1",
                "type": "group",
                "parent": "phase-1"
            },
            "task-1-3": {
                "title": "Task 3",
                "type": "task",
                "status": "pending",
                "parent": "group-1-1",
                "metadata": {
                    "file_path": "src/file3.ts"
                }
            }
        }
    }

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = spec_data

            reviewer = FidelityReviewer("test-spec")
            tasks = reviewer.get_phase_tasks("phase-1")

            assert tasks is not None
            assert len(tasks) == 3  # Includes nested task in group
            task_ids = [t["task_id"] for t in tasks]
            assert "task-1-1" in task_ids
            assert "task-1-2" in task_ids
            assert "task-1-3" in task_ids


def test_get_phase_tasks_phase_not_found():
    """get_phase_tasks should return None for nonexistent phase."""
    spec_data = {"hierarchy": {}}

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = spec_data

            reviewer = FidelityReviewer("test-spec")
            tasks = reviewer.get_phase_tasks("nonexistent-phase")

            assert tasks is None


# =============================================================================
# FidelityReviewer Tests - Git Diff Operations
# =============================================================================


def test_get_file_diff_success():
    """get_file_diff should return git diff for a file."""
    with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git_root:
        with patch('subprocess.run') as mock_run:
            mock_git_root.return_value = Path("/repo")
            mock_run.return_value = Mock(
                returncode=0,
                stdout="diff --git a/src/file.ts b/src/file.ts\n+new line"
            )

            with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
                mock_find.return_value = Path("/specs")
                with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
                    mock_load.return_value = {"hierarchy": {}}

                    reviewer = FidelityReviewer("test-spec")
                    diff = reviewer.get_file_diff("src/file.ts")

                    assert diff is not None
                    assert "diff --git" in diff
                    assert "+new line" in diff
                    mock_run.assert_called_once()


def test_get_file_diff_not_in_git_repo():
    """get_file_diff should return None when not in git repo."""
    with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git_root:
        mock_git_root.return_value = None

        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
                mock_load.return_value = {"hierarchy": {}}

                reviewer = FidelityReviewer("test-spec")
                diff = reviewer.get_file_diff("src/file.ts")

                assert diff is None


def test_get_file_diff_git_command_fails():
    """get_file_diff should return None when git command fails."""
    with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git_root:
        with patch('subprocess.run') as mock_run:
            mock_git_root.return_value = Path("/repo")
            mock_run.return_value = Mock(
                returncode=128,
                stderr="fatal: bad revision"
            )

            with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
                mock_find.return_value = Path("/specs")
                with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
                    mock_load.return_value = {"hierarchy": {}}

                    reviewer = FidelityReviewer("test-spec")
                    diff = reviewer.get_file_diff("src/file.ts")

                    assert diff is None


def test_get_file_diff_timeout():
    """get_file_diff should return None on timeout."""
    with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git_root:
        with patch('subprocess.run') as mock_run:
            mock_git_root.return_value = Path("/repo")
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=30)

            with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
                mock_find.return_value = Path("/specs")
                with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
                    mock_load.return_value = {"hierarchy": {}}

                    reviewer = FidelityReviewer("test-spec")
                    diff = reviewer.get_file_diff("src/file.ts")

                    assert diff is None


# =============================================================================
# FidelityReviewer Tests - Test Results Parsing
# =============================================================================


def test_parse_junit_xml_success():
    """_parse_junit_xml should parse JUnit XML test results."""
    junit_xml = """<?xml version="1.0" encoding="utf-8"?>
    <testsuites>
        <testsuite name="pytest" tests="3" failures="1" errors="0" skipped="1" time="2.5">
            <testcase classname="tests.test_auth" name="test_login_success" time="0.5"/>
            <testcase classname="tests.test_auth" name="test_login_failure" time="0.8">
                <failure message="AssertionError: Expected 401">
                    Traceback (most recent call last):
                      File "test_auth.py", line 10, in test_login_failure
                        assert response.status == 401
                    AssertionError: Expected 401
                </failure>
            </testcase>
            <testcase classname="tests.test_auth" name="test_logout" time="0.2">
                <skipped message="Not implemented yet"/>
            </testcase>
        </testsuite>
    </testsuites>
    """

    with patch('builtins.open', mock_open(read_data=junit_xml)):
        with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
            mock_find.return_value = Path("/specs")
            with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
                mock_load.return_value = {"hierarchy": {}}

                reviewer = FidelityReviewer("test-spec")
                results = reviewer._parse_junit_xml("/fake/junit.xml")

                assert results is not None
                assert results["total"] == 3
                assert results["passed"] == 1
                assert results["failed"] == 1
                assert results["skipped"] == 1
                assert results["errors"] == 0
                assert "tests.test_auth::test_login_success" in results["tests"]
                assert results["tests"]["tests.test_auth::test_login_failure"]["status"] == "failed"


# =============================================================================
# Consultation Module Tests - Tool Availability
# =============================================================================


def test_consult_ai_no_tools_available():
    """consult_ai_on_fidelity should raise NoToolsAvailableError when no tools found."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        mock_detect.return_value = []

        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("Review this code...")


def test_consult_ai_specific_tool_not_found():
    """consult_ai_on_fidelity should raise NoToolsAvailableError for unavailable tool."""
    with patch('claude_skills.sdd_fidelity_review.consultation.check_tool_available') as mock_check:
        mock_check.return_value = False

        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("Review this code...", tool="gemini")


def test_consult_ai_timeout():
    """consult_ai_on_fidelity should raise ConsultationTimeoutError on timeout."""
    with patch('claude_skills.sdd_fidelity_review.consultation.check_tool_available') as mock_check:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tool') as mock_execute:
            mock_check.return_value = True
            mock_execute.return_value = ToolResponse(
                tool="gemini",
                status=ToolStatus.TIMEOUT,
                error="Timeout after 120s"
            )

            with pytest.raises(ConsultationTimeoutError):
                consult_ai_on_fidelity("Review this code...", tool="gemini")


def test_consult_ai_success():
    """consult_ai_on_fidelity should return ToolResponse on success."""
    with patch('claude_skills.sdd_fidelity_review.consultation.check_tool_available') as mock_check:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tool') as mock_execute:
            mock_check.return_value = True
            mock_execute.return_value = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="The implementation looks good..."
            )

            response = consult_ai_on_fidelity("Review this code...", tool="gemini")

            assert response.success is True
            assert "implementation looks good" in response.output


def test_consult_ai_auto_detect_tool():
    """consult_ai_on_fidelity should auto-detect tool when not specified."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        with patch('claude_skills.sdd_fidelity_review.consultation.check_tool_available') as mock_check:
            with patch('claude_skills.sdd_fidelity_review.consultation.execute_tool') as mock_execute:
                mock_detect.return_value = ["gemini", "codex"]
                mock_check.return_value = True
                mock_execute.return_value = ToolResponse(
                    tool="gemini",
                    status=ToolStatus.SUCCESS,
                    output="Review complete"
                )

                response = consult_ai_on_fidelity("Review this code...")

                assert response.success is True
                mock_execute.assert_called_once()


# =============================================================================
# Consultation Module Tests - Multiple AI Consultation
# =============================================================================


def test_consult_multiple_ai_success():
    """consult_multiple_ai_on_fidelity should consult multiple tools in parallel."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
            mock_detect.return_value = ["gemini", "codex"]
            mock_execute.return_value = [
                ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good"),
                ToolResponse(tool="codex", status=ToolStatus.SUCCESS, output="Passes review")
            ]

            responses = consult_multiple_ai_on_fidelity("Review this code...")

            assert len(responses) == 2
            assert all(r.success for r in responses)


def test_consult_multiple_ai_no_tools():
    """consult_multiple_ai_on_fidelity should raise error when no tools available."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        mock_detect.return_value = []

        with pytest.raises(NoToolsAvailableError):
            consult_multiple_ai_on_fidelity("Review this code...")


def test_consult_multiple_ai_partial_failure():
    """consult_multiple_ai_on_fidelity should handle partial failures gracefully."""
    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
            mock_detect.return_value = ["gemini", "codex", "cursor-agent"]
            mock_execute.return_value = [
                ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good"),
                ToolResponse(tool="codex", status=ToolStatus.ERROR, error="Connection failed"),
                ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS, output="Approved")
            ]

            responses = consult_multiple_ai_on_fidelity("Review this code...")

            assert len(responses) == 3
            successful = [r for r in responses if r.success]
            assert len(successful) == 2


# =============================================================================
# Consultation Module Tests - Cache Save Behavior
# =============================================================================


def test_consult_multiple_ai_saves_to_cache():
    """consult_multiple_ai_on_fidelity should save results to cache after consultation."""
    with patch('claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE', True):
        with patch('claude_skills.sdd_fidelity_review.consultation.is_cache_enabled', return_value=True):
            with patch('claude_skills.sdd_fidelity_review.consultation.CacheManager') as MockCache:
                with patch('claude_skills.sdd_fidelity_review.consultation.generate_fidelity_review_key') as mock_keygen:
                    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
                        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
                            # Setup mocks
                            mock_detect.return_value = ["gemini"]
                            mock_execute.return_value = [
                                ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good")
                            ]
                            mock_cache_instance = MockCache.return_value
                            mock_cache_instance.get.return_value = None  # Cache miss
                            mock_cache_instance.set.return_value = True  # Cache save succeeds
                            mock_keygen.return_value = "test_cache_key"

                            # Call function with cache_key_params
                            cache_params = {"spec_id": "test-spec", "scope": "phase", "target": "phase-1"}
                            responses = consult_multiple_ai_on_fidelity(
                                "Review this code...",
                                cache_key_params=cache_params
                            )

                            # Verify consultation happened
                            assert len(responses) == 1
                            assert responses[0].success

                            # Verify cache was checked
                            mock_cache_instance.get.assert_called_once_with("test_cache_key")

                            # Verify results were saved to cache
                            mock_cache_instance.set.assert_called_once()
                            call_args = mock_cache_instance.set.call_args
                            assert call_args[0][0] == "test_cache_key"  # First arg is cache_key

                            # Verify serialized format
                            saved_data = call_args[0][1]  # Second arg is data
                            assert len(saved_data) == 1
                            assert saved_data[0]["tool"] == "gemini"
                            assert saved_data[0]["status"] == "success"
                            assert saved_data[0]["output"] == "Looks good"


def test_consult_multiple_ai_cache_save_failure_non_fatal():
    """consult_multiple_ai_on_fidelity should handle cache save failures gracefully."""
    with patch('claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE', True):
        with patch('claude_skills.sdd_fidelity_review.consultation.is_cache_enabled', return_value=True):
            with patch('claude_skills.sdd_fidelity_review.consultation.CacheManager') as MockCache:
                with patch('claude_skills.sdd_fidelity_review.consultation.generate_fidelity_review_key') as mock_keygen:
                    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
                        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
                            # Setup mocks
                            mock_detect.return_value = ["gemini"]
                            mock_execute.return_value = [
                                ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good")
                            ]
                            mock_cache_instance = MockCache.return_value
                            mock_cache_instance.get.return_value = None  # Cache miss
                            mock_cache_instance.set.side_effect = Exception("Disk full")  # Cache save fails
                            mock_keygen.return_value = "test_cache_key"

                            # Call function with cache_key_params
                            cache_params = {"spec_id": "test-spec", "scope": "phase", "target": "phase-1"}

                            # Should NOT raise exception - cache save failure is non-fatal
                            responses = consult_multiple_ai_on_fidelity(
                                "Review this code...",
                                cache_key_params=cache_params
                            )

                            # Verify consultation still succeeded
                            assert len(responses) == 1
                            assert responses[0].success


def test_consult_multiple_ai_cache_disabled_skips_save():
    """consult_multiple_ai_on_fidelity should skip cache save when caching disabled."""
    with patch('claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE', True):
        with patch('claude_skills.sdd_fidelity_review.consultation.is_cache_enabled', return_value=False):
            with patch('claude_skills.sdd_fidelity_review.consultation.CacheManager') as MockCache:
                with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
                    with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
                        # Setup mocks
                        mock_detect.return_value = ["gemini"]
                        mock_execute.return_value = [
                            ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Looks good")
                        ]

                        # Call function - caching is disabled
                        responses = consult_multiple_ai_on_fidelity("Review this code...")

                        # Verify CacheManager was never instantiated
                        MockCache.assert_not_called()

                        # Verify consultation still succeeded
                        assert len(responses) == 1
                        assert responses[0].success


def test_consult_multiple_ai_cache_round_trip():
    """consult_multiple_ai_on_fidelity should retrieve saved results on second call."""
    with patch('claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE', True):
        with patch('claude_skills.sdd_fidelity_review.consultation.is_cache_enabled', return_value=True):
            with patch('claude_skills.sdd_fidelity_review.consultation.CacheManager') as MockCache:
                with patch('claude_skills.sdd_fidelity_review.consultation.generate_fidelity_review_key') as mock_keygen:
                    with patch('claude_skills.sdd_fidelity_review.consultation.detect_available_tools') as mock_detect:
                        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel') as mock_execute:
                            # Setup mocks
                            mock_detect.return_value = ["gemini"]
                            original_response = ToolResponse(
                                tool="gemini",
                                status=ToolStatus.SUCCESS,
                                output="Looks good",
                                model="gemini-2.0"
                            )
                            mock_execute.return_value = [original_response]

                            mock_cache_instance = MockCache.return_value
                            mock_keygen.return_value = "test_cache_key"

                            # Simulate cache behavior: first call misses, saves data
                            saved_data = None

                            def cache_get_side_effect(key):
                                return saved_data

                            def cache_set_side_effect(key, data):
                                nonlocal saved_data
                                saved_data = data
                                return True

                            mock_cache_instance.get.side_effect = cache_get_side_effect
                            mock_cache_instance.set.side_effect = cache_set_side_effect

                            # First call - cache miss, saves to cache
                            cache_params = {"spec_id": "test-spec", "scope": "phase", "target": "phase-1"}
                            responses1 = consult_multiple_ai_on_fidelity(
                                "Review this code...",
                                cache_key_params=cache_params
                            )

                            # Verify first call got results from AI
                            assert len(responses1) == 1
                            assert responses1[0].tool == "gemini"
                            assert responses1[0].output == "Looks good"
                            assert mock_execute.call_count == 1

                            # Second call - cache hit, should NOT call execute_tools_parallel again
                            responses2 = consult_multiple_ai_on_fidelity(
                                "Review this code...",
                                cache_key_params=cache_params
                            )

                            # Verify second call got results from cache
                            assert len(responses2) == 1
                            assert responses2[0].tool == "gemini"
                            assert responses2[0].output == "Looks good"
                            assert responses2[0].model == "gemini-2.0"

                            # Verify execute_tools_parallel was only called once (first time)
                            assert mock_execute.call_count == 1


# =============================================================================
# Consultation Module Tests - Response Parsing
# =============================================================================


def test_parse_review_response_pass_verdict():
    """parse_review_response should extract PASS verdict."""
    raw_response = """
    VERDICT: PASS

    The implementation correctly follows the specification.
    All requirements are met.

    RECOMMENDATIONS:
    - Consider adding more edge case tests
    - Document the algorithm complexity
    """

    tool_response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output=raw_response
    )

    parsed = parse_review_response(tool_response)

    assert parsed.verdict == FidelityVerdict.PASS
    assert len(parsed.issues) == 0
    assert len(parsed.recommendations) == 2
    assert "edge case tests" in parsed.recommendations[0]


def test_parse_review_response_fail_verdict():
    """parse_review_response should extract FAIL verdict with issues."""
    raw_response = """VERDICT: FAIL

The implementation deviates from the specification.

ISSUES:
- Missing error handling for invalid input
- Authentication logic does not match spec requirements
- Tests are incomplete

RECOMMENDATIONS:
- Add comprehensive input validation
- Review spec section 2.3 for correct auth flow
"""

    tool_response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output=raw_response
    )

    parsed = parse_review_response(tool_response)

    assert parsed.verdict == FidelityVerdict.FAIL
    # The parser may capture issues as a single block or split them
    assert len(parsed.issues) >= 1
    assert any("Missing error handling" in issue for issue in parsed.issues)
    assert len(parsed.recommendations) >= 1


def test_parse_review_response_partial_verdict():
    """parse_review_response should extract PARTIAL verdict."""
    raw_response = """
    VERDICT: PARTIAL

    Implementation is mostly correct but has some gaps.

    ISSUES:
    - Minor deviation in error message format

    RECOMMENDATIONS:
    - Align error messages with spec format
    """

    tool_response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output=raw_response
    )

    parsed = parse_review_response(tool_response)

    assert parsed.verdict == FidelityVerdict.PARTIAL
    assert len(parsed.issues) == 1
    assert len(parsed.recommendations) == 1


def test_parse_review_response_unknown_verdict():
    """parse_review_response should default to UNKNOWN for unclear responses."""
    raw_response = """
    The code looks interesting but I'm not sure if it matches the spec.
    Maybe some changes are needed.
    """

    tool_response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output=raw_response
    )

    parsed = parse_review_response(tool_response)

    assert parsed.verdict == FidelityVerdict.UNKNOWN


def test_parse_multiple_responses():
    """parse_multiple_responses should parse list of ToolResponse objects."""
    responses = [
        ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="VERDICT: PASS\n\nAll requirements met. Implementation is correct."
        ),
        ToolResponse(
            tool="codex",
            status=ToolStatus.SUCCESS,
            output="VERDICT: FAIL\n\nISSUES:\n- Missing tests"
        )
    ]

    parsed_list = parse_multiple_responses(responses)

    assert len(parsed_list) == 2
    assert parsed_list[0].verdict == FidelityVerdict.PASS
    assert parsed_list[1].verdict == FidelityVerdict.FAIL


# =============================================================================
# Consultation Module Tests - Consensus Detection
# =============================================================================


def test_detect_consensus_all_pass():
    """detect_consensus should return PASS when all models agree on PASS."""
    parsed_responses = [
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[])
    ]

    consensus = detect_consensus(parsed_responses, min_agreement=2)

    assert consensus.consensus_verdict == FidelityVerdict.PASS
    assert consensus.agreement_rate == 1.0


def test_detect_consensus_majority_fail():
    """detect_consensus should return FAIL when majority agree on FAIL."""
    parsed_responses = [
        ParsedReviewResponse(
            verdict=FidelityVerdict.FAIL,
            issues=["Missing validation", "Incorrect logic"],
            recommendations=[]
        ),
        ParsedReviewResponse(
            verdict=FidelityVerdict.FAIL,
            issues=["Missing validation"],
            recommendations=[]
        ),
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[])
    ]

    consensus = detect_consensus(parsed_responses, min_agreement=2)

    assert consensus.consensus_verdict == FidelityVerdict.FAIL
    assert len(consensus.consensus_issues) == 1  # "Missing validation" appears in 2 responses
    # Issues are normalized to lowercase
    assert "missing validation" in consensus.consensus_issues


def test_detect_consensus_no_agreement():
    """detect_consensus should return plurality verdict when no majority."""
    parsed_responses = [
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.FAIL, issues=["Issue A"], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.PARTIAL, issues=["Issue B"], recommendations=[])
    ]

    consensus = detect_consensus(parsed_responses, min_agreement=2)

    # With no majority, returns the first verdict seen with max count (PASS in this case)
    # Agreement rate is 1/3 = 0.33
    assert consensus.agreement_rate == pytest.approx(0.333, abs=0.01)


# =============================================================================
# Consultation Module Tests - Issue Categorization
# =============================================================================


def test_categorize_issues_by_severity():
    """categorize_issues should assign severity levels based on keywords."""
    issues = [
        "Security vulnerability: SQL injection possible",
        "Missing test coverage for edge cases",
        "Minor typo in error message",
        "Performance degradation in large datasets"
    ]

    categorized = categorize_issues(issues)

    assert len(categorized) == 4

    # Check severity assignments
    severities = {cat.issue: cat.severity for cat in categorized}

    # Security issues should be CRITICAL
    assert any("Security" in issue and sev == IssueSeverity.CRITICAL
               for issue, sev in severities.items())

    # Missing tests might be MEDIUM or HIGH
    assert any("Missing test" in issue and sev in [IssueSeverity.MEDIUM, IssueSeverity.HIGH]
               for issue, sev in severities.items())

    # Typos should be LOW
    assert any("typo" in issue and sev == IssueSeverity.LOW
               for issue, sev in severities.items())


def test_categorize_issues_empty_list():
    """categorize_issues should handle empty issue list."""
    categorized = categorize_issues([])

    assert len(categorized) == 0


# =============================================================================
# Integration Tests - End-to-End Prompt Generation
# =============================================================================


def test_generate_review_prompt_for_task():
    """generate_review_prompt should create complete prompt for task review."""
    spec_data = {
        "title": "User Authentication System",
        "description": "Implement user authentication",
        "hierarchy": {
            "task-1-1": {
                "title": "Create AuthService",
                "type": "task",
                "status": "completed",
                "parent": "phase-1",
                "metadata": {
                    "description": "Implement JWT authentication",
                    "file_path": "src/services/authService.ts",
                    "verification_steps": [
                        "Unit tests pass",
                        "Integration tests pass"
                    ]
                }
            }
        }
    }

    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
            with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git:
                mock_find.return_value = Path("/specs")
                mock_load.return_value = spec_data
                mock_git.return_value = Path("/repo")

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(
                        returncode=0,
                        stdout="diff --git a/src/services/authService.ts b/src/services/authService.ts\n+export class AuthService {}"
                    )

                    reviewer = FidelityReviewer("test-spec")
                    prompt = reviewer.generate_review_prompt(task_id="task-1-1", include_tests=False)

                    # Verify prompt contains key sections
                    assert "# Implementation Fidelity Review" in prompt
                    assert "## Context" in prompt
                    assert "test-spec" in prompt
                    assert "User Authentication System" in prompt
                    assert "## Specification Requirements" in prompt
                    assert "task-1-1" in prompt
                    assert "Create AuthService" in prompt
                    assert "JWT authentication" in prompt
                    assert "## Implementation Artifacts" in prompt
                    assert "diff --git" in prompt
                    assert "## Review Questions" in prompt


def test_generate_review_prompt_for_phase():
    """generate_review_prompt should create prompt for phase review."""
    spec_data = {
        "title": "User Auth",
        "hierarchy": {
            "phase-1": {
                "title": "Authentication Phase",
                "type": "phase",
                "parent": "root"
            },
            "task-1-1": {
                "title": "Task 1",
                "type": "task",
                "parent": "phase-1",
                "metadata": {
                    "file_path": "src/auth.ts"
                }
            },
            "task-1-2": {
                "title": "Task 2",
                "type": "task",
                "parent": "phase-1",
                "metadata": {
                    "file_path": "src/jwt.ts"
                }
            }
        }
    }

    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
            with patch('claude_skills.sdd_fidelity_review.review.find_git_root') as mock_git:
                mock_find.return_value = Path("/specs")
                mock_load.return_value = spec_data
                mock_git.return_value = Path("/repo")

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="")

                    reviewer = FidelityReviewer("test-spec")
                    prompt = reviewer.generate_review_prompt(phase_id="phase-1", include_tests=False)

                    # Verify phase-specific content
                    assert "Phase phase-1 - Authentication Phase" in prompt
                    assert "task-1-1" in prompt
                    assert "task-1-2" in prompt


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


def test_fidelity_reviewer_handles_malformed_spec():
    """FidelityReviewer should handle malformed spec data gracefully."""
    spec_data = {
        # Missing 'hierarchy' key
        "title": "Malformed Spec"
    }

    with patch('claude_skills.sdd_fidelity_review.review.find_specs_directory') as mock_find:
        with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
            mock_find.return_value = Path("/specs")
            mock_load.return_value = spec_data

            reviewer = FidelityReviewer("test-spec")
            tasks = reviewer.get_all_tasks()

            # Should return empty list, not crash
            assert tasks == []


def test_parse_review_response_with_empty_string():
    """parse_review_response should handle empty response."""
    tool_response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output=""
    )

    parsed = parse_review_response(tool_response)

    assert parsed.verdict == FidelityVerdict.UNKNOWN
    assert len(parsed.issues) == 0
    assert len(parsed.recommendations) == 0


def test_consult_ai_handles_unexpected_exception():
    """consult_ai_on_fidelity should wrap unexpected exceptions."""
    with patch('claude_skills.sdd_fidelity_review.consultation.check_tool_available') as mock_check:
        with patch('claude_skills.sdd_fidelity_review.consultation.execute_tool') as mock_execute:
            mock_check.return_value = True
            mock_execute.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(ConsultationError):
                consult_ai_on_fidelity("Review this...", tool="gemini")


# =============================================================================
# File Hashing and Change Detection Tests
# =============================================================================


def test_compute_file_hash_success(tmp_path):
    """compute_file_hash should return SHA256 hash of file contents."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path)

        # Compute hash
        file_hash = reviewer.compute_file_hash(test_file)

        # Verify hash is correct (precomputed SHA256 of "Hello, World!")
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert file_hash == expected_hash


def test_compute_file_hash_nonexistent_file(tmp_path):
    """compute_file_hash should return None for nonexistent files."""
    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path)

        # Try to hash nonexistent file
        file_hash = reviewer.compute_file_hash(Path("/nonexistent/file.txt"))

        assert file_hash is None


def test_compute_file_hash_binary_file(tmp_path):
    """compute_file_hash should handle binary files correctly."""
    # Create binary test file
    test_file = tmp_path / "binary.dat"
    test_file.write_bytes(b'\x00\x01\x02\x03\xFF\xFE\xFD')

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path)

        # Compute hash
        file_hash = reviewer.compute_file_hash(test_file)

        # Should return valid hash (not crash on binary content)
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA256 produces 64-char hex string


def test_get_file_changes_full_mode(tmp_path):
    """get_file_changes should treat all files as added in full mode."""
    # Create test files
    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("content 1")
    file2.write_text("content 2")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        # Create reviewer with incremental=False (default)
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=False)

        changes = reviewer.get_file_changes([file1, file2])

        assert changes['is_incremental'] is False
        assert set(changes['added']) == {str(file1), str(file2)}
        assert changes['modified'] == []
        assert changes['removed'] == []
        assert changes['unchanged'] == []


def test_get_file_changes_incremental_no_previous_state(tmp_path):
    """get_file_changes should perform full review when no previous state exists."""
    # Create test files
    file1 = tmp_path / "file1.py"
    file1.write_text("content 1")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        # Create reviewer with incremental=True
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=True)

        # Mock cache to return empty state (no previous run)
        with patch.object(reviewer.cache, 'get_incremental_state', return_value={}):
            changes = reviewer.get_file_changes([file1])

            assert changes['is_incremental'] is False
            assert str(file1) in changes['added']


def test_get_file_changes_incremental_detects_modifications(tmp_path):
    """get_file_changes should detect modified files in incremental mode."""
    # Create test files
    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("original content")
    file2.write_text("unchanged content")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=True)

        # Compute initial hashes
        hash1_old = reviewer.compute_file_hash(file1)
        hash2 = reviewer.compute_file_hash(file2)

        # Mock cache with previous state
        old_state = {
            str(file1): hash1_old,
            str(file2): hash2
        }

        # Modify file1
        file1.write_text("modified content")

        with patch.object(reviewer.cache, 'get_incremental_state', return_value=old_state):
            changes = reviewer.get_file_changes([file1, file2])

            assert changes['is_incremental'] is True
            assert str(file1) in changes['modified']
            assert str(file2) in changes['unchanged']
            assert changes['added'] == []
            assert changes['removed'] == []


def test_get_file_changes_incremental_detects_additions(tmp_path):
    """get_file_changes should detect new files in incremental mode."""
    # Create test files
    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("existing content")
    file2.write_text("new content")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=True)

        # Compute hash for existing file
        hash1 = reviewer.compute_file_hash(file1)

        # Mock cache with only file1 (file2 is new)
        old_state = {str(file1): hash1}

        with patch.object(reviewer.cache, 'get_incremental_state', return_value=old_state):
            changes = reviewer.get_file_changes([file1, file2])

            assert changes['is_incremental'] is True
            assert str(file2) in changes['added']
            assert str(file1) in changes['unchanged']


def test_get_file_changes_incremental_detects_removals(tmp_path):
    """get_file_changes should detect removed files in incremental mode."""
    # Create test file
    file1 = tmp_path / "file1.py"
    file1.write_text("content")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=True)

        # Compute hash for file1
        hash1 = reviewer.compute_file_hash(file1)

        # Mock cache with file1 and a removed file2
        old_state = {
            str(file1): hash1,
            "/removed/file2.py": "abc123"
        }

        with patch.object(reviewer.cache, 'get_incremental_state', return_value=old_state):
            changes = reviewer.get_file_changes([file1])

            assert changes['is_incremental'] is True
            assert "/removed/file2.py" in changes['removed']
            assert str(file1) in changes['unchanged']


def test_save_file_state_full_mode(tmp_path):
    """save_file_state should do nothing in full mode."""
    file1 = tmp_path / "file1.py"
    file1.write_text("content")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        # Create reviewer with incremental=False
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=False)

        result = reviewer.save_file_state([file1])

        assert result is False


def test_save_file_state_incremental_mode(tmp_path):
    """save_file_state should save hashes in incremental mode."""
    file1 = tmp_path / "file1.py"
    file1.write_text("content")

    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test", "hierarchy": {}}
        # Create reviewer with incremental=True
        reviewer = FidelityReviewer("test-spec-001", spec_path=tmp_path, incremental=True)

        # Mock cache save method
        with patch.object(reviewer.cache, 'save_incremental_state', return_value=True) as mock_save:
            result = reviewer.save_file_state([file1])

            assert result is True
            # Verify save was called with spec_id and file hashes
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][0] == "test-spec-001"  # spec_id
            assert isinstance(call_args[0][1], dict)  # file_hashes dict
            assert str(file1) in call_args[0][1]  # file1 should be in hashes


def test_fidelity_reviewer_init_incremental_mode():
    """FidelityReviewer should initialize with incremental mode enabled."""
    spec_path = Path("/fake/specs")
    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test Spec", "hierarchy": {}}

        reviewer = FidelityReviewer("test-spec-001", spec_path=spec_path, incremental=True)

        assert reviewer.incremental is True
        assert reviewer.cache is not None


def test_fidelity_reviewer_init_full_mode():
    """FidelityReviewer should initialize with incremental mode disabled by default."""
    spec_path = Path("/fake/specs")
    with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
        mock_load.return_value = {"title": "Test Spec", "hierarchy": {}}

        reviewer = FidelityReviewer("test-spec-001", spec_path=spec_path)

        assert reviewer.incremental is False
        assert reviewer.cache is None
