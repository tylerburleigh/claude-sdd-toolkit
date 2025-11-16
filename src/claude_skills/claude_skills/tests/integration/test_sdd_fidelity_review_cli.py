import json

import pytest

from .cli_runner import run_cli


def _create_spec(tmp_path):
    base_specs = tmp_path / "specs"
    for sub in ("active", "completed", "pending", "archived"):
        (base_specs / sub).mkdir(parents=True, exist_ok=True)
    spec_data = {
        "spec_id": "demo-spec",
        "metadata": {"status": "completed"},
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Demo",
                "status": "completed",
                "children": [],
                "metadata": {},
            }
        },
    }
    (base_specs / "completed" / "demo-spec.json").write_text(json.dumps(spec_data), encoding="utf-8")


@pytest.mark.integration
def test_fidelity_review_json_no_ai(tmp_path):
    _create_spec(tmp_path)

    result = run_cli(
        "--json",
        "fidelity-review",
        "demo-spec",
        "--path",
        str(tmp_path),
        "--no-ai",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["spec_id"] == "demo-spec"
    assert payload["mode"] == "no-ai"
    assert payload["issue_counts"] == {}
