"""
Setup Project Permissions Commands

Configures .claude/settings.local.json with required SDD tool permissions.
Used by /sdd-begin command and sdd-plan skill to ensure proper permissions.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from claude_skills.common import PrettyPrinter
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
    "Skill(sdd-toolkit:llm-doc-gen)",
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
    "Skill(llm-doc-gen)",
    "Skill(doc-query)",
    # Slash commands
    "SlashCommand(/sdd-begin)",
    # CLI command permissions (unified sdd CLI + legacy standalone commands)
    # NOTE: Bash(sdd:*) allows command chaining that could bypass Read() restrictions
    # (e.g., "sdd --version && cat specs/active/spec.json"). This is accepted as a
    # workflow trade-off. Protection against reading spec files is guidance-based
    # (skills are instructed to use sdd tools exclusively) rather than security-based.
    # The focus is on efficiency (avoiding context waste) rather than access control.
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
    # Note: Git/GitHub CLI permissions can be optionally configured during setup.
    # See GIT_READ_PERMISSIONS and GIT_WRITE_PERMISSIONS below for available options.
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
# These allow Claude to inspect repository state without making changes
GIT_READ_PERMISSIONS = [
    "Bash(git status:*)",
    "Bash(git log:*)",
    "Bash(git branch:*)",
    "Bash(git diff:*)",
    "Bash(git show:*)",
    "Bash(git describe:*)",
    "Bash(git rev-parse:*)",
    "Bash(git ls-tree:*)",  # Inspect tree objects
    "Bash(gh pr view:*)",
]

# Git write permissions (safe write operations)
# These allow Claude to modify repository state with standard workflows
GIT_WRITE_PERMISSIONS = [
    "Bash(git checkout:*)",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git mv:*)",
]

# Git operations allowed only with explicit approval, even when write access is enabled
GIT_APPROVAL_PERMISSIONS = [
    "Bash(git push:*)",
    "Bash(gh pr create:*)",
    "Bash(git rm:*)",
]

# Git dangerous permissions (destructive operations requiring user approval)
# ⚠️ These operations can cause data loss or rewrite history
# Automatically added to ASK list when git write is enabled
GIT_DANGEROUS_PERMISSIONS = [
    # Force operations (can overwrite remote history or delete local files)
    "Bash(git push --force:*)",
    "Bash(git push -f:*)",
    "Bash(git push --force-with-lease:*)",
    "Bash(git clean -f:*)",
    "Bash(git clean -fd:*)",
    "Bash(git clean -fx:*)",
    # History rewriting operations (can lose commits or changes)
    "Bash(git reset --hard:*)",
    "Bash(git reset --mixed:*)",
    "Bash(git reset:*)",  # Covers all reset modes (defaults to --mixed)
    "Bash(git rebase:*)",
    "Bash(git commit --amend:*)",
    "Bash(git filter-branch:*)",
    "Bash(git filter-repo:*)",
    # Deletion operations (can remove branches or tags)
    "Bash(git branch -D:*)",
    "Bash(git push origin --delete:*)",
    "Bash(git tag -d:*)",
    # Reflog and stash operations (can lose commit references)
    "Bash(git reflog expire:*)",
    "Bash(git reflog delete:*)",
    "Bash(git stash drop:*)",
    "Bash(git stash clear:*)",
    # Aggressive garbage collection
    "Bash(git gc --prune=now:*)",
]


def _strip_git_permissions(settings: dict) -> None:
    """Remove bundled git permissions from template-derived settings."""

    permissions = settings.get("permissions", {})
    allow_list = permissions.get("allow", [])
    ask_list = permissions.get("ask", [])

    git_allow = set(GIT_READ_PERMISSIONS + GIT_WRITE_PERMISSIONS)
    git_ask = set(GIT_DANGEROUS_PERMISSIONS + GIT_APPROVAL_PERMISSIONS)

    if isinstance(allow_list, list):
        permissions["allow"] = [perm for perm in allow_list if perm not in git_allow]
    if isinstance(ask_list, list):
        permissions["ask"] = [perm for perm in ask_list if perm not in git_ask]


def _prompt_for_config(printer: PrettyPrinter) -> dict:
    """Prompt user for SDD configuration preferences.

    Returns:
        Dict with user's configuration preferences
    """
    printer.info("📋 SDD CLI Configuration Setup")
    printer.info("")
    printer.info("Let's configure your default output preferences for SDD commands.")
    printer.info("")

    # Prompt for output mode preference with benchmark data
    printer.info("Output Format Options:")
    printer.info("  • json:     Machine-readable format (RECOMMENDED)")
    printer.info("              ⚡ 76% more efficient for AI agents (859 vs 3,601 tokens avg)")
    printer.info("              📊 Best for: Claude Code, automation, LLM consumption")
    printer.info("")
    printer.info("  • text:     Rich TUI with colors, tables, and progress bars")
    printer.info("              📺 Best for: Human reading, interactive terminals")
    printer.info("")
    printer.info("  • markdown: Human-readable markdown output")
    printer.info("              📝 Best for: Documentation, reports")
    printer.info("")

    while True:
        mode_pref = input("Default output mode? [json/text/markdown] (default: json): ").strip().lower()
        if mode_pref in ["", "j", "json"]:
            default_mode = "json"
            break
        if mode_pref in ["t", "text"]:
            default_mode = "text"
            break
        if mode_pref in ["m", "md", "markdown"]:
            default_mode = "markdown"
            break
        printer.warning("Please enter 'json', 'text', or 'markdown'")

    # Only ask about compact if JSON is enabled
    use_compact = True  # default
    if default_mode == "json":
        printer.info("")
        printer.info("JSON Formatting:")
        printer.info("  • Compact: Single-line JSON (smaller output, recommended)")
        printer.info("  • Pretty:  Multi-line JSON (more readable)")
        printer.info("")

        while True:
            compact_pref = input("Use compact JSON formatting? [Y/n]: ").strip().lower()
            if compact_pref in ["", "y", "yes"]:
                use_compact = True
                break
            if compact_pref in ["n", "no"]:
                use_compact = False
                break
            printer.warning("Please enter 'y' for yes or 'n' for no")

    return {
        "output": {
            "default_mode": default_mode,
            "json_compact": use_compact,
        }
    }


def _create_config_file(project_path: Path, config: dict, printer: PrettyPrinter) -> bool:
    """Create .claude/sdd_config.json with user preferences."""
    config_file = project_path / ".claude" / "sdd_config.json"

    try:
        # Create .claude directory if needed
        config_file.parent.mkdir(parents=True, exist_ok=True)

        base_config = deepcopy(load_json_template_clean("sdd_config.json"))
        output_config = base_config.setdefault("output", {})
        user_output = config.get("output", {})

        default_mode = user_output.get("default_mode")
        if default_mode:
            output_config["default_mode"] = default_mode
            # Maintain compatibility: json flag reflects whether json output is enabled
            output_config["json"] = default_mode == "json"

        json_compact = user_output.get("json_compact")
        if json_compact is not None:
            output_config["json_compact"] = json_compact
            # Older configs used 'compact'; keep in sync if template still exposes it
            if "compact" in output_config:
                output_config["compact"] = json_compact

        with config_file.open("w", encoding="utf-8") as f:
            json.dump(base_config, f, indent=2)
            f.write("\n")

        printer.success(f"✅ Created configuration file: {config_file}")
        printer.info("")
        printer.info("Your preferences:")
        printer.info(f"  • Default output mode: {output_config.get('default_mode', 'text')}")
        if output_config.get("default_mode") == "json":
            printer.info(
                f"  • JSON format: {'compact' if output_config.get('json_compact', True) else 'pretty-printed'}"
            )
        printer.info("")

        return True
    except (IOError, OSError, ValueError) as exc:
        printer.error(f"❌ Failed to create config file: {exc}")
        return False


def _prompt_for_git_permissions(printer: PrettyPrinter) -> dict:
    """Prompt user about adding git/GitHub permissions."""
    permissions = {"allow": [], "ask": []}

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
        if response in ["y", "yes"]:
            # Add read-only permissions automatically
            printer.info("")
            printer.info("✓ Adding read-only git permissions (status, log, diff, etc.)")
            permissions["allow"].extend(GIT_READ_PERMISSIONS)
            break
        if response in ["n", "no"]:
            printer.info("")
            printer.info("⊘ Skipping git integration setup")
            printer.info("  You can manually add git permissions to .claude/settings.local.json later")
            printer.info("")
            return permissions
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
    printer.info("  • Remove files (git rm)")
    printer.info("  • Create pull requests (gh pr create)")
    printer.info("")
    printer.warning("RISK: These operations can modify your repository and push changes.")
    printer.warning("Always review Claude's proposed changes before approval.")
    printer.info("")

    while True:
        response = input("Enable git write operations? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            printer.info("")
            printer.info("✓ Adding git write permissions (local operations)")
            permissions["allow"].extend(GIT_WRITE_PERMISSIONS)

            # Automatically add approval-required operations to ASK list
            printer.info("✓ Adding approval-only git operations to ASK list (requires approval)")
            permissions["ask"].extend(GIT_APPROVAL_PERMISSIONS)

            printer.info("✓ Adding dangerous git operations to ASK list (requires approval)")
            printer.info("")
            printer.info("  Dangerous operations requiring approval:")
            printer.info("    • Force push (git push --force)")
            printer.info("    • Hard reset (git reset --hard)")
            printer.info("    • Rebase operations (git rebase)")
            printer.info("    • History rewriting (git commit --amend)")
            printer.info("    • Force deletion (git branch -D, git clean -f)")
            printer.info("")
            permissions["ask"].extend(GIT_DANGEROUS_PERMISSIONS)
            break
        if response in ["n", "no"]:
            printer.info("")
            printer.info("✓ Git integration enabled (read-only)")
            printer.info("  You can manually add write permissions later if needed")
            break
        printer.warning("Please enter 'y' for yes or 'n' for no")

    printer.info("")
    return permissions


def cmd_update(args, printer: PrettyPrinter) -> int:
    """Update .claude/settings.local.json with SDD permissions."""
    import sys

    project_path = Path(args.project_root).resolve()
    settings_file = project_path / ".claude" / "settings.local.json"

    # Create .claude directory if it doesn't exist
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    # Detect non-interactive mode
    non_interactive = getattr(args, "non_interactive", False) or not sys.stdin.isatty()

    # Note: sdd_config.json creation is now delegated to 'sdd skills-dev start-helper ensure-sdd-config'
    # This keeps setup-permissions focused solely on permission management

    # Load existing settings or start from the packaged template
    settings_existed = settings_file.exists()
    if settings_existed:
        with settings_file.open(encoding="utf-8") as f:
            settings = json.load(f)
    else:
        settings = deepcopy(load_json_template_clean("settings.local.json"))
        # Respect the upcoming git prompt by removing bundled git permissions.
        _strip_git_permissions(settings)

    # Ensure permissions structure exists
    permissions = settings.setdefault("permissions", {})
    permissions.setdefault("allow", [])
    permissions.setdefault("deny", [])
    permissions.setdefault("ask", [])

    # Track existing permissions across both allow and ask lists
    existing_allow = set(permissions["allow"])
    existing_ask = set(permissions["ask"])
    new_permissions: list[str] = []
    new_ask_permissions: list[str] = []

    # Add SDD permissions (avoid duplicates)
    for perm in SDD_PERMISSIONS:
        if perm not in existing_allow:
            new_permissions.append(perm)
            permissions["allow"].append(perm)
            existing_allow.add(perm)

    # Show what's being added (if not in JSON mode)
    if not args.json and new_permissions:
        printer.info(f"Adding {len(new_permissions)} permissions:")
        for perm in new_permissions[:5]:
            printer.info(f"  • {perm}")
        if len(new_permissions) > 5:
            printer.info(f"  ... and {len(new_permissions) - 5} more")
        printer.info("")

    # Handle git permissions based on mode
    if non_interactive:
        # Non-interactive mode: use CLI parameters
        enable_git = getattr(args, "enable_git", None)
        git_write = getattr(args, "git_write", None)

        if enable_git:
            # Add git read permissions
            git_permissions = {"allow": list(GIT_READ_PERMISSIONS), "ask": []}

            if git_write:
                # Add git write permissions to allow list
                git_permissions["allow"].extend(GIT_WRITE_PERMISSIONS)
                # Add approval-required and dangerous operations to ask list
                git_permissions["ask"].extend(GIT_APPROVAL_PERMISSIONS)
                git_permissions["ask"].extend(GIT_DANGEROUS_PERMISSIONS)

                if not args.json:
                    printer.info("✓ Git integration enabled with write permissions")
            else:
                if not args.json:
                    printer.info("✓ Git integration enabled (read-only)")

            # Add git permissions to allow list (avoid duplicates)
            for perm in git_permissions["allow"]:
                if perm not in existing_allow:
                    new_permissions.append(perm)
                    permissions["allow"].append(perm)
                    existing_allow.add(perm)

            # Add git permissions that require approval (avoid duplicates)
            for perm in git_permissions["ask"]:
                if perm not in existing_ask:
                    new_ask_permissions.append(perm)
                    permissions["ask"].append(perm)
                    existing_ask.add(perm)
        # If enable_git is None or False, don't add any git permissions

    else:
        # Interactive mode: prompt user for git permissions
        git_permissions = _prompt_for_git_permissions(printer)

        # Add git permissions to allow list (avoid duplicates)
        for perm in git_permissions["allow"]:
            if perm not in existing_allow:
                new_permissions.append(perm)
                permissions["allow"].append(perm)
                existing_allow.add(perm)

        # Add git permissions that require approval (avoid duplicates)
        for perm in git_permissions["ask"]:
            if perm not in existing_ask:
                new_ask_permissions.append(perm)
                permissions["ask"].append(perm)
                existing_ask.add(perm)

    # Write updated settings
    with settings_file.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    result = {
        "success": True,
        "settings_file": str(settings_file),
        "permissions_added": len(new_permissions),
        "ask_permissions_added": len(new_ask_permissions),
        "total_allow_permissions": len(permissions["allow"]),
        "total_ask_permissions": len(permissions["ask"]),
        "new_permissions": new_permissions,
        "new_ask_permissions": new_ask_permissions,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        total_added = len(new_permissions) + len(new_ask_permissions)
        if total_added > 0:
            printer.success(f"✅ Added {len(new_permissions)} new permissions to ALLOW list")
            if new_ask_permissions:
                printer.success(
                    f"✅ Added {len(new_ask_permissions)} dangerous operations to ASK list (requires approval)"
                )
        else:
            printer.success(f"✅ All SDD permissions already configured in {settings_file}")

    return 0


def categorize_missing_permissions(missing: list[str]) -> dict[str, list[str]]:
    """Categorize missing permissions by type for better reporting."""
    categories = {
        "skills": [],
        "commands": [],
        "bash": [],
        "file_access": [],
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
    settings_file = project_path / ".claude" / "settings.local.json"

    if not settings_file.exists():
        result = {
            "configured": False,
            "status": "not_configured",
            "settings_file": str(settings_file),
            "exists": False,
            "total_required": len(SDD_PERMISSIONS),
            "total_present": 0,
            "total_missing": len(SDD_PERMISSIONS),
            "message": "Settings file does not exist",
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            printer.error(f"Settings file does not exist: {settings_file}")
            printer.info(f"Missing all {len(SDD_PERMISSIONS)} SDD permissions")
        return 1

    with settings_file.open(encoding="utf-8") as f:
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
        "missing_by_category": missing_by_category,
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
        "setup-permissions",
        parents=[parent_parser],
        help="Configure SDD project permissions",
        description="Configure .claude/settings.local.json with required SDD tool permissions",
    )

    # Create subparsers for setup-permissions commands
    setup_perms_subparsers = setup_perms_parser.add_subparsers(
        title="setup-permissions commands", dest="setup_permissions_command", required=True
    )

    # update command
    update_cmd = setup_perms_subparsers.add_parser(
        "update",
        parents=[parent_parser],
        help="Update project settings with SDD permissions",
    )
    update_cmd.add_argument("project_root", help='Project root directory (e.g., "." for current)')

    # Non-interactive mode
    update_cmd.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive prompts (use with other flags to specify config)",
    )

    # SDD config options
    update_cmd.add_argument(
        "--default-mode",
        choices=["json", "text", "markdown"],
        help="Default output mode for sdd_config.json",
    )
    update_cmd.add_argument(
        "--verbosity",
        choices=["quiet", "normal", "verbose"],
        help="Default verbosity level",
    )
    update_cmd.add_argument(
        "--work-mode",
        choices=["single", "autonomous"],
        help="Work mode (single task or autonomous phase completion)",
    )

    # Git permission options
    update_cmd.add_argument(
        "--enable-git",
        action="store_true",
        dest="enable_git",
        help="Add git read permissions to settings",
    )
    update_cmd.add_argument(
        "--no-enable-git",
        action="store_false",
        dest="enable_git",
        help="Do not add git permissions",
    )
    update_cmd.add_argument(
        "--git-write",
        action="store_true",
        dest="git_write",
        help="Add git write permissions (requires --enable-git)",
    )
    update_cmd.add_argument(
        "--no-git-write",
        action="store_false",
        dest="git_write",
        help="Do not add git write permissions",
    )

    update_cmd.set_defaults(func=cmd_update, enable_git=None, git_write=None)

    # check command
    check_cmd = setup_perms_subparsers.add_parser(
        "check",
        parents=[parent_parser],
        help="Check if SDD permissions are configured",
    )
    check_cmd.add_argument("project_root", help="Project root directory")
    check_cmd.set_defaults(func=cmd_check)
