#!/usr/bin/env python3
"""
Codebase Documentation Generator CLI
Main command-line interface for generating comprehensive codebase documentation.

Usage:
    sdd doc generate <project_directory> [options]
    sdd doc validate <json_file>
    sdd doc analyze <project_directory> [options]

Subcommands:
    generate    Generate codebase analysis JSON
    validate    Validate generated JSON against schema
    analyze     Analyze codebase and print statistics only
 
Options for generate:
    --output-dir DIR     Output directory for analysis data (default: ./docs)
    --name NAME          Project name (default: directory name)
    --version VERSION    Project version (default: 1.0.0)
    --language LANG      Filter by language (python, javascript, go, etc.)
    --exclude PATTERN    Exclude files matching pattern
    --verbose, -v        Verbose output


Examples:
    sdd doc generate ./src
    sdd doc generate ./src --name MyProject --version 0.1.0
    sdd doc generate ./src --output-dir ./docs
    sdd doc analyze ./src --verbose
    sdd doc validate ./docs/codebase.json
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Iterable, Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.schema_loader import load_json_schema
from claude_skills.common.metrics import track_metrics
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    DOC_GENERATE_ESSENTIAL,
    DOC_GENERATE_STANDARD,
    DOC_VALIDATE_ESSENTIAL,
    DOC_VALIDATE_STANDARD,
    DOC_ANALYZE_ESSENTIAL,
    DOC_ANALYZE_STANDARD,
)
from claude_skills.llm_doc_gen.analysis.generator import DocumentationGenerator
from claude_skills.llm_doc_gen.analysis.parsers import Language, create_parser_factory
from claude_skills.llm_doc_gen.analysis.calculator import calculate_statistics
from claude_skills.llm_doc_gen.analysis.optimization.filters import FilterProfile, create_filter_chain
from claude_skills.llm_doc_gen.analysis.detectors import (
    detect_framework,
    identify_key_files,
    detect_layers,
    suggest_reading_order,
    extract_readme,
    create_context_summary,
)
from claude_skills.llm_doc_gen.analysis.ai_consultation import (
    get_available_tools,
    generate_architecture_docs,
    generate_ai_context_docs,
    compose_architecture_doc,
    compose_ai_context_doc,
)

BASE_EXCLUDES = [
    # Version control
    '.git', '.svn', '.hg', '.bzr',
    # Python
    '__pycache__', 'venv', '.venv', '.tox', '.mypy_cache', '.pytest_cache',
    '*.egg-info', 'build', 'dist', '.eggs',
    # JavaScript/Node
    'node_modules', '.next', '.nuxt', 'coverage', '.nyc_output',
    # IDE
    '.idea', '.vscode', '.vs', '.fleet', '.sublime-project', '.sublime-workspace',
    # Build/Cache
    '.cache', 'tmp', 'temp', 'target', 'out',
    # Environment
    '.env', '.env.local', '.env.*.local',
    # OS
    '.DS_Store', 'Thumbs.db',
]

_DOC_SCHEMA_NAME = "documentation-schema.json"
_REQUIRED_DOC_KEYS = [
    "metadata",
    "statistics",
    "modules",
    "classes",
    "functions",
    "dependencies",
]
def _basic_doc_validation(doc: dict) -> list[str]:
    if not isinstance(doc, dict):
        return _REQUIRED_DOC_KEYS.copy()
    return [key for key in _REQUIRED_DOC_KEYS if key not in doc]


def _schema_warning(printer: PrettyPrinter, args: argparse.Namespace, message: str) -> None:
    if getattr(args, "json", False):
        return
    printer.warning(message)



def _dump_json(payload: object) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _print_if_json(args: argparse.Namespace, payload: object, printer: PrettyPrinter) -> bool:
    if getattr(args, 'json', False):
        _dump_json(payload)
        return True
    return False


def _exclude_patterns(extra: Optional[Iterable[str]]) -> list[str]:
    return BASE_EXCLUDES + list(extra or [])


def _handle_error(args: argparse.Namespace, printer: PrettyPrinter, exc: Exception) -> int:
    if getattr(args, 'json', False):
        _dump_json({"status": "error", "message": str(exc)})
        return 1
    printer.error(str(exc))
    if getattr(args, 'verbose', False):
        traceback.print_exc()
    return 1


def _parse_model_override(values: Optional[list[str]]) -> Optional[object]:
    """
    Parse repeated model override flags into an ai_config-compatible structure.
    """
    if not values:
        return None

    overrides: dict[str, str] = {}
    default_override: Optional[str] = None

    for raw_value in values:
        if not raw_value:
            continue
        entry = raw_value.strip()
        if not entry:
            continue

        separator_index = -1
        for separator in ("=", ":"):
            if separator in entry:
                separator_index = entry.find(separator)
                break

        if separator_index > 0:
            key = entry[:separator_index].strip()
            value = entry[separator_index + 1 :].strip()
            if key and value:
                overrides[key] = value
            continue

        default_override = entry

    if overrides:
        if default_override:
            overrides.setdefault("default", default_override)
        return overrides

    return default_override


def cmd_generate(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    project_dir = Path(args.directory)
    if not project_dir.exists():
        message = f"Directory '{project_dir}' does not exist"
        if _print_if_json(args, {"status": "error", "message": message}, printer):
            return 1
        printer.error(message)
        return 1

    project_name = args.name or project_dir.name
    output_dir = Path(args.output_dir)
    exclude_patterns = _exclude_patterns(args.exclude)

    languages = None
    if getattr(args, 'language', None):
        try:
            languages = [Language[args.language.upper()]]
        except KeyError as lang_exc:
            warning = (
                "Unknown language: {lang}. Supported: python, javascript, typescript, go, html, css"
                .format(lang=args.language)
            )
            if _print_if_json(args, {"status": "error", "message": warning}, printer):
                return 1
            printer.warning(str(lang_exc))
            printer.detail("Continuing with all languages...")
            languages = None

    # Handle filter profile and custom overrides
    filter_profile = None
    if getattr(args, 'filter_mode', None):
        filter_profile = FilterProfile(args.filter_mode)

    # Handle cache options
    cache_dir = None
    if getattr(args, 'cache', False) or getattr(args, 'cache_dir', None):
        # Use specified cache_dir or default
        cache_dir = Path(getattr(args, 'cache_dir', None) or './.doc-cache')

        # Clear cache if requested
        if getattr(args, 'clear_cache', False):
            from claude_skills.llm_doc_gen.analysis.optimization.cache import PersistentCache
            if cache_dir.exists():
                cache = PersistentCache(cache_dir)
                cache.clear()
                if not _print_if_json(args, {"status": "info", "message": "Cache cleared"}, printer):
                    printer.detail(f"Cache cleared at {cache_dir}")

    generator = DocumentationGenerator(
        project_dir,
        project_name,
        args.version,
        exclude_patterns,
        languages,
        filter_profile,
        cache_dir,
    )

    try:
        generator.generate_all(
            output_dir,
            verbose=getattr(args, 'verbose', False),
            parallel=getattr(args, 'parallel', False),
            num_workers=getattr(args, 'workers', None),
            streaming=getattr(args, 'streaming', False),
            compress=getattr(args, 'compress', False),
        )
        output_data = {
            "status": "ok",
            "project": project_name,
            "output_dir": str(output_dir.resolve()),
            "format": "json",
        }
        output_data = prepare_output(output_data, args, DOC_GENERATE_ESSENTIAL, DOC_GENERATE_STANDARD)
        if _print_if_json(args, output_data, printer):
            return 0
        printer.success(f"Documentation generated at {output_dir}")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        return _handle_error(args, printer, exc)


def cmd_validate(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    json_path = Path(args.json_file)
    if not json_path.exists():
        message = f"File '{json_path}' does not exist"
        if _print_if_json(args, {"status": "error", "message": message}, printer):
            return 1
        printer.error(message)
        return 1

    try:
        with open(json_path, 'r', encoding='utf-8') as fh:
            doc = json.load(fh)
    except json.JSONDecodeError as exc:
        return _handle_error(args, printer, exc)
    except Exception as exc:  # pylint: disable=broad-except
        return _handle_error(args, printer, exc)

    schema, source, load_error = load_json_schema(_DOC_SCHEMA_NAME)
    schema_info: dict[str, Optional[str] | list[str] | bool] = {
        "source": source,
        "warnings": [],
        "errors": [],
    }
    if load_error:
        schema_info["error"] = load_error

    def _emit_payload(status: str, message: str, errors: Optional[list[str]] = None) -> int:
        if errors is not None:
            schema_info["errors"] = errors
        payload = {"status": status, "message": message, "schema": schema_info}
        payload = prepare_output(payload, args, DOC_VALIDATE_ESSENTIAL, DOC_VALIDATE_STANDARD)
        if _print_if_json(args, payload, printer):
            return 0 if status == "ok" else 1
        if status == "ok":
            printer.success(message)
            return 0
        printer.error(message)
        return 1

    def _emit_error(message: str, errors: Optional[list[str]] = None) -> int:
        if errors is not None:
            schema_info["errors"] = errors
        payload = {"status": "error", "message": message, "schema": schema_info}
        payload = prepare_output(payload, args, DOC_VALIDATE_ESSENTIAL, DOC_VALIDATE_STANDARD)
        if _print_if_json(args, payload, printer):
            return 1
        printer.error(message)
        return 1

    if schema is None:
        warning_message = load_error or "Documentation schema not found."
        schema_info["warnings"].append(warning_message)
        _schema_warning(printer, args, warning_message)
        skip_message = "Schema validation skipped: documentation schema unavailable."
        schema_info["warnings"].append(skip_message)
        _schema_warning(printer, args, skip_message)
        missing_keys = _basic_doc_validation(doc)
        if missing_keys:
            missing_message = f"Missing required keys: {', '.join(missing_keys)}"
            return _emit_error(missing_message)
        success_message = "Basic validation passed (schema unavailable)."
        return _emit_payload("ok", success_message)

    try:
        import jsonschema  # type: ignore  # pylint: disable=import-error
    except ImportError:
        warning_message = (
            "Schema validation skipped: install the 'jsonschema' package "
            "or use optional dependency group 'validation' to enable Draft 7 validation."
        )
        schema_info["warnings"].append(warning_message)
        _schema_warning(printer, args, warning_message)
        missing_keys = _basic_doc_validation(doc)
        if missing_keys:
            missing_message = f"Missing required keys: {', '.join(missing_keys)}"
            return _emit_error(missing_message)
        success_message = "Basic validation passed (install jsonschema for full validation)."
        return _emit_payload("ok", success_message)

    validator = jsonschema.Draft7Validator(schema)  # type: ignore[attr-defined]
    validation_errors = sorted(validator.iter_errors(doc), key=lambda err: list(err.path))  # type: ignore[attr-defined]

    if validation_errors:
        formatted = []
        for error in validation_errors:
            pointer = "/".join(str(part) for part in error.path) or "<root>"
            formatted.append(f"{pointer}: {error.message}")
        schema_info["errors"] = formatted
        if not getattr(args, "json", False):
            for item in formatted[:5]:
                printer.error(f"Schema violation at {item}")
            if len(formatted) > 5:
                printer.error(f"... {len(formatted) - 5} more schema warnings (re-run with --json for details)")
        return _emit_error("JSON documentation failed schema validation", formatted)

    if source:
        schema_info["validated"] = True

    return _emit_payload("ok", "JSON documentation is valid")


def cmd_analyze(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    project_dir = Path(args.directory)
    if not project_dir.exists():
        message = f"Directory '{project_dir}' does not exist"
        if _print_if_json(args, {"status": "error", "message": message}, printer):
            return 1
        printer.error(message)
        return 1

    exclude_patterns = _exclude_patterns(args.exclude)
    try:
        factory = create_parser_factory(project_dir, exclude_patterns)
        parse_result = factory.parse_all(verbose=getattr(args, 'verbose', False))

        statistics = calculate_statistics(
            [module.to_dict() for module in parse_result.modules],
            [func.to_dict() for func in parse_result.functions],
        )

        payload = {
            "status": "ok",
            "project": args.name or project_dir.name,
            "statistics": statistics,
        }
        payload = prepare_output(payload, args, DOC_ANALYZE_ESSENTIAL, DOC_ANALYZE_STANDARD)
        if _print_if_json(args, payload, printer):
            return 0

        printer.detail("\n📊 Project Statistics:")
        printer.detail(f"   Total Files:      {statistics['total_files']}")
        printer.detail(f"   Total Lines:      {statistics['total_lines']}")
        printer.detail(f"   Total Classes:    {statistics['total_classes']}")
        printer.detail(f"   Total Functions:  {statistics['total_functions']}")
        printer.detail(f"   Avg Complexity:   {statistics['avg_complexity']}")
        printer.detail(f"   Max Complexity:   {statistics['max_complexity']}")

        if statistics.get('by_language'):
            printer.detail("\n🌐 Language Breakdown:")
            for lang, lang_stats in sorted(statistics['by_language'].items()):
                printer.detail(f"   {lang.upper()}:")
                printer.detail(
                    "      Files: {files}, Lines: {lines}, Functions: {functions}".format(
                        files=lang_stats['files'],
                        lines=lang_stats['lines'],
                        functions=lang_stats['functions'],
                    )
                )

        if statistics['high_complexity_functions']:
            printer.detail("\n⚠️  High Complexity Functions:")
            for func in statistics['high_complexity_functions']:
                printer.detail(f"   - {func}")

        return 0
    except Exception as exc:  # pylint: disable=broad-except
        return _handle_error(args, printer, exc)


def cmd_analyze_with_ai(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    project_dir = Path(args.directory)
    if not project_dir.exists():
        message = f"Directory '{project_dir}' does not exist"
        if getattr(args, 'json', False):
            _dump_json({"status": "error", "message": message})
            return 1
        printer.error(message)
        return 1

    if getattr(args, 'json', False):
        _dump_json({"status": "error", "message": "--json is not supported for analyze-with-ai"})
        return 1

    project_name = args.name or project_dir.name
    output_dir = Path(args.output_dir)
    exclude_patterns = _exclude_patterns(args.exclude)

    try:
        printer.detail(f"📊 Analyzing {project_name} structure...")
        generator = DocumentationGenerator(
            project_dir,
            project_name,
            args.version,
            exclude_patterns,
        )

        result = generator.generate(verbose=getattr(args, 'verbose', False))
        analysis = result['analysis']
        statistics = result['statistics']

        printer.detail("\n🔍 Detecting framework and architectural patterns...")
        framework_info = detect_framework(analysis['modules'])
        key_files = identify_key_files(analysis['modules'], project_dir)
        layers = detect_layers(analysis['modules'])
        reading_order = suggest_reading_order(key_files, framework_info)
        readme_content = extract_readme(project_dir)

        if framework_info['primary']:
            printer.detail(f"   Framework: {framework_info['primary']}")
        printer.detail(f"   Key files identified: {len(key_files)}")
        printer.detail(f"   Architectural layers: {len(layers)}")

        context_summary = create_context_summary(
            framework_info,
            reading_order,
            layers,
            statistics,
            readme_content,
        )

        printer.detail("\n🤖 Checking AI tool availability...")
        available_tools = get_available_tools()
        if not available_tools:
            printer.warning("No AI tools available. Generating structural documentation only.")
            printer.detail("Install cursor-agent, gemini, or codex for AI-generated docs:")
            printer.detail("   - cursor-agent: Check cursor.com")
            printer.detail("   - gemini: npm install -g @google/generative-ai-cli")
            printer.detail("   - codex: npm install -g @anthropic/codex")

            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / 'codebase.json'
            generator.save_json(json_path, analysis, statistics, verbose=getattr(args, 'verbose', False))
            printer.success(f"Structural analysis saved to {json_path}")
            return 0

        printer.detail(f"   Available tools: {', '.join(available_tools)}")

        use_multi_agent = not args.single_agent
        tool_arg = args.ai_tool if hasattr(args, 'ai_tool') else "auto"
        model_override = _parse_model_override(getattr(args, "model", None))

        printer.detail("\n🧠 Generating AI documentation...")
        if use_multi_agent and len(available_tools) >= 2:
            printer.detail("   Mode: Multi-agent (parallel consultation)")
        else:
            printer.detail(f"   Mode: Single-agent ({tool_arg})")

        # Gather AI research (returns dict with responses_by_tool)
        arch_result = None
        arch_success = False
        if not args.skip_architecture:
            printer.detail("\n📐 Gathering architecture research...")
            arch_success, arch_result = generate_architecture_docs(
                context_summary,
                reading_order,
                project_dir,
                tool=tool_arg,
                use_multi_agent=use_multi_agent,
                dry_run=args.dry_run,
                verbose=getattr(args, 'verbose', False),
                printer=printer,
                model_override=model_override,
            )
            if not arch_success:
                printer.warning(f"Failed to get architecture research")

        context_result = None
        context_success = False
        if not args.skip_ai_context:
            printer.detail("\n📝 Gathering AI context research...")
            context_success, context_result = generate_ai_context_docs(
                context_summary,
                reading_order,
                project_dir,
                tool=tool_arg,
                use_multi_agent=use_multi_agent,
                dry_run=args.dry_run,
                verbose=getattr(args, 'verbose', False),
                printer=printer,
                model_override=model_override,
            )
            if not context_success:
                printer.warning(f"Failed to get AI context research")

        if args.dry_run:
            printer.detail("\n🔍 Dry run complete. No files saved.")
            return 0

        # Always write structural documentation
        printer.detail(f"\n💾 Saving structural analysis to {output_dir}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / 'codebase.json'
        generator.save_json(json_path, analysis, statistics, verbose=False)
        printer.success(f"   ✅ {json_path}")

        # Return JSON with separate AI responses for main agent synthesis
        import json as json_module

        printer.detail("\n📤 Returning AI research for main agent synthesis...")

        research_output = {
            "status": "success",
            "project_name": project_name,
            "version": args.version,
            "output_dir": str(output_dir),
            "architecture_research": arch_result.get("responses_by_tool", {}) if arch_success and arch_result else None,
            "ai_context_research": context_result.get("responses_by_tool", {}) if context_success and context_result else None,
            "statistics": statistics,
        }

        # Print JSON to stdout for main agent to parse
        print("\n" + "=" * 80)
        print("RESEARCH_JSON_START")
        print(json_module.dumps(research_output, indent=2))
        print("RESEARCH_JSON_END")
        print("=" * 80)

        printer.success("\n✅ Research gathering complete!")
        printer.detail("\n📋 Next steps for main agent:")
        printer.detail("   1. Parse JSON output from stdout")
        printer.detail("   2. Synthesize architecture_research from all AI tools")
        printer.detail("   3. Synthesize ai_context_research from all AI tools")
        printer.detail("   4. Use architecture_research to generate architecture.md and related shards")
        printer.detail("   5. Apply ai_context_research insights when composing index.md and guidance sections")

        return 0

    except Exception as exc:  # pylint: disable=broad-except
        return _handle_error(args, printer, exc)


def register_code_doc(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[attr-defined]
    """Register documentation commands for the unified CLI."""
    generate_parser = subparsers.add_parser(
        'generate',
        parents=[parent_parser],
        help='Generate codebase documentation',
        description='Generate documentation (Markdown/JSON)',
    )
    generate_parser.add_argument('directory', help='Project directory to analyze')
    generate_parser.add_argument('--output-dir', default='./docs', help='Output directory (default: ./docs)')
    generate_parser.add_argument('--name', help='Project name (default: directory name)')
    generate_parser.add_argument('--version', default='1.0.0', help='Project version (default: 1.0.0)')
    generate_parser.add_argument('--language', help='Filter by language (python, javascript, typescript, go, html, css)')
    generate_parser.add_argument('--exclude', action='append', default=[], help='Exclude pattern (can be used multiple times)')

    # Filter options for large codebases
    generate_parser.add_argument(
        '--filter-mode',
        choices=['fast', 'balanced', 'complete'],
        help='Filter profile: fast (aggressive filtering for large codebases), balanced (moderate filtering), complete (minimal filtering)'
    )
    generate_parser.add_argument('--max-file-size', type=int, help='Maximum file size in bytes (overrides filter-mode default)')
    generate_parser.add_argument('--max-files-per-dir', type=int, help='Maximum files per directory (overrides filter-mode default)')
    generate_parser.add_argument('--sample-rate', type=float, help='Sampling rate 0.0-1.0 for very large projects (overrides filter-mode default)')

    # Parallel processing options
    generate_parser.add_argument('--parallel', action='store_true', help='Enable parallel parsing using multiprocessing (faster on multi-core systems)')
    generate_parser.add_argument('--workers', type=int, metavar='N', help='Number of worker processes for parallel parsing (default: auto-detect CPU count - 1)')

    # Streaming and compression options for JSON output
    generate_parser.add_argument('--streaming', action='store_true', help='Use streaming generation for JSON output (memory efficient for large codebases)')
    generate_parser.add_argument('--compress', action='store_true', help='Use gzip compression for JSON output')

    # Cache options
    generate_parser.add_argument('--cache', action='store_true', help='Enable persistent caching of parse results (speeds up subsequent runs)')
    generate_parser.add_argument('--cache-dir', type=str, help='Directory for cache storage (default: ./.doc-cache)')
    generate_parser.add_argument('--clear-cache', action='store_true', help='Clear the cache before generating documentation')

    generate_parser.set_defaults(func=cmd_generate)

    validate_parser = subparsers.add_parser(
        'validate-json',
        parents=[parent_parser],
        aliases=['validate'],
        help='Validate generated JSON documentation against schema',
    )
    validate_parser.add_argument('json_file', help='JSON file to validate')
    validate_parser.set_defaults(func=cmd_validate)

    analyze_parser = subparsers.add_parser(
        'analyze',
        parents=[parent_parser],
        help='Analyze codebase and print statistics only',
    )
    analyze_parser.add_argument('directory', help='Project directory to analyze')
    analyze_parser.add_argument('--name', help='Project name (default: directory name)')
    analyze_parser.add_argument('--language', help='Filter by language (python, javascript, typescript, go, html, css)')
    analyze_parser.add_argument('--exclude', action='append', default=[], help='Exclude pattern (can be used multiple times)')
    analyze_parser.set_defaults(func=cmd_analyze)

    analyze_ai_parser = subparsers.add_parser(
        'analyze-with-ai',
        parents=[parent_parser],
        help='Generate comprehensive documentation with AI assistance',
    )
    analyze_ai_parser.add_argument('directory', help='Project directory to analyze')
    analyze_ai_parser.add_argument('--output-dir', default='./docs', help='Output directory (default: ./docs)')
    analyze_ai_parser.add_argument('--name', help='Project name (default: directory name)')
    analyze_ai_parser.add_argument('--version', default='1.0.0', help='Project version (default: 1.0.0)')
    analyze_ai_parser.add_argument('--exclude', action='append', default=[], help='Exclude pattern (can be used multiple times)')
    analyze_ai_parser.add_argument('--ai-tool', choices=['auto', 'cursor-agent', 'gemini', 'codex'], default='auto', help='AI tool to use (default: auto-select)')
    analyze_ai_parser.add_argument(
        '--model',
        action='append',
        metavar='MODEL',
        help='Override model selection (repeat for per-tool overrides, e.g., gemini=gemini-pro)',
    )
    analyze_ai_parser.add_argument('--single-agent', action='store_true', help='Use single agent instead of multi-agent consultation')
    analyze_ai_parser.add_argument('--skip-architecture', action='store_true', help='Skip architecture.md shard generation')
    analyze_ai_parser.add_argument('--skip-ai-context', action='store_true', help='Skip AI context research')
    analyze_ai_parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without running AI')
    analyze_ai_parser.set_defaults(func=cmd_analyze_with_ai)
