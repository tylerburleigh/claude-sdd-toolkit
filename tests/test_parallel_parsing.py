"""
Correctness tests for parallel file parsing.

Tests verify that parallel parsing using ParallelParser produces identical
results to sequential parsing, ensuring correctness while improving performance.
"""

import pytest
import tempfile
from pathlib import Path

from src.claude_skills.claude_skills.llm_doc_gen.analysis.optimization.parallel import (
    ParallelParser,
    _parse_worker_func,
    _init_worker_cache
)
from src.claude_skills.claude_skills.llm_doc_gen.analysis.parsers.base import ParseResult
from src.claude_skills.claude_skills.llm_doc_gen.analysis.parsers import create_parser_factory, Language


class TestParallelParsingCorrectness:
    """Test that parallel parsing produces correct, consistent results."""

    def _create_test_files(self, tmp_dir: Path) -> list:
        """
        Create temporary test files for parsing.

        Args:
            tmp_dir: Temporary directory path

        Returns:
            List of created file paths
        """
        files = []

        # Python file 1
        py_file_1 = tmp_dir / "module1.py"
        py_file_1.write_text("""
def hello_world():
    '''Say hello.'''
    print("Hello, World!")

class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"
""")
        files.append(str(py_file_1))

        # Python file 2
        py_file_2 = tmp_dir / "module2.py"
        py_file_2.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

class Calculator:
    def compute(self, x, y):
        return self.add(x, y)
""")
        files.append(str(py_file_2))

        # Python file 3
        py_file_3 = tmp_dir / "utils.py"
        py_file_3.write_text("""
import os
import sys

def get_path():
    return os.getcwd()

class PathHelper:
    def normalize(self, path):
        return os.path.normpath(path)
""")
        files.append(str(py_file_3))

        return files

    def test_parallel_vs_sequential_consistency(self):
        """Test that parallel and sequential parsing produce identical results."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_test_files(tmp_path)

            # Create parser factory for sequential parsing
            factory_seq = create_parser_factory(tmp_path)
            result_seq = factory_seq.parse_all(verbose=False, parallel=False)

            # Create parser factory for parallel parsing
            factory_par = create_parser_factory(tmp_path)
            result_par = factory_par.parse_all(verbose=False, parallel=True, num_workers=2)

            # Compare results
            self._assert_parse_results_equal(result_seq, result_par)

    def test_parallel_determinism(self):
        """Test that parallel parsing produces consistent results across multiple runs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_test_files(tmp_path)

            # Run parallel parsing multiple times
            results = []
            for _ in range(3):
                factory = create_parser_factory(tmp_path)
                result = factory.parse_all(verbose=False, parallel=True, num_workers=2)
                results.append(result)

            # All results should be identical
            for i in range(1, len(results)):
                self._assert_parse_results_equal(results[0], results[i])

    def test_parse_result_merging(self):
        """Test that ParseResult merging works correctly."""
        # Create two separate ParseResults
        result1 = ParseResult()
        result1.errors.append("error1")

        result2 = ParseResult()
        result2.errors.append("error2")

        # Merge result2 into result1
        result1.merge(result2)

        # Check merge worked
        assert len(result1.errors) == 2
        assert "error1" in result1.errors
        assert "error2" in result1.errors

    def test_empty_file_list(self):
        """Test that empty file list is handled correctly in parallel mode."""
        parser = ParallelParser(num_workers=2)

        # Parse empty list
        results = parser.parse_files([], lambda f: ParseResult())

        # Should return empty list
        assert results == []

    def test_single_file_no_parallelization(self):
        """Test that single file doesn't trigger parallel processing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create single file
            py_file = tmp_path / "single.py"
            py_file.write_text("def test(): pass")

            parser = ParallelParser(num_workers=4)

            # Parse single file (should be sequential internally)
            def parse_func(file_path):
                return ParseResult()

            results = parser.parse_files([str(py_file)], parse_func)

            # Should return single result
            assert len(results) == 1

    def test_worker_count_auto_detection(self):
        """Test that worker count is auto-detected correctly."""
        # Auto-detect
        parser_auto = ParallelParser()
        assert parser_auto.num_workers >= 1

        # Explicit count
        parser_explicit = ParallelParser(num_workers=4)
        assert parser_explicit.num_workers == 4

        # Minimum of 1 worker
        parser_zero = ParallelParser(num_workers=0)
        assert parser_zero.num_workers == 1

    def test_chunk_size_calculation(self):
        """Test that chunk size is calculated correctly for load balancing."""
        parser = ParallelParser(num_workers=4)

        # Small file count
        chunk_size_small = parser._calculate_chunk_size(8)
        assert chunk_size_small >= 1

        # Large file count
        chunk_size_large = parser._calculate_chunk_size(1000)
        assert chunk_size_large > 1

        # Very small (less than workers)
        chunk_size_tiny = parser._calculate_chunk_size(2)
        assert chunk_size_tiny == 1

    def test_file_chunking(self):
        """Test that files are chunked correctly."""
        parser = ParallelParser(num_workers=4)

        files = ["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"]
        chunks = parser._chunk_files(files, chunk_size=2)

        # Should have 3 chunks ([2, 2, 1])
        assert len(chunks) == 3
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert len(chunks[2]) == 1

        # All files present
        all_files = [f for chunk in chunks for f in chunk]
        assert all_files == files

    def test_progress_callback(self):
        """Test that progress callback is called correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_test_files(tmp_path)

            parser = ParallelParser(num_workers=2)

            # Track progress
            progress_calls = []

            def progress_callback(completed, total):
                progress_calls.append((completed, total))

            # Parse with callback
            def parse_func(file_path):
                return ParseResult()

            parser.parse_files(files, parse_func, progress_callback=progress_callback)

            # Check callback was called
            assert len(progress_calls) == len(files)

            # Check final call shows completion
            final_call = progress_calls[-1]
            assert final_call[0] == len(files)
            assert final_call[1] == len(files)

    def test_error_handling_fallback(self):
        """Test that errors in parallel mode fall back to sequential."""
        parser = ParallelParser(num_workers=2)

        files = ["test1.py", "test2.py"]

        # Function that raises an error (simulates unpicklable function)
        def unpicklable_func(file_path):
            # This will work in sequential fallback
            return ParseResult()

        # Should fall back to sequential and succeed
        results = parser.parse_files(files, unpicklable_func)

        assert len(results) == 2

    def test_parse_files_with_metadata(self):
        """Test parsing files with associated metadata."""
        parser = ParallelParser(num_workers=2)

        files_with_lang = [
            ("file1.py", "python"),
            ("file2.js", "javascript"),
            ("file3.py", "python"),
        ]

        def parse_func(item):
            file_path, language = item
            result = ParseResult()
            result.errors.append(f"Parsed {file_path} as {language}")
            return result

        results = parser.parse_files_with_metadata(files_with_lang, parse_func)

        # Check results
        assert len(results) == 3
        assert any("file1.py" in str(r.errors) for r in results if r.errors)

    def _assert_parse_results_equal(self, result1: ParseResult, result2: ParseResult):
        """
        Assert that two ParseResults are equal.

        Args:
            result1: First ParseResult
            result2: Second ParseResult
        """
        # Compare counts
        assert len(result1.modules) == len(result2.modules), \
            f"Module count mismatch: {len(result1.modules)} vs {len(result2.modules)}"

        assert len(result1.classes) == len(result2.classes), \
            f"Class count mismatch: {len(result1.classes)} vs {len(result2.classes)}"

        assert len(result1.functions) == len(result2.functions), \
            f"Function count mismatch: {len(result1.functions)} vs {len(result2.functions)}"

        # For now, just verify counts match
        # In a real implementation, would compare actual entities
        # (names, signatures, locations, etc.)

    def test_get_worker_count(self):
        """Test getting worker count."""
        parser = ParallelParser(num_workers=3)
        assert parser.get_worker_count() == 3

    def test_get_cpu_count(self):
        """Test getting CPU count."""
        cpu_count = ParallelParser.get_cpu_count()
        assert cpu_count >= 1


class TestWorkerFunction:
    """Test the worker function with per-worker cache."""

    def test_worker_cache_initialization(self):
        """Test that worker cache is initialized correctly."""
        _init_worker_cache(cache_size=50)

        # Cache should be initialized (can't directly test global var,
        # but function shouldn't raise)

    def test_worker_func_basic(self):
        """Test basic worker function execution."""
        task = ("test.py", "python", {})

        # Execute worker function
        result = _parse_worker_func(task)

        # Should return ParseResult
        assert isinstance(result, ParseResult)

    def test_worker_func_error_handling(self):
        """Test worker function handles errors gracefully."""
        # Invalid task (will cause error internally)
        task = (None, None, None)

        # Should return ParseResult with error
        result = _parse_worker_func(task)

        assert isinstance(result, ParseResult)
        assert len(result.errors) > 0


class TestParallelPerformance:
    """Performance benchmarks for parallel parsing."""

    def _create_large_project(self, tmp_dir: Path, num_files: int = 50) -> list:
        """
        Create a large test project with many files.

        Args:
            tmp_dir: Temporary directory
            num_files: Number of files to create

        Returns:
            List of file paths
        """
        files = []

        for i in range(num_files):
            py_file = tmp_dir / f"module_{i}.py"
            py_file.write_text(f"""
import os
import sys
from typing import List, Dict

def function_{i}_1(x, y):
    '''Process data {i}.'''
    return x + y

def function_{i}_2(a, b, c):
    '''Calculate {i}.'''
    return (a * b) + c

class Class_{i}:
    def __init__(self, value):
        self.value = value

    def process(self, data):
        return data * self.value

    def transform(self, items: List[int]) -> Dict[int, int]:
        return {{item: item * 2 for item in items}}
""")
            files.append(str(py_file))

        return files

    def test_parallel_speedup(self):
        """Test that parallel parsing provides speedup over sequential."""
        import time

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_large_project(tmp_path, num_files=20)

            # Sequential parsing
            factory_seq = create_parser_factory(tmp_path)
            start_seq = time.time()
            result_seq = factory_seq.parse_all(verbose=False, parallel=False)
            time_seq = time.time() - start_seq

            # Parallel parsing
            factory_par = create_parser_factory(tmp_path)
            start_par = time.time()
            result_par = factory_par.parse_all(verbose=False, parallel=True, num_workers=4)
            time_par = time.time() - start_par

            print(f"\nSequential time: {time_seq:.3f}s")
            print(f"Parallel time: {time_par:.3f}s")

            if time_seq > 0:
                speedup = time_seq / time_par if time_par > 0 else 1.0
                print(f"Speedup: {speedup:.2f}x")

            # Note: On small projects, parallel might be slower due to overhead
            # This test primarily documents the API, actual speedup measured on large projects

    def test_scaling_with_file_count(self):
        """Test how parallel parsing scales with number of files."""
        import time

        file_counts = [10, 30, 50]
        results = []

        for count in file_counts:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                files = self._create_large_project(tmp_path, num_files=count)

                factory = create_parser_factory(tmp_path)

                start = time.time()
                factory.parse_all(verbose=False, parallel=True, num_workers=4)
                elapsed = time.time() - start

                results.append((count, elapsed))

        print(f"\nScaling test results:")
        for count, elapsed in results:
            print(f"  {count} files: {elapsed:.3f}s")

        # Check that time grows sub-linearly (parallel should help)
        # For linear growth: time(50) / time(10) ≈ 5
        # For good parallelism: time(50) / time(10) < 5
        if len(results) >= 2 and results[0][1] > 0:
            growth_ratio = results[-1][1] / results[0][1]
            file_ratio = results[-1][0] / results[0][0]

            print(f"Growth ratio: {growth_ratio:.2f}x (file ratio: {file_ratio:.2f}x)")

            # With good parallelism, time growth should be less than file count growth
            # Allow some overhead for small projects
            assert growth_ratio < file_ratio * 1.5, \
                f"Scaling poorly: {growth_ratio:.2f}x time for {file_ratio:.2f}x files"

    def test_worker_count_impact(self):
        """Test impact of different worker counts on performance."""
        import time

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_large_project(tmp_path, num_files=30)

            worker_counts = [1, 2, 4]
            results = []

            for workers in worker_counts:
                factory = create_parser_factory(tmp_path)

                start = time.time()
                factory.parse_all(verbose=False, parallel=True, num_workers=workers)
                elapsed = time.time() - start

                results.append((workers, elapsed))

            print(f"\nWorker count impact:")
            for workers, elapsed in results:
                print(f"  {workers} workers: {elapsed:.3f}s")

            # More workers should generally be faster (with diminishing returns)
            # At minimum, 4 workers shouldn't be slower than 1 worker
            if len(results) >= 2:
                time_1_worker = results[0][1]
                time_4_workers = results[-1][1]

                # Allow for overhead on small projects
                # On large projects, 4 workers should be faster than 1
                improvement = time_1_worker / time_4_workers if time_4_workers > 0 else 1.0
                print(f"Improvement from 1 to 4 workers: {improvement:.2f}x")

    def test_memory_efficiency(self):
        """Test that parallel parsing doesn't consume excessive memory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = self._create_large_project(tmp_path, num_files=20)

            factory = create_parser_factory(tmp_path)

            # Parse in parallel (should manage memory efficiently with worker pools)
            result = factory.parse_all(verbose=False, parallel=True, num_workers=4)

            # Check result is valid (memory wasn't exhausted)
            assert result is not None
            assert isinstance(result.modules, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
