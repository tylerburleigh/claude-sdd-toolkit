"""Plugin registration system for subcommands.

This module provides the central registry for all SDD subcommands.
All registered commands automatically inherit global options including:
- Verbosity control (--quiet/-q, --verbose/-v)
- Output formatting (--json, --no-json, --compact, --no-compact)
- Project paths (--path, --specs-dir)
- Debug options (--debug, --no-color)

Command Handler Verbosity Interface:
    All command handlers receive args.verbosity_level automatically set
    to one of: VerbosityLevel.QUIET, VerbosityLevel.NORMAL, or VerbosityLevel.VERBOSE

    Use output utilities for verbosity-aware output:
        from claude_skills.cli.sdd.output_utils import prepare_output
        filtered_output = prepare_output(data, args, essential_fields, standard_fields)
"""
import importlib
import logging
from typing import Callable, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

_OPTIONAL_MODULES: Sequence[Tuple[str, str, str]] = (
    ("claude_skills.sdd_render.cli", "register_render", "sdd_render"),
    ("claude_skills.sdd_fidelity_review.cli", "register_commands", "sdd_fidelity_review"),
)


def get_verbosity_level(args):
    """Get the verbosity level from command arguments.

    Convenience wrapper for accessing the verbosity level in command handlers.
    The verbosity level is automatically set by the main CLI after parsing.

    Args:
        args: Parsed argparse.Namespace from command handler

    Returns:
        VerbosityLevel enum (QUIET, NORMAL, or VERBOSE)

    Example:
        def my_command_handler(args, printer):
            from claude_skills.cli.sdd.registry import get_verbosity_level
            from claude_skills.cli.sdd.verbosity import VerbosityLevel

            level = get_verbosity_level(args)
            if level == VerbosityLevel.QUIET:
                # Minimal output
                return {"status": "ok"}
            elif level == VerbosityLevel.VERBOSE:
                # Include debug info
                return {"status": "ok", "_debug": {...}}
            else:
                # Normal output
                return {"status": "ok", "details": {...}}
    """
    from claude_skills.cli.sdd.verbosity import VerbosityLevel
    return getattr(args, 'verbosity_level', VerbosityLevel.NORMAL)


def is_quiet_mode(args) -> bool:
    """Check if quiet mode is active.

    Args:
        args: Parsed argparse.Namespace from command handler

    Returns:
        True if --quiet flag was specified or verbosity_level is QUIET

    Example:
        if is_quiet_mode(args):
            # Omit empty fields and reduce output
            output = prepare_output(data, args, essential_fields)
    """
    from claude_skills.cli.sdd.verbosity import VerbosityLevel
    return get_verbosity_level(args) == VerbosityLevel.QUIET


def is_verbose_mode(args) -> bool:
    """Check if verbose mode is active.

    Args:
        args: Parsed argparse.Namespace from command handler

    Returns:
        True if --verbose flag was specified or verbosity_level is VERBOSE

    Example:
        if is_verbose_mode(args):
            # Include debug information
            output['_debug'] = {'timing_ms': elapsed, 'cache_hit': True}
    """
    from claude_skills.cli.sdd.verbosity import VerbosityLevel
    return get_verbosity_level(args) == VerbosityLevel.VERBOSE


def prepare_command_output(data, args, essential_fields=None, standard_fields=None):
    """Prepare command output with verbosity filtering.

    Convenience wrapper that applies verbosity-based field filtering to command output.
    This is the recommended way for command handlers to prepare their output.

    Args:
        data: Dictionary of output data from the command
        args: Parsed argparse.Namespace from command handler
        essential_fields: Optional set of field names always included (even in QUIET)
        standard_fields: Optional set of field names included in NORMAL/VERBOSE

    Returns:
        Filtered dictionary with fields appropriate for the verbosity level

    Example:
        def list_specs_handler(args, printer):
            # Gather all data
            data = {
                'spec_id': spec_id,
                'title': title,
                'status': status,
                'progress_percentage': percentage,
                'total_tasks': total,
                'metadata': metadata  # May be empty
            }

            # Define field categories
            essential = {'spec_id', 'title', 'status', 'progress_percentage'}
            standard = essential | {'total_tasks', 'metadata'}

            # Apply verbosity filtering
            output = prepare_command_output(data, args, essential, standard)
            return output
    """
    from claude_skills.cli.sdd.output_utils import prepare_output
    return prepare_output(data, args, essential_fields, standard_fields)


def register_all_subcommands(subparsers, parent_parser):
    """
    Register all subcommands from skill modules.

    Uses lazy imports to avoid loading unnecessary modules and handles
    optional plugins gracefully (e.g., orchestration during Phase 1).

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options to inherit

    Note:
        Handlers will receive printer when invoked, not during registration.
        This allows printer to be configured after parsing global flags.
    """
    # Import register functions from each module (lazy imports for performance)
    from claude_skills.sdd_next.cli import register_next
    from claude_skills.sdd_update.cli import register_update
    from claude_skills.sdd_validate.cli import register_validate
    from claude_skills.sdd_plan.cli import register_plan
    from claude_skills.sdd_plan_review.cli import register_plan_review
    from claude_skills.sdd_pr.cli import register_pr
    from claude_skills.context_tracker.cli import register_context, register_session_marker
    from claude_skills.sdd_spec_mod.cli import register_spec_mod
    from claude_skills.common.cache.cli import register_cache
    from claude_skills.cli.sdd.work_mode import register_get_work_mode
    from claude_skills.cli.sdd.schema import register_schema
    from claude_skills.cli.sdd.llm_doc_gen_cmd import register_llm_doc_gen

    # Register core SDD subcommands
    register_next(subparsers, parent_parser)
    register_update(subparsers, parent_parser)
    register_validate(subparsers, parent_parser)
    register_plan(subparsers, parent_parser)
    register_plan_review(subparsers, parent_parser)
    register_pr(subparsers, parent_parser)
    register_context(subparsers, parent_parser)
    register_session_marker(subparsers, parent_parser)
    register_spec_mod(subparsers, parent_parser)
    register_cache(subparsers, parent_parser)
    register_get_work_mode(subparsers, parent_parser)
    register_schema(subparsers, parent_parser)
    register_llm_doc_gen(subparsers, parent_parser)

    # Register unified CLIs as SDD subcommands
    _register_doc_cli(subparsers, parent_parser)
    _register_test_cli(subparsers, parent_parser)
    _register_skills_dev_cli(subparsers, parent_parser)
    _register_optional_modules(subparsers, parent_parser)

    # Optional: register workflow orchestration (may not exist in Phase 1)
    try:
        from claude_skills.orchestration.workflows import register_workflow
        register_workflow(subparsers)
        logger.debug("Workflow orchestration registered")
    except ImportError:
        logger.debug("Workflow orchestration not available (Phase 1 scaffolding)")
        # This is fine - workflows are added in Phase 3
        pass


def _register_doc_cli(subparsers, parent_parser):
    """Register the doc CLI as an SDD subcommand."""
    from claude_skills.llm_doc_gen.analysis.cli import register_code_doc
    from claude_skills.doc_query.cli import register_doc_query

    doc_parser = subparsers.add_parser(
        'doc',
        parents=[parent_parser],
        help='Documentation generation and querying',
        description='Unified documentation generation and querying CLI'
    )
    doc_subparsers = doc_parser.add_subparsers(
        title='doc commands',
        dest='doc_command',
        required=True
    )
    register_code_doc(doc_subparsers, parent_parser)
    register_doc_query(doc_subparsers, parent_parser)


def _register_test_cli(subparsers, parent_parser):
    """Register the test CLI as an SDD subcommand."""
    from claude_skills.run_tests.cli import register_run_tests

    test_parser = subparsers.add_parser(
        'test',
        parents=[parent_parser],
        help='Testing and debugging utilities',
        description='Unified testing and debugging CLI'
    )
    test_subparsers = test_parser.add_subparsers(
        title='test commands',
        dest='test_command',
        required=True
    )
    register_run_tests(test_subparsers, parent_parser)


def _register_skills_dev_cli(subparsers, parent_parser):
    """Register the skills-dev CLI as an SDD subcommand."""
    from claude_skills.cli.skills_dev.registry import register_all_subcommands as register_skills_dev_subcommands

    skills_dev_parser = subparsers.add_parser(
        'skills-dev',
        parents=[parent_parser],
        help='Skills development utilities',
        description='Internal development utilities for claude_skills'
    )
    skills_dev_subparsers = skills_dev_parser.add_subparsers(
        title='skills-dev commands',
        dest='skills_dev_command',
        required=True
    )
    register_skills_dev_subcommands(skills_dev_subparsers, parent_parser)


def _register_optional_modules(subparsers, parent_parser) -> None:
    """Register optional CLI extensions if their modules are present."""

    for module_name, attr_name, label in _OPTIONAL_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            logger.warning("Optional module '%s' not available; skipping registration", label)
            continue
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.warning("Failed to import optional module '%s': %s", label, exc)
            continue

        register_fn: Optional[Callable] = getattr(module, attr_name, None)
        if not callable(register_fn):
            logger.warning(
                "Optional module '%s' missing callable '%s'; skipping registration",
                label,
                attr_name,
            )
            continue

        try:
            register_fn(subparsers, parent_parser)
            logger.debug("Optional module '%s' registered", label)
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.warning(
                "Optional module '%s' failed to register (%s)", label, exc
            )
