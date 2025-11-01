"""
Process detection utilities for identifying the current Claude Code session.

This module provides cross-platform utilities to:
1. Walk the process tree to find parent processes
2. Validate if PIDs are still alive
3. Match the current process to a cached Claude Code session
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any


def get_parent_pids(pid: Optional[int] = None, max_depth: int = 10) -> List[int]:
    """
    Get the chain of parent process IDs up the process tree.

    Args:
        pid: Starting PID (defaults to current process)
        max_depth: Maximum depth to traverse (prevents infinite loops)

    Returns:
        List of PIDs from current process up to init, excluding current PID
    """
    if pid is None:
        pid = os.getpid()

    parent_pids = []
    current_pid = pid

    system = platform.system()

    for _ in range(max_depth):
        try:
            parent_pid = _get_parent_pid(current_pid, system)
            if parent_pid is None or parent_pid == 0 or parent_pid == 1:
                # Reached init or no parent
                break
            if parent_pid in parent_pids:
                # Circular reference, shouldn't happen but be safe
                break
            parent_pids.append(parent_pid)
            current_pid = parent_pid
        except Exception:
            # If we can't get parent, stop here
            break

    return parent_pids


def _get_parent_pid(pid: int, system: str) -> Optional[int]:
    """
    Get the parent PID of a given process.

    Args:
        pid: Process ID to get parent of
        system: Platform system name (Linux, Darwin, Windows)

    Returns:
        Parent PID or None if not found
    """
    if system == "Linux":
        return _get_parent_pid_linux(pid)
    elif system == "Darwin":
        return _get_parent_pid_macos(pid)
    elif system == "Windows":
        return _get_parent_pid_windows(pid)
    else:
        return None


def _get_parent_pid_linux(pid: int) -> Optional[int]:
    """Get parent PID on Linux using /proc filesystem."""
    try:
        stat_file = Path(f"/proc/{pid}/stat")
        if not stat_file.exists():
            return None

        stat_content = stat_file.read_text()
        # /proc/[pid]/stat format: pid (comm) state ppid ...
        # comm can contain spaces and parens, so we need to find the last )
        last_paren = stat_content.rfind(')')
        if last_paren == -1:
            return None

        # Split the part after the comm field
        parts = stat_content[last_paren + 1:].split()
        if len(parts) >= 2:
            # First field after comm is state, second is ppid
            return int(parts[1])
        return None
    except (FileNotFoundError, ValueError, IndexError):
        return None


def _get_parent_pid_macos(pid: int) -> Optional[int]:
    """Get parent PID on macOS using ps command."""
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "ppid="],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
        return None
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        return None


def _get_parent_pid_windows(pid: int) -> Optional[int]:
    """Get parent PID on Windows using wmic or psutil."""
    try:
        # Try wmic first (built-in, no dependencies)
        result = subprocess.run(
            ["wmic", "process", "where", f"ProcessId={pid}", "get", "ParentProcessId"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                return int(lines[1].strip())
        return None
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        # Fallback: try psutil if available
        try:
            import psutil
            process = psutil.Process(pid)
            return process.ppid()
        except (ImportError, Exception):
            return None


def is_pid_alive(pid: int) -> bool:
    """
    Check if a process with the given PID is currently running.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    if pid <= 0:
        return False

    system = platform.system()

    if system in ("Linux", "Darwin"):
        # Try to send signal 0 (null signal) - doesn't kill, just checks existence
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    elif system == "Windows":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return str(pid) in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    else:
        # Unknown platform, assume it might be alive
        return True


def find_session_by_pid(sessions_cache: Dict[str, Any]) -> Optional[str]:
    """
    Find which cached session matches the current process by walking the process tree.

    Args:
        sessions_cache: The sessions cache dictionary for current directory
                       Format: {"sessions": {"session-id": {"ppid": 12345, ...}}, ...}

    Returns:
        Session ID if found, None otherwise
    """
    if not sessions_cache or "sessions" not in sessions_cache:
        return None

    # Get our parent PIDs
    parent_pids = get_parent_pids()
    if not parent_pids:
        return None

    # Check each cached session
    sessions = sessions_cache.get("sessions", {})
    for session_id, session_data in sessions.items():
        cached_ppid = session_data.get("ppid")
        if cached_ppid is None:
            continue

        # Check if the cached PPID is in our parent chain
        if cached_ppid in parent_pids:
            # Verify the PID is still alive
            if is_pid_alive(cached_ppid):
                return session_id

    return None


def get_current_ppid() -> int:
    """
    Get the parent process ID of the current process.

    Returns:
        Parent PID
    """
    return os.getppid()


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """
    Get information about a process.

    Args:
        pid: Process ID

    Returns:
        Dictionary with process info (name, cmdline, etc.) or None if not found
    """
    system = platform.system()

    if system == "Linux":
        return _get_process_info_linux(pid)
    elif system == "Darwin":
        return _get_process_info_macos(pid)
    elif system == "Windows":
        return _get_process_info_windows(pid)
    else:
        return None


def _get_process_info_linux(pid: int) -> Optional[Dict[str, Any]]:
    """Get process info on Linux using /proc filesystem."""
    try:
        stat_file = Path(f"/proc/{pid}/stat")
        cmdline_file = Path(f"/proc/{pid}/cmdline")

        if not stat_file.exists():
            return None

        stat_content = stat_file.read_text()
        # Extract comm (process name)
        start_paren = stat_content.find('(')
        end_paren = stat_content.rfind(')')
        if start_paren != -1 and end_paren != -1:
            name = stat_content[start_paren + 1:end_paren]
        else:
            name = "unknown"

        cmdline = ""
        if cmdline_file.exists():
            cmdline = cmdline_file.read_text().replace('\x00', ' ').strip()

        return {
            "pid": pid,
            "name": name,
            "cmdline": cmdline
        }
    except Exception:
        return None


def _get_process_info_macos(pid: int) -> Optional[Dict[str, Any]]:
    """Get process info on macOS using ps command."""
    try:
        # Get process name and command line
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm=,command="],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        if not output:
            return None

        # Parse output - first line has comm and full command
        lines = output.split('\n')
        if not lines:
            return None

        # ps output format: "comm command"
        parts = lines[0].split(maxsplit=1)
        name = parts[0] if parts else "unknown"
        cmdline = parts[1] if len(parts) > 1 else ""

        return {
            "pid": pid,
            "name": name,
            "cmdline": cmdline
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
        return None


def _get_process_info_windows(pid: int) -> Optional[Dict[str, Any]]:
    """Get process info on Windows using wmic or psutil."""
    try:
        # Try wmic first (built-in, no dependencies)
        result = subprocess.run(
            ["wmic", "process", "where", f"ProcessId={pid}", "get", "Name,CommandLine"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Skip header line, get data line
            if len(lines) >= 2:
                data_line = lines[1].strip()
                # Parse: "CommandLine Name"
                parts = data_line.split(maxsplit=1)
                if parts:
                    cmdline = parts[0] if parts else ""
                    name = parts[1] if len(parts) > 1 else "unknown"
                    return {
                        "pid": pid,
                        "name": name,
                        "cmdline": cmdline
                    }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: try psutil if available
    try:
        import psutil
        process = psutil.Process(pid)
        return {
            "pid": pid,
            "name": process.name(),
            "cmdline": " ".join(process.cmdline())
        }
    except (ImportError, Exception):
        return None
