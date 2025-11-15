#!/usr/bin/env python3
"""
Cache Management CLI - Commands for managing the SDD consultation cache.

Provides commands to inspect, manage, and maintain the cache used for
AI consultation results.
"""

import argparse
import json
import sys
from pathlib import Path

from claude_skills.common import PrettyPrinter
from claude_skills.common.cache import CacheManager
from claude_skills.common.config import get_cache_config, is_cache_enabled
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    CACHE_CLEAR_ESSENTIAL,
    CACHE_CLEAR_STANDARD,
    CACHE_STATS_ESSENTIAL,
    CACHE_STATS_STANDARD,
)


def handle_cache_clear(args, printer: PrettyPrinter):
    """
    Handle 'sdd cache clear' command.

    Clears cache entries with optional filters:
    - --spec: Clear only entries for a specific spec ID
    - --type: Clear only entries of a specific review type (fidelity, plan)

    Args:
        args: Parsed command-line arguments
        printer: PrettyPrinter instance for formatted output

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Check if caching is enabled
        if not is_cache_enabled():
            if getattr(args, 'json', None):
                output_json({"error": "Cache is disabled in configuration"}, args.compact)
            else:
                printer.warning("Cache is disabled in configuration")
                printer.info("To enable caching, check .claude/config.json")
            return 1

        # Extract filters from args
        spec_id = getattr(args, 'spec_id', None)
        review_type = getattr(args, 'review_type', None)

        # Initialize cache manager
        cache = CacheManager()

        # Perform clear operation
        count = cache.clear(spec_id=spec_id, review_type=review_type)

        # Format output
        if getattr(args, 'json', None):
            payload = {
                "entries_deleted": count,
                "filters": {}
            }
            if spec_id:
                payload["filters"]["spec_id"] = spec_id
            if review_type:
                payload["filters"]["review_type"] = review_type

            # Apply verbosity filtering
            filtered_output = prepare_output(payload, args, CACHE_CLEAR_ESSENTIAL, CACHE_CLEAR_STANDARD)
            output_json(filtered_output, args.compact)
        else:
            # Human-readable output
            if count == 0:
                printer.warning("No cache entries matched the specified filters")
                if spec_id:
                    printer.info(f"Filter: spec_id={spec_id}")
                if review_type:
                    printer.info(f"Filter: review_type={review_type}")
            else:
                printer.success(f"Cleared {count} cache entries")
                if spec_id or review_type:
                    printer.blank()
                    printer.header("Filters Applied")
                    if spec_id:
                        printer.result("Spec ID", spec_id)
                    if review_type:
                        printer.result("Review Type", review_type)

        return 0

    except Exception as e:
        printer.error(f"Error clearing cache: {e}")
        if getattr(args, 'debug', False):
            import traceback
            printer.error(traceback.format_exc())
        return 1


def handle_cache_info(args, printer: PrettyPrinter):
    """
    Handle 'sdd cache info' command.

    Displays cache statistics including:
    - Cache location (directory path)
    - Total cache size (MB)
    - Number of entries (total, active, expired)
    - Cache hit rate (if trackable)

    Args:
        args: Parsed command-line arguments
        printer: PrettyPrinter instance for formatted output
    """
    try:
        # Check if caching is enabled
        if not is_cache_enabled():
            if getattr(args, 'json', None):
                output_json({"error": "Cache is disabled in configuration"}, args.compact)
            else:
                printer.warning("Cache is disabled in configuration")
                printer.info("To enable caching, check .claude/config.json")
            return 1

        # Initialize cache manager
        cache = CacheManager()

        # Get cache statistics
        stats = cache.get_stats()

        # Handle error case
        if "error" in stats:
            if getattr(args, 'json', None):
                output_json({"error": stats['error']}, args.compact)
            else:
                printer.error(f"Failed to get cache stats: {stats['error']}")
            return 1

        # Format output based on output mode
        # Check for explicit JSON flag (args.json can be True, False, or None)
        json_output = getattr(args, 'json', None)
        if json_output:
            # Apply verbosity filtering
            filtered_output = prepare_output(stats, args, CACHE_STATS_ESSENTIAL, CACHE_STATS_STANDARD)
            output_json(filtered_output, args.compact)
            return 0

        # Human-readable output
        printer.header("Cache Information")
        printer.result("Location", stats['cache_dir'])
        printer.blank()

        printer.header("Cache Statistics")
        printer.result("Total entries", str(stats['total_entries']))
        printer.result("Active entries", str(stats['active_entries']))

        if stats['expired_entries'] > 0:
            printer.result("Expired entries", f"{stats['expired_entries']} (cleanup recommended)")
        else:
            printer.result("Expired entries", str(stats['expired_entries']))

        printer.blank()

        printer.header("Cache Size")
        printer.result("Total size", f"{stats['total_size_mb']} MB ({stats['total_size_bytes']} bytes)")

        # Check if cache directory exists and is writable
        cache_path = Path(stats['cache_dir'])
        if cache_path.exists():
            if cache_path.is_dir():
                printer.success("Cache directory is accessible")
            else:
                printer.error("Cache directory path exists but is not a directory")
        else:
            printer.warning("Cache directory does not exist (will be created on first use)")

        # Suggest cleanup if there are expired entries
        if stats['expired_entries'] > 0:
            printer.blank()
            printer.action("Run 'sdd cache cleanup' to remove expired entries")

        return 0

    except Exception as e:
        printer.error(f"Error getting cache info: {e}")
        if args.debug:
            import traceback
            printer.error(traceback.format_exc())
        return 1


def register_cache(subparsers, parent_parser):
    """
    Register 'cache' subcommand for unified SDD CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'cache',
        parents=[parent_parser],
        help='Manage AI consultation cache',
        description='Commands for inspecting and managing the SDD consultation cache'
    )

    # Create subcommands for cache operations
    cache_subparsers = parser.add_subparsers(
        title='cache commands',
        dest='cache_command',
        required=True,
        help='Cache management operations'
    )

    # Register 'info' subcommand
    info_parser = cache_subparsers.add_parser(
        'info',
        parents=[parent_parser],
        help='Show cache information and statistics',
        description='Display cache location, size, and entry statistics'
    )
    info_parser.set_defaults(func=handle_cache_info)

    # Register 'clear' subcommand
    clear_parser = cache_subparsers.add_parser(
        'clear',
        parents=[parent_parser],
        help='Clear cache entries with optional filters',
        description='Remove cache entries, optionally filtered by spec ID or review type'
    )
    clear_parser.add_argument(
        '--spec-id',
        type=str,
        dest='spec_id',
        metavar='SPEC_ID',
        help='Clear only entries for the specified spec ID'
    )
    clear_parser.add_argument(
        '--review-type',
        type=str,
        dest='review_type',
        metavar='TYPE',
        choices=['fidelity', 'plan'],
        help='Clear only entries of the specified review type (fidelity or plan)'
    )
    clear_parser.set_defaults(func=handle_cache_clear)

    # Note: Additional subcommand (cleanup) will be added in future task
    # This follows the spec's task breakdown:
    # - task-1-4-1: Implement 'info' command (completed)
    # - task-1-4-2: Implement 'clear' command with filters (this task)
    # - task-1-4-3: Implement 'cleanup' command (removes expired entries)
