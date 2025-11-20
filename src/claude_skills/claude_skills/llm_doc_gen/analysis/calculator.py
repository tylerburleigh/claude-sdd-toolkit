"""
Metrics and complexity calculation module.
Handles code quality metrics, complexity analysis, and statistics.
Supports multi-language analysis.
"""

import ast
from typing import Dict, List, Any
from collections import defaultdict


def calculate_complexity(node: ast.FunctionDef) -> int:
    """
    Calculate cyclomatic complexity for a function.

    Args:
        node: AST node representing a function

    Returns:
        Cyclomatic complexity score
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def calculate_statistics(modules: List[Dict], functions: List[Dict]) -> Dict[str, Any]:
    """
    Calculate project-wide statistics with multi-language support.

    Args:
        modules: List of module information dictionaries
        functions: List of function information dictionaries

    Returns:
        Dictionary of calculated statistics including per-language breakdowns
    """
    total_complexity = sum(f.get('complexity', 1) for f in functions)
    avg_complexity = total_complexity / len(functions) if functions else 0

    # Calculate per-language statistics
    language_stats = calculate_language_statistics(modules, functions)

    statistics = {
        'total_files': len(modules),
        'total_lines': sum(m['lines'] for m in modules),
        'total_classes': sum(len(m['classes']) for m in modules),
        'total_functions': len(functions),
        'avg_complexity': round(avg_complexity, 2),
        'max_complexity': max((f.get('complexity', 1) for f in functions), default=0),
        'high_complexity_functions': [
            f"{f['name']} ({f.get('complexity', 1)})"
            for f in sorted(functions, key=lambda x: x.get('complexity', 1), reverse=True)[:5]
            if f.get('complexity', 1) > 10
        ],
        'by_language': language_stats
    }

    return statistics


def calculate_language_statistics(modules: List[Dict], functions: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate statistics broken down by programming language.

    Args:
        modules: List of module information dictionaries
        functions: List of function information dictionaries

    Returns:
        Dictionary mapping language to its statistics
    """
    lang_stats = defaultdict(lambda: {
        'files': 0,
        'lines': 0,
        'classes': 0,
        'functions': 0,
        'avg_complexity': 0,
    })

    # Aggregate module stats by language
    for module in modules:
        lang = module.get('language', 'unknown')
        lang_stats[lang]['files'] += 1
        lang_stats[lang]['lines'] += module.get('lines', 0)
        lang_stats[lang]['classes'] += len(module.get('classes', []))

    # Aggregate function stats by language
    lang_functions = defaultdict(list)
    for func in functions:
        lang = func.get('language', 'unknown')
        lang_stats[lang]['functions'] += 1
        lang_functions[lang].append(func)

    # Calculate average complexity per language
    for lang, funcs in lang_functions.items():
        if funcs:
            total_complexity = sum(f.get('complexity', 1) for f in funcs)
            lang_stats[lang]['avg_complexity'] = round(total_complexity / len(funcs), 2)

    return dict(lang_stats)


def analyze_code_quality(statistics: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyze code quality based on calculated statistics.

    Args:
        statistics: Dictionary of code statistics

    Returns:
        Dictionary with quality assessment
    """
    quality = {}

    # Complexity assessment
    avg_complexity = statistics.get('avg_complexity', 0)
    if avg_complexity < 5:
        quality['complexity'] = 'Good'
    elif avg_complexity < 10:
        quality['complexity'] = 'Moderate'
    else:
        quality['complexity'] = 'Needs Attention'

    # Function size assessment
    avg_lines_per_function = (
        statistics['total_lines'] / statistics['total_functions']
        if statistics.get('total_functions', 0) > 0
        else 0
    )

    if avg_lines_per_function < 20:
        quality['function_size'] = 'Good'
    elif avg_lines_per_function < 50:
        quality['function_size'] = 'Moderate'
    else:
        quality['function_size'] = 'Large'

    return quality
