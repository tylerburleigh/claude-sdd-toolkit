#!/usr/bin/env python3
"""Documentation query CLI with unified CLI integration."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.metrics import track_metrics
from claude_skills.doc_query.doc_query_lib import (
    DocumentationQuery,
    QueryResult,
    check_docs_exist,
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _dump_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _maybe_json(args: argparse.Namespace, payload: Any) -> bool:
    if getattr(args, 'json', False):
        _dump_json(payload)
        return True
    return False


def _ensure_query(args: argparse.Namespace, printer: PrettyPrinter) -> Optional[DocumentationQuery]:
    docs_path = getattr(args, 'docs_path', None)
    if docs_path and not check_docs_exist(docs_path):
        message = f"Documentation not found at {docs_path}. Run 'doc generate' first."
        if _maybe_json(args, {"status": "error", "message": message}):
            return None
        printer.error(message)
        return None

    query = DocumentationQuery(docs_path)
    if not query.load():
        message = f"Documentation not found at {query.docs_path}. Run 'doc generate' first."
        if _maybe_json(args, {"status": "error", "message": message}):
            return None
        printer.error(message)
        return None
    return query


def _results_to_json(results: List[QueryResult], include_meta: bool = False) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for result in results:
        if include_meta:
            payload.append({
                'entity_type': result.entity_type,
                'name': result.name,
                **result.data,
            })
        else:
            payload.append(result.data)
    return payload


def _context_to_json(context: Dict[str, List[QueryResult]]) -> Dict[str, List[Dict[str, Any]]]:
    return {
        key: [item.data for item in value]
        for key, value in context.items()
    }


def _print_results(args: argparse.Namespace, results: List[QueryResult]) -> None:
    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} result(s):\n")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {format_result(result, args.verbose)}")
        print()


def format_result(result: QueryResult, verbose: bool = False) -> str:
    lines: List[str] = []

    if result.entity_type == 'class':
        lines.append(f"Class: {result.name}")
        lines.append(f"  File: {result.data.get('file', 'unknown')}")
        if result.data.get('line'):
            lines.append(f"  Line: {result.data['line']}")
        if result.data.get('bases'):
            lines.append(f"  Inherits: {', '.join(result.data['bases'])}")
        if verbose and result.data.get('docstring'):
            lines.append(f"  Description: {result.data['docstring'][:200]}")
        elif result.data.get('docstring_excerpt'):
            lines.append(f"  Summary: {result.data['docstring_excerpt']}")
        if verbose and result.data.get('methods'):
            lines.append(f"  Methods: {len(result.data['methods'])}")

    elif result.entity_type == 'function':
        lines.append(f"Function: {result.name}")
        lines.append(f"  File: {result.data.get('file', 'unknown')}")
        if result.data.get('line'):
            lines.append(f"  Line: {result.data['line']}")
        complexity = result.data.get('complexity', 0)
        lines.append(f"  Complexity: {complexity}")
        if result.data.get('high_complexity'):
            lines.append("  🔴 Flagged as high complexity")
        if result.data.get('parameters'):
            params = result.data['parameters']
            if params and isinstance(params[0], dict):
                param_strs = [p.get('name', str(p)) for p in params]
                lines.append(f"  Parameters: {', '.join(param_strs)}")
            elif params and isinstance(params[0], str):
                lines.append(f"  Parameters: {', '.join(params)}")
            else:
                lines.append(f"  Parameters: {len(params)}")
        if verbose and result.data.get('docstring'):
            lines.append(f"  Description: {result.data['docstring'][:200]}")
        elif result.data.get('docstring_excerpt'):
            lines.append(f"  Summary: {result.data['docstring_excerpt']}")

    elif result.entity_type == 'module':
        lines.append(f"Module: {result.name}")
        if result.data.get('docstring_excerpt'):
            lines.append(f"  Docstring: {result.data['docstring_excerpt']}")
        stats = result.data.get('statistics', {})
        lines.append(
            "  Classes: {class_count} | Functions: {function_count} | Avg Complexity: {avg}".format(
                class_count=stats.get('class_count', result.data.get('class_count', 0)),
                function_count=stats.get('function_count', result.data.get('function_count', 0)),
                avg=stats.get('avg_complexity', 'n/a'),
            )
        )
        if stats.get('high_complexity_count'):
            lines.append(f"  High Complexity Functions: {stats['high_complexity_count']}")
        imports = result.data.get('imports', []) or result.data.get('dependencies', [])
        if imports:
            preview = ', '.join(str(i) for i in imports[:5])
            if len(imports) > 5:
                preview += f", +{len(imports) - 5} more"
            lines.append(f"  Imports: {preview}")

    elif result.entity_type == 'dependency':
        lines.append(f"Dependency: {result.name}")
        if 'depends_on' in result.data:
            lines.append(f"  Depends on: {result.data['depends_on']}")
        if 'depended_by' in result.data:
            lines.append(f"  Depended by: {result.data['depended_by']}")

    return '\n'.join(lines)


def print_context(context: Dict[str, List[QueryResult]], verbose: bool = False) -> None:
    total = sum(len(items) for items in context.values())
    print(f"\nFound {total} total entities:\n")

    if context['classes']:
        print(f"Classes ({len(context['classes'])}):")
        for cls in context['classes']:
            excerpt = cls.data.get('docstring_excerpt')
            summary = f" - {excerpt}" if excerpt else ''
            print(f"  - {cls.name} ({cls.data.get('file', 'unknown')}){summary}")
        print()

    if context['functions']:
        print(f"Functions ({len(context['functions'])}):")
        for func in context['functions']:
            complexity = func.data.get('complexity', 0)
            highlight = ' 🔴' if func.data.get('high_complexity') else ''
            excerpt = func.data.get('docstring_excerpt')
            if excerpt and verbose:
                print(f"  - {func.name}{highlight} (complexity: {complexity}, {func.data.get('file', 'unknown')})")
                print(f"      {excerpt}")
            else:
                summary = f" - {excerpt}" if excerpt else ''
                print(f"  - {func.name}{highlight} (complexity: {complexity}, {func.data.get('file', 'unknown')}){summary}")
        print()

    if context['modules']:
        print(f"Modules ({len(context['modules'])}):")
        for mod in context['modules']:
            stats = mod.data.get('statistics', {})
            classes = stats.get('class_count', mod.data.get('class_count', 0))
            functions = stats.get('function_count', mod.data.get('function_count', 0))
            avg_complexity = stats.get('avg_complexity', 'n/a')
            high_count = stats.get('high_complexity_count', 0)
            doc_excerpt = mod.data.get('docstring_excerpt')
            print(f"  - {mod.name}")
            print(f"    Classes: {classes}, Functions: {functions}, Avg Complexity: {avg_complexity}")
            if high_count:
                print(f"    High-complexity functions: {high_count}")
            if doc_excerpt:
                print(f"    Docstring: {doc_excerpt}")
            imports = mod.data.get('imports', [])
            if imports:
                preview = ', '.join(imports[:5])
                if len(imports) > 5:
                    preview += f", +{len(imports) - 5} more"
                print(f"    Imports: {preview}")
        print()

    if context['dependencies']:
        print(f"Dependencies ({len(context['dependencies'])}):")
        for dep in context['dependencies']:
            if 'depends_on' in dep.data:
                print(f"  - {dep.name} depends on {dep.data['depends_on']}")
            elif 'depended_by' in dep.data:
                print(f"  - {dep.name} <- depended by {dep.data['depended_by']}")
            else:
                print(f"  - {dep.name}")
        print()


def print_module_summary(summary: Dict[str, Any], verbose: bool = False) -> None:
    print(f"Module: {summary.get('file') or summary.get('name')}")
    if summary.get('docstring_excerpt'):
        print(f"  Docstring: {summary['docstring_excerpt']}")
    stats = summary.get('statistics', {})
    print(
        "  Classes: {classes} | Functions: {functions} | Avg Complexity: {avg} | Max Complexity: {maxc}".format(
            classes=stats.get('class_count', summary.get('class_count', 0)),
            functions=stats.get('function_count', summary.get('function_count', 0)),
            avg=stats.get('avg_complexity', 'n/a'),
            maxc=stats.get('max_complexity', 'n/a'),
        )
    )
    if stats.get('high_complexity_count'):
        print(f"  High Complexity Functions: {stats['high_complexity_count']}")

    if summary.get('imports'):
        imports_preview = ', '.join(str(i) for i in summary['imports'][:8])
        if len(summary['imports']) > 8:
            imports_preview += f", +{len(summary['imports']) - 8} more"
        print(f"  Imports: {imports_preview}")

    if summary.get('dependencies'):
        deps_preview = ', '.join(summary['dependencies'][:8])
        if len(summary['dependencies']) > 8:
            deps_preview += f", +{len(summary['dependencies']) - 8} more"
        print(f"  Outgoing Dependencies: {deps_preview}")

    if summary.get('reverse_dependencies'):
        rev_preview = ', '.join(summary['reverse_dependencies'][:8])
        if len(summary['reverse_dependencies']) > 8:
            rev_preview += f", +{len(summary['reverse_dependencies']) - 8} more"
        print(f"  Incoming Dependencies: {rev_preview}")

    if summary.get('classes'):
        print(f"\n  Classes ({len(summary['classes'])}):")
        for cls in summary['classes']:
            line = f"    - {cls.get('name', 'unknown')}"
            if cls.get('docstring_excerpt') and verbose:
                line += f" — {cls['docstring_excerpt']}"
            print(line)

    if summary.get('functions'):
        print(f"\n  Key Functions ({len(summary['functions'])} listed):")
        for func in summary['functions']:
            complexity = func.get('complexity', 'n/a')
            highlight = ' 🔴' if func.get('complexity', 0) >= 5 else ''
            line = f"    - {func.get('name', 'unknown')} (complexity: {complexity}){highlight}"
            if func.get('docstring_excerpt') and verbose:
                line += f" — {func['docstring_excerpt']}"
            print(line)

    print()


# ---------------------------------------------------------------------------
# Command handlers (printer aware)
# ---------------------------------------------------------------------------


def cmd_find_class(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.find_class(args.name, pattern=args.pattern)
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


def cmd_find_function(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.find_function(args.name, pattern=args.pattern)
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


def cmd_find_module(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.find_module(args.name, pattern=args.pattern)
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


def cmd_complexity(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.get_high_complexity(threshold=args.threshold, module=args.module)
    if _maybe_json(args, _results_to_json(results, include_meta=True)):
        return 0
    _print_results(args, results)
    return 0


def cmd_dependencies(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.get_dependencies(args.module, reverse=args.reverse)
    if _maybe_json(args, _results_to_json(results, include_meta=True)):
        return 0
    _print_results(args, results)
    return 0


def cmd_search(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.search_entities(args.query)
    if _maybe_json(args, _results_to_json(results, include_meta=True)):
        return 0
    _print_results(args, results)
    return 0


def cmd_context(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    context = query.get_context_for_area(
        args.area,
        limit=args.limit,
        include_docstrings=args.include_docstrings,
        include_stats=args.include_stats,
    )
    if _maybe_json(args, _context_to_json(context)):
        return 0
    print_context(context, verbose=args.verbose)
    return 0


def cmd_describe_module(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    summary = query.describe_module(
        args.module,
        top_functions=args.top_functions,
        include_docstrings=args.include_docstrings,
        include_dependencies=not args.skip_dependencies,
    )
    if _maybe_json(args, summary):
        return 0
    print_module_summary(summary, verbose=args.verbose)
    return 0


def cmd_stats(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    stats = query.get_stats()
    if _maybe_json(args, stats):
        return 0
    metadata = stats.get('metadata', {})
    statistics = stats.get('statistics', {})
    print("\nDocumentation Statistics:")
    print(f"  Project: {metadata.get('project_name', 'unknown')} (version {metadata.get('version', 'unknown')})")
    print(f"  Generated At: {stats.get('generated_at', 'unknown')}")
    languages = metadata.get('languages', [])
    if languages:
        print(f"  Languages: {', '.join(languages)}")
    print(f"  Total Files: {statistics.get('total_files', 'unknown')}")
    print(f"  Total Modules: {statistics.get('total_modules', 'unknown')}")
    print(f"  Total Classes: {statistics.get('total_classes', 'unknown')}")
    print(f"  Total Functions: {statistics.get('total_functions', 'unknown')}")
    print(f"  Total Lines: {statistics.get('total_lines', 'unknown')}")
    print(f"  Average Complexity: {statistics.get('avg_complexity', 'unknown')}")
    print(f"  Max Complexity: {statistics.get('max_complexity', 'unknown')}")
    print(f"  High Complexity Functions (≥5): {statistics.get('high_complexity_count', 'unknown')}")
    print()
    return 0


def cmd_list_classes(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.list_classes(module=args.module)
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


def cmd_list_functions(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.list_functions(module=args.module)
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


def cmd_list_modules(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.list_modules()
    if _maybe_json(args, _results_to_json(results, include_meta=False)):
        return 0
    _print_results(args, results)
    return 0


# ---------------------------------------------------------------------------
# Unified CLI registration
# ---------------------------------------------------------------------------


def register_doc_query(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[attr-defined]
    """Register documentation query commands for the unified doc CLI."""
    find_class = subparsers.add_parser('find-class', parents=[parent_parser], help='Find class by name or pattern')
    find_class.add_argument('name', help='Class name or regex pattern')
    find_class.add_argument('--pattern', action='store_true', help='Treat name as regex pattern')
    find_class.set_defaults(func=cmd_find_class)

    find_function = subparsers.add_parser('find-function', parents=[parent_parser], help='Find function by name or pattern')
    find_function.add_argument('name', help='Function name or regex pattern')
    find_function.add_argument('--pattern', action='store_true', help='Treat name as regex pattern')
    find_function.set_defaults(func=cmd_find_function)

    find_module = subparsers.add_parser('find-module', parents=[parent_parser], help='Find module by name or pattern')
    find_module.add_argument('name', help='Module name or regex pattern')
    find_module.add_argument('--pattern', action='store_true', help='Treat name as regex pattern')
    find_module.set_defaults(func=cmd_find_module)

    complexity = subparsers.add_parser('complexity', parents=[parent_parser], help='Show high-complexity functions')
    complexity.add_argument('--threshold', type=int, default=5, help='Minimum complexity (default: 5)')
    complexity.add_argument('--module', help='Filter by module')
    complexity.set_defaults(func=cmd_complexity)

    deps = subparsers.add_parser('dependencies', parents=[parent_parser], help='Show module dependencies')
    deps.add_argument('module', help='Module path')
    deps.add_argument('--reverse', action='store_true', help='Show reverse dependencies (who depends on this)')
    deps.set_defaults(func=cmd_dependencies)

    search = subparsers.add_parser('search', parents=[parent_parser], help='Search all documented entities')
    search.add_argument('query', help='Search query (regex)')
    search.set_defaults(func=cmd_search)

    context = subparsers.add_parser('context', parents=[parent_parser], help='Gather context for feature area')
    context.add_argument('area', help='Feature area pattern')
    context.add_argument('--limit', type=int, default=None, help='Limit number of results per entity type')
    context.add_argument('--include-docstrings', action='store_true', help='Include docstring excerpts in results')
    context.add_argument('--include-stats', action='store_true', help='Include statistics in module summaries')
    context.set_defaults(func=cmd_context)

    describe = subparsers.add_parser('describe-module', parents=[parent_parser], help='Describe a module with summaries and stats')
    describe.add_argument('module', help='Module path or name')
    describe.add_argument('--top-functions', type=int, default=None, help='Limit functions shown to top N by complexity')
    describe.add_argument('--include-docstrings', action='store_true', help='Include docstring excerpts in summaries')
    describe.add_argument('--skip-dependencies', action='store_true', help='Skip dependency details in summary')
    describe.set_defaults(func=cmd_describe_module)

    stats_cmd = subparsers.add_parser('stats', parents=[parent_parser], help='Show documentation statistics')
    stats_cmd.set_defaults(func=cmd_stats)

    list_classes = subparsers.add_parser('list-classes', parents=[parent_parser], help='List all classes')
    list_classes.add_argument('--module', help='Filter by module')
    list_classes.set_defaults(func=cmd_list_classes)

    list_functions = subparsers.add_parser('list-functions', parents=[parent_parser], help='List all functions')
    list_functions.add_argument('--module', help='Filter by module')
    list_functions.set_defaults(func=cmd_list_functions)

    list_modules = subparsers.add_parser('list-modules', parents=[parent_parser], help='List all modules')
    list_modules.set_defaults(func=cmd_list_modules)
