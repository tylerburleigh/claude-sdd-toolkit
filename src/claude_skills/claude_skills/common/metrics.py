"""
Metrics collection system for Claude Skills.

Tracks skill and command usage, execution duration, and success/failure rates.
Automatically excludes metrics when running in test environments.
"""

import os
import sys
import json
import time
import shlex
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager


# Metrics storage location
METRICS_DIR = Path.home() / ".claude" / "metrics"
METRICS_FILE = METRICS_DIR / "skills.jsonl"

# Maximum file size before rotation (10MB)
MAX_METRICS_FILE_SIZE = 10 * 1024 * 1024


def _is_test_environment() -> bool:
    """
    Detect if we're running in a test environment.

    Returns True if any of the following conditions are met:
    1. pytest is loaded in sys.modules
    2. PYTEST_CURRENT_TEST environment variable is set
    3. DISABLE_METRICS environment variable is set
    """
    # Check for pytest in loaded modules
    if 'pytest' in sys.modules:
        return True

    # Check for pytest environment variable (set automatically by pytest)
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True

    # Check for manual disable flag
    if os.environ.get('DISABLE_METRICS'):
        return True

    return False


def _ensure_metrics_dir():
    """Ensure metrics directory exists."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)


def _rotate_metrics_file_if_needed():
    """Rotate metrics file if it exceeds max size."""
    if not METRICS_FILE.exists():
        return

    if METRICS_FILE.stat().st_size > MAX_METRICS_FILE_SIZE:
        # Rotate: skills.jsonl -> skills.jsonl.1
        # If skills.jsonl.1 exists, move to skills.jsonl.2, etc.
        rotation_index = 1
        while True:
            rotated_path = METRICS_FILE.with_suffix(f'.jsonl.{rotation_index}')
            if not rotated_path.exists():
                METRICS_FILE.rename(rotated_path)
                break
            rotation_index += 1


def record_metric(
    skill: str,
    command: str,
    duration_ms: int,
    status: str,
    exit_code: int,
    error_message: Optional[str] = None
):
    """
    Record a single metric entry to the JSONL file.

    Args:
        skill: Name of the skill (e.g., 'sdd-next', 'doc-query')
        command: Command/subcommand executed (e.g., 'discover', 'search')
        duration_ms: Execution duration in milliseconds
        status: 'success' or 'failure'
        exit_code: Command exit code (0 for success, non-zero for failure)
        error_message: Optional error message if status is 'failure'
    """
    # Skip if in test environment
    if _is_test_environment():
        return

    # Prepare metric entry
    metric = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'skill': skill,
        'command': command,
        'duration_ms': duration_ms,
        'status': status,
        'exit_code': exit_code
    }

    if error_message:
        metric['error'] = error_message

    # Ensure directory exists and rotate if needed
    _ensure_metrics_dir()
    _rotate_metrics_file_if_needed()

    # Append to JSONL file (atomic write with newline)
    try:
        with open(METRICS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metric) + '\n')
    except Exception:
        # Silent fail - metrics should never break the actual command
        pass


@contextmanager
def capture_metrics(skill: str, command: str):
    """
    Context manager for capturing metrics around a block of code.

    Usage:
        with capture_metrics('sdd-next', 'discover'):
            # do work
            pass

    Args:
        skill: Name of the skill
        command: Command being executed
    """
    if _is_test_environment():
        # In test environment, just yield without tracking
        yield
        return

    start_time = time.time()
    error_message = None
    exit_code = 0

    try:
        yield
    except Exception as e:
        error_message = str(e)
        exit_code = 1
        raise
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        status = 'success' if exit_code == 0 and not error_message else 'failure'
        record_metric(skill, command, duration_ms, status, exit_code, error_message)


def track_metrics(skill_name: str):
    """
    Decorator for tracking metrics on CLI main() functions.

    Usage:
        @track_metrics('sdd-next')
        def main():
            # CLI logic
            return 0  # exit code

    Args:
        skill_name: Name of the skill (e.g., 'sdd-next', 'doc-query')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip if in test environment
            if _is_test_environment():
                return func(*args, **kwargs)

            start_time = time.time()
            exit_code = 0
            error_message = None
            command = 'main'

            try:
                # Extract command from sys.argv, reconstructing quotes where needed
                if len(sys.argv) > 1:
                    # Use shlex.quote to add quotes around arguments with spaces/special chars
                    command = ' '.join(shlex.quote(arg) for arg in sys.argv[1:])

                exit_code = func(*args, **kwargs) or 0
                return exit_code

            except SystemExit as e:
                # Capture exit code from sys.exit() calls
                exit_code = e.code if e.code is not None else 0
                if exit_code != 0:
                    error_message = f"Command exited with code {exit_code}"
                raise

            except Exception as e:
                error_message = str(e)
                exit_code = 1
                raise

            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                status = 'success' if exit_code == 0 and not error_message else 'failure'
                record_metric(skill_name, command, duration_ms, status, exit_code, error_message)

        return wrapper
    return decorator


def get_metrics_file_path() -> Path:
    """Return the path to the metrics JSONL file."""
    return METRICS_FILE


def is_metrics_enabled() -> bool:
    """Check if metrics collection is enabled (not in test environment)."""
    return not _is_test_environment()
