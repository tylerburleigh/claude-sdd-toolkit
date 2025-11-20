"""
Documentation Helper Functions

Provides integration between SDD skills and the documentation/doc-query system.
These functions enable proactive documentation generation and context gathering.
"""

import json
import subprocess
import shutil
from typing import Optional
from pathlib import Path


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


def get_task_context_from_docs(task_description: str, project_root: str = ".") -> Optional[dict]:
    """
    Get task-relevant context from codebase documentation.

    Args:
        task_description: Description of the task to find context for
        project_root: Root directory of the project (default: current dir)

    Returns:
        dict | None: {
            "files": list[str],          # Suggested relevant files
            "dependencies": list[str],   # Related dependencies
            "similar": list[str],        # Similar implementations
            "complexity": dict           # Complexity insights
        } or None if unavailable

    Example:
        >>> context = get_task_context_from_docs("implement JWT auth")
        >>> if context:
        ...     print(f"Check these files: {context['files']}")
    """
    if not check_sdd_integration_available():
        return None

    try:
        # Execute sdd-integration task-context command
        proc = subprocess.run(
            ["sdd-integration", "task-context", task_description],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        if proc.returncode == 0:
            # Parse JSON output
            try:
                context = json.loads(proc.stdout)
                return context
            except json.JSONDecodeError:
                # If not JSON, return structured text
                return {
                    "files": [],
                    "dependencies": [],
                    "similar": [],
                    "complexity": {},
                    "raw_output": proc.stdout
                }
        else:
            return None

    except subprocess.TimeoutExpired:
        return None
    except Exception:
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
