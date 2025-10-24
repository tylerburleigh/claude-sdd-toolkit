"""
Tests for lifecycle.py - JSON-only lifecycle management operations.
"""
import pytest
import json
from pathlib import Path

from claude_skills.sdd_update.lifecycle import move_spec, complete_spec
from claude_skills.common.spec import load_json_spec, save_json_spec


class TestMoveSpec:
    """Test move_spec() function."""

    def test_move_spec_to_completed(self, specs_structure):
        """Test moving spec file to completed folder."""
        # Create a test spec file in active folder
        spec_file = specs_structure / "active" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="completed",
            printer=None
        )

        assert result is True
        assert not spec_file.exists()
        assert (specs_structure / "completed" / "test-spec.json").exists()

    def test_move_spec_to_archived(self, specs_structure):
        """Test moving spec file to archived folder."""
        spec_file = specs_structure / "active" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="archived",
            printer=None
        )

        assert result is True
        assert not spec_file.exists()
        assert (specs_structure / "archived" / "test-spec.json").exists()

    def test_move_spec_to_active(self, specs_structure):
        """Test moving spec file to active folder."""
        spec_file = specs_structure / "completed" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="active",
            printer=None
        )

        assert result is True
        assert not spec_file.exists()
        assert (specs_structure / "active" / "test-spec.json").exists()

    def test_move_spec_invalid_target(self, specs_structure):
        """Test moving spec to invalid folder."""
        spec_file = specs_structure / "active" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="invalid-folder",
            printer=None
        )

        assert result is False
        assert spec_file.exists()  # File should remain

    def test_move_spec_file_not_found(self, specs_structure):
        """Test moving non-existent spec file."""
        spec_file = specs_structure / "active" / "nonexistent.json"

        result = move_spec(
            spec_file=spec_file,
            target_folder="completed",
            printer=None
        )

        assert result is False

    def test_move_spec_target_exists(self, specs_structure):
        """Test moving spec when target file already exists."""
        # Create source file
        spec_file = specs_structure / "active" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        # Create target file
        target_file = specs_structure / "completed" / "test-spec.json"
        target_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="completed",
            printer=None
        )

        assert result is False
        assert spec_file.exists()  # Source should remain

    def test_move_spec_dry_run(self, specs_structure):
        """Test dry run doesn't actually move file."""
        spec_file = specs_structure / "active" / "test-spec.json"
        spec_data = {"spec_id": "test", "title": "Test"}
        spec_file.write_text(json.dumps(spec_data))

        result = move_spec(
            spec_file=spec_file,
            target_folder="completed",
            dry_run=True,
            printer=None
        )

        assert result is True
        assert spec_file.exists()  # File should remain in place
        assert not (specs_structure / "completed" / "test-spec.json").exists()


class TestCompleteSpec:
    """Test complete_spec() function."""

    def test_complete_spec_all_tasks_done(self, specs_structure, sample_json_spec_completed):
        """Test completing spec when all tasks are done."""
        spec_id = "completed-spec-2025-01-01-007"

        # Create spec file in active folder
        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_file.write_text(json.dumps(spec_data))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            actual_hours=12.5,
            printer=None
        )

        assert result is True

        # Verify metadata was updated
        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["status"] == "completed"
        assert "completed_date" in spec_data["metadata"]
        assert spec_data["metadata"]["actual_hours"] == 12.5

        # Verify file was moved
        assert not spec_file.exists()
        assert (specs_structure / "completed" / f"{spec_id}.json").exists()

    def test_complete_spec_without_actual_hours(self, specs_structure, sample_json_spec_completed):
        """Test completing spec without providing actual hours."""
        spec_id = "completed-spec-2025-01-01-007"

        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_file.write_text(json.dumps(spec_data))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["status"] == "completed"
        assert "actual_hours" not in spec_data["metadata"]

    def test_complete_spec_incomplete_tasks(self, specs_structure, sample_json_spec_simple):
        """Test completing spec with incomplete tasks fails."""
        spec_id = "simple-spec-2025-01-01-001"

        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_file.write_text(json.dumps(spec_data))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is False

        # Verify metadata was NOT updated
        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data.get("metadata", {}).get("status") != "completed"

        # Verify file was NOT moved
        assert spec_file.exists()

    def test_complete_spec_dry_run(self, specs_structure, sample_json_spec_completed):
        """Test dry run doesn't save changes or move file."""
        spec_id = "completed-spec-2025-01-01-007"

        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_data = load_json_spec(spec_id, specs_structure)
        original_data = spec_data.copy()
        spec_file.write_text(json.dumps(spec_data))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            actual_hours=15.0,
            dry_run=True,
            printer=None
        )

        assert result is True

        # Verify metadata was NOT updated
        spec_data = load_json_spec(spec_id, specs_structure)
        assert "completed" not in spec_data.get("metadata", {}).get("status", "")

        # Verify file was NOT moved
        assert spec_file.exists()
        assert not (specs_structure / "completed" / f"{spec_id}.json").exists()

    def test_complete_spec_creates_metadata(self, specs_structure, sample_json_spec_completed):
        """Test completing spec creates metadata object if it doesn't exist."""
        spec_id = "completed-spec-2025-01-01-007"

        # Remove metadata from state
        spec_data = load_json_spec(spec_id, specs_structure)
        if "metadata" in spec_data:
            del spec_data["metadata"]
        save_json_spec(spec_id, specs_structure, spec_data)

        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_file.write_text(json.dumps(spec_data))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert "metadata" in spec_data
        assert spec_data["metadata"]["status"] == "completed"

    def test_complete_spec_updates_last_updated(self, specs_structure, sample_json_spec_completed):
        """Test completing spec updates last_updated timestamp."""
        spec_id = "completed-spec-2025-01-01-007"

        spec_data_before = load_json_spec(spec_id, specs_structure)
        original_timestamp = spec_data_before.get("last_updated")

        spec_file = specs_structure / "active" / f"{spec_id}.json"
        spec_file.write_text(json.dumps(spec_data_before))

        result = complete_spec(
            spec_id=spec_id,
            spec_file=spec_file,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data_after = load_json_spec(spec_id, specs_structure)
        new_timestamp = spec_data_after.get("last_updated")

        assert new_timestamp != original_timestamp
