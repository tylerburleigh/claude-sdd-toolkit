# Provider Security Architecture

## Overview

The claude-sdd-toolkit implements a comprehensive read-only security model across all AI providers to prevent unintended modifications during code analysis and documentation generation. This document details the security architecture, implementation approaches, and known limitations across all five supported providers.

## Security Philosophy

**Core Principle**: All AI providers operate in **read-only mode** to ensure safe codebase analysis without risk of accidental or malicious modifications.

**Three-Tier Defense-in-Depth**:
1. **Tool Restriction**: Block dangerous tools at the provider level
2. **Permission Enforcement**: Use native CLI flags, config files, or OS-level sandboxing
3. **AI Education**: Inject security warnings into system prompts to inform the AI model

## Provider Security Models

### 1. Codex Provider ⭐⭐⭐⭐⭐ (Most Secure)

**Enforcement**: Native OS-level sandboxing via `--sandbox read-only` flag

**Implementation**:
```bash
codex exec --sandbox read-only --json -m gpt-5-codex "prompt"
```

**Security Mechanism**:
- **macOS**: Seatbelt sandbox policy
- **Linux**: Landlock LSM + seccomp filters
- **Windows**: Restricted token + job objects

**Strengths**:
- ✅ OS-level enforcement - cannot be bypassed by pipe commands or tool name variations
- ✅ Most robust security model
- ✅ Native CLI support - no additional configuration needed
- ✅ Platform-specific sandboxing tailored to each OS

**Allowed Operations** (enforced by sandbox):
- Read files and directories
- List directory contents
- Search file contents
- View file metadata
- Read-only git commands (log, show, diff, status, grep, blame)
- View running processes
- Check system information

**Blocked Operations** (enforced by sandbox):
- File modifications (write, edit, delete, move, copy)
- Directory creation
- Permission changes
- Web operations (WebFetch - prevents data exfiltration)
- Package installations
- System configuration changes
- Execute arbitrary shell commands with side effects

**Documentation Lists** (in code):
- `SANDBOX_ALLOWED_OPERATIONS`: ~95 documented read-only operations
- `SANDBOX_BLOCKED_OPERATIONS`: ~50 documented blocked operations
- `SANDBOX_WARNING`: System prompt explaining OS-level restrictions

**Key Insight**: Codex doesn't need tool filtering because the OS blocks operations directly.

---

### 2. Claude Provider ⭐⭐⭐⭐ (Strong)

**Enforcement**: Explicit allowlist/denylist via CLI flags

**Implementation**:
```bash
claude --print "prompt" --output-format json \
  --allowed-tools Read Grep Glob Task Bash(cat) Bash(git\ log:*) ... \
  --disallowed-tools Write Edit WebSearch WebFetch Bash(rm:*) Bash(git\ commit:*) ... \
  --system-prompt "SECURITY WARNING..."
```

**Security Mechanism**:
- Tool name pattern matching
- Granular Bash command patterns (e.g., `Bash(git log:*)`)
- Explicit denylist for dangerous operations

**Strengths**:
- ✅ Detailed allowlist with ~120 permitted operations
- ✅ Granular Bash command filtering
- ✅ Explicit denylist prevents accidental allowance
- ✅ Native Claude CLI feature

**Allowed Tools**:
- **Core**: Read, Grep, Glob, Task
- **Bash (viewing)**: cat, head, tail, bat, ls, tree, pwd
- **Bash (search)**: grep, rg, ag, find, fd
- **Bash (git read-only)**: git log, show, diff, status, grep, blame, branch, rev-parse, describe, ls-tree
- **Bash (text)**: wc, cut, paste, column, sort, uniq
- **Bash (data)**: jq, yq
- **Bash (analysis)**: file, stat, du, df
- **Bash (checksums)**: md5sum, shasum, sha256sum

**Disallowed Tools**:
- Write, Edit
- WebSearch, WebFetch (prevents data exfiltration)
- Bash(rm), Bash(rmdir), Bash(dd), Bash(mkfs)
- Bash(touch), Bash(mkdir), Bash(mv), Bash(cp), Bash(chmod), Bash(chown), Bash(sed), Bash(awk)
- Bash(git add), Bash(git commit), Bash(git push), Bash(git pull), Bash(git merge), Bash(git rebase)
- Bash(npm install), Bash(pip install), Bash(apt install), Bash(brew install)
- Bash(sudo), Bash(halt), Bash(reboot), Bash(shutdown)

**Known Limitations**:
- ⚠️ Piped commands may bypass checks (only first command in pipe is validated)
- ⚠️ Workaround documented in `SHELL_COMMAND_WARNING`

**Code References**:
- `ALLOWED_TOOLS`: src/claude_skills/common/providers/claude.py:41-109
- `DISALLOWED_TOOLS`: src/claude_skills/common/providers/claude.py:112-154
- `SHELL_COMMAND_WARNING`: src/claude_skills/common/providers/claude.py:157-163

---

### 3. Gemini Provider ⭐⭐⭐⭐ (Strong)

**Enforcement**: Tool allowlist via CLI flags (class and function names)

**Implementation**:
```bash
gemini -m gemini-2.5-flash --output-format json \
  --allowed-tools ReadFileTool read_file LSTool list_directory GlobTool glob ... \
  -p "SECURITY WARNING... User prompt"
```

**Security Mechanism**:
- Class name filtering (e.g., `ReadFileTool`, `GlobTool`)
- Function name filtering (e.g., `read_file`, `glob`)
- Supports both naming conventions for compatibility

**Strengths**:
- ✅ Comprehensive allowlist
- ✅ Dual naming support (class + function names)
- ✅ Native Gemini CLI policy engine

**Allowed Tools**:
- **Core**: ReadFileTool, GrepTool, LSTool, GlobTool
- **Shell**: ShellTool(cat), ShellTool(head), ShellTool(ls), ShellTool(grep), ShellTool(git log), etc.
- Similar coverage to Claude provider (web operations excluded for security)

**Known Limitations**:
- ⚠️ Piped commands bypass tool allowlist checks
- ⚠️ Only first command in pipe is validated by Gemini CLI
- ⚠️ Documented in `PIPED_COMMAND_WARNING`

**Code References**:
- `ALLOWED_TOOLS`: src/claude_skills/common/providers/gemini.py:39-111
- `PIPED_COMMAND_WARNING`: src/claude_skills/common/providers/gemini.py:114-118

---

### 4. Opencode Provider ⭐⭐⭐ (Good)

**Enforcement**: Dual-layer protection (tool configuration + permission denial)

**Implementation**:
```python
# Temporary config created at runtime
{
  "$schema": "https://opencode.ai/config.json",
  "tools": {
    "write": false, "edit": false, "bash": false,  # Disable write operations
    "read": true, "grep": true, "glob": true       # Enable read operations
  },
  "permission": {
    "edit": "deny",                                 # Double-guard
    "bash": "deny",
    "external_directory": "deny"
  }
}
```

**Security Mechanism**:
- Server config file at temporary location
- Tool disabling (tools.write: false)
- Permission denial (permission.edit: deny)
- Server started with `OPENCODE_CONFIG` env var pointing to config

**Strengths**:
- ✅ Dual-layer protection (tools + permissions)
- ✅ No shell execution allowed
- ✅ Temporary config per provider instance

**Allowed Operations**:
- Read, Grep, Glob, List, Task
- **No Bash/Shell access** (stricter than Claude/Gemini)
- **No web operations** (prevents data exfiltration)

**Blocked Operations**:
- Write, Edit, Patch, TodoWrite
- WebFetch (data exfiltration risk)
- All Bash/Shell commands
- External directory access

**Known Limitations**:
- ⚠️ **MCP Tool Bypass**: Tool blocking may not work for MCP tools ([OpenCode issue #3756](https://github.com/opencode-ai/opencode/issues/3756))
- ⚠️ **Server-Wide Config**: Configuration affects all sessions on the same server instance
- ⚠️ Temporary files require cleanup (implemented in `__del__`)

**Code References**:
- `READONLY_TOOLS_CONFIG`: src/claude_skills/common/providers/opencode.py:49-76
- Config creation: src/claude_skills/common/providers/opencode.py:221-240
- Cleanup: src/claude_skills/common/providers/opencode.py:242-258

---

### 5. Cursor Agent Provider ⭐⭐⭐ (Good)

**Enforcement**: Temporary config file with permission system

**Implementation**:
```json
// Temporary .cursor/cli-config.json
{
  "permissions": [
    "Read(**/*)",           // Allow all reads
    "Write()",              // Deny all writes (empty = deny)
    "Shell(cat)",           // Allow cat command
    "Shell(git)",           // Allow git command
    ...
  ],
  "description": "Read-only mode enforced by claude-sdd-toolkit"
}
```

**Security Mechanism**:
- Temporary directory with `.cursor/cli-config.json`
- Used as `--working-directory` for cursor-agent
- Permission format: Read(pathOrGlob), Write(pathOrGlob), Shell(commandBase)
- Shell permissions use first token only (e.g., "git log" → "git")

**Strengths**:
- ✅ Config-based allowlist approach
- ✅ Temporary config per execution
- ✅ Automatic cleanup after execution

**Allowed Operations**:
- Read, Grep, Glob, List, Task
- Shell commands: cat, head, tail, ls, tree, grep, find, git (read-only subcommands)

**Blocked Operations**:
- Write, Edit, Patch, Delete
- WebFetch (data exfiltration risk)
- Dangerous file operations (rm, dd, mkfs)
- File modifications (touch, mkdir, mv, cp, chmod, sed, awk)
- Git write operations (add, commit, push, pull, merge, rebase)
- Package installations

**Known Limitations**:
- ⚠️ **Weaker Security Model**: Cursor Agent's deprecated denylist approach had known bypasses
- ⚠️ **Shell Permission Granularity**: Only first token validated (e.g., "git" allows all git commands at config level)
- ⚠️ **Working Directory Override**: User-provided working directory is ignored in favor of config directory

**Code References**:
- `ALLOWED_TOOLS`: src/claude_skills/common/providers/cursor_agent.py:44-112
- `DISALLOWED_TOOLS`: src/claude_skills/common/providers/cursor_agent.py:115-159
- Config creation: src/claude_skills/common/providers/cursor_agent.py:285-337
- Cleanup: src/claude_skills/common/providers/cursor_agent.py:339-360

---

## Security Comparison Matrix

| Feature | Codex | Claude | Gemini | Opencode | Cursor Agent |
|---------|-------|--------|--------|----------|--------------|
| **Enforcement Level** | OS kernel | CLI tool | CLI tool | Server config | Temp config file |
| **Bypass Resistance** | Very High | High | High | Medium | Medium |
| **Pipe Command Safe** | ✅ Yes | ⚠️ No | ⚠️ No | N/A (no shell) | ⚠️ No |
| **MCP Tool Safe** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Shell Access** | Read-only | Read-only | Read-only | ❌ Disabled | Read-only |
| **Config Overhead** | None | None | None | Temp file | Temp file |
| **Platform Support** | macOS/Linux/Win | All | All | All | macOS/Linux |
| **Granularity** | OS-level | Command patterns | Tool classes | Tool categories | Permission paths |
| **Performance** | Fast (native) | Fast | Fast | Medium (server) | Medium (config I/O) |

## System Prompt Warnings

All providers inject security warnings into system prompts to educate the AI:

### Claude Provider
```
IMPORTANT SECURITY NOTE: When using shell commands, be aware of the following restrictions:
1. Only specific read-only commands are allowed (cat, grep, git log, etc.)
2. Write operations, file modifications, and destructive commands are blocked
3. Avoid using piped commands as they may bypass some security checks
4. Use sequential commands or alternative approaches when possible
```

### Gemini Provider
```
IMPORTANT SECURITY NOTE: When using shell commands, avoid piped commands (e.g., cat file.txt | wc -l).
Piped commands bypass the tool allowlist checks in Gemini CLI - only the first command in a pipe is validated.
Instead, use sequential commands or alternative approaches to achieve the same result safely.
```

### Opencode Provider
```
IMPORTANT SECURITY NOTE: This session is running in read-only mode with the following restrictions:
1. File write operations (write, edit, patch) are disabled
2. Shell command execution (bash) is disabled
3. Web operations (webfetch) are disabled to prevent data exfiltration
4. Only read operations are available (read, grep, glob, list)
5. Attempts to modify files, execute commands, or access the web will be blocked by the server
```

### Cursor Agent Provider
```
IMPORTANT SECURITY NOTE: This session is running in read-only mode with the following restrictions:
1. File write operations (Write, Edit, Patch, Delete) are disabled via Cursor Agent config
2. Only approved read-only shell commands are permitted
3. Cursor Agent's security model is weaker than other CLIs - be cautious
4. Configuration is enforced via temporary .cursor/cli-config.json file
5. Note: Cursor Agent's deprecated denylist approach had known bypasses - this uses allowlist
```

### Codex Provider
```
IMPORTANT SECURITY NOTE: This session runs with Codex CLI's native --sandbox read-only mode:
1. Native OS-level sandboxing enforced by the operating system:
   - macOS: Seatbelt sandbox policy
   - Linux: Landlock LSM + seccomp filters
   - Windows: Restricted token + job objects
2. Only read operations are permitted - writes are blocked at the OS level
3. Shell commands are restricted to read-only operations by the sandbox
4. The sandbox is enforced by the Codex CLI itself, not just tool filtering
5. This is the most robust security model - cannot be bypassed by piped commands or escapes
6. Attempts to write files or modify system state will be blocked by the OS
```

## Testing & Validation

All security implementations are validated through comprehensive unit tests:

**Test Coverage**:
- 80 total tests across all providers
- Specific security tests for each provider
- Config file generation and cleanup validation
- Security warning injection verification
- Tool restriction enforcement testing

**Key Test Files**:
- `test_claude_provider.py`: 20 tests
- `test_gemini_provider.py`: 5 tests
- `test_opencode_provider.py`: 30 tests (includes security-specific tests)
- `test_cursor_agent_provider.py`: 7 tests (includes config creation/cleanup)
- `test_codex_provider.py`: 6 tests (includes sandbox warning injection)

See [Security Testing Documentation](./TESTING.md) for detailed validation procedures.

## Adding New Providers: Security Checklist

When adding a new AI provider, ensure the following security requirements:

- [ ] **Read-Only Enforcement**: Implement mechanism to block write operations
- [ ] **Tool Allowlist**: Define explicit list of allowed read-only tools
- [ ] **Tool Denylist**: Define explicit list of blocked dangerous tools
- [ ] **System Prompt Warning**: Inject security notice into all prompts
- [ ] **Security Flags**: Set `security_flags={"writes_allowed": False, "read_only": True}`
- [ ] **Test Coverage**: Add tests for:
  - [ ] Config/restriction creation
  - [ ] Security warning injection
  - [ ] Cleanup of temporary files (if applicable)
  - [ ] Attempt to use blocked tools (should fail gracefully)
- [ ] **Documentation**: Update this document with new provider's security model
- [ ] **Known Limitations**: Document any bypass vulnerabilities
- [ ] **Comparison Table**: Add to security matrix above

## Related Documentation

- [Threat Model](./THREAT_MODEL.md) - Attack scenarios and protection mechanisms
- [Security Testing](./TESTING.md) - Validation procedures
- [Provider Overview](../providers/OVERVIEW.md) - General provider documentation
- [Opencode Provider Security](../providers/OPENCODE.md#security-model) - Detailed Opencode security
