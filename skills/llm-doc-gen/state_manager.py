"""
State file management for LLM-based documentation generation.

This module provides state persistence for resumable documentation generation:
- Track processing progress across multiple runs
- Store file and language metadata
- Handle incremental updates
- Support rollback and recovery
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import shutil
from enum import Enum


class ProcessingStatus(Enum):
    """Status of a file or component in the documentation process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileProcessingState:
    """State information for a single file."""
    file_path: str
    status: ProcessingStatus
    language: Optional[str] = None
    last_modified: Optional[str] = None
    processing_started: Optional[str] = None
    processing_completed: Optional[str] = None
    error_message: Optional[str] = None
    entity_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': self.file_path,
            'status': self.status.value,
            'language': self.language,
            'last_modified': self.last_modified,
            'processing_started': self.processing_started,
            'processing_completed': self.processing_completed,
            'error_message': self.error_message,
            'entity_count': self.entity_count
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FileProcessingState':
        """Create instance from dictionary."""
        return FileProcessingState(
            file_path=data['file_path'],
            status=ProcessingStatus(data['status']),
            language=data.get('language'),
            last_modified=data.get('last_modified'),
            processing_started=data.get('processing_started'),
            processing_completed=data.get('processing_completed'),
            error_message=data.get('error_message'),
            entity_count=data.get('entity_count', 0)
        )


@dataclass
class DocumentationState:
    """Complete state of documentation generation process."""
    project_root: str
    output_folder: str
    session_id: str
    created_at: str
    updated_at: str
    version: str = "1.0"

    # Processing metadata
    files: Dict[str, FileProcessingState] = field(default_factory=dict)
    languages_detected: List[str] = field(default_factory=list)
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0

    # Configuration snapshot
    exclude_patterns: List[str] = field(default_factory=list)

    # Progress tracking
    current_phase: Optional[str] = None
    phases_completed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'project_root': self.project_root,
            'output_folder': self.output_folder,
            'session_id': self.session_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'files': {path: file_state.to_dict() for path, file_state in self.files.items()},
            'languages_detected': self.languages_detected,
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'skipped_files': self.skipped_files,
            'exclude_patterns': self.exclude_patterns,
            'current_phase': self.current_phase,
            'phases_completed': self.phases_completed
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DocumentationState':
        """Create instance from dictionary."""
        files = {
            path: FileProcessingState.from_dict(file_data)
            for path, file_data in data.get('files', {}).items()
        }

        return DocumentationState(
            version=data.get('version', '1.0'),
            project_root=data['project_root'],
            output_folder=data['output_folder'],
            session_id=data['session_id'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            files=files,
            languages_detected=data.get('languages_detected', []),
            total_files=data.get('total_files', 0),
            completed_files=data.get('completed_files', 0),
            failed_files=data.get('failed_files', 0),
            skipped_files=data.get('skipped_files', 0),
            exclude_patterns=data.get('exclude_patterns', []),
            current_phase=data.get('current_phase'),
            phases_completed=data.get('phases_completed', [])
        )


class StateManager:
    """
    Manages documentation generation state persistence.

    Features:
    - Atomic writes with backup
    - State validation
    - Progress tracking
    - Resume capability
    - Error recovery
    """

    STATE_FILENAME = "doc-gen-state.json"
    BACKUP_SUFFIX = ".backup"

    def __init__(self, output_folder: Path, verbose: bool = False):
        """
        Initialize the state manager.

        Args:
            output_folder: Directory where state file will be stored
            verbose: Enable verbose output
        """
        self.output_folder = Path(output_folder).resolve()
        self.state_file = self.output_folder / self.STATE_FILENAME
        self.backup_file = self.output_folder / f"{self.STATE_FILENAME}{self.BACKUP_SUFFIX}"
        self.verbose = verbose

        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def create_new_state(
        self,
        project_root: Path,
        session_id: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> DocumentationState:
        """
        Create a new documentation state.

        Args:
            project_root: Root directory of the project being documented
            session_id: Optional session identifier (generated if not provided)
            exclude_patterns: Patterns to exclude from processing

        Returns:
            New DocumentationState instance
        """
        now = datetime.utcnow().isoformat()

        if session_id is None:
            session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        state = DocumentationState(
            project_root=str(project_root.resolve()),
            output_folder=str(self.output_folder),
            session_id=session_id,
            created_at=now,
            updated_at=now,
            exclude_patterns=exclude_patterns or []
        )

        if self.verbose:
            print(f"📝 Created new state for session: {session_id}")

        return state

    def save_state(self, state: DocumentationState) -> None:
        """
        Save state to disk with atomic write and backup.

        Args:
            state: State to save

        Raises:
            IOError: If write fails
        """
        # Update timestamp
        state.updated_at = datetime.utcnow().isoformat()

        # Create backup if state file exists
        if self.state_file.exists():
            shutil.copy2(self.state_file, self.backup_file)
            if self.verbose:
                print(f"💾 Created backup: {self.backup_file.name}")

        # Write to temporary file first (atomic write)
        temp_file = self.state_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)

            # Atomic rename
            temp_file.replace(self.state_file)

            if self.verbose:
                print(f"✅ Saved state to: {self.state_file.name}")

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise IOError(f"Failed to save state: {e}")

    def load_state(self) -> Optional[DocumentationState]:
        """
        Load state from disk.

        Returns:
            DocumentationState if file exists and is valid, None otherwise
        """
        if not self.state_file.exists():
            if self.verbose:
                print(f"ℹ️  No state file found: {self.state_file.name}")
            return None

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            state = DocumentationState.from_dict(data)

            if self.verbose:
                print(f"📖 Loaded state from: {self.state_file.name}")
                print(f"   Session: {state.session_id}")
                print(f"   Progress: {state.completed_files}/{state.total_files} files")

            return state

        except (json.JSONDecodeError, KeyError) as e:
            if self.verbose:
                print(f"⚠️  Failed to load state: {e}")

            # Try to restore from backup
            return self._restore_from_backup()

    def _restore_from_backup(self) -> Optional[DocumentationState]:
        """
        Attempt to restore state from backup file.

        Returns:
            DocumentationState if backup exists and is valid, None otherwise
        """
        if not self.backup_file.exists():
            if self.verbose:
                print(f"❌ No backup file found: {self.backup_file.name}")
            return None

        try:
            with open(self.backup_file, 'r') as f:
                data = json.load(f)

            state = DocumentationState.from_dict(data)

            if self.verbose:
                print(f"♻️  Restored state from backup: {self.backup_file.name}")

            # Save restored state as current
            self.save_state(state)

            return state

        except (json.JSONDecodeError, KeyError) as e:
            if self.verbose:
                print(f"❌ Failed to restore from backup: {e}")
            return None

    def state_exists(self) -> bool:
        """
        Check if a state file exists.

        Returns:
            True if state file exists, False otherwise
        """
        return self.state_file.exists()

    def delete_state(self, keep_backup: bool = True) -> None:
        """
        Delete the state file.

        Args:
            keep_backup: If True, keep the backup file
        """
        if self.state_file.exists():
            if keep_backup and not self.backup_file.exists():
                shutil.copy2(self.state_file, self.backup_file)

            self.state_file.unlink()

            if self.verbose:
                print(f"🗑️  Deleted state file: {self.state_file.name}")

    def update_file_status(
        self,
        state: DocumentationState,
        file_path: str,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
        entity_count: int = 0
    ) -> None:
        """
        Update the status of a file in the state.

        Args:
            state: Current state
            file_path: Path to file being updated
            status: New processing status
            error_message: Optional error message if status is FAILED
            entity_count: Number of entities found in file
        """
        now = datetime.utcnow().isoformat()

        # Check if file existed before
        is_new_file = file_path not in state.files

        if is_new_file:
            state.files[file_path] = FileProcessingState(
                file_path=file_path,
                status=status
            )
            old_status = None
        else:
            old_status = state.files[file_path].status

        file_state = state.files[file_path]
        file_state.status = status

        if status == ProcessingStatus.IN_PROGRESS:
            file_state.processing_started = now
        elif status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.SKIPPED):
            file_state.processing_completed = now

        if error_message:
            file_state.error_message = error_message

        if entity_count > 0:
            file_state.entity_count = entity_count

        # Update counters - only increment if status actually changed or is new
        if old_status != status:
            if status == ProcessingStatus.COMPLETED:
                state.completed_files += 1
            elif status == ProcessingStatus.FAILED:
                state.failed_files += 1
            elif status == ProcessingStatus.SKIPPED:
                state.skipped_files += 1

    def get_resumable_files(self, state: DocumentationState) -> List[str]:
        """
        Get list of files that can be resumed (pending or failed).

        Args:
            state: Current state

        Returns:
            List of file paths that need processing
        """
        resumable = []
        for file_path, file_state in state.files.items():
            if file_state.status in (ProcessingStatus.PENDING, ProcessingStatus.FAILED):
                resumable.append(file_path)

        return resumable

    def get_progress_summary(self, state: DocumentationState) -> Dict[str, Any]:
        """
        Get a summary of processing progress.

        Args:
            state: Current state

        Returns:
            Dictionary with progress metrics
        """
        total = state.total_files
        completed = state.completed_files
        failed = state.failed_files
        skipped = state.skipped_files
        pending = total - completed - failed - skipped

        percentage = (completed / total * 100) if total > 0 else 0

        return {
            'total_files': total,
            'completed': completed,
            'failed': failed,
            'skipped': skipped,
            'pending': pending,
            'percentage': round(percentage, 1),
            'languages': state.languages_detected,
            'current_phase': state.current_phase,
            'phases_completed': state.phases_completed
        }


def create_state_manager(
    output_folder: str,
    verbose: bool = False
) -> StateManager:
    """
    Create a state manager instance.

    Args:
        output_folder: Directory where state file will be stored
        verbose: Enable verbose output

    Returns:
        Configured StateManager instance

    Example:
        >>> manager = create_state_manager("/path/to/output", verbose=True)
        >>> state = manager.create_new_state(Path("/path/to/project"))
        >>> manager.save_state(state)
    """
    return StateManager(Path(output_folder), verbose=verbose)
