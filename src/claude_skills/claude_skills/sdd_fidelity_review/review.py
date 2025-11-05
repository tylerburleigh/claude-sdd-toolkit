"""
Implementation Fidelity Review Core Module

Core functionality for comparing implementation against specifications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

from claude_skills.common.spec import load_json_spec, get_node
from claude_skills.common.paths import find_specs_directory


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
