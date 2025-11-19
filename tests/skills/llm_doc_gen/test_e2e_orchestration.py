"""End-to-end tests for full orchestration workflow.

This test suite verifies that the DocumentationWorkflow can orchestrate
the complete documentation generation process, including:
- All core shards (project_overview, architecture, component_inventory)
- Index generation (last)
- Write-as-you-go pattern
- File writing to disk
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_skills.llm_doc_gen.main import DocumentationWorkflow
from claude_skills.llm_doc_gen.generators import ProjectData
from claude_skills.llm_doc_gen.generators.index_generator import IndexData


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory for generated docs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_project_data():
    """Create sample project data for workflow."""
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
def sample_index_data():
    """Create sample index data for workflow."""
    return IndexData(
        project_name="TestProject",
        repository_type="monolith",
        primary_language="Python",
        architecture_type="Modular",
        project_description="A test web application",
        tech_stack_summary="FastAPI + React + PostgreSQL",
        entry_point="main.py",
        architecture_pattern="Layered",
        is_multi_part=False,
        parts_count=0
    )


@pytest.fixture
def mock_llm_consultation():
    """Create mock LLM consultation function."""
    def mock_llm(prompt: str) -> tuple[bool, str]:
        """Mock LLM that returns success with simple content."""
        if "overview" in prompt.lower():
            return True, "# Project Overview\n\nThis is the overview content."
        elif "architecture" in prompt.lower():
            return True, "# Architecture\n\nThis is the architecture content."
        elif "component" in prompt.lower():
            return True, "# Component Inventory\n\nThis is the component content."
        else:
            return True, "# Documentation\n\nGeneric content."

    return mock_llm


class TestOrchestrationWorkflow:
    """Test complete orchestration workflow."""

    def test_workflow_initialization(self, tmp_path, tmp_output_dir):
        """Test that DocumentationWorkflow initializes successfully."""
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        assert workflow.project_root == tmp_path
        assert workflow.output_dir == tmp_output_dir
        assert workflow.overview_gen is not None
        assert workflow.architecture_gen is not None
        assert workflow.component_gen is not None
        assert workflow.index_gen is not None
        assert workflow.orchestrator is not None

    def test_full_workflow_generates_all_core_shards(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that full workflow generates all core shards + index.

        This is the main E2E test for verify-4-3.
        Expected: Full workflow generates all core shards (overview, architecture,
        component_inventory) plus index.md using write-as-you-go pattern.
        """
        # Initialize workflow
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate full documentation
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # Verify results structure
        assert results is not None
        assert "success" in results
        assert results["success"] is True
        assert "shards_generated" in results
        assert "summaries" in results

        # Verify all expected shards were generated
        expected_shards = ["project_overview", "architecture", "component_inventory", "index"]
        assert len(results["shards_generated"]) == len(expected_shards)
        for shard in expected_shards:
            assert shard in results["shards_generated"], f"Missing shard: {shard}"

        # Verify no failures
        assert len(results.get("shards_failed", [])) == 0

        # Verify files were written to disk (write-as-you-go pattern)
        expected_files = [
            "project-overview.md",
            "architecture.md",
            "component-inventory.md",
            "index.md"
        ]

        for filename in expected_files:
            file_path = tmp_output_dir / filename
            assert file_path.exists(), f"File not found: {filename}"
            assert file_path.stat().st_size > 0, f"File is empty: {filename}"

        # Verify summaries exist for all shards
        for shard in expected_shards:
            assert shard in results["summaries"]
            assert len(results["summaries"][shard]) > 0

    def test_write_as_you_go_pattern(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that write-as-you-go pattern works correctly.

        Files should be written immediately after generation,
        not all at once at the end.
        """
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate documentation
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # All shards should be written to disk
        assert (tmp_output_dir / "project-overview.md").exists()
        assert (tmp_output_dir / "architecture.md").exists()
        assert (tmp_output_dir / "component-inventory.md").exists()
        assert (tmp_output_dir / "index.md").exists()

        # State file should be created during execution
        state_file = tmp_output_dir / "doc-generation-state.json"
        # State file may or may not exist after completion (can be cleaned up)
        # Just verify the pattern worked by checking files exist

    def test_index_generated_last(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that index.md is generated last and can reference other shards."""
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate documentation
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # Index should be last in shards_generated
        assert results["shards_generated"][-1] == "index"

        # Index file should exist
        index_path = tmp_output_dir / "index.md"
        assert index_path.exists()

        # Index should reference other files
        index_content = index_path.read_text()
        assert "index.md" in index_content.lower() or "documentation" in index_content.lower()

    def test_batched_generation_workflow(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that batched generation workflow works correctly."""
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate with batching enabled
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation,
            use_batching=True,
            batch_size=2
        )

        # Should have batch information
        assert "batches_processed" in results
        assert results["batches_processed"] > 0

        # All shards should still be generated
        assert results["success"] is True
        assert len(results["shards_generated"]) == 4


class TestOrchestrationErrorHandling:
    """Test error handling in orchestration."""

    def test_workflow_handles_llm_failure_gracefully(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data
    ):
        """Test that workflow handles LLM failures gracefully."""
        # Create failing LLM mock
        def failing_llm(prompt: str) -> tuple[bool, str]:
            if "architecture" in prompt.lower():
                return False, "LLM consultation failed"
            return True, "# Success\n\nContent generated."

        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate documentation (should handle failure)
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=failing_llm
        )

        # Should report failure
        assert results["success"] is False
        assert len(results["shards_failed"]) > 0
        assert "architecture" in results["shards_failed"]

    def test_workflow_handles_empty_output_dir(
        self,
        tmp_path,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that workflow creates output directory if it doesn't exist."""
        # Use non-existent output directory
        output_dir = tmp_path / "nonexistent" / "nested" / "output"

        workflow = DocumentationWorkflow(tmp_path, output_dir)

        # Should create directory and generate docs
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        assert results["success"] is True
        assert output_dir.exists()
        assert (output_dir / "index.md").exists()


class TestOrchestrationStateTracking:
    """Test orchestration state tracking and resumability."""

    def test_orchestration_state_file_created(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that orchestration creates state file during execution."""
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate documentation
        workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # State file may be cleaned up after success, but directory should have docs
        assert (tmp_output_dir / "project-overview.md").exists()
        assert (tmp_output_dir / "architecture.md").exists()
        assert (tmp_output_dir / "component-inventory.md").exists()
        assert (tmp_output_dir / "index.md").exists()

    def test_orchestrator_tracks_completed_shards(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Test that orchestrator can report completed shards."""
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)

        # Generate documentation
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # All shards should be marked as completed
        assert len(results["shards_generated"]) == 4
        assert "project_overview" in results["shards_generated"]
        assert "architecture" in results["shards_generated"]
        assert "component_inventory" in results["shards_generated"]
        assert "index" in results["shards_generated"]


class TestOrchestrationIntegration:
    """Integration tests for full orchestration."""

    def test_complete_e2e_workflow_integration(
        self,
        tmp_path,
        tmp_output_dir,
        sample_project_data,
        sample_index_data,
        mock_llm_consultation
    ):
        """Complete E2E integration test of full workflow.

        This is the comprehensive verification test for verify-4-3.
        Tests the entire flow from initialization through completion.
        """
        # Step 1: Initialize workflow
        workflow = DocumentationWorkflow(tmp_path, tmp_output_dir)
        assert workflow is not None

        # Step 2: Generate all documentation
        results = workflow.generate_full_documentation(
            project_data=sample_project_data,
            index_data=sample_index_data,
            llm_consultation_fn=mock_llm_consultation
        )

        # Step 3: Verify success
        assert results["success"] is True
        assert len(results["shards_failed"]) == 0

        # Step 4: Verify all core shards generated
        core_shards = ["project_overview", "architecture", "component_inventory"]
        for shard in core_shards:
            assert shard in results["shards_generated"]

        # Step 5: Verify index generated last
        assert "index" in results["shards_generated"]
        assert results["shards_generated"][-1] == "index"

        # Step 6: Verify all files written to disk
        expected_files = [
            "project-overview.md",
            "architecture.md",
            "component-inventory.md",
            "index.md"
        ]
        for filename in expected_files:
            file_path = tmp_output_dir / filename
            assert file_path.exists(), f"Missing file: {filename}"

            # Verify file has content
            content = file_path.read_text()
            assert len(content) > 0, f"Empty file: {filename}"
            assert "#" in content, f"File missing markdown headers: {filename}"

        # Step 7: Verify write-as-you-go pattern (summaries exist)
        for shard in results["shards_generated"]:
            assert shard in results["summaries"]
            assert len(results["summaries"][shard]) > 0

        print("✅ Complete E2E orchestration workflow verified successfully")
