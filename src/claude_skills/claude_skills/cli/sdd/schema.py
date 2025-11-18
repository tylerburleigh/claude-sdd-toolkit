#!/usr/bin/env python3
"""
Schema - Get the SDD spec JSON schema.

Returns the complete sdd-spec-schema.json from the plugin installation,
allowing agents to understand spec structure without needing to know
the installation path.

Usage:
  sdd schema

Returns:
  Complete JSON schema for SDD spec files
"""

from claude_skills.common.schema_loader import load_json_schema
from claude_skills.common.json_output import output_json


def cmd_get_schema(args, printer):
    """
    Handler for 'sdd schema' command.

    Loads and outputs the sdd-spec-schema.json from the plugin installation
    using the schema loader which handles finding the schema across different
    installation locations.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output (not used for JSON-only command)
    """
    schema, source, error = load_json_schema("sdd-spec-schema.json")

    if schema is None:
        # If schema couldn't be loaded, output error
        result = {
            "error": "Schema not found",
            "details": error or "Unknown error loading schema"
        }
        output_json(result, compact=True)
        return 1

    # Output the full schema
    output_json(schema, compact=True)
    return 0


def register_schema(subparsers, parent_parser):
    """
    Register 'schema' subcommand for unified SDD CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'schema',
        parents=[parent_parser],
        help='Get the SDD spec JSON schema',
        description='Returns the complete sdd-spec-schema.json from the plugin installation'
    )

    parser.set_defaults(func=cmd_get_schema)
