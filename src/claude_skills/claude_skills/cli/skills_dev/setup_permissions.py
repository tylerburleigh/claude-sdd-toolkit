"""
Setup Project Permissions Commands

Configures .claude/settings.json with required SDD tool permissions.
Used by /sdd-begin command and sdd-plan skill to ensure proper permissions.
"""

import json
import sys
from pathlib import Path

from claude_skills.common import PrettyPrinter


# Standard SDD permissions to add
SDD_PERMISSIONS = [
    # Skills (fully qualified with plugin namespace)
    "Skill(sdd-toolkit:run-tests)",
    "Skill(sdd-toolkit:sdd-plan)",
    "Skill(sdd-toolkit:sdd-next)",
    "Skill(sdd-toolkit:sdd-update)",
    "Skill(sdd-toolkit:sdd-pr)",
    "Skill(sdd-toolkit:sdd-plan-review)",
    "Skill(sdd-toolkit:sdd-validate)",
    "Skill(sdd-toolkit:sdd-render)",
    "Skill(sdd-toolkit:code-doc)",
    "Skill(sdd-toolkit:doc-query)",

    # Skills (short form without namespace - also needed)
    "Skill(run-tests)",
    "Skill(sdd-plan)",
    "Skill(sdd-next)",
    "Skill(sdd-update)",
    "Skill(sdd-pr)",
    "Skill(sdd-plan-review)",
    "Skill(sdd-validate)",
    "Skill(sdd-render)",
    "Skill(code-doc)",
    "Skill(doc-query)",

    # Slash commands
    "SlashCommand(/sdd-begin)",

    # CLI command permissions (unified sdd CLI + legacy standalone commands)
    # NOTE: Bash(sdd:*) allows command chaining that could bypass Read() restrictions
    # (e.g., "sdd --version && cat specs/active/spec.json"). This is accepted as a
    # workflow trade-off. Protection against reading spec files is guidance-based
    # (skills are instructed to use sdd tools exclusively) rather than security-based.
    # The focus is on efficiency (avoiding context waste) rather than access control.
    "Bash(sdd:*)",      # Covers: sdd doc, sdd test, sdd skills-dev, sdd <any-command>

    # AI CLI tool permissions
    "Bash(cursor-agent:*)",
    "Bash(gemini:*)",
    "Bash(codex:*)",

    # Note: Git/GitHub CLI permissions can be optionally configured during setup.
    # See GIT_READ_PERMISSIONS and GIT_WRITE_PERMISSIONS below for available options.

    # File access permissions
    "Write(//**/specs/active/**)",
    "Write(//**/specs/pending/**)",
    "Write(//**/specs/completed/**)",
    "Write(//**/specs/archived/**)",
    "Edit(//**/specs/active/**)",
    "Edit(//**/specs/pending/**)",
]

# Git read-only permissions (safe operations)
# These allow Claude to inspect repository state without making changes
GIT_READ_PERMISSIONS = [
    "Bash(git status:*)",
    "Bash(git log:*)",
    "Bash(git branch:*)",
    "Bash(git diff:*)",
    "Bash(git rev-parse:*)",
    "Bash(git show:*)",
    "Bash(git describe:*)",
    "Bash(gh pr view:*)",
]

# Git write permissions (potentially destructive operations)
# ⚠️ These allow Claude to modify repository state and push changes
GIT_WRITE_PERMISSIONS = [
    "Bash(git checkout:*)",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git push:*)",
    "Bash(git rm:*)",
    "Bash(gh pr create:*)",
]


def _prompt_for_config(printer: PrettyPrinter) -> dict:
    """Prompt user for SDD configuration preferences.

    Returns:
        Dict with user's configuration preferences
    """
    printer.info("📋 SDD CLI Configuration Setup")
    printer.info("")
    printer.info("Let's configure your default output preferences for SDD commands.")
    printer.info("")

    # Prompt for JSON output preference
    printer.info("Output Format:")
    printer.info("  • JSON: Machine-readable format (good for automation)")
    printer.info("  • Human-readable: Easy-to-read terminal output")
    printer.info("")

    while True:
        json_pref = input("Default to JSON output? [Y/n]: ").strip().lower()
        if json_pref in ['', 'y', 'yes']:
            use_json = True
            break
        elif json_pref in ['n', 'no']:
            use_json = False
            break
        else:
            printer.warning("Please enter 'y' for yes or 'n' for no")

    # Only ask about compact if JSON is enabled
    use_compact = True  # default
    if use_json:
        printer.info("")
        printer.info("JSON Formatting:")
        printer.info("  • Compact: Single-line JSON (smaller output)")
        printer.info("  • Pretty: Multi-line JSON (more readable)")
        printer.info("")

        while True:
            compact_pref = input("Use compact JSON formatting? [Y/n]: ").strip().lower()
            if compact_pref in ['', 'y', 'yes']:
                use_compact = True
                break
            elif compact_pref in ['n', 'no']:
                use_compact = False
                break
            else:
                printer.warning("Please enter 'y' for yes or 'n' for no")

    return {
        "output": {
            "json": use_json,
            "compact": use_compact
        }
    }


def _create_config_file(project_path: Path, config: dict, printer: PrettyPrinter) -> bool:
    """Create .claude/sdd_config.json with user preferences.

    Args:
        project_path: Project root directory
        config: Configuration dict to write
        printer: PrettyPrinter instance

    Returns:
        True if config was created successfully, False otherwise
    """
    config_file = project_path / ".claude" / "sdd_config.json"

    try:
        # Create .claude directory if needed
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write config file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            f.write('\n')  # Add trailing newline

        printer.success(f"✅ Created configuration file: {config_file}")
        printer.info("")
        printer.info("Your preferences:")
        printer.info(f"  • JSON output: {'enabled' if config['output']['json'] else 'disabled'}")
        if config['output']['json']:
            printer.info(f"  • JSON format: {'compact' if config['output']['compact'] else 'pretty-printed'}")
        printer.info("")

        return True

    except (IOError, OSError) as e:
        printer.error(f"❌ Failed to create config file: {e}")
        return False


def _prompt_for_git_permissions(printer: PrettyPrinter) -> list:
    """Prompt user about adding git/GitHub permissions.

    Returns:
        List of git permissions to add (may include read-only, write, or both)
    """
    permissions_to_add = []

    printer.info("")
    printer.info("🔧 Git Integration Setup")
    printer.info("")
    printer.info("Git integration allows Claude to:")
    printer.info("  • View repository status and history")
    printer.info("  • Create branches and commits")
    printer.info("  • Push changes and create pull requests")
    printer.info("")

    # Prompt 1: Enable git integration at all?
    while True:
        response = input("Enable git integration? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            # Add read-only permissions automatically
            printer.info("")
            printer.info("✓ Adding read-only git permissions (status, log, diff, etc.)")
            permissions_to_add.extend(GIT_READ_PERMISSIONS)
            break
        elif response in ['n', 'no']:
            printer.info("")
            printer.info("⊘ Skipping git integration setup")
            printer.info("  You can manually add git permissions to .claude/settings.json later")
            printer.info("")
            return permissions_to_add
        else:
            printer.warning("Please enter 'y' for yes or 'n' for no")

    # Prompt 2: Enable write operations?
    printer.info("")
    printer.info("⚠️  Git Write Operations")
    printer.info("")
    printer.info("Write operations allow Claude to:")
    printer.info("  • Switch branches (git checkout)")
    printer.info("  • Stage changes (git add)")
    printer.info("  • Create commits (git commit)")
    printer.info("  • Push to remote (git push)")
    printer.info("  • Create pull requests (gh pr create)")
    printer.info("")
    printer.warning("RISK: These operations can modify your repository and push changes.")
    printer.warning("Always review Claude's proposed changes before approval.")
    printer.info("")

    while True:
        response = input("Enable git write operations? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            printer.info("")
            printer.info("✓ Adding git write permissions")
            permissions_to_add.extend(GIT_WRITE_PERMISSIONS)
            break
        elif response in ['n', 'no']:
            printer.info("")
            printer.info("✓ Git integration enabled (read-only)")
            printer.info("  You can manually add write permissions later if needed")
            break
        else:
            printer.warning("Please enter 'y' for yes or 'n' for no")

    printer.info("")
    return permissions_to_add


def cmd_update(args, printer: PrettyPrinter) -> int:
    """Update .claude/settings.json with SDD permissions."""
    project_path = Path(args.project_root).resolve()
    settings_file = project_path / ".claude" / "settings.json"

    # Create .claude directory if it doesn't exist
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if sdd_config.json already exists
    config_file = project_path / ".claude" / "sdd_config.json"
    config_exists = config_file.exists()

    # Prompt for configuration if not in JSON mode and config doesn't exist
    if not args.json and not config_exists:
        printer.info("")
        config = _prompt_for_config(printer)
        _create_config_file(project_path, config, printer)

    # Load existing settings or create new
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    else:
        settings = {
            "$schema": "https://json.schemastore.org/claude-code-settings.json",
            "permissions": {
                "allow": [],
                "deny": [],
                "ask": []
            }
        }

    # Ensure permissions structure exists
    if "permissions" not in settings:
        settings["permissions"] = {"allow": [], "deny": [], "ask": []}
    if "allow" not in settings["permissions"]:
        settings["permissions"]["allow"] = []

    # Add SDD permissions (avoid duplicates)
    existing_permissions = set(settings["permissions"]["allow"])
    new_permissions = []

    for perm in SDD_PERMISSIONS:
        if perm not in existing_permissions:
            new_permissions.append(perm)
            settings["permissions"]["allow"].append(perm)

    # Show what's being added (if not in JSON mode)
    if not args.json and new_permissions:
        printer.info(f"Adding {len(new_permissions)} permissions:")
        # Show first 5 permissions
        for perm in new_permissions[:5]:
            printer.info(f"  • {perm}")
        if len(new_permissions) > 5:
            printer.info(f"  ... and {len(new_permissions) - 5} more")
        printer.info("")

    # Prompt for git permissions (if not in JSON mode)
    if not args.json:
        git_permissions = _prompt_for_git_permissions(printer)

        # Add git permissions (avoid duplicates)
        for perm in git_permissions:
            if perm not in existing_permissions:
                new_permissions.append(perm)
                settings["permissions"]["allow"].append(perm)
                existing_permissions.add(perm)

    # Write updated settings
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')  # Add trailing newline

    result = {
        "success": True,
        "settings_file": str(settings_file),
        "permissions_added": len(new_permissions),
        "total_permissions": len(settings["permissions"]["allow"]),
        "new_permissions": new_permissions
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if new_permissions:
            printer.success(f"✅ Added {len(new_permissions)} new SDD permissions to {settings_file}")
        else:
            printer.success(f"✅ All SDD permissions already configured in {settings_file}")

    return 0


def categorize_missing_permissions(missing: list) -> dict:
    """Categorize missing permissions by type for better reporting."""
    categories = {
        "skills": [],
        "commands": [],
        "bash": [],
        "file_access": []
    }

    for perm in missing:
        if perm.startswith("Skill("):
            categories["skills"].append(perm)
        elif perm.startswith("SlashCommand("):
            categories["commands"].append(perm)
        elif perm.startswith("Bash("):
            categories["bash"].append(perm)
        elif perm.startswith(("Read(", "Write(", "Edit(")):
            categories["file_access"].append(perm)

    return categories


def cmd_check(args, printer: PrettyPrinter) -> int:
    """Check if SDD permissions are configured."""
    project_path = Path(args.project_root).resolve()
    settings_file = project_path / ".claude" / "settings.json"

    if not settings_file.exists():
        result = {
            "configured": False,
            "status": "not_configured",
            "settings_file": str(settings_file),
            "exists": False,
            "total_required": len(SDD_PERMISSIONS),
            "total_present": 0,
            "total_missing": len(SDD_PERMISSIONS),
            "message": "Settings file does not exist"
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            printer.error(f"Settings file does not exist: {settings_file}")
            printer.info(f"Missing all {len(SDD_PERMISSIONS)} SDD permissions")
        return 1

    with open(settings_file, 'r') as f:
        settings = json.load(f)

    existing_permissions = set(settings.get("permissions", {}).get("allow", []))

    # Check which permissions are present and which are missing
    present = []
    missing = []

    for perm in SDD_PERMISSIONS:
        if perm in existing_permissions:
            present.append(perm)
        else:
            missing.append(perm)

    # Determine configuration status
    total_required = len(SDD_PERMISSIONS)
    total_present = len(present)
    total_missing = len(missing)

    # Define core permissions needed for basic functionality
    core_permissions = [
        "Skill(sdd-toolkit:sdd-plan)",
        "Skill(sdd-toolkit:sdd-next)",
        "Skill(sdd-toolkit:sdd-update)",
    ]
    has_core = all(perm in existing_permissions for perm in core_permissions)

    if total_missing == 0:
        status = "fully_configured"
        configured = True
    elif has_core and total_present >= 3:
        status = "partially_configured"
        configured = False
    else:
        status = "not_configured"
        configured = False

    # Categorize missing permissions
    missing_by_category = categorize_missing_permissions(missing)

    result = {
        "configured": configured,
        "status": status,
        "settings_file": str(settings_file),
        "exists": True,
        "total_required": total_required,
        "total_present": total_present,
        "total_missing": total_missing,
        "missing_permissions": missing,
        "missing_by_category": missing_by_category
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if status == "fully_configured":
            printer.success(f"SDD permissions are fully configured ({total_present}/{total_required})")
        elif status == "partially_configured":
            printer.warning(f"SDD permissions are partially configured ({total_present}/{total_required})")
            printer.info("")
            printer.info(f"Missing {total_missing} permissions:")

            # Show categorized missing permissions
            if missing_by_category["skills"]:
                count = len(missing_by_category["skills"])
                printer.info(f"  • {count} skill permission{'s' if count != 1 else ''}")
            if missing_by_category["bash"]:
                count = len(missing_by_category["bash"])
                printer.info(f"  • {count} bash/git permission{'s' if count != 1 else ''}")
            if missing_by_category["commands"]:
                count = len(missing_by_category["commands"])
                printer.info(f"  • {count} slash command{'s' if count != 1 else ''}")
            if missing_by_category["file_access"]:
                count = len(missing_by_category["file_access"])
                printer.info(f"  • {count} file access permission{'s' if count != 1 else ''}")

            printer.info("")
            printer.info("Run 'sdd skills-dev setup-permissions update .' to add missing permissions")
        else:
            printer.error(f"SDD permissions not configured ({total_present}/{total_required})")
            printer.info("Run 'sdd skills-dev setup-permissions update .' to configure")

    return 0 if configured else 1


def register_setup_permissions(subparsers, parent_parser):
    """Register setup-permissions subcommands."""
    # Create setup-permissions parser
    setup_perms_parser = subparsers.add_parser(
        'setup-permissions',
        parents=[parent_parser],
        help='Configure SDD project permissions',
        description='Configure .claude/settings.json with required SDD tool permissions'
    )

    # Create subparsers for setup-permissions commands
    setup_perms_subparsers = setup_perms_parser.add_subparsers(
        title='setup-permissions commands',
        dest='setup_permissions_command',
        required=True
    )

    # update command
    update_cmd = setup_perms_subparsers.add_parser(
        'update',
        parents=[parent_parser],
        help='Update project settings with SDD permissions'
    )
    update_cmd.add_argument('project_root', help='Project root directory (e.g., "." for current)')
    update_cmd.set_defaults(func=cmd_update)

    # check command
    check_cmd = setup_perms_subparsers.add_parser(
        'check',
        parents=[parent_parser],
        help='Check if SDD permissions are configured'
    )
    check_cmd.add_argument('project_root', help='Project root directory')
    check_cmd.set_defaults(func=cmd_check)
