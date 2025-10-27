"""
Verification result documentation for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Import from sdd-common
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import load_json_spec, save_json_spec, update_node
from claude_skills.common.paths import find_specs_directory


def add_verification_result(
    spec_id: str,
    verify_id: str,
    status: str,
    command: Optional[str] = None,
    output: Optional[str] = None,
    issues: Optional[str] = None,
    notes: Optional[str] = None,
    specs_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Add verification results to the JSON spec file hierarchy node metadata.

    Args:
        spec_id: Specification ID
        verify_id: Verification identifier (e.g., 'verify-1-1')
        status: PASSED, FAILED, or PARTIAL
        command: Command that was run (if automated)
        output: Command output or test results
        issues: Issues found during verification
        notes: Additional notes
        specs_dir: Optional specs directory (auto-detected if not provided)
        dry_run: If True, show result without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # Load JSON spec file
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec file for {spec_id}")
        return False

    valid_statuses = ["PASSED", "FAILED", "PARTIAL"]
    status = status.upper()
    if status not in valid_statuses:
        printer.error(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        return False

    # Check if verify node exists
    hierarchy = spec_data.get("hierarchy", {})
    if verify_id not in hierarchy:
        printer.error(f"Verification step {verify_id} not found in spec hierarchy")
        return False

    # Get status emoji
    status_emoji = {"PASSED": "✅", "FAILED": "❌", "PARTIAL": "⚠️"}.get(status, "")

    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Create verification result object
    verification_result = {
        "date": timestamp,
        "status": status
    }

    if command:
        verification_result["command"] = command

    if output:
        verification_result["output"] = output

    if issues:
        verification_result["issues"] = issues

    if notes:
        verification_result["notes"] = notes

    # Get verify node title for display
    verify_node = hierarchy[verify_id]
    title = verify_node.get("title", verify_id)

    printer.info(f"Verification Result: {status_emoji} {verify_id}: {title}")
    printer.detail(f"  Status: {status}")
    if command:
        printer.detail(f"  Command: {command}")
    if output:
        printer.detail(f"  Output: {output[:100]}{'...' if len(output) > 100 else ''}")
    if notes:
        printer.detail(f"  Notes: {notes}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    try:
        # Get or create metadata for verify node
        verify_metadata = verify_node.get("metadata", {})
        verify_metadata["verification_result"] = verification_result

        # Update the verify node
        updates = {"metadata": verify_metadata}
        if not update_node(spec_data, verify_id, updates):
            printer.error("Failed to update verify node with result")
            return False

        # Update last_updated timestamp
        spec_data["last_updated"] = timestamp

        # Save JSON spec file
        if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
            printer.error("Failed to save spec file")
            return False

        printer.success(f"Verification result added for {verify_id} in {spec_id}.json")
        return True

    except Exception as e:
        printer.error(f"Failed to add verification result: {e}")
        return False


def format_verification_summary(verification_results: list[dict]) -> str:
    """
    Format a summary of multiple verification results with proper newlines.

    Args:
        verification_results: List of dicts with keys:
            - verify_id: str (e.g., 'verify-1-1')
            - title: str
            - status: str ('PASSED', 'FAILED', 'PARTIAL')
            - command: Optional[str]
            - result: Optional[str]
            - notes: Optional[str]

    Returns:
        Formatted summary string ready for display
    """
    lines = []

    # Count results by status
    passed = sum(1 for v in verification_results if v.get('status', '').upper() == 'PASSED')
    failed = sum(1 for v in verification_results if v.get('status', '').upper() == 'FAILED')
    partial = sum(1 for v in verification_results if v.get('status', '').upper() == 'PARTIAL')
    total = len(verification_results)

    # Header
    all_passed = (passed == total)
    if all_passed:
        lines.append(f"✅ Phase Verification Complete!")
        lines.append("")
        lines.append(f"All {total} verification steps executed successfully.")
    else:
        lines.append(f"⚠️ Phase Verification Results")
        lines.append("")
        lines.append(f"Total: {total} | Passed: {passed} | Failed: {failed} | Partial: {partial}")

    lines.append("")
    lines.append("📊 Verification Results Summary")
    lines.append("")

    # Individual results
    for v in verification_results:
        verify_id = v.get('verify_id', 'unknown')
        title = v.get('title', 'Unknown')
        status = v.get('status', 'UNKNOWN').upper()
        command = v.get('command')
        result = v.get('result')
        notes = v.get('notes')

        # Status emoji
        status_emoji = {
            'PASSED': '✅',
            'FAILED': '❌',
            'PARTIAL': '⚠️'
        }.get(status, '❓')

        # Verification header
        lines.append(f"{status_emoji} {verify_id}: {title}")
        lines.append("")  # Blank line

        # Status
        lines.append(f"Status: {status}")

        # Command
        if command:
            lines.append(f"Command: {command}")

        # Result
        if result:
            lines.append(f"Result: {result}")

        # Notes
        if notes:
            lines.append(f"Notes: {notes}")

        lines.append("")  # Blank line before next verification
        lines.append("---")
        lines.append("")  # Blank line after separator

    return '\n'.join(lines)
