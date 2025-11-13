# AI Consultation Fallback & Limits - Test Playbook

This playbook provides comprehensive testing procedures for the AI consultation fallback mechanism and tool limits feature.

## Overview

The AI consultation system now supports:
- **Tool-level fallback**: Automatic fallback from one AI provider to another (e.g., gemini → cursor-agent → codex)
- **Hybrid retry strategy**: Retries on transient errors (timeout, generic errors), skips on permanent failures
- **Consultation limits**: Limits the number of unique tools/providers used per skill invocation

## Table of Contents

1. [Unit Tests](#unit-tests)
2. [Integration Tests](#integration-tests)
3. [Manual Testing Scenarios](#manual-testing-scenarios)
4. [Configuration Testing](#configuration-testing)
5. [Edge Cases & Failure Scenarios](#edge-cases--failure-scenarios)
6. [Performance Testing](#performance-testing)

---

## Unit Tests

### ConsultationTracker Tests

**File**: `tests/test_consultation_limits.py`

```python
import pytest
from claude_skills.common.consultation_limits import ConsultationTracker


def test_tracker_initialization():
    """Test tracker starts with empty tool set."""
    tracker = ConsultationTracker()
    assert tracker.get_count() == 0
    assert len(tracker.get_tools_used()) == 0


def test_record_consultation():
    """Test recording tool consultations."""
    tracker = ConsultationTracker()

    tracker.record_consultation("gemini")
    assert tracker.get_count() == 1
    assert "gemini" in tracker.get_tools_used()

    tracker.record_consultation("cursor-agent")
    assert tracker.get_count() == 2
    assert tracker.get_tools_used() == {"gemini", "cursor-agent"}


def test_record_same_tool_twice():
    """Test that recording the same tool twice doesn't increase count."""
    tracker = ConsultationTracker()

    tracker.record_consultation("gemini")
    tracker.record_consultation("gemini")

    assert tracker.get_count() == 1
    assert tracker.get_tools_used() == {"gemini"}


def test_check_limit_with_no_limit():
    """Test check_limit with None returns True."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")

    # No limit means always allowed
    assert tracker.check_limit("cursor-agent", None) is True


def test_check_limit_below_threshold():
    """Test check_limit returns True when under limit."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")

    # Limit of 3, used 1, should allow new tool
    assert tracker.check_limit("cursor-agent", 3) is True


def test_check_limit_at_threshold():
    """Test check_limit returns False when at limit."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    # Limit of 2, used 2, should reject new tool
    assert tracker.check_limit("codex", 2) is False


def test_check_limit_allows_existing_tool():
    """Test check_limit returns True for already-used tool."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    # Even at limit, should allow re-using existing tool
    assert tracker.check_limit("gemini", 2) is True


def test_reset():
    """Test reset clears all tracked tools."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    tracker.reset()

    assert tracker.get_count() == 0
    assert len(tracker.get_tools_used()) == 0


def test_thread_safety():
    """Test tracker is thread-safe."""
    import threading

    tracker = ConsultationTracker()
    tools = ["gemini", "cursor-agent", "codex", "claude"]

    def record_tools():
        for tool in tools:
            tracker.record_consultation(tool)

    threads = [threading.Thread(target=record_tools) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have exactly 4 unique tools despite 40 recordings
    assert tracker.get_count() == 4
```

### Config Resolution Tests

**File**: `tests/test_ai_config_fallback.py`

```python
import pytest
from claude_skills.common import ai_config


def test_get_tool_priority_skill_override():
    """Test skill-specific tool_priority overrides global."""
    priority = ai_config.get_tool_priority("run-tests")
    assert priority == ["gemini", "cursor-agent"]


def test_get_tool_priority_global_default():
    """Test falls back to global tool_priority."""
    priority = ai_config.get_tool_priority("unknown-skill")
    assert priority == ["gemini", "cursor-agent", "codex", "claude"]


def test_get_fallback_config_defaults():
    """Test fallback config returns correct defaults."""
    config = ai_config.get_fallback_config("run-tests")

    assert config["enabled"] is True
    assert config["max_retries_per_tool"] == 2
    assert "timeout" in config["retry_on_status"]
    assert "error" in config["retry_on_status"]
    assert "not_found" in config["skip_on_status"]
    assert "invalid_output" in config["skip_on_status"]


def test_get_fallback_config_skill_override():
    """Test skill can override fallback settings."""
    config = ai_config.get_fallback_config("run-tests")
    # run-tests has max_retries_per_tool: 3 in config
    assert config["max_retries_per_tool"] == 3


def test_get_consultation_limit():
    """Test consultation limit resolution."""
    limit = ai_config.get_consultation_limit("run-tests")
    assert limit == 2  # From config

    limit_default = ai_config.get_consultation_limit("unknown-skill")
    assert limit_default == 4  # Global default


def test_get_consultation_limit_none():
    """Test returns None when no limit configured."""
    # If we remove limits from config, should return None
    pass  # Would need to mock config
```

### Fallback Logic Tests

**File**: `tests/test_execute_tool_fallback.py`

```python
import pytest
from unittest.mock import Mock, patch
from claude_skills.common.ai_tools import execute_tool_with_fallback, ToolStatus, ToolResponse
from claude_skills.common.consultation_limits import ConsultationTracker


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_success_first_tool(mock_execute):
    """Test successful consultation on first tool doesn't trigger fallback."""
    mock_execute.return_value = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="Analysis complete"
    )

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "gemini"
    assert tracker.get_count() == 1
    assert mock_execute.call_count == 1


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_on_timeout(mock_execute):
    """Test fallback to next tool on timeout."""
    # First call times out, second succeeds
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT, error="Timed out"),
        ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS, output="Done")
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "cursor-agent"
    assert tracker.get_count() == 2  # Both tools attempted
    assert mock_execute.call_count > 1  # Retries + fallback


@patch('claude_skills.common.ai_tools.execute_tool')
@patch('claude_skills.common.ai_tools.time.sleep')
def test_retry_on_timeout(mock_sleep, mock_execute):
    """Test retries same tool on timeout before fallback."""
    # Timeout twice, then succeed
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT),
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT),
        ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Done"),
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert mock_execute.call_count == 3  # 1 initial + 2 retries
    assert mock_sleep.call_count == 2  # Delay between retries
    assert tracker.get_count() == 1  # Only gemini used


@patch('claude_skills.common.ai_tools.execute_tool')
def test_skip_on_not_found(mock_execute):
    """Test immediately skips to next tool on NOT_FOUND."""
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.NOT_FOUND),
        ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS, output="Done"),
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "cursor-agent"
    # Should not retry gemini, just move to next tool
    assert mock_execute.call_count == 2


@patch('claude_skills.common.ai_tools.execute_tool')
def test_respects_consultation_limit(mock_execute):
    """Test respects max_tools_per_run limit."""
    # All tools fail
    mock_execute.return_value = ToolResponse(
        tool="any",
        status=ToolStatus.ERROR,
        error="Failed"
    )

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",  # Has max_tools_per_run: 2
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    # Should try gemini and cursor-agent, but not codex (limit of 2)
    assert tracker.get_count() <= 2


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_disabled(mock_execute):
    """Test fallback can be disabled."""
    mock_execute.return_value = ToolResponse(
        tool="gemini",
        status=ToolStatus.TIMEOUT
    )

    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        fallback_enabled=False
    )

    assert not response.success
    assert mock_execute.call_count == 1  # No retries or fallback
```

---

## Integration Tests

### End-to-End Skill Tests

**File**: `tests/integration/test_fallback_integration.py`

```python
import pytest
import subprocess


def test_run_tests_fallback_gemini_to_cursor():
    """Test run-tests falls back from gemini to cursor-agent."""
    # Rename gemini binary temporarily to simulate unavailability
    # (This is a simplified example - actual test would need proper setup)

    result = subprocess.run(
        ["python", "-m", "claude_skills.run_tests.cli",
         "consult", "assertion", "Test failed", "Root cause unknown"],
        capture_output=True,
        text=True
    )

    # Should succeed even if gemini unavailable
    assert result.returncode == 0
    # Should mention which tool was used
    assert "cursor-agent" in result.stdout.lower() or "gemini" in result.stdout.lower()


def test_sdd_plan_review_with_limits():
    """Test sdd-plan-review respects consultation limits."""
    # Run plan review that might consult multiple models
    result = subprocess.run(
        ["sdd", "plan-review", "test-spec-id"],
        capture_output=True,
        text=True,
        env={"HOME": "/tmp/test_home"}  # Use test config
    )

    # Parse output to verify tool count
    # Implementation would check that no more than max_tools_per_run were used
    pass


def test_fidelity_review_retry_on_timeout():
    """Test fidelity review retries on timeout."""
    # Set very short timeout to force timeout
    result = subprocess.run(
        ["sdd", "fidelity-review", "test-spec-id",
         "--timeout", "1"],  # 1 second timeout
        capture_output=True,
        text=True
    )

    # Should have attempted retries (check logs or output)
    pass
```

---

## Manual Testing Scenarios

### Scenario 1: Basic Fallback

**Setup**:
1. Ensure gemini and cursor-agent are both installed
2. Configure `run-tests` with `tool_priority: [gemini, cursor-agent]`

**Test**:
```bash
# Make gemini unavailable
mv $(which gemini) $(which gemini).bak

# Run consultation
sdd run-tests consult assertion "Test failed" "Root cause"

# Verify:
# - Command succeeds
# - Output shows "Consulting cursor-agent" or fallback message
# - cursor-agent was used instead of gemini
```

**Restore**:
```bash
mv $(which gemini).bak $(which gemini)
```

### Scenario 2: Retry on Timeout

**Setup**:
1. Create a wrapper script that delays gemini responses:
   ```bash
   #!/bin/bash
   # fake-gemini.sh
   sleep 10  # Simulate slow response
   gemini "$@"
   ```
2. Put wrapper in PATH before real gemini

**Test**:
```bash
# Run with short timeout
sdd run-tests consult assertion "Test" "Cause" --timeout 5

# Verify:
# - See retry attempts in output
# - Eventually falls back to cursor-agent
# - Check delay between retries (should be ~1s)
```

### Scenario 3: Consultation Limits

**Setup**:
1. Configure in `.claude/ai_config.yaml`:
   ```yaml
   run-tests:
     tool_priority: [gemini, cursor-agent, codex, claude]
     consultation_limits:
       max_tools_per_run: 2
   ```

**Test**:
```bash
# Make first 2 tools fail
mv $(which gemini) $(which gemini).bak
mv $(which cursor-agent) $(which cursor-agent).bak

# Run consultation
sdd run-tests consult assertion "Test" "Cause"

# Verify:
# - Command fails (hit limit before finding working tool)
# - Error message mentions consultation limit
# - Only 2 tools attempted (gemini, cursor-agent), not codex
```

**Restore**:
```bash
mv $(which gemini).bak $(which gemini)
mv $(which cursor-agent).bak $(which cursor-agent)
```

### Scenario 4: Per-Skill Configuration

**Setup**:
1. Configure different limits for different skills:
   ```yaml
   run-tests:
     consultation_limits:
       max_tools_per_run: 2

   sdd-plan-review:
     consultation_limits:
       max_tools_per_run: 4
   ```

**Test**:
```bash
# Test run-tests
sdd run-tests consult assertion "Test" "Cause"
# Should try max 2 tools

# Test plan-review
sdd plan-review some-spec
# Should be able to try up to 4 tools
```

### Scenario 5: Disable Fallback

**Setup**:
1. Configure fallback disabled:
   ```yaml
   run-tests:
     fallback:
       enabled: false
   ```

**Test**:
```bash
# Make gemini unavailable
mv $(which gemini) $(which gemini).bak

# Run consultation
sdd run-tests consult assertion "Test" "Cause"

# Verify:
# - Command fails immediately
# - No fallback attempted
# - Error about gemini not available
```

---

## Configuration Testing

### Test Configuration Precedence

**Test**: Verify configuration hierarchy works correctly

1. **Global defaults** (lowest priority)
   ```yaml
   tool_priority:
     default: [gemini, cursor-agent, codex, claude]
   consultation_limits:
     max_tools_per_run: 4
   ```

2. **Skill-specific overrides** (highest priority)
   ```yaml
   run-tests:
     tool_priority: [cursor-agent, gemini]
     consultation_limits:
       max_tools_per_run: 2
   ```

**Verification**:
```python
from claude_skills.common import ai_config

# Should use skill override
priority = ai_config.get_tool_priority("run-tests")
assert priority == ["cursor-agent", "gemini"]

limit = ai_config.get_consultation_limit("run-tests")
assert limit == 2

# Should use global default
priority = ai_config.get_tool_priority("unknown-skill")
assert priority == ["gemini", "cursor-agent", "codex", "claude"]
```

### Test Configuration Validation

**Test**: Invalid configuration is handled gracefully

```yaml
# Invalid config
consultation_limits:
  max_tools_per_run: -1  # Invalid: negative

fallback:
  max_retries_per_tool: "not a number"  # Invalid: wrong type
```

**Verification**:
- Config loading doesn't crash
- Invalid values use safe defaults
- Warning messages logged

---

## Edge Cases & Failure Scenarios

### Edge Case 1: All Tools Fail

**Test**:
```bash
# Make all tools unavailable
for tool in gemini cursor-agent codex claude; do
  [ -f "$(which $tool)" ] && mv "$(which $tool)" "$(which $tool).bak"
done

# Run consultation
sdd run-tests consult assertion "Test" "Cause"

# Verify:
# - Returns error response
# - Error message indicates all tools failed
# - Doesn't crash
```

### Edge Case 2: Empty Tool Priority List

**Test**:
```yaml
run-tests:
  tool_priority: []  # Empty list
```

**Verification**:
- Falls back to enabled tools from config
- Still respects consultation limits

### Edge Case 3: Consultation Limit of 0

**Test**:
```yaml
consultation_limits:
  max_tools_per_run: 0
```

**Verification**:
- Immediately returns error
- No tools consulted

### Edge Case 4: Concurrent Consultations

**Test**: Multiple parallel consultations with same tracker

```python
from concurrent.futures import ThreadPoolExecutor
from claude_skills.common import consultation_limits
from claude_skills.common.ai_tools import execute_tool_with_fallback

tracker = consultation_limits.ConsultationTracker()

def consult(i):
    return execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt=f"Test {i}",
        tracker=tracker
    )

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(consult, range(10)))

# Verify:
# - All consultations complete
# - Tracker count is accurate
# - No race conditions
```

### Edge Case 5: Tool Returns Invalid Output

**Test**: Tool succeeds but returns malformed output

**Verification**:
- Status is INVALID_OUTPUT
- Skips to next tool (no retry)
- Doesn't treat as success

---

## Performance Testing

### Test 1: Fallback Latency

**Goal**: Measure overhead of fallback logic

```python
import time
from claude_skills.common.ai_tools import execute_tool, execute_tool_with_fallback

# Baseline (no fallback)
start = time.time()
response = execute_tool("gemini", "Quick test", timeout=10)
baseline_time = time.time() - start

# With fallback
start = time.time()
response = execute_tool_with_fallback(
    skill_name="run-tests",
    tool="gemini",
    prompt="Quick test",
    timeout=10
)
fallback_time = time.time() - start

# Overhead should be minimal (<100ms)
overhead = fallback_time - baseline_time
assert overhead < 0.1  # Less than 100ms
```

### Test 2: Retry Delay Accuracy

**Goal**: Verify retry delays are accurate

```python
import time
from unittest.mock import patch
from claude_skills.common.ai_tools import execute_tool_with_fallback, ToolResponse, ToolStatus

with patch('claude_skills.common.ai_tools.execute_tool') as mock:
    mock.return_value = ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT)

    start = time.time()
    execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test"
    )
    elapsed = time.time() - start

    # Should have 2 retries with 1s delay each
    # Plus some overhead
    assert 2.0 <= elapsed <= 2.5
```

### Test 3: Parallel Consultation Throughput

**Goal**: Verify parallel consultations don't degrade performance

```python
from concurrent.futures import ThreadPoolExecutor
import time

def single_consultation():
    return execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test"
    )

# Serial
start = time.time()
for _ in range(5):
    single_consultation()
serial_time = time.time() - start

# Parallel
start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    list(executor.map(lambda _: single_consultation(), range(5)))
parallel_time = time.time() - start

# Parallel should be faster
assert parallel_time < serial_time
```

---

## Testing Checklist

Before considering the implementation complete, verify:

### Unit Tests
- [ ] ConsultationTracker basic operations
- [ ] ConsultationTracker thread safety
- [ ] Config resolution (tool_priority, fallback_config, consultation_limit)
- [ ] Fallback logic with success on first tool
- [ ] Fallback logic with retry on timeout
- [ ] Fallback logic with skip on permanent error
- [ ] Consultation limit enforcement
- [ ] Fallback can be disabled

### Integration Tests
- [ ] End-to-end fallback in run-tests
- [ ] End-to-end fallback in sdd-plan-review
- [ ] End-to-end fallback in sdd-fidelity-review
- [ ] End-to-end fallback in code-doc
- [ ] End-to-end fallback in sdd-render
- [ ] Consultation limits enforced across skills

### Manual Tests
- [ ] Basic fallback scenario
- [ ] Retry on timeout scenario
- [ ] Consultation limits scenario
- [ ] Per-skill configuration
- [ ] Disable fallback scenario

### Edge Cases
- [ ] All tools fail
- [ ] Empty tool priority list
- [ ] Consultation limit of 0
- [ ] Concurrent consultations
- [ ] Invalid output from tool

### Performance
- [ ] Fallback overhead acceptable
- [ ] Retry delays accurate
- [ ] Parallel consultations performant

### Documentation
- [ ] Updated user-facing docs
- [ ] Updated configuration reference
- [ ] Added troubleshooting guide
- [ ] This test playbook!

---

## Troubleshooting Test Failures

### Issue: Fallback Not Triggering

**Symptoms**: Tool fails but doesn't fallback

**Debug**:
1. Check `fallback.enabled` in config
2. Verify tool_priority list has multiple tools
3. Check tool status is retryable/skippable
4. Add debug logging to see execution flow

### Issue: Consultation Limit Not Enforced

**Symptoms**: More tools used than limit allows

**Debug**:
1. Verify `consultation_limits.max_tools_per_run` is set
2. Check tracker is being passed correctly
3. Verify tracker is not reset mid-execution
4. Add logging to tracker.check_limit()

### Issue: Tests Failing in CI

**Symptoms**: Tests pass locally but fail in CI

**Debug**:
1. Check tool availability in CI environment
2. Verify network access for tools
3. Check timeout settings (CI may be slower)
4. Use mocks instead of real tool calls

### Issue: Flaky Tests

**Symptoms**: Tests intermittently fail

**Debug**:
1. Check for race conditions in parallel tests
2. Verify mocks are properly reset between tests
3. Add delays or retry logic to tests
4. Isolate state between tests (fresh tracker, config)

---

## Next Steps

After completing this test playbook:

1. **Implement unit tests** - Start with ConsultationTracker and config resolution
2. **Add integration tests** - Test real skill invocations with fallback
3. **Manual testing** - Verify behavior matches expectations
4. **Document findings** - Update docs based on test results
5. **Performance tuning** - Optimize based on performance tests
6. **CI integration** - Add tests to CI pipeline

## References

- [AI Configuration Guide](./AI_CONFIGURATION.md)
- [Fallback Design Document](./FALLBACK_DESIGN.md)
- [Consultation Limits Specification](./CONSULTATION_LIMITS.md)
