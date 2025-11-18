"""
SDD Start Helper Commands

Provides commands for /sdd-begin slash command and session management.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.integrations import get_session_state
from claude_skills.cli.skills_dev.git_config_helper import (
    cmd_check_git_config,
    cmd_setup_git_config,
    detect_git_config_state,
    format_git_config_summary,
)
from claude_skills.common.setup_templates import load_json_template_clean


# Core permissions required for SDD workflows. These mirror the critical
# permissions checked in setup_permissions.cmd_check and provide a precise
# signal rather than the previous substring heuristic (which matched any
# permission containing "specs").
CORE_SDD_PERMISSIONS = {
    "Skill(sdd-toolkit:sdd-plan)",
    "Skill(sdd-toolkit:sdd-next)",
    "Skill(sdd-toolkit:sdd-update)",
}


def _get_permissions_status(project_root: Path) -> dict:
    specs_dir = project_root / "specs"
    has_specs = specs_dir.exists()

    settings_file = project_root / ".claude" / "settings.local.json"
    if not settings_file.exists():
        return {
            "configured": False,
            "status": "not_configured",
            "settings_file": str(settings_file),
            "exists": False,
            "has_specs": has_specs,
            "message": "Settings file does not exist",
        }

    try:
        with settings_file.open('r') as f:
            settings = json.load(f)
    except Exception:
        return {
            "configured": False,
            "status": "not_configured",
            "settings_file": str(settings_file),
            "exists": True,
            "has_specs": has_specs,
            "message": "Failed to parse settings file",
        }

    existing_permissions = set(settings.get('permissions', {}).get('allow', []))
    has_permissions = CORE_SDD_PERMISSIONS.issubset(existing_permissions)

    status = "fully_configured" if has_permissions else ("partially_configured" if existing_permissions else "not_configured")

    return {
        "configured": has_permissions,
        "status": status,
        "settings_file": str(settings_file),
        "exists": True,
        "has_specs": has_specs,
    }


def _get_git_status(project_root: Path) -> dict:
    git_config_file = project_root / ".claude" / "git_config.json"
    exists, enabled, needs_setup = detect_git_config_state(project_root)

    status = {
        "configured": not needs_setup,
        "git_config_file": str(git_config_file),
        "exists": exists,
        "enabled": enabled,
        "needs_setup": needs_setup,
    }

    if exists and not needs_setup:
        try:
            with git_config_file.open('r') as f:
                config = json.load(f)
            status["settings"] = {
                "auto_branch": config.get("auto_branch"),
                "auto_commit": config.get("auto_commit"),
                "auto_push": config.get("auto_push"),
                "commit_cadence": config.get("commit_cadence"),
                "file_staging": config.get("file_staging", {}),
                "ai_pr": config.get("ai_pr", {}),
            }
        except Exception:
            pass

    return status


def _collect_specs_info(project_root: Path) -> dict:
    specs_dir = project_root / "specs"
    specs_pending = specs_dir / "pending"
    specs_active = specs_dir / "active"

    if not specs_dir.exists():
        return {
            "active_work_found": False,
            "specs": [],
            "pending_specs": [],
            "message": "No specs directory found",
        }

    specs = []
    search_dirs = []
    if specs_pending.exists():
        search_dirs.append(("pending", specs_pending))
    if specs_active.exists():
        search_dirs.append(("active", specs_active))

    if not search_dirs:
        return {
            "active_work_found": False,
            "specs": [],
            "pending_specs": [],
            "message": "No specs/pending or specs/active directory found",
        }

    for folder_status, search_dir in search_dirs:
        for spec_file in search_dir.glob("*.json"):
            try:
                with open(spec_file, 'r') as f:
                    spec_data = json.load(f)

                hierarchy = spec_data.get('hierarchy', {})
                spec_root = hierarchy.get('spec-root', {})

                completed = spec_root.get('completed_tasks', 0)
                total = spec_root.get('total_tasks', 0)
                percentage = int((completed / total) * 100) if total > 0 else 0

                spec_info = {
                    "spec_id": spec_data.get('spec_id'),
                    "spec_file": str(spec_file),
                    "title": spec_root.get('title', 'Unknown'),
                    "completed": completed,
                    "total": total,
                    "percentage": percentage,
                    "status": spec_root.get('status', 'unknown'),
                    "folder_status": folder_status,
                    "last_updated": spec_data.get('last_updated', ''),
                }
                spec_info["progress"] = {
                    "completed": completed,
                    "total": total,
                    "percentage": percentage,
                }
                specs.append(spec_info)
            except Exception:
                continue

    pending_specs = [
        {"spec_id": spec["spec_id"], "title": spec["title"]}
        for spec in specs
        if spec.get("folder_status") == "pending"
    ]

    return {
        "active_work_found": len(specs) > 0,
        "specs": specs,
        "pending_specs": pending_specs,
        "message": None,
        "count": len(specs),
    }


def _render_active_work(specs: list[dict], session_state: dict) -> str:
    if not specs:
        return "📋 No active SDD work found.\n\nNo specs/active directory or no pending/in-progress tasks detected."

    lines = ["📋 Active SDD Specifications:", ""]

    last_accessed = session_state.get("last_task") if session_state else None

    for spec in specs:
        status_icon = "⚡" if spec.get("folder_status") == "active" else "📝"
        lines.append(f"{status_icon} {spec.get('spec_id', 'unknown')} - {spec.get('title', 'Untitled')}")
        lines.append(
            f"   Progress: {spec.get('completed', 0)}/{spec.get('total', 0)} tasks ({spec.get('percentage', 0)}%)"
        )
        lines.append(f"   Folder: {spec.get('folder_status', 'unknown')} | Status: {spec.get('status', 'unknown')}")
        lines.append("")

    if last_accessed:
        lines.append("🕐 Last accessed task:")
        lines.append(f"   Spec: {last_accessed.get('spec_id', 'unknown')} | Task: {last_accessed.get('task_id', 'unknown')}")
        lines.append("")

    in_progress_count = session_state.get("in_progress_count", 0) if session_state else 0
    if in_progress_count:
        lines.append(f"💡 {in_progress_count} task{'s' if in_progress_count != 1 else ''} currently in progress")

    return "\n".join(lines)


def cmd_check_permissions(args, printer: PrettyPrinter) -> int:
    """Check if SDD permissions are configured for the project."""
    # Note: CLAUDE_TRANSCRIPT_PATH env var is automatically set by session-start hook
    # and inherited by all child processes. No cache or validation needed.

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    status = _get_permissions_status(project_root)
    needs_setup = not status.get("configured", False)

    result = {
        "has_specs_dir": status.get("has_specs", False),
        "needs_setup": needs_setup,
        "project_root": str(project_root),
        "status": status.get("status"),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if needs_setup:
            printer.warning("SDD permissions need setup")
        else:
            printer.success("SDD permissions are configured")

    return 0 if not needs_setup else 1


def cmd_find_active_work(args, printer: PrettyPrinter) -> int:
    """Find all active SDD specifications with resumable work."""
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    result = _collect_specs_info(project_root)
    result["project_root"] = str(project_root)

    print(json.dumps(result, indent=2))
    return 0


def cmd_format_output(args, printer: PrettyPrinter) -> int:
    """Format active work as human-readable text with last-accessed task info."""
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    specs_info = _collect_specs_info(project_root)
    session_state = get_session_state(str(project_root / "specs"))
    text = _render_active_work(specs_info.get("specs", []), session_state or {})
    print(text)
    return 0


def cmd_get_session_info(args, printer: PrettyPrinter) -> int:
    """Get session state information as JSON."""
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    specs_dir = project_root / "specs"

    if not specs_dir.exists():
        result = {
            "has_specs": False,
            "message": "No specs directory found"
        }
        print(json.dumps(result, indent=2))
        return 0

    # Get session state
    session_state = get_session_state(str(specs_dir))

    # Build pending_specs list from specs in pending folder
    specs_pending = specs_dir / "pending"
    pending_specs = []
    if specs_pending.exists():
        for spec_file in specs_pending.glob("*.json"):
            try:
                with open(spec_file, 'r') as f:
                    spec_data = json.load(f)
                hierarchy = spec_data.get('hierarchy', {})
                spec_root = hierarchy.get('spec-root', {})
                pending_specs.append({
                    "spec_id": spec_data.get('spec_id'),
                    "title": spec_root.get('title', 'Unknown')
                })
            except Exception:
                continue

    # Combine with active work info
    result = {
        "has_specs": True,
        "last_task": session_state.get("last_task"),
        "active_specs": session_state.get("active_specs", []),
        "pending_specs": pending_specs,
        "in_progress_count": session_state.get("in_progress_count", 0),
        "timestamp": session_state.get("timestamp")
    }

    print(json.dumps(result, indent=2))
    return 0


def cmd_inspect_config(args, printer: PrettyPrinter) -> int:
    """Report the current state of .claude config files."""

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    claude_dir = project_root / ".claude"

    files = {
        "settings": claude_dir / "settings.local.json",
        "git_config": claude_dir / "git_config.json",
        "sdd_config": claude_dir / "sdd_config.json",
    }

    files_state = {
        key: {
            "path": str(path),
            "exists": path.exists(),
        }
        for key, path in files.items()
    }

    result = {
        "project_root": str(project_root),
        "claude_dir": str(claude_dir),
        "claude_dir_exists": claude_dir.exists(),
        "files": files_state,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "present" if result["claude_dir_exists"] else "missing"
        printer.info(f".claude directory: {status}")
        for key, info in files_state.items():
            label = key.replace("_", " ").title()
            if info["exists"]:
                printer.success(f"✅ {label}: {info['path']}")
            else:
                printer.info(f"ℹ️  {label} will be created (expected at {info['path']})")

    return 0


def cmd_session_summary(args, printer: PrettyPrinter) -> int:
    """Return consolidated permissions, git status, and active work summary."""

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    permissions = _get_permissions_status(project_root)
    git_status = _get_git_status(project_root)
    specs_info = _collect_specs_info(project_root)
    session_state = get_session_state(str(project_root / "specs")) if (project_root / "specs").exists() else {}
    formatted_text = _render_active_work(specs_info.get("specs", []), session_state or {})

    result = {
        "project_root": str(project_root),
        "permissions": permissions,
        "git": git_status,
        "active_work": {
            **specs_info,
            "text": formatted_text,
        },
        "session_state": session_state,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        perm_status = permissions.get("status", "unknown")
        git_msg = "configured" if git_status.get("configured") else "needs setup"
        printer.info(f"Permissions status: {perm_status}")
        printer.info(f"Git integration: {git_msg}")
        printer.info("")
        print(formatted_text)

    return 0


def _write_sdd_config(config_path: Path, printer: PrettyPrinter) -> bool:
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = load_json_template_clean("sdd_config.json")
        with config_path.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
        printer.success(f"✅ Created {config_path}")
        return True
    except Exception as exc:  # pragma: no cover - unexpected filesystem errors
        printer.error(f"❌ Failed to create {config_path}: {exc}")
        return False


def cmd_ensure_sdd_config(args, printer: PrettyPrinter) -> int:
    """Ensure .claude/sdd_config.json exists, creating it from the template if missing."""

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    config_path = project_root / ".claude" / "sdd_config.json"

    if config_path.exists():
        result = {
            "created": False,
            "path": str(config_path),
            "project_root": str(project_root),
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            printer.success(f"✅ SDD CLI config already exists at {config_path}")
        return 0

    created = _write_sdd_config(config_path, printer)
    result = {
        "created": created,
        "path": str(config_path),
        "project_root": str(project_root),
    }
    if args.json:
        print(json.dumps(result, indent=2))

    return 0 if created else 1


def register_start_helper(subparsers, parent_parser):
    """Register start-helper subcommands."""
    # Create start-helper parser
    start_helper_parser = subparsers.add_parser(
        'start-helper',
        parents=[parent_parser],
        help='Session start helper commands',
        description='Commands for /sdd-begin slash command and session management'
    )

    # Create subparsers for start-helper commands
    start_helper_subparsers = start_helper_parser.add_subparsers(
        title='start-helper commands',
        dest='start_helper_command',
        required=True
    )

    # check-permissions command
    check_perms = start_helper_subparsers.add_parser(
        'check-permissions',
        parents=[parent_parser],
        help='Check if SDD permissions are configured'
    )
    check_perms.add_argument('project_root', nargs='?', help='Project root directory')
    check_perms.set_defaults(func=cmd_check_permissions)

    # find-active-work command
    find_work = start_helper_subparsers.add_parser(
        'find-active-work',
        parents=[parent_parser],
        help='Find all active SDD specs (JSON)'
    )
    find_work.add_argument('project_root', nargs='?', help='Project root directory')
    find_work.set_defaults(func=cmd_find_active_work)

    # format-output command
    format_out = start_helper_subparsers.add_parser(
        'format-output',
        parents=[parent_parser],
        help='Format active work as human-readable text'
    )
    format_out.add_argument('project_root', nargs='?', help='Project root directory')
    format_out.set_defaults(func=cmd_format_output)

    # get-session-info command
    session_info = start_helper_subparsers.add_parser(
        'get-session-info',
        parents=[parent_parser],
        help='Get session state with last-accessed task (JSON)'
    )
    session_info.add_argument('project_root', nargs='?', help='Project root directory')
    session_info.set_defaults(func=cmd_get_session_info)

    # session-summary command
    session_summary = start_helper_subparsers.add_parser(
        'session-summary',
        parents=[parent_parser],
        help='Combined permissions, git, and active work summary'
    )
    session_summary.add_argument('project_root', nargs='?', help='Project root directory')
    session_summary.set_defaults(func=cmd_session_summary)

    # inspect-config command
    inspect_config = start_helper_subparsers.add_parser(
        'inspect-config',
        parents=[parent_parser],
        help='Show current .claude config state'
    )
    inspect_config.add_argument('project_root', nargs='?', help='Project root directory')
    inspect_config.set_defaults(func=cmd_inspect_config)

    # ensure-sdd-config command
    ensure_sdd_config = start_helper_subparsers.add_parser(
        'ensure-sdd-config',
        parents=[parent_parser],
        help='Create .claude/sdd_config.json from template if missing'
    )
    ensure_sdd_config.add_argument('project_root', nargs='?', help='Project root directory')
    ensure_sdd_config.set_defaults(func=cmd_ensure_sdd_config)

    # check-git-config command
    check_git = start_helper_subparsers.add_parser(
        'check-git-config',
        parents=[parent_parser],
        help='Check if git configuration is set up'
    )
    check_git.add_argument('project_root', nargs='?', help='Project root directory')
    check_git.set_defaults(func=cmd_check_git_config)

    # setup-git-config command
    setup_git = start_helper_subparsers.add_parser(
        'setup-git-config',
        parents=[parent_parser],
        help='Interactive git configuration wizard'
    )
    setup_git.add_argument('project_root', nargs='?', help='Project root directory')
    setup_git.add_argument('--force', action='store_true', help='Force reconfiguration')
    setup_git.add_argument('--non-interactive', action='store_true',
                          help='Non-interactive mode - use CLI flags or defaults')
    setup_git.add_argument('--enabled', action='store_true', default=None,
                          help='Enable git integration (default: True in non-interactive mode)')
    setup_git.add_argument('--no-enabled', dest='enabled', action='store_false',
                          help='Disable git integration')
    setup_git.add_argument('--auto-branch', action='store_true', default=None,
                          help='Auto-create feature branches (default: True)')
    setup_git.add_argument('--no-auto-branch', dest='auto_branch', action='store_false',
                          help='Disable auto-branch')
    setup_git.add_argument('--auto-commit', action='store_true', default=None,
                          help='Auto-commit on task completion (default: True)')
    setup_git.add_argument('--no-auto-commit', dest='auto_commit', action='store_false',
                          help='Disable auto-commit')
    setup_git.add_argument('--auto-push', action='store_true', default=None,
                          help='Auto-push to remote (default: False)')
    setup_git.add_argument('--no-auto-push', dest='auto_push', action='store_false',
                          help='Disable auto-push')
    setup_git.add_argument('--commit-cadence', choices=['task', 'phase', 'manual'],
                          help='When to commit: task, phase, or manual (default: task)')
    setup_git.add_argument('--show-files', action='store_true', default=None,
                          help='Show files before commit (default: True)')
    setup_git.add_argument('--no-show-files', dest='show_files', action='store_false',
                          help='Do not show files before commit')
    setup_git.add_argument('--ai-pr', action='store_true', default=None,
                          help='Enable AI-powered PRs (default: True, always uses sonnet model)')
    setup_git.add_argument('--no-ai-pr', dest='ai_pr', action='store_false',
                          help='Disable AI-powered PRs')
    setup_git.set_defaults(func=cmd_setup_git_config)
