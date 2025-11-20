#!/usr/bin/env python3
"""
Generate SKILL.md documentation from CLI argparse definitions.

This script dynamically introspects any claude_skills CLI module and generates
markdown documentation for commands, arguments, and options.

Usage:
    claude-skills-gendocs sdd-validate
    claude-skills-gendocs sdd-next --output-file /path/to/output.md
    claude-skills-gendocs doc-query --section commands
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import io
from contextlib import redirect_stdout, redirect_stderr


# Map skill names to module paths
SKILL_MODULE_MAP = {
    'sdd-validate': 'claude_skills.sdd_validate.cli',
    'sdd-next': 'claude_skills.sdd_next.cli',
    'sdd-update': 'claude_skills.sdd_update.cli',
    'doc-query': 'claude_skills.doc_query.cli',
    'run-tests': 'claude_skills.run_tests.cli',
    'code-doc': 'claude_skills.llm_doc_gen.analysis.cli',
    'sdd-integration': 'claude_skills.doc_query.sdd_integration',
}


def get_parser_from_module(module_name: str) -> argparse.ArgumentParser:
    """
    Import a CLI module and extract its ArgumentParser.

    This function attempts to get the parser by:
    1. Looking for a get_parser() function
    2. Calling main() with --help and capturing the parser
    3. Looking for a global 'parser' variable
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {e}")

    # Method 1: Check for get_parser() function
    if hasattr(module, 'get_parser'):
        return module.get_parser()

    # Method 2: Check for create_parser() function
    if hasattr(module, 'create_parser'):
        return module.create_parser()

    # Method 3: Try to extract parser by monkey-patching
    # This is a fallback for modules that create parser in main()
    original_parser_init = argparse.ArgumentParser.__init__
    captured_parser = None

    def capture_parser(self, *args, **kwargs):
        nonlocal captured_parser
        original_parser_init(self, *args, **kwargs)
        if captured_parser is None:
            captured_parser = self

    argparse.ArgumentParser.__init__ = capture_parser

    try:
        # Try calling main with empty args to trigger parser creation
        # Suppress output and catch SystemExit
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            try:
                if hasattr(module, 'main'):
                    # Save original sys.argv
                    original_argv = sys.argv
                    sys.argv = [module_name, '--help']
                    try:
                        module.main()
                    except SystemExit:
                        pass
                    finally:
                        sys.argv = original_argv
            except:
                pass
    finally:
        # Restore original __init__
        argparse.ArgumentParser.__init__ = original_parser_init

    if captured_parser:
        return captured_parser

    # Method 4: Check for global parser variable
    if hasattr(module, 'parser'):
        return module.parser

    raise RuntimeError(
        f"Could not extract ArgumentParser from module '{module_name}'. "
        f"The module should expose a get_parser() or create_parser() function, "
        f"or have a global 'parser' variable."
    )


def format_argument(action: argparse.Action) -> Tuple[str, str]:
    """Format a single argument for documentation."""
    # Build argument signature
    if action.option_strings:
        signature = ', '.join(action.option_strings)
        if action.metavar:
            signature += f" {action.metavar}"
        elif action.nargs in ('+', '*'):
            signature += " ..."
        elif action.type and action.type != bool:
            signature += f" <{action.type.__name__}>"
    else:
        # Positional argument
        if action.metavar:
            signature = f"<{action.metavar}>"
        else:
            signature = f"<{action.dest}>"

    help_text = action.help or ""

    return signature, help_text


def generate_global_options(parser: argparse.ArgumentParser, skill_name: str) -> str:
    """Generate markdown for global options section."""
    lines = ["## Global Options", ""]
    lines.append("These options are available on all commands:")
    lines.append("")

    has_options = False
    for action in parser._actions:
        if action.option_strings and action.dest not in ('help', 'command'):
            sig, help_text = format_argument(action)
            lines.append(f"- `{sig}` - {help_text}")
            has_options = True

    if not has_options:
        return ""

    lines.append("")
    return "\n".join(lines)


def extract_subparsers(parser: argparse.ArgumentParser) -> Optional[Dict[str, argparse.ArgumentParser]]:
    """Extract subparsers from an ArgumentParser."""
    subparsers = {}

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, subparser in action.choices.items():
                subparsers[name] = subparser

    return subparsers if subparsers else None


def generate_command_reference(subparsers: Dict[str, argparse.ArgumentParser], skill_name: str) -> str:
    """Generate markdown for the Command Reference section."""
    if not subparsers:
        return ""

    lines = ["## Command Reference", ""]

    for cmd_name, cmd_parser in subparsers.items():
        lines.append(f"### {cmd_name}")

        # Add description if available
        if cmd_parser.description:
            lines.append(cmd_parser.description.strip())
        elif cmd_parser.epilog:
            lines.append(cmd_parser.epilog.strip())

        lines.append("")

        # Build usage line
        usage_parts = [f"{skill_name} {cmd_name}"]

        # Positional arguments
        positionals = [a for a in cmd_parser._actions if not a.option_strings and a.dest not in ('help', 'command')]
        for action in positionals:
            if action.metavar:
                usage_parts.append(f"<{action.metavar}>")
            else:
                usage_parts.append(f"<{action.dest}>")

        usage_parts.append("[options]")

        lines.append(f"**Usage:** `{' '.join(usage_parts)}`")
        lines.append("")

        # Arguments
        if positionals:
            lines.append("**Arguments:**")
            for action in positionals:
                sig, help_text = format_argument(action)
                lines.append(f"- `{sig}` - {help_text}")
            lines.append("")

        # Options
        optionals = [a for a in cmd_parser._actions if a.option_strings and a.dest != 'help']
        if optionals:
            lines.append("**Options:**")
            for action in optionals:
                sig, help_text = format_argument(action)
                if action.default and action.default != argparse.SUPPRESS:
                    if isinstance(action.default, bool):
                        if action.default:
                            help_text += " (default: enabled)"
                    else:
                        help_text += f" (default: {action.default})"
                lines.append(f"- `{sig}` - {help_text}")
            lines.append("")

    return "\n".join(lines)


def generate_simple_usage(parser: argparse.ArgumentParser, skill_name: str) -> str:
    """Generate usage section for CLIs without subcommands."""
    lines = ["## Usage", ""]

    # Build usage line
    usage_parts = [skill_name]

    # Positional arguments
    positionals = [a for a in parser._actions if not a.option_strings and a.dest not in ('help', 'command')]
    for action in positionals:
        if action.metavar:
            usage_parts.append(f"<{action.metavar}>")
        else:
            usage_parts.append(f"<{action.dest}>")

    if any(a.option_strings for a in parser._actions if a.dest != 'help'):
        usage_parts.append("[options]")

    lines.append(f"**Usage:** `{' '.join(usage_parts)}`")
    lines.append("")

    # Arguments
    if positionals:
        lines.append("**Arguments:**")
        for action in positionals:
            sig, help_text = format_argument(action)
            lines.append(f"- `{sig}` - {help_text}")
        lines.append("")

    # Options
    optionals = [a for a in parser._actions if a.option_strings and a.dest != 'help']
    if optionals:
        lines.append("**Options:**")
        for action in optionals:
            sig, help_text = format_argument(action)
            if action.default and action.default != argparse.SUPPRESS:
                if isinstance(action.default, bool):
                    if action.default:
                        help_text += " (default: enabled)"
                else:
                    help_text += f" (default: {action.default})"
            lines.append(f"- `{sig}` - {help_text}")
        lines.append("")

    return "\n".join(lines)


def generate_documentation(skill_name: str, sections: Optional[List[str]] = None) -> str:
    """
    Generate complete documentation for a skill.

    Args:
        skill_name: Name of the skill (e.g., 'sdd-validate')
        sections: List of sections to include. Options: 'global', 'commands', 'usage'
                 If None, includes all applicable sections.

    Returns:
        Generated markdown documentation
    """
    # Get module path
    module_name = SKILL_MODULE_MAP.get(skill_name)
    if not module_name:
        raise ValueError(
            f"Unknown skill: {skill_name}\n"
            f"Available skills: {', '.join(SKILL_MODULE_MAP.keys())}"
        )

    # Get parser
    parser = get_parser_from_module(module_name)

    # Generate output
    lines = [f"# {skill_name} Command Reference", ""]
    lines.append("*This section is auto-generated from CLI definitions.*")
    lines.append("")

    # Extract subparsers
    subparsers = extract_subparsers(parser)

    # Determine which sections to include
    if sections is None:
        sections = ['global', 'commands' if subparsers else 'usage']

    # Generate sections
    if 'global' in sections:
        global_opts = generate_global_options(parser, skill_name)
        if global_opts:
            lines.append(global_opts)

    if 'commands' in sections and subparsers:
        lines.append(generate_command_reference(subparsers, skill_name))
    elif 'usage' in sections and not subparsers:
        lines.append(generate_simple_usage(parser, skill_name))

    return "\n".join(lines)


def main():
    """Main entry point for the documentation generator."""
    parser = argparse.ArgumentParser(
        prog='claude-skills-gendocs',
        description='Generate markdown documentation from CLI argparse definitions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available skills:
  {', '.join(SKILL_MODULE_MAP.keys())}

Examples:
  claude-skills-gendocs sdd-validate
  claude-skills-gendocs sdd-next --output-file docs/commands.md
  claude-skills-gendocs doc-query --sections global commands
        """
    )

    parser.add_argument('skill', choices=SKILL_MODULE_MAP.keys(),
                       help='Skill name to generate documentation for')
    parser.add_argument('--output-file', '-o',
                       help='Output file path (default: stdout)')
    parser.add_argument('--sections', nargs='+',
                       choices=['global', 'commands', 'usage'],
                       help='Sections to include (default: all applicable)')

    args = parser.parse_args()

    try:
        # Generate documentation
        output = generate_documentation(args.skill, args.sections)

        # Write output
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output)
            print(f"Documentation written to: {output_path}", file=sys.stderr)
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
