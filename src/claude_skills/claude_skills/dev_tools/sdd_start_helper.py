#!/usr/bin/env python3
"""
SDD Start Helper Script

Provides commands for /sdd-start slash command and session management:
- check-permissions: Check if SDD permissions are configured
- format-output: Human-readable formatted text for active specs with last-accessed task
- find-active-work: JSON with all resumable specs
- get-session-info: Session state with last-accessed task (JSON)
- check-wrappers: Check if wrapper scripts are installed in ~/.claude/bin
- install-wrappers: Install wrapper scripts from this project to ~/.claude/bin
"""

import argparse
import json
import os
import sys
import stat
import shutil
from pathlib import Path
from datetime import datetime

# Import get_session_state from integrations
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.integrations import get_session_state

# Configuration
CLAUDE_HOME = Path.home() / ".claude"
GLOBAL_BIN_DIR = CLAUDE_HOME / "bin"
GLOBAL_SKILLS_DIR = CLAUDE_HOME / "skills"
SETTINGS_FILE = CLAUDE_HOME / "settings.json"

# Source locations (this project or installed location)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up from .claude/scripts/ to project root
SOURCE_BIN_DIR = SCRIPT_DIR.parent / "bin"  # .claude/bin in this project

# Wrapper script names
WRAPPER_NAMES = ["sdd-next", "sdd-update", "sdd-plan", "doc-query", "sdd-validate"]


def check_permissions(project_root=None):
    """Check if SDD permissions are configured for the project."""
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()

    # Check if specs directory exists
    specs_dir = project_root / "specs"
    has_specs = specs_dir.exists()

    # Check if permissions are in settings
    needs_setup = False
    if has_specs and SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
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
        except Exception as e:
            # Skip malformed specs
            continue

    result = {
        "active_work_found": len(specs) > 0,
        "specs": specs,
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


def check_wrappers():
    """Check if wrapper scripts are installed in ~/.claude/bin."""
    result = {
        "bin_dir_exists": GLOBAL_BIN_DIR.exists(),
        "wrappers_installed": {},
        "missing_wrappers": [],
        "path_configured": str(GLOBAL_BIN_DIR) in os.environ.get('PATH', ''),
        "global_bin_dir": str(GLOBAL_BIN_DIR),
    }

    for name in WRAPPER_NAMES:
        wrapper_path = GLOBAL_BIN_DIR / name
        exists = wrapper_path.exists()
        executable = wrapper_path.is_file() and os.access(wrapper_path, os.X_OK) if exists else False

        result["wrappers_installed"][name] = {
            "exists": exists,
            "executable": executable,
            "path": str(wrapper_path)
        }

        if not exists or not executable:
            result["missing_wrappers"].append(name)

    result["all_installed"] = len(result["missing_wrappers"]) == 0 and result["bin_dir_exists"]

    print(json.dumps(result, indent=2))
    return 0 if result["all_installed"] else 1


def install_wrappers():
    """Install wrapper scripts from source to ~/.claude/bin."""
    # Ensure global bin directory exists
    GLOBAL_BIN_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    errors = []

    # Check if source directory exists
    if not SOURCE_BIN_DIR.exists():
        error_msg = f"Source bin directory not found: {SOURCE_BIN_DIR}"
        print(json.dumps({"success": False, "error": error_msg}, indent=2))
        print(f"❌ {error_msg}", file=sys.stderr)
        return 1

    for name in WRAPPER_NAMES:
        source_wrapper = SOURCE_BIN_DIR / name
        dest_wrapper = GLOBAL_BIN_DIR / name

        # Check if source wrapper exists
        if not source_wrapper.exists():
            errors.append(f"{name}: Source wrapper not found at {source_wrapper}")
            continue

        try:
            # Copy wrapper script
            shutil.copy2(source_wrapper, dest_wrapper)

            # Ensure it's executable
            st = os.stat(dest_wrapper)
            os.chmod(dest_wrapper, st.st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            created.append(name)
        except Exception as e:
            errors.append(f"{name}: {str(e)}")

    result = {
        "bin_dir": str(GLOBAL_BIN_DIR),
        "source_dir": str(SOURCE_BIN_DIR),
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "success": len(errors) == 0
    }

    print(json.dumps(result, indent=2))

    # Also print human-readable summary to stderr
    if created:
        print(f"\n✅ Installed {len(created)} wrapper script(s) to {GLOBAL_BIN_DIR}", file=sys.stderr)
        for name in created:
            print(f"   - {name}", file=sys.stderr)

    if errors:
        print(f"\n❌ Encountered {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"   - {error}", file=sys.stderr)

    if result["success"]:
        # Check if PATH is configured
        if str(GLOBAL_BIN_DIR) not in os.environ.get('PATH', ''):
            print(f"\n💡 Add to PATH: export PATH=\"{GLOBAL_BIN_DIR}:$PATH\"", file=sys.stderr)
            print(f"   (This will be done automatically by session-start hook)", file=sys.stderr)

    return 0 if result["success"] else 1


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

    # check-wrappers command
    subparsers.add_parser('check-wrappers', help='Check if wrapper scripts are installed in ~/.claude/bin')

    # install-wrappers command
    subparsers.add_parser('install-wrappers', help='Install wrapper scripts from source to ~/.claude/bin')

    args = parser.parse_args()

    if args.command == 'check-permissions':
        return check_permissions(args.project_root)
    elif args.command == 'find-active-work':
        return find_active_work(args.project_root)
    elif args.command == 'format-output':
        return format_output(args.project_root)
    elif args.command == 'get-session-info':
        return get_session_info(args.project_root)
    elif args.command == 'check-wrappers':
        return check_wrappers()
    elif args.command == 'install-wrappers':
        return install_wrappers()
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
