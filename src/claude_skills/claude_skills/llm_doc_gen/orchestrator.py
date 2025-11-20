"""
Documentation Generation Orchestrator.

Implements write-as-you-go pattern to prevent context exhaustion:
- Generate shards one at a time
- Write immediately to disk after generation
- Purge detailed content from context, keep only summaries
- Batch processing for memory management
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ShardResult:
    """Result of generating a single documentation shard."""

    shard_name: str
    filename: str
    success: bool
    summary: str  # Brief 1-2 sentence summary (purge detailed content)
    error: Optional[str] = None


@dataclass
class OrchestrationState:
    """Tracks orchestration progress for resumability."""

    project_root: str
    output_folder: str
    started_at: str
    last_updated: str
    completed_shards: List[str]
    failed_shards: List[str]
    pending_shards: List[str]
    shard_summaries: Dict[str, str]  # shard_name -> summary


class DocumentationOrchestrator:
    """
    Orchestrates documentation generation with write-as-you-go pattern.

    Key principles:
    1. Write shards immediately to disk
    2. Purge detailed findings from context after writing
    3. Keep only 1-2 sentence summaries in memory
    4. Batch processing to manage memory
    5. State tracking for resumability
    """

    def __init__(self, project_root: Path, output_dir: Path):
        """
        Initialize orchestrator.

        Args:
            project_root: Root directory of the project being documented
            output_dir: Directory where documentation will be written
        """
        self.project_root = project_root
        self.output_dir = output_dir
        self.state_file = output_dir / "doc-generation-state.json"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_documentation(
        self,
        project_data: Dict[str, Any],
        shard_generators: Dict[str, Callable],
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Generate all documentation shards with write-as-you-go pattern.

        Args:
            project_data: Structured project data for generation
            shard_generators: Dict mapping shard names to generator callables
            resume: Whether to resume from previous state

        Returns:
            Dict with generation results and summaries
        """
        # Initialize or load state
        state = self._load_or_init_state(project_data, list(shard_generators.keys()), resume)

        results = {
            "success": True,
            "shards_generated": [],
            "shards_failed": [],
            "summaries": {}
        }

        # Process each pending shard
        for shard_name in state.pending_shards[:]:  # Copy list to allow modification
            try:
                # Generate shard
                generator_func = shard_generators[shard_name]
                shard_content = generator_func(project_data)

                # IMMEDIATELY write to disk
                shard_filename = self._get_shard_filename(shard_name)
                shard_path = self.output_dir / shard_filename
                shard_path.write_text(shard_content)

                # Create brief summary (PURGE detailed content)
                summary = self._create_summary(shard_name, shard_content)

                # Update state
                state.completed_shards.append(shard_name)
                state.pending_shards.remove(shard_name)
                state.shard_summaries[shard_name] = summary
                state.last_updated = datetime.now().isoformat()

                # Save state after each shard (resumability)
                self._save_state(state)

                # Store result (summary only, detailed content purged)
                results["shards_generated"].append(shard_name)
                results["summaries"][shard_name] = summary

                # Context purging: detailed shard_content no longer referenced
                # Python will garbage collect it automatically

            except Exception as e:
                # Handle failure
                error_msg = f"Failed to generate {shard_name}: {str(e)}"
                state.failed_shards.append(shard_name)
                state.pending_shards.remove(shard_name)
                state.last_updated = datetime.now().isoformat()
                self._save_state(state)

                results["shards_failed"].append(shard_name)
                results["summaries"][shard_name] = error_msg
                results["success"] = False

        return results

    def generate_documentation_batched(
        self,
        project_data: Dict[str, Any],
        shard_generators: Dict[str, Callable],
        batch_size: int = 3,
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Generate documentation in batches for better memory management.

        Processes shards in groups, allowing for memory cleanup between batches.

        Args:
            project_data: Structured project data for generation
            shard_generators: Dict mapping shard names to generator callables
            batch_size: Number of shards to process before yielding control
            resume: Whether to resume from previous state

        Returns:
            Dict with generation results and summaries
        """
        # Initialize or load state
        state = self._load_or_init_state(project_data, list(shard_generators.keys()), resume)

        results = {
            "success": True,
            "shards_generated": [],
            "shards_failed": [],
            "summaries": {},
            "batches_processed": 0
        }

        # Process shards in batches
        pending = state.pending_shards[:]
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]

            # Process batch
            for shard_name in batch:
                try:
                    # Generate shard
                    generator_func = shard_generators[shard_name]
                    shard_content = generator_func(project_data)

                    # IMMEDIATELY write to disk
                    shard_filename = self._get_shard_filename(shard_name)
                    shard_path = self.output_dir / shard_filename
                    shard_path.write_text(shard_content)

                    # Create brief summary (PURGE detailed content)
                    summary = self._create_summary(shard_name, shard_content)

                    # Update state
                    state.completed_shards.append(shard_name)
                    state.pending_shards.remove(shard_name)
                    state.shard_summaries[shard_name] = summary
                    state.last_updated = datetime.now().isoformat()

                    # Save state after each shard
                    self._save_state(state)

                    # Store result (summary only)
                    results["shards_generated"].append(shard_name)
                    results["summaries"][shard_name] = summary

                except Exception as e:
                    # Handle failure
                    error_msg = f"Failed to generate {shard_name}: {str(e)}"
                    state.failed_shards.append(shard_name)
                    state.pending_shards.remove(shard_name)
                    state.last_updated = datetime.now().isoformat()
                    self._save_state(state)

                    results["shards_failed"].append(shard_name)
                    results["summaries"][shard_name] = error_msg
                    results["success"] = False

            # Batch complete - increment counter
            results["batches_processed"] += 1

            # Explicit context cleanup between batches
            # (Python's GC will handle this, but we can hint at it)
            # In practice, this is where you might yield control or checkpoint

        return results

    def _load_or_init_state(
        self,
        project_data: Dict[str, Any],
        shard_names: List[str],
        resume: bool
    ) -> OrchestrationState:
        """Load existing state or initialize new state."""
        if resume and self.state_file.exists():
            # Load existing state
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            return OrchestrationState(
                project_root=data["project_root"],
                output_folder=data["output_folder"],
                started_at=data["started_at"],
                last_updated=data["last_updated"],
                completed_shards=data["completed_shards"],
                failed_shards=data["failed_shards"],
                pending_shards=data["pending_shards"],
                shard_summaries=data["shard_summaries"]
            )
        else:
            # Initialize new state
            return OrchestrationState(
                project_root=str(self.project_root),
                output_folder=str(self.output_dir),
                started_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                completed_shards=[],
                failed_shards=[],
                pending_shards=shard_names,
                shard_summaries={}
            )

    def _save_state(self, state: OrchestrationState) -> None:
        """Save current state to disk for resumability."""
        state_data = {
            "project_root": state.project_root,
            "output_folder": state.output_folder,
            "started_at": state.started_at,
            "last_updated": state.last_updated,
            "completed_shards": state.completed_shards,
            "failed_shards": state.failed_shards,
            "pending_shards": state.pending_shards,
            "shard_summaries": state.shard_summaries
        }

        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

    def _get_shard_filename(self, shard_name: str) -> str:
        """Map shard name to output filename."""
        # Common mappings
        filename_map = {
            "project_overview": "project-overview.md",
            "architecture": "architecture.md",
            "component_inventory": "component-inventory.md",
            "source_tree": "source-tree-analysis.md",
            "development_guide": "development-guide.md",
            "api_contracts": "api-contracts.md",
            "data_models": "data-models.md",
            "integration_architecture": "integration-architecture.md",
            "index": "index.md"
        }

        return filename_map.get(shard_name, f"{shard_name}.md")

    def _create_summary(self, shard_name: str, content: str) -> str:
        """
        Create brief 1-2 sentence summary of shard (for context purging).

        Following write-as-you-go pattern: keep only summary, purge detailed content.

        Args:
            shard_name: Name of the shard
            content: Full content of the shard

        Returns:
            Brief summary string
        """
        # Count approximate tokens (rough estimate: 4 chars per token)
        token_count = len(content) // 4
        line_count = content.count('\n')

        # Create summary
        summary = f"{shard_name} generated: {line_count} lines, ~{token_count} tokens"

        return summary

    def get_completed_shards(self) -> List[str]:
        """Get list of completed shards (for index generation)."""
        if not self.state_file.exists():
            return []

        with open(self.state_file, 'r') as f:
            data = json.load(f)

        return data.get("completed_shards", [])

    def cleanup_state(self) -> None:
        """Remove state file after successful completion."""
        if self.state_file.exists():
            self.state_file.unlink()
