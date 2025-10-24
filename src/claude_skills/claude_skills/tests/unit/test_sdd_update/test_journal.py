"""
Tests for journal.py - JSON-only journal and metadata operations.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

from claude_skills.sdd_update.journal import add_journal_entry, add_revision_entry, bulk_journal_tasks, sync_metadata_from_state, update_metadata
from claude_skills.common.spec import load_json_spec


class TestAddJournalEntry:
    """Test add_journal_entry() function."""

    def test_add_journal_entry_basic(self, specs_structure, sample_json_spec_simple):
        """Test adding a basic journal entry."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_journal_entry(
            spec_id=spec_id,
            title="Test Entry",
            content="This is a test journal entry",
            specs_dir=specs_structure,
            printer=None
)

        assert result is True

        # Load state and verify journal entry was added
        spec_data = load_json_spec(spec_id, specs_structure)
        assert "journal" in spec_data
        assert len(spec_data["journal"]) == 1

        entry = spec_data["journal"][0]
        assert entry["title"] == "Test Entry"
        assert entry["content"] == "This is a test journal entry"
        assert entry["entry_type"] == "note"
        assert entry["author"] == "claude-code"
        assert "timestamp" in entry
        assert "metadata" in entry

    def test_add_journal_entry_with_task_id(self, specs_structure, sample_json_spec_simple):
        """Test adding journal entry with task reference."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_journal_entry(
            spec_id=spec_id,
            title="Task Started",
            content="Beginning work on task",
            task_id="task-1-1",
            entry_type="status_change",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        entry = spec_data["journal"][0]
        assert entry["task_id"] == "task-1-1"
        assert entry["entry_type"] == "status_change"

    def test_add_journal_entry_custom_author(self, specs_structure, sample_json_spec_simple):
        """Test adding journal entry with custom author."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_journal_entry(
            spec_id=spec_id,
            title="Decision Made",
            content="Decided to use approach A",
            entry_type="decision",
            author="alice@example.com",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        entry = spec_data["journal"][0]
        assert entry["author"] == "alice@example.com"
        assert entry["entry_type"] == "decision"

    def test_add_journal_entry_updates_timestamp(self, specs_structure, sample_json_spec_simple):
        """Test that adding journal entry updates last_updated."""
        spec_id = "simple-spec-2025-01-01-001"

        # Get original timestamp
        spec_data_before = load_json_spec(spec_id, specs_structure)
        original_timestamp = spec_data_before.get("last_updated")

        result = add_journal_entry(
            spec_id=spec_id,
            title="Test",
            content="Test content",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data_after = load_json_spec(spec_id, specs_structure)
        new_timestamp = spec_data_after.get("last_updated")

        # Timestamp should be updated
        assert new_timestamp != original_timestamp

    def test_add_journal_entry_dry_run(self, specs_structure, sample_json_spec_simple):
        """Test dry run mode doesn't save changes."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_journal_entry(
            spec_id=spec_id,
            title="Test",
            content="Test content",
            specs_dir=specs_structure,
            dry_run=True,
            printer=None
        )

        assert result is True

        # Verify no journal entry was added
        spec_data = load_json_spec(spec_id, specs_structure)
        assert "journal" not in spec_data or len(spec_data.get("journal", [])) == 0

    def test_add_journal_entry_invalid_spec(self, specs_structure):
        """Test adding journal entry for non-existent spec."""
        result = add_journal_entry(
            spec_id="nonexistent-spec",
            title="Test",
            content="Test content",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is False


class TestUpdateMetadata:
    """Test update_metadata() function."""

    def test_update_metadata_simple(self, specs_structure, sample_json_spec_simple):
        """Test updating a simple metadata field."""
        spec_id = "simple-spec-2025-01-01-001"

        result = update_metadata(
            spec_id=spec_id,
            key="priority",
            value="high",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["priority"] == "high"

    def test_update_metadata_numeric_value(self, specs_structure, sample_json_spec_simple):
        """Test updating metadata with numeric value."""
        spec_id = "simple-spec-2025-01-01-001"

        result = update_metadata(
            spec_id=spec_id,
            key="progress_percentage",
            value=75,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["progress_percentage"] == 75

    def test_update_metadata_creates_metadata_object(self, specs_structure, sample_json_spec_simple):
        """Test that metadata object is created if it doesn't exist."""
        spec_id = "simple-spec-2025-01-01-001"

        # Ensure metadata doesn't exist initially
        spec_data = load_json_spec(spec_id, specs_structure)
        if "metadata" in spec_data:
            del spec_data["metadata"]
            from claude_skills.common.spec import save_json_spec
            save_json_spec(spec_id, specs_structure, spec_data)

        result = update_metadata(
            spec_id=spec_id,
            key="status",
            value="active",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert "metadata" in spec_data
        assert spec_data["metadata"]["status"] == "active"

    def test_update_metadata_dry_run(self, specs_structure, sample_json_spec_simple):
        """Test dry run doesn't save changes."""
        spec_id = "simple-spec-2025-01-01-001"

        result = update_metadata(
            spec_id=spec_id,
            key="priority",
            value="urgent",
            specs_dir=specs_structure,
            dry_run=True,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert "priority" not in spec_data.get("metadata", {})


class TestAddRevisionEntry:
    """Test add_revision_entry() function."""

    def test_add_revision_entry_basic(self, specs_structure, sample_json_spec_simple):
        """Test adding a basic revision entry."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_revision_entry(
            spec_id=spec_id,
            version="1.1",
            changes="Updated task hierarchy",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert "metadata" in spec_data
        assert "revisions" in spec_data["metadata"]
        assert len(spec_data["metadata"]["revisions"]) == 1

        revision = spec_data["metadata"]["revisions"][0]
        assert revision["version"] == "1.1"
        assert revision["changes"] == "Updated task hierarchy"
        assert revision["author"] == "claude-code"
        assert "date" in revision

    def test_add_revision_entry_custom_author(self, specs_structure, sample_json_spec_simple):
        """Test adding revision with custom author."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_revision_entry(
            spec_id=spec_id,
            version="2.0",
            changes="Major refactoring",
            author="bob@example.com",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        revision = spec_data["metadata"]["revisions"][0]
        assert revision["author"] == "bob@example.com"

    def test_add_revision_entry_multiple(self, specs_structure, sample_json_spec_simple):
        """Test adding multiple revision entries."""
        spec_id = "simple-spec-2025-01-01-001"

        add_revision_entry(
            spec_id=spec_id,
            version="1.1",
            changes="First change",
            specs_dir=specs_structure,
            printer=None
        )

        add_revision_entry(
            spec_id=spec_id,
            version="1.2",
            changes="Second change",
            specs_dir=specs_structure,
            printer=None
        )

        spec_data = load_json_spec(spec_id, specs_structure)
        assert len(spec_data["metadata"]["revisions"]) == 2
        assert spec_data["metadata"]["version"] == "1.2"

    def test_add_revision_entry_dry_run(self, specs_structure, sample_json_spec_simple):
        """Test dry run doesn't save changes."""
        spec_id = "simple-spec-2025-01-01-001"

        result = add_revision_entry(
            spec_id=spec_id,
            version="1.1",
            changes="Test change",
            specs_dir=specs_structure,
            dry_run=True,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert "revisions" not in spec_data.get("metadata", {})


class TestSyncMetadataFromState:
    """Test sync_metadata_from_state() function."""

    def test_sync_metadata_calculates_progress(self, specs_structure, sample_json_spec_simple):
        """Test syncing metadata calculates progress correctly."""
        spec_id = "simple-spec-2025-01-01-001"

        # Mark one task as completed
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data["hierarchy"]["spec-root"]["completed_tasks"] = 1
        spec_data["hierarchy"]["spec-root"]["total_tasks"] = 4
        from claude_skills.common.spec import save_json_spec
        save_json_spec(spec_id, specs_structure, spec_data)

        result = sync_metadata_from_state(
            spec_id=spec_id,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["progress_percentage"] == 25  # 1/4 = 25%

    def test_sync_metadata_sets_completed_status(self, specs_structure, sample_json_spec_simple):
        """Test syncing metadata sets completed status when all tasks done."""
        spec_id = "simple-spec-2025-01-01-001"

        # Mark all tasks as completed
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_data["hierarchy"]["spec-root"]["completed_tasks"] = 4
        spec_data["hierarchy"]["spec-root"]["total_tasks"] = 4
        from claude_skills.common.spec import save_json_spec
        save_json_spec(spec_id, specs_structure, spec_data)

        result = sync_metadata_from_state(
            spec_id=spec_id,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["status"] == "completed"
        assert spec_data["metadata"]["progress_percentage"] == 100

    def test_sync_metadata_finds_current_phase(self, specs_structure, sample_json_spec_simple):
        """Test syncing metadata finds current in-progress phase."""
        spec_id = "simple-spec-2025-01-01-001"

        # Set phase-1 to in_progress
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_data["hierarchy"]["phase-1"]["status"] = "in_progress"
        from claude_skills.common.spec import save_json_spec
        save_json_spec(spec_id, specs_structure, spec_data)

        result = sync_metadata_from_state(
            spec_id=spec_id,
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        assert spec_data["metadata"]["current_phase"] == "phase-1"

    def test_sync_metadata_dry_run(self, specs_structure, sample_json_spec_simple):
        """Test dry run doesn't save changes."""
        spec_id = "simple-spec-2025-01-01-001"

        # Set up data that would trigger updates
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_data["hierarchy"]["spec-root"]["completed_tasks"] = 2
        spec_data["hierarchy"]["spec-root"]["total_tasks"] = 4
        from claude_skills.common.spec import save_json_spec
        save_json_spec(spec_id, specs_structure, spec_data)

        result = sync_metadata_from_state(
            spec_id=spec_id,
            specs_dir=specs_structure,
            dry_run=True,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        # Metadata should not be created/updated in dry run
        assert "progress_percentage" not in spec_data.get("metadata", {})
