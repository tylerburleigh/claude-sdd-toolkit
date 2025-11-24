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
        "dependencies",
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


def test_prepare_task_context_warns_when_parent_missing(sample_json_spec_simple, specs_structure):
    spec_path = sample_json_spec_simple
    spec_data = json.loads(spec_path.read_text())
    hierarchy = spec_data["hierarchy"]
    hierarchy["task-1-2"]["parent"] = None
    spec_path.write_text(json.dumps(spec_data, indent=2))

    with patch(
        "claude_skills.sdd_next.discovery.validate_spec_before_proceed",
        return_value={"valid": True, "errors": [], "warnings": [], "can_autofix": False, "autofix_command": ""},
    ):
        result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")

    context = result["context"]
    assert context["parent_task"] is None
    assert context["parent_task_warning"] == {"parent_missing": True}


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


def test_prepare_task_context_includes_dependencies(sample_json_spec_simple, specs_structure):
    """Test that context.dependencies includes detailed dependency info"""
    spec_path = sample_json_spec_simple
    spec_data = json.loads(spec_path.read_text())

    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")

    context = result["context"]
    dependencies = context["dependencies"]

    # Verify dependencies structure
    assert isinstance(dependencies, dict)
    assert "blocking" in dependencies
    assert "blocked_by_details" in dependencies
    assert "soft_depends" in dependencies

    # All should be lists
    assert isinstance(dependencies["blocking"], list)
    assert isinstance(dependencies["blocked_by_details"], list)
    assert isinstance(dependencies["soft_depends"], list)


def test_prepare_task_json_output_pretty(sample_json_spec_simple, specs_structure):
    """Test that prepare_task output can be serialized as pretty JSON"""
    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    # Should serialize without errors
    pretty_json = json.dumps(result, indent=2)
    assert pretty_json
    assert "\n" in pretty_json  # Pretty format has newlines

    # Verify it's valid JSON
    parsed = json.loads(pretty_json)
    assert parsed == result


def test_prepare_task_json_output_compact(sample_json_spec_simple, specs_structure):
    """Test that prepare_task output can be serialized as compact JSON"""
    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    # Should serialize without errors
    compact_json = json.dumps(result, separators=(',', ':'))
    assert compact_json

    # Compact format should be shorter (no extra whitespace)
    pretty_json = json.dumps(result, indent=2)
    assert len(compact_json) < len(pretty_json)

    # Verify it's valid JSON
    parsed = json.loads(compact_json)
    assert parsed == result


def test_prepare_task_latency_budget_100ms(sample_json_spec_simple, specs_structure):
    """Test that prepare_task completes within 100ms latency budget"""
    # Warm-up call to avoid cold-start effects
    prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")

    # Measure actual execution time over multiple runs
    timings = []
    for _ in range(5):
        start = perf_counter()
        prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-2")
        timings.append((perf_counter() - start) * 1000)  # Convert to ms

    # Use median to avoid outliers
    median_ms = sorted(timings)[len(timings) // 2]
    assert median_ms < 100, f"Median latency {median_ms:.2f}ms exceeds 100ms budget"


def test_prepare_task_includes_doc_context_when_available(sample_json_spec_simple, specs_structure):
    """Test that context.file_docs is populated when doc-query is available"""
    mock_doc_context = {
        "files": ["src/test.py", "src/utils.py"],
        "dependencies": ["json", "pathlib"],
        "similar": [],
        "complexity": {},
        "provenance": {
            "source_doc_id": "/tmp/docs",
            "generated_at": "2025-11-24T10:00:00Z",
            "generated_at_commit": "abc123",
            "freshness_ms": 45
        }
    }

    with ExitStack() as stack:
        # Mock doc-query availability (patch where it's used in discovery.py)
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_query_available", return_value={"available": True})
        )
        # Mock doc context response (patch where it's used in discovery.py)
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_task_context_from_docs", return_value=mock_doc_context)
        )
        # Mock doc availability status
        from claude_skills.common.doc_integration import DocStatus
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_availability", return_value=DocStatus.AVAILABLE)
        )

        result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    # Verify doc_context is in result
    assert result.get("doc_context") == mock_doc_context

    # Verify file_docs is in context
    context = result["context"]
    assert "file_docs" in context
    assert context["file_docs"] == mock_doc_context
    assert context["file_docs"]["files"] == ["src/test.py", "src/utils.py"]
    assert context["file_docs"]["dependencies"] == ["json", "pathlib"]


def test_prepare_task_fallback_when_docs_unavailable(sample_json_spec_simple, specs_structure):
    """Test that prepare_task works gracefully when doc-query is unavailable"""
    with ExitStack() as stack:
        # Mock doc-query unavailable (patch where it's used in discovery.py)
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_query_available", return_value={"available": False})
        )

        result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    # Verify doc_context is None
    assert result.get("doc_context") is None

    # Verify file_docs is NOT in context
    context = result["context"]
    assert "file_docs" not in context

    # Verify other context fields are still populated
    assert context["previous_sibling"] is not None or context["parent_task"] is not None
    assert "phase" in context
    assert "sibling_files" in context


def test_prepare_task_doc_context_overhead_under_30ms(sample_json_spec_simple, specs_structure):
    """Test that doc context integration adds <30ms overhead (10-call median)"""
    def measure_median(repetitions: int = 10) -> float:
        """Measure median latency over N repetitions"""
        timings = []
        for _ in range(repetitions):
            start = perf_counter()
            prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")
            timings.append((perf_counter() - start) * 1000)  # Convert to ms
        return sorted(timings)[len(timings) // 2]  # Return median

    # Warm-up call
    prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

    # Baseline: measure without doc context
    with ExitStack() as stack:
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_query_available", return_value={"available": False})
        )
        baseline_ms = measure_median(10)

    # With doc context: measure with mocked doc-query
    mock_doc_context = {
        "files": ["src/test.py"],
        "dependencies": [],
        "similar": [],
        "complexity": {},
        "provenance": {"source_doc_id": "/tmp", "generated_at": "2025-11-24", "freshness_ms": 10}
    }

    with ExitStack() as stack:
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_query_available", return_value={"available": True})
        )
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.get_task_context_from_docs", return_value=mock_doc_context)
        )
        from claude_skills.common.doc_integration import DocStatus
        stack.enter_context(
            patch("claude_skills.sdd_next.discovery.check_doc_availability", return_value=DocStatus.AVAILABLE)
        )
        with_doc_ms = measure_median(10)

    # Calculate overhead
    overhead_ms = with_doc_ms - baseline_ms

    # Assert overhead is under 30ms
    assert overhead_ms < 30, f"Doc context integration added {overhead_ms:.2f}ms overhead, expected <30ms (baseline: {baseline_ms:.2f}ms, with_doc: {with_doc_ms:.2f}ms)"
