#!/usr/bin/env python3
"""
Spec template management for sdd-plan.

Provides predefined templates for different types of specifications.
"""

from typing import Dict, Any
from datetime import datetime


TEMPLATES = {
    "simple": {
        "name": "Simple Feature",
        "description": "Basic feature with 1-2 phases, < 5 files",
        "recommended_for": "Small features, bug fixes, simple refactoring",
        "phases": 2,
        "estimated_hours": 8,
        "complexity": "low",
        "risk_level": "low",
    },
    "medium": {
        "name": "Medium Feature",
        "description": "Standard feature with 2-4 phases, 5-15 files",
        "recommended_for": "New features, moderate refactoring, API changes",
        "phases": 3,
        "estimated_hours": 24,
        "complexity": "medium",
        "risk_level": "medium",
    },
    "complex": {
        "name": "Complex Feature",
        "description": "Large feature with 4-6 phases, > 15 files",
        "recommended_for": "Major features, architecture changes, system redesigns",
        "phases": 5,
        "estimated_hours": 60,
        "complexity": "high",
        "risk_level": "high",
    },
    "security": {
        "name": "Security Feature",
        "description": "Security-focused feature with emphasis on validation and testing",
        "recommended_for": "Auth/authz, data validation, encryption, secrets management",
        "phases": 4,
        "estimated_hours": 40,
        "complexity": "high",
        "risk_level": "critical",
        "security_sensitive": True,
    },
}


def list_templates() -> Dict[str, Dict[str, Any]]:
    """
    Get all available templates.

    Returns:
        Dictionary of template_id -> template_info
    """
    return TEMPLATES


def get_template(template_id: str) -> Dict[str, Any]:
    """
    Get a specific template by ID.

    Args:
        template_id: Template identifier (simple, medium, complex, security)

    Returns:
        Template dictionary or None if not found
    """
    return TEMPLATES.get(template_id)


def generate_spec_from_template(
    template_id: str,
    title: str,
    spec_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate a spec structure from a template.

    Args:
        template_id: Template to use
        title: Specification title
        spec_id: Optional spec ID (auto-generated if not provided)
        **kwargs: Additional metadata to override template defaults

    Returns:
        Spec dictionary ready to be serialized to JSON
    """
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template '{template_id}' not found")

    # Generate spec_id if not provided
    if not spec_id:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        safe_title = title.lower().replace(" ", "-")[:30]
        spec_id = f"{safe_title}-{timestamp}"

    now = datetime.now().isoformat() + "Z"

    # Build base spec structure
    spec = {
        "spec_id": spec_id,
        "title": title,
        "generated": now,
        "last_updated": now,
        "metadata": {
            "template": template_id,
            "complexity": template.get("complexity", "medium"),
            "risk_level": template.get("risk_level", "medium"),
            "estimated_hours": template.get("estimated_hours", 24),
            "security_sensitive": template.get("security_sensitive", False),
        },
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": title,
                "status": "pending",
                "parent": None,
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {}
            }
        }
    }

    # Override with any provided kwargs
    spec["metadata"].update(kwargs)

    # Generate placeholder phases based on template
    num_phases = template.get("phases", 2)
    phase_ids = []

    for i in range(1, num_phases + 1):
        phase_id = f"phase-{i}"
        phase_ids.append(phase_id)

        spec["hierarchy"][phase_id] = {
            "type": "phase",
            "title": f"Phase {i}: [To Be Defined]",
            "status": "pending",
            "parent": "spec-root",
            "children": [],
            "total_tasks": 0,
            "completed_tasks": 0,
            "metadata": {}
        }

    # Update root children
    spec["hierarchy"]["spec-root"]["children"] = phase_ids

    return spec


def get_template_description(template_id: str) -> str:
    """
    Get a human-readable description of a template.

    Args:
        template_id: Template identifier

    Returns:
        Formatted description string
    """
    template = get_template(template_id)
    if not template:
        return f"Template '{template_id}' not found"

    lines = [
        f"Template: {template['name']}",
        f"Description: {template['description']}",
        f"Recommended for: {template['recommended_for']}",
        f"Phases: {template['phases']}",
        f"Estimated hours: {template['estimated_hours']}",
        f"Complexity: {template['complexity']}",
        f"Risk level: {template['risk_level']}",
    ]

    if template.get("security_sensitive"):
        lines.append("Security sensitive: Yes")

    return "\n".join(lines)
