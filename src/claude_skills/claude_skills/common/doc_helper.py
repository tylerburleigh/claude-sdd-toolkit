"""
Documentation Helper Functions

Provides integration between SDD skills and the documentation/doc-query system.
These functions enable proactive documentation generation and context gathering.
"""

import json
import logging
import subprocess
import shutil
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def get_current_git_commit(project_root: str = ".") -> Optional[str]:
    """
    Get the current HEAD commit SHA.

    Args:
        project_root: Root directory of the project

    Returns:
        str | None: Full commit SHA or None if not a git repo
    """
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=project_root
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"get_current_git_commit failed: {e}")
    return None


def count_commits_between(commit_a: str, commit_b: str, project_root: str = ".") -> int:
    """
    Count commits between two git commits.

    Args:
        commit_a: Earlier commit SHA (e.g., when docs were generated)
        commit_b: Later commit SHA (e.g., current HEAD)
        project_root: Root directory of the project

    Returns:
        int: Number of commits between commit_a and commit_b (0 if error)
    """
    try:
        # Use git rev-list to count commits
        proc = subprocess.run(
            ["git", "rev-list", "--count", f"{commit_a}..{commit_b}"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if proc.returncode == 0:
            return int(proc.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, Exception) as e:
        logger.debug(f"count_commits_between failed ({commit_a}..{commit_b}): {e}")
    return 0


def get_current_git_commit(project_root: str = ".") -> Optional[str]:
    """
    Get the current HEAD commit SHA.

    Args:
        project_root: Root directory of the project

    Returns:
        str | None: Full commit SHA or None if not a git repo
    """
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=project_root
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None


def count_commits_between(commit_a: str, commit_b: str, project_root: str = ".") -> int:
    """
    Count commits between two git commits.

    Args:
        commit_a: Earlier commit SHA (e.g., when docs were generated)
        commit_b: Later commit SHA (e.g., current HEAD)
        project_root: Root directory of the project

    Returns:
        int: Number of commits between commit_a and commit_b (0 if error)
    """
    try:
        # Use git rev-list to count commits
        proc = subprocess.run(
            ["git", "rev-list", "--count", f"{commit_a}..{commit_b}"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if proc.returncode == 0:
            return int(proc.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, Exception):
        pass
    return 0


def count_files_changed_between(commit_a: str, commit_b: str, project_root: str = ".") -> int:
    """
    Count files changed between two git commits.

    Args:
        commit_a: Earlier commit SHA
        commit_b: Later commit SHA
        project_root: Root directory of the project

    Returns:
        int: Number of files changed (0 if error)
    """
    try:
        # Use git diff to count changed files
        proc = subprocess.run(
            ["git", "diff", "--name-only", commit_a, commit_b],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if proc.returncode == 0:
            files = [line for line in proc.stdout.strip().split('\n') if line]
            return len(files)
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return 0


def check_doc_query_available() -> dict:
    """
    Check if doc-query documentation exists and is accessible.

    Returns:
        dict: {
            "available": bool,           # True if doc-query can be used
            "message": str,              # Human-readable status message
            "stats": dict | None,        # Stats from doc-query if available
            "location": str | None       # Path to documentation
        }

    Example:
        >>> result = check_doc_query_available()
        >>> if result["available"]:
        ...     print(f"Documentation found at {result['location']}")
    """
    result = {
        "available": False,
        "message": "",
        "stats": None,
        "location": None
    }

    try:
        # Run doc-query stats to check availability
        proc = subprocess.run(
            ["doc-query", "stats"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if proc.returncode == 0:
            # Parse the output to extract stats
            output = proc.stdout.strip()

            # Try to find location in output
            for line in output.split('\n'):
                if 'Documentation location:' in line or 'Location:' in line:
                    result["location"] = line.split(':', 1)[1].strip()
                    break

            # Extract basic stats (simplified parsing)
            stats = {}
            for line in output.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to convert numbers
                    try:
                        if value.isdigit():
                            stats[key] = int(value)
                        else:
                            stats[key] = value
                    except:
                        stats[key] = value

            result["available"] = True
            result["message"] = "Documentation available"
            result["stats"] = stats if stats else None
        else:
            result["message"] = "Documentation not found or doc-query command failed"

    except FileNotFoundError:
        result["message"] = "doc-query command not found in PATH"
    except subprocess.TimeoutExpired:
        result["message"] = "doc-query command timed out"
    except Exception as e:
        result["message"] = f"Error checking doc-query: {str(e)}"

    return result


def check_sdd_integration_available() -> bool:
    """
    Check if sdd-integration command is available in PATH.

    Returns:
        bool: True if sdd-integration command exists and is executable

    Example:
        >>> if check_sdd_integration_available():
        ...     context = get_task_context_from_docs("implement auth")
    """
    return shutil.which("sdd-integration") is not None


def get_task_context_from_docs(
    task_description: str,
    project_root: str = ".",
    file_path: Optional[str] = None,
    spec_id: Optional[str] = None
) -> Optional[dict]:
    """
    Get task-relevant context from codebase documentation with provenance metadata.

    Args:
        task_description: Description of the task to find context for
        project_root: Root directory of the project (default: current dir)
        file_path: Optional specific file path to focus context on
        spec_id: Optional spec ID for additional context

    Returns:
        dict | None: {
            "files": list[str],          # Suggested relevant files
            "dependencies": list[str],   # Related dependencies
            "similar": list[str],        # Similar implementations
            "complexity": dict,          # Complexity insights
            "provenance": {              # Metadata about doc source
                "source_doc_id": str,    # Documentation location
                "generated_at": str,     # ISO timestamp
                "generated_at_commit": str,  # Git SHA when docs generated
                "freshness_ms": int      # Query execution time
            }
        } or None if unavailable

    Example:
        >>> context = get_task_context_from_docs(
        ...     "implement JWT auth",
        ...     file_path="src/auth.py"
        ... )
        >>> if context:
        ...     print(f"Check these files: {context['files']}")
        ...     print(f"Freshness: {context['provenance']['freshness_ms']}ms")
    """
    if not check_sdd_integration_available():
        return None

    try:
        import time
        start_time = time.time()

        # Build command with optional parameters
        cmd = ["sdd-integration", "task-context", task_description]
        if file_path:
            cmd.extend(["--file-path", file_path])
        if spec_id:
            cmd.extend(["--spec-id", spec_id])

        # Execute sdd-integration task-context command
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        query_time_ms = int((time.time() - start_time) * 1000)

        if proc.returncode == 0:
            # Parse JSON output
            try:
                context = json.loads(proc.stdout)
                logger.debug(f"get_task_context_from_docs: returned {len(context.get('files', []))} files in {query_time_ms}ms")
                return context
            except json.JSONDecodeError:
                logger.debug(f"get_task_context_from_docs: non-JSON output, returning raw")
                # If not JSON, return structured text
                return {
                    "files": [],
                    "dependencies": [],
                    "similar": [],
                    "complexity": {},
                    "raw_output": proc.stdout
                }
        else:
            logger.debug(f"get_task_context_from_docs: sdd-integration returned code {proc.returncode}")
            return None

    except subprocess.TimeoutExpired:
        logger.debug("get_task_context_from_docs: subprocess timed out")
        return None
    except Exception as e:
        logger.debug(f"get_task_context_from_docs: exception {e}")
        return None


def get_call_context_from_docs(
    function_name: Optional[str] = None,
    file_path: Optional[str] = None,
    project_root: str = "."
) -> Optional[dict]:
    """
    Get call graph context from codebase documentation.

    Retrieves caller/callee information for a function or file using the
    sdd-integration call-context command.

    Args:
        function_name: Name of the function to query callers/callees for
        file_path: Path to file to get call context for all functions
        project_root: Root directory of the project (default: current dir)

    Returns:
        dict | None: {
            "function_name": str | None,  # The queried function (if provided)
            "file_path": str | None,      # The queried file (if provided)
            "callers": list[dict],        # List of {name, file, line}
            "callees": list[dict],        # List of {name, file, line}
            "functions_found": list[str]  # Functions found matching query
        } or None if unavailable

    Raises:
        ValueError: If neither function_name nor file_path is provided

    Example:
        >>> context = get_call_context_from_docs(function_name="process_data")
        >>> if context:
        ...     print(f"Callers: {len(context['callers'])}")
        ...     print(f"Callees: {len(context['callees'])}")
    """
    if not function_name and not file_path:
        raise ValueError("Either function_name or file_path must be provided")

    if not check_sdd_integration_available():
        logger.debug("get_call_context_from_docs: sdd-integration not available")
        return None

    try:
        # Build command
        cmd = ["sdd-integration", "call-context"]
        if function_name:
            cmd.extend(["--function", function_name])
        if file_path:
            cmd.extend(["--file", file_path])
        cmd.append("--json")

        # Execute command
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        if proc.returncode == 0:
            try:
                context = json.loads(proc.stdout)
                logger.debug(
                    f"get_call_context_from_docs: returned "
                    f"{len(context.get('callers', []))} callers, "
                    f"{len(context.get('callees', []))} callees"
                )
                return context
            except json.JSONDecodeError:
                logger.debug("get_call_context_from_docs: non-JSON output")
                return None
        else:
            logger.debug(
                f"get_call_context_from_docs: sdd-integration returned code {proc.returncode}"
            )
            return None

    except subprocess.TimeoutExpired:
        logger.debug("get_call_context_from_docs: subprocess timed out")
        return None
    except Exception as e:
        logger.debug(f"get_call_context_from_docs: exception {e}")
        return None


def get_test_context_from_docs(
    module_path: str,
    project_root: str = "."
) -> Optional[dict]:
    """
    Get test context for a module from codebase documentation.

    Retrieves test files and test functions related to a module
    using the sdd-integration test-context command.

    Args:
        module_path: Path to the module to analyze
        project_root: Root directory of the project (default: current dir)

    Returns:
        dict | None: {
            "module": str,            # The module path queried
            "test_files": list[str],  # Test file paths
            "test_functions": list[str],  # Test function names
            "test_classes": list[str],    # Test class names
        } or None if unavailable

    Example:
        >>> context = get_test_context_from_docs("src/auth.py")
        >>> if context:
        ...     print(f"Test files: {context['test_files']}")
    """
    if not check_sdd_integration_available():
        logger.debug("get_test_context_from_docs: sdd-integration not available")
        return None

    try:
        # Build command
        cmd = ["sdd-integration", "test-context", module_path, "--json"]

        # Execute command
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        if proc.returncode == 0:
            try:
                context = json.loads(proc.stdout)
                logger.debug(
                    f"get_test_context_from_docs: returned "
                    f"{len(context.get('test_files', []))} test files, "
                    f"coverage={context.get('coverage_estimate', 'unknown')}"
                )
                return context
            except json.JSONDecodeError:
                logger.debug("get_test_context_from_docs: non-JSON output")
                return None
        else:
            logger.debug(
                f"get_test_context_from_docs: sdd-integration returned code {proc.returncode}"
            )
            return None

    except subprocess.TimeoutExpired:
        logger.debug("get_test_context_from_docs: subprocess timed out")
        return None
    except Exception as e:
        logger.debug(f"get_test_context_from_docs: exception {e}")
        return None


def get_complexity_hotspots_from_docs(
    file_path: Optional[str] = None,
    threshold: int = 5,
    project_root: str = "."
) -> Optional[dict]:
    """
    Get complexity hotspots from codebase documentation.

    Retrieves high-complexity functions that may need careful attention
    using the sdd-integration complexity command.

    Args:
        file_path: Optional path to filter results to a specific file
        threshold: Complexity threshold (default: 5)
        project_root: Root directory of the project (default: current dir)

    Returns:
        dict | None: {
            "file_path": str | None,       # The file filter (if provided)
            "threshold": int,              # The complexity threshold used
            "hotspots": list[dict],        # List of {name, complexity, line, file}
            "total_count": int             # Total number of hotspots
        } or None if unavailable

    Example:
        >>> result = get_complexity_hotspots_from_docs(
        ...     file_path="src/auth.py",
        ...     threshold=5
        ... )
        >>> if result:
        ...     for hotspot in result['hotspots']:
        ...         print(f"{hotspot['name']}: {hotspot['complexity']}")
    """
    if not check_sdd_integration_available():
        logger.debug("get_complexity_hotspots_from_docs: sdd-integration not available")
        return None

    try:
        # Build command
        cmd = ["sdd-integration", "complexity", "--json"]
        if file_path:
            cmd.extend(["--file", file_path])
        cmd.extend(["--threshold", str(threshold)])

        # Execute command
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        if proc.returncode == 0:
            try:
                result = json.loads(proc.stdout)
                logger.debug(
                    f"get_complexity_hotspots_from_docs: returned "
                    f"{result.get('total_count', 0)} hotspots"
                )
                return result
            except json.JSONDecodeError:
                logger.debug("get_complexity_hotspots_from_docs: non-JSON output")
                return None
        else:
            logger.debug(
                f"get_complexity_hotspots_from_docs: sdd-integration returned code {proc.returncode}"
            )
            return None

    except subprocess.TimeoutExpired:
        logger.debug("get_complexity_hotspots_from_docs: subprocess timed out")
        return None
    except Exception as e:
        logger.debug(f"get_complexity_hotspots_from_docs: exception {e}")
        return None


def should_generate_docs(project_root: str = ".", interactive: bool = True) -> dict:
    """
    Check if documentation should be generated.

    Args:
        project_root: Root directory of the project
        interactive: If True, may prompt user for decision

    Returns:
        dict: {
            "should_generate": bool,     # Recommendation
            "reason": str,               # Explanation
            "available": bool,           # Current doc availability
            "user_confirmed": bool | None # User response (if interactive)
        }

    Example:
        >>> result = should_generate_docs()
        >>> if result["should_generate"] and result["user_confirmed"]:
        ...     # Run doc generation
        ...     print("Generating documentation...")
    """
    # Check if docs are already available
    doc_check = check_doc_query_available()

    result = {
        "should_generate": False,
        "reason": "",
        "available": doc_check["available"],
        "user_confirmed": None
    }

    if doc_check["available"]:
        result["reason"] = "Documentation already available"
        return result

    # Docs are missing
    result["should_generate"] = True
    result["reason"] = "No documentation found - generation recommended for faster analysis"

    if interactive:
        # In practice, this would prompt the user
        # For now, we return the recommendation without actual prompting
        # The calling code can handle the interactive prompt
        pass

    return result


def ensure_documentation_exists(
    project_root: Optional[str] = None,
    prompt_user: bool = True,
    auto_generate: bool = False
) -> tuple[bool, str]:
    """
    Ensure codebase documentation exists, optionally generating it.

    This is a high-level convenience function that combines:
    - check_doc_query_available() - Check if docs exist
    - should_generate_docs() - Determine if generation is needed
    - `sdd doc generate` command invocation - Actually generate docs

    Args:
        project_root: Root directory (default: auto-detect)
        prompt_user: If True, prompt user to generate missing docs
        auto_generate: If True, auto-generate without prompting

    Returns:
        tuple[bool, str]: (success, message)
            - success: True if docs are available (existing or newly generated)
            - message: Path to docs OR error/info message

    Example:
        >>> # In sdd-plan Phase 1.2
        >>> success, result = ensure_documentation_exists(prompt_user=True)
        >>> if success:
        ...     print(f"Using docs at: {result}")
        ...     # Proceed with doc-query analysis
        ... else:
        ...     print(f"No docs: {result}")
        ...     # Fall back to manual exploration
    """
    if project_root is None:
        project_root = str(Path.cwd())

    # Fast path: Check if docs already exist
    doc_check = check_doc_query_available()

    if doc_check["available"]:
        location = doc_check.get("location") or "unknown location"
        return True, location

    # Docs don't exist - check if we should generate
    generation_check = should_generate_docs(project_root, interactive=prompt_user)

    if not generation_check["should_generate"]:
        return False, "Documentation not available and generation not recommended"

    # Auto-generate if requested
    if auto_generate:
        try:
            # Invoke doc generation via unified CLI
            proc = subprocess.run(
                ["sdd", "doc", "generate", project_root],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            if proc.returncode == 0:
                # Re-check availability
                doc_check = check_doc_query_available()
                if doc_check["available"]:
                    location = doc_check.get("location") or "unknown location"
                    return True, location
                else:
                    return False, "Documentation generation completed but docs not found"
            else:
                return False, f"Documentation generation failed: {proc.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Documentation generation timed out"
        except FileNotFoundError:
            return False, "sdd command not found in PATH"
        except Exception as e:
            return False, f"Error generating documentation: {str(e)}"

    # If prompt_user is True, return recommendation for user to decide
    if prompt_user:
        return False, "Documentation not found - recommend running `sdd doc generate`"

    # No auto-generate, no prompt - just return not available
    return False, "Documentation not available"
