"""
Unit tests for sdd_common.integrations module.

Tests cross-skill integration functions: validate_spec_before_proceed,
execute_verify_task, and get_session_state.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import subprocess
import json
from pathlib import Path
from claude_skills.common.integrations import (
    validate_spec_before_proceed,
    execute_verify_task,
    get_session_state,
)
from claude_skills.common.validation import EnhancedError, JsonSpecValidationResult
from claude_skills.common.spec import load_json_spec


class TestValidateSpecBeforeProceed:
    """Tests for validate_spec_before_proceed function."""

    @patch("claude_skills.common.integrations.validate_spec_hierarchy")
    def test_valid_spec(self, mock_validate, tmp_path):
        """Test validation of a valid spec."""
        # Create a temporary spec file
        spec_file = tmp_path / "test.json"
        spec_data = {"spec_id": "test-001", "tasks": {}}
        spec_file.write_text(json.dumps(spec_data))

        mock_validate.return_value = JsonSpecValidationResult(
            spec_id="test-001",
            generated="2025-01-01T00:00:00Z",
            last_updated="2025-01-01T00:00:00Z"
        )

        result = validate_spec_before_proceed(str(spec_file))

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert result["can_autofix"] is False

    @patch("claude_skills.common.integrations.validate_spec_hierarchy")
    def test_spec_with_errors(self, mock_validate, tmp_path):
        """Test validation of spec with errors."""
        # Create a temporary spec file
        spec_file = tmp_path / "test.json"
        spec_data = {"spec_id": "test-001", "tasks": {}}
        spec_file.write_text(json.dumps(spec_data))

        validation_result = JsonSpecValidationResult(
            spec_id="test-001",
            generated="2025-01-01T00:00:00Z",
            last_updated="2025-01-01T00:00:00Z"
        )
        validation_result.structure_errors.append("Missing required field: title")
        mock_validate.return_value = validation_result

        result = validate_spec_before_proceed(str(spec_file))

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "Missing required field: title" in result["errors"][0]["message"]
        assert result["can_autofix"] is True
        assert "sdd-validate" in result["autofix_command"]

    @patch("claude_skills.common.integrations.validate_spec_hierarchy")
    def test_spec_with_warnings(self, mock_validate, tmp_path):
        """Test validation of spec with warnings only."""
        # Create a temporary spec file
        spec_file = tmp_path / "test.json"
        spec_data = {"spec_id": "test-001", "tasks": {}}
        spec_file.write_text(json.dumps(spec_data))

        validation_result = JsonSpecValidationResult(
            spec_id="test-001",
            generated="2025-01-01T00:00:00Z",
            last_updated="2025-01-01T00:00:00Z"
        )
        validation_result.structure_warnings.append("Task has no dependencies")
        mock_validate.return_value = validation_result

        result = validate_spec_before_proceed(str(spec_file))

        assert result["valid"] is True
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["severity"] == "warning"

    def test_file_not_found(self):
        """Test validation when spec file doesn't exist."""
        result = validate_spec_before_proceed("/nonexistent/specs/missing.json")

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0]["message"]

    def test_invalid_json(self, tmp_path):
        """Test validation with invalid JSON."""
        # Create a file with invalid JSON
        spec_file = tmp_path / "bad.json"
        spec_file.write_text("{ invalid json }")

        result = validate_spec_before_proceed(str(spec_file))

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "Invalid JSON" in result["errors"][0]["message"]

    @patch("claude_skills.common.integrations.validate_spec_hierarchy")
    def test_autofix_detection(self, mock_validate, tmp_path):
        """Test detection of auto-fixable issues."""
        # Create a temporary spec file
        spec_file = tmp_path / "test.json"
        spec_data = {"spec_id": "test-001", "tasks": {}}
        spec_file.write_text(json.dumps(spec_data))

        validation_result = JsonSpecValidationResult(
            spec_id="test-001",
            generated="2025-01-01T00:00:00Z",
            last_updated="2025-01-01T00:00:00Z"
        )
        validation_result.structure_errors.append("Invalid status value")
        validation_result.node_errors.append("Timestamp format incorrect")
        mock_validate.return_value = validation_result

        result = validate_spec_before_proceed(str(spec_file))

        assert result["can_autofix"] is True
        assert "auto-fix" in result["autofix_command"]


class TestExecuteVerifyTask:
    """Tests for execute_verify_task function."""

    def test_verify_task_not_found(self):
        """Test execution when verify task doesn't exist."""
        spec_data = {"spec_id": "test-001", "tasks": {}}

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0]

    def test_manual_verification_task(self):
        """Test execution of manual verification task."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Manual check",
                    "metadata": {
                        "verification_type": "manual"
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "manual verification" in result["errors"][0]

    def test_verify_task_no_command_or_skill(self):
        """Test execution when task has no skill or command."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Auto check",
                    "metadata": {
                        "verification_type": "auto"
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "no skill or command" in result["errors"][0]

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_run_tests_skill_success(self, mock_run):
        """Test successful execution with run-tests skill."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Run tests",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "run-tests",
                        "command": "run tests/"
                    }
                }
            }
        }

        mock_run.return_value = Mock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        assert result["skill_used"] == "run-tests"
        assert "All tests passed" in result["output"]
        assert len(result["errors"]) == 0

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_run_tests_skill_failure(self, mock_run):
        """Test failed execution with run-tests skill."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Run tests",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "run-tests",
                        "command": "run tests/"
                    }
                }
            }
        }

        mock_run.return_value = Mock(
            returncode=1,
            stdout="3 tests failed",
            stderr="Error details"
        )

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert result["skill_used"] == "run-tests"
        assert len(result["errors"]) > 0
        assert "failed" in result["errors"][0]

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_command_execution_success(self, mock_run):
        """Test successful direct command execution."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Lint code",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "pylint src/"
                    }
                }
            }
        }

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Your code has been rated at 10/10",
            stderr=""
        )

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        assert result["skill_used"] is None
        assert "10/10" in result["output"]

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_execution_timeout(self, mock_run):
        """Test execution timeout."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Run tests",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "pytest"
                    }
                }
            }
        }

        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "timed out" in result["errors"][0]

    def test_unknown_skill(self):
        """Test execution with unknown skill."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Unknown",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "unknown-skill"
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "Unknown skill" in result["errors"][0]

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_duration_tracking(self, mock_run):
        """Test that execution duration is tracked."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Run tests",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "pytest"
                    }
                }
            }
        }

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert "duration" in result
        assert isinstance(result["duration"], float)
        assert result["duration"] >= 0

    @patch("claude_skills.common.integrations.subprocess.run")
    @patch("claude_skills.common.integrations.time.sleep")
    def test_on_failure_retry_logic(self, mock_sleep, mock_run):
        """Test that retry logic works with on_failure.max_retries."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Flaky test",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "run-tests",
                        "command": "run tests/flaky/",
                        "on_failure": {
                            "max_retries": 2
                        }
                    }
                }
            }
        }

        # First call fails, second call succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout="Failed", stderr=""),
            Mock(returncode=0, stdout="Passed", stderr="")
        ]

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        # When retry succeeds, it returns the successful result with that retry's count
        assert result["retry_count"] == 1
        # The successful retry result should have actions from the retry
        assert "Retrying" in result["actions_taken"] if result["actions_taken"] else True
        mock_sleep.assert_called_once_with(1)
        # Verify that run was called twice (initial + 1 retry)
        assert mock_run.call_count == 2

    @patch("claude_skills.common.integrations.subprocess.run")
    @patch("claude_skills.common.integrations.time.sleep")
    def test_on_failure_max_retries_exhausted(self, mock_sleep, mock_run):
        """Test that all retries are attempted before giving up."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Always fails",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "run-tests",
                        "command": "run failing",
                        "on_failure": {
                            "max_retries": 2
                        }
                    }
                }
            }
        }

        # All calls fail
        mock_run.return_value = Mock(returncode=1, stdout="Failed", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert result["retry_count"] == 2
        assert mock_run.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2
        # Should have retry actions recorded
        retry_actions = [a for a in result["actions_taken"] if "Retrying" in a]
        assert len(retry_actions) == 2

    def test_on_failure_consult_flag(self):
        """Test that consult flag is recorded in actions_taken."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Complex test",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "false",  # Always fails
                        "on_failure": {
                            "consult": True
                        }
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "AI consultation recommended" in result["actions_taken"]
        assert result["on_failure"]["consult"] is True

    def test_on_failure_notification(self):
        """Test that notification method is recorded."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Important test",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "false",
                        "on_failure": {
                            "notify": "slack"
                        }
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "Notification: slack" in result["actions_taken"]

    def test_on_failure_continue_on_failure(self):
        """Test that continue_on_failure flag is recorded."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Non-blocking test",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "false",
                        "on_failure": {
                            "continue_on_failure": True
                        }
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "Continuing with other verifications" in result["actions_taken"]

    def test_on_failure_custom_revert_status(self):
        """Test that custom revert status is stored in result."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "API check",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "curl https://api.example.com",
                        "on_failure": {
                            "revert_status": "blocked"
                        }
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert result["on_failure"]["revert_status"] == "blocked"

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_on_failure_all_actions_combined(self, mock_run):
        """Test that all on_failure actions are recorded together."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Full test",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "run-tests",
                        "command": "run all",
                        "on_failure": {
                            "consult": True,
                            "notify": "email",
                            "continue_on_failure": True,
                            "revert_status": "blocked"
                        }
                    }
                }
            }
        }

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is False
        assert "Notification: email" in result["actions_taken"]
        assert "AI consultation recommended" in result["actions_taken"]
        assert "Continuing with other verifications" in result["actions_taken"]
        assert result["on_failure"]["revert_status"] == "blocked"

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_new_skill_sdd_validate(self, mock_run):
        """Test execution with sdd-validate skill."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Validate spec",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "sdd-validate",
                        "command": "specs/test.json"
                    }
                }
            }
        }

        mock_run.return_value = Mock(returncode=0, stdout="Valid", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        assert result["skill_used"] == "sdd-validate"

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_new_skill_code_doc(self, mock_run):
        """Test execution with code-doc skill."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Check docs",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "code-doc",
                        "command": "stats"
                    }
                }
            }
        }

        mock_run.return_value = Mock(returncode=0, stdout="Docs OK", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        assert result["skill_used"] == "code-doc"

    @patch("claude_skills.common.integrations.subprocess.run")
    def test_new_skill_doc_query(self, mock_run):
        """Test execution with doc-query skill."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Query docs",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "skill": "doc-query",
                        "command": "stats"
                    }
                }
            }
        }

        mock_run.return_value = Mock(returncode=0, stdout="Stats OK", stderr="")

        result = execute_verify_task(spec_data, "verify-1-1")

        assert result["success"] is True
        assert result["skill_used"] == "doc-query"

    def test_hierarchy_lookup(self):
        """Test that verify task is looked up in hierarchy field."""
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "verify-1-1": {
                    "title": "Test in hierarchy",
                    "type": "verify",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "echo hello"
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        # Should not error on not found
        assert "not found" not in str(result["errors"])

    def test_backward_compat_tasks_field(self):
        """Test backward compatibility with tasks field."""
        spec_data = {
            "spec_id": "test-001",
            "tasks": {
                "verify-1-1": {
                    "title": "Test in tasks",
                    "metadata": {
                        "verification_type": "auto",
                        "command": "echo hello"
                    }
                }
            }
        }

        result = execute_verify_task(spec_data, "verify-1-1")

        # Should not error on not found
        assert "not found" not in str(result["errors"])


class TestGetSessionState:
    """Tests for get_session_state function."""

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_no_specs_directory(self, mock_find):
        """Test when specs directory doesn't exist."""
        mock_find.return_value = None

        result = get_session_state()

        assert result["active_specs"] == []
        assert result["last_task"] is None
        assert result["in_progress_count"] == 0

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_active_specs_found(self, mock_find, tmp_path):
        """Test finding active specs with in-progress tasks using hierarchy structure."""
        # Setup test directories
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_find.return_value = str(specs_dir)

        # Create real JSON spec file with modern hierarchy structure
        json_spec_file = active_dir / "test-001.json"
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Test Feature",
                    "status": "in_progress",
                    "type": "spec"
                },
                "task-1-1": {
                    "title": "Task 1",
                    "status": "in_progress",
                    "type": "task"
                },
                "task-1-2": {
                    "title": "Task 2",
                    "status": "pending",
                    "type": "task"
                }
            }
        }
        json_spec_file.write_text(json.dumps(spec_data))

        result = get_session_state(str(specs_dir))

        assert len(result["active_specs"]) == 1
        assert result["active_specs"][0]["spec_id"] == "test-001"
        assert result["active_specs"][0]["title"] == "Test Feature"
        assert result["active_specs"][0]["status"] == "in_progress"
        assert result["active_specs"][0]["in_progress_tasks"] == 1
        assert result["in_progress_count"] == 1
        assert result["last_task"] is not None
        assert result["last_task"]["task_id"] == "task-1-1"
        assert result["last_task"]["title"] == "Task 1"

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_multiple_in_progress_tasks(self, mock_find, tmp_path):
        """Test with multiple in-progress tasks across specs using hierarchy structure."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_find.return_value = str(specs_dir)

        # Create two real JSON specs with hierarchy structure
        json_spec_file1 = active_dir / "test-001.json"
        spec_data1 = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Feature A",
                    "status": "in_progress",
                    "type": "spec"
                },
                "task-1-1": {"title": "Task 1", "status": "in_progress", "type": "task"}
            }
        }
        json_spec_file1.write_text(json.dumps(spec_data1))

        json_spec_file2 = active_dir / "test-002.json"
        spec_data2 = {
            "spec_id": "test-002",
            "hierarchy": {
                "spec-root": {
                    "title": "Feature B",
                    "status": "in_progress",
                    "type": "spec"
                },
                "task-2-1": {"title": "Task 2", "status": "in_progress", "type": "task"}
            }
        }
        json_spec_file2.write_text(json.dumps(spec_data2))

        result = get_session_state(str(specs_dir))

        assert len(result["active_specs"]) == 2
        assert result["in_progress_count"] == 2
        assert result["last_task"] is not None

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_completed_specs_ignored(self, mock_find, tmp_path):
        """Test that completed specs are ignored using hierarchy structure."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_find.return_value = str(specs_dir)

        json_spec_file = active_dir / "test-001.json"
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Completed Feature",
                    "status": "completed",
                    "type": "spec"
                }
            }
        }
        json_spec_file.write_text(json.dumps(spec_data))

        result = get_session_state(str(specs_dir))

        assert len(result["active_specs"]) == 0
        assert result["in_progress_count"] == 0

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_backward_compat_legacy_tasks_structure(self, mock_find, tmp_path):
        """Test backward compatibility with legacy tasks structure."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_find.return_value = str(specs_dir)

        # Create spec with legacy tasks structure (no hierarchy)
        json_spec_file = active_dir / "legacy-001.json"
        spec_data = {
            "spec_id": "legacy-001",
            "title": "Legacy Feature",
            "status": "in_progress",
            "tasks": {
                "task-1": {
                    "title": "Legacy Task",
                    "status": "in_progress"
                }
            }
        }
        json_spec_file.write_text(json.dumps(spec_data))

        result = get_session_state(str(specs_dir))

        # Should still work with legacy structure
        assert len(result["active_specs"]) == 1
        assert result["active_specs"][0]["spec_id"] == "legacy-001"
        assert result["active_specs"][0]["title"] == "Legacy Feature"
        assert result["active_specs"][0]["status"] == "in_progress"
        assert result["active_specs"][0]["in_progress_tasks"] == 1
        assert result["in_progress_count"] == 1
        assert result["last_task"] is not None
        assert result["last_task"]["task_id"] == "task-1"

    @patch("claude_skills.common.paths.find_specs_directory")
    def test_invalid_json_specs_skipped(self, mock_find, tmp_path):
        """Test that invalid JSON specs are skipped gracefully."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_find.return_value = str(specs_dir)

        # Create a JSON spec with invalid content
        json_spec_file = active_dir / "bad.json"
        json_spec_file.write_text("{ invalid json }")

        result = get_session_state(str(specs_dir))

        # Should handle error gracefully
        assert result["active_specs"] == []
