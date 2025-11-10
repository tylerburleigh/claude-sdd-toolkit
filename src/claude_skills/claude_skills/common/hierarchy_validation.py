"""
Hierarchy validation operations for sdd-plan.
Validates the hierarchy structure within JSON spec files for compliance with sdd-plan requirements.
"""

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional, Set

# Add parent directories to path for imports

from claude_skills.common import (
    EnhancedError,
    JsonSpecValidationResult,
    validate_status,
    validate_node_type,
    validate_spec_id_format,
    validate_iso8601_date,
    normalize_message_text,
    load_json_schema,
)


_LOCATION_PATTERNS = (
    re.compile(r"(?:Node|node|Task node|Phase node|Verify node) ['\"]([^'\"]+)['\"]"),
    re.compile(r"node ['\"]([^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"task ['\"]([^'\"]+)['\"]", re.IGNORECASE),
)

_SPEC_SCHEMA_FILENAME = "sdd-spec-schema.json"


def _extract_location(message: str) -> Optional[str]:
    """Attempt to extract a node identifier from a validation message."""

    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(message or "")
        if match:
            return match.group(1)
    return None


def _determine_severity(message: str, severity_hint: str) -> str:
    lowered = (message or "").lower()
    if "critical" in lowered:
        return "critical"
    if "warning" in lowered and severity_hint == "error":
        return "warning"
    if "info" in lowered and severity_hint == "warning":
        return "info"
    return severity_hint


def _is_auto_fixable(category: str, normalized_message: str) -> bool:
    text = normalized_message.lower()

    if category == "counts":
        return "total_tasks" in text or "completed_tasks" in text
    if category == "metadata":
        return (
            "metadata" in text
            or "file_path" in text
            or "verification" in text
            or "task_category" in text
        )
    if category == "hierarchy":
        return ("parent/child mismatch" in text or
                "orphaned node" in text or
                "not reachable from spec-root" in text)
    if category == "structure":
        return "iso" in text or "date" in text
    if category == "node":
        return (("status" in text and ("invalid" in text or "should" in text)) or
                "missing required field" in text or
                "empty title" in text or
                "invalid type" in text or
                "should have total_tasks=1" in text)
    if category == "dependency":
        return ("bidirectional dependency inconsistency" in text or
                "dependencies must be a dictionary" in text)
    return False


def _suggest_fix(category: str, normalized_message: str) -> Optional[str]:
    text = normalized_message.lower()

    if category == "counts":
        return "Recalculate total/completed task rollups for parent nodes."
    if category == "metadata":
        if "file_path" in text:
            return "Add metadata.file_path or provide a default placeholder."
        if "task_category" in text:
            if "invalid" in text:
                return "Fix task_category to one of: investigation, implementation, refactoring, decision, research."
            else:
                return "Add metadata.task_category (choose: investigation for exploring, implementation for new code, refactoring for improving code, decision for design choices, research for gathering info)."
        if "metadata" in text:
            return "Add metadata object with required defaults."
        if "verification" in text:
            return "Populate verification metadata (type, command, expected)."
    if category == "hierarchy":
        if "parent/child mismatch" in text:
            return "Align parent references with children list to resolve mismatch."
        if "orphaned node" in text or "not reachable from spec-root" in text:
            return "Attach orphaned nodes to spec-root or remove them."
    if category == "structure" and ("iso" in text or "date" in text):
        return "Normalize generated/last_updated timestamps to ISO 8601."
    if category == "node":
        if "status" in text:
            return "Normalize status to pending/in_progress/completed/blocked."
        if "missing required field" in text:
            return "Add missing required fields with sensible defaults."
        if "empty title" in text:
            return "Generate title from node ID."
        if "invalid type" in text:
            return "Normalize node type to valid value."
        if "should have total_tasks=1" in text:
            return "Set leaf node total_tasks to 1."
    if category == "dependency":
        if "bidirectional dependency inconsistency" in text:
            return "Synchronize bidirectional dependency relationships."
        if "dependencies must be a dictionary" in text:
            return "Create dependencies dict with blocks/blocked_by/depends arrays."
    return None


def _build_enhanced_errors(
    messages: Iterable[str],
    *,
    severity_hint: str,
    category: str,
) -> List[EnhancedError]:
    enhanced: List[EnhancedError] = []
    for raw in messages or []:
        normalized = normalize_message_text(raw)
        if not normalized:
            continue
        location = _extract_location(raw)
        severity = _determine_severity(raw, severity_hint)
        auto_fixable = _is_auto_fixable(category, normalized)
        suggested_fix = _suggest_fix(category, normalized) if auto_fixable else None

        enhanced.append(
            EnhancedError(
                message=normalized,
                severity=severity,
                category=category,
                location=location,
                suggested_fix=suggested_fix,
                auto_fixable=auto_fixable,
            )
        )

    return enhanced


def _validate_against_schema(spec_data: Dict) -> Tuple[List[str], List[str], Optional[str]]:
    """
    Run JSON Schema validation against the canonical SDD spec schema.

    Returns:
        Tuple of (schema_errors, schema_warnings, schema_source).
    """

    schema, source, load_error = load_json_schema(_SPEC_SCHEMA_FILENAME)
    if schema is None:
        message = load_error or "Schema validation skipped: schema not found."
        return [], [message], source

    try:
        import jsonschema  # type: ignore  # pylint: disable=import-error
    except ImportError:
        warning = (
            "Schema validation skipped: install the 'jsonschema' package "
            "or use optional dependency group 'validation' to enable Draft 7 validation."
        )
        return [], [warning], source

    validator = jsonschema.Draft7Validator(schema)
    validation_errors = sorted(validator.iter_errors(spec_data), key=lambda err: list(err.path))

    schema_errors: List[str] = []
    schema_warnings: List[str] = []
    for error in validation_errors:
        pointer = "/".join(str(part) for part in error.path) or "<root>"
        message = f"Schema violation at '{pointer}': {error.message}"

        # Backward compatibility: legacy specs omit metadata.id on hierarchy nodes.
        # Treat the Draft 7 'id' requirement as a warning so old specs remain valid.
        if (
            pointer.startswith("hierarchy/")
            and error.validator == "required"
            and isinstance(getattr(error, "message", ""), str)
            and "'id' is a required property" in error.message
        ):
            schema_warnings.append(message.replace("Schema violation", "Schema caution"))
            continue

        schema_errors.append(message)

    return schema_errors, schema_warnings, source


def validate_structure(spec_data: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate top-level JSON structure and required fields.

    Args:
        spec_data: JSON spec file data dictionary

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    # Required top-level fields
    required_fields = ['spec_id', 'generated', 'last_updated', 'hierarchy']
    for field in required_fields:
        if field not in spec_data:
            errors.append(f"❌ CRITICAL: Missing required field '{field}' in spec file")

    # Validate spec_id type and format
    if 'spec_id' in spec_data:
        spec_id = spec_data['spec_id']
        if not isinstance(spec_id, str):
            errors.append(f"❌ ERROR: 'spec_id' must be a string, got {type(spec_id).__name__}")
        elif not validate_spec_id_format(spec_id):
            warnings.append(
                f"⚠️  WARNING: spec_id '{spec_id}' doesn't follow recommended format: " +
                "{{feature}}-{{YYYY-MM-DD}}-{{nnn}}"
            )

    # Validate title type if present
    if 'title' in spec_data:
        title = spec_data['title']
        if not isinstance(title, str):
            errors.append(f"❌ ERROR: 'title' must be a string, got {type(title).__name__}")

    # Validate date formats
    date_fields = ['generated', 'last_updated']
    for field in date_fields:
        if field in spec_data and spec_data[field]:
            if not isinstance(spec_data[field], str):
                errors.append(f"❌ ERROR: '{field}' must be a string, got {type(spec_data[field]).__name__}")
            elif not validate_iso8601_date(spec_data[field]):
                warnings.append(
                    f"⚠️  WARNING: '{field}' should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"
                )

    # Check that hierarchy exists and is a dict
    if 'hierarchy' in spec_data:
        if not isinstance(spec_data['hierarchy'], dict):
            errors.append("❌ CRITICAL: 'hierarchy' field must be a dictionary/object")
        elif len(spec_data['hierarchy']) == 0:
            errors.append("❌ CRITICAL: 'hierarchy' is empty")

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_hierarchy(hierarchy: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate hierarchy integrity: parent/child references, no orphans, no cycles.

    Args:
        hierarchy: Hierarchy dictionary from JSON spec file

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    # Check spec-root exists
    if 'spec-root' not in hierarchy:
        errors.append("❌ CRITICAL: Missing 'spec-root' node in hierarchy")
        return (False, errors, warnings)

    root = hierarchy['spec-root']
    if root.get('parent') is not None:
        errors.append("❌ CRITICAL: 'spec-root' must have parent: null")

    # Validate all parent references
    for node_id, node in hierarchy.items():
        parent_id = node.get('parent')

        if node_id != 'spec-root' and parent_id is None:
            errors.append(f"❌ ERROR: Node '{node_id}' has null parent (only spec-root should)")

        if parent_id and parent_id not in hierarchy:
            errors.append(f"❌ CRITICAL: Node '{node_id}' references non-existent parent '{parent_id}'")

    # Validate all child references
    for node_id, node in hierarchy.items():
        children = node.get('children', [])

        if not isinstance(children, list):
            errors.append(f"❌ ERROR: Node '{node_id}' children field must be a list")
            continue

        for child_id in children:
            if child_id not in hierarchy:
                errors.append(f"❌ CRITICAL: Node '{node_id}' references non-existent child '{child_id}'")
            else:
                # Check bidirectional relationship
                child_node = hierarchy[child_id]
                if child_node.get('parent') != node_id:
                    errors.append(
                        f"❌ ERROR: Parent/child mismatch: '{node_id}' lists '{child_id}' as child, " +
                        f"but '{child_id}' has parent='{child_node.get('parent')}'"
                    )

    # Check for orphaned nodes (nodes not reachable from spec-root)
    reachable = set()

    def traverse(node_id):
        if node_id in reachable:
            return
        reachable.add(node_id)
        node = hierarchy.get(node_id, {})
        for child_id in node.get('children', []):
            if child_id in hierarchy:
                traverse(child_id)

    traverse('spec-root')

    orphaned = set(hierarchy.keys()) - reachable
    if orphaned:
        orphan_list = ", ".join(sorted(orphaned))
        errors.append(
            f"❌ ERROR: Found {len(orphaned)} orphaned node(s) not reachable from spec-root: {orphan_list}"
        )

    # Check for cycles (simple DFS cycle detection)
    visited = set()
    rec_stack = set()

    def has_cycle(node_id):
        visited.add(node_id)
        rec_stack.add(node_id)

        node = hierarchy.get(node_id, {})
        for child_id in node.get('children', []):
            if child_id not in visited:
                if has_cycle(child_id):
                    return True
            elif child_id in rec_stack:
                return True

        rec_stack.remove(node_id)
        return False

    if has_cycle('spec-root'):
        errors.append("❌ CRITICAL: Cycle detected in hierarchy tree")

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_nodes(hierarchy: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate node structure and required fields for each node.

    Args:
        hierarchy: Hierarchy dictionary from JSON spec file

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    required_fields = ['type', 'title', 'status', 'parent', 'children', 'total_tasks', 'completed_tasks', 'metadata']

    for node_id, node in hierarchy.items():
        # Check required fields
        for field in required_fields:
            if field not in node:
                errors.append(f"❌ ERROR: Node '{node_id}' missing required field '{field}'")

        # Validate type
        node_type = node.get('type')
        if node_type and not validate_node_type(node_type):
            errors.append(
                f"❌ ERROR: Node '{node_id}' has invalid type '{node_type}'"
            )

        # Validate status
        status = node.get('status')
        if status and not validate_status(status):
            errors.append(
                f"❌ ERROR: Node '{node_id}' has invalid status '{status}'"
            )

        # Check title is not empty
        title = node.get('title')
        if title is not None and not str(title).strip():
            warnings.append(f"⚠️  WARNING: Node '{node_id}' has empty title")

        # Validate dependencies structure if present
        if 'dependencies' in node:
            deps = node['dependencies']
            if not isinstance(deps, dict):
                errors.append(f"❌ ERROR: Node '{node_id}' dependencies must be a dictionary")
            else:
                for dep_key in ['blocks', 'blocked_by', 'depends']:
                    if dep_key in deps and not isinstance(deps[dep_key], list):
                        errors.append(f"❌ ERROR: Node '{node_id}' dependencies.{dep_key} must be a list")

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_task_counts(hierarchy: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate task count accuracy and propagation up the hierarchy.

    Args:
        hierarchy: Hierarchy dictionary from JSON spec file

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    for node_id, node in hierarchy.items():
        total_tasks = node.get('total_tasks', 0)
        completed_tasks = node.get('completed_tasks', 0)
        children = node.get('children', [])

        # Completed can't exceed total
        if completed_tasks > total_tasks:
            errors.append(
                f"❌ ERROR: Node '{node_id}' has completed_tasks ({completed_tasks}) > " +
                f"total_tasks ({total_tasks})"
            )

        # If node has children, verify counts match sum of children
        if children:
            child_total = 0
            child_completed = 0

            # Check that all children exist
            for child_id in children:
                if child_id not in hierarchy:
                    errors.append(
                        f"❌ ERROR: Node '{node_id}' lists non-existent child '{child_id}'"
                    )

            for child_id in children:
                if child_id in hierarchy:
                    child_node = hierarchy[child_id]
                    child_total += child_node.get('total_tasks', 0)
                    child_completed += child_node.get('completed_tasks', 0)

            if total_tasks != child_total:
                errors.append(
                    f"❌ ERROR: Node '{node_id}' total_tasks ({total_tasks}) doesn't match " +
                    f"sum of children ({child_total})"
                )

            if completed_tasks != child_completed:
                errors.append(
                    f"❌ ERROR: Node '{node_id}' completed_tasks ({completed_tasks}) doesn't match " +
                    f"sum of children ({child_completed})"
                )
        else:
            # Leaf nodes should have total_tasks = 1 (or 0 for groups)
            node_type = node.get('type')
            if node_type in ['task', 'subtask', 'verify']:
                if total_tasks != 1:
                    warnings.append(
                        f"⚠️  WARNING: Leaf node '{node_id}' (type={node_type}) should have " +
                        f"total_tasks=1, has {total_tasks}"
                    )

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_dependencies(hierarchy: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate dependency graph: references exist, no circular dependencies.

    Args:
        hierarchy: Hierarchy dictionary from JSON spec file

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    for node_id, node in hierarchy.items():
        if 'dependencies' not in node:
            continue

        deps = node['dependencies']

        # Check all dependency references exist
        for dep_type in ['blocks', 'blocked_by', 'depends']:
            if dep_type not in deps:
                continue

            for dep_id in deps[dep_type]:
                if dep_id not in hierarchy:
                    errors.append(
                        f"❌ ERROR: Node '{node_id}' {dep_type} references non-existent node '{dep_id}'"
                    )

    # Check for circular dependencies in 'blocked_by' relationships
    def has_blocking_cycle(node_id, visited=None, rec_stack=None):
        if visited is None:
            visited = set()
        if rec_stack is None:
            rec_stack = set()

        visited.add(node_id)
        rec_stack.add(node_id)

        node = hierarchy.get(node_id, {})
        deps = node.get('dependencies', {})

        # Handle malformed dependencies (should be dict, not list)
        if not isinstance(deps, dict):
            deps = {}

        for blocked_id in deps.get('blocked_by', []):
            if blocked_id not in hierarchy:
                continue

            if blocked_id not in visited:
                if has_blocking_cycle(blocked_id, visited, rec_stack):
                    return True
            elif blocked_id in rec_stack:
                return True

        rec_stack.remove(node_id)
        return False

    checked = set()
    for node_id in hierarchy:
        if node_id not in checked:
            if has_blocking_cycle(node_id):
                errors.append(f"❌ ERROR: Circular dependency detected involving node '{node_id}'")
            checked.add(node_id)

    # Check bidirectional dependency consistency
    for node_id, node in hierarchy.items():
        if 'dependencies' not in node:
            continue

        deps = node['dependencies']

        # Handle malformed dependencies (should be dict, not list)
        if not isinstance(deps, dict):
            errors.append(
                f"❌ ERROR: Node '{node_id}' has malformed dependencies field (expected dict, got {type(deps).__name__})"
            )
            continue

        # If A blocks B, then B should list A in blocked_by
        for blocked_id in deps.get('blocks', []):
            if blocked_id in hierarchy:
                blocked_node = hierarchy[blocked_id]
                blocked_deps = blocked_node.get('dependencies', {})
                # Handle malformed dependencies in blocked node
                if not isinstance(blocked_deps, dict):
                    blocked_deps = {}
                if node_id not in blocked_deps.get('blocked_by', []):
                    errors.append(
                        f"❌ ERROR: Bidirectional dependency inconsistency: '{node_id}' blocks '{blocked_id}', " +
                        f"but '{blocked_id}' doesn't list '{node_id}' in blocked_by"
                    )

        # If A is blocked_by B, then B should list A in blocks
        for blocker_id in deps.get('blocked_by', []):
            if blocker_id in hierarchy:
                blocker_node = hierarchy[blocker_id]
                blocker_deps = blocker_node.get('dependencies', {})
                # Handle malformed dependencies in blocker node
                if not isinstance(blocker_deps, dict):
                    blocker_deps = {}
                if node_id not in blocker_deps.get('blocks', []):
                    errors.append(
                        f"❌ ERROR: Bidirectional dependency inconsistency: '{node_id}' blocked_by '{blocker_id}', " +
                        f"but '{blocker_id}' doesn't list '{node_id}' in blocks"
                    )

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_metadata(hierarchy: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate type-specific metadata requirements.

    Args:
        hierarchy: Hierarchy dictionary from JSON spec file

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []

    for node_id, node in hierarchy.items():
        node_type = node.get('type')
        metadata = node.get('metadata', {})

        if not isinstance(metadata, dict):
            errors.append(f"❌ ERROR: Node '{node_id}' metadata must be a dictionary")
            continue

        # Verify nodes should have verification_type, command, expected
        if node_type == 'verify':
            if 'verification_type' not in metadata:
                errors.append(
                    f"❌ ERROR: Verify node '{node_id}' missing metadata.verification_type"
                )
            elif metadata['verification_type'] not in ['auto', 'manual', 'fidelity']:
                errors.append(
                    f"❌ ERROR: Verify node '{node_id}' verification_type must be 'auto', 'manual', or 'fidelity'"
                )

            # command and expected are only relevant for auto/manual verification
            verification_type = metadata.get('verification_type')
            if verification_type in ['auto', 'manual']:
                if 'command' not in metadata:
                    warnings.append(f"⚠️  WARNING: Verify node '{node_id}' missing metadata.command")

                if 'expected' not in metadata:
                    warnings.append(f"⚠️  WARNING: Verify node '{node_id}' missing metadata.expected")

            # fidelity verification should have scope and target
            elif verification_type == 'fidelity':
                if 'agent' not in metadata:
                    warnings.append(f"⚠️  WARNING: Verify node '{node_id}' with fidelity type should have metadata.agent = 'sdd-fidelity-review'")
                if 'scope' not in metadata:
                    warnings.append(f"⚠️  WARNING: Verify node '{node_id}' with fidelity type missing metadata.scope (phase/task/file)")
                if 'target' not in metadata:
                    warnings.append(f"⚠️  WARNING: Verify node '{node_id}' with fidelity type missing metadata.target")

        # Task nodes should have file_path based on task_category
        if node_type == 'task':
            # Define allowed task categories
            allowed_categories = ['investigation', 'implementation', 'refactoring', 'decision', 'research']

            raw_category = metadata.get('task_category')
            has_explicit_category = 'task_category' in metadata

            if isinstance(raw_category, str):
                normalized_category = raw_category.strip()
            else:
                normalized_category = raw_category

            if has_explicit_category and (normalized_category is None or normalized_category == ""):
                errors.append(
                    f"❌ ERROR: Task node '{node_id}' has empty task_category; "
                    f"set it to one of: {', '.join(allowed_categories)}"
                )
                normalized_category = None

            task_category = normalized_category or 'implementation'

            # Validate task_category is in allowed enum values
            if has_explicit_category and normalized_category and task_category not in allowed_categories:
                errors.append(
                    f"❌ ERROR: Task node '{node_id}' has invalid task_category '{task_category}'. "
                    f"Must be one of: {', '.join(allowed_categories)}"
                )

            # file_path required for implementation and refactoring tasks
            if task_category in ['implementation', 'refactoring']:
                if 'file_path' not in metadata:
                    errors.append(
                        f"❌ ERROR: Task node '{node_id}' with category '{task_category}' missing metadata.file_path"
                    )

            # Warning if non-code tasks have file_path (unusual but not wrong)
            if task_category in ['investigation', 'decision', 'research']:
                if 'file_path' in metadata:
                    warnings.append(
                        f"⚠️  WARNING: Task node '{node_id}' with category '{task_category}' has metadata.file_path "
                        f"(usually not needed for this category)"
                    )

    is_valid = len(errors) == 0
    return (is_valid, errors, warnings)


def validate_spec_hierarchy(spec_data: Dict) -> JsonSpecValidationResult:
    """
    Validate JSON spec file hierarchy with all checks.

    Args:
        spec_data: JSON spec file data dictionary

    Returns:
        JsonSpecValidationResult with all validation findings
    """
    # Initialize result
    result = JsonSpecValidationResult(
        spec_id=spec_data.get('spec_id', 'unknown'),
        generated=spec_data.get('generated', 'unknown'),
        last_updated=spec_data.get('last_updated', 'unknown'),
        spec_data=spec_data,
    )

    schema_errors, schema_warnings, schema_source = _validate_against_schema(spec_data)
    result.schema_errors = schema_errors
    result.schema_warnings = schema_warnings
    result.schema_source = schema_source
    result.enhanced_errors.extend(
        _build_enhanced_errors(schema_errors, severity_hint="error", category="schema")
    )
    result.enhanced_errors.extend(
        _build_enhanced_errors(schema_warnings, severity_hint="warning", category="schema")
    )

    hierarchy = spec_data.get('hierarchy', {})

    # 1. Validate structure
    struct_valid, struct_errors, struct_warnings = validate_structure(spec_data)
    result.structure_errors = struct_errors
    result.structure_warnings = struct_warnings
    result.enhanced_errors.extend(
        _build_enhanced_errors(struct_errors, severity_hint="error", category="structure")
    )
    result.enhanced_errors.extend(
        _build_enhanced_errors(struct_warnings, severity_hint="warning", category="structure")
    )

    # 2. Validate hierarchy
    if hierarchy:
        hier_valid, hier_errors, hier_warnings = validate_hierarchy(hierarchy)
        result.hierarchy_errors = hier_errors
        result.hierarchy_warnings = hier_warnings
        result.enhanced_errors.extend(
            _build_enhanced_errors(hier_errors, severity_hint="error", category="hierarchy")
        )
        result.enhanced_errors.extend(
            _build_enhanced_errors(hier_warnings, severity_hint="warning", category="hierarchy")
        )

        # 3. Validate nodes
        node_valid, node_errors, node_warnings = validate_nodes(hierarchy)
        result.node_errors = node_errors
        result.node_warnings = node_warnings
        result.enhanced_errors.extend(
            _build_enhanced_errors(node_errors, severity_hint="error", category="node")
        )
        result.enhanced_errors.extend(
            _build_enhanced_errors(node_warnings, severity_hint="warning", category="node")
        )

        # 4. Validate task counts
        count_valid, count_errors, count_warnings = validate_task_counts(hierarchy)
        result.count_errors = count_errors
        result.count_warnings = count_warnings
        result.enhanced_errors.extend(
            _build_enhanced_errors(count_errors, severity_hint="error", category="counts")
        )
        result.enhanced_errors.extend(
            _build_enhanced_errors(count_warnings, severity_hint="warning", category="counts")
        )

        # 5. Validate dependencies
        dep_valid, dep_errors, dep_warnings = validate_dependencies(hierarchy)
        result.dependency_errors = dep_errors
        result.dependency_warnings = dep_warnings
        result.enhanced_errors.extend(
            _build_enhanced_errors(dep_errors, severity_hint="error", category="dependency")
        )
        result.enhanced_errors.extend(
            _build_enhanced_errors(dep_warnings, severity_hint="warning", category="dependency")
        )

        # 6. Validate metadata
        meta_valid, meta_errors, meta_warnings = validate_metadata(hierarchy)
        result.metadata_errors = meta_errors
        result.metadata_warnings = meta_warnings
        result.enhanced_errors.extend(
            _build_enhanced_errors(meta_errors, severity_hint="error", category="metadata")
        )
        result.enhanced_errors.extend(
            _build_enhanced_errors(meta_warnings, severity_hint="warning", category="metadata")
        )

        # Calculate stats
        result.total_nodes = len(hierarchy)
        if 'spec-root' in hierarchy:
            root = hierarchy['spec-root']
            result.total_tasks = root.get('total_tasks', 0)
            result.completed_tasks = root.get('completed_tasks', 0)

    return result
