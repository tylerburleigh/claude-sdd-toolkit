"""Verbosity level definitions for SDD CLI output control.

This module defines the verbosity level system that controls output detail
across all SDD commands. It implements the three-tier policy defined in
spec cli-verbosity-reduction-2025-11-09-001.
"""

from enum import Enum
from typing import Any, Dict


class VerbosityLevel(Enum):
    """Verbosity levels for CLI output.

    Attributes:
        QUIET: Minimal output - essential data only, omit empty fields
        NORMAL: Balanced output - all standard fields, current default
        VERBOSE: Maximum output - includes debug information and metrics
    """
    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"

    def __str__(self):
        return self.value

    @classmethod
    def from_args(cls, args, config: Dict[str, Any] = None) -> 'VerbosityLevel':
        """Determine verbosity level from parsed command-line arguments.

        Args:
            args: Parsed argparse.Namespace with quiet and verbose flags
            config: Optional configuration dictionary for default verbosity fallback

        Returns:
            VerbosityLevel based on flags (QUIET if --quiet, VERBOSE if --verbose,
            config default if available, NORMAL otherwise)

        Raises:
            ValueError: If both --quiet and --verbose are specified
        """
        has_quiet = getattr(args, 'quiet', False)
        has_verbose = getattr(args, 'verbose', False)

        if has_quiet and has_verbose:
            raise ValueError("Cannot specify both --quiet and --verbose flags")

        if has_quiet:
            return cls.QUIET
        elif has_verbose:
            return cls.VERBOSE
        elif config is not None:
            # Fall back to config default when no CLI flags provided
            return cls.from_config(config)
        else:
            return cls.NORMAL

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'VerbosityLevel':
        """Get default verbosity level from configuration.

        Args:
            config: Configuration dictionary (from sdd_config.json)

        Returns:
            VerbosityLevel from config, defaults to NORMAL if not specified
        """
        verbosity_str = config.get('output', {}).get('default_verbosity', 'normal')
        try:
            return cls(verbosity_str)
        except ValueError:
            # Invalid config value, fall back to NORMAL
            return cls.NORMAL


def should_omit_empty_fields(level: VerbosityLevel) -> bool:
    """Check if empty/null fields should be omitted from output.

    Args:
        level: Current verbosity level

    Returns:
        True if empty fields should be omitted (QUIET mode), False otherwise
    """
    return level == VerbosityLevel.QUIET


def should_include_debug_info(level: VerbosityLevel) -> bool:
    """Check if debug information should be included in output.

    Args:
        level: Current verbosity level

    Returns:
        True if debug info should be included (VERBOSE mode), False otherwise
    """
    return level == VerbosityLevel.VERBOSE


def filter_output_fields(data: Dict[str, Any], level: VerbosityLevel,
                         essential_fields: set = None,
                         standard_fields: set = None) -> Dict[str, Any]:
    """Filter output fields based on verbosity level.

    Implements the field filtering policy from the verbosity specification:
    - QUIET: Include only essential fields, omit null/empty values
    - NORMAL: Include essential and standard fields
    - VERBOSE: Include all fields plus debug info

    Args:
        data: Dictionary of output data
        level: Current verbosity level
        essential_fields: Set of field names that are always included (optional)
        standard_fields: Set of field names included in NORMAL/VERBOSE (optional)

    Returns:
        Filtered dictionary based on verbosity level
    """
    if level == VerbosityLevel.VERBOSE:
        # VERBOSE: Include everything
        return data

    # Build field classification if not provided
    if essential_fields is None:
        essential_fields = set()

    if standard_fields is None:
        standard_fields = set(data.keys())

    filtered: Dict[str, Any] = {}
    included_keys = set()

    for key, value in data.items():
        if key in essential_fields:
            if level == VerbosityLevel.QUIET:
                if value is None or value == [] or value == {}:
                    continue
            filtered[key] = value
            included_keys.add(key)
        elif key in standard_fields and level != VerbosityLevel.QUIET:
            filtered[key] = value
            included_keys.add(key)

    if level == VerbosityLevel.NORMAL:
        for key, value in data.items():
            if key in included_keys or key.startswith('_'):
                continue
            filtered[key] = value

    return filtered
