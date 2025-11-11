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
import hashlib

from claude_skills.common.spec import load_json_spec, get_node
from claude_skills.common.paths import find_specs_directory
from claude_skills.common.git_metadata import find_git_root
from claude_skills.common.cache import CacheManager

logger = logging.getLogger(__name__)


class FidelityReviewer:
    """
    Core class for performing fidelity reviews of implementations against specs.

    This class will be implemented in Phase 3 (Core Review Logic).
    """

    def __init__(self, spec_id: str, spec_path: Optional[Path] = None, incremental: bool = False):
        """
        Initialize the fidelity reviewer.

        Args:
            spec_id: Specification ID to review against
            spec_path: Optional path to specs directory
            incremental: Enable incremental mode (only review changed files)
        """
        self.spec_id = spec_id
        self.spec_path = spec_path
        self.spec_data: Optional[Dict[str, Any]] = None
        self.incremental = incremental
        self.cache = CacheManager() if incremental else None
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

    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Compute SHA256 hash of file contents.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal hash string, or None if file cannot be read

        Note:
            Reads file in binary mode to handle all file types correctly.
            Uses chunked reading to efficiently handle large files.
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read file in 8KB chunks for memory efficiency
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return None

    def get_file_changes(self, files: List[Path]) -> Dict[str, Any]:
        """
        Detect file changes compared to previous review run.

        This method uses incremental state tracking to identify which files
        have been added, modified, or removed since the last review.

        Args:
            files: List of file paths to check

        Returns:
            Dictionary containing:
            {
                'added': List[str],      # Files that are new
                'modified': List[str],   # Files with changed content
                'removed': List[str],    # Files that no longer exist
                'unchanged': List[str],  # Files with same content
                'is_incremental': bool   # Whether incremental mode was used
            }

        Note:
            If incremental mode is disabled (self.incremental=False), this
            returns all files as 'added' (full review mode).
        """
        if not self.incremental or self.cache is None:
            # Full review mode - treat all files as new
            return {
                'added': [str(f) for f in files],
                'modified': [],
                'removed': [],
                'unchanged': [],
                'is_incremental': False
            }

        # Load previous state from cache
        old_hashes = self.cache.get_incremental_state(self.spec_id)

        if not old_hashes:
            # No previous state - first incremental run
            logger.info(f"No previous state found for {self.spec_id}, performing full review")
            return {
                'added': [str(f) for f in files],
                'modified': [],
                'removed': [],
                'unchanged': [],
                'is_incremental': False
            }

        # Compute hashes for current files
        new_hashes = {}
        for file_path in files:
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                new_hashes[str(file_path)] = file_hash

        # Detect changes using CacheManager utility
        changes = CacheManager.compare_file_hashes(old_hashes, new_hashes)
        changes['is_incremental'] = True

        logger.info(
            f"File changes for {self.spec_id}: "
            f"{len(changes['added'])} added, "
            f"{len(changes['modified'])} modified, "
            f"{len(changes['removed'])} removed, "
            f"{len(changes['unchanged'])} unchanged"
        )

        return changes

    def save_file_state(self, files: List[Path]) -> bool:
        """
        Save current file hashes for future incremental reviews.

        Args:
            files: List of file paths to hash and save

        Returns:
            True if state was saved successfully, False otherwise

        Note:
            Only saves state if incremental mode is enabled.
        """
        if not self.incremental or self.cache is None:
            # Not in incremental mode, skip saving
            return False

        # Compute hashes for all files
        file_hashes = {}
        for file_path in files:
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                file_hashes[str(file_path)] = file_hash

        # Save to cache
        result = self.cache.save_incremental_state(self.spec_id, file_hashes)

        if result:
            logger.info(f"Saved incremental state for {self.spec_id}: {len(file_hashes)} files")
        else:
            logger.warning(f"Failed to save incremental state for {self.spec_id}")

        return result

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

    def get_journal_entries(
        self,
        task_id: Optional[str] = None,
        include_internal: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get journal entries from the spec, optionally filtered by task.

        Args:
            task_id: Optional task ID to filter entries (None = all entries)
            include_internal: Include internal journal entries (default: False)

        Returns:
            List of journal entry dictionaries:
            [
                {
                    "timestamp": str,
                    "type": str,
                    "title": str,
                    "content": str,
                    "task_id": Optional[str],
                    "metadata": Dict
                }
            ]
        """
        if self.spec_data is None:
            print("Error: Spec not loaded", file=sys.stderr)
            return []

        journals = self.spec_data.get("journals", [])
        if not journals:
            return []

        # Filter journals
        filtered = []
        for entry in journals:
            # Skip internal entries if not requested
            if not include_internal and entry.get("type") == "internal":
                continue

            # Filter by task_id if specified
            if task_id and entry.get("task_id") != task_id:
                continue

            filtered.append(entry)

        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return filtered

    def get_task_journals(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get journal entries specifically related to a task.

        Args:
            task_id: Task ID to get journals for

        Returns:
            List of journal entries for this task
        """
        return self.get_journal_entries(task_id=task_id, include_internal=False)

    def generate_review_prompt(
        self,
        task_id: Optional[str] = None,
        phase_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        include_tests: bool = True,
        base_branch: str = "main"
    ) -> str:
        """
        Generate AI review prompt comparing implementation against specification.

        This method will be implemented in task-3-7 according to the template
        structure defined below.

        Args:
            task_id: Optional task ID to review
            phase_id: Optional phase ID to review
            file_paths: Optional list of specific files to review
            include_tests: Include test results in prompt (default: True)
            base_branch: Base branch for git diff (default: "main")

        Returns:
            Formatted prompt string ready for AI reviewer

        Template Structure:
        ------------------

        The prompt follows this structure with clear sections:

        1. CONTEXT SECTION
           - Spec overview (spec_id, title, description)
           - Review scope (task/phase/files)
           - Success criteria from spec

        2. SPECIFICATION REQUIREMENTS
           - Task/phase requirements from spec JSON
           - Expected behavior and outcomes
           - Verification steps defined in spec
           - Dependencies and constraints

        3. IMPLEMENTATION ARTIFACTS
           - Git diffs showing actual changes
           - File paths and modifications
           - Code snippets (if needed)

        4. TEST RESULTS (if include_tests=True)
           - Test execution summary (passed/failed/skipped)
           - Failed test details with tracebacks
           - Coverage information (if available)

        5. JOURNAL ENTRIES
           - Relevant journal entries for context
           - Decisions and deviations documented
           - Implementation notes from developer

        6. REVIEW QUESTIONS
           - Does implementation match spec requirements?
           - Are all verification steps satisfied?
           - Are there any deviations? If so, are they justified?
           - Are tests comprehensive and passing?
           - Are there any quality or maintainability concerns?

        Data Flow:
        ----------
        - Spec requirements: get_task_requirements() / get_phase_tasks()
        - Git diffs: get_task_diffs() / get_branch_diff()
        - Test results: get_task_test_results() / get_test_results()
        - Journal entries: get_task_journals() / get_journal_entries()

        Format Notes:
        -------------
        - Use markdown formatting for readability
        - Include code blocks with syntax highlighting
        - Separate sections with clear headers
        - Keep diffs focused (truncate if too large)
        - Highlight critical information (failures, deviations)

        Example Output Structure:
        -------------------------

        # Implementation Fidelity Review

        ## Context
        **Spec:** {spec_id} - {title}
        **Scope:** Task {task_id} - {task_title}
        **File:** {file_path}

        ## Specification Requirements
        **Objective:** {description}
        **Success Criteria:**
        - {verification_step_1}
        - {verification_step_2}

        ## Implementation Artifacts
        ### Git Diff
        ```diff
        {git_diff_output}
        ```

        ## Test Results
        **Status:** {passed}/{total} tests passed
        **Failed Tests:**
        - {test_name}: {failure_message}

        ## Journal Entries
        - {timestamp} - {title}: {content}

        ## Review Questions
        1. Does the implementation match spec requirements?
        2. Are all verification steps satisfied?
        3. Are there any deviations from the spec?
        4. Are tests comprehensive and passing?
        5. Are there quality or maintainability concerns?

        ---

        Note: Implementation for this method will be added in task-3-7.
        """
        if self.spec_data is None:
            return "Error: Specification not loaded"

        # Determine review scope
        scope_description = ""
        requirements_list = []

        if task_id:
            # Single task review
            task_reqs = self.get_task_requirements(task_id)
            if not task_reqs:
                return f"Error: Task {task_id} not found"
            requirements_list = [task_reqs]
            scope_description = f"Task {task_id} - {task_reqs['title']}"
        elif phase_id:
            # Phase review
            phase_tasks = self.get_phase_tasks(phase_id)
            if not phase_tasks:
                return f"Error: Phase {phase_id} not found"
            requirements_list = phase_tasks
            phase_node = get_node(self.spec_data, phase_id)
            phase_title = phase_node.get("title", "") if phase_node else ""
            scope_description = f"Phase {phase_id} - {phase_title}"
        elif file_paths:
            # File-based review
            scope_description = f"Files: {', '.join(file_paths)}"
            # Note: File-based review doesn't have specific task requirements
        else:
            # Full spec review
            requirements_list = self.get_all_tasks() or []
            scope_description = "Full Specification"

        # Build prompt sections
        prompt_parts = []

        # 1. CONTEXT SECTION
        prompt_parts.append("# Implementation Fidelity Review\n")
        prompt_parts.append("## Context\n")
        prompt_parts.append(f"**Spec ID:** {self.spec_id}\n")

        spec_title = self.spec_data.get("title", "Untitled")
        prompt_parts.append(f"**Spec Title:** {spec_title}\n")

        spec_description = self.spec_data.get("description", "")
        if spec_description:
            prompt_parts.append(f"**Description:** {spec_description}\n")

        prompt_parts.append(f"**Review Scope:** {scope_description}\n\n")

        # 2. SPECIFICATION REQUIREMENTS
        if requirements_list:
            prompt_parts.append("## Specification Requirements\n\n")

            for req in requirements_list:
                prompt_parts.append(f"### {req['task_id']}: {req['title']}\n\n")

                if req.get('description'):
                    prompt_parts.append(f"**Objective:** {req['description']}\n\n")

                if req.get('file_path'):
                    prompt_parts.append(f"**File:** `{req['file_path']}`\n\n")

                verification_steps = req.get('verification_steps', [])
                if verification_steps:
                    prompt_parts.append("**Success Criteria:**\n")
                    for step in verification_steps:
                        prompt_parts.append(f"- {step}\n")
                    prompt_parts.append("\n")

                dependencies = req.get('dependencies', {})
                blocked_by = dependencies.get('blocked_by', [])
                if blocked_by:
                    prompt_parts.append(f"**Dependencies:** {', '.join(blocked_by)}\n\n")

        # 3. IMPLEMENTATION ARTIFACTS
        prompt_parts.append("## Implementation Artifacts\n\n")

        if task_id:
            # Get diffs for specific task
            task_diffs = self.get_task_diffs(task_id)
            if task_diffs:
                for file_path, diff_content in task_diffs.items():
                    if diff_content:
                        prompt_parts.append(f"### File: `{file_path}`\n\n")
                        prompt_parts.append("```diff\n")
                        prompt_parts.append(diff_content)
                        prompt_parts.append("\n```\n\n")
                    else:
                        prompt_parts.append(f"### File: `{file_path}`\n\n")
                        prompt_parts.append("*No changes detected*\n\n")
            else:
                prompt_parts.append("*No git diff available*\n\n")
        elif phase_id:
            # Get diffs for entire phase
            phase_diffs = self.get_phase_diffs(phase_id)
            if phase_diffs:
                for tid, file_diffs in phase_diffs.items():
                    prompt_parts.append(f"### Task: {tid}\n\n")
                    for file_path, diff_content in file_diffs.items():
                        if diff_content:
                            prompt_parts.append(f"**File:** `{file_path}`\n\n")
                            prompt_parts.append("```diff\n")
                            # Truncate large diffs
                            if len(diff_content) > 5000:
                                prompt_parts.append(diff_content[:5000])
                                prompt_parts.append("\n... (truncated)\n")
                            else:
                                prompt_parts.append(diff_content)
                            prompt_parts.append("\n```\n\n")
            else:
                prompt_parts.append("*No git diffs available*\n\n")
        elif file_paths:
            # Get diffs for specific files
            for file_path in file_paths:
                diff_content = self.get_file_diff(file_path)
                if diff_content:
                    prompt_parts.append(f"### File: `{file_path}`\n\n")
                    prompt_parts.append("```diff\n")
                    prompt_parts.append(diff_content)
                    prompt_parts.append("\n```\n\n")
                else:
                    prompt_parts.append(f"### File: `{file_path}`\n\n")
                    prompt_parts.append("*No changes detected*\n\n")
        else:
            # Full spec - get branch diff
            branch_diff = self.get_branch_diff(base_branch)
            if branch_diff:
                prompt_parts.append("### Full Branch Diff\n\n")
                prompt_parts.append("```diff\n")
                prompt_parts.append(branch_diff)
                prompt_parts.append("\n```\n\n")
            else:
                prompt_parts.append("*No git diff available*\n\n")

        # 4. TEST RESULTS
        if include_tests:
            prompt_parts.append("## Test Results\n\n")

            test_results = None
            if task_id:
                test_results = self.get_task_test_results(task_id)

            if test_results:
                total = test_results.get('total', 0)
                passed = test_results.get('passed', 0)
                failed = test_results.get('failed', 0)
                errors = test_results.get('errors', 0)
                skipped = test_results.get('skipped', 0)
                duration = test_results.get('duration', 0.0)

                prompt_parts.append(f"**Status:** {passed}/{total} tests passed\n")
                prompt_parts.append(f"**Duration:** {duration:.2f}s\n")

                if failed > 0 or errors > 0:
                    prompt_parts.append(f"**Failed:** {failed}, **Errors:** {errors}\n\n")

                    # Show failed test details
                    prompt_parts.append("**Failed Tests:**\n")
                    tests = test_results.get('tests', {})
                    for test_name, test_data in tests.items():
                        if test_data['status'] in ['failed', 'error']:
                            prompt_parts.append(f"\n- **{test_name}**\n")
                            message = test_data.get('message', '')
                            if message:
                                prompt_parts.append(f"  - Message: {message}\n")
                            traceback = test_data.get('traceback')
                            if traceback:
                                prompt_parts.append(f"  - Traceback:\n```\n{traceback}\n```\n")
                else:
                    prompt_parts.append("\n*All tests passed!*\n")

                if skipped > 0:
                    prompt_parts.append(f"\n**Skipped:** {skipped} tests\n")

                prompt_parts.append("\n")
            else:
                prompt_parts.append("*No test results available*\n\n")

        # 5. JOURNAL ENTRIES
        prompt_parts.append("## Journal Entries\n\n")

        journal_entries = []
        if task_id:
            journal_entries = self.get_task_journals(task_id)
        elif phase_id:
            # Get all journals, filter by phase tasks later if needed
            journal_entries = self.get_journal_entries()
        else:
            journal_entries = self.get_journal_entries()

        if journal_entries:
            for entry in journal_entries:
                timestamp = entry.get('timestamp', '')
                title = entry.get('title', '')
                content = entry.get('content', '')
                entry_task_id = entry.get('task_id', '')

                if entry_task_id:
                    prompt_parts.append(f"**[{timestamp}] {title}** (Task: {entry_task_id})\n")
                else:
                    prompt_parts.append(f"**[{timestamp}] {title}**\n")

                if content:
                    prompt_parts.append(f"{content}\n\n")
        else:
            prompt_parts.append("*No journal entries found*\n\n")

        # 6. REVIEW QUESTIONS
        prompt_parts.append("## Review Questions\n\n")
        prompt_parts.append("Please evaluate the implementation against the specification:\n\n")
        prompt_parts.append("1. **Requirement Alignment:** Does the implementation match the spec requirements?\n")
        prompt_parts.append("2. **Success Criteria:** Are all verification steps satisfied?\n")
        prompt_parts.append("3. **Deviations:** Are there any deviations from the spec? If so, are they justified?\n")

        if include_tests:
            prompt_parts.append("4. **Test Coverage:** Are tests comprehensive and passing?\n")

        prompt_parts.append("5. **Code Quality:** Are there any quality, maintainability, or security concerns?\n")
        prompt_parts.append("6. **Documentation:** Is the implementation properly documented?\n\n")

        prompt_parts.append("### Required Response Format\n\n")
        prompt_parts.append(
            "Respond **only** with valid JSON matching the schema below. Do not include Markdown, prose, or additional commentary outside the JSON object.\n\n"
        )
        prompt_parts.append("```json\n")
        prompt_parts.append(
            '{\n'
            '  "verdict": "pass|fail|partial|unknown",\n'
            '  "summary": "Overall findings (any length).",\n'
            '  "requirement_alignment": {\n'
            '    "answer": "yes|no|partial",\n'
            '    "details": "Explain how implementation aligns or diverges."\n'
            '  },\n'
            '  "success_criteria": {\n'
            '    "met": "yes|no|partial",\n'
            '    "details": "Call out verification steps passed or missing."\n'
            '  },\n'
            '  "deviations": [\n'
            '    {\n'
            '      "description": "Describe deviation from the spec.",\n'
            '      "justification": "Optional rationale or evidence.",\n'
            '      "severity": "blocking|major|minor"\n'
            '    }\n'
            '  ],\n'
            '  "test_coverage": {\n'
            '    "status": "sufficient|insufficient|not_applicable",\n'
            '    "details": "Summarise test evidence or gaps."\n'
            '  },\n'
            '  "code_quality": {\n'
            '    "issues": ["Describe each notable quality concern."],\n'
            '    "details": "Optional supporting commentary."\n'
            '  },\n'
            '  "documentation": {\n'
            '    "status": "adequate|inadequate|not_applicable",\n'
            '    "details": "Note doc updates or omissions."\n'
            '  },\n'
            '  "issues": ["Concise list of primary issues for consensus logic."],\n'
          '  "recommendations": ["Actionable next steps to resolve findings."]\n'
            '}\n'
        )
        prompt_parts.append("```\n\n")
        prompt_parts.append(
            "Rules:\n"
            "- Use lowercase values shown for enumerated fields (e.g., `verdict`, status flags).\n"
            "- Keep arrays as arrays (use `[]` when a section has nothing to report).\n"
            "- Populate `issues` and `recommendations` with the key takeaways you want surfaced downstream.\n"
            "- Feel free to include additional keys if needed, but never omit the ones above.\n\n"
        )

        prompt_parts.append("## IMPORTANT CONSTRAINTS\n\n")
        prompt_parts.append("**CRITICAL: This is a READ-ONLY review. You MUST NOT:**\n")
        prompt_parts.append("- Write, create, or modify ANY files on disk\n")
        prompt_parts.append("- Execute code or commands\n")
        prompt_parts.append("- Make changes to the codebase\n\n")
        prompt_parts.append("**Your role is ANALYSIS ONLY:**\n")
        prompt_parts.append("- Review the specification and implementation\n")
        prompt_parts.append("- Identify deviations and issues\n")
        prompt_parts.append("- Provide your findings as TEXT in your response\n")
        prompt_parts.append("- Do not reference external files you create or write\n\n")

        prompt_parts.append("---\n")
        prompt_parts.append("\n*Please provide a detailed review addressing each question above.*\n")

        return "".join(prompt_parts)
