"""
Tests for A/B Testing Framework.

Validates the framework for comparing documentation generation with and without
codebase analysis insights.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from claude_skills.llm_doc_gen.ab_testing import (
    TestVariant,
    EvaluationMetrics,
    ABTestResult,
    EvaluationRubric,
    ABTestFramework,
    create_example_test
)


class TestEvaluationMetrics:
    """Test EvaluationMetrics data structure and computations."""

    def test_metrics_initialization(self):
        """Test that metrics initialize with None values."""
        metrics = EvaluationMetrics()

        assert metrics.architecture_patterns_accuracy is None
        assert metrics.coverage_score is None
        assert metrics.hallucination_count == 0
        assert metrics.overall_score is None

    def test_compute_composites_all_metrics(self):
        """Test composite computation with all metrics set."""
        metrics = EvaluationMetrics(
            architecture_patterns_accuracy=4,
            technology_stack_accuracy=5,
            component_relationships_accuracy=4,
            coverage_score=3,
            detail_depth=4,
            missing_critical_info=4,
            context_relevance=5,
            actionability=4,
            developer_usefulness=5,
            hallucination_count=0,
            redundancy_score=4
        )

        metrics.compute_composites()

        # Check accuracy composite (4 + 5 + 4) / 3 = 4.33
        assert metrics.accuracy_composite == pytest.approx(4.33, rel=0.01)

        # Check completeness composite (3 + 4 + 4) / 3 = 3.67
        assert metrics.completeness_composite == pytest.approx(3.67, rel=0.01)

        # Check relevance composite (5 + 4 + 5) / 3 = 4.67
        assert metrics.relevance_composite == pytest.approx(4.67, rel=0.01)

        # Check overall score (average of composites)
        expected_overall = (4.33 + 3.67 + 4.67) / 3
        assert metrics.overall_score == pytest.approx(expected_overall, rel=0.01)

    def test_compute_composites_with_hallucinations(self):
        """Test that hallucinations apply penalty to overall score."""
        metrics = EvaluationMetrics(
            architecture_patterns_accuracy=5,
            technology_stack_accuracy=5,
            component_relationships_accuracy=5,
            coverage_score=5,
            detail_depth=5,
            missing_critical_info=5,
            context_relevance=5,
            actionability=5,
            developer_usefulness=5,
            hallucination_count=3,  # 3 hallucinations = -0.3 penalty
            redundancy_score=5
        )

        metrics.compute_composites()

        # All scores are 5, so composites should be 5.0
        assert metrics.accuracy_composite == 5.0
        assert metrics.completeness_composite == 5.0
        assert metrics.relevance_composite == 5.0

        # Overall should be 5.0 - 0.3 = 4.7
        assert metrics.overall_score == pytest.approx(4.7, rel=0.01)

    def test_compute_composites_partial_metrics(self):
        """Test composite computation with only some metrics set."""
        metrics = EvaluationMetrics(
            architecture_patterns_accuracy=4,
            technology_stack_accuracy=5,
            # component_relationships_accuracy not set
            coverage_score=3,
            # Other metrics not set
        )

        metrics.compute_composites()

        # Accuracy composite from 2 values: (4 + 5) / 2 = 4.5
        assert metrics.accuracy_composite == 4.5

        # Completeness composite from 1 value: 3
        assert metrics.completeness_composite == 3.0

        # Relevance composite should be None (no metrics set)
        assert metrics.relevance_composite is None

        # Overall score from 2 composites: (4.5 + 3.0) / 2 = 3.75
        assert metrics.overall_score == pytest.approx(3.75, rel=0.01)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = EvaluationMetrics(
            architecture_patterns_accuracy=4,
            coverage_score=3,
            hallucination_count=1
        )
        metrics.compute_composites()

        result = metrics.to_dict()

        assert 'accuracy' in result
        assert 'completeness' in result
        assert 'relevance' in result
        assert 'meta' in result
        assert result['accuracy']['architecture_patterns'] == 4
        assert result['completeness']['coverage'] == 3
        assert result['meta']['hallucination_count'] == 1
        assert 'overall_score' in result


class TestABTestResult:
    """Test ABTestResult data structure and winner determination."""

    def test_result_initialization(self):
        """Test basic result initialization."""
        result = ABTestResult(
            test_id="test_001",
            timestamp="2025-11-21T10:00:00",
            generator_type="architecture",
            control_output="Control output",
            treatment_output="Treatment output",
            control_metrics=EvaluationMetrics(),
            treatment_metrics=EvaluationMetrics()
        )

        assert result.test_id == "test_001"
        assert result.generator_type == "architecture"
        assert result.winner is None

    def test_determine_winner_treatment_wins(self):
        """Test winner determination when treatment is better."""
        control_metrics = EvaluationMetrics(
            architecture_patterns_accuracy=3,
            technology_stack_accuracy=3,
            component_relationships_accuracy=3,
            coverage_score=3,
            detail_depth=3,
            missing_critical_info=3,
            context_relevance=3,
            actionability=3,
            developer_usefulness=3
        )
        control_metrics.compute_composites()

        treatment_metrics = EvaluationMetrics(
            architecture_patterns_accuracy=5,
            technology_stack_accuracy=5,
            component_relationships_accuracy=5,
            coverage_score=5,
            detail_depth=5,
            missing_critical_info=5,
            context_relevance=5,
            actionability=5,
            developer_usefulness=5
        )
        treatment_metrics.compute_composites()

        result = ABTestResult(
            test_id="test_001",
            timestamp="2025-11-21",
            generator_type="architecture",
            control_output="",
            treatment_output="",
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics
        )

        result.determine_winner()

        assert result.winner == TestVariant.TREATMENT
        assert result.improvement_percentage > 0

    def test_determine_winner_control_wins(self):
        """Test winner determination when control is better."""
        control_metrics = EvaluationMetrics(
            architecture_patterns_accuracy=5,
            technology_stack_accuracy=5,
            component_relationships_accuracy=5,
            coverage_score=5,
            detail_depth=5,
            missing_critical_info=5,
            context_relevance=5,
            actionability=5,
            developer_usefulness=5
        )
        control_metrics.compute_composites()

        treatment_metrics = EvaluationMetrics(
            architecture_patterns_accuracy=3,
            technology_stack_accuracy=3,
            component_relationships_accuracy=3,
            coverage_score=3,
            detail_depth=3,
            missing_critical_info=3,
            context_relevance=3,
            actionability=3,
            developer_usefulness=3
        )
        treatment_metrics.compute_composites()

        result = ABTestResult(
            test_id="test_001",
            timestamp="2025-11-21",
            generator_type="architecture",
            control_output="",
            treatment_output="",
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics
        )

        result.determine_winner()

        assert result.winner == TestVariant.CONTROL
        assert result.improvement_percentage > 0

    def test_determine_winner_tie(self):
        """Test winner determination when scores are equal."""
        metrics = EvaluationMetrics(
            architecture_patterns_accuracy=4,
            technology_stack_accuracy=4,
            component_relationships_accuracy=4,
            coverage_score=4,
            detail_depth=4,
            missing_critical_info=4,
            context_relevance=4,
            actionability=4,
            developer_usefulness=4
        )
        metrics.compute_composites()

        result = ABTestResult(
            test_id="test_001",
            timestamp="2025-11-21",
            generator_type="architecture",
            control_output="",
            treatment_output="",
            control_metrics=metrics,
            treatment_metrics=metrics
        )

        result.determine_winner()

        assert result.winner is None
        assert result.improvement_percentage == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        control_metrics = EvaluationMetrics(architecture_patterns_accuracy=3)
        control_metrics.compute_composites()

        treatment_metrics = EvaluationMetrics(architecture_patterns_accuracy=5)
        treatment_metrics.compute_composites()

        result = ABTestResult(
            test_id="test_001",
            timestamp="2025-11-21",
            generator_type="architecture",
            control_output="Control",
            treatment_output="Treatment",
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics,
            codebase_size=100
        )
        result.determine_winner()

        result_dict = result.to_dict()

        assert result_dict['test_id'] == "test_001"
        assert result_dict['generator_type'] == "architecture"
        assert 'control_metrics' in result_dict
        assert 'treatment_metrics' in result_dict
        assert 'metadata' in result_dict
        assert result_dict['metadata']['codebase_size'] == 100
        assert 'winner' in result_dict


class TestEvaluationRubric:
    """Test EvaluationRubric structure and default rubric."""

    def test_default_rubric_structure(self):
        """Test that default rubric has all required criteria."""
        rubric = EvaluationRubric.default_rubric()

        assert rubric.name == "Documentation Quality Rubric"

        # Check key metrics exist
        assert 'architecture_patterns_accuracy' in rubric.criteria
        assert 'coverage_score' in rubric.criteria
        assert 'context_relevance' in rubric.criteria

        # Check that each criterion has 5 levels
        for criterion, levels in rubric.criteria.items():
            assert len(levels) == 5
            assert all(level in levels for level in [1, 2, 3, 4, 5])

    def test_rubric_to_dict(self):
        """Test rubric serialization."""
        rubric = EvaluationRubric.default_rubric()
        rubric_dict = rubric.to_dict()

        assert 'name' in rubric_dict
        assert 'description' in rubric_dict
        assert 'criteria' in rubric_dict
        assert len(rubric_dict['criteria']) > 0


class TestABTestFramework:
    """Test ABTestFramework orchestration and result management."""

    def test_framework_initialization(self):
        """Test framework initializes with results directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            assert framework.results_dir == results_dir
            assert results_dir.exists()
            assert framework.rubric is not None

    def test_run_test_success(self):
        """Test successful test execution with mock generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Mock generator function
            def mock_generator(analysis_path):
                if analysis_path is None:
                    return True, "Control output without insights"
                else:
                    return True, "Treatment output with insights"

            # Create dummy analysis path to trigger treatment variant
            analysis_path = Path(tmpdir) / 'dummy_analysis.json'
            analysis_path.write_text('{}')

            # Run test
            result = framework.run_test(
                generator_type='architecture',
                generator_fn=mock_generator,
                analysis_data_path=analysis_path,
                test_id='test_mock'
            )

            assert result.test_id == 'test_mock'
            assert result.generator_type == 'architecture'
            assert result.control_output == "Control output without insights"
            assert result.treatment_output == "Treatment output with insights"
            assert result.control_generation_time_s is not None
            assert result.treatment_generation_time_s is not None

    def test_run_test_with_analysis_data(self):
        """Test test execution with analysis data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Create mock analysis data
            analysis_path = Path(tmpdir) / 'codebase.json'
            analysis_data = {
                'functions': [
                    {'name': 'func1', 'file': 'file1.py'},
                    {'name': 'func2', 'file': 'file2.py'}
                ],
                'classes': []
            }
            with open(analysis_path, 'w') as f:
                json.dump(analysis_data, f)

            def mock_generator(analysis_path):
                return True, f"Generated with analysis: {analysis_path is not None}"

            result = framework.run_test(
                generator_type='component',
                generator_fn=mock_generator,
                analysis_data_path=analysis_path
            )

            assert result.codebase_size == 2  # 2 unique files
            assert result.analysis_data_size_kb is not None
            assert result.analysis_data_size_kb > 0

    def test_save_and_load_result(self):
        """Test saving and loading test results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Create example result
            example = create_example_test()

            # Save result
            saved_path = framework.save_result(example)
            assert saved_path.exists()

            # Load result
            loaded = framework.load_result(example.test_id)
            assert loaded['test_id'] == example.test_id
            assert loaded['generator_type'] == example.generator_type

    def test_generate_report(self):
        """Test report generation from multiple tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Create and save multiple test results
            test_ids = []
            for i in range(3):
                result = create_example_test()
                result.test_id = f"test_{i}"
                framework.save_result(result)
                test_ids.append(result.test_id)

            # Generate report
            report = framework.generate_report(test_ids)

            assert "A/B Testing Report" in report
            assert "Summary" in report
            assert "Detailed Results" in report
            assert "Metric Breakdown" in report
            assert all(tid in report for tid in test_ids)

    def test_export_rubric(self):
        """Test rubric export to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Export rubric
            rubric_path = framework.export_rubric()

            assert rubric_path.exists()
            assert rubric_path.name == 'rubric.json'

            # Load and verify
            with open(rubric_path, 'r') as f:
                rubric_data = json.load(f)

            assert 'name' in rubric_data
            assert 'criteria' in rubric_data


class TestExampleGeneration:
    """Test example test creation."""

    def test_create_example_test(self):
        """Test that example test is properly configured."""
        example = create_example_test()

        assert example.test_id is not None
        assert example.generator_type == "architecture"
        assert example.control_output is not None
        assert example.treatment_output is not None
        assert example.control_metrics.overall_score is not None
        assert example.treatment_metrics.overall_score is not None
        assert example.winner is not None

        # Treatment should win in the example
        assert example.winner == TestVariant.TREATMENT


class TestIntegration:
    """Integration tests for full A/B testing workflow."""

    def test_full_workflow(self):
        """Test complete workflow from test run to report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            # Mock generator
            def mock_generator(analysis_path):
                if analysis_path:
                    return True, "Enhanced documentation with analysis insights"
                return True, "Basic documentation"

            # Run test
            result = framework.run_test(
                generator_type='architecture',
                generator_fn=mock_generator,
                test_id='integration_test'
            )

            # Manually score the results
            result.control_metrics.architecture_patterns_accuracy = 3
            result.control_metrics.technology_stack_accuracy = 3
            result.control_metrics.component_relationships_accuracy = 3
            result.control_metrics.coverage_score = 3
            result.control_metrics.detail_depth = 3
            result.control_metrics.missing_critical_info = 3
            result.control_metrics.context_relevance = 3
            result.control_metrics.actionability = 3
            result.control_metrics.developer_usefulness = 3
            result.control_metrics.compute_composites()

            result.treatment_metrics.architecture_patterns_accuracy = 5
            result.treatment_metrics.technology_stack_accuracy = 5
            result.treatment_metrics.component_relationships_accuracy = 5
            result.treatment_metrics.coverage_score = 4
            result.treatment_metrics.detail_depth = 5
            result.treatment_metrics.missing_critical_info = 4
            result.treatment_metrics.context_relevance = 5
            result.treatment_metrics.actionability = 5
            result.treatment_metrics.developer_usefulness = 5
            result.treatment_metrics.compute_composites()

            result.determine_winner()

            # Save result
            framework.save_result(result)

            # Generate report
            report = framework.generate_report(['integration_test'])

            # Verify report content
            assert 'integration_test' in report
            assert 'Treatment Wins' in report or 'Control Wins' in report
            assert result.winner.value in report

    def test_multiple_tests_aggregation(self):
        """Test aggregation of multiple test results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / 'results'
            framework = ABTestFramework(results_dir=results_dir)

            test_ids = []

            # Run multiple tests with varying results
            for i in range(5):
                result = create_example_test()
                result.test_id = f"multi_test_{i}"
                framework.save_result(result)
                test_ids.append(result.test_id)

            # Generate aggregate report
            report = framework.generate_report(test_ids)

            assert "**Tests Analyzed:** 5" in report
            assert "Summary" in report
            assert "Detailed Results" in report
