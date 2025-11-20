"""
Unit tests for the parser wrapper module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from .parsers import (
    DeepScanParser,
    ScanConfig,
    create_deep_scanner,
    quick_scan
)


@pytest.fixture
def temp_project():
    """Create a temporary test project."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create test Python file
    (temp_dir / "main.py").write_text("""
def hello_world():
    '''Say hello.'''
    print("Hello, world!")

class TestClass:
    '''A test class.'''
    def method(self):
        pass
""")

    # Create test JavaScript file
    (temp_dir / "app.js").write_text("""
function greet(name) {
    console.log(`Hello, ${name}!`);
}

class MyClass {
    constructor() {}
}
""")

    # Create directory to exclude
    excluded = temp_dir / "node_modules"
    excluded.mkdir()
    (excluded / "dependency.js").write_text("// Should be excluded")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_scan_config_creation():
    """Test ScanConfig creation."""
    config = ScanConfig(
        project_root=Path("."),
        exclude_patterns=["test"],
        verbose=True
    )
    # ScanConfig doesn't resolve paths, scanner does
    assert config.project_root == Path(".")
    assert "test" in config.exclude_patterns
    assert config.verbose is True


def test_create_deep_scanner():
    """Test scanner creation."""
    scanner = create_deep_scanner(
        project_root=Path("."),
        verbose=False
    )
    assert isinstance(scanner, DeepScanParser)
    assert scanner.config.verbose is False


def test_scan_python_file(temp_project):
    """Test scanning a Python file."""
    scanner = create_deep_scanner(
        project_root=temp_project,
        verbose=False
    )
    result = scanner.scan()

    assert result.files_scanned > 0
    assert len(result.parse_result.functions) >= 1  # hello_world function
    assert len(result.parse_result.classes) >= 1    # TestClass


def test_scan_multi_language(temp_project):
    """Test scanning multiple languages."""
    scanner = create_deep_scanner(
        project_root=temp_project,
        verbose=False
    )
    result = scanner.scan()

    # Should detect both Python and JavaScript
    assert len(result.languages_detected) >= 2
    assert result.files_scanned >= 2  # main.py and app.js


def test_exclusion_patterns(temp_project):
    """Test that exclusion patterns work."""
    scanner = create_deep_scanner(
        project_root=temp_project,
        exclude_patterns=["node_modules"],
        verbose=False
    )
    result = scanner.scan()

    # Should not include files from node_modules
    for module in result.parse_result.modules:
        assert "node_modules" not in module.file


def test_quick_scan(temp_project):
    """Test quick_scan convenience function."""
    result = quick_scan(str(temp_project), verbose=False)

    assert isinstance(result.parse_result.modules, list)
    assert result.files_scanned > 0


def test_language_statistics(temp_project):
    """Test language statistics calculation."""
    scanner = create_deep_scanner(
        project_root=temp_project,
        verbose=False
    )
    result = scanner.scan()
    stats = scanner.get_language_statistics(result)

    # Should have statistics for at least Python
    assert "python" in stats
    assert stats["python"]["files"] > 0


def test_scan_result_to_dict(temp_project):
    """Test ScanResult serialization."""
    result = quick_scan(str(temp_project), verbose=False)
    result_dict = result.to_dict()

    assert "parse_result" in result_dict
    assert "files_scanned" in result_dict
    assert "languages_detected" in result_dict
    assert isinstance(result_dict["languages_detected"], list)


def test_scan_single_file(temp_project):
    """Test scanning a single file."""
    scanner = create_deep_scanner(
        project_root=temp_project,
        verbose=False
    )

    main_py = temp_project / "main.py"
    result = scanner.scan_file(main_py)

    assert len(result.functions) >= 1
    assert len(result.classes) >= 1


def test_empty_directory():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = quick_scan(temp_dir, verbose=False)
        assert result.files_scanned == 0
        assert len(result.languages_detected) == 0


def test_scan_with_errors():
    """Test scanning with syntax errors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create file with syntax error
        (temp_path / "bad.py").write_text("def broken(\npass")

        result = quick_scan(temp_dir, verbose=False)

        # Should capture the error
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
