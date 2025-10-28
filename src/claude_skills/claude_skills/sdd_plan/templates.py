#!/usr/bin/env python3
"""
Spec template management for sdd-plan.

Provides predefined templates for different types of specifications.
"""

from typing import Dict, Any
from datetime import datetime, timezone


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
    default_category: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate a spec structure from a template.

    Args:
        template_id: Template to use
        title: Specification title
        spec_id: Optional spec ID (auto-generated if not provided)
        default_category: Optional default task category (overrides automatic inference)
                         One of: investigation, implementation, refactoring, decision, research
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

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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

    # Add default_category to metadata if provided
    if default_category:
        spec["metadata"]["default_category"] = default_category

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


def infer_task_category(task_title: str, task_type: str = "task") -> str:
    """
    Infer task_category based on keywords in the task title.

    Analyzes the task title for category-specific keywords and returns
    the most likely task category. Defaults to 'implementation' when
    keywords are ambiguous or absent.

    The function checks keywords in priority order:
    1. investigation - exploring/analyzing existing code
    2. refactoring - improving code structure
    3. decision - architectural/design choices
    4. research - gathering external information
    5. implementation - creating new functionality (default)

    Args:
        task_title: The task title to analyze
        task_type: Type of node (task, subtask, verify, etc.) - currently unused
                   but reserved for future enhancements

    Returns:
        One of: 'investigation', 'implementation', 'refactoring', 'decision', 'research'

    Examples:
        >>> infer_task_category("Analyze current authentication flow")
        'investigation'

        >>> infer_task_category("Create user service")
        'implementation'

        >>> infer_task_category("Extract validation to utility")
        'refactoring'

        >>> infer_task_category("Choose between JWT vs sessions")
        'decision'

        >>> infer_task_category("Research OAuth 2.0 best practices")
        'research'

        >>> infer_task_category("")
        'implementation'
    """
    if not task_title:
        return "implementation"

    title_lower = task_title.lower()

    # Investigation keywords (exploring existing code)
    # Priority: Check first as understanding should precede implementation
    investigation_keywords = [
        "analyze", "understand", "trace", "map",
        "investigate", "review existing", "examine", "inspect",
        "study existing", "audit", "assess current", "explore existing"
    ]
    if any(keyword in title_lower for keyword in investigation_keywords):
        return "investigation"

    # Refactoring keywords (improving code structure)
    # Priority: Second as these are modifications, not new features
    refactoring_keywords = [
        "refactor", "reorganize", "extract", "improve code",
        "restructure", "simplify", "split", "combine",
        "consolidate", "clean up", "optimize structure"
    ]
    if any(keyword in title_lower for keyword in refactoring_keywords):
        return "refactoring"

    # Decision keywords (architectural choices)
    # Priority: Third as decisions often inform implementation
    decision_keywords = [
        "choose", "decide", "select", "compare", "evaluate",
        "architectural", "design choice", "between", "vs",
        "determine approach", "pick"
    ]
    if any(keyword in title_lower for keyword in decision_keywords):
        return "decision"

    # Research keywords (external learning)
    # Priority: Fourth as research informs decisions and implementation
    # Use specific phrases to avoid false positives
    research_keywords = [
        "research", "learn about", "gather information",
        "best practices", "review oauth", "investigate external",
        "read documentation", "review docs", "explore external", "study external"
    ]
    if any(keyword in title_lower for keyword in research_keywords):
        return "research"

    # Implementation keywords (creating new code)
    # Priority: Checked last as it's the most common and serves as default
    implementation_keywords = [
        "create", "add", "implement", "build", "write",
        "develop", "generate", "new", "setup", "configure",
        "integrate", "construct", "update"
    ]
    if any(keyword in title_lower for keyword in implementation_keywords):
        return "implementation"

    # Safe default for ambiguous or unmatched titles
    return "implementation"
