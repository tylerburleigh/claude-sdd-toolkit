"""
JSON spec file operations for SDD workflows.
Provides loading, saving, and backup with atomic writes.
"""

import sys
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Union

from .paths import find_spec_file, resolve_spec_file, ensure_backups_directory


def extract_frontmatter(spec_file: Union[str, Path]) -> Dict[str, Any]:
    """Extract metadata/frontmatter information from a specification file.

    Supports both JSON-based specs (current default) and legacy Markdown specs
    that contain a YAML-style frontmatter block delimited by ``---`` markers.

    Args:
        spec_file: Path to the specification file.

    Returns:
        Dictionary containing extracted metadata. On failure, returns a
        dictionary with an ``"error"`` key describing the failure.
    """

    path = Path(spec_file)

    if not path.exists():
        return {"error": f"Spec file not found: {path}"}

    suffix = path.suffix.lower()

    if suffix == ".json":
        return _extract_json_frontmatter(path)

    if suffix in {".md", ".markdown"}:
        return _extract_markdown_frontmatter(path)

    # Default to JSON parsing if extension is unknown but the contents look
    # like JSON, otherwise try Markdown parsing so callers still get useful
    # feedback for atypical file names.
    try:
        return _extract_json_frontmatter(path)
    except Exception:  # pragma: no cover - fallback only
        return _extract_markdown_frontmatter(path)


def _extract_json_frontmatter(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid JSON in spec file {path}: {exc}"}
    except OSError as exc:
        return {"error": f"Error reading spec file {path}: {exc}"}

    if not isinstance(data, dict):
        return {"error": "Spec file must contain a JSON object"}

    result: Dict[str, Any] = {}

    for key in ("spec_id", "title", "generated", "last_updated", "version"):
        value = data.get(key)
        if value is not None:
            result[key] = value

    metadata = data.get("metadata")
    if metadata is not None:
        result["metadata"] = metadata

    # Some generators may store precomputed frontmatter metadata separately.
    extra_frontmatter = data.get("frontmatter")
    if isinstance(extra_frontmatter, dict):
        for key, value in extra_frontmatter.items():
            result.setdefault(key, value)

    if "spec_id" not in result:
        result["spec_id"] = path.stem

    return result


def _extract_markdown_frontmatter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text()
    except OSError as exc:
        return {"error": f"Error reading spec file {path}: {exc}"}

    if not text.strip():
        return {"error": "Spec file is empty"}

    if not text.lstrip().startswith("---"):
        return {"error": "No frontmatter found in spec file"}

    # Split on first two occurrences of the delimiter to isolate the block.
    segments = text.split("---", 2)
    if len(segments) < 3:
        return {"error": "No closing frontmatter delimiter found"}

    frontmatter_block = segments[1]
    lines = frontmatter_block.splitlines()

    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_value: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if not line or line.lstrip().startswith("#"):
            continue

        if not line.startswith(" ") and ":" in line:
            # Commit previous key/value.
            if current_key is not None:
                result[current_key] = _coerce_scalar("\n".join(current_value).strip())

            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            current_value = [value] if value else []
        elif current_key is not None:
            # Continuation of the previous key (indented content).
            current_value.append(line.strip())

    if current_key is not None:
        result[current_key] = _coerce_scalar("\n".join(current_value).strip())

    if "spec_id" not in result:
        result["spec_id"] = path.stem

    return result


def _coerce_scalar(value: str) -> Any:
    if not value:
        return ""

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    for cast in (int, float):
        try:
            return cast(value)
        except (ValueError, TypeError):
            continue

    return value


def load_json_spec(spec_id: str, specs_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Load the JSON spec file for a given spec ID or path.

    Accepts both spec names and paths for maximum flexibility:
    - Spec names (e.g., 'my-spec')
    - Relative paths (e.g., 'specs/pending/my-spec.json')
    - Absolute paths (e.g., '/full/path/to/my-spec.json')

    Args:
        spec_id: Specification ID or path to spec file
        specs_dir: Path to specs directory (optional, auto-detected if not provided)

    Returns:
        Spec data dictionary, or None if not found
    """
    spec_file = resolve_spec_file(spec_id, specs_dir)

    if not spec_file:
        print(f"Error: Spec file not found for: {spec_id}", file=sys.stderr)
        if specs_dir:
            print(f"Searched in: {specs_dir}/pending, {specs_dir}/active, {specs_dir}/completed, {specs_dir}/archived", file=sys.stderr)
        return None

    try:
        with open(spec_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in spec file {spec_file}: {e}", file=sys.stderr)
        return None
    except IOError as e:
        print(f"Error reading spec file {spec_file}: {e}", file=sys.stderr)
        return None


def save_json_spec(
    spec_id: str,
    specs_dir: Optional[Path] = None,
    spec_data: Dict = None,
    backup: bool = True,
    validate: bool = True
) -> bool:
    """
    Save JSON spec file with atomic write and optional backup.

    Accepts both spec names and paths for maximum flexibility.
    Updates the existing spec file in its current location (pending/active/completed/archived).

    Args:
        spec_id: Specification ID or path to spec file
        specs_dir: Path to specs directory (optional, auto-detected if not provided)
        spec_data: Spec data to write
        backup: Create backup before writing (default: True)
        validate: Validate JSON before writing (default: True)

    Returns:
        True if successful, False otherwise
    """
    spec_file = resolve_spec_file(spec_id, specs_dir)

    if not spec_file:
        print(f"Error: Spec file not found for spec_id: {spec_id}", file=sys.stderr)
        print(f"Cannot save - spec file must exist first", file=sys.stderr)
        return False

    # Validate spec data structure if requested
    if validate:
        if not _validate_spec_structure(spec_data):
            print("Error: Spec data failed validation", file=sys.stderr)
            return False

    # Update last_updated timestamp
    spec_data["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Create backup if backup is requested
    if backup:
        if not backup_json_spec(spec_id, specs_dir):
            print("Warning: Could not create backup, proceeding anyway", file=sys.stderr)

    # Atomic write: write to temp file, then rename
    temp_file = spec_file.with_suffix('.tmp')
    try:
        with open(temp_file, 'w') as f:
            json.dump(spec_data, f, indent=2)

        # Atomic rename
        temp_file.replace(spec_file)
        return True

    except (IOError, OSError) as e:
        print(f"Error writing spec file: {e}", file=sys.stderr)
        if temp_file.exists():
            temp_file.unlink()
        return False


def backup_json_spec(spec_id: str, specs_dir: Optional[Path] = None, suffix: str = ".backup") -> Optional[Path]:
    """
    Create a backup copy of the JSON spec file in the .backups/ directory.

    Accepts both spec names and paths for maximum flexibility.

    Args:
        spec_id: Specification ID or path to spec file
        specs_dir: Path to specs directory (optional, auto-detected if not provided)
        suffix: Backup file suffix (default: .backup)

    Returns:
        Path to backup file if created, None otherwise
    """
    spec_file = resolve_spec_file(spec_id, specs_dir)

    if not spec_file:
        return None

    # Ensure .backups/ directory exists (creates directory and README if needed)
    backups_dir = ensure_backups_directory(specs_dir)

    # Create backup in .backups/ directory with spec_id as filename
    backup_file = backups_dir / f"{spec_id}{suffix}"

    try:
        shutil.copy2(spec_file, backup_file)
        return backup_file
    except (IOError, OSError) as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        return None


def _validate_spec_structure(spec_data: Dict) -> bool:
    """
    Validate basic JSON spec file structure.

    Args:
        spec_data: Spec data dictionary

    Returns:
        True if valid, False otherwise
    """
    # Check required top-level fields
    required_fields = ["spec_id", "hierarchy"]
    for field in required_fields:
        if field not in spec_data:
            print(f"Error: Missing required field '{field}' in spec data", file=sys.stderr)
            return False

    # Check hierarchy structure
    hierarchy = spec_data.get("hierarchy", {})
    if not isinstance(hierarchy, dict):
        print("Error: 'hierarchy' must be a dictionary", file=sys.stderr)
        return False

    # Validate each node in hierarchy
    for node_id, node_data in hierarchy.items():
        if not isinstance(node_data, dict):
            print(f"Error: Node '{node_id}' must be a dictionary", file=sys.stderr)
            return False

        # Check required node fields
        required_node_fields = ["type", "status"]
        for field in required_node_fields:
            if field not in node_data:
                print(f"Error: Node '{node_id}' missing required field '{field}'", file=sys.stderr)
                return False

        # Validate status value
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        if node_data["status"] not in valid_statuses:
            print(f"Error: Node '{node_id}' has invalid status '{node_data['status']}'", file=sys.stderr)
            return False

    return True


def get_node(spec_data: Dict, node_id: str) -> Optional[Dict]:
    """
    Get a specific node from the state hierarchy.

    Args:
        spec_data: JSON spec file data
        node_id: Node identifier

    Returns:
        Node data dictionary or None if not found
    """
    hierarchy = spec_data.get("hierarchy", {})
    return hierarchy.get(node_id)


def update_node(spec_data: Dict, node_id: str, updates: Dict) -> bool:
    """
    Update a node in the state hierarchy.

    Special handling for metadata: existing metadata fields are preserved
    and merged with new metadata fields, rather than being replaced entirely.

    Args:
        spec_data: JSON spec file data
        node_id: Node identifier
        updates: Dictionary of fields to update

    Returns:
        True if node exists and was updated, False otherwise
    """
    hierarchy = spec_data.get("hierarchy", {})

    if node_id not in hierarchy:
        return False

    node = hierarchy[node_id]

    # Special handling for metadata: merge instead of replace
    if "metadata" in updates:
        existing_metadata = node.get("metadata", {})
        new_metadata = updates["metadata"]

        # Create a shallow copy of updates to avoid modifying the input
        updates = updates.copy()

        # Merge existing metadata with new metadata
        updates["metadata"] = {**existing_metadata, **new_metadata}

    node.update(updates)
    return True
