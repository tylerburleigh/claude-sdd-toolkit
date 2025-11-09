#!/usr/bin/env python3
"""
Setup Project Permissions Script

Configures .claude/settings.local.json with required SDD tool permissions.
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

    # CLI command permissions
    "Bash(sdd:*)",
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
    "Edit(//**/specs/pending/**)"
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


def _prompt_for_git_permissions() -> list:
    """Prompt user about adding git/GitHub permissions.

    Returns:
        List of git permissions to add (may include read-only, write, or both)
    """
    permissions_to_add = []

    print("\n🔧 Git Integration Setup\n", file=sys.stderr)
    print("Git integration allows Claude to:", file=sys.stderr)
    print("  • View repository status and history", file=sys.stderr)
    print("  • Create branches and commits", file=sys.stderr)
    print("  • Push changes and create pull requests", file=sys.stderr)
    print("", file=sys.stderr)

    # Prompt 1: Enable git integration at all?
    while True:
        response = input("Enable git integration? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            # Add read-only permissions automatically
            print("", file=sys.stderr)
            print("✓ Adding read-only git permissions (status, log, diff, etc.)", file=sys.stderr)
            permissions_to_add.extend(GIT_READ_PERMISSIONS)
            break
        elif response in ['n', 'no']:
            print("", file=sys.stderr)
            print("⊘ Skipping git integration setup", file=sys.stderr)
            print("  You can manually add git permissions to .claude/settings.local.json later", file=sys.stderr)
            print("", file=sys.stderr)
            return permissions_to_add
        else:
            print("Please enter 'y' for yes or 'n' for no", file=sys.stderr)

    # Prompt 2: Enable write operations?
    print("", file=sys.stderr)
    print("⚠️  Git Write Operations\n", file=sys.stderr)
    print("Write operations allow Claude to:", file=sys.stderr)
    print("  • Switch branches (git checkout)", file=sys.stderr)
    print("  • Stage changes (git add)", file=sys.stderr)
    print("  • Create commits (git commit)", file=sys.stderr)
    print("  • Push to remote (git push)", file=sys.stderr)
    print("  • Create pull requests (gh pr create)", file=sys.stderr)
    print("", file=sys.stderr)
    print("RISK: These operations can modify your repository and push changes.", file=sys.stderr)
    print("Always review Claude's proposed changes before approval.", file=sys.stderr)
    print("", file=sys.stderr)

    while True:
        response = input("Enable git write operations? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            print("", file=sys.stderr)
            print("✓ Adding git write permissions", file=sys.stderr)
            permissions_to_add.extend(GIT_WRITE_PERMISSIONS)
            break
        elif response in ['n', 'no']:
            print("", file=sys.stderr)
            print("✓ Git integration enabled (read-only)", file=sys.stderr)
            print("  You can manually add write permissions later if needed", file=sys.stderr)
            break
        else:
            print("Please enter 'y' for yes or 'n' for no", file=sys.stderr)

    print("", file=sys.stderr)
    return permissions_to_add


def ensure_gitignore_pattern(project_root, pattern):
    """Add a pattern to .gitignore if not already present.

    Args:
        project_root: Root directory of the project
        pattern: Pattern to add to .gitignore (e.g., "specs/.fidelity-reviews/")

    Returns:
        Tuple of (success: bool, message: str, already_present: bool)
    """
    project_path = Path(project_root).resolve()
    gitignore_file = project_path / ".gitignore"

    try:
        # Read existing .gitignore if it exists
        if gitignore_file.exists():
            gitignore_content = gitignore_file.read_text()
            # Check if pattern already exists
            if pattern in gitignore_content:
                return True, f"Pattern already in .gitignore: {pattern}", True
        else:
            gitignore_content = ""

        # Ensure pattern ends with newline for consistency
        pattern_to_add = pattern if pattern.endswith('\n') else pattern + '\n'

        # Add pattern if not present
        if pattern not in gitignore_content:
            # Add a comment explaining the pattern
            if "SDD Toolkit" not in gitignore_content:
                new_content = gitignore_content + "\n# SDD Toolkit\n" + pattern_to_add
            else:
                # If SDD Toolkit section exists, add pattern there
                new_content = gitignore_content + pattern_to_add

            gitignore_file.write_text(new_content)
            return True, f"Added pattern to .gitignore: {pattern}", False
        else:
            return True, f"Pattern already in .gitignore: {pattern}", True

    except (OSError, PermissionError) as e:
        return False, f"Could not update .gitignore: {e}", False


def update_permissions(project_root):
    """Update .claude/settings.local.json with SDD permissions."""
    project_path = Path(project_root).resolve()
    settings_file = project_path / ".claude" / "settings.local.json"

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

    # Prompt for git permissions (interactive setup)
    git_permissions = _prompt_for_git_permissions()

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

    # Update .gitignore to include specs/.fidelity-reviews/
    gitignore_success, gitignore_msg, already_present = ensure_gitignore_pattern(
        project_path, "specs/.fidelity-reviews/"
    )

    result = {
        "success": True,
        "settings_file": str(settings_file),
        "permissions_added": len(new_permissions),
        "total_permissions": len(settings["permissions"]["allow"]),
        "new_permissions": new_permissions,
        "gitignore": {
            "success": gitignore_success,
            "message": gitignore_msg,
            "already_present": already_present
        }
    }

    print(json.dumps(result, indent=2))

    # Human-readable output to stderr
    if new_permissions:
        print(f"\n✅ Added {len(new_permissions)} new SDD permissions to {settings_file}", file=sys.stderr)
    else:
        print(f"\n✅ All SDD permissions already configured in {settings_file}", file=sys.stderr)

    if gitignore_success:
        if already_present:
            print(f"✅ {gitignore_msg}", file=sys.stderr)
        else:
            print(f"✅ {gitignore_msg}", file=sys.stderr)
    else:
        print(f"⚠️  {gitignore_msg}", file=sys.stderr)

    return 0


def check_permissions(project_root):
    """Check if SDD permissions are configured."""
    project_path = Path(project_root).resolve()
    settings_file = project_path / ".claude" / "settings.local.json"

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
