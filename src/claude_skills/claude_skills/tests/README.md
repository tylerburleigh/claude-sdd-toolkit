# SDD Python Tools Test Suite

Comprehensive test suite for the Spec-Driven Development (SDD) Python tools, including sdd-next, sdd-update, and sdd_common modules.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Coverage](#coverage)
- [Continuous Integration](#continuous-integration)

## Overview

This test suite provides comprehensive coverage for all SDD Python tools:

- **sdd_common**: Shared utilities for state management, spec parsing, progress tracking
- **sdd-next**: Task discovery and workflow planning operations
- **sdd-update**: Progress tracking and state update operations
- **sdd plan**: Spec and state validation, auto-fix, and reporting operations
- **CLI Integration**: End-to-end tests for command-line interfaces

**Test Statistics:**
- Total test files: 20+
- Total test cases: 400+
- Target coverage: 85%+

## Installation

### Prerequisites

```bash
# Python 3.8+
python --version

# Install testing dependencies
pip install -r requirements-test.txt
```

### Testing Dependencies

```bash
pytest>=7.4.0          # Test framework
pytest-cov>=4.1.0      # Coverage reporting
pytest-mock>=3.12.0    # Mocking support
pytest-xdist>=3.5.0    # Parallel execution
```

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests for specific module
pytest tests/unit/test_sdd_common/
pytest tests/unit/test_sdd_next/
pytest tests/unit/test_sdd_update/
pytest tests/unit/test_sdd_plan/
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test File

```bash
# Run specific test file
pytest tests/unit/test_sdd_common/test_state.py

# Run specific test class
pytest tests/unit/test_sdd_common/test_spec.py::TestLoadJsonSpec

# Run specific test function
pytest tests/unit/test_sdd_common/test_spec.py::TestLoadJsonSpec::test_load_existing_json_spec
```

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Run tests in parallel (auto-detect CPUs)
pytest -n auto
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── fixtures/                      # Test data
│   ├── sample_specs/             # Sample spec markdown files
│   ├── sample_json_specs/        # Sample JSON spec files
│   └── sample_projects/          # Sample project structures
├── unit/                         # Unit tests
│   ├── test_sdd_common/         # sdd_common module tests
│   │   ├── test_spec.py         # JSON spec operations
│   │   ├── test_spec.py         # Spec parsing
│   │   ├── test_progress.py     # Progress calculation
│   │   ├── test_paths.py        # Path utilities
│   │   └── test_printer.py      # Output formatting
│   ├── test_sdd_next/           # sdd-next module tests
│   │   ├── test_discovery.py    # Task discovery
│   │   ├── test_project.py      # Project analysis
│   │   ├── test_validation.py   # Validation operations
│   │   └── test_workflow.py     # Workflow utilities
│   ├── test_sdd_update/         # sdd-update module tests
│   │   ├── test_status.py       # Status updates
│   │   ├── test_journal.py      # Journaling
│   │   ├── test_time_tracking.py # Time tracking
│   │   └── test_lifecycle.py    # Spec lifecycle
│   └── test_sdd_plan/           # sdd plan module tests
│       ├── test_spec_validation.py  # Spec validation operations
│       ├── test_state_validation.py # State validation operations
│       └── test_cross_validation.py # Cross-validation operations
└── integration/                  # Integration tests
    ├── test_sdd_next_cli.py     # CLI integration tests
    ├── test_sdd_update_cli.py   # CLI integration tests
    ├── test_sdd_plan_cli.py     # CLI integration tests
    └── test_end_to_end.py       # End-to-end workflows
```

## Test Categories

### Unit Tests

Unit tests test individual functions and methods in isolation.

**Location:** `tests/unit/`

**Characteristics:**
- Fast execution
- Isolated from external dependencies
- Use mocks for file I/O and external calls
- Test edge cases and error handling

**Example:**
```python
def test_load_existing_json_spec(sample_state_simple, specs_structure):
    """Test loading an existing JSON spec."""
    spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

    assert spec_data is not None
    assert spec_data["spec_id"] == "simple-spec-2025-01-01-001"
```

### Integration Tests

Integration tests test how components work together, including CLI interfaces.

**Location:** `tests/integration/`

**Characteristics:**
- Test CLI commands end-to-end
- Use real subprocess calls
- Test JSON output
- Verify complete workflows

**Example:**
```python
def test_next_task_json_output(sample_state_simple, specs_structure):
    """Test next-task with JSON output."""
    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "next-task", "simple-spec-2025-01-01-001",
         "--path", str(specs_structure.parent), "--json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "task_id" in data
```

## Writing Tests

### Test Function Naming

Follow the naming convention: `test_<function>_<scenario>`

```python
def test_load_json_spec_success()           # Good
def test_load_json_spec_nonexistent()       # Good
def test_load_json_spec_invalid_json()      # Good
```

### Using Fixtures

Leverage the comprehensive fixtures in `conftest.py`:

```python
def test_my_function(sample_spec_simple, sample_json_spec_simple, specs_structure):
    """Test using pre-built fixtures."""
    # Fixtures are automatically created and cleaned up
    spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
    # ... test code
```

### Available Fixtures

- **`temp_dir`**: Temporary directory for test files
- **`specs_structure`**: Complete specs directory structure
- **`sample_spec_simple`**: Simple spec file (2 phases, 2 tasks each)
- **`sample_spec_complex`**: Complex spec file (3 phases, 3 tasks each)
- **`sample_json_spec_simple`**: Simple JSON spec fixture
- **`sample_json_spec_with_deps`**: JSON spec with dependencies
- **`sample_json_spec_circular_deps`**: JSON spec with circular dependencies
- **`sample_node_project`**: Node.js project structure
- **`sample_python_project`**: Python project structure

### Test Patterns

#### Testing Success Cases

```python
def test_function_success(fixture):
    """Test successful operation."""
    result = function_under_test(input)

    assert result is not None
    assert result["key"] == expected_value
```

#### Testing Error Cases

```python
def test_function_error_handling(fixture):
    """Test error handling."""
    result = function_under_test(invalid_input)

    assert "error" in result or result is None
```

#### Testing with JSON Output

```python
def test_function_json_output(capsys):
    """Test JSON output format."""
    function_that_prints_json()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "expected_key" in data
```

### Using Markers

Mark tests appropriately:

```python
@pytest.mark.unit
def test_unit_test():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration_test():
    """Integration test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Test that takes a while."""
    pass
```

## Coverage

### Viewing Coverage Reports

```bash
# Run tests with coverage
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# Open HTML report
open htmlcov/index.html
```

### Coverage Goals

- **Overall Coverage:** 85%+
- **Critical Modules:** 90%+
  - `sdd_common/state.py`
  - `sdd_common/spec.py`
  - `operations/discovery.py`
- **Acceptable:** 70%+
  - CLI wrappers
  - Formatting code

### Improving Coverage

1. Identify uncovered code:
   ```bash
   pytest --cov --cov-report=term-missing
   ```

2. Add tests for missing lines

3. Verify improvement:
   ```bash
   pytest --cov
   ```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest --cov --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure sdd_common is in Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest
```

**Fixture Not Found:**
```python
# Make sure you're using the correct fixture name
def test_my_test(sample_spec_simple):  # Correct
def test_my_test(simple_spec):         # Wrong - fixture doesn't exist
```

**Test Timeout:**
```bash
# Increase timeout for slow tests
pytest --timeout=300
```

## Best Practices

1. **Keep tests independent** - Each test should run in isolation
2. **Use descriptive names** - Test names should explain what they test
3. **Test one thing** - Each test should verify one behavior
4. **Use fixtures** - Reuse test data and setup code
5. **Mock external dependencies** - Don't rely on external services
6. **Test edge cases** - Empty inputs, None values, invalid data
7. **Write integration tests** - Test components working together
8. **Maintain coverage** - Aim for 85%+ coverage
9. **Run tests frequently** - Before commits and pushes
10. **Keep tests fast** - Use `@pytest.mark.slow` for slow tests

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add tests for new functionality
4. Maintain coverage above 85%
5. Update this README if needed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For issues or questions about tests:
1. Check this README
2. Review existing tests for patterns
3. Open an issue with test failure details
