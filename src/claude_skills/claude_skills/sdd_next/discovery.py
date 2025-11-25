"""
Task discovery and analysis operations for SDD workflows.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

# Clean imports
from claude_skills.common import load_json_spec, get_node, get_progress_summary
from .context_utils import (
    get_previous_sibling,
    get_parent_context,
    get_phase_context,
    get_sibling_files,
    get_task_journal_summary,
    collect_phase_task_ids,
    get_dependency_details,
    get_plan_validation_context,
    get_enhanced_sibling_files,
)
from claude_skills.common import (
    validate_spec_before_proceed,
    get_task_context_from_docs,
    get_call_context_from_docs,
    get_test_context_from_docs,
    check_doc_query_available,
)
from claude_skills.common.doc_integration import (
    check_doc_availability,
    prompt_for_generation,
    clear_doc_status_cache,
    DocStatus
)
from claude_skills.common.paths import find_spec_file
from claude_skills.common.completion import check_spec_completion, should_prompt_completion
from claude_skills.common.git_metadata import find_git_root, check_dirty_tree
from claude_skills.common.git_config import is_git_enabled
from claude_skills.common.sdd_config import get_doc_context_settings

logger = logging.getLogger(__name__)

# Pattern to detect file references in task description/title
import re
_FILE_PATTERN = re.compile(r'\b[\w./]+\.(py|ts|tsx|js|jsx|go|rs|java|rb|c|cpp|h|hpp|cs|swift|kt|scala|vue|svelte|md|json|yaml|yml|toml)\b', re.IGNORECASE)


def _should_gather_doc_context(task_data: dict) -> bool:
    """
    Determine if doc context would be valuable for this task.

    Skips doc context gathering for abstract/meta tasks that have no
    file associations, reducing unnecessary subprocess calls.

    Args:
        task_data: Task metadata from spec

    Returns:
        bool: True if doc context should be gathered
    """
    # Always gather if task has explicit file_path
    file_path = task_data.get("metadata", {}).get("file_path")
    if file_path:
        return True

    # Check if description or title mentions specific files
    description = task_data.get("description", "")
    title = task_data.get("title", "")
    combined_text = f"{title} {description}"

    if _FILE_PATTERN.search(combined_text):
        return True

    # Skip for abstract tasks with no file references
    logger.debug(f"Doc context: skipping (no file references in task)")
    return False


def is_unblocked(spec_data: Dict, task_id: str, task_data: Dict) -> bool:
    """
    Check if all blocking dependencies are completed.

    This checks both task-level dependencies and phase-level dependencies.
    A task is blocked if:
    1. Any of its direct task dependencies are not completed, OR
    2. Its parent phase is blocked by an incomplete phase

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier
        task_data: Task data dictionary

    Returns:
        True if task has no blockers or all blockers are completed
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Check task-level dependencies
    blocked_by = task_data.get("dependencies", {}).get("blocked_by", [])
    for blocker_id in blocked_by:
        blocker = hierarchy.get(blocker_id)
        if not blocker or blocker.get("status") != "completed":
            return False

    # Check phase-level dependencies
    # Walk up to find the parent phase
    parent_phase_id = None
    current = task_data
    while current:
        parent_id = current.get("parent")
        if not parent_id:
            break
        parent = hierarchy.get(parent_id)
        if not parent:
            break
        if parent.get("type") == "phase":
            parent_phase_id = parent_id
            break
        current = parent

    # If task belongs to a phase, check if that phase is blocked
    if parent_phase_id:
        parent_phase = hierarchy.get(parent_phase_id)
        if parent_phase:
            phase_blocked_by = parent_phase.get("dependencies", {}).get("blocked_by", [])
            for blocker_id in phase_blocked_by:
                blocker = hierarchy.get(blocker_id)
                if not blocker or blocker.get("status") != "completed":
                    return False

    return True


def is_in_current_phase(spec_data: Dict, task_id: str, phase_id: str) -> bool:
    """
    Check if task belongs to current phase (including nested groups).

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier
        phase_id: Phase identifier to check against

    Returns:
        True if task is within the phase hierarchy
    """
    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return False

    # Walk up parent chain to find phase
    current = task
    while current:
        parent_id = current.get("parent")
        if parent_id == phase_id:
            return True
        if not parent_id:
            return False
        current = hierarchy.get(parent_id)
    return False


def get_next_task(spec_data: Dict) -> Optional[Tuple[str, Dict]]:
    """
    Find the next actionable task.

    Args:
        spec_data: JSON spec file data

    Returns:
        Tuple of (task_id, task_data) or None if no task available
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Get all phases in order
    spec_root = hierarchy.get("spec-root", {})
    phase_order = spec_root.get("children", [])

    # Build list of phases to check: in_progress first, then pending
    phases_to_check = []

    # First, add any in_progress phases
    for phase_id in phase_order:
        phase = hierarchy.get(phase_id, {})
        if phase.get("type") == "phase" and phase.get("status") == "in_progress":
            phases_to_check.append(phase_id)

    # Then add pending phases
    for phase_id in phase_order:
        phase = hierarchy.get(phase_id, {})
        if phase.get("type") == "phase" and phase.get("status") == "pending":
            phases_to_check.append(phase_id)

    if not phases_to_check:
        return None

    # Try each phase until we find actionable tasks
    for current_phase in phases_to_check:
        # Find first available task or subtask in current phase
        # Prefer leaf tasks (no children) over parent tasks
        candidates = []
        for key, value in hierarchy.items():
            if (value.get("type") in ["task", "subtask", "verify"] and
                value.get("status") == "pending" and
                is_unblocked(spec_data, key, value) and
                is_in_current_phase(spec_data, key, current_phase)):
                has_children = len(value.get("children", [])) > 0
                candidates.append((key, value, has_children))

        if candidates:
            # Sort: leaf tasks first (has_children=False), then by ID
            candidates.sort(key=lambda x: (x[2], x[0]))
            return (candidates[0][0], candidates[0][1])

    # No actionable tasks found in any phase
    return None


def get_task_info(spec_data: Dict, task_id: str) -> Optional[Dict]:
    """
    Get detailed information about a task.

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier

    Returns:
        Task data dictionary or None
    """
    return get_node(spec_data, task_id)


def check_dependencies(spec_data: Dict, task_id: str) -> Dict:
    """
    Check dependency status for a task.

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier

    Returns:
        Dictionary with dependency analysis
    """
    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)

    if not task:
        return {"error": f"Task {task_id} not found"}

    deps = task.get("dependencies", {})
    blocked_by = deps.get("blocked_by", [])
    depends = deps.get("depends", [])
    blocks = deps.get("blocks", [])

    result = {
        "task_id": task_id,
        "can_start": is_unblocked(spec_data, task_id, task),
        "blocked_by": [],
        "soft_depends": [],
        "blocks": []
    }

    # Get info for blocking tasks
    for dep_id in blocked_by:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["blocked_by"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    # Get info for soft dependencies
    for dep_id in depends:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["soft_depends"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    # Get info for tasks this blocks
    for dep_id in blocks:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["blocks"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    return result


def prepare_task(
    spec_id: str,
    specs_dir: Path,
    task_id: Optional[str] = None,
    include_full_journal: bool = False,
    include_phase_history: bool = False,
    include_spec_overview: bool = False,
) -> Dict:
    """
    Prepare complete context for task implementation.

    Combines task discovery, dependency checking, and detail extraction.
    Includes automatic spec validation, doc-query context gathering, and
    completion detection when no actionable tasks are found.

    When no actionable tasks are found, checks if the spec is complete
    (all tasks completed) vs. blocked (tasks waiting on dependencies).
    Returns completion information for caller to handle.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        task_id: Optional task ID (auto-discovers if not provided)

    Returns:
        Complete task preparation data with validation and context.

        When no tasks found:
        - If spec complete: success=True, spec_complete=True, completion_info set
        - If tasks blocked: success=False, spec_complete=False, completion_info set

        Fields:
            success (bool): True if task found or spec complete
            task_id (str|None): Next task ID if found
            task_data (dict|None): Task details if found
            spec_complete (bool): True if all tasks completed
            completion_info (dict|None): Completion check details
            error (str|None): Error message if applicable
    """
    result = {
        "success": False,
        "task_id": task_id,
        "task_data": None,
        "task_details": None,
        "dependencies": None,
        "spec_file": None,
        "doc_context": None,
        "validation_warnings": [],
        "git_warnings": [],
        "repo_root": None,
        "needs_branch_creation": False,
        "dirty_tree_status": None,
        "suggested_branch_name": None,
        "needs_commit_cadence": False,
        "commit_cadence_options": None,
        "suggested_commit_cadence": None,
        "spec_complete": False,
        "completion_info": None,
        "context": None,
        "extended_context": None,
        "error": None
    }

    # Phase 1: Find spec file and validate before proceeding
    # Search in pending/, active/, completed/, archived/
    spec_path = find_spec_file(spec_id, specs_dir)
    if not spec_path:
        result["error"] = f"Spec file not found for {spec_id}"
        return result

    validation_result = validate_spec_before_proceed(str(spec_path), quiet=True)

    if not validation_result["valid"]:
        # Spec has critical errors - suggest fixing before proceeding
        error_summary = f"Spec validation failed with {len(validation_result['errors'])} error(s)"
        if validation_result["can_autofix"]:
            error_summary += f"\n\nSuggested fix: {validation_result['autofix_command']}"
        else:
            error_summary += "\n\nErrors:\n" + "\n".join([
                f"  - {err['message']}" for err in validation_result['errors'][:3]
            ])
        result["error"] = error_summary
        return result

    # Store any warnings for reporting (non-blocking)
    if validation_result["warnings"]:
        result["validation_warnings"] = [w["message"] for w in validation_result["warnings"]]

    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        result["error"] = "Failed to load JSON spec"
        return result

    # Phase 2: Git Integration - Repo root detection and drift detection
    # Step 1: Find git repository root
    try:
        repo_root = find_git_root(spec_path.parent)

        if repo_root is None:
            # Not in a git repository - skip all git operations
            logger.debug("No git repository found, skipping git operations")
            result["repo_root"] = None
        else:
            # Step 2: Check if git integration is enabled
            if not is_git_enabled(repo_root):
                logger.debug("Git integration is disabled, skipping git operations")
                result["repo_root"] = str(repo_root)
            else:
                result["repo_root"] = str(repo_root)

                # Note: Git metadata is no longer stored in specs
                # Git information is queried on-demand from git/gh CLIs
                logger.debug("Git integration enabled, repo_root available for git operations")

                # Check dirty tree status
                is_dirty, dirty_message = check_dirty_tree(repo_root)
                result["dirty_tree_status"] = {
                    "is_dirty": is_dirty,
                    "message": dirty_message
                }

                result["repo_root"] = str(repo_root)
    except Exception as e:
        # Git operations should not block task preparation
        logger.warning(f"Git operations failed: {e}")
        result["git_warnings"] = [f"Git operations error: {str(e)}"]
        result["repo_root"] = None

    # Check if spec is in pending folder
    if '/pending/' in str(spec_path):
        result["error"] = (
            f"This spec is in your pending backlog. "
            f"Run 'sdd activate-spec {spec_id}' to move it to active/ before starting work."
        )
        return result

    # Get task ID if not provided
    if not task_id:
        next_task = get_next_task(spec_data)
        if not next_task:
            # Check if spec is complete before returning error
            completion_check = should_prompt_completion(spec_data)

            if completion_check["should_prompt"]:
                # Spec is complete - return success with completion flag
                result["success"] = True
                result["spec_complete"] = True
                result["completion_info"] = completion_check
                result["error"] = None
                return result
            else:
                # Not complete - return error with completion context
                result["error"] = "No actionable tasks found"
                result["spec_complete"] = False
                result["completion_info"] = completion_check
                return result
        task_id, _ = next_task
        result["task_id"] = task_id

    # Get task info from state
    task_data = get_task_info(spec_data, task_id)
    if not task_data:
        result["error"] = f"Task {task_id} not found in state"
        return result

    result["task_data"] = task_data

    # Check dependencies
    deps = check_dependencies(spec_data, task_id)
    result["dependencies"] = deps

    # Phase 3: Context gathering from doc-query (Priority 1 Integration)
    # Check documentation availability first (proactive)
    doc_status = check_doc_availability()
    logger.debug(f"Doc context: status={doc_status.value}")

    # If docs are missing or stale, note this for CLI to handle
    # (Library functions can't directly invoke skills or prompt, so we flag it)
    if doc_status in (DocStatus.MISSING, DocStatus.STALE):
        # Store status in result for CLI layer to handle
        result["doc_status"] = doc_status.value
        result["doc_prompt_needed"] = True
        logger.debug(f"Doc context: skipped (status={doc_status.value}, prompt_needed=True)")

    # Automatically gather codebase context ONLY if documentation is fresh (AVAILABLE)
    # Stale docs are omitted to signal agent should use manual exploration
    # Also skip for abstract tasks with no file references (lazy evaluation)
    if doc_status == DocStatus.AVAILABLE and _should_gather_doc_context(task_data):
        doc_check = check_doc_query_available()
        if doc_check["available"]:
            logger.debug("Doc context: gathering context from doc-query")
            # Extract task description for context gathering
            task_title = task_data.get("title", "")
            task_description = task_data.get("description", task_title)

            # Extract file_path from task metadata if available
            task_file_path = task_data.get("metadata", {}).get("file_path")

            # Get context from documentation with enhanced parameters
            doc_context = get_task_context_from_docs(
                task_description,
                project_root=str(spec_path.parent),
                file_path=task_file_path,
                spec_id=spec_id
            )
            if doc_context:
                result["doc_context"] = doc_context
                logger.debug(f"Doc context: gathered {len(doc_context.get('files', []))} files")

                # Add helpful message
                if doc_context.get("files"):
                    result["doc_context"]["message"] = (
                        f"Found {len(doc_context['files'])} relevant files from codebase documentation"
                    )
            else:
                logger.debug("Doc context: get_task_context_from_docs returned None")

    # Phase 4: Prepare enhanced context payload (defensive)
    try:
        hierarchy = spec_data.get("hierarchy", {})
        task_node = hierarchy.get(task_id, {})
        previous_sibling = get_previous_sibling(spec_data, task_id)
        parent_task = get_parent_context(spec_data, task_id)
        phase_context = get_phase_context(spec_data, task_id)
        sibling_files = get_enhanced_sibling_files(spec_data, task_id)
        task_journal = get_task_journal_summary(spec_data, task_id)
        dependency_details = get_dependency_details(spec_data, task_id)
        plan_validation = get_plan_validation_context(spec_data, task_id)

        parent_warning = None
        parent_pointer = task_node.get("parent") if isinstance(task_node, dict) else None
        if parent_task is None:
            if parent_pointer is None:
                parent_warning = {"parent_missing": True}
            elif parent_pointer not in hierarchy:
                parent_warning = {
                    "parent_missing": True,
                    "missing_parent_id": parent_pointer,
                }

        result["context"] = {
            "previous_sibling": previous_sibling,
            "parent_task": parent_task,
            "phase": phase_context,
            "sibling_files": sibling_files,
            "task_journal": task_journal,
            "dependencies": dependency_details,
        }

        # Add file_docs to context if doc_context is available
        if result.get("doc_context"):
            file_docs = dict(result["doc_context"])

            # Gather enrichment context if we have a file_path and docs are available
            task_file_path = task_data.get("metadata", {}).get("file_path")
            if task_file_path and doc_status == DocStatus.AVAILABLE:
                # Load enrichment settings from config
                doc_settings = get_doc_context_settings(spec_path.parent)
                project_root = str(spec_path.parent)

                # Run enabled enrichment queries in parallel
                from concurrent.futures import ThreadPoolExecutor, as_completed

                def gather_call_graph():
                    if not doc_settings.get("call_graph", True):
                        return None
                    try:
                        call_context = get_call_context_from_docs(
                            file_path=task_file_path,
                            project_root=project_root
                        )
                        if call_context:
                            return ("call_graph", {
                                "callers": call_context.get("callers", []),
                                "callees": call_context.get("callees", []),
                                "functions_found": call_context.get("functions_found", [])
                            })
                    except Exception as e:
                        logger.debug(f"Doc context: call_graph gathering failed: {e}")
                    return None

                def gather_test_context():
                    if not doc_settings.get("test_context", True):
                        return None
                    try:
                        test_context = get_test_context_from_docs(
                            module_path=task_file_path,
                            project_root=project_root
                        )
                        if test_context:
                            return ("test_context", {
                                "test_files": test_context.get("test_files", []),
                                "test_functions": test_context.get("test_functions", []),
                            })
                    except Exception as e:
                        logger.debug(f"Doc context: test_context gathering failed: {e}")
                    return None

                # Execute all enabled queries in parallel
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(gather_call_graph),
                        executor.submit(gather_test_context),
                    ]

                    for future in as_completed(futures):
                        try:
                            result_tuple = future.result()
                            if result_tuple:
                                key, value = result_tuple
                                file_docs[key] = value
                                logger.debug(f"Doc context: gathered {key}")
                        except Exception as e:
                            logger.debug(f"Doc context: parallel gather failed: {e}")

            result["context"]["file_docs"] = file_docs

        # Add plan validation only if task has a plan
        if plan_validation:
            result["context"]["plan_validation"] = plan_validation

        if parent_warning:
            result["context"]["parent_task_warning"] = parent_warning

        extended_context = {}
        if include_full_journal:
            prev_journal_entries = []
            if previous_sibling and previous_sibling.get("id"):
                prev_id = previous_sibling["id"]
                prev_journal_entries = [
                    entry for entry in spec_data.get("journal", []) or []
                    if entry.get("task_id") == prev_id
                ]
            extended_context["previous_sibling_journal"] = prev_journal_entries

        if include_phase_history and phase_context and phase_context.get("id"):
            phase_id = phase_context["id"]
            phase_task_ids = collect_phase_task_ids(spec_data, phase_id)
            phase_journal = [
                entry for entry in spec_data.get("journal", []) or []
                if entry.get("task_id") in phase_task_ids
            ]
            extended_context["phase_journal"] = phase_journal

        if include_spec_overview:
            extended_context["spec_overview"] = get_progress_summary(spec_data)

        if extended_context:
            result["extended_context"] = extended_context
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.warning(f"Context gathering failed for {task_id}: {exc}")
        result["context"] = {
            "previous_sibling": None,
            "parent_task": None,
            "phase": None,
            "sibling_files": [],
            "task_journal": {"entry_count": 0, "entries": []},
            "dependencies": {
                "blocking": [],
                "blocked_by_details": [],
                "soft_depends": []
            },
        }
        if include_full_journal or include_phase_history or include_spec_overview:
            fallback = {}
            if include_full_journal:
                fallback["previous_sibling_journal"] = []
            if include_phase_history:
                fallback["phase_journal"] = []
            if include_spec_overview:
                fallback["spec_overview"] = {}
            result["extended_context"] = fallback

    # Note: All task details are already in task_data from the JSON spec
    # The spec_file and task_details fields are kept for backwards compatibility
    # but remain None as specs are now JSON format, not markdown

    result["success"] = True
    return result
