from __future__ import annotations

import pytest

from claude_skills.sdd_spec_mod.modification import update_node_field


pytestmark = pytest.mark.unit


def create_minimal_spec() -> dict:
    """Create a minimal valid spec structure for testing."""
    return {
        "spec_id": "test-spec-001",
        "title": "Test Specification",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Test Specification",
                "status": "in_progress",
                "parent": None,
                "children": ["phase-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "description": "Initial phase",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {"estimated_hours": 8},
            },
            "task-1-1": {
                "type": "task",
                "title": "Implement feature X",
                "description": "Add new functionality",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {"file_path": "src/feature.py"},
                "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
            },
        },
    }


class TestUpdateNodeField:
    """Test suite for update_node_field() function."""

    def test_update_title(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "title", "New Feature Title")
        assert result["success"] is True
        assert result["old_value"] == "Implement feature X"
        assert spec["hierarchy"]["task-1-1"]["title"] == "New Feature Title"

    def test_update_description(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "description", "Updated description")
        assert result["success"] is True
        assert result["old_value"] == "Add new functionality"
        assert spec["hierarchy"]["task-1-1"]["description"] == "Updated description"

    def test_update_status(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "status", "in_progress")
        assert result["success"] is True
        assert result["old_value"] == "pending"
        assert spec["hierarchy"]["task-1-1"]["status"] == "in_progress"

    def test_update_status_invalid_value(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "status", "invalid_status")
        assert result["success"] is False
        assert "Invalid status" in result["message"]
        assert spec["hierarchy"]["task-1-1"]["status"] == "pending"

    def test_update_type(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "type", "subtask")
        assert result["success"] is True
        assert result["old_value"] == "task"
        assert spec["hierarchy"]["task-1-1"]["type"] == "subtask"

    def test_update_type_invalid_value(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "type", "invalid_type")
        assert result["success"] is False
        assert "Invalid type" in result["message"]
        assert spec["hierarchy"]["task-1-1"]["type"] == "task"

    def test_update_metadata_merges(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(
            spec,
            "task-1-1",
            "metadata",
            {"estimated_hours": 4, "task_category": "implementation"},
        )
        assert result["success"] is True
        metadata = spec["hierarchy"]["task-1-1"]["metadata"]
        assert metadata["file_path"] == "src/feature.py"
        assert metadata["estimated_hours"] == 4
        assert metadata["task_category"] == "implementation"

    def test_update_metadata_non_dict_fails(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "metadata", "not a dict")
        assert result["success"] is False
        assert "dictionary" in result["message"]

    def test_update_dependencies(self) -> None:
        spec = create_minimal_spec()
        new_deps = {"blocks": ["task-1-2"], "blocked_by": [], "depends": []}
        result = update_node_field(spec, "task-1-1", "dependencies", new_deps)
        assert result["success"] is True
        assert spec["hierarchy"]["task-1-1"]["dependencies"] == new_deps

    def test_update_dependencies_adds_missing_keys(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(
            spec,
            "task-1-1",
            "dependencies",
            {"blocks": ["task-1-2"]},
        )
        assert result["success"] is True
        deps = spec["hierarchy"]["task-1-1"]["dependencies"]
        assert deps["blocks"] == ["task-1-2"]
        assert deps["blocked_by"] == []
        assert deps["depends"] == []

    def test_update_dependencies_non_dict_fails(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "dependencies", ["not", "a", "dict"])
        assert result["success"] is False
        assert "dictionary" in result["message"]

    def test_update_dependencies_invalid_list_fails(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(
            spec,
            "task-1-1",
            "dependencies",
            {"blocks": "not a list", "blocked_by": [], "depends": []},
        )
        assert result["success"] is False
        assert "must be a list" in result["message"]

    def test_update_protected_field_raises_error(self) -> None:
        spec = create_minimal_spec()
        for field in ["parent", "children", "total_tasks", "completed_tasks"]:
            with pytest.raises(ValueError, match="protected field"):
                update_node_field(spec, "task-1-1", field, "new_value")

    def test_update_nonexistent_node_raises_error(self) -> None:
        spec = create_minimal_spec()
        with pytest.raises(KeyError):
            update_node_field(spec, "non-existent", "title", "New Title")

    def test_update_title_empty_fails(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "title", "   ")
        assert result["success"] is False
        assert "empty" in result["message"]
        assert spec["hierarchy"]["task-1-1"]["title"] == "Implement feature X"

    def test_update_title_strips_whitespace(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "title", "  New Title  ")
        assert result["success"] is True
        assert spec["hierarchy"]["task-1-1"]["title"] == "New Title"

    def test_update_custom_field(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "custom_field", "custom value")
        assert result["success"] is True
        assert spec["hierarchy"]["task-1-1"]["custom_field"] == "custom value"

    def test_update_multiple_fields_sequentially(self) -> None:
        spec = create_minimal_spec()
        assert update_node_field(spec, "task-1-1", "title", "New Title")["success"] is True
        assert update_node_field(spec, "task-1-1", "status", "in_progress")["success"] is True
        assert update_node_field(spec, "task-1-1", "description", "New description")["success"] is True
        node = spec["hierarchy"]["task-1-1"]
        assert node["title"] == "New Title"
        assert node["status"] == "in_progress"
        assert node["description"] == "New description"

    def test_update_field_returns_old_value(self) -> None:
        spec = create_minimal_spec()
        result = update_node_field(spec, "task-1-1", "status", "completed")
        assert result["success"] is True
        assert result["old_value"] == "pending"

    def test_update_field_none_old_value(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["task-1-1"].pop("description", None)
        result = update_node_field(spec, "task-1-1", "new_field", "new value")
        assert result["success"] is True
        assert result["old_value"] is None

    def test_update_all_valid_statuses(self) -> None:
        spec = create_minimal_spec()
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        for status in valid_statuses:
            result = update_node_field(spec, "task-1-1", "status", status)
            assert result["success"] is True
            assert spec["hierarchy"]["task-1-1"]["status"] == status

    def test_update_all_valid_types(self) -> None:
        spec = create_minimal_spec()
        valid_types = ["phase", "task", "subtask", "verify", "group", "spec"]
        for node_type in valid_types:
            result = update_node_field(spec, "task-1-1", "type", node_type)
            assert result["success"] is True
            assert spec["hierarchy"]["task-1-1"]["type"] == node_type
