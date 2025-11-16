import json

import pytest

from .cli_runner import run_cli


def _create_sample_spec(tmp_path):
    specs_dir = tmp_path / "specs" / "active"
    specs_dir.mkdir(parents=True)
    spec_data = {
        "spec_id": "demo-spec",
        "metadata": {"status": "pending"},
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Demo",
                "status": "pending",
                "children": [],
                "metadata": {},
            }
        },
    }
    spec_file = specs_dir / "demo-spec.json"
    spec_file.write_text(json.dumps(spec_data), encoding="utf-8")
    return spec_file


@pytest.mark.integration
def test_apply_modifications_json_output(tmp_path):
    spec_file = _create_sample_spec(tmp_path)
    mods_file = tmp_path / "mods.json"
    mods_file.write_text(
        json.dumps(
            {
                "modifications": [
                    {
                        "operation": "update_node_field",
                        "node_id": "spec-root",
                        "field": "status",
                        "value": "completed",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = run_cli(
        "--json",
        "apply-modifications",
        "demo-spec",
        "--from",
        str(mods_file),
        "--path",
        str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["total_operations"] == 1

    updated_spec = json.loads(spec_file.read_text())
    assert updated_spec["hierarchy"]["spec-root"]["status"] == "completed"


@pytest.mark.integration
def test_parse_review_json_output(tmp_path):
    _create_sample_spec(tmp_path)
    review_file = tmp_path / "review.json"
    review_file.write_text(
        json.dumps(
            {
                "consensus": {
                    "overall_score": 7.0,
                    "recommendation": "REVISE",
                    "consensus_level": "moderate",
                    "synthesis_text": "",
                },
                "metadata": {"spec_id": "demo-spec", "spec_title": "Demo Spec"},
            }
        ),
        encoding="utf-8",
    )
    suggestions_path = tmp_path / "suggestions.json"

    result = run_cli(
        "--json",
        "parse-review",
        "demo-spec",
        "--review",
        str(review_file),
        "--output",
        str(suggestions_path),
        "--path",
        str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion_count"] == 0
    assert payload["issues_total"] == 0
