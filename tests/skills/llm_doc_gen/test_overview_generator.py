"""Tests for overview generator."""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.generators.overview_generator import OverviewGenerator, ProjectData


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
    assert research_findings in doc
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
