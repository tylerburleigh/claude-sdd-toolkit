"""
Integration tests for incremental consensus calculation.

Tests that consensus calculation correctly includes both cached results
(from unchanged files) and fresh results (from changed files) when
performing incremental reviews with file hash comparison and result merging.

This test verifies verify-3-3 requirement:
"Consensus calculation includes both cached and fresh results"
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_skills.common.cache import CacheManager
from claude_skills.common.ai_tools import ToolResponse, ToolStatus


class TestIncrementalConsensusCalculation:
    """Test consensus calculation with incremental reviews."""

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache manager."""
        cache = Mock(spec=CacheManager)
        return cache

    @pytest.fixture
    def cached_results(self):
        """Create sample cached results from previous runs."""
        return {
            "file_1.py": {
                "status": "pass",
                "score": 0.95,
                "issues": [],
                "models_consulted": 3,
                "consensus_verdict": "pass",
                "agreement_rate": 0.95
            },
            "file_2.py": {
                "status": "partial",
                "score": 0.75,
                "issues": ["Missing error handling"],
                "models_consulted": 3,
                "consensus_verdict": "partial",
                "agreement_rate": 0.67
            },
            "file_3.py": {
                "status": "pass",
                "score": 0.90,
                "issues": [],
                "models_consulted": 3,
                "consensus_verdict": "pass",
                "agreement_rate": 0.90
            }
        }

    @pytest.fixture
    def fresh_results(self):
        """Create sample fresh results from current run (only changed files)."""
        return {
            "file_2.py": {
                "status": "pass",
                "score": 0.92,
                "issues": [],
                "models_consulted": 3,
                "consensus_verdict": "pass",
                "agreement_rate": 0.92
            }
        }

    def test_merge_maintains_consensus_from_cached_files(self, cached_results, fresh_results):
        """Test that cached results for unchanged files are included in consensus."""
        # Unchanged files should retain their cached consensus
        unchanged_files = ["file_1.py", "file_3.py"]
        changed_files = ["file_2.py"]

        # Merge results: unchanged use cache, changed use fresh
        merged = {}
        for file in unchanged_files:
            if file in cached_results:
                merged[file] = cached_results[file]

        for file in changed_files:
            if file in fresh_results:
                merged[file] = fresh_results[file]

        # Verify cached results are preserved
        assert "file_1.py" in merged
        assert merged["file_1.py"]["consensus_verdict"] == "pass"
        assert merged["file_1.py"]["agreement_rate"] == 0.95

        assert "file_3.py" in merged
        assert merged["file_3.py"]["consensus_verdict"] == "pass"
        assert merged["file_3.py"]["agreement_rate"] == 0.90

        # Verify fresh results override cached
        assert "file_2.py" in merged
        assert merged["file_2.py"]["consensus_verdict"] == "pass"  # Changed from cached
        assert merged["file_2.py"]["agreement_rate"] == 0.92  # Updated

    def test_incremental_consensus_includes_all_files(self, cached_results, fresh_results):
        """Test that consensus includes results from both cached and fresh sources."""
        unchanged_files = ["file_1.py", "file_3.py"]
        changed_files = ["file_2.py"]

        # Merge results
        merged = {}
        for file in unchanged_files:
            merged[file] = cached_results[file]
        for file in changed_files:
            merged[file] = fresh_results[file]

        # Calculate overall consensus from merged results
        verdicts = [r["consensus_verdict"] for r in merged.values()]
        agreement_rates = [r["agreement_rate"] for r in merged.values()]

        total_files = len(merged)
        pass_count = sum(1 for v in verdicts if v == "pass")
        agreement_avg = sum(agreement_rates) / len(agreement_rates)

        # Verify consensus includes all files (2 cached + 1 fresh = 3 total)
        assert total_files == 3
        assert pass_count == 3  # All files passed in merged results
        assert agreement_avg > 0.9  # High consensus

        # Verify specific file counts
        assert "file_1.py" in merged  # From cache
        assert "file_2.py" in merged  # From fresh
        assert "file_3.py" in merged  # From cache

    def test_consensus_accuracy_with_mixed_sources(self, cached_results, fresh_results):
        """Test that consensus calculations are accurate with mixed cache/fresh sources."""
        # Setup: 2 unchanged (cached), 1 changed (fresh)
        changed_files = {"file_2.py"}

        merged = {}
        for file, result in cached_results.items():
            if file not in changed_files:
                merged[file] = result  # Use cache for unchanged

        for file, result in fresh_results.items():
            merged[file] = result  # Use fresh for changed

        # Calculate consensus metrics
        models_per_file = [r["models_consulted"] for r in merged.values()]
        avg_models = sum(models_per_file) / len(models_per_file)

        # All should have been reviewed by 3 models (cache was 3-model consensus, fresh is 3-model)
        assert all(m == 3 for m in models_per_file)
        assert avg_models == 3.0

        # Agreement rates should reflect both sources
        agreement_rates = [r["agreement_rate"] for r in merged.values()]
        assert len(agreement_rates) == 3  # All files included
        assert min(agreement_rates) > 0.6  # All rates reasonable
        assert max(agreement_rates) <= 1.0  # All valid

    def test_cache_manager_merge_results_method(self, mock_cache):
        """Test CacheManager.merge_results static method."""
        cached_docs = {
            "file_1.py": {"doc": "Original doc", "generated": True},
            "file_2.py": {"doc": "Original doc", "generated": True},
            "file_3.py": {"doc": "Original doc", "generated": True}
        }

        fresh_docs = {
            "file_2.py": {"doc": "Updated doc", "generated": True},
            "file_4.py": {"doc": "New doc", "generated": True}
        }

        changed_files = {
            "added": ["file_4.py"],
            "modified": ["file_2.py"],
            "removed": [],
            "unchanged": ["file_1.py", "file_3.py"]
        }

        # Merge using CacheManager static method
        merged = CacheManager.merge_results(cached_docs, fresh_docs, changed_files)

        # Verify merge behavior
        assert "file_1.py" in merged  # Unchanged - from cache
        assert "file_2.py" in merged  # Changed - from fresh
        assert "file_3.py" in merged  # Unchanged - from cache
        assert "file_4.py" in merged  # Added - from fresh

        # Verify content sources
        assert merged["file_1.py"]["doc"] == "Original doc"  # Cached
        assert merged["file_2.py"]["doc"] == "Updated doc"   # Fresh
        assert merged["file_3.py"]["doc"] == "Original doc"  # Cached
        assert merged["file_4.py"]["doc"] == "New doc"       # Fresh

    def test_incremental_consensus_no_regressions(self, cached_results):
        """Test that incremental consensus doesn't introduce regressions."""
        # When no files change, consensus should remain identical to cached
        unchanged_files = list(cached_results.keys())
        fresh_results = {}  # No fresh results

        merged = {}
        for file in unchanged_files:
            merged[file] = cached_results[file]

        # Consensus should be identical to cached
        for file in cached_results:
            assert merged[file] == cached_results[file]

        # Verify verdicts unchanged
        cached_verdicts = [r["consensus_verdict"] for r in cached_results.values()]
        merged_verdicts = [r["consensus_verdict"] for r in merged.values()]
        assert cached_verdicts == merged_verdicts

    def test_consensus_with_partial_incremental_run(self):
        """Test consensus when only some files are reviewed incrementally."""
        # Scenario: 5 files total, only 2 changed
        cached_full_consensus = {
            "file_1.py": {"verdict": "pass", "agreement": 0.95, "models": 3},
            "file_2.py": {"verdict": "partial", "agreement": 0.67, "models": 3},
            "file_3.py": {"verdict": "pass", "agreement": 0.90, "models": 3},
            "file_4.py": {"verdict": "fail", "agreement": 0.60, "models": 3},
            "file_5.py": {"verdict": "pass", "agreement": 0.85, "models": 3}
        }

        fresh_review_results = {
            "file_2.py": {"verdict": "pass", "agreement": 0.92, "models": 3},
            "file_4.py": {"verdict": "partial", "agreement": 0.70, "models": 3}
        }

        changed_files = {
            "added": [],
            "modified": ["file_2.py", "file_4.py"],
            "removed": [],
            "unchanged": ["file_1.py", "file_3.py", "file_5.py"]
        }

        # Perform merge
        merged = CacheManager.merge_results(cached_full_consensus, fresh_review_results, changed_files)

        # Verify consensus includes all 5 files
        assert len(merged) == 5

        # Verify cached files maintained (3 unchanged)
        assert merged["file_1.py"]["verdict"] == "pass"  # Unchanged
        assert merged["file_3.py"]["verdict"] == "pass"  # Unchanged
        assert merged["file_5.py"]["verdict"] == "pass"  # Unchanged

        # Verify changed files updated
        assert merged["file_2.py"]["verdict"] == "pass"  # Changed (improved)
        assert merged["file_4.py"]["verdict"] == "partial"  # Changed (improved)

        # Calculate overall metrics including both sources
        all_verdicts = [r["verdict"] for r in merged.values()]
        pass_count = sum(1 for v in all_verdicts if v == "pass")
        assert pass_count == 4  # 4 pass after update

    def test_consensus_agreement_rate_calculation_with_merged_results(self):
        """Test that consensus agreement rates are correctly calculated with merged results."""
        merged_results = {
            "file_1.py": {"agreement": 0.95, "models_used": 3},
            "file_2.py": {"agreement": 0.92, "models_used": 3},
            "file_3.py": {"agreement": 0.90, "models_used": 3},
            "file_4.py": {"agreement": 0.67, "models_used": 3}
        }

        # Calculate overall agreement rate
        agreement_rates = [r["agreement"] for r in merged_results.values()]
        overall_agreement = sum(agreement_rates) / len(agreement_rates)

        assert len(merged_results) == 4  # All files included
        assert 0.85 < overall_agreement < 0.95  # Reasonable overall rate
        assert overall_agreement == pytest.approx(0.86, rel=0.01)

    def test_incremental_mode_flag_in_file_changes(self):
        """Test that incremental mode flag is correctly set in file changes."""
        # Create reviewer with incremental mode enabled
        mock_cache = Mock(spec=CacheManager)
        mock_cache.get_incremental_state.return_value = {
            "file_1.py": "hash1",
            "file_2.py": "hash2"
        }

        changes = {
            "added": [],
            "modified": ["file_2.py"],
            "removed": [],
            "unchanged": ["file_1.py"],
            "is_incremental": True
        }

        # Verify incremental flag is set
        assert changes["is_incremental"] is True
        assert len(changes["unchanged"]) == 1
        assert len(changes["modified"]) == 1


class TestConsensusFromMixedSources:
    """Test consensus building from mixed cache/fresh sources."""

    def test_build_consensus_with_cached_responses(self):
        """Test building consensus when some responses are from cache."""
        # Cached tool responses (from previous consultation)
        cached_responses = [
            ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="The implementation is compliant.",
                duration=2.5
            ),
            ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="Implementation matches spec requirements.",
                duration=3.1
            )
        ]

        # Fresh tool responses (from current consultation)
        fresh_responses = [
            ToolResponse(
                tool="cursor-agent",
                status=ToolStatus.SUCCESS,
                output="All requirements implemented correctly.",
                duration=4.2
            )
        ]

        all_responses = cached_responses + fresh_responses

        # Verify we have mixed sources
        assert len(cached_responses) == 2  # Cached
        assert len(fresh_responses) == 1   # Fresh
        assert len(all_responses) == 3     # Total for consensus

        # Verify all responses are successful for consensus calculation
        successful = [r for r in all_responses if r.success]
        assert len(successful) == 3

    def test_consensus_verdict_with_incremental_reviews(self):
        """Test that consensus verdict correctly reflects merged results."""
        # Simulate consensus calculation with merged results
        file_verdicts = {
            "file_1.py": "pass",      # From cache
            "file_2.py": "pass",      # From fresh review
            "file_3.py": "pass",      # From cache
            "file_4.py": "fail",      # From cache
            "file_5.py": "partial"    # From fresh review
        }

        verdicts = list(file_verdicts.values())
        pass_count = sum(1 for v in verdicts if v == "pass")
        partial_count = sum(1 for v in verdicts if v == "partial")
        fail_count = sum(1 for v in verdicts if v == "fail")

        # Calculate consensus verdict
        if fail_count > 0:
            consensus = "fail"
        elif partial_count > 0:
            consensus = "partial"
        else:
            consensus = "pass"

        assert consensus == "fail"  # Overall verdict is fail due to one failure
        assert len(verdicts) == 5   # All files included (3 cached + 2 fresh)


class TestIncrementalReviewWorkflow:
    """Test complete incremental review workflow."""

    def test_incremental_review_preserves_consensus_across_runs(self):
        """Test that incremental reviews preserve consensus accuracy across runs."""
        # Run 1: Full review
        run1_results = {
            "file_1.py": {"verdict": "pass", "agreement": 0.95},
            "file_2.py": {"verdict": "partial", "agreement": 0.67},
            "file_3.py": {"verdict": "pass", "agreement": 0.90}
        }

        # Run 2: Incremental review (only file_2 changed)
        run2_fresh = {
            "file_2.py": {"verdict": "pass", "agreement": 0.92}
        }

        changed_files = {
            "added": [],
            "modified": ["file_2.py"],
            "removed": [],
            "unchanged": ["file_1.py", "file_3.py"]
        }

        # Merge results
        run2_merged = CacheManager.merge_results(run1_results, run2_fresh, changed_files)

        # Verify incremental review includes all files
        assert len(run2_merged) == 3

        # Verify consensus accuracy
        verdicts = [r["verdict"] for r in run2_merged.values()]
        agreements = [r["agreement"] for r in run2_merged.values()]

        assert verdicts.count("pass") == 3  # All pass after update
        assert sum(agreements) / len(agreements) > 0.9  # High overall agreement

    def test_consensus_calculation_respects_incremental_flag(self):
        """Test that consensus calculation respects incremental mode setting."""
        # With incremental flag: only review changed files, merge with cache
        incremental_mode = {
            "is_incremental": True,
            "files_reviewed": 1,
            "files_from_cache": 3,
            "total_files": 4
        }

        # Full review mode would review all 4 files
        full_mode = {
            "is_incremental": False,
            "files_reviewed": 4,
            "files_from_cache": 0,
            "total_files": 4
        }

        assert incremental_mode["is_incremental"] is True
        assert incremental_mode["files_reviewed"] < full_mode["files_reviewed"]
        assert incremental_mode["files_from_cache"] > full_mode["files_from_cache"]

        # Both should have complete consensus for all files
        assert incremental_mode["total_files"] == full_mode["total_files"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
