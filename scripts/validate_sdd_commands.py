#!/usr/bin/env python3
"""
Validate sdd commands in SKILL.md files.

This script extracts all sdd command invocations from SKILL.md files
and validates them against the actual CLI structure.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class Command:
    """Represents an extracted sdd command."""
    file_path: Path
    line_number: int
    raw_command: str
    parsed_parts: List[str]  # e.g., ['doc', 'find-class']


@dataclass
class ValidationResult:
    """Result of validating a command."""
    command: Command
    is_valid: bool
    error_message: Optional[str] = None
    suggestion: Optional[str] = None


class CommandRegistry:
    """Registry of valid sdd commands."""

    def __init__(self):
        self.commands: Dict[str, Set[str]] = {}
        self.aliases: Dict[Tuple[str, ...], Tuple[str, ...]] = {}

    def add_command(self, path: List[str]):
        """Add a command to the registry.

        Args:
            path: Command path, e.g., ['doc', 'find-class']
        """
        if not path:
            return

        if len(path) == 1:
            # Top-level command
            if '' not in self.commands:
                self.commands[''] = set()
            self.commands[''].add(path[0])
        else:
            # Nested command
            parent = '.'.join(path[:-1])
            if parent not in self.commands:
                self.commands[parent] = set()
            self.commands[parent].add(path[-1])

    def add_alias(self, alias_path: List[str], real_path: List[str]):
        """Add a command alias.

        Args:
            alias_path: Alias command path
            real_path: Real command path
        """
        self.aliases[tuple(alias_path)] = tuple(real_path)

    def is_valid(self, command_parts: List[str]) -> bool:
        """Check if a command is valid.

        Args:
            command_parts: Command parts, e.g., ['doc', 'find-class']

        Returns:
            True if the command is valid
        """
        if not command_parts:
            return False

        # Check if it's an alias
        command_tuple = tuple(command_parts)
        if command_tuple in self.aliases:
            command_parts = list(self.aliases[command_tuple])

        # Check top-level command
        if command_parts[0] not in self.commands.get('', set()):
            return False

        # Check nested commands
        for i in range(1, len(command_parts)):
            parent = '.'.join(command_parts[:i])
            if parent not in self.commands:
                return False
            if command_parts[i] not in self.commands[parent]:
                return False

        return True

    def get_similar_commands(self, command_parts: List[str], max_suggestions: int = 3) -> List[str]:
        """Get similar valid commands for suggestions.

        Args:
            command_parts: Invalid command parts
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested command strings
        """
        suggestions = []

        # If first part is invalid, suggest valid top-level commands
        if command_parts[0] not in self.commands.get('', set()):
            valid_top_level = self.commands.get('', set())
            # Simple substring matching
            matches = [cmd for cmd in valid_top_level if command_parts[0] in cmd or cmd in command_parts[0]]
            suggestions.extend(matches[:max_suggestions])
        else:
            # Find valid subcommands at the deepest valid level
            for i in range(1, len(command_parts)):
                parent = '.'.join(command_parts[:i])
                if parent in self.commands:
                    invalid_part = command_parts[i]
                    valid_subcommands = self.commands[parent]
                    matches = [cmd for cmd in valid_subcommands if invalid_part in cmd or cmd in invalid_part]
                    full_commands = [f"sdd {' '.join(command_parts[:i])} {match}" for match in matches]
                    suggestions.extend(full_commands[:max_suggestions])
                    break

        return suggestions[:max_suggestions]


class CommandExtractor:
    """Extract sdd commands from SKILL.md files."""

    # Pattern to match sdd commands
    SDD_PATTERN = re.compile(r'^\s*sdd\s+(.+?)(?:\s*(?:#|$))', re.MULTILINE)

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    def find_skill_files(self) -> List[Path]:
        """Find all SKILL.md files."""
        return sorted(self.skills_dir.glob('*/SKILL.md'))

    def extract_from_file(self, file_path: Path, registry: Optional[CommandRegistry] = None) -> List[Command]:
        """Extract commands from a single SKILL.md file.

        Args:
            file_path: Path to SKILL.md file
            registry: Optional command registry for better parsing

        Returns:
            List of extracted commands
        """
        commands = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        for line_num, line in enumerate(lines, start=1):
            # Look for sdd commands
            if 'sdd ' in line:
                # Extract the command part
                match = re.search(r'sdd\s+([a-z0-9-]+(?:\s+[a-z0-9-]+)*)', line)
                if match:
                    raw_command = match.group(0)
                    command_args = match.group(1)

                    # Parse command parts (stop at first non-command-like token)
                    all_parts = []
                    for part in command_args.split():
                        # Stop at flags, file paths, or arguments
                        if part.startswith('-') or part.startswith('<') or '/' in part:
                            break
                        # Only include command-like tokens (lowercase, hyphens)
                        if re.match(r'^[a-z0-9-]+$', part):
                            all_parts.append(part)
                        else:
                            break

                    # If registry is available, find the longest valid command
                    if registry and all_parts:
                        # Try from longest to shortest to find valid command
                        for length in range(min(len(all_parts), 3), 0, -1):
                            parts = all_parts[:length]
                            if registry.is_valid(parts):
                                commands.append(Command(
                                    file_path=file_path,
                                    line_number=line_num,
                                    raw_command=raw_command,
                                    parsed_parts=parts
                                ))
                                break
                        else:
                            # No valid command found, but still record it
                            # Use max 2 parts for unknown commands (most are 2-level)
                            parts = all_parts[:min(len(all_parts), 2)]
                            commands.append(Command(
                                file_path=file_path,
                                line_number=line_num,
                                raw_command=raw_command,
                                parsed_parts=parts
                            ))
                    elif all_parts:
                        # No registry, use heuristic: limit to 2 parts max
                        parts = all_parts[:min(len(all_parts), 2)]
                        commands.append(Command(
                            file_path=file_path,
                            line_number=line_num,
                            raw_command=raw_command,
                            parsed_parts=parts
                        ))

        return commands

    def extract_all(self) -> Dict[Path, List[Command]]:
        """Extract commands from all SKILL.md files.

        Returns:
            Dictionary mapping file paths to lists of commands
        """
        results = {}
        for skill_file in self.find_skill_files():
            commands = self.extract_from_file(skill_file)
            if commands:
                results[skill_file] = commands
        return results


def build_registry() -> CommandRegistry:
    """Build the command registry from sdd --help output.

    Returns:
        CommandRegistry with all valid commands
    """
    registry = CommandRegistry()

    # Get top-level commands from sdd --help
    try:
        result = subprocess.run(['sdd', '--help'], capture_output=True, text=True, check=True)
        help_text = result.stdout

        # Extract commands from the {command1,command2,...} pattern
        commands_match = re.search(r'\{([^}]+)\}', help_text)
        if commands_match:
            commands = commands_match.group(1).split(',')
            for cmd in commands:
                registry.add_command([cmd.strip()])
    except subprocess.CalledProcessError as e:
        print(f"Error running 'sdd --help': {e}", file=sys.stderr)
        sys.exit(1)

    # Get doc subcommands
    try:
        result = subprocess.run(['sdd', 'doc', '--help'], capture_output=True, text=True, check=True)
        help_text = result.stdout

        commands_match = re.search(r'\{([^}]+)\}', help_text)
        if commands_match:
            commands = commands_match.group(1).split(',')
            for cmd in commands:
                cmd = cmd.strip()
                # Handle aliases like "validate-json (validate)"
                if '(' in cmd:
                    main_cmd, alias = cmd.split('(')
                    main_cmd = main_cmd.strip()
                    alias = alias.strip().rstrip(')')
                    registry.add_command(['doc', main_cmd])
                    registry.add_alias(['doc', alias], ['doc', main_cmd])
                else:
                    registry.add_command(['doc', cmd])
    except subprocess.CalledProcessError:
        pass  # Subcommand might not exist

    # Get test subcommands
    try:
        result = subprocess.run(['sdd', 'test', '--help'], capture_output=True, text=True, check=True)
        help_text = result.stdout

        commands_match = re.search(r'\{([^}]+)\}', help_text)
        if commands_match:
            commands = commands_match.group(1).split(',')
            for cmd in commands:
                registry.add_command(['test', cmd.strip()])
    except subprocess.CalledProcessError:
        pass

    # Get skills-dev subcommands
    try:
        result = subprocess.run(['sdd', 'skills-dev', '--help'], capture_output=True, text=True, check=True)
        help_text = result.stdout

        commands_match = re.search(r'\{([^}]+)\}', help_text)
        if commands_match:
            commands = commands_match.group(1).split(',')
            for cmd in commands:
                registry.add_command(['skills-dev', cmd.strip()])
    except subprocess.CalledProcessError:
        pass

    return registry


def validate_commands(
    commands_by_file: Dict[Path, List[Command]],
    registry: CommandRegistry
) -> Dict[Path, List[ValidationResult]]:
    """Validate all commands against the registry.

    Args:
        commands_by_file: Commands grouped by file
        registry: Command registry

    Returns:
        Validation results grouped by file
    """
    results = {}

    for file_path, commands in commands_by_file.items():
        file_results = []

        for command in commands:
            is_valid = registry.is_valid(command.parsed_parts)

            if is_valid:
                file_results.append(ValidationResult(
                    command=command,
                    is_valid=True
                ))
            else:
                # Get suggestions for invalid commands
                suggestions = registry.get_similar_commands(command.parsed_parts)
                suggestion = suggestions[0] if suggestions else None

                error_msg = f"Unknown command: sdd {' '.join(command.parsed_parts)}"

                file_results.append(ValidationResult(
                    command=command,
                    is_valid=False,
                    error_message=error_msg,
                    suggestion=suggestion
                ))

        results[file_path] = file_results

    return results


def print_report(
    results: Dict[Path, List[ValidationResult]],
    verbose: bool = False,
    json_output: bool = False
):
    """Print validation report.

    Args:
        results: Validation results grouped by file
        verbose: Whether to print verbose output
        json_output: Whether to output JSON
    """
    total_valid = sum(sum(1 for r in file_results if r.is_valid) for file_results in results.values())
    total_invalid = sum(sum(1 for r in file_results if not r.is_valid) for file_results in results.values())
    total_commands = total_valid + total_invalid

    if json_output:
        # JSON output
        output = {
            'summary': {
                'total_files': len(results),
                'total_commands': total_commands,
                'valid_commands': total_valid,
                'invalid_commands': total_invalid
            },
            'files': []
        }

        for file_path, file_results in results.items():
            file_data = {
                'file': str(file_path.relative_to(file_path.parent.parent.parent)),
                'total': len(file_results),
                'valid': sum(1 for r in file_results if r.is_valid),
                'invalid': sum(1 for r in file_results if not r.is_valid),
                'errors': []
            }

            for result in file_results:
                if not result.is_valid:
                    file_data['errors'].append({
                        'line': result.command.line_number,
                        'command': result.command.raw_command,
                        'error': result.error_message,
                        'suggestion': result.suggestion
                    })

            output['files'].append(file_data)

        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print("Validating sdd commands in SKILL.md files...\n")
        print(f"Found {len(results)} SKILL.md files")
        print(f"Extracted {total_commands} sdd commands\n")

        print("Results by file:")
        print("━" * 60)

        for file_path, file_results in sorted(results.items()):
            rel_path = file_path.relative_to(file_path.parent.parent.parent)
            valid_count = sum(1 for r in file_results if r.is_valid)
            invalid_count = sum(1 for r in file_results if not r.is_valid)

            if invalid_count == 0:
                print(f"✓ {rel_path} ({len(file_results)} commands, all valid)")
            else:
                print(f"✗ {rel_path} ({len(file_results)} commands, {invalid_count} invalid)")

                for result in file_results:
                    if not result.is_valid:
                        print(f"  - Line {result.command.line_number}: '{result.command.raw_command}'")
                        print(f"    {result.error_message}")
                        if result.suggestion:
                            print(f"    Suggestion: {result.suggestion}")
                        else:
                            print(f"    No similar command found")

            if verbose and invalid_count == 0:
                # Show all commands in verbose mode
                for result in file_results:
                    print(f"  ✓ Line {result.command.line_number}: {result.command.raw_command}")

        print("\n" + "━" * 60)
        print("Summary:")
        print(f"✓ {total_valid} valid commands")
        print(f"✗ {total_invalid} invalid commands")

        if total_invalid > 0:
            sys.exit(1)
        else:
            print("\n✓ All commands are valid!")
            sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate sdd commands in SKILL.md files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show all commands, not just invalid ones'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--skills-dir',
        type=Path,
        default=Path.cwd() / '.claude' / 'skills',
        help='Path to skills directory (default: .claude/skills)'
    )

    args = parser.parse_args()

    # Build command registry
    registry = build_registry()

    # Extract commands from SKILL.md files
    extractor = CommandExtractor(args.skills_dir)
    commands_by_file = extractor.extract_all()

    if not commands_by_file:
        print("No SKILL.md files found or no commands extracted.", file=sys.stderr)
        sys.exit(1)

    # Validate commands
    results = validate_commands(commands_by_file, registry)

    # Print report
    print_report(results, verbose=args.verbose, json_output=args.json)


if __name__ == '__main__':
    main()
