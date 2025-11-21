"""
Architecture Generator for LLM-based Documentation.

Generates architecture documentation using LLM prompts based on codebase analysis.
Implements patterns from ai_consultation.py.
Identifies architecture patterns, design decisions, and architecture types.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..markdown_validator import sanitize_llm_output
from ..analysis.analysis_insights import (
    extract_insights_from_analysis,
    format_insights_for_prompt
)


@dataclass
class ArchitectureData:
    """Structured architecture data for documentation generation."""

    project_name: str
    project_type: str
    primary_languages: List[str]
    tech_stack: Dict[str, Any]
    file_count: int
    total_loc: int
    directory_structure: Dict[str, Any]
    detected_patterns: Optional[List[str]] = None  # e.g., ['realtime_collaboration', 'saas_platform']
    quality_attributes: Optional[List[str]] = None  # e.g., ['high_availability', 'scalability']


class ArchitectureGenerator:
    """
    Generates architecture documentation using structured LLM prompts.

    Capabilities:
    - Identifies requirement patterns (e.g., realtime collaboration, ecommerce, SaaS)
    - Detects quality attributes (e.g., high availability, performance, security)
    - Maps architecture decisions to patterns
    - Structured prompts for clarity and token efficiency
    """

    def __init__(self, project_root: Path):
        """
        Initialize architecture generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

    def format_architecture_prompt(
        self,
        arch_data: ArchitectureData,
        key_files: List[str],
        max_files: int = 15,
        analysis_data: Optional[Path] = None
    ) -> str:
        """
        Format LLM prompt for architecture analysis.

        Creates a structured prompt that guides the LLM to identify:
        - Architecture patterns (layered, microservices, event-driven, etc.)
        - Design decisions and their rationale
        - Technology choices and integration points
        - Implementation patterns and consistency rules

        Args:
            arch_data: Structured architecture data
            key_files: List of key file paths to analyze
            max_files: Maximum number of files to include in prompt
            analysis_data: Optional path to codebase.json for codebase insights

        Returns:
            Formatted prompt string for LLM
        """
        prompt_parts = []

        # Header with clear instructions
        prompt_parts.append("# Task: Architecture Analysis Research (Read-Only)")
        prompt_parts.append("")
        prompt_parts.append("**IMPORTANT: You have READ-ONLY access. Do not attempt to write files.**")
        prompt_parts.append("Analyze this codebase to identify architecture patterns, design decisions, and implementation patterns.")
        prompt_parts.append("Your findings will be used to compose the final architecture documentation.")
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
        prompt_parts.append(f"- **Project Name:** {arch_data.project_name}")
        prompt_parts.append(f"- **Project Type:** {arch_data.project_type}")
        prompt_parts.append(f"- **Primary Languages:** {', '.join(arch_data.primary_languages)}")
        prompt_parts.append(f"- **File Count:** {arch_data.file_count}")
        prompt_parts.append(f"- **Total LOC:** {arch_data.total_loc:,}")
        prompt_parts.append("")

        # Technology stack
        prompt_parts.append("### Technology Stack")
        prompt_parts.append("")
        for category, tech in arch_data.tech_stack.items():
            prompt_parts.append(f"- **{category}:** {tech}")
        prompt_parts.append("")

        # Pre-detected patterns (if any)
        if arch_data.detected_patterns:
            prompt_parts.append("### Pre-Detected Patterns")
            prompt_parts.append("")
            prompt_parts.append("Based on static analysis, these requirement patterns were detected:")
            prompt_parts.append("")
            for pattern in arch_data.detected_patterns:
                prompt_parts.append(f"- `{pattern}`")
            prompt_parts.append("")
            prompt_parts.append("Please validate and expand on these patterns in your analysis.")
            prompt_parts.append("")

        if arch_data.quality_attributes:
            prompt_parts.append("### Pre-Detected Quality Attributes")
            prompt_parts.append("")
            prompt_parts.append("Based on static analysis, these quality attributes were detected:")
            prompt_parts.append("")
            for attr in arch_data.quality_attributes:
                prompt_parts.append(f"- `{attr}`")
            prompt_parts.append("")

        # Add codebase analysis insights if available
        if analysis_data and analysis_data.exists():
            try:
                insights = extract_insights_from_analysis(analysis_data)
                formatted_insights = format_insights_for_prompt(
                    insights,
                    generator_type='architecture',
                    docs_path=analysis_data
                )
                prompt_parts.append("### Codebase Analysis Insights")
                prompt_parts.append("")
                prompt_parts.append(formatted_insights)
                prompt_parts.append("")
            except Exception as e:
                # Gracefully handle any errors in insight extraction
                pass

        # Key files to analyze
        prompt_parts.append("## Key Files to Analyze")
        prompt_parts.append("")
        prompt_parts.append("Please read and analyze these files to identify architecture patterns:")
        prompt_parts.append("")
        for file in key_files[:max_files]:
            prompt_parts.append(f"- `{file}`")
        prompt_parts.append("")

        # Research objectives - structured sections
        prompt_parts.append("## Research Findings to Provide")
        prompt_parts.append("")

        prompt_parts.append("### 1. Executive Summary")
        prompt_parts.append("- High-level architecture overview (2-3 sentences)")
        prompt_parts.append("- Primary architecture pattern (e.g., layered, microservices, event-driven, client-server)")
        prompt_parts.append("- Key architectural characteristics")
        prompt_parts.append("")

        prompt_parts.append("### 2. Architecture Pattern Identification")
        prompt_parts.append("")
        prompt_parts.append("Identify the dominant architecture pattern(s) from:")
        prompt_parts.append("- **Layered Architecture:** Organized in horizontal layers (presentation, business, data)")
        prompt_parts.append("- **Microservices:** Independent services with separate deployment")
        prompt_parts.append("- **Event-Driven:** Asynchronous event processing and pub/sub")
        prompt_parts.append("- **Client-Server:** Clear separation between client and server components")
        prompt_parts.append("- **Plugin Architecture:** Core system with extensible plugins")
        prompt_parts.append("- **Monolith:** Single unified codebase and deployment")
        prompt_parts.append("- **Other:** Describe if different pattern")
        prompt_parts.append("")
        prompt_parts.append("For each identified pattern, explain:")
        prompt_parts.append("- Evidence from the codebase (specific files/directories)")
        prompt_parts.append("- How the pattern is implemented")
        prompt_parts.append("- Benefits this pattern provides for this project")
        prompt_parts.append("")

        prompt_parts.append("### 3. Key Architectural Decisions")
        prompt_parts.append("")
        prompt_parts.append("Identify major architectural decisions and their rationale:")
        prompt_parts.append("")
        prompt_parts.append("| Decision Category | Choice Made | Rationale/Evidence |")
        prompt_parts.append("| --- | --- | --- |")
        prompt_parts.append("| Database Architecture | ? | Based on code analysis |")
        prompt_parts.append("| API Pattern | ? | Based on code analysis |")
        prompt_parts.append("| State Management | ? | Based on code analysis |")
        prompt_parts.append("| Authentication/Authorization | ? | Based on code analysis |")
        prompt_parts.append("| Deployment Model | ? | Based on code analysis |")
        prompt_parts.append("")
        prompt_parts.append("Add additional decision categories as you identify them.")
        prompt_parts.append("")

        prompt_parts.append("### 4. Project Structure Analysis")
        prompt_parts.append("")
        prompt_parts.append("Describe the directory structure and organization:")
        prompt_parts.append("- How is the code organized? (by feature, by layer, by module?)")
        prompt_parts.append("- What are the main components/modules?")
        prompt_parts.append("- How do components relate to each other?")
        prompt_parts.append("- Identify any nested sub-projects or workspaces")
        prompt_parts.append("")

        prompt_parts.append("### 5. Technology Integration Points")
        prompt_parts.append("")
        prompt_parts.append("Identify how different technologies integrate:")
        prompt_parts.append("- External APIs and services used")
        prompt_parts.append("- Database connections and ORM/query patterns")
        prompt_parts.append("- Frontend-backend communication")
        prompt_parts.append("- Third-party libraries and frameworks")
        prompt_parts.append("- Authentication/authorization integration")
        prompt_parts.append("")

        prompt_parts.append("### 6. Implementation Patterns")
        prompt_parts.append("")
        prompt_parts.append("Identify consistent patterns used across the codebase:")
        prompt_parts.append("")
        prompt_parts.append("**Naming Conventions:**")
        prompt_parts.append("- How are files/classes/functions named?")
        prompt_parts.append("- Any consistent prefixes/suffixes?")
        prompt_parts.append("")
        prompt_parts.append("**Code Organization:**")
        prompt_parts.append("- How are related files grouped?")
        prompt_parts.append("- Module/package structure patterns")
        prompt_parts.append("")
        prompt_parts.append("**Error Handling:**")
        prompt_parts.append("- How are errors handled consistently?")
        prompt_parts.append("- Custom error types or standard approaches?")
        prompt_parts.append("")
        prompt_parts.append("**Logging/Monitoring:**")
        prompt_parts.append("- What logging approach is used?")
        prompt_parts.append("- Any monitoring or observability patterns?")
        prompt_parts.append("")

        prompt_parts.append("### 7. Data Architecture")
        prompt_parts.append("")
        prompt_parts.append("Analyze data handling:")
        prompt_parts.append("- Data models and their relationships")
        prompt_parts.append("- Data flow through the system")
        prompt_parts.append("- Persistence strategies")
        prompt_parts.append("- Caching approaches (if any)")
        prompt_parts.append("")

        prompt_parts.append("### 8. Security Architecture")
        prompt_parts.append("")
        prompt_parts.append("Identify security patterns:")
        prompt_parts.append("- Authentication mechanisms")
        prompt_parts.append("- Authorization/access control")
        prompt_parts.append("- Data protection (encryption, validation)")
        prompt_parts.append("- API security (rate limiting, CORS, etc.)")
        prompt_parts.append("")

        prompt_parts.append("### 9. Performance Considerations")
        prompt_parts.append("")
        prompt_parts.append("Identify performance strategies:")
        prompt_parts.append("- Caching layers")
        prompt_parts.append("- Async/parallel processing")
        prompt_parts.append("- Database query optimization")
        prompt_parts.append("- Resource management")
        prompt_parts.append("")

        prompt_parts.append("### 10. Novel or Unique Design Patterns")
        prompt_parts.append("")
        prompt_parts.append("Identify any unique or noteworthy design patterns:")
        prompt_parts.append("- Custom patterns specific to this project")
        prompt_parts.append("- Creative solutions to specific problems")
        prompt_parts.append("- Innovative architecture choices")
        prompt_parts.append("")

        # Output format guidance
        prompt_parts.append("## Output Format")
        prompt_parts.append("")
        prompt_parts.append("Provide your research findings as structured text following the sections above.")
        prompt_parts.append("Use markdown formatting (headers, lists, tables, code references).")
        prompt_parts.append("Be specific and reference actual files/code when making observations.")
        prompt_parts.append("Use the decision table format where applicable.")
        prompt_parts.append("Focus on evidence-based analysis from the actual codebase.")
        prompt_parts.append("")
        prompt_parts.append("**DO NOT write documentation files yourself.**")
        prompt_parts.append("Just return your research findings as text output.")

        return "\n".join(prompt_parts)

    def compose_architecture_doc(
        self,
        research_findings: str,
        arch_data: ArchitectureData,
        generated_date: str
    ) -> str:
        """
        Compose final architecture document from LLM research findings.

        Implements composition layer (separate from LLM research) following
        structured template format.

        Args:
            research_findings: Raw research output from LLM
            arch_data: Structured architecture data
            generated_date: Document generation date

        Returns:
            Formatted architecture documentation markdown
        """
        doc_parts = []

        # Header
        doc_parts.append(f"# {arch_data.project_name} - Architecture Documentation")
        doc_parts.append("")
        doc_parts.append(f"**Date:** {generated_date}")
        doc_parts.append(f"**Project Type:** {arch_data.project_type}")
        doc_parts.append(f"**Primary Language(s):** {', '.join(arch_data.primary_languages)}")
        doc_parts.append("")

        # Technology Stack Summary
        doc_parts.append("## Technology Stack Details")
        doc_parts.append("")
        doc_parts.append("### Core Technologies")
        doc_parts.append("")
        for category, tech in arch_data.tech_stack.items():
            doc_parts.append(f"- **{category}:** {tech}")
        doc_parts.append("")

        # Pre-detected patterns section (if any)
        if arch_data.detected_patterns or arch_data.quality_attributes:
            doc_parts.append("## Detected Patterns and Attributes")
            doc_parts.append("")

            if arch_data.detected_patterns:
                doc_parts.append("### Requirement Patterns")
                doc_parts.append("")
                for pattern in arch_data.detected_patterns:
                    doc_parts.append(f"- `{pattern}`")
                doc_parts.append("")

            if arch_data.quality_attributes:
                doc_parts.append("### Quality Attributes")
                doc_parts.append("")
                for attr in arch_data.quality_attributes:
                    doc_parts.append(f"- `{attr}`")
                doc_parts.append("")

        # LLM research findings (sanitized for markdown validity)
        doc_parts.append("---")
        doc_parts.append("")
        sanitized_findings, warnings = sanitize_llm_output(research_findings)
        if warnings:
            # Log warnings (in production, you might want to use proper logging)
            for warning in warnings:
                print(f"[WARN] Markdown validation: {warning}")

            # Check for truncation warnings specifically
            truncation_warnings = [w for w in warnings if "Section header with no content" in w or "truncation" in w.lower()]
            if truncation_warnings:
                print(f"\n[ERROR] LLM response appears truncated. This will result in incomplete documentation.")
                print("Possible solutions:")
                print("  - Reduce prompt complexity or split into smaller sections")
                print("  - Increase model output token limits")
                print("  - Use a model with larger context window")
                print("  - Try regenerating with a different AI tool\n")
                # Continue anyway but flag the issue
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
        doc_parts.append("- `development-guide.md` - Development workflow and setup")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")
        doc_parts.append("*Generated using LLM-based documentation workflow*")

        return "\n".join(doc_parts)

    def generate_architecture_doc(
        self,
        arch_data: ArchitectureData,
        key_files: List[str],
        llm_consultation_fn: Any,
        max_files: int = 15,
        analysis_data: Optional[Path] = None
    ) -> tuple[bool, str]:
        """
        Generate architecture documentation.

        Orchestrates the full workflow:
        1. Format architecture research prompt
        2. Consult LLM (via provided function)
        3. Compose final architecture document

        Args:
            arch_data: Structured architecture data
            key_files: List of key files to analyze
            llm_consultation_fn: Function to call LLM (signature: (prompt: str) -> tuple[bool, str])
            max_files: Maximum files to include in prompt
            analysis_data: Optional path to codebase.json for codebase insights

        Returns:
            Tuple of (success: bool, documentation: str)
        """
        from datetime import datetime

        # Format prompt
        prompt = self.format_architecture_prompt(arch_data, key_files, max_files, analysis_data)

        # Consult LLM
        success, findings = llm_consultation_fn(prompt)

        if not success:
            return False, f"LLM consultation failed: {findings}"

        # Compose final document
        generated_date = datetime.now().strftime("%Y-%m-%d")
        documentation = self.compose_architecture_doc(findings, arch_data, generated_date)

        return True, documentation

    def generate_architecture_doc_multi_model(
        self,
        arch_data: ArchitectureData,
        key_files: List[str],
        providers: Optional[List[str]] = None,
        max_files: int = 15,
        timeout: int = 120,
        verbose: bool = False
    ) -> tuple[bool, str]:
        """
        Generate architecture documentation using multiple AI models for richer insights.

        Consults multiple models in parallel, synthesizes their findings, and produces
        a comprehensive architecture document enriched with diverse perspectives.

        Args:
            arch_data: Structured architecture data
            key_files: List of key files to analyze
            providers: List of AI providers to consult (auto-selected if None)
            max_files: Maximum files to include in prompt
            timeout: Timeout in seconds per provider
            verbose: Enable verbose output

        Returns:
            Tuple of (success: bool, documentation: str)
        """
        from datetime import datetime

        # Import multi-agent consultation
        try:
            from ..ai_consultation import consult_multi_agent
        except ImportError:
            return False, "Multi-agent consultation not available. Install required dependencies."

        # Format prompt
        prompt = self.format_architecture_prompt(arch_data, key_files, max_files)

        # Consult multiple models
        results = consult_multi_agent(
            prompt=prompt,
            providers=providers,
            timeout=timeout,
            verbose=verbose
        )

        # Check if any consultation succeeded
        successful_results = {
            provider: result
            for provider, result in results.items()
            if result.success
        }

        if not successful_results:
            errors = [f"{p}: {r.error}" for p, r in results.items()]
            return False, f"All model consultations failed:\n" + "\n".join(errors)

        # Synthesize findings from multiple models
        synthesized_findings = self._synthesize_multi_model_findings(
            successful_results,
            arch_data
        )

        # Compose final document
        generated_date = datetime.now().strftime("%Y-%m-%d")
        documentation = self.compose_architecture_doc(
            synthesized_findings,
            arch_data,
            generated_date
        )

        return True, documentation

    def _synthesize_multi_model_findings(
        self,
        results: Dict[str, Any],
        arch_data: ArchitectureData
    ) -> str:
        """
        Synthesize findings from multiple AI models into a cohesive analysis.

        Combines insights from different models, highlighting consensus and
        unique perspectives.

        Args:
            results: Dictionary mapping provider names to ConsultationResults
            arch_data: Architecture data for context

        Returns:
            Synthesized findings as markdown text
        """
        synthesis_parts = []

        # Header
        synthesis_parts.append("## Multi-Model Architecture Analysis")
        synthesis_parts.append("")
        synthesis_parts.append(f"This analysis synthesizes insights from {len(results)} AI models:")
        synthesis_parts.append("")
        for provider in results.keys():
            synthesis_parts.append(f"- {provider}")
        synthesis_parts.append("")
        synthesis_parts.append("---")
        synthesis_parts.append("")

        # Individual model findings
        for provider, result in results.items():
            synthesis_parts.append(f"### Findings from {provider}")
            synthesis_parts.append("")
            synthesis_parts.append(result.output)
            synthesis_parts.append("")
            synthesis_parts.append("---")
            synthesis_parts.append("")

        # Synthesis summary
        synthesis_parts.append("## Synthesis Summary")
        synthesis_parts.append("")
        synthesis_parts.append("### Consensus Patterns")
        synthesis_parts.append("")
        synthesis_parts.append("Patterns identified by multiple models:")
        synthesis_parts.append("")
        synthesis_parts.append("*(Analyze the findings above to identify common themes)*")
        synthesis_parts.append("")

        synthesis_parts.append("### Unique Insights")
        synthesis_parts.append("")
        synthesis_parts.append("Perspectives unique to specific models:")
        synthesis_parts.append("")
        synthesis_parts.append("*(Highlight insights mentioned by only one model)*")
        synthesis_parts.append("")

        synthesis_parts.append("### Recommended Next Steps")
        synthesis_parts.append("")
        synthesis_parts.append("Based on the multi-model analysis:")
        synthesis_parts.append("")
        synthesis_parts.append("1. Review consensus patterns for architectural foundation")
        synthesis_parts.append("2. Investigate unique insights for potential blind spots")
        synthesis_parts.append("3. Validate findings against actual codebase")
        synthesis_parts.append("")

        return "\n".join(synthesis_parts)
