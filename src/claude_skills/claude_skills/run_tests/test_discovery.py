"""
Test Discovery Operations

Discovers and analyzes test structure in a project, including test files,
fixtures, markers, configuration, and organization.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory to path to import sdd_common

from claude_skills.common import PrettyPrinter


def find_test_files(root_dir: str = ".") -> List[Path]:
    """
    Find all test files in the project.

    Args:
        root_dir: Root directory to search from

    Returns:
        List of Path objects for test files
    """
    root = Path(root_dir).resolve()
    test_files = []

    # Common test file patterns
    patterns = ["test_*.py", "*_test.py"]

    for pattern in patterns:
        test_files.extend(root.rglob(pattern))

    # Remove duplicates and sort
    return sorted(set(test_files))


def find_conftest_files(root_dir: str = ".") -> List[Path]:
    """
    Find all conftest.py files.

    Args:
        root_dir: Root directory to search from

    Returns:
        List of Path objects for conftest.py files
    """
    root = Path(root_dir).resolve()
    return sorted(root.rglob("conftest.py"))


def analyze_test_file(file_path: Path) -> Dict:
    """
    Analyze a test file for its structure.

    Args:
        file_path: Path to the test file

    Returns:
        Dictionary with analysis results
    """
    info = {
        "test_functions": [],
        "test_classes": [],
        "fixtures": [],
        "imports": [],
        "markers": set(),
        "parametrize": 0,
    }

    try:
        # Validate file exists and is readable
        if not file_path.exists():
            info["error"] = "File not found"
            return info

        if not file_path.is_file():
            info["error"] = "Not a file"
            return info

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find test functions
        test_funcs = re.findall(r'^def (test_\w+)\(', content, re.MULTILINE)
        info["test_functions"] = test_funcs

        # Find test classes
        test_classes = re.findall(r'^class (Test\w+)', content, re.MULTILINE)
        info["test_classes"] = test_classes

        # Find fixtures
        fixtures = re.findall(r'@pytest\.fixture.*?\ndef (\w+)\(', content, re.DOTALL)
        info["fixtures"] = fixtures

        # Find imports
        imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
        info["imports"] = imports[:10]  # Limit to first 10

        # Find markers
        markers = re.findall(r'@pytest\.mark\.(\w+)', content)
        info["markers"] = set(markers)

        # Count parametrize decorators
        info["parametrize"] = len(re.findall(r'@pytest\.mark\.parametrize', content))

    except UnicodeDecodeError:
        info["error"] = "File encoding error (not UTF-8)"
    except PermissionError:
        info["error"] = "Permission denied"
    except Exception as e:
        info["error"] = f"Error analyzing file: {str(e)}"

    return info


def analyze_conftest(file_path: Path) -> Dict:
    """
    Analyze a conftest.py file for fixtures and configuration.

    Args:
        file_path: Path to conftest.py file

    Returns:
        Dictionary with analysis results
    """
    info = {
        "fixtures": [],
        "hooks": [],
        "plugins": [],
    }

    try:
        # Validate file exists and is readable
        if not file_path.exists():
            info["error"] = "File not found"
            return info

        if not file_path.is_file():
            info["error"] = "Not a file"
            return info

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find fixtures
        fixtures = re.findall(
            r'@pytest\.fixture(?:\([^)]*\))?\s*\ndef (\w+)\(',
            content,
            re.DOTALL
        )
        info["fixtures"] = fixtures

        # Find pytest hooks
        hooks = re.findall(r'def (pytest_\w+)\(', content)
        info["hooks"] = hooks

        # Find pytest plugins
        plugins = re.findall(r'pytest_plugins\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if plugins:
            plugin_list = re.findall(r'["\']([^"\']+)["\']', plugins[0])
            info["plugins"] = plugin_list

    except UnicodeDecodeError:
        info["error"] = "File encoding error (not UTF-8)"
    except PermissionError:
        info["error"] = "Permission denied"
    except Exception as e:
        info["error"] = f"Error analyzing file: {str(e)}"

    return info


def get_directory_structure(test_files: List[Path], root: Path) -> Dict:
    """
    Build a directory structure from test files.

    Args:
        test_files: List of test file paths
        root: Root directory path

    Returns:
        Dictionary mapping directory paths to lists of file names
    """
    structure = defaultdict(list)

    for test_file in test_files:
        try:
            rel_path = test_file.relative_to(root)
            dir_path = rel_path.parent
            structure[str(dir_path)].append(test_file.name)
        except ValueError:
            # File is outside root
            pass

    return dict(structure)


def print_tree_structure(structure: Dict, indent: int = 0):
    """
    Print directory structure as a tree.

    Args:
        structure: Directory structure dictionary
        indent: Indentation level
    """
    for directory in sorted(structure.keys()):
        if directory == ".":
            dir_display = "(root)"
        else:
            dir_display = directory

        print(f"{'  ' * indent}{dir_display}/")

        # Print files in this directory
        for file in sorted(structure[directory]):
            print(f"{'  ' * (indent + 1)}{file}")


def get_summary_stats(test_files: List[Path], conftest_files: List[Path]) -> Dict:
    """
    Get summary statistics for all test files.

    Args:
        test_files: List of test file paths
        conftest_files: List of conftest file paths

    Returns:
        Dictionary with summary statistics
    """
    total_tests = 0
    total_fixtures = 0
    all_markers = set()

    for test_file in test_files:
        analysis = analyze_test_file(test_file)
        total_tests += len(analysis["test_functions"])
        total_tests += sum(1 for _ in analysis["test_classes"])  # Approximate
        all_markers.update(analysis["markers"])

    for conftest in conftest_files:
        analysis = analyze_conftest(conftest)
        total_fixtures += len(analysis["fixtures"])

    return {
        "total_tests": total_tests,
        "total_fixtures": total_fixtures,
        "markers": sorted(all_markers),
    }


def collect_all_fixtures(conftest_files: List[Path], root: Path) -> Dict[str, List[str]]:
    """
    Collect all fixtures from conftest files.

    Args:
        conftest_files: List of conftest file paths
        root: Root directory path

    Returns:
        Dictionary mapping fixture names to their locations
    """
    all_fixtures = defaultdict(list)

    for conftest in conftest_files:
        try:
            rel_path = conftest.relative_to(root)
        except ValueError:
            rel_path = conftest

        analysis = analyze_conftest(conftest)
        for fixture in analysis["fixtures"]:
            all_fixtures[fixture].append(str(rel_path))

    return dict(all_fixtures)


def collect_all_markers(test_files: List[Path]) -> Dict[str, int]:
    """
    Collect all markers from test files with usage counts.

    Args:
        test_files: List of test file paths

    Returns:
        Dictionary mapping marker names to usage counts
    """
    all_markers = defaultdict(int)

    for test_file in test_files:
        analysis = analyze_test_file(test_file)
        for marker in analysis["markers"]:
            all_markers[marker] += 1

    return dict(all_markers)


def print_discovery_report(
    root_dir: str = ".",
    show_summary: bool = False,
    show_tree: bool = False,
    show_fixtures: bool = False,
    show_markers: bool = False,
    show_detailed: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> int:
    """
    Print a comprehensive discovery report.

    Args:
        root_dir: Root directory to analyze
        show_summary: Show summary statistics only
        show_tree: Show directory tree structure
        show_fixtures: Show all fixtures
        show_markers: Show all markers
        show_detailed: Show detailed analysis of each file
        printer: PrettyPrinter instance (creates default if None)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if printer is None:
        printer = PrettyPrinter()

    root = Path(root_dir).resolve()

    if not root.exists():
        printer.error(f"Directory '{root_dir}' not found")
        return 1

    # Find all test files and conftest files
    test_files = find_test_files(root)
    conftest_files = find_conftest_files(root)

    if not test_files and not conftest_files:
        printer.warning("No test files or conftest.py files found")
        return 0

    # Header
    printer.header(f"Test Discovery in: {root}")
    printer.blank()
    printer.info(f"Test files found: {len(test_files)}")
    printer.info(f"Conftest files found: {len(conftest_files)}")
    printer.blank()

    # Summary
    if show_summary:
        stats = get_summary_stats(test_files, conftest_files)
        print(f"Total test functions: ~{stats['total_tests']}")
        print(f"Total fixtures: {stats['total_fixtures']}")
        markers_str = ', '.join(stats['markers']) if stats['markers'] else 'None'
        print(f"Markers used: {markers_str}")
        return 0

    # Tree structure (default if nothing else specified)
    if show_tree or not (show_fixtures or show_markers or show_detailed):
        print("Directory Structure:")
        print("-" * 60)
        structure = get_directory_structure(test_files, root)
        print_tree_structure(structure)
        print()

    # Conftest files (always show if present, unless summary-only)
    if conftest_files and not show_summary:
        print("Configuration Files (conftest.py):")
        print("-" * 60)
        for conftest in conftest_files:
            try:
                rel_path = conftest.relative_to(root)
            except ValueError:
                rel_path = conftest

            analysis = analyze_conftest(conftest)
            print(f"\n{rel_path}")

            if analysis["fixtures"]:
                print(f"  Fixtures ({len(analysis['fixtures'])}): {', '.join(analysis['fixtures'][:5])}")
                if len(analysis["fixtures"]) > 5:
                    print(f"    ... and {len(analysis['fixtures']) - 5} more")

            if analysis["hooks"]:
                print(f"  Hooks: {', '.join(analysis['hooks'])}")

            if analysis["plugins"]:
                print(f"  Plugins: {', '.join(analysis['plugins'])}")

        print()

    # Show all fixtures if requested
    if show_fixtures:
        all_fixtures = collect_all_fixtures(conftest_files, root)

        print("All Fixtures:")
        print("-" * 60)
        for fixture in sorted(all_fixtures.keys()):
            locations = all_fixtures[fixture]
            print(f"{fixture:30} (in {len(locations)} file(s))")
            for loc in locations[:3]:
                print(f"  - {loc}")
            if len(locations) > 3:
                print(f"  ... and {len(locations) - 3} more")
        print()

    # Show all markers if requested
    if show_markers:
        all_markers = collect_all_markers(test_files)

        print("Markers Found:")
        print("-" * 60)
        if all_markers:
            for marker in sorted(all_markers.keys()):
                print(f"  @pytest.mark.{marker:20} (used {all_markers[marker]} times)")
        else:
            print("  No markers found")
        print()

    # Detailed analysis
    if show_detailed:
        print("Detailed Test File Analysis:")
        print("-" * 60)

        for test_file in test_files:
            try:
                rel_path = test_file.relative_to(root)
            except ValueError:
                rel_path = test_file

            analysis = analyze_test_file(test_file)

            print(f"\n{rel_path}")
            print(f"  Test functions: {len(analysis['test_functions'])}")
            if analysis["test_functions"]:
                for func in analysis["test_functions"][:3]:
                    print(f"    - {func}")
                if len(analysis["test_functions"]) > 3:
                    print(f"    ... and {len(analysis['test_functions']) - 3} more")

            if analysis["test_classes"]:
                print(f"  Test classes: {', '.join(analysis['test_classes'])}")

            if analysis["fixtures"]:
                print(f"  Defines fixtures: {', '.join(analysis['fixtures'])}")

            if analysis["markers"]:
                print(f"  Uses markers: {', '.join(sorted(analysis['markers']))}")

            if analysis["parametrize"]:
                print(f"  Parametrized tests: {analysis['parametrize']}")

    return 0
