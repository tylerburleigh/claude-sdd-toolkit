"""
Unit tests for code-doc detectors module.

Tests framework detection, key file identification, layer detection,
and context summary generation.
"""

import pytest
from pathlib import Path

from claude_skills.llm_doc_gen.analysis.detectors import (
    detect_framework,
    identify_key_files,
    detect_layers,
    suggest_reading_order,
    extract_readme,
    create_context_summary
)


class TestFrameworkDetection:
    """Tests for detect_framework()."""

    def test_detect_fastapi(self, sample_modules):
        """Should detect FastAPI as primary framework."""
        result = detect_framework(sample_modules)

        assert 'FastAPI' in result['detected']
        assert result['primary'] == 'FastAPI'
        assert result['type'] == 'web'
        assert result['confidence']['FastAPI'] > 0.5

    def test_detect_django(self, django_modules):
        """Should detect Django as primary framework."""
        result = detect_framework(django_modules)

        assert 'Django' in result['detected']
        assert result['primary'] == 'Django'
        assert result['type'] == 'web'

    def test_detect_flask(self, flask_modules):
        """Should detect Flask as primary framework."""
        result = detect_framework(flask_modules)

        assert 'Flask' in result['detected']
        assert result['primary'] == 'Flask'
        assert result['type'] == 'web'

    def test_detect_multiple_frameworks(self, sample_modules):
        """Should detect multiple frameworks and libraries."""
        result = detect_framework(sample_modules)

        # Should detect FastAPI and Pydantic
        assert 'FastAPI' in result['detected']
        assert 'Pydantic' in result['detected']
        assert len(result['detected']) >= 2

    def test_detect_no_framework(self, plain_modules):
        """Should return None for plain Python library."""
        result = detect_framework(plain_modules)

        assert result['primary'] is None
        assert result['type'] == 'library'
        assert len(result['detected']) == 0

    def test_confidence_scores(self, sample_modules):
        """Should provide confidence scores for detected frameworks."""
        result = detect_framework(sample_modules)

        assert 'confidence' in result
        assert all(0 <= conf <= 1 for conf in result['confidence'].values())


class TestKeyFileIdentification:
    """Tests for identify_key_files()."""

    def test_identify_main_py(self, sample_modules):
        """Should identify main.py as a key file."""
        key_files = identify_key_files(sample_modules)

        assert 'app/main.py' in key_files

    def test_identify_config_files(self, sample_modules):
        """Should identify config.py as a key file."""
        key_files = identify_key_files(sample_modules)

        assert 'app/config.py' in key_files

    def test_prioritize_root_files(self, sample_modules):
        """Should prioritize files closer to root."""
        key_files = identify_key_files(sample_modules)

        # main.py at app/main.py should come before deeply nested files
        main_index = next(i for i, f in enumerate(key_files) if 'main.py' in f)
        deep_nested = [i for i, f in enumerate(key_files) if 'deep/nested' in f]

        if deep_nested:
            assert main_index < deep_nested[0]

    def test_prioritize_with_docstrings(self, sample_modules):
        """Should boost priority for files with docstrings."""
        key_files = identify_key_files(sample_modules)

        # Files with docstrings should be prioritized
        files_with_docs = ['app/main.py', 'app/config.py', 'app/models/user.py']
        assert any(f in key_files for f in files_with_docs)

    def test_exclude_test_files_from_top(self, sample_modules):
        """Test files should not be in top priority."""
        key_files = identify_key_files(sample_modules)

        # main.py should come before test files
        main_index = next(i for i, f in enumerate(key_files) if 'main.py' in f)
        test_indices = [i for i, f in enumerate(key_files) if 'test' in f.lower()]

        if test_indices:
            assert main_index < min(test_indices)

    def test_limit_key_files(self, sample_modules):
        """Should return reasonable number of key files."""
        key_files = identify_key_files(sample_modules)

        # Should not return all files, only key ones
        assert len(key_files) <= 15
        assert len(key_files) > 0

    def test_with_readme(self, sample_modules, temp_project_dir):
        """Should include README if it exists."""
        key_files = identify_key_files(sample_modules, temp_project_dir)

        assert any('README' in f for f in key_files)


class TestLayerDetection:
    """Tests for detect_layers()."""

    def test_detect_routers_layer(self, sample_modules):
        """Should detect router files."""
        layers = detect_layers(sample_modules)

        assert 'routers' in layers
        assert 'app/routers/users.py' in layers['routers']

    def test_detect_models_layer(self, sample_modules):
        """Should detect model files."""
        layers = detect_layers(sample_modules)

        assert 'models' in layers
        assert 'app/models/user.py' in layers['models']

    def test_detect_services_layer(self, sample_modules):
        """Should detect service files."""
        layers = detect_layers(sample_modules)

        assert 'services' in layers
        assert 'app/services/user_service.py' in layers['services']

    def test_detect_repositories_layer(self, sample_modules):
        """Should detect repository files."""
        layers = detect_layers(sample_modules)

        assert 'repositories' in layers
        assert 'app/repositories/user_repo.py' in layers['repositories']

    def test_detect_utils_layer(self, sample_modules):
        """Should detect utility files."""
        layers = detect_layers(sample_modules)

        assert 'utils' in layers
        assert 'app/utils/helpers.py' in layers['utils']

    def test_detect_middleware_layer(self, sample_modules):
        """Should detect middleware files."""
        layers = detect_layers(sample_modules)

        assert 'middleware' in layers
        assert 'app/middleware/auth.py' in layers['middleware']

    def test_detect_config_layer(self, sample_modules):
        """Should detect config files."""
        layers = detect_layers(sample_modules)

        assert 'config' in layers
        assert 'app/config.py' in layers['config']

    def test_detect_tests_layer(self, sample_modules):
        """Should detect test files."""
        layers = detect_layers(sample_modules)

        assert 'tests' in layers
        assert 'tests/test_users.py' in layers['tests']


class TestReadingOrder:
    """Tests for suggest_reading_order()."""

    def test_reading_order_entry_first(self, sample_modules, sample_framework_info):
        """Entry point files should come first."""
        key_files = identify_key_files(sample_modules)
        reading_order = suggest_reading_order(key_files, sample_framework_info)

        # main.py should be in first few files
        main_index = next((i for i, f in enumerate(reading_order) if 'main.py' in f), None)
        assert main_index is not None
        assert main_index < 3

    def test_reading_order_config_early(self, sample_modules, sample_framework_info):
        """Config files should come early."""
        key_files = identify_key_files(sample_modules)
        reading_order = suggest_reading_order(key_files, sample_framework_info)

        # config.py should be in first few files
        config_index = next((i for i, f in enumerate(reading_order) if 'config.py' in f), None)
        if config_index is not None:
            assert config_index < 5

    def test_reading_order_models_before_routes(self, sample_modules, sample_framework_info):
        """Models should generally come before routes."""
        key_files = identify_key_files(sample_modules)
        reading_order = suggest_reading_order(key_files, sample_framework_info)

        model_indices = [i for i, f in enumerate(reading_order) if 'model' in f.lower()]
        route_indices = [i for i, f in enumerate(reading_order) if 'router' in f.lower() or 'route' in f.lower()]

        if model_indices and route_indices:
            # At least some models should come before routes
            assert min(model_indices) < max(route_indices)


class TestReadmeExtraction:
    """Tests for extract_readme()."""

    def test_extract_readme_md(self, temp_project_dir):
        """Should extract README.md content."""
        content = extract_readme(temp_project_dir)

        assert content is not None
        assert "Test Project" in content

    def test_extract_readme_not_found(self, tmp_path):
        """Should return None when README not found."""
        content = extract_readme(tmp_path)

        assert content is None


class TestContextSummary:
    """Tests for create_context_summary()."""

    def test_create_basic_summary(
        self,
        sample_framework_info,
        sample_modules,
        sample_layers,
        sample_statistics
    ):
        """Should create a valid context summary."""
        key_files = identify_key_files(sample_modules)
        summary = create_context_summary(
            sample_framework_info,
            key_files,
            sample_layers,
            sample_statistics
        )

        assert "FastAPI" in summary
        assert "Total Files" in summary
        assert "Architectural Layers" in summary
        assert "Key Files" in summary

    def test_summary_with_readme(
        self,
        sample_framework_info,
        sample_modules,
        sample_layers,
        sample_statistics
    ):
        """Should include README excerpt when provided."""
        key_files = identify_key_files(sample_modules)
        readme_content = "# My Project\n\nThis is a sample project."

        summary = create_context_summary(
            sample_framework_info,
            key_files,
            sample_layers,
            sample_statistics,
            readme_content
        )

        assert "README" in summary
        assert "My Project" in summary

    def test_summary_structure(
        self,
        sample_framework_info,
        sample_modules,
        sample_layers,
        sample_statistics
    ):
        """Summary should have expected sections."""
        key_files = identify_key_files(sample_modules)
        summary = create_context_summary(
            sample_framework_info,
            key_files,
            sample_layers,
            sample_statistics
        )

        # Should have section headers
        assert "##" in summary
        assert "**" in summary  # Bold markers
        assert "- " in summary  # List items
