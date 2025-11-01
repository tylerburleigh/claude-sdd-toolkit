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
    "Skill(sdd-toolkit:sdd-plan-review)",
    "Skill(sdd-toolkit:sdd-validate)",
    "Skill(sdd-toolkit:code-doc)",
    "Skill(sdd-toolkit:doc-query)",

    # Skills (short form without namespace - also needed)
    "Skill(run-tests)",
    "Skill(sdd-plan)",
    "Skill(sdd-next)",
    "Skill(sdd-update)",
    "Skill(sdd-plan-review)",
    "Skill(sdd-validate)",
    "Skill(code-doc)",
    "Skill(doc-query)",

    # Slash commands
    "SlashCommand(/sdd-begin)",

    # CLI command permissions (unified sdd CLI + legacy standalone commands)
    "Bash(sdd:*)",      # Covers: sdd doc, sdd test, sdd skills-dev, sdd <any-command>

    # AI CLI tool permissions
    "Bash(cursor-agent:*)",
    "Bash(gemini:*)",
    "Bash(codex:*)",

    # File access permissions
    "Read(//Users/tylerburleigh/.claude/skills/**)",
    "Write(//**/specs/active/**)",
    "Write(//**/specs/pending/**)",
    "Write(//**/specs/completed/**)",
    "Write(//**/specs/archived/**)",
    "Edit(//**/specs/active/**)",
    "Edit(//**/specs/pending/**)",
]


def cmd_update(args, printer: PrettyPrinter) -> int:
    """Update .claude/settings.json with SDD permissions."""
    project_path = Path(args.project_root).resolve()
    settings_file = project_path / ".claude" / "settings.json"

    # Create .claude directory if it doesn't exist
    settings_file.parent.mkdir(parents=True, exist_ok=True)

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
            printer.success(f"Added {len(new_permissions)} new SDD permissions to {settings_file}")
        else:
            printer.success(f"All SDD permissions already configured in {settings_file}")

    return 0


def cmd_check(args, printer: PrettyPrinter) -> int:
    """Check if SDD permissions are configured."""
    project_path = Path(args.project_root).resolve()
    settings_file = project_path / ".claude" / "settings.json"

    if not settings_file.exists():
        result = {
            "configured": False,
            "settings_file": str(settings_file),
            "exists": False,
            "message": "Settings file does not exist"
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            printer.error(f"Settings file does not exist: {settings_file}")
        return 1

    with open(settings_file, 'r') as f:
        settings = json.load(f)

    existing_permissions = set(settings.get("permissions", {}).get("allow", []))

    # Check if key SDD permissions are present
    required_permissions = [
        "Skill(sdd-toolkit:sdd-plan)",
        "Skill(sdd-toolkit:sdd-next)",
        "Skill(sdd-toolkit:sdd-update)",
    ]

    configured = all(perm in existing_permissions for perm in required_permissions)

    result = {
        "configured": configured,
        "settings_file": str(settings_file),
        "exists": True,
        "total_permissions": len(existing_permissions),
        "has_required": configured
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if configured:
            printer.success("SDD permissions are configured")
        else:
            printer.warning("SDD permissions need to be configured")

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
