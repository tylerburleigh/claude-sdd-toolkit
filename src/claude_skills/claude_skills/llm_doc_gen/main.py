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
        batch_size: int = 3,
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Generate complete documentation suite.

        Args:
            project_data: Structured project data for generators
            index_data: Structured data for index generation
            llm_consultation_fn: Function to call LLM (signature: (prompt: str) -> tuple[bool, str])
            use_batching: Whether to use batched generation
            batch_size: Batch size if using batching
            resume: Whether to resume from previous interrupted generation

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
                batch_size=batch_size,
                resume=resume
            )
        else:
            results = self.orchestrator.generate_documentation(
                project_data=self._project_data_to_dict(project_data),
                shard_generators=shard_generators,
                resume=resume
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
            # Determine path to codebase.json for analysis insights
            analysis_data_path = self.output_dir / "codebase.json" if self.output_dir else None

            success, content = self.overview_gen.generate_overview(
                project_data,
                key_files=data.get("key_files", []),
                llm_consultation_fn=llm_consultation_fn,
                analysis_data=analysis_data_path
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

            # Determine path to codebase.json for analysis insights
            analysis_data_path = self.output_dir / "codebase.json" if self.output_dir else None

            success, content = self.architecture_gen.generate_architecture_doc(
                arch_data,
                key_files=data.get("key_files", []),
                llm_consultation_fn=llm_consultation_fn,
                analysis_data=analysis_data_path
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

            # Determine path to codebase.json for analysis insights
            analysis_data_path = self.output_dir / "codebase.json" if self.output_dir else None

            success, content = self.component_gen.generate_component_doc(
                component_data,
                directories_to_analyze=data.get("source_files", []),
                llm_consultation_fn=llm_consultation_fn,
                analysis_data=analysis_data_path
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


def build_directory_tree(project_root: Path, max_depth: int = 3) -> str:
    """
    Build a text-based directory tree representation.

    Args:
        project_root: Root directory to scan
        max_depth: Maximum depth to traverse

    Returns:
        String representation of directory tree
    """
    def _tree_recursive(path: Path, prefix: str = "", depth: int = 0) -> List[str]:
        """Recursive helper to build tree structure."""
        if depth > max_depth:
            return []

        # Skip common ignore dirs
        ignore_dirs = {
            "node_modules", "dist", "build", ".git", "__pycache__",
            ".venv", "venv", ".tox", ".pytest_cache", ".mypy_cache",
            ".eggs", "*.egg-info", "__pypackages__", ".coverage",
            "specs", ".claude", ".agents"
        }

        items = []
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return []

        # Filter out ignored directories
        entries = [e for e in entries if e.name not in ignore_dirs and not e.name.startswith('.')]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            items.append(f"{prefix}{connector}{entry.name}")

            # Recurse into directories
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                items.extend(_tree_recursive(entry, prefix + extension, depth + 1))

        return items

    tree_lines = [project_root.name + "/"]
    tree_lines.extend(_tree_recursive(project_root))
    return "\n".join(tree_lines)


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
            if any(part in file_path.parts for part in ["node_modules", "dist", "build", ".git", "__pycache__", "specs", ".claude", ".agents"]):
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
    project_name: str,
    output_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None
) -> ProjectData:
    """
    Create ProjectData from project scan using DocumentationGenerator.

    Args:
        project_root: Root directory of project
        project_name: Name of the project
        cache_dir: Optional cache directory for persistent caching
        output_dir: Optional output directory to save codebase.json

    Returns:
        ProjectData instance populated with analysis data
    """
    from .analysis.generator import DocumentationGenerator

    # Initialize DocumentationGenerator
    generator = DocumentationGenerator(
        project_dir=project_root,
        project_name=project_name,
        version="1.0.0",
        exclude_patterns=[],
        cache_dir=cache_dir
    )

    # Run the generator (verbose=False for silent operation)
    result = generator.generate(verbose=False)

    # Save JSON artifact as codebase.json (DO NOT save markdown)
    if output_dir:
        output_path = output_dir / "codebase.json"
        generator.save_json(
            output_path=output_path,
            analysis=result.get("analysis", {}),
            statistics=result.get("statistics", {}),
            verbose=False
        )

    # Extract statistics and full analysis from result
    statistics = result.get("statistics", {})
    analysis = {
        "modules": result.get("analysis", {}).get("modules", []),
        "statistics": statistics
    }

    # Detect structure
    structure = detect_project_structure(project_root)

    # Build directory tree
    directory_tree = build_directory_tree(project_root, max_depth=3)

    # Extract languages from statistics
    languages_data = statistics.get("by_language", {})
    primary_languages = sorted(
        languages_data.keys(),
        key=lambda lang: languages_data[lang].get("lines", 0),
        reverse=True
    )[:3] if languages_data else ["Unknown"]

    # Build tech stack from detected info
    tech_stack = {}
    if primary_languages:
        tech_stack["Languages"] = ", ".join(primary_languages)

    # Create ProjectData with actual analysis data
    return ProjectData(
        project_name=project_name,
        project_type="Software Project",
        repository_type=structure["repository_type"],
        primary_languages=primary_languages,
        tech_stack=tech_stack,
        directory_structure=directory_tree,
        file_count=statistics.get("total_files", 0),
        total_loc=statistics.get("total_lines", 0),
        parts=None,  # Would be populated for multi-part
        analysis=analysis  # Include analysis data for prompt enhancement
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
        parts_count=len(project_data.parts) if project_data.parts else 0,
        file_count=project_data.file_count,  # Pass statistics from ProjectData
        total_loc=project_data.total_loc,  # Pass LOC count
        primary_languages=project_data.primary_languages  # Pass language list
    )
