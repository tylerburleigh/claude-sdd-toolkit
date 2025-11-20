"""
Project structure detection for LLM-based documentation generation.

This module provides detection capabilities for different project structures:
- Monorepo (multiple packages/services in one repository)
- Monolith (single cohesive application)
- Client/Server architecture
- Workspace patterns (npm/yarn workspaces, Python packages, etc.)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json


class ProjectStructure(Enum):
    """Types of project structures."""
    MONOREPO = "monorepo"
    MONOLITH = "monolith"
    CLIENT_SERVER = "client_server"
    UNKNOWN = "unknown"


class ProjectType(Enum):
    """Types of projects based on functionality."""
    WEB_APP = "web_app"
    BACKEND_API = "backend_api"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    UNKNOWN = "unknown"


@dataclass
class ProjectPart:
    """Represents a distinct part of a project (e.g., package, service)."""
    name: str
    path: Path
    type: str  # e.g., "package", "service", "client", "server"
    languages: Set[str]
    has_package_json: bool = False
    has_setup_py: bool = False
    has_pyproject_toml: bool = False
    has_go_mod: bool = False


@dataclass
class ProjectStructureInfo:
    """Information about detected project structure."""
    structure_type: ProjectStructure
    parts: List[ProjectPart]
    root_path: Path
    project_type: Optional[ProjectType] = None
    workspace_config: Optional[Dict] = None
    confidence: float = 0.0  # 0.0 to 1.0
    indicators: List[str] = None  # Human-readable detection reasoning

    def __post_init__(self):
        if self.indicators is None:
            self.indicators = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'structure_type': self.structure_type.value,
            'project_type': self.project_type.value if self.project_type else None,
            'parts': [
                {
                    'name': p.name,
                    'path': str(p.path),
                    'type': p.type,
                    'languages': list(p.languages),
                    'has_package_json': p.has_package_json,
                    'has_setup_py': p.has_setup_py,
                    'has_pyproject_toml': p.has_pyproject_toml,
                    'has_go_mod': p.has_go_mod
                }
                for p in self.parts
            ],
            'root_path': str(self.root_path),
            'workspace_config': self.workspace_config,
            'confidence': self.confidence,
            'indicators': self.indicators
        }


class ProjectStructureDetector:
    """
    Detects project structure patterns.

    Identifies:
    - Monorepos with multiple packages/services
    - Monolithic applications
    - Client/server architectures
    - Workspace configurations
    """

    def __init__(self, project_root: Path, verbose: bool = False):
        """
        Initialize the detector.

        Args:
            project_root: Root directory of the project
            verbose: Enable verbose output
        """
        self.project_root = project_root.resolve()
        self.verbose = verbose

    def detect(self) -> ProjectStructureInfo:
        """
        Detect the project structure.

        Returns:
            ProjectStructureInfo with detected structure type and parts
        """
        if self.verbose:
            print(f"🔍 Detecting project structure in {self.project_root}...")

        # Check for workspace configurations first
        workspace_config = self._detect_workspace_config()

        # Scan for project parts
        parts = self._scan_for_parts()

        # Determine structure type
        structure_type, confidence, indicators = self._determine_structure_type(
            parts, workspace_config
        )

        # Classify project type
        project_type = self._classify_project_type(parts)

        result = ProjectStructureInfo(
            structure_type=structure_type,
            project_type=project_type,
            parts=parts,
            root_path=self.project_root,
            workspace_config=workspace_config,
            confidence=confidence,
            indicators=indicators
        )

        if self.verbose:
            self._print_detection_summary(result)

        return result

    def _detect_workspace_config(self) -> Optional[Dict]:
        """
        Detect workspace configuration files.

        Returns:
            Dictionary with workspace config info or None
        """
        config = {}

        # Check for npm/yarn workspaces
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "workspaces" in data:
                        config["npm_workspaces"] = data["workspaces"]
            except (json.JSONDecodeError, IOError):
                pass

        # Check for pnpm workspace
        pnpm_workspace = self.project_root / "pnpm-workspace.yaml"
        if pnpm_workspace.exists():
            config["pnpm_workspace"] = True

        # Check for lerna
        lerna_json = self.project_root / "lerna.json"
        if lerna_json.exists():
            config["lerna"] = True

        # Check for nx workspace
        nx_json = self.project_root / "nx.json"
        if nx_json.exists():
            config["nx"] = True

        return config if config else None

    def _scan_for_parts(self) -> List[ProjectPart]:
        """
        Scan directory structure for distinct project parts.

        Returns:
            List of detected project parts
        """
        parts = []

        # Common monorepo directories
        monorepo_dirs = ["packages", "apps", "services", "libs", "modules", "src"]

        for dir_name in monorepo_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.is_dir():
                # Scan subdirectories
                for subdir in dir_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.'):
                        part = self._analyze_directory(subdir, dir_name)
                        if part:
                            parts.append(part)

        # Check for client/server structure at root level
        for name in ["client", "server", "frontend", "backend", "api"]:
            dir_path = self.project_root / name
            if dir_path.is_dir():
                part = self._analyze_directory(dir_path, "root")
                if part:
                    parts.append(part)

        # Check for Python package in src/
        src_dir = self.project_root / "src"
        if src_dir.is_dir() and not parts:
            # If src/ contains a single package, check it
            for subdir in src_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    part = self._analyze_directory(subdir, "src")
                    if part:
                        parts.append(part)

        # If no parts found, treat entire project as single part
        if not parts:
            root_part = self._analyze_directory(self.project_root, "root")
            if root_part:
                root_part.name = "root"
                parts.append(root_part)

        return parts

    def _analyze_directory(self, dir_path: Path, parent_type: str) -> Optional[ProjectPart]:
        """
        Analyze a directory to determine if it's a project part.

        Args:
            dir_path: Directory to analyze
            parent_type: Type of parent directory (e.g., "packages", "root")

        Returns:
            ProjectPart if directory contains recognizable project structure, None otherwise
        """
        # Check for package/project indicators
        has_package_json = (dir_path / "package.json").exists()
        has_setup_py = (dir_path / "setup.py").exists()
        has_pyproject_toml = (dir_path / "pyproject.toml").exists()
        has_go_mod = (dir_path / "go.mod").exists()

        # Must have at least one project indicator
        if not any([has_package_json, has_setup_py, has_pyproject_toml, has_go_mod]):
            return None

        # Detect languages
        languages = set()
        if has_package_json or any(dir_path.glob("**/*.js")) or any(dir_path.glob("**/*.ts")):
            languages.add("javascript")
        if has_setup_py or has_pyproject_toml or any(dir_path.glob("**/*.py")):
            languages.add("python")
        if has_go_mod or any(dir_path.glob("**/*.go")):
            languages.add("go")

        # Determine part type
        part_type = self._determine_part_type(dir_path, parent_type)

        return ProjectPart(
            name=dir_path.name,
            path=dir_path,
            type=part_type,
            languages=languages,
            has_package_json=has_package_json,
            has_setup_py=has_setup_py,
            has_pyproject_toml=has_pyproject_toml,
            has_go_mod=has_go_mod
        )

    def _determine_part_type(self, dir_path: Path, parent_type: str) -> str:
        """
        Determine the type of a project part.

        Args:
            dir_path: Path to the directory
            parent_type: Type of parent directory

        Returns:
            Part type string (e.g., "package", "service", "client", "server")
        """
        name_lower = dir_path.name.lower()

        # Check for specific types based on name
        if "client" in name_lower or "frontend" in name_lower:
            return "client"
        elif "server" in name_lower or "backend" in name_lower or "api" in name_lower:
            return "server"
        elif parent_type == "packages":
            return "package"
        elif parent_type == "services" or parent_type == "apps":
            return "service"
        elif parent_type == "libs" or parent_type == "modules":
            return "library"
        else:
            return "package"

    def _determine_structure_type(
        self,
        parts: List[ProjectPart],
        workspace_config: Optional[Dict]
    ) -> tuple[ProjectStructure, float, List[str]]:
        """
        Determine the overall project structure type.

        Args:
            parts: List of detected project parts
            workspace_config: Workspace configuration if any

        Returns:
            Tuple of (structure_type, confidence, indicators)
        """
        indicators = []
        confidence = 0.0

        # Check for workspace configuration (strong monorepo indicator)
        if workspace_config:
            indicators.append(f"Workspace config found: {', '.join(workspace_config.keys())}")
            confidence += 0.4

        # Check number of parts
        if len(parts) > 1:
            indicators.append(f"Multiple parts detected: {len(parts)}")
            confidence += 0.3
        elif len(parts) == 1:
            indicators.append("Single part detected")

        # Check for client/server pattern
        has_client = any(p.type == "client" for p in parts)
        has_server = any(p.type in ("server", "backend") for p in parts)

        if has_client and has_server:
            indicators.append("Client and server parts detected")
            return ProjectStructure.CLIENT_SERVER, min(confidence + 0.3, 1.0), indicators

        # Check for monorepo indicators
        monorepo_indicators = sum([
            len(parts) > 2,
            workspace_config is not None,
            any(p.type in ("package", "service") for p in parts)
        ])

        if monorepo_indicators >= 2:
            confidence += 0.3
            indicators.append(f"Monorepo indicators: {monorepo_indicators}/3")
            return ProjectStructure.MONOREPO, min(confidence, 1.0), indicators

        # Default to monolith if single part or unclear
        if len(parts) <= 1:
            indicators.append("Single cohesive structure")
            return ProjectStructure.MONOLITH, 0.7, indicators

        # Multiple parts but unclear structure
        return ProjectStructure.UNKNOWN, confidence, indicators

    def _classify_project_type(self, parts: List[ProjectPart]) -> ProjectType:
        """
        Classify the project type based on patterns and files.

        Args:
            parts: List of detected project parts

        Returns:
            ProjectType classification
        """
        # Collect all files for pattern matching
        web_indicators = 0
        api_indicators = 0
        cli_indicators = 0
        library_indicators = 0

        # Check package.json for clues
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg_data = json.load(f)
                    dependencies = pkg_data.get("dependencies", {})
                    dev_dependencies = pkg_data.get("devDependencies", {})
                    all_deps = {**dependencies, **dev_dependencies}

                    # Web framework indicators
                    web_frameworks = ["react", "vue", "angular", "svelte", "next", "nuxt", "gatsby"]
                    if any(fw in all_deps for fw in web_frameworks):
                        web_indicators += 2

                    # Build tools for web
                    if any(tool in all_deps for tool in ["webpack", "vite", "parcel"]):
                        web_indicators += 1

                    # Backend/API indicators
                    api_frameworks = ["express", "fastify", "koa", "hapi", "nest"]
                    if any(fw in all_deps for fw in api_frameworks):
                        api_indicators += 2

                    # CLI indicators
                    if "bin" in pkg_data:
                        cli_indicators += 2
                    cli_libs = ["commander", "yargs", "inquirer", "chalk", "ora"]
                    if any(lib in all_deps for lib in cli_libs):
                        cli_indicators += 1

                    # Library indicators
                    if pkg_data.get("main") and not pkg_data.get("bin"):
                        library_indicators += 1
            except (json.JSONDecodeError, IOError):
                pass

        # Check Python files
        setup_py = self.project_root / "setup.py"
        pyproject_toml = self.project_root / "pyproject.toml"

        if setup_py.exists() or pyproject_toml.exists():
            # Check for common Python patterns
            if (self.project_root / "setup.py").exists():
                try:
                    content = (self.project_root / "setup.py").read_text()
                    if "entry_points" in content and "console_scripts" in content:
                        cli_indicators += 2
                except IOError:
                    pass

            # Check for web frameworks
            requirements_files = list(self.project_root.glob("*requirements*.txt"))
            requirements_files.extend(self.project_root.glob("requirements/*.txt"))

            for req_file in requirements_files:
                try:
                    content = req_file.read_text().lower()
                    if any(fw in content for fw in ["django", "flask", "fastapi", "starlette"]):
                        if "fastapi" in content or "starlette" in content:
                            api_indicators += 2
                        else:
                            web_indicators += 2

                    if any(lib in content for fw in ["click", "typer", "argparse"]):
                        cli_indicators += 1
                except IOError:
                    pass

        # Check for common file patterns
        has_public_or_static = (
            (self.project_root / "public").exists() or
            (self.project_root / "static").exists()
        )
        has_src_pages = (self.project_root / "src" / "pages").exists()
        has_views_or_templates = (
            (self.project_root / "views").exists() or
            (self.project_root / "templates").exists()
        )

        if has_public_or_static or has_src_pages or has_views_or_templates:
            web_indicators += 1

        # Check for API-specific patterns
        has_api_dir = (
            (self.project_root / "api").exists() or
            (self.project_root / "routes").exists() or
            (self.project_root / "endpoints").exists()
        )
        if has_api_dir:
            api_indicators += 1

        # Check for CLI-specific patterns
        has_cli_dir = (self.project_root / "cli").exists()
        has_bin_dir = (self.project_root / "bin").exists()
        if has_cli_dir or has_bin_dir:
            cli_indicators += 1

        # Library patterns
        has_lib_structure = (
            (self.project_root / "lib").exists() or
            (self.project_root / "src").exists() and not has_src_pages
        )
        no_executables = not (has_bin_dir or has_cli_dir)
        if has_lib_structure and no_executables and library_indicators == 0:
            # Only increment if no other strong indicators
            if web_indicators == 0 and api_indicators == 0 and cli_indicators == 0:
                library_indicators += 1

        # Determine project type based on scores
        scores = {
            ProjectType.WEB_APP: web_indicators,
            ProjectType.BACKEND_API: api_indicators,
            ProjectType.CLI_TOOL: cli_indicators,
            ProjectType.LIBRARY: library_indicators,
        }

        # Get highest score
        max_score = max(scores.values())
        if max_score == 0:
            return ProjectType.UNKNOWN

        # Return type with highest score
        for proj_type, score in scores.items():
            if score == max_score:
                return proj_type

        return ProjectType.UNKNOWN

    def _print_detection_summary(self, result: ProjectStructureInfo):
        """Print summary of detection results."""
        print(f"\n✅ Structure detected: {result.structure_type.value}")
        if result.project_type:
            print(f"   Project type: {result.project_type.value}")
        print(f"   Confidence: {result.confidence:.0%}")

        if result.indicators:
            print(f"   Indicators:")
            for indicator in result.indicators:
                print(f"     • {indicator}")

        if result.parts:
            print(f"\n   Parts found ({len(result.parts)}):")
            for part in result.parts:
                langs = ", ".join(sorted(part.languages))
                print(f"     • {part.name} ({part.type}) - {langs}")


def detect_project_structure(
    project_path: str,
    verbose: bool = False
) -> ProjectStructureInfo:
    """
    Detect the structure of a project.

    Args:
        project_path: Path to project directory
        verbose: Enable verbose output

    Returns:
        ProjectStructureInfo with detected structure

    Example:
        >>> info = detect_project_structure("/path/to/project", verbose=True)
        >>> print(f"Structure: {info.structure_type.value}")
        >>> print(f"Parts: {len(info.parts)}")
    """
    detector = ProjectStructureDetector(Path(project_path), verbose=verbose)
    return detector.detect()


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Detect project structure")
    parser.add_argument("project_path", help="Path to project to analyze")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = detect_project_structure(args.project_path, verbose=not args.quiet)

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
    elif args.quiet:
        print(result.structure_type.value)
