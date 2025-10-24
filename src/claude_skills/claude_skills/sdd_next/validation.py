"""JSON-aware validation helpers for sdd-next."""

import json
from pathlib import Path
from typing import Dict, Optional

from claude_skills.common import (
    load_json_spec,
    find_circular_dependencies,
    validate_and_normalize_paths,
    validate_spec_hierarchy
)
from claude_skills.common.spec_analysis import get_json_spec_metadata


def validate_spec(spec_file: Path, specs_dir: Optional[Path] = None) -> Dict:
    """Validate a JSON spec file using the shared hierarchy validator."""
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "spec_file": str(spec_file.resolve()),
        "spec_id": None,
        "json_spec_file": None
    }

    if not spec_file.exists():
        result["errors"].append(f"Spec file not found: {spec_file}")
        return result

    try:
        spec_data = load_json_spec(spec_file.stem, specs_dir or spec_file.parent.parent)
    except Exception:  # pragma: no cover - load_json_spec already reports the error
        spec_data = None

    if not spec_data:
        result["errors"].append("Unable to load JSON spec data")
        return result

    validation = validate_spec_hierarchy(spec_data)
    result["spec_id"] = validation.spec_id
    result["errors"] = validation.structure_errors + validation.hierarchy_errors + validation.node_errors
    result["warnings"] = validation.structure_warnings + validation.hierarchy_warnings + validation.node_warnings
    result["valid"] = validation.is_valid()
    return result


def find_circular_deps(spec_data: Dict) -> Dict:
    """Detected circular dependencies wrapper (backwards compatible)."""
    return find_circular_dependencies(spec_data)


def validate_paths(paths: list, base_directory: Optional[Path] = None) -> Dict:
    """Validate and normalize filesystem paths."""
    return validate_and_normalize_paths(paths, base_directory)


def spec_stats(spec_file: Path, json_spec_file: Optional[Path] = None) -> Dict:
    """Return statistics and metadata about a JSON spec file."""
    spec_file = Path(spec_file)
    json_spec_file = Path(json_spec_file) if json_spec_file else None

    exists = spec_file.exists()
    result: Dict = {
        "spec_file": str(spec_file.resolve() if exists else spec_file),
        "exists": exists,
        "file_size": 0,
        "line_count": 0,
        "phase_count": 0,
        "task_count": 0,
        "verify_count": 0,
        "hierarchy_summary": {},
        "frontmatter": {},
        "state_info": None
    }

    if not exists:
        return result

    try:
        file_text = spec_file.read_text()
        result["line_count"] = len(file_text.splitlines())
        result["file_size"] = spec_file.stat().st_size
    except (OSError, IOError) as exc:
        result["error"] = f"Unable to read spec file: {exc}"
        return result

    try:
        spec_data = json.loads(file_text)
    except json.JSONDecodeError as exc:
        result["error"] = f"Invalid spec JSON: {exc}"
        return result

    hierarchy = spec_data.get("hierarchy", {}) if isinstance(spec_data, dict) else {}
    if isinstance(hierarchy, dict):
        phase_count = sum(1 for node in hierarchy.values() if node.get("type") == "phase")
        task_count = sum(1 for node in hierarchy.values() if node.get("type") == "task")
        verify_count = sum(1 for node in hierarchy.values() if node.get("type") == "verify")
        subtask_count = sum(1 for node in hierarchy.values() if node.get("type") == "subtask")
        total_nodes = len(hierarchy)

        result.update({
            "phase_count": phase_count,
            "task_count": task_count,
            "verify_count": verify_count,
            "hierarchy_summary": {
                "total_nodes": total_nodes,
                "phase_count": phase_count,
                "task_count": task_count,
                "verify_count": verify_count,
                "subtask_count": subtask_count
            }
        })

    spec_id = spec_data.get("spec_id") if isinstance(spec_data, dict) else None
    result["frontmatter"] = {
        key: value
        for key, value in (
            ("spec_id", spec_id or spec_file.stem),
            ("title", spec_data.get("title") if isinstance(spec_data, dict) else None),
            ("generated", spec_data.get("generated") if isinstance(spec_data, dict) else None),
            ("last_updated", spec_data.get("last_updated") if isinstance(spec_data, dict) else None),
            ("metadata", spec_data.get("metadata") if isinstance(spec_data, dict) else None)
        )
        if value is not None
    }

    spec_data = None
    spec_error: Optional[str] = None

    if json_spec_file:
        if json_spec_file.exists():
            try:
                with json_spec_file.open("r") as fh:
                    spec_data = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                spec_error = f"Unable to load JSON spec: {exc}"
        else:
            spec_error = f"JSON spec file not found: {json_spec_file}"
    else:
        specs_dir = spec_file.parent.parent
        lookup_spec_id = spec_id or spec_file.stem
        try:
            spec_data = load_json_spec(lookup_spec_id, specs_dir)
        except Exception:
            spec_data = None
        if spec_data is None and spec_id is None:
            spec_error = "Spec identifier not available; skipping state lookup"

    if spec_data:
        result["state_info"] = get_json_spec_metadata(spec_data)
    else:
        result["state_info"] = None
        if spec_error:
            result["spec_error"] = spec_error

    return result
