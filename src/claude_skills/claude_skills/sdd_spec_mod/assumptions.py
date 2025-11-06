"""
Assumption management for SDD specifications.

Provides functions for adding, listing, and managing assumptions in spec metadata.
Assumptions track important constraints, requirements, and design decisions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


def add_assumption(
    spec_data: Dict[str, Any],
    text: str,
    assumption_type: str = "requirement",
    added_by: str = "claude-code"
) -> Dict[str, Any]:
    """
    Add an assumption to the spec metadata.

    Creates the assumptions array if it doesn't exist. Assumptions are appended
    to the end of the list (chronological order).

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        text: Description of the assumption
        assumption_type: Type of assumption ("constraint", "requirement", etc.)
        added_by: Identifier for who added the assumption

    Returns:
        Dict with success status and assumption ID:
        {
            "success": True,
            "assumption_id": "assumption-1",
            "message": "Added assumption: <text>"
        }

    Raises:
        ValueError: If spec data is invalid or text is empty
    """
    # Validate spec structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "metadata" not in spec_data:
        raise ValueError("spec_data must have 'metadata' key")

    if not isinstance(spec_data["metadata"], dict):
        raise ValueError("metadata must be a dictionary")

    # Validate inputs
    if not text or not text.strip():
        raise ValueError("assumption text cannot be empty")

    if assumption_type not in ["constraint", "requirement"]:
        raise ValueError(f"Invalid assumption type: {assumption_type}. Must be 'constraint' or 'requirement'")

    if not added_by or not added_by.strip():
        raise ValueError("added_by cannot be empty")

    # Initialize assumptions array if it doesn't exist
    if "assumptions" not in spec_data["metadata"]:
        spec_data["metadata"]["assumptions"] = []

    assumptions = spec_data["metadata"]["assumptions"]

    # Generate assumption ID
    assumption_id = f"assumption-{len(assumptions) + 1}"

    # Create assumption entry
    assumption_entry = {
        "id": assumption_id,
        "text": text.strip(),
        "type": assumption_type,
        "added_by": added_by.strip(),
        "added_at": datetime.now(timezone.utc).isoformat()
    }

    # Add to assumptions array
    assumptions.append(assumption_entry)

    return {
        "success": True,
        "assumption_id": assumption_id,
        "message": f"Added {assumption_type}: {text[:50]}{'...' if len(text) > 50 else ''}"
    }


def list_assumptions(
    spec_data: Dict[str, Any],
    assumption_type: Optional[str] = None
) -> List[Any]:
    """
    List all assumptions from the spec metadata.

    Supports both legacy string format and new structured dict format.

    Args:
        spec_data: The full spec data dictionary
        assumption_type: Optional filter by assumption type (only works with structured format)

    Returns:
        List of assumption entries (can be strings or dicts depending on format)
    """
    if not isinstance(spec_data, dict) or "metadata" not in spec_data:
        return []

    metadata = spec_data.get("metadata", {})
    assumptions = metadata.get("assumptions", [])

    # If filtering by type, only return structured assumptions that match
    if assumption_type:
        # Filter only works on dict assumptions
        return [a for a in assumptions if isinstance(a, dict) and a.get("type") == assumption_type]

    return assumptions


def remove_assumption(
    spec_data: Dict[str, Any],
    assumption_id: str
) -> Dict[str, Any]:
    """
    Remove an assumption from the spec metadata.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        assumption_id: ID of the assumption to remove

    Returns:
        Dict with success status:
        {
            "success": True,
            "message": "Removed assumption: assumption-1"
        }

    Raises:
        ValueError: If spec data is invalid or assumption not found
    """
    if not isinstance(spec_data, dict) or "metadata" not in spec_data:
        raise ValueError("Invalid spec data")

    assumptions = spec_data["metadata"].get("assumptions", [])

    # Find and remove assumption
    for i, assumption in enumerate(assumptions):
        if assumption.get("id") == assumption_id:
            removed = assumptions.pop(i)
            return {
                "success": True,
                "message": f"Removed {removed.get('type', 'assumption')}: {assumption_id}"
            }

    raise ValueError(f"Assumption not found: {assumption_id}")


def update_assumption(
    spec_data: Dict[str, Any],
    assumption_id: str,
    text: Optional[str] = None,
    assumption_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing assumption's text or type.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        assumption_id: ID of the assumption to update
        text: New text (if provided)
        assumption_type: New type (if provided)

    Returns:
        Dict with success status

    Raises:
        ValueError: If spec data is invalid or assumption not found
    """
    if not isinstance(spec_data, dict) or "metadata" not in spec_data:
        raise ValueError("Invalid spec data")

    assumptions = spec_data["metadata"].get("assumptions", [])

    # Find and update assumption
    for assumption in assumptions:
        if assumption.get("id") == assumption_id:
            if text is not None:
                assumption["text"] = text.strip()
            if assumption_type is not None:
                if assumption_type not in ["constraint", "requirement"]:
                    raise ValueError(f"Invalid assumption type: {assumption_type}")
                assumption["type"] = assumption_type

            # Update timestamp
            assumption["updated_at"] = datetime.now(timezone.utc).isoformat()

            return {
                "success": True,
                "message": f"Updated assumption: {assumption_id}"
            }

    raise ValueError(f"Assumption not found: {assumption_id}")
