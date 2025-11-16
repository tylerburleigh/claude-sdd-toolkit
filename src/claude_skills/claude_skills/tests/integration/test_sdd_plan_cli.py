import json

import pytest

from .cli_runner import run_cli


@pytest.mark.integration
class TestSddPlanCLI:
    def test_template_list_json_output(self):
        result = run_cli(
            "--json",
            "template",
            "list",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data["templates"], list)
        assert data["count"] == len(data["templates"])

    def test_create_json_output(self, tmp_path):
        result = run_cli(
            "--json",
            "create",
            "New Feature",
            "--template",
            "simple",
            "--path",
            str(tmp_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["success"] is True
        assert payload["spec_id"]
        spec_path = tmp_path / "specs" / "pending" / f"{payload['spec_id']}.json"
        assert spec_path.exists()
