"""
Project detection and analysis operations for sdd-next.

This module provides functions for detecting project types, finding tests,
checking environment requirements, and discovering related files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def detect_project(directory: Optional[Path] = None) -> Dict:
    """
    Detect project type and extract dependencies.

    Args:
        directory: Directory to analyze (defaults to current directory)

    Returns:
        Dictionary with project type, dependencies, and metadata
    """
    if not directory:
        directory = Path.cwd()
    else:
        directory = Path(directory)

    result = {
        "project_type": "unknown",
        "dependency_manager": None,
        "dependencies": {},
        "dev_dependencies": {},
        "config_files": []
    }

    # Node.js project
    package_json = directory / "package.json"
    if package_json.exists():
        result["project_type"] = "nodejs"
        result["dependency_manager"] = "npm"
        result["config_files"].append(str(package_json))

        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                result["dependencies"] = data.get("dependencies", {})
                result["dev_dependencies"] = data.get("devDependencies", {})
        except (json.JSONDecodeError, IOError):
            pass

    # Python project
    requirements_txt = directory / "requirements.txt"
    pyproject_toml = directory / "pyproject.toml"
    setup_py = directory / "setup.py"

    if requirements_txt.exists() or pyproject_toml.exists() or setup_py.exists():
        result["project_type"] = "python"

        if pyproject_toml.exists():
            result["dependency_manager"] = "poetry"
            result["config_files"].append(str(pyproject_toml))
        elif requirements_txt.exists():
            result["dependency_manager"] = "pip"
            result["config_files"].append(str(requirements_txt))

            # Parse requirements.txt
            try:
                with open(requirements_txt, 'r') as f:
                    deps = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Simple parsing: package==version or package
                            if '==' in line:
                                pkg, ver = line.split('==', 1)
                                deps[pkg.strip()] = ver.strip()
                            else:
                                deps[line] = "*"
                    result["dependencies"] = deps
            except IOError:
                pass

    # Rust project
    cargo_toml = directory / "Cargo.toml"
    if cargo_toml.exists():
        result["project_type"] = "rust"
        result["dependency_manager"] = "cargo"
        result["config_files"].append(str(cargo_toml))

    # Go project
    go_mod = directory / "go.mod"
    if go_mod.exists():
        result["project_type"] = "go"
        result["dependency_manager"] = "go modules"
        result["config_files"].append(str(go_mod))

    # Java/Maven
    pom_xml = directory / "pom.xml"
    if pom_xml.exists():
        result["project_type"] = "java"
        result["dependency_manager"] = "maven"
        result["config_files"].append(str(pom_xml))

    # Java/Gradle
    build_gradle = directory / "build.gradle"
    build_gradle_kts = directory / "build.gradle.kts"
    if build_gradle.exists() or build_gradle_kts.exists():
        result["project_type"] = "java"
        result["dependency_manager"] = "gradle"
        if build_gradle.exists():
            result["config_files"].append(str(build_gradle))
        if build_gradle_kts.exists():
            result["config_files"].append(str(build_gradle_kts))

    return result


def find_tests(directory: Optional[Path] = None, source_file: Optional[str] = None) -> Dict:
    """
    Discover test files and patterns in the project.

    Args:
        directory: Directory to search (defaults to current directory)
        source_file: Optional source file to find corresponding test

    Returns:
        Dictionary with test files, patterns, and framework detection
    """
    if not directory:
        directory = Path.cwd()
    else:
        directory = Path(directory)

    result = {
        "test_files": [],
        "test_framework": None,
        "test_patterns": [],
        "corresponding_test": None
    }

    # Common test file patterns
    patterns = [
        "**/*.test.js",
        "**/*.spec.js",
        "**/*.test.ts",
        "**/*.spec.ts",
        "**/*_test.py",
        "**/*_test.go",
        "**/test_*.py",
        "**/*_spec.rb",
        "**/*Test.java"
    ]

    test_files = []
    for pattern in patterns:
        matches = list(directory.glob(pattern))
        test_files.extend([str(m.resolve()) for m in matches if m.is_file()])

    result["test_files"] = sorted(list(set(test_files)))

    # Detect testing framework
    package_json = directory / "package.json"
    if package_json.exists():
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "jest" in all_deps:
                    result["test_framework"] = "jest"
                elif "mocha" in all_deps:
                    result["test_framework"] = "mocha"
                elif "vitest" in all_deps:
                    result["test_framework"] = "vitest"
        except (json.JSONDecodeError, IOError):
            pass

    # Python test framework detection
    requirements_txt = directory / "requirements.txt"
    if requirements_txt.exists():
        try:
            with open(requirements_txt, 'r') as f:
                content = f.read().lower()
                if "pytest" in content:
                    result["test_framework"] = "pytest"
                elif "unittest" in content:
                    result["test_framework"] = "unittest"
        except IOError:
            pass

    # Find corresponding test file for source file
    if source_file:
        source_path = Path(source_file)
        stem = source_path.stem
        ext = source_path.suffix

        # Try common test naming conventions
        test_patterns = [
            f"{stem}.test{ext}",
            f"{stem}.spec{ext}",
            f"{stem}_test{ext}",
            f"test_{stem}{ext}",
            f"{stem}Test{ext}"
        ]

        for pattern in test_patterns:
            # Search in common test directories
            test_dirs = ["tests", "test", "__tests__", "spec"]
            for test_dir in test_dirs:
                test_path = directory / test_dir / pattern
                if test_path.exists():
                    result["corresponding_test"] = str(test_path.resolve())
                    break

            # Also check in same directory
            same_dir_test = source_path.parent / pattern
            if same_dir_test.exists():
                result["corresponding_test"] = str(same_dir_test.resolve())
                break

    return result


def check_environment(directory: Optional[Path] = None, required_deps: Optional[List[str]] = None) -> Dict:
    """
    Check environmental requirements and configuration.

    Args:
        directory: Directory to check (defaults to current directory)
        required_deps: Optional list of required dependencies to check

    Returns:
        Dictionary with environment validation results
    """
    if not directory:
        directory = Path.cwd()
    else:
        directory = Path(directory)

    if required_deps is None:
        required_deps = []

    result = {
        "valid": True,
        "missing_dependencies": [],
        "missing_config_files": [],
        "warnings": [],
        "installed_dependencies": {},
        "config_files_found": []
    }

    # Detect project type first
    project = detect_project(directory)

    # Add project-specific config files to result
    result["config_files_found"].extend(project.get("config_files", []))

    # Check dependencies based on project type
    if project["project_type"] == "nodejs":
        all_deps = {**project.get("dependencies", {}), **project.get("dev_dependencies", {})}
        result["installed_dependencies"] = all_deps

        for req_dep in required_deps:
            if req_dep not in all_deps:
                result["missing_dependencies"].append(req_dep)
                result["valid"] = False

    elif project["project_type"] == "python":
        result["installed_dependencies"] = project.get("dependencies", {})

        for req_dep in required_deps:
            if req_dep not in result["installed_dependencies"]:
                result["missing_dependencies"].append(req_dep)
                result["valid"] = False

    # Check for common configuration files
    common_configs = [
        ".env",
        ".env.example",
        "config.json",
        "config.yaml",
        "tsconfig.json",
        "jest.config.js",
        "pytest.ini"
    ]

    for config in common_configs:
        config_path = directory / config
        if config_path.exists():
            resolved_path = str(config_path.resolve())
            if resolved_path not in result["config_files_found"]:
                result["config_files_found"].append(resolved_path)

    # Check for .env.example without .env
    env_example = directory / ".env.example"
    env_file = directory / ".env"
    if env_example.exists() and not env_file.exists():
        result["warnings"].append("Found .env.example but no .env file")

    return result


def find_related_files(file_path: str, directory: Optional[Path] = None) -> Dict:
    """
    Find files related to a given file.

    Args:
        file_path: Path to the source file
        directory: Project directory (defaults to current directory)

    Returns:
        Dictionary with categorized related files
    """
    if not directory:
        directory = Path.cwd()
    else:
        directory = Path(directory)

    # Resolve file_path relative to directory
    if Path(file_path).is_absolute():
        source_file = Path(file_path)
    else:
        source_file = directory / file_path
    
    result = {
        "source_file": str(source_file.resolve()) if source_file.exists() else file_path,
        "same_directory": [],
        "test_files": [],
        "similar_files": [],
        "imported_by": []
    }

    if not source_file.exists():
        return result

    # Files in same directory
    if source_file.parent.exists():
        same_dir_files = [
            str(f.resolve()) for f in source_file.parent.iterdir()
            if f.is_file() and f != source_file and f.suffix == source_file.suffix
        ]
        result["same_directory"] = same_dir_files

    # Find test files
    test_info = find_tests(directory, str(source_file))
    if test_info.get("corresponding_test"):
        result["test_files"].append(test_info["corresponding_test"])

    # Find similar files (same prefix or pattern)
    stem = source_file.stem
    ext = source_file.suffix

    # Extract base name (remove Service, Controller, Model suffixes)
    base_patterns = [
        stem.replace("Service", ""),
        stem.replace("Controller", ""),
        stem.replace("Model", ""),
        stem.replace("Helper", ""),
        stem.replace("Util", "")
    ]

    for base in base_patterns:
        if base and base != stem:
            pattern = f"**/{base}*{ext}"
            # Use glob to find matches
            matches = directory.glob(pattern)
            result["similar_files"].extend([
                str(m.resolve()) for m in matches
                if m.is_file() and str(m.resolve()) != str(source_file.resolve())
            ])

    # Remove duplicates
    result["similar_files"] = sorted(list(set(result["similar_files"])))

    return result
