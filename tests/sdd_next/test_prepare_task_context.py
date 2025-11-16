import json
from contextlib import ExitStack
from time import perf_counter
from unittest.mock import patch

pytest_plugins = ["claude_skills.tests.conftest"]

from claude_skills.sdd_next.discovery import prepare_task


def test_prepare_task_returns_context(sample_json_spec_simple, specs_structure):
    spec_data_path = sample_json_spec_simple
    spec_data = json.loads(spec_data_path.read_text())
    spec_data_path.write_text(json.dumps(spec_data, indent=2))

    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    context = result.get("context")
    assert context
    assert set(context.keys()) == {
        "previous_sibling",
        "parent_task",
        "phase",
        "sibling_files",
        "task_journal",
    }


def test_prepare_task_enhancement_flags(sample_json_spec_simple, specs_structure):
    spec_data_path = sample_json_spec_simple
    spec_data = json.loads(spec_data_path.read_text())
    spec_data["journal"] = [
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T11:00:00Z",
            "entry_type": "note",
            "title": "First",
            "content": "Entry",
        }
    ]
    spec_data_path.write_text(json.dumps(spec_data, indent=2))

    result = prepare_task(
        "simple-spec-2025-01-01-001",
        specs_structure,
        "task-1-2",
        include_full_journal=True,
        include_phase_history=True,
        include_spec_overview=True,
    )

    extended = result.get("extended_context")
    assert extended
    assert "previous_sibling_journal" in extended
    assert "phase_journal" in extended
    assert "spec_overview" in extended


def test_prepare_task_context_includes_realistic_values(sample_json_spec_simple, specs_structure):
    spec_path = sample_json_spec_simple
    spec_data = json.loads(spec_path.read_text())
    hierarchy = spec_data["hierarchy"]

    hierarchy["task-1-1"]["status"] = "completed"
    hierarchy["task-1-1"]["metadata"]["completed_at"] = "2025-11-16T10:00:00Z"
    hierarchy["task-1-1"]["completed_tasks"] = 1
    hierarchy["phase-1"]["completed_tasks"] = 1
    hierarchy["spec-root"]["completed_tasks"] = 1
    hierarchy["phase-1"]["metadata"]["description"] = "Implementation focus"
    spec_data["journal"] = [
        {
            "task_id": "task-1-1",
            "timestamp": "2025-11-16T11:00:00Z",
            "entry_type": "status_change",
            "title": "Completed baseline",
            "content": "Documented prepare-task behavior",
        },
        {
            "task_id": "task-1-2",
            "timestamp": "2025-11-16T12:00:00Z",
            "entry_type": "note",
            "title": "Latest note",
            "content": "Clarified next deliverable",
        },
        {
            "task_id": "task-1-2",
            "timestamp": "2025-11-16T11:30:00Z",
            "entry_type": "decision",
            "title": "Earlier note",
            "content": "Captured scope risk",
        },
    ]
    spec_path.write_text(json.dumps(spec_data, indent=2))

    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")

    context = result["context"]
    previous = context["previous_sibling"]
    assert previous["id"] == "task-1-1"
    assert previous["completed_at"] == "2025-11-16T10:00:00Z"
    assert previous["journal_excerpt"]["summary"].startswith("Documented prepare-task")

    parent = context["parent_task"]
    assert parent["id"] == "phase-1"
    assert parent["position_label"] == "2 of 2 children"

    phase = context["phase"]
    assert phase["percentage"] == 50
    assert phase["summary"] == "Implementation focus"

    sibling_files = {item["file_path"] for item in context["sibling_files"]}
    assert "src/test_1_1.py" in sibling_files
    assert "src/test_1_2.py" in sibling_files

    task_journal = context["task_journal"]
    assert task_journal["entry_count"] == 2
    assert task_journal["entries"][0]["title"] == "Latest note"


def test_prepare_task_context_overhead_under_30ms(sample_json_spec_simple, specs_structure):
    def measure_call(repetitions: int = 3) -> float:
        timings = []
        for _ in range(repetitions):
            start = perf_counter()
            prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")
            timings.append(perf_counter() - start)
        return min(timings)

    # Warm-up to avoid cold-start noise
    prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")

    with ExitStack() as stack:
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_previous_sibling", lambda *_, **__: None)
        )
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_parent_context", lambda *_, **__: None)
        )
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_phase_context", lambda *_, **__: None)
        )
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_sibling_files", lambda *_, **__: [])
        )
        stack.enter_context(
            patch(
                "claude_skills.sdd_next.discovery.get_task_journal_summary",
                lambda *_, **__: {"entry_count": 0, "entries": []},
            )
        )
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.collect_phase_task_ids", lambda *_, **__: [])
        )
        baseline = measure_call()

    actual = measure_call()
    overhead_ms = (actual - baseline) * 1000
    assert overhead_ms < 30, f"Context gathering added {overhead_ms:.2f}ms, expected <30ms"
