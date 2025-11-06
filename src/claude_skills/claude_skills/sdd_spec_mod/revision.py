"""
Revision tracking for SDD specifications.

Provides functions for tracking spec versions, creating revision history entries,
and managing spec modifications over time.
"""

import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


def _bump_version(current_version: str) -> str:
    """
    Increment the version number.

    Supports simple X.Y format (e.g., "1.0" -> "1.1", "1.9" -> "2.0").

    Args:
        current_version: Current version string (e.g., "1.0", "2.5")

    Returns:
        Bumped version string

    Raises:
        ValueError: If version format is invalid
    """
    if not current_version:
        return "1.0"

    # Handle simple X.Y format
    parts = current_version.split(".")
    if len(parts) < 2:
        # If just "1", treat as "1.0"
        try:
            major = int(current_version)
            return f"{major}.1"
        except ValueError:
            raise ValueError(f"Invalid version format: {current_version}")

    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid version format: {current_version}")

    # Increment minor version
    minor += 1

    # Roll over to next major version at minor=10
    if minor >= 10:
        major += 1
        minor = 0

    return f"{major}.{minor}"


def _validate_spec_metadata(spec_data: Dict[str, Any]) -> bool:
    """
    Validate that spec data has required metadata structure.

    Args:
        spec_data: The spec data dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(spec_data, dict):
        return False

    if "metadata" not in spec_data:
        return False

    if not isinstance(spec_data["metadata"], dict):
        return False

    return True


def create_revision(
    spec_data: Dict[str, Any],
    changelog: str,
    modified_by: str
) -> Dict[str, Any]:
    """
    Create a new revision entry for the spec.

    Increments the version number and adds a revision entry to
    metadata.revision_history[]. Creates the history array if it
    doesn't exist. The new revision is prepended to the history
    (most recent first).

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        changelog: Description of changes in this revision
        modified_by: Identifier for who made the changes (e.g., email, username)

    Returns:
        Dict with success status and new version:
        {
            "success": True|False,
            "message": "Description of result",
            "version": "X.Y" (new version number, only if success=True)
        }

    Example:
        >>> spec = {"metadata": {"version": "1.0"}}
        >>> result = create_revision(spec, "Added new task", "user@example.com")
        >>> result
        {"success": True, "message": "...", "version": "1.1"}
        >>> spec["metadata"]["version"]
        "1.1"
        >>> len(spec["metadata"]["revision_history"])
        1
    """
    # Validate inputs
    if not _validate_spec_metadata(spec_data):
        return {
            "success": False,
            "message": "Invalid spec data: missing or invalid metadata"
        }

    if not changelog or not isinstance(changelog, str):
        return {
            "success": False,
            "message": "Changelog must be a non-empty string"
        }

    if not modified_by or not isinstance(modified_by, str):
        return {
            "success": False,
            "message": "modified_by must be a non-empty string"
        }

    metadata = spec_data["metadata"]

    # Get current version and bump it
    current_version = metadata.get("version", "0.9")

    try:
        new_version = _bump_version(current_version)
    except ValueError as e:
        return {
            "success": False,
            "message": f"Failed to bump version: {e}"
        }

    # Create revision entry
    date = datetime.now(timezone.utc).isoformat()
    revision_entry = {
        "version": new_version,
        "date": date,
        "modified_by": modified_by,
        "changelog": changelog
    }

    # Initialize revision_history if it doesn't exist
    if "revision_history" not in metadata:
        metadata["revision_history"] = []

    # Prepend new revision (most recent first)
    metadata["revision_history"].insert(0, revision_entry)

    # Update version in metadata
    metadata["version"] = new_version

    return {
        "success": True,
        "message": f"Created revision {new_version}",
        "version": new_version
    }


def get_revision_history(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get the revision history for a spec.

    Returns the list of all revisions with details, ordered from most
    recent to oldest.

    Args:
        spec_data: The full spec data dictionary

    Returns:
        List of revision entries, or empty list if no history exists.
        Each entry contains:
        {
            "version": "X.Y",
            "date": "ISO 8601 timestamp",
            "modified_by": "identifier",
            "changelog": "description of changes"
        }

    Example:
        >>> spec = {"metadata": {"revision_history": [...]}}
        >>> history = get_revision_history(spec)
        >>> len(history)
        3
        >>> history[0]["version"]  # Most recent
        "1.2"
    """
    if not _validate_spec_metadata(spec_data):
        return []

    metadata = spec_data["metadata"]
    return metadata.get("revision_history", [])


def rollback_to_version(
    spec_data: Dict[str, Any],
    target_version: str
) -> Dict[str, Any]:
    """
    Revert spec to a previous version.

    Note: This implementation removes revisions newer than the target version
    from the history but does NOT restore the actual spec content from that
    version. Full snapshot-based rollback would require storing complete spec
    state at each revision, which is not implemented yet.

    This function is a placeholder for future enhancement where snapshots
    would be stored alongside revision entries.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        target_version: Version to rollback to (e.g., "1.3")

    Returns:
        Dict with success status and information:
        {
            "success": True|False,
            "message": "Description of result",
            "version": "X.Y" (version after rollback, only if success=True)
        }

    Example:
        >>> spec = {
        ...     "metadata": {
        ...         "version": "1.5",
        ...         "revision_history": [
        ...             {"version": "1.5", ...},
        ...             {"version": "1.4", ...},
        ...             {"version": "1.3", ...}
        ...         ]
        ...     }
        ... }
        >>> result = rollback_to_version(spec, "1.3")
        >>> result["success"]
        True
        >>> spec["metadata"]["version"]
        "1.3"
    """
    if not _validate_spec_metadata(spec_data):
        return {
            "success": False,
            "message": "Invalid spec data: missing or invalid metadata"
        }

    if not target_version or not isinstance(target_version, str):
        return {
            "success": False,
            "message": "target_version must be a non-empty string"
        }

    metadata = spec_data["metadata"]
    history = metadata.get("revision_history", [])

    if not history:
        return {
            "success": False,
            "message": "No revision history available for rollback"
        }

    # Find the target version in history
    target_index = None
    for i, entry in enumerate(history):
        if entry.get("version") == target_version:
            target_index = i
            break

    if target_index is None:
        return {
            "success": False,
            "message": f"Version {target_version} not found in revision history"
        }

    # Remove all revisions newer than the target
    metadata["revision_history"] = history[target_index:]

    # Update current version
    metadata["version"] = target_version

    return {
        "success": True,
        "message": f"Rolled back to version {target_version} (history trimmed, content not restored)",
        "version": target_version
    }
