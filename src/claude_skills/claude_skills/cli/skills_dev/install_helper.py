"""
SDD Installation Helper Commands

Provides unified installation commands for pip and npm dependencies.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from claude_skills.common import PrettyPrinter
from claude_skills.common.sdd_config import get_default_format


def _detect_plugin_location() -> Optional[Path]:
    """
    Detect the installation location of claude_skills package.

    Returns:
        Path to the src/claude_skills directory, or None if not found
    """
    try:
        import claude_skills
        # Get path to claude_skills/__init__.py
        init_file = Path(claude_skills.__file__)
        # Navigate up to src/claude_skills directory
        # Structure: .../src/claude_skills/claude_skills/__init__.py
        src_claude_skills = init_file.parent.parent
        if src_claude_skills.name == "claude_skills" and (src_claude_skills / "pyproject.toml").exists():
            return src_claude_skills
        return None
    except Exception:
        return None


def _check_python_version() -> Tuple[bool, str]:
    """Check if Python version is >= 3.9."""
    version_info = sys.version_info
    if version_info >= (3, 9):
        return True, f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    return False, f"{version_info.major}.{version_info.minor}.{version_info.micro}"


def _check_node_version() -> Tuple[bool, Optional[str], str]:
    """
    Check if Node.js is installed and version >= 18.x.

    Returns:
        (is_valid, version_string, error_message)
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            # Parse version (format: v18.0.0)
            if version_str.startswith('v'):
                version_str = version_str[1:]
            major_version = int(version_str.split('.')[0])
            if major_version >= 18:
                return True, version_str, ""
            return False, version_str, f"Node.js version {version_str} is too old (need >= 18.x)"
        return False, None, "Node.js command failed"
    except FileNotFoundError:
        return False, None, "Node.js not found in PATH"
    except Exception as e:
        return False, None, f"Error checking Node.js: {str(e)}"


def _check_npm_available() -> bool:
    """Check if npm is available."""
    return shutil.which("npm") is not None


def _run_pip_install(package_dir: Path, printer: PrettyPrinter) -> bool:
    """
    Run pip install -e . in the specified directory.

    Args:
        package_dir: Directory containing pyproject.toml
        printer: PrettyPrinter for output

    Returns:
        True if successful, False otherwise
    """
    printer.action("Installing Python package with pip...")
    printer.info(f"Running: pip install -e . --upgrade --force-reinstall")
    printer.info(f"Directory: {package_dir}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--upgrade", "--force-reinstall"],
            cwd=str(package_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )

        if result.returncode == 0:
            printer.success("Python package installed successfully")
            return True
        else:
            printer.error("Failed to install Python package")
            printer.error(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        printer.error("pip install timed out (5 minutes)")
        return False
    except Exception as e:
        printer.error(f"Failed to run pip install: {str(e)}")
        return False


def _run_npm_install(providers_dir: Path, printer: PrettyPrinter) -> bool:
    """
    Run npm install in the providers directory.

    Args:
        providers_dir: Directory containing package.json
        printer: PrettyPrinter for output

    Returns:
        True if successful, False otherwise
    """
    printer.action("Installing Node.js dependencies for OpenCode provider...")
    printer.info(f"Running: npm install")
    printer.info(f"Directory: {providers_dir}")

    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(providers_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )

        if result.returncode == 0:
            printer.success("Node.js dependencies installed successfully")
            return True
        else:
            printer.error("Failed to install Node.js dependencies")
            printer.error(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        printer.error("npm install timed out (5 minutes)")
        return False
    except Exception as e:
        printer.error(f"Failed to run npm install: {str(e)}")
        return False


def _verify_sdd_command() -> Tuple[bool, Optional[str]]:
    """
    Verify that the sdd command is available.

    Returns:
        (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ["sdd", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from output (format may vary)
            version = result.stdout.strip()
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None


def _verify_opencode_provider() -> Tuple[bool, str]:
    """
    Verify that the OpenCode provider can be imported.

    Returns:
        (is_available, message)
    """
    try:
        from claude_skills.common.providers.opencode import create_provider
        return True, "OpenCode provider is available"
    except ImportError as e:
        return False, f"OpenCode provider not available: {str(e)}"
    except Exception as e:
        return False, f"Error checking OpenCode provider: {str(e)}"


def cmd_install(args, printer: PrettyPrinter) -> int:
    """
    Main installation command that handles both pip and npm installations.

    This command:
    1. Detects installation location
    2. Checks prerequisites (Python, Node.js)
    3. Runs pip install -e .
    4. Runs npm install for OpenCode provider
    5. Verifies installations
    6. Reports status and next steps
    """
    # Output format
    use_json = args.json if hasattr(args, 'json') else (get_default_format() == "json")

    # Phase 1: Pre-checks
    printer.header("SDD Toolkit Installation")
    printer.action("Phase 1: Pre-installation checks")

    # Check Python version
    py_ok, py_version = _check_python_version()
    if py_ok:
        printer.success(f"Python version {py_version} (>= 3.9 required)")
    else:
        printer.error(f"Python version {py_version} is too old (>= 3.9 required)")
        return 1

    # Detect installation location
    package_dir = _detect_plugin_location()
    if not package_dir:
        printer.error("Could not detect claude_skills installation location")
        printer.info("Make sure you're running this from an installed package")
        return 1

    printer.success(f"Found installation at: {package_dir}")

    # Check for pyproject.toml
    pyproject_file = package_dir / "pyproject.toml"
    if not pyproject_file.exists():
        printer.error(f"pyproject.toml not found at {pyproject_file}")
        return 1

    # Check Node.js version
    node_ok, node_version, node_error = _check_node_version()
    if node_ok:
        printer.success(f"Node.js version {node_version} (>= 18.x required)")
    else:
        printer.error(f"Node.js check failed: {node_error}")
        printer.info("OpenCode provider requires Node.js >= 18.x")
        printer.info("Install from: https://nodejs.org/")
        return 1

    # Check npm
    if not _check_npm_available():
        printer.error("npm not found in PATH")
        printer.info("npm is required for installing OpenCode dependencies")
        return 1

    printer.success("npm is available")
    printer.blank()

    # Phase 2: Install Python package
    printer.action("Phase 2: Installing Python package")
    if not _run_pip_install(package_dir, printer):
        return 1
    printer.blank()

    # Phase 3: Install Node.js dependencies
    printer.action("Phase 3: Installing Node.js dependencies for OpenCode")
    providers_dir = package_dir / "claude_skills" / "common" / "providers"

    if not providers_dir.exists():
        printer.error(f"Providers directory not found: {providers_dir}")
        return 1

    package_json = providers_dir / "package.json"
    if not package_json.exists():
        printer.error(f"package.json not found: {package_json}")
        return 1

    if not _run_npm_install(providers_dir, printer):
        return 1
    printer.blank()

    # Phase 4: Verify installations
    printer.action("Phase 4: Verifying installation")

    # Verify sdd command
    sdd_ok, sdd_version = _verify_sdd_command()
    if sdd_ok:
        printer.success(f"sdd command is available: {sdd_version}")
    else:
        printer.warning("sdd command not found in PATH")
        printer.info("You may need to restart your terminal or update your PATH")

    # Verify OpenCode provider
    opencode_ok, opencode_msg = _verify_opencode_provider()
    if opencode_ok:
        printer.success(opencode_msg)
    else:
        printer.warning(opencode_msg)

    printer.blank()

    # Phase 5: Report and next steps
    printer.success("Installation complete!")
    printer.blank()
    printer.header("Next Steps")
    printer.info("1. Restart Claude Code if it's running")
    printer.info("2. Open your project in Claude Code")
    printer.info("3. Run: /sdd-setup")
    printer.blank()

    if not sdd_ok:
        printer.warning("Note: If 'sdd' command is not found, try:")
        printer.info("  - Restart your terminal")
        printer.info("  - Check your PATH includes pip install location")
        printer.info("  - Run: python -m claude_skills.cli.sdd --version")

    return 0


def cmd_verify_install(args, printer: PrettyPrinter) -> int:
    """
    Verify installation status of SDD Toolkit.

    Checks:
    - Python package installation
    - sdd command availability
    - OpenCode provider availability
    - Node.js dependencies

    Returns status report in text or JSON format.
    """
    use_json = args.json if hasattr(args, 'json') else (get_default_format() == "json")

    # Collect status information
    status = {
        "python": {},
        "package": {},
        "sdd_command": {},
        "opencode": {},
        "node": {},
        "overall": "unknown"
    }

    # Check Python version
    py_ok, py_version = _check_python_version()
    status["python"] = {
        "version": py_version,
        "valid": py_ok,
        "required": ">= 3.9"
    }

    # Check package location
    package_dir = _detect_plugin_location()
    status["package"] = {
        "detected": package_dir is not None,
        "location": str(package_dir) if package_dir else None
    }

    # Check sdd command
    sdd_ok, sdd_version = _verify_sdd_command()
    status["sdd_command"] = {
        "available": sdd_ok,
        "version": sdd_version
    }

    # Check OpenCode provider
    opencode_ok, opencode_msg = _verify_opencode_provider()
    status["opencode"] = {
        "available": opencode_ok,
        "message": opencode_msg
    }

    # Check Node.js
    node_ok, node_version, node_error = _check_node_version()
    status["node"] = {
        "available": node_ok,
        "version": node_version,
        "error": node_error if not node_ok else None,
        "required": ">= 18.x"
    }

    # Determine overall status
    if all([py_ok, package_dir is not None, sdd_ok, opencode_ok, node_ok]):
        status["overall"] = "fully_installed"
    elif package_dir is not None:
        status["overall"] = "partially_installed"
    else:
        status["overall"] = "not_installed"

    # Output
    if use_json:
        print(json.dumps(status, indent=2))
    else:
        printer.header("SDD Toolkit Installation Status")
        printer.blank()

        # Python
        if py_ok:
            printer.success(f"Python: {py_version} (>= 3.9)")
        else:
            printer.error(f"Python: {py_version} (>= 3.9 required)")

        # Package location
        if package_dir:
            printer.success(f"Package: {package_dir}")
        else:
            printer.error("Package: Not detected")

        # sdd command
        if sdd_ok:
            printer.success(f"sdd command: Available ({sdd_version})")
        else:
            printer.warning("sdd command: Not found in PATH")

        # OpenCode
        if opencode_ok:
            printer.success(f"OpenCode provider: Available")
        else:
            printer.warning(f"OpenCode provider: {opencode_msg}")

        # Node.js
        if node_ok:
            printer.success(f"Node.js: {node_version} (>= 18.x)")
        else:
            printer.error(f"Node.js: {node_error}")

        printer.blank()

        # Overall status
        if status["overall"] == "fully_installed":
            printer.success("Status: Fully installed and ready to use")
        elif status["overall"] == "partially_installed":
            printer.warning("Status: Partially installed - run 'sdd skills-dev install'")
        else:
            printer.error("Status: Not installed - run 'sdd skills-dev install'")

    return 0 if status["overall"] == "fully_installed" else 1


def register_install_helper(subparsers, parent_parser):
    """Register install helper commands."""

    # install command
    install_parser = subparsers.add_parser(
        'install',
        parents=[parent_parser],
        help='Install SDD Toolkit dependencies (pip + npm)',
        description='Unified installation helper for pip and npm dependencies'
    )
    install_parser.set_defaults(func=cmd_install)

    # verify-install command
    verify_parser = subparsers.add_parser(
        'verify-install',
        parents=[parent_parser],
        help='Verify SDD Toolkit installation status',
        description='Check installation status of Python package, sdd command, and OpenCode provider'
    )
    verify_parser.set_defaults(func=cmd_verify_install)
