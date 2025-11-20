"""
Tests for two-tier documentation generation.

Verifies that two-tier output produces correct summary and detail files,
with summary containing signatures only and detail files containing full data.
"""

import json
from pathlib import Path
from typing import Dict, Any

import pytest

from claude_skills.llm_doc_gen.analysis.formatter import JSONGenerator


@pytest.fixture
def sample_analysis() -> Dict[str, Any]:
    """Create sample analysis data for testing."""
    return {
        'modules': [
            {
                'path': 'module.py',
                'language': 'python',
                'lines': 100,
                'classes': ['Greeter'],
                'functions': ['hello']
            },
            {
                'path': 'utils.py',
                'language': 'python',
                'lines': 50,
                'classes': [],
                'functions': ['helper']
            }
        ],
        'classes': [
            {
                'name': 'Greeter',
                'file': 'module.py',
                'line': 10,
                'bases': ['object'],
                'docstring': 'A simple greeter class.',
                'methods': [
                    {
                        'name': 'greet',
                        'signature': 'greet(self, name: str) -> str',
                        'line': 12,
                        'parameters': [{'name': 'name', 'type': 'str'}],
                        'return_type': 'str',
                        'docstring': 'Greet someone by name.'
                    }
                ],
                'properties': []
            }
        ],
        'functions': [
            {
                'name': 'hello',
                'signature': 'hello() -> str',
                'file': 'module.py',
                'line': 5,
                'parameters': [],
                'return_type': 'str',
                'docstring': 'Say hello.',
                'decorators': [],
                'complexity': 1,
                'is_async': False
            },
            {
                'name': 'helper',
                'signature': 'helper(x: int) -> int',
                'file': 'utils.py',
                'line': 3,
                'parameters': [{'name': 'x', 'type': 'int'}],
                'return_type': 'int',
                'docstring': 'Helper function.',
                'decorators': [],
                'complexity': 2,
                'is_async': False
            }
        ],
        'dependencies': {
            'os': ['path', 'environ'],
            'sys': ['argv']
        }
    }


@pytest.fixture
def sample_statistics() -> Dict[str, Any]:
    """Create sample statistics data for testing."""
    return {
        'total_files': 2,
        'total_lines': 150,
        'total_classes': 1,
        'total_functions': 2
    }


def test_generate_two_tier_creates_files(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify generate_two_tier creates summary and detail files."""
    generator = JSONGenerator('TestProject', '1.0.0')

    result = generator.generate_two_tier(
        tmp_path,
        sample_analysis,
        sample_statistics
    )

    # Verify return structure
    assert 'summary_file' in result
    assert 'detail_files' in result

    # Verify summary file exists
    summary_file = result['summary_file']
    assert summary_file.exists()
    assert summary_file.name == 'codebase.json'

    # Verify details directory exists
    details_dir = tmp_path / 'details'
    assert details_dir.exists()
    assert details_dir.is_dir()

    # Verify detail files exist
    detail_files = result['detail_files']
    assert len(detail_files) == 2  # Two modules
    for detail_file in detail_files:
        assert detail_file.exists()
        assert detail_file.parent.name == 'details'


def test_summary_contains_signatures_only(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify summary file contains signatures without docstrings or bodies."""
    generator = JSONGenerator('TestProject', '1.0.0')

    result = generator.generate_two_tier(
        tmp_path,
        sample_analysis,
        sample_statistics
    )

    # Load summary file
    with open(result['summary_file'], 'r', encoding='utf-8') as f:
        summary = json.load(f)

    # Verify summary metadata
    assert summary['metadata']['summary'] is True
    assert summary['metadata']['project_name'] == 'TestProject'
    assert summary['metadata']['version'] == '1.0.0'

    # Verify lightweight statistics (no full statistics object)
    assert 'statistics' in summary
    stats = summary['statistics']
    assert stats['total_files'] == 2
    assert stats['total_classes'] == 1
    assert stats['total_functions'] == 2
    assert stats['total_lines'] == 150

    # Verify modules are lightweight
    assert 'modules' in summary
    assert len(summary['modules']) == 2
    module = summary['modules'][0]
    assert 'path' in module
    assert 'language' in module
    assert 'lines' in module
    assert 'classes' in module
    assert 'functions' in module

    # Verify functions have signatures but no docstrings
    assert 'functions' in summary
    assert len(summary['functions']) == 2
    func = summary['functions'][0]
    assert 'name' in func
    assert 'signature' in func
    assert 'file' in func
    assert 'line' in func
    assert 'parameters' in func
    assert 'return_type' in func
    # Docstrings should NOT be in summary
    assert 'docstring' not in func

    # Verify classes have signatures but no docstrings
    assert 'classes' in summary
    assert len(summary['classes']) == 1
    cls = summary['classes'][0]
    assert 'name' in cls
    assert 'file' in cls
    assert 'line' in cls
    assert 'bases' in cls
    assert 'methods' in cls
    # Docstrings should NOT be in summary
    assert 'docstring' not in cls


def test_detail_files_contain_full_data(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify detail files contain complete documentation with docstrings."""
    generator = JSONGenerator('TestProject', '1.0.0')

    result = generator.generate_two_tier(
        tmp_path,
        sample_analysis,
        sample_statistics
    )

    # Load first detail file (module.py)
    detail_file = [f for f in result['detail_files'] if 'module.py' in str(f)][0]
    with open(detail_file, 'r', encoding='utf-8') as f:
        detail = json.load(f)

    # Verify detail metadata
    assert detail['metadata']['project_name'] == 'TestProject'
    assert detail['metadata']['module_path'] == 'module.py'

    # Verify module data is complete
    assert 'module' in detail
    module = detail['module']
    assert module['path'] == 'module.py'
    assert module['lines'] == 100

    # Verify classes contain full data including docstrings
    assert 'classes' in detail
    assert len(detail['classes']) == 1
    cls = detail['classes'][0]
    assert cls['name'] == 'Greeter'
    assert cls['docstring'] == 'A simple greeter class.'
    assert 'methods' in cls
    method = cls['methods'][0]
    assert method['docstring'] == 'Greet someone by name.'

    # Verify functions contain full data including docstrings
    assert 'functions' in detail
    assert len(detail['functions']) == 1
    func = detail['functions'][0]
    assert func['name'] == 'hello'
    assert func['docstring'] == 'Say hello.'

    # Verify statistics for this module
    assert 'statistics' in detail
    assert detail['statistics']['classes_count'] == 1
    assert detail['statistics']['functions_count'] == 1


def test_custom_detail_directory(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify custom detail directory name is respected."""
    generator = JSONGenerator('TestProject', '1.0.0')

    result = generator.generate_two_tier(
        tmp_path,
        sample_analysis,
        sample_statistics,
        detail_dir='custom_details'
    )

    # Verify custom directory was created
    custom_dir = tmp_path / 'custom_details'
    assert custom_dir.exists()
    assert custom_dir.is_dir()

    # Verify detail files are in custom directory
    for detail_file in result['detail_files']:
        assert detail_file.parent.name == 'custom_details'


def test_generate_with_two_tier_parameter(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify generate() method with two_tier=True delegates correctly."""
    generator = JSONGenerator('TestProject', '1.0.0')

    output_path = tmp_path / 'codebase.json'
    result = generator.generate(
        sample_analysis,
        sample_statistics,
        two_tier=True,
        output_path=output_path
    )

    # Verify return structure
    assert 'summary_file' in result
    assert 'detail_files' in result

    # Verify files were created
    assert result['summary_file'].exists()
    assert len(result['detail_files']) > 0


def test_generate_two_tier_false_maintains_compatibility(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify generate() with two_tier=False maintains backward compatibility."""
    generator = JSONGenerator('TestProject', '1.0.0')

    # Default behavior (two_tier=False)
    result = generator.generate(
        sample_analysis,
        sample_statistics,
        two_tier=False
    )

    # Should return in-memory dict (traditional behavior)
    assert isinstance(result, dict)
    assert 'metadata' in result
    assert 'statistics' in result
    assert 'modules' in result
    assert 'classes' in result
    assert 'functions' in result


def test_two_tier_requires_output_path(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any]
):
    """Verify two_tier=True requires output_path."""
    generator = JSONGenerator('TestProject', '1.0.0')

    with pytest.raises(ValueError, match='output_path required'):
        generator.generate(
            sample_analysis,
            sample_statistics,
            two_tier=True,
            output_path=None
        )


def test_detail_files_per_module(
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify one detail file is created per module."""
    generator = JSONGenerator('TestProject', '1.0.0')

    result = generator.generate_two_tier(
        tmp_path,
        sample_analysis,
        sample_statistics
    )

    # Should have 2 detail files (module.py and utils.py)
    assert len(result['detail_files']) == 2

    # Verify filenames
    filenames = [f.name for f in result['detail_files']]
    assert 'module.py.json' in filenames
    assert 'utils.py.json' in filenames
