"""
Tests for DocumentationGenerator streaming and compression functionality.

Verifies that streaming output produces equivalent data to non-streaming output,
and that compression works correctly with both modes.
"""

import json
import gzip
from pathlib import Path
from typing import Dict, Any

import pytest

from claude_skills.llm_doc_gen.analysis.generator import DocumentationGenerator


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a minimal test project with Python files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create a simple Python file
    (project_dir / "module.py").write_text(
        """
\"\"\"Sample module for testing.\"\"\"

def hello():
    \"\"\"Say hello.\"\"\"
    return "hello"

class Greeter:
    \"\"\"A simple greeter class.\"\"\"

    def greet(self, name: str) -> str:
        \"\"\"Greet someone by name.\"\"\"
        return f"Hello, {name}!"
""",
        encoding="utf-8"
    )

    return project_dir


@pytest.fixture
def sample_analysis() -> Dict[str, Any]:
    """Create sample analysis data for testing."""
    return {
        'modules': [
            {
                'name': 'module',
                'file': 'module.py',
                'imports': [],
                'docstring': 'Sample module for testing.',
                'classes': [
                    {
                        'name': 'Greeter',
                        'file': 'module.py',
                        'docstring': 'A simple greeter class.',
                        'methods': [
                            {
                                'name': 'greet',
                                'params': [{'name': 'name', 'type': 'str'}],
                                'returns': 'str',
                                'docstring': 'Greet someone by name.'
                            }
                        ]
                    }
                ],
                'functions': [
                    {
                        'name': 'hello',
                        'file': 'module.py',
                        'docstring': 'Say hello.',
                        'params': [],
                        'returns': 'str'
                    }
                ],
                'lines': 16
            }
        ],
        'classes': [
            {
                'name': 'Greeter',
                'file': 'module.py',
                'docstring': 'A simple greeter class.',
                'methods': [
                    {
                        'name': 'greet',
                        'params': [{'name': 'name', 'type': 'str'}],
                        'returns': 'str',
                        'docstring': 'Greet someone by name.'
                    }
                ]
            }
        ],
        'functions': [
            {
                'name': 'hello',
                'file': 'module.py',
                'docstring': 'Say hello.',
                'params': [],
                'returns': 'str'
            }
        ],
        'dependencies': {},
        'errors': []
    }


@pytest.fixture
def sample_statistics() -> Dict[str, Any]:
    """Create sample statistics data for testing."""
    return {
        'total_files': 1,
        'total_lines': 16,
        'total_classes': 1,
        'total_functions': 1,
        'avg_complexity': 1.0,
        'max_complexity': 1,
        'high_complexity_functions': []
    }


def test_streaming_produces_equivalent_output(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify streaming and non-streaming produce equivalent content."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate non-streaming output
    non_streaming_path = tmp_path / "non_streaming.json"
    generator.save_json(
        non_streaming_path,
        sample_analysis,
        sample_statistics,
        streaming=False
    )

    # Generate streaming output
    streaming_path = tmp_path / "streaming.json"
    generator.save_json(
        streaming_path,
        sample_analysis,
        sample_statistics,
        streaming=True
    )

    # Load both outputs
    with open(non_streaming_path, 'r', encoding='utf-8') as f:
        non_streaming_data = json.load(f)

    with open(streaming_path, 'r', encoding='utf-8') as f:
        streaming_data = json.load(f)

    # Streaming merges statistics into metadata, so we need to normalize
    # Extract core content for comparison (ignoring structure differences)

    # Non-streaming has separate statistics key
    assert 'statistics' in non_streaming_data
    assert 'metadata' in non_streaming_data

    # Streaming merges statistics into metadata
    assert 'metadata' in streaming_data
    streaming_stats = {
        k: streaming_data['metadata'][k]
        for k in ['total_files', 'total_lines', 'total_classes', 'total_functions']
        if k in streaming_data['metadata']
    }

    # Compare statistics content (regardless of structure)
    for key in ['total_files', 'total_lines', 'total_classes', 'total_functions']:
        assert non_streaming_data['statistics'][key] == streaming_stats[key], \
            f"Statistics mismatch for {key}"

    # Compare core content arrays (should be identical)
    assert non_streaming_data['modules'] == streaming_data['modules']
    assert non_streaming_data['classes'] == streaming_data['classes']
    assert non_streaming_data['functions'] == streaming_data['functions']
    assert non_streaming_data['dependencies'] == streaming_data['dependencies']


def test_compression_with_streaming(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify compressed streaming output can be decompressed and loaded."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate compressed streaming output
    compressed_path = tmp_path / "compressed_streaming.json.gz"
    generator.save_json(
        compressed_path,
        sample_analysis,
        sample_statistics,
        streaming=True,
        compress=True
    )

    # Verify file was created and is compressed
    assert compressed_path.exists()
    assert compressed_path.suffix == '.gz'

    # Load and decompress
    with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
        compressed_data = json.load(f)

    # Verify essential structure (streaming merges statistics into metadata)
    assert 'metadata' in compressed_data
    assert 'modules' in compressed_data

    # Verify content matches expected
    assert compressed_data['metadata']['project_name'] == "TestProject"
    # In streaming mode, statistics are in metadata
    assert compressed_data['metadata']['total_files'] == 1


def test_compression_produces_equivalent_output(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify compressed and uncompressed outputs contain the same data."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate uncompressed output
    uncompressed_path = tmp_path / "uncompressed.json"
    generator.save_json(
        uncompressed_path,
        sample_analysis,
        sample_statistics,
        streaming=True,
        compress=False
    )

    # Generate compressed output
    compressed_path = tmp_path / "compressed.json.gz"
    generator.save_json(
        compressed_path,
        sample_analysis,
        sample_statistics,
        streaming=True,
        compress=True
    )

    # Load both outputs
    with open(uncompressed_path, 'r', encoding='utf-8') as f:
        uncompressed_data = json.load(f)

    with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
        compressed_data = json.load(f)

    # Compare core content (ignoring timestamp differences)
    # Both use streaming mode so structure is the same
    assert uncompressed_data['modules'] == compressed_data['modules']
    assert uncompressed_data['classes'] == compressed_data['classes']
    assert uncompressed_data['functions'] == compressed_data['functions']
    assert uncompressed_data['dependencies'] == compressed_data['dependencies']

    # Verify metadata keys match (except generated_at which may differ slightly)
    for key in ['project_name', 'version', 'languages', 'schema_version']:
        assert uncompressed_data['metadata'][key] == compressed_data['metadata'][key]


def test_non_streaming_with_compression(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify non-streaming mode respects compress flag."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Non-streaming doesn't support compression (uses json.dump)
    # This test verifies it doesn't break when compress=True is passed
    output_path = tmp_path / "non_streaming_with_compress.json"
    generator.save_json(
        output_path,
        sample_analysis,
        sample_statistics,
        streaming=False,
        compress=True  # Should be ignored for non-streaming
    )

    # Should create uncompressed file (non-streaming ignores compress flag)
    assert output_path.exists()
    assert output_path.suffix == '.json'  # Not .gz

    # Should be readable as regular JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert 'metadata' in data
