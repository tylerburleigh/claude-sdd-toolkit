import json

import pytest

from .cli_runner import run_cli


@pytest.mark.integration
def test_render_json_output(tmp_path):
    specs_dir = tmp_path / "specs" / "active"
    specs_dir.mkdir(parents=True)

    spec_data = {
        "spec_id": "demo-001",
        "project_metadata": {"name": "Demo Spec"},
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Demo Spec",
                "status": "pending",
                "total_tasks": 0,
                "completed_tasks": 0,
                "children": [],
            }
        },
    }
    (specs_dir / "demo-001.json").write_text(json.dumps(spec_data), encoding="utf-8")

    result = run_cli(
        "--json",
        "render",
        "demo-001",
        "--path",
        str(tmp_path),
        "--mode",
        "basic",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["spec_id"] == "demo-001"
    assert payload["output_path"].endswith("demo-001.md")
    assert payload["fallback_used"] is False
