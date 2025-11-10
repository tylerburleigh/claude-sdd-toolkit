#!/usr/bin/env python3
"""
SDD Start Helper Script

Provides commands for /sdd-begin slash command and session management:
- check-permissions: Check if SDD permissions are configured
- format-output: Human-readable formatted text for active specs with last-accessed task
- find-active-work: JSON with all resumable specs
- get-session-info: Session state with last-accessed task (JSON)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Import get_session_state from integrations
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.integrations import get_session_state

def check_permissions(project_root=None):
    """Check if SDD permissions are configured for the project."""
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    # Check if specs directory exists
    specs_dir = project_root / "specs"
    has_specs = specs_dir.exists()

    # Check if permissions are in project-local settings
    settings_file = project_root / ".claude" / "settings.local.json"
    needs_setup = False
    if has_specs and settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            permissions = settings.get('permissions', {}).get('allow', [])

            # Check for key SDD permissions
            has_permissions = any(
                any(req in perm for req in ['specs', 'sdd-next', 'sdd-update'])
                for perm in permissions
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

    print(json.dumps(result, indent=2))
    return 0 if not needs_setup else 1


def find_active_work(project_root=None):
    """Find all active SDD specifications with resumable work."""
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    specs_dir = project_root / "specs"
    specs_pending = specs_dir / "pending"
    specs_active = specs_dir / "active"

    # Check if specs directory exists
    if not specs_dir.exists():
        result = {
            "active_work_found": False,
            "specs": [],
            "message": "No specs directory found"
        }
        print(json.dumps(result, indent=2))
        return 0

    # Find all JSON spec files from both pending and active
    specs = []
    search_dirs = []
    if specs_pending.exists():
        search_dirs.append(("pending", specs_pending))
    if specs_active.exists():
        search_dirs.append(("active", specs_active))

    if not search_dirs:
        result = {
            "active_work_found": False,
            "specs": [],
            "message": "No specs/pending or specs/active directory found"
        }
        print(json.dumps(result, indent=2))
        return 0

    for folder_status, search_dir in search_dirs:
        for spec_file in search_dir.glob("*.json"):
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
                    "folder_status": folder_status,  # Add folder status (pending/active)
                    "last_updated": spec_data.get('last_updated', ''),
                }

                specs.append(spec_info)
            except Exception as e:
                # Skip malformed specs
                continue

    # Create simplified pending_specs list for backlog display
    pending_specs = [
        {"spec_id": spec["spec_id"], "title": spec["title"]}
        for spec in specs
        if spec.get("folder_status") == "pending"
    ]

    result = {
        "active_work_found": len(specs) > 0,
        "specs": specs,
        "pending_specs": pending_specs,
        "count": len(specs)
    }

    print(json.dumps(result, indent=2))
    return 0


def format_output(project_root=None):
    """Format active work as human-readable text with last-accessed task info."""
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    specs_dir = project_root / "specs"
    specs_pending = specs_dir / "pending"
    specs_active = specs_dir / "active"

    # Check if specs directory exists
    if not specs_dir.exists():
        print("📋 No active SDD work found.\n")
        print("No specs directory found.")
        return 0

    # Get session state with last-accessed task info
    session_state = get_session_state(str(specs_dir))

    # Find all JSON spec files from both pending and active
    specs = []
    search_dirs = []
    if specs_pending.exists():
        search_dirs.append(("pending", specs_pending))
    if specs_active.exists():
        search_dirs.append(("active", specs_active))

    if not search_dirs:
        print("📋 No active SDD work found.\n")
        print("No specs/pending or specs/active directory found.")
        return 0

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
                    "title": spec_root.get('title', 'Unknown'),
                    "completed": completed,
                    "total": total,
                    "percentage": percentage,
                    "status": spec_root.get('status', 'unknown'),
                    "folder_status": folder_status,  # Add folder status (pending/active)
                }

                specs.append(spec_info)
            except Exception:
                continue

    if not specs:
        print("📋 No active SDD work found.\n")
        print("No specs/active directory or no pending/in-progress tasks detected.")
        return 0

    # Format output
    print(f"📋 Found {len(specs)} specification{'s' if len(specs) != 1 else ''}:\n")

    for i, spec in enumerate(specs, 1):
        # Add folder status indicator
        if spec['folder_status'] == 'pending':
            status_emoji = "⏸️"  # Pending/paused emoji
            folder_label = " [PENDING]"
        else:
            status_emoji = "⚡" if spec['status'] == 'in_progress' else "📝"
            folder_label = ""

        print(f"{i}. {status_emoji} {spec['title']}{folder_label}")
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


def get_session_info(project_root=None):
    """Get session state information as JSON."""
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

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




def main():
    parser = argparse.ArgumentParser(description='SDD Start Helper Script')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # check-permissions command
    check_perms = subparsers.add_parser('check-permissions', help='Check if SDD permissions are configured')
    check_perms.add_argument('project_root', nargs='?', help='Project root directory')

    # find-active-work command
    find_work = subparsers.add_parser('find-active-work', help='Find all active SDD specs (JSON)')
    find_work.add_argument('project_root', nargs='?', help='Project root directory')

    # format-output command
    format_out = subparsers.add_parser('format-output', help='Format active work as human-readable text')
    format_out.add_argument('project_root', nargs='?', help='Project root directory')

    # get-session-info command
    session_info = subparsers.add_parser('get-session-info', help='Get session state with last-accessed task (JSON)')
    session_info.add_argument('project_root', nargs='?', help='Project root directory')

    args = parser.parse_args()

    if args.command == 'check-permissions':
        return check_permissions(args.project_root)
    elif args.command == 'find-active-work':
        return find_active_work(args.project_root)
    elif args.command == 'format-output':
        return format_output(args.project_root)
    elif args.command == 'get-session-info':
        return get_session_info(args.project_root)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
