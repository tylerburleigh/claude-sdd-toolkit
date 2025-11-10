from __future__ import annotations

from pathlib import Path

import pytest

from claude_skills.sdd_fidelity_review.review import FidelityReviewer


pytestmark = pytest.mark.integration


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_get_file_changes_falls_back_on_first_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_json_spec_simple,
    specs_structure,
) -> None:
    """The first incremental run should behave like a full review."""
    monkeypatch.setenv("SDD_CACHE_DIR", str(tmp_path / "cache"))
    reviewer = FidelityReviewer(
        "simple-spec-2025-01-01-001",
        spec_path=specs_structure,
        incremental=True,
    )

    files = [
        _write(tmp_path / "alpha.py", "print('alpha')"),
        _write(tmp_path / "beta.py", "print('beta')"),
    ]

    changes = reviewer.get_file_changes(files)

    assert changes["is_incremental"] is False
    assert set(changes["added"]) == {str(path) for path in files}
    assert changes["modified"] == []
    assert changes["unchanged"] == []


def test_incremental_file_changes_detect_modifications(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_json_spec_simple,
    specs_structure,
) -> None:
    """Subsequent runs should detect modified, added, and unchanged files."""
    monkeypatch.setenv("SDD_CACHE_DIR", str(tmp_path / "cache"))
    reviewer = FidelityReviewer(
        "simple-spec-2025-01-01-001",
        spec_path=specs_structure,
        incremental=True,
    )

    alpha = _write(tmp_path / "alpha.py", "print('alpha')")
    beta = _write(tmp_path / "beta.py", "print('beta')")

    reviewer.save_file_state([alpha, beta])

    # Modify alpha, keep beta unchanged, introduce gamma.
    _write(alpha, "print('alpha-updated')")
    gamma = _write(tmp_path / "gamma.py", "print('gamma')")

    changes = reviewer.get_file_changes([alpha, beta, gamma])

    assert changes["is_incremental"] is True
    assert str(alpha) in changes["modified"]
    assert str(beta) in changes["unchanged"]
    assert str(gamma) in changes["added"]
    assert changes["removed"] == []
