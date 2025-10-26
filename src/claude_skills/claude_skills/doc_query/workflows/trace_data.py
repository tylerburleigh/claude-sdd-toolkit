#!/usr/bin/env python3
"""
Trace-data workflow: Trace data object lifecycle through the codebase.

This workflow provides lifecycle tracking for data objects (classes), showing
creation patterns, CRUD operations, data flow by layer, and mutation analysis.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import json


def trace_data_lifecycle(
    query: Any,  # DocumentationQuery
    class_name: str,
    include_properties: bool = False
) -> Dict[str, Any]:
    """
    Trace the lifecycle of a data object (class) through the codebase.

    Analyzes how instances of a class are created, used, modified, and destroyed,
    providing insights into data flow patterns and usage across architectural layers.

    Args:
        query: DocumentationQuery instance
        class_name: Name of the class to trace
        include_properties: Whether to include detailed property access analysis

    Returns:
        Dictionary with keys:
        - class_name: Name of the traced class
        - class_info: Basic class information
        - lifecycle: Dict with creation, read, update, delete operations
        - data_flow: Flow organized by architectural layer
        - property_analysis: Property access patterns (if include_properties=True)
        - summary: Statistics about the lifecycle

    Example:
        >>> query = DocumentationQuery()
        >>> query.load()
        >>> result = trace_data_lifecycle(query, "User", include_properties=True)
        >>> print(f"Found {result['summary']['total_operations']} operations")
    """
    # Find the class definition
    classes = [c for c in query.data.get('classes', [])
               if c.get('name') == class_name]

    if not classes:
        # Class not found - return empty result
        return {
            'class_name': class_name,
            'class_info': None,
            'lifecycle': {
                'create': [],
                'read': [],
                'update': [],
                'delete': []
            },
            'data_flow': {},
            'property_analysis': {} if include_properties else None,
            'summary': {
                'class_found': False,
                'total_operations': 0,
                'layers_involved': []
            }
        }

    class_info = classes[0]

    # Get instantiation points from cross-reference data
    instantiated_by = class_info.get('instantiated_by', [])

    # Detect CRUD operations
    crud_ops = detect_crud_operations(query, class_name, class_info)

    # Build data flow by layer
    data_flow = build_data_flow(query, class_name, crud_ops)

    # Property analysis (if requested)
    property_analysis = None
    if include_properties:
        property_analysis = analyze_property_access(
            query, class_name, class_info, crud_ops
        )

    # Calculate summary statistics
    total_ops = (len(crud_ops['create']) + len(crud_ops['read']) +
                 len(crud_ops['update']) + len(crud_ops['delete']))

    layers_involved = sorted(set(data_flow.keys()))

    summary = {
        'class_found': True,
        'total_operations': total_ops,
        'create_count': len(crud_ops['create']),
        'read_count': len(crud_ops['read']),
        'update_count': len(crud_ops['update']),
        'delete_count': len(crud_ops['delete']),
        'layers_involved': layers_involved,
        'instantiation_points': len(instantiated_by)
    }

    return {
        'class_name': class_name,
        'class_info': {
            'name': class_info.get('name'),
            'file': class_info.get('file'),
            'line': class_info.get('line'),
            'docstring': class_info.get('docstring', ''),
            'methods': class_info.get('methods', []),
            'properties': class_info.get('properties', [])
        },
        'lifecycle': crud_ops,
        'data_flow': data_flow,
        'property_analysis': property_analysis,
        'summary': summary
    }


def detect_crud_operations(
    query: Any,
    class_name: str,
    class_info: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect Create, Read, Update, Delete operations for a class.

    Uses heuristic analysis of function names, instantiation data,
    and method calls to classify operations.

    Args:
        query: DocumentationQuery instance
        class_name: Name of the class being traced
        class_info: Class information dictionary

    Returns:
        Dictionary with keys 'create', 'read', 'update', 'delete',
        each containing a list of operation dictionaries with:
        - function: Function name performing the operation
        - file: File path
        - line: Line number
        - operation_type: Specific operation (e.g., 'constructor', 'getter', 'setter')
    """
    crud_ops = {
        'create': [],
        'read': [],
        'update': [],
        'delete': []
    }

    # Get instantiation data (CREATE operations)
    instantiated_by = class_info.get('instantiated_by', [])
    for inst in instantiated_by:
        func_name = inst.get('caller', '')

        # Find the function details
        functions = [f for f in query.data.get('functions', [])
                    if f.get('name') == func_name]

        if functions:
            func = functions[0]
            crud_ops['create'].append({
                'function': func_name,
                'file': func.get('file', 'unknown'),
                'line': inst.get('line', 0),
                'operation_type': 'instantiation'
            })

    # Get all functions that use this class
    all_functions = query.data.get('functions', [])

    for func in all_functions:
        func_name = func.get('name', '')
        func_name_lower = func_name.lower()

        # Check if function calls any methods of this class
        calls = func.get('calls', [])
        class_method_calls = [c for c in calls
                             if any(c.get('name', '').startswith(m)
                                   for m in class_info.get('methods', []))]

        if not class_method_calls:
            continue

        # Classify based on function name patterns
        operation_type = None
        category = None

        # CREATE patterns
        if any(pattern in func_name_lower for pattern in
               ['create', 'new', 'build', 'make', 'init', 'construct']):
            category = 'create'
            operation_type = 'factory_method'

        # READ patterns
        elif any(pattern in func_name_lower for pattern in
                ['get', 'find', 'fetch', 'load', 'read', 'query', 'search', 'list']):
            category = 'read'
            operation_type = 'accessor'

        # UPDATE patterns
        elif any(pattern in func_name_lower for pattern in
                ['set', 'update', 'modify', 'change', 'edit', 'save', 'write']):
            category = 'update'
            operation_type = 'mutator'

        # DELETE patterns
        elif any(pattern in func_name_lower for pattern in
                ['delete', 'remove', 'destroy', 'clear', 'drop']):
            category = 'delete'
            operation_type = 'destructor'

        # Default to READ if no clear pattern (conservative)
        else:
            category = 'read'
            operation_type = 'accessor'

        if category:
            crud_ops[category].append({
                'function': func_name,
                'file': func.get('file', 'unknown'),
                'line': func.get('line', 0),
                'operation_type': operation_type,
                'method_calls': [c.get('name') for c in class_method_calls]
            })

    return crud_ops


def build_data_flow(
    query: Any,
    class_name: str,
    crud_ops: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Build data flow organized by architectural layer.

    Groups CRUD operations by layer (Presentation, Business Logic, Data, etc.)
    to show how data flows through the architecture.

    Args:
        query: DocumentationQuery instance
        class_name: Name of the class being traced
        crud_ops: CRUD operations from detect_crud_operations()

    Returns:
        Dictionary mapping layer names to operation categories:
        {
            'Presentation': {'create': [...], 'read': [...], ...},
            'Business Logic': {'create': [...], 'read': [...], ...},
            ...
        }
    """
    # Layer detection patterns (same as trace_entry.py)
    layer_patterns = {
        'Presentation': ['routes', 'cli', 'api', 'handlers', 'controllers', 'views'],
        'Business Logic': ['services', 'business', 'workflows', 'processors', 'logic'],
        'Data': ['models', 'database', 'repositories', 'dao', 'persistence', 'storage'],
        'Utility': ['utils', 'helpers', 'common', 'lib', 'tools']
    }

    data_flow: Dict[str, Dict[str, List[str]]] = {}

    # Process all CRUD operations
    for operation_category, operations in crud_ops.items():
        for op in operations:
            file_path = op.get('file', '').lower()

            # Determine layer
            layer = 'Core'  # Default
            if file_path in ('external', 'unknown'):
                layer = 'External'
            else:
                for layer_name, patterns in layer_patterns.items():
                    if any(f'/{pattern}/' in file_path or
                          file_path.startswith(f'{pattern}/')
                          for pattern in patterns):
                        layer = layer_name
                        break

            # Initialize layer if needed
            if layer not in data_flow:
                data_flow[layer] = {
                    'create': [],
                    'read': [],
                    'update': [],
                    'delete': []
                }

            # Add function to appropriate category
            func_name = op.get('function', '')
            if func_name and func_name not in data_flow[layer][operation_category]:
                data_flow[layer][operation_category].append(func_name)

    return data_flow


def analyze_property_access(
    query: Any,
    class_name: str,
    class_info: Dict[str, Any],
    crud_ops: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Analyze property access patterns for the class.

    Identifies which properties are accessed in which operations,
    highlighting frequently accessed or modified properties.

    Args:
        query: DocumentationQuery instance
        class_name: Name of the class
        class_info: Class information dictionary
        crud_ops: CRUD operations from detect_crud_operations()

    Returns:
        Dictionary with property access statistics:
        - properties: List of property names
        - access_patterns: Dict mapping properties to access counts
        - mutation_hot_spots: Properties frequently modified
    """
    properties = class_info.get('properties', [])

    if not properties:
        return {
            'properties': [],
            'access_patterns': {},
            'mutation_hot_spots': []
        }

    # Track property access (simplified heuristic based on method names)
    access_patterns: Dict[str, Dict[str, int]] = {}

    for prop in properties:
        access_patterns[prop] = {
            'read_count': 0,
            'write_count': 0
        }

    # Analyze read operations
    for op in crud_ops.get('read', []):
        method_calls = op.get('method_calls', [])
        for method in method_calls:
            # Heuristic: getter methods often contain property name
            for prop in properties:
                if prop.lower() in method.lower():
                    access_patterns[prop]['read_count'] += 1

    # Analyze update operations
    for op in crud_ops.get('update', []):
        method_calls = op.get('method_calls', [])
        for method in method_calls:
            # Heuristic: setter methods often contain property name
            for prop in properties:
                if prop.lower() in method.lower():
                    access_patterns[prop]['write_count'] += 1

    # Identify mutation hot spots (frequently written properties)
    mutation_hot_spots = [
        {
            'property': prop,
            'write_count': stats['write_count']
        }
        for prop, stats in access_patterns.items()
        if stats['write_count'] > 0
    ]
    mutation_hot_spots.sort(key=lambda x: -x['write_count'])

    return {
        'properties': properties,
        'access_patterns': access_patterns,
        'mutation_hot_spots': mutation_hot_spots[:5]  # Top 5
    }


def format_lifecycle_view(trace_result: Dict[str, Any]) -> str:
    """
    Format lifecycle visualization showing CRUD flow.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        Formatted string with lifecycle stages
    """
    class_name = trace_result['class_name']
    class_info = trace_result['class_info']
    lifecycle = trace_result['lifecycle']

    if not class_info:
        return f"❌ Class '{class_name}' not found in documentation"

    lines = [f"📦 Data Lifecycle: {class_name}"]
    lines.append("")
    lines.append(f"Defined in: {class_info['file']}:{class_info['line']}")
    if class_info['docstring']:
        lines.append(f"Purpose: {class_info['docstring'][:100]}...")
    lines.append("")

    # CREATE stage
    create_ops = lifecycle.get('create', [])
    lines.append(f"🆕 CREATE ({len(create_ops)} operations)")
    if create_ops:
        for op in create_ops[:5]:  # Show first 5
            lines.append(f"  • {op['function']}() in {op['file']}")
        if len(create_ops) > 5:
            lines.append(f"  ... and {len(create_ops) - 5} more")
    else:
        lines.append("  (No instantiation points found)")
    lines.append("")

    # READ stage
    read_ops = lifecycle.get('read', [])
    lines.append(f"👁️  READ ({len(read_ops)} operations)")
    if read_ops:
        for op in read_ops[:5]:
            lines.append(f"  • {op['function']}() - {op['operation_type']}")
        if len(read_ops) > 5:
            lines.append(f"  ... and {len(read_ops) - 5} more")
    else:
        lines.append("  (No read operations found)")
    lines.append("")

    # UPDATE stage
    update_ops = lifecycle.get('update', [])
    lines.append(f"✏️  UPDATE ({len(update_ops)} operations)")
    if update_ops:
        for op in update_ops[:5]:
            lines.append(f"  • {op['function']}() - {op['operation_type']}")
        if len(update_ops) > 5:
            lines.append(f"  ... and {len(update_ops) - 5} more")
    else:
        lines.append("  (No update operations found)")
    lines.append("")

    # DELETE stage
    delete_ops = lifecycle.get('delete', [])
    lines.append(f"🗑️  DELETE ({len(delete_ops)} operations)")
    if delete_ops:
        for op in delete_ops[:5]:
            lines.append(f"  • {op['function']}() - {op['operation_type']}")
        if len(delete_ops) > 5:
            lines.append(f"  ... and {len(delete_ops) - 5} more")
    else:
        lines.append("  (No delete operations found)")

    return "\n".join(lines)


def format_usage_map(trace_result: Dict[str, Any]) -> str:
    """
    Format usage map organized by architectural layer.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        Formatted string with layer breakdown
    """
    data_flow = trace_result['data_flow']

    if not data_flow:
        return "No data flow detected."

    lines = ["📊 Usage by Layer:"]
    lines.append("")

    for layer in sorted(data_flow.keys()):
        layer_ops = data_flow[layer]

        # Count total operations in this layer
        total = sum(len(ops) for ops in layer_ops.values())

        lines.append(f"### {layer} ({total} operations)")

        for op_type in ['create', 'read', 'update', 'delete']:
            ops = layer_ops.get(op_type, [])
            if ops:
                lines.append(f"  {op_type.upper()}: {len(ops)} function(s)")
                for func in ops[:3]:  # Show first 3
                    lines.append(f"    - {func}()")
                if len(ops) > 3:
                    lines.append(f"    ... and {len(ops) - 3} more")

        lines.append("")

    return "\n".join(lines)


def format_property_analysis(trace_result: Dict[str, Any]) -> str:
    """
    Format property access analysis.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        Formatted string with property analysis
    """
    property_analysis = trace_result.get('property_analysis')

    if not property_analysis:
        return ""

    properties = property_analysis.get('properties', [])
    if not properties:
        return "🔍 Property Analysis: No properties detected\n"

    lines = ["🔍 Property Analysis:"]
    lines.append("")

    access_patterns = property_analysis.get('access_patterns', {})

    lines.append(f"Total Properties: {len(properties)}")
    lines.append("")

    # Show access patterns
    lines.append("Access Patterns:")
    for prop, stats in sorted(access_patterns.items(),
                             key=lambda x: -(x[1]['read_count'] + x[1]['write_count'])):
        read_count = stats['read_count']
        write_count = stats['write_count']
        if read_count > 0 or write_count > 0:
            lines.append(f"  • {prop}: {read_count} reads, {write_count} writes")
    lines.append("")

    # Show mutation hot spots
    mutation_hot_spots = property_analysis.get('mutation_hot_spots', [])
    if mutation_hot_spots:
        lines.append("🔥 Mutation Hot Spots:")
        for hot_spot in mutation_hot_spots:
            lines.append(f"  • {hot_spot['property']}: {hot_spot['write_count']} writes")
        lines.append("")

    return "\n".join(lines)


def format_summary(trace_result: Dict[str, Any]) -> str:
    """
    Format summary statistics.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        Formatted string with summary
    """
    summary = trace_result['summary']

    lines = ["📈 Summary:"]
    lines.append(f"  Total operations: {summary['total_operations']}")
    lines.append(f"  Create: {summary['create_count']}")
    lines.append(f"  Read: {summary['read_count']}")
    lines.append(f"  Update: {summary['update_count']}")
    lines.append(f"  Delete: {summary['delete_count']}")
    lines.append(f"  Layers involved: {', '.join(summary['layers_involved'])}")
    lines.append(f"  Instantiation points: {summary['instantiation_points']}")

    return "\n".join(lines)


def format_text_output(trace_result: Dict[str, Any]) -> str:
    """
    Format complete text output for trace-data command.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        Formatted string with all sections
    """
    sections = []

    # Lifecycle view
    sections.append(format_lifecycle_view(trace_result))
    sections.append("")

    # Usage map by layer
    sections.append(format_usage_map(trace_result))
    sections.append("")

    # Property analysis (if available)
    if trace_result.get('property_analysis'):
        sections.append(format_property_analysis(trace_result))
        sections.append("")

    # Summary
    sections.append(format_summary(trace_result))

    return "\n".join(sections)


def format_json_output(trace_result: Dict[str, Any]) -> str:
    """
    Format trace result as JSON.

    Args:
        trace_result: Output from trace_data_lifecycle()

    Returns:
        JSON string
    """
    return json.dumps(trace_result, indent=2)
