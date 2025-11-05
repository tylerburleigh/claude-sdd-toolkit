# Tool Availability Checking Patterns

## Overview

This document describes the patterns and best practices for checking tool availability in the Claude SDD Toolkit. These patterns ensure graceful degradation when external CLI tools (gemini, codex, cursor-agent) are unavailable.

## Core Pattern: Two-Phase Approach

The toolkit uses a two-phase approach for tool availability:

1. **Discovery Phase**: Check if tools are available before attempting to use them
2. **Execution Phase**: Handle errors gracefully when tools fail during execution

## Discovery Methods

### Method 1: shutil.which() (Preferred)

The simplest and most reliable method for checking if a command is available in PATH:

```python
import shutil

def is_tool_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None

# Usage
if is_tool_available("gemini"):
    # Tool is available, proceed with usage
    result = subprocess.run(["gemini", "..."])
else:
    # Tool not available, handle gracefully
    logger.warning("gemini CLI not found in PATH")
```

**When to use:**
- Quick PATH checks
- Before subprocess calls
- In tool discovery loops

**Example from codebase:**
See `run_tests/tool_checking.py:142-157` for the `discover_tools()` implementation.

### Method 2: Version Check with subprocess

Verify that a tool not only exists but also works correctly:

```python
import subprocess

def check_tool_works(command: str, timeout: int = 5) -> bool:
    """Verify tool exists and responds to --version."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

# Usage
if check_tool_works("codex"):
    # Tool works correctly
    pass
```

**When to use:**
- Initial setup/configuration
- Diagnostic tools
- When tool existence isn't enough (need to verify it works)

**Example from codebase:**
See `run_tests/tool_checking.py:58-79` for the `check_tool_available()` implementation.

### Method 3: Configuration-Based Gating

Check both availability AND configuration flags:

```python
def should_use_tool(command: str, config: dict) -> bool:
    """Check if tool is both available and enabled in config."""
    # Check config first (fast)
    if not config.get("tools", {}).get(command, {}).get("enabled", True):
        return False

    # Then check availability (slower)
    return shutil.which(command) is not None

# Usage
if should_use_tool("cursor-agent", config):
    # Tool is enabled AND available
    pass
```

**When to use:**
- User-facing features that can be disabled
- Beta/experimental tools
- Tools with licensing concerns

**Example from codebase:**
See `run_tests/tool_checking.py:96-107` for the `get_available_tools()` implementation.

## Error Handling During Execution

### Standard Exception Types

When executing external tools, handle these exceptions:

```python
import subprocess
from typing import Tuple, Optional

def run_tool_safely(
    command: list[str],
    timeout: int = 90
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Run external tool with comprehensive error handling.

    Returns:
        (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return True, result.stdout, None
        else:
            return False, result.stdout, result.stderr

    except FileNotFoundError:
        # Tool not installed
        return False, None, f"Tool not found: {command[0]}"

    except subprocess.TimeoutExpired:
        # Tool hung or too slow
        return False, None, f"Tool timed out after {timeout}s"

    except KeyboardInterrupt:
        # User interrupted
        return False, None, "Interrupted by user"

    except Exception as e:
        # Unexpected error
        return False, None, f"Unexpected error: {str(e)}"

# Usage
success, output, error = run_tool_safely(["gemini", "analyze", "code.py"], timeout=60)
if not success:
    logger.error(f"Tool failed: {error}")
    # Handle failure (fallback, skip, etc.)
```

**Example from codebase:**
See `run_tests/consultation.py:47-149` for the `consult_external_tool()` implementation.

### Exit Code Mapping

Map subprocess exit codes to meaningful error types:

| Exit Code | Meaning | Handling Strategy |
|-----------|---------|-------------------|
| 0 | Success | Parse output, use result |
| 1 | General error | Try fallback tool |
| 124 | Timeout | Increase timeout or skip |
| 130 | User interrupt | Stop cleanly, don't retry |
| Other | Unknown error | Log for debugging, try fallback |

## Auto-Routing System

The toolkit includes an auto-routing system that selects the best available tool for different failure types:

```python
# Failure type -> preferred tools (in priority order)
FAILURE_ROUTING = {
    "assertion": ["gemini", "codex", "cursor-agent"],
    "exception": ["codex", "gemini", "cursor-agent"],
    "import": ["cursor-agent", "codex", "gemini"],
    "fixture": ["cursor-agent", "gemini", "codex"],
    "timeout": ["gemini", "cursor-agent", "codex"],
    "flaky": ["gemini", "codex", "cursor-agent"],
    "multi-file": ["cursor-agent", "gemini", "codex"],
    "unclear-error": ["gemini", "codex", "cursor-agent"],
    "validation": ["codex", "gemini", "cursor-agent"],
}

def select_tool_for_failure(failure_type: str, available_tools: list[str]) -> Optional[str]:
    """Select best available tool for the given failure type."""
    preferred = FAILURE_ROUTING.get(failure_type, ["gemini", "codex", "cursor-agent"])

    for tool in preferred:
        if tool in available_tools:
            return tool

    return None  # No suitable tool available
```

**Example from codebase:**
See `run_tests/tool_checking.py:109-140` for the `get_tool_for_failure_type()` implementation.

## Configuration Management

### YAML-Based Configuration

Tools are configured in YAML with fallback to hardcoded defaults:

```yaml
tools:
  gemini:
    enabled: true
    command: "gemini"
    models: ["gemini-exp-1114", "gemini-2.0-flash-exp"]
    default_model: "gemini-exp-1114"
    timeout: 90

  codex:
    enabled: true
    command: "codex"
    models: ["claude-3.7-sonnet"]
    default_model: "claude-3.7-sonnet"
    timeout: 90

  cursor-agent:
    enabled: true
    command: "cursor-agent"
    timeout: 90
```

**Example from codebase:**
See `skills/run-tests/config.yaml` for the full configuration schema.

### Loading Configuration

```python
import yaml
from pathlib import Path
from typing import Dict, Any

def load_tool_config(config_path: Path) -> Dict[str, Any]:
    """Load tool configuration with fallback to defaults."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config.get("tools", {})
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        return get_default_tool_config()

def get_default_tool_config() -> Dict[str, Any]:
    """Hardcoded defaults if config file unavailable."""
    return {
        "gemini": {"enabled": True, "timeout": 90},
        "codex": {"enabled": True, "timeout": 90},
        "cursor-agent": {"enabled": True, "timeout": 90},
    }
```

**Example from codebase:**
See `run_tests/tool_checking.py:24-56` for the `load_config()` and `get_hardcoded_defaults()` implementations.

## Timeout Management

Different operations require different timeouts:

| Operation | Timeout | Rationale |
|-----------|---------|-----------|
| Tool discovery (`--version`) | 5s | Should be instant |
| Tool consultation (analysis) | 90s | Complex AI analysis |
| Plan review (multi-step) | 600s | Multiple AI calls |
| Documentation generation | 90s | Per-file analysis |

```python
# Tool detection - fast timeout
def detect_tools() -> list[str]:
    """Quick detection with 5s timeout."""
    available = []
    for tool in ["gemini", "codex", "cursor-agent"]:
        try:
            subprocess.run([tool, "--version"], timeout=5, capture_output=True)
            available.append(tool)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return available

# Tool consultation - longer timeout
def consult_tool(command: list[str]) -> str:
    """Run consultation with 90s timeout."""
    result = subprocess.run(command, timeout=90, capture_output=True, text=True)
    return result.stdout
```

## Best Practices

### 1. Check Early, Fail Fast

Check tool availability early in the workflow before investing time:

```python
# Good: Check before starting expensive work
available_tools = discover_tools()
if not available_tools:
    logger.error("No AI tools available, cannot proceed")
    return None

# Proceed with work knowing tools are available
results = process_with_tools(available_tools)
```

### 2. Graceful Degradation

Provide useful output even when tools are unavailable:

```python
# Good: Provide fallback behavior
tools = discover_tools()
if tools:
    analysis = consult_tool(tools[0], context)
else:
    analysis = "AI tools unavailable. Manual review recommended."
```

### 3. Respect Configuration

Always check both availability AND configuration:

```python
# Good: Check config before checking PATH
if config["tools"]["gemini"]["enabled"]:
    if shutil.which("gemini"):
        # Use gemini
        pass
```

### 4. Log Appropriately

Use appropriate log levels for different scenarios:

```python
# Tool discovery - debug level (expected to sometimes fail)
if not shutil.which("gemini"):
    logger.debug("gemini not found in PATH")

# Tool failure during execution - warning level
try:
    result = subprocess.run(["gemini", "..."], timeout=90)
except subprocess.TimeoutExpired:
    logger.warning("gemini timed out, trying fallback")

# No tools available when required - error level
if not available_tools:
    logger.error("No AI consultation tools available")
```

### 5. Test Both Paths

Always test code with and without tools available:

```python
# Test with tools available
def test_consultation_with_tools(mocker):
    mocker.patch("shutil.which", return_value="/usr/bin/gemini")
    result = consult("test")
    assert result.success

# Test with tools unavailable
def test_consultation_without_tools(mocker):
    mocker.patch("shutil.which", return_value=None)
    result = consult("test")
    assert result.fallback_used
```

## Common Patterns in Codebase

### Pattern 1: Discovery + Routing + Execution

```python
# 1. Discovery
available = discover_tools(config)

# 2. Routing
tool = get_tool_for_failure_type("assertion", available)

# 3. Execution
if tool:
    result = consult_external_tool(tool, context, timeout=90)
else:
    result = None  # Handle unavailability
```

**Used in:** `run_tests/consultation.py:47-149`

### Pattern 2: Config-Driven Tool Selection

```python
# Load config with fallback
config = load_config(config_path)

# Respect config settings
available = get_available_tools(config, filter_enabled=True)

# Use configured timeouts
timeout = config["tools"][tool]["timeout"]
```

**Used in:** `run_tests/tool_checking.py:24-107`

### Pattern 3: Multi-Tool Parallel Execution

```python
# Run multiple tools in parallel
tools = discover_tools()
with ThreadPoolExecutor(max_workers=len(tools)) as executor:
    futures = {
        executor.submit(consult_tool, tool, context): tool
        for tool in tools
    }

    results = {}
    for future in as_completed(futures):
        tool = futures[future]
        try:
            results[tool] = future.result(timeout=90)
        except Exception as e:
            logger.warning(f"{tool} failed: {e}")
```

**Used in:** `sdd_plan_review/reviewer.py:176-253`

## Related Documentation

- `run_tests/tool_checking.py` - Main tool checking utilities
- `run_tests/consultation.py` - Tool execution with error handling
- `skills/run-tests/config.yaml` - Tool configuration schema
- `code_doc/ai_consultation.py` - Documentation AI consultation
- `sdd_plan_review/reviewer.py` - Multi-tool parallel execution

## Migration Notes

When refactoring tool checking code:

1. **Extract common patterns** into `common/tool_utils.py`
2. **Standardize timeouts** across all tool invocations
3. **Unify configuration** handling with single source of truth
4. **Consistent error handling** with standard exception types
5. **Add tests** for both available and unavailable tool scenarios

## Summary

The tool availability checking patterns in the Claude SDD Toolkit follow these principles:

1. **Two-phase approach**: Discover before executing
2. **Configuration-driven**: Respect user settings and enabled/disabled flags
3. **Graceful degradation**: Provide fallback behavior when tools unavailable
4. **Comprehensive error handling**: Handle all subprocess failure modes
5. **Timeout management**: Use appropriate timeouts for different operations
6. **Auto-routing**: Select best tool for each failure type
7. **Logging**: Use appropriate log levels for different scenarios

These patterns ensure robust behavior across different environments while providing the best possible experience when AI consultation tools are available.
