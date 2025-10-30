"""
SDD Start Helper Commands

Provides commands for /sdd-begin slash command and session management.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.integrations import get_session_state


# Configuration
CLAUDE_HOME = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_HOME / "settings.json"


def cmd_check_permissions(args, printer: PrettyPrinter) -> int:
    """Check if SDD permissions are configured for the project."""
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    # Check if specs directory exists
    specs_dir = project_root / "specs"
    has_specs = specs_dir.exists()

    # Check if permissions are in settings
    needs_setup = False
    if has_specs:
        try:
            # Collect permissions from both global and project-local settings
            all_permissions = []

            # Check global settings
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r') as f:
                    global_settings = json.load(f)
                all_permissions.extend(global_settings.get('permissions', {}).get('allow', []))

            # Check project-local settings
            local_settings_file = project_root / ".claude" / "settings.local.json"
            if local_settings_file.exists():
                with open(local_settings_file, 'r') as f:
                    local_settings = json.load(f)
                all_permissions.extend(local_settings.get('permissions', {}).get('allow', []))

            # Check for key SDD permissions
            has_permissions = any(
                any(req in perm for req in ['specs', 'sdd-next', 'sdd-update'])
                for perm in all_permissions
            )

            needs_setup = not has_permissions
        except Exception:
            needs_setup = True
    elif has_specs:
        needs_setup = True

    result = {
        "has_specs_dir": has_specs,
        "needs_setup": needs_setup,
        "project_root": str(project_root)
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

    specs_active = project_root / "specs" / "active"

    if not specs_active.exists():
        result = {
            "active_work_found": False,
            "specs": [],
            "message": "No specs/active directory found"
        }
        print(json.dumps(result, indent=2))
        return 0

    # Find all JSON spec files
    specs = []
    for spec_file in specs_active.glob("*.json"):
        try:
            with open(spec_file, 'r') as f:
                spec_data = json.load(f)

            hierarchy = spec_data.get('hierarchy', {})
            spec_root = hierarchy.get('spec-root', {})

            spec_info = {
                "spec_id": spec_data.get('spec_id'),
                "spec_file": str(spec_file),
                "title": spec_root.get('title', 'Unknown'),
                "progress": {
                    "completed": spec_root.get('completed_tasks', 0),
                    "total": spec_root.get('total_tasks', 0),
                    "percentage": int((spec_root.get('completed_tasks', 0) / spec_root.get('total_tasks', 1)) * 100)
                },
                "status": spec_root.get('status', 'unknown'),
                "last_updated": spec_data.get('last_updated', ''),
            }

            specs.append(spec_info)
        except Exception:
            # Skip malformed specs
            continue

    result = {
        "active_work_found": len(specs) > 0,
        "specs": specs,
        "count": len(specs)
    }

    print(json.dumps(result, indent=2))
    return 0


def cmd_format_output(args, printer: PrettyPrinter) -> int:
    """Format active work as human-readable text with last-accessed task info."""
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = project_root.resolve()

    specs_active = project_root / "specs" / "active"

    if not specs_active.exists():
        print("📋 No active SDD work found.\n")
        print("No specs/active directory or no pending/in-progress tasks detected.")
        return 0

    # Get session state with last-accessed task info
    specs_dir = project_root / "specs"
    session_state = get_session_state(str(specs_dir))

    # Find all JSON spec files
    specs = []
    for spec_file in specs_active.glob("*.json"):
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
                "title": spec_root.get('title', 'Unknown'),
                "completed": completed,
                "total": total,
                "percentage": percentage,
                "status": spec_root.get('status', 'unknown'),
            }

            specs.append(spec_info)
        except Exception:
            continue

    if not specs:
        print("📋 No active SDD work found.\n")
        print("No specs/active directory or no pending/in-progress tasks detected.")
        return 0

    # Format output
    print(f"📋 Found {len(specs)} active specification{'s' if len(specs) != 1 else ''}:\n")

    for i, spec in enumerate(specs, 1):
        status_emoji = "⚡" if spec['status'] == 'in_progress' else "📝"
        print(f"{i}. {status_emoji} {spec['title']}")
        print(f"   ID: {spec['spec_id']}")
        print(f"   Progress: {spec['completed']}/{spec['total']} tasks ({spec['percentage']}%)")
        print()

    # Show last-accessed task information
    if session_state.get("last_task"):
        last_task = session_state["last_task"]
        print("🕐 Last accessed task:")
        print(f"   Spec: {last_task['spec_id']}")
        print(f"   Task: {last_task['task_id']} - {last_task['title']}")

        # Format modified time in human-readable format
        try:
            modified_dt = datetime.fromisoformat(last_task['modified'])
            time_diff = datetime.now() - modified_dt

            if time_diff.total_seconds() < 60:
                time_str = "just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_str = f"{days} day{'s' if days != 1 else ''} ago"

            print(f"   Last modified: {time_str}")
        except Exception:
            print(f"   Last modified: {last_task['modified']}")

        print()

    if session_state.get("in_progress_count", 0) > 0:
        count = session_state["in_progress_count"]
        print(f"💡 {count} task{'s' if count != 1 else ''} currently in progress")
        print()

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

    # Combine with active work info
    result = {
        "has_specs": True,
        "last_task": session_state.get("last_task"),
        "active_specs": session_state.get("active_specs", []),
        "in_progress_count": session_state.get("in_progress_count", 0),
        "timestamp": session_state.get("timestamp")
    }

    print(json.dumps(result, indent=2))
    return 0


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
