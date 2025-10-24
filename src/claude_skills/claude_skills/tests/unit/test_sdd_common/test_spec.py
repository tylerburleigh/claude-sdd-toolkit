"""Unit tests for ``claude_skills.common.spec`` module."""

import json
from pathlib import Path

import pytest

from claude_skills.common import (
    extract_frontmatter,
    load_json_spec,
    save_json_spec,
    backup_json_spec,
    get_node,
)


class TestExtractFrontmatter:
    """Tests for ``extract_frontmatter`` helper."""

    def test_extract_frontmatter_from_json_spec(self, sample_spec_simple):
        result = extract_frontmatter(sample_spec_simple)

        assert result["spec_id"] == "simple-spec-2025-01-01-001"
        assert result["title"] == "Simple Test Spec"
        assert "metadata" in result

    def test_extract_frontmatter_handles_missing_fields(self, tmp_path):
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps({"title": "Untitled"}, indent=2))

        result = extract_frontmatter(spec_file)

        assert result["spec_id"] == "spec"
        assert result["title"] == "Untitled"

    def test_extract_frontmatter_invalid_json(self, tmp_path):
        spec_file = tmp_path / "broken.json"
        spec_file.write_text("{broken json")

        result = extract_frontmatter(spec_file)

        assert "error" in result
        assert "Invalid JSON" in result["error"]

    def test_extract_frontmatter_markdown(self, tmp_path):
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(
            "---\n"
            "spec_id: markdown-spec\n"
            "title: Markdown Spec\n"
            "estimated_hours: 8\n"
            "---\n"
            "\n"
            "# Heading\n"
        )

        result = extract_frontmatter(spec_file)

        assert result["spec_id"] == "markdown-spec"
        assert result["title"] == "Markdown Spec"
        assert result["estimated_hours"] == 8

    def test_extract_frontmatter_missing_file(self, tmp_path):
        spec_file = tmp_path / "missing.json"

        result = extract_frontmatter(spec_file)

        assert result == {"error": f"Spec file not found: {spec_file}"}


class TestLoadJsonSpec:
    """Tests for ``load_json_spec`` function."""

    def test_load_existing_json_spec(self, sample_json_spec_simple, specs_structure):
        """Test loading an existing JSON spec."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        assert spec_data is not None
        assert spec_data["spec_id"] == "simple-spec-2025-01-01-001"
        assert "hierarchy" in spec_data
        assert "generated" in spec_data

    def test_load_nonexistent_json_spec(self, specs_structure):
        """Test loading a non-existent JSON spec returns None."""
        spec_data = load_json_spec("nonexistent-spec", specs_structure)

        assert spec_data is None

    def test_load_invalid_json_spec(self, specs_structure):
        """Test loading an invalid JSON JSON spec."""
        # Create invalid JSON file
        invalid_state = specs_structure / "active" / "invalid-spec.json"
        invalid_state.write_text("{invalid json content")

        spec_data = load_json_spec("invalid-spec", specs_structure)

        assert spec_data is None

    def test_load_json_spec_with_dependencies(self, sample_json_spec_with_deps, specs_structure):
        """Test loading JSON spec with task dependencies."""
        spec_data = load_json_spec("deps-spec-2025-01-01-003", specs_structure)

        assert spec_data is not None
        assert "task-2-2" in spec_data["hierarchy"]
        assert spec_data["hierarchy"]["task-2-2"]["dependencies"]["blocked_by"] == ["task-2-1"]


class TestSaveJsonSpec:
    """Tests for save_json_spec function."""

    def test_save_new_json_spec(self, specs_structure):
        """Test saving to an existing spec file (JSON specs don't support creating new files)."""
        spec_data = {
            "spec_id": "new-spec-2025-01-01-999",
            "title": "New Spec",
            "generated": "2025-01-01T12:00:00",
            "hierarchy": {}
        }

        # JSON specs must exist before saving - create the file first
        spec_file = specs_structure / "active" / "new-spec-2025-01-01-999.json"
        spec_file.write_text(json.dumps(spec_data, indent=2))

        # Now update it
        spec_data["title"] = "Updated Title"
        result = save_json_spec("new-spec-2025-01-01-999", specs_structure, spec_data)

        assert result is True
        assert spec_file.exists()

        # Verify content was updated
        loaded_data = json.loads(spec_file.read_text())
        assert loaded_data["spec_id"] == "new-spec-2025-01-01-999"
        assert loaded_data["title"] == "Updated Title"

    def test_save_updates_existing_json_spec(self, sample_json_spec_simple, specs_structure):
        """Test updating an existing JSON spec."""
        # Load existing
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Modify
        spec_data["title"] = "Modified Title"

        # Save
        result = save_json_spec("simple-spec-2025-01-01-001", specs_structure, spec_data)

        assert result is True

        # Reload and verify
        reloaded = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assert reloaded["title"] == "Modified Title"

    def test_save_json_spec_with_nonexistent_path_creates_dir(self, tmp_path):
        """Test that saving fails when spec file doesn't exist (JSON specs require existing files)."""
        nonexistent_dir = tmp_path / "nonexistent" / "path"
        spec_data = {"spec_id": "test", "hierarchy": {}}

        result = save_json_spec("test", nonexistent_dir, spec_data)

        # Should fail because spec file doesn't exist
        # JSON specs must be created first via sdd-plan, not via save_json_spec
        assert result is False


class TestBackupJsonSpec:
    """Tests for backup_json_spec function."""

    def test_create_backup_of_existing_json_spec(self, sample_json_spec_simple, specs_structure):
        """Test creating a backup of an existing JSON spec."""
        backup_path = backup_json_spec("simple-spec-2025-01-01-001", specs_structure)

        assert backup_path is not None
        assert backup_path.exists()

        # Verify backup content matches original
        original = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        backup_data = json.loads(backup_path.read_text())
        assert backup_data["spec_id"] == original["spec_id"]

    def test_backup_nonexistent_json_spec(self, specs_structure):
        """Test backing up a non-existent JSON spec."""
        result = backup_json_spec("nonexistent-spec", specs_structure)

        assert result is None

    def test_multiple_backups_dont_overwrite(self, sample_json_spec_simple, specs_structure):
        """Test that multiple backups with different suffixes both exist."""
        backup1 = backup_json_spec("simple-spec-2025-01-01-001", specs_structure)
        backup2 = backup_json_spec("simple-spec-2025-01-01-001", specs_structure, suffix=".backup2")

        assert backup1 is not None
        assert backup2 is not None
        assert backup1.exists()
        assert backup2.exists()


class TestGetNode:
    """Tests for get_node function."""

    def test_get_existing_task_node(self, sample_json_spec_simple, specs_structure):
        """Test retrieving an existing task node."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        node = get_node(spec_data, "task-1-1")

        assert node is not None
        assert node["id"] == "task-1-1"
        assert node["type"] == "task"
        assert "metadata" in node

    def test_get_existing_phase_node(self, sample_json_spec_simple, specs_structure):
        """Test retrieving an existing phase node."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        node = get_node(spec_data, "phase-1")

        assert node is not None
        assert node["id"] == "phase-1"
        assert node["type"] == "phase"
        assert "children" in node

    def test_get_nonexistent_node(self, sample_json_spec_simple, specs_structure):
        """Test retrieving a non-existent node returns None."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        node = get_node(spec_data, "nonexistent-node")

        assert node is None

    def test_get_node_from_empty_hierarchy(self):
        """Test retrieving node from state with empty hierarchy."""
        spec_data = {"spec_id": "test", "hierarchy": {}}
        node = get_node(spec_data, "task-1-1")

        assert node is None

    def test_get_node_validates_structure(self, sample_json_spec_simple, specs_structure):
        """Test that retrieved node has expected structure."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        node = get_node(spec_data, "task-1-1")

        # Verify expected fields
        assert "id" in node
        assert "type" in node
        assert "title" in node
        assert "status" in node
        assert "parent" in node


@pytest.mark.integration
class TestJsonSpecIntegration:
    """Integration tests for JSON spec operations."""

    def test_load_modify_save_workflow(self, sample_json_spec_simple, specs_structure):
        """Test complete workflow: load -> modify -> save -> reload."""
        spec_id = "simple-spec-2025-01-01-001"

        # Load
        state = load_json_spec(spec_id, specs_structure)
        assert state is not None

        # Modify task status
        state["hierarchy"]["task-1-1"]["status"] = "completed"

        # Save
        save_result = save_json_spec(spec_id, specs_structure, state)
        assert save_result is True

        # Reload and verify
        reloaded = load_json_spec(spec_id, specs_structure)
        assert reloaded["hierarchy"]["task-1-1"]["status"] == "completed"

    def test_backup_before_modification(self, sample_json_spec_simple, specs_structure):
        """Test backing up state before modifying it."""
        spec_id = "simple-spec-2025-01-01-001"

        # Create backup
        backup_path = backup_json_spec(spec_id, specs_structure)
        assert backup_path is not None
        assert backup_path.exists()

        # Load and modify
        state = load_json_spec(spec_id, specs_structure)
        original_title = state["title"]
        state["title"] = "Modified"

        # Save
        save_json_spec(spec_id, specs_structure, state)

        # Verify backup still has original
        backup_data = json.loads(backup_path.read_text())
        assert backup_data["title"] == original_title
