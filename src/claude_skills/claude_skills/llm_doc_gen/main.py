"""
Main entry point for LLM-based documentation generation.

Coordinates workflow between generators and orchestrator.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .orchestrator import DocumentationOrchestrator
from .generators.overview_generator import OverviewGenerator, ProjectData
from .generators.architecture_generator import ArchitectureGenerator
from .generators.component_generator import ComponentGenerator
from .generators.index_generator import IndexGenerator, IndexData, ProjectPart, ExistingDoc


class DocumentationWorkflow:
    """
    Main workflow coordinator for documentation generation.

    Ties together:
    - Project structure detection
    - Generator coordination (overview, architecture, component, index)
    - Orchestration with write-as-you-go pattern
    """

    def __init__(self, project_root: Path, output_dir: Path):
        """
        Initialize documentation workflow.

        Args:
            project_root: Root directory of project to document
            output_dir: Directory where documentation will be written
        """
        self.project_root = project_root
        self.output_dir = output_dir

        # Initialize generators
        self.overview_gen = OverviewGenerator(project_root)
        self.architecture_gen = ArchitectureGenerator(project_root)
        self.component_gen = ComponentGenerator(project_root)
        self.index_gen = IndexGenerator(project_root)

        # Initialize orchestrator
        self.orchestrator = DocumentationOrchestrator(project_root, output_dir)

    def generate_full_documentation(
        self,
        project_data: ProjectData,
        index_data: IndexData,
        llm_consultation_fn: Callable[[str], tuple[bool, str]],
        use_batching: bool = False,
        batch_size: int = 3
    ) -> Dict[str, Any]:
        """
        Generate complete documentation suite.

        Args:
            project_data: Structured project data for generators
            index_data: Structured data for index generation
            llm_consultation_fn: Function to call LLM (signature: (prompt: str) -> tuple[bool, str])
            use_batching: Whether to use batched generation
            batch_size: Batch size if using batching

        Returns:
            Dict with generation results
        """
        # Define shard generators
        shard_generators = self._create_shard_generators(
            project_data,
            index_data,
            llm_consultation_fn
        )

        # Generate shards with orchestrator (write-as-you-go pattern)
        if use_batching:
            results = self.orchestrator.generate_documentation_batched(
                project_data=self._project_data_to_dict(project_data),
                shard_generators=shard_generators,
                batch_size=batch_size
            )
        else:
            results = self.orchestrator.generate_documentation(
                project_data=self._project_data_to_dict(project_data),
                shard_generators=shard_generators
            )

        return results

    def _create_shard_generators(
        self,
        project_data: ProjectData,
        index_data: IndexData,
        llm_consultation_fn: Callable
    ) -> Dict[str, Callable]:
        """
        Create shard generator functions.

        Returns dict mapping shard names to callables that generate content.
        """
        generators = {}

        # Overview shard
        def generate_overview(data: Dict[str, Any]) -> str:
            success, content = self.overview_gen.generate_overview(
                project_data,
                key_files=data.get("key_files", []),
                llm_consultation_fn=llm_consultation_fn
            )
            if not success:
                raise Exception(f"Overview generation failed: {content}")
            return content

        generators["project_overview"] = generate_overview

        # Architecture shard
        def generate_architecture(data: Dict[str, Any]) -> str:
            # Convert ProjectData to ArchitectureData
            from .generators.architecture_generator import ArchitectureData
            arch_data = ArchitectureData(
                project_name=project_data.project_name,
                project_type=project_data.project_type,
                primary_languages=project_data.primary_languages,
                tech_stack=project_data.tech_stack,
                file_count=project_data.file_count,
                total_loc=project_data.total_loc,
                directory_structure=project_data.directory_structure
            )
            success, content = self.architecture_gen.generate_architecture_doc(
                arch_data,
                key_files=data.get("key_files", []),
                llm_consultation_fn=llm_consultation_fn
            )
            if not success:
                raise Exception(f"Architecture generation failed: {content}")
            return content

        generators["architecture"] = generate_architecture

        # Component inventory shard
        def generate_components(data: Dict[str, Any]) -> str:
            # Convert ProjectData to ComponentData
            from .generators.component_generator import ComponentData
            component_data = ComponentData(
                project_name=project_data.project_name,
                project_root=str(self.project_root),
                is_multi_part=project_data.repository_type in ["monorepo", "multi-part"],
                complete_source_tree=str(project_data.directory_structure),
                critical_folders=[],
                main_entry_point="",
                file_type_patterns=[],
                config_files=[]
            )
            success, content = self.component_gen.generate_component_doc(
                component_data,
                directories_to_analyze=data.get("source_files", []),
                llm_consultation_fn=llm_consultation_fn
            )
            if not success:
                raise Exception(f"Component generation failed: {content}")
            return content

        generators["component_inventory"] = generate_components

        # Index shard (generated last, after other shards exist)
        def generate_index(data: Dict[str, Any]) -> str:
            generated_date = datetime.now().strftime("%Y-%m-%d")
            content = self.index_gen.generate_index(
                index_data,
                generated_date,
                output_dir=self.output_dir  # For auto-detecting existing shards
            )
            return content

        generators["index"] = generate_index

        return generators

    def _project_data_to_dict(self, project_data: ProjectData) -> Dict[str, Any]:
        """Convert ProjectData to dict for orchestrator."""
        return {
            "project_name": project_data.project_name,
            "project_type": project_data.project_type,
            "repository_type": project_data.repository_type,
            "primary_languages": project_data.primary_languages,
            "tech_stack": project_data.tech_stack,
            "file_count": project_data.file_count,
            "total_loc": project_data.total_loc,
            "parts": project_data.parts,
            "key_files": [],  # Populated based on project analysis
            "source_files": []  # Populated based on project analysis
        }


def detect_project_structure(project_root: Path) -> Dict[str, Any]:
    """
    Detect project structure (monolith, monorepo, multi-part).

    Args:
        project_root: Root directory of project

    Returns:
        Dict with structure information
    """
    # Basic structure detection
    # This is a simplified version - full implementation would scan for
    # client/, server/, api/, apps/, packages/, etc.

    structure = {
        "repository_type": "monolith",
        "parts": [],
        "primary_languages": [],
        "tech_stack": {}
    }

    # Check for common multi-part indicators
    common_part_dirs = ["client", "server", "api", "frontend", "backend", "apps", "packages"]
    detected_parts = []

    for dir_name in common_part_dirs:
        part_dir = project_root / dir_name
        if part_dir.exists() and part_dir.is_dir():
            detected_parts.append(dir_name)

    if len(detected_parts) >= 2:
        structure["repository_type"] = "monorepo" if len(detected_parts) > 2 else "multi-part"
        structure["parts"] = detected_parts

    return structure


def scan_project_files(project_root: Path, max_files: int = 50) -> Dict[str, List[str]]:
    """
    Scan project for key files and source files.

    Args:
        project_root: Root directory of project
        max_files: Maximum files to return

    Returns:
        Dict with 'key_files' and 'source_files' lists
    """
    key_files = []
    source_files = []

    # Key files to look for
    key_file_names = [
        "README.md",
        "package.json",
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle"
    ]

    # Find key files
    for file_name in key_file_names:
        file_path = project_root / file_name
        if file_path.exists():
            key_files.append(str(file_path.relative_to(project_root)))

    # Find source files (limited)
    source_extensions = {".py", ".js", ".ts", ".go", ".java", ".rs", ".c", ".cpp"}
    count = 0

    for ext in source_extensions:
        for file_path in project_root.rglob(f"*{ext}"):
            # Skip common ignore dirs
            if any(part in file_path.parts for part in ["node_modules", "dist", "build", ".git", "__pycache__"]):
                continue

            source_files.append(str(file_path.relative_to(project_root)))
            count += 1

            if count >= max_files:
                break

        if count >= max_files:
            break

    return {
        "key_files": key_files,
        "source_files": source_files
    }


def create_project_data_from_scan(
    project_root: Path,
    project_name: str
) -> ProjectData:
    """
    Create ProjectData from project scan.

    Args:
        project_root: Root directory of project
        project_name: Name of the project

    Returns:
        ProjectData instance
    """
    # Detect structure
    structure = detect_project_structure(project_root)

    # Create ProjectData
    # This is simplified - full implementation would detect actual values
    return ProjectData(
        project_name=project_name,
        project_type="Software Project",  # Would be detected
        repository_type=structure["repository_type"],
        primary_languages=["Python"],  # Would be detected
        tech_stack={"Language": "Python"},  # Would be detected
        directory_structure={},
        file_count=0,  # Would be counted
        total_loc=0,  # Would be counted
        parts=None  # Would be populated for multi-part
    )


def create_index_data_from_project(
    project_data: ProjectData,
    project_description: str
) -> IndexData:
    """
    Create IndexData from ProjectData.

    Args:
        project_data: Project data from scan
        project_description: Description of the project

    Returns:
        IndexData instance
    """
    return IndexData(
        project_name=project_data.project_name,
        repository_type=project_data.repository_type,
        primary_language=project_data.primary_languages[0] if project_data.primary_languages else "Unknown",
        architecture_type="Modular",  # Would be detected
        project_description=project_description,
        tech_stack_summary="Python",  # Would be detected
        entry_point="main.py",  # Would be detected
        architecture_pattern="Layered",  # Would be detected
        is_multi_part=project_data.repository_type in ["monorepo", "multi-part"],
        parts_count=len(project_data.parts) if project_data.parts else 0
    )
