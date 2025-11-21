"""
Analysis insights data structures for LLM documentation generation.

This module defines data structures for storing extracted codebase analysis
insights that enhance AI-generated documentation. These insights are extracted
from documentation.json and formatted for inclusion in AI consultation prompts.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


@dataclass
class AnalysisInsights:
    """
    Container for codebase analysis insights extracted from documentation.json.

    These insights provide high-level codebase metrics and patterns that help
    AI models generate more contextual and accurate documentation.

    Attributes:
        high_complexity_functions: List of function names with high complexity
        most_called_functions: List of dicts with function call statistics
            Format: [{"name": str, "file": str, "call_count": int}, ...]
        most_instantiated_classes: List of dicts with class instantiation statistics
            Format: [{"name": str, "file": str, "instantiation_count": int}, ...]
        entry_points: List of dicts identifying codebase entry points (NEW from consensus)
            Format: [{"name": str, "file": str, "type": str}, ...]
        integration_points: List of dicts with external integration information
            Format: [{"name": str, "type": str, "details": str}, ...]
        cross_module_dependencies: List of dicts mapping module dependencies (NEW from consensus)
            Format: [{"from_module": str, "to_module": str, "dependency_count": int}, ...]
        fan_out_analysis: List of dicts showing function fan-out metrics (NEW from consensus)
            Format: [{"name": str, "file": str, "calls_count": int, "unique_callees": int}, ...]
        language_breakdown: Dict mapping language to statistics
            Format: {"python": {"file_count": int, "line_count": int}, ...}
        module_statistics: Dict with module-level statistics
            Format: {"total_modules": int, "total_functions": int, "total_classes": int, ...}
    """

    high_complexity_functions: List[str] = field(default_factory=list)
    most_called_functions: List[Dict[str, Any]] = field(default_factory=list)
    most_instantiated_classes: List[Dict[str, Any]] = field(default_factory=list)
    entry_points: List[Dict[str, Any]] = field(default_factory=list)
    integration_points: List[Dict[str, Any]] = field(default_factory=list)
    cross_module_dependencies: List[Dict[str, Any]] = field(default_factory=list)
    fan_out_analysis: List[Dict[str, Any]] = field(default_factory=list)
    language_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    module_statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert insights to dictionary for JSON serialization.

        Returns:
            Dictionary representation of all analysis insights
        """
        return {
            'high_complexity_functions': self.high_complexity_functions,
            'most_called_functions': self.most_called_functions,
            'most_instantiated_classes': self.most_instantiated_classes,
            'entry_points': self.entry_points,
            'integration_points': self.integration_points,
            'cross_module_dependencies': self.cross_module_dependencies,
            'fan_out_analysis': self.fan_out_analysis,
            'language_breakdown': self.language_breakdown,
            'module_statistics': self.module_statistics
        }


# Global cache for loaded documentation JSON
_documentation_cache: Optional[Dict[str, Any]] = None
_cache_path: Optional[Path] = None


def extract_insights_from_analysis(
    docs_path: Path,
    codebase_size: Optional[int] = None,
    use_cache: bool = True
) -> AnalysisInsights:
    """
    Extract analysis insights from documentation.json.

    Implements adaptive scaling based on codebase size:
    - Small (<100 files): Top 10 items per metric
    - Medium (100-500 files): Top 20 items per metric
    - Large (>500 files): Top 30 items per metric

    Args:
        docs_path: Path to documentation.json file
        codebase_size: Number of files in codebase (auto-detected if None)
        use_cache: Whether to use global cache for loaded JSON

    Returns:
        AnalysisInsights object with extracted metrics

    Raises:
        FileNotFoundError: If documentation.json doesn't exist
        json.JSONDecodeError: If documentation.json is invalid
    """
    global _documentation_cache, _cache_path

    # Load documentation.json with caching
    if use_cache and _cache_path == docs_path and _documentation_cache is not None:
        data = _documentation_cache
    else:
        if not docs_path.exists():
            raise FileNotFoundError(f"Documentation file not found: {docs_path}")

        with open(docs_path, 'r') as f:
            data = json.load(f)

        if use_cache:
            _documentation_cache = data
            _cache_path = docs_path

    # Auto-detect codebase size if not provided
    if codebase_size is None:
        # Count unique files mentioned in functions and classes
        files_set = set()
        for func in data.get('functions', []):
            if 'file' in func and func['file']:
                files_set.add(func['file'])
        for cls in data.get('classes', []):
            if 'file' in cls and cls['file']:
                files_set.add(cls['file'])
        codebase_size = len(files_set)

    # Determine scaling factor based on codebase size
    if codebase_size < 100:
        top_n = 10
    elif codebase_size <= 500:
        top_n = 20
    else:
        top_n = 30

    # Extract Priority 1 metrics
    most_called = _extract_most_called_functions(data, top_n)
    high_complexity = _extract_high_complexity_functions(data, top_n)
    entry_points = _extract_entry_points(data, top_n)
    cross_module_deps = _extract_cross_module_dependencies(data, top_n)

    # Extract Priority 2 metrics
    most_instantiated = _extract_most_instantiated_classes(data, top_n)
    fan_out = _extract_fan_out_analysis(data, top_n)

    # Extract integration points (external dependencies)
    integration_points = _extract_integration_points(data)

    # Calculate language breakdown and module statistics
    language_breakdown = _calculate_language_breakdown(data)
    module_stats = _calculate_module_statistics(data)

    return AnalysisInsights(
        high_complexity_functions=high_complexity,
        most_called_functions=most_called,
        most_instantiated_classes=most_instantiated,
        entry_points=entry_points,
        integration_points=integration_points,
        cross_module_dependencies=cross_module_deps,
        fan_out_analysis=fan_out,
        language_breakdown=language_breakdown,
        module_statistics=module_stats
    )


def _extract_most_called_functions(data: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    """Extract functions with highest call counts."""
    functions = data.get('functions', [])

    # Filter functions with call_count data and sort
    called_functions = [
        {
            'name': func['name'],
            'file': func.get('file', ''),
            'call_count': func.get('call_count', 0)
        }
        for func in functions
        if func.get('call_count') is not None and func.get('call_count', 0) > 0
    ]

    # Sort by call_count descending and take top N
    called_functions.sort(key=lambda x: x['call_count'], reverse=True)
    return called_functions[:top_n]


def _extract_high_complexity_functions(data: Dict[str, Any], top_n: int) -> List[str]:
    """Extract function names with high complexity (threshold: 10+)."""
    functions = data.get('functions', [])

    # Filter functions with complexity >= 10, sort by complexity
    complex_functions = [
        (func['name'], func.get('complexity', 0))
        for func in functions
        if func.get('complexity', 0) >= 10
    ]

    # Sort by complexity descending and take top N names
    complex_functions.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in complex_functions[:top_n]]


def _extract_entry_points(data: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    """
    Extract entry points (functions with 0-2 callers).

    Entry points are functions that are rarely called by other code,
    suggesting they may be CLI commands, API endpoints, or main functions.
    """
    functions = data.get('functions', [])

    entry_points = []
    for func in functions:
        callers = func.get('callers', [])
        caller_count = len(callers) if callers else 0

        # Entry points: 0-2 callers
        if caller_count <= 2:
            # Determine type based on name patterns
            name = func['name']
            if name == 'main' or name.startswith('main_'):
                entry_type = 'main'
            elif name.startswith('cli_') or name.endswith('_cli'):
                entry_type = 'cli'
            elif name.startswith('handle_') or name.startswith('on_'):
                entry_type = 'handler'
            else:
                entry_type = 'entry_point'

            entry_points.append({
                'name': name,
                'file': func.get('file', ''),
                'type': entry_type,
                'caller_count': caller_count
            })

    # Sort by caller_count ascending (true entry points have 0 callers)
    entry_points.sort(key=lambda x: x['caller_count'])
    return entry_points[:top_n]


def _extract_cross_module_dependencies(data: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    """
    Build cross-module dependency map.

    Analyzes function calls to identify which modules depend on which other modules.
    """
    dependencies = data.get('dependencies', {})

    # Build module -> module dependency counts
    module_deps: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for module, imported_modules in dependencies.items():
        if not isinstance(imported_modules, list):
            continue

        for imported in imported_modules:
            # Normalize module names (remove .py extension if present)
            from_mod = module.replace('.py', '').replace('/', '.')
            to_mod = imported.replace('.py', '').replace('/', '.')

            # Skip self-dependencies
            if from_mod != to_mod:
                module_deps[from_mod][to_mod] += 1

    # Flatten to list of dicts
    dep_list = []
    for from_mod, to_mods in module_deps.items():
        for to_mod, count in to_mods.items():
            dep_list.append({
                'from_module': from_mod,
                'to_module': to_mod,
                'dependency_count': count
            })

    # Sort by dependency_count descending
    dep_list.sort(key=lambda x: x['dependency_count'], reverse=True)
    return dep_list[:top_n]


def _extract_most_instantiated_classes(data: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    """Extract classes with highest instantiation counts."""
    classes = data.get('classes', [])

    # Filter classes with instantiation_count data
    instantiated_classes = [
        {
            'name': cls['name'],
            'file': cls.get('file', ''),
            'instantiation_count': cls.get('instantiation_count', 0)
        }
        for cls in classes
        if cls.get('instantiation_count') is not None and cls.get('instantiation_count', 0) > 0
    ]

    # Sort by instantiation_count descending
    instantiated_classes.sort(key=lambda x: x['instantiation_count'], reverse=True)
    return instantiated_classes[:top_n]


def _extract_fan_out_analysis(data: Dict[str, Any], top_n: int) -> List[Dict[str, Any]]:
    """
    Extract fan-out analysis (functions calling 8+ others).

    High fan-out suggests coordination/orchestration functions.
    """
    functions = data.get('functions', [])

    fan_out_functions = []
    for func in functions:
        calls = func.get('calls', [])
        if not calls:
            continue

        calls_count = len(calls)

        # Only include functions with fan-out >= 8
        if calls_count >= 8:
            # Count unique callees
            unique_callees = len(set(call['name'] for call in calls if isinstance(call, dict) and 'name' in call))

            fan_out_functions.append({
                'name': func['name'],
                'file': func.get('file', ''),
                'calls_count': calls_count,
                'unique_callees': unique_callees
            })

    # Sort by calls_count descending
    fan_out_functions.sort(key=lambda x: x['calls_count'], reverse=True)
    return fan_out_functions[:top_n]


def _extract_integration_points(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract external integration points.

    Identifies dependencies on external libraries/frameworks.
    """
    dependencies = data.get('dependencies', {})

    # Common external library patterns
    external_patterns = [
        'django', 'flask', 'fastapi', 'requests', 'sqlalchemy',
        'pandas', 'numpy', 'torch', 'tensorflow', 'aws', 'google',
        'azure', 'redis', 'celery', 'pytest', 'unittest'
    ]

    integration_points = []
    seen = set()

    for module, imports in dependencies.items():
        if not isinstance(imports, list):
            continue

        for imported in imports:
            # Check if it's an external library
            imported_lower = imported.lower()
            for pattern in external_patterns:
                if pattern in imported_lower and imported not in seen:
                    integration_points.append({
                        'name': imported,
                        'type': 'external_library',
                        'details': f'Imported by {module}'
                    })
                    seen.add(imported)
                    break

    return integration_points


def _calculate_language_breakdown(data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Calculate language breakdown statistics.

    Returns file counts and line counts per language (if available).
    """
    # Try to extract from metadata if available
    metadata = data.get('metadata', {})
    if 'language_breakdown' in metadata:
        return metadata['language_breakdown']

    # Fallback: infer from file extensions
    language_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'file_count': 0, 'line_count': 0})

    # Count files by extension
    files_seen = set()
    for func in data.get('functions', []):
        file_path = func.get('file', '')
        if file_path and file_path not in files_seen:
            files_seen.add(file_path)
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                language_stats['python']['file_count'] += 1
            elif ext in ['.js', '.jsx']:
                language_stats['javascript']['file_count'] += 1
            elif ext in ['.ts', '.tsx']:
                language_stats['typescript']['file_count'] += 1
            elif ext == '.go':
                language_stats['go']['file_count'] += 1

    for cls in data.get('classes', []):
        file_path = cls.get('file', '')
        if file_path and file_path not in files_seen:
            files_seen.add(file_path)
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                language_stats['python']['file_count'] += 1
            elif ext in ['.js', '.jsx']:
                language_stats['javascript']['file_count'] += 1
            elif ext in ['.ts', '.tsx']:
                language_stats['typescript']['file_count'] += 1
            elif ext == '.go':
                language_stats['go']['file_count'] += 1

    return dict(language_stats)


def _calculate_module_statistics(data: Dict[str, Any]) -> Dict[str, int]:
    """Calculate module-level statistics."""
    functions = data.get('functions', [])
    classes = data.get('classes', [])

    # Count unique modules
    modules = set()
    for func in functions:
        if 'file' in func and func['file']:
            modules.add(func['file'])
    for cls in classes:
        if 'file' in cls and cls['file']:
            modules.add(cls['file'])

    return {
        'total_modules': len(modules),
        'total_functions': len(functions),
        'total_classes': len(classes),
        'total_dependencies': len(data.get('dependencies', {}))
    }
