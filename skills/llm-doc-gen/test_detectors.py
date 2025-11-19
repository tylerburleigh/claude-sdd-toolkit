"""
Unit tests for the project structure detector module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json

from detectors import (
    ProjectStructureDetector,
    ProjectStructure,
    detect_project_structure
)


@pytest.fixture
def temp_monolith():
    """Create a temporary monolithic project."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create package.json at root
    (temp_dir / "package.json").write_text(json.dumps({
        "name": "my-app",
        "version": "1.0.0"
    }))

    # Create source files
    src = temp_dir / "src"
    src.mkdir()
    (src / "index.js").write_text("console.log('hello');")
    (src / "app.py").write_text("print('hello')")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_monorepo():
    """Create a temporary monorepo project."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create workspace config
    (temp_dir / "package.json").write_text(json.dumps({
        "name": "my-workspace",
        "workspaces": ["packages/*"]
    }))

    # Create multiple packages
    packages = temp_dir / "packages"
    packages.mkdir()

    for name in ["package-a", "package-b", "package-c"]:
        pkg_dir = packages / name
        pkg_dir.mkdir()
        (pkg_dir / "package.json").write_text(json.dumps({
            "name": name,
            "version": "1.0.0"
        }))
        (pkg_dir / "index.js").write_text(f"// {name}")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_client_server():
    """Create a temporary client/server project."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create client directory
    client = temp_dir / "client"
    client.mkdir()
    (client / "package.json").write_text(json.dumps({
        "name": "client",
        "version": "1.0.0"
    }))
    (client / "app.js").write_text("// Client app")

    # Create server directory
    server = temp_dir / "server"
    server.mkdir()
    (server / "package.json").write_text(json.dumps({
        "name": "server",
        "version": "1.0.0"
    }))
    (server / "server.js").write_text("// Server app")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_python_package():
    """Create a temporary Python package."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create pyproject.toml
    (temp_dir / "pyproject.toml").write_text("""
[build-system]
requires = ["setuptools"]

[project]
name = "my-package"
version = "1.0.0"
""")

    # Create src structure
    src = temp_dir / "src" / "my_package"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text("def main(): pass")

    yield temp_dir
    shutil.rmtree(temp_dir)


def test_detector_initialization():
    """Test detector initialization."""
    detector = ProjectStructureDetector(Path("."), verbose=False)
    assert detector.project_root == Path(".").resolve()
    assert detector.verbose is False


def test_detect_monolith(temp_monolith):
    """Test detection of monolithic structure."""
    result = detect_project_structure(str(temp_monolith), verbose=False)
    assert result.structure_type == ProjectStructure.MONOLITH
    assert len(result.parts) == 1


def test_detect_monorepo(temp_monorepo):
    """Test detection of monorepo structure."""
    result = detect_project_structure(str(temp_monorepo), verbose=False)
    assert result.structure_type == ProjectStructure.MONOREPO
    assert len(result.parts) >= 3  # package-a, package-b, package-c
    assert result.workspace_config is not None
    assert "npm_workspaces" in result.workspace_config


def test_detect_client_server(temp_client_server):
    """Test detection of client/server structure."""
    result = detect_project_structure(str(temp_client_server), verbose=False)
    assert result.structure_type == ProjectStructure.CLIENT_SERVER
    assert len(result.parts) == 2

    # Check that client and server are detected
    types = {p.type for p in result.parts}
    assert "client" in types
    assert "server" in types


def test_detect_python_package(temp_python_package):
    """Test detection of Python package."""
    result = detect_project_structure(str(temp_python_package), verbose=False)
    # Should detect as monolith with one package
    assert len(result.parts) >= 1
    assert result.parts[0].has_pyproject_toml or any(
        p.has_pyproject_toml for p in result.parts
    )


def test_workspace_config_detection(temp_monorepo):
    """Test workspace configuration detection."""
    detector = ProjectStructureDetector(Path(temp_monorepo), verbose=False)
    config = detector._detect_workspace_config()
    assert config is not None
    assert "npm_workspaces" in config


def test_part_languages(temp_client_server):
    """Test language detection for project parts."""
    result = detect_project_structure(str(temp_client_server), verbose=False)
    for part in result.parts:
        assert "javascript" in part.languages


def test_result_to_dict(temp_monolith):
    """Test ProjectStructureInfo serialization."""
    result = detect_project_structure(str(temp_monolith), verbose=False)
    result_dict = result.to_dict()

    assert "structure_type" in result_dict
    assert "parts" in result_dict
    assert "confidence" in result_dict
    assert isinstance(result_dict["parts"], list)


def test_confidence_scoring(temp_monorepo):
    """Test confidence scoring."""
    result = detect_project_structure(str(temp_monorepo), verbose=False)
    # Monorepo with workspace config should have high confidence
    assert result.confidence >= 0.7


def test_empty_directory():
    """Test detection on empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = detect_project_structure(temp_dir, verbose=False)
        # Should default to monolith with no parts or UNKNOWN
        assert result.structure_type in (ProjectStructure.MONOLITH, ProjectStructure.UNKNOWN)


def test_indicators_present(temp_monorepo):
    """Test that indicators are provided."""
    result = detect_project_structure(str(temp_monorepo), verbose=False)
    assert len(result.indicators) > 0
    assert any("workspace" in indicator.lower() for indicator in result.indicators)


def test_detect_lerna_workspace():
    """Test detection of Lerna workspace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create lerna.json
        (temp_path / "lerna.json").write_text(json.dumps({
            "version": "1.0.0",
            "packages": ["packages/*"]
        }))

        result = detect_project_structure(temp_dir, verbose=False)
        assert result.workspace_config is not None
        assert "lerna" in result.workspace_config


def test_detect_nx_workspace():
    """Test detection of Nx workspace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create nx.json
        (temp_path / "nx.json").write_text(json.dumps({
            "npmScope": "myorg"
        }))

        result = detect_project_structure(temp_dir, verbose=False)
        assert result.workspace_config is not None
        assert "nx" in result.workspace_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
