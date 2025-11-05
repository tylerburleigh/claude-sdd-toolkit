# Command Building and Execution Patterns

## Overview

This document describes the patterns and best practices for building and executing commands to external AI CLI tools (gemini, codex, cursor-agent) in the Claude SDD Toolkit.

## Core Principles

1. **List-Based Commands**: Always use Python lists, never shell strings
2. **No Shell Injection**: Use `shell=False` (default) for subprocess calls
3. **Timeout Management**: Set appropriate timeouts for all operations
4. **Comprehensive Error Handling**: Handle all subprocess failure modes
5. **Output Capture**: Capture both stdout and stderr separately
6. **Result Structuring**: Return structured data, not raw strings

## Command Construction

### Pattern: List-Based Command Building

The safest way to build subprocess commands is using Python lists:

```python
# Good: List-based (shell-safe)
command = [tool_name, "--flag", argument]

# Bad: String-based (shell injection risk)
command = f"{tool_name} --flag {argument}"  # DON'T DO THIS
```

### Tool-Specific Command Patterns

Each AI CLI tool has its own command structure:

```python
def build_gemini_command(prompt: str, model: str = "gemini-exp-1114") -> list[str]:
    """Build gemini CLI command."""
    return [
        "gemini",
        "-m", model,
        "-p", prompt  # gemini uses -p flag for prompt
    ]

def build_codex_command(prompt: str, model: str = "claude-3.7-sonnet") -> list[str]:
    """Build codex CLI command."""
    return [
        "codex",
        "-m", model,
        prompt  # codex uses positional arg for prompt
    ]

def build_cursor_agent_command(prompt: str) -> list[str]:
    """Build cursor-agent CLI command."""
    return [
        "cursor-agent",
        "--print",  # Print to stdout instead of editing
        prompt
    ]
```

**Example from codebase:**
See `run_tests/consultation.py:47-149` for the `consult_external_tool()` implementation.

### Dynamic Command Building

Build commands dynamically based on configuration:

```python
def build_command(
    tool: str,
    prompt: str,
    config: dict,
    failure_type: Optional[str] = None
) -> list[str]:
    """Build command with config-based customization."""
    tool_config = config.get("tools", {}).get(tool, {})

    # Get base command
    base_cmd = tool_config.get("command", tool)

    # Get model (may vary by failure type)
    if failure_type and "failure_models" in tool_config:
        model = tool_config["failure_models"].get(failure_type)
    else:
        model = tool_config.get("default_model")

    # Build tool-specific command
    if tool == "gemini":
        cmd = [base_cmd, "-m", model, "-p", prompt]
    elif tool == "codex":
        cmd = [base_cmd, "-m", model, prompt]
    elif tool == "cursor-agent":
        cmd = [base_cmd, "--print", prompt]
    else:
        raise ValueError(f"Unknown tool: {tool}")

    return cmd
```

**Example from codebase:**
See `run_tests/tool_checking.py:109-140` for failure-type specific model selection.

## Prompt Construction

### Pattern: String List Assembly

Build prompts by assembling a list of strings, then joining:

```python
def build_prompt(
    instruction: str,
    context: str,
    additional_info: Optional[str] = None
) -> str:
    """Build prompt from components."""
    parts = [
        "# Task",
        instruction,
        "",
        "# Context",
        context,
    ]

    if additional_info:
        parts.extend(["", "# Additional Information", additional_info])

    return "\n".join(parts)

# Usage
prompt = build_prompt(
    instruction="Analyze this test failure",
    context=failure_output,
    additional_info=related_code
)
```

**Example from codebase:**
See `run_tests/consultation.py:151-238` for the `_build_test_consultation_prompt()` implementation.

### Embedding File References

Rather than passing file contents via stdin, embed references in prompts:

```python
def build_prompt_with_files(
    instruction: str,
    file_paths: list[str],
    read_contents: bool = False
) -> str:
    """Build prompt referencing or including files."""
    parts = [
        "# Task",
        instruction,
        "",
        "# Files",
    ]

    for path in file_paths:
        if read_contents:
            # Include file contents inline
            with open(path, 'r') as f:
                content = f.read()
            parts.append(f"## {path}")
            parts.append(f"```\n{content}\n```")
        else:
            # Just reference the path
            parts.append(f"- {path}")

    return "\n".join(parts)
```

**Example from codebase:**
See `code_doc/ai_consultation.py:113-209` for the `_create_prompt_for_phase()` implementation with file content inclusion.

## Input Sanitization

### Implicit Safety Through List Arguments

Using list-based subprocess calls provides automatic safety:

```python
# Safe: No shell interpretation
subprocess.run(["tool", user_input])  # user_input is passed as-is

# Unsafe: Shell injection possible
subprocess.run(f"tool {user_input}", shell=True)  # DON'T DO THIS
```

### Explicit Validation Patterns

Validate inputs before using them:

```python
from pathlib import Path

def validate_file_path(path: str) -> bool:
    """Validate file path before using."""
    p = Path(path)

    # Check existence
    if not p.exists():
        return False

    # Check type
    if not p.is_file():
        return False

    # Check readable
    if not os.access(p, os.R_OK):
        return False

    return True

# Usage
if validate_file_path(user_provided_path):
    with open(user_provided_path, 'r') as f:
        content = f.read()
```

**Example from codebase:**
See `code_doc/ai_consultation.py:37-76` for comprehensive file validation.

### Configuration Validation

Validate configuration data:

```python
import yaml

def load_validated_config(config_path: Path) -> dict:
    """Load and validate YAML config."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)  # Use safe_load, not load

        # Validate structure
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        if "tools" not in config:
            raise ValueError("Config missing 'tools' section")

        # Validate tool entries
        for tool, settings in config["tools"].items():
            if "enabled" not in settings:
                raise ValueError(f"Tool {tool} missing 'enabled' setting")

        return config

    except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
        logger.warning(f"Config validation failed: {e}")
        return get_default_config()
```

**Example from codebase:**
See `run_tests/tool_checking.py:24-56` for YAML config loading with fallback.

## Command Execution

### Standard Execution Pattern

Execute commands with comprehensive error handling:

```python
import subprocess
from typing import Tuple, Optional
from collections import namedtuple

# Result structure
ConsultationResponse = namedtuple(
    "ConsultationResponse",
    ["success", "output", "error", "tool", "duration"]
)

def execute_command(
    command: list[str],
    timeout: int = 90
) -> ConsultationResponse:
    """
    Execute command with full error handling.

    Args:
        command: Command as list of strings
        timeout: Timeout in seconds

    Returns:
        ConsultationResponse with structured results
    """
    import time

    start_time = time.time()
    tool = command[0]

    try:
        result = subprocess.run(
            command,
            capture_output=True,  # Capture stdout and stderr separately
            text=True,            # Decode as text, not bytes
            timeout=timeout,      # Prevent hanging
            check=False           # Don't raise on non-zero exit
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            return ConsultationResponse(
                success=True,
                output=result.stdout.strip(),
                error=None,
                tool=tool,
                duration=duration
            )
        else:
            return ConsultationResponse(
                success=False,
                output=result.stdout,
                error=result.stderr,
                tool=tool,
                duration=duration
            )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ConsultationResponse(
            success=False,
            output=None,
            error=f"Command timed out after {timeout}s",
            tool=tool,
            duration=duration
        )

    except FileNotFoundError:
        duration = time.time() - start_time
        return ConsultationResponse(
            success=False,
            output=None,
            error=f"Tool not found: {tool}",
            tool=tool,
            duration=duration
        )

    except Exception as e:
        duration = time.time() - start_time
        return ConsultationResponse(
            success=False,
            output=None,
            error=f"Unexpected error: {str(e)}",
            tool=tool,
            duration=duration
        )

# Usage
response = execute_command(["gemini", "-m", "gemini-exp-1114", "-p", "Analyze code"])
if response.success:
    print(f"Success! Output: {response.output}")
else:
    print(f"Failed: {response.error}")
```

**Example from codebase:**
See `run_tests/consultation.py:47-149` for the full `consult_external_tool()` implementation.

### Parallel Execution Pattern

Execute multiple commands concurrently:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

def execute_commands_parallel(
    commands: Dict[str, list[str]],  # tool_name -> command
    timeout: int = 90
) -> Dict[str, ConsultationResponse]:
    """
    Execute multiple commands in parallel.

    Args:
        commands: Dictionary mapping tool names to commands
        timeout: Timeout per command

    Returns:
        Dictionary mapping tool names to results
    """
    results = {}

    with ThreadPoolExecutor(max_workers=len(commands)) as executor:
        # Submit all commands
        future_to_tool = {
            executor.submit(execute_command, cmd, timeout): tool
            for tool, cmd in commands.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                result = future.result(timeout=timeout)
                results[tool] = result
            except Exception as e:
                logger.error(f"Tool {tool} raised exception: {e}")
                results[tool] = ConsultationResponse(
                    success=False,
                    output=None,
                    error=str(e),
                    tool=tool,
                    duration=0
                )

    return results

# Usage
commands = {
    "gemini": ["gemini", "-m", "gemini-exp-1114", "-p", prompt],
    "codex": ["codex", "-m", "claude-3.7-sonnet", prompt],
    "cursor-agent": ["cursor-agent", "--print", prompt]
}

results = execute_commands_parallel(commands, timeout=90)
for tool, result in results.items():
    print(f"{tool}: {'success' if result.success else 'failed'}")
```

**Example from codebase:**
See `sdd_plan_review/reviewer.py:176-253` for parallel review orchestration.

## Output Processing

### Pattern: JSON Wrapper Extraction

Some tools wrap output in JSON, some don't:

```python
import json
import re

def extract_output(raw_output: str, tool: str) -> str:
    """
    Extract actual output from tool response.

    Some tools wrap output in JSON, others return plain text.
    """
    if tool == "gemini":
        # gemini wraps in JSON: {"response": "actual content"}
        try:
            data = json.loads(raw_output)
            return data.get("response", raw_output)
        except json.JSONDecodeError:
            # Fallback to raw output if not valid JSON
            return raw_output
    else:
        # Other tools return plain text
        return raw_output

# Usage
response = execute_command(command)
if response.success:
    output = extract_output(response.output, response.tool)
```

**Example from codebase:**
See `run_tests/consultation.py:47-149` for gemini JSON extraction with fallback.

### Pattern: Multi-Response Collection

Collect responses from multiple tools:

```python
def collect_responses(
    results: Dict[str, ConsultationResponse]
) -> Dict[str, any]:
    """
    Process multiple tool responses into structured format.

    Returns:
        Dictionary with raw_responses, parsed_responses, failures
    """
    raw_responses = {}
    parsed_responses = {}
    failures = []

    for tool, response in results.items():
        if response.success:
            # Extract and store output
            raw_responses[tool] = response.output
            parsed_responses[tool] = extract_output(response.output, tool)
        else:
            # Track failure
            failures.append({
                "tool": tool,
                "error": response.error,
                "duration": response.duration
            })

    return {
        "raw_responses": raw_responses,
        "parsed_responses": parsed_responses,
        "failures": failures,
        "success_count": len(parsed_responses),
        "failure_count": len(failures)
    }
```

**Example from codebase:**
See `sdd_plan_review/reviewer.py:176-253` for multi-response collection.

### Pattern: AI-Based Synthesis

Use AI to synthesize multiple responses into consensus:

```python
def synthesize_responses(
    responses: Dict[str, str],
    original_prompt: str
) -> str:
    """
    Use AI to synthesize multiple responses into consensus.

    Args:
        responses: Dictionary mapping tool names to their outputs
        original_prompt: The original prompt sent to tools

    Returns:
        Synthesized consensus analysis
    """
    # Build synthesis prompt
    synthesis_parts = [
        "# Task",
        "Analyze these multiple AI responses and synthesize a consensus view.",
        "",
        "# Original Prompt",
        original_prompt,
        "",
        "# Responses",
    ]

    for tool, response in responses.items():
        synthesis_parts.append(f"## {tool}")
        synthesis_parts.append(response)
        synthesis_parts.append("")

    synthesis_parts.extend([
        "# Instructions",
        "Synthesize these responses into a consensus analysis.",
        "Highlight areas of agreement and note any disagreements.",
        "Provide confidence indicators where appropriate."
    ])

    synthesis_prompt = "\n".join(synthesis_parts)

    # Call gemini for synthesis
    command = ["gemini", "-m", "gemini-exp-1114", "-p", synthesis_prompt]
    result = execute_command(command, timeout=120)  # Longer timeout for synthesis

    if result.success:
        return extract_output(result.output, "gemini")
    else:
        # Fallback: return concatenated responses
        return "\n\n---\n\n".join(
            f"**{tool}:**\n{resp}" for tool, resp in responses.items()
        )

# Usage
responses = {
    "gemini": "Analysis from gemini...",
    "codex": "Analysis from codex...",
    "cursor-agent": "Analysis from cursor-agent..."
}

consensus = synthesize_responses(responses, original_prompt)
```

**Example from codebase:**
See `sdd_plan_review/synthesis.py:20-87` for the `synthesize_reviews()` implementation.

## Result Structures

### Single Tool Response

Use named tuples for single responses:

```python
from collections import namedtuple

ConsultationResponse = namedtuple(
    "ConsultationResponse",
    ["success", "output", "error", "tool", "duration"]
)

# Create response
response = ConsultationResponse(
    success=True,
    output="Analysis complete",
    error=None,
    tool="gemini",
    duration=2.5
)

# Access fields
if response.success:
    print(response.output)
```

### Multi-Tool Response

Use dictionaries for complex multi-tool results:

```python
def create_multi_tool_result(
    raw_responses: Dict[str, str],
    parsed_responses: Dict[str, str],
    failures: List[dict],
    synthesis: Optional[str] = None
) -> dict:
    """Create structured multi-tool result."""
    return {
        "raw_responses": raw_responses,
        "parsed_responses": parsed_responses,
        "failures": failures,
        "success_count": len(parsed_responses),
        "failure_count": len(failures),
        "synthesis": synthesis,
        "tools_used": list(parsed_responses.keys()),
        "timestamp": datetime.now().isoformat()
    }
```

## Configuration-Driven Execution

### Load Configuration with Defaults

```python
import yaml
from pathlib import Path

def load_execution_config(config_path: Path) -> dict:
    """Load execution configuration with fallback."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config
    except (FileNotFoundError, yaml.YAMLError):
        return get_default_execution_config()

def get_default_execution_config() -> dict:
    """Hardcoded default configuration."""
    return {
        "tools": {
            "gemini": {
                "enabled": True,
                "command": "gemini",
                "default_model": "gemini-exp-1114",
                "timeout": 90,
                "failure_models": {
                    "assertion": "gemini-exp-1114",
                    "exception": "gemini-exp-1114"
                }
            },
            "codex": {
                "enabled": True,
                "command": "codex",
                "default_model": "claude-3.7-sonnet",
                "timeout": 90
            },
            "cursor-agent": {
                "enabled": True,
                "command": "cursor-agent",
                "timeout": 90
            }
        },
        "parallel_execution": True,
        "synthesis_enabled": True
    }
```

### Execute Based on Configuration

```python
def execute_with_config(
    prompt: str,
    config: dict,
    failure_type: Optional[str] = None
) -> dict:
    """Execute commands based on configuration."""
    # Get available tools
    available_tools = [
        tool for tool, settings in config["tools"].items()
        if settings.get("enabled", True) and shutil.which(settings.get("command", tool))
    ]

    if not available_tools:
        return {"error": "No tools available"}

    # Build commands
    commands = {}
    for tool in available_tools:
        tool_config = config["tools"][tool]

        # Select model (may vary by failure type)
        if failure_type and "failure_models" in tool_config:
            model = tool_config["failure_models"].get(
                failure_type,
                tool_config["default_model"]
            )
        else:
            model = tool_config.get("default_model")

        # Build command
        if tool == "gemini":
            cmd = [tool, "-m", model, "-p", prompt]
        elif tool == "codex":
            cmd = [tool, "-m", model, prompt]
        else:
            cmd = [tool, "--print", prompt]

        commands[tool] = cmd

    # Execute (parallel or serial based on config)
    if config.get("parallel_execution", True) and len(commands) > 1:
        results = execute_commands_parallel(
            commands,
            timeout=config["tools"][tool]["timeout"]
        )
    else:
        results = {
            tool: execute_command(cmd, timeout=config["tools"][tool]["timeout"])
            for tool, cmd in commands.items()
        }

    # Collect responses
    collected = collect_responses(results)

    # Synthesize if enabled
    if config.get("synthesis_enabled") and len(collected["parsed_responses"]) > 1:
        collected["synthesis"] = synthesize_responses(
            collected["parsed_responses"],
            prompt
        )

    return collected
```

## Timeout Management

### Context-Appropriate Timeouts

Different operations need different timeouts:

```python
# Tool detection - should be instant
DETECTION_TIMEOUT = 5  # seconds

# Tool consultation - complex analysis
CONSULTATION_TIMEOUT = 90  # seconds

# Multi-tool review - parallel execution
REVIEW_TIMEOUT = 600  # seconds (10 minutes)

# Synthesis - additional AI processing
SYNTHESIS_TIMEOUT = 120  # seconds

def get_timeout_for_operation(operation: str) -> int:
    """Get appropriate timeout for operation type."""
    timeouts = {
        "detection": 5,
        "consultation": 90,
        "review": 600,
        "synthesis": 120,
    }
    return timeouts.get(operation, 90)  # Default 90s
```

## Best Practices

### 1. Always Use List-Based Commands

```python
# Good: Shell-safe
command = ["tool", "--flag", user_input]

# Bad: Shell injection risk
command = f"tool --flag {user_input}"
```

### 2. Set Appropriate Timeouts

```python
# Good: Timeout specified
subprocess.run(command, timeout=90)

# Bad: No timeout (can hang forever)
subprocess.run(command)
```

### 3. Capture Output Separately

```python
# Good: Separate stdout and stderr
result = subprocess.run(command, capture_output=True, text=True)
output = result.stdout
errors = result.stderr

# Bad: Combined output (harder to debug)
result = subprocess.run(command, capture_output=True, stderr=subprocess.STDOUT)
```

### 4. Return Structured Data

```python
# Good: Structured response
return ConsultationResponse(
    success=True,
    output=result.stdout,
    error=None,
    tool=tool,
    duration=2.5
)

# Bad: Raw data (hard to handle)
return result.stdout if result.returncode == 0 else None
```

### 5. Handle All Error Cases

```python
# Good: Comprehensive error handling
try:
    result = subprocess.run(command, timeout=90, capture_output=True, check=False)
    if result.returncode == 0:
        return handle_success(result)
    else:
        return handle_failure(result)
except subprocess.TimeoutExpired:
    return handle_timeout()
except FileNotFoundError:
    return handle_missing_tool()
except Exception as e:
    return handle_unexpected(e)

# Bad: Minimal error handling
result = subprocess.run(command)
return result.stdout
```

### 6. Test Error Paths

```python
# Test successful execution
def test_execute_success(mocker):
    mocker.patch("subprocess.run", return_value=MockResult(returncode=0, stdout="ok"))
    response = execute_command(["tool", "arg"])
    assert response.success

# Test timeout
def test_execute_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 90))
    response = execute_command(["tool", "arg"])
    assert not response.success
    assert "timed out" in response.error

# Test missing tool
def test_execute_missing_tool(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError())
    response = execute_command(["tool", "arg"])
    assert not response.success
    assert "not found" in response.error
```

## Common Patterns Summary

### Single Tool Consultation

```python
# 1. Build command
command = build_command(tool, prompt, config)

# 2. Execute with timeout
response = execute_command(command, timeout=90)

# 3. Process result
if response.success:
    output = extract_output(response.output, tool)
    return output
else:
    logger.error(f"Tool failed: {response.error}")
    return None
```

### Multi-Tool Parallel Consultation

```python
# 1. Build commands for all tools
commands = {
    tool: build_command(tool, prompt, config)
    for tool in available_tools
}

# 2. Execute in parallel
results = execute_commands_parallel(commands, timeout=90)

# 3. Collect responses
collected = collect_responses(results)

# 4. Synthesize consensus
if len(collected["parsed_responses"]) > 1:
    consensus = synthesize_responses(
        collected["parsed_responses"],
        prompt
    )
    collected["synthesis"] = consensus

return collected
```

### Configuration-Driven Execution

```python
# 1. Load config
config = load_execution_config(config_path)

# 2. Discover available tools
available = discover_tools(config)

# 3. Execute based on config
result = execute_with_config(prompt, config, failure_type)

return result
```

## Related Documentation

- `run_tests/consultation.py` - Single/multi-agent consultation
- `code_doc/ai_consultation.py` - Documentation generation
- `sdd_plan_review/reviewer.py` - Parallel review orchestration
- `sdd_plan_review/synthesis.py` - Response synthesis
- `run_tests/tool_checking.py` - Tool discovery and config
- `TOOL_AVAILABILITY_PATTERNS.md` - Tool checking patterns

## Summary

The command building and execution patterns follow these principles:

1. **List-based commands**: Shell-safe, no injection risk
2. **Comprehensive error handling**: All subprocess failure modes covered
3. **Structured results**: Named tuples and dictionaries, not raw strings
4. **Timeout management**: Context-appropriate timeouts for all operations
5. **Output processing**: JSON extraction, multi-response collection, AI synthesis
6. **Configuration-driven**: YAML-based with sensible defaults
7. **Parallel execution**: ThreadPoolExecutor for concurrent tool calls
8. **Input validation**: Path checking, config validation, safe loading

These patterns ensure robust, secure, and maintainable execution of external AI CLI tools across different environments.
