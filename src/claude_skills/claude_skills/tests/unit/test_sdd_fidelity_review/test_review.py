from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from claude_skills.common.cache.cache_manager import CacheManager
from claude_skills.sdd_fidelity_review.review import FidelityReviewer


pytestmark = pytest.mark.unit


@pytest.fixture
def sample_spec() -> Dict[str, object]:
    return {
        "title": "User Authentication System",
        "hierarchy": {
            "phase-1": {"title": "Phase 1", "type": "phase", "parent": "root"},
            "group-1": {"title": "Group", "type": "group", "parent": "phase-1"},
            "task-1": {
                "title": "Implement login",
                "type": "task",
                "status": "completed",
                "parent": "group-1",
                "metadata": {
                    "description": "Implement login endpoint",
                    "file_path": "src/auth.py",
                    "verification_steps": ["pytest tests/auth/test_login.py"],
                },
            },
            "task-2": {
                "title": "Add logout",
                "type": "task",
                "status": "pending",
                "parent": "phase-1",
                "metadata": {
                    "description": "Implement logout endpoint",
                    "file_path": "src/auth_logout.py",
                },
            },
        },
        "journals": [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "note",
                "title": "Kickoff",
                "content": "Work started.",
                "task_id": None,
            }
        ],
    }


def _make_reviewer(spec_data: Dict[str, object], spec_path: Path | None = None, incremental: bool = False) -> FidelityReviewer:
    with patch("claude_skills.sdd_fidelity_review.review.load_json_spec", return_value=spec_data):
        with patch("claude_skills.sdd_fidelity_review.review.find_specs_directory", return_value=spec_path or Path("/specs")):
            reviewer = FidelityReviewer("test-spec", spec_path=spec_path, incremental=incremental)
    return reviewer


def test_fidelity_reviewer_init_with_spec_path(tmp_path: Path, sample_spec: Dict[str, object]) -> None:
    with patch("claude_skills.sdd_fidelity_review.review.load_json_spec", return_value=sample_spec) as mock_load:
        reviewer = FidelityReviewer("test-spec", spec_path=tmp_path)

    assert reviewer.spec_id == "test-spec"
    assert reviewer.spec_path == tmp_path
    assert reviewer.spec_data == sample_spec
    mock_load.assert_called_once_with("test-spec", tmp_path)


def test_fidelity_reviewer_auto_discovers_specs(sample_spec: Dict[str, object]) -> None:
    with patch("claude_skills.sdd_fidelity_review.review.find_specs_directory", return_value=Path("/auto/specs")) as mock_find:
        with patch("claude_skills.sdd_fidelity_review.review.load_json_spec", return_value=sample_spec) as mock_load:
            reviewer = FidelityReviewer("test-spec")

    assert reviewer.spec_path == Path("/auto/specs")
    mock_find.assert_called_once()
    mock_load.assert_called_once_with("test-spec", Path("/auto/specs"))


def test_fidelity_reviewer_handles_missing_specs_directory() -> None:
    with patch("claude_skills.sdd_fidelity_review.review.find_specs_directory", return_value=None):
        reviewer = FidelityReviewer("missing-spec")

    assert reviewer.spec_path is None
    assert reviewer.spec_data is None


def test_get_task_requirements_success(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    requirements = reviewer.get_task_requirements("task-1")
    assert requirements is not None
    assert requirements["task_id"] == "task-1"
    assert requirements["title"] == "Implement login"
    assert requirements["file_path"] == "src/auth.py"
    assert "verification_steps" in requirements


def test_get_task_requirements_missing_task(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    assert reviewer.get_task_requirements("unknown") is None


def test_get_phase_tasks_recursively_collects(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    tasks = reviewer.get_phase_tasks("phase-1")
    assert tasks is not None
    task_ids = {task["task_id"] for task in tasks}
    assert task_ids == {"task-1", "task-2"}


def test_get_phase_tasks_handles_missing_phase(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    assert reviewer.get_phase_tasks("missing-phase") is None


def test_get_all_tasks_handles_malformed_spec() -> None:
    malformed_spec = {"title": "Test Spec"}
    reviewer = _make_reviewer(malformed_spec)
    assert reviewer.get_all_tasks() == []


def test_get_file_diff_success(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    with patch("claude_skills.sdd_fidelity_review.review.find_git_root", return_value=Path("/repo")):
        completed = MagicMock(returncode=0, stdout="diff --git a/src/file.py b/src/file.py\n+change", stderr="")
        with patch("subprocess.run", return_value=completed) as mock_run:
            diff = reviewer.get_file_diff("src/file.py", base_ref="HEAD~1")

    assert diff.startswith("diff --git")
    mock_run.assert_called_once_with(
        ["git", "diff", "HEAD~1", "--", "src/file.py"],
        cwd=Path("/repo"),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_get_file_diff_handles_missing_repo(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    with patch("claude_skills.sdd_fidelity_review.review.find_git_root", return_value=None):
        assert reviewer.get_file_diff("src/file.py") is None


def test_get_file_diff_handles_git_error(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    with patch("claude_skills.sdd_fidelity_review.review.find_git_root", return_value=Path("/repo")):
        completed = MagicMock(returncode=128, stdout="", stderr="fatal: bad revision")
        with patch("subprocess.run", return_value=completed):
            assert reviewer.get_file_diff("src/file.py") is None


def test_get_file_diff_handles_timeout(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    with patch("claude_skills.sdd_fidelity_review.review.find_git_root", return_value=Path("/repo")):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["git"], timeout=30)):
            assert reviewer.get_file_diff("src/file.py") is None


def test_parse_junit_xml_success(tmp_path: Path, sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    junit_xml = """<?xml version="1.0"?>
    <testsuites>
        <testsuite name="pytest" tests="2" failures="1" errors="0" skipped="0" time="1.5">
            <testcase classname="tests.test_auth" name="test_login_passes" time="0.7"/>
            <testcase classname="tests.test_auth" name="test_login_fails" time="0.8">
                <failure message="AssertionError">details</failure>
            </testcase>
        </testsuite>
    </testsuites>
    """

    xml_path = tmp_path / "results.xml"
    xml_path.write_text(junit_xml)

    results = reviewer._parse_junit_xml(str(xml_path))
    assert results is not None
    assert results["total"] == 2
    assert results["failed"] == 1
    assert "tests.test_auth::test_login_passes" in results["tests"]


def test_compute_file_hash_success(tmp_path: Path, sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    file_path = tmp_path / "data.txt"
    file_path.write_text("hello world")

    digest = reviewer.compute_file_hash(file_path)
    assert digest is not None
    assert len(digest) == 64


def test_compute_file_hash_handles_missing_file(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    assert reviewer.compute_file_hash(Path("/missing/file")) is None


def test_get_file_changes_full_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    files = [tmp_path / "a.py", tmp_path / "b.py"]
    for file in files:
        file.write_text("print('hi')")

    changes = reviewer.get_file_changes(files)
    assert changes["is_incremental"] is False
    assert set(changes["added"]) == {str(p) for p in files}


def test_get_file_changes_incremental_detects_modifications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_spec: Dict[str, object]
) -> None:
    monkeypatch.setenv("SDD_CACHE_DIR", str(tmp_path / "cache"))
    reviewer = _make_reviewer(sample_spec, incremental=True)
    reviewer.cache = reviewer.cache or CacheManager(cache_dir=tmp_path / "cache", auto_cleanup=False)

    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("v1")
    file2.write_text("v2")

    reviewer.save_file_state([file1, file2])

    file1.write_text("v1 modified")

    changes = reviewer.get_file_changes([file1, file2])
    assert changes["is_incremental"] is True
    assert str(file1) in changes["modified"]
    assert str(file2) in changes["unchanged"]


def test_save_file_state_requires_incremental(tmp_path: Path, sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)
    file = tmp_path / "code.py"
    file.write_text("data")

    assert reviewer.save_file_state([file]) is False


def test_save_file_state_incremental(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_spec: Dict[str, object]) -> None:
    monkeypatch.setenv("SDD_CACHE_DIR", str(tmp_path / "cache"))
    reviewer = _make_reviewer(sample_spec, incremental=True)
    reviewer.cache = reviewer.cache or CacheManager(cache_dir=tmp_path / "cache", auto_cleanup=False)

    file = tmp_path / "code.py"
    file.write_text("data")

    assert reviewer.save_file_state([file]) is True
    state = reviewer.cache.get_incremental_state("test-spec")
    assert str(file) in state


def test_get_task_diffs_collects_primary_file(sample_spec: Dict[str, object]) -> None:
    reviewer = _make_reviewer(sample_spec)

    diff_output = "diff --git a/src/auth.py b/src/auth.py\n+change"
    with patch.object(reviewer, "get_file_diff", return_value=diff_output):
        diffs = reviewer.get_task_diffs("task-1")

    assert diffs == {"src/auth.py": diff_output}


def test_get_task_test_results_runs_pytest(tmp_path: Path, sample_spec: Dict[str, object]) -> None:
    test_file = tmp_path / "tests" / "auth" / "test_login.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_dummy():\n    assert True\n")

    abs_test_path = str(test_file)
    sample_spec["hierarchy"]["task-1"]["metadata"]["verification_files"] = [abs_test_path]

    reviewer = _make_reviewer(sample_spec)

    fake_results = {"total": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "tests": {}}
    with patch.object(reviewer, "_run_and_parse_tests", return_value=fake_results) as mock_runner:
        results = reviewer.get_task_test_results("task-1")

    assert results == fake_results
    mock_runner.assert_called_once_with(abs_test_path)
