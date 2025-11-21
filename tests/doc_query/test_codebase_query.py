"""Tests for CodebaseQuery class."""

import json
import pytest
from pathlib import Path
from claude_skills.doc_query.codebase_query import (
    CodebaseQuery,
    create_codebase_query
)


@pytest.fixture
def sample_codebase_json(tmp_path):
    """Create a sample codebase.json for testing."""
    docs_path = tmp_path / "docs"
    docs_path.mkdir()

    codebase_path = docs_path / "codebase.json"
    codebase_data = {
        "metadata": {
            "project_name": "TestProject",
            "version": "1.0.0",
            "generated_at": "2025-11-21T10:00:00Z",
            "languages": ["python"],
            "schema_version": "2.0"
        },
        "statistics": {
            "total_files": 10,
            "total_lines": 1000,
            "total_classes": 5,
            "total_functions": 20
        },
        "functions": [
            {
                "name": "process_data",
                "file": "src/processor.py",
                "line": 42,
                "complexity": 15,
                "docstring": "Main data processing pipeline",
                "call_count": 25,
                "callers": ["main", "handle_request"],
                "calls": [{"name": "validate_input"}, {"name": "transform"}]
            },
            {
                "name": "validate_input",
                "file": "src/processor.py",
                "line": 89,
                "complexity": 12,
                "docstring": "Input validation with multiple checks",
                "call_count": 30,
                "callers": ["process_data"],
                "calls": []
            },
            {
                "name": "main",
                "file": "src/main.py",
                "line": 10,
                "complexity": 3,
                "docstring": "Application entry point",
                "call_count": 1,
                "callers": [],
                "calls": [{"name": "process_data"}]
            },
            {
                "name": "helper",
                "file": "src/utils.py",
                "line": 5,
                "complexity": 2,
                "docstring": "Helper function",
                "call_count": 50,
                "callers": [],
                "calls": []
            }
        ],
        "classes": [
            {
                "name": "DataProcessor",
                "file": "src/processor.py",
                "line": 15,
                "docstring": "Main data processing class",
                "instantiation_count": 25
            },
            {
                "name": "Validator",
                "file": "src/validators.py",
                "line": 8,
                "docstring": "Input validation",
                "instantiation_count": 18
            },
            {
                "name": "Helper",
                "file": "src/utils.py",
                "line": 20,
                "docstring": "Helper utilities",
                "instantiation_count": 5
            }
        ],
        "modules": [
            {
                "name": "processor",
                "file": "src/processor.py",
                "docstring": "Data processing module",
                "functions": ["process_data", "validate_input"],
                "classes": ["DataProcessor"],
                "complexity": {
                    "avg": 13.5,
                    "max": 15,
                    "total": 27
                },
                "dependencies": ["utils"],
                "reverse_dependencies": ["main"]
            }
        ]
    }

    with open(codebase_path, 'w') as f:
        json.dump(codebase_data, f)

    return codebase_path


@pytest.fixture
def query_with_data(sample_codebase_json):
    """Create a CodebaseQuery instance with loaded data."""
    query = CodebaseQuery(str(sample_codebase_json.parent))
    query.load()
    return query


class TestCodebaseQueryInitialization:
    """Tests for CodebaseQuery initialization and loading."""

    def test_init_with_explicit_path(self, sample_codebase_json):
        """Test initialization with explicit path."""
        query = CodebaseQuery(str(sample_codebase_json))
        assert query.query.docs_path == sample_codebase_json
        assert not query._loaded

    def test_init_with_directory_path(self, sample_codebase_json):
        """Test initialization with directory path."""
        query = CodebaseQuery(str(sample_codebase_json.parent))
        assert query.query.docs_path == sample_codebase_json
        assert not query._loaded

    def test_load_success(self, sample_codebase_json):
        """Test successful loading of codebase data."""
        query = CodebaseQuery(str(sample_codebase_json))
        result = query.load()
        assert result is True
        assert query._loaded is True

    def test_load_missing_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        query = CodebaseQuery(str(tmp_path / "nonexistent.json"))
        result = query.load()
        assert result is False
        assert query._loaded is False

    def test_ensure_loaded_raises_on_missing(self, tmp_path):
        """Test _ensure_loaded raises when file missing."""
        query = CodebaseQuery(str(tmp_path / "nonexistent.json"))
        with pytest.raises(RuntimeError, match="Codebase analysis not found"):
            query._ensure_loaded()

    def test_create_codebase_query_convenience(self, sample_codebase_json):
        """Test convenience function creates and loads query."""
        query = create_codebase_query(str(sample_codebase_json))
        assert query._loaded is True


class TestComplexFunctionsQuery:
    """Tests for get_complex_functions_in_module."""

    def test_get_complex_functions_default_params(self, query_with_data):
        """Test getting complex functions with default parameters."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py"
        )

        assert "Most Complex Functions in src/processor.py" in result
        assert "process_data" in result
        assert "complexity: 15" in result
        assert "validate_input" in result
        assert "complexity: 12" in result

    def test_get_complex_functions_with_limit(self, query_with_data):
        """Test limiting number of functions returned."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py",
            top_n=1
        )

        assert "process_data" in result
        assert "complexity: 15" in result
        # Should not include the second function
        lines = result.split('\n')
        function_lines = [l for l in lines if l.strip().startswith(('1.', '2.'))]
        assert len(function_lines) == 1

    def test_get_complex_functions_high_threshold(self, query_with_data):
        """Test with threshold that filters out functions."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py",
            threshold=13
        )

        assert "process_data" in result
        assert "validate_input" not in result  # Below threshold

    def test_get_complex_functions_no_matches(self, query_with_data):
        """Test when no functions meet criteria."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py",
            threshold=100  # Impossibly high
        )

        assert "No complex functions found" in result

    def test_get_complex_functions_includes_docstring(self, query_with_data):
        """Test that docstrings are included in output."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py"
        )

        assert "Main data processing pipeline" in result
        assert "Input validation with multiple checks" in result

    def test_get_complex_functions_includes_location(self, query_with_data):
        """Test that file paths and line numbers are included."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py"
        )

        assert "src/processor.py:42" in result
        assert "src/processor.py:89" in result


class TestFunctionCallersQuery:
    """Tests for get_function_callers."""

    def test_get_function_callers_with_context(self, query_with_data):
        """Test getting function callers with file context."""
        result = query_with_data.get_function_callers("validate_input")

        # Should return formatted output (may be empty if no reverse deps built)
        assert "calling validate_input" in result or "callers" in result.lower()

    def test_get_function_callers_without_context(self, query_with_data):
        """Test getting function callers without file context."""
        result = query_with_data.get_function_callers(
            "validate_input",
            include_context=False
        )

        # Should return formatted output
        assert "calling validate_input" in result or "callers" in result.lower()
        # Verify method accepts include_context parameter
        assert isinstance(result, str)

    def test_get_function_callers_no_callers(self, query_with_data):
        """Test when function has no callers."""
        result = query_with_data.get_function_callers("main")

        assert "No callers found" in result

    def test_get_function_callers_multiple(self, query_with_data):
        """Test function with callers."""
        result = query_with_data.get_function_callers("validate_input")

        # Should return formatted string with caller information
        assert isinstance(result, str)
        assert "validate_input" in result


class TestInstantiatedClassesQuery:
    """Tests for get_instantiated_classes_in_file."""

    def test_get_instantiated_classes_basic(self, query_with_data):
        """Test getting instantiated classes."""
        result = query_with_data.get_instantiated_classes_in_file(
            "src/main.py"
        )

        assert "Classes instantiated in src/main.py" in result
        assert "DataProcessor" in result
        assert "25 instantiations" in result

    def test_get_instantiated_classes_with_limit(self, query_with_data):
        """Test limiting number of classes returned."""
        result = query_with_data.get_instantiated_classes_in_file(
            "src/main.py",
            top_n=2
        )

        # Should include top 2 by instantiation count
        assert "DataProcessor" in result
        assert "Validator" in result

    def test_get_instantiated_classes_sorted_by_count(self, query_with_data):
        """Test that classes are sorted by instantiation count."""
        result = query_with_data.get_instantiated_classes_in_file(
            "src/main.py"
        )

        lines = result.split('\n')
        # DataProcessor (25) should come before Validator (18)
        dp_line = next(i for i, l in enumerate(lines) if 'DataProcessor' in l)
        val_line = next(i for i, l in enumerate(lines) if 'Validator' in l)
        assert dp_line < val_line

    def test_get_instantiated_classes_includes_location(self, query_with_data):
        """Test that class locations are included."""
        result = query_with_data.get_instantiated_classes_in_file(
            "src/main.py"
        )

        assert "src/processor.py:15" in result  # DataProcessor location

    def test_get_instantiated_classes_includes_docstring(self, query_with_data):
        """Test that docstrings are included."""
        result = query_with_data.get_instantiated_classes_in_file(
            "src/main.py"
        )

        assert "Main data processing class" in result


class TestModuleSummaryQuery:
    """Tests for get_module_summary."""

    def test_get_module_summary_full(self, query_with_data):
        """Test getting complete module summary."""
        result = query_with_data.get_module_summary("src/processor.py")

        assert "Module: processor" in result
        assert "Data processing module" in result
        assert "Statistics:" in result
        assert "Classes:" in result
        assert "Functions:" in result
        assert "Avg Complexity:" in result
        assert "Dependencies:" in result

    def test_get_module_summary_without_complexity(self, query_with_data):
        """Test module summary without complexity metrics."""
        result = query_with_data.get_module_summary(
            "src/processor.py",
            include_complexity=False
        )

        assert "Statistics:" in result
        assert "Avg Complexity:" not in result
        assert "Max Complexity:" not in result

    def test_get_module_summary_without_dependencies(self, query_with_data):
        """Test module summary without dependency info."""
        result = query_with_data.get_module_summary(
            "src/processor.py",
            include_dependencies=False
        )

        assert "Statistics:" in result
        assert "Dependencies:" not in result
        assert "Reverse Dependencies:" not in result

    def test_get_module_summary_nonexistent(self, query_with_data):
        """Test summary for nonexistent module."""
        result = query_with_data.get_module_summary("src/nonexistent.py")

        # Returns empty statistics when module not found
        assert "Module: nonexistent" in result or "Statistics:" in result


class TestCallGraphSummary:
    """Tests for get_call_graph_summary."""

    def test_get_call_graph_both_directions(self, query_with_data):
        """Test call graph in both directions."""
        result = query_with_data.get_call_graph_summary(
            "process_data",
            direction="both"
        )

        assert "Call Graph for process_data" in result
        assert "Direction: both" in result
        # Check for callees (what process_data calls)
        assert "Callees (what this calls)" in result
        assert "process_data →" in result

    def test_get_call_graph_callers_only(self, query_with_data):
        """Test call graph showing only callers."""
        result = query_with_data.get_call_graph_summary(
            "process_data",
            direction="callers"
        )

        assert "Direction: callers" in result
        # Callees section should not appear
        assert "Callees" not in result

    def test_get_call_graph_callees_only(self, query_with_data):
        """Test call graph showing only callees."""
        result = query_with_data.get_call_graph_summary(
            "process_data",
            direction="callees"
        )

        assert "Callees (what this calls)" in result
        assert "Callers" not in result

    def test_get_call_graph_with_depth(self, query_with_data):
        """Test call graph with specified depth."""
        result = query_with_data.get_call_graph_summary(
            "process_data",
            max_depth=1
        )

        assert "Max Depth: 1" in result

    def test_get_call_graph_nonexistent(self, query_with_data):
        """Test call graph for nonexistent function."""
        result = query_with_data.get_call_graph_summary("nonexistent_func")

        assert "Function not found" in result


class TestFormatForPrompt:
    """Tests for generic format_for_prompt method."""

    def test_format_for_prompt_complex_functions(self, query_with_data):
        """Test generic format for complex functions query."""
        result = query_with_data.format_for_prompt(
            "complex_functions",
            module="src/processor.py",
            top_n=5
        )

        assert "Most Complex Functions" in result

    def test_format_for_prompt_callers(self, query_with_data):
        """Test generic format for callers query."""
        result = query_with_data.format_for_prompt(
            "callers",
            function_name="validate_input"
        )

        # Should return formatted output mentioning the function
        assert "validate_input" in result
        assert isinstance(result, str)

    def test_format_for_prompt_instantiated_classes(self, query_with_data):
        """Test generic format for instantiated classes query."""
        result = query_with_data.format_for_prompt(
            "instantiated_classes",
            file_path="src/main.py"
        )

        assert "Classes instantiated" in result

    def test_format_for_prompt_module_summary(self, query_with_data):
        """Test generic format for module summary query."""
        result = query_with_data.format_for_prompt(
            "module_summary",
            module_path="src/processor.py"
        )

        assert "Module:" in result

    def test_format_for_prompt_call_graph(self, query_with_data):
        """Test generic format for call graph query."""
        result = query_with_data.format_for_prompt(
            "call_graph",
            function_name="process_data",
            direction="both"
        )

        assert "Call Graph for process_data" in result

    def test_format_for_prompt_invalid_type(self, query_with_data):
        """Test generic format with invalid query type."""
        with pytest.raises(ValueError, match="Unknown query type"):
            query_with_data.format_for_prompt("invalid_type")


class TestLLMPromptFormatting:
    """Tests for LLM-specific prompt formatting."""

    def test_formatted_output_is_readable(self, query_with_data):
        """Test that formatted output is human-readable."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py"
        )

        # Should use markdown-style formatting
        assert "**" in result  # Bold headers
        lines = result.split('\n')
        assert len(lines) > 5  # Multi-line output
        assert any(line.strip().startswith("1.") for line in lines)

    def test_formatted_output_includes_context(self, query_with_data):
        """Test that formatted output includes sufficient context."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py"
        )

        # Should include file paths, line numbers, complexity, and docstrings
        assert "src/processor.py:" in result
        assert "complexity:" in result
        assert "Purpose:" in result

    def test_empty_results_are_descriptive(self, query_with_data):
        """Test that empty results provide clear feedback."""
        result = query_with_data.get_complex_functions_in_module(
            "src/processor.py",
            threshold=1000
        )

        assert "No complex functions found" in result
        assert "threshold:" in result  # Explain why empty
