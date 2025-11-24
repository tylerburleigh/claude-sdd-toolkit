"""Integration tests for prepare-task CLI with default context."""
import json
import subprocess
import sys
from pathlib import Path


def run_prepare_task_command(spec_id: str, *args) -> dict:
    """Run sdd prepare-task command and return parsed JSON output."""
    cmd = ["sdd", "prepare-task", spec_id] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON output: {result.stdout}") from e


def test_default_payload_no_extra_flags():
    """Test that CLI invocation emits plan/files/validation without extra flags.

    Verifies that the default prepare-task behavior returns:
    - task_id
    - task_data
    - dependencies
    - validation_warnings
    - context (with standard fields)

    Without extra fields from enhancement flags like:
    - --include-full-journal
    - --include-phase-history
    - --include-spec-overview
    """
    spec_id = "prepare-task-default-context-2025-11-23-001"

    # Run prepare-task with no enhancement flags
    result = run_prepare_task_command(spec_id)

    # Verify essential fields are present
    assert "task_id" in result
    assert "task_data" in result
    assert "dependencies" in result
    assert "validation_warnings" in result
    assert "context" in result

    # Verify task_data has expected structure
    task_data = result["task_data"]
    assert task_data["type"] == "verify"
    assert "title" in task_data
    assert "status" in task_data

    # Verify context has standard fields (no enhancement fields)
    context = result["context"]
    standard_fields = {
        "previous_sibling",
        "parent_task",
        "phase",
        "sibling_files",
        "task_journal",
        "dependencies",
    }
    context_keys = set(context.keys())

    # Context should have the standard fields
    for field in standard_fields:
        assert field in context_keys, f"Missing standard field: {field}"

    # Verify no enhanced context fields are present without flags
    enhanced_fields = {
        "previous_sibling_journal",
        "phase_journal",
        "spec_overview",
    }
    for field in enhanced_fields:
        assert field not in context_keys, (
            f"Field '{field}' should not be in default context. "
            f"Use --include-full-journal, --include-phase-history, or "
            f"--include-spec-overview flags instead."
        )


def test_default_payload_has_validation_warnings():
    """Test that default payload includes validation warnings."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)

    # Verify validation_warnings is a list
    assert "validation_warnings" in result
    assert isinstance(result["validation_warnings"], list)

    # The spec should have some warnings (based on actual spec)
    if result["validation_warnings"]:
        # Check that warnings are strings
        for warning in result["validation_warnings"]:
            assert isinstance(warning, str)


def test_default_payload_includes_dependencies():
    """Test that default payload includes task dependencies."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)

    # Verify dependencies structure
    assert "dependencies" in result
    deps = result["dependencies"]

    # Should have dependency fields
    assert "task_id" in deps
    assert "can_start" in deps
    assert "blocked_by" in deps
    assert "soft_depends" in deps

    # can_start should be a boolean
    assert isinstance(deps["can_start"], bool)

    # blocked_by and soft_depends should be lists
    assert isinstance(deps["blocked_by"], list)
    assert isinstance(deps["soft_depends"], list)


def test_default_payload_without_enhancement_flags():
    """Test that enhancement flags are not included by default.

    This test verifies the core requirement: when using prepare-task
    without explicit enhancement flags (--include-full-journal,
    --include-phase-history, --include-spec-overview), the output
    should NOT contain:
    - previous_sibling_journal
    - phase_journal
    - spec_overview
    """
    spec_id = "prepare-task-default-context-2025-11-23-001"

    # Run with NO enhancement flags
    result = run_prepare_task_command(spec_id)

    context = result.get("context", {})

    # These should NOT be present without explicit flags
    assert "previous_sibling_journal" not in context
    assert "phase_journal" not in context
    assert "spec_overview" not in context

    # But extended_context should not exist at all in default output
    assert "extended_context" not in result


def test_context_previous_sibling_has_journal_excerpt():
    """Test that previous_sibling includes journal_excerpt summary."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)
    context = result["context"]

    previous_sibling = context.get("previous_sibling")
    if previous_sibling:
        # If there is a previous sibling, verify it has a journal excerpt
        assert "journal_excerpt" in previous_sibling
        excerpt = previous_sibling["journal_excerpt"]

        # Journal excerpt should have summary (not full entry)
        assert "summary" in excerpt
        assert isinstance(excerpt["summary"], str)


def test_context_phase_has_progress_info():
    """Test that phase context includes progress metrics."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)
    context = result["context"]

    phase = context.get("phase")
    if phase:  # Phase can be null
        # Verify phase has key fields
        assert "completed_tasks" in phase
        assert "total_tasks" in phase
        assert "percentage" in phase

        # These should be numbers
        assert isinstance(phase["completed_tasks"], int)
        assert isinstance(phase["total_tasks"], int)
        assert isinstance(phase["percentage"], (int, float))


def test_context_sibling_files_is_list():
    """Test that sibling_files is always a list."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)
    context = result["context"]

    assert "sibling_files" in context
    assert isinstance(context["sibling_files"], list)


def test_context_task_journal_has_entries():
    """Test that task_journal includes entries list."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)
    context = result["context"]

    task_journal = context.get("task_journal")
    assert task_journal is not None

    # Should have entry_count and entries list
    assert "entry_count" in task_journal
    assert "entries" in task_journal
    assert isinstance(task_journal["entries"], list)
    assert isinstance(task_journal["entry_count"], int)

    # Entry count should match entries list length
    assert task_journal["entry_count"] == len(task_journal["entries"])


def test_end_to_end_json_output_pretty():
    """Test that CLI output can be serialized as pretty JSON."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)

    # Serialize to pretty JSON
    pretty_json = json.dumps(result, indent=2)

    # Should have newlines (pretty formatting)
    assert "\n" in pretty_json
    assert "  " in pretty_json  # indentation present

    # Should be valid JSON roundtrip
    parsed = json.loads(pretty_json)
    assert parsed == result


def test_end_to_end_json_output_compact():
    """Test that CLI output can be serialized as compact JSON."""
    spec_id = "prepare-task-default-context-2025-11-23-001"

    result = run_prepare_task_command(spec_id)

    # Serialize to compact JSON
    compact_json = json.dumps(result, separators=(',', ':'))

    # Should be smaller than pretty version
    pretty_json = json.dumps(result, indent=2)
    assert len(compact_json) < len(pretty_json)

    # Should be valid JSON roundtrip
    parsed = json.loads(compact_json)
    assert parsed == result


def test_task_info_redundant_with_prepare_task():
    """Test that task-info provides no additional value beyond prepare-task.

    This verifies that the default prepare-task output includes all the
    information that task-info would provide, making task-info redundant
    for standard workflows.
    """
    spec_id = "prepare-task-default-context-2025-11-23-001"

    # Get prepare-task output
    prepare_result = run_prepare_task_command(spec_id)

    # Get task-info output for comparison
    task_id = prepare_result["task_id"]
    task_info_cmd = ["sdd", "task-info", spec_id, task_id, "--json"]
    task_info_result = subprocess.run(
        task_info_cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    task_info_data = json.loads(task_info_result.stdout)

    # Verify prepare-task.task_data contains same info as task-info
    prepare_task_data = prepare_result["task_data"]

    # Key fields that task-info provides should be in prepare-task output
    assert prepare_task_data["title"] == task_info_data["title"]
    assert prepare_task_data["status"] == task_info_data["status"]

    # Metadata should also be present
    if "metadata" in task_info_data:
        assert "metadata" in prepare_task_data
        # File path should match if present
        if "file_path" in task_info_data["metadata"]:
            assert prepare_task_data["metadata"]["file_path"] == \
                   task_info_data["metadata"]["file_path"]


def test_check_deps_redundant_with_prepare_task():
    """Test that check-deps provides no additional value beyond prepare-task.

    This verifies that context.dependencies in prepare-task output provides
    the same dependency information as check-deps, making check-deps redundant.
    """
    spec_id = "prepare-task-default-context-2025-11-23-001"

    # Get prepare-task output
    prepare_result = run_prepare_task_command(spec_id)

    # Get check-deps output for comparison
    task_id = prepare_result["task_id"]
    check_deps_cmd = ["sdd", "check-deps", spec_id, task_id, "--json"]
    check_deps_result = subprocess.run(
        check_deps_cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    check_deps_data = json.loads(check_deps_result.stdout)

    # Verify prepare-task includes dependency info from check-deps
    prepare_deps = prepare_result["dependencies"]

    # prepare-task should have dependencies with can_start
    assert prepare_deps is not None
    assert "can_start" in prepare_deps

    # The critical field from check-deps (can_start) should match
    assert prepare_deps["can_start"] == check_deps_data["can_start"]

    # prepare-task provides MORE information than check-deps:
    # - task_id, blocked_by, soft_depends, blocks
    assert "task_id" in prepare_deps
    assert "blocked_by" in prepare_deps
    assert "soft_depends" in prepare_deps

    # context.dependencies provides even more detailed info
    context_deps = prepare_result["context"]["dependencies"]
    assert "blocking" in context_deps
    assert "blocked_by_details" in context_deps
    assert "soft_depends" in context_deps
