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
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    PR_CONTEXT_ESSENTIAL,
    PR_CONTEXT_STANDARD,
    PR_CREATE_ESSENTIAL,
    PR_CREATE_STANDARD,
)
from claude_skills.sdd_pr.pr_context import gather_pr_context
from claude_skills.sdd_pr.pr_creation import (
    show_pr_draft_and_wait,
    create_pr_with_ai_description,
    validate_pr_readiness,
)

logger = logging.getLogger(__name__)


def _pr_output_json(data, args, essential_fields, standard_fields):
    """Emit filtered JSON payload if --json is enabled."""
    if getattr(args, 'json', False):
        payload = prepare_output(data, args, essential_fields, standard_fields)
        output_json(payload, getattr(args, 'compact', False))
        return True
    return False


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

        context_counts = {
            'commits': len(context['commits']),
            'tasks': len(context['tasks']),
            'phases': len(context['phases']),
            'journals': len(context['journals']),
        }
        diff_bytes = len(context['git_diff'].encode('utf-8')) if context.get('git_diff') else 0
        draft_payload = {
            'mode': 'draft',
            'spec_id': args.spec_id,
            'branch_name': context['branch_name'],
            'base_branch': context['base_branch'],
            'context_counts': context_counts,
            'diff_bytes': diff_bytes,
            'repo_root': str(context['repo_root']),
        }

        # MODE 1: Draft-only (show context and draft)
        if getattr(args, 'draft_only', False):
            if _pr_output_json(draft_payload, args, PR_CONTEXT_ESSENTIAL, PR_CONTEXT_STANDARD):
                return 0

            diff_kb = diff_bytes / 1024 if diff_bytes else 0
            printer.success("Draft mode: context gathered")
            printer.info(
                "Commits: {commits} • Tasks: {tasks} • Phases: {phases} • "
                "Journals: {journals} • Diff: {diff:.1f} KB".format(
                    commits=context_counts['commits'],
                    tasks=context_counts['tasks'],
                    phases=context_counts['phases'],
                    journals=context_counts['journals'],
                    diff=diff_kb,
                )
            )
            printer.info(f"Branch: {context['branch_name']} → {context['base_branch']}")
            printer.info("Provide --description and run with --approve to create the PR.")
            return 0

        # MODE 2: Full creation (requires --approve and description)
        if not getattr(args, 'approve', False):
            printer.error("PR creation requires --approve flag")
            printer.info("Run draft mode first, then rerun with --approve and --description.")
            error_payload = {
                'success': False,
                'spec_id': args.spec_id,
                'pr_url': None,
                'pr_number': None,
                'branch_name': context['branch_name'],
                'base_branch': context['base_branch'],
                'pr_title': None,
                'error': 'approve flag missing',
            }
            _pr_output_json(error_payload, args, PR_CREATE_ESSENTIAL, PR_CREATE_STANDARD)
            return 1

        # Get PR title and body from args
        pr_title = getattr(args, 'title', None)
        pr_body = getattr(args, 'description', None)

        if not pr_title:
            # Use spec title as default
            pr_title = context['metadata'].get('title', args.spec_id)
            printer.info(f"Using spec title as PR title: {pr_title}")

        if not pr_body:
            printer.error("PR body is required for creation")
            printer.info("Agent should provide --description with AI-generated PR body")
            error_payload = {
                'success': False,
                'spec_id': args.spec_id,
                'pr_url': None,
                'pr_number': None,
                'branch_name': context['branch_name'],
                'base_branch': context['base_branch'],
                'pr_title': pr_title,
                'error': 'missing PR body',
            }
            _pr_output_json(error_payload, args, PR_CREATE_ESSENTIAL, PR_CREATE_STANDARD)
            return 1

        # Create PR immediately (user has already approved via agent)
        # The --approve flag signals that the user reviewed the draft and approved
        success, pr_result = create_pr_with_ai_description(
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

        pr_result.setdefault('spec_id', args.spec_id)
        if _pr_output_json(pr_result, args, PR_CREATE_ESSENTIAL, PR_CREATE_STANDARD):
            return 0 if success else 1

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
