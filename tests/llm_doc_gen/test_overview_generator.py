"""Tests for overview generator with analysis insights integration."""

import json
import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.generators.overview_generator import (
    OverviewGenerator,
    ProjectData
)


@pytest.fixture
def sample_project_data():
    """Create sample project data for testing."""
    return ProjectData(
        project_name="TestProject",
        project_type="Web Application",
        repository_type="monolith",
        primary_languages=["Python", "TypeScript"],
        tech_stack={
            "Framework": "FastAPI",
            "Frontend": "React",
            "Database": "PostgreSQL"
        },
        directory_structure={},
        file_count=150,
        total_loc=12000
    )


@pytest.fixture
def multipart_project_data():
    """Create multi-part project data for testing."""
    return ProjectData(
        project_name="FullStackApp",
        project_type="Full-Stack Application",
        repository_type="monorepo",
        primary_languages=["TypeScript", "Python"],
        tech_stack={
            "Backend": "FastAPI",
            "Frontend": "React",
            "Database": "PostgreSQL"
        },
        directory_structure={},
        file_count=300,
        total_loc=25000,
        parts=[
            {
                "name": "Frontend",
                "path": "apps/web",
                "type": "React SPA",
                "tech_stack": "React + TypeScript"
            },
            {
                "name": "Backend",
                "path": "apps/api",
                "type": "REST API",
                "tech_stack": "FastAPI + Python"
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
                "name": "handle_request",
                "file": "src/api/routes.py",
                "complexity": 12,
                "call_count": 80,
                "callers": ["main"],
                "calls": [{"name": "validate"}, {"name": "process"}]
            },
            {
                "name": "utility_fn",
                "file": "src/utils.py",
                "complexity": 3,
                "call_count": 120,
                "callers": ["handle_request", "main"],
                "calls": []
            }
        ],
        "classes": [
            {
                "name": "RequestHandler",
                "file": "src/api/routes.py",
                "instantiation_count": 40
            }
        ],
        "dependencies": {
            "src/main.py": ["src/api/routes.py", "src/utils.py"],
            "src/api/routes.py": ["src/utils.py"]
        }
    }

    with open(analysis_path, 'w') as f:
        json.dump(analysis_data, f)

    return analysis_path


def test_generator_initialization(tmp_path):
    """Test overview generator can be initialized."""
    generator = OverviewGenerator(tmp_path)
    assert generator.project_root == tmp_path


def test_format_overview_prompt_monolith(tmp_path, sample_project_data):
    """Test prompt formatting for monolith project."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["src/main.py", "src/api/routes.py", "README.md"]

    prompt = generator.format_overview_prompt(
        sample_project_data,
        key_files,
        max_files=10
    )

    # Verify prompt structure
    assert "# Task: Project Overview Research (Read-Only)" in prompt
    assert "**IMPORTANT: You have READ-ONLY access" in prompt
    assert sample_project_data.project_name in prompt
    assert sample_project_data.project_type in prompt
    assert "12,000" in prompt  # LOC with comma formatting
    assert "src/main.py" in prompt


def test_format_overview_prompt_multipart(tmp_path, multipart_project_data):
    """Test prompt formatting for multi-part project."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["apps/web/package.json", "apps/api/main.py"]

    prompt = generator.format_overview_prompt(
        multipart_project_data,
        key_files,
        max_files=10
    )

    # Verify multi-part structure is included
    assert "monorepo" in prompt
    assert "2 parts" in prompt
    assert "Frontend" in prompt
    assert "Backend" in prompt
    assert "apps/web" in prompt
    assert "apps/api" in prompt
    assert "How Parts Integrate" in prompt


def test_format_overview_prompt_file_limit(tmp_path, sample_project_data):
    """Test that file list is limited to max_files."""
    generator = OverviewGenerator(tmp_path)
    key_files = [f"file{i}.py" for i in range(20)]

    prompt = generator.format_overview_prompt(
        sample_project_data,
        key_files,
        max_files=5
    )

    # Should only include first 5 files
    assert "file0.py" in prompt
    assert "file4.py" in prompt
    assert "file5.py" not in prompt
    assert "file19.py" not in prompt


def test_format_overview_prompt_with_insights(tmp_path, sample_project_data, sample_analysis_data):
    """Test prompt formatting includes codebase analysis insights."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["src/main.py", "README.md"]

    prompt = generator.format_overview_prompt(
        sample_project_data,
        key_files,
        max_files=10,
        analysis_data=sample_analysis_data
    )

    # Verify insights section is present
    assert "### Codebase Analysis Insights" in prompt

    # Check that insights contain expected content
    assert "Codebase Overview" in prompt or "**Codebase Overview:**" in prompt

    # Verify insights are placed after tech stack but before key files
    insights_pos = prompt.find("### Codebase Analysis Insights")
    key_files_pos = prompt.find("## Key Files to Analyze")
    assert insights_pos < key_files_pos


def test_format_overview_prompt_without_insights(tmp_path, sample_project_data):
    """Test prompt formatting without insights (backward compatibility)."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["src/main.py"]

    prompt = generator.format_overview_prompt(
        sample_project_data,
        key_files,
        max_files=10,
        analysis_data=None
    )

    # Should not include insights section
    assert "### Codebase Analysis Insights" not in prompt

    # But should still have all other sections
    assert "## Research Findings to Provide" in prompt
    assert "### 1. Executive Summary" in prompt


def test_format_overview_prompt_with_nonexistent_insights(tmp_path, sample_project_data):
    """Test prompt formatting gracefully handles nonexistent analysis file."""
    generator = OverviewGenerator(tmp_path)
    nonexistent_path = tmp_path / "nonexistent.json"

    # Should not raise exception, just skip insights
    prompt = generator.format_overview_prompt(
        sample_project_data,
        ["src/main.py"],
        max_files=10,
        analysis_data=nonexistent_path
    )

    # Should not include insights section
    assert "### Codebase Analysis Insights" not in prompt


def test_format_overview_prompt_insights_position(tmp_path, sample_project_data, sample_analysis_data):
    """Test that insights are positioned correctly in the prompt."""
    generator = OverviewGenerator(tmp_path)

    prompt = generator.format_overview_prompt(
        sample_project_data,
        ["src/main.py"],
        max_files=10,
        analysis_data=sample_analysis_data
    )

    # Find positions of key sections
    tech_stack_pos = prompt.find("### Technology Stack")
    insights_pos = prompt.find("### Codebase Analysis Insights")
    key_files_pos = prompt.find("## Key Files to Analyze")

    # Verify ordering: tech_stack < insights < key_files
    assert tech_stack_pos < insights_pos < key_files_pos


def test_compose_overview_doc_monolith(sample_project_data):
    """Test document composition for monolith."""
    generator = OverviewGenerator(Path("/tmp"))
    research_findings = """
## Executive Summary

TestProject is a web application that helps users manage their tasks.

## Key Features

- Task management with priorities
- User authentication
- Real-time updates
"""

    doc = generator.compose_overview_doc(
        research_findings,
        sample_project_data,
        "2025-01-15"
    )

    # Verify document structure
    assert "# TestProject - Project Overview" in doc
    assert "**Date:** 2025-01-15" in doc
    assert "**Type:** Web Application" in doc
    assert "## Project Classification" in doc
    assert "**Repository Type:** monolith" in doc
    assert "**Primary Language(s):** Python, TypeScript" in doc
    assert "## Technology Stack Summary" in doc
    assert "FastAPI" in doc
    assert research_findings.strip() in doc
    assert "## Documentation Map" in doc
    assert "*Generated using LLM-based documentation workflow*" in doc


def test_compose_overview_doc_multipart(multipart_project_data):
    """Test document composition for multi-part project."""
    generator = OverviewGenerator(Path("/tmp"))
    research_findings = "## Research findings here"

    doc = generator.compose_overview_doc(
        research_findings,
        multipart_project_data,
        "2025-01-15"
    )

    # Verify multi-part sections
    assert "## Multi-Part Structure" in doc
    assert "2 distinct parts" in doc
    assert "### Frontend" in doc
    assert "### Backend" in doc
    assert "apps/web" in doc
    assert "apps/api" in doc


def test_generate_overview_success(tmp_path, sample_project_data):
    """Test full overview generation workflow."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["main.py"]

    # Mock LLM consultation function
    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        return True, "## Executive Summary\n\nMock findings"

    success, doc = generator.generate_overview(
        sample_project_data,
        key_files,
        mock_llm_fn,
        max_files=10
    )

    assert success is True
    assert "# TestProject - Project Overview" in doc
    assert "Mock findings" in doc


def test_generate_overview_with_insights(tmp_path, sample_project_data, sample_analysis_data):
    """Test full workflow with analysis insights integration."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["src/main.py"]

    # Track what prompt was sent to LLM
    received_prompt = None

    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        nonlocal received_prompt
        received_prompt = prompt
        return True, "## Executive Summary\n\nOverview with insights"

    success, doc = generator.generate_overview(
        sample_project_data,
        key_files,
        mock_llm_fn,
        max_files=10,
        analysis_data=sample_analysis_data
    )

    # Verify success
    assert success is True
    assert "Executive Summary" in doc
    assert "Overview with insights" in doc

    # Verify insights were included in prompt sent to LLM
    assert received_prompt is not None
    assert "### Codebase Analysis Insights" in received_prompt


def test_generate_overview_llm_failure(tmp_path, sample_project_data):
    """Test overview generation handles LLM failure."""
    generator = OverviewGenerator(tmp_path)
    key_files = ["main.py"]

    # Mock failing LLM consultation
    def mock_failing_llm(prompt: str) -> tuple[bool, str]:
        return False, "Connection timeout"

    success, result = generator.generate_overview(
        sample_project_data,
        key_files,
        mock_failing_llm
    )

    assert success is False
    assert "LLM consultation failed" in result
    assert "Connection timeout" in result


def test_prompt_includes_research_sections(tmp_path, sample_project_data):
    """Test that prompt includes all required research sections."""
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(sample_project_data, [], max_files=10)

    # Verify all research sections are present
    assert "### 1. Executive Summary" in prompt
    assert "### 2. Key Features" in prompt
    assert "### 3. Architecture Highlights" in prompt
    assert "### 5. Development Overview" in prompt  # Note: 4 is conditional
    assert "## Output Format" in prompt


def test_prompt_read_only_emphasis(tmp_path, sample_project_data):
    """Test that prompt emphasizes read-only nature."""
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(sample_project_data, [], max_files=10)

    # Should have multiple read-only warnings
    assert prompt.count("READ-ONLY") >= 1
    assert "DO NOT write" in prompt
    assert "Just return your research findings" in prompt


def test_prompt_ignores_specs_directory(tmp_path, sample_project_data):
    """Test that prompt explicitly instructs to ignore specs/ directory."""
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(sample_project_data, [], max_files=10)

    # Verify specs directory is in ignore list
    assert "## Files and Directories to Ignore" in prompt
    assert "`specs/`" in prompt
    assert "Project specifications" in prompt


def test_insights_format_for_overview_generator(tmp_path, sample_project_data, sample_analysis_data):
    """Test that insights are formatted appropriately for overview generator."""
    from claude_skills.llm_doc_gen.analysis.analysis_insights import (
        extract_insights_from_analysis,
        format_insights_for_prompt
    )

    # Extract and format insights
    insights = extract_insights_from_analysis(sample_analysis_data)
    formatted = format_insights_for_prompt(insights, generator_type='overview')

    # Verify format is appropriate (should be compact)
    assert len(formatted) < 1500  # Overview should have ~250 token budget
    assert "**Codebase Overview:**" in formatted

    # Generate prompt and verify insights integration
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(
        sample_project_data,
        ["src/main.py"],
        max_files=10,
        analysis_data=sample_analysis_data
    )

    # Insights should be present and properly formatted
    assert "### Codebase Analysis Insights" in prompt
    assert "**Codebase Overview:**" in prompt


def test_format_overview_prompt_with_analysis_field(tmp_path):
    """Test prompt formatting with legacy analysis field in ProjectData."""
    project_data = ProjectData(
        project_name="AnalysisProject",
        project_type="Library",
        repository_type="monolith",
        primary_languages=["Python"],
        tech_stack={"Framework": "pytest"},
        directory_structure={},
        file_count=50,
        total_loc=5000,
        analysis={
            "modules": [
                {
                    "name": "core.py",
                    "complexity": {"total": 45},
                    "functions": [{"name": "fn1"}, {"name": "fn2"}],
                    "classes": [{"name": "CoreClass"}]
                },
                {
                    "name": "utils.py",
                    "complexity": {"total": 20},
                    "functions": [{"name": "helper"}],
                    "classes": []
                }
            ],
            "statistics": {
                "by_language": {
                    "Python": {"lines": 5000, "files": 50},
                    "Markdown": {"lines": 200, "files": 5}
                }
            }
        }
    )

    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(project_data, [], max_files=10)

    # Verify analysis data is included in prompt
    assert "## Codebase Structure Statistics" in prompt
    assert "### Top Modules by Complexity" in prompt
    assert "core.py" in prompt
    assert "Complexity 45" in prompt
    assert "### Language Breakdown" in prompt
    assert "5,000 lines" in prompt


def test_multipart_prompt_includes_integration_section(tmp_path, multipart_project_data):
    """Test that multi-part prompts include integration points section."""
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(multipart_project_data, [], max_files=10)

    # Multi-part projects should have integration section
    assert "### 4. How Parts Integrate (Multi-Part Projects)" in prompt
    assert "How do the different parts communicate?" in prompt
    assert "What is the data flow between parts?" in prompt


def test_prompt_structure_ordering(tmp_path, sample_project_data):
    """Test that prompt sections appear in the correct order."""
    generator = OverviewGenerator(tmp_path)
    prompt = generator.format_overview_prompt(sample_project_data, ["main.py"], max_files=10)

    # Get positions of major sections
    header_pos = prompt.find("# Task: Project Overview Research")
    ignore_pos = prompt.find("## Files and Directories to Ignore")
    context_pos = prompt.find("## Project Context")
    tech_pos = prompt.find("### Technology Stack")
    files_pos = prompt.find("## Key Files to Analyze")
    research_pos = prompt.find("## Research Findings to Provide")
    output_pos = prompt.find("## Output Format")

    # Verify ordering
    assert header_pos < ignore_pos < context_pos < tech_pos < files_pos < research_pos < output_pos


def test_project_data_with_string_directory_structure():
    """Test ProjectData with string directory_structure (tree representation)."""
    data = ProjectData(
        project_name="TreeProject",
        project_type="CLI Tool",
        repository_type="monolith",
        primary_languages=["Python"],
        tech_stack={"CLI": "Click"},
        directory_structure="src/\n  cli.py\n  commands/\n    run.py",
        file_count=15,
        total_loc=1500
    )

    assert isinstance(data.directory_structure, str)
    assert "src/" in data.directory_structure
    assert "commands/" in data.directory_structure


def test_project_data_with_dict_directory_structure():
    """Test ProjectData with dict directory_structure (legacy format)."""
    data = ProjectData(
        project_name="DictProject",
        project_type="Web App",
        repository_type="monolith",
        primary_languages=["JavaScript"],
        tech_stack={"Frontend": "Vue"},
        directory_structure={"src": {"components": [], "utils": []}},
        file_count=80,
        total_loc=8000
    )

    assert isinstance(data.directory_structure, dict)
    assert "src" in data.directory_structure
