# A/B Testing Framework for Documentation Generation

## Overview

The A/B Testing Framework enables systematic evaluation of documentation quality improvements when using codebase analysis insights. It compares documentation generated **with** and **without** analysis data to measure the impact of codebase insights on documentation quality.

## Key Features

- **Dual Variant Testing**: Generate documentation both with (treatment) and without (control) analysis insights
- **Comprehensive Evaluation Rubric**: Score documentation across accuracy, completeness, and relevance dimensions
- **Structured Metrics**: 10+ metrics with 1-5 scoring scale for consistent evaluation
- **Automated Reporting**: Generate summary reports across multiple test runs
- **Result Persistence**: Save and load test results as JSON for later analysis

## Architecture

### Core Components

```
ABTestFramework
├── EvaluationMetrics - Individual quality metrics with composite scoring
├── ABTestResult - Single test run with both variants and evaluation
├── EvaluationRubric - Criteria definitions for consistent scoring
└── Result Management - Save, load, and aggregate test results
```

### Test Variants

- **Control**: Documentation generated WITHOUT analysis insights (baseline)
- **Treatment**: Documentation generated WITH analysis insights (experimental)

## Quick Start

### 1. Basic Test Execution

```python
from pathlib import Path
from claude_skills.llm_doc_gen.ab_testing import ABTestFramework

# Initialize framework
framework = ABTestFramework(results_dir=Path('./ab_test_results'))

# Define your documentation generator function
def my_generator(analysis_data_path):
    """
    Your generator function that produces documentation.

    Args:
        analysis_data_path: Path to codebase.json (None for control variant)

    Returns:
        tuple[bool, str]: (success, documentation_output)
    """
    # Your generation logic here
    if analysis_data_path:
        # Generate with insights
        return True, "Documentation with analysis insights..."
    else:
        # Generate without insights
        return True, "Basic documentation..."

# Run A/B test
result = framework.run_test(
    generator_type='architecture',  # or 'component', 'overview'
    generator_fn=my_generator,
    analysis_data_path=Path('./codebase.json')  # Optional
)

# Save result
framework.save_result(result)
```

### 2. Manual Evaluation

After generating both variants, manually evaluate using the rubric:

```python
# Score control variant (1-5 scale for each metric)
result.control_metrics.architecture_patterns_accuracy = 3
result.control_metrics.technology_stack_accuracy = 3
result.control_metrics.component_relationships_accuracy = 2
result.control_metrics.coverage_score = 3
result.control_metrics.detail_depth = 2
result.control_metrics.missing_critical_info = 2
result.control_metrics.context_relevance = 2
result.control_metrics.actionability = 2
result.control_metrics.developer_usefulness = 3
result.control_metrics.hallucination_count = 2
result.control_metrics.redundancy_score = 3

# Compute composite scores
result.control_metrics.compute_composites()

# Score treatment variant
result.treatment_metrics.architecture_patterns_accuracy = 5
result.treatment_metrics.technology_stack_accuracy = 4
result.treatment_metrics.component_relationships_accuracy = 4
result.treatment_metrics.coverage_score = 4
result.treatment_metrics.detail_depth = 5
result.treatment_metrics.missing_critical_info = 4
result.treatment_metrics.context_relevance = 5
result.treatment_metrics.actionability = 4
result.treatment_metrics.developer_usefulness = 5
result.treatment_metrics.hallucination_count = 0
result.treatment_metrics.redundancy_score = 4

# Compute composite scores
result.treatment_metrics.compute_composites()

# Determine winner
result.determine_winner()

print(f"Winner: {result.winner}")
print(f"Improvement: {result.improvement_percentage:.1f}%")
```

### 3. Generate Report

After running multiple tests:

```python
# Load test IDs
test_ids = ['test_001', 'test_002', 'test_003']

# Generate summary report
report = framework.generate_report(test_ids)

print(report)
```

## Evaluation Rubric

### Metric Categories

#### 1. Accuracy Metrics (Correctness)

**Architecture Patterns Accuracy** (1-5)
- 1: Major patterns misidentified or missing
- 2: Some patterns identified but with significant errors
- 3: Basic patterns identified correctly, some details missing
- 4: Most patterns identified accurately with good detail
- 5: All major patterns identified with excellent accuracy

**Technology Stack Accuracy** (1-5)
- 1: Major technologies misidentified or missing
- 2: Some technologies identified but with errors
- 3: Core technologies identified correctly
- 4: Detailed technology identification with minor gaps
- 5: Comprehensive and accurate technology analysis

**Component Relationships Accuracy** (1-5)
- 1: Component relationships incorrectly described
- 2: Some relationships identified but with errors
- 3: Basic relationships described correctly
- 4: Most relationships accurately described with detail
- 5: Comprehensive and accurate relationship mapping

#### 2. Completeness Metrics (Coverage)

**Coverage Score** (1-5)
- 1: Less than 20% of codebase covered
- 2: 20-40% of codebase covered
- 3: 40-60% of codebase covered
- 4: 60-80% of codebase covered
- 5: 80%+ of codebase covered comprehensively

**Detail Depth** (1-5)
- 1: Superficial, lacks meaningful details
- 2: Basic details, missing important context
- 3: Adequate details for understanding basics
- 4: Good detail level, helpful for developers
- 5: Excellent depth with actionable insights

**Missing Critical Info** (1-5, inverse scoring)
- 1: Many critical details missing
- 2: Some critical details missing
- 3: Most critical info present, minor gaps
- 4: Nearly complete, very minor gaps
- 5: All critical information present

#### 3. Relevance Metrics (Usefulness)

**Context Relevance** (1-5)
- 1: Information not relevant to codebase
- 2: Some relevant info, much is generic
- 3: Mostly relevant with some generic content
- 4: Highly relevant with minimal generic content
- 5: Perfectly tailored to this specific codebase

**Actionability** (1-5)
- 1: No actionable insights or guidance
- 2: Few actionable points, mostly descriptive
- 3: Some actionable insights present
- 4: Many actionable insights and recommendations
- 5: Highly actionable with clear next steps

**Developer Usefulness** (1-5)
- 1: Would not help developers understand codebase
- 2: Minimally helpful for developers
- 3: Moderately helpful for understanding
- 4: Very helpful for onboarding and development
- 5: Extremely valuable reference for all developers

#### 4. Meta Metrics

**Hallucination Count** (integer)
- Count of incorrect or fabricated details
- Each hallucination applies -0.1 penalty to overall score (capped at -2.0)

**Redundancy Score** (1-5, inverse scoring)
- 1: Highly redundant with repeated information
- 2: Noticeable redundancy throughout
- 3: Some redundancy, mostly concise
- 4: Minimal redundancy, well-organized
- 5: No redundancy, perfectly concise

### Composite Scores

The framework automatically computes:

- **Accuracy Composite**: Average of accuracy metrics
- **Completeness Composite**: Average of completeness metrics
- **Relevance Composite**: Average of relevance metrics
- **Overall Score**: Average of composites minus hallucination penalty

## Example Results

### Sample Test Result

```json
{
  "test_id": "architecture_20251121_001",
  "timestamp": "2025-11-21T10:30:00",
  "generator_type": "architecture",
  "control_metrics": {
    "accuracy": {
      "architecture_patterns": 3,
      "technology_stack": 3,
      "component_relationships": 2,
      "composite": 2.67
    },
    "completeness": {
      "coverage": 3,
      "detail_depth": 2,
      "missing_critical_info": 2,
      "composite": 2.33
    },
    "relevance": {
      "context_relevance": 2,
      "actionability": 2,
      "developer_usefulness": 3,
      "composite": 2.33
    },
    "overall_score": 2.24
  },
  "treatment_metrics": {
    "accuracy": {
      "architecture_patterns": 5,
      "technology_stack": 4,
      "component_relationships": 4,
      "composite": 4.33
    },
    "completeness": {
      "coverage": 4,
      "detail_depth": 5,
      "missing_critical_info": 4,
      "composite": 4.33
    },
    "relevance": {
      "context_relevance": 5,
      "actionability": 4,
      "developer_usefulness": 5,
      "composite": 4.67
    },
    "overall_score": 4.44
  },
  "winner": "treatment",
  "improvement_percentage": 98.0
}
```

### Sample Report

```markdown
# A/B Testing Report: Documentation with Analysis Insights

**Generated:** 2025-11-21 10:45:00
**Tests Analyzed:** 5

## Summary

- **Treatment Wins:** 5 (100.0%)
- **Control Wins:** 0 (0.0%)
- **Ties:** 0 (0.0%)

**Average Treatment Improvement:** 92.3%

## Metric Breakdown

### Accuracy
- **Control Average:** 2.55
- **Treatment Average:** 4.40
- **Difference:** +1.85

### Completeness
- **Control Average:** 2.40
- **Treatment Average:** 4.35
- **Difference:** +1.95

### Relevance
- **Control Average:** 2.30
- **Treatment Average:** 4.65
- **Difference:** +2.35
```

## Advanced Usage

### Custom Rubric

```python
from claude_skills.llm_doc_gen.ab_testing import EvaluationRubric

# Create custom rubric
rubric = EvaluationRubric(
    name="Custom Documentation Rubric",
    description="Specialized rubric for API documentation"
)

# Add custom criteria
rubric.criteria['api_completeness'] = {
    1: "Less than 25% of APIs documented",
    2: "25-50% of APIs documented",
    3: "50-75% of APIs documented",
    4: "75-95% of APIs documented",
    5: "Complete API documentation"
}

# Export rubric
framework.export_rubric(Path('./custom_rubric.json'))
```

### Batch Testing

```python
import glob
from pathlib import Path

# Run tests across multiple codebases
test_ids = []

for codebase_path in glob.glob('./codebases/*'):
    codebase = Path(codebase_path)
    analysis_data = codebase / 'codebase.json'

    # Define generator for this codebase
    def codebase_generator(analysis_path):
        # Generation logic...
        return True, "Documentation output"

    result = framework.run_test(
        generator_type='architecture',
        generator_fn=codebase_generator,
        analysis_data_path=analysis_data
    )

    # Manual evaluation...
    result.control_metrics.architecture_patterns_accuracy = 3
    # ... etc
    result.control_metrics.compute_composites()

    result.treatment_metrics.architecture_patterns_accuracy = 5
    # ... etc
    result.treatment_metrics.compute_composites()

    result.determine_winner()
    framework.save_result(result)
    test_ids.append(result.test_id)

# Generate aggregate report
report = framework.generate_report(test_ids)
with open('batch_report.md', 'w') as f:
    f.write(report)
```

## Interpretation Guidelines

### When Treatment Wins

Treatment variant (with analysis insights) performs better when:
- Accuracy composite is higher (patterns identified correctly)
- Completeness composite is higher (more thorough coverage)
- Relevance composite is higher (more contextually specific)
- Fewer hallucinations (more grounded in actual code)

**Interpretation**: Analysis insights improve documentation quality by providing factual grounding and comprehensive codebase understanding.

### When Control Wins

Control variant (without insights) performs better when:
- Treatment has high hallucination count (over-reliance on potentially stale data)
- Treatment is redundant (insights add noise, not value)
- Control is more concise and actionable

**Interpretation**: Analysis insights may be adding noise or the insights are not well-integrated into documentation.

### Improvement Percentage

- **<10%**: Marginal improvement, may not justify cost
- **10-30%**: Noticeable improvement, worth considering
- **30-50%**: Significant improvement, strong case for insights
- **>50%**: Major improvement, insights are highly valuable

## Best Practices

1. **Blind Evaluation**: Evaluate control and treatment separately without knowing which is which
2. **Multiple Evaluators**: Have 2-3 people score independently and average results
3. **Consistent Rubric**: Use the same rubric across all tests for comparable results
4. **Document Context**: Record codebase size, language, and domain for context
5. **Track Time**: Monitor generation time differences between variants
6. **Iterative Refinement**: Use results to improve insight extraction and formatting

## File Locations

```
src/claude_skills/claude_skills/llm_doc_gen/
├── ab_testing.py                    # Core framework
├── AB_TESTING_README.md             # This file
└── analysis/
    └── analysis_insights.py         # Insight extraction used in treatment

tests/llm_doc_gen/
└── test_ab_testing.py               # Comprehensive test suite

ab_test_results/                     # Generated results (created on first use)
├── test_001.json
├── test_002.json
└── rubric.json
```

## Contributing

When adding new metrics:

1. Add metric to `EvaluationMetrics` dataclass
2. Add criteria to `EvaluationRubric.default_rubric()`
3. Update composite computation if needed
4. Add tests to verify metric behavior
5. Update this README with metric description

## Future Enhancements

Potential improvements:

- **Automated Scoring**: Use LLM to score documentation quality automatically
- **Statistical Analysis**: Add significance testing and confidence intervals
- **Visualization**: Generate charts and graphs for metric comparisons
- **Real-time Dashboards**: Web interface for monitoring test results
- **Metric Weights**: Allow custom weighting of different metric categories
