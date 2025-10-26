#!/usr/bin/env python3
"""
Impact analysis workflow: Calculate blast radius of code changes.

This workflow provides change impact analysis showing what code will be affected
by modifying a function or class, including test coverage and risk assessment.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import json


def analyze_impact(
    query: Any,  # DocumentationQuery
    entity_name: str,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Analyze the impact of changing a function or class.

    Calculates the "blast radius" showing all directly and indirectly affected code,
    test coverage, and risk assessment with refactoring recommendations.

    Args:
        query: DocumentationQuery instance
        entity_name: Name of the function or class to analyze
        depth: Maximum depth for indirect dependency traversal (default: 2)

    Returns:
        Dictionary with keys:
        - entity_name: Name of the analyzed entity
        - entity_type: 'function' or 'class'
        - entity_info: Basic entity information
        - blast_radius: Dict with direct_dependents, indirect_dependents
        - test_coverage: Dict with test files and estimated coverage
        - risk_assessment: Dict with score, level, factors
        - recommendations: List of actionable recommendations
        - summary: Statistics about the impact

    Example:
        >>> query = DocumentationQuery()
        >>> query.load()
        >>> result = analyze_impact(query, "load", depth=2)
        >>> print(f"Risk level: {result['risk_assessment']['level']}")
    """
    # Determine entity type and find entity
    entity_type, entity_info = _find_entity(query, entity_name)

    if not entity_info:
        # Entity not found - return empty result
        return {
            'entity_name': entity_name,
            'entity_type': None,
            'entity_info': None,
            'blast_radius': {
                'direct_dependents': [],
                'indirect_dependents': []
            },
            'test_coverage': {
                'test_files': [],
                'estimated_coverage': 0
            },
            'risk_assessment': {
                'score': 0,
                'level': 'unknown',
                'factors': {}
            },
            'recommendations': [],
            'summary': {
                'entity_found': False,
                'total_dependents': 0,
                'layers_affected': []
            }
        }

    # Calculate blast radius
    blast_radius = calculate_blast_radius(query, entity_name, entity_type, entity_info, depth)

    # Find test coverage
    test_coverage = find_test_coverage(query, entity_name, entity_type, entity_info)

    # Calculate risk score
    risk_assessment = calculate_risk_score(
        blast_radius,
        test_coverage,
        entity_info
    )

    # Generate recommendations
    recommendations = generate_recommendations(
        entity_name,
        entity_type,
        blast_radius,
        test_coverage,
        risk_assessment
    )

    # Calculate summary statistics
    all_dependents = (blast_radius['direct_dependents'] +
                     blast_radius['indirect_dependents'])

    layers_affected = set()
    for dep in all_dependents:
        layers_affected.add(dep.get('layer', 'Unknown'))

    summary = {
        'entity_found': True,
        'total_dependents': len(all_dependents),
        'direct_count': len(blast_radius['direct_dependents']),
        'indirect_count': len(blast_radius['indirect_dependents']),
        'layers_affected': sorted(layers_affected),
        'test_files': len(test_coverage['test_files']),
        'risk_level': risk_assessment['level']
    }

    return {
        'entity_name': entity_name,
        'entity_type': entity_type,
        'entity_info': entity_info,
        'blast_radius': blast_radius,
        'test_coverage': test_coverage,
        'risk_assessment': risk_assessment,
        'recommendations': recommendations,
        'summary': summary
    }


def _find_entity(query: Any, entity_name: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Find entity and determine its type.

    Args:
        query: DocumentationQuery instance
        entity_name: Name to search for

    Returns:
        Tuple of (entity_type, entity_info) or (None, None) if not found
    """
    # Try to find as function first
    functions = [f for f in query.data.get('functions', [])
                if f.get('name') == entity_name]

    if functions:
        func = functions[0]
        return ('function', {
            'name': func.get('name'),
            'file': func.get('file'),
            'line': func.get('line'),
            'complexity': func.get('complexity', 0),
            'docstring': func.get('docstring', '')
        })

    # Try to find as class
    classes = [c for c in query.data.get('classes', [])
              if c.get('name') == entity_name]

    if classes:
        cls = classes[0]
        return ('class', {
            'name': cls.get('name'),
            'file': cls.get('file'),
            'line': cls.get('line'),
            'methods': cls.get('methods', []),
            'docstring': cls.get('docstring', '')
        })

    return (None, None)


def calculate_blast_radius(
    query: Any,
    entity_name: str,
    entity_type: str,
    entity_info: Dict[str, Any],
    depth: int
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate the blast radius of changing an entity.

    Finds all direct dependents and indirect dependents up to specified depth.

    Args:
        query: DocumentationQuery instance
        entity_name: Name of the entity
        entity_type: 'function' or 'class'
        entity_info: Entity information dictionary
        depth: Maximum depth for traversal

    Returns:
        Dictionary with:
        - direct_dependents: List of functions/classes that directly depend on entity
        - indirect_dependents: List of 2nd+ degree dependents
    """
    direct_dependents = []
    indirect_dependents = []

    # Get direct dependents based on entity type
    if entity_type == 'function':
        # For functions, find callers
        all_functions = query.data.get('functions', [])
        target_funcs = [f for f in all_functions if f.get('name') == entity_name]

        if target_funcs:
            target_func = target_funcs[0]
            callers = target_func.get('callers', [])

            for caller_ref in callers:
                caller_name = caller_ref.get('caller', '')
                # Find the caller function
                caller_funcs = [f for f in all_functions if f.get('name') == caller_name]

                if caller_funcs:
                    caller_func = caller_funcs[0]
                    direct_dependents.append({
                        'name': caller_name,
                        'type': 'function',
                        'file': caller_func.get('file', 'unknown'),
                        'line': caller_ref.get('line', 0),
                        'layer': _determine_layer(caller_func.get('file', ''))
                    })

    elif entity_type == 'class':
        # For classes, find instantiation points
        all_classes = query.data.get('classes', [])
        target_classes = [c for c in all_classes if c.get('name') == entity_name]

        if target_classes:
            target_class = target_classes[0]
            instantiated_by = target_class.get('instantiated_by', [])

            for inst_ref in instantiated_by:
                inst_name = inst_ref.get('caller', '')
                # Find the instantiating function
                all_functions = query.data.get('functions', [])
                inst_funcs = [f for f in all_functions if f.get('name') == inst_name]

                if inst_funcs:
                    inst_func = inst_funcs[0]
                    direct_dependents.append({
                        'name': inst_name,
                        'type': 'function',
                        'file': inst_func.get('file', 'unknown'),
                        'line': inst_ref.get('line', 0),
                        'layer': _determine_layer(inst_func.get('file', ''))
                    })

    # Calculate indirect dependents (2nd degree and beyond)
    if depth > 1:
        visited = {entity_name}
        for dep in direct_dependents:
            visited.add(dep['name'])

        current_level = [dep['name'] for dep in direct_dependents]

        for level in range(2, depth + 1):
            next_level = []

            for dep_name in current_level:
                # Find dependents of this dependent
                dep_funcs = [f for f in query.data.get('functions', [])
                           if f.get('name') == dep_name]

                if dep_funcs:
                    dep_func = dep_funcs[0]
                    dep_callers = dep_func.get('callers', [])

                    for caller_ref in dep_callers:
                        caller_name = caller_ref.get('caller', '')

                        if caller_name in visited:
                            continue

                        visited.add(caller_name)
                        next_level.append(caller_name)

                        # Find caller info
                        all_functions = query.data.get('functions', [])
                        caller_funcs = [f for f in all_functions
                                      if f.get('name') == caller_name]

                        if caller_funcs:
                            caller_func = caller_funcs[0]
                            indirect_dependents.append({
                                'name': caller_name,
                                'type': 'function',
                                'file': caller_func.get('file', 'unknown'),
                                'line': caller_ref.get('line', 0),
                                'layer': _determine_layer(caller_func.get('file', '')),
                                'depth': level
                            })

            current_level = next_level

            if not current_level:
                break  # No more dependents

    return {
        'direct_dependents': direct_dependents,
        'indirect_dependents': indirect_dependents
    }


def _determine_layer(file_path: str) -> str:
    """
    Determine architectural layer from file path.

    Args:
        file_path: Path to file

    Returns:
        Layer name (Presentation, Business Logic, Data, Utility, Core, External)
    """
    layer_patterns = {
        'Presentation': ['routes', 'cli', 'api', 'handlers', 'controllers', 'views'],
        'Business Logic': ['services', 'business', 'workflows', 'processors', 'logic'],
        'Data': ['models', 'database', 'repositories', 'dao', 'persistence', 'storage'],
        'Utility': ['utils', 'helpers', 'common', 'lib', 'tools']
    }

    file_path_lower = file_path.lower()

    if file_path in ('external', 'unknown'):
        return 'External'

    for layer_name, patterns in layer_patterns.items():
        if any(f'/{pattern}/' in file_path_lower or
              file_path_lower.startswith(f'{pattern}/')
              for pattern in patterns):
            return layer_name

    return 'Core'


def find_test_coverage(
    query: Any,
    entity_name: str,
    entity_type: str,
    entity_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Find test files that cover the entity.

    Uses heuristics to identify tests that exercise the code.

    Args:
        query: DocumentationQuery instance
        entity_name: Name of the entity
        entity_type: 'function' or 'class'
        entity_info: Entity information dictionary

    Returns:
        Dictionary with:
        - test_files: List of test files that reference the entity
        - estimated_coverage: Percentage estimate (0-100)
    """
    test_files = []
    all_functions = query.data.get('functions', [])

    # Find functions in test files that call the entity
    for func in all_functions:
        file_path = func.get('file', '')

        # Check if this is a test file
        if not _is_test_file(file_path):
            continue

        # Check if this test function calls the entity
        calls = func.get('calls', [])
        call_names = [c.get('name', '') for c in calls]

        if entity_name in call_names:
            test_files.append({
                'file': file_path,
                'test_function': func.get('name', ''),
                'line': func.get('line', 0)
            })

    # Estimate coverage (very rough heuristic)
    # If we have tests, assume some coverage
    if test_files:
        # Simple heuristic: each test file gives ~30% confidence
        estimated_coverage = min(len(test_files) * 30, 90)
    else:
        estimated_coverage = 0

    return {
        'test_files': test_files,
        'estimated_coverage': estimated_coverage
    }


def _is_test_file(file_path: str) -> bool:
    """Check if file path indicates a test file."""
    test_indicators = ['test_', '_test.', 'tests/', '/test/', 'spec.', '_spec.']
    file_path_lower = file_path.lower()
    return any(indicator in file_path_lower for indicator in test_indicators)


def calculate_risk_score(
    blast_radius: Dict[str, List[Dict[str, Any]]],
    test_coverage: Dict[str, Any],
    entity_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate risk score for changing the entity.

    Uses formula: Risk = (direct * 3) + (indirect * 1) + (layers * 5) - (coverage * 0.1)

    Args:
        blast_radius: Blast radius from calculate_blast_radius()
        test_coverage: Test coverage from find_test_coverage()
        entity_info: Entity information

    Returns:
        Dictionary with:
        - score: Numeric risk score
        - level: 'low', 'medium', or 'high'
        - factors: Breakdown of risk factors
    """
    direct_count = len(blast_radius['direct_dependents'])
    indirect_count = len(blast_radius['indirect_dependents'])
    coverage = test_coverage['estimated_coverage']

    # Count layers affected
    all_dependents = (blast_radius['direct_dependents'] +
                     blast_radius['indirect_dependents'])
    layers = set(dep.get('layer', 'Unknown') for dep in all_dependents)
    layer_count = len(layers)

    # Calculate risk score
    score = (direct_count * 3) + (indirect_count * 1) + (layer_count * 5) - (coverage * 0.1)

    # Determine risk level
    if score < 20:
        level = 'low'
    elif score < 50:
        level = 'medium'
    else:
        level = 'high'

    factors = {
        'direct_dependents': direct_count,
        'indirect_dependents': indirect_count,
        'layers_affected': layer_count,
        'test_coverage': coverage,
        'complexity': entity_info.get('complexity', 0)
    }

    return {
        'score': round(score, 1),
        'level': level,
        'factors': factors
    }


def generate_recommendations(
    entity_name: str,
    entity_type: str,
    blast_radius: Dict[str, List[Dict[str, Any]]],
    test_coverage: Dict[str, Any],
    risk_assessment: Dict[str, Any]
) -> List[str]:
    """
    Generate actionable refactoring recommendations.

    Args:
        entity_name: Name of the entity
        entity_type: 'function' or 'class'
        blast_radius: Blast radius data
        test_coverage: Test coverage data
        risk_assessment: Risk assessment data

    Returns:
        List of recommendation strings
    """
    recommendations = []
    risk_level = risk_assessment['level']
    factors = risk_assessment['factors']

    # Test coverage recommendations
    if factors['test_coverage'] < 30:
        recommendations.append(
            f"⚠️  Add comprehensive tests before refactoring - current coverage is low ({factors['test_coverage']}%)"
        )
    elif factors['test_coverage'] < 60:
        recommendations.append(
            f"📝 Consider adding more tests to increase confidence (current: {factors['test_coverage']}%)"
        )

    # Blast radius recommendations
    if factors['direct_dependents'] > 20:
        recommendations.append(
            f"🔄 High coupling detected ({factors['direct_dependents']} direct dependents) - "
            "consider introducing an abstraction layer"
        )
    elif factors['direct_dependents'] > 10:
        recommendations.append(
            "💡 Moderate coupling - ensure backward compatibility or update dependents in same PR"
        )

    # Layer recommendations
    if factors['layers_affected'] > 3:
        recommendations.append(
            f"🏗️  Cross-layer impact ({factors['layers_affected']} layers) - "
            "coordinate changes across architectural boundaries"
        )

    # Risk-level specific recommendations
    if risk_level == 'high':
        recommendations.append(
            "🚨 HIGH RISK CHANGE - Strongly recommend:"
            "\n  1. Create feature flag for gradual rollout"
            "\n  2. Add integration tests covering all affected paths"
            "\n  3. Review changes with team before merging"
            "\n  4. Plan rollback strategy"
        )
    elif risk_level == 'medium':
        recommendations.append(
            "⚡ MEDIUM RISK - Recommended actions:"
            "\n  1. Review all direct dependents for compatibility"
            "\n  2. Run full test suite before merging"
            "\n  3. Document breaking changes in PR description"
        )
    else:
        recommendations.append(
            "✅ LOW RISK - Safe to refactor with standard practices"
        )

    # Indirect dependency warning
    if factors['indirect_dependents'] > 10:
        recommendations.append(
            f"📊 {factors['indirect_dependents']} indirect dependents detected - "
            "verify changes don't create cascading failures"
        )

    return recommendations


def format_dependency_tree(impact_result: Dict[str, Any]) -> str:
    """
    Format dependency tree visualization.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with dependency tree
    """
    entity_name = impact_result['entity_name']
    blast_radius = impact_result['blast_radius']
    direct = blast_radius['direct_dependents']
    indirect = blast_radius['indirect_dependents']

    lines = [f"🎯 Blast Radius: {entity_name}"]
    lines.append("")

    # Direct dependents
    lines.append(f"📍 DIRECT DEPENDENTS ({len(direct)})")
    if direct:
        # Group by layer
        by_layer: Dict[str, List[Dict[str, Any]]] = {}
        for dep in direct:
            layer = dep.get('layer', 'Unknown')
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(dep)

        for layer in sorted(by_layer.keys()):
            deps = by_layer[layer]
            lines.append(f"  [{layer}]")
            for dep in deps[:5]:  # Show first 5
                lines.append(f"    • {dep['name']}() in {dep['file']}")
            if len(deps) > 5:
                lines.append(f"    ... and {len(deps) - 5} more")
    else:
        lines.append("  (No direct dependents found)")
    lines.append("")

    # Indirect dependents
    lines.append(f"🔗 INDIRECT DEPENDENTS ({len(indirect)})")
    if indirect:
        # Group by depth
        by_depth: Dict[int, List[Dict[str, Any]]] = {}
        for dep in indirect:
            depth = dep.get('depth', 2)
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append(dep)

        for depth in sorted(by_depth.keys()):
            deps = by_depth[depth]
            lines.append(f"  Level {depth} ({len(deps)} functions)")
            for dep in deps[:3]:  # Show first 3
                lines.append(f"    • {dep['name']}() [{dep['layer']}]")
            if len(deps) > 3:
                lines.append(f"    ... and {len(deps) - 3} more")
    else:
        lines.append("  (No indirect dependents found)")

    return "\n".join(lines)


def format_test_coverage(impact_result: Dict[str, Any]) -> str:
    """
    Format test coverage report.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with test coverage
    """
    test_coverage = impact_result['test_coverage']
    test_files = test_coverage['test_files']
    coverage = test_coverage['estimated_coverage']

    lines = [f"🧪 Test Coverage: {coverage}%"]
    lines.append("")

    if test_files:
        lines.append(f"Test Files ({len(test_files)}):")
        for test in test_files[:5]:  # Show first 5
            lines.append(f"  • {test['test_function']}() in {test['file']}")
        if len(test_files) > 5:
            lines.append(f"  ... and {len(test_files) - 5} more")
    else:
        lines.append("⚠️  No test coverage detected")
        lines.append("Recommendation: Add tests before refactoring")

    return "\n".join(lines)


def format_risk_assessment(impact_result: Dict[str, Any]) -> str:
    """
    Format risk assessment display.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with risk assessment
    """
    risk = impact_result['risk_assessment']
    score = risk['score']
    level = risk['level']
    factors = risk['factors']

    # Risk level icon
    level_icons = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴'
    }
    icon = level_icons.get(level, '⚪')

    lines = [f"{icon} Risk Assessment: {level.upper()} (score: {score})"]
    lines.append("")
    lines.append("Risk Factors:")
    lines.append(f"  • Direct dependents: {factors['direct_dependents']}")
    lines.append(f"  • Indirect dependents: {factors['indirect_dependents']}")
    lines.append(f"  • Layers affected: {factors['layers_affected']}")
    lines.append(f"  • Test coverage: {factors['test_coverage']}%")
    if factors.get('complexity', 0) > 0:
        lines.append(f"  • Complexity: {factors['complexity']}")

    return "\n".join(lines)


def format_recommendations(impact_result: Dict[str, Any]) -> str:
    """
    Format recommendations section.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with recommendations
    """
    recommendations = impact_result['recommendations']

    if not recommendations:
        return "💡 Recommendations: None"

    lines = ["💡 Recommendations:"]
    lines.append("")
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
        lines.append("")

    return "\n".join(lines)


def format_summary(impact_result: Dict[str, Any]) -> str:
    """
    Format summary statistics.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with summary
    """
    summary = impact_result['summary']
    entity_info = impact_result['entity_info']

    lines = ["📊 Summary:"]
    lines.append(f"  Entity: {entity_info['name']} ({impact_result['entity_type']})")
    lines.append(f"  File: {entity_info['file']}:{entity_info['line']}")
    lines.append(f"  Total dependents: {summary['total_dependents']}")
    lines.append(f"    - Direct: {summary['direct_count']}")
    lines.append(f"    - Indirect: {summary['indirect_count']}")
    lines.append(f"  Layers affected: {', '.join(summary['layers_affected'])}")
    lines.append(f"  Test files: {summary['test_files']}")
    lines.append(f"  Risk level: {summary['risk_level']}")

    return "\n".join(lines)


def format_text_output(impact_result: Dict[str, Any]) -> str:
    """
    Format complete text output for impact command.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        Formatted string with all sections
    """
    if not impact_result['entity_info']:
        return f"❌ Entity '{impact_result['entity_name']}' not found in documentation"

    sections = []

    # Dependency tree
    sections.append(format_dependency_tree(impact_result))
    sections.append("")

    # Test coverage
    sections.append(format_test_coverage(impact_result))
    sections.append("")

    # Risk assessment
    sections.append(format_risk_assessment(impact_result))
    sections.append("")

    # Recommendations
    sections.append(format_recommendations(impact_result))
    sections.append("")

    # Summary
    sections.append(format_summary(impact_result))

    return "\n".join(sections)


def format_json_output(impact_result: Dict[str, Any]) -> str:
    """
    Format impact result as JSON.

    Args:
        impact_result: Output from analyze_impact()

    Returns:
        JSON string
    """
    return json.dumps(impact_result, indent=2)
