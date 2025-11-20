"""
Cross-Skill Integration Utilities

Provides integration functions for SDD skills to work together seamlessly.
Includes spec validation, verification task execution, and session state management.
"""

import json
import logging
import subprocess
import time
from typing import Optional
from pathlib import Path
from datetime import datetime

from .hierarchy_validation import validate_spec_hierarchy

logger = logging.getLogger(__name__)


def validate_spec_before_proceed(spec_path: str, quiet: bool = False) -> dict:
    """
    Validate spec file before proceeding with task operations.

    Args:
        spec_path: Path to spec JSON file
        quiet: If True, suppress verbose output

    Returns:
        dict: {
            "valid": bool,               # Overall validation result
            "errors": list[dict],        # Critical errors
            "warnings": list[dict],      # Non-critical warnings
            "can_autofix": bool,         # Whether auto-fix is available
            "autofix_command": str       # Command to run for auto-fix
        }

    Example:
        >>> result = validate_spec_before_proceed("specs/auth-001.json")
        >>> if not result["valid"]:
        ...     if result["can_autofix"]:
        ...         print(f"Run: {result['autofix_command']}")
        ...     else:
        ...         print(f"Errors: {result['errors']}")
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "can_autofix": False,
        "autofix_command": ""
    }

    try:
        # Load and validate the spec
        with open(spec_path, 'r') as f:
            spec_data = json.load(f)

        # Use existing validation function
        validation_result = validate_spec_hierarchy(spec_data)

        # Check if validation passed
        if not validation_result.is_valid():
            result["valid"] = False

            # Collect all error messages from different categories
            all_errors = (
                validation_result.structure_errors +
                validation_result.hierarchy_errors +
                validation_result.node_errors +
                validation_result.count_errors +
                validation_result.dependency_errors +
                validation_result.metadata_errors +
                validation_result.cross_val_errors
            )

            for error_msg in all_errors:
                result["errors"].append({
                    "message": error_msg,
                    "path": spec_path,
                    "severity": "error"
                })

            # Collect all warning messages
            all_warnings = (
                validation_result.structure_warnings +
                validation_result.hierarchy_warnings +
                validation_result.node_warnings +
                validation_result.count_warnings +
                validation_result.dependency_warnings +
                validation_result.metadata_warnings +
                validation_result.cross_val_warnings
            )

            for warning_msg in all_warnings:
                result["warnings"].append({
                    "message": warning_msg,
                    "path": spec_path,
                    "severity": "warning"
                })

            # Check if auto-fix is possible
            # Common auto-fixable issues:
            autofix_patterns = [
                "missing required field",
                "invalid status",
                "timestamp format",
                "progress calculation"
            ]

            for error in result["errors"]:
                msg_lower = error["message"].lower()
                if any(pattern in msg_lower for pattern in autofix_patterns):
                    result["can_autofix"] = True
                    break

            if result["can_autofix"]:
                result["autofix_command"] = f"sdd-validate auto-fix {spec_path}"

        else:
            # Valid but may have warnings
            all_warnings = (
                validation_result.structure_warnings +
                validation_result.hierarchy_warnings +
                validation_result.node_warnings +
                validation_result.count_warnings +
                validation_result.dependency_warnings +
                validation_result.metadata_warnings +
                validation_result.cross_val_warnings
            )

            for warning_msg in all_warnings:
                result["warnings"].append({
                    "message": warning_msg,
                    "path": spec_path,
                    "severity": "warning"
                })

    except FileNotFoundError:
        result["valid"] = False
        result["errors"].append({
            "message": f"Spec file not found: {spec_path}",
            "path": spec_path,
            "severity": "critical"
        })
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append({
            "message": f"Invalid JSON: {str(e)}",
            "path": spec_path,
            "severity": "critical"
        })
    except Exception as e:
        result["valid"] = False
        result["errors"].append({
            "message": f"Validation error: {str(e)}",
            "path": spec_path,
            "severity": "error"
        })

    return result


def execute_verify_task(spec_data: dict, task_id: str, spec_root: str = ".", retry_count: int = 0) -> dict:
    """
    Execute a verification task based on its metadata.

    Args:
        spec_data: Loaded JSON spec data
        task_id: Task ID (e.g., "verify-1-1")
        spec_root: Root directory for the spec (default: current dir)
        retry_count: Current retry attempt number (internal use)

    Returns:
        dict: {
            "success": bool,             # Overall success
            "output": str,               # Execution output
            "errors": list[str],         # Error messages
            "skill_used": str | None,    # Skill invoked (if any)
            "duration": float,           # Execution time in seconds
            "on_failure": dict | None,   # on_failure configuration used
            "retry_count": int,          # Number of retries attempted
            "actions_taken": list[str]   # Actions taken on failure
        }

    Example:
        >>> spec_data = load_json_spec("auth-001", specs_dir)
        >>> result = execute_verify_task(spec_data, "verify-1-1")
        >>> if not result["success"]:
        ...     print(f"Verification failed: {result['errors']}")
        ...     print(f"Actions taken: {result['actions_taken']}")
    """
    result = {
        "success": False,
        "output": "",
        "errors": [],
        "skill_used": None,
        "duration": 0.0,
        "on_failure": None,
        "retry_count": retry_count,
        "actions_taken": []
    }

    start_time = time.time()

    try:
        # Find the verify task in the spec (check hierarchy first, then tasks for backward compat)
        verify_task = None
        if "hierarchy" in spec_data and task_id in spec_data["hierarchy"]:
            verify_task = spec_data["hierarchy"][task_id]
        elif "tasks" in spec_data and task_id in spec_data["tasks"]:
            verify_task = spec_data["tasks"][task_id]
        else:
            result["errors"].append(f"Verify task not found: {task_id}")
            return result

        # Check if task has verification metadata
        metadata = verify_task.get("metadata", {})
        verification_type = metadata.get("verification_type", "manual")

        # Store on_failure configuration
        on_failure = metadata.get("on_failure", {})
        result["on_failure"] = on_failure if on_failure else None

        if verification_type == "manual":
            result["errors"].append(f"Task {task_id} is manual verification - cannot auto-execute")
            return result

        # Get agent or command (support legacy 'skill' alias for compatibility)
        agent = metadata.get("agent") or metadata.get("skill")
        command = metadata.get("command")

        if not agent and not command:
            result["errors"].append(f"Task {task_id} has no skill or command specified")
            return result

        # Execute based on type
        if agent:
            result["agent_used"] = agent
            result["skill_used"] = agent
            execution_success = False

            # Agent registry - dispatch to appropriate handler
            if agent == "run-tests":
                # Execute run-tests skill
                test_command = command or "run"
                proc = subprocess.run(
                    ["run-tests", test_command],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes
                    cwd=spec_root
                )

                result["output"] = proc.stdout
                execution_success = proc.returncode == 0

                if not execution_success:
                    result["errors"].append(f"Tests failed with exit code {proc.returncode}")
                    if proc.stderr:
                        result["errors"].append(proc.stderr)

            elif agent == "sdd-validate":
                # Execute sdd-validate skill
                validate_command = ["sdd-validate", "validate"]
                if command:
                    validate_command.append(command)

                proc = subprocess.run(
                    validate_command,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minutes
                    cwd=spec_root
                )

                result["output"] = proc.stdout
                execution_success = proc.returncode == 0

                if not execution_success:
                    result["errors"].append(f"Validation failed with exit code {proc.returncode}")
                    if proc.stderr:
                        result["errors"].append(proc.stderr)

            elif agent == "code-doc":
                # Execute doc generation via unified CLI
                doc_command = ["sdd", "doc"]
                if command:
                    doc_command.extend(command.split())

                proc = subprocess.run(
                    doc_command,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes for doc generation
                    cwd=spec_root
                )

                result["output"] = proc.stdout
                execution_success = proc.returncode == 0

                if not execution_success:
                    result["errors"].append(f"Documentation check failed with exit code {proc.returncode}")
                    if proc.stderr:
                        result["errors"].append(proc.stderr)

            elif agent == "doc-query":
                # Execute doc-query skill
                query_command = ["doc-query"]
                if command:
                    query_command.extend(command.split())

                proc = subprocess.run(
                    query_command,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute
                    cwd=spec_root
                )

                result["output"] = proc.stdout
                execution_success = proc.returncode == 0

                if not execution_success:
                    result["errors"].append(f"Documentation query failed with exit code {proc.returncode}")
                    if proc.stderr:
                        result["errors"].append(proc.stderr)

            else:
                result["errors"].append(f"Unknown skill '{agent}'")
                execution_success = False

            result["success"] = execution_success

        elif command:
            # Execute command directly
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                shell=True,
                cwd=spec_root
            )

            result["output"] = proc.stdout
            result["success"] = proc.returncode == 0

            if not result["success"]:
                result["errors"].append(f"Command failed with exit code {proc.returncode}")
                if proc.stderr:
                    result["errors"].append(proc.stderr)

        # Handle failure with on_failure actions
        if not result["success"] and on_failure:
            # Check for retry logic
            max_retries = on_failure.get("max_retries", 0)
            if retry_count < max_retries:
                result["actions_taken"].append(f"Retrying (attempt {retry_count + 1}/{max_retries})")
                # Recursively retry
                time.sleep(1)  # Brief delay before retry
                retry_result = execute_verify_task(spec_data, task_id, spec_root, retry_count + 1)
                # If retry succeeds, return the successful result
                if retry_result["success"]:
                    return retry_result
                # If retry also fails, return the retry result with cumulative actions
                retry_result["actions_taken"] = result["actions_taken"] + retry_result["actions_taken"]
                return retry_result

            # Record notification action
            notify_method = on_failure.get("notify", "log")
            if notify_method and notify_method != "none":
                result["actions_taken"].append(f"Notification: {notify_method}")

            # Record consult action
            if on_failure.get("consult", False):
                result["actions_taken"].append("AI consultation recommended")

            # Record continue_on_failure setting
            if on_failure.get("continue_on_failure", False):
                result["actions_taken"].append("Continuing with other verifications")

    except subprocess.TimeoutExpired:
        result["errors"].append("Verification timed out")
        result["actions_taken"].append("Timeout occurred")
    except Exception as e:
        result["errors"].append(f"Execution error: {str(e)}")
        result["actions_taken"].append(f"Exception: {type(e).__name__}")
    finally:
        result["duration"] = time.time() - start_time

    return result


def get_session_state(specs_dir: Optional[str] = None) -> dict:
    """
    Get current session state for enhanced resumption.

    Args:
        specs_dir: Path to specs directory (auto-detected if None)

    Returns:
        dict: {
            "active_specs": list[dict],  # Active spec summaries
            "last_task": dict | None,    # Most recently modified task
            "timestamp": str,            # Last activity timestamp (ISO8601)
            "in_progress_count": int     # Number of in_progress tasks
        }

    Example:
        >>> state = get_session_state()
        >>> if state["last_task"]:
        ...     spec_id = state["last_task"]["spec_id"]
        ...     task_id = state["last_task"]["task_id"]
        ...     print(f"Resume work on {spec_id}:{task_id}?")
    """
    from .paths import find_specs_directory

    result = {
        "active_specs": [],
        "last_task": None,
        "timestamp": None,
        "in_progress_count": 0
    }

    try:
        # Find specs directory
        if specs_dir is None:
            specs_dir = find_specs_directory()

        if not specs_dir:
            return result

        specs_path = Path(specs_dir)
        active_dir = specs_path / "active"

        if not active_dir.exists():
            return result

        # Scan for active JSON specs
        active_specs = []
        all_in_progress_tasks = []

        for spec_file in active_dir.glob("*.json"):
            try:
                with open(spec_file, 'r') as f:
                    spec_data = json.load(f)

                # Get hierarchy and spec-root for modern spec structure
                hierarchy = spec_data.get("hierarchy", {})
                spec_root = hierarchy.get("spec-root", {})

                # Check if spec is active (not completed/archived)
                # Try hierarchy first, fall back to top-level for backward compatibility
                spec_status = spec_root.get("status", spec_data.get("status", "pending"))

                if spec_status in ["pending", "in_progress"]:
                    spec_id = spec_data.get("spec_id", spec_file.stem)

                    # Count in-progress tasks
                    in_progress_tasks = []

                    # Iterate through hierarchy to find in-progress tasks (modern structure)
                    for node_id, node_data in hierarchy.items():
                        node_type = node_data.get("type", "")
                        if node_type == "task" and node_data.get("status") == "in_progress":
                            # Use file mtime as proxy for task modification time
                            mtime = spec_file.stat().st_mtime

                            in_progress_tasks.append({
                                "spec_id": spec_id,
                                "task_id": node_id,
                                "title": node_data.get("title", "Untitled"),
                                "modified": datetime.fromtimestamp(mtime).isoformat(),
                                "mtime": mtime
                            })

                    # Fall back to legacy tasks structure for backward compatibility
                    if not in_progress_tasks:
                        tasks = spec_data.get("tasks", {})
                        for task_id, task_data in tasks.items():
                            if task_data.get("status") == "in_progress":
                                mtime = spec_file.stat().st_mtime
                                in_progress_tasks.append({
                                    "spec_id": spec_id,
                                    "task_id": task_id,
                                    "title": task_data.get("title", "Untitled"),
                                    "modified": datetime.fromtimestamp(mtime).isoformat(),
                                    "mtime": mtime
                                })

                    # Add to active specs list
                    # Get title from hierarchy first, fall back to top-level
                    spec_title = spec_root.get("title", spec_data.get("title", "Untitled Spec"))

                    active_specs.append({
                        "spec_id": spec_id,
                        "title": spec_title,
                        "status": spec_status,
                        "in_progress_tasks": len(in_progress_tasks)
                    })

                    all_in_progress_tasks.extend(in_progress_tasks)

            except Exception as e:
                # Skip invalid JSON specs, but log the error
                logger.warning(f"Skipping spec {spec_file.name}: {str(e)}")
                continue

        result["active_specs"] = active_specs
        result["in_progress_count"] = len(all_in_progress_tasks)

        # Find most recent in-progress task
        if all_in_progress_tasks:
            # Sort by modification time
            all_in_progress_tasks.sort(key=lambda x: x["mtime"], reverse=True)
            last_task = all_in_progress_tasks[0]

            # Remove mtime from result
            last_task_clean = {
                "spec_id": last_task["spec_id"],
                "task_id": last_task["task_id"],
                "title": last_task["title"],
                "modified": last_task["modified"]
            }

            result["last_task"] = last_task_clean
            result["timestamp"] = last_task["modified"]

    except Exception as e:
        # Log error but return partial results
        logger.error(f"Error in get_session_state: {str(e)}")

    return result
