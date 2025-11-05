# AI Tool Consultation Interfaces Design

## Overview

This document defines the standardized interfaces and data structures for AI tool consultation across the Claude SDD Toolkit. These interfaces provide a consistent API for interacting with external AI CLI tools (gemini, codex, cursor-agent).

## Design Goals

1. **Type Safety**: Use dataclasses with type hints for compile-time checking
2. **Immutability**: Response objects should be immutable after creation
3. **Extensibility**: Easy to add new tools and response fields
4. **Rich Metadata**: Capture comprehensive information about tool execution
5. **Backwards Compatibility**: Support migration from existing NamedTuple
6. **Error Handling**: Clear distinction between different failure modes

## Core Data Structures

### ToolResponse Dataclass

The primary response type for single tool consultations:

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum

class ToolStatus(Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_OUTPUT = "invalid_output"
    ERROR = "error"

@dataclass(frozen=True)
class ToolResponse:
    """
    Standardized response from AI tool consultation.

    This is the core response type used throughout the toolkit for
    all AI tool interactions.

    Attributes:
        tool: Name of the tool (gemini, codex, cursor-agent)
        status: Execution status (success, timeout, error, etc.)
        output: Raw output from the tool (stdout)
        error: Error message if any (stderr or exception message)
        duration: Execution time in seconds
        timestamp: When the consultation started (ISO format)
        model: Model used by the tool (if applicable)
        prompt: The prompt sent to the tool (optional, for debugging)
        exit_code: Process exit code (None if didn't run)
        metadata: Additional tool-specific metadata
    """
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

    @property
    def success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Check if tool execution failed."""
        return not self.success

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "tool": self.tool,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "model": self.model,
            "prompt": self.prompt,
            "exit_code": self.exit_code,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ToolResponse":
        """Create from dictionary."""
        data["status"] = ToolStatus(data["status"])
        return cls(**data)
```

**Key Features:**
- **Frozen**: Immutable after creation (using `frozen=True`)
- **Rich Metadata**: Captures timestamp, model, prompt for debugging
- **Status Enum**: Clear distinction between failure types
- **Convenience Properties**: `success` and `failed` for easy checking
- **Serialization**: `to_dict()` and `from_dict()` for JSON storage

**Migration from NamedTuple:**
The existing `ConsultationResponse` NamedTuple can be converted:

```python
# Old NamedTuple
old_response = ConsultationResponse(
    tool="gemini",
    success=True,
    output="result",
    error=None,
    duration=2.5
)

# New dataclass
new_response = ToolResponse(
    tool="gemini",
    status=ToolStatus.SUCCESS,
    output="result",
    error=None,
    duration=2.5
)
```

### MultiToolResponse Dataclass

For parallel multi-tool consultations:

```python
@dataclass(frozen=True)
class MultiToolResponse:
    """
    Response from multiple tool consultations run in parallel.

    Attributes:
        responses: Dictionary mapping tool names to their responses
        synthesis: Optional synthesis/consensus from all responses
        total_duration: Total wall-clock time (parallel execution)
        max_duration: Longest individual tool duration
        success_count: Number of successful tool calls
        failure_count: Number of failed tool calls
        timestamp: When the multi-tool consultation started
        failure_type: Optional failure type that triggered consultation
    """
    responses: dict[str, ToolResponse]
    synthesis: Optional[str] = None
    total_duration: float = 0.0
    max_duration: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_type: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if at least one tool succeeded."""
        return self.success_count > 0

    @property
    def all_failed(self) -> bool:
        """Check if all tools failed."""
        return self.success_count == 0

    @property
    def all_succeeded(self) -> bool:
        """Check if all tools succeeded."""
        return self.failure_count == 0

    def get_successful_responses(self) -> dict[str, ToolResponse]:
        """Get only successful tool responses."""
        return {
            tool: response
            for tool, response in self.responses.items()
            if response.success
        }

    def get_failed_responses(self) -> dict[str, ToolResponse]:
        """Get only failed tool responses."""
        return {
            tool: response
            for tool, response in self.responses.items()
            if response.failed
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "responses": {
                tool: response.to_dict()
                for tool, response in self.responses.items()
            },
            "synthesis": self.synthesis,
            "total_duration": self.total_duration,
            "max_duration": self.max_duration,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timestamp": self.timestamp,
            "failure_type": self.failure_type
        }
```

**Key Features:**
- **Aggregated Statistics**: Success/failure counts, durations
- **Filter Methods**: Get successful or failed responses easily
- **Optional Synthesis**: AI-generated consensus from multiple tools
- **Failure Type Tracking**: Remember why consultation was triggered

## Core Function Signatures

### Single Tool Consultation

```python
def consult_tool(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    timeout: int = 90,
    failure_type: Optional[str] = None,
    config: Optional[dict] = None
) -> ToolResponse:
    """
    Consult a single AI tool with a prompt.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        prompt: The prompt to send to the tool
        model: Optional model override (uses config default if None)
        timeout: Timeout in seconds (default 90)
        failure_type: Optional failure type for model selection
        config: Optional config dict (loads from file if None)

    Returns:
        ToolResponse with results and metadata

    Raises:
        ValueError: If tool is unknown or not configured
    """
    ...
```

### Multi-Tool Parallel Consultation

```python
def consult_tools_parallel(
    tools: list[str],
    prompt: str,
    *,
    timeout: int = 90,
    failure_type: Optional[str] = None,
    synthesize: bool = True,
    config: Optional[dict] = None
) -> MultiToolResponse:
    """
    Consult multiple AI tools in parallel with same prompt.

    Args:
        tools: List of tool names to consult
        prompt: The prompt to send to all tools
        timeout: Timeout per tool in seconds (default 90)
        failure_type: Optional failure type for model selection
        synthesize: Whether to synthesize responses into consensus
        config: Optional config dict (loads from file if None)

    Returns:
        MultiToolResponse with all results and optional synthesis

    Raises:
        ValueError: If no valid tools provided
    """
    ...
```

### Tool Availability Checking

```python
def check_tool_available(
    tool: str,
    *,
    check_version: bool = False,
    config: Optional[dict] = None
) -> bool:
    """
    Check if a tool is available and optionally working.

    Args:
        tool: Tool name to check
        check_version: If True, verify tool responds to --version
        config: Optional config dict (checks enabled flag)

    Returns:
        True if tool is available (and working if check_version=True)
    """
    ...
```

### Tool Discovery

```python
def discover_available_tools(
    *,
    config: Optional[dict] = None,
    filter_disabled: bool = True
) -> list[str]:
    """
    Discover all available AI tools in PATH.

    Args:
        config: Optional config dict (checks enabled flags)
        filter_disabled: If True, exclude disabled tools from config

    Returns:
        List of available tool names (empty if none found)
    """
    ...
```

### Auto-Routing

```python
def get_recommended_tool(
    failure_type: str,
    *,
    available_tools: Optional[list[str]] = None,
    config: Optional[dict] = None
) -> Optional[str]:
    """
    Get recommended tool for a specific failure type.

    Args:
        failure_type: Type of failure (assertion, exception, import, etc.)
        available_tools: Optional pre-discovered tools (discovers if None)
        config: Optional config dict (loads from file if None)

    Returns:
        Recommended tool name or None if no suitable tool available
    """
    ...
```

### Command Building

```python
def build_tool_command(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[dict] = None
) -> list[str]:
    """
    Build command list for tool execution.

    Args:
        tool: Tool name
        prompt: The prompt to include in command
        model: Optional model override
        config: Optional config dict

    Returns:
        Command as list of strings (shell-safe)

    Raises:
        ValueError: If tool is unknown
    """
    ...
```

## Helper Functions

### Output Processing

```python
def extract_tool_output(
    raw_output: str,
    tool: str
) -> str:
    """
    Extract actual output from tool response.

    Some tools (like gemini) wrap output in JSON.
    Others return plain text.

    Args:
        raw_output: Raw stdout from tool
        tool: Tool name

    Returns:
        Extracted output (unwrapped if JSON)
    """
    ...
```

### Response Synthesis

```python
def synthesize_tool_responses(
    responses: dict[str, ToolResponse],
    original_prompt: str,
    *,
    synthesis_tool: str = "gemini",
    timeout: int = 120,
    config: Optional[dict] = None
) -> Optional[str]:
    """
    Use AI to synthesize multiple tool responses into consensus.

    Args:
        responses: Dictionary of tool responses
        original_prompt: The original prompt sent to tools
        synthesis_tool: Tool to use for synthesis (default gemini)
        timeout: Timeout for synthesis (default 120s)
        config: Optional config dict

    Returns:
        Synthesized consensus or None if synthesis fails
    """
    ...
```

### Timeout Helpers

```python
def get_timeout_for_operation(
    operation: str,
    *,
    config: Optional[dict] = None
) -> int:
    """
    Get appropriate timeout for operation type.

    Args:
        operation: Operation type (detection, consultation, review, synthesis)
        config: Optional config dict (uses hardcoded defaults if None)

    Returns:
        Timeout in seconds
    """
    ...
```

## Usage Examples

### Example 1: Single Tool Consultation

```python
from claude_skills.common.ai_tools import consult_tool

# Simple consultation
response = consult_tool("gemini", "Analyze this code:\n\n```python\ndef foo(): pass\n```")

if response.success:
    print(f"Analysis: {response.output}")
    print(f"Duration: {response.duration:.2f}s")
else:
    print(f"Failed: {response.error}")

# With options
response = consult_tool(
    tool="codex",
    prompt="Fix this test failure: AssertionError...",
    model="claude-3.7-sonnet",
    timeout=60,
    failure_type="assertion"
)
```

### Example 2: Multi-Tool Parallel Consultation

```python
from claude_skills.common.ai_tools import consult_tools_parallel

# Consult all available tools
response = consult_tools_parallel(
    tools=["gemini", "codex", "cursor-agent"],
    prompt="Review this implementation for security issues...",
    synthesize=True
)

print(f"Success: {response.success_count}/{len(response.responses)}")

for tool, tool_response in response.get_successful_responses().items():
    print(f"\n{tool}:")
    print(tool_response.output)

if response.synthesis:
    print(f"\nConsensus:\n{response.synthesis}")
```

### Example 3: Auto-Routing Based on Failure Type

```python
from claude_skills.common.ai_tools import (
    get_recommended_tool,
    consult_tool
)

# Get best tool for assertion failures
tool = get_recommended_tool("assertion")

if tool:
    response = consult_tool(
        tool=tool,
        prompt=f"Debug this assertion failure:\n{failure_output}",
        failure_type="assertion"
    )

    if response.success:
        print(f"Recommendation from {tool}:\n{response.output}")
```

### Example 4: Tool Discovery and Availability

```python
from claude_skills.common.ai_tools import (
    discover_available_tools,
    check_tool_available
)

# Discover all available tools
available = discover_available_tools()
print(f"Available tools: {', '.join(available)}")

# Check specific tool
if check_tool_available("gemini", check_version=True):
    print("Gemini is available and working")
else:
    print("Gemini is not available")
```

### Example 5: Serialization for Storage

```python
import json
from claude_skills.common.ai_tools import consult_tool

# Consult and serialize
response = consult_tool("gemini", "Analyze...")

# Save to JSON
with open("consultation_result.json", "w") as f:
    json.dump(response.to_dict(), f, indent=2)

# Load from JSON
with open("consultation_result.json") as f:
    data = json.load(f)
    loaded_response = ToolResponse.from_dict(data)

print(f"Loaded: {loaded_response.tool} - {loaded_response.status.value}")
```

## Error Handling

### Expected Errors

```python
from claude_skills.common.ai_tools import consult_tool, ToolStatus

response = consult_tool("gemini", prompt)

# Check specific error types
if response.status == ToolStatus.TIMEOUT:
    print(f"Tool timed out after {response.duration}s")
elif response.status == ToolStatus.NOT_FOUND:
    print(f"Tool '{response.tool}' not installed")
elif response.status == ToolStatus.INVALID_OUTPUT:
    print(f"Tool returned invalid output: {response.error}")
elif response.status == ToolStatus.ERROR:
    print(f"Tool error: {response.error}")
elif response.success:
    print(f"Success: {response.output}")
```

### Handling Failures Gracefully

```python
from claude_skills.common.ai_tools import consult_tools_parallel

# Try multiple tools, at least one should work
response = consult_tools_parallel(
    tools=["gemini", "codex", "cursor-agent"],
    prompt=prompt,
    synthesize=False  # Don't synthesize if some failed
)

if response.all_failed:
    print("All tools failed - manual review needed")
elif response.success_count > 0:
    # Use the first successful response
    successful = response.get_successful_responses()
    first_success = next(iter(successful.values()))
    print(f"Using {first_success.tool} response: {first_success.output}")
```

## Migration Path

### Phase 1: Parallel Implementation (Current → Transition)

Maintain both old and new APIs during migration:

```python
# Old API (NamedTuple)
from claude_skills.run_tests.consultation import (
    consult_external_tool,  # Returns ConsultationResponse NamedTuple
)

# New API (dataclass)
from claude_skills.common.ai_tools import (
    consult_tool,  # Returns ToolResponse dataclass
)

# Both work during transition
```

### Phase 2: Deprecation Warnings (Transition)

Add deprecation warnings to old API:

```python
import warnings

def consult_external_tool(...):
    warnings.warn(
        "consult_external_tool is deprecated, use ai_tools.consult_tool instead",
        DeprecationWarning,
        stacklevel=2
    )
    # Call new implementation internally
    response = consult_tool(...)
    # Convert to old format for backwards compat
    return ConsultationResponse(...)
```

### Phase 3: Remove Old API (Future)

After all code migrated, remove old implementations.

## Configuration Schema

The tool configuration YAML supports these interfaces:

```yaml
tools:
  gemini:
    enabled: true
    command: "gemini"
    models: ["gemini-exp-1114", "gemini-2.0-flash-exp"]
    default_model: "gemini-exp-1114"
    timeout: 90
    failure_models:
      assertion: "gemini-exp-1114"
      exception: "gemini-exp-1114"
      timeout: "gemini-2.0-flash-exp"

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

timeouts:
  detection: 5
  consultation: 90
  review: 600
  synthesis: 120

routing:
  assertion: ["gemini", "codex", "cursor-agent"]
  exception: ["codex", "gemini", "cursor-agent"]
  import: ["cursor-agent", "codex", "gemini"]
  fixture: ["cursor-agent", "gemini", "codex"]
  timeout: ["gemini", "cursor-agent", "codex"]
```

## Testing Strategy

### Unit Tests

```python
def test_tool_response_immutable():
    """ToolResponse should be immutable."""
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)

    with pytest.raises(dataclasses.FrozenInstanceError):
        response.output = "modified"  # Should raise

def test_tool_response_success_property():
    """success property should match status."""
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)
    assert response.success is True
    assert response.failed is False

def test_tool_response_serialization():
    """ToolResponse should serialize to/from dict."""
    original = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="test",
        duration=1.5
    )

    data = original.to_dict()
    restored = ToolResponse.from_dict(data)

    assert restored == original

def test_multi_tool_response_filters():
    """MultiToolResponse should filter by success/failure."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=1,
        failure_count=1
    )

    successful = multi.get_successful_responses()
    assert len(successful) == 1
    assert "gemini" in successful

    failed = multi.get_failed_responses()
    assert len(failed) == 1
    assert "codex" in failed
```

### Integration Tests

```python
def test_consult_tool_with_real_tool(mocker):
    """Test real tool invocation."""
    # Mock subprocess for controlled testing
    mocker.patch("subprocess.run", return_value=MockResult(
        returncode=0,
        stdout="Analysis result",
        stderr=""
    ))

    response = consult_tool("gemini", "test prompt")

    assert response.success
    assert response.tool == "gemini"
    assert "Analysis result" in response.output

def test_consult_tools_parallel_all_succeed(mocker):
    """Test parallel consultation with all successes."""
    mocker.patch("subprocess.run", return_value=MockResult(
        returncode=0,
        stdout="OK",
        stderr=""
    ))

    response = consult_tools_parallel(
        tools=["gemini", "codex"],
        prompt="test",
        synthesize=False
    )

    assert response.all_succeeded
    assert response.success_count == 2
    assert response.failure_count == 0
```

## Summary

This design provides:

1. **Type-Safe Interfaces**: Dataclasses with full type hints
2. **Rich Metadata**: Comprehensive execution information
3. **Flexible API**: Single tool, multi-tool, auto-routing patterns
4. **Error Handling**: Clear status enum for different failure modes
5. **Serialization**: Easy JSON storage and restoration
6. **Testing**: Immutable, testable data structures
7. **Migration Path**: Smooth transition from existing NamedTuple
8. **Extensibility**: Easy to add new tools and features

The interfaces balance simplicity for common cases with power for advanced use cases, while maintaining backwards compatibility during migration.
