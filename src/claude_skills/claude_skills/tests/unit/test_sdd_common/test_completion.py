"""
Unit tests for completion detection utilities.
"""

import pytest
from claude_skills.common.completion import (
    check_spec_completion,
    get_all_tasks_in_subtree,
    is_task_complete,
    should_prompt_completion,
    count_blocked_tasks,
    format_completion_prompt
)


class TestIsTaskComplete:
    """Tests for is_task_complete() function."""

    def test_completed_task(self):
        """Task with status='completed' should return True."""
        task = {"status": "completed"}
        assert is_task_complete(task) is True

    def test_pending_task(self):
        """Task with status='pending' should return False."""
        task = {"status": "pending"}
        assert is_task_complete(task) is False

    def test_in_progress_task(self):
        """Task with status='in_progress' should return False."""
        task = {"status": "in_progress"}
        assert is_task_complete(task) is False

    def test_blocked_task(self):
        """Task with status='blocked' should return False."""
        task = {"status": "blocked"}
        assert is_task_complete(task) is False

    def test_no_status(self):
        """Task without status field should return False."""
        task = {}
        assert is_task_complete(task) is False

    def test_none_task(self):
        """None task should return False."""
        assert is_task_complete(None) is False


class TestGetAllTasksInSubtree:
    """Tests for get_all_tasks_in_subtree() function."""

    def test_single_task(self):
        """Should find single task node."""
        hierarchy = {
            "task-1": {
                "type": "task",
                "status": "completed",
                "children": []
            }
        }
        result = get_all_tasks_in_subtree(hierarchy, "task-1")
        assert result == ["task-1"]

    def test_nested_tasks(self):
        """Should find all tasks in nested hierarchy."""
        hierarchy = {
            "phase-1": {
                "type": "phase",
                "children": ["task-1", "task-2"]
            },
            "task-1": {
                "type": "task",
                "children": []
            },
            "task-2": {
                "type": "task",
                "children": ["task-2-1"]
            },
            "task-2-1": {
                "type": "task",
                "children": []
            }
        }
        result = get_all_tasks_in_subtree(hierarchy, "phase-1")
        assert set(result) == {"task-1", "task-2", "task-2-1"}

    def test_only_tasks_included(self):
        """Should only include nodes with type='task'."""
        hierarchy = {
            "spec-root": {
                "type": "spec",
                "children": ["phase-1"]
            },
            "phase-1": {
                "type": "phase",
                "children": ["task-1"]
            },
            "task-1": {
                "type": "task",
                "children": []
            }
        }
        result = get_all_tasks_in_subtree(hierarchy, "spec-root")
        assert result == ["task-1"]

    def test_empty_hierarchy(self):
        """Should return empty list for missing node."""
        hierarchy = {}
        result = get_all_tasks_in_subtree(hierarchy, "task-1")
        assert result == []

    def test_node_with_no_children(self):
        """Should handle nodes without children gracefully."""
        hierarchy = {
            "phase-1": {
                "type": "phase"
                # No 'children' key
            }
        }
        result = get_all_tasks_in_subtree(hierarchy, "phase-1")
        assert result == []


class TestCheckSpecCompletion:
    """Tests for check_spec_completion() function."""

    def test_all_tasks_complete(self):
        """Spec with all tasks completed should return is_complete=True."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"],
                    "status": "completed"
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                },
                "task-2": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is True
        assert result["total_tasks"] == 2
        assert result["completed_tasks"] == 2
        assert result["percentage"] == 100
        assert result["incomplete_tasks"] == []
        assert result["can_finalize"] is True
        assert result["error"] is None

    def test_partial_completion(self):
        """Spec with some incomplete tasks should return is_complete=False."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2", "task-3"]
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                },
                "task-2": {
                    "type": "task",
                    "status": "pending",
                    "children": []
                },
                "task-3": {
                    "type": "task",
                    "status": "in_progress",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is False
        assert result["total_tasks"] == 3
        assert result["completed_tasks"] == 1
        assert result["percentage"] == 33
        assert set(result["incomplete_tasks"]) == {"task-2", "task-3"}
        assert result["can_finalize"] is False
        assert result["error"] is None

    def test_empty_spec(self):
        """Spec with no tasks should return is_complete=True."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is True
        assert result["total_tasks"] == 0
        assert result["completed_tasks"] == 0
        assert result["percentage"] == 100
        assert result["incomplete_tasks"] == []
        assert result["can_finalize"] is True

    def test_specific_phase_completion(self):
        """Should check completion of specific phase when phase_id provided."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["phase-1", "phase-2"]
                },
                "phase-1": {
                    "type": "phase",
                    "children": ["task-1-1"],
                    "status": "completed"
                },
                "task-1-1": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                },
                "phase-2": {
                    "type": "phase",
                    "children": ["task-2-1"],
                    "status": "pending"
                },
                "task-2-1": {
                    "type": "task",
                    "status": "pending",
                    "children": []
                }
            }
        }

        # Check phase-1 (should be complete)
        result_phase_1 = check_spec_completion(spec_data, phase_id="phase-1")
        assert result_phase_1["is_complete"] is True
        assert result_phase_1["total_tasks"] == 1
        assert result_phase_1["node_id"] == "phase-1"

        # Check phase-2 (should be incomplete)
        result_phase_2 = check_spec_completion(spec_data, phase_id="phase-2")
        assert result_phase_2["is_complete"] is False
        assert result_phase_2["total_tasks"] == 1
        assert result_phase_2["node_id"] == "phase-2"

    def test_nested_task_hierarchy(self):
        """Should handle multi-level nested task hierarchies."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["phase-1"]
                },
                "phase-1": {
                    "type": "phase",
                    "children": ["task-1"]
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": ["task-1-1", "task-1-2"]
                },
                "task-1-1": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                },
                "task-1-2": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is True
        assert result["total_tasks"] == 3  # task-1, task-1-1, task-1-2
        assert result["completed_tasks"] == 3

    def test_blocked_tasks_not_complete(self):
        """Blocked tasks should not count as complete."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"]
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": []
                },
                "task-2": {
                    "type": "task",
                    "status": "blocked",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is False
        assert result["total_tasks"] == 2
        assert result["completed_tasks"] == 1
        assert "task-2" in result["incomplete_tasks"]

    def test_in_progress_tasks_not_complete(self):
        """In-progress tasks should not count as complete."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1"]
                },
                "task-1": {
                    "type": "task",
                    "status": "in_progress",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is False
        assert result["completed_tasks"] == 0
        assert "task-1" in result["incomplete_tasks"]

    def test_no_spec_data(self):
        """Should handle None or empty spec_data gracefully."""
        result = check_spec_completion(None)

        assert result["is_complete"] is False
        assert result["error"] == "No spec data provided"

    def test_no_hierarchy(self):
        """Should handle spec_data without hierarchy."""
        spec_data = {"spec_id": "test-spec"}

        result = check_spec_completion(spec_data)

        assert result["is_complete"] is False
        assert result["error"] == "No hierarchy found in spec data"

    def test_invalid_phase_id(self):
        """Should handle invalid phase_id gracefully."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": []
                }
            }
        }

        result = check_spec_completion(spec_data, phase_id="nonexistent-phase")

        assert result["is_complete"] is False
        assert "not found" in result["error"]
        assert result["node_id"] == "nonexistent-phase"

    def test_percentage_calculation(self):
        """Should calculate percentage correctly."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2", "task-3", "task-4"]
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "completed", "children": []},
                "task-3": {"type": "task", "status": "completed", "children": []},
                "task-4": {"type": "task", "status": "pending", "children": []}
            }
        }

        result = check_spec_completion(spec_data)

        assert result["percentage"] == 75  # 3/4 = 75%
        assert result["completed_tasks"] == 3
        assert result["total_tasks"] == 4


class TestCountBlockedTasks:
    """Tests for count_blocked_tasks() function."""

    def test_no_blocked_tasks(self):
        """Should return 0 when no tasks are blocked."""
        hierarchy = {
            "spec-root": {
                "type": "spec",
                "children": ["task-1", "task-2"]
            },
            "task-1": {"type": "task", "status": "completed", "children": []},
            "task-2": {"type": "task", "status": "pending", "children": []}
        }

        count, blocked = count_blocked_tasks(hierarchy, "spec-root")

        assert count == 0
        assert blocked == []

    def test_single_blocked_task(self):
        """Should find single blocked task."""
        hierarchy = {
            "spec-root": {
                "type": "spec",
                "children": ["task-1", "task-2"]
            },
            "task-1": {"type": "task", "status": "completed", "children": []},
            "task-2": {"type": "task", "status": "blocked", "children": []}
        }

        count, blocked = count_blocked_tasks(hierarchy, "spec-root")

        assert count == 1
        assert blocked == ["task-2"]

    def test_multiple_blocked_tasks(self):
        """Should find all blocked tasks in hierarchy."""
        hierarchy = {
            "spec-root": {
                "type": "spec",
                "children": ["phase-1"]
            },
            "phase-1": {
                "type": "phase",
                "children": ["task-1", "task-2", "task-3"]
            },
            "task-1": {"type": "task", "status": "blocked", "children": []},
            "task-2": {"type": "task", "status": "completed", "children": []},
            "task-3": {"type": "task", "status": "blocked", "children": []}
        }

        count, blocked = count_blocked_tasks(hierarchy, "spec-root")

        assert count == 2
        assert set(blocked) == {"task-1", "task-3"}

    def test_nested_blocked_tasks(self):
        """Should find blocked tasks in deeply nested hierarchy."""
        hierarchy = {
            "spec-root": {
                "type": "spec",
                "children": ["phase-1"]
            },
            "phase-1": {
                "type": "phase",
                "children": ["task-1"]
            },
            "task-1": {
                "type": "task",
                "status": "completed",
                "children": ["task-1-1"]
            },
            "task-1-1": {
                "type": "task",
                "status": "blocked",
                "children": []
            }
        }

        count, blocked = count_blocked_tasks(hierarchy, "spec-root")

        assert count == 1
        assert blocked == ["task-1-1"]

    def test_invalid_node_id(self):
        """Should handle invalid node ID gracefully."""
        hierarchy = {"spec-root": {"type": "spec", "children": []}}

        count, blocked = count_blocked_tasks(hierarchy, "nonexistent")

        assert count == 0
        assert blocked == []


class TestShouldPromptCompletion:
    """Tests for should_prompt_completion() function."""

    def test_should_prompt_when_complete_and_no_blocks(self):
        """Should prompt when all tasks complete and no blocked tasks."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"],
                    "status": "completed"
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is True
        assert result["is_complete"] is True
        assert result["blocked_count"] == 0
        assert result["blocked_tasks"] == []
        assert "ready" in result["reason"].lower()
        assert result["error"] is None

    def test_should_not_prompt_when_incomplete(self):
        """Should not prompt when tasks are still pending."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"]
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "pending", "children": []}
            }
        }

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is False
        assert result["is_complete"] is False
        assert "not all tasks are complete" in result["reason"].lower()
        assert result["error"] is None

    def test_should_not_prompt_when_blocked_tasks_exist(self):
        """Should not prompt when blocked tasks exist (they count as incomplete)."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"]
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "blocked", "children": []}
            }
        }

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is False
        assert result["is_complete"] is False  # blocked tasks count as incomplete
        # Blocked tasks are reported as incomplete, not counted separately
        assert result["blocked_count"] == 0
        assert "not all tasks are complete" in result["reason"].lower()

    def test_should_not_prompt_when_in_progress(self):
        """Should not prompt when tasks are in progress."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1", "task-2"]
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "in_progress", "children": []}
            }
        }

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is False
        assert result["is_complete"] is False
        assert "remaining" in result["reason"].lower()

    def test_phase_level_prompt_check(self):
        """Should check specific phase completion when phase_id provided."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["phase-1", "phase-2"]
                },
                "phase-1": {
                    "type": "phase",
                    "children": ["task-1-1"],
                    "status": "completed"
                },
                "task-1-1": {"type": "task", "status": "completed", "children": []},
                "phase-2": {
                    "type": "phase",
                    "children": ["task-2-1"],
                    "status": "pending"
                },
                "task-2-1": {"type": "task", "status": "pending", "children": []}
            }
        }

        # Check phase-1 (should prompt)
        result_phase_1 = should_prompt_completion(spec_data, phase_id="phase-1")
        assert result_phase_1["should_prompt"] is True
        assert result_phase_1["node_id"] == "phase-1"

        # Check phase-2 (should not prompt)
        result_phase_2 = should_prompt_completion(spec_data, phase_id="phase-2")
        assert result_phase_2["should_prompt"] is False
        assert result_phase_2["node_id"] == "phase-2"

    def test_all_complete_but_has_blocked_tasks(self):
        """Should not prompt if all non-blocked tasks complete but blocked tasks exist."""
        # Edge case: All tasks that can be completed ARE completed,
        # but there are blocked tasks preventing true completion
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["task-1"]
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": ["task-1-1", "task-1-2"]
                },
                "task-1-1": {"type": "task", "status": "completed", "children": []},
                "task-1-2": {"type": "task", "status": "blocked", "children": []}
            }
        }

        result = should_prompt_completion(spec_data)

        # Blocked tasks count as incomplete in check_spec_completion
        assert result["should_prompt"] is False
        assert result["is_complete"] is False
        assert "remaining" in result["reason"].lower()

    def test_empty_spec_should_prompt(self):
        """Empty spec with no tasks should prompt (edge case)."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": []
                }
            }
        }

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is True
        assert result["is_complete"] is True
        assert result["blocked_count"] == 0

    def test_error_handling_no_spec_data(self):
        """Should handle None spec_data gracefully."""
        result = should_prompt_completion(None)

        assert result["should_prompt"] is False
        assert result["error"] is not None
        assert "cannot check completion" in result["reason"].lower()

    def test_error_handling_no_hierarchy(self):
        """Should handle spec without hierarchy."""
        spec_data = {"spec_id": "test-spec"}

        result = should_prompt_completion(spec_data)

        assert result["should_prompt"] is False
        assert result["error"] is not None

    def test_error_handling_invalid_phase_id(self):
        """Should handle invalid phase_id gracefully."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": []
                }
            }
        }

        result = should_prompt_completion(spec_data, phase_id="nonexistent")

        assert result["should_prompt"] is False
        assert result["error"] is not None
        assert "not found" in result["error"].lower()


class TestFormatCompletionPrompt:
    """Tests for format_completion_prompt() function."""

    def test_spec_level_prompt_with_hours(self):
        """Should generate spec completion prompt with hours input."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "User Authentication System",
                    "children": ["task-1", "task-2"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 15.5
                    }
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert result["requires_input"] is True
        assert "All tasks complete!" in result["prompt_text"]
        assert "Spec: User Authentication System" in result["prompt_text"]
        assert "Progress: 2/2 tasks (100%)" in result["prompt_text"]
        assert "Estimated: 15.5 hours" in result["prompt_text"]
        assert "How many actual hours did this take?" in result["prompt_text"]

        # Check completion context
        context = result["completion_context"]
        assert context["node_id"] == "spec-root"
        assert context["node_type"] == "spec"
        assert context["total_tasks"] == 2
        assert context["completed_tasks"] == 2
        assert context["estimated_hours"] == 15.5
        assert context["has_hours_estimate"] is True

    def test_spec_level_prompt_without_hours_estimate(self):
        """Should generate spec completion prompt without hours when not estimated."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Simple Spec",
                    "children": ["task-1"],
                    "status": "completed"
                    # No metadata with estimated_hours
                },
                "task-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert result["requires_input"] is False
        assert "All tasks complete!" in result["prompt_text"]
        assert "Spec: Simple Spec" in result["prompt_text"]
        assert "Progress: 1/1 tasks (100%)" in result["prompt_text"]
        assert "Estimated:" not in result["prompt_text"]
        assert "How many actual hours" not in result["prompt_text"]
        assert "Mark this spec as complete?" in result["prompt_text"]

        # Check completion context
        context = result["completion_context"]
        assert context["estimated_hours"] is None
        assert context["has_hours_estimate"] is False

    def test_phase_level_prompt_with_hours(self):
        """Should generate phase completion prompt with hours input."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["phase-1"]
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Database Schema Setup",
                    "children": ["task-1-1"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 3
                    }
                },
                "task-1-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data, phase_id="phase-1")

        assert result["error"] is None
        assert result["requires_input"] is True
        assert "All tasks complete!" in result["prompt_text"]
        assert "Phase: Database Schema Setup" in result["prompt_text"]
        assert "Progress: 1/1 tasks (100%)" in result["prompt_text"]
        assert "Estimated: 3 hours" in result["prompt_text"]
        assert "How many actual hours did this take?" in result["prompt_text"]

        # Check completion context
        context = result["completion_context"]
        assert context["node_id"] == "phase-1"
        assert context["node_type"] == "phase"
        assert context["estimated_hours"] == 3
        assert context["has_hours_estimate"] is True

    def test_phase_level_prompt_without_hours(self):
        """Should generate phase completion prompt without hours input."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": ["phase-1"]
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Testing Phase",
                    "children": ["task-1-1"],
                    "status": "completed"
                },
                "task-1-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data, phase_id="phase-1")

        assert result["error"] is None
        assert result["requires_input"] is False
        assert "Phase: Testing Phase" in result["prompt_text"]
        assert "Mark this phase as complete?" in result["prompt_text"]
        assert "How many actual hours" not in result["prompt_text"]

    def test_show_hours_input_disabled(self):
        """Should not show hours input when show_hours_input=False."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "children": ["task-1"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 10
                    }
                },
                "task-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data, show_hours_input=False)

        assert result["error"] is None
        assert result["requires_input"] is False
        assert "Estimated: 10 hours" in result["prompt_text"]  # Still shows estimate
        assert "How many actual hours" not in result["prompt_text"]  # But no input prompt
        assert "Mark this spec as complete?" in result["prompt_text"]

        # Context still includes estimate
        assert result["completion_context"]["estimated_hours"] == 10
        assert result["completion_context"]["has_hours_estimate"] is True

    def test_empty_spec_prompt(self):
        """Should handle empty spec (0 tasks) appropriately."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Empty Spec",
                    "children": []
                }
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert result["requires_input"] is False
        assert "Spec is ready to complete!" in result["prompt_text"]
        assert "Progress: 0/0 tasks (100%)" in result["prompt_text"]

        context = result["completion_context"]
        assert context["total_tasks"] == 0
        assert context["completed_tasks"] == 0

    def test_nested_task_hierarchy(self):
        """Should correctly count nested tasks in prompt."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Nested Spec",
                    "children": ["phase-1"]
                },
                "phase-1": {
                    "type": "phase",
                    "children": ["task-1"]
                },
                "task-1": {
                    "type": "task",
                    "status": "completed",
                    "children": ["task-1-1", "task-1-2"]
                },
                "task-1-1": {"type": "task", "status": "completed", "children": []},
                "task-1-2": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert "Progress: 3/3 tasks (100%)" in result["prompt_text"]

    def test_no_spec_data(self):
        """Should handle None spec_data gracefully."""
        result = format_completion_prompt(None)

        assert result["error"] == "No spec data provided"
        assert result["prompt_text"] == ""
        assert result["requires_input"] is False
        assert result["completion_context"] == {}

    def test_invalid_phase_id(self):
        """Should handle invalid phase_id gracefully."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "children": []
                }
            }
        }

        result = format_completion_prompt(spec_data, phase_id="nonexistent-phase")

        assert result["error"] is not None
        assert "Cannot generate prompt" in result["error"]
        assert "not found" in result["error"].lower()
        assert result["prompt_text"] == ""

    def test_no_hierarchy(self):
        """Should handle spec without hierarchy."""
        spec_data = {"spec_id": "test-spec"}

        result = format_completion_prompt(spec_data)

        assert result["error"] is not None
        assert "Cannot generate prompt" in result["error"]
        assert result["prompt_text"] == ""

    def test_node_without_title(self):
        """Should use 'Untitled' when node has no title."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    # No title field
                    "children": ["task-1"],
                    "status": "completed"
                },
                "task-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert "Spec: Untitled" in result["prompt_text"]

    def test_estimated_hours_zero(self):
        """Should treat 0 estimated hours as no estimate."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "children": ["task-1"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 0
                    }
                },
                "task-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        assert result["error"] is None
        assert result["requires_input"] is False
        assert "Estimated:" not in result["prompt_text"]
        assert result["completion_context"]["has_hours_estimate"] is False
        assert result["completion_context"]["estimated_hours"] is None

    def test_prompt_text_structure(self):
        """Should have properly structured prompt with newlines."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "children": ["task-1"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 5
                    }
                },
                "task-1": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        # Check structure has newlines for readability
        assert "\n" in result["prompt_text"]
        lines = result["prompt_text"].split("\n")

        # Should have multiple lines
        assert len(lines) >= 5

        # First line should be header
        assert lines[0] == "All tasks complete!"

        # Should have blank lines for spacing
        assert "" in lines

    def test_completion_context_completeness(self):
        """Should return complete completion context metadata."""
        spec_data = {
            "spec_id": "test-spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "children": ["task-1", "task-2"],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 8
                    }
                },
                "task-1": {"type": "task", "status": "completed", "children": []},
                "task-2": {"type": "task", "status": "completed", "children": []}
            }
        }

        result = format_completion_prompt(spec_data)

        context = result["completion_context"]

        # All required fields present
        assert "node_id" in context
        assert "node_type" in context
        assert "total_tasks" in context
        assert "completed_tasks" in context
        assert "estimated_hours" in context
        assert "has_hours_estimate" in context

        # Values correct
        assert context["node_id"] == "spec-root"
        assert context["node_type"] == "spec"
        assert context["total_tasks"] == 2
        assert context["completed_tasks"] == 2
        assert context["estimated_hours"] == 8
        assert context["has_hours_estimate"] is True
