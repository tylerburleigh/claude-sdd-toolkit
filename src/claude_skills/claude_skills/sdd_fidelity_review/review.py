"""
Implementation Fidelity Review Core Module

Core functionality for comparing implementation against specifications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
import subprocess
import logging
import xml.etree.ElementTree as ET

from claude_skills.common.spec import load_json_spec, get_node
from claude_skills.common.paths import find_specs_directory
from claude_skills.common.git_metadata import find_git_root

logger = logging.getLogger(__name__)


class FidelityReviewer:
    """
    Core class for performing fidelity reviews of implementations against specs.

    This class will be implemented in Phase 3 (Core Review Logic).
    """

    def __init__(self, spec_id: str, spec_path: Optional[Path] = None):
        """
        Initialize the fidelity reviewer.

        Args:
            spec_id: Specification ID to review against
            spec_path: Optional path to specs directory
        """
        self.spec_id = spec_id
        self.spec_path = spec_path
        self.spec_data: Optional[Dict[str, Any]] = None
        self._load_spec()

    def review_task(self, task_id: str) -> Dict[str, Any]:
        """
        Review a specific task implementation against its specification.

        Args:
            task_id: Task ID to review

        Returns:
            Dictionary containing review results

        Note:
            Implementation will be added in Phase 3.
        """
        raise NotImplementedError("Task review will be implemented in Phase 3")

    def review_phase(self, phase_id: str) -> Dict[str, Any]:
        """
        Review a phase implementation against its specification.

        Args:
            phase_id: Phase ID to review

        Returns:
            Dictionary containing review results

        Note:
            Implementation will be added in Phase 3.
        """
        raise NotImplementedError("Phase review will be implemented in Phase 3")

    def review_full_spec(self) -> Dict[str, Any]:
        """
        Review full spec implementation.

        Returns:
            Dictionary containing review results

        Note:
            Implementation will be added in Phase 3.
        """
        raise NotImplementedError("Full spec review will be implemented in Phase 3")

    def review_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Review specific files against specification.

        Args:
            file_paths: List of file paths to review

        Returns:
            Dictionary containing review results

        Note:
            Implementation will be added in Phase 3.
        """
        raise NotImplementedError("File review will be implemented in Phase 3")

    def analyze_deviation(
        self,
        task_id: Optional[str],
        deviation_description: str
    ) -> Dict[str, Any]:
        """
        Analyze a specific deviation from the specification.

        Args:
            task_id: Optional task ID for context
            deviation_description: Description of the deviation

        Returns:
            Dictionary containing deviation analysis

        Note:
            Implementation will be added in Phase 3.
        """
        raise NotImplementedError("Deviation analysis will be implemented in Phase 3")

    def _load_spec(self) -> None:
        """
        Load the specification JSON file.

        Populates self.spec_data with the loaded spec.
        Prints error and sets spec_data to None if loading fails.
        """
        # Find specs directory if not provided
        if self.spec_path is None:
            self.spec_path = find_specs_directory()
            if self.spec_path is None:
                print("Error: Could not find specs directory", file=sys.stderr)
                self.spec_data = None
                return

        # Load spec JSON
        self.spec_data = load_json_spec(self.spec_id, self.spec_path)
        if self.spec_data is None:
            print(f"Error: Failed to load spec {self.spec_id}", file=sys.stderr)

    def get_task_requirements(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract task requirements from the loaded specification.

        Args:
            task_id: Task ID to extract requirements for

        Returns:
            Dictionary containing task requirements, or None if not found or spec not loaded

        Requirements dictionary structure:
            {
                "task_id": str,
                "title": str,
                "type": str,
                "status": str,
                "parent": str,
                "description": str,
                "file_path": Optional[str],
                "estimated_hours": Optional[float],
                "dependencies": Dict[str, List[str]],
                "verification_steps": List[str],
                "metadata": Dict[str, Any]
            }
        """
        if self.spec_data is None:
            print("Error: Spec not loaded", file=sys.stderr)
            return None

        # Get task node from hierarchy
        task_node = get_node(self.spec_data, task_id)
        if task_node is None:
            print(f"Error: Task {task_id} not found in spec", file=sys.stderr)
            return None

        # Extract task requirements
        metadata = task_node.get("metadata", {})
        dependencies = task_node.get("dependencies", {})

        requirements = {
            "task_id": task_id,
            "title": task_node.get("title", ""),
            "type": task_node.get("type", ""),
            "status": task_node.get("status", ""),
            "parent": task_node.get("parent", ""),
            "description": metadata.get("description", ""),
            "file_path": metadata.get("file_path"),
            "estimated_hours": metadata.get("estimated_hours"),
            "dependencies": dependencies,
            "verification_steps": metadata.get("verification_steps", []),
            "metadata": metadata
        }

        return requirements

    def get_phase_tasks(self, phase_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all tasks within a specific phase.

        Args:
            phase_id: Phase ID to extract tasks from

        Returns:
            List of task requirement dictionaries, or None if phase not found

        Each task dictionary has the same structure as returned by get_task_requirements().
        """
        if self.spec_data is None:
            print("Error: Spec not loaded", file=sys.stderr)
            return None

        # Get phase node
        phase_node = get_node(self.spec_data, phase_id)
        if phase_node is None:
            print(f"Error: Phase {phase_id} not found in spec", file=sys.stderr)
            return None

        # Collect all task IDs within this phase
        task_ids = self._collect_task_ids_recursive(phase_id)

        # Extract requirements for each task
        tasks = []
        for task_id in task_ids:
            task_reqs = self.get_task_requirements(task_id)
            if task_reqs:
                tasks.append(task_reqs)

        return tasks

    def get_all_tasks(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all tasks from the specification.

        Returns:
            List of all task requirement dictionaries, or None if spec not loaded

        Each task dictionary has the same structure as returned by get_task_requirements().
        """
        if self.spec_data is None:
            print("Error: Spec not loaded", file=sys.stderr)
            return None

        hierarchy = self.spec_data.get("hierarchy", {})
        tasks = []

        for node_id, node_data in hierarchy.items():
            # Include tasks, verify nodes, but exclude groups and phases
            node_type = node_data.get("type", "")
            if node_type in ["task", "verify"]:
                task_reqs = self.get_task_requirements(node_id)
                if task_reqs:
                    tasks.append(task_reqs)

        return tasks

    def _collect_task_ids_recursive(self, parent_id: str) -> List[str]:
        """
        Recursively collect all task IDs under a parent node.

        Args:
            parent_id: Parent node ID to start from

        Returns:
            List of task IDs (includes nested tasks through groups)
        """
        if self.spec_data is None:
            return []

        hierarchy = self.spec_data.get("hierarchy", {})
        task_ids = []

        for node_id, node_data in hierarchy.items():
            if node_data.get("parent") == parent_id:
                node_type = node_data.get("type", "")

                if node_type in ["task", "verify"]:
                    # This is a task - add it
                    task_ids.append(node_id)
                elif node_type == "group":
                    # This is a group - recursively collect its children
                    task_ids.extend(self._collect_task_ids_recursive(node_id))

        return task_ids

    def get_file_diff(
        self,
        file_path: str,
        base_ref: str = "HEAD",
        compare_ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get git diff for a specific file.

        Args:
            file_path: Path to the file (relative to repo root or absolute)
            base_ref: Base git reference to compare from (default: HEAD)
            compare_ref: Git reference to compare to (default: working tree)

        Returns:
            Git diff output as string, or None if error occurs

        Examples:
            # Get unstaged changes for a file
            diff = reviewer.get_file_diff("src/file.py")

            # Get diff between HEAD and a specific commit
            diff = reviewer.get_file_diff("src/file.py", base_ref="abc123")

            # Get diff between two commits
            diff = reviewer.get_file_diff("src/file.py", base_ref="abc123", compare_ref="def456")
        """
        # Find git repository root
        repo_root = find_git_root()
        if repo_root is None:
            print("Error: Not in a git repository", file=sys.stderr)
            return None

        # Build git diff command
        if compare_ref:
            # Compare between two refs
            cmd = ["git", "diff", base_ref, compare_ref, "--", file_path]
        else:
            # Compare against working tree
            cmd = ["git", "diff", base_ref, "--", file_path]

        try:
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )

            if result.returncode != 0:
                logger.warning(f"Git diff failed for {file_path}: {result.stderr}")
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.warning(f"Git diff timed out for {file_path}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get git diff for {file_path}: {e}")
            return None

    def get_task_diffs(
        self,
        task_id: str,
        base_ref: str = "HEAD",
        compare_ref: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Get git diffs for all files associated with a task.

        Extracts file paths from task metadata and collects diffs for each file.

        Args:
            task_id: Task ID to get diffs for
            base_ref: Base git reference to compare from (default: HEAD)
            compare_ref: Git reference to compare to (default: working tree)

        Returns:
            Dictionary mapping file paths to their diff output.
            Files that failed to diff will have None as value.

        Example:
            {
                "src/file1.py": "diff --git a/src/file1.py...",
                "src/file2.py": None,  # Failed to get diff
                "tests/test_file.py": "diff --git a/tests/test_file.py..."
            }
        """
        task_reqs = self.get_task_requirements(task_id)
        if task_reqs is None:
            return {}

        # Collect file paths from task metadata
        file_paths = []

        # Get primary file path
        primary_file = task_reqs.get("file_path")
        if primary_file:
            file_paths.append(primary_file)

        # Get additional files from metadata
        metadata = task_reqs.get("metadata", {})
        additional_files = metadata.get("files", [])
        if additional_files:
            file_paths.extend(additional_files)

        # Get verification files
        verification_files = metadata.get("verification_files", [])
        if verification_files:
            file_paths.extend(verification_files)

        # Collect diffs for all files
        diffs = {}
        for file_path in file_paths:
            diff_output = self.get_file_diff(file_path, base_ref, compare_ref)
            diffs[file_path] = diff_output

        return diffs

    def get_phase_diffs(
        self,
        phase_id: str,
        base_ref: str = "HEAD",
        compare_ref: Optional[str] = None
    ) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Get git diffs for all tasks in a phase.

        Args:
            phase_id: Phase ID to get diffs for
            base_ref: Base git reference to compare from (default: HEAD)
            compare_ref: Git reference to compare to (default: working tree)

        Returns:
            Dictionary mapping task IDs to their file diff dictionaries.

        Example:
            {
                "task-1-1": {
                    "src/file1.py": "diff --git...",
                    "src/file2.py": "diff --git..."
                },
                "task-1-2": {
                    "tests/test.py": "diff --git..."
                }
            }
        """
        phase_tasks = self.get_phase_tasks(phase_id)
        if phase_tasks is None:
            return {}

        phase_diffs = {}
        for task in phase_tasks:
            task_id = task["task_id"]
            task_diffs = self.get_task_diffs(task_id, base_ref, compare_ref)
            if task_diffs:
                phase_diffs[task_id] = task_diffs

        return phase_diffs

    def get_branch_diff(
        self,
        base_branch: str = "main",
        max_size_kb: int = 100
    ) -> str:
        """
        Get full git diff between current branch and base branch.

        Similar to pr_context.get_spec_git_diffs but tailored for fidelity review.

        Args:
            base_branch: Base branch name to compare against (default: "main")
            max_size_kb: Maximum diff size in KB (truncate if larger)

        Returns:
            Git diff output as string, or empty string if error occurs.
            Large diffs (>max_size_kb) are truncated with a summary message.
        """
        repo_root = find_git_root()
        if repo_root is None:
            print("Error: Not in a git repository", file=sys.stderr)
            return ""

        try:
            result = subprocess.run(
                ['git', 'diff', f'{base_branch}...HEAD'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )

            if result.returncode != 0:
                logger.warning(f"Git diff failed: {result.stderr}")
                return ""

            diff_output = result.stdout

            # Check size and truncate if necessary
            diff_size_kb = len(diff_output.encode('utf-8')) / 1024
            if diff_size_kb > max_size_kb:
                logger.info(f"Diff size ({diff_size_kb:.1f}KB) exceeds limit ({max_size_kb}KB), truncating")
                # Get file-level summary instead
                result = subprocess.run(
                    ['git', 'diff', '--stat', f'{base_branch}...HEAD'],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10
                )

                if result.returncode == 0:
                    summary = result.stdout
                    return f"[Diff too large ({diff_size_kb:.1f}KB), showing summary only]\n\n{summary}"
                else:
                    return f"[Diff too large ({diff_size_kb:.1f}KB), summary unavailable]"

            return diff_output

        except subprocess.TimeoutExpired:
            logger.warning("Git diff timed out (>30s)")
            return "[Git diff timed out]"
        except Exception as e:
            logger.warning(f"Failed to get git diff: {e}")
            return ""

    def get_test_results(
        self,
        test_file: Optional[str] = None,
        junit_xml_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract test results from pytest execution or JUnit XML file.

        Args:
            test_file: Optional specific test file to run (if running tests)
            junit_xml_path: Optional path to existing JUnit XML file to parse

        Returns:
            Dictionary containing test results:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "errors": int,
                "skipped": int,
                "duration": float,
                "tests": {
                    "test_name": {
                        "status": "passed"|"failed"|"error"|"skipped",
                        "message": str,
                        "duration": float,
                        "traceback": Optional[str]
                    }
                }
            }

        Note:
            If neither test_file nor junit_xml_path is provided, returns None.
            If test_file is provided, runs pytest and parses the results.
            If junit_xml_path is provided, parses the existing XML file.
        """
        if junit_xml_path:
            # Parse existing JUnit XML file
            return self._parse_junit_xml(junit_xml_path)
        elif test_file:
            # Run pytest and parse results
            return self._run_and_parse_tests(test_file)
        else:
            logger.warning("No test file or junit_xml_path provided")
            return None

    def _run_and_parse_tests(self, test_file: str) -> Optional[Dict[str, Any]]:
        """
        Run pytest on a test file and parse the results.

        Args:
            test_file: Path to test file to run

        Returns:
            Test results dictionary or None if execution fails
        """
        # Create temporary XML file for results
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            xml_path = tmp.name

        try:
            # Run pytest with JUnit XML output
            result = subprocess.run(
                ['pytest', test_file, f'--junit-xml={xml_path}', '-v'],
                capture_output=True,
                text=True,
                check=False,
                timeout=300  # 5 minute timeout
            )

            # Parse the generated XML
            if Path(xml_path).exists():
                test_results = self._parse_junit_xml(xml_path)
                Path(xml_path).unlink()  # Clean up temp file
                return test_results
            else:
                logger.warning(f"JUnit XML file not created for {test_file}")
                return None

        except subprocess.TimeoutExpired:
            logger.warning(f"Test execution timed out for {test_file}")
            return None
        except Exception as e:
            logger.warning(f"Failed to run tests for {test_file}: {e}")
            return None
        finally:
            # Ensure temp file is cleaned up
            if Path(xml_path).exists():
                Path(xml_path).unlink()

    def _parse_junit_xml(self, xml_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse JUnit XML test results.

        Args:
            xml_path: Path to JUnit XML file

        Returns:
            Test results dictionary or None if parsing fails
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Initialize results structure
            results = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "duration": 0.0,
                "tests": {}
            }

            # Parse testsuite attributes
            testsuite = root.find('testsuite')
            if testsuite is None:
                testsuite = root  # Root might be testsuite itself

            results["total"] = int(testsuite.get('tests', 0))
            results["failed"] = int(testsuite.get('failures', 0))
            results["errors"] = int(testsuite.get('errors', 0))
            results["skipped"] = int(testsuite.get('skipped', 0))
            results["passed"] = results["total"] - results["failed"] - results["errors"] - results["skipped"]
            results["duration"] = float(testsuite.get('time', 0))

            # Parse individual test cases
            for testcase in root.iter('testcase'):
                test_name = testcase.get('name', 'unknown')
                classname = testcase.get('classname', '')
                duration = float(testcase.get('time', 0))

                # Determine test status
                failure = testcase.find('failure')
                error = testcase.find('error')
                skipped = testcase.find('skipped')

                if failure is not None:
                    status = "failed"
                    message = failure.get('message', '')
                    traceback = failure.text or ''
                elif error is not None:
                    status = "error"
                    message = error.get('message', '')
                    traceback = error.text or ''
                elif skipped is not None:
                    status = "skipped"
                    message = skipped.get('message', '')
                    traceback = None
                else:
                    status = "passed"
                    message = ''
                    traceback = None

                # Store test result
                full_test_name = f"{classname}::{test_name}" if classname else test_name
                results["tests"][full_test_name] = {
                    "status": status,
                    "message": message,
                    "duration": duration,
                    "traceback": traceback
                }

            return results

        except ET.ParseError as e:
            logger.warning(f"Failed to parse JUnit XML {xml_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing test results from {xml_path}: {e}")
            return None

    def get_task_test_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get test results for a specific task.

        Looks for test files associated with the task and attempts to extract results.

        Args:
            task_id: Task ID to get test results for

        Returns:
            Test results dictionary or None if no test results available
        """
        task_reqs = self.get_task_requirements(task_id)
        if task_reqs is None:
            return None

        # Look for test files in task metadata
        metadata = task_reqs.get("metadata", {})
        test_files = metadata.get("verification_files", [])

        if not test_files:
            # Try to infer test file from main file path
            file_path = task_reqs.get("file_path")
            if file_path and file_path.startswith("src/"):
                # Convert src/module/file.py to tests/test_module/test_file.py
                test_path = file_path.replace("src/", "tests/test_", 1)
                test_path = test_path.replace(".py", ".py").replace("/", "/test_", 1)
                test_files = [test_path]

        # Try to get results from each test file
        all_results = None
        for test_file in test_files:
            if Path(test_file).exists():
                results = self._run_and_parse_tests(test_file)
                if results:
                    if all_results is None:
                        all_results = results
                    else:
                        # Merge results from multiple test files
                        all_results["total"] += results["total"]
                        all_results["passed"] += results["passed"]
                        all_results["failed"] += results["failed"]
                        all_results["errors"] += results["errors"]
                        all_results["skipped"] += results["skipped"]
                        all_results["duration"] += results["duration"]
                        all_results["tests"].update(results["tests"])

        return all_results
