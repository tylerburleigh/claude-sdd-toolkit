"""
Unit tests for revision tracking module.

Tests create_revision(), get_revision_history(), and rollback_to_version()
functions from claude_skills.sdd_spec_mod.revision module.
"""

import pytest
from datetime import datetime
from claude_skills.sdd_spec_mod.revision import (
    create_revision,
    get_revision_history,
    rollback_to_version,
    _bump_version,
    _validate_spec_metadata
)


class TestBumpVersion:
    """Tests for _bump_version() helper function."""

    def test_increment_minor_version(self):
        """Should increment minor version (1.0 -> 1.1)."""
        assert _bump_version("1.0") == "1.1"

    def test_increment_from_1_9_to_2_0(self):
        """Should rollover to next major version (1.9 -> 2.0)."""
        assert _bump_version("1.9") == "2.0"

    def test_increment_from_2_9_to_3_0(self):
        """Should rollover from any major version."""
        assert _bump_version("2.9") == "3.0"

    def test_increment_mid_range(self):
        """Should increment versions in mid-range (1.5 -> 1.6)."""
        assert _bump_version("1.5") == "1.6"

    def test_handle_single_digit_version(self):
        """Should treat '1' as '1.0' and increment to '1.1'."""
        assert _bump_version("1") == "1.1"

    def test_empty_version_defaults_to_1_0(self):
        """Should default empty version to '1.0'."""
        assert _bump_version("") == "1.0"

    def test_invalid_version_raises_error(self):
        """Should raise ValueError for invalid version format."""
        with pytest.raises(ValueError):
            _bump_version("abc")

    def test_invalid_version_with_letters_raises_error(self):
        """Should raise ValueError for version with letters."""
        with pytest.raises(ValueError):
            _bump_version("1.x")


class TestValidateSpecMetadata:
    """Tests for _validate_spec_metadata() helper function."""

    def test_valid_spec_with_metadata(self):
        """Should return True for valid spec with metadata."""
        spec = {"metadata": {}}
        assert _validate_spec_metadata(spec) is True

    def test_missing_metadata_key(self):
        """Should return False when metadata key is missing."""
        spec = {}
        assert _validate_spec_metadata(spec) is False

    def test_metadata_not_dict(self):
        """Should return False when metadata is not a dict."""
        spec = {"metadata": "not a dict"}
        assert _validate_spec_metadata(spec) is False

    def test_none_spec(self):
        """Should return False for None spec."""
        assert _validate_spec_metadata(None) is False

    def test_non_dict_spec(self):
        """Should return False for non-dict spec."""
        assert _validate_spec_metadata("not a dict") is False


class TestCreateRevision:
    """Tests for create_revision() function."""

    def test_create_first_revision(self):
        """Should create first revision and bump version."""
        spec = {"metadata": {"version": "1.0"}}
        result = create_revision(spec, "Initial revision", "test@example.com")

        assert result["success"] is True
        assert result["version"] == "1.1"
        assert spec["metadata"]["version"] == "1.1"
        assert len(spec["metadata"]["revision_history"]) == 1

    def test_create_multiple_revisions(self):
        """Should create multiple revisions in sequence."""
        spec = {"metadata": {"version": "1.0"}}

        # First revision
        result1 = create_revision(spec, "First change", "user@test.com")
        assert result1["version"] == "1.1"

        # Second revision
        result2 = create_revision(spec, "Second change", "user@test.com")
        assert result2["version"] == "1.2"

        # Third revision
        result3 = create_revision(spec, "Third change", "user@test.com")
        assert result3["version"] == "1.3"

        assert len(spec["metadata"]["revision_history"]) == 3

    def test_revision_entry_structure(self):
        """Should create revision entry with correct fields."""
        spec = {"metadata": {"version": "1.0"}}
        result = create_revision(spec, "Test change", "test@example.com")

        entry = spec["metadata"]["revision_history"][0]
        assert "version" in entry
        assert "date" in entry
        assert "modified_by" in entry
        assert "changelog" in entry
        assert entry["version"] == "1.1"
        assert entry["changelog"] == "Test change"
        assert entry["modified_by"] == "test@example.com"

    def test_revision_history_prepends_new_entries(self):
        """Should prepend new revisions (most recent first)."""
        spec = {"metadata": {"version": "1.0"}}

        create_revision(spec, "First", "user@test.com")
        create_revision(spec, "Second", "user@test.com")
        create_revision(spec, "Third", "user@test.com")

        history = spec["metadata"]["revision_history"]
        assert history[0]["changelog"] == "Third"  # Most recent
        assert history[1]["changelog"] == "Second"
        assert history[2]["changelog"] == "First"   # Oldest

    def test_initialize_revision_history_if_missing(self):
        """Should initialize revision_history array if it doesn't exist."""
        spec = {"metadata": {"version": "1.0"}}
        assert "revision_history" not in spec["metadata"]

        create_revision(spec, "First revision", "user@test.com")

        assert "revision_history" in spec["metadata"]
        assert isinstance(spec["metadata"]["revision_history"], list)

    def test_default_version_if_missing(self):
        """Should use default version 0.9 if not present."""
        spec = {"metadata": {}}
        result = create_revision(spec, "Initial", "user@test.com")

        assert result["success"] is True
        assert result["version"] == "1.0"  # 0.9 -> 1.0

    def test_empty_changelog_fails(self):
        """Should fail with empty changelog."""
        spec = {"metadata": {"version": "1.0"}}
        result = create_revision(spec, "", "user@test.com")

        assert result["success"] is False
        assert "Changelog must be a non-empty string" in result["message"]

    def test_empty_modified_by_fails(self):
        """Should fail with empty modified_by."""
        spec = {"metadata": {"version": "1.0"}}
        result = create_revision(spec, "Test", "")

        assert result["success"] is False
        assert "modified_by must be a non-empty string" in result["message"]

    def test_invalid_spec_fails(self):
        """Should fail with invalid spec data."""
        spec = {}
        result = create_revision(spec, "Test", "user@test.com")

        assert result["success"] is False
        assert "Invalid spec data" in result["message"]

    def test_invalid_version_format_fails(self):
        """Should fail with invalid version format."""
        spec = {"metadata": {"version": "invalid"}}
        result = create_revision(spec, "Test", "user@test.com")

        assert result["success"] is False
        assert "Failed to bump version" in result["message"]


class TestGetRevisionHistory:
    """Tests for get_revision_history() function."""

    def test_get_populated_history(self):
        """Should return all revision entries."""
        spec = {"metadata": {"version": "1.0"}}
        create_revision(spec, "First", "user@test.com")
        create_revision(spec, "Second", "user@test.com")

        history = get_revision_history(spec)
        assert len(history) == 2
        assert history[0]["version"] == "1.2"  # Most recent
        assert history[1]["version"] == "1.1"  # Older

    def test_get_empty_history(self):
        """Should return empty list when no history exists."""
        spec = {"metadata": {}}
        history = get_revision_history(spec)

        assert history == []

    def test_get_history_from_invalid_spec(self):
        """Should return empty list for invalid spec."""
        history = get_revision_history({})
        assert history == []

    def test_get_history_from_none_spec(self):
        """Should return empty list for None spec."""
        history = get_revision_history(None)
        assert history == []

    def test_history_entries_have_required_fields(self):
        """Should ensure all entries have required fields."""
        spec = {"metadata": {"version": "1.0"}}
        create_revision(spec, "Test", "user@test.com")

        history = get_revision_history(spec)
        entry = history[0]

        assert "version" in entry
        assert "date" in entry
        assert "modified_by" in entry
        assert "changelog" in entry


class TestRollbackToVersion:
    """Tests for rollback_to_version() function."""

    def test_rollback_to_previous_version(self):
        """Should rollback to specified version."""
        spec = {"metadata": {"version": "1.0"}}

        # Create multiple revisions
        create_revision(spec, "First", "user@test.com")
        create_revision(spec, "Second", "user@test.com")
        create_revision(spec, "Third", "user@test.com")

        # Rollback to 1.1
        result = rollback_to_version(spec, "1.1")

        assert result["success"] is True
        assert result["version"] == "1.1"
        assert spec["metadata"]["version"] == "1.1"

    def test_rollback_trims_newer_revisions(self):
        """Should remove revisions newer than target."""
        spec = {"metadata": {"version": "1.0"}}

        create_revision(spec, "First", "user@test.com")   # 1.1
        create_revision(spec, "Second", "user@test.com")  # 1.2
        create_revision(spec, "Third", "user@test.com")   # 1.3

        # Before rollback: 3 revisions
        assert len(spec["metadata"]["revision_history"]) == 3

        # Rollback to 1.1
        rollback_to_version(spec, "1.1")

        # After rollback: only 1 revision (1.1)
        assert len(spec["metadata"]["revision_history"]) == 1
        assert spec["metadata"]["revision_history"][0]["version"] == "1.1"

    def test_rollback_to_nonexistent_version_fails(self):
        """Should fail when target version not in history."""
        spec = {"metadata": {"version": "1.0"}}
        create_revision(spec, "First", "user@test.com")

        result = rollback_to_version(spec, "5.0")

        assert result["success"] is False
        assert "not found in revision history" in result["message"]

    def test_rollback_with_no_history_fails(self):
        """Should fail when no revision history exists."""
        spec = {"metadata": {"version": "1.0"}}

        result = rollback_to_version(spec, "1.0")

        assert result["success"] is False
        assert "No revision history" in result["message"]

    def test_rollback_with_invalid_spec_fails(self):
        """Should fail with invalid spec data."""
        result = rollback_to_version({}, "1.0")

        assert result["success"] is False
        assert "Invalid spec data" in result["message"]

    def test_rollback_with_empty_version_fails(self):
        """Should fail with empty target version."""
        spec = {"metadata": {"version": "1.0", "revision_history": []}}

        result = rollback_to_version(spec, "")

        assert result["success"] is False
        assert "target_version must be a non-empty string" in result["message"]

    def test_rollback_preserves_target_and_older(self):
        """Should preserve target version and all older revisions."""
        spec = {"metadata": {"version": "1.0"}}

        create_revision(spec, "V1.1", "user@test.com")
        create_revision(spec, "V1.2", "user@test.com")
        create_revision(spec, "V1.3", "user@test.com")
        create_revision(spec, "V1.4", "user@test.com")

        # Rollback to 1.2
        rollback_to_version(spec, "1.2")

        # Should have 2 revisions: 1.2 and 1.1
        history = spec["metadata"]["revision_history"]
        assert len(history) == 2
        assert history[0]["version"] == "1.2"
        assert history[0]["changelog"] == "V1.2"
        assert history[1]["version"] == "1.1"
        assert history[1]["changelog"] == "V1.1"


class TestIntegration:
    """Integration tests for full revision workflow."""

    def test_full_revision_lifecycle(self):
        """Test create, query, and rollback workflow."""
        # Start with fresh spec
        spec = {"metadata": {"version": "1.0"}}

        # Create several revisions
        create_revision(spec, "Added feature A", "dev1@example.com")
        create_revision(spec, "Added feature B", "dev2@example.com")
        create_revision(spec, "Fixed bug in A", "dev1@example.com")

        # Verify current state
        assert spec["metadata"]["version"] == "1.3"
        history = get_revision_history(spec)
        assert len(history) == 3

        # Rollback to previous version
        rollback_to_version(spec, "1.2")

        # Verify rollback
        assert spec["metadata"]["version"] == "1.2"
        history_after = get_revision_history(spec)
        assert len(history_after) == 2

        # Create new revision after rollback
        create_revision(spec, "Alternative fix", "dev3@example.com")

        # Verify new branch
        assert spec["metadata"]["version"] == "1.3"
        final_history = get_revision_history(spec)
        assert len(final_history) == 3
        assert final_history[0]["changelog"] == "Alternative fix"

    def test_revision_timestamps_are_iso8601(self):
        """Ensure revision timestamps are valid ISO 8601 format."""
        spec = {"metadata": {"version": "1.0"}}
        create_revision(spec, "Test", "user@test.com")

        history = get_revision_history(spec)
        date_str = history[0]["date"]

        # Should be parseable as ISO 8601
        parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        assert isinstance(parsed_date, datetime)
