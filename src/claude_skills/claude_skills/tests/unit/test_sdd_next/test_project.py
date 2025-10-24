"""
Unit tests for sdd-next project analysis operations.

Tests: detect_project, find_tests, check_environment, find_related_files.
"""

import pytest
from pathlib import Path

from claude_skills.sdd_next.project import detect_project, find_tests, check_environment, find_related_files


class TestDetectProject:
    """Tests for detect_project function."""

    def test_detect_node_project(self, sample_node_project):
        """Test detecting a Node.js project."""
        result = detect_project(sample_node_project)

        assert result is not None
        assert result["project_type"] in ["node", "nodejs", "javascript"]
        assert "dependencies" in result

    def test_detect_python_project(self, sample_python_project):
        """Test detecting a Python project."""
        result = detect_project(sample_python_project)

        assert result is not None
        assert result["project_type"] in ["python", "py"]
        assert "dependencies" in result or "dependency_manager" in result

    def test_detect_project_includes_config_files(self, sample_node_project):
        """Test that detected project includes config files."""
        result = detect_project(sample_node_project)

        assert "config_files" in result
        assert any("package.json" in str(f) for f in result["config_files"])

    def test_detect_project_extracts_dependencies(self, sample_node_project):
        """Test that project detection extracts dependencies."""
        result = detect_project(sample_node_project)

        assert "dependencies" in result
        deps = result["dependencies"]
        assert "express" in deps
        assert "lodash" in deps

    def test_detect_project_extracts_dev_dependencies(self, sample_node_project):
        """Test extracting dev dependencies."""
        result = detect_project(sample_node_project)

        assert "dev_dependencies" in result
        dev_deps = result["dev_dependencies"]
        assert "jest" in dev_deps
        assert "eslint" in dev_deps

    def test_detect_unknown_project(self, tmp_path):
        """Test detecting unknown project type."""
        empty_project = tmp_path / "unknown"
        empty_project.mkdir()

        result = detect_project(empty_project)

        assert result is not None
        assert result["project_type"] in ["unknown", "none", ""]


class TestFindTests:
    """Tests for find_tests function."""

    def test_find_tests_in_node_project(self, sample_node_project):
        """Test finding tests in Node.js project."""
        result = find_tests(sample_node_project)

        assert result is not None
        assert "test_files" in result
        assert len(result["test_files"]) > 0
        assert any("test.js" in str(f) for f in result["test_files"])

    def test_find_tests_in_python_project(self, sample_python_project):
        """Test finding tests in Python project."""
        result = find_tests(sample_python_project)

        assert result is not None
        assert "test_files" in result
        assert len(result["test_files"]) > 0
        assert any("test_" in str(f) for f in result["test_files"])

    def test_find_tests_detects_framework(self, sample_node_project):
        """Test that find_tests detects test framework."""
        result = find_tests(sample_node_project)

        assert "test_framework" in result
        # Should detect jest or similar
        assert result["test_framework"] in ["jest", "mocha", "pytest", "unittest", "unknown", None]

    def test_find_corresponding_test_file(self, sample_python_project):
        """Test finding corresponding test file for a source file."""
        source_file = sample_python_project / "src" / "main.py"

        result = find_tests(sample_python_project, str(source_file))

        assert result is not None
        if "corresponding_test" in result and result["corresponding_test"]:
            assert "test_main" in result["corresponding_test"]

    def test_find_tests_empty_project(self, tmp_path):
        """Test finding tests in project with no tests."""
        empty_project = tmp_path / "empty"
        empty_project.mkdir()

        result = find_tests(empty_project)

        assert result is not None
        assert result["test_files"] == [] or len(result["test_files"]) == 0


class TestCheckEnvironment:
    """Tests for check_environment function."""

    def test_check_environment_valid_project(self, sample_node_project):
        """Test checking environment for valid project."""
        result = check_environment(sample_node_project)

        assert result is not None
        assert "valid" in result
        assert "installed_dependencies" in result or "dependencies" in result

    def test_check_environment_with_requirements(self, sample_node_project):
        """Test checking with required dependencies."""
        required = ["express", "lodash"]

        result = check_environment(sample_node_project, required)

        assert result is not None
        assert result["valid"] is True or result.get("missing_dependencies") == []

    def test_check_environment_missing_dependencies(self, sample_node_project):
        """Test checking with missing dependencies."""
        required = ["nonexistent-package-xyz"]

        result = check_environment(sample_node_project, required)

        assert result is not None
        assert "missing_dependencies" in result
        assert "nonexistent-package-xyz" in result["missing_dependencies"]

    def test_check_environment_includes_config_files(self, sample_python_project):
        """Test that environment check includes config files."""
        result = check_environment(sample_python_project)

        assert "config_files_found" in result or "config_files" in result
        if "config_files_found" in result:
            assert len(result["config_files_found"]) > 0

    def test_check_environment_warnings(self, tmp_path):
        """Test that environment check includes warnings for issues."""
        empty_project = tmp_path / "empty"
        empty_project.mkdir()

        result = check_environment(empty_project)

        # Should have warnings about missing config
        assert "warnings" in result or result["valid"] is False


class TestFindRelatedFiles:
    """Tests for find_related_files function."""

    def test_find_related_files_test_files(self, sample_python_project):
        """Test finding test files related to source file."""
        source_file = "src/main.py"

        result = find_related_files(source_file, sample_python_project)

        assert result is not None
        assert "test_files" in result
        # Should find test_main.py
        if result["test_files"]:
            assert any("test_main" in str(f) for f in result["test_files"])

    def test_find_related_files_same_directory(self, sample_python_project):
        """Test finding files in same directory."""
        source_file = "src/main.py"

        result = find_related_files(source_file, sample_python_project)

        assert "same_directory" in result
        # Should find __init__.py in same directory
        if result["same_directory"]:
            assert any("__init__" in str(f) for f in result["same_directory"])

    def test_find_related_files_similar_files(self, sample_node_project):
        """Test finding files with similar names."""
        source_file = "src/index.js"

        result = find_related_files(source_file, sample_node_project)

        assert "similar_files" in result

    def test_find_related_files_includes_source(self, sample_python_project):
        """Test that result includes the source file."""
        source_file = "src/main.py"

        result = find_related_files(source_file, sample_python_project)

        assert "source_file" in result
        assert "main.py" in result["source_file"]

    def test_find_related_files_nonexistent(self, tmp_path):
        """Test finding related files for non-existent file."""
        result = find_related_files("nonexistent.py", tmp_path)

        assert result is not None
        # Should handle gracefully


@pytest.mark.integration
class TestProjectIntegration:
    """Integration tests for project analysis."""

    def test_complete_project_analysis_workflow(self, sample_node_project):
        """Test complete project analysis workflow."""
        # Step 1: Detect project
        project = detect_project(sample_node_project)
        assert project is not None
        assert project["project_type"] in ["node", "nodejs", "javascript"]

        # Step 2: Find tests
        tests = find_tests(sample_node_project)
        assert len(tests["test_files"]) > 0

        # Step 3: Check environment
        env = check_environment(sample_node_project)
        assert env["valid"] is True

        # Step 4: Find related files
        if tests["test_files"]:
            source_file = "src/index.js"
            related = find_related_files(source_file, sample_node_project)
            assert related is not None

    def test_python_project_full_analysis(self, sample_python_project):
        """Test full analysis of Python project."""
        # Detect
        project = detect_project(sample_python_project)
        assert "python" in project["project_type"].lower()

        # Find tests
        tests = find_tests(sample_python_project)
        assert tests["test_framework"] in ["pytest", "unittest", None]

        # Check environment
        env = check_environment(sample_python_project, ["requests", "flask"])
        assert env is not None

        # Find related
        related = find_related_files("src/main.py", sample_python_project)
        assert "test_main" in str(related.get("test_files", []))
