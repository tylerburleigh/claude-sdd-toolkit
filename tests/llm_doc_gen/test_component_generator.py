"""Tests for component generator with analysis insights integration."""

import json
import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.generators.component_generator import (
    ComponentGenerator,
    ComponentData
)


@pytest.fixture
def sample_component_data():
    """Create sample component data for testing."""
    return ComponentData(
        project_name="TestProject",
        project_root="/path/to/project",
        is_multi_part=False,
        complete_source_tree="src/\n  main.py\n  utils/\n    helpers.py",
        critical_folders=[
            {
                "path": "src",
                "purpose": "Main application code",
                "contents": "Python modules"
            }
        ],
        main_entry_point="src/main.py",
        file_type_patterns=[
            {
                "type": "Python Source",
                "pattern": "*.py",
                "purpose": "Application code"
            }
        ],
        config_files=[
            {
                "path": "pyproject.toml",
                "description": "Python project configuration"
            }
        ]
    )


@pytest.fixture
def multipart_component_data():
    """Create multi-part component data for testing."""
    return ComponentData(
        project_name="FullStackApp",
        project_root="/path/to/app",
        is_multi_part=True,
        parts_count=2,
        complete_source_tree="apps/\n  web/\n    src/\n  api/\n    src/",
        project_parts=[
            {
                "name": "Frontend",
                "path": "apps/web",
                "type": "React SPA",
                "tech_stack": "React + TypeScript",
                "purpose": "User interface"
            },
            {
                "name": "Backend",
                "path": "apps/api",
                "type": "REST API",
                "tech_stack": "FastAPI + Python",
                "purpose": "API server"
            }
        ]
    )


@pytest.fixture
def sample_analysis_data(tmp_path):
    """Create sample codebase.json for insights testing."""
    analysis_path = tmp_path / "codebase.json"
    analysis_data = {
        "functions": [
            {
                "name": "main",
                "file": "src/main.py",
                "complexity": 5,
                "call_count": 50,
                "callers": [],
                "calls": []
            },
            {
                "name": "process_data",
                "file": "src/processor.py",
                "complexity": 15,
                "call_count": 30,
                "callers": ["main"],
                "calls": [{"name": "validate"}, {"name": "transform"}]
            },
            {
                "name": "helper_fn",
                "file": "src/utils/helpers.py",
                "complexity": 3,
                "call_count": 100,
                "callers": ["process_data", "main"],
                "calls": []
            }
        ],
        "classes": [
            {
                "name": "DataProcessor",
                "file": "src/processor.py",
                "instantiation_count": 25
            }
        ],
        "dependencies": {
            "src/main.py": ["src/processor.py", "src/utils/helpers.py"],
            "src/processor.py": ["src/utils/helpers.py"]
        }
    }

    with open(analysis_path, 'w') as f:
        json.dump(analysis_data, f)

    return analysis_path


def test_generator_initialization(tmp_path):
    """Test component generator can be initialized."""
    generator = ComponentGenerator(tmp_path)
    assert generator.project_root == tmp_path


def test_component_data_defaults():
    """Test ComponentData dataclass with minimal fields."""
    data = ComponentData(
        project_name="Test",
        project_root="/test",
        is_multi_part=False
    )

    assert data.project_name == "Test"
    assert data.project_root == "/test"
    assert data.is_multi_part is False
    assert data.parts_count == 0
    assert data.complete_source_tree == ""
    assert data.critical_folders == []
    assert data.project_parts is None
    assert data.main_entry_point is None


def test_format_component_prompt_single_part(tmp_path, sample_component_data):
    """Test prompt formatting for single-part project."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src", "tests", "docs"]

    prompt = generator.format_component_prompt(
        sample_component_data,
        directories,
        max_directories=10
    )

    # Verify prompt structure
    assert "# Task: Component Inventory Analysis (Read-Only)" in prompt
    assert "**IMPORTANT: You have READ-ONLY access" in prompt
    assert sample_component_data.project_name in prompt
    assert "Single-part" in prompt
    assert "src" in prompt
    assert "tests" in prompt
    assert "docs" in prompt


def test_format_component_prompt_multi_part(tmp_path, multipart_component_data):
    """Test prompt formatting for multi-part project."""
    generator = ComponentGenerator(tmp_path)
    directories = ["apps/web/src", "apps/api/src"]

    prompt = generator.format_component_prompt(
        multipart_component_data,
        directories,
        max_directories=10
    )

    # Verify multi-part structure
    assert "Multi-part" in prompt
    assert "**Parts Count:** 2" in prompt
    assert "Frontend" in prompt
    assert "Backend" in prompt
    assert "apps/web" in prompt
    assert "apps/api" in prompt
    assert "Integration Points" in prompt


def test_format_component_prompt_directory_limit(tmp_path, sample_component_data):
    """Test that directory list is limited to max_directories."""
    generator = ComponentGenerator(tmp_path)
    directories = [f"dir{i}" for i in range(20)]

    prompt = generator.format_component_prompt(
        sample_component_data,
        directories,
        max_directories=5
    )

    # Should only include first 5 directories
    assert "dir0" in prompt
    assert "dir4" in prompt
    assert "dir5" not in prompt
    assert "dir19" not in prompt


def test_format_component_prompt_research_sections(tmp_path, sample_component_data):
    """Test that prompt includes all required research sections."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    # Verify all major research sections are present
    assert "### 1. Source Tree Overview" in prompt
    assert "### 2. Critical Directories" in prompt
    assert "### 3. Entry Points" in prompt
    assert "### 4. File Organization Patterns" in prompt
    assert "### 5. Key File Types" in prompt
    assert "### 6. Configuration Files" in prompt
    assert "### 7. Asset Locations" in prompt
    # For single-part projects, Development Notes is section 8
    assert "### 8. Development Notes" in prompt


def test_format_component_prompt_includes_source_tree(tmp_path, sample_component_data):
    """Test that prompt includes source tree if provided."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    assert "### Complete Directory Structure" in prompt
    assert "src/" in prompt
    assert "main.py" in prompt
    assert "helpers.py" in prompt


def test_format_component_prompt_with_insights(tmp_path, sample_component_data, sample_analysis_data):
    """Test prompt formatting includes codebase analysis insights."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src", "tests"]

    prompt = generator.format_component_prompt(
        sample_component_data,
        directories,
        max_directories=10,
        analysis_data=sample_analysis_data
    )

    # Verify insights section is present
    assert "### Codebase Analysis Insights" in prompt

    # Check that insights contain expected content
    assert "Codebase Overview" in prompt or "**Codebase Overview:**" in prompt

    # Verify insights are placed before the research objectives section
    insights_pos = prompt.find("### Codebase Analysis Insights")
    research_pos = prompt.find("## Research Findings to Provide")
    assert insights_pos < research_pos


def test_format_component_prompt_without_insights(tmp_path, sample_component_data):
    """Test prompt formatting without insights (backward compatibility)."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src", "tests"]

    prompt = generator.format_component_prompt(
        sample_component_data,
        directories,
        max_directories=10,
        analysis_data=None
    )

    # Should not include insights section
    assert "### Codebase Analysis Insights" not in prompt

    # But should still have all other sections
    assert "## Research Findings to Provide" in prompt
    assert "### 1. Source Tree Overview" in prompt


def test_format_component_prompt_with_nonexistent_insights(tmp_path, sample_component_data):
    """Test prompt formatting gracefully handles nonexistent analysis file."""
    generator = ComponentGenerator(tmp_path)
    nonexistent_path = tmp_path / "nonexistent.json"

    # Should not raise exception, just skip insights
    prompt = generator.format_component_prompt(
        sample_component_data,
        ["src"],
        max_directories=10,
        analysis_data=nonexistent_path
    )

    # Should not include insights section
    assert "### Codebase Analysis Insights" not in prompt


def test_format_component_prompt_insights_position(tmp_path, sample_component_data, sample_analysis_data):
    """Test that insights are positioned correctly in the prompt."""
    generator = ComponentGenerator(tmp_path)

    prompt = generator.format_component_prompt(
        sample_component_data,
        ["src"],
        max_directories=10,
        analysis_data=sample_analysis_data
    )

    # Find positions of key sections
    source_tree_pos = prompt.find("### Complete Directory Structure")
    insights_pos = prompt.find("### Codebase Analysis Insights")
    directories_pos = prompt.find("## Directories to Analyze")

    # Verify ordering: source_tree < insights < directories
    assert source_tree_pos < insights_pos < directories_pos


def test_compose_component_doc_single_part(sample_component_data):
    """Test document composition for single-part project."""
    generator = ComponentGenerator(Path("/tmp"))
    research_findings = """
## Source Tree Overview

The project follows a standard Python package structure.

## Critical Directories

- **src**: Main application code
"""

    doc = generator.compose_component_doc(
        research_findings,
        sample_component_data,
        "2025-01-15"
    )

    # Verify document structure
    assert "# TestProject - Component Inventory" in doc
    assert "**Date:** 2025-01-15" in doc
    assert "## Complete Directory Structure" in doc
    assert "src/" in doc
    assert research_findings.strip() in doc
    assert "## Related Documentation" in doc
    assert "*Generated using LLM-based documentation workflow*" in doc


def test_compose_component_doc_multi_part(multipart_component_data):
    """Test document composition for multi-part project."""
    generator = ComponentGenerator(Path("/tmp"))
    research_findings = "## Analysis results"

    doc = generator.compose_component_doc(
        research_findings,
        multipart_component_data,
        "2025-01-15"
    )

    # Verify multi-part sections
    assert "## Multi-Part Structure" in doc
    assert "2 distinct parts" in doc
    assert "**Frontend** (`apps/web`)" in doc
    assert "**Backend** (`apps/api`)" in doc
    assert "User interface" in doc
    assert "API server" in doc


def test_compose_component_doc_with_source_tree(sample_component_data):
    """Test that source tree is included in composed document."""
    generator = ComponentGenerator(Path("/tmp"))
    research_findings = "Research"

    doc = generator.compose_component_doc(
        research_findings,
        sample_component_data,
        "2025-01-15"
    )

    # Verify source tree is included
    assert "```" in doc
    assert "src/" in doc
    assert "main.py" in doc


def test_generate_component_doc_success(tmp_path, sample_component_data):
    """Test full component documentation generation workflow."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src", "tests"]

    # Mock LLM consultation function
    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        return True, "## Component Analysis\n\nWell-organized Python project"

    success, doc = generator.generate_component_doc(
        sample_component_data,
        directories,
        mock_llm_fn,
        max_directories=10
    )

    assert success is True
    assert "# TestProject - Component Inventory" in doc
    assert "Well-organized Python project" in doc


def test_generate_component_doc_with_insights(tmp_path, sample_component_data, sample_analysis_data):
    """Test full workflow with analysis insights integration."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src", "tests"]

    # Track what prompt was sent to LLM
    received_prompt = None

    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        nonlocal received_prompt
        received_prompt = prompt
        return True, "## Component Analysis\n\nProject analyzed with insights"

    success, doc = generator.generate_component_doc(
        sample_component_data,
        directories,
        mock_llm_fn,
        max_directories=10,
        analysis_data=sample_analysis_data
    )

    # Verify success
    assert success is True
    assert "Component Analysis" in doc

    # Verify insights were included in prompt sent to LLM
    assert received_prompt is not None
    assert "### Codebase Analysis Insights" in received_prompt


def test_generate_component_doc_llm_failure(tmp_path, sample_component_data):
    """Test component generation handles LLM failure."""
    generator = ComponentGenerator(tmp_path)
    directories = ["src"]

    # Mock failing LLM consultation
    def mock_failing_llm(prompt: str) -> tuple[bool, str]:
        return False, "Connection timeout"

    success, result = generator.generate_component_doc(
        sample_component_data,
        directories,
        mock_failing_llm
    )

    assert success is False
    assert "LLM consultation failed" in result
    assert "Connection timeout" in result


def test_prompt_read_only_emphasis(tmp_path, sample_component_data):
    """Test that prompt emphasizes read-only nature."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    # Should have multiple read-only warnings
    assert prompt.count("READ-ONLY") >= 1
    assert "DO NOT write" in prompt
    assert "Just return your research findings" in prompt


def test_prompt_includes_tables(tmp_path, sample_component_data):
    """Test that prompt includes table templates for structured data."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    # Verify table templates
    assert "| Directory Path | Purpose | Contents Summary |" in prompt
    assert "| File Type | Pattern | Purpose | Examples |" in prompt


def test_prompt_output_format_guidance(tmp_path, sample_component_data):
    """Test that prompt includes clear output format guidance."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    # Verify output format section
    assert "## Output Format" in prompt
    assert "structured text" in prompt
    assert "markdown formatting" in prompt
    assert "reference actual directories/files" in prompt
    assert "evidence-based analysis" in prompt


def test_multipart_prompt_includes_integration_section(tmp_path, multipart_component_data):
    """Test that multi-part prompts include integration points section."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(multipart_component_data, [], max_directories=10)

    # Multi-part projects should have integration section
    assert "### 8. Integration Points (Multi-Part Projects)" in prompt
    assert "Communication patterns between parts" in prompt
    assert "Data flow between parts" in prompt


def test_component_data_with_assets():
    """Test ComponentData with asset information."""
    data = ComponentData(
        project_name="AssetProject",
        project_root="/path",
        is_multi_part=False,
        has_assets=True,
        asset_locations=[
            {
                "type": "Images",
                "location": "public/images",
                "file_count": "150",
                "total_size": "2.5MB"
            }
        ]
    )

    assert data.has_assets is True
    assert data.asset_locations is not None
    assert len(data.asset_locations) == 1
    assert data.asset_locations[0]["type"] == "Images"


def test_prompt_ignores_specs_directory(tmp_path, sample_component_data):
    """Test that prompt explicitly instructs to ignore specs/ directory."""
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(sample_component_data, [], max_directories=10)

    # Verify specs directory is in ignore list
    assert "## Files and Directories to Ignore" in prompt
    assert "`specs/`" in prompt
    assert "Project specifications" in prompt


def test_insights_format_for_component_generator(tmp_path, sample_component_data, sample_analysis_data):
    """Test that insights are formatted appropriately for component generator."""
    from claude_skills.llm_doc_gen.analysis.analysis_insights import (
        extract_insights_from_analysis,
        format_insights_for_prompt
    )

    # Extract and format insights
    insights = extract_insights_from_analysis(sample_analysis_data)
    formatted = format_insights_for_prompt(insights, generator_type='component')

    # Verify format is appropriate (should be relatively compact)
    assert len(formatted) < 2000  # Component should have ~350 token budget
    assert "**Codebase Overview:**" in formatted

    # Generate prompt and verify insights integration
    generator = ComponentGenerator(tmp_path)
    prompt = generator.format_component_prompt(
        sample_component_data,
        ["src"],
        max_directories=10,
        analysis_data=sample_analysis_data
    )

    # Insights should be present and properly formatted
    assert "### Codebase Analysis Insights" in prompt
    assert "**Codebase Overview:**" in prompt
