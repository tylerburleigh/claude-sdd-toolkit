#!/usr/bin/env python3
"""
Setup Project Permissions Script

Configures `.claude/settings.local.json` with required SDD tool permissions and
bootstraps `.claude/ai_config.yaml`. This legacy utility mirrors the modern CLI
workflow while remaining available for direct invocation.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

from claude_skills.common.ai_config_setup import ensure_ai_config
from claude_skills.common.setup_templates import copy_template_to, load_json_template_clean

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
    "Skill(sdd-toolkit:sdd-fidelity-review)",
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
    "Skill(doc-query)",
    # Slash commands
    "SlashCommand(/sdd-begin)",
    # CLI command permissions (unified sdd CLI + legacy standalone commands)
    # NOTE: Bash(sdd:*) allows command chaining that could bypass Read() restrictions
    # (e.g., "sdd --version && cat specs/active/spec.json"). This is accepted as a
    # workflow trade-off. The focus is on efficiency rather than access control.
    "Bash(sdd:*)",  # Covers: sdd doc, sdd test, sdd skills-dev, sdd <any-command>
    # AI CLI tool permissions
    "Bash(cursor-agent:*)",
    "Bash(gemini:*)",
    "Bash(codex:*)",
    # Testing permissions (for run-tests skill)
    "Bash(pytest:*)",
    "Bash(python -m pytest:*)",
    "Bash(pip show:*)",  # Useful for debugging package issues
    # System utilities (commonly needed for workflows)
    "Bash(mkdir:*)",  # Creating directories
    "Bash(find:*)",  # Finding files
    "Bash(cat:*)",  # Quick file reads
    # Web search for documentation and debugging
    "WebSearch",
    # File access permissions
    "Read(//**/specs/**)",  # Reading spec files
    "Read(//tmp/**)",  # Temp file read access for testing
    "Write(//tmp/**)",  # Temp file write access for testing/debugging
    "Write(//**/specs/active/**)",
    "Write(//**/specs/pending/**)",
    "Write(//**/specs/completed/**)",
    "Write(//**/specs/archived/**)",
    "Edit(//**/specs/active/**)",
    "Edit(//**/specs/pending/**)",
]

# Git read-only permissions (safe operations)
GIT_READ_PERMISSIONS = [
    "Bash(git status:*)",
    "Bash(git log:*)",
    "Bash(git branch:*)",
    "Bash(git diff:*)",
    "Bash(git show:*)",
    "Bash(git describe:*)",
    "Bash(git rev-parse:*)",
    "Bash(git ls-tree:*)",
    "Bash(gh pr view:*)",
]

# Git write permissions (safe write operations)
GIT_WRITE_PERMISSIONS = [
    "Bash(git checkout:*)",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git mv:*)",
]

GIT_APPROVAL_PERMISSIONS = [
    "Bash(git push:*)",
    "Bash(gh pr create:*)",
    "Bash(git rm:*)",
]

# Git dangerous permissions (destructive operations requiring approval)
GIT_DANGEROUS_PERMISSIONS = [
    "Bash(git push --force:*)",
    "Bash(git push -f:*)",
    "Bash(git push --force-with-lease:*)",
    "Bash(git clean -f:*)",
    "Bash(git clean -fd:*)",
    "Bash(git clean -fx:*)",
    "Bash(git reset --hard:*)",
    "Bash(git reset --mixed:*)",
    "Bash(git reset:*)",
    "Bash(git rebase:*)",
    "Bash(git commit --amend:*)",
    "Bash(git filter-branch:*)",
    "Bash(git filter-repo:*)",
    "Bash(git branch -D:*)",
    "Bash(git push origin --delete:*)",
    "Bash(git tag -d:*)",
    "Bash(git reflog expire:*)",
    "Bash(git reflog delete:*)",
    "Bash(git stash drop:*)",
    "Bash(git stash clear:*)",
    "Bash(git gc --prune=now:*)",
]


def _prompt_for_git_permissions() -> dict[str, list[str]]:
    """Prompt user about adding git/GitHub permissions."""
    permissions: dict[str, list[str]] = {"allow": [], "ask": []}

    print("\n🔧 Git Integration Setup\n", file=sys.stderr)
    print("Git integration allows Claude to:", file=sys.stderr)
    print("  • View repository status and history", file=sys.stderr)
    print("  • Create branches and commits", file=sys.stderr)
    print("  • Push changes and create pull requests", file=sys.stderr)
    print("", file=sys.stderr)

    # Prompt 1: Enable git integration at all?
    while True:
        response = input("Enable git integration? (y/n): ").strip().lower()
        if response in {"y", "yes"}:
            print("", file=sys.stderr)
            print("✓ Adding read-only git permissions (status, log, diff, etc.)", file=sys.stderr)
            permissions["allow"].extend(GIT_READ_PERMISSIONS)
            break
        if response in {"n", "no"}:
            print("", file=sys.stderr)
            print("⊘ Skipping git integration setup", file=sys.stderr)
            print("  You can manually add git permissions to .claude/settings.local.json later", file=sys.stderr)
            print("", file=sys.stderr)
            return permissions
        print("Please enter 'y' for yes or 'n' for no", file=sys.stderr)

    # Prompt 2: Enable write operations?
    print("", file=sys.stderr)
    print("⚠️  Git Write Operations\n", file=sys.stderr)
    print("Write operations allow Claude to:", file=sys.stderr)
    print("  • Switch branches (git checkout)", file=sys.stderr)
    print("  • Stage changes (git add)", file=sys.stderr)
    print("  • Create commits (git commit)", file=sys.stderr)
    print("  • Push to remote (git push)", file=sys.stderr)
    print("  • Remove files (git rm)", file=sys.stderr)
    print("  • Create pull requests (gh pr create)", file=sys.stderr)
    print("", file=sys.stderr)
    print("RISK: These operations can modify your repository and push changes.", file=sys.stderr)
    print("Always review Claude's proposed changes before approval.", file=sys.stderr)
    print("", file=sys.stderr)

    while True:
        response = input("Enable git write operations? (y/n): ").strip().lower()
        if response in {"y", "yes"}:
            print("", file=sys.stderr)
            print("✓ Adding git write permissions (local operations)", file=sys.stderr)
            permissions["allow"].extend(GIT_WRITE_PERMISSIONS)
            print("✓ Adding approval-only git operations to ASK list (requires approval)", file=sys.stderr)
            permissions["ask"].extend(GIT_APPROVAL_PERMISSIONS)
            print("✓ Adding dangerous git operations to ASK list (requires approval)", file=sys.stderr)
            permissions["ask"].extend(GIT_DANGEROUS_PERMISSIONS)
            break
        if response in {"n", "no"}:
            print("", file=sys.stderr)
            print("✓ Git integration enabled (read-only)", file=sys.stderr)
            print("  You can manually add write permissions later if needed", file=sys.stderr)
            break
        print("Please enter 'y' for yes or 'n' for no", file=sys.stderr)

    print("", file=sys.stderr)
    return permissions


def ensure_gitignore_pattern(project_root: Path | str, pattern: str) -> tuple[bool, str, bool]:
    """Add a pattern to .gitignore if not already present."""
    project_path = Path(project_root).resolve()
    gitignore_file = project_path / ".gitignore"

    try:
        if gitignore_file.exists():
            gitignore_content = gitignore_file.read_text()
            if pattern in gitignore_content:
                return True, f"Pattern already in .gitignore: {pattern}", True
        else:
            gitignore_content = ""

        pattern_to_add = pattern if pattern.endswith("\n") else f"{pattern}\n"

        if pattern not in gitignore_content:
            if "SDD Toolkit" not in gitignore_content:
                new_content = f"{gitignore_content}\n# SDD Toolkit\n{pattern_to_add}"
            else:
                new_content = f"{gitignore_content}{pattern_to_add}"

            gitignore_file.write_text(new_content)
            return True, f"Added pattern to .gitignore: {pattern}", False

        return True, f"Pattern already in .gitignore: {pattern}", True
    except (OSError, PermissionError) as exc:
        return False, f"Could not update .gitignore: {exc}", False


def update_permissions(project_root: Path | str) -> int:
    """Update `.claude/settings.local.json` with SDD permissions."""
    project_path = Path(project_root).resolve()
    settings_file = project_path / ".claude" / "settings.local.json"
    config_file = project_path / ".claude" / "sdd_config.json"

    settings_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        copy_template_to("sdd_config.json", config_file)

    if settings_file.exists():
        with settings_file.open(encoding="utf-8") as file:
            settings = json.load(file)
    else:
        settings = deepcopy(load_json_template_clean("settings.local.json"))

    if not isinstance(settings, dict):
        settings = {}

    permissions = settings.setdefault("permissions", {})
    permissions.setdefault("allow", [])
    permissions.setdefault("deny", [])
    permissions.setdefault("ask", [])

    existing_allow = set(permissions["allow"])
    existing_ask = set(permissions["ask"])
    new_permissions: list[str] = []
    new_ask_permissions: list[str] = []

    for perm in SDD_PERMISSIONS:
        if perm not in existing_allow:
            permissions["allow"].append(perm)
            new_permissions.append(perm)
            existing_allow.add(perm)

    git_permissions = _prompt_for_git_permissions()

    for perm in git_permissions["allow"]:
        if perm not in existing_allow:
            permissions["allow"].append(perm)
            new_permissions.append(perm)
            existing_allow.add(perm)

    for perm in git_permissions["ask"]:
        if perm not in existing_ask:
            permissions["ask"].append(perm)
            new_ask_permissions.append(perm)
            existing_ask.add(perm)

    with settings_file.open("w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)
        file.write("\n")

    gitignore_success, gitignore_msg, already_present = ensure_gitignore_pattern(
        project_path, "specs/.fidelity-reviews/"
    )

    ai_config_result = ensure_ai_config(project_path)

    result = {
        "success": True,
        "settings_file": str(settings_file),
        "permissions_added": len(new_permissions),
        "ask_permissions_added": len(new_ask_permissions),
        "total_allow_permissions": len(permissions["allow"]),
        "total_ask_permissions": len(permissions["ask"]),
        "new_permissions": new_permissions,
        "new_ask_permissions": new_ask_permissions,
        "gitignore": {
            "success": gitignore_success,
            "message": gitignore_msg,
            "already_present": already_present,
        },
        "ai_config": ai_config_result.to_dict(),
    }

    print(json.dumps(result, indent=2))

    if new_permissions or new_ask_permissions:
        print(
            f"\n✅ Added {len(new_permissions)} ALLOW and {len(new_ask_permissions)} ASK permissions in {settings_file}",
            file=sys.stderr,
        )
    else:
        print(f"\n✅ All SDD permissions already configured in {settings_file}", file=sys.stderr)

    if gitignore_success:
        print(f"✅ {gitignore_msg}", file=sys.stderr)
    else:
        print(f"⚠️  {gitignore_msg}", file=sys.stderr)

    if ai_config_result.success:
        print(f"✅ {ai_config_result.message}", file=sys.stderr)
        if ai_config_result.created:
            print(
                "   Tip: Adjust per-skill model priorities under `.claude/ai_config.yaml` "
                "or use CLI overrides like `--model gemini=pro` during consultations.",
                file=sys.stderr,
            )
    else:
        print(f"⚠️  {ai_config_result.message}", file=sys.stderr)

    return 0


def check_permissions(project_root: Path | str) -> int:
    """Check if SDD permissions are configured."""
    project_path = Path(project_root).resolve()
    settings_file = project_path / ".claude" / "settings.local.json"

    if not settings_file.exists():
        result = {
            "configured": False,
            "settings_file": str(settings_file),
            "exists": False,
            "message": "Settings file does not exist",
        }
        print(json.dumps(result, indent=2))
        return 1

    with settings_file.open(encoding="utf-8") as file:
        settings = json.load(file)

    existing_permissions = set(settings.get("permissions", {}).get("allow", []))

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
        "has_required": configured,
    }

    print(json.dumps(result, indent=2))
    return 0 if configured else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup SDD Project Permissions")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    update_cmd = subparsers.add_parser("update", help="Update project settings with SDD permissions")
    update_cmd.add_argument("project_root", help='Project root directory (e.g., "." for current)')

    check_cmd = subparsers.add_parser("check", help="Check if SDD permissions are configured")
    check_cmd.add_argument("project_root", help="Project root directory")

    args = parser.parse_args()

    if args.command == "update":
        return update_permissions(args.project_root)
    if args.command == "check":
        return check_permissions(args.project_root)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
