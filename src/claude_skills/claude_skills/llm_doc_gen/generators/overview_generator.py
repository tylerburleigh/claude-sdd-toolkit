"""
Overview Generator for LLM-based Documentation.

Generates project overview documentation using LLM prompts based on codebase analysis.
Implements patterns from ai_consultation.py.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from ..analysis.analysis_insights import (
    extract_insights_from_analysis,
    format_insights_for_prompt
)


@dataclass
class ProjectData:
    """Structured project data for overview generation."""

    project_name: str
    project_type: str
    repository_type: str  # monolith, monorepo, multi-part
    primary_languages: List[str]
    tech_stack: Dict[str, Any]
    directory_structure: Union[Dict[str, Any], str]  # Dict for legacy, str for tree representation
    file_count: int
    total_loc: int
    parts: Optional[List[Dict[str, Any]]] = None  # For multi-part projects
    analysis: Optional[Dict[str, Any]] = None  # Codebase analysis from DocumentationGenerator


class OverviewGenerator:
    """
    Generates project overview documentation using structured LLM prompts.

    Based on research findings from ai_consultation.py:
    - Structured prompt sections for clarity
    - Limited file lists to manage token budget
    - Separation of research (LLM) from composition (Python)
    """

    def __init__(self, project_root: Path):
        """
        Initialize overview generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

    def format_overview_prompt(
        self,
        project_data: ProjectData,
        key_files: List[str],
        max_files: int = 10,
        analysis_data: Optional[Path] = None
    ) -> str:
        """
        Format LLM prompt for project overview generation.

        Based on ai_consultation.py pattern with structured sections and
        clear research objectives.

        Args:
            project_data: Structured project data
            key_files: List of key file paths to analyze
            max_files: Maximum number of files to include in prompt
            analysis_data: Optional path to codebase.json for insights

        Returns:
            Formatted prompt string for LLM
        """
        prompt_parts = []

        # Header with clear instructions
        prompt_parts.append("# Task: Project Overview Research (Read-Only)")
        prompt_parts.append("")
        prompt_parts.append("**IMPORTANT: You have READ-ONLY access. Do not attempt to write files.**")
        prompt_parts.append("Analyze this codebase and provide research findings for a project overview.")
        prompt_parts.append("Your findings will be used to compose the final documentation.")
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

        # Project context summary
        prompt_parts.append("## Project Context")
        prompt_parts.append("")
        prompt_parts.append(f"- **Project Name:** {project_data.project_name}")
        prompt_parts.append(f"- **Project Type:** {project_data.project_type}")
        prompt_parts.append(f"- **Repository Type:** {project_data.repository_type}")
        prompt_parts.append(f"- **Primary Languages:** {', '.join(project_data.primary_languages)}")
        prompt_parts.append(f"- **File Count:** {project_data.file_count}")
        prompt_parts.append(f"- **Total LOC:** {project_data.total_loc:,}")
        prompt_parts.append("")

        # Multi-part project structure
        if project_data.parts:
            prompt_parts.append("### Project Structure")
            prompt_parts.append("")
            prompt_parts.append(f"This is a {project_data.repository_type} with {len(project_data.parts)} parts:")
            prompt_parts.append("")
            for part in project_data.parts:
                prompt_parts.append(f"**{part['name']}** (`{part['path']}`)")
                prompt_parts.append(f"  - Type: {part['type']}")
                prompt_parts.append(f"  - Tech: {part['tech_stack']}")
                prompt_parts.append("")

        # Technology stack summary
        prompt_parts.append("### Technology Stack")
        prompt_parts.append("")
        for category, tech in project_data.tech_stack.items():
            prompt_parts.append(f"- **{category}:** {tech}")
        prompt_parts.append("")

        # Codebase Structure Statistics (from analysis)
        if project_data.analysis:
            prompt_parts.append("## Codebase Structure Statistics")
            prompt_parts.append("")
            prompt_parts.append("The following statistics provide ground truth about the system's structure:")
            prompt_parts.append("")

            # Module/file statistics
            modules = project_data.analysis.get("modules", [])
            if modules:
                prompt_parts.append(f"### Top Modules by Complexity ({len(modules)} total)")
                prompt_parts.append("")
                # Sort by complexity and show top 10
                sorted_modules = sorted(
                    modules,
                    key=lambda m: m.get("complexity", {}).get("total", 0),
                    reverse=True
                )[:10]
                for module in sorted_modules:
                    name = module.get("name", "Unknown")
                    complexity = module.get("complexity", {}).get("total", 0)
                    func_count = len(module.get("functions", []))
                    class_count = len(module.get("classes", []))
                    prompt_parts.append(f"- **{name}**: Complexity {complexity}, {func_count} functions, {class_count} classes")
                prompt_parts.append("")

            # Language statistics
            languages = project_data.analysis.get("statistics", {}).get("by_language", {})
            if languages:
                prompt_parts.append("### Language Breakdown")
                prompt_parts.append("")
                for lang, stats in sorted(languages.items(), key=lambda x: x[1].get("lines", 0), reverse=True)[:5]:
                    lines = stats.get("lines", 0)
                    files = stats.get("files", 0)
                    prompt_parts.append(f"- **{lang}**: {lines:,} lines across {files} files")
                prompt_parts.append("")

        # Add codebase analysis insights if available
        if analysis_data and analysis_data.exists():
            try:
                insights = extract_insights_from_analysis(analysis_data)
                formatted_insights = format_insights_for_prompt(
                    insights,
                    generator_type='overview',
                    docs_path=analysis_data
                )
                prompt_parts.append("### Codebase Analysis Insights")
                prompt_parts.append("")
                prompt_parts.append(formatted_insights)
                prompt_parts.append("")
            except Exception as e:
                # Gracefully handle any errors in insight extraction
                pass

        # Key files to analyze (limited to manage token budget)
        prompt_parts.append("## Key Files to Analyze")
        prompt_parts.append("")
        prompt_parts.append("Please read and analyze these files:")
        prompt_parts.append("")
        for file in key_files[:max_files]:
            prompt_parts.append(f"- `{file}`")
        prompt_parts.append("")

        # Research objectives - structured sections
        prompt_parts.append("## Research Findings to Provide")
        prompt_parts.append("")

        prompt_parts.append("### 1. Executive Summary (2-3 paragraphs)")
        prompt_parts.append("- What does this project do? (Purpose and functionality)")
        prompt_parts.append("- Who is it for? (Target users/audience)")
        prompt_parts.append("- What problem does it solve?")
        prompt_parts.append("- What makes it unique or notable?")
        prompt_parts.append("")

        prompt_parts.append("### 2. Key Features (3-5 main features)")
        prompt_parts.append("- List the most important features/capabilities")
        prompt_parts.append("- Brief description of each feature")
        prompt_parts.append("- Why each feature matters to users")
        prompt_parts.append("")

        prompt_parts.append("### 3. Architecture Highlights")
        prompt_parts.append("- High-level architecture pattern (e.g., layered, microservices, client-server)")
        prompt_parts.append("- Key architectural decisions you can identify")
        prompt_parts.append("- Notable design patterns in use")
        prompt_parts.append("")

        if project_data.parts:
            prompt_parts.append("### 4. How Parts Integrate (Multi-Part Projects)")
            prompt_parts.append("- How do the different parts communicate?")
            prompt_parts.append("- What is the data flow between parts?")
            prompt_parts.append("- What is the deployment relationship?")
            prompt_parts.append("")

        prompt_parts.append("### 5. Development Overview")
        prompt_parts.append("- Prerequisites needed to work on this project")
        prompt_parts.append("- Key setup/installation steps")
        prompt_parts.append("- Primary development commands (install, dev, build, test)")
        prompt_parts.append("")

        # Output format guidance
        prompt_parts.append("## Output Format")
        prompt_parts.append("")
        prompt_parts.append("Provide your research findings as structured text with clear section headers.")
        prompt_parts.append("Use markdown formatting for readability (headers, lists, code references).")
        prompt_parts.append("Be specific and reference actual code/files when making observations.")
        prompt_parts.append("Keep the executive summary concise (2-3 paragraphs max).")
        prompt_parts.append("")
        prompt_parts.append("**DO NOT write documentation files yourself.**")
        prompt_parts.append("Just return your research findings as text output.")

        return "\n".join(prompt_parts)

    def compose_overview_doc(
        self,
        research_findings: str,
        project_data: ProjectData,
        generated_date: str
    ) -> str:
        """
        Compose final project overview document from LLM research findings.

        Implements composition layer (separate from LLM research) as seen in
        ai_consultation.py compose_architecture_doc().

        Args:
            research_findings: Raw research output from LLM
            project_data: Structured project data
            generated_date: Document generation date

        Returns:
            Formatted project overview markdown
        """
        doc_parts = []

        # Header
        doc_parts.append(f"# {project_data.project_name} - Project Overview")
        doc_parts.append("")
        doc_parts.append(f"**Date:** {generated_date}")
        doc_parts.append(f"**Type:** {project_data.project_type}")
        doc_parts.append(f"**Architecture:** {project_data.repository_type}")
        doc_parts.append("")

        # Project classification
        doc_parts.append("## Project Classification")
        doc_parts.append("")
        doc_parts.append(f"- **Repository Type:** {project_data.repository_type}")
        doc_parts.append(f"- **Project Type:** {project_data.project_type}")
        doc_parts.append(f"- **Primary Language(s):** {', '.join(project_data.primary_languages)}")
        doc_parts.append("")

        # Multi-part structure section
        if project_data.parts:
            doc_parts.append("## Multi-Part Structure")
            doc_parts.append("")
            doc_parts.append(f"This project consists of {len(project_data.parts)} distinct parts:")
            doc_parts.append("")

            for part in project_data.parts:
                doc_parts.append(f"### {part['name']}")
                doc_parts.append("")
                doc_parts.append(f"- **Type:** {part['type']}")
                doc_parts.append(f"- **Location:** `{part['path']}`")
                doc_parts.append(f"- **Tech Stack:** {part['tech_stack']}")
                doc_parts.append("")

        # Technology stack summary
        doc_parts.append("## Technology Stack Summary")
        doc_parts.append("")
        for category, tech in project_data.tech_stack.items():
            doc_parts.append(f"- **{category}:** {tech}")
        doc_parts.append("")

        # LLM research findings
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append(research_findings)
        doc_parts.append("")

        # Footer
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append("## Documentation Map")
        doc_parts.append("")
        doc_parts.append("For detailed information, see:")
        doc_parts.append("")
        doc_parts.append("- `index.md` - Master documentation index")
        doc_parts.append("- `architecture.md` - Detailed architecture")
        doc_parts.append("- `development-guide.md` - Development workflow")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append("*Generated using LLM-based documentation workflow*")

        return "\n".join(doc_parts)

    def generate_overview(
        self,
        project_data: ProjectData,
        key_files: List[str],
        llm_consultation_fn: Any,
        max_files: int = 10,
        analysis_data: Optional[Path] = None
    ) -> tuple[bool, str]:
        """
        Generate project overview documentation.

        Orchestrates the full workflow:
        1. Format research prompt
        2. Consult LLM (via provided function)
        3. Compose final document

        Args:
            project_data: Structured project data
            key_files: List of key files to analyze
            llm_consultation_fn: Function to call LLM (signature: (prompt: str) -> tuple[bool, str])
            max_files: Maximum files to include in prompt
            analysis_data: Optional path to codebase.json for insights

        Returns:
            Tuple of (success: bool, documentation: str)
        """
        from datetime import datetime

        # Format prompt
        prompt = self.format_overview_prompt(project_data, key_files, max_files, analysis_data)

        # Consult LLM
        success, findings = llm_consultation_fn(prompt)

        if not success:
            return False, f"LLM consultation failed: {findings}"

        # Compose final document
        generated_date = datetime.now().strftime("%Y-%m-%d")
        documentation = self.compose_overview_doc(findings, project_data, generated_date)

        return True, documentation
