#!/usr/bin/env python3
"""
Refactor-candidates workflow: Identify high-priority functions to refactor.

This workflow provides technical debt prioritization by combining complexity
metrics with usage data to identify which functions would benefit most from
refactoring.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import json


def find_refactor_candidates(
    query: Any,  # DocumentationQuery
    min_complexity: int = 10,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Find high-priority refactoring candidates.

    Identifies functions that would benefit most from refactoring by combining
    complexity metrics with usage data. Priority score = complexity × dependents.

    Args:
        query: DocumentationQuery instance
        min_complexity: Minimum complexity threshold (default: 10)
        limit: Maximum number of candidates to return (default: 20)

    Returns:
        Dictionary with keys:
        - candidates: List of candidate dictionaries sorted by priority
        - quick_wins: Subset with high complexity, low dependents
        - major_refactors: Subset with high complexity, high dependents
        - summary: Statistics about the analysis

    Example:
        >>> query = DocumentationQuery()
        >>> query.load()
        >>> result = find_refactor_candidates(query, min_complexity=15, limit=10)
        >>> print(f"Found {len(result['candidates'])} candidates")
    """
    # Get all functions with complexity >= threshold
    all_functions = query.data.get('functions', [])
    high_complexity = [f for f in all_functions
                      if f.get('complexity', 0) >= min_complexity]

    # Calculate priority score for each
    candidates = []
    for func in high_complexity:
        score_data = calculate_priority_score(func)
        candidates.append(score_data)

    # Sort by priority score (highest first)
    candidates.sort(key=lambda x: -x['priority_score'])

    # Limit results
    candidates = candidates[:limit]

    # Identify quick wins and major refactors
    quick_wins = identify_quick_wins(candidates)
    major_refactors = identify_major_refactors(candidates)

    # Calculate summary statistics
    if candidates:
        avg_complexity = sum(c['complexity'] for c in candidates) / len(candidates)
        avg_dependents = sum(c['dependent_count'] for c in candidates) / len(candidates)
        avg_score = sum(c['priority_score'] for c in candidates) / len(candidates)
    else:
        avg_complexity = 0
        avg_dependents = 0
        avg_score = 0

    # Risk distribution
    risk_counts = {'high': 0, 'medium': 0, 'low': 0}
    for candidate in candidates:
        risk_level = candidate.get('risk_level', 'low')
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

    summary = {
        'total_candidates': len(candidates),
        'quick_wins': len(quick_wins),
        'major_refactors': len(major_refactors),
        'avg_complexity': round(avg_complexity, 1),
        'avg_dependents': round(avg_dependents, 1),
        'avg_priority_score': round(avg_score, 1),
        'risk_distribution': risk_counts,
        'min_complexity_threshold': min_complexity
    }

    return {
        'candidates': candidates,
        'quick_wins': quick_wins,
        'major_refactors': major_refactors,
        'summary': summary
    }


def calculate_priority_score(func: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate priority score for a function.

    Priority score = complexity × dependent_count
    Higher score = higher priority for refactoring

    Args:
        func: Function dictionary from documentation

    Returns:
        Dictionary with:
        - name: Function name
        - file: File path
        - line: Line number
        - complexity: Cyclomatic complexity
        - dependent_count: Number of callers
        - priority_score: complexity × dependents
        - risk_level: 'high', 'medium', or 'low'
    """
    name = func.get('name', 'unknown')
    file_path = func.get('file', 'unknown')
    line = func.get('line', 0)
    complexity = func.get('complexity', 0)

    # Get dependent count from callers
    callers = func.get('callers', [])
    dependent_count = len(callers)

    # Calculate priority score
    priority_score = complexity * dependent_count

    # Categorize risk level
    risk_level = categorize_risk_level(priority_score, complexity, dependent_count)

    return {
        'name': name,
        'file': file_path,
        'line': line,
        'complexity': complexity,
        'dependent_count': dependent_count,
        'priority_score': priority_score,
        'risk_level': risk_level
    }


def categorize_risk_level(
    priority_score: int,
    complexity: int,
    dependent_count: int
) -> str:
    """
    Categorize risk level for refactoring.

    Args:
        priority_score: Priority score (complexity × dependents)
        complexity: Cyclomatic complexity
        dependent_count: Number of dependents

    Returns:
        Risk level: 'high', 'medium', or 'low'

    Risk Level Criteria:
        - High: score > 100 (complex + widely used)
        - Medium: score 50-100 (moderately risky)
        - Low: score < 50 (safer to refactor)
    """
    if priority_score > 100:
        return 'high'
    elif priority_score >= 50:
        return 'medium'
    else:
        return 'low'


def identify_quick_wins(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify quick win refactoring candidates.

    Quick wins are functions with high complexity but low dependent count,
    meaning they're isolated complexity that's safe to refactor.

    Criteria: complexity > 15 AND dependents <= 3

    Args:
        candidates: List of candidate dictionaries

    Returns:
        Subset of candidates that are quick wins
    """
    quick_wins = []

    for candidate in candidates:
        complexity = candidate.get('complexity', 0)
        dependents = candidate.get('dependent_count', 0)

        if complexity > 15 and dependents <= 3:
            quick_wins.append(candidate)

    return quick_wins


def identify_major_refactors(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify major refactoring candidates.

    Major refactors are functions with high complexity AND high dependent count,
    meaning they require careful planning and coordination.

    Criteria: complexity > 20 AND dependents > 10

    Args:
        candidates: List of candidate dictionaries

    Returns:
        Subset of candidates that are major refactors
    """
    major_refactors = []

    for candidate in candidates:
        complexity = candidate.get('complexity', 0)
        dependents = candidate.get('dependent_count', 0)

        if complexity > 20 and dependents > 10:
            major_refactors.append(candidate)

    return major_refactors


def format_candidates_list(result: Dict[str, Any]) -> str:
    """
    Format candidates list organized by risk level.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with prioritized candidate list
    """
    candidates = result['candidates']

    if not candidates:
        return "No refactoring candidates found matching the criteria."

    lines = ["🔧 Refactor Candidates (Prioritized by Impact)"]
    lines.append("")

    # Group by risk level
    by_risk: Dict[str, List[Dict[str, Any]]] = {
        'high': [],
        'medium': [],
        'low': []
    }

    for candidate in candidates:
        risk = candidate.get('risk_level', 'low')
        by_risk[risk].append(candidate)

    # Display high priority first
    rank = 1

    if by_risk['high']:
        lines.append(f"🔴 HIGH PRIORITY ({len(by_risk['high'])} candidates)")
        lines.append("")
        for candidate in by_risk['high']:
            lines.append(format_candidate_entry(candidate, rank))
            rank += 1
        lines.append("")

    if by_risk['medium']:
        lines.append(f"🟡 MEDIUM PRIORITY ({len(by_risk['medium'])} candidates)")
        lines.append("")
        for candidate in by_risk['medium']:
            lines.append(format_candidate_entry(candidate, rank))
            rank += 1
        lines.append("")

    if by_risk['low']:
        lines.append(f"🟢 LOW PRIORITY ({len(by_risk['low'])} candidates)")
        lines.append("")
        for candidate in by_risk['low'][:5]:  # Show first 5 low priority
            lines.append(format_candidate_entry(candidate, rank))
            rank += 1
        if len(by_risk['low']) > 5:
            lines.append(f"   ... and {len(by_risk['low']) - 5} more low priority candidates")
        lines.append("")

    return "\n".join(lines)


def format_candidate_entry(candidate: Dict[str, Any], rank: int) -> str:
    """
    Format a single candidate entry.

    Args:
        candidate: Candidate dictionary
        rank: Overall rank (1-based)

    Returns:
        Formatted string for one candidate
    """
    name = candidate['name']
    score = candidate['priority_score']
    complexity = candidate['complexity']
    dependents = candidate['dependent_count']
    file_path = candidate['file']
    line = candidate['line']

    entry = f"{rank}. {name}() - Score: {score} (complexity: {complexity}, dependents: {dependents})"
    entry += f"\n   File: {file_path}:{line}"

    return entry


def format_quick_wins(result: Dict[str, Any]) -> str:
    """
    Format quick wins section.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with quick wins
    """
    quick_wins = result['quick_wins']

    if not quick_wins:
        return ""

    lines = [f"⚡ QUICK WINS ({len(quick_wins)} candidates)"]
    lines.append("")
    lines.append("These functions have high complexity but few dependents.")
    lines.append("They're isolated and safe to refactor with minimal impact.")
    lines.append("")

    for i, candidate in enumerate(quick_wins[:5], 1):  # Show first 5
        name = candidate['name']
        complexity = candidate['complexity']
        dependents = candidate['dependent_count']
        lines.append(f"{i}. 💡 {name}() - Complexity: {complexity}, Dependents: {dependents}")
        lines.append(f"   Recommendation: Safe to refactor, minimal coordination needed")
        lines.append("")

    if len(quick_wins) > 5:
        lines.append(f"   ... and {len(quick_wins) - 5} more quick wins")
        lines.append("")

    return "\n".join(lines)


def format_major_refactors(result: Dict[str, Any]) -> str:
    """
    Format major refactors section.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with major refactors
    """
    major_refactors = result['major_refactors']

    if not major_refactors:
        return ""

    lines = [f"⚠️  MAJOR REFACTORS ({len(major_refactors)} candidates)"]
    lines.append("")
    lines.append("These functions have high complexity AND many dependents.")
    lines.append("Refactoring requires careful planning and coordination.")
    lines.append("")

    for i, candidate in enumerate(major_refactors[:5], 1):  # Show first 5
        name = candidate['name']
        complexity = candidate['complexity']
        dependents = candidate['dependent_count']
        score = candidate['priority_score']
        lines.append(f"{i}. ⚠️  {name}() - Score: {score} (complexity: {complexity}, dependents: {dependents})")
        lines.append(f"   Recommendation: High impact - add tests, plan rollout, coordinate with team")
        lines.append("")

    if len(major_refactors) > 5:
        lines.append(f"   ... and {len(major_refactors) - 5} more major refactors")
        lines.append("")

    return "\n".join(lines)


def format_recommendations(result: Dict[str, Any]) -> str:
    """
    Format general recommendations section.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with recommendations
    """
    summary = result['summary']
    quick_wins = result['quick_wins']
    major_refactors = result['major_refactors']

    lines = ["💡 Recommendations:"]
    lines.append("")

    # Quick wins recommendation
    if quick_wins:
        lines.append(f"1. Start with Quick Wins ({len(quick_wins)} available)")
        lines.append("   These provide immediate complexity reduction with minimal risk")
        lines.append("")

    # Major refactors recommendation
    if major_refactors:
        lines.append(f"2. Plan Major Refactors ({len(major_refactors)} identified)")
        lines.append("   High impact changes - allocate dedicated time and resources")
        lines.append("   Recommended approach:")
        lines.append("     • Add comprehensive tests first")
        lines.append("     • Break into smaller incremental changes")
        lines.append("     • Use feature flags for gradual rollout")
        lines.append("     • Document changes thoroughly")
        lines.append("")

    # General recommendations
    lines.append("3. General Best Practices")
    lines.append("   • Prioritize functions with high priority scores")
    lines.append("   • Ensure test coverage before refactoring")
    lines.append("   • Use impact analysis to understand dependencies")
    lines.append("   • Refactor incrementally with frequent commits")
    lines.append("")

    # Risk distribution advice
    risk_dist = summary['risk_distribution']
    if risk_dist.get('high', 0) > 0:
        lines.append(f"4. Risk Management ({risk_dist['high']} high-risk candidates)")
        lines.append("   High-risk refactors need:")
        lines.append("     • Team review before starting")
        lines.append("     • Dedicated testing resources")
        lines.append("     • Rollback plan in place")

    return "\n".join(lines)


def format_summary(result: Dict[str, Any]) -> str:
    """
    Format summary statistics.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with summary
    """
    summary = result['summary']

    lines = ["📊 Summary:"]
    lines.append(f"  Total candidates: {summary['total_candidates']}")
    lines.append(f"  Quick wins: {summary['quick_wins']}")
    lines.append(f"  Major refactors: {summary['major_refactors']}")
    lines.append(f"  Average complexity: {summary['avg_complexity']}")
    lines.append(f"  Average dependents: {summary['avg_dependents']}")
    lines.append(f"  Average priority score: {summary['avg_priority_score']}")
    lines.append("")

    risk_dist = summary['risk_distribution']
    lines.append(f"  Risk Distribution:")
    lines.append(f"    🔴 High: {risk_dist['high']}")
    lines.append(f"    🟡 Medium: {risk_dist['medium']}")
    lines.append(f"    🟢 Low: {risk_dist['low']}")
    lines.append("")
    lines.append(f"  Complexity threshold: >= {summary['min_complexity_threshold']}")

    return "\n".join(lines)


def format_text_output(result: Dict[str, Any]) -> str:
    """
    Format complete text output for refactor-candidates command.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        Formatted string with all sections
    """
    sections = []

    # Main candidates list
    sections.append(format_candidates_list(result))
    sections.append("")

    # Quick wins
    quick_wins_section = format_quick_wins(result)
    if quick_wins_section:
        sections.append(quick_wins_section)
        sections.append("")

    # Major refactors
    major_refactors_section = format_major_refactors(result)
    if major_refactors_section:
        sections.append(major_refactors_section)
        sections.append("")

    # Recommendations
    sections.append(format_recommendations(result))
    sections.append("")

    # Summary
    sections.append(format_summary(result))

    return "\n".join(sections)


def format_json_output(result: Dict[str, Any]) -> str:
    """
    Format result as JSON.

    Args:
        result: Output from find_refactor_candidates()

    Returns:
        JSON string
    """
    return json.dumps(result, indent=2)
