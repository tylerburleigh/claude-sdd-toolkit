#!/usr/bin/env python3
"""
Freshness checking for codebase analysis documentation.

This module provides utilities to determine if codebase.json needs regeneration
by comparing its timestamp with source file modification times.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone


class FreshnessChecker:
    """
    Check if codebase analysis documentation is up-to-date.

    Compares the generated_at timestamp in codebase.json with source file
    modification times to determine if regeneration is needed.

    Example:
        >>> checker = FreshnessChecker()
        >>> is_fresh, details = checker.check_freshness()
        >>> if not is_fresh:
        ...     print(f"Documentation is stale: {details['reason']}")
    """

    def __init__(
        self,
        docs_path: Optional[str] = None,
        project_root: Optional[str] = None
    ):
        """
        Initialize freshness checker.

        Args:
            docs_path: Path to codebase.json or its directory.
                      Auto-detects in common locations if not provided.
            project_root: Root directory of the project to check.
                         Defaults to current working directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_path = self._resolve_docs_path(docs_path)
        self.metadata: Optional[Dict[str, Any]] = None

    def _resolve_docs_path(self, docs_path: Optional[str]) -> Optional[Path]:
        """
        Resolve path to codebase.json file.

        Args:
            docs_path: Provided path or None for auto-detection

        Returns:
            Path to codebase.json or None if not found
        """
        if docs_path:
            path = Path(docs_path)
            if path.is_dir():
                # Look for codebase.json in directory
                candidate = path / "codebase.json"
                if candidate.exists():
                    return candidate
            elif path.exists():
                return path

        # Auto-detect in common locations
        common_locations = [
            self.project_root / "docs" / "codebase.json",
            self.project_root / ".docs" / "codebase.json",
            self.project_root / "codebase.json",
        ]

        for location in common_locations:
            if location.exists():
                return location

        return None

    def load_metadata(self) -> bool:
        """
        Load metadata from codebase.json.

        Returns:
            True if metadata loaded successfully, False otherwise
        """
        if not self.docs_path or not self.docs_path.exists():
            return False

        try:
            with open(self.docs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data.get('metadata', {})
                return True
        except (json.JSONDecodeError, IOError):
            return False

    def get_generated_timestamp(self) -> Optional[datetime]:
        """
        Get the timestamp when codebase.json was generated.

        Returns:
            Datetime object or None if not available
        """
        if not self.metadata:
            if not self.load_metadata():
                return None

        generated_at = self.metadata.get('generated_at')
        if not generated_at:
            return None

        try:
            # Parse ISO format timestamp
            return datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def get_newest_source_file(
        self,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Tuple[Optional[Path], Optional[datetime]]:
        """
        Find the most recently modified source file.

        Args:
            extensions: List of file extensions to check (e.g., ['.py', '.js'])
                       Defaults to common source file extensions
            exclude_patterns: Directory patterns to exclude (e.g., ['__pycache__', 'node_modules'])

        Returns:
            Tuple of (file_path, modification_time) or (None, None) if no files found
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.rb', '.php']

        if exclude_patterns is None:
            exclude_patterns = [
                '__pycache__', 'node_modules', '.git', '.venv', 'venv',
                'build', 'dist', '.eggs', '*.egg-info', '.tox', '.pytest_cache'
            ]

        newest_file: Optional[Path] = None
        newest_time: Optional[datetime] = None

        def should_exclude(path: Path) -> bool:
            """Check if path matches any exclude pattern."""
            path_str = str(path)
            for pattern in exclude_patterns:
                if pattern in path_str:
                    return True
            return False

        # Walk project directory
        for file_path in self.project_root.rglob('*'):
            # Skip excluded directories
            if should_exclude(file_path):
                continue

            # Check extension
            if file_path.suffix not in extensions:
                continue

            # Skip if not a file
            if not file_path.is_file():
                continue

            try:
                # Get modification time
                mtime = datetime.fromtimestamp(
                    file_path.stat().st_mtime,
                    tz=timezone.utc
                )

                if newest_time is None or mtime > newest_time:
                    newest_time = mtime
                    newest_file = file_path
            except (OSError, ValueError):
                # Skip files we can't read
                continue

        return newest_file, newest_time

    def check_freshness(
        self,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if codebase.json is fresh (up-to-date).

        Args:
            extensions: List of file extensions to check
            exclude_patterns: Directory patterns to exclude

        Returns:
            Tuple of (is_fresh, details_dict)

            is_fresh: True if documentation is current, False if stale
            details: Dictionary containing:
                - status: 'fresh', 'stale', or 'missing'
                - reason: Human-readable explanation
                - generated_at: When docs were generated (if available)
                - newest_file: Path to newest source file (if found)
                - newest_file_time: Modification time of newest file
                - age_seconds: How old the docs are vs newest source
        """
        details: Dict[str, Any] = {
            'status': 'unknown',
            'reason': '',
            'generated_at': None,
            'newest_file': None,
            'newest_file_time': None,
            'age_seconds': None
        }

        # Check if docs exist
        if not self.docs_path or not self.docs_path.exists():
            details['status'] = 'missing'
            details['reason'] = 'No codebase.json found. Run `sdd doc generate` to create it.'
            return False, details

        # Get generated timestamp
        generated_at = self.get_generated_timestamp()
        if not generated_at:
            details['status'] = 'unknown'
            details['reason'] = 'Unable to read generated_at timestamp from codebase.json'
            return False, details

        details['generated_at'] = generated_at.isoformat()

        # Find newest source file
        newest_file, newest_time = self.get_newest_source_file(
            extensions=extensions,
            exclude_patterns=exclude_patterns
        )

        if not newest_file or not newest_time:
            details['status'] = 'unknown'
            details['reason'] = 'No source files found to compare'
            return True, details  # Assume fresh if no sources found

        details['newest_file'] = str(newest_file.relative_to(self.project_root))
        details['newest_file_time'] = newest_time.isoformat()

        # Compare timestamps
        if newest_time > generated_at:
            age_seconds = (newest_time - generated_at).total_seconds()
            details['status'] = 'stale'
            details['age_seconds'] = age_seconds
            details['reason'] = (
                f"Documentation is outdated. Newest source file "
                f"({details['newest_file']}) was modified "
                f"{int(age_seconds)} seconds after docs were generated."
            )
            return False, details
        else:
            details['status'] = 'fresh'
            details['reason'] = 'Documentation is up-to-date'
            return True, details

    def format_freshness_report(
        self,
        is_fresh: bool,
        details: Dict[str, Any],
        include_details: bool = True
    ) -> str:
        """
        Format freshness check results as human-readable text.

        Args:
            is_fresh: Result from check_freshness()
            details: Details dict from check_freshness()
            include_details: Include detailed information

        Returns:
            Formatted string suitable for display
        """
        lines = []

        # Status indicator
        status = details.get('status', 'unknown')
        if status == 'fresh':
            lines.append("✅ Documentation is fresh")
        elif status == 'stale':
            lines.append("⚠️  Documentation is stale")
        elif status == 'missing':
            lines.append("❌ Documentation missing")
        else:
            lines.append("❓ Documentation status unknown")

        # Reason
        lines.append(f"   {details.get('reason', 'No details available')}")

        if include_details:
            lines.append("")

            # Generated at
            generated_at = details.get('generated_at')
            if generated_at:
                lines.append(f"Generated: {generated_at}")

            # Newest file
            newest_file = details.get('newest_file')
            newest_time = details.get('newest_file_time')
            if newest_file and newest_time:
                lines.append(f"Newest source: {newest_file}")
                lines.append(f"Modified: {newest_time}")

            # Age
            age = details.get('age_seconds')
            if age is not None and age > 0:
                hours = int(age / 3600)
                minutes = int((age % 3600) / 60)
                if hours > 0:
                    lines.append(f"Age: {hours}h {minutes}m behind")
                else:
                    lines.append(f"Age: {minutes}m behind")

        return "\n".join(lines)


def check_documentation_freshness(
    docs_path: Optional[str] = None,
    project_root: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to check documentation freshness.

    Args:
        docs_path: Path to codebase.json or its directory
        project_root: Root directory of the project

    Returns:
        Tuple of (is_fresh, details_dict)
    """
    checker = FreshnessChecker(docs_path=docs_path, project_root=project_root)
    return checker.check_freshness()
