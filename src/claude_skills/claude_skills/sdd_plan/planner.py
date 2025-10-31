#!/usr/bin/env python3
"""
Core planning logic for sdd-plan.

Provides spec creation, codebase analysis, and planning workflows.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


def analyze_codebase(directory: Path) -> Dict[str, Any]:
    """
    Analyze codebase using doc-query if available.

    Args:
        directory: Directory to analyze

    Returns:
        Analysis results dictionary
    """
    analysis = {
        "success": False,
        "has_documentation": False,
        "stats": {},
        "error": None
    }

    # Check if doc-query is available
    try:
        result = subprocess.run(
            ["doc-query", "stats"],
            cwd=str(directory),
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            analysis["success"] = True
            analysis["has_documentation"] = True
            analysis["stats"] = parse_doc_query_stats(result.stdout)
        else:
            analysis["error"] = "doc-query failed or no documentation found"

    except FileNotFoundError:
        analysis["error"] = "doc-query not installed"
    except subprocess.TimeoutExpired:
        analysis["error"] = "doc-query timed out"
    except Exception as e:
        analysis["error"] = f"Unexpected error: {str(e)}"

    return analysis


def parse_doc_query_stats(output: str) -> Dict[str, Any]:
    """
    Parse doc-query stats output.

    Args:
        output: stdout from doc-query stats

    Returns:
        Parsed statistics dictionary
    """
    stats = {}
    for line in output.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            # Try to convert to number
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            stats[key] = value

    return stats


def create_spec_interactive(
    title: Optional[str] = None,
    template: str = "medium",
    specs_dir: Path = None,
    default_category: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Create a new spec interactively.

    Args:
        title: Optional spec title (will prompt if not provided)
        template: Template to use (simple, medium, complex, security)
        specs_dir: Directory to save spec (defaults to specs/active)
        default_category: Optional default task category (overrides automatic inference)
                         One of: investigation, implementation, refactoring, decision, research

    Returns:
        Tuple of (success, message, spec_dict)
    """
    from claude_skills.sdd_plan.templates import (
        generate_spec_from_template,
        get_template,
    )

    # Validate template
    if not get_template(template):
        return False, f"Invalid template: {template}", None

    # Prompt for title if not provided
    if not title:
        return False, "Title is required", None

    # Generate spec from template
    try:
        spec = generate_spec_from_template(template, title, default_category=default_category)
    except Exception as e:
        return False, f"Failed to generate spec: {str(e)}", None

    # Determine output path
    if not specs_dir:
        specs_dir = Path("specs/pending")

    specs_dir.mkdir(parents=True, exist_ok=True)
    spec_path = specs_dir / f"{spec['spec_id']}.json"

    # Save spec
    try:
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2)
    except Exception as e:
        return False, f"Failed to save spec: {str(e)}", None

    return True, f"Spec created: {spec_path}", spec


def find_specs_directory() -> Optional[Path]:
    """
    Find the specs directory in the project.

    Returns:
        Path to specs directory or None if not found
    """
    current = Path.cwd()

    # Check current directory and parents
    for path in [current] + list(current.parents):
        specs_dir = path / "specs"
        if specs_dir.exists() and specs_dir.is_dir():
            return specs_dir

    return None


def suggest_documentation_generation(directory: Path) -> str:
    """
    Suggest generating documentation if not available.

    Args:
        directory: Project directory

    Returns:
        Suggestion message
    """
    return (
        "No codebase documentation found. Consider generating it for faster analysis:\n"
        "\n"
        "  codebase-documentation generate\n"
        "\n"
        "This will enable:\n"
        "  - 10x faster codebase analysis\n"
        "  - Better quality specs with comprehensive pattern understanding\n"
        "  - Consistent adherence to existing patterns\n"
    )


def get_project_context(directory: Path) -> Dict[str, Any]:
    """
    Get context about the project for planning.

    Args:
        directory: Project directory

    Returns:
        Context dictionary with project info
    """
    context = {
        "directory": str(directory),
        "has_specs": False,
        "specs_directory": None,
        "codebase_analysis": None,
    }

    # Check for specs directory
    specs_dir = find_specs_directory()
    if specs_dir:
        context["has_specs"] = True
        context["specs_directory"] = str(specs_dir)

    # Try to analyze codebase
    analysis = analyze_codebase(directory)
    context["codebase_analysis"] = analysis

    return context
