"""
Component Generator for LLM-based Documentation.

Generates component inventory documentation with LLM-enhanced narrative descriptions.
Analyzes directory structure, file organization patterns, and component purposes.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..markdown_validator import sanitize_llm_output
from ..analysis.analysis_insights import (
    extract_insights_from_analysis,
    format_insights_for_prompt
)


@dataclass
class ComponentData:
    """Structured component data for documentation generation."""

    project_name: str
    project_root: str
    is_multi_part: bool
    parts_count: int = 0

    # Directory structure
    complete_source_tree: str = ""
    critical_folders: List[Dict[str, str]] = field(default_factory=list)

    # Multi-part project data
    project_parts: Optional[List[Dict[str, Any]]] = None

    # Entry points
    main_entry_point: Optional[str] = None
    additional_entry_points: Optional[List[Dict[str, str]]] = None

    # File organization
    file_type_patterns: List[Dict[str, str]] = field(default_factory=list)
    config_files: List[Dict[str, str]] = field(default_factory=list)

    # Assets
    has_assets: bool = False
    asset_locations: Optional[List[Dict[str, str]]] = None


class ComponentGenerator:
    """
    Generates component inventory documentation using structured LLM prompts.

    Capabilities:
    - Analyzes directory structure and organization patterns
    - Identifies critical folders and their purposes
    - Describes entry points and file organization
    - Documents component relationships and integration points
    """

    def __init__(self, project_root: Path):
        """
        Initialize component generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

    def format_component_prompt(
        self,
        component_data: ComponentData,
        directories_to_analyze: List[str],
        max_directories: int = 10,
        analysis_data: Optional[Path] = None
    ) -> str:
        """
        Format LLM prompt for component analysis.

        Creates a structured prompt that guides the LLM to analyze:
        - Directory purposes and contents
        - File organization patterns
        - Component relationships
        - Entry points and integration patterns

        Args:
            component_data: Structured component data
            directories_to_analyze: List of directory paths to analyze
            max_directories: Maximum number of directories to include in prompt
            analysis_data: Optional path to codebase.json for insights

        Returns:
            Formatted prompt string for LLM
        """
        prompt_parts = []

        # Header with clear instructions
        prompt_parts.append("# Task: Component Inventory Analysis (Read-Only)")
        prompt_parts.append("")
        prompt_parts.append("**IMPORTANT: You have READ-ONLY access. Do not attempt to write files.**")
        prompt_parts.append("Analyze this codebase to understand component organization, directory purposes, and file patterns.")
        prompt_parts.append("Your findings will be used to compose the final component inventory documentation.")
        prompt_parts.append("")

        # Files and directories to ignore
        prompt_parts.append("## Files and Directories to Ignore")
        prompt_parts.append("")
        prompt_parts.append("When analyzing this codebase, **ignore and do not read** the following:")
        prompt_parts.append("")
        prompt_parts.append("- `specs/` - Project specifications (not source code)")
        prompt_parts.append("- `.claude/` - Claude AI configuration")
        prompt_parts.append("- `.agents/` - Agent configuration")
        prompt_parts.append("- `AGENTS.md` - Agent documentation")
        prompt_parts.append("- `CLAUDE.md` - Claude documentation")
        prompt_parts.append("- Any paths matching `.gitignore` patterns")
        prompt_parts.append("- Standard build/dependency directories (node_modules, dist, build, etc.)")
        prompt_parts.append("")
        prompt_parts.append("Focus only on actual source code and project documentation.")
        prompt_parts.append("")

        # Project context
        prompt_parts.append("## Project Context")
        prompt_parts.append("")
        prompt_parts.append(f"- **Project Name:** {component_data.project_name}")
        prompt_parts.append(f"- **Project Root:** `{component_data.project_root}`")
        prompt_parts.append(f"- **Structure Type:** {'Multi-part' if component_data.is_multi_part else 'Single-part'}")
        if component_data.is_multi_part:
            prompt_parts.append(f"- **Parts Count:** {component_data.parts_count}")
        prompt_parts.append("")

        # Multi-part structure
        if component_data.project_parts:
            prompt_parts.append("### Project Parts")
            prompt_parts.append("")
            for part in component_data.project_parts:
                prompt_parts.append(f"**{part['name']}** (`{part['path']}`)")
                prompt_parts.append(f"  - Type: {part.get('type', 'Unknown')}")
                prompt_parts.append(f"  - Tech: {part.get('tech_stack', 'Not specified')}")
                prompt_parts.append("")

        # Source tree overview
        if component_data.complete_source_tree:
            prompt_parts.append("### Complete Directory Structure")
            prompt_parts.append("")
            prompt_parts.append("```")
            prompt_parts.append(component_data.complete_source_tree)
            prompt_parts.append("```")
            prompt_parts.append("")

        # Add codebase analysis insights if available
        if analysis_data and analysis_data.exists():
            try:
                insights = extract_insights_from_analysis(analysis_data)
                formatted_insights = format_insights_for_prompt(
                    insights,
                    generator_type='component',
                    docs_path=analysis_data
                )
                prompt_parts.append("### Codebase Analysis Insights")
                prompt_parts.append("")
                prompt_parts.append(formatted_insights)
                prompt_parts.append("")
            except Exception as e:
                # Gracefully handle any errors in insight extraction
                pass

        # Directories to analyze
        prompt_parts.append("## Directories to Analyze")
        prompt_parts.append("")
        prompt_parts.append("Please analyze these key directories:")
        prompt_parts.append("")
        for directory in directories_to_analyze[:max_directories]:
            prompt_parts.append(f"- `{directory}`")
        prompt_parts.append("")

        # Research objectives
        prompt_parts.append("## Research Findings to Provide")
        prompt_parts.append("")

        prompt_parts.append("### 1. Source Tree Overview")
        prompt_parts.append("- High-level description of how the codebase is organized (2-3 sentences)")
        prompt_parts.append("- Primary organizational pattern (by feature, by layer, by module, hybrid)")
        prompt_parts.append("- Notable characteristics of the directory structure")
        prompt_parts.append("")

        prompt_parts.append("### 2. Critical Directories")
        prompt_parts.append("")
        prompt_parts.append("For each critical directory, provide:")
        prompt_parts.append("")
        prompt_parts.append("| Directory Path | Purpose | Contents Summary | Entry Points | Integration Notes |")
        prompt_parts.append("| --- | --- | --- | --- | --- |")
        prompt_parts.append("| (Fill in) | (Why it exists) | (What it contains) | (Main files) | (How it connects) |")
        prompt_parts.append("")
        prompt_parts.append("Examples of critical directories:")
        prompt_parts.append("- Main application code directories")
        prompt_parts.append("- Configuration directories")
        prompt_parts.append("- Test directories")
        prompt_parts.append("- Build/deployment directories")
        prompt_parts.append("- Documentation directories")
        prompt_parts.append("")

        prompt_parts.append("### 3. Entry Points")
        prompt_parts.append("")
        if component_data.is_multi_part and component_data.project_parts:
            prompt_parts.append("For each project part, identify:")
            prompt_parts.append("- Main entry point file")
            prompt_parts.append("- How the application bootstraps/initializes")
            prompt_parts.append("- Additional entry points (CLI, API, tests, etc.)")
        else:
            prompt_parts.append("Identify:")
            prompt_parts.append("- Main application entry point")
            prompt_parts.append("- Additional entry points (CLI tools, API servers, etc.)")
            prompt_parts.append("- How the application starts/bootstraps")
        prompt_parts.append("")

        prompt_parts.append("### 4. File Organization Patterns")
        prompt_parts.append("")
        prompt_parts.append("Describe how files are organized:")
        prompt_parts.append("- Naming conventions (camelCase, snake_case, kebab-case)")
        prompt_parts.append("- File grouping strategies (by feature, by type, by domain)")
        prompt_parts.append("- Module/package structure")
        prompt_parts.append("- Co-location patterns (tests with code, styles with components, etc.)")
        prompt_parts.append("")

        prompt_parts.append("### 5. Key File Types")
        prompt_parts.append("")
        prompt_parts.append("Identify important file type patterns:")
        prompt_parts.append("")
        prompt_parts.append("| File Type | Pattern | Purpose | Examples |")
        prompt_parts.append("| --- | --- | --- | --- |")
        prompt_parts.append("| Source Code | `*.ext` | What these files do | Specific examples |")
        prompt_parts.append("| Tests | `*.test.*` | Testing approach | Test file examples |")
        prompt_parts.append("| Config | `*.config.*` | Configuration purpose | Config examples |")
        prompt_parts.append("")

        prompt_parts.append("### 6. Configuration Files")
        prompt_parts.append("")
        prompt_parts.append("Identify and describe key configuration files:")
        prompt_parts.append("- Build configuration (package.json, setup.py, Cargo.toml, etc.)")
        prompt_parts.append("- Runtime configuration (.env, config files)")
        prompt_parts.append("- Development tools (linters, formatters, IDE configs)")
        prompt_parts.append("- CI/CD configuration")
        prompt_parts.append("")

        prompt_parts.append("### 7. Asset Locations")
        prompt_parts.append("")
        prompt_parts.append("If applicable, identify asset directories:")
        prompt_parts.append("- Static assets (images, fonts, icons)")
        prompt_parts.append("- Styles (CSS, SCSS, style files)")
        prompt_parts.append("- Documentation files")
        prompt_parts.append("- Example/sample data")
        prompt_parts.append("")

        # Conditionally add section 8 for multi-part projects
        next_section_num = 8
        if component_data.is_multi_part and component_data.project_parts:
            prompt_parts.append(f"### {next_section_num}. Integration Points (Multi-Part Projects)")
            prompt_parts.append("")
            prompt_parts.append("Describe how different parts integrate:")
            prompt_parts.append("- Communication patterns between parts")
            prompt_parts.append("- Shared dependencies or code")
            prompt_parts.append("- Data flow between parts")
            prompt_parts.append("- Build/deployment relationships")
            prompt_parts.append("")
            next_section_num += 1

        prompt_parts.append(f"### {next_section_num}. Development Notes")
        prompt_parts.append("")
        prompt_parts.append("Provide helpful notes for developers:")
        prompt_parts.append("- Where to find specific functionality")
        prompt_parts.append("- Important directories for common tasks")
        prompt_parts.append("- Potential confusion points or gotchas")
        prompt_parts.append("- Recommendations for navigating the codebase")
        prompt_parts.append("")

        # Output format guidance
        prompt_parts.append("## Output Format")
        prompt_parts.append("")
        prompt_parts.append("Provide your research findings as structured text following the sections above.")
        prompt_parts.append("Use markdown formatting (headers, lists, tables, code references).")
        prompt_parts.append("Be specific and reference actual directories/files when making observations.")
        prompt_parts.append("Use the table formats provided where applicable.")
        prompt_parts.append("Focus on evidence-based analysis from the actual directory structure.")
        prompt_parts.append("")
        prompt_parts.append("**DO NOT write documentation files yourself.**")
        prompt_parts.append("Just return your research findings as text output.")

        return "\n".join(prompt_parts)

    def compose_component_doc(
        self,
        research_findings: str,
        component_data: ComponentData,
        generated_date: str
    ) -> str:
        """
        Compose final component inventory document from LLM research findings.

        Implements composition layer (separate from LLM research) following
        structured template format.

        Args:
            research_findings: Raw research output from LLM
            component_data: Structured component data
            generated_date: Document generation date

        Returns:
            Formatted component inventory documentation markdown
        """
        doc_parts = []

        # Header
        doc_parts.append(f"# {component_data.project_name} - Component Inventory")
        doc_parts.append("")
        doc_parts.append(f"**Date:** {generated_date}")
        doc_parts.append("")

        # Multi-part structure section
        if component_data.is_multi_part and component_data.project_parts:
            doc_parts.append("## Multi-Part Structure")
            doc_parts.append("")
            doc_parts.append(f"This project is organized into {component_data.parts_count} distinct parts:")
            doc_parts.append("")

            for part in component_data.project_parts:
                doc_parts.append(f"- **{part['name']}** (`{part['path']}`): {part.get('purpose', 'Purpose to be determined')}")
            doc_parts.append("")

        # Complete directory structure
        if component_data.complete_source_tree:
            doc_parts.append("## Complete Directory Structure")
            doc_parts.append("")
            doc_parts.append("```")
            doc_parts.append(component_data.complete_source_tree)
            doc_parts.append("```")
            doc_parts.append("")

        # LLM research findings (sanitized for markdown validity)
        doc_parts.append("---")
        doc_parts.append("")
        sanitized_findings, warnings = sanitize_llm_output(research_findings)
        if warnings:
            # Log warnings (in production, you might want to use proper logging)
            for warning in warnings:
                print(f"[WARN] Markdown validation: {warning}")
        doc_parts.append(sanitized_findings)
        doc_parts.append("")

        # Footer with references
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append("## Related Documentation")
        doc_parts.append("")
        doc_parts.append("For additional information, see:")
        doc_parts.append("")
        doc_parts.append("- `index.md` - Master documentation index")
        doc_parts.append("- `project-overview.md` - Project overview and summary")
        doc_parts.append("- `architecture.md` - Detailed architecture")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append("*Generated using LLM-based documentation workflow*")

        return "\n".join(doc_parts)

    def generate_component_doc(
        self,
        component_data: ComponentData,
        directories_to_analyze: List[str],
        llm_consultation_fn: Any,
        max_directories: int = 10,
        analysis_data: Optional[Path] = None
    ) -> tuple[bool, str]:
        """
        Generate component inventory documentation.

        Orchestrates the full workflow:
        1. Format component research prompt
        2. Consult LLM (via provided function)
        3. Compose final component inventory document

        Args:
            component_data: Structured component data
            directories_to_analyze: List of directories to analyze
            llm_consultation_fn: Function to call LLM (signature: (prompt: str) -> tuple[bool, str])
            max_directories: Maximum directories to include in prompt
            analysis_data: Optional path to codebase.json for insights

        Returns:
            Tuple of (success: bool, documentation: str)
        """
        from datetime import datetime

        # Format prompt
        prompt = self.format_component_prompt(
            component_data,
            directories_to_analyze,
            max_directories,
            analysis_data
        )

        # Consult LLM
        success, findings = llm_consultation_fn(prompt)

        if not success:
            return False, f"LLM consultation failed: {findings}"

        # Compose final document
        generated_date = datetime.now().strftime("%Y-%m-%d")
        documentation = self.compose_component_doc(findings, component_data, generated_date)

        return True, documentation
