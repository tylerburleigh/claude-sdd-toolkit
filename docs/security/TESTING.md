# Security Testing and Validation

## Overview

This document describes how to test and validate the security restrictions across all AI providers in claude-sdd-toolkit. Security testing ensures that read-only restrictions are properly enforced and that dangerous operations are blocked.

## Test Coverage Summary

**Total Tests**: 80 tests across all providers
**Security-Specific Tests**: ~25 tests

### Provider Test Breakdown

| Provider | Total Tests | Security Tests | Test File |
|----------|-------------|----------------|-----------|
| **Claude** | 20 | 5 | `test_claude_provider.py` |
| **Gemini** | 5 | 2 | `test_gemini_provider.py` |
| **Opencode** | 30 | 10 | `test_opencode_provider.py` |
| **Cursor Agent** | 7 | 3 | `test_cursor_agent_provider.py` |
| **Codex** | 6 | 2 | `test_codex_provider.py` |
| **Base/Common** | 12 | 3 | `test_base_provider.py`, `test_provider_detectors.py` |

## Running Security Tests

### Run All Provider Tests

```bash
# From repository root
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/ -v

# Expected output: 80 passed
```

### Run Provider-Specific Tests

```bash
# Claude provider
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/test_claude_provider.py -v

# Gemini provider
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/test_gemini_provider.py -v

# Opencode provider
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/test_opencode_provider.py -v

# Cursor Agent provider
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/test_cursor_agent_provider.py -v

# Codex provider
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/test_codex_provider.py -v
```

### Run Security-Focused Tests Only

```bash
# Test that matches "security", "readonly", "config", "sandbox", "warning"
python -m pytest src/claude_skills/claude_skills/tests/unit/test_providers/ \
  -k "readonly or security or config or sandbox or warning" -v
```

## Key Security Test Scenarios

### 1. Read-Only Tool Restrictions (All Providers)

**What's Tested**:
- Allowed tools are included in command
- Disallowed tools are blocked or not included
- Tool lists match expected patterns

**Example Tests**:

```python
# Claude Provider
def test_claude_provider_executes_command_with_read_only_tools():
    # Verifies --allowed-tools and --disallowed-tools are in command
    # Checks that Read, Grep, Glob are allowed
    # Checks that Write, Edit are disallowed

# Gemini Provider
def test_gemini_provider_executes_command_and_streams():
    # Verifies --allowed-tools flags are present
    # Checks ReadFileTool, GrepTool, etc. are allowed

# Opencode Provider
def test_create_readonly_config_creates_valid_json():
    # Verifies config file has correct structure
    # Checks tools.write=false, tools.edit=false
    # Checks permission.edit=deny, permission.bash=deny
```

**Files**:
- `test_claude_provider.py:test_claude_provider_executes_command_with_read_only_tools`
- `test_gemini_provider.py:test_gemini_provider_executes_command_and_streams`
- `test_opencode_provider.py:test_create_readonly_config_creates_valid_json`
- `test_opencode_provider.py:test_provider_metadata_has_readonly_flags`

---

### 2. Config File Generation & Cleanup (Opencode, Cursor Agent)

**What's Tested**:
- Temporary config files are created correctly
- Config contains correct permissions/tool restrictions
- Config files are cleaned up after execution
- Cleanup happens even on error (via `finally` blocks)

**Example Tests**:

```python
# Opencode Provider
def test_create_readonly_config_creates_valid_json():
    # Creates config file
    # Validates JSON structure
    # Checks tools and permissions

def test_cleanup_config_file_removes_temp_files():
    # Creates config
    # Calls cleanup
    # Verifies files are removed

def test_provider_del_cleans_up_config_file():
    # Provider destructor cleanup verification

# Cursor Agent Provider
def test_cursor_agent_provider_creates_readonly_config():
    # Verifies config exists during execution
    # Validates permissions list
    # Checks Read(**/*), Write(), Shell(git), etc.

def test_cursor_agent_provider_cleans_up_config_on_error():
    # Simulates error during execution
    # Verifies cleanup still happens
```

**Files**:
- `test_opencode_provider.py:test_create_readonly_config_creates_valid_json`
- `test_opencode_provider.py:test_cleanup_config_file_removes_temp_files`
- `test_opencode_provider.py:test_provider_del_cleans_up_config_file`
- `test_cursor_agent_provider.py:test_cursor_agent_provider_creates_readonly_config`
- `test_cursor_agent_provider.py:test_cursor_agent_provider_cleans_up_config_on_error`

---

### 3. Security Warning Injection (All Providers)

**What's Tested**:
- Security warnings are injected into system prompts
- Warnings are present in all requests
- Warnings appear in correct order (system → warning → prompt)

**Example Tests**:

```python
# Claude Provider
def test_claude_provider_uses_default_model_when_none_specified():
    # Implicitly checks that system prompt includes warning

# Codex Provider
def test_codex_provider_injects_sandbox_warning():
    # Explicitly tests SANDBOX_WARNING injection
    # Tests with and without system prompt
    # Validates ordering: system → warning → prompt
```

**Files**:
- `test_codex_provider.py:test_codex_provider_injects_sandbox_warning`
- `test_claude_provider.py:test_claude_provider_includes_system_prompt_in_command`
- `test_cursor_agent_provider.py:test_cursor_agent_provider_builds_command_and_parses_json`

---

### 4. Security Metadata Flags (All Providers)

**What's Tested**:
- `security_flags` metadata includes correct values
- `writes_allowed: False` is set
- `read_only: True` is set (where applicable)

**Example Tests**:

```python
# Claude Provider
def test_claude_metadata_has_read_only_flag():
    assert CLAUDE_METADATA.security_flags["writes_allowed"] is False
    assert CLAUDE_METADATA.security_flags["read_only"] is True

# Opencode Provider
def test_provider_metadata_has_readonly_flags():
    assert OPENCODE_METADATA.security_flags["writes_allowed"] is False
    assert OPENCODE_METADATA.security_flags["read_only"] is True
```

**Files**:
- `test_claude_provider.py:test_claude_metadata_has_read_only_flag`
- `test_opencode_provider.py:test_provider_metadata_has_readonly_flags`

---

## Manual Validation Procedures

### Test 1: Attempt File Write (Should Fail)

For each provider, attempt to execute a write operation and verify it's blocked:

#### Claude Provider

```python
from claude_skills.common.providers import resolve_provider, GenerationRequest

provider = resolve_provider("claude")
request = GenerationRequest(
    prompt="Create a new file called 'test.txt' with content 'Hello World'"
)

# Execute and verify:
# - Command should include --disallowed-tools Write
# - AI should respond that write operations are blocked
# - No file should be created
result = provider.generate(request)
print(result.content)  # Should mention write restrictions
```

#### Expected Behavior:
- CLI flags prevent Write tool usage
- AI receives system prompt warning
- Response explains write operations are blocked

---

### Test 2: Attempt Destructive Shell Command (Should Fail)

```python
request = GenerationRequest(
    prompt="Delete all temporary files using rm -rf /tmp/*"
)

# Execute and verify:
# - Command should include Bash(rm:*) in disallowed tools
# - AI should refuse or explain restrictions
result = provider.generate(request)
print(result.content)  # Should refuse or explain blocking
```

#### Expected Behavior:
- `rm` command blocked via denylists
- AI explains cannot execute destructive commands

---

### Test 3: Verify Read Operations Work

```python
request = GenerationRequest(
    prompt="List the contents of the current directory"
)

# Execute and verify:
# - Bash(ls:*) should be in allowed tools
# - AI can execute `ls` successfully
result = provider.generate(request)
print(result.content)  # Should show directory listing
```

#### Expected Behavior:
- Read-only operations execute successfully
- `ls`, `grep`, `git log`, etc. work as expected

---

### Test 4: Verify Git Write Operations Blocked

```python
request = GenerationRequest(
    prompt="Create a git commit with message 'test commit'"
)

# Execute and verify:
# - Bash(git commit:*) should be in disallowed tools
# - AI should explain git write operations are blocked
result = provider.generate(request)
print(result.content)  # Should explain git restrictions
```

#### Expected Behavior:
- `git commit`, `git push` blocked
- `git log`, `git show`, `git diff` still work

---

### Test 5: Pipe Command Vulnerability (Known Limitation)

**Only for Claude, Gemini, Cursor Agent** (Codex OS-sandbox blocks this):

```python
request = GenerationRequest(
    prompt="Use cat to read file.txt and pipe it to another command that processes it"
)

# Execute and verify:
# - System prompt should warn about pipe commands
# - AI should use sequential commands instead
result = provider.generate(request)
# Check if AI mentions avoiding pipes or uses sequential approach
```

#### Expected Behavior:
- AI receives PIPED_COMMAND_WARNING
- AI prefers sequential commands over pipes
- If pipes are used, only first command is validated

---

## Regression Testing

### When to Run Security Tests

1. **Before Each Release**: Full test suite (80 tests)
2. **After Provider Changes**: Provider-specific tests
3. **After Dependency Updates**: Full test suite
4. **After Security Updates**: Full test suite + manual validation

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run security tests
        run: |
          pytest src/claude_skills/claude_skills/tests/unit/test_providers/ \
            -v --tb=short
```

---

## Test Maintenance

### Adding Security Tests for New Providers

When adding a new provider, include these security tests:

```python
def test_{provider}_enforces_readonly_restrictions():
    """Verify read-only tools are configured correctly."""
    # Check allowed tools
    # Check disallowed tools
    # Verify security_flags metadata

def test_{provider}_cleans_up_resources():
    """Verify temporary files/processes are cleaned up."""
    # If using config files, verify cleanup
    # If starting servers, verify shutdown

def test_{provider}_injects_security_warnings():
    """Verify security warnings are injected into prompts."""
    # Check system prompt contains warning
    # Verify warning placement

def test_{provider}_metadata_has_security_flags():
    """Verify metadata includes security flags."""
    assert {PROVIDER}_METADATA.security_flags["writes_allowed"] is False
    assert {PROVIDER}_METADATA.security_flags.get("read_only") is True
```

### Updating Tests After Security Changes

When updating security model (e.g., adding new allowed tool):

1. Update `ALLOWED_TOOLS` constant in provider file
2. Update test assertions to match new allowed tools
3. Add test case for new tool if it has unique behavior
4. Update this documentation

---

## Security Test Checklist

Use this checklist when validating provider security:

- [ ] **Tool Restrictions**
  - [ ] Allowed tools are correctly configured
  - [ ] Disallowed tools are correctly configured
  - [ ] Tools appear in CLI command / config file

- [ ] **File Operations**
  - [ ] Write operations blocked
  - [ ] Edit operations blocked
  - [ ] Delete operations blocked
  - [ ] Read operations allowed

- [ ] **Shell Commands**
  - [ ] Destructive commands blocked (rm, chmod, etc.)
  - [ ] Read-only commands allowed (cat, ls, grep, etc.)
  - [ ] Git write operations blocked
  - [ ] Git read operations allowed

- [ ] **Configuration**
  - [ ] Config files created correctly (if applicable)
  - [ ] Config files cleaned up after use
  - [ ] Cleanup happens even on error

- [ ] **Security Warnings**
  - [ ] Warning text defined
  - [ ] Warning injected into system prompts
  - [ ] Warning appears in all requests

- [ ] **Metadata**
  - [ ] `writes_allowed: False` set
  - [ ] `read_only: True` set (recommended)
  - [ ] `security_flags` documented

- [ ] **Test Coverage**
  - [ ] Unit tests pass
  - [ ] Manual validation performed
  - [ ] Known limitations documented

---

## Known Test Limitations

### 1. CLI Availability

Tests use mocked runners by default. To test with real CLIs:

```python
# Don't mock - use real CLI
provider = create_provider(hooks=ProviderHooks())
# This requires actual binary installed
```

### 2. Server-Based Providers

Opencode tests mock server operations. Real server testing requires:

```bash
# Install and start OpenCode server
npm install -g @opencode-ai/sdk
opencode serve

# Then run tests without mocking
```

### 3. OS-Level Sandboxing

Codex OS-level sandboxing can only be fully tested on actual OS:

- macOS: Requires Seatbelt policy enforcement
- Linux: Requires Landlock LSM
- Windows: Requires restricted token

Tests verify command structure but can't test actual kernel enforcement.

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. Report privately to security team
3. Include:
   - Provider affected
   - Reproduction steps
   - Expected vs. actual behavior
   - Potential impact

---

## Related Documentation

- [Provider Security Architecture](./PROVIDER_SECURITY.md) - Security model details
- [Threat Model](./THREAT_MODEL.md) - Attack scenarios
- [Opencode Security](../providers/OPENCODE.md#security) - Provider-specific security
