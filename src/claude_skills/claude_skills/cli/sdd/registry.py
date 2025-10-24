"""Plugin registration system for subcommands."""
import logging

logger = logging.getLogger(__name__)


def register_all_subcommands(subparsers):
    """
    Register all subcommands from skill modules.

    Uses lazy imports to avoid loading unnecessary modules and handles
    optional plugins gracefully (e.g., orchestration during Phase 1).

    Args:
        subparsers: ArgumentParser subparsers object

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

    # Register core SDD subcommands
    register_next(subparsers)
    register_update(subparsers)
    register_validate(subparsers)
    register_plan(subparsers)
    register_plan_review(subparsers)

    # Register unified CLIs as SDD subcommands
    _register_doc_cli(subparsers)
    _register_test_cli(subparsers)
    _register_skills_dev_cli(subparsers)

    # Optional: register workflow orchestration (may not exist in Phase 1)
    try:
        from claude_skills.orchestration.workflows import register_workflow
        register_workflow(subparsers)
        logger.debug("Workflow orchestration registered")
    except ImportError:
        logger.debug("Workflow orchestration not available (Phase 1 scaffolding)")
        # This is fine - workflows are added in Phase 3
        pass


def _register_doc_cli(subparsers):
    """Register the doc CLI as an SDD subcommand."""
    from claude_skills.code_doc.cli import register_code_doc
    from claude_skills.doc_query.cli import register_doc_query

    doc_parser = subparsers.add_parser(
        'doc',
        help='Documentation generation and querying',
        description='Unified documentation generation and querying CLI'
    )
    doc_subparsers = doc_parser.add_subparsers(
        title='doc commands',
        dest='doc_command',
        required=True
    )
    register_code_doc(doc_subparsers)
    register_doc_query(doc_subparsers)


def _register_test_cli(subparsers):
    """Register the test CLI as an SDD subcommand."""
    from claude_skills.run_tests.cli import register_run_tests

    test_parser = subparsers.add_parser(
        'test',
        help='Testing and debugging utilities',
        description='Unified testing and debugging CLI'
    )
    test_subparsers = test_parser.add_subparsers(
        title='test commands',
        dest='test_command',
        required=True
    )
    register_run_tests(test_subparsers)


def _register_skills_dev_cli(subparsers):
    """Register the skills-dev CLI as an SDD subcommand."""
    from claude_skills.cli.skills_dev.registry import register_all_subcommands as register_skills_dev_subcommands

    skills_dev_parser = subparsers.add_parser(
        'skills-dev',
        help='Skills development utilities',
        description='Internal development utilities for claude_skills'
    )
    skills_dev_subparsers = skills_dev_parser.add_subparsers(
        title='skills-dev commands',
        dest='skills_dev_command',
        required=True
    )
    register_skills_dev_subcommands(skills_dev_subparsers)
