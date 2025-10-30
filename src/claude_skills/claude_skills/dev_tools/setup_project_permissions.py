#!/usr/bin/env python3
"""
Setup Project Permissions Script

Configures .claude/settings.json with required SDD tool permissions.
Used by /sdd-begin command and sdd-plan skill to ensure proper permissions.
"""

import argparse
import json
import sys
from pathlib import Path


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

    # CLI command permissions
    "Bash(sdd:*)",
    "Bash(cursor-agent:*)",
    "Bash(gemini:*)",
    "Bash(codex:*)",

    # File access permissions
    "Read(//**/specs/**)",
    "Write(//**/specs/active/**)",
    "Write(//**/specs/completed/**)",
    "Write(//**/specs/archived/**)",
    "Edit(//**/specs/active/**)"
]


def update_permissions(project_root):
    """Update .claude/settings.json with SDD permissions."""
    project_path = Path(project_root).resolve()
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

    print(json.dumps(result, indent=2))

    # Human-readable output to stderr
    if new_permissions:
        print(f"\n✅ Added {len(new_permissions)} new SDD permissions to {settings_file}", file=sys.stderr)
    else:
        print(f"\n✅ All SDD permissions already configured in {settings_file}", file=sys.stderr)

    return 0


def check_permissions(project_root):
    """Check if SDD permissions are configured."""
    project_path = Path(project_root).resolve()
    settings_file = project_path / ".claude" / "settings.json"

    if not settings_file.exists():
        result = {
            "configured": False,
            "settings_file": str(settings_file),
            "exists": False,
            "message": "Settings file does not exist"
        }
        print(json.dumps(result, indent=2))
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

    print(json.dumps(result, indent=2))
    return 0 if configured else 1


def main():
    parser = argparse.ArgumentParser(description='Setup SDD Project Permissions')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # update command
    update_cmd = subparsers.add_parser('update', help='Update project settings with SDD permissions')
    update_cmd.add_argument('project_root', help='Project root directory (e.g., "." for current)')

    # check command
    check_cmd = subparsers.add_parser('check', help='Check if SDD permissions are configured')
    check_cmd.add_argument('project_root', help='Project root directory')

    args = parser.parse_args()

    if args.command == 'update':
        return update_permissions(args.project_root)
    elif args.command == 'check':
        return check_permissions(args.project_root)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
