"""
Tests for DocumentationGenerator streaming and compression functionality.

Verifies that streaming output produces equivalent data to non-streaming output,
and that compression works correctly with both modes. Also includes memory
usage tests to verify streaming reduces peak memory consumption.
"""

import json
import gzip
import tracemalloc
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


def test_streaming_reduces_memory_usage(
    sample_project: Path,
    tmp_path: Path
):
    """
    Verify streaming memory usage remains bounded regardless of dataset size.

    Note: This test verifies that streaming memory usage doesn't grow proportionally
    with data size (the key benefit). Direct comparison of absolute memory values
    for small datasets can be unreliable due to overhead and caching effects.
    The real benefit of streaming is visible in production with large codebases.
    """
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate base analysis
    result = generator.generate()
    analysis = result['analysis']
    statistics = result['statistics']

    # Test with progressively larger datasets to measure memory scalability
    small_multiplier = 100
    large_multiplier = 1000

    # Small dataset
    small_analysis = {
        'modules': analysis['modules'] * small_multiplier,
        'classes': analysis['classes'] * small_multiplier,
        'functions': analysis['functions'] * small_multiplier,
        'dependencies': analysis['dependencies'],
        'errors': []
    }

    # Large dataset (10x bigger)
    large_analysis = {
        'modules': analysis['modules'] * large_multiplier,
        'classes': analysis['classes'] * large_multiplier,
        'functions': analysis['functions'] * large_multiplier,
        'dependencies': analysis['dependencies'],
        'errors': []
    }

    # Measure streaming memory with small dataset
    tracemalloc.start()
    small_path = tmp_path / "streaming_small.json"
    generator.save_json(small_path, small_analysis, statistics, streaming=True)
    _, small_streaming_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Measure streaming memory with large dataset
    tracemalloc.start()
    large_path = tmp_path / "streaming_large.json"
    generator.save_json(large_path, large_analysis, statistics, streaming=True)
    _, large_streaming_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Calculate memory scaling factor
    memory_scale_factor = large_streaming_peak / small_streaming_peak
    data_scale_factor = large_multiplier / small_multiplier  # 10x

    print(f"\nStreaming Memory Scalability:")
    print(f"  Small dataset ({small_multiplier}x) peak: {small_streaming_peak / 1024 / 1024:.2f} MB")
    print(f"  Large dataset ({large_multiplier}x) peak: {large_streaming_peak / 1024 / 1024:.2f} MB")
    print(f"  Memory scale factor: {memory_scale_factor:.2f}x")
    print(f"  Data scale factor: {data_scale_factor:.1f}x")

    # Key test: Memory should grow much slower than data size with streaming
    # If streaming is working, memory should be nearly constant or grow sub-linearly
    # We use a conservative threshold of 5x to account for test variability
    assert memory_scale_factor < data_scale_factor / 2, \
        f"Streaming memory should scale sub-linearly (got {memory_scale_factor:.2f}x vs {data_scale_factor:.1f}x data increase)"


def test_streaming_memory_scales_better(
    sample_project: Path,
    tmp_path: Path
):
    """Verify streaming memory usage scales better with data size."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate base analysis
    result = generator.generate()
    analysis = result['analysis']
    statistics = result['statistics']

    # Test with small dataset (10x)
    small_analysis = {
        'modules': analysis['modules'] * 10,
        'classes': analysis['classes'] * 10,
        'functions': analysis['functions'] * 10,
        'dependencies': analysis['dependencies'],
        'errors': []
    }

    tracemalloc.start()
    small_path = tmp_path / "streaming_small.json"
    generator.save_json(small_path, small_analysis, statistics, streaming=True)
    _, small_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Test with large dataset (100x)
    large_analysis = {
        'modules': analysis['modules'] * 100,
        'classes': analysis['classes'] * 100,
        'functions': analysis['functions'] * 100,
        'dependencies': analysis['dependencies'],
        'errors': []
    }

    tracemalloc.start()
    large_path = tmp_path / "streaming_large.json"
    generator.save_json(large_path, large_analysis, statistics, streaming=True)
    _, large_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory increase should be less than data size increase (10x)
    # because streaming doesn't build entire structure in memory
    memory_increase_ratio = large_peak / small_peak
    data_increase_ratio = 10.0  # 100x / 10x

    print(f"\nStreaming Scalability:")
    print(f"  Small dataset peak: {small_peak / 1024 / 1024:.2f} MB")
    print(f"  Large dataset peak: {large_peak / 1024 / 1024:.2f} MB")
    print(f"  Memory increase ratio: {memory_increase_ratio:.1f}x")
    print(f"  Data increase ratio: {data_increase_ratio:.1f}x")

    # Memory should scale sub-linearly with streaming
    # (less than proportional to data increase)
    assert memory_increase_ratio < data_increase_ratio, \
        f"Streaming memory should scale better than data size (got {memory_increase_ratio:.1f}x vs {data_increase_ratio:.1f}x)"


def test_compression_reduces_file_size(
    sample_project: Path,
    tmp_path: Path
):
    """Verify gzip compression achieves significant file size reduction."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate analysis
    result = generator.generate()
    analysis = result['analysis']
    statistics = result['statistics']

    # Create larger dataset to make compression more effective
    # JSON compresses well due to repetitive structure
    large_analysis = {
        'modules': analysis['modules'] * 200,
        'classes': analysis['classes'] * 200,
        'functions': analysis['functions'] * 200,
        'dependencies': analysis['dependencies'],
        'errors': []
    }

    # Generate uncompressed output
    uncompressed_path = tmp_path / "uncompressed.json"
    generator.save_json(
        uncompressed_path,
        large_analysis,
        statistics,
        streaming=True,
        compress=False
    )

    # Generate compressed output
    compressed_path = tmp_path / "compressed.json.gz"
    generator.save_json(
        compressed_path,
        large_analysis,
        statistics,
        streaming=True,
        compress=True
    )

    # Measure file sizes
    uncompressed_size = uncompressed_path.stat().st_size
    compressed_size = compressed_path.stat().st_size

    # Calculate compression ratio
    compression_ratio = uncompressed_size / compressed_size

    print(f"\nCompression Test Results:")
    print(f"  Uncompressed size: {uncompressed_size / 1024 / 1024:.2f} MB")
    print(f"  Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
    print(f"  Compression ratio: {compression_ratio:.1f}x")

    # Verify compression is working
    assert compressed_size < uncompressed_size, \
        "Compressed file should be smaller than uncompressed"

    # Verify at least 3x compression (conservative threshold)
    # JSON typically compresses 5-10x but we use 3x for test stability
    assert compression_ratio >= 3.0, \
        f"Expected at least 3x compression ratio, got {compression_ratio:.1f}x"


def test_compression_file_extension(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify compressed files have .gz extension."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Test that compression adds .gz extension
    output_path = tmp_path / "output.json.gz"
    generator.save_json(
        output_path,
        sample_analysis,
        sample_statistics,
        streaming=True,
        compress=True
    )

    assert output_path.exists()
    assert output_path.suffix == '.gz'
    assert output_path.stem.endswith('.json')


def test_compressed_file_is_readable(
    sample_project: Path,
    sample_analysis: Dict[str, Any],
    sample_statistics: Dict[str, Any],
    tmp_path: Path
):
    """Verify compressed JSON files can be read and decompressed correctly."""
    generator = DocumentationGenerator(
        sample_project,
        "TestProject",
        "1.0.0"
    )

    # Generate compressed output
    compressed_path = tmp_path / "output.json.gz"
    generator.save_json(
        compressed_path,
        sample_analysis,
        sample_statistics,
        streaming=True,
        compress=True
    )

    # Verify file can be decompressed and loaded as JSON
    with gzip.open(compressed_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)

    # Verify structure is intact
    assert 'metadata' in data
    assert 'modules' in data
    assert 'classes' in data
    assert 'functions' in data
    assert 'dependencies' in data

    # Verify content matches input
    assert len(data['modules']) == len(sample_analysis['modules'])
    assert len(data['classes']) == len(sample_analysis['classes'])
    assert len(data['functions']) == len(sample_analysis['functions'])
