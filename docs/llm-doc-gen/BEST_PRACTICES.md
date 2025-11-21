# Best Practices for Using Analysis Insights in LLM Documentation Generation

## Introduction

This guide provides actionable best practices for effectively integrating codebase analysis insights into LLM-generated documentation workflows. Following these practices will help you maximize documentation quality while maintaining performance and reliability.

## Table of Contents

1. [Data Freshness](#data-freshness)
2. [Cache Management](#cache-management)
3. [Performance Optimization](#performance-optimization)
4. [Error Handling](#error-handling)
5. [Quality Validation](#quality-validation)
6. [Metric Selection](#metric-selection)
7. [Token Budget Management](#token-budget-management)
8. [Integration Patterns](#integration-patterns)
9. [Testing & Validation](#testing--validation)
10. [Common Pitfalls](#common-pitfalls)

---

## 1. Data Freshness

### Keep Analysis Data Current

**Why it matters:** Stale analysis data leads to outdated insights and potential inaccuracies in generated documentation.

### ✅ DO:

```bash
# Regenerate documentation.json after significant code changes
git pull
sdd analyze-codebase --force

# Automate freshness checks
if [ $(find documentation.json -mtime +7) ]; then
    echo "Analysis data is >7 days old, regenerating..."
    sdd analyze-codebase --force
fi
```

```python
# Check staleness before using
from claude_skills.llm_doc_gen.analysis.analysis_insights import extract_insights_from_analysis

insights = extract_insights_from_analysis(
    docs_path,
    warn_stale=True  # Logs warning if >24h old
)
```

### ❌ DON'T:

```python
# Don't ignore staleness warnings
insights = extract_insights_from_analysis(
    docs_path,
    warn_stale=False  # Suppresses important warnings
)
```

```bash
# Don't use months-old analysis data
# Check: ls -lh documentation.json
```

### Recommendation:

- **Small projects (<100 files):** Regenerate weekly or after major changes
- **Medium projects (100-500):** Regenerate after each sprint/milestone
- **Large projects (>500):** Automate nightly regeneration

---

## 2. Cache Management

### Use Caching for Multi-Generator Runs

**Why it matters:** Cache provides 50-1000x speedup on repeated extractions.

### ✅ DO:

```python
# Single session with multiple generators
from claude_skills.llm_doc_gen.analysis.analysis_insights import (
    extract_insights_from_analysis
)

# Cache warming
insights = extract_insights_from_analysis(docs_path, use_cache=True)

# Subsequent calls are instant
arch_insights = extract_insights_from_analysis(docs_path)  # From cache
comp_insights = extract_insights_from_analysis(docs_path)  # From cache
over_insights = extract_insights_from_analysis(docs_path)  # From cache
```

### ❌ DON'T:

```python
# Don't disable caching without reason
insights = extract_insights_from_analysis(docs_path, use_cache=False)  # Slow!
```

### Clear Cache Strategically

**When to clear:**
- After regenerating `documentation.json`
- Between independent documentation runs
- When switching codebases

```python
from claude_skills.llm_doc_gen.analysis.analysis_insights import clear_cache

# Clear cache after regeneration
clear_cache()
insights = extract_insights_from_analysis(docs_path)  # Fresh load
```

### Monitor Cache Effectiveness

```python
from claude_skills.llm_doc_gen.analysis.analysis_insights import get_cache_metrics

metrics = get_cache_metrics()
print(f"Hit rate: {metrics.hit_rate():.1%}")

# Good: >50% hit rate
# Poor: <20% hit rate (consider workflow optimization)
```

---

## 3. Performance Optimization

### Validate Performance Targets

**Why it matters:** Keep documentation generation responsive (<2s overhead).

### ✅ DO:

```python
from claude_skills.llm_doc_gen.analysis.performance_benchmark import (
    validate_performance_target
)

# Regular performance checks
passes = validate_performance_target(
    docs_path,
    target_seconds=2.0
)

if not passes:
    print("WARNING: Performance target exceeded!")
    print("Consider: reducing codebase size, optimizing analysis, or increasing target")
```

### Profile Bottlenecks

```python
from claude_skills.llm_doc_gen.analysis.performance_benchmark import quick_benchmark

result = quick_benchmark(docs_path)

print(f"Cold cache: {result['metrics']['timing']['cold_cache_seconds']}s")
print(f"Warm cache: {result['metrics']['timing']['warm_cache_seconds']}s")
print(f"Format: {result['metrics']['timing']['format_seconds']}s")

# Identify slowest component and optimize
```

### Optimize Large Codebases

For codebases exceeding performance targets:

```python
# Option 1: Exclude non-essential directories
sdd analyze-codebase --exclude-dirs tests,vendor,node_modules

# Option 2: Use adaptive scaling (automatic)
insights = extract_insights_from_analysis(
    docs_path,
    codebase_size=None  # Auto-detects and scales metrics appropriately
)

# Option 3: Reduce metric counts
# Edit analysis_insights.py top_n values for large codebases
```

---

## 4. Error Handling

### Handle Missing Analysis Data Gracefully

**Why it matters:** Documentation generation shouldn't fail if analysis data is unavailable.

### ✅ DO:

```python
from pathlib import Path

def generate_with_insights(data, llm_fn):
    """Generate documentation with optional insights."""
    docs_path = Path('./documentation.json')

    # Check if analysis data exists
    if not docs_path.exists():
        print("INFO: No analysis data found. Generating without insights.")
        docs_path = None

    try:
        return generator.generate_doc(
            data=data,
            llm_consultation_fn=llm_fn,
            analysis_data=docs_path
        )
    except Exception as e:
        print(f"ERROR: Generation failed: {e}")
        return False, str(e)
```

```python
# In generator implementations
if analysis_data and analysis_data.exists():
    try:
        insights = extract_insights_from_analysis(analysis_data)
        formatted = format_insights_for_prompt(insights, 'architecture')
    except Exception as e:
        # Log but don't fail
        logging.warning(f"Insight extraction failed: {e}")
        formatted = ""  # Continue without insights
```

### ❌ DON'T:

```python
# Don't let insight extraction break generation
insights = extract_insights_from_analysis(docs_path)  # Unhandled exception!
formatted = format_insights_for_prompt(insights, 'architecture')
```

### Validate Analysis Data

```python
def validate_analysis_data(docs_path: Path) -> bool:
    """Validate documentation.json format."""
    try:
        with open(docs_path, 'r') as f:
            data = json.load(f)

        # Check required keys
        required = ['functions', 'classes', 'dependencies']
        if not all(k in data for k in required):
            print(f"ERROR: Missing required keys in {docs_path}")
            return False

        return True
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {docs_path}")
        return False
    except Exception as e:
        print(f"ERROR: Cannot read {docs_path}: {e}")
        return False
```

---

## 5. Quality Validation

### Use A/B Testing to Measure Impact

**Why it matters:** Quantify documentation quality improvements from insights.

### ✅ DO:

```python
from claude_skills.llm_doc_gen.ab_testing import ABTestFramework

framework = ABTestFramework()

# Run controlled experiment
result = framework.run_test(
    generator_type='architecture',
    generator_fn=my_generator,
    analysis_data_path=Path('./documentation.json')
)

# Score both variants
result.control_metrics.architecture_patterns_accuracy = 3
result.control_metrics.technology_stack_accuracy = 3
# ... score all metrics

result.treatment_metrics.architecture_patterns_accuracy = 5
result.treatment_metrics.technology_stack_accuracy = 4
# ... score all metrics

# Evaluate
result.control_metrics.compute_composites()
result.treatment_metrics.compute_composites()
result.determine_winner()

print(f"Winner: {result.winner}")
print(f"Improvement: {result.improvement_percentage:.1f}%")

# Save for future reference
framework.save_result(result)
```

### Track Quality Over Time

```python
# Regular quality checks
test_ids = []
for version in ['v1.0', 'v1.1', 'v1.2']:
    result = framework.run_test(...)
    test_ids.append(result.test_id)

# Generate trend report
report = framework.generate_report(test_ids)
with open('quality_trends.md', 'w') as f:
    f.write(report)
```

### Blind Evaluation

For unbiased results:

1. Generate both variants
2. Randomize order (A/B or B/A)
3. Evaluate without knowing which is which
4. Reveal after scoring

---

## 6. Metric Selection

### Choose Relevant Metrics for Your Generator

**Why it matters:** Different generators benefit from different insights.

### Architecture Generator

**High Priority:**
- Most Called Functions (identify critical paths)
- Cross-Module Dependencies (architecture visualization)
- Entry Points (application structure)
- High Complexity Functions (refactoring candidates)

```python
# Architecture-specific metrics emphasized
formatted = format_insights_for_prompt(
    insights,
    generator_type='architecture',  # Prioritizes arch-relevant metrics
    docs_path=docs_path
)
```

### Component Generator

**High Priority:**
- File Organization Patterns (directory structure)
- Entry Points (main files)
- Most Instantiated Classes (core components)
- Integration Points (external dependencies)

```python
formatted = format_insights_for_prompt(
    insights,
    generator_type='component',  # Emphasizes component-relevant metrics
    docs_path=docs_path
)
```

### Overview Generator

**High Priority:**
- Language Breakdown (project composition)
- Module Statistics (high-level numbers)
- Technology Stack (quick overview)

```python
formatted = format_insights_for_prompt(
    insights,
    generator_type='overview',  # Focuses on high-level metrics
    docs_path=docs_path
)
```

### Custom Metrics

For domain-specific documentation:

```python
# Extract custom metrics
def extract_custom_metrics(data: Dict) -> Dict:
    """Extract domain-specific metrics."""
    custom = {}

    # Example: API endpoint analysis
    endpoints = [
        f for f in data.get('functions', [])
        if f.get('name', '').startswith('handle_')
    ]
    custom['api_endpoints'] = len(endpoints)

    # Example: Test coverage estimation
    test_functions = [
        f for f in data.get('functions', [])
        if 'test' in f.get('file', '').lower()
    ]
    custom['test_coverage_estimate'] = len(test_functions) / len(data.get('functions', []))

    return custom
```

---

## 7. Token Budget Management

### Respect Token Limits

**Why it matters:** Stay within LLM context windows and control costs.

### ✅ DO:

```python
# Use built-in token budgets
formatted = format_insights_for_prompt(
    insights,
    generator_type='architecture',  # 450 token budget
    docs_path=docs_path
)

# Verify formatted output size
estimated_tokens = len(formatted) // 4  # Rough estimate
print(f"Estimated tokens: {estimated_tokens}")
```

### Adjust for Context Constraints

```python
# For tight context windows, use overview (250 token budget)
formatted = format_insights_for_prompt(
    insights,
    generator_type='overview',
    docs_path=docs_path
)
```

### Monitor Budget Usage

```python
# Check if truncation occurred
insights = extract_insights_from_analysis(docs_path, codebase_size=600)
formatted = format_insights_for_prompt(insights, 'architecture')

# If codebase is large (>500 files), verify important metrics included
if codebase_size > 500:
    assert 'Most Called Functions' in formatted
    assert 'Entry Points' in formatted
```

---

## 8. Integration Patterns

### Follow Standard Integration Pattern

**Why it matters:** Consistency across generators improves maintainability.

### ✅ DO:

```python
# Standard pattern for all generators
class MyGenerator:
    def format_prompt(
        self,
        my_data: MyData,
        analysis_data: Optional[Path] = None  # Standard parameter name
    ) -> str:
        prompt_parts = []

        # ... build prompt ...

        # Standard integration block
        if analysis_data and analysis_data.exists():
            try:
                insights = extract_insights_from_analysis(analysis_data)
                formatted_insights = format_insights_for_prompt(
                    insights,
                    generator_type='my_type',
                    docs_path=analysis_data
                )
                prompt_parts.append("### Codebase Analysis Insights")
                prompt_parts.append("")
                prompt_parts.append(formatted_insights)
                prompt_parts.append("")
            except Exception as e:
                logging.warning(f"Insight extraction failed: {e}")

        return "\n".join(prompt_parts)
```

### ❌ DON'T:

```python
# Don't use inconsistent parameter names
def format_prompt(self, my_data, insights_file=None):  # Inconsistent!
    ...

# Don't hard-code paths
insights = extract_insights_from_analysis(Path('./doc.json'))  # Inflexible!
```

### Make Insights Optional

```python
# Allow users to opt out
def generate_doc(
    self,
    data,
    llm_fn,
    analysis_data: Optional[Path] = None,  # Optional!
    use_insights: bool = True  # Feature flag
):
    if use_insights and analysis_data:
        # Use insights
    else:
        # Skip insights
```

---

## 9. Testing & Validation

### Test With and Without Insights

**Why it matters:** Ensure graceful degradation.

### ✅ DO:

```python
import pytest

def test_generator_without_insights():
    """Test generation works without analysis data."""
    generator = MyGenerator(project_root)

    success, output = generator.generate_doc(
        data=test_data,
        llm_consultation_fn=mock_llm,
        analysis_data=None  # No insights
    )

    assert success
    assert len(output) > 0
    assert 'Codebase Analysis Insights' not in output

def test_generator_with_insights(tmp_path):
    """Test generation includes insights when available."""
    # Create test documentation.json
    docs_path = tmp_path / 'documentation.json'
    with open(docs_path, 'w') as f:
        json.dump(test_analysis_data, f)

    generator = MyGenerator(project_root)

    success, output = generator.generate_doc(
        data=test_data,
        llm_consultation_fn=mock_llm,
        analysis_data=docs_path
    )

    assert success
    assert 'Codebase Analysis Insights' in output
    assert 'Most Called Functions' in output
```

### Test Error Conditions

```python
def test_generator_with_corrupt_insights(tmp_path):
    """Test generation continues with corrupt analysis data."""
    docs_path = tmp_path / 'documentation.json'
    docs_path.write_text('{ invalid json')

    generator = MyGenerator(project_root)

    success, output = generator.generate_doc(
        data=test_data,
        llm_consultation_fn=mock_llm,
        analysis_data=docs_path
    )

    # Should succeed without insights
    assert success
    assert 'Codebase Analysis Insights' not in output
```

### Benchmark Performance in Tests

```python
def test_performance_target():
    """Verify insight extraction meets performance target."""
    from claude_skills.llm_doc_gen.analysis.performance_benchmark import (
        validate_performance_target
    )

    passes = validate_performance_target(docs_path, target_seconds=2.0)
    assert passes, "Performance target exceeded!"
```

---

## 10. Common Pitfalls

### Pitfall 1: Ignoring Staleness Warnings

**Problem:** Using outdated analysis data leads to inaccurate documentation.

**Solution:**
```python
# Always enable staleness warnings
insights = extract_insights_from_analysis(docs_path, warn_stale=True)

# Act on warnings
if cache_age_hours > 24:
    print("Regenerating stale analysis data...")
    os.system('sdd analyze-codebase --force')
```

### Pitfall 2: Not Handling Missing Data

**Problem:** Generator crashes when `documentation.json` doesn't exist.

**Solution:**
```python
# Always check existence
if analysis_data and analysis_data.exists():
    # Use insights
else:
    # Skip insights (graceful degradation)
```

### Pitfall 3: Over-Reliance on Insights

**Problem:** Documentation becomes purely data-driven without narrative context.

**Solution:**
- Use insights to supplement, not replace, AI reasoning
- Balance quantitative metrics with qualitative analysis
- Let LLM interpret insights in context

### Pitfall 4: Ignoring Performance Impact

**Problem:** Large codebase analysis causes >2s overhead.

**Solution:**
```python
# Profile regularly
result = quick_benchmark(docs_path)
if result['metrics']['meets_target'] is False:
    # Optimize or increase budget
```

### Pitfall 5: Not Testing A/B Impact

**Problem:** Assuming insights always improve documentation without validation.

**Solution:**
- Run A/B tests on representative codebases
- Track improvement percentages
- Iterate based on results

### Pitfall 6: Hardcoding Paths

**Problem:** Generators only work in specific directory structures.

**Solution:**
```python
# Make paths configurable
def generate_doc(self, data, llm_fn, analysis_data: Optional[Path] = None):
    # User provides path
    ...
```

### Pitfall 7: Disabling Caching Unnecessarily

**Problem:** Slow performance from repeated file I/O.

**Solution:**
```python
# Enable caching by default
insights = extract_insights_from_analysis(docs_path, use_cache=True)

# Only disable for specific reasons
insights = extract_insights_from_analysis(docs_path, use_cache=False)  # Rare!
```

### Pitfall 8: Exceeding Token Budgets

**Problem:** Insights consume too much context, limiting prompt space.

**Solution:**
```python
# Use appropriate generator type
formatted = format_insights_for_prompt(
    insights,
    generator_type='overview',  # 250 tokens (smallest)
    docs_path=docs_path
)

# Or manually truncate if needed
if len(formatted) > max_tokens * 4:
    formatted = formatted[: max_tokens * 4]
```

---

## Quick Reference

### Checklist for Integration

- [ ] Add `analysis_data: Optional[Path]` parameter
- [ ] Check `analysis_data.exists()` before using
- [ ] Wrap extraction in try/except
- [ ] Enable cache (`use_cache=True`)
- [ ] Enable staleness warnings (`warn_stale=True`)
- [ ] Use appropriate `generator_type`
- [ ] Handle errors gracefully
- [ ] Test with and without insights
- [ ] Benchmark performance
- [ ] Run A/B test to validate impact

### Command Quick Reference

```bash
# Regenerate analysis data
sdd analyze-codebase --force

# Check data freshness
ls -lh documentation.json

# Run performance benchmark
python -m claude_skills.llm_doc_gen.analysis.performance_benchmark

# Run A/B test
python -m claude_skills.llm_doc_gen.ab_testing
```

### Code Snippets

**Basic Integration:**
```python
if analysis_data and analysis_data.exists():
    try:
        insights = extract_insights_from_analysis(analysis_data)
        formatted = format_insights_for_prompt(insights, 'architecture')
        prompt_parts.append(formatted)
    except Exception as e:
        logging.warning(f"Continuing without insights: {e}")
```

**Performance Check:**
```python
from claude_skills.llm_doc_gen.analysis.performance_benchmark import validate_performance_target
assert validate_performance_target(docs_path)
```

**A/B Testing:**
```python
from claude_skills.llm_doc_gen.ab_testing import ABTestFramework
framework = ABTestFramework()
result = framework.run_test('architecture', my_generator, docs_path)
```

---

## Conclusion

Following these best practices ensures that analysis insights enhance your documentation generation workflow without compromising performance, reliability, or maintainability. Remember:

1. **Keep data fresh** - Regenerate analysis regularly
2. **Use caching** - Enable for multi-generator runs
3. **Handle errors** - Graceful degradation is key
4. **Validate quality** - A/B test to measure impact
5. **Monitor performance** - Stay below 2s overhead
6. **Test thoroughly** - With and without insights
7. **Follow patterns** - Consistency aids maintenance

For detailed implementation guidance, see:
- [Analysis Integration Guide](./ANALYSIS_INTEGRATION.md)
- [A/B Testing Framework](../../src/claude_skills/claude_skills/llm_doc_gen/AB_TESTING_README.md)
- [Performance Benchmarking](../../src/claude_skills/claude_skills/llm_doc_gen/analysis/performance_benchmark.py)
