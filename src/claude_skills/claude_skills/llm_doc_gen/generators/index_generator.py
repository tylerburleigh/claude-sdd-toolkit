"""
Index Generator for LLM-based Documentation.

Generates index.md following 7-section structure with project navigation.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ProjectPart:
    """Represents a single part in a multi-part project."""

    part_id: str
    part_name: str
    project_type: str
    root_path: str
    tech_stack_summary: str
    entry_point: str
    architecture_pattern: str
    prerequisites: str
    setup_command: str
    run_command: str
    has_components: bool = False
    has_api: bool = False
    has_data: bool = False


@dataclass
class ExistingDoc:
    """Represents existing documentation in the project."""

    title: str
    path: str
    description: str


@dataclass
class IndexData:
    """Structured data for index.md generation."""

    project_name: str
    repository_type: str  # monolith, monorepo, multi-part
    primary_language: str
    architecture_type: str
    project_description: str
    tech_stack_summary: str  # For single-part projects
    entry_point: str  # For single-part projects
    architecture_pattern: str  # For single-part projects
    database: Optional[str] = None
    deployment_platform: Optional[str] = None
    prerequisites: Optional[str] = None
    setup_commands: Optional[str] = None
    run_commands: Optional[str] = None
    test_commands: Optional[str] = None
    is_multi_part: bool = False
    parts_count: int = 0
    project_parts: Optional[List[ProjectPart]] = None
    integration_summary: Optional[str] = None
    has_ui_components: bool = False
    has_api_docs: bool = False
    has_data_models: bool = False
    has_deployment_guide: bool = False
    has_contribution_guide: bool = False
    existing_docs: Optional[List[ExistingDoc]] = None
    ui_part_id: Optional[str] = None  # For multi-part: which part is UI
    api_part_id: Optional[str] = None  # For multi-part: which part is API
    file_count: Optional[int] = None  # Total files in project
    total_loc: Optional[int] = None  # Total lines of code
    primary_languages: Optional[List[str]] = None  # Top languages by usage


class IndexGenerator:
    """
    Generates index.md following 7-section structure.

    The 7 sections:
    1. Header (project metadata)
    2. Project Overview (description + multi-part structure)
    3. Quick Reference (stack/entry/patterns)
    4. Generated Documentation (links to shards)
    5. Existing Documentation (pre-existing docs)
    6. Getting Started (setup/run/test)
    7. For AI-Assisted Development (navigation guidance)
    """

    def __init__(self, project_root: Path):
        """
        Initialize index generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.output_dir: Optional[Path] = None

    def generate_index(
        self,
        index_data: IndexData,
        generated_date: str,
        output_dir: Optional[Path] = None
    ) -> str:
        """
        Generate complete index.md from structured data.

        Args:
            index_data: Structured index data
            generated_date: Document generation date
            output_dir: Optional directory where documentation will be written
                       (used to check which shards already exist)

        Returns:
            Complete index.md content as markdown string
        """
        # Store output_dir for shard existence checking
        self.output_dir = output_dir

        sections = []

        # Section 1: Header
        sections.append(self._generate_header(index_data, generated_date))

        # Section 2: Project Overview
        sections.append(self._generate_overview(index_data))

        # Section 3: Quick Reference
        sections.append(self._generate_quick_reference(index_data))

        # Section 4: Generated Documentation
        sections.append(self._generate_documentation_links(index_data))

        # Section 5: Existing Documentation
        sections.append(self._generate_existing_docs(index_data))

        # Section 6: Getting Started
        sections.append(self._generate_getting_started(index_data))

        # Section 7: For AI-Assisted Development
        sections.append(self._generate_ai_guidance(index_data))

        # Footer
        sections.append(self._generate_footer())

        return "\n".join(sections)

    def _check_shard_exists(self, filename: str) -> bool:
        """
        Check if a documentation shard exists in output directory.

        Args:
            filename: Name of the documentation file (e.g., 'architecture.md')

        Returns:
            True if file exists, False otherwise
        """
        if self.output_dir is None:
            return True  # Assume exists if we can't check

        file_path = self.output_dir / filename
        return file_path.exists()

    def _format_doc_link(self, filename: str, title: str, description: str) -> str:
        """
        Format a documentation link with existence marker.

        Args:
            filename: Name of the documentation file
            title: Display title for the link
            description: Description text after the link

        Returns:
            Formatted markdown link with optional "To be generated" marker
        """
        exists = self._check_shard_exists(filename)
        link = f"[{title}](./{filename})"

        if not exists:
            link += " _(To be generated)_"

        return f"- {link} - {description}"

    def _generate_header(self, data: IndexData, date: str) -> str:
        """Generate Section 1: Header with project metadata."""
        lines = []
        lines.append(f"# {data.project_name} Documentation Index")
        lines.append("")

        type_line = f"**Type:** {data.repository_type}"
        if data.is_multi_part:
            type_line += f" with {data.parts_count} parts"
        lines.append(type_line)

        lines.append(f"**Primary Language:** {data.primary_language}")
        lines.append(f"**Architecture:** {data.architecture_type}")
        lines.append(f"**Last Updated:** {date}")
        lines.append("")

        # Project Vital Signs section (if statistics are available)
        if data.file_count is not None or data.total_loc is not None or data.primary_languages:
            lines.append("## Project Vital Signs")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")

            if data.total_loc is not None:
                lines.append(f"| **Lines of Code** | {data.total_loc:,} |")
            if data.file_count is not None:
                lines.append(f"| **Total Files** | {data.file_count:,} |")
            if data.primary_languages:
                languages_str = ", ".join(data.primary_languages[:5])  # Top 5 languages
                lines.append(f"| **Top Languages** | {languages_str} |")

            lines.append("")

        return "\n".join(lines)

    def _generate_overview(self, data: IndexData) -> str:
        """Generate Section 2: Project Overview."""
        lines = []
        lines.append("## Project Overview")
        lines.append("")
        lines.append(data.project_description)
        lines.append("")

        # Multi-part structure
        if data.is_multi_part and data.project_parts:
            lines.append("## Project Structure")
            lines.append("")
            lines.append(f"This project consists of {data.parts_count} parts:")
            lines.append("")

            for part in data.project_parts:
                lines.append(f"### {part.part_name} ({part.part_id})")
                lines.append("")
                lines.append(f"- **Type:** {part.project_type}")
                lines.append(f"- **Location:** `{part.root_path}`")
                lines.append(f"- **Tech Stack:** {part.tech_stack_summary}")
                lines.append(f"- **Entry Point:** {part.entry_point}")
                lines.append("")

            if data.integration_summary:
                lines.append("## Cross-Part Integration")
                lines.append("")
                lines.append(data.integration_summary)
                lines.append("")

        return "\n".join(lines)

    def _generate_quick_reference(self, data: IndexData) -> str:
        """Generate Section 3: Quick Reference."""
        lines = []
        lines.append("## Quick Reference")
        lines.append("")

        if not data.is_multi_part:
            # Single-part quick ref
            lines.append(f"- **Tech Stack:** {data.tech_stack_summary}")
            lines.append(f"- **Entry Point:** {data.entry_point}")
            lines.append(f"- **Architecture Pattern:** {data.architecture_pattern}")
            if data.database:
                lines.append(f"- **Database:** {data.database}")
            if data.deployment_platform:
                lines.append(f"- **Deployment:** {data.deployment_platform}")
        else:
            # Multi-part quick refs
            if data.project_parts:
                for part in data.project_parts:
                    lines.append(f"### {part.part_name} Quick Ref")
                    lines.append("")
                    lines.append(f"- **Stack:** {part.tech_stack_summary}")
                    lines.append(f"- **Entry:** {part.entry_point}")
                    lines.append(f"- **Pattern:** {part.architecture_pattern}")
                    lines.append("")

        return "\n".join(lines)

    def _generate_documentation_links(self, data: IndexData) -> str:
        """Generate Section 4: Generated Documentation."""
        lines = []
        lines.append("## Generated Documentation")
        lines.append("")
        lines.append("### Core Documentation")
        lines.append("")
        lines.append(self._format_doc_link("project-overview.md", "Project Overview", "Executive summary and high-level architecture"))
        lines.append("")

        if not data.is_multi_part:
            # Single-part documentation links
            lines.append(self._format_doc_link("architecture.md", "Architecture", "Detailed technical architecture"))

            comp_desc = "Component inventory with directory structure and organization patterns"
            if data.has_ui_components:
                comp_desc += " including UI elements"
            lines.append(self._format_doc_link("component-inventory.md", "Component Inventory", comp_desc))

            lines.append(self._format_doc_link("development-guide.md", "Development Guide", "Local setup and development workflow"))

            if data.has_api_docs:
                lines.append(self._format_doc_link("api-contracts.md", "API Contracts", "API endpoints and schemas"))
            if data.has_data_models:
                lines.append(self._format_doc_link("data-models.md", "Data Models", "Database schema and models"))
        else:
            # Multi-part documentation links
            lines.append("### Part-Specific Documentation")
            lines.append("")

            if data.project_parts:
                for part in data.project_parts:
                    lines.append(f"#### {part.part_name} ({part.part_id})")
                    lines.append("")
                    lines.append(self._format_doc_link(f"architecture-{part.part_id}.md", "Architecture", f"Technical architecture for {part.part_name}"))
                    if part.has_components:
                        lines.append(self._format_doc_link(f"component-inventory-{part.part_id}.md", "Components", "Component catalog"))
                    lines.append(self._format_doc_link(f"development-guide-{part.part_id}.md", "Development Guide", "Setup and dev workflow"))
                    if part.has_api:
                        lines.append(self._format_doc_link(f"api-contracts-{part.part_id}.md", "API Contracts", "API documentation"))
                    if part.has_data:
                        lines.append(self._format_doc_link(f"data-models-{part.part_id}.md", "Data Models", "Data architecture"))
                    lines.append("")

            lines.append("### Integration")
            lines.append("")
            lines.append(self._format_doc_link("integration-architecture.md", "Integration Architecture", "How parts communicate"))
            lines.append(self._format_doc_link("project-parts.json", "Project Parts Metadata", "Machine-readable structure"))
            lines.append("")

        # Optional documentation
        lines.append("### Optional Documentation")
        lines.append("")
        if data.has_deployment_guide:
            lines.append(self._format_doc_link("deployment-guide.md", "Deployment Guide", "Deployment process and infrastructure"))
        if data.has_contribution_guide:
            lines.append(self._format_doc_link("contribution-guide.md", "Contribution Guide", "Contributing guidelines and standards"))
        lines.append("")

        return "\n".join(lines)

    def _generate_existing_docs(self, data: IndexData) -> str:
        """Generate Section 5: Existing Documentation."""
        lines = []
        lines.append("## Existing Documentation")
        lines.append("")

        if data.existing_docs and len(data.existing_docs) > 0:
            for doc in data.existing_docs:
                lines.append(f"- [{doc.title}]({doc.path}) - {doc.description}")
        else:
            lines.append("No existing documentation files were found in the project.")

        lines.append("")
        return "\n".join(lines)

    def _generate_getting_started(self, data: IndexData) -> str:
        """Generate Section 6: Getting Started."""
        lines = []
        lines.append("## Getting Started")
        lines.append("")

        if not data.is_multi_part:
            # Single-part setup
            if data.prerequisites:
                lines.append("### Prerequisites")
                lines.append("")
                lines.append(data.prerequisites)
                lines.append("")

            if data.setup_commands:
                lines.append("### Setup")
                lines.append("")
                lines.append("```bash")
                lines.append(data.setup_commands)
                lines.append("```")
                lines.append("")

            if data.run_commands:
                lines.append("### Run Locally")
                lines.append("")
                lines.append("```bash")
                lines.append(data.run_commands)
                lines.append("```")
                lines.append("")

            if data.test_commands:
                lines.append("### Run Tests")
                lines.append("")
                lines.append("```bash")
                lines.append(data.test_commands)
                lines.append("```")
                lines.append("")
        else:
            # Multi-part setup
            if data.project_parts:
                for part in data.project_parts:
                    lines.append(f"### {part.part_name} Setup")
                    lines.append("")
                    lines.append(f"**Prerequisites:** {part.prerequisites}")
                    lines.append("")
                    lines.append("**Install & Run:**")
                    lines.append("")
                    lines.append("```bash")
                    lines.append(f"cd {part.root_path}")
                    lines.append(part.setup_command)
                    lines.append(part.run_command)
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _generate_ai_guidance(self, data: IndexData) -> str:
        """Generate Section 7: For AI-Assisted Development."""
        lines = []
        lines.append("## For AI-Assisted Development")
        lines.append("")
        lines.append("This documentation was generated specifically to enable AI agents to understand and extend this codebase.")
        lines.append("")
        lines.append("### When Planning New Features:")
        lines.append("")

        # UI-only features
        lines.append("**UI-only features:**")
        if data.is_multi_part and data.ui_part_id:
            lines.append(f"→ Reference: `architecture-{data.ui_part_id}.md`, `component-inventory-{data.ui_part_id}.md`")
        else:
            lines.append("→ Reference: `architecture.md`, `component-inventory.md`")
        lines.append("")

        # API/Backend features
        lines.append("**API/Backend features:**")
        if data.is_multi_part and data.api_part_id:
            lines.append(f"→ Reference: `architecture-{data.api_part_id}.md`, `api-contracts-{data.api_part_id}.md`, `data-models-{data.api_part_id}.md`")
        else:
            ref = "→ Reference: `architecture.md`"
            if data.has_api_docs:
                ref += ", `api-contracts.md`"
            if data.has_data_models:
                ref += ", `data-models.md`"
            lines.append(ref)
        lines.append("")

        # Full-stack features
        lines.append("**Full-stack features:**")
        if data.is_multi_part:
            lines.append("→ Reference: All architecture docs + `integration-architecture.md`")
        else:
            lines.append("→ Reference: All architecture docs")
        lines.append("")

        # Deployment changes
        lines.append("**Deployment changes:**")
        if data.has_deployment_guide:
            lines.append("→ Reference: `deployment-guide.md`")
        else:
            lines.append("→ Review CI/CD configs in project")
        lines.append("")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate footer."""
        lines = []
        lines.append("---")
        lines.append("")
        lines.append("_Documentation generated using LLM-based documentation workflow_")
        return "\n".join(lines)
