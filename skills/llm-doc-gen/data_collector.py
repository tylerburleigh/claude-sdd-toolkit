"""
Data collection orchestration for LLM-based documentation generation.

This module coordinates parsing, statistics collection, and data aggregation
to prepare comprehensive project data for LLM consumption.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import json

# Import local modules
from .parsers import DeepScanParser, ScanConfig, ScanResult
from .detectors import ProjectStructureDetector, ProjectStructureInfo
from .state_manager import (
    StateManager,
    DocumentationState,
    ProcessingStatus,
    create_state_manager
)


@dataclass
class CollectionConfig:
    """Configuration for data collection."""
    project_root: Path
    output_folder: Path

    # Scan configuration
    exclude_patterns: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    max_files_per_language: Optional[int] = None

    # State management
    resume_if_available: bool = True
    verbose: bool = False


@dataclass
class ProjectMetadata:
    """Aggregated project metadata."""
    project_root: str
    structure_info: Dict[str, Any]

    # File counts
    total_files: int = 0
    files_by_language: Dict[str, int] = field(default_factory=dict)

    # Code entity counts
    total_modules: int = 0
    total_classes: int = 0
    total_functions: int = 0

    # Per-language statistics
    language_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'project_root': self.project_root,
            'structure_info': self.structure_info,
            'total_files': self.total_files,
            'files_by_language': self.files_by_language,
            'total_modules': self.total_modules,
            'total_classes': self.total_classes,
            'total_functions': self.total_functions,
            'language_statistics': self.language_statistics
        }


@dataclass
class CollectionResult:
    """Result of data collection orchestration."""
    metadata: ProjectMetadata
    scan_result: ScanResult
    state: DocumentationState

    # Collection statistics
    collection_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'metadata': self.metadata.to_dict(),
            'scan_result': self.scan_result.to_dict(),
            'state': self.state.to_dict(),
            'collection_time_seconds': self.collection_time_seconds,
            'errors': self.errors
        }


class DataCollector:
    """
    Orchestrates data collection for documentation generation.

    Responsibilities:
    - Coordinate project structure detection
    - Orchestrate code parsing via DeepScanParser
    - Collect and aggregate statistics
    - Manage state for resumability
    - Prepare data for LLM consumption
    """

    def __init__(self, config: CollectionConfig):
        """
        Initialize the data collector.

        Args:
            config: Collection configuration
        """
        self.config = config
        self.project_root = config.project_root.resolve()
        self.output_folder = config.output_folder.resolve()
        self.verbose = config.verbose

        # Initialize state manager
        self.state_manager = create_state_manager(
            str(self.output_folder),
            verbose=self.verbose
        )

        # Initialize structure detector
        self.structure_detector = ProjectStructureDetector(
            self.project_root,
            verbose=self.verbose
        )

    def collect(self) -> CollectionResult:
        """
        Execute the full data collection workflow.

        Returns:
            CollectionResult with all collected data and state
        """
        import time
        start_time = time.time()

        errors = []

        try:
            # Step 1: Check for resumable session
            state = self._initialize_or_resume_state()

            # Step 2: Detect project structure
            if self.verbose:
                print("\n🔍 Phase 1: Detecting project structure...")

            self.state_manager.start_workflow_step(state, "structure_detection")
            structure_info = self._detect_project_structure(state)
            self.state_manager.complete_workflow_step(state)
            self.state_manager.save_state(state)

            # Step 3: Parse codebase
            if self.verbose:
                print("\n📝 Phase 2: Parsing codebase...")

            self.state_manager.start_workflow_step(state, "parsing")
            scan_result = self._parse_codebase(state)
            self.state_manager.complete_workflow_step(state)
            self.state_manager.save_state(state)

            # Step 4: Aggregate metadata
            if self.verbose:
                print("\n📊 Phase 3: Aggregating metadata...")

            self.state_manager.start_workflow_step(state, "aggregation")
            metadata = self._aggregate_metadata(structure_info, scan_result, state)
            self.state_manager.complete_workflow_step(state)
            self.state_manager.save_state(state)

            # Mark collection phase complete
            if "collection" not in state.phases_completed:
                state.phases_completed.append("collection")
            state.current_phase = "generation"
            self.state_manager.save_state(state)

        except Exception as e:
            errors.append(f"Collection failed: {str(e)}")
            if self.verbose:
                print(f"\n❌ Error: {e}")
            raise

        finally:
            collection_time = time.time() - start_time

        result = CollectionResult(
            metadata=metadata,
            scan_result=scan_result,
            state=state,
            collection_time_seconds=collection_time,
            errors=errors
        )

        if self.verbose:
            self._print_collection_summary(result)

        return result

    def _initialize_or_resume_state(self) -> DocumentationState:
        """Initialize new state or resume existing session."""
        if self.config.resume_if_available and self.state_manager.check_resume_available():
            if self.verbose:
                print(self.state_manager.format_resume_prompt())
                print("\n✅ Resuming previous session...\n")

            state = self.state_manager.load_state()
            if state is None:
                raise RuntimeError("Failed to load resumable state")

            self.state_manager.add_finding(
                state,
                "info",
                "Session resumed",
                {"session_id": state.session_id}
            )

            return state

        # Create new state
        if self.verbose:
            print("📝 Starting new documentation session...\n")

        state = self.state_manager.create_new_state(
            project_root=self.project_root,
            exclude_patterns=self.config.exclude_patterns or []
        )
        state.current_phase = "collection"

        self.state_manager.save_state(state)
        return state

    def _detect_project_structure(self, state: DocumentationState) -> ProjectStructureInfo:
        """Detect and analyze project structure."""
        structure_info = self.structure_detector.detect()

        # Record findings
        self.state_manager.add_finding(
            state,
            "metric",
            f"Project structure: {structure_info.structure_type.value}",
            {
                "structure_type": structure_info.structure_type.value,
                "project_type": structure_info.project_type.value if structure_info.project_type else None,
                "parts_count": len(structure_info.parts),
                "confidence": structure_info.confidence
            }
        )

        if structure_info.parts:
            parts_summary = ", ".join(p.name for p in structure_info.parts[:5])
            if len(structure_info.parts) > 5:
                parts_summary += f", ... ({len(structure_info.parts)} total)"

            self.state_manager.add_finding(
                state,
                "insight",
                f"Detected {len(structure_info.parts)} project parts: {parts_summary}",
                {"parts": [p.name for p in structure_info.parts]}
            )

        return structure_info

    def _parse_codebase(self, state: DocumentationState) -> ScanResult:
        """Parse codebase using DeepScanParser."""
        scan_config = ScanConfig(
            project_root=self.project_root,
            exclude_patterns=self.config.exclude_patterns,
            languages=None,  # Auto-detect
            max_files_per_language=self.config.max_files_per_language,
            verbose=self.verbose
        )

        parser = DeepScanParser(scan_config)
        scan_result = parser.scan()

        # Update state with file information
        state.total_files = scan_result.files_scanned
        state.languages_detected = [lang.value for lang in scan_result.languages_detected]

        # Track individual files
        for module in scan_result.parse_result.modules:
            file_path = str(module.file_path)

            # Determine language from file extension
            lang = self._guess_language(Path(file_path))

            # Calculate entity count for this file
            entity_count = len([c for c in scan_result.parse_result.classes if c.file_path == file_path])
            entity_count += len([f for f in scan_result.parse_result.functions if f.file_path == file_path])

            self.state_manager.update_file_status(
                state,
                file_path=file_path,
                status=ProcessingStatus.COMPLETED,
                entity_count=entity_count
            )

            if lang:
                state.files[file_path].language = lang

        # Record scan findings
        self.state_manager.add_finding(
            state,
            "metric",
            f"Scanned {scan_result.files_scanned} files across {len(scan_result.languages_detected)} languages",
            {
                "files_scanned": scan_result.files_scanned,
                "files_skipped": scan_result.files_skipped,
                "languages": [lang.value for lang in scan_result.languages_detected]
            }
        )

        self.state_manager.add_finding(
            state,
            "metric",
            f"Found {len(scan_result.parse_result.classes)} classes, {len(scan_result.parse_result.functions)} functions",
            {
                "classes": len(scan_result.parse_result.classes),
                "functions": len(scan_result.parse_result.functions),
                "modules": len(scan_result.parse_result.modules)
            }
        )

        if scan_result.errors:
            self.state_manager.add_finding(
                state,
                "warning",
                f"Encountered {len(scan_result.errors)} parsing errors",
                {"error_count": len(scan_result.errors)}
            )

        return scan_result

    def _aggregate_metadata(
        self,
        structure_info: ProjectStructureInfo,
        scan_result: ScanResult,
        state: DocumentationState
    ) -> ProjectMetadata:
        """Aggregate all collected data into project metadata."""
        # Count files by language
        files_by_language: Dict[str, int] = {}
        for file_path, file_state in state.files.items():
            if file_state.language:
                files_by_language[file_state.language] = files_by_language.get(file_state.language, 0) + 1

        # Get language statistics from parser
        lang_stats = {}
        if hasattr(scan_result.parse_result, 'language_statistics'):
            lang_stats = scan_result.parse_result.language_statistics
        else:
            # Build from scan result if not available
            from .parsers import DeepScanParser
            parser = DeepScanParser(ScanConfig(project_root=self.project_root))
            lang_stats = parser.get_language_statistics(scan_result)

        metadata = ProjectMetadata(
            project_root=str(self.project_root),
            structure_info=structure_info.to_dict(),
            total_files=scan_result.files_scanned,
            files_by_language=files_by_language,
            total_modules=len(scan_result.parse_result.modules),
            total_classes=len(scan_result.parse_result.classes),
            total_functions=len(scan_result.parse_result.functions),
            language_statistics=lang_stats
        )

        # Record aggregation findings
        self.state_manager.add_finding(
            state,
            "info",
            "Metadata aggregation complete",
            {
                "total_files": metadata.total_files,
                "total_modules": metadata.total_modules,
                "total_classes": metadata.total_classes,
                "total_functions": metadata.total_functions
            }
        )

        return metadata

    def _guess_language(self, file_path: Path) -> Optional[str]:
        """Guess language from file extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.rb': 'ruby',
            '.php': 'php',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp'
        }
        return ext_map.get(file_path.suffix.lower())

    def _print_collection_summary(self, result: CollectionResult):
        """Print a summary of collection results."""
        print("\n" + "=" * 60)
        print("📊 Collection Summary")
        print("=" * 60)

        meta = result.metadata
        print(f"\n📁 Project: {meta.project_root}")
        print(f"   Structure: {meta.structure_info['structure_type']}")
        if meta.structure_info.get('project_type'):
            print(f"   Type: {meta.structure_info['project_type']}")

        print(f"\n📄 Files: {meta.total_files}")
        for lang, count in sorted(meta.files_by_language.items(), key=lambda x: -x[1]):
            print(f"   {lang}: {count}")

        print(f"\n🏗️  Code Entities:")
        print(f"   Modules: {meta.total_modules}")
        print(f"   Classes: {meta.total_classes}")
        print(f"   Functions: {meta.total_functions}")

        print(f"\n⏱️  Collection time: {result.collection_time_seconds:.2f}s")

        if result.errors:
            print(f"\n⚠️  Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"   - {error}")

        print("\n" + "=" * 60)


def collect_project_data(
    project_root: str,
    output_folder: str,
    exclude_patterns: Optional[List[str]] = None,
    resume_if_available: bool = True,
    verbose: bool = True
) -> CollectionResult:
    """
    Convenience function to collect project data.

    Args:
        project_root: Root directory of project to analyze
        output_folder: Directory for output and state files
        exclude_patterns: Patterns to exclude from analysis
        resume_if_available: Resume previous session if available
        verbose: Enable verbose output

    Returns:
        CollectionResult with all collected data

    Example:
        >>> result = collect_project_data(
        ...     "/path/to/project",
        ...     "/path/to/output",
        ...     verbose=True
        ... )
        >>> print(f"Collected {result.metadata.total_files} files")
    """
    config = CollectionConfig(
        project_root=Path(project_root),
        output_folder=Path(output_folder),
        exclude_patterns=exclude_patterns,
        resume_if_available=resume_if_available,
        verbose=verbose
    )

    collector = DataCollector(config)
    return collector.collect()
