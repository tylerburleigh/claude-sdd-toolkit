"""Tests for architecture generator."""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.generators.architecture_generator import (
    ArchitectureGenerator,
    ArchitectureData
)


@pytest.fixture
def sample_arch_data():
    """Create sample architecture data for testing."""
    return ArchitectureData(
        project_name="TestProject",
        project_type="Web Application",
        primary_languages=["Python", "TypeScript"],
        tech_stack={
            "Framework": "FastAPI",
            "Frontend": "React",
            "Database": "PostgreSQL",
            "Cache": "Redis"
        },
        file_count=150,
        total_loc=12000,
        directory_structure={}
    )


@pytest.fixture
def arch_data_with_patterns():
    """Create architecture data with pre-detected patterns."""
    return ArchitectureData(
        project_name="SaaSApp",
        project_type="SaaS Platform",
        primary_languages=["TypeScript", "Python"],
        tech_stack={
            "Backend": "NestJS",
            "Frontend": "Next.js",
            "Database": "PostgreSQL",
            "Queue": "BullMQ"
        },
        file_count=500,
        total_loc=45000,
        directory_structure={},
        detected_patterns=["saas_platform", "realtime_collaboration"],
        quality_attributes=["high_availability", "scalability"]
    )


def test_generator_initialization(tmp_path):
    """Test architecture generator can be initialized."""
    generator = ArchitectureGenerator(tmp_path)
    assert generator.project_root == tmp_path


def test_format_architecture_prompt_basic(tmp_path, sample_arch_data):
    """Test basic architecture prompt formatting."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = ["src/main.py", "src/api/routes.py", "src/models/user.py"]

    prompt = generator.format_architecture_prompt(
        sample_arch_data,
        key_files,
        max_files=15
    )

    # Verify prompt structure
    assert "# Task: Architecture Analysis Research (Read-Only)" in prompt
    assert "**IMPORTANT: You have READ-ONLY access" in prompt
    assert sample_arch_data.project_name in prompt
    assert sample_arch_data.project_type in prompt
    assert "12,000" in prompt  # LOC with comma formatting

    # Verify key files included
    assert "src/main.py" in prompt
    assert "src/api/routes.py" in prompt
    assert "src/models/user.py" in prompt


def test_format_architecture_prompt_with_patterns(tmp_path, arch_data_with_patterns):
    """Test architecture prompt with pre-detected patterns."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = ["src/app.ts"]

    prompt = generator.format_architecture_prompt(
        arch_data_with_patterns,
        key_files,
        max_files=15
    )

    # Verify pre-detected patterns section
    assert "### Pre-Detected Patterns" in prompt
    assert "saas_platform" in prompt
    assert "realtime_collaboration" in prompt

    # Verify quality attributes section
    assert "### Pre-Detected Quality Attributes" in prompt
    assert "high_availability" in prompt
    assert "scalability" in prompt


def test_format_architecture_prompt_file_limit(tmp_path, sample_arch_data):
    """Test that file list is limited to max_files."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = [f"file{i}.py" for i in range(25)]

    prompt = generator.format_architecture_prompt(
        sample_arch_data,
        key_files,
        max_files=10
    )

    # Should only include first 10 files
    assert "file0.py" in prompt
    assert "file9.py" in prompt
    assert "file10.py" not in prompt
    assert "file24.py" not in prompt


def test_format_architecture_prompt_research_sections(tmp_path, sample_arch_data):
    """Test that prompt includes all required research sections."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Verify all major research sections are present
    assert "### 1. Executive Summary" in prompt
    assert "### 2. Architecture Pattern Identification" in prompt
    assert "### 3. Key Architectural Decisions" in prompt
    assert "### 4. Project Structure Analysis" in prompt
    assert "### 5. Technology Integration Points" in prompt
    assert "### 6. Implementation Patterns" in prompt
    assert "### 7. Data Architecture" in prompt
    assert "### 8. Security Architecture" in prompt
    assert "### 9. Performance Considerations" in prompt
    assert "### 10. Novel or Unique Design Patterns" in prompt


def test_format_architecture_prompt_pattern_types(tmp_path, sample_arch_data):
    """Test that prompt includes architecture pattern types."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Verify architecture patterns are described
    assert "Layered Architecture" in prompt
    assert "Microservices" in prompt
    assert "Event-Driven" in prompt
    assert "Client-Server" in prompt
    assert "Plugin Architecture" in prompt
    assert "Monolith" in prompt


def test_format_architecture_prompt_decision_table(tmp_path, sample_arch_data):
    """Test that prompt includes decision table template."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Verify decision table structure
    assert "| Decision Category | Choice Made | Rationale/Evidence |" in prompt
    assert "| Database Architecture |" in prompt
    assert "| API Pattern |" in prompt
    assert "| State Management |" in prompt
    assert "| Authentication/Authorization |" in prompt
    assert "| Deployment Model |" in prompt


def test_compose_architecture_doc_basic(sample_arch_data):
    """Test basic architecture document composition."""
    generator = ArchitectureGenerator(Path("/tmp"))
    research_findings = """
## Executive Summary

This is a layered web application built with FastAPI and React.

## Architecture Pattern

The application follows a client-server pattern with clear separation.
"""

    doc = generator.compose_architecture_doc(
        research_findings,
        sample_arch_data,
        "2025-01-15"
    )

    # Verify document structure
    assert "# TestProject - Architecture Documentation" in doc
    assert "**Date:** 2025-01-15" in doc
    assert "**Project Type:** Web Application" in doc
    assert "**Primary Language(s):** Python, TypeScript" in doc
    assert "## Technology Stack Details" in doc
    assert "FastAPI" in doc
    assert "React" in doc
    assert "PostgreSQL" in doc
    assert research_findings in doc
    assert "## Related Documentation" in doc
    assert "*Generated using LLM-based documentation workflow*" in doc


def test_compose_architecture_doc_with_patterns(arch_data_with_patterns):
    """Test architecture document composition with pre-detected patterns."""
    generator = ArchitectureGenerator(Path("/tmp"))
    research_findings = "## Analysis results"

    doc = generator.compose_architecture_doc(
        research_findings,
        arch_data_with_patterns,
        "2025-01-15"
    )

    # Verify pattern sections
    assert "## Detected Patterns and Attributes" in doc
    assert "### Requirement Patterns" in doc
    assert "saas_platform" in doc
    assert "realtime_collaboration" in doc
    assert "### Quality Attributes" in doc
    assert "high_availability" in doc
    assert "scalability" in doc


def test_compose_architecture_doc_tech_stack(sample_arch_data):
    """Test that tech stack is properly included in composed document."""
    generator = ArchitectureGenerator(Path("/tmp"))
    research_findings = "Research"

    doc = generator.compose_architecture_doc(
        research_findings,
        sample_arch_data,
        "2025-01-15"
    )

    # Verify all tech stack items are included
    assert "**Framework:** FastAPI" in doc
    assert "**Frontend:** React" in doc
    assert "**Database:** PostgreSQL" in doc
    assert "**Cache:** Redis" in doc


def test_generate_architecture_doc_success(tmp_path, sample_arch_data):
    """Test full architecture documentation generation workflow."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py", "api.py"]

    # Mock LLM consultation function
    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        return True, "## Architecture Analysis\n\nLayered architecture detected"

    success, doc = generator.generate_architecture_doc(
        sample_arch_data,
        key_files,
        mock_llm_fn,
        max_files=15
    )

    assert success is True
    assert "# TestProject - Architecture Documentation" in doc
    assert "Layered architecture detected" in doc


def test_generate_architecture_doc_llm_failure(tmp_path, sample_arch_data):
    """Test architecture generation handles LLM failure."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py"]

    # Mock failing LLM consultation
    def mock_failing_llm(prompt: str) -> tuple[bool, str]:
        return False, "Connection timeout"

    success, result = generator.generate_architecture_doc(
        sample_arch_data,
        key_files,
        mock_failing_llm
    )

    assert success is False
    assert "LLM consultation failed" in result
    assert "Connection timeout" in result


def test_prompt_read_only_emphasis(tmp_path, sample_arch_data):
    """Test that prompt emphasizes read-only nature."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Should have multiple read-only warnings
    assert prompt.count("READ-ONLY") >= 1
    assert "DO NOT write" in prompt
    assert "Just return your research findings" in prompt


def test_prompt_implementation_patterns_section(tmp_path, sample_arch_data):
    """Test that prompt includes implementation patterns guidance."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Verify implementation patterns sub-sections
    assert "**Naming Conventions:**" in prompt
    assert "**Code Organization:**" in prompt
    assert "**Error Handling:**" in prompt
    assert "**Logging/Monitoring:**" in prompt


def test_prompt_output_format_guidance(tmp_path, sample_arch_data):
    """Test that prompt includes clear output format guidance."""
    generator = ArchitectureGenerator(tmp_path)
    prompt = generator.format_architecture_prompt(sample_arch_data, [], max_files=15)

    # Verify output format section
    assert "## Output Format" in prompt
    assert "structured text" in prompt
    assert "markdown formatting" in prompt
    assert "reference actual files/code" in prompt
    assert "evidence-based analysis" in prompt


def test_architecture_data_defaults():
    """Test ArchitectureData dataclass with default values."""
    data = ArchitectureData(
        project_name="Test",
        project_type="Application",
        primary_languages=["Python"],
        tech_stack={},
        file_count=100,
        total_loc=5000,
        directory_structure={}
    )

    assert data.detected_patterns is None
    assert data.quality_attributes is None


def test_architecture_data_with_optional_fields():
    """Test ArchitectureData with all optional fields."""
    data = ArchitectureData(
        project_name="Test",
        project_type="Application",
        primary_languages=["Python"],
        tech_stack={"Framework": "Django"},
        file_count=100,
        total_loc=5000,
        directory_structure={},
        detected_patterns=["api_service"],
        quality_attributes=["performance"]
    )

    assert data.detected_patterns == ["api_service"]
    assert data.quality_attributes == ["performance"]


def test_generate_architecture_doc_multi_model_success(tmp_path, sample_arch_data):
    """Test multi-model architecture generation with successful consultations."""
    from unittest.mock import Mock, patch
    from claude_skills.llm_doc_gen.ai_consultation import ConsultationResult

    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py"]

    # Mock consultation results from multiple providers
    mock_results = {
        "provider1": ConsultationResult(
            success=True,
            output="## Architecture\n\nLayered architecture detected.",
            tool_used="provider1",
            duration=1.5
        ),
        "provider2": ConsultationResult(
            success=True,
            output="## Architecture\n\nMicroservices pattern identified.",
            tool_used="provider2",
            duration=2.0
        )
    }

    with patch('claude_skills.llm_doc_gen.ai_consultation.consult_multi_agent', return_value=mock_results):
        success, doc = generator.generate_architecture_doc_multi_model(
            sample_arch_data,
            key_files,
            providers=["provider1", "provider2"],
            max_files=15
        )

    assert success is True
    assert "# TestProject - Architecture Documentation" in doc
    assert "Multi-Model Architecture Analysis" in doc
    assert "provider1" in doc
    assert "provider2" in doc
    assert "Layered architecture detected" in doc
    assert "Microservices pattern identified" in doc


def test_generate_architecture_doc_multi_model_partial_failure(tmp_path, sample_arch_data):
    """Test multi-model generation with some providers failing."""
    from unittest.mock import patch
    from claude_skills.llm_doc_gen.ai_consultation import ConsultationResult

    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py"]

    # Mix of successful and failed results
    mock_results = {
        "provider1": ConsultationResult(
            success=True,
            output="## Architecture Analysis\n\nDetailed findings here.",
            tool_used="provider1",
            duration=1.5
        ),
        "provider2": ConsultationResult(
            success=False,
            output="",
            error="Connection timeout",
            tool_used="provider2",
            duration=120.0
        )
    }

    with patch('claude_skills.llm_doc_gen.ai_consultation.consult_multi_agent', return_value=mock_results):
        success, doc = generator.generate_architecture_doc_multi_model(
            sample_arch_data,
            key_files,
            providers=["provider1", "provider2"]
        )

    # Should succeed with partial results
    assert success is True
    assert "provider1" in doc
    assert "Detailed findings here" in doc


def test_generate_architecture_doc_multi_model_all_fail(tmp_path, sample_arch_data):
    """Test multi-model generation when all providers fail."""
    from unittest.mock import patch
    from claude_skills.llm_doc_gen.ai_consultation import ConsultationResult

    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py"]

    # All failed results
    mock_results = {
        "provider1": ConsultationResult(
            success=False,
            output="",
            error="Connection timeout",
            tool_used="provider1",
            duration=120.0
        ),
        "provider2": ConsultationResult(
            success=False,
            output="",
            error="Service unavailable",
            tool_used="provider2",
            duration=120.0
        )
    }

    with patch('claude_skills.llm_doc_gen.ai_consultation.consult_multi_agent', return_value=mock_results):
        success, result = generator.generate_architecture_doc_multi_model(
            sample_arch_data,
            key_files
        )

    # Should fail when all providers fail
    assert success is False
    assert "All model consultations failed" in result
    assert "Connection timeout" in result
    assert "Service unavailable" in result


def test_synthesize_multi_model_findings(tmp_path, sample_arch_data):
    """Test synthesis of findings from multiple models."""
    from claude_skills.llm_doc_gen.ai_consultation import ConsultationResult

    generator = ArchitectureGenerator(tmp_path)

    results = {
        "claude": ConsultationResult(
            success=True,
            output="Finding from Claude",
            tool_used="claude",
            duration=1.0
        ),
        "gemini": ConsultationResult(
            success=True,
            output="Finding from Gemini",
            tool_used="gemini",
            duration=1.2
        )
    }

    synthesis = generator._synthesize_multi_model_findings(results, sample_arch_data)

    # Verify synthesis structure
    assert "Multi-Model Architecture Analysis" in synthesis
    assert "2 AI models" in synthesis
    assert "claude" in synthesis
    assert "gemini" in synthesis
    assert "Finding from Claude" in synthesis
    assert "Finding from Gemini" in synthesis
    assert "Synthesis Summary" in synthesis
    assert "Consensus Patterns" in synthesis
    assert "Unique Insights" in synthesis
    assert "Recommended Next Steps" in synthesis


def test_format_architecture_prompt_with_analysis_insights(tmp_path, sample_arch_data):
    """Test architecture prompt with codebase analysis insights."""
    import json

    generator = ArchitectureGenerator(tmp_path)
    key_files = ["src/main.py"]

    # Create a mock codebase.json analysis file
    analysis_file = tmp_path / "codebase.json"
    mock_analysis = {
        "statistics": {
            "total_files": 150,
            "total_lines": 12000,
            "by_language": {
                "Python": {"files": 120, "lines": 10000},
                "TypeScript": {"files": 30, "lines": 2000}
            }
        },
        "analysis": {
            "modules": [
                {
                    "name": "main",
                    "path": "src/main.py",
                    "functions": [{"name": "app_startup", "lines": 50}],
                    "classes": []
                }
            ]
        }
    }
    analysis_file.write_text(json.dumps(mock_analysis))

    # Generate prompt with analysis insights
    prompt = generator.format_architecture_prompt(
        sample_arch_data,
        key_files,
        max_files=15,
        analysis_data=analysis_file
    )

    # Verify insights section is included
    assert "### Codebase Analysis Insights" in prompt

    # Basic structure should still be present
    assert "# Task: Architecture Analysis Research (Read-Only)" in prompt
    assert sample_arch_data.project_name in prompt


def test_format_architecture_prompt_with_missing_analysis_file(tmp_path, sample_arch_data):
    """Test that missing analysis file is handled gracefully."""
    generator = ArchitectureGenerator(tmp_path)
    key_files = ["src/main.py"]

    # Point to non-existent file
    non_existent_file = tmp_path / "nonexistent.json"

    # Should not raise exception
    prompt = generator.format_architecture_prompt(
        sample_arch_data,
        key_files,
        max_files=15,
        analysis_data=non_existent_file
    )

    # Should generate prompt without insights section
    assert "# Task: Architecture Analysis Research (Read-Only)" in prompt
    assert "### Codebase Analysis Insights" not in prompt


def test_generate_architecture_doc_with_analysis_data(tmp_path, sample_arch_data):
    """Test generate_architecture_doc accepts and uses analysis_data parameter."""
    import json

    generator = ArchitectureGenerator(tmp_path)
    key_files = ["main.py"]

    # Create analysis file
    analysis_file = tmp_path / "codebase.json"
    mock_analysis = {
        "statistics": {"total_files": 150, "total_lines": 12000},
        "analysis": {"modules": []}
    }
    analysis_file.write_text(json.dumps(mock_analysis))

    # Mock LLM consultation
    def mock_llm_fn(prompt: str) -> tuple[bool, str]:
        # Verify prompt contains insights section
        assert "### Codebase Analysis Insights" in prompt
        return True, "## Architecture Analysis\n\nDetailed findings"

    success, doc = generator.generate_architecture_doc(
        sample_arch_data,
        key_files,
        mock_llm_fn,
        max_files=15,
        analysis_data=analysis_file
    )

    assert success is True
    assert "# TestProject - Architecture Documentation" in doc
