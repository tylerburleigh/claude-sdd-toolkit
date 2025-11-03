#!/usr/bin/env python3
"""CLI interface for AI-powered PR creation."""

from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

from claude_skills.common import find_specs_directory
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import find_spec_file
from claude_skills.sdd_pr.pr_context import gather_pr_context
from claude_skills.sdd_pr.pr_creation import (
    show_pr_draft_and_wait,
    create_pr_with_ai_description,
    validate_pr_readiness,
)

logger = logging.getLogger(__name__)


def cmd_create_pr(args, printer: PrettyPrinter) -> int:
    """Create PR with AI-generated description.

    This command can operate in two modes:
    1. Draft-only (--draft-only): Show draft without creating PR
    2. Full creation (--approve): Create PR with provided description

    The typical workflow is:
    1. Skill invokes with --draft-only to show draft
    2. User reviews draft
    3. Agent invokes with --approve and --description to create PR

    Args:
        args: Parsed command-line arguments
        printer: PrettyPrinter for formatted output

    Returns:
        Exit code: 0 for success, 1 for error
    """
    printer.header("SDD PR - AI-Powered Pull Request Creation")
    printer.info("")

    # Find specs directory
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        printer.info("Run this command from project root or specify --path")
        return 1

    # Find spec file
    spec_file = find_spec_file(args.spec_id, specs_dir)
    if not spec_file:
        printer.error(f"Spec file not found: {args.spec_id}")
        printer.info(f"Searched in: {specs_dir}")
        return 1

    printer.action(f"Loading spec: {args.spec_id}")
    printer.info("")

    try:
        # Gather all context
        context = gather_pr_context(
            spec_id=args.spec_id,
            spec_path=spec_file,
            specs_dir=specs_dir,
            max_diff_size_kb=getattr(args, 'max_diff_kb', 50)
        )

        # Validate PR readiness
        if not validate_pr_readiness(context['spec_data'], printer):
            return 1

        printer.success("Spec loaded successfully")
        printer.info("")

        # MODE 1: Draft-only (show context and draft)
        if getattr(args, 'draft_only', False):
            printer.info("Draft-only mode: No PR will be created")
            printer.info("")
            printer.info("Context gathered:")
            printer.detail(f"  Commits: {len(context['commits'])}")
            printer.detail(f"  Tasks: {len(context['tasks'])}")
            printer.detail(f"  Phases: {len(context['phases'])}")
            printer.detail(f"  Journals: {len(context['journals'])}")
            printer.detail(f"  Diff size: {len(context['git_diff'])} bytes")
            printer.info("")
            printer.info("Agent should now analyze this context and generate PR description")
            printer.info("")
            return 0

        # MODE 2: Full creation (requires --approve and description)
        if not getattr(args, 'approve', False):
            printer.error("PR creation requires --approve flag")
            printer.info("")
            printer.info("Workflow:")
            printer.info("  1. Agent analyzes context and generates description")
            printer.info("  2. Agent shows draft to user for approval")
            printer.info("  3. Run with --approve flag to create PR")
            printer.info("")
            return 1

        # Get PR title and body from args
        pr_title = getattr(args, 'title', None)
        pr_body = getattr(args, 'description', None)

        if not pr_title:
            # Use spec title as default
            pr_title = context['metadata'].get('title', args.spec_id)
            printer.info(f"Using spec title as PR title: {pr_title}")
            printer.info("")

        if not pr_body:
            printer.error("PR body is required for creation")
            printer.info("Agent should provide --description with AI-generated PR body")
            return 1

        # Create PR immediately (user has already approved via agent)
        # The --approve flag signals that the user reviewed the draft and approved
        success = create_pr_with_ai_description(
            repo_root=context['repo_root'],
            branch_name=context['branch_name'],
            base_branch=context['base_branch'],
            pr_title=pr_title,
            pr_body=pr_body,
            spec_data=context['spec_data'],
            spec_id=args.spec_id,
            specs_dir=specs_dir,
            printer=printer
        )

        return 0 if success else 1

    except FileNotFoundError as e:
        printer.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        printer.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        printer.error(f"Unexpected error: {e}")
        logger.exception("PR creation failed")
        return 1


def register_pr(subparsers, parent_parser):
    """Register sdd-pr subcommands in the main CLI.

    Args:
        subparsers: Subparsers object from argparse
        parent_parser: Parent parser for common arguments
    """
    parser = subparsers.add_parser(
        'create-pr',
        parents=[parent_parser],
        help='Create AI-powered pull request',
        description=(
            'Generate comprehensive PR description from spec context.\n\n'
            'This command analyzes spec metadata, git diffs, commit history, '
            'and journal entries to create detailed pull requests.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        'spec_id',
        help='Specification ID'
    )

    # Mode flags
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--draft-only',
        action='store_true',
        help='Gather context without creating PR (used by agent for analysis)'
    )
    mode_group.add_argument(
        '--approve',
        action='store_true',
        help='Approve and create PR (requires --description)'
    )

    # PR content
    parser.add_argument(
        '--title',
        help='PR title (defaults to spec title)'
    )
    parser.add_argument(
        '--description',
        help='PR body (AI-generated markdown description)'
    )

    # Options
    parser.add_argument(
        '--max-diff-kb',
        type=int,
        default=50,
        help='Maximum diff size in KB before truncation (default: 50)'
    )

    parser.set_defaults(func=cmd_create_pr)


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description='SDD PR - AI-powered pull request creation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parent_parser.add_argument(
        '--path',
        help='Path to project directory (default: current directory)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)
    register_pr(subparsers, parent_parser)

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Create printer
    printer = PrettyPrinter(verbose=args.verbose)

    # Execute command
    try:
        return args.func(args, printer)
    except Exception as e:
        printer.error(f"Command failed: {e}")
        if args.verbose:
            logger.exception("Command execution failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
