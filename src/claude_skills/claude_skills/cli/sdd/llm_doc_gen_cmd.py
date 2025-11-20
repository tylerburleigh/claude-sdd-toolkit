#!/usr/bin/env python3
"""
LLM-Based Documentation Generator CLI

Command-line interface for generating comprehensive documentation using LLMs.

Usage:
    sdd llm-doc-gen generate <project_directory> [options]

Subcommands:
    generate    Generate documentation using LLMs

Options for generate:
    --output-dir DIR     Output directory for documentation (default: ./docs)
    --name NAME          Project name (default: directory name)
    --description DESC   Project description
    --batch-size N       Number of shards to process per batch (default: 3)
    --no-batching        Disable batched generation
    --resume             Resume from previous interrupted generation
    --verbose, -v        Verbose output

Examples:
    sdd llm-doc-gen generate ./src
    sdd llm-doc-gen generate ./src --name MyProject --description "A web application"
    sdd llm-doc-gen generate ./src --output-dir ./docs/ai --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.metrics import track_metrics
from claude_skills.cli.sdd.output_utils import prepare_output


@track_metrics('llm_doc_gen_generate')
def handle_generate(args, printer: PrettyPrinter) -> int:
    """Handle the generate command."""
    try:
        # Import here to avoid slow startup times
        from claude_skills.llm_doc_gen.main import (
            DocumentationWorkflow,
            create_project_data_from_scan,
            create_index_data_from_project,
            scan_project_files,
        )
        from claude_skills.llm_doc_gen.ai_consultation import consult_llm

        # Create wrapper to adapt ConsultationResult to tuple format expected by generators
        def llm_consultation_wrapper(prompt: str) -> tuple[bool, str]:
            """Wrapper to convert ConsultationResult to (bool, str) tuple."""
            result = consult_llm(prompt, verbose=args.verbose)
            if result.success:
                return (True, result.output)
            else:
                error_msg = result.error or "LLM consultation failed"
                return (False, error_msg)

        project_root = Path(args.directory).resolve()
        if not project_root.exists():
            printer.error(f"Project directory not found: {project_root}")
            return 1

        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine project name
        project_name = args.name or project_root.name

        printer.info(f"Generating LLM-based documentation for: {project_name}")
        printer.info(f"Project root: {project_root}")
        printer.info(f"Output directory: {output_dir}")
        if args.resume:
            printer.info("Resume mode: Will continue from previous state if available")

        # Handle cache options
        cache_dir = None
        if getattr(args, 'cache', False) or getattr(args, 'cache_dir', None):
            # Use specified cache_dir or default
            cache_dir = Path(getattr(args, 'cache_dir', None) or './.doc-cache')
            printer.info(f"Cache enabled: {cache_dir}")

            # Clear cache if requested
            if getattr(args, 'clear_cache', False):
                from claude_skills.llm_doc_gen.analysis.optimization.cache import PersistentCache
                if cache_dir.exists():
                    cache = PersistentCache(cache_dir)
                    cache.clear()
                    printer.info(f"Cache cleared at {cache_dir}")

        # Create project data from scan
        printer.info("Scanning project...")
        project_data = create_project_data_from_scan(project_root, project_name, output_dir, cache_dir)

        # Create index data
        project_description = args.description or f"{project_name} documentation"
        index_data = create_index_data_from_project(project_data, project_description)

        # Scan for key files
        file_info = scan_project_files(project_root)
        project_data_dict = {
            "project_name": project_data.project_name,
            "project_type": project_data.project_type,
            "repository_type": project_data.repository_type,
            "primary_languages": project_data.primary_languages,
            "tech_stack": project_data.tech_stack,
            "file_count": project_data.file_count,
            "total_loc": project_data.total_loc,
            "parts": project_data.parts,
            "key_files": file_info.get("key_files", []),
            "source_files": file_info.get("source_files", [])
        }

        # Create workflow
        workflow = DocumentationWorkflow(project_root, output_dir)

        # Generate documentation
        printer.info("Generating documentation shards...")
        use_batching = not args.no_batching
        batch_size = args.batch_size if use_batching else 3

        results = workflow.generate_full_documentation(
            project_data=project_data,
            index_data=index_data,
            llm_consultation_fn=llm_consultation_wrapper,
            use_batching=use_batching,
            batch_size=batch_size,
            resume=args.resume
        )

        # Report results
        if results["success"]:
            printer.success(f"✓ Documentation generated successfully!")
            printer.info(f"  Shards generated: {len(results['shards_generated'])}")
            for shard in results["shards_generated"]:
                printer.info(f"    - {shard}")

            if results.get("batches_processed"):
                printer.info(f"  Batches processed: {results['batches_processed']}")

            printer.info(f"\nDocumentation written to: {output_dir}")

            # List generated files
            generated_files = list(output_dir.glob("*.md"))
            if generated_files:
                printer.info(f"\nGenerated files:")
                for file in sorted(generated_files):
                    size_kb = file.stat().st_size / 1024
                    printer.info(f"  - {file.name} ({size_kb:.1f} KB)")

            return 0
        else:
            printer.error("✗ Documentation generation failed")
            if results.get("shards_failed"):
                printer.error(f"  Failed shards: {len(results['shards_failed'])}")
                for shard in results["shards_failed"]:
                    error_msg = results["summaries"].get(shard, "Unknown error")
                    printer.error(f"    - {shard}: {error_msg}")
            return 1

    except Exception as e:
        printer.error(f"Error generating documentation: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def register_llm_doc_gen(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[attr-defined]
    """Register llm-doc-gen commands for the unified CLI."""
    # Create main llm-doc-gen parser
    llm_doc_gen_parser = subparsers.add_parser(
        'llm-doc-gen',
        parents=[parent_parser],
        help='Generate documentation using LLMs',
        description='LLM-Based Documentation Generator - Generate comprehensive documentation using Large Language Models'
    )

    # Create subparsers for llm-doc-gen commands
    llm_doc_gen_subparsers = llm_doc_gen_parser.add_subparsers(
        title='llm-doc-gen commands',
        dest='llm_doc_gen_command',
        required=True
    )

    # Register 'generate' subcommand
    generate_parser = llm_doc_gen_subparsers.add_parser(
        'generate',
        parents=[parent_parser],
        help='Generate documentation using LLMs',
        description='Generate comprehensive documentation using Large Language Models'
    )
    generate_parser.add_argument('directory', help='Project directory to document')
    generate_parser.add_argument(
        '--output-dir',
        default='./docs',
        help='Output directory for documentation (default: ./docs)'
    )
    generate_parser.add_argument(
        '--name',
        help='Project name (default: directory name)'
    )
    generate_parser.add_argument(
        '--description',
        help='Project description for documentation'
    )
    generate_parser.add_argument(
        '--batch-size',
        type=int,
        default=3,
        help='Number of shards to process per batch (default: 3)'
    )
    generate_parser.add_argument(
        '--no-batching',
        action='store_true',
        help='Disable batched generation'
    )
    generate_parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous interrupted generation (uses saved state)'
    )
    generate_parser.add_argument(
        '--cache',
        action='store_true',
        help='Enable persistent caching of parse results (speeds up subsequent runs)'
    )
    generate_parser.add_argument(
        '--cache-dir',
        type=str,
        help='Directory for cache storage (default: ./.doc-cache)'
    )
    generate_parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the cache before generating documentation'
    )
    generate_parser.set_defaults(func=handle_generate)
