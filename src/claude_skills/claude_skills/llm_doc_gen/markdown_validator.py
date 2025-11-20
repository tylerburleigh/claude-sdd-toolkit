"""Markdown validation and sanitization utilities for LLM-generated documentation.

This module provides functions to validate and fix common issues in LLM-generated
markdown content, such as unclosed code fences, incomplete tables, and truncated responses.
"""

import re
from typing import List, Tuple, Optional


def validate_and_fix_markdown(content: str) -> Tuple[str, List[str]]:
    """Validate and fix common markdown issues in LLM-generated content.

    Args:
        content: Raw markdown content from LLM

    Returns:
        Tuple of (fixed_content, list_of_warnings)
    """
    warnings = []
    fixed_content = content

    # Fix unclosed code fences
    fixed_content, fence_warnings = fix_unclosed_code_fences(fixed_content)
    warnings.extend(fence_warnings)

    # Validate tables
    table_warnings = validate_tables(fixed_content)
    warnings.extend(table_warnings)

    # Check for truncated content
    truncation_warnings = detect_truncation(fixed_content)
    warnings.extend(truncation_warnings)

    return fixed_content, warnings


def fix_unclosed_code_fences(content: str) -> Tuple[str, List[str]]:
    """Detect and close any unclosed markdown code fences.

    Args:
        content: Markdown content to check

    Returns:
        Tuple of (fixed_content, list_of_warnings)
    """
    warnings = []
    lines = content.split('\n')

    # Count code fence markers
    fence_pattern = re.compile(r'^```')
    fence_count = 0

    for line in lines:
        if fence_pattern.match(line):
            fence_count += 1

    # If odd number of fences, there's an unclosed fence
    if fence_count % 2 != 0:
        warnings.append("Found unclosed code fence - adding closing fence at end")
        content = content.rstrip() + '\n```\n'

    return content, warnings


def validate_tables(content: str) -> List[str]:
    """Validate markdown tables have both headers and content.

    Args:
        content: Markdown content to check

    Returns:
        List of validation warnings
    """
    warnings = []
    lines = content.split('\n')

    # Look for table headers (lines starting with |)
    table_header_pattern = re.compile(r'^\s*\|')
    separator_pattern = re.compile(r'^\s*\|[\s\-:|]+\|?\s*$')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Found potential table header
        if table_header_pattern.match(line):
            # Check if next line is separator
            if i + 1 < len(lines) and separator_pattern.match(lines[i + 1]):
                # Check if there's at least one data row after separator
                if i + 2 >= len(lines) or not table_header_pattern.match(lines[i + 2]):
                    # Table has header and separator but no data rows
                    table_start = max(0, i - 2)
                    context = '\n'.join(lines[table_start:i+3])
                    warnings.append(f"Incomplete table found (has header but no data rows):\n{context}")
            elif i + 1 < len(lines) and not table_header_pattern.match(lines[i + 1]):
                # Single line that looks like table header but no continuation
                warnings.append(f"Truncated table header found at line {i + 1}: {line}")

        i += 1

    return warnings


def detect_truncation(content: str) -> List[str]:
    """Detect signs of truncated LLM responses.

    Args:
        content: Markdown content to check

    Returns:
        List of truncation warnings
    """
    warnings = []

    # Check for incomplete sections (headers with no content)
    lines = content.split('\n')
    header_pattern = re.compile(r'^#+\s+')

    for i, line in enumerate(lines):
        if header_pattern.match(line):
            # Check if this is the last line or followed only by blank lines
            remaining_lines = lines[i + 1:]
            has_content = any(l.strip() for l in remaining_lines)

            if not has_content:
                warnings.append(f"Section header with no content found: {line.strip()}")

    # Check for common truncation indicators
    truncation_indicators = [
        (r'\|\s*$', "Line ending with incomplete table cell"),
        (r'^\*\*[^*]+$', "Line with unclosed bold marker"),
        (r'^-\s*$', "Empty list item at end"),
    ]

    last_lines = '\n'.join(lines[-5:])
    for pattern, description in truncation_indicators:
        if re.search(pattern, last_lines, re.MULTILINE):
            warnings.append(f"Possible truncation detected: {description}")

    return warnings


def ensure_balanced_markdown(content: str) -> Tuple[str, List[str]]:
    """Ensure markdown formatting markers are balanced.

    Args:
        content: Markdown content to check

    Returns:
        Tuple of (fixed_content, list_of_warnings)
    """
    warnings = []
    fixed_content = content

    # Check bold markers
    bold_pattern = r'\*\*'
    bold_count = len(re.findall(bold_pattern, fixed_content))
    if bold_count % 2 != 0:
        warnings.append("Unbalanced bold markers (**) detected")

    # Check italic markers
    italic_pattern = r'(?<!\*)\*(?!\*)'
    italic_count = len(re.findall(italic_pattern, fixed_content))
    if italic_count % 2 != 0:
        warnings.append("Unbalanced italic markers (*) detected")

    # Check code markers
    code_pattern = r'`(?!``)'
    code_count = len(re.findall(code_pattern, fixed_content))
    if code_count % 2 != 0:
        warnings.append("Unbalanced inline code markers (`) detected")

    return fixed_content, warnings


def sanitize_llm_output(content: str, strict: bool = False) -> Tuple[str, List[str]]:
    """Comprehensive sanitization of LLM-generated markdown.

    Args:
        content: Raw LLM output
        strict: If True, raise exceptions on validation failures instead of warnings

    Returns:
        Tuple of (sanitized_content, list_of_warnings)
    """
    all_warnings = []

    # Apply all validations and fixes
    content, warnings = validate_and_fix_markdown(content)
    all_warnings.extend(warnings)

    content, warnings = ensure_balanced_markdown(content)
    all_warnings.extend(warnings)

    if strict and all_warnings:
        raise ValueError(f"Markdown validation failed with {len(all_warnings)} issues:\n" +
                        '\n'.join(f"  - {w}" for w in all_warnings))

    return content, all_warnings
