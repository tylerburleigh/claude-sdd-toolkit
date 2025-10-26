#!/usr/bin/env python3
"""
Trace-entry workflow: Trace execution flow from an entry function.

This workflow provides call chain traversal with architectural layer detection,
complexity analysis, and hot spot identification.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import json


def trace_execution_flow(
    query: Any,  # DocumentationQuery
    function_name: str,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Trace the execution flow starting from an entry function.

    Builds a call chain showing all functions called (directly or indirectly)
    from the specified entry function, with architectural layer detection
    and complexity analysis.

    Args:
        query: DocumentationQuery instance
        function_name: Name of the entry function to trace from
        max_depth: Maximum call chain depth to traverse (default: 5)

    Returns:
        Dictionary with keys:
        - entry_function: Starting function name
        - max_depth: Maximum depth used
        - call_chain: Dict with nodes, edges, layers, hot_spots
        - summary: Statistics about the trace

    Example:
        >>> query = DocumentationQuery()
        >>> query.load()
        >>> result = trace_execution_flow(query, "main", max_depth=3)
        >>> print(f"Traced {result['summary']['total_functions']} functions")
    """
    # Build call graph using existing function (downstream only)
    graph = query.build_call_graph(
        function_name,
        direction="callees",  # Only downstream calls
        max_depth=max_depth,
        include_metadata=True
    )

    # Enrich nodes with additional information
    enriched_nodes = {}
    for node_name, node_data in graph.get('nodes', {}).items():
        # Get function details from documentation
        functions = [f for f in query.data.get('functions', [])
                    if f.get('name') == node_name]

        if functions:
            func = functions[0]
            enriched_nodes[node_name] = {
                'name': node_name,
                'file': func.get('file', 'unknown'),
                'complexity': func.get('complexity', 0),
                'line': func.get('line', 0),
                'calls_count': len(func.get('calls', [])),
                'depth': node_data.get('depth', 0)
            }
        else:
            # Node exists in graph but not in documentation (external call)
            enriched_nodes[node_name] = {
                'name': node_name,
                'file': 'external',
                'complexity': 0,
                'line': 0,
                'calls_count': 0,
                'depth': node_data.get('depth', 0)
            }

    # Identify architectural layers
    layers = identify_layers(enriched_nodes)

    # Add layer information to nodes
    for node_name in enriched_nodes:
        enriched_nodes[node_name]['layer'] = layers.get(node_name, 'Core')

    # Identify hot spots
    hot_spots = identify_hot_spots(enriched_nodes)

    # Build layer summary
    layer_groups: Dict[str, List[str]] = {}
    for node_name, layer in layers.items():
        if layer not in layer_groups:
            layer_groups[layer] = []
        layer_groups[layer].append(node_name)

    # Calculate summary statistics
    complexities = [node['complexity'] for node in enriched_nodes.values()
                   if node['complexity'] > 0]

    summary = {
        'total_functions': len(enriched_nodes),
        'max_depth_reached': graph.get('truncated', False),
        'layers_involved': sorted(layer_groups.keys()),
        'complexity_range': (min(complexities) if complexities else 0,
                            max(complexities) if complexities else 0),
        'avg_complexity': (sum(complexities) / len(complexities) if complexities else 0),
        'hot_spot_count': len(hot_spots)
    }

    return {
        'entry_function': function_name,
        'max_depth': max_depth,
        'call_chain': {
            'nodes': enriched_nodes,
            'edges': graph.get('edges', []),
            'layers': layer_groups,
            'hot_spots': hot_spots
        },
        'summary': summary
    }


def identify_layers(nodes: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """
    Identify architectural layer for each function based on file path patterns.

    Uses heuristic matching on file paths to classify functions into
    architectural layers (Presentation, Business Logic, Data, Utility, Core).

    Args:
        nodes: Dictionary of function nodes with 'file' attribute

    Returns:
        Dictionary mapping function name to layer name

    Layer Classification Rules:
        - Presentation: routes/, cli/, api/, handlers/, controllers/
        - Business Logic: services/, business/, workflows/, processors/
        - Data: models/, database/, repositories/, dao/, persistence/
        - Utility: utils/, helpers/, common/, lib/
        - Core: Everything else
    """
    layers = {}

    # Layer detection patterns (path components)
    layer_patterns = {
        'Presentation': ['routes', 'cli', 'api', 'handlers', 'controllers', 'views'],
        'Business Logic': ['services', 'business', 'workflows', 'processors', 'logic'],
        'Data': ['models', 'database', 'repositories', 'dao', 'persistence', 'storage'],
        'Utility': ['utils', 'helpers', 'common', 'lib', 'tools']
    }

    for node_name, node_data in nodes.items():
        file_path = node_data.get('file', '').lower()

        # Skip external functions
        if file_path == 'external' or file_path == 'unknown':
            layers[node_name] = 'External'
            continue

        # Check each layer pattern
        matched = False
        for layer_name, patterns in layer_patterns.items():
            if any(f'/{pattern}/' in file_path or file_path.startswith(f'{pattern}/')
                   for pattern in patterns):
                layers[node_name] = layer_name
                matched = True
                break

        # Default to Core if no match
        if not matched:
            layers[node_name] = 'Core'

    return layers


def identify_hot_spots(nodes: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify complexity hot spots in the call chain.

    Hot spots are functions that exhibit concerning characteristics:
    - High cyclomatic complexity (> 10)
    - High fan-out (many direct calls, > 5)
    - Both high complexity AND high fan-out (critical)

    Args:
        nodes: Dictionary of function nodes with complexity and calls_count

    Returns:
        List of hot spot dictionaries with:
        - function: Function name
        - reason: Why it's flagged
        - severity: 'high', 'medium', or 'low'
        - complexity: Complexity score
        - fan_out: Number of direct calls
    """
    hot_spots = []

    HIGH_COMPLEXITY_THRESHOLD = 10
    HIGH_FAN_OUT_THRESHOLD = 5

    for node_name, node_data in nodes.items():
        complexity = node_data.get('complexity', 0)
        fan_out = node_data.get('calls_count', 0)

        # Skip external functions
        if node_data.get('file') in ('external', 'unknown'):
            continue

        reasons = []
        severity = 'low'

        # Check complexity
        if complexity > HIGH_COMPLEXITY_THRESHOLD * 2:  # Very high (> 20)
            reasons.append(f'very high complexity ({complexity})')
            severity = 'high'
        elif complexity > HIGH_COMPLEXITY_THRESHOLD:  # High (> 10)
            reasons.append(f'high complexity ({complexity})')
            if severity != 'high':
                severity = 'medium'

        # Check fan-out
        if fan_out > HIGH_FAN_OUT_THRESHOLD * 2:  # Very high (> 10)
            reasons.append(f'very high fan-out ({fan_out} calls)')
            severity = 'high'
        elif fan_out > HIGH_FAN_OUT_THRESHOLD:  # High (> 5)
            reasons.append(f'high fan-out ({fan_out} calls)')
            if severity == 'low':
                severity = 'medium'

        # Both high complexity and fan-out = critical
        if complexity > HIGH_COMPLEXITY_THRESHOLD and fan_out > HIGH_FAN_OUT_THRESHOLD:
            severity = 'high'
            reasons.append('complex logic with many dependencies')

        if reasons:
            hot_spots.append({
                'function': node_name,
                'reason': ', '.join(reasons),
                'severity': severity,
                'complexity': complexity,
                'fan_out': fan_out,
                'file': node_data.get('file', 'unknown'),
                'layer': node_data.get('layer', 'Unknown')
            })

    # Sort by severity (high first), then complexity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    hot_spots.sort(key=lambda x: (severity_order[x['severity']], -x['complexity']))

    return hot_spots


def format_tree_view(trace_result: Dict[str, Any]) -> str:
    """
    Format trace result as an ASCII tree visualization.

    Creates a hierarchical tree showing the call chain from the entry function,
    with layer annotations, complexity scores, and hot spot markers.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        Formatted tree string with Unicode box-drawing characters

    Example Output:
        main [Presentation] (complexity: 8)
        ├─ process_data [Business Logic] (complexity: 15) 🔥
        │  ├─ validate [Utility] (complexity: 3)
        │  └─ save [Data] (complexity: 5)
        └─ format_output [Presentation] (complexity: 2)
    """
    entry_function = trace_result['entry_function']
    nodes = trace_result['call_chain']['nodes']
    edges = trace_result['call_chain']['edges']
    hot_spots = trace_result['call_chain']['hot_spots']

    # Create hot spot lookup for fast checking
    hot_spot_names = {hs['function'] for hs in hot_spots}

    # Build adjacency list for tree traversal
    adjacency: Dict[str, List[str]] = {}
    for edge in edges:
        from_func = edge['from']
        to_func = edge['to']
        if from_func not in adjacency:
            adjacency[from_func] = []
        adjacency[from_func].append(to_func)

    # Build tree recursively
    lines = []
    visited: Set[str] = set()

    def build_tree(func_name: str, prefix: str = "", is_last: bool = True):
        """Recursively build tree representation."""
        if func_name in visited:
            return  # Avoid cycles
        visited.add(func_name)

        # Get node info
        node = nodes.get(func_name, {})
        layer = node.get('layer', 'Unknown')
        complexity = node.get('complexity', 0)

        # Build line
        connector = "└─ " if is_last else "├─ "
        hot_spot_marker = " 🔥" if func_name in hot_spot_names else ""

        if func_name == entry_function:
            # Root node - no connector
            line = f"{func_name} [{layer}] (complexity: {complexity}){hot_spot_marker}"
        else:
            line = f"{prefix}{connector}{func_name} [{layer}] (complexity: {complexity}){hot_spot_marker}"

        lines.append(line)

        # Get children
        children = adjacency.get(func_name, [])
        if not children:
            return

        # Build prefix for children
        if func_name == entry_function:
            child_prefix = ""
        else:
            child_prefix = prefix + ("   " if is_last else "│  ")

        # Recursively process children
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            build_tree(child, child_prefix, is_last_child)

    build_tree(entry_function)

    return "\n".join(lines)


def format_layer_summary(trace_result: Dict[str, Any]) -> str:
    """
    Format layer breakdown summary.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        Formatted string with layer statistics
    """
    layers = trace_result['call_chain']['layers']

    lines = ["Layer Breakdown:"]
    for layer in sorted(layers.keys()):
        functions = layers[layer]
        lines.append(f"  {layer}: {len(functions)} function(s)")
        # Show first few functions as examples
        examples = functions[:3]
        for func in examples:
            lines.append(f"    - {func}")
        if len(functions) > 3:
            lines.append(f"    ... and {len(functions) - 3} more")

    return "\n".join(lines)


def format_hot_spots(trace_result: Dict[str, Any]) -> str:
    """
    Format hot spots table.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        Formatted string with hot spots table
    """
    hot_spots = trace_result['call_chain']['hot_spots']

    if not hot_spots:
        return "No hot spots detected."

    lines = [f"Hot Spots Detected: {len(hot_spots)}"]
    lines.append("")

    for i, hs in enumerate(hot_spots, 1):
        severity_icon = "🔴" if hs['severity'] == 'high' else "🟡" if hs['severity'] == 'medium' else "🟢"
        lines.append(f"{i}. {severity_icon} {hs['function']} ({hs['layer']})")
        lines.append(f"   Reason: {hs['reason']}")
        lines.append(f"   File: {hs['file']}")
        lines.append("")

    return "\n".join(lines)


def format_summary(trace_result: Dict[str, Any]) -> str:
    """
    Format summary statistics.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        Formatted string with summary statistics
    """
    summary = trace_result['summary']

    lines = ["Summary:"]
    lines.append(f"  Total functions: {summary['total_functions']}")
    lines.append(f"  Layers: {', '.join(summary['layers_involved'])}")
    lines.append(f"  Complexity range: {summary['complexity_range'][0]}-{summary['complexity_range'][1]} (avg: {summary['avg_complexity']:.1f})")
    lines.append(f"  Hot spots: {summary['hot_spot_count']}")

    if summary['max_depth_reached']:
        lines.append(f"  ⚠️  Max depth ({trace_result['max_depth']}) reached - call chain may be incomplete")

    return "\n".join(lines)


def format_text_output(trace_result: Dict[str, Any]) -> str:
    """
    Format complete text output for trace-entry command.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        Formatted string with all sections
    """
    sections = []

    # Header
    sections.append(f"🎯 Execution Flow: {trace_result['entry_function']}")
    sections.append("")

    # Tree view
    sections.append(format_tree_view(trace_result))
    sections.append("")

    # Hot spots
    sections.append(format_hot_spots(trace_result))
    sections.append("")

    # Layer summary
    sections.append(format_layer_summary(trace_result))
    sections.append("")

    # Summary
    sections.append(format_summary(trace_result))

    return "\n".join(sections)


def format_json_output(trace_result: Dict[str, Any]) -> str:
    """
    Format trace result as JSON.

    Args:
        trace_result: Output from trace_execution_flow()

    Returns:
        JSON string
    """
    return json.dumps(trace_result, indent=2)
