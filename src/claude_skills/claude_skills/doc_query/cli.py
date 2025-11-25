#!/usr/bin/env python3
"""Documentation query CLI with unified CLI integration."""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.json_output import output_json
from claude_skills.common.metrics import track_metrics
from claude_skills.common.sdd_config import get_default_format
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    STATS_DOC_QUERY_ESSENTIAL,
    STATS_DOC_QUERY_STANDARD,
    LIST_CLASSES_ESSENTIAL,
    LIST_CLASSES_STANDARD,
    LIST_FUNCTIONS_ESSENTIAL,
    LIST_FUNCTIONS_STANDARD,
    LIST_MODULES_ESSENTIAL,
    LIST_MODULES_STANDARD,
    CALLERS_ESSENTIAL,
    CALLERS_STANDARD,
    CALLEES_ESSENTIAL,
    CALLEES_STANDARD,
    CALL_GRAPH_ESSENTIAL,
    CALL_GRAPH_STANDARD,
    TRACE_ENTRY_ESSENTIAL,
    TRACE_ENTRY_STANDARD,
    TRACE_DATA_ESSENTIAL,
    TRACE_DATA_STANDARD,
    IMPACT_ESSENTIAL,
    IMPACT_STANDARD,
    REFACTOR_CANDIDATES_ESSENTIAL,
    REFACTOR_CANDIDATES_STANDARD,
    FIND_CLASS_ESSENTIAL,
    FIND_CLASS_STANDARD,
    FIND_FUNCTION_ESSENTIAL,
    FIND_FUNCTION_STANDARD,
    FIND_MODULE_ESSENTIAL,
    FIND_MODULE_STANDARD,
    COMPLEXITY_ESSENTIAL,
    COMPLEXITY_STANDARD,
    DEPENDENCIES_ESSENTIAL,
    DEPENDENCIES_STANDARD,
    SEARCH_ESSENTIAL,
    SEARCH_STANDARD,
    CONTEXT_DOC_QUERY_ESSENTIAL,
    CONTEXT_DOC_QUERY_STANDARD,
    DESCRIBE_MODULE_ESSENTIAL,
    DESCRIBE_MODULE_STANDARD,
    SCOPE_ESSENTIAL,
    SCOPE_STANDARD,
)
from claude_skills.doc_query.doc_query_lib import (
    DocumentationQuery,
    QueryResult,
    check_docs_exist,
    check_documentation_staleness,
)
from claude_skills.doc_query.workflows.trace_entry import (
    trace_execution_flow,
    format_text_output,
    format_json_output
)
from claude_skills.doc_query.workflows.trace_data import (
    trace_data_lifecycle,
    format_text_output as format_trace_data_text,
    format_json_output as format_trace_data_json
)
from claude_skills.doc_query.workflows.impact_analysis import (
    analyze_impact,
    format_text_output as format_impact_text,
    format_json_output as format_impact_json
)
from claude_skills.doc_query.workflows.refactor_candidates import (
    find_refactor_candidates,
    format_text_output as format_refactor_text,
    format_json_output as format_refactor_json
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _maybe_json(args: argparse.Namespace, payload: Any) -> bool:
    if getattr(args, 'json', False):
        output_json(payload, compact=getattr(args, 'compact', False))
        return True
    return False


def _ensure_query(args: argparse.Namespace, printer: PrettyPrinter) -> Optional[DocumentationQuery]:
    import subprocess

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

    # Check staleness unless disabled
    no_staleness_check = getattr(args, 'no_staleness_check', False)
    skip_refresh = getattr(args, 'skip_refresh', False)
    # Keep refresh for backwards compatibility, but it's now redundant
    refresh = getattr(args, 'refresh', False)

    if not no_staleness_check:
        staleness_info = check_documentation_staleness(
            docs_path=str(query.docs_path),
            source_dir=getattr(args, 'source_dir', None)
        )

        # Auto-regenerate by default if docs are stale (unless --skip-refresh is set)
        if staleness_info.get('is_stale') and not skip_refresh:
            if not _maybe_json(args, {"status": "info", "message": "Regenerating stale documentation..."}):
                printer.info("\n🔄 Documentation is stale, regenerating...")

            # Determine source directory for regeneration
            from pathlib import Path
            source_dir = Path(getattr(args, 'source_dir', None) or query.docs_path.parent.parent / 'src')
            if not source_dir.exists():
                source_dir = query.docs_path.parent.parent

            # Run doc generate command
            try:
                # Build regeneration command
                regen_cmd = [
                    'sdd', 'doc', 'generate',
                    str(source_dir),
                    '--output-dir', str(query.docs_path.parent)
                ]

                result = subprocess.run(
                    regen_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    if not _maybe_json(args, {"status": "success", "message": "Documentation regenerated successfully"}):
                        printer.success("✅ Documentation regenerated successfully\n")
                    # Reload the query with fresh docs
                    query = DocumentationQuery(docs_path)
                    if not query.load():
                        message = "Failed to load regenerated documentation"
                        if _maybe_json(args, {"status": "error", "message": message}):
                            return None
                        printer.error(message)
                        return None
                else:
                    error_msg = f"Failed to regenerate documentation: {result.stderr}"
                    if not _maybe_json(args, {"status": "warning", "message": error_msg}):
                        printer.warning(f"⚠️  {error_msg}")
                        printer.warning("Continuing with stale documentation...\n")
            except Exception as e:
                error_msg = f"Error regenerating documentation: {e}"
                if not _maybe_json(args, {"status": "warning", "message": error_msg}):
                    printer.warning(f"⚠️  {error_msg}")
                    printer.warning("Continuing with stale documentation...\n")

        # Show warning if stale and user explicitly skipped refresh
        elif staleness_info.get('is_stale') and skip_refresh:
            warning_msg = staleness_info.get('message', 'Documentation may be stale')
            refresh_hint = "To auto-refresh: remove --skip-refresh flag or run 'sdd doc generate'"
            suppress_hint = "To suppress this warning: use --no-staleness-check"

            if not _maybe_json(args, {
                "status": "warning",
                "message": warning_msg,
                "hints": [refresh_hint, suppress_hint],
                "staleness_info": staleness_info
            }):
                printer.warning(f"\n⚠️  {warning_msg}")
                printer.info(f"    {refresh_hint}")
                printer.info(f"    {suppress_hint}\n")

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


def format_call_graph_as_dot(graph: Dict[str, Any]) -> str:
    """Format call graph as GraphViz DOT format."""
    lines = []
    lines.append(f"digraph call_graph {{")
    lines.append(f"  label=\"Call Graph for {graph['root']}\";")
    lines.append(f"  labelloc=\"t\";")
    lines.append("")

    # Add nodes with metadata
    for node_name, node_data in graph.get('nodes', {}).items():
        label = node_name
        if node_data.get('file'):
            label += f"\\n{node_data['file']}"
        if node_data.get('call_count') is not None:
            label += f"\\nCalls: {node_data['call_count']}"

        # Different shape for root node
        if node_name == graph['root']:
            lines.append(f'  "{node_name}" [label="{label}", shape=box, style=filled, fillcolor=lightblue];')
        else:
            lines.append(f'  "{node_name}" [label="{label}"];')

    lines.append("")

    # Add edges
    for edge in graph.get('edges', []):
        from_node = edge.get('from', '')
        to_node = edge.get('to', '')
        call_type = edge.get('call_type', 'unknown')
        lines.append(f'  "{from_node}" -> "{to_node}" [label="{call_type}"];')

    lines.append("}")
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

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, FIND_CLASS_ESSENTIAL, FIND_CLASS_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_find_function(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.find_function(args.name, pattern=args.pattern)

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, FIND_FUNCTION_ESSENTIAL, FIND_FUNCTION_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_find_module(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.find_module(args.name, pattern=args.pattern)

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, FIND_MODULE_ESSENTIAL, FIND_MODULE_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_complexity(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.get_high_complexity(threshold=args.threshold, module=args.module)

    # Apply module-pattern filter if provided
    if hasattr(args, 'module_pattern') and args.module_pattern:
        # Extract list of result dicts for filtering
        items = [result.data for result in results]
        # Filter using apply_pattern_filter - match on 'file' field
        filtered = DocumentationQuery.apply_pattern_filter(
            items,
            args.module_pattern,
            pattern=True,
            key_func=lambda x: x.get('file', '')
        )
        # Rebuild QueryResult list with preserved relevance_score (complexity)
        results = [
            QueryResult(
                entity_type='function',
                name=item.get('name', ''),
                data=item,
                relevance_score=item.get('complexity', 0)
            )
            for item in filtered
        ]

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, COMPLEXITY_ESSENTIAL, COMPLEXITY_STANDARD),
            relevance_score=result.relevance_score
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=True)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_dependencies(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.get_dependencies(args.module, reverse=args.reverse)

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, DEPENDENCIES_ESSENTIAL, DEPENDENCIES_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=True)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_search(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.search_entities(args.query)

    # Apply limit if provided
    if hasattr(args, 'limit') and args.limit is not None:
        results = results[:args.limit]

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, SEARCH_ESSENTIAL, SEARCH_STANDARD),
            relevance_score=result.relevance_score
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=True)):
        return 0
    _print_results(args, filtered_results)
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

    # Apply verbosity filtering to each result's data in each category
    filtered_context = {
        key: [
            QueryResult(
                entity_type=result.entity_type,
                name=result.name,
                data=prepare_output(result.data, args, CONTEXT_DOC_QUERY_ESSENTIAL, CONTEXT_DOC_QUERY_STANDARD)
            )
            for result in value
        ]
        for key, value in context.items()
    }

    if _maybe_json(args, _context_to_json(filtered_context)):
        return 0
    print_context(filtered_context, verbose=args.verbose)
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

    # Apply verbosity filtering
    filtered_summary = prepare_output(summary, args, DESCRIBE_MODULE_ESSENTIAL, DESCRIBE_MODULE_STANDARD)

    if _maybe_json(args, filtered_summary):
        return 0
    print_module_summary(filtered_summary, verbose=args.verbose)
    return 0


def cmd_stats(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    stats = query.get_stats()
    # Apply verbosity filtering
    filtered_stats = prepare_output(stats, args, STATS_DOC_QUERY_ESSENTIAL, STATS_DOC_QUERY_STANDARD)
    if _maybe_json(args, filtered_stats):
        return 0
    # Use filtered_stats for text output
    stats = filtered_stats
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

    # Apply pattern filter if provided
    if hasattr(args, 'pattern') and args.pattern:
        # Extract list of result dicts for filtering
        items = [result.data for result in results]
        # Filter using apply_pattern_filter - match on 'name' field
        filtered = DocumentationQuery.apply_pattern_filter(
            items,
            args.pattern,
            pattern=True,
            key_func=lambda x: x.get('name', '')
        )
        # Rebuild QueryResult list
        results = [
            QueryResult(
                entity_type='class',
                name=item.get('name', ''),
                data=item
            )
            for item in filtered
        ]

    # Apply limit if provided
    if hasattr(args, 'limit') and args.limit:
        results = results[:args.limit]

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, LIST_CLASSES_ESSENTIAL, LIST_CLASSES_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_list_functions(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.list_functions(module=args.module)

    # Apply pattern filter if provided
    if hasattr(args, 'pattern') and args.pattern:
        # Extract list of result dicts for filtering
        items = [result.data for result in results]
        # Filter using apply_pattern_filter - match on 'name' field
        filtered = DocumentationQuery.apply_pattern_filter(
            items,
            args.pattern,
            pattern=True,
            key_func=lambda x: x.get('name', '')
        )
        # Rebuild QueryResult list
        results = [
            QueryResult(
                entity_type='function',
                name=item.get('name', ''),
                data=item
            )
            for item in filtered
        ]

    # Apply limit if provided
    if hasattr(args, 'limit') and args.limit:
        results = results[:args.limit]

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, LIST_FUNCTIONS_ESSENTIAL, LIST_FUNCTIONS_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_list_modules(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    query = _ensure_query(args, printer)
    if not query:
        return 1
    results = query.list_modules()

    # Apply pattern filter if provided
    if hasattr(args, 'pattern') and args.pattern:
        # Extract list of result dicts for filtering
        items = [result.data for result in results]
        # Filter using apply_pattern_filter - match on both 'name' and 'file' fields
        filtered = DocumentationQuery.apply_pattern_filter(
            items,
            args.pattern,
            pattern=True,
            key_func=lambda x: f"{x.get('name', '')} {x.get('file', '')}"
        )
        # Rebuild QueryResult list
        results = [
            QueryResult(
                entity_type='module',
                name=item.get('file', item.get('name', '')),
                data=item
            )
            for item in filtered
        ]

    # Apply limit if provided
    if hasattr(args, 'limit') and args.limit:
        results = results[:args.limit]

    # Apply verbosity filtering to each result's data
    filtered_results = [
        QueryResult(
            entity_type=result.entity_type,
            name=result.name,
            data=prepare_output(result.data, args, LIST_MODULES_ESSENTIAL, LIST_MODULES_STANDARD)
        )
        for result in results
    ]

    if _maybe_json(args, _results_to_json(filtered_results, include_meta=False)):
        return 0
    _print_results(args, filtered_results)
    return 0


def cmd_callers(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Show functions that call the specified function."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    callers = query.get_callers(
        args.function_name,
        include_file=True,
        include_line=True
    )

    # Apply verbosity filtering to each caller
    filtered_callers = [
        prepare_output(caller, args, CALLERS_ESSENTIAL, CALLERS_STANDARD)
        for caller in callers
    ]

    if _maybe_json(args, filtered_callers):
        return 0

    # Text output
    if not filtered_callers:
        print(f"\nNo callers found for function '{args.function_name}'")
        print("(Note: Requires schema v2.0 documentation with cross-reference data)")
        return 0

    print(f"\nFound {len(filtered_callers)} caller(s) for '{args.function_name}':\n")
    for idx, caller in enumerate(filtered_callers, 1):
        name = caller.get('name', 'unknown')
        call_type = caller.get('call_type', 'unknown')
        file_path = caller.get('file', '')
        line = caller.get('line')

        location = f"{file_path}:{line}" if line else file_path
        print(f"{idx}. {name} ({call_type})")
        print(f"   Location: {location}")
        print()

    return 0


def cmd_callees(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Show functions called by the specified function."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    callees = query.get_callees(
        args.function_name,
        include_file=True,
        include_line=True
    )

    # Apply verbosity filtering to each callee
    filtered_callees = [
        prepare_output(callee, args, CALLEES_ESSENTIAL, CALLEES_STANDARD)
        for callee in callees
    ]

    if _maybe_json(args, filtered_callees):
        return 0

    # Text output
    if not filtered_callees:
        print(f"\nNo callees found for function '{args.function_name}'")
        print("(Note: Requires schema v2.0 documentation with cross-reference data)")
        return 0

    print(f"\nFound {len(filtered_callees)} function(s) called by '{args.function_name}':\n")
    for idx, callee in enumerate(filtered_callees, 1):
        name = callee.get('name', 'unknown')
        call_type = callee.get('call_type', 'unknown')
        file_path = callee.get('file', '')
        line = callee.get('line')

        location = f"{file_path}:{line}" if line else file_path
        print(f"{idx}. {name} ({call_type})")
        print(f"   Location: {location}")
        print()

    return 0


def cmd_call_graph(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Build and display call graph for a function."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    # Build the call graph
    graph = query.build_call_graph(
        args.function_name,
        direction=args.direction,
        max_depth=args.max_depth,
        include_metadata=True
    )

    # Check if function exists
    if not graph.get('nodes'):
        print(f"\nFunction '{args.function_name}' not found in documentation")
        return 1

    # Apply verbosity filtering to the graph
    filtered_graph = prepare_output(graph, args, CALL_GRAPH_ESSENTIAL, CALL_GRAPH_STANDARD)

    # Handle output format
    output_format = getattr(args, 'format', 'text')

    if output_format == 'json' or _maybe_json(args, filtered_graph):
        return 0

    if output_format == 'dot':
        print(format_call_graph_as_dot(filtered_graph))
        return 0

    # Text output (default)
    print(f"\nCall Graph for '{args.function_name}':")
    print(f"  Direction: {filtered_graph['direction']}")
    print(f"  Max Depth: {filtered_graph['max_depth']}")
    print(f"  Nodes: {len(filtered_graph.get('nodes', {}))}")
    print(f"  Edges: {len(filtered_graph.get('edges', []))}")

    if filtered_graph.get('truncated'):
        print(f"  ⚠️  Graph truncated at max depth")

    print("\nNodes:")
    for node_name, node_data in filtered_graph.get('nodes', {}).items():
        depth = node_data.get('depth', 0)
        indent = "  " * (depth + 1)
        file_info = f" ({node_data.get('file', 'unknown')})" if node_data.get('file') else ""
        marker = "→ " if node_name == filtered_graph['root'] else "  "
        print(f"{indent}{marker}{node_name}{file_info}")

    print("\nEdges:")
    for edge in filtered_graph.get('edges', []):
        from_node = edge.get('from', 'unknown')
        to_node = edge.get('to', 'unknown')
        call_type = edge.get('call_type', 'unknown')
        print(f"  {from_node} --[{call_type}]--> {to_node}")

    print()
    return 0


def cmd_trace_entry(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Trace execution flow from an entry function."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    # Get parameters
    function_name = args.function
    max_depth = getattr(args, 'max_depth', 5)
    output_format = getattr(args, 'format', 'text')

    # Trace execution flow
    try:
        trace_result = trace_execution_flow(query, function_name, max_depth)
    except Exception as e:
        error_msg = f"Error tracing function '{function_name}': {str(e)}"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Check if function was found
    if trace_result['summary']['total_functions'] == 0:
        error_msg = f"Function '{function_name}' not found in documentation"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Apply verbosity filtering
    filtered_result = prepare_output(trace_result, args, TRACE_ENTRY_ESSENTIAL, TRACE_ENTRY_STANDARD)

    # Handle output format
    if _maybe_json(args, filtered_result):
        return 0

    if output_format == 'json':
        output = format_json_output(filtered_result)
        print(output)
        return 0

    # Text output (default)
    output = format_text_output(filtered_result)
    print(output)
    return 0


def cmd_trace_data(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Trace data object lifecycle through the codebase."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    # Get parameters
    class_name = args.classname
    include_properties = getattr(args, 'include_properties', False)
    output_format = getattr(args, 'format', 'text')

    # Trace data lifecycle
    try:
        trace_result = trace_data_lifecycle(query, class_name, include_properties)
    except Exception as e:
        error_msg = f"Error tracing class '{class_name}': {str(e)}"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Check if class was found
    if not trace_result['summary']['class_found']:
        error_msg = f"Class '{class_name}' not found in documentation"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Apply verbosity filtering
    filtered_result = prepare_output(trace_result, args, TRACE_DATA_ESSENTIAL, TRACE_DATA_STANDARD)

    # Handle output format
    if _maybe_json(args, filtered_result):
        return 0

    if output_format == 'json':
        output = format_trace_data_json(filtered_result)
        print(output)
        return 0

    # Text output (default)
    output = format_trace_data_text(filtered_result)
    print(output)
    return 0


def cmd_impact(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Analyze impact of changing a function or class."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    # Get parameters
    entity_name = args.entity
    depth = getattr(args, 'depth', 2)
    output_format = getattr(args, 'format', 'text')

    # Analyze impact
    try:
        impact_result = analyze_impact(query, entity_name, depth)
    except Exception as e:
        error_msg = f"Error analyzing impact for '{entity_name}': {str(e)}"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Check if entity was found
    if not impact_result['summary']['entity_found']:
        error_msg = f"Entity '{entity_name}' not found in documentation"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Apply verbosity filtering
    filtered_result = prepare_output(impact_result, args, IMPACT_ESSENTIAL, IMPACT_STANDARD)

    # Handle output format
    if _maybe_json(args, filtered_result):
        return 0

    if output_format == 'json':
        output = format_impact_json(filtered_result)
        print(output)
        return 0

    # Text output (default)
    output = format_impact_text(filtered_result)
    print(output)
    return 0


def cmd_refactor_candidates(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Find high-priority refactoring candidates."""
    query = _ensure_query(args, printer)
    if not query:
        return 1

    # Get parameters
    min_complexity = getattr(args, 'min_complexity', 10)
    limit = getattr(args, 'limit', 20)
    output_format = getattr(args, 'format', 'text')

    # Find refactor candidates
    try:
        result = find_refactor_candidates(query, min_complexity, limit)
    except Exception as e:
        error_msg = f"Error finding refactor candidates: {str(e)}"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Check if any candidates found
    if result['summary']['total_candidates'] == 0:
        msg = f"No refactoring candidates found with complexity >= {min_complexity}"
        if _maybe_json(args, {"status": "success", "message": msg, "candidates": []}):
            return 0
        print(msg)
        return 0

    # Apply verbosity filtering
    filtered_result = prepare_output(result, args, REFACTOR_CANDIDATES_ESSENTIAL, REFACTOR_CANDIDATES_STANDARD)

    # Handle output format
    if _maybe_json(args, filtered_result):
        return 0

    if output_format == 'json':
        output = format_refactor_json(filtered_result)
        print(output)
        return 0

    # Text output (default)
    output = format_refactor_text(filtered_result)
    print(output)
    return 0


def cmd_scope(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Get scoped documentation for planning or implementing changes to a module."""
    from claude_skills.doc_query.codebase_query import CodebaseQuery

    # Validate preset
    preset = getattr(args, 'preset', None)
    if not preset:
        error_msg = "Preset is required (--plan or --implement)"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    if preset not in ['plan', 'implement']:
        error_msg = f"Invalid preset '{preset}'. Must be 'plan' or 'implement'"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Get module path
    module = getattr(args, 'module', None)
    if not module:
        error_msg = "Module path is required"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Get function name (optional for --plan, recommended for --implement)
    function = getattr(args, 'function', None)

    # Initialize CodebaseQuery
    docs_path = getattr(args, 'docs_path', None)
    codebase_query = CodebaseQuery(docs_path)

    if not codebase_query.load():
        error_msg = f"Documentation not found at {codebase_query.query.docs_path}. Run 'sdd doc generate' first."
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Build output based on preset
    output_sections = []

    try:
        if preset == 'plan':
            # Plan preset: module summary + complex functions
            module_summary = codebase_query.get_module_summary(
                module,
                include_complexity=True,
                include_dependencies=True
            )
            output_sections.append(module_summary)

            complex_functions = codebase_query.get_complex_functions_in_module(
                module,
                top_n=10,
                threshold=5
            )
            if complex_functions:
                output_sections.append("\n" + complex_functions)

        elif preset == 'implement':
            # Implement preset: callers + call graph + instantiated classes

            # If function is provided, show detailed call analysis
            if function:
                # Show function callers
                callers = codebase_query.get_function_callers(
                    function,
                    include_context=True
                )
                output_sections.append(callers)

                # Show call graph
                call_graph = codebase_query.get_call_graph_summary(
                    function,
                    direction='both',
                    max_depth=2
                )
                output_sections.append("\n" + call_graph)

            # Always show instantiated classes for the module
            instantiated = codebase_query.get_instantiated_classes_in_file(
                module,
                top_n=10
            )
            output_sections.append("\n" + instantiated)

            # If no function provided, suggest using --function
            if not function:
                output_sections.append("\n**Tip:** Use --function <name> for detailed call graph and caller analysis")

    except Exception as e:
        error_msg = f"Error generating scope for module '{module}': {str(e)}"
        if _maybe_json(args, {"status": "error", "message": error_msg}):
            return 1
        printer.error(error_msg)
        return 1

    # Output results
    final_output = "\n".join(output_sections)

    # Prepare structured output for JSON
    result = {
        "preset": preset,
        "module": module,
        "output": final_output
    }
    if function:
        result["function"] = function

    # Apply verbosity filtering
    filtered_result = prepare_output(result, args, SCOPE_ESSENTIAL, SCOPE_STANDARD)

    if _maybe_json(args, filtered_result):
        return 0

    print(final_output)
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
    complexity.add_argument('--module-pattern', help='Filter modules by regex pattern (case-insensitive)')
    complexity.set_defaults(func=cmd_complexity)

    deps = subparsers.add_parser('dependencies', parents=[parent_parser], help='Show module dependencies')
    deps.add_argument('module', help='Module path')
    deps.add_argument('--reverse', action='store_true', help='Show reverse dependencies (who depends on this)')
    deps.set_defaults(func=cmd_dependencies)

    search = subparsers.add_parser('search', parents=[parent_parser], help='Search all documented entities')
    search.add_argument('query', help='Search query (regex)')
    search.add_argument('--limit', type=int, default=None, help='Limit number of results shown')
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
    list_classes.add_argument('--pattern', help='Filter classes by regex pattern (case-insensitive)')
    list_classes.add_argument('--limit', type=int, default=None, help='Limit number of results shown')
    list_classes.set_defaults(func=cmd_list_classes)

    list_functions = subparsers.add_parser('list-functions', parents=[parent_parser], help='List all functions')
    list_functions.add_argument('--module', help='Filter by module')
    list_functions.add_argument('--pattern', help='Filter functions by regex pattern (case-insensitive)')
    list_functions.add_argument('--limit', type=int, default=None, help='Limit number of results shown')
    list_functions.set_defaults(func=cmd_list_functions)

    list_modules = subparsers.add_parser('list-modules', parents=[parent_parser], help='List all modules')
    list_modules.add_argument('--pattern', help='Filter modules by regex pattern (case-insensitive)')
    list_modules.add_argument('--limit', type=int, default=None, help='Limit number of results shown')
    list_modules.set_defaults(func=cmd_list_modules)

    callers = subparsers.add_parser('callers', parents=[parent_parser], help='Show functions that call the specified function')
    callers.add_argument('function_name', help='Name of the function to query')
    callers.set_defaults(func=cmd_callers)

    callees = subparsers.add_parser('callees', parents=[parent_parser], help='Show functions called by the specified function')
    callees.add_argument('function_name', help='Name of the function to query')
    callees.set_defaults(func=cmd_callees)

    call_graph = subparsers.add_parser('call-graph', parents=[parent_parser], help='Build and display call graph for a function')
    call_graph.add_argument('function_name', help='Name of the function to analyze')
    call_graph.add_argument('--direction', choices=['callers', 'callees', 'both'], default='both', help='Direction to traverse (default: both)')
    call_graph.add_argument('--max-depth', type=int, default=3, help='Maximum recursion depth (default: 3)')
    # Get default format from config (call-graph supports text/json/dot)
    default_fmt_cg = get_default_format()
    if default_fmt_cg not in ['text', 'json', 'dot']:
        default_fmt_cg = 'text'
    call_graph.add_argument('--format', choices=['text', 'json', 'dot'], default=default_fmt_cg, help=f'Output format (default: {default_fmt_cg} from config)')
    call_graph.set_defaults(func=cmd_call_graph)

    trace_entry = subparsers.add_parser('trace-entry', parents=[parent_parser], help='Trace execution flow from entry function')
    trace_entry.add_argument('function', help='Name of the entry function to trace from')
    trace_entry.add_argument('--max-depth', type=int, default=5, help='Maximum call chain depth (default: 5)')
    # Get default format from config (text/json only)
    default_fmt_te = get_default_format()
    if default_fmt_te not in ['text', 'json']:
        default_fmt_te = 'text'
    trace_entry.add_argument('--format', choices=['text', 'json'], default=default_fmt_te, help=f'Output format (default: {default_fmt_te} from config)')
    trace_entry.set_defaults(func=cmd_trace_entry)

    trace_data = subparsers.add_parser('trace-data', parents=[parent_parser], help='Trace data object lifecycle through codebase')
    trace_data.add_argument('classname', help='Name of the class to trace')
    trace_data.add_argument('--include-properties', action='store_true', help='Include detailed property access analysis')
    # Get default format from config (text/json only)
    default_fmt_td = get_default_format()
    if default_fmt_td not in ['text', 'json']:
        default_fmt_td = 'text'
    trace_data.add_argument('--format', choices=['text', 'json'], default=default_fmt_td, help=f'Output format (default: {default_fmt_td} from config)')
    trace_data.set_defaults(func=cmd_trace_data)

    impact = subparsers.add_parser('impact', parents=[parent_parser], help='Analyze impact of changing a function or class')
    impact.add_argument('entity', help='Name of the function or class to analyze')
    impact.add_argument('--depth', type=int, default=2, help='Maximum depth for indirect dependency traversal (default: 2)')
    # Get default format from config (text/json only)
    default_fmt_im = get_default_format()
    if default_fmt_im not in ['text', 'json']:
        default_fmt_im = 'text'
    impact.add_argument('--format', choices=['text', 'json'], default=default_fmt_im, help=f'Output format (default: {default_fmt_im} from config)')
    impact.set_defaults(func=cmd_impact)

    refactor = subparsers.add_parser('refactor-candidates', parents=[parent_parser], help='Find high-priority refactoring candidates')
    refactor.add_argument('--min-complexity', type=int, default=10, help='Minimum complexity threshold (default: 10)')
    refactor.add_argument('--limit', type=int, default=20, help='Maximum number of candidates to return (default: 20)')
    # Get default format from config (text/json only)
    default_fmt_rf = get_default_format()
    if default_fmt_rf not in ['text', 'json']:
        default_fmt_rf = 'text'
    refactor.add_argument('--format', choices=['text', 'json'], default=default_fmt_rf, help=f'Output format (default: {default_fmt_rf} from config)')
    refactor.set_defaults(func=cmd_refactor_candidates)

    scope = subparsers.add_parser('scope', parents=[parent_parser], help='Get scoped documentation for planning or implementing changes')
    scope.add_argument('module', help='Module path to analyze')
    scope.add_argument('--plan', dest='preset', action='store_const', const='plan', help='Planning preset: module summary + complex functions')
    scope.add_argument('--implement', dest='preset', action='store_const', const='implement', help='Implementation preset: callers + call graph + instantiated classes')
    scope.add_argument('--function', help='Function name for detailed call analysis (required for --implement preset)')
    scope.set_defaults(func=cmd_scope)
