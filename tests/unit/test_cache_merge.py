"""
Unit tests for CacheManager.merge_results() functionality.

Tests the merge logic for combining cached results with fresh results
for incremental documentation generation and review operations.
"""

import pytest
from claude_skills.common.cache import CacheManager


class TestCacheMergeResults:
    """Tests for CacheManager.merge_results static method."""

    def test_merge_all_unchanged(self):
        """Merge with all files unchanged should return cached results."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50},
            'src/config.py': {'functions': ['load_config'], 'lines': 30}
        }
        fresh = {}
        changed_files = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # All cached results should be preserved
        assert result == cached
        assert len(result) == 3

    def test_merge_all_changed(self):
        """Merge with all files changed should return fresh results."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50}
        }
        fresh = {
            'src/main.py': {'functions': ['main', 'init'], 'lines': 120},
            'src/utils.py': {'functions': ['helper', 'format'], 'lines': 75}
        }
        changed_files = {'src/main.py', 'src/utils.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Fresh results should override cached
        assert result == fresh
        assert result['src/main.py']['lines'] == 120
        assert result['src/utils.py']['lines'] == 75

    def test_merge_mixed_scenario(self):
        """Merge with some changed and some unchanged files."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50},
            'src/config.py': {'functions': ['load_config'], 'lines': 30}
        }
        fresh = {
            'src/main.py': {'functions': ['main', 'init'], 'lines': 120}
        }
        changed_files = {'src/main.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Should have 3 files total
        assert len(result) == 3

        # Changed file uses fresh version
        assert result['src/main.py'] == fresh['src/main.py']
        assert result['src/main.py']['lines'] == 120

        # Unchanged files use cached versions
        assert result['src/utils.py'] == cached['src/utils.py']
        assert result['src/config.py'] == cached['src/config.py']

    def test_merge_new_files_added(self):
        """Merge with new files added (not in cache)."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50}
        }
        fresh = {
            'src/new_feature.py': {'functions': ['feature_func'], 'lines': 80}
        }
        changed_files = {'src/new_feature.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Should have cached + new file
        assert len(result) == 3
        assert 'src/main.py' in result
        assert 'src/utils.py' in result
        assert 'src/new_feature.py' in result
        assert result['src/new_feature.py'] == fresh['src/new_feature.py']

    def test_merge_files_deleted(self):
        """Merge with files deleted (in cache, marked as changed, not in fresh)."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50},
            'src/old.py': {'functions': ['old_func'], 'lines': 30}
        }
        fresh = {}  # old.py was deleted, so no fresh result
        changed_files = {'src/old.py'}  # Marked as changed (deleted)

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Deleted file should be excluded
        assert len(result) == 2
        assert 'src/main.py' in result
        assert 'src/utils.py' in result
        assert 'src/old.py' not in result

    def test_merge_empty_cache(self):
        """Merge with empty cache (first run scenario)."""
        cached = {}
        fresh = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50}
        }
        changed_files = {'src/main.py', 'src/utils.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # All fresh results should be included
        assert result == fresh
        assert len(result) == 2

    def test_merge_empty_fresh(self):
        """Merge with empty fresh results (no changes scenario)."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/utils.py': {'functions': ['helper'], 'lines': 50}
        }
        fresh = {}
        changed_files = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # All cached results preserved
        assert result == cached

    def test_merge_both_empty(self):
        """Merge with both empty (edge case)."""
        cached = {}
        fresh = {}
        changed_files = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Should return empty dict
        assert result == {}

    def test_merge_preserves_data_structure(self):
        """Merge preserves complex nested data structures."""
        cached = {
            'src/main.py': {
                'functions': [
                    {'name': 'main', 'args': ['argc', 'argv'], 'returns': 'int'}
                ],
                'classes': [
                    {'name': 'App', 'methods': ['run', 'stop']}
                ],
                'imports': ['sys', 'os'],
                'metadata': {'author': 'Alice', 'version': '1.0'}
            }
        }
        fresh = {}
        changed_files = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Complex structure should be preserved exactly
        assert result == cached
        assert result['src/main.py']['functions'][0]['name'] == 'main'
        assert result['src/main.py']['classes'][0]['methods'] == ['run', 'stop']

    def test_merge_overwrites_cached_with_fresh(self):
        """Merge correctly overwrites cached version when file changed."""
        cached = {
            'src/api.py': {
                'endpoints': ['/users', '/posts'],
                'version': 'v1',
                'deprecated': False
            }
        }
        fresh = {
            'src/api.py': {
                'endpoints': ['/users', '/posts', '/comments'],
                'version': 'v2',
                'deprecated': False,
                'new_field': 'added'
            }
        }
        changed_files = {'src/api.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Fresh version should completely replace cached
        assert result['src/api.py'] == fresh['src/api.py']
        assert result['src/api.py']['version'] == 'v2'
        assert 'new_field' in result['src/api.py']
        assert len(result['src/api.py']['endpoints']) == 3

    def test_merge_handles_generation_failure(self):
        """Merge handles files marked changed but missing from fresh results."""
        cached = {
            'src/main.py': {'functions': ['main'], 'lines': 100},
            'src/broken.py': {'functions': ['broken'], 'lines': 50},
            'src/utils.py': {'functions': ['helper'], 'lines': 30}
        }
        fresh = {
            # src/broken.py failed to generate, so it's missing
            'src/main.py': {'functions': ['main', 'init'], 'lines': 120}
        }
        changed_files = {'src/main.py', 'src/broken.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # src/main.py should use fresh
        # src/broken.py should be excluded (changed but missing from fresh)
        # src/utils.py should use cached
        assert len(result) == 2
        assert result['src/main.py'] == fresh['src/main.py']
        assert result['src/utils.py'] == cached['src/utils.py']
        assert 'src/broken.py' not in result

    def test_merge_large_result_set(self):
        """Merge handles large numbers of files efficiently."""
        # Create 1000 cached files
        cached = {f'src/file{i}.py': {'lines': i} for i in range(1000)}

        # Modify 10 files
        fresh = {f'src/file{i}.py': {'lines': i * 2} for i in range(0, 10)}
        changed_files = {f'src/file{i}.py' for i in range(0, 10)}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Should have all 1000 files
        assert len(result) == 1000

        # Changed files should use fresh values
        for i in range(0, 10):
            assert result[f'src/file{i}.py']['lines'] == i * 2

        # Unchanged files should use cached values
        for i in range(10, 1000):
            assert result[f'src/file{i}.py']['lines'] == i

    def test_merge_with_file_path_variations(self):
        """Merge handles different file path formats."""
        cached = {
            'src/main.py': {'lines': 100},
            './src/utils.py': {'lines': 50},
            '/abs/path/config.py': {'lines': 30}
        }
        fresh = {
            'src/main.py': {'lines': 120}
        }
        changed_files = {'src/main.py'}

        result = CacheManager.merge_results(cached, fresh, changed_files)

        # Should preserve path formats as-is
        assert 'src/main.py' in result
        assert './src/utils.py' in result
        assert '/abs/path/config.py' in result
        assert result['src/main.py']['lines'] == 120

    def test_merge_idempotence(self):
        """Merge with same inputs should produce same output."""
        cached = {
            'src/main.py': {'lines': 100},
            'src/utils.py': {'lines': 50}
        }
        fresh = {
            'src/main.py': {'lines': 120}
        }
        changed_files = {'src/main.py'}

        result1 = CacheManager.merge_results(cached, fresh, changed_files)
        result2 = CacheManager.merge_results(cached, fresh, changed_files)

        # Results should be identical
        assert result1 == result2

    def test_merge_does_not_modify_inputs(self):
        """Merge does not mutate input dictionaries."""
        cached = {
            'src/main.py': {'lines': 100},
            'src/utils.py': {'lines': 50}
        }
        fresh = {
            'src/main.py': {'lines': 120}
        }
        changed_files = {'src/main.py'}

        # Make copies for comparison
        cached_copy = cached.copy()
        fresh_copy = fresh.copy()
        changed_copy = changed_files.copy()

        CacheManager.merge_results(cached, fresh, changed_files)

        # Inputs should be unchanged
        assert cached == cached_copy
        assert fresh == fresh_copy
        assert changed_files == changed_copy


class TestCacheMergeIntegration:
    """Integration tests for merge_results with compare_file_hashes."""

    def test_merge_with_compare_file_hashes_workflow(self):
        """Test typical workflow: compare hashes → merge results."""
        # Step 1: Previous state
        old_hashes = {
            'src/main.py': 'hash_a',
            'src/utils.py': 'hash_b',
            'src/old.py': 'hash_c'
        }

        # Step 2: Current state
        new_hashes = {
            'src/main.py': 'hash_a_modified',  # Modified
            'src/utils.py': 'hash_b',          # Unchanged
            'src/new.py': 'hash_d'             # Added
        }

        # Step 3: Compare to find changes
        changes = CacheManager.compare_file_hashes(old_hashes, new_hashes)

        # Step 4: Use changed files for merge
        cached_results = {
            'src/main.py': {'docs': 'old version'},
            'src/utils.py': {'docs': 'unchanged'},
            'src/old.py': {'docs': 'deleted file'}
        }

        fresh_results = {
            'src/main.py': {'docs': 'new version'},
            'src/new.py': {'docs': 'new file'}
        }

        # Combine added + modified + removed = changed_files set
        # NOTE: Removed files need to be marked as changed to exclude them from result
        changed_files = set(changes['added'] + changes['modified'] + changes['removed'])

        result = CacheManager.merge_results(cached_results, fresh_results, changed_files)

        # Verify correct merge
        assert result['src/main.py']['docs'] == 'new version'  # Fresh (modified)
        assert result['src/utils.py']['docs'] == 'unchanged'   # Cached (unchanged)
        assert result['src/new.py']['docs'] == 'new file'      # Fresh (added)
        assert 'src/old.py' not in result                      # Removed (marked as changed, not in fresh)

        # Verify counts
        assert len(result) == 3
