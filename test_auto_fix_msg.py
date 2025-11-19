
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.abspath("src/claude_skills"))

from claude_skills.sdd_validate.cli import cmd_validate

# Mock args
class Args:
    spec_file = "some-spec"
    auto_fix = True
    json = False
    compact = False
    verbosity_level = 1
    quiet = False
    # Add other required args with defaults
    report = False
    report_format = 'markdown'
    path = '.'
    specs_dir = None

mock_printer = MagicMock()

print("Running cmd_validate with --auto-fix...")
exit_code = cmd_validate(Args(), mock_printer)

print(f"Exit code: {exit_code}")
# Verify printer called with error
mock_printer.error.assert_called_with("The --auto-fix flag is not supported for 'validate'. Please use 'sdd fix' command instead.")
print("Verification successful!")
