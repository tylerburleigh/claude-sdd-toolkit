"""
Review report parsing for apply-review workflow.

Extracts structured issue data from sdd-plan-review markdown or JSON reports.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


def parse_review_report(report_path: str) -> Dict[str, Any]:
    """
    Parse a review report file and extract issues by severity.

    Supports both markdown (from sdd-plan-review) and JSON formats.
    Extracts issues grouped by severity: critical, high, medium, low.

    Args:
        report_path: Path to the review report file (.md or .json)

    Returns:
        Dict with parsed issues:
        {
            "success": True|False,
            "format": "markdown"|"json",
            "issues": {
                "critical": [
                    {
                        "title": "Issue title",
                        "description": "Full description",
                        "flagged_by": ["model1", "model2"],
                        "impact": "Impact description",
                        "fix": "Recommended fix"
                    },
                    ...
                ],
                "high": [...],
                "medium": [...],
                "low": [...]
            },
            "metadata": {
                "spec_id": "...",
                "spec_title": "...",
                "overall_score": X.X,
                "recommendation": "APPROVE|REVISE|REJECT",
                "consensus_level": "...",
                "models_consulted": [...]
            },
            "error": "Error message" (only if success=False)
        }

    Raises:
        FileNotFoundError: If report file doesn't exist
    """
    report_file = Path(report_path)
    if not report_file.exists():
        raise FileNotFoundError(f"Review report not found: {report_path}")

    # Determine format by extension
    if report_file.suffix.lower() == '.json':
        return _parse_json_report(report_file)
    elif report_file.suffix.lower() in ['.md', '.markdown', '.txt']:
        return _parse_markdown_report(report_file)
    else:
        return {
            "success": False,
            "error": f"Unsupported file format: {report_file.suffix}. Expected .md, .markdown, .txt, or .json"
        }


def _parse_json_report(report_file: Path) -> Dict[str, Any]:
    """
    Parse JSON format review report.

    JSON reports are expected to have the structure:
    {
        "consensus": {
            "overall_score": X.X,
            "recommendation": "...",
            "consensus_level": "...",
            "synthesis_text": "..."
        },
        "metadata": {...}
    }
    """
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }

    # Extract metadata
    consensus = data.get("consensus", {})
    metadata_section = data.get("metadata", {})

    metadata = {
        "spec_id": metadata_section.get("spec_id", ""),
        "spec_title": metadata_section.get("spec_title", ""),
        "overall_score": consensus.get("overall_score", 0.0),
        "recommendation": consensus.get("recommendation", ""),
        "consensus_level": consensus.get("consensus_level", ""),
        "models_consulted": consensus.get("models", [])
    }

    # Parse synthesis text as markdown to extract issues
    synthesis_text = consensus.get("synthesis_text", "")
    if synthesis_text:
        issues = _extract_issues_from_markdown(synthesis_text)
    else:
        issues = {"critical": [], "high": [], "medium": [], "low": []}

    return {
        "success": True,
        "format": "json",
        "issues": issues,
        "metadata": metadata
    }


def _parse_markdown_report(report_file: Path) -> Dict[str, Any]:
    """
    Parse markdown format review report.

    Extracts issues from sections:
    - ### Critical Issues (Must Fix)
    - ### High Priority Issues
    - ### Medium/Low Priority
    """
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "File encoding error. Expected UTF-8."
        }

    # Extract metadata from header
    metadata = _extract_metadata_from_markdown(content)

    # Extract issues by severity
    issues = _extract_issues_from_markdown(content)

    return {
        "success": True,
        "format": "markdown",
        "issues": issues,
        "metadata": metadata
    }


def _extract_metadata_from_markdown(content: str) -> Dict[str, Any]:
    """Extract metadata fields from markdown report header."""
    metadata = {
        "spec_id": "",
        "spec_title": "",
        "overall_score": 0.0,
        "recommendation": "",
        "consensus_level": "",
        "models_consulted": []
    }

    # Extract spec ID and title
    # Format: **Spec**: Title (`spec-id`)
    spec_match = re.search(r'\*\*Spec\*\*:\s*(.+?)\s*\(`([^`]+)`\)', content)
    if spec_match:
        metadata["spec_title"] = spec_match.group(1).strip()
        metadata["spec_id"] = spec_match.group(2).strip()

    # Extract consensus score
    # Format: - **Consensus Score**: X.X/10
    score_match = re.search(r'\*\*Consensus Score\*\*:\s*(\d+\.?\d*)/10', content)
    if score_match:
        metadata["overall_score"] = float(score_match.group(1))

    # Extract recommendation
    # Format: - **Final Recommendation**: APPROVE/REVISE/REJECT
    rec_match = re.search(r'\*\*Final Recommendation\*\*:\s*(APPROVE|REVISE|REJECT)', content, re.IGNORECASE)
    if rec_match:
        metadata["recommendation"] = rec_match.group(1).upper()

    # Extract consensus level
    # Format: - **Consensus Level**: Strong/Moderate/Weak/Conflicted
    consensus_match = re.search(r'\*\*Consensus Level\*\*:\s*(\w+)', content)
    if consensus_match:
        metadata["consensus_level"] = consensus_match.group(1)

    # Extract models consulted
    # Format: **Models Consulted**: 3 (model1, model2, model3)
    models_match = re.search(r'\*\*Models Consulted\*\*:\s*\d+\s*\(([^)]+)\)', content)
    if models_match:
        models_str = models_match.group(1)
        metadata["models_consulted"] = [m.strip() for m in models_str.split(',')]

    return metadata


def _extract_issues_from_markdown(content: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract issues by severity from markdown content.

    Returns dict with keys: critical, high, medium, low
    """
    issues = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    # Parse Critical Issues section
    critical_section = _extract_section(content, r'###\s*Critical Issues\s*\(Must Fix\)')
    if critical_section:
        issues["critical"] = _parse_issue_list(critical_section, "critical")

    # Parse High Priority Issues section
    high_section = _extract_section(content, r'###\s*High Priority Issues')
    if high_section:
        issues["high"] = _parse_issue_list(high_section, "high")

    # Parse Medium/Low Priority section
    medium_section = _extract_section(content, r'###\s*Medium/Low Priority')
    if medium_section:
        # Split between medium and low based on keywords or treat all as medium
        parsed_issues = _parse_issue_list(medium_section, "medium")
        issues["medium"] = parsed_issues

    return issues


def _extract_section(content: str, header_pattern: str) -> Optional[str]:
    """
    Extract content between a header and the next header of equal or higher level.

    Args:
        content: Full markdown content
        header_pattern: Regex pattern for the section header

    Returns:
        Section content (excluding header) or None if not found
    """
    # Find section start
    match = re.search(header_pattern, content, re.IGNORECASE)
    if not match:
        return None

    start = match.end()

    # Find next header of equal or higher level (### or ##)
    # This marks the end of this section
    next_header = re.search(r'\n#{1,3}\s+', content[start:])
    if next_header:
        end = start + next_header.start()
        return content[start:end].strip()
    else:
        # No next section, take rest of document
        return content[start:].strip()


def _parse_issue_list(section_content: str, severity: str) -> List[Dict[str, Any]]:
    """
    Parse a list of issues from a section.

    Expected format:
    - Issue title - flagged by: [model names]
      - Impact: ...
      - Recommended fix: ...
      - Details: ...

    Or simpler format:
    - Issue title - flagged by: [model names]

    Args:
        section_content: Content of the issues section
        severity: Severity level (for metadata)

    Returns:
        List of issue dicts
    """
    issues = []

    # Split by top-level bullets (lines starting with "- " or "* ")
    # Use regex to find issue blocks
    issue_pattern = r'^[-*]\s+(.+?)(?=^[-*]\s+|\Z)'
    issue_blocks = re.findall(issue_pattern, section_content, re.MULTILINE | re.DOTALL)

    for block in issue_blocks:
        issue = _parse_single_issue(block.strip(), severity)
        if issue:
            issues.append(issue)

    return issues


def _parse_single_issue(issue_text: str, severity: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single issue block into structured data.

    Args:
        issue_text: Text of the issue block
        severity: Severity level

    Returns:
        Issue dict or None if parsing fails
    """
    lines = issue_text.split('\n')
    if not lines:
        return None

    # First line contains title and optionally flagged_by
    first_line = lines[0].strip()

    # Extract title and flagged_by
    # Format: "Issue title - flagged by: [model1, model2]"
    flagged_match = re.search(r'-\s*flagged by:\s*\[([^\]]+)\]', first_line, re.IGNORECASE)

    if flagged_match:
        title = first_line[:flagged_match.start()].strip()
        flagged_by_str = flagged_match.group(1)
        flagged_by = [m.strip() for m in flagged_by_str.split(',')]
    else:
        # No flagged_by info, just use full line as title
        title = first_line.strip()
        flagged_by = []

    # Initialize issue dict
    issue = {
        "title": title,
        "severity": severity,
        "flagged_by": flagged_by,
        "impact": "",
        "fix": "",
        "description": ""
    }

    # Parse sub-bullets for impact, fix, details
    description_parts = []

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # Check for sub-bullet patterns
        impact_match = re.match(r'[-*]\s*Impact:\s*(.+)', line, re.IGNORECASE)
        fix_match = re.match(r'[-*]\s*(?:Recommended fix|Fix):\s*(.+)', line, re.IGNORECASE)

        if impact_match:
            issue["impact"] = impact_match.group(1).strip()
        elif fix_match:
            issue["fix"] = fix_match.group(1).strip()
        else:
            # Other details go into description
            # Remove leading bullet if present
            clean_line = re.sub(r'^[-*]\s+', '', line)
            if clean_line:
                description_parts.append(clean_line)

    # Combine description parts
    if description_parts:
        issue["description"] = ' '.join(description_parts)

    return issue
