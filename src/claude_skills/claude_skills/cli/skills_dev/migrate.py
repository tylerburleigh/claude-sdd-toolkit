"""
Migration Guidance Commands

Provides guidance for migrating from legacy commands to new unified CLI.
"""

from claude_skills.common import PrettyPrinter


MIGRATION_GUIDE = """
Migration Guide: Legacy dev_tools to Unified CLI
═══════════════════════════════════════════════════

Legacy Python scripts in dev_tools/ have been replaced with unified CLI commands.
All legacy scripts have been removed.

OLD (Removed):
─────────────────
  python3 ~/.claude/scripts/sdd_start_helper.py check-permissions
  python3 ~/.claude/scripts/sdd_start_helper.py format-output
  claude-skills-gendocs sdd-validate

NEW (Current):
──────────────
  sdd skills-dev start-helper -- check-permissions
  sdd skills-dev start-helper -- format-output
  sdd skills-dev setup-permissions -- update .
  sdd skills-dev gendocs -- sdd-validate

Command Mappings:
─────────────────
  sdd_start_helper.py  → sdd skills-dev start-helper --
  claude-skills-gendocs → sdd skills-dev gendocs --

Available Commands:
───────────────────
  sdd skills-dev start-helper -- <cmd>        Session start helpers
  sdd skills-dev setup-permissions -- <cmd>   Permission management
  sdd skills-dev gendocs -- <skill>           Documentation generation
  sdd skills-dev migrate                      This help message

Examples:
─────────
  # Check if permissions are configured
  sdd skills-dev start-helper -- check-permissions .

  # Format active work for display
  sdd skills-dev start-helper -- format-output

  # Set up SDD permissions for current project
  sdd skills-dev setup-permissions -- update .

  # Generate documentation for a skill
  sdd skills-dev gendocs -- sdd-validate

For more help:
──────────────
  sdd skills-dev start-helper -- --help
  sdd skills-dev setup-permissions -- --help
  sdd skills-dev gendocs -- --help
"""


def cmd_migrate(args, printer: PrettyPrinter) -> int:
    """Show migration guidance."""
    print(MIGRATION_GUIDE)
    return 0


def register_migrate(subparsers, parent_parser):
    """Register migrate command."""
    migrate_parser = subparsers.add_parser(
        'migrate',
        parents=[parent_parser],
        help='Show migration guidance from legacy commands',
        description='Provides guidance for migrating from legacy dev_tools commands to new unified CLI'
    )
    migrate_parser.set_defaults(func=cmd_migrate)
