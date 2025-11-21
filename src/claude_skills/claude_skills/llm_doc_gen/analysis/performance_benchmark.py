"""
Performance Benchmarking for Analysis Insights.

Measures the performance impact of codebase analysis insight extraction and
caching on documentation generation workflows. Validates that insight extraction
overhead stays below 2 seconds as specified in requirements.

Key metrics:
- Insight extraction time (cold and warm cache)
- Cache hit/miss rates
- Memory usage
- Performance across different codebase sizes
"""

import time
import json
import tempfile
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .analysis_insights import (
    extract_insights_from_analysis,
    format_insights_for_prompt,
    get_cache_metrics,
    reset_cache_metrics,
    clear_cache
)


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""

    # Timing metrics (seconds)
    cold_cache_time: float
    warm_cache_time: float
    format_time: float
    total_time: float

    # Cache metrics
    cache_hits: int
    cache_misses: int
    cache_invalidations: int
    hit_rate: float

    # Memory metrics (MB)
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float

    # Codebase context
    codebase_size: int  # Number of files
    analysis_file_size_kb: float

    def meets_performance_target(self, target_seconds: float = 2.0) -> bool:
        """
        Check if performance meets target threshold.

        Args:
            target_seconds: Maximum acceptable overhead in seconds

        Returns:
            True if total time is below target
        """
        return self.total_time <= target_seconds

    def speedup_factor(self) -> float:
        """
        Calculate speedup factor from cache usage.

        Returns:
            Ratio of cold cache time to warm cache time
        """
        if self.warm_cache_time == 0:
            return float('inf')
        return self.cold_cache_time / self.warm_cache_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'timing': {
                'cold_cache_seconds': round(self.cold_cache_time, 4),
                'warm_cache_seconds': round(self.warm_cache_time, 4),
                'format_seconds': round(self.format_time, 4),
                'total_seconds': round(self.total_time, 4),
                'speedup_factor': round(self.speedup_factor(), 2)
            },
            'cache': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'invalidations': self.cache_invalidations,
                'hit_rate': round(self.hit_rate, 3)
            },
            'memory': {
                'before_mb': round(self.memory_before_mb, 2),
                'after_mb': round(self.memory_after_mb, 2),
                'delta_mb': round(self.memory_delta_mb, 2)
            },
            'codebase': {
                'file_count': self.codebase_size,
                'analysis_size_kb': round(self.analysis_file_size_kb, 2)
            },
            'meets_target': self.meets_performance_target()
        }


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    benchmark_id: str
    timestamp: str
    codebase_category: str  # 'small', 'medium', 'large'
    metrics: PerformanceMetrics
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'benchmark_id': self.benchmark_id,
            'timestamp': self.timestamp,
            'codebase_category': self.codebase_category,
            'metrics': self.metrics.to_dict(),
            'notes': self.notes
        }


class PerformanceBenchmark:
    """
    Performance benchmark suite for analysis insight extraction.

    Measures timing, caching efficiency, and memory usage across different
    codebase sizes.
    """

    def __init__(self, results_dir: Optional[Path] = None):
        """
        Initialize performance benchmark.

        Args:
            results_dir: Directory to store benchmark results (defaults to ./benchmark_results)
        """
        self.results_dir = results_dir or Path('./benchmark_results')
        self.results_dir.mkdir(exist_ok=True, parents=True)

    def benchmark_extraction(
        self,
        docs_path: Path,
        benchmark_id: Optional[str] = None,
        generator_type: str = 'architecture'
    ) -> BenchmarkResult:
        """
        Benchmark insight extraction and formatting performance.

        Measures:
        1. Cold cache extraction time (first load)
        2. Warm cache extraction time (cached load)
        3. Formatting time for prompt inclusion
        4. Memory usage
        5. Cache hit rates

        Args:
            docs_path: Path to codebase.json file
            benchmark_id: Optional custom ID (auto-generated if None)
            generator_type: Generator type for formatting ('architecture', 'component', 'overview')

        Returns:
            BenchmarkResult with detailed performance metrics
        """
        from datetime import datetime

        # Generate benchmark ID if not provided
        if benchmark_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            benchmark_id = f"perf_{timestamp}"

        # Get codebase size and file size
        analysis_size_kb = docs_path.stat().st_size / 1024

        with open(docs_path, 'r') as f:
            data = json.load(f)
            files = set()
            for func in data.get('functions', []):
                if 'file' in func:
                    files.add(func['file'])
            for cls in data.get('classes', []):
                if 'file' in cls:
                    files.add(cls['file'])
            codebase_size = len(files)

        # Determine codebase category
        if codebase_size < 100:
            category = 'small'
        elif codebase_size <= 500:
            category = 'medium'
        else:
            category = 'large'

        # Reset cache and metrics
        clear_cache()
        reset_cache_metrics()

        # Measure memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Measure cold cache extraction (first load)
        start_cold = time.time()
        insights_cold = extract_insights_from_analysis(docs_path, use_cache=True)
        cold_time = time.time() - start_cold

        # Measure warm cache extraction (cached load)
        start_warm = time.time()
        insights_warm = extract_insights_from_analysis(docs_path, use_cache=True)
        warm_time = time.time() - start_warm

        # Measure formatting time
        start_format = time.time()
        formatted = format_insights_for_prompt(insights_warm, generator_type, docs_path)
        format_time = time.time() - start_format

        # Measure memory after
        memory_after = process.memory_info().rss / (1024 * 1024)  # MB
        memory_delta = memory_after - memory_before

        # Get cache metrics
        cache_metrics = get_cache_metrics()

        # Calculate total time (cold path is worst case)
        total_time = cold_time + format_time

        # Create metrics object
        metrics = PerformanceMetrics(
            cold_cache_time=cold_time,
            warm_cache_time=warm_time,
            format_time=format_time,
            total_time=total_time,
            cache_hits=cache_metrics.hits,
            cache_misses=cache_metrics.misses,
            cache_invalidations=cache_metrics.invalidations,
            hit_rate=cache_metrics.hit_rate(),
            memory_before_mb=memory_before,
            memory_after_mb=memory_after,
            memory_delta_mb=memory_delta,
            codebase_size=codebase_size,
            analysis_file_size_kb=analysis_size_kb
        )

        # Create result
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            timestamp=datetime.now().isoformat(),
            codebase_category=category,
            metrics=metrics
        )

        return result

    def benchmark_multiple_runs(
        self,
        docs_path: Path,
        num_runs: int = 10,
        generator_type: str = 'architecture'
    ) -> Dict[str, Any]:
        """
        Run multiple benchmark iterations to get statistical data.

        Args:
            docs_path: Path to codebase.json
            num_runs: Number of benchmark iterations
            generator_type: Generator type for formatting

        Returns:
            Dictionary with aggregated statistics
        """
        cold_times = []
        warm_times = []
        format_times = []
        memory_deltas = []

        for i in range(num_runs):
            # Clear cache between runs for consistent cold measurements
            clear_cache()
            reset_cache_metrics()

            result = self.benchmark_extraction(
                docs_path,
                benchmark_id=f"multi_run_{i}",
                generator_type=generator_type
            )

            cold_times.append(result.metrics.cold_cache_time)
            warm_times.append(result.metrics.warm_cache_time)
            format_times.append(result.metrics.format_time)
            memory_deltas.append(result.metrics.memory_delta_mb)

        # Calculate statistics
        def stats(values: List[float]) -> Dict[str, float]:
            return {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'median': sorted(values)[len(values) // 2]
            }

        return {
            'num_runs': num_runs,
            'cold_cache': stats(cold_times),
            'warm_cache': stats(warm_times),
            'format_time': stats(format_times),
            'memory_delta_mb': stats(memory_deltas),
            'total_time_mean': stats(cold_times)['mean'] + stats(format_times)['mean']
        }

    def benchmark_by_codebase_size(
        self,
        test_cases: List[tuple[Path, str]]
    ) -> Dict[str, BenchmarkResult]:
        """
        Benchmark across different codebase sizes.

        Args:
            test_cases: List of (docs_path, category_name) tuples
                       e.g., [(Path('./small.json'), 'small'), ...]

        Returns:
            Dictionary mapping category name to BenchmarkResult
        """
        results = {}

        for docs_path, category in test_cases:
            result = self.benchmark_extraction(
                docs_path,
                benchmark_id=f"size_{category}",
                generator_type='architecture'
            )
            results[category] = result

        return results

    def save_result(self, result: BenchmarkResult, filename: Optional[str] = None) -> Path:
        """
        Save benchmark result to disk.

        Args:
            result: BenchmarkResult to save
            filename: Optional custom filename (defaults to benchmark_id.json)

        Returns:
            Path to saved result file
        """
        if filename is None:
            filename = f"{result.benchmark_id}.json"

        result_path = self.results_dir / filename

        with open(result_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        return result_path

    def load_result(self, benchmark_id: str) -> Dict[str, Any]:
        """
        Load benchmark result from disk.

        Args:
            benchmark_id: Benchmark ID to load

        Returns:
            Dictionary with benchmark result data
        """
        result_path = self.results_dir / f"{benchmark_id}.json"

        if not result_path.exists():
            raise FileNotFoundError(f"Benchmark result not found: {result_path}")

        with open(result_path, 'r') as f:
            return json.load(f)

    def generate_report(self, benchmark_ids: List[str]) -> str:
        """
        Generate summary report from multiple benchmark results.

        Args:
            benchmark_ids: List of benchmark IDs to include

        Returns:
            Formatted markdown report
        """
        results = [self.load_result(bid) for bid in benchmark_ids]

        report_parts = []
        report_parts.append("# Performance Benchmark Report: Analysis Insights")
        report_parts.append("")
        report_parts.append(f"**Tests Analyzed:** {len(results)}")
        report_parts.append(f"**Performance Target:** <2.0 seconds")
        report_parts.append("")

        # Summary statistics
        passes = sum(1 for r in results if r['metrics']['meets_target'])
        pass_rate = (passes / len(results)) * 100

        report_parts.append("## Summary")
        report_parts.append("")
        report_parts.append(f"- **Tests Passing Target:** {passes}/{len(results)} ({pass_rate:.1f}%)")
        report_parts.append("")

        # Timing statistics by codebase size
        by_category = {}
        for r in results:
            cat = r['codebase_category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r)

        report_parts.append("## Performance by Codebase Size")
        report_parts.append("")

        for category in ['small', 'medium', 'large']:
            if category not in by_category:
                continue

            cat_results = by_category[category]
            avg_cold = sum(r['metrics']['timing']['cold_cache_seconds'] for r in cat_results) / len(cat_results)
            avg_warm = sum(r['metrics']['timing']['warm_cache_seconds'] for r in cat_results) / len(cat_results)
            avg_total = sum(r['metrics']['timing']['total_seconds'] for r in cat_results) / len(cat_results)
            avg_speedup = sum(r['metrics']['timing']['speedup_factor'] for r in cat_results) / len(cat_results)

            report_parts.append(f"### {category.title()} Codebases")
            report_parts.append("")
            report_parts.append(f"- **Average Cold Cache:** {avg_cold:.4f}s")
            report_parts.append(f"- **Average Warm Cache:** {avg_warm:.4f}s")
            report_parts.append(f"- **Average Total:** {avg_total:.4f}s")
            report_parts.append(f"- **Cache Speedup:** {avg_speedup:.1f}x")
            report_parts.append("")

        # Detailed results table
        report_parts.append("## Detailed Results")
        report_parts.append("")
        report_parts.append("| Benchmark ID | Category | Cold | Warm | Total | Speedup | Target Met |")
        report_parts.append("| --- | --- | --- | --- | --- | --- | --- |")

        for r in results:
            bid = r['benchmark_id']
            cat = r['codebase_category']
            cold = r['metrics']['timing']['cold_cache_seconds']
            warm = r['metrics']['timing']['warm_cache_seconds']
            total = r['metrics']['timing']['total_seconds']
            speedup = r['metrics']['timing']['speedup_factor']
            meets = "✅" if r['metrics']['meets_target'] else "❌"

            report_parts.append(
                f"| {bid} | {cat} | {cold:.4f}s | {warm:.4f}s | {total:.4f}s | {speedup:.1f}x | {meets} |"
            )

        report_parts.append("")

        # Cache effectiveness
        report_parts.append("## Cache Effectiveness")
        report_parts.append("")

        for r in results:
            cache = r['metrics']['cache']
            report_parts.append(f"**{r['benchmark_id']}**")
            report_parts.append(f"- Hits: {cache['hits']}")
            report_parts.append(f"- Misses: {cache['misses']}")
            report_parts.append(f"- Hit Rate: {cache['hit_rate']:.1%}")
            report_parts.append("")

        return "\n".join(report_parts)


# Convenience functions for quick benchmarking
def quick_benchmark(docs_path: Path, generator_type: str = 'architecture') -> Dict[str, Any]:
    """
    Quick benchmark for a single documentation file.

    Args:
        docs_path: Path to codebase.json
        generator_type: Generator type for formatting

    Returns:
        Dictionary with benchmark results
    """
    benchmark = PerformanceBenchmark()
    result = benchmark.benchmark_extraction(docs_path, generator_type=generator_type)
    return result.to_dict()


def validate_performance_target(docs_path: Path, target_seconds: float = 2.0) -> bool:
    """
    Check if insight extraction meets performance target.

    Args:
        docs_path: Path to codebase.json
        target_seconds: Maximum acceptable overhead

    Returns:
        True if performance meets target
    """
    benchmark = PerformanceBenchmark()
    result = benchmark.benchmark_extraction(docs_path)
    return result.metrics.meets_performance_target(target_seconds)
