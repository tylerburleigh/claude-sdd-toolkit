"""
Analysis insights data structures for LLM documentation generation.

This module defines data structures for storing extracted codebase analysis
insights that enhance AI-generated documentation. These insights are extracted
from codebase.json and formatted for inclusion in AI consultation prompts.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


@dataclass
class AnalysisInsights:
    """
    Container for codebase analysis insights extracted from codebase.json.

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


# Global cache for loaded documentation JSON with freshness tracking
@dataclass
class CacheEntry:
    """Cache entry with freshness tracking."""
    data: Dict[str, Any]
    path: Path
    load_time: float  # Unix timestamp
    file_mtime: float  # File modification time

    def is_fresh(self) -> bool:
        """Check if cached data is still fresh (file hasn't changed)."""
        try:
            current_mtime = self.path.stat().st_mtime
            return current_mtime == self.file_mtime
        except (OSError, FileNotFoundError):
            return False

    def age_hours(self) -> float:
        """Get age of cache entry in hours."""
        import time
        return (time.time() - self.load_time) / 3600


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    invalidations: int = 0

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# Global cache singleton
_documentation_cache: Optional[CacheEntry] = None
_cache_metrics = CacheMetrics()


def _load_and_cache(docs_path: Path) -> Dict[str, Any]:
    """
    Load codebase.json and create cache entry.

    Args:
        docs_path: Path to codebase.json

    Returns:
        Loaded JSON data
    """
    global _documentation_cache
    import time

    with open(docs_path, 'r') as f:
        data = json.load(f)

    # Get file modification time
    file_mtime = docs_path.stat().st_mtime

    # Create cache entry
    _documentation_cache = CacheEntry(
        data=data,
        path=docs_path,
        load_time=time.time(),
        file_mtime=file_mtime
    )

    return data


def get_cache_metrics() -> CacheMetrics:
    """
    Get current cache performance metrics.

    Returns:
        CacheMetrics object with hit/miss/invalidation counts
    """
    global _cache_metrics
    return _cache_metrics


def reset_cache_metrics() -> None:
    """Reset cache metrics to zero."""
    global _cache_metrics
    _cache_metrics = CacheMetrics()


def clear_cache() -> None:
    """Clear the documentation cache."""
    global _documentation_cache
    _documentation_cache = None


def extract_insights_from_analysis(
    docs_path: Path,
    codebase_size: Optional[int] = None,
    use_cache: bool = True,
    warn_stale: bool = True
) -> AnalysisInsights:
    """
    Extract analysis insights from codebase.json.

    Implements adaptive scaling based on codebase size:
    - Small (<100 files): Top 10 items per metric
    - Medium (100-500 files): Top 20 items per metric
    - Large (>500 files): Top 30 items per metric

    Args:
        docs_path: Path to codebase.json file
        codebase_size: Number of files in codebase (auto-detected if None)
        use_cache: Whether to use global cache for loaded JSON
        warn_stale: Whether to log warnings for stale data (>24 hours)

    Returns:
        AnalysisInsights object with extracted metrics

    Raises:
        FileNotFoundError: If codebase.json doesn't exist
        json.JSONDecodeError: If codebase.json is invalid
    """
    global _documentation_cache, _cache_metrics
    import time
    import logging

    # Check if file exists
    if not docs_path.exists():
        raise FileNotFoundError(f"Documentation file not found: {docs_path}")

    # Load codebase.json with freshness-aware caching
    if use_cache and _documentation_cache is not None:
        # Check if cache is for the same file and still fresh
        if _documentation_cache.path == docs_path and _documentation_cache.is_fresh():
            _cache_metrics.hits += 1
            data = _documentation_cache.data

            # Check for staleness warning (>24 hours old)
            if warn_stale and _documentation_cache.age_hours() > 24:
                logging.warning(
                    f"Documentation cache is {_documentation_cache.age_hours():.1f} hours old. "
                    "Consider regenerating documentation for up-to-date insights."
                )
        else:
            # Cache invalid (file changed or different path)
            if _documentation_cache is not None:
                _cache_metrics.invalidations += 1
            _cache_metrics.misses += 1
            data = _load_and_cache(docs_path)
    else:
        # Cache disabled or first load
        _cache_metrics.misses += 1
        if use_cache:
            data = _load_and_cache(docs_path)
        else:
            # Load without caching
            with open(docs_path, 'r') as f:
                data = json.load(f)

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


def format_insights_for_prompt(
    insights: AnalysisInsights,
    generator_type: str,
    docs_path: Optional[Path] = None
) -> str:
    """
    Format analysis insights for inclusion in AI consultation prompts.

    Uses table format for 30% token savings. Implements adaptive token budgets
    and priority-based truncation.

    Token budgets per generator type:
    - architecture: 450 tokens
    - component: 350 tokens
    - overview: 250 tokens

    Args:
        insights: AnalysisInsights object to format
        generator_type: One of 'architecture', 'component', 'overview'
        docs_path: Optional path to codebase.json for reference

    Returns:
        Formatted string ready for prompt inclusion
    """
    # Determine token budget based on generator type
    token_budgets = {
        'architecture': 450,
        'component': 350,
        'overview': 250
    }
    budget = token_budgets.get(generator_type, 350)

    # Build sections with priority ordering
    sections = []

    # Section 1: Module Statistics (always included, ~50 tokens)
    if insights.module_statistics:
        stats = insights.module_statistics
        sections.append(
            f"**Codebase Overview:**\n"
            f"Modules: {stats.get('total_modules', 0)} | "
            f"Functions: {stats.get('total_functions', 0)} | "
            f"Classes: {stats.get('total_classes', 0)} | "
            f"Dependencies: {stats.get('total_dependencies', 0)}"
        )

    # Section 2: Priority 1 - Most Called Functions (high priority)
    if insights.most_called_functions:
        table_rows = [f"{func['name']} ({func.get('file', 'N/A')}) | {func['call_count']} calls"
                      for func in insights.most_called_functions[:10]]
        sections.append(
            f"**Most Called Functions:**\n" + "\n".join(table_rows)
        )

    # Section 3: Priority 1 - Entry Points (high priority)
    if insights.entry_points:
        table_rows = [f"{ep['name']} ({ep.get('type', 'N/A')}) | {ep.get('file', 'N/A')}"
                      for ep in insights.entry_points[:8]]
        sections.append(
            f"**Entry Points:**\n" + "\n".join(table_rows)
        )

    # Section 4: Priority 1 - Cross-Module Dependencies (high priority for architecture)
    if insights.cross_module_dependencies and generator_type == 'architecture':
        table_rows = [f"{dep['from_module']} → {dep['to_module']} | {dep['dependency_count']} refs"
                      for dep in insights.cross_module_dependencies[:8]]
        sections.append(
            f"**Cross-Module Dependencies:**\n" + "\n".join(table_rows)
        )

    # Section 5: High Complexity Functions (medium priority)
    if insights.high_complexity_functions:
        func_list = ", ".join(insights.high_complexity_functions[:8])
        sections.append(
            f"**High Complexity Functions:**\n{func_list}"
        )

    # Section 6: Priority 2 - Most Instantiated Classes (lower priority)
    if insights.most_instantiated_classes and generator_type in ['architecture', 'component']:
        table_rows = [f"{cls['name']} ({cls.get('file', 'N/A')}) | {cls['instantiation_count']} instances"
                      for cls in insights.most_instantiated_classes[:6]]
        sections.append(
            f"**Most Used Classes:**\n" + "\n".join(table_rows)
        )

    # Section 7: Fan-Out Analysis (lower priority, mainly for architecture)
    if insights.fan_out_analysis and generator_type == 'architecture':
        table_rows = [f"{func['name']} | calls {func['calls_count']} functions"
                      for func in insights.fan_out_analysis[:5]]
        sections.append(
            f"**Orchestration Functions (High Fan-Out):**\n" + "\n".join(table_rows)
        )

    # Section 8: Integration Points (lower priority)
    if insights.integration_points:
        lib_list = ", ".join([ip['name'] for ip in insights.integration_points[:10]])
        sections.append(
            f"**External Integrations:**\n{lib_list}"
        )

    # Combine sections and check budget
    formatted_text = "\n\n".join(sections)

    # Rough token estimation (1 token ≈ 4 characters)
    estimated_tokens = len(formatted_text) // 4

    # If over budget, truncate lower priority sections
    if estimated_tokens > budget:
        formatted_text = _truncate_to_budget(sections, budget)

    # Add file path reference if provided
    if docs_path:
        file_ref = (
            f"\n\n**Full Analysis Available:**\n"
            f"Path: `{docs_path}`\n"
            f"Query examples: Most called functions, entry points, dependency graph"
        )
        formatted_text += file_ref

    return formatted_text


def _truncate_to_budget(sections: List[str], budget: int) -> str:
    """
    Truncate sections to fit within token budget using priority-based approach.

    Priority order (highest to lowest):
    1. Codebase Overview (always included)
    2. Most Called Functions
    3. Entry Points
    4. Cross-Module Dependencies
    5. High Complexity Functions
    6. Most Used Classes
    7. Orchestration Functions
    8. External Integrations

    Args:
        sections: List of formatted section strings (in priority order)
        budget: Maximum token budget

    Returns:
        Truncated formatted text within budget
    """
    result_sections = []
    current_tokens = 0

    for section in sections:
        section_tokens = len(section) // 4

        # Always include first section (Codebase Overview)
        if not result_sections:
            result_sections.append(section)
            current_tokens += section_tokens
            continue

        # Check if adding this section exceeds budget
        if current_tokens + section_tokens + 20 <= budget:  # 20 token buffer
            result_sections.append(section)
            current_tokens += section_tokens
        else:
            # Try to include a truncated version
            remaining_budget = budget - current_tokens - 20
            if remaining_budget > 50:  # Minimum 50 tokens to be useful
                # Truncate section to fit
                truncated = _truncate_section(section, remaining_budget * 4)
                result_sections.append(truncated)
            break

    return "\n\n".join(result_sections)


def _truncate_section(section: str, max_chars: int) -> str:
    """
    Truncate a section to fit within character limit.

    Args:
        section: Section text to truncate
        max_chars: Maximum characters allowed

    Returns:
        Truncated section with ellipsis if truncated
    """
    if len(section) <= max_chars:
        return section

    # Split by lines and truncate
    lines = section.split('\n')
    result_lines = [lines[0]]  # Always keep header
    current_len = len(lines[0])

    for line in lines[1:]:
        if current_len + len(line) + 10 <= max_chars:  # 10 char buffer
            result_lines.append(line)
            current_len += len(line) + 1
        else:
            result_lines.append("... (truncated)")
            break

    return '\n'.join(result_lines)
