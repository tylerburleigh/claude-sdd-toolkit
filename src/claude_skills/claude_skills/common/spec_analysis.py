"""
Spec file analysis and statistics.

Provides functions for analyzing spec documents, counting elements,
and extracting metadata.

Migrated from sdd-next/scripts/validation.py to eliminate duplication.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional

# Import from other sdd_common modules
from .spec import extract_frontmatter


def get_spec_statistics(spec_file: Path, json_spec_file: Optional[Path] = None) -> Dict:
    """
    Get comprehensive statistics about a spec file.

    Analyzes the spec document and extracts:
    - File size and line count
    - Task/phase/verification counts
    - Frontmatter metadata
    - JSON spec file info (if available)

    Args:
        spec_file: Path to spec markdown file
        json_spec_file: Optional path to JSON spec (auto-detected if not provided)

    Returns:
        Dictionary with spec statistics and metrics

    Example:
        >>> stats = get_spec_statistics(Path("specs/active/my-spec.md"))
        >>> print(f"Tasks: {stats['task_count']}, Phases: {stats['phase_count']}")
    """
    result = {
        "spec_file": str(spec_file.resolve()) if spec_file.exists() else str(spec_file),
        "exists": spec_file.exists(),
        "file_size": 0,
        "line_count": 0,
        "task_count": 0,
        "subtask_count": 0,
        "phase_count": 0,
        "verify_count": 0,
        "frontmatter": {},
        "json_spec_info": None
    }

    if not spec_file.exists():
        return result

    # File size
    result["file_size"] = spec_file.stat().st_size

    try:
        with open(spec_file, 'r') as f:
            lines = f.readlines()
            result["line_count"] = len(lines)
            content = ''.join(lines)

            # Count elements using the shared function
            counts = count_spec_elements(content)
            result.update(counts)

    except IOError:
        pass

    # Extract frontmatter
    result["frontmatter"] = extract_frontmatter(spec_file)

    # Load JSON spec if provided or discoverable
    if json_spec_file and json_spec_file.exists():
        try:
            with open(json_spec_file, 'r') as f:
                spec_data = json.load(f)
                result["json_spec_info"] = get_json_spec_metadata(spec_data)
        except (json.JSONDecodeError, IOError):
            pass
    elif "spec_id" in result["frontmatter"]:
        # Try to find JSON spec automatically
        spec_id = result["frontmatter"]["spec_id"]
        active_dir = spec_file.parent.parent / "active"
        auto_spec_file = active_dir / f"{spec_id}.json"

        if auto_spec_file.exists():
            try:
                with open(auto_spec_file, 'r') as f:
                    spec_data = json.load(f)
                    result["json_spec_info"] = get_json_spec_metadata(spec_data)
            except (json.JSONDecodeError, IOError):
                pass

    return result


def count_spec_elements(spec_content: str) -> Dict:
    """
    Count tasks, phases, verifications, and subtasks in spec content.

    Args:
        spec_content: Full spec markdown content as string

    Returns:
        Dictionary with counts for each element type

    Example:
        >>> with open("spec.md") as f:
        ...     content = f.read()
        >>> counts = count_spec_elements(content)
        >>> print(counts)
        {'task_count': 15, 'subtask_count': 42, 'phase_count': 3, 'verify_count': 8}
    """
    counts = {
        "task_count": 0,
        "subtask_count": 0,
        "phase_count": 0,
        "verify_count": 0
    }

    # Count task anchors (format: {#task-N-M})
    task_pattern = r'\{#task-\d+-\d+\}'
    counts["task_count"] = len(re.findall(task_pattern, spec_content))

    # Count subtask anchors (format: {#task-N-M-P})
    subtask_pattern = r'\{#task-\d+-\d+-\d+\}'
    counts["subtask_count"] = len(re.findall(subtask_pattern, spec_content))

    # Count phase anchors (format: {#phase-N})
    phase_pattern = r'\{#phase-\d+\}'
    counts["phase_count"] = len(re.findall(phase_pattern, spec_content))

    # Count verification anchors (format: {#verify-N-M})
    verify_pattern = r'\{#verify-\d+-\d+\}'
    counts["verify_count"] = len(re.findall(verify_pattern, spec_content))

    return counts


def get_json_spec_metadata(spec_data: Dict) -> Dict:
    """
    Extract metadata from JSON spec.

    Args:
        spec_data: JSON spec file data dictionary

    Returns:
        Dictionary with JSON spec metadata

    Example:
        >>> with open("specs/active/my-spec.json") as f:
        ...     spec_data = json.load(f)
        >>> metadata = get_json_spec_metadata(spec_data)
        >>> print(f"Last updated: {metadata['last_updated']}")
    """
    metadata = {
        "spec_id": spec_data.get("spec_id", ""),
        "generated": spec_data.get("generated", ""),
        "last_updated": spec_data.get("last_updated", "")
    }

    # Add hierarchy statistics if available
    hierarchy = spec_data.get("hierarchy", {})
    if hierarchy:
        total_nodes = len(hierarchy)
        total_tasks = sum(
            1 for node in hierarchy.values()
            if node.get("type") in ["task", "subtask"]
        )
        completed_tasks = sum(
            1 for node in hierarchy.values()
            if node.get("type") in ["task", "subtask"] and node.get("status") == "completed"
        )

        metadata.update({
            "total_nodes": total_nodes,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        })

    return metadata


def analyze_spec_complexity(spec_file: Path) -> Dict:
    """
    Analyze spec complexity metrics.

    Provides insights into spec complexity including:
    - Average tasks per phase
    - Average subtasks per task
    - Depth of task hierarchy
    - Verification coverage ratio

    Args:
        spec_file: Path to spec markdown file

    Returns:
        Dictionary with complexity metrics

    Example:
        >>> complexity = analyze_spec_complexity(Path("specs/active/my-spec.md"))
        >>> print(f"Average tasks per phase: {complexity['avg_tasks_per_phase']}")
    """
    if not spec_file.exists():
        return {"error": "Spec file not found"}

    try:
        with open(spec_file, 'r') as f:
            content = f.read()

        counts = count_spec_elements(content)

        # Calculate metrics
        task_count = counts["task_count"]
        subtask_count = counts["subtask_count"]
        phase_count = counts["phase_count"]
        verify_count = counts["verify_count"]

        metrics = {
            "task_count": task_count,
            "subtask_count": subtask_count,
            "phase_count": phase_count,
            "verify_count": verify_count,
            "avg_tasks_per_phase": round(task_count / phase_count, 1) if phase_count > 0 else 0,
            "avg_subtasks_per_task": round(subtask_count / task_count, 1) if task_count > 0 else 0,
            "has_subtasks": subtask_count > 0,
            "verification_coverage": round(verify_count / (task_count + phase_count) * 100, 1) if (task_count + phase_count) > 0 else 0,
            "estimated_hours": None  # Can be populated from frontmatter if available
        }

        # Try to get estimated hours from frontmatter
        frontmatter = extract_frontmatter(spec_file)
        if "estimated_hours" in frontmatter:
            metrics["estimated_hours"] = frontmatter["estimated_hours"]

        return metrics

    except IOError:
        return {"error": "Could not read spec file"}


def compare_spec_files(md_spec_file: Path, json_spec_file: Path) -> Dict:
    """
    Compare markdown spec counts to JSON spec counts.

    Identifies mismatches between the markdown spec document and JSON spec,
    which may indicate synchronization issues.

    Args:
        md_spec_file: Path to spec markdown file
        json_spec_file: Path to JSON spec file

    Returns:
        Dictionary with comparison results and any discrepancies

    Example:
        >>> comparison = compare_spec_files(md_path, json_path)
        >>> if comparison['has_mismatches']:
        ...     print("Warning: Markdown and JSON specs are out of sync")
    """
    result = {
        "has_mismatches": False,
        "mismatches": [],
        "md_spec_counts": {},
        "json_spec_counts": {}
    }

    # Get markdown spec counts
    if md_spec_file.exists():
        with open(md_spec_file, 'r') as f:
            content = f.read()
        result["md_spec_counts"] = count_spec_elements(content)
    else:
        result["mismatches"].append("Markdown spec file not found")
        result["has_mismatches"] = True
        return result

    # Get JSON spec counts
    if json_spec_file.exists():
        try:
            with open(json_spec_file, 'r') as f:
                spec_data = json.load(f)

            hierarchy = spec_data.get("hierarchy", {})
            json_task_count = sum(
                1 for node in hierarchy.values()
                if node.get("type") == "task"
            )
            json_subtask_count = sum(
                1 for node in hierarchy.values()
                if node.get("type") == "subtask"
            )
            json_phase_count = sum(
                1 for node in hierarchy.values()
                if node.get("type") == "phase"
            )
            json_verify_count = sum(
                1 for node in hierarchy.values()
                if node.get("type") == "verify"
            )

            result["json_spec_counts"] = {
                "task_count": json_task_count,
                "subtask_count": json_subtask_count,
                "phase_count": json_phase_count,
                "verify_count": json_verify_count
            }

        except (json.JSONDecodeError, IOError):
            result["mismatches"].append("Invalid or unreadable JSON spec")
            result["has_mismatches"] = True
            return result
    else:
        result["mismatches"].append("JSON spec file not found")
        result["has_mismatches"] = True
        return result

    # Compare counts
    for key in ["task_count", "phase_count", "verify_count"]:
        md_value = result["md_spec_counts"].get(key, 0)
        json_value = result["json_spec_counts"].get(key, 0)

        if md_value != json_value:
            result["mismatches"].append({
                "element": key.replace("_count", ""),
                "markdown": md_value,
                "json": json_value,
                "difference": md_value - json_value
            })
            result["has_mismatches"] = True

    return result
