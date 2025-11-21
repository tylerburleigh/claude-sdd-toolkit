"""
A/B Testing Framework for Documentation Generation with Analysis Insights.

This module provides a framework for comparing documentation generated with and
without codebase analysis insights to evaluate the impact of analysis data on
documentation quality.

Key capabilities:
- Generate documentation with both control (no insights) and treatment (with insights)
- Define evaluation rubrics for documentation quality
- Measure: accuracy of architectural patterns, completeness, and relevance
- Collect structured results for comparison
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class TestVariant(Enum):
    """A/B test variants."""
    CONTROL = "control"  # Without analysis insights
    TREATMENT = "treatment"  # With analysis insights


@dataclass
class EvaluationMetrics:
    """
    Metrics for evaluating documentation quality.

    Each metric is scored on a scale of 1-5:
    - 1: Poor
    - 2: Below Average
    - 3: Average
    - 4: Good
    - 5: Excellent
    """

    # Accuracy metrics
    architecture_patterns_accuracy: Optional[int] = None  # 1-5: Correctness of identified patterns
    technology_stack_accuracy: Optional[int] = None  # 1-5: Accuracy of tech stack details
    component_relationships_accuracy: Optional[int] = None  # 1-5: Accuracy of component interactions

    # Completeness metrics
    coverage_score: Optional[int] = None  # 1-5: How much of the codebase is covered
    detail_depth: Optional[int] = None  # 1-5: Level of detail provided
    missing_critical_info: Optional[int] = None  # 1-5: (inverse) Amount of critical info missing

    # Relevance metrics
    context_relevance: Optional[int] = None  # 1-5: How relevant insights are to the codebase
    actionability: Optional[int] = None  # 1-5: How actionable the documentation is
    developer_usefulness: Optional[int] = None  # 1-5: Perceived usefulness for developers

    # Meta metrics
    hallucination_count: int = 0  # Number of incorrect/fabricated details
    redundancy_score: Optional[int] = None  # 1-5: (inverse) Amount of redundant information

    # Composite scores (computed)
    accuracy_composite: Optional[float] = None
    completeness_composite: Optional[float] = None
    relevance_composite: Optional[float] = None
    overall_score: Optional[float] = None

    def compute_composites(self) -> None:
        """Compute composite scores from individual metrics."""
        # Accuracy composite (average of accuracy metrics)
        accuracy_metrics = [
            self.architecture_patterns_accuracy,
            self.technology_stack_accuracy,
            self.component_relationships_accuracy
        ]
        accuracy_valid = [m for m in accuracy_metrics if m is not None]
        if accuracy_valid:
            self.accuracy_composite = sum(accuracy_valid) / len(accuracy_valid)

        # Completeness composite (average of completeness metrics)
        completeness_metrics = [
            self.coverage_score,
            self.detail_depth,
            self.missing_critical_info
        ]
        completeness_valid = [m for m in completeness_metrics if m is not None]
        if completeness_valid:
            self.completeness_composite = sum(completeness_valid) / len(completeness_valid)

        # Relevance composite (average of relevance metrics)
        relevance_metrics = [
            self.context_relevance,
            self.actionability,
            self.developer_usefulness
        ]
        relevance_valid = [m for m in relevance_metrics if m is not None]
        if relevance_valid:
            self.relevance_composite = sum(relevance_valid) / len(relevance_valid)

        # Overall score (average of all composites)
        composites = [
            self.accuracy_composite,
            self.completeness_composite,
            self.relevance_composite
        ]
        valid_composites = [c for c in composites if c is not None]
        if valid_composites:
            # Apply hallucination penalty (subtract 0.1 per hallucination, capped at -2.0)
            hallucination_penalty = min(self.hallucination_count * 0.1, 2.0)
            self.overall_score = max(1.0, sum(valid_composites) / len(valid_composites) - hallucination_penalty)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'accuracy': {
                'architecture_patterns': self.architecture_patterns_accuracy,
                'technology_stack': self.technology_stack_accuracy,
                'component_relationships': self.component_relationships_accuracy,
                'composite': self.accuracy_composite
            },
            'completeness': {
                'coverage': self.coverage_score,
                'detail_depth': self.detail_depth,
                'missing_critical_info': self.missing_critical_info,
                'composite': self.completeness_composite
            },
            'relevance': {
                'context_relevance': self.context_relevance,
                'actionability': self.actionability,
                'developer_usefulness': self.developer_usefulness,
                'composite': self.relevance_composite
            },
            'meta': {
                'hallucination_count': self.hallucination_count,
                'redundancy_score': self.redundancy_score
            },
            'overall_score': self.overall_score
        }


@dataclass
class ABTestResult:
    """Results from a single A/B test run."""

    test_id: str
    timestamp: str
    generator_type: str  # 'architecture', 'component', 'overview'

    # Generated documentation
    control_output: str  # Documentation without insights
    treatment_output: str  # Documentation with insights

    # Evaluation metrics
    control_metrics: EvaluationMetrics
    treatment_metrics: EvaluationMetrics

    # Test metadata
    codebase_size: Optional[int] = None
    analysis_data_size_kb: Optional[float] = None
    control_generation_time_s: Optional[float] = None
    treatment_generation_time_s: Optional[float] = None

    # Winner determination
    winner: Optional[TestVariant] = None
    improvement_percentage: Optional[float] = None

    def determine_winner(self) -> None:
        """
        Determine which variant performed better based on overall scores.

        Sets winner and improvement_percentage attributes.
        """
        if self.control_metrics.overall_score is None or self.treatment_metrics.overall_score is None:
            return

        control_score = self.control_metrics.overall_score
        treatment_score = self.treatment_metrics.overall_score

        if treatment_score > control_score:
            self.winner = TestVariant.TREATMENT
            self.improvement_percentage = ((treatment_score - control_score) / control_score) * 100
        elif control_score > treatment_score:
            self.winner = TestVariant.CONTROL
            self.improvement_percentage = ((control_score - treatment_score) / treatment_score) * 100
        else:
            self.winner = None
            self.improvement_percentage = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'test_id': self.test_id,
            'timestamp': self.timestamp,
            'generator_type': self.generator_type,
            'control_metrics': self.control_metrics.to_dict(),
            'treatment_metrics': self.treatment_metrics.to_dict(),
            'metadata': {
                'codebase_size': self.codebase_size,
                'analysis_data_size_kb': self.analysis_data_size_kb,
                'control_generation_time_s': self.control_generation_time_s,
                'treatment_generation_time_s': self.treatment_generation_time_s
            },
            'winner': self.winner.value if self.winner else None,
            'improvement_percentage': self.improvement_percentage
        }


@dataclass
class EvaluationRubric:
    """
    Rubric for evaluating documentation quality.

    Provides structured guidance for scoring each metric consistently.
    """

    name: str
    description: str
    criteria: Dict[str, Dict[int, str]] = field(default_factory=dict)

    @staticmethod
    def default_rubric() -> 'EvaluationRubric':
        """
        Create default evaluation rubric for documentation quality.

        Returns:
            EvaluationRubric with comprehensive criteria
        """
        rubric = EvaluationRubric(
            name="Documentation Quality Rubric",
            description="Comprehensive rubric for evaluating AI-generated documentation quality"
        )

        # Architecture Patterns Accuracy
        rubric.criteria['architecture_patterns_accuracy'] = {
            1: "Major architectural patterns misidentified or missing",
            2: "Some patterns identified but with significant errors",
            3: "Basic patterns identified correctly, some details missing",
            4: "Most patterns identified accurately with good detail",
            5: "All major patterns identified with excellent accuracy"
        }

        # Technology Stack Accuracy
        rubric.criteria['technology_stack_accuracy'] = {
            1: "Major technologies misidentified or missing",
            2: "Some technologies identified but with errors",
            3: "Core technologies identified correctly",
            4: "Detailed technology identification with minor gaps",
            5: "Comprehensive and accurate technology analysis"
        }

        # Component Relationships Accuracy
        rubric.criteria['component_relationships_accuracy'] = {
            1: "Component relationships incorrectly described",
            2: "Some relationships identified but with errors",
            3: "Basic relationships described correctly",
            4: "Most relationships accurately described with detail",
            5: "Comprehensive and accurate relationship mapping"
        }

        # Coverage Score
        rubric.criteria['coverage_score'] = {
            1: "Less than 20% of codebase covered",
            2: "20-40% of codebase covered",
            3: "40-60% of codebase covered",
            4: "60-80% of codebase covered",
            5: "80%+ of codebase covered comprehensively"
        }

        # Detail Depth
        rubric.criteria['detail_depth'] = {
            1: "Superficial, lacks meaningful details",
            2: "Basic details, missing important context",
            3: "Adequate details for understanding basics",
            4: "Good detail level, helpful for developers",
            5: "Excellent depth with actionable insights"
        }

        # Missing Critical Info (inverse scoring)
        rubric.criteria['missing_critical_info'] = {
            1: "Many critical details missing",
            2: "Some critical details missing",
            3: "Most critical info present, minor gaps",
            4: "Nearly complete, very minor gaps",
            5: "All critical information present"
        }

        # Context Relevance
        rubric.criteria['context_relevance'] = {
            1: "Information not relevant to codebase",
            2: "Some relevant info, much is generic",
            3: "Mostly relevant with some generic content",
            4: "Highly relevant with minimal generic content",
            5: "Perfectly tailored to this specific codebase"
        }

        # Actionability
        rubric.criteria['actionability'] = {
            1: "No actionable insights or guidance",
            2: "Few actionable points, mostly descriptive",
            3: "Some actionable insights present",
            4: "Many actionable insights and recommendations",
            5: "Highly actionable with clear next steps"
        }

        # Developer Usefulness
        rubric.criteria['developer_usefulness'] = {
            1: "Would not help developers understand codebase",
            2: "Minimally helpful for developers",
            3: "Moderately helpful for understanding",
            4: "Very helpful for onboarding and development",
            5: "Extremely valuable reference for all developers"
        }

        # Redundancy Score (inverse scoring)
        rubric.criteria['redundancy_score'] = {
            1: "Highly redundant with repeated information",
            2: "Noticeable redundancy throughout",
            3: "Some redundancy, mostly concise",
            4: "Minimal redundancy, well-organized",
            5: "No redundancy, perfectly concise"
        }

        return rubric

    def to_dict(self) -> Dict[str, Any]:
        """Convert rubric to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'criteria': self.criteria
        }


class ABTestFramework:
    """
    Framework for running A/B tests on documentation generation.

    Coordinates test execution, documentation generation, and result collection.
    """

    def __init__(self, results_dir: Optional[Path] = None):
        """
        Initialize A/B test framework.

        Args:
            results_dir: Directory to store test results (defaults to ./ab_test_results)
        """
        self.results_dir = results_dir or Path('./ab_test_results')
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.rubric = EvaluationRubric.default_rubric()

    def run_test(
        self,
        generator_type: str,
        generator_fn: Callable[[Optional[Path]], tuple[bool, str]],
        analysis_data_path: Optional[Path] = None,
        test_id: Optional[str] = None
    ) -> ABTestResult:
        """
        Run A/B test comparing documentation generation with and without insights.

        Args:
            generator_type: Type of generator ('architecture', 'component', 'overview')
            generator_fn: Function that generates documentation
                         Signature: (analysis_data_path: Optional[Path]) -> tuple[success, output]
            analysis_data_path: Path to codebase.json (for treatment variant)
            test_id: Optional custom test ID (auto-generated if None)

        Returns:
            ABTestResult with both variants and initial metrics structure
        """
        import time

        # Generate test ID
        if test_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_id = f"{generator_type}_{timestamp}"

        # Run control variant (without insights)
        print(f"Running control variant (without insights)...")
        control_start = time.time()
        control_success, control_output = generator_fn(None)
        control_time = time.time() - control_start

        if not control_success:
            raise RuntimeError(f"Control variant generation failed: {control_output}")

        # Run treatment variant (with insights)
        print(f"Running treatment variant (with insights)...")
        treatment_start = time.time()
        treatment_success, treatment_output = generator_fn(analysis_data_path)
        treatment_time = time.time() - treatment_start

        if not treatment_success:
            raise RuntimeError(f"Treatment variant generation failed: {treatment_output}")

        # Gather metadata
        codebase_size = None
        analysis_size_kb = None
        if analysis_data_path and analysis_data_path.exists():
            analysis_size_kb = analysis_data_path.stat().st_size / 1024

            # Try to extract codebase size from analysis data
            try:
                with open(analysis_data_path, 'r') as f:
                    analysis_data = json.load(f)
                    # Count unique files
                    files = set()
                    for func in analysis_data.get('functions', []):
                        if 'file' in func:
                            files.add(func['file'])
                    for cls in analysis_data.get('classes', []):
                        if 'file' in cls:
                            files.add(cls['file'])
                    codebase_size = len(files)
            except Exception:
                pass

        # Create result object
        result = ABTestResult(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            generator_type=generator_type,
            control_output=control_output,
            treatment_output=treatment_output,
            control_metrics=EvaluationMetrics(),
            treatment_metrics=EvaluationMetrics(),
            codebase_size=codebase_size,
            analysis_data_size_kb=analysis_size_kb,
            control_generation_time_s=control_time,
            treatment_generation_time_s=treatment_time
        )

        return result

    def save_result(self, result: ABTestResult, filename: Optional[str] = None) -> Path:
        """
        Save test result to disk.

        Args:
            result: ABTestResult to save
            filename: Optional custom filename (defaults to test_id.json)

        Returns:
            Path to saved result file
        """
        if filename is None:
            filename = f"{result.test_id}.json"

        result_path = self.results_dir / filename

        # Save result as JSON
        with open(result_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        return result_path

    def load_result(self, test_id: str) -> Dict[str, Any]:
        """
        Load test result from disk.

        Args:
            test_id: Test ID to load

        Returns:
            Dictionary with test result data
        """
        result_path = self.results_dir / f"{test_id}.json"

        if not result_path.exists():
            raise FileNotFoundError(f"Test result not found: {result_path}")

        with open(result_path, 'r') as f:
            return json.load(f)

    def generate_report(self, test_ids: List[str]) -> str:
        """
        Generate summary report across multiple test results.

        Args:
            test_ids: List of test IDs to include in report

        Returns:
            Formatted markdown report
        """
        results = [self.load_result(tid) for tid in test_ids]

        report_parts = []
        report_parts.append("# A/B Testing Report: Documentation with Analysis Insights")
        report_parts.append("")
        report_parts.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append(f"**Tests Analyzed:** {len(results)}")
        report_parts.append("")

        # Summary statistics
        treatment_wins = sum(1 for r in results if r.get('winner') == 'treatment')
        control_wins = sum(1 for r in results if r.get('winner') == 'control')
        ties = sum(1 for r in results if r.get('winner') is None)

        report_parts.append("## Summary")
        report_parts.append("")
        report_parts.append(f"- **Treatment Wins:** {treatment_wins} ({treatment_wins/len(results)*100:.1f}%)")
        report_parts.append(f"- **Control Wins:** {control_wins} ({control_wins/len(results)*100:.1f}%)")
        report_parts.append(f"- **Ties:** {ties} ({ties/len(results)*100:.1f}%)")
        report_parts.append("")

        # Average improvements
        improvements = [r.get('improvement_percentage', 0) for r in results if r.get('winner') == 'treatment']
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            report_parts.append(f"**Average Treatment Improvement:** {avg_improvement:.1f}%")
            report_parts.append("")

        # Detailed results table
        report_parts.append("## Detailed Results")
        report_parts.append("")
        report_parts.append("| Test ID | Generator | Winner | Improvement | Control Score | Treatment Score |")
        report_parts.append("| --- | --- | --- | --- | --- | --- |")

        for r in results:
            test_id = r['test_id']
            generator = r['generator_type']
            winner = r.get('winner', 'N/A')
            improvement = r.get('improvement_percentage', 0)
            control_score = r['control_metrics']['overall_score']
            treatment_score = r['treatment_metrics']['overall_score']

            report_parts.append(
                f"| {test_id} | {generator} | {winner} | {improvement:.1f}% | "
                f"{control_score:.2f} | {treatment_score:.2f} |"
            )

        report_parts.append("")

        # Metric breakdown
        report_parts.append("## Metric Breakdown")
        report_parts.append("")

        for metric_category in ['accuracy', 'completeness', 'relevance']:
            # Calculate averages
            control_scores = []
            treatment_scores = []

            for r in results:
                control_comp = r['control_metrics'][metric_category].get('composite')
                treatment_comp = r['treatment_metrics'][metric_category].get('composite')

                if control_comp is not None:
                    control_scores.append(control_comp)
                if treatment_comp is not None:
                    treatment_scores.append(treatment_comp)

            if control_scores and treatment_scores:
                avg_control = sum(control_scores) / len(control_scores)
                avg_treatment = sum(treatment_scores) / len(treatment_scores)

                report_parts.append(f"### {metric_category.title()}")
                report_parts.append("")
                report_parts.append(f"- **Control Average:** {avg_control:.2f}")
                report_parts.append(f"- **Treatment Average:** {avg_treatment:.2f}")
                report_parts.append(f"- **Difference:** {(avg_treatment - avg_control):.2f}")
                report_parts.append("")

        return "\n".join(report_parts)

    def export_rubric(self, output_path: Optional[Path] = None) -> Path:
        """
        Export evaluation rubric to JSON file.

        Args:
            output_path: Optional custom path (defaults to rubric.json in results_dir)

        Returns:
            Path to exported rubric file
        """
        if output_path is None:
            output_path = self.results_dir / 'rubric.json'

        with open(output_path, 'w') as f:
            json.dump(self.rubric.to_dict(), f, indent=2)

        return output_path


# Example usage and test helpers
def create_example_test() -> ABTestResult:
    """
    Create an example test result for documentation purposes.

    Returns:
        Example ABTestResult with sample data
    """
    control_metrics = EvaluationMetrics(
        architecture_patterns_accuracy=3,
        technology_stack_accuracy=3,
        component_relationships_accuracy=2,
        coverage_score=3,
        detail_depth=2,
        missing_critical_info=2,
        context_relevance=2,
        actionability=2,
        developer_usefulness=3,
        hallucination_count=2,
        redundancy_score=3
    )
    control_metrics.compute_composites()

    treatment_metrics = EvaluationMetrics(
        architecture_patterns_accuracy=5,
        technology_stack_accuracy=4,
        component_relationships_accuracy=4,
        coverage_score=4,
        detail_depth=5,
        missing_critical_info=4,
        context_relevance=5,
        actionability=4,
        developer_usefulness=5,
        hallucination_count=0,
        redundancy_score=4
    )
    treatment_metrics.compute_composites()

    result = ABTestResult(
        test_id="example_architecture_20251121",
        timestamp=datetime.now().isoformat(),
        generator_type="architecture",
        control_output="# Example Control Output\n\nGeneric architecture documentation...",
        treatment_output="# Example Treatment Output\n\nEnriched with specific insights...",
        control_metrics=control_metrics,
        treatment_metrics=treatment_metrics,
        codebase_size=150,
        analysis_data_size_kb=245.5,
        control_generation_time_s=12.3,
        treatment_generation_time_s=15.7
    )

    result.determine_winner()
    return result
