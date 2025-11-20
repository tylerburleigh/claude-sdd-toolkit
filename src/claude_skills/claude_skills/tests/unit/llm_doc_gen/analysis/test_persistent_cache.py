"""Unit tests for PersistentCache in llm_doc_gen.analysis.optimization.cache.

Tests cover cache hit/miss scenarios, file change invalidation, dependency tracking,
and cascade invalidation.
"""

import time
import tempfile
from pathlib import Path

import pytest

from claude_skills.llm_doc_gen.analysis.optimization.cache import PersistentCache
from claude_skills.llm_doc_gen.analysis.parsers.base import ParseResult, ParsedFunction, ParsedClass, ParsedModule, Language


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    return cache_dir


@pytest.fixture
def cache(temp_cache_dir):
    """Create PersistentCache instance with temporary directory."""
    return PersistentCache(temp_cache_dir)


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory with test files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    return project_dir


# ============================================================================
# Cache Initialization Tests
# ============================================================================


class TestCacheInitialization:
    """Test cache initialization and schema creation."""

    def test_init_creates_directory(self, temp_cache_dir):
        """Test that cache directory is created on init."""
        cache = PersistentCache(temp_cache_dir)
        assert temp_cache_dir.exists()
        assert temp_cache_dir.is_dir()

    def test_init_creates_database(self, temp_cache_dir):
        """Test that database file is created."""
        cache = PersistentCache(temp_cache_dir)
        db_path = temp_cache_dir / "parse_cache.db"
        assert db_path.exists()
        assert db_path.is_file()

    def test_init_creates_schema(self, cache):
        """Test that database schema is created."""
        stats = cache.get_stats()
        assert 'files_cached' in stats
        assert 'results_cached' in stats
        assert 'dependencies_tracked' in stats


# ============================================================================
# Cache Hit/Miss Tests
# ============================================================================


class TestCacheHitMiss:
    """Test cache hit and miss scenarios."""

    def test_cache_miss_on_first_access(self, cache, temp_project_dir):
        """Test that first access results in cache miss."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        result = cache.get_cached_result(test_file)
        assert result is None

    def test_cache_hit_after_store(self, cache, temp_project_dir):
        """Test that stored result can be retrieved (cache hit)."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        # Create and store result
        parse_result = ParseResult(
            functions=[ParsedFunction(
                name="test",
                file=str(test_file),
                line=1,
                language=Language.PYTHON
            )]
        )
        cache.store_result(test_file, parse_result)

        # Retrieve from cache
        cached_result = cache.get_cached_result(test_file)
        assert cached_result is not None
        assert len(cached_result.functions) == 1
        assert cached_result.functions[0].name == "test"

    def test_cache_miss_on_nonexistent_file(self, cache, temp_project_dir):
        """Test that nonexistent file returns None."""
        nonexistent = temp_project_dir / "nonexistent.py"
        result = cache.get_cached_result(nonexistent)
        assert result is None

    def test_multiple_cache_hits(self, cache, temp_project_dir):
        """Test multiple cache hits return same result."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        parse_result = ParseResult(functions=[ParsedFunction(
            name="test", file=str(test_file), line=1, language=Language.PYTHON
        )])
        cache.store_result(test_file, parse_result)

        # Multiple retrievals should all hit cache
        for _ in range(5):
            cached = cache.get_cached_result(test_file)
            assert cached is not None
            assert len(cached.functions) == 1


# ============================================================================
# File Change Invalidation Tests
# ============================================================================


class TestFileChangeInvalidation:
    """Test cache invalidation on file changes."""

    def test_cache_miss_after_content_change(self, cache, temp_project_dir):
        """Test that cache miss occurs after file content changes."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        # Store initial result
        parse_result = ParseResult(functions=[ParsedFunction(
            name="test", file=str(test_file), line=1, language=Language.PYTHON
        )])
        cache.store_result(test_file, parse_result)

        # Verify cache hit
        assert cache.get_cached_result(test_file) is not None

        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        test_file.write_text("def test_modified(): pass")

        # Should be cache miss now
        result = cache.get_cached_result(test_file)
        assert result is None

    def test_cache_hit_with_unchanged_content(self, cache, temp_project_dir):
        """Test that cache hit occurs when content hasn't changed."""
        test_file = temp_project_dir / "test.py"
        content = "def test(): pass"
        test_file.write_text(content)

        # Store result
        parse_result = ParseResult(functions=[ParsedFunction(
            name="test", file=str(test_file), line=1, language=Language.PYTHON
        )])
        cache.store_result(test_file, parse_result)

        # Rewrite same content (changes mtime but not hash)
        time.sleep(0.01)
        test_file.write_text(content)

        # Should still be cache hit (content-addressed)
        result = cache.get_cached_result(test_file)
        assert result is not None

    def test_manual_invalidation(self, cache, temp_project_dir):
        """Test manual cache invalidation."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        parse_result = ParseResult(functions=[ParsedFunction(
            name="test", file=str(test_file), line=1, language=Language.PYTHON
        )])
        cache.store_result(test_file, parse_result)

        # Verify cached
        assert cache.get_cached_result(test_file) is not None

        # Invalidate
        cache.invalidate_file(test_file, cascade=False)

        # Should be cache miss
        assert cache.get_cached_result(test_file) is None


# ============================================================================
# Dependency Tracking Tests
# ============================================================================


class TestDependencyTracking:
    """Test dependency tracking and retrieval."""

    def test_store_dependencies(self, cache, temp_project_dir):
        """Test that dependencies are stored."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"
        file_c = temp_project_dir / "c.py"

        for f in [file_a, file_b, file_c]:
            f.write_text("pass")

        # Store result with dependencies
        result = ParseResult(
            dependencies={str(file_a): [str(file_b), str(file_c)]}
        )
        cache.store_result(file_a, result)

        # Check dependencies were tracked
        stats = cache.get_stats()
        assert stats['dependencies_tracked'] == 2

    def test_get_dependencies(self, cache, temp_project_dir):
        """Test retrieving dependencies for a file."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"

        for f in [file_a, file_b]:
            f.write_text("pass")

        result = ParseResult(dependencies={str(file_a): [str(file_b)]})
        cache.store_result(file_a, result)

        deps = cache.get_dependencies(file_a)
        assert len(deps) == 1
        assert str(file_b) in deps

    def test_get_dependents(self, cache, temp_project_dir):
        """Test retrieving files that depend on a given file."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"
        file_c = temp_project_dir / "c.py"

        for f in [file_a, file_b, file_c]:
            f.write_text("pass")

        # a depends on c, b depends on c
        result_a = ParseResult(dependencies={str(file_a): [str(file_c)]})
        result_b = ParseResult(dependencies={str(file_b): [str(file_c)]})

        cache.store_result(file_a, result_a)
        cache.store_result(file_b, result_b)

        # Get files that depend on c
        dependents = cache.get_dependents(file_c)
        assert len(dependents) == 2
        assert str(file_a) in dependents
        assert str(file_b) in dependents


# ============================================================================
# Cascade Invalidation Tests
# ============================================================================


class TestCascadeInvalidation:
    """Test cascade invalidation of dependent files."""

    def test_cascade_invalidation_enabled(self, cache, temp_project_dir):
        """Test that cascade invalidation works when enabled."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"
        file_c = temp_project_dir / "c.py"

        for f in [file_a, file_b, file_c]:
            f.write_text("pass")

        # a depends on b and c, b depends on c
        result_a = ParseResult(dependencies={str(file_a): [str(file_b), str(file_c)]})
        result_b = ParseResult(dependencies={str(file_b): [str(file_c)]})
        result_c = ParseResult(dependencies={str(file_c): []})

        cache.store_result(file_a, result_a)
        cache.store_result(file_b, result_b)
        cache.store_result(file_c, result_c)

        # All should be cached
        assert cache.get_stats()['files_cached'] == 3

        # Invalidate c with cascade
        cache.invalidate_file(file_c, cascade=True)

        # All should be invalidated (a and b depend on c)
        stats = cache.get_stats()
        assert stats['files_cached'] == 0
        assert stats['dependencies_tracked'] == 0

    def test_cascade_invalidation_disabled(self, cache, temp_project_dir):
        """Test that cascade invalidation can be disabled."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"

        for f in [file_a, file_b]:
            f.write_text("pass")

        result_a = ParseResult(dependencies={str(file_a): [str(file_b)]})
        result_b = ParseResult(dependencies={str(file_b): []})

        cache.store_result(file_a, result_a)
        cache.store_result(file_b, result_b)

        # Invalidate b without cascade
        cache.invalidate_file(file_b, cascade=False)

        # Only b should be invalidated
        assert cache.get_cached_result(file_a) is not None
        assert cache.get_cached_result(file_b) is None


# ============================================================================
# Cache Statistics Tests
# ============================================================================


class TestCacheStatistics:
    """Test cache statistics and metadata."""

    def test_get_stats_empty_cache(self, cache):
        """Test stats for empty cache."""
        stats = cache.get_stats()
        assert stats['files_cached'] == 0
        assert stats['results_cached'] == 0
        assert stats['total_size_bytes'] == 0
        assert stats['dependencies_tracked'] == 0

    def test_get_stats_with_data(self, cache, temp_project_dir):
        """Test stats with cached data."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"

        for f in [file_a, file_b]:
            f.write_text("def test(): pass")

        result = ParseResult(
            functions=[ParsedFunction(name="test", file=str(file_a), line=1, language=Language.PYTHON)],
            dependencies={str(file_a): [str(file_b)]}
        )
        cache.store_result(file_a, result)

        stats = cache.get_stats()
        assert stats['files_cached'] == 1
        assert stats['results_cached'] == 1
        assert stats['total_size_bytes'] > 0
        assert stats['dependencies_tracked'] == 1

    def test_clear_cache(self, cache, temp_project_dir):
        """Test clearing all cache data."""
        test_file = temp_project_dir / "test.py"
        test_file.write_text("def test(): pass")

        result = ParseResult(functions=[ParsedFunction(
            name="test", file=str(test_file), line=1, language=Language.PYTHON
        )])
        cache.store_result(test_file, result)

        # Verify data exists
        assert cache.get_stats()['files_cached'] > 0

        # Clear cache
        cache.clear()

        # Verify empty
        stats = cache.get_stats()
        assert stats['files_cached'] == 0
        assert stats['results_cached'] == 0
        assert stats['dependencies_tracked'] == 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_store_nonexistent_file(self, cache, temp_project_dir):
        """Test storing result for nonexistent file (should do nothing)."""
        nonexistent = temp_project_dir / "nonexistent.py"
        result = ParseResult()
        cache.store_result(nonexistent, result)  # Should not raise error

        stats = cache.get_stats()
        assert stats['files_cached'] == 0

    def test_invalidate_nonexistent_file(self, cache, temp_project_dir):
        """Test invalidating nonexistent file (should do nothing)."""
        nonexistent = temp_project_dir / "nonexistent.py"
        cache.invalidate_file(nonexistent)  # Should not raise error

    def test_get_dependencies_uncached_file(self, cache, temp_project_dir):
        """Test getting dependencies for uncached file returns empty list."""
        test_file = temp_project_dir / "test.py"
        deps = cache.get_dependencies(test_file)
        assert deps == []

    def test_get_dependents_uncached_file(self, cache, temp_project_dir):
        """Test getting dependents for uncached file returns empty list."""
        test_file = temp_project_dir / "test.py"
        dependents = cache.get_dependents(test_file)
        assert dependents == []

    def test_update_dependencies_on_restore(self, cache, temp_project_dir):
        """Test that dependencies are updated when file is re-stored."""
        file_a = temp_project_dir / "a.py"
        file_b = temp_project_dir / "b.py"
        file_c = temp_project_dir / "c.py"

        for f in [file_a, file_b, file_c]:
            f.write_text("pass")

        # Store with initial dependencies
        result1 = ParseResult(dependencies={str(file_a): [str(file_b)]})
        cache.store_result(file_a, result1)

        assert cache.get_dependencies(file_a) == [str(file_b)]

        # Update dependencies
        result2 = ParseResult(dependencies={str(file_a): [str(file_c)]})
        cache.store_result(file_a, result2)

        # Dependencies should be updated
        deps = cache.get_dependencies(file_a)
        assert len(deps) == 1
        assert str(file_c) in deps
        assert str(file_b) not in deps
