import json

pytest_plugins = ["claude_skills.tests.conftest"]

from claude_skills.common import load_json_spec
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
