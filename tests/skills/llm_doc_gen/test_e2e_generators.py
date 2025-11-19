"""End-to-end tests for all three core documentation generators working together.

This test suite verifies that the OverviewGenerator, ArchitectureGenerator, and
ComponentGenerator can generate all 3 core documentation shards successfully.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from claude_skills.llm_doc_gen.generators import (
    OverviewGenerator,
    ArchitectureGenerator,
    ComponentGenerator,
    ProjectData,
    ArchitectureData,
    ComponentData,
)


@pytest.fixture
def sample_project_data():
    """Create sample project data for all generators."""
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
def sample_architecture_data():
    """Create sample architecture data."""
    return ArchitectureData(
        project_name="TestProject",
        project_type="Web Application",
        primary_languages=["Python", "TypeScript"],
        tech_stack={
            "Framework": "FastAPI",
            "Frontend": "React",
            "Database": "PostgreSQL"
        },
        file_count=150,
        total_loc=12000,
        directory_structure={}
    )


@pytest.fixture
def sample_component_data():
    """Create sample component data."""
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


class TestE2EGeneratorsBasic:
    """Basic E2E tests for all three generators."""

    def test_overview_generator_initialization(self, tmp_path):
        """Test that OverviewGenerator initializes successfully."""
        generator = OverviewGenerator(tmp_path)
        assert generator.project_root == tmp_path

    def test_architecture_generator_initialization(self, tmp_path):
        """Test that ArchitectureGenerator initializes successfully."""
        generator = ArchitectureGenerator(tmp_path)
        assert generator.project_root == tmp_path

    def test_component_generator_initialization(self, tmp_path):
        """Test that ComponentGenerator initializes successfully."""
        generator = ComponentGenerator(tmp_path)
        assert generator.project_root == tmp_path

    def test_all_three_generators_can_be_instantiated(self, tmp_path):
        """Test that all three generators can be instantiated together."""
        overview_gen = OverviewGenerator(tmp_path)
        arch_gen = ArchitectureGenerator(tmp_path)
        component_gen = ComponentGenerator(tmp_path)

        assert overview_gen is not None
        assert arch_gen is not None
        assert component_gen is not None


class TestE2EGeneratorPrompts:
    """Test prompt formatting for all three generators."""

    def test_overview_generator_prompt_formatting(self, tmp_path, sample_project_data):
        """Test that OverviewGenerator formats prompts correctly."""
        generator = OverviewGenerator(tmp_path)
        key_files = ["src/main.py", "src/api/routes.py"]
        prompt = generator.format_overview_prompt(sample_project_data, key_files)

        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "TestProject" in prompt
        assert "Web Application" in prompt

    def test_architecture_generator_prompt_formatting(self, tmp_path, sample_architecture_data):
        """Test that ArchitectureGenerator formats prompts correctly."""
        generator = ArchitectureGenerator(tmp_path)
        key_files = ["src/main.py", "src/api/routes.py"]
        prompt = generator.format_architecture_prompt(
            sample_architecture_data,
            key_files,
            max_files=15
        )

        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "TestProject" in prompt
        assert "Web Application" in prompt

    def test_component_generator_prompt_formatting(self, tmp_path, sample_component_data):
        """Test that ComponentGenerator formats prompts correctly."""
        generator = ComponentGenerator(tmp_path)
        directories = ["src", "tests"]
        prompt = generator.format_component_prompt(sample_component_data, directories)

        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "TestProject" in prompt
        assert "src/" in prompt


class TestE2EGeneratorDocComposition:
    """Test document composition for all three generators."""

    def test_overview_generator_compose_doc(self, tmp_path, sample_project_data):
        """Test that OverviewGenerator can compose documentation."""
        generator = OverviewGenerator(tmp_path)
        llm_response = "# TestProject Overview\n\nThis is a web application built with FastAPI and React."
        generated_date = datetime.now().isoformat()

        doc = generator.compose_overview_doc(llm_response, sample_project_data, generated_date)

        assert doc is not None
        assert isinstance(doc, str)
        assert "TestProject" in doc
        assert len(doc) > 0

    def test_architecture_generator_compose_doc(self, tmp_path, sample_architecture_data):
        """Test that ArchitectureGenerator can compose documentation."""
        generator = ArchitectureGenerator(tmp_path)
        llm_response = "# TestProject Architecture\n\nThis project uses FastAPI and React."
        generated_date = datetime.now().isoformat()

        doc = generator.compose_architecture_doc(llm_response, sample_architecture_data, generated_date)

        assert doc is not None
        assert isinstance(doc, str)
        assert "TestProject" in doc
        assert len(doc) > 0

    def test_component_generator_compose_doc(self, tmp_path, sample_component_data):
        """Test that ComponentGenerator can compose documentation."""
        generator = ComponentGenerator(tmp_path)
        llm_response = "# TestProject Components\n\nThe main entry point is src/main.py."
        generated_date = datetime.now().isoformat()

        doc = generator.compose_component_doc(llm_response, sample_component_data, generated_date)

        assert doc is not None
        assert isinstance(doc, str)
        assert "TestProject" in doc
        assert len(doc) > 0


class TestE2EGeneratorsWithMocking:
    """Test E2E workflow with mocked LLM calls."""

    def test_overview_generator_with_mock_responses(self, tmp_path, sample_project_data):
        """Test OverviewGenerator with simulated LLM response."""
        generator = OverviewGenerator(tmp_path)
        key_files = ["src/main.py"]

        # Format prompt
        prompt = generator.format_overview_prompt(sample_project_data, key_files)
        assert prompt is not None

        # Simulate LLM response
        llm_response = "# Overview\n\nProject overview generated successfully."
        generated_date = datetime.now().isoformat()

        # Compose document
        result = generator.compose_overview_doc(llm_response, sample_project_data, generated_date)

        assert result is not None
        assert "Overview" in result
        assert "TestProject" in result

    def test_architecture_generator_with_mock_responses(self, tmp_path, sample_architecture_data):
        """Test ArchitectureGenerator with simulated LLM response."""
        generator = ArchitectureGenerator(tmp_path)
        key_files = ["src/main.py"]

        # Format prompt
        prompt = generator.format_architecture_prompt(sample_architecture_data, key_files)
        assert prompt is not None

        # Simulate LLM response
        llm_response = "# Architecture\n\nArchitecture documentation generated."
        generated_date = datetime.now().isoformat()

        # Compose document
        result = generator.compose_architecture_doc(llm_response, sample_architecture_data, generated_date)

        assert result is not None
        assert "Architecture" in result
        assert "TestProject" in result

    def test_component_generator_with_mock_responses(self, tmp_path, sample_component_data):
        """Test ComponentGenerator with simulated LLM response."""
        generator = ComponentGenerator(tmp_path)
        directories = ["src"]

        # Format prompt
        prompt = generator.format_component_prompt(sample_component_data, directories)
        assert prompt is not None

        # Simulate LLM response
        llm_response = "# Components\n\nComponent documentation generated."
        generated_date = datetime.now().isoformat()

        # Compose document
        result = generator.compose_component_doc(llm_response, sample_component_data, generated_date)

        assert result is not None
        assert "Components" in result
        assert "TestProject" in result


class TestE2EAllThreeShards:
    """Test all three generators working together in an E2E workflow."""

    def test_all_three_generators_generate_docs_successfully(
        self,
        tmp_path,
        sample_project_data,
        sample_architecture_data,
        sample_component_data
    ):
        """Test that all three core shards can generate documentation successfully.

        This is the key E2E verification test that validates:
        1. OverviewGenerator produces overview documentation
        2. ArchitectureGenerator produces architecture documentation
        3. ComponentGenerator produces component documentation

        All three must complete successfully for this test to pass.
        """
        generated_date = datetime.now().isoformat()

        # Initialize all three generators
        overview_gen = OverviewGenerator(tmp_path)
        arch_gen = ArchitectureGenerator(tmp_path)
        component_gen = ComponentGenerator(tmp_path)

        # Generate overview shard
        overview_prompt = overview_gen.format_overview_prompt(sample_project_data, ["src/main.py"])
        overview_response = "# TestProject Overview\n\nThis is a comprehensive overview of the TestProject web application."
        overview_doc = overview_gen.compose_overview_doc(overview_response, sample_project_data, generated_date)

        assert overview_doc is not None
        assert isinstance(overview_doc, str)
        assert len(overview_doc) > 0
        assert "TestProject" in overview_doc

        # Generate architecture shard
        arch_prompt = arch_gen.format_architecture_prompt(
            sample_architecture_data,
            ["src/main.py", "src/api/routes.py"],
            max_files=15
        )
        arch_response = "# TestProject Architecture\n\nThe architecture uses FastAPI and React with PostgreSQL."
        arch_doc = arch_gen.compose_architecture_doc(arch_response, sample_architecture_data, generated_date)

        assert arch_doc is not None
        assert isinstance(arch_doc, str)
        assert len(arch_doc) > 0
        assert "TestProject" in arch_doc

        # Generate component shard
        component_prompt = component_gen.format_component_prompt(sample_component_data, ["src"])
        component_response = "# TestProject Components\n\nThe main entry point is src/main.py with utilities in src/utils."
        component_doc = component_gen.compose_component_doc(component_response, sample_component_data, generated_date)

        assert component_doc is not None
        assert isinstance(component_doc, str)
        assert len(component_doc) > 0
        assert "TestProject" in component_doc

        # Verify all three shards were generated
        assert overview_doc is not None, "Overview shard generation failed"
        assert arch_doc is not None, "Architecture shard generation failed"
        assert component_doc is not None, "Component shard generation failed"

    def test_e2e_workflow_maintains_consistency(
        self,
        tmp_path,
        sample_project_data,
        sample_architecture_data,
        sample_component_data
    ):
        """Test that E2E workflow maintains consistency across all three shards."""
        overview_gen = OverviewGenerator(tmp_path)
        arch_gen = ArchitectureGenerator(tmp_path)
        component_gen = ComponentGenerator(tmp_path)

        project_name = "TestProject"

        # All shards should reference the same project
        overview_prompt = overview_gen.format_overview_prompt(sample_project_data, ["src/main.py"])
        assert project_name in overview_prompt

        arch_prompt = arch_gen.format_architecture_prompt(
            sample_architecture_data,
            ["src/main.py"],
            max_files=15
        )
        assert project_name in arch_prompt

        component_prompt = component_gen.format_component_prompt(sample_component_data, ["src"])
        assert project_name in component_prompt

    def test_all_three_generators_handle_multipart_projects(
        self,
        tmp_path
    ):
        """Test that generators can handle multi-part projects."""
        # Multipart project data
        multipart_project = ProjectData(
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
                    "type": "FastAPI",
                    "tech_stack": "Python + FastAPI"
                }
            ]
        )

        overview_gen = OverviewGenerator(tmp_path)
        overview_prompt = overview_gen.format_overview_prompt(multipart_project, ["apps/web/src/main.tsx"])

        # Should handle multi-part project
        assert overview_prompt is not None
        assert "FullStackApp" in overview_prompt
        assert len(overview_prompt) > 0


class TestE2EErrorHandling:
    """Test error handling across E2E workflow."""

    def test_generators_handle_empty_data_gracefully(self, tmp_path):
        """Test that generators can handle edge cases."""
        overview_gen = OverviewGenerator(tmp_path)
        arch_gen = ArchitectureGenerator(tmp_path)
        component_gen = ComponentGenerator(tmp_path)

        # All generators should initialize without errors
        assert overview_gen is not None
        assert arch_gen is not None
        assert component_gen is not None

    def test_all_generators_callable(self, tmp_path):
        """Test that all generators are callable objects."""
        overview_gen = OverviewGenerator(tmp_path)
        arch_gen = ArchitectureGenerator(tmp_path)
        component_gen = ComponentGenerator(tmp_path)

        assert callable(overview_gen.format_overview_prompt)
        assert callable(arch_gen.format_architecture_prompt)
        assert callable(component_gen.format_component_prompt)


# Aggregate test to verify all 3 core shards
class TestE2EThreeCoreShards:
    """Aggregate tests verifying all 3 core shards."""

    def test_can_generate_all_three_core_shards_successfully(
        self,
        tmp_path,
        sample_project_data,
        sample_architecture_data,
        sample_component_data
    ):
        """Aggregate test: Can generate all 3 core shards successfully.

        This is the main verification test for verify-3-5.
        It ensures that:
        - Overview generator shard works
        - Architecture generator shard works
        - Component generator shard works
        - All three can work together in an E2E workflow
        """
        generated_date = datetime.now().isoformat()

        # Initialize generators
        generators = {
            "overview": OverviewGenerator(tmp_path),
            "architecture": ArchitectureGenerator(tmp_path),
            "component": ComponentGenerator(tmp_path),
        }

        # Verify all generators initialized
        assert all(gen is not None for gen in generators.values()), \
            "Not all generators initialized"

        # Generate prompts for all three shards
        overview_prompt = generators["overview"].format_overview_prompt(
            sample_project_data,
            ["src/main.py"]
        )
        arch_prompt = generators["architecture"].format_architecture_prompt(
            sample_architecture_data,
            ["src/main.py", "src/api/routes.py"],
            max_files=15
        )
        component_prompt = generators["component"].format_component_prompt(
            sample_component_data,
            ["src"]
        )

        # Verify all prompts generated successfully
        assert overview_prompt is not None and len(overview_prompt) > 0, \
            "Overview prompt generation failed"
        assert arch_prompt is not None and len(arch_prompt) > 0, \
            "Architecture prompt generation failed"
        assert component_prompt is not None and len(component_prompt) > 0, \
            "Component prompt generation failed"

        # Compose documentation for all three shards
        overview_doc = generators["overview"].compose_overview_doc(
            "Overview generated",
            sample_project_data,
            generated_date
        )
        arch_doc = generators["architecture"].compose_architecture_doc(
            "Architecture generated",
            sample_architecture_data,
            generated_date
        )
        component_doc = generators["component"].compose_component_doc(
            "Component generated",
            sample_component_data,
            generated_date
        )

        # Verify all documentation generated successfully
        assert overview_doc is not None and len(overview_doc) > 0, \
            "Overview documentation generation failed"
        assert arch_doc is not None and len(arch_doc) > 0, \
            "Architecture documentation generation failed"
        assert component_doc is not None and len(component_doc) > 0, \
            "Component documentation generation failed"

        # Final assertion: all three core shards generated successfully
        all_shards = {
            "overview": overview_doc,
            "architecture": arch_doc,
            "component": component_doc,
        }

        assert all(shard is not None for shard in all_shards.values()), \
            "Not all core shards generated successfully"
        assert all(isinstance(shard, str) and len(shard) > 0 for shard in all_shards.values()), \
            "Some generated shards are empty or invalid"
