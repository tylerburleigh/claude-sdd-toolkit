"""Tests for freshness checking module."""

import json
import pytest
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from claude_skills.llm_doc_gen.freshness import (
    FreshnessChecker,
    check_documentation_freshness
)


@pytest.fixture
def sample_codebase_json(tmp_path):
    """Create a sample codebase.json with metadata."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()

    codebase_path = docs_path / "codebase.json"

    # Generate timestamp from 1 hour ago
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    codebase_data = {
        "metadata": {
            "project_name": "TestProject",
            "version": "1.0.0",
            "generated_at": one_hour_ago.isoformat(),
            "languages": ["python"],
            "schema_version": "2.0"
        },
        "statistics": {
            "total_files": 10,
            "total_lines": 1000
        }
    }

    with open(codebase_path, 'w') as f:
        json.dump(codebase_data, f)

    return codebase_path


@pytest.fixture
def sample_source_files(tmp_path):
    """Create sample source files."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create a Python file
    py_file = src_dir / "main.py"
    py_file.write_text("# Main module\nprint('hello')\n")

    # Create a JS file
    js_file = src_dir / "app.js"
    js_file.write_text("console.log('hello');\n")

    return src_dir


@pytest.fixture
def fresh_codebase_json(tmp_path, sample_source_files):
    """Create a codebase.json newer than source files."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()

    codebase_path = docs_path / "codebase.json"

    # Create docs after source files, making it fresh
    time.sleep(0.1)  # Ensure timestamp difference

    now = datetime.now(timezone.utc)
    codebase_data = {
        "metadata": {
            "generated_at": now.isoformat()
        }
    }

    with open(codebase_path, 'w') as f:
        json.dump(codebase_data, f)

    return codebase_path


class TestFreshnessCheckerInitialization:
    """Tests for FreshnessChecker initialization."""

    def test_init_with_explicit_path(self, sample_codebase_json):
        """Test initialization with explicit docs path."""
        checker = FreshnessChecker(docs_path=str(sample_codebase_json))
        assert checker.docs_path == sample_codebase_json
        assert checker.metadata is None

    def test_init_with_directory_path(self, sample_codebase_json):
        """Test initialization with directory path."""
        docs_dir = sample_codebase_json.parent
        checker = FreshnessChecker(docs_path=str(docs_dir))
        assert checker.docs_path == sample_codebase_json

    def test_init_with_project_root(self, tmp_path, sample_codebase_json):
        """Test initialization with project root."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json.parent),
            project_root=str(tmp_path)
        )
        assert checker.project_root == tmp_path

    def test_auto_detection_docs_codebase_json(self, tmp_path, monkeypatch):
        """Test auto-detection of docs/codebase.json."""
        monkeypatch.chdir(tmp_path)

        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        codebase_file = docs_path / "codebase.json"
        codebase_file.write_text('{"metadata": {}}')

        checker = FreshnessChecker()
        assert checker.docs_path == codebase_file

    def test_auto_detection_docs_documentation_json(self, tmp_path, monkeypatch):
        """Test auto-detection of docs/codebase.json."""
        monkeypatch.chdir(tmp_path)

        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        doc_file = docs_path / "codebase.json"
        doc_file.write_text('{"metadata": {}}')

        checker = FreshnessChecker()
        assert checker.docs_path == doc_file

    def test_no_docs_found(self, tmp_path, monkeypatch):
        """Test when no documentation found."""
        monkeypatch.chdir(tmp_path)
        checker = FreshnessChecker()
        assert checker.docs_path is None


class TestMetadataLoading:
    """Tests for metadata loading."""

    def test_load_metadata_success(self, sample_codebase_json):
        """Test successful metadata loading."""
        checker = FreshnessChecker(docs_path=str(sample_codebase_json))
        result = checker.load_metadata()

        assert result is True
        assert checker.metadata is not None
        assert checker.metadata['project_name'] == "TestProject"
        assert 'generated_at' in checker.metadata

    def test_load_metadata_missing_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        # Use a path that definitely doesn't exist and won't auto-detect
        nonexistent = tmp_path / "missing" / "nonexistent.json"
        checker = FreshnessChecker(
            docs_path=str(nonexistent),
            project_root=str(tmp_path)
        )
        result = checker.load_metadata()

        assert result is False
        assert checker.metadata is None

    def test_load_metadata_invalid_json(self, tmp_path):
        """Test loading with invalid JSON."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json{")

        checker = FreshnessChecker(docs_path=str(bad_json))
        result = checker.load_metadata()

        assert result is False

    def test_get_generated_timestamp_success(self, sample_codebase_json):
        """Test getting generated timestamp."""
        checker = FreshnessChecker(docs_path=str(sample_codebase_json))
        timestamp = checker.get_generated_timestamp()

        assert timestamp is not None
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo is not None  # Should be timezone-aware

    def test_get_generated_timestamp_no_metadata(self, tmp_path):
        """Test getting timestamp when no metadata loaded."""
        nonexistent = tmp_path / "missing" / "nonexistent.json"
        checker = FreshnessChecker(
            docs_path=str(nonexistent),
            project_root=str(tmp_path)
        )
        timestamp = checker.get_generated_timestamp()

        assert timestamp is None

    def test_get_generated_timestamp_missing_field(self, tmp_path):
        """Test when generated_at field is missing."""
        docs_file = tmp_path / "docs.json"
        docs_file.write_text('{"metadata": {}}')

        checker = FreshnessChecker(docs_path=str(docs_file))
        checker.load_metadata()
        timestamp = checker.get_generated_timestamp()

        assert timestamp is None


class TestSourceFileScanning:
    """Tests for source file scanning."""

    def test_get_newest_source_file_default_extensions(self, tmp_path, sample_source_files):
        """Test finding newest source file with default extensions."""
        checker = FreshnessChecker(project_root=str(tmp_path))

        newest_file, newest_time = checker.get_newest_source_file()

        assert newest_file is not None
        assert newest_time is not None
        assert newest_file.suffix in ['.py', '.js']

    def test_get_newest_source_file_custom_extensions(self, tmp_path, sample_source_files):
        """Test finding newest file with custom extensions."""
        checker = FreshnessChecker(project_root=str(tmp_path))

        # Only look for Python files
        newest_file, newest_time = checker.get_newest_source_file(extensions=['.py'])

        assert newest_file is not None
        assert newest_file.suffix == '.py'

    def test_get_newest_source_file_excludes_patterns(self, tmp_path):
        """Test that excluded patterns are ignored."""
        # Create files in excluded directories
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("compiled")

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.js").write_text("library")

        # Create a valid source file
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("main")

        checker = FreshnessChecker(project_root=str(tmp_path))
        newest_file, newest_time = checker.get_newest_source_file()

        # Should only find main.py, not files in excluded dirs
        assert newest_file is not None
        assert "__pycache__" not in str(newest_file)
        assert "node_modules" not in str(newest_file)

    def test_get_newest_source_file_no_files(self, tmp_path):
        """Test when no source files exist."""
        checker = FreshnessChecker(project_root=str(tmp_path))

        newest_file, newest_time = checker.get_newest_source_file()

        assert newest_file is None
        assert newest_time is None

    def test_get_newest_source_file_returns_newest(self, tmp_path):
        """Test that the newest file is returned."""
        src = tmp_path / "src"
        src.mkdir()

        old_file = src / "old.py"
        old_file.write_text("old")

        time.sleep(0.1)  # Ensure timestamp difference

        new_file = src / "new.py"
        new_file.write_text("new")

        checker = FreshnessChecker(project_root=str(tmp_path))
        newest_file, newest_time = checker.get_newest_source_file()

        assert newest_file.name == "new.py"


class TestFreshnessChecking:
    """Tests for freshness checking."""

    def test_check_freshness_missing_docs(self, tmp_path):
        """Test when documentation doesn't exist."""
        checker = FreshnessChecker(
            docs_path=str(tmp_path / "nonexistent.json"),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()

        assert is_fresh is False
        assert details['status'] == 'missing'
        assert 'No codebase.json found' in details['reason']

    def test_check_freshness_stale_docs(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test when documentation is stale."""
        # Docs were created 1 hour ago (from fixture)
        # Source files were just created
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()

        assert is_fresh is False
        assert details['status'] == 'stale'
        assert 'outdated' in details['reason'].lower()
        assert details['age_seconds'] is not None
        assert details['age_seconds'] > 0

    def test_check_freshness_fresh_docs(self, tmp_path, fresh_codebase_json, sample_source_files):
        """Test when documentation is fresh."""
        checker = FreshnessChecker(
            docs_path=str(fresh_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()

        assert is_fresh is True
        assert details['status'] == 'fresh'
        assert 'up-to-date' in details['reason'].lower()

    def test_check_freshness_no_source_files(self, tmp_path, sample_codebase_json):
        """Test when no source files exist."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()

        # Should assume fresh if no sources to compare
        assert is_fresh is True
        assert details['status'] == 'unknown'

    def test_check_freshness_includes_details(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test that freshness check includes all expected details."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()

        assert 'status' in details
        assert 'reason' in details
        assert 'generated_at' in details
        assert 'newest_file' in details or details['status'] == 'missing'

    def test_check_freshness_custom_extensions(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test freshness check with custom file extensions."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness(extensions=['.py'])

        # Should work with custom extensions
        assert isinstance(is_fresh, bool)
        assert 'status' in details


class TestReportFormatting:
    """Tests for report formatting."""

    def test_format_fresh_report(self, tmp_path, fresh_codebase_json, sample_source_files):
        """Test formatting of fresh documentation report."""
        checker = FreshnessChecker(
            docs_path=str(fresh_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details)

        assert "✅" in report
        assert "fresh" in report.lower()

    def test_format_stale_report(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test formatting of stale documentation report."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details)

        assert "⚠️" in report
        assert "stale" in report.lower()

    def test_format_missing_report(self, tmp_path):
        """Test formatting of missing documentation report."""
        checker = FreshnessChecker(
            docs_path=str(tmp_path / "nonexistent.json"),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details)

        assert "❌" in report
        assert "missing" in report.lower()

    def test_format_report_with_details(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test report includes details when requested."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details, include_details=True)

        # Should include generated timestamp
        assert "Generated:" in report

    def test_format_report_without_details(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test report without details."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details, include_details=False)

        # Should not include detailed info
        assert "Generated:" not in report

    def test_format_report_includes_age(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test that report includes age information for stale docs."""
        checker = FreshnessChecker(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        is_fresh, details = checker.check_freshness()
        report = checker.format_freshness_report(is_fresh, details, include_details=True)

        if not is_fresh and details['status'] == 'stale':
            assert "Age:" in report or "behind" in report


class TestConvenienceFunction:
    """Tests for convenience function."""

    def test_check_documentation_freshness_function(self, tmp_path, sample_codebase_json, sample_source_files):
        """Test convenience function."""
        is_fresh, details = check_documentation_freshness(
            docs_path=str(sample_codebase_json),
            project_root=str(tmp_path)
        )

        assert isinstance(is_fresh, bool)
        assert isinstance(details, dict)
        assert 'status' in details
        assert 'reason' in details

    def test_convenience_function_auto_detection(self, tmp_path, monkeypatch):
        """Test convenience function with auto-detection."""
        monkeypatch.chdir(tmp_path)

        docs_path = tmp_path / "docs"
        docs_path.mkdir()

        codebase_file = docs_path / "codebase.json"
        codebase_data = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        with open(codebase_file, 'w') as f:
            json.dump(codebase_data, f)

        is_fresh, details = check_documentation_freshness()

        assert isinstance(is_fresh, bool)
        assert 'status' in details
