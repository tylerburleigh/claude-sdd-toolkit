# AI Tools API Reference

Comprehensive API documentation for `claude_skills.common.ai_tools` module.

## Overview

The `ai_tools` module provides standardized interfaces for interacting with external AI CLI tools (gemini, codex, cursor-agent). It offers type-safe dataclasses, a unified API, and comprehensive error handling.

**Key Features:**
- Unified interface for multiple AI tools
- Type-safe response dataclasses
- Parallel execution support
- Comprehensive error handling
- Tool availability detection
- Configurable timeouts

**Supported Tools:**
- **gemini** - Google Gemini CLI
- **codex** - Anthropic Codex CLI
- **cursor-agent** - Cursor AI agent

## Table of Contents

- [Enums](#enums)
  - [ToolStatus](#toolstatus)
- [Data Classes](#data-classes)
  - [ToolResponse](#toolresponse)
  - [MultiToolResponse](#multitoolresponse)
- [Functions](#functions)
  - [Tool Availability](#tool-availability)
  - [Tool Execution](#tool-execution)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Enums

### ToolStatus

```python
class ToolStatus(Enum):
    """Status of AI tool execution."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_OUTPUT = "invalid_output"
    ERROR = "error"
```

Represents the execution status of an AI tool consultation.

**Values:**

| Value | Description |
|-------|-------------|
| `SUCCESS` | Tool executed successfully and returned output |
| `TIMEOUT` | Tool execution exceeded the timeout limit |
| `NOT_FOUND` | Tool executable not found in PATH |
| `INVALID_OUTPUT` | Tool returned malformed or invalid output |
| `ERROR` | General error during execution (non-zero exit code, exceptions) |

**Usage:**
```python
from claude_skills.common.ai_tools import ToolStatus

if response.status == ToolStatus.SUCCESS:
    print("Tool executed successfully")
elif response.status == ToolStatus.TIMEOUT:
    print("Tool timed out")
```

---

## Data Classes

### ToolResponse

```python
@dataclass(frozen=True)
class ToolResponse:
    """Standardized response from AI tool consultation."""
    tool: str
    status: ToolStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: Optional[str] = None
    prompt: Optional[str] = None
    exit_code: Optional[int] = None
    metadata: dict = field(default_factory=dict)
```

Core response type for all AI tool interactions. Immutable dataclass containing execution results and metadata.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `tool` | `str` | Name of the tool (gemini, codex, cursor-agent) |
| `status` | `ToolStatus` | Execution status enum |
| `output` | `str` | Raw output from tool (stdout) |
| `error` | `Optional[str]` | Error message if any (stderr or exception message) |
| `duration` | `float` | Execution time in seconds |
| `timestamp` | `str` | ISO format timestamp when consultation started |
| `model` | `Optional[str]` | Model used by the tool (if applicable) |
| `prompt` | `Optional[str]` | The prompt sent to the tool (optional, for debugging) |
| `exit_code` | `Optional[int]` | Process exit code (None if didn't run) |
| `metadata` | `dict` | Additional tool-specific metadata |

**Properties:**

#### success

```python
@property
def success(self) -> bool:
    """Check if tool execution was successful."""
```

Returns `True` if status is `ToolStatus.SUCCESS`.

**Example:**
```python
if response.success:
    print(f"Output: {response.output}")
```

#### failed

```python
@property
def failed(self) -> bool:
    """Check if tool execution failed."""
```

Returns `True` if status is not `ToolStatus.SUCCESS`.

**Example:**
```python
if response.failed:
    print(f"Error: {response.error}")
```

**Methods:**

#### to_dict()

```python
def to_dict(self) -> dict:
    """Convert to dictionary for serialization."""
```

Converts the ToolResponse to a dictionary suitable for JSON serialization.

**Returns:** Dictionary with all attributes, status converted to string value.

**Example:**
```python
response_dict = response.to_dict()
json.dump(response_dict, file)
```

#### from_dict()

```python
@classmethod
def from_dict(cls, data: dict) -> "ToolResponse":
    """Create from dictionary."""
```

Creates a ToolResponse instance from a dictionary.

**Parameters:**
- `data` (dict): Dictionary with tool response data

**Returns:** `ToolResponse` instance

**Raises:** `ValueError` if status value is invalid

**Example:**
```python
data = json.load(file)
response = ToolResponse.from_dict(data)
```

---

### MultiToolResponse

```python
@dataclass(frozen=True)
class MultiToolResponse:
    """Response from multiple tool consultations run in parallel."""
    responses: dict[str, ToolResponse]
    synthesis: Optional[str] = None
    total_duration: float = 0.0
    max_duration: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_type: Optional[str] = None
```

Response container for parallel multi-tool consultations. Immutable dataclass containing individual tool responses and aggregated statistics.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `responses` | `dict[str, ToolResponse]` | Dictionary mapping tool names to their responses |
| `synthesis` | `Optional[str]` | Optional synthesis/consensus from all responses |
| `total_duration` | `float` | Total wall-clock time (parallel execution) |
| `max_duration` | `float` | Longest individual tool duration |
| `success_count` | `int` | Number of successful tool calls |
| `failure_count` | `int` | Number of failed tool calls |
| `timestamp` | `str` | ISO format timestamp when consultation started |
| `failure_type` | `Optional[str]` | Optional failure type that triggered consultation |

**Properties:**

#### success

```python
@property
def success(self) -> bool:
    """Check if at least one tool succeeded."""
```

Returns `True` if `success_count > 0`.

#### all_failed

```python
@property
def all_failed(self) -> bool:
    """Check if all tools failed."""
```

Returns `True` if `success_count == 0`.

#### all_succeeded

```python
@property
def all_succeeded(self) -> bool:
    """Check if all tools succeeded."""
```

Returns `True` if `failure_count == 0`.

**Methods:**

#### get_successful_responses()

```python
def get_successful_responses(self) -> dict[str, ToolResponse]:
    """Get only successful tool responses."""
```

Filters and returns only the responses with `success == True`.

**Returns:** Dictionary mapping tool names to successful responses

**Example:**
```python
successful = multi_response.get_successful_responses()
for tool, response in successful.items():
    print(f"{tool}: {response.output}")
```

#### get_failed_responses()

```python
def get_failed_responses(self) -> dict[str, ToolResponse]:
    """Get only failed tool responses."""
```

Filters and returns only the responses with `failed == True`.

**Returns:** Dictionary mapping tool names to failed responses

**Example:**
```python
failed = multi_response.get_failed_responses()
for tool, response in failed.items():
    print(f"{tool} failed: {response.error}")
```

#### to_dict()

```python
def to_dict(self) -> dict:
    """Convert to dictionary for serialization."""
```

Converts the MultiToolResponse to a dictionary, recursively converting nested ToolResponse objects.

**Returns:** Dictionary suitable for JSON serialization

#### from_dict()

```python
@classmethod
def from_dict(cls, data: dict) -> "MultiToolResponse":
    """Create from dictionary."""
```

Creates a MultiToolResponse instance from a dictionary, reconstructing nested ToolResponse objects.

**Parameters:**
- `data` (dict): Dictionary with multi-tool response data

**Returns:** `MultiToolResponse` instance

---

## Functions

### Tool Availability

#### check_tool_available()

```python
def check_tool_available(
    tool: str,
    *,
    check_version: bool = False,
    timeout: int = 5
) -> bool:
```

Check if a tool is available and optionally verify it's working.

Uses `shutil.which()` for fast PATH lookup. Can optionally verify tool responds to `--version` flag.

**Parameters:**
- `tool` (str): Tool name to check (e.g., "gemini", "codex", "cursor-agent")
- `check_version` (bool, optional): If True, verify tool responds to --version. Default: False
- `timeout` (int, optional): Timeout in seconds for version check. Default: 5

**Returns:** `True` if tool is available (and working if `check_version=True`)

**Example:**
```python
# Quick PATH check
if check_tool_available("gemini"):
    print("Gemini is available")

# Verify tool is working
if check_tool_available("gemini", check_version=True):
    print("Gemini is available and responding")
```

**Performance:**
- PATH check: < 1ms
- With version check: ~10-500ms depending on tool

---

#### detect_available_tools()

```python
def detect_available_tools(
    tools: Optional[list[str]] = None,
    *,
    check_version: bool = False
) -> list[str]:
```

Detect which AI tools are available in PATH.

**Parameters:**
- `tools` (Optional[list[str]]): Optional list of tool names to check. If None, checks default tools: ["gemini", "codex", "cursor-agent"]
- `check_version` (bool, optional): If True, verify each tool responds to --version. Default: False

**Returns:** List of available tool names (empty list if none found)

**Example:**
```python
# Check default tools
available = detect_available_tools()
print(f"Available tools: {available}")
# Output: ['gemini', 'codex']

# Check specific tools
available = detect_available_tools(["gemini", "custom-tool"])
# Output: ['gemini']

# Verify tools are working
available = detect_available_tools(check_version=True)
# Output: ['gemini']
```

**Use Cases:**
- Startup checks to determine available tools
- Fallback logic when preferred tool unavailable
- User feedback about missing dependencies

---

#### build_tool_command()

```python
def build_tool_command(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None
) -> list[str]:
```

Build command list for tool execution with tool-specific patterns.

**Tool-Specific Command Patterns:**
- **gemini**: `gemini -m <model> -p <prompt>`
- **codex**: `codex -m <model> <prompt>`
- **cursor-agent**: `cursor-agent --print <prompt>` (no model selection)

**Parameters:**
- `tool` (str): Tool name ("gemini", "codex", "cursor-agent")
- `prompt` (str): The prompt to include in command
- `model` (Optional[str]): Optional model override

**Returns:** Command as list of strings (shell-safe)

**Raises:** `ValueError` if tool is unknown

**Example:**
```python
# Gemini with model
cmd = build_tool_command("gemini", "Analyze code", model="gemini-exp-1114")
# Returns: ['gemini', '-m', 'gemini-exp-1114', '-p', 'Analyze code']

# Codex with model
cmd = build_tool_command("codex", "Fix bug", model="claude-3.7-sonnet")
# Returns: ['codex', '-m', 'claude-3.7-sonnet', 'Fix bug']

# Cursor without model (not supported)
cmd = build_tool_command("cursor-agent", "Review code")
# Returns: ['cursor-agent', '--print', 'Review code']

# Unknown tool
try:
    cmd = build_tool_command("unknown", "test")
except ValueError as e:
    print(e)  # "Unknown tool: unknown. Supported: gemini, codex, cursor-agent"
```

**Security:**
- Returns list (not string) to avoid shell injection
- Safe for subprocess.run() without shell=True

---

### Tool Execution

#### execute_tool()

```python
def execute_tool(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    timeout: int = 90
) -> ToolResponse:
```

Execute AI tool with a prompt and return structured response.

Handles all subprocess error modes: timeout, not found, invalid output, and general errors. Always returns a ToolResponse with appropriate status.

**Parameters:**
- `tool` (str): Tool name ("gemini", "codex", "cursor-agent")
- `prompt` (str): The prompt to send to the tool
- `model` (Optional[str]): Optional model override
- `timeout` (int, optional): Timeout in seconds. Default: 90

**Returns:** `ToolResponse` with execution results and metadata

**Error Handling:**

The function never raises exceptions. All errors are captured in the ToolResponse:

| Error Type | ToolResponse.status | ToolResponse.error |
|------------|---------------------|-------------------|
| Timeout | `TIMEOUT` | "Tool timed out after Ns" |
| Not found | `NOT_FOUND` | "Tool 'X' not found in PATH" |
| Non-zero exit | `ERROR` | stderr or "Tool exited with code N" |
| Unknown tool | `ERROR` | ValueError message |
| Other exceptions | `ERROR` | "Unexpected error: ..." |

**Example:**
```python
# Basic execution
response = execute_tool("gemini", "Analyze this code: def foo(): pass")

if response.success:
    print(f"Analysis: {response.output}")
    print(f"Took {response.duration:.2f}s")
else:
    print(f"Failed ({response.status.value}): {response.error}")

# With model and timeout
response = execute_tool(
    "codex",
    "Review for security issues",
    model="claude-3.7-sonnet",
    timeout=60
)

# Check specific status
if response.status == ToolStatus.TIMEOUT:
    print("Tool took too long, consider increasing timeout")
elif response.status == ToolStatus.NOT_FOUND:
    print("Tool not installed, please install it first")
```

**Performance Considerations:**
- Average execution time: 1-30 seconds (depends on prompt complexity and model)
- Timeout should be set based on expected prompt complexity
- Use parallel execution for multiple tools

---

#### execute_tools_parallel()

```python
def execute_tools_parallel(
    tools: list[str],
    prompt: str,
    *,
    models: Optional[dict[str, str]] = None,
    timeout: int = 90
) -> MultiToolResponse:
```

Execute multiple AI tools in parallel with the same prompt.

Uses `ThreadPoolExecutor` to run tools concurrently. Returns as soon as each tool completes (doesn't wait for slowest).

**Parameters:**
- `tools` (list[str]): List of tool names to execute
- `prompt` (str): The prompt to send to all tools
- `models` (Optional[dict[str, str]]): Optional dict mapping tool names to models
- `timeout` (int, optional): Timeout per tool in seconds. Default: 90

**Returns:** `MultiToolResponse` with all results and aggregated statistics

**Example:**
```python
# Execute multiple tools
response = execute_tools_parallel(
    tools=["gemini", "codex", "cursor-agent"],
    prompt="Analyze this function for bugs"
)

print(f"Success rate: {response.success_count}/{len(response.responses)}")
print(f"Total time: {response.total_duration:.2f}s")
print(f"Longest tool: {response.max_duration:.2f}s")

# Get successful responses
for tool, resp in response.get_successful_responses().items():
    print(f"\n{tool} says:")
    print(resp.output)

# Get failed responses
for tool, resp in response.get_failed_responses().items():
    print(f"\n{tool} failed: {resp.error}")

# With custom models
response = execute_tools_parallel(
    tools=["gemini", "codex"],
    prompt="Review security",
    models={
        "gemini": "gemini-exp-1114",
        "codex": "claude-3.7-sonnet"
    },
    timeout=60
)
```

**Performance Benefits:**
- 3 tools @ 10s each: 10s parallel vs 30s sequential (3x faster)
- Returns as soon as each tool completes
- Timeout applies per tool, not total

**Edge Cases:**
```python
# Empty tool list
response = execute_tools_parallel(tools=[], prompt="test")
assert response.success_count == 0
assert len(response.responses) == 0

# All tools fail
response = execute_tools_parallel(
    tools=["nonexistent1", "nonexistent2"],
    prompt="test"
)
assert response.all_failed
assert response.success_count == 0
```

---

## Usage Examples

### Basic Single Tool Execution

```python
from claude_skills.common.ai_tools import execute_tool

# Execute a single tool
response = execute_tool("gemini", "What are best practices for error handling?")

if response.success:
    print("Response:", response.output)
else:
    print(f"Error: {response.error}")
    print(f"Status: {response.status.value}")
```

### Checking Tool Availability Before Use

```python
from claude_skills.common.ai_tools import check_tool_available, execute_tool

tool = "gemini"

if check_tool_available(tool):
    response = execute_tool(tool, "Analyze code")
    print(response.output)
else:
    print(f"{tool} not available, please install it")
```

### Parallel Multi-Tool Consultation

```python
from claude_skills.common.ai_tools import execute_tools_parallel, detect_available_tools

# Detect available tools
available = detect_available_tools()

if not available:
    print("No AI tools available")
    exit(1)

# Execute all available tools
response = execute_tools_parallel(
    tools=available,
    prompt="Review this code for potential issues"
)

# Analyze results
print(f"Consulted {len(response.responses)} tools")
print(f"Success: {response.success_count}, Failed: {response.failure_count}")

# Show successful responses
for tool, resp in response.get_successful_responses().items():
    print(f"\n=== {tool.upper()} ===")
    print(resp.output)
```

### Custom Model Selection

```python
from claude_skills.common.ai_tools import execute_tools_parallel

response = execute_tools_parallel(
    tools=["gemini", "codex"],
    prompt="Explain this algorithm",
    models={
        "gemini": "gemini-exp-1114",  # Latest experimental model
        "codex": "claude-3.7-sonnet"   # Sonnet for code analysis
    }
)
```

### Handling Timeouts

```python
from claude_skills.common.ai_tools import execute_tool, ToolStatus

# Complex prompt that may take time
response = execute_tool(
    "gemini",
    "Analyze this 500-line codebase...",
    timeout=120  # 2 minutes
)

if response.status == ToolStatus.TIMEOUT:
    print("Tool took too long. Try:")
    print("1. Increase timeout")
    print("2. Simplify prompt")
    print("3. Break into smaller prompts")
```

### Serialization and Persistence

```python
import json
from claude_skills.common.ai_tools import execute_tool, ToolResponse

# Execute and serialize
response = execute_tool("gemini", "Analyze code")
response_dict = response.to_dict()

# Save to file
with open("consultation.json", "w") as f:
    json.dump(response_dict, f, indent=2)

# Load and reconstruct
with open("consultation.json", "r") as f:
    data = json.load(f)

restored = ToolResponse.from_dict(data)
assert restored.tool == response.tool
assert restored.output == response.output
```

### Fallback Logic

```python
from claude_skills.common.ai_tools import detect_available_tools, execute_tool

# Preferred tools in order
preferred = ["gemini", "codex", "cursor-agent"]

# Find first available
available = detect_available_tools(preferred)

if available:
    tool = available[0]  # Use first available
    response = execute_tool(tool, "Analyze code")
    print(f"Used {tool}: {response.output}")
else:
    print("No AI tools available, falling back to manual analysis")
```

---

## Error Handling

### Design Philosophy

The ai_tools module follows a **no-exceptions** design for tool execution:
- All errors are captured in ToolResponse/MultiToolResponse
- Functions return structured error information instead of raising exceptions
- Callers check `.success` or `.status` rather than using try/except

### Error Categories

#### 1. Tool Not Found

**Cause:** Tool executable not in PATH

**Detection:**
```python
if response.status == ToolStatus.NOT_FOUND:
    print(f"Install {response.tool} first")
```

**Solutions:**
- Install the tool
- Check PATH configuration
- Use `detect_available_tools()` before execution

#### 2. Timeout

**Cause:** Tool exceeded timeout limit

**Detection:**
```python
if response.status == ToolStatus.TIMEOUT:
    print(f"Timed out after {response.duration:.1f}s")
```

**Solutions:**
- Increase timeout for complex prompts
- Simplify prompt
- Break into smaller consultations
- Check if tool/API is responding slowly

#### 3. Execution Error

**Cause:** Tool returned non-zero exit code

**Detection:**
```python
if response.status == ToolStatus.ERROR:
    print(f"Exit code: {response.exit_code}")
    print(f"Error: {response.error}")
```

**Common Causes:**
- API key not set
- Invalid model name
- Network issues
- Tool-specific configuration errors

**Solutions:**
- Check environment variables (API keys)
- Verify model names
- Check network connectivity
- Review tool-specific logs

#### 4. Invalid Output

**Cause:** Tool returned malformed output

**Detection:**
```python
if response.status == ToolStatus.INVALID_OUTPUT:
    print("Tool returned invalid output")
```

**Solutions:**
- Check tool version compatibility
- Verify tool is properly installed
- Review raw output for debugging

### Error Handling Patterns

#### Pattern 1: Graceful Degradation

```python
response = execute_tool("gemini", prompt)

if response.success:
    return response.output
else:
    # Log error and continue with fallback
    logger.warning(f"Tool failed: {response.error}")
    return fallback_analysis()
```

#### Pattern 2: Retry Logic

```python
def execute_with_retry(tool, prompt, max_retries=2):
    for attempt in range(max_retries):
        response = execute_tool(tool, prompt)

        if response.success:
            return response

        if response.status == ToolStatus.TIMEOUT:
            # Don't retry timeouts
            break

        if attempt < max_retries - 1:
            time.sleep(1)  # Brief delay before retry

    return response  # Return last attempt
```

#### Pattern 3: Multi-Tool Redundancy

```python
response = execute_tools_parallel(["gemini", "codex", "cursor-agent"], prompt)

if response.success_count > 0:
    # At least one tool succeeded
    successful = response.get_successful_responses()
    return list(successful.values())[0].output
else:
    # All tools failed
    raise RuntimeError("All AI tools failed")
```

---

## Best Practices

### 1. Tool Availability Checks

**Always check availability before critical operations:**

```python
# Good
if check_tool_available("gemini"):
    response = execute_tool("gemini", prompt)
else:
    # Handle missing tool
    use_fallback()

# Better - detect all at startup
available_tools = detect_available_tools()
if not available_tools:
    print("Warning: No AI tools available")
```

### 2. Timeout Configuration

**Set timeouts based on prompt complexity:**

```python
# Quick questions - short timeout
response = execute_tool("gemini", "What is X?", timeout=30)

# Complex analysis - longer timeout
response = execute_tool("gemini", "Analyze 500 lines...", timeout=180)

# Default (90s) is reasonable for most cases
response = execute_tool("gemini", prompt)
```

### 3. Parallel Execution for Speed

**Use parallel execution when consulting multiple tools:**

```python
# Slow - sequential (30s total if each takes 10s)
gemini_resp = execute_tool("gemini", prompt)
codex_resp = execute_tool("codex", prompt)
cursor_resp = execute_tool("cursor-agent", prompt)

# Fast - parallel (10s total, saves 20s)
response = execute_tools_parallel(
    ["gemini", "codex", "cursor-agent"],
    prompt
)
```

### 4. Response Checking

**Always check response status:**

```python
# Bad - assumes success
output = execute_tool("gemini", prompt).output  # May be empty on error!

# Good - check success
response = execute_tool("gemini", prompt)
if response.success:
    output = response.output
else:
    handle_error(response)
```

### 5. Model Selection

**Use appropriate models for the task:**

```python
models = {
    "gemini": "gemini-exp-1114",      # Latest experimental
    "codex": "claude-3.7-sonnet"      # Good for code analysis
}

response = execute_tools_parallel(tools, prompt, models=models)
```

### 6. Error Logging

**Log failures for debugging:**

```python
import logging

response = execute_tool("gemini", prompt)

if response.failed:
    logging.error(
        f"Tool execution failed",
        extra={
            "tool": response.tool,
            "status": response.status.value,
            "error": response.error,
            "duration": response.duration,
            "prompt_length": len(response.prompt or "")
        }
    )
```

### 7. Prompt Design

**Design prompts for clarity and specificity:**

```python
# Vague
response = execute_tool("gemini", "check this")

# Better - specific and clear
response = execute_tool(
    "gemini",
    """Analyze this Python function for:
    1. Security vulnerabilities
    2. Performance issues
    3. Best practice violations

    Code:
    {code}
    """
)
```

### 8. Resource Management

**Consider rate limits and costs:**

```python
# Check if consultation is necessary
if is_simple_case(code):
    return simple_analysis(code)

# Only consult AI for complex cases
response = execute_tool("gemini", complex_prompt)
```

---

## Related Documentation

- **Design Documentation:** `docs/AI_TOOL_INTERFACES_DESIGN.md` - Complete design rationale and architecture
- **Integration Tests:** `tests/integration/test_ai_tools_integration.py` - Comprehensive test suite with examples
- **Usage Patterns:** See `code-doc`, `sdd-plan-review`, and `run-tests` skills for real-world usage

---

## Version History

- **v1.0.0** (2025-11-05) - Initial API documentation
  - Complete API reference for all public interfaces
  - Comprehensive examples and error handling guide
  - Best practices and usage patterns

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/anthropics/claude-sdd-toolkit/issues
- See CONTRIBUTING.md for contribution guidelines
