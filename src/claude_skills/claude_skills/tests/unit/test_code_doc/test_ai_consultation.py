"""
Unit tests for code-doc AI consultation module.

Tests prompt formatting, tool detection, and multi-agent coordination.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from claude_skills.code_doc.ai_consultation import (
    format_architecture_research_prompt,
    format_ai_context_research_prompt,
    get_best_tool,
    run_consultation,
    DOC_TYPE_ROUTING
)


class TestPromptFormatting:
    """Tests for prompt formatting functions."""

    def test_format_architecture_prompt_structure(self, temp_project_dir):
        """Architecture prompt should have required structure."""
        context_summary = "## Codebase Context\n**Framework:** FastAPI"
        # Use files that actually exist in temp_project_dir
        key_files = ["main.py", "README.md"]

        prompt = format_architecture_research_prompt(context_summary, key_files, temp_project_dir)

        # Should have task header
        assert "# Task:" in prompt or "ARCHITECTURE.md" in prompt

        # Should include context
        assert "FastAPI" in prompt

        # Should list key files (checks if section exists)
        assert "Key Files" in prompt or "read these files" in prompt.lower()

        # Should have required sections
        assert "System Overview" in prompt
        assert "Architecture" in prompt
        assert "Component" in prompt or "Data Flow" in prompt

    def test_format_architecture_prompt_key_files(self, temp_project_dir):
        """Should include key files to read."""
        context_summary = "## Test"
        # Create files in temp dir so they exist
        (temp_project_dir / "app").mkdir(exist_ok=True)
        (temp_project_dir / "app" / "main.py").write_text("# main")

        key_files = ["app/main.py", "main.py"]

        prompt = format_architecture_research_prompt(context_summary, key_files, temp_project_dir)

        # Should mention at least one existing file
        assert "main.py" in prompt or "app/main.py" in prompt

    def test_format_ai_context_prompt_structure(self, temp_project_dir):
        """AI context prompt should have required structure."""
        context_summary = "## Codebase Context\n**Framework:** FastAPI"
        key_files = ["app/main.py"]

        prompt = format_ai_context_research_prompt(context_summary, key_files, temp_project_dir)

        # Should have task header
        assert "AI_CONTEXT.md" in prompt

        # Should have required sections
        assert "Project Overview" in prompt
        assert "Domain Concepts" in prompt
        assert "Critical Files" in prompt or "Key Files" in prompt
        assert "Common Workflows" in prompt or "Workflow" in prompt

    def test_format_ai_context_prompt_concise(self, temp_project_dir):
        """AI context prompt should emphasize conciseness."""
        context_summary = "## Test"
        key_files = ["main.py"]

        prompt = format_ai_context_research_prompt(context_summary, key_files, temp_project_dir)

        # Should mention being concise or quick reference
        assert "concise" in prompt.lower() or "quick" in prompt.lower() or "brief" in prompt.lower()


class TestToolSelection:
    """Tests for AI tool selection."""

    def test_get_best_tool_for_architecture(self):
        """Should prefer cursor-agent for architecture docs."""
        available_tools = ["cursor-agent", "gemini", "codex"]

        tool = get_best_tool("architecture", available_tools)

        # Should select cursor-agent (1M context)
        assert tool == "cursor-agent"

    def test_get_best_tool_fallback(self):
        """Should fallback when primary tool not available."""
        available_tools = ["gemini", "codex"]  # No cursor-agent

        tool = get_best_tool("architecture", available_tools)

        # Should fallback to gemini (secondary)
        assert tool in available_tools

    def test_get_best_tool_no_tools(self):
        """Should return None when no tools available."""
        tool = get_best_tool("architecture", [])

        assert tool is None

    def test_get_best_tool_unknown_type(self):
        """Should return first available for unknown doc type."""
        available_tools = ["gemini", "codex"]

        tool = get_best_tool("unknown_type", available_tools)

        assert tool == "gemini"  # First in list


class TestConsultation:
    """Tests for run_consultation()."""

    def test_run_consultation_success(self, mock_subprocess_run):
        """Should successfully run consultation."""
        prompt = "Generate documentation"

        success, output = run_consultation("gemini", prompt, dry_run=False, verbose=False)

        assert success is True
        assert "Mock AI" in output

    def test_run_consultation_failure(self, mock_subprocess_run_failure):
        """Should handle consultation failure."""
        prompt = "Generate documentation"

        success, output = run_consultation("gemini", prompt, dry_run=False, verbose=False)

        assert success is False
        assert output != ""  # Should have error message

    def test_run_consultation_dry_run(self):
        """Dry run should not execute subprocess."""
        prompt = "Generate documentation"

        success, output = run_consultation("gemini", prompt, dry_run=True, verbose=False)

        assert success is True
        assert "Dry run" in output

    def test_run_consultation_unknown_tool(self):
        """Should fail for unknown tool."""
        prompt = "Generate documentation"

        success, output = run_consultation("unknown_tool", prompt, dry_run=False, verbose=False)

        assert success is False
        assert "Unknown tool" in output or "unknown_tool" in output.lower()


class TestRoutingMatrix:
    """Tests for documentation type routing."""

    def test_routing_matrix_has_architecture(self):
        """Routing matrix should define architecture routing."""
        assert "architecture" in DOC_TYPE_ROUTING

    def test_routing_matrix_has_ai_context(self):
        """Routing matrix should define ai_context routing."""
        assert "ai_context" in DOC_TYPE_ROUTING

    def test_routing_matrix_valid_tools(self):
        """All routing should specify valid tools."""
        valid_tools = {"cursor-agent", "gemini", "codex"}

        for doc_type, (primary, fallback) in DOC_TYPE_ROUTING.items():
            assert primary in valid_tools or primary == "web"
            assert fallback in valid_tools or fallback == "web"


class TestPromptContentValidation:
    """Tests to ensure prompts contain critical information."""

    def test_architecture_prompt_has_output_format(self, temp_project_dir):
        """Architecture prompt should specify output format."""
        context_summary = "Test"
        key_files = ["main.py"]

        prompt = format_architecture_research_prompt(context_summary, key_files, temp_project_dir)

        # Should specify markdown format
        assert "markdown" in prompt.lower() or "Markdown" in prompt

    def test_architecture_prompt_requests_component_analysis(self, temp_project_dir):
        """Architecture prompt should request component analysis."""
        context_summary = "Test"
        key_files = ["main.py"]

        prompt = format_architecture_research_prompt(context_summary, key_files, temp_project_dir)

        # Should ask for component identification and data flow
        assert "Component Identification" in prompt or "Component" in prompt
        assert "Data Flow" in prompt

    def test_ai_context_prompt_limits_output(self, temp_project_dir):
        """AI context prompt should specify output limits."""
        context_summary = "Test"
        key_files = ["main.py"]

        prompt = format_ai_context_research_prompt(context_summary, key_files, temp_project_dir)

        # Should specify number limits (e.g., "5-10 terms", "3-5 workflows")
        has_limits = any(char.isdigit() for char in prompt)
        assert has_limits

    def test_prompts_include_context_summary(self, temp_project_dir):
        """Both prompts should include the context summary."""
        context_summary = "## Codebase Context\nUnique marker XYZ123"
        key_files = ["main.py"]

        arch_prompt = format_architecture_research_prompt(context_summary, key_files, temp_project_dir)
        context_prompt = format_ai_context_research_prompt(context_summary, key_files, temp_project_dir)

        assert "XYZ123" in arch_prompt
        assert "XYZ123" in context_prompt
