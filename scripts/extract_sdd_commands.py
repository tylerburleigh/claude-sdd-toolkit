#!/usr/bin/env python3
"""
Extract sdd commands from SKILL.md files for manual review.

This script extracts all sdd command invocations from SKILL.md files
and displays them in an organized format for manual review.
"""

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class Command:
    """Represents an extracted sdd command."""
    file_path: Path
    line_number: int
    raw_line: str
    command: str


def extract_commands_from_file(file_path: Path) -> List[Command]:
    """Extract all sdd commands from a SKILL.md file.

    Args:
        file_path: Path to SKILL.md file

    Returns:
        List of extracted commands
    """
    commands = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        # Look for lines containing 'sdd '
        if 'sdd ' in line:
            # Extract the sdd command (from 'sdd' to end of logical command)
            # Handle various formats:
            # - sdd command args
            # - `sdd command args`
            # - sdd command args | pipeline

            # Find the sdd command
            match = re.search(r'sdd\s+[^\n`|#]+', line)
            if match:
                cmd = match.group(0).strip()
                # Clean up common artifacts
                cmd = cmd.rstrip('`').rstrip('\\').strip()

                commands.append(Command(
                    file_path=file_path,
                    line_number=line_num,
                    raw_line=line.strip(),
                    command=cmd
                ))

    return commands


def extract_all_commands(skills_dir: Path) -> Dict[Path, List[Command]]:
    """Extract commands from all SKILL.md files.

    Args:
        skills_dir: Path to skills directory

    Returns:
        Dictionary mapping file paths to lists of commands
    """
    results = {}
    skill_files = sorted(skills_dir.glob('*/SKILL.md'))

    for skill_file in skill_files:
        commands = extract_commands_from_file(skill_file)
        if commands:
            results[skill_file] = commands

    return results


def get_unique_commands(commands_by_file: Dict[Path, List[Command]]) -> List[str]:
    """Get sorted list of unique command patterns.

    Args:
        commands_by_file: Commands grouped by file

    Returns:
        Sorted list of unique command strings
    """
    unique = set()
    for commands in commands_by_file.values():
        for cmd in commands:
            unique.add(cmd.command)
    return sorted(unique)


def print_by_file(commands_by_file: Dict[Path, List[Command]]):
    """Print commands grouped by file.

    Args:
        commands_by_file: Commands grouped by file
    """
    total_commands = sum(len(cmds) for cmds in commands_by_file.values())

    print(f"Found {len(commands_by_file)} SKILL.md files")
    print(f"Extracted {total_commands} sdd commands\n")
    print("=" * 80)

    for file_path, commands in sorted(commands_by_file.items()):
        rel_path = file_path.relative_to(file_path.parent.parent.parent)
        print(f"\n{rel_path} ({len(commands)} commands)")
        print("-" * 80)

        for cmd in commands:
            print(f"  Line {cmd.line_number:4d}: {cmd.command}")


def print_unique(commands_by_file: Dict[Path, List[Command]]):
    """Print unique commands.

    Args:
        commands_by_file: Commands grouped by file
    """
    unique = get_unique_commands(commands_by_file)

    print(f"Found {len(unique)} unique sdd command patterns\n")
    print("=" * 80)

    for cmd in unique:
        print(cmd)


def print_grouped(commands_by_file: Dict[Path, List[Command]]):
    """Print commands grouped by command pattern.

    Args:
        commands_by_file: Commands grouped by file
    """
    # Group by command pattern
    by_pattern = defaultdict(list)
    for file_path, commands in commands_by_file.items():
        for cmd in commands:
            by_pattern[cmd.command].append((file_path, cmd.line_number))

    print(f"Found {len(by_pattern)} unique command patterns\n")
    print("=" * 80)

    for pattern in sorted(by_pattern.keys()):
        locations = by_pattern[pattern]
        print(f"\n{pattern}")
        print(f"  Used in {len(locations)} location(s):")
        for file_path, line_num in sorted(locations):
            rel_path = file_path.relative_to(file_path.parent.parent.parent)
            print(f"    - {rel_path}:{line_num}")


def print_json_output(commands_by_file: Dict[Path, List[Command]]):
    """Print commands in JSON format.

    Args:
        commands_by_file: Commands grouped by file
    """
    output = {
        'total_files': len(commands_by_file),
        'total_commands': sum(len(cmds) for cmds in commands_by_file.values()),
        'files': []
    }

    for file_path, commands in sorted(commands_by_file.items()):
        rel_path = str(file_path.relative_to(file_path.parent.parent.parent))
        file_data = {
            'file': rel_path,
            'command_count': len(commands),
            'commands': [
                {
                    'line': cmd.line_number,
                    'command': cmd.command,
                    'raw_line': cmd.raw_line
                }
                for cmd in commands
            ]
        }
        output['files'].append(file_data)

    print(json.dumps(output, indent=2))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract sdd commands from SKILL.md files'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['by-file', 'unique', 'grouped', 'json'],
        default='by-file',
        help='Output format (default: by-file)'
    )
    parser.add_argument(
        '--skills-dir',
        type=Path,
        default=Path.cwd() / '.claude' / 'skills',
        help='Path to skills directory (default: .claude/skills)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Write output to file instead of stdout'
    )

    args = parser.parse_args()

    # Extract commands
    commands_by_file = extract_all_commands(args.skills_dir)

    if not commands_by_file:
        print("No SKILL.md files found or no commands extracted.", file=sys.stderr)
        return 1

    # Redirect output if requested
    if args.output:
        import sys
        original_stdout = sys.stdout
        sys.stdout = open(args.output, 'w', encoding='utf-8')

    try:
        # Print in requested format
        if args.format == 'by-file':
            print_by_file(commands_by_file)
        elif args.format == 'unique':
            print_unique(commands_by_file)
        elif args.format == 'grouped':
            print_grouped(commands_by_file)
        elif args.format == 'json':
            print_json_output(commands_by_file)
    finally:
        if args.output:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Output written to {args.output}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
