from claude_skills.sdd_next.context_utils import (
    get_previous_sibling,
    get_parent_context,
    get_phase_context,
    get_sibling_files,
    get_task_journal_summary,
    collect_phase_task_ids,
)


def build_spec_with_siblings():
    hierarchy = {
        "phase-1": {
            "id": "phase-1",
            "type": "phase",
            "status": "in_progress",
            "parent": "spec-root",
            "children": ["task-1-1", "task-1-2", "task-1-3"],
        },
        "task-1-1": {
            "id": "task-1-1",
            "type": "task",
            "title": "Document baseline",
            "status": "completed",
            "parent": "phase-1",
            "children": [],
            "metadata": {
                "file_path": "docs/task_1_1.md",
                "completed_at": "2025-11-16T13:06:23Z",
            },
        },
        "task-1-2": {
            "id": "task-1-2",
            "type": "task",
            "title": "Design schema",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "metadata": {
                "file_path": "docs/task_1_2.md",
            },
        },
        "task-1-3": {
            "id": "task-1-3",
            "type": "task",
            "title": "Perf analysis",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "metadata": {},
        },
    }

    journal = [
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T13:06:23Z",
            "entry_type": "note",
            "content": "Documented context gaps for prepare-task and saved findings.",
        }
    ]

    return {"hierarchy": hierarchy, "journal": journal}


def build_spec_with_nested_phase():
    hierarchy = {
        "spec-root": {
            "id": "spec-root",
            "type": "spec",
            "status": "in_progress",
            "parent": None,
            "children": ["phase-1", "phase-2"],
        },
        "phase-1": {
            "id": "phase-1",
            "type": "phase",
            "title": "Phase One",
            "status": "completed",
            "parent": "spec-root",
            "children": [],
            "completed_tasks": 3,
            "total_tasks": 3,
            "metadata": {"description": "Initial analysis"},
        },
        "phase-2": {
            "id": "phase-2",
            "type": "phase",
            "title": "Phase Two",
            "status": "in_progress",
            "parent": "spec-root",
            "children": ["group-1"],
            "completed_tasks": 1,
            "total_tasks": 5,
            "metadata": {"description": "Implementation work"},
            "dependencies": {"blocked_by": ["phase-1-verify"]},
        },
        "group-1": {
            "id": "group-1",
            "type": "group",
            "title": "Group Tasks",
            "parent": "phase-2",
            "children": ["task-2-1"],
        },
        "task-2-1": {
            "id": "task-2-1",
            "type": "task",
            "title": "Implement helper",
            "status": "pending",
            "parent": "group-1",
            "children": [],
        },
    }
    return {"hierarchy": hierarchy}


def build_phase_with_nested_tasks():
    hierarchy = {
        "phase-alpha": {
            "id": "phase-alpha",
            "type": "phase",
            "title": "Alpha",
            "status": "in_progress",
            "parent": "spec-root",
            "children": ["group-alpha", "task-alpha-verification"],
        },
        "group-alpha": {
            "id": "group-alpha",
            "type": "group",
            "status": "in_progress",
            "parent": "phase-alpha",
            "children": ["task-alpha-1", "group-alpha-sub"],
        },
        "group-alpha-sub": {
            "id": "group-alpha-sub",
            "type": "group",
            "status": "pending",
            "parent": "group-alpha",
            "children": ["task-alpha-2"],
        },
        "task-alpha-1": {
            "id": "task-alpha-1",
            "type": "task",
            "title": "First task",
            "status": "completed",
            "parent": "group-alpha",
            "children": [],
        },
        "task-alpha-2": {
            "id": "task-alpha-2",
            "type": "subtask",
            "title": "Nested subtask",
            "status": "pending",
            "parent": "group-alpha-sub",
            "children": [],
        },
        "task-alpha-verification": {
            "id": "task-alpha-verification",
            "type": "verify",
            "title": "Verify alpha",
            "status": "pending",
            "parent": "phase-alpha",
            "children": [],
        },
    }

    return {"hierarchy": hierarchy}


def test_get_previous_sibling_returns_metadata():
    spec_data = build_spec_with_siblings()

    previous = get_previous_sibling(spec_data, "task-1-2")

    assert previous is not None
    assert previous["id"] == "task-1-1"
    assert previous["title"] == "Document baseline"
    assert previous["status"] == "completed"
    assert previous["file_path"] == "docs/task_1_1.md"
    assert previous["completed_at"] == "2025-11-16T13:06:23Z"
    assert previous["journal_excerpt"]["summary"].startswith("Documented context gaps")


def test_get_previous_sibling_returns_none_for_first_child():
    spec_data = build_spec_with_siblings()

    previous = get_previous_sibling(spec_data, "task-1-1")

    assert previous is None


def test_get_previous_sibling_truncates_journal_summary():
    spec_data = build_spec_with_siblings()
    long_text = "A" * 250
    spec_data["journal"].append(
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T14:00:00Z",
            "entry_type": "decision",
            "content": long_text,
        }
    )

    previous = get_previous_sibling(spec_data, "task-1-2")

    assert previous is not None
    assert len(previous["journal_excerpt"]["summary"]) == 200


def test_get_previous_sibling_handles_missing_journal_entries():
    spec_data = build_spec_with_siblings()
    spec_data["journal"] = []  # Remove entries

    previous = get_previous_sibling(spec_data, "task-1-2")

    assert previous is not None
    assert previous["journal_excerpt"] is None


def test_get_previous_sibling_handles_parent_without_children_list():
    spec_data = build_spec_with_siblings()
    spec_data["hierarchy"]["phase-1"].pop("children", None)

    previous = get_previous_sibling(spec_data, "task-1-2")

    assert previous is not None
    assert previous["id"] == "task-1-1"


def test_get_previous_sibling_preserves_declared_order():
    spec_data = build_spec_with_siblings()
    hierarchy = spec_data["hierarchy"]
    hierarchy["task-1-10"] = {
        "id": "task-1-10",
        "type": "task",
        "title": "Late addition",
        "status": "pending",
        "parent": "phase-1",
        "children": [],
        "metadata": {},
    }
    hierarchy["phase-1"]["children"] = ["task-1-2", "task-1-10"]

    previous = get_previous_sibling(spec_data, "task-1-10")

    assert previous is not None
    assert previous["id"] == "task-1-2"


def test_get_parent_context_for_task_parent():
    spec_data = build_spec_with_siblings()
    # Make task-1-1 the parent of a subtask
    hierarchy = spec_data["hierarchy"]
    hierarchy["task-1-1"]["children"] = ["task-1-1-1", "task-1-1-2"]
    hierarchy["task-1-1"]["metadata"]["description"] = "Parent description"
    hierarchy["task-1-1"]["completed_tasks"] = 1
    hierarchy["task-1-1"]["total_tasks"] = 3
    hierarchy["task-1-1-1"] = {
        "id": "task-1-1-1",
        "type": "subtask",
        "title": "Sub 1",
        "status": "pending",
        "parent": "task-1-1",
        "children": [],
        "metadata": {},
    }
    hierarchy["task-1-1-2"] = {
        "id": "task-1-1-2",
        "type": "subtask",
        "title": "Sub 2",
        "status": "pending",
        "parent": "task-1-1",
        "children": [],
        "metadata": {},
    }

    context = get_parent_context(spec_data, "task-1-1-2")

    assert context is not None
    assert context["id"] == "task-1-1"
    assert context["description"] == "Parent description"
    assert context["position_label"] == "2 of 2 subtasks"
    assert len(context["children"]) == 2
    assert context["remaining_tasks"] == 2


def test_get_parent_context_for_group_without_children_array():
    spec_data = build_spec_with_siblings()
    hierarchy = spec_data["hierarchy"]
    hierarchy["group-1"] = {
        "id": "group-1",
        "type": "group",
        "title": "Parent Group",
        "status": "pending",
        "parent": "phase-1",
        "metadata": {"note": "Group note"},
    }
    hierarchy["task-1-2"]["parent"] = "group-1"
    hierarchy["task-1-3"]["parent"] = "group-1"

    context = get_parent_context(spec_data, "task-1-3")

    assert context is not None
    assert context["notes"] == ["Group note"]
    assert context["position_label"] == "2 of 2 children"
    assert context["children"][0]["id"] == "task-1-2"


def test_get_parent_context_returns_none_for_missing_parent():
    spec_data = build_spec_with_siblings()
    spec_data["hierarchy"]["task-1-2"]["parent"] = None

    assert get_parent_context(spec_data, "task-1-2") is None


def test_get_phase_context_returns_phase_info():
    spec_data = build_spec_with_nested_phase()

    context = get_phase_context(spec_data, "task-2-1")

    assert context is not None
    assert context["id"] == "phase-2"
    assert context["sequence_index"] == 2
    assert context["percentage"] == 20
    assert context["summary"] == "Implementation work"
    assert context["blockers"] == ["phase-1-verify"]


def test_get_phase_context_returns_none_when_no_phase():
    spec_data = build_spec_with_siblings()
    spec_data["hierarchy"]["task-1-2"]["parent"] = None

    assert get_phase_context(spec_data, "task-1-2") is None


def test_get_phase_context_handles_missing_progress_values():
    spec_data = build_spec_with_nested_phase()
    phase = spec_data["hierarchy"]["phase-2"]
    phase.pop("completed_tasks", None)
    phase["total_tasks"] = 0

    context = get_phase_context(spec_data, "task-2-1")

    assert context is not None
    assert context["percentage"] is None


def test_get_sibling_files_returns_file_entries():
    spec_data = build_spec_with_siblings()

    files = get_sibling_files(spec_data, "task-1-2")

    assert len(files) == 2
    assert files[0]["file_path"] == "docs/task_1_1.md"
    assert files[1]["file_path"] == "docs/task_1_2.md"


def test_get_sibling_files_skips_missing_paths():
    spec_data = build_spec_with_siblings()
    spec_data["hierarchy"]["task-1-2"]["metadata"].pop("file_path")

    files = get_sibling_files(spec_data, "task-1-2")

    assert len(files) == 1
    assert files[0]["task_id"] == "task-1-1"


def test_get_sibling_files_deduplicates_paths():
    spec_data = build_spec_with_siblings()
    hierarchy = spec_data["hierarchy"]
    hierarchy["task-1-4"] = {
        "id": "task-1-4",
        "type": "task",
        "title": "Duplicate path",
        "status": "pending",
        "parent": "phase-1",
        "metadata": {"file_path": "docs/task_1_1.md"},
    }
    hierarchy["phase-1"]["children"].append("task-1-4")

    files = get_sibling_files(spec_data, "task-1-2")

    assert len(files) == 2


def test_get_task_journal_summary_returns_recent_entries():
    spec_data = build_spec_with_siblings()
    spec_data["journal"].append(
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T15:20:00Z",
            "entry_type": "status_change",
            "title": "Marked completed",
            "content": "Finished documenting baseline behavior.",
            "author": "agent",
        }
    )

    summary = get_task_journal_summary(spec_data, "task-1-1")

    assert summary["entry_count"] == 2
    assert summary["entries"][0]["title"] == "Marked completed"


def test_get_task_journal_summary_includes_three_entries_by_default():
    spec_data = build_spec_with_siblings()
    for idx in range(3):
        spec_data["journal"].append(
            {
                "task_id": "task-1-1",
                "timestamp": f"2025-11-16T15:2{idx}:00Z",
                "entry_type": "note",
                "title": f"Entry {idx}",
                "content": f"Detail {idx}",
            }
        )

    summary = get_task_journal_summary(spec_data, "task-1-1")

    assert len(summary["entries"]) == 3


def test_get_task_journal_summary_handles_empty_journal():
    spec_data = build_spec_with_siblings()

    summary = get_task_journal_summary(spec_data, "task-1-3")

    assert summary["entry_count"] == 0
    assert summary["entries"] == []


def test_get_task_journal_summary_truncates_content():
    spec_data = build_spec_with_siblings()
    long_text = "B" * 300
    spec_data["journal"].append(
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T16:00:00Z",
            "entry_type": "note",
            "title": "Long note",
            "content": long_text,
        }
    )

    summary = get_task_journal_summary(spec_data, "task-1-1", max_entries=1)

    assert len(summary["entries"][0]["summary"]) == 160


def test_collect_phase_task_ids_includes_nested_tasks_and_verifications():
    spec_data = build_phase_with_nested_tasks()

    task_ids = collect_phase_task_ids(spec_data, "phase-alpha")

    assert set(task_ids) == {
        "task-alpha-1",
        "task-alpha-2",
        "task-alpha-verification",
    }


def test_collect_phase_task_ids_handles_invalid_input():
    spec_data = build_phase_with_nested_tasks()

    assert collect_phase_task_ids(spec_data, None) == []
    assert collect_phase_task_ids(spec_data, "missing-phase") == []
    assert collect_phase_task_ids({}, "phase-alpha") == []
