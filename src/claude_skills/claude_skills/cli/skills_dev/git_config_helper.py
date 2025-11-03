"""
Git Configuration Helper Commands

Provides interactive setup for git integration configuration.
Used by /sdd-begin command to configure git features during project setup.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

from claude_skills.common import PrettyPrinter


# Default git configuration template
DEFAULT_GIT_CONFIG = {
    "enabled": False,
    "auto_branch": True,
    "auto_commit": True,
    "auto_push": False,
    "auto_pr": False,
    "commit_cadence": "task",
    "file_staging": {
        "show_before_commit": True,
    },
    "ai_pr": {
        "enabled": False,
        "model": "sonnet",
        "include_journals": True,
        "include_diffs": True,
        "max_diff_size_kb": 50,
    }
}


def detect_git_config_state(project_path: Path) -> Tuple[bool, bool, bool]:
    """
    Detect the state of git configuration.

    Returns:
        (exists, enabled, needs_setup)
        - exists: .claude/git_config.json file exists
        - enabled: git integration is enabled in config
        - needs_setup: user should be prompted to configure
    """
    git_config_file = project_path / ".claude" / "git_config.json"

    if not git_config_file.exists():
        return (False, False, True)

    try:
        with open(git_config_file, 'r') as f:
            config = json.load(f)

        # Check if git integration is enabled
        enabled = config.get("enabled", False)

        # If config exists and has enabled field, no setup needed
        needs_setup = False

        return (True, enabled, needs_setup)

    except (json.JSONDecodeError, IOError):
        # Config file exists but is invalid - needs setup
        return (True, False, True)


def format_git_config_summary(settings: dict) -> str:
    """Format git configuration as human-readable summary.

    Args:
        settings: Dict with git config settings (from check-git-config result)

    Returns:
        Formatted string with config summary
    """
    if not settings:
        return "No configuration found"

    lines = []
    lines.append("Current Git Configuration:")
    lines.append("")

    # Auto-branch
    auto_branch = settings.get("auto_branch", False)
    lines.append(f"  • Auto-branch: {'Yes' if auto_branch else 'No'}")

    # Auto-commit with cadence
    auto_commit = settings.get("auto_commit", False)
    if auto_commit:
        cadence = settings.get("commit_cadence", "task")
        lines.append(f"  • Auto-commit: Yes (per {cadence})")
    else:
        lines.append("  • Auto-commit: No")

    # File staging
    file_staging = settings.get("file_staging", {})
    show_before = file_staging.get("show_before_commit", False)
    lines.append(f"  • Show files before commit: {'Yes' if show_before else 'No'}")

    # Auto-push
    auto_push = settings.get("auto_push", False)
    lines.append(f"  • Auto-push: {'Yes' if auto_push else 'No'}")

    # AI-powered PRs
    ai_pr = settings.get("ai_pr", {})
    ai_enabled = ai_pr.get("enabled", False)
    if ai_enabled:
        model = ai_pr.get("model", "sonnet")
        lines.append(f"  • AI-powered PRs: Yes (model: {model})")
    else:
        lines.append("  • AI-powered PRs: No")

    return "\n".join(lines)


def cmd_check_git_config(args, printer: PrettyPrinter) -> int:
    """Check if git configuration is set up."""
    project_path = Path(args.project_root).resolve()
    git_config_file = project_path / ".claude" / "git_config.json"

    exists, enabled, needs_setup = detect_git_config_state(project_path)

    result = {
        "configured": not needs_setup,
        "git_config_file": str(git_config_file),
        "exists": exists,
        "enabled": enabled,
        "needs_setup": needs_setup
    }

    # Load and include current settings if config exists
    if exists and not needs_setup:
        try:
            with open(git_config_file, 'r') as f:
                config = json.load(f)

            result["settings"] = {
                "auto_branch": config.get("auto_branch"),
                "auto_commit": config.get("auto_commit"),
                "auto_push": config.get("auto_push"),
                "commit_cadence": config.get("commit_cadence"),
                "file_staging": config.get("file_staging", {}),
                "ai_pr": config.get("ai_pr", {})
            }
        except (json.JSONDecodeError, IOError):
            # If we can't load settings, don't include them
            pass

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not needs_setup:
            status = "enabled" if enabled else "disabled"
            printer.success(f"Git configuration is set ({status})")
        else:
            printer.warning("Git configuration needs setup")

    return 0 if not needs_setup else 1


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question and return boolean answer."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{question} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ('y', 'yes')


def ask_choice(question: str, choices: list, default: str) -> str:
    """Ask a multiple choice question."""
    print(f"\n{question}")
    for i, choice in enumerate(choices, 1):
        marker = "*" if choice == default else " "
        print(f"  {marker} {i}) {choice}")

    while True:
        response = input(f"Choice [1-{len(choices)}] (default: {default}): ").strip()

        if not response:
            return default

        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass

        print(f"Invalid choice. Please enter 1-{len(choices)}")


def cmd_setup_git_config(args, printer: PrettyPrinter) -> int:
    """Interactive git configuration wizard."""
    project_path = Path(args.project_root).resolve()
    git_config_file = project_path / ".claude" / "git_config.json"

    # Create .claude directory if it doesn't exist
    git_config_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if config already exists
    exists, enabled, needs_setup = detect_git_config_state(project_path)

    if exists and not needs_setup:
        if not args.force:
            printer.info(f"Git configuration already exists at {git_config_file}")
            printer.info("Use --force to reconfigure")
            return 0

    # Start interactive wizard
    printer.header("="*70)
    printer.header("Git Integration Setup")
    printer.header("="*70)
    printer.info("")
    printer.info("Configure git integration for spec-driven development.")
    printer.info("You can change these settings later in .claude/git_config.json")
    printer.info("")

    config = {}

    # Question 1: Enable git integration?
    config["enabled"] = ask_yes_no(
        "Enable git integration?",
        default=True
    )

    if not config["enabled"]:
        # User disabled git - write minimal config and exit
        printer.info("")
        printer.info("Git integration disabled. Writing config...")

        with open(git_config_file, 'w') as f:
            json.dump({"enabled": False}, f, indent=2)
            f.write('\n')

        printer.success(f"Configuration saved to {git_config_file}")
        return 0

    # Question 2: Auto-branch
    printer.info("")
    config["auto_branch"] = ask_yes_no(
        "Auto-create feature branches when starting specs?",
        default=True
    )

    # Question 3: Auto-commit
    printer.info("")
    config["auto_commit"] = ask_yes_no(
        "Auto-commit changes when completing tasks?",
        default=True
    )

    # Question 4: Commit cadence (only if auto_commit enabled)
    if config["auto_commit"]:
        printer.info("")
        config["commit_cadence"] = ask_choice(
            "When should commits be created?",
            choices=["task", "phase", "manual"],
            default="task"
        )
    else:
        config["commit_cadence"] = "manual"

    # Question 5: Show files before commit
    printer.info("")
    config["file_staging"] = {
        "show_before_commit": ask_yes_no(
            "Show files for review before committing? (recommended)",
            default=True
        )
    }

    # Question 6: Auto-push (WARNING)
    printer.info("")
    printer.warning("⚠️  Auto-push will automatically push commits to remote")
    config["auto_push"] = ask_yes_no(
        "Enable auto-push to remote?",
        default=False
    )

    # Question 7: AI-powered PRs
    printer.info("")
    ai_pr_enabled = ask_yes_no(
        "Enable AI-powered pull request creation?",
        default=True
    )

    if ai_pr_enabled:
        # Question 8: AI model
        printer.info("")
        ai_model = ask_choice(
            "Which AI model for PR generation?",
            choices=["sonnet", "haiku", "opus"],
            default="sonnet"
        )

        config["ai_pr"] = {
            "enabled": True,
            "model": ai_model,
            "include_journals": True,
            "include_diffs": True,
            "max_diff_size_kb": 50
        }
    else:
        config["ai_pr"] = {
            "enabled": False,
            "model": "sonnet",
            "include_journals": True,
            "include_diffs": True,
            "max_diff_size_kb": 50
        }

    # Legacy auto_pr (kept for compatibility, but not asked)
    config["auto_pr"] = False

    # Write configuration
    printer.info("")
    printer.info("Writing configuration...")

    with open(git_config_file, 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')

    # Show summary
    printer.info("")
    printer.header("="*70)
    printer.header("Configuration Summary")
    printer.header("="*70)
    printer.success(f"✅ Git Integration: {'Enabled' if config['enabled'] else 'Disabled'}")

    if config["enabled"]:
        printer.info(f"  • Auto-branch: {'Yes' if config['auto_branch'] else 'No'}")
        printer.info(f"  • Auto-commit: {'Yes' if config['auto_commit'] else 'No'}")
        printer.info(f"  • Commit cadence: {config['commit_cadence']}")
        printer.info(f"  • Show files before commit: {'Yes' if config['file_staging']['show_before_commit'] else 'No'}")
        printer.info(f"  • Auto-push: {'Yes' if config['auto_push'] else 'No'}")
        printer.info(f"  • AI-powered PRs: {'Yes' if config['ai_pr']['enabled'] else 'No'}")
        if config['ai_pr']['enabled']:
            printer.info(f"    - Model: {config['ai_pr']['model']}")

    printer.info("")
    printer.success(f"Configuration saved to {git_config_file}")
    printer.info("")
    printer.info("You can manually edit this file to change settings later.")
    printer.header("="*70)

    return 0


def register_git_config_helper(subparsers, parent_parser):
    """Register git config helper commands."""
    # This function is called from start_helper.py to add commands to start-helper
    pass  # Commands are registered individually in start_helper.py
