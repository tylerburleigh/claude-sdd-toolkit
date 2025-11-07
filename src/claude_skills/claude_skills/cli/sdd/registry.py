"""Plugin registration system for subcommands."""
import logging

logger = logging.getLogger(__name__)


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
    from claude_skills.sdd_render.cli import register_render
    from claude_skills.sdd_pr.cli import register_pr
    from claude_skills.context_tracker.cli import register_context, register_session_marker
    from claude_skills.sdd_fidelity_review.cli import register_commands as register_fidelity_review
    from claude_skills.sdd_spec_mod.cli import register_spec_mod
    from claude_skills.common.cache.cli import register_cache

    # Register core SDD subcommands
    register_next(subparsers, parent_parser)
    register_update(subparsers, parent_parser)
    register_validate(subparsers, parent_parser)
    register_plan(subparsers, parent_parser)
    register_plan_review(subparsers, parent_parser)
    register_render(subparsers, parent_parser)
    register_pr(subparsers, parent_parser)
    register_context(subparsers, parent_parser)
    register_session_marker(subparsers, parent_parser)
    register_fidelity_review(subparsers, parent_parser)
    register_spec_mod(subparsers, parent_parser)
    register_cache(subparsers, parent_parser)

    # Register unified CLIs as SDD subcommands
    _register_doc_cli(subparsers, parent_parser)
    _register_test_cli(subparsers, parent_parser)
    _register_skills_dev_cli(subparsers, parent_parser)

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
    from claude_skills.code_doc.cli import register_code_doc
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
