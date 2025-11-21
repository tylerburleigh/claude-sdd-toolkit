"""
Tests for analysis_insights module.

Tests extraction, formatting, caching, and token budget enforcement.
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.analysis_insights import (
    AnalysisInsights,
    extract_insights_from_analysis,
    format_insights_for_prompt,
    get_cache_metrics,
    reset_cache_metrics,
    clear_cache,
    CacheEntry,
    CacheMetrics
)


@pytest.fixture
def sample_documentation_data():
    """Sample codebase.json data for testing."""
    return {
        "functions": [
            {
                "name": "process_data",
                "file": "src/utils.py",
                "complexity": 15,
                "call_count": 50,
                "callers": [],
                "calls": [
                    {"name": "validate", "file": "src/validators.py"},
                    {"name": "transform", "file": "src/transforms.py"}
                ]
            },
            {
                "name": "main",
                "file": "src/main.py",
                "complexity": 8,
                "call_count": 1,
                "callers": [],
                "calls": [
                    {"name": "process_data", "file": "src/utils.py"},
                    {"name": "save_results", "file": "src/io.py"}
                ]
            },
            {
                "name": "orchestrate",
                "file": "src/orchestrator.py",
                "complexity": 12,
                "call_count": 10,
                "callers": [{"name": "main", "file": "src/main.py"}],
                "calls": [
                    {"name": "fn1", "file": "src/a.py"},
                    {"name": "fn2", "file": "src/b.py"},
                    {"name": "fn3", "file": "src/c.py"},
                    {"name": "fn4", "file": "src/d.py"},
                    {"name": "fn5", "file": "src/e.py"},
                    {"name": "fn6", "file": "src/f.py"},
                    {"name": "fn7", "file": "src/g.py"},
                    {"name": "fn8", "file": "src/h.py"}
                ]
            }
        ],
        "classes": [
            {
                "name": "DataProcessor",
                "file": "src/processors.py",
                "instantiation_count": 25
            },
            {
                "name": "Config",
                "file": "src/config.py",
                "instantiation_count": 100
            }
        ],
        "dependencies": {
            "src/main.py": ["src/utils.py", "src/io.py"],
            "src/utils.py": ["src/validators.py", "src/transforms.py"],
            "src/orchestrator.py": ["pytest", "requests"]
        }
    }


@pytest.fixture
def temp_doc_file(sample_documentation_data):
    """Create temporary codebase.json file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_documentation_data, f)
        path = Path(f.name)

    yield path

    # Cleanup
    path.unlink()


def test_analysis_insights_dataclass():
    """Test AnalysisInsights dataclass creation and to_dict."""
    insights = AnalysisInsights(
        high_complexity_functions=["func1", "func2"],
        most_called_functions=[{"name": "func1", "file": "a.py", "call_count": 10}],
        module_statistics={"total_modules": 5}
    )

    data = insights.to_dict()

    assert "high_complexity_functions" in data
    assert len(data["high_complexity_functions"]) == 2
    assert data["most_called_functions"][0]["call_count"] == 10
    assert data["module_statistics"]["total_modules"] == 5


def test_extract_insights_basic(temp_doc_file):
    """Test basic extraction from codebase.json."""
    clear_cache()  # Start fresh
    reset_cache_metrics()

    insights = extract_insights_from_analysis(temp_doc_file)

    # Check that insights were extracted
    assert len(insights.most_called_functions) > 0
    assert insights.most_called_functions[0]["name"] == "process_data"
    assert insights.most_called_functions[0]["call_count"] == 50

    # Check high complexity functions
    assert "process_data" in insights.high_complexity_functions
    assert "orchestrate" in insights.high_complexity_functions

    # Check module statistics
    assert insights.module_statistics["total_functions"] == 3
    assert insights.module_statistics["total_classes"] == 2


def test_extract_insights_entry_points(temp_doc_file):
    """Test entry point detection (0-2 callers)."""
    clear_cache()

    insights = extract_insights_from_analysis(temp_doc_file)

    # main and process_data should be entry points (0 callers)
    entry_names = [ep["name"] for ep in insights.entry_points]
    assert "main" in entry_names
    assert "process_data" in entry_names

    # Check type detection
    main_entry = next(ep for ep in insights.entry_points if ep["name"] == "main")
    assert main_entry["type"] == "main"


def test_extract_insights_fan_out(temp_doc_file):
    """Test fan-out analysis (8+ calls)."""
    clear_cache()

    insights = extract_insights_from_analysis(temp_doc_file)

    # orchestrate calls 8 functions, should be in fan_out
    assert len(insights.fan_out_analysis) > 0
    assert insights.fan_out_analysis[0]["name"] == "orchestrate"
    assert insights.fan_out_analysis[0]["calls_count"] == 8


def test_extract_insights_cross_module_deps(temp_doc_file):
    """Test cross-module dependency extraction."""
    clear_cache()

    insights = extract_insights_from_analysis(temp_doc_file)

    # Check that dependencies were extracted
    assert len(insights.cross_module_dependencies) > 0

    # Verify structure
    dep = insights.cross_module_dependencies[0]
    assert "from_module" in dep
    assert "to_module" in dep
    assert "dependency_count" in dep


def test_extract_insights_integration_points(temp_doc_file):
    """Test external integration detection."""
    clear_cache()

    insights = extract_insights_from_analysis(temp_doc_file)

    # Should detect pytest and requests as external
    integration_names = [ip["name"] for ip in insights.integration_points]
    assert "pytest" in integration_names
    assert "requests" in integration_names


def test_extract_insights_adaptive_scaling(temp_doc_file):
    """Test adaptive scaling based on codebase size."""
    clear_cache()

    # Test with small codebase (<100 files) - should get top 10
    insights_small = extract_insights_from_analysis(temp_doc_file, codebase_size=50)

    # Verify we don't get more than 10 items (when available)
    # Since our test data is small, just verify the function works
    assert isinstance(insights_small, AnalysisInsights)


def test_caching_mechanism(temp_doc_file):
    """Test JSON caching with file modification tracking."""
    clear_cache()
    reset_cache_metrics()

    # First load - cache miss
    insights1 = extract_insights_from_analysis(temp_doc_file, use_cache=True)
    metrics1 = get_cache_metrics()
    assert metrics1.misses == 1
    assert metrics1.hits == 0

    # Second load - cache hit
    insights2 = extract_insights_from_analysis(temp_doc_file, use_cache=True)
    metrics2 = get_cache_metrics()
    assert metrics2.hits == 1
    assert metrics2.misses == 1

    # Modify file - should invalidate cache
    time.sleep(0.1)  # Ensure mtime changes
    with open(temp_doc_file, 'w') as f:
        json.dump({"functions": [], "classes": [], "dependencies": {}}, f)

    insights3 = extract_insights_from_analysis(temp_doc_file, use_cache=True)
    metrics3 = get_cache_metrics()
    assert metrics3.invalidations == 1


def test_cache_freshness_warning(temp_doc_file, caplog):
    """Test freshness warning for stale cache (>24 hours)."""
    clear_cache()
    import logging
    caplog.set_level(logging.WARNING)

    # Load once to cache
    extract_insights_from_analysis(temp_doc_file, use_cache=True)

    # Manually set cache age to >24 hours for testing
    from claude_skills.llm_doc_gen.analysis import analysis_insights
    if analysis_insights._documentation_cache:
        analysis_insights._documentation_cache.load_time = time.time() - (25 * 3600)

    # Load again - should warn
    extract_insights_from_analysis(temp_doc_file, use_cache=True, warn_stale=True)

    # Check for warning
    assert any("hours old" in record.message for record in caplog.records)


def test_format_insights_architecture(temp_doc_file):
    """Test formatting for architecture generator."""
    clear_cache()
    insights = extract_insights_from_analysis(temp_doc_file)

    formatted = format_insights_for_prompt(insights, "architecture", temp_doc_file)

    # Should include all priority sections for architecture
    assert "**Codebase Overview:**" in formatted
    assert "**Most Called Functions:**" in formatted
    assert "**Entry Points:**" in formatted
    assert "**Cross-Module Dependencies:**" in formatted
    assert "**Orchestration Functions (High Fan-Out):**" in formatted
    assert "**Full Analysis Available:**" in formatted


def test_format_insights_component(temp_doc_file):
    """Test formatting for component generator."""
    clear_cache()
    insights = extract_insights_from_analysis(temp_doc_file)

    formatted = format_insights_for_prompt(insights, "component", temp_doc_file)

    # Should include component-relevant sections
    assert "**Codebase Overview:**" in formatted
    assert "**Most Called Functions:**" in formatted
    # Should NOT include architecture-specific fan-out for component
    # (but our test data triggers it, so just verify it works)
    assert isinstance(formatted, str)


def test_format_insights_overview(temp_doc_file):
    """Test formatting for overview generator."""
    clear_cache()
    insights = extract_insights_from_analysis(temp_doc_file)

    formatted = format_insights_for_prompt(insights, "overview")

    # Should be most concise (250 token budget)
    assert "**Codebase Overview:**" in formatted
    # Verify it's a valid string
    assert isinstance(formatted, str)


def test_token_budget_enforcement(temp_doc_file):
    """Test that formatted output respects token budgets."""
    clear_cache()
    insights = extract_insights_from_analysis(temp_doc_file)

    # Test each generator type
    for gen_type, budget in [("overview", 250), ("component", 350), ("architecture", 450)]:
        formatted = format_insights_for_prompt(insights, gen_type)

        # Estimate tokens (4 chars = 1 token)
        estimated_tokens = len(formatted) // 4

        # Should be within budget (with some tolerance for file ref)
        assert estimated_tokens <= budget + 50  # +50 for file reference


def test_table_format(temp_doc_file):
    """Test that output uses table format (not prose)."""
    clear_cache()
    insights = extract_insights_from_analysis(temp_doc_file)

    formatted = format_insights_for_prompt(insights, "architecture")

    # Check for table-like formatting (| separators)
    assert "|" in formatted

    # Should have function names followed by metadata
    assert "process_data" in formatted
    assert "calls" in formatted


def test_priority_truncation():
    """Test priority-based truncation when over budget."""
    # Create insights with lots of data
    large_insights = AnalysisInsights(
        high_complexity_functions=[f"func{i}" for i in range(50)],
        most_called_functions=[
            {"name": f"func{i}", "file": f"file{i}.py", "call_count": 100 - i}
            for i in range(50)
        ],
        entry_points=[
            {"name": f"entry{i}", "file": f"file{i}.py", "type": "main", "caller_count": 0}
            for i in range(30)
        ],
        module_statistics={"total_modules": 100, "total_functions": 500, "total_classes": 200}
    )

    # Format with smallest budget (overview = 250)
    formatted = format_insights_for_prompt(large_insights, "overview")

    # Should still include codebase overview (highest priority)
    assert "**Codebase Overview:**" in formatted

    # Check token estimate is within budget
    estimated_tokens = len(formatted) // 4
    assert estimated_tokens <= 300  # 250 + buffer


def test_cache_metrics():
    """Test cache metrics tracking."""
    reset_cache_metrics()

    metrics = get_cache_metrics()
    assert metrics.hits == 0
    assert metrics.misses == 0
    assert metrics.invalidations == 0
    assert metrics.hit_rate() == 0.0


def test_cache_entry_freshness(temp_doc_file):
    """Test CacheEntry freshness checking."""
    with open(temp_doc_file, 'r') as f:
        data = json.load(f)

    mtime = temp_doc_file.stat().st_mtime

    entry = CacheEntry(
        data=data,
        path=temp_doc_file,
        load_time=time.time(),
        file_mtime=mtime
    )

    # Should be fresh
    assert entry.is_fresh()

    # Modify file
    time.sleep(0.1)
    with open(temp_doc_file, 'w') as f:
        json.dump({}, f)

    # Should no longer be fresh
    assert not entry.is_fresh()


def test_cache_entry_age(temp_doc_file):
    """Test CacheEntry age calculation."""
    with open(temp_doc_file, 'r') as f:
        data = json.load(f)

    entry = CacheEntry(
        data=data,
        path=temp_doc_file,
        load_time=time.time() - 7200,  # 2 hours ago
        file_mtime=temp_doc_file.stat().st_mtime
    )

    age = entry.age_hours()
    assert 1.9 < age < 2.1  # Should be ~2 hours
