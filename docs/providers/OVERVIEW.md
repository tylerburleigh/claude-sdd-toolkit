# AI Provider Overview

## Introduction

The claude-sdd-toolkit supports five AI providers for code analysis and documentation generation. Each provider has different capabilities, security models, and setup requirements. This document provides a comprehensive comparison and setup guide for all providers.

## Quick Comparison

| Provider | Security | Setup Complexity | Prerequisites | Best For |
|----------|----------|------------------|---------------|----------|
| **Codex** | ⭐⭐⭐⭐⭐ OS-level | Easy | Codex CLI | Maximum security, production use |
| **Claude** | ⭐⭐⭐⭐ Strong | Easy | Claude CLI | General analysis, high security |
| **Gemini** | ⭐⭐⭐⭐ Strong | Easy | Gemini CLI, API key | Large context (1M), high security |
| **Opencode** | ⭐⭐⭐ Good | Medium | Node.js, npm | Flexible, OpenCode ecosystem |
| **Cursor Agent** | ⭐⭐⭐ Good | Medium | Cursor subscription | Cursor IDE integration |

## Security Comparison

| Provider | Enforcement | Shell Access | MCP Safe | Known Issues |
|----------|-------------|--------------|----------|--------------|
| **Codex** | OS kernel (Seatbelt/Landlock) | Read-only (sandboxed) | ✅ Yes | None |
| **Claude** | CLI flags (allowlist/denylist) | Read-only (filtered) | ✅ Yes | ⚠️ Pipe bypass |
| **Gemini** | CLI flags (allowlist) | Read-only (filtered) | ✅ Yes | ⚠️ Pipe bypass |
| **Opencode** | Config file + permissions | ❌ Disabled | ⚠️ No | MCP bypass |
| **Cursor Agent** | Temp config file | Read-only (filtered) | ✅ Yes | ⚠️ Weaker model |

See [Security Architecture](../security/PROVIDER_SECURITY.md) for detailed security analysis.

---

## Provider Details

### 1. Codex Provider ⭐ Recommended for Production

**Description**: OpenAI Codex CLI with native OS-level read-only sandboxing.

**Security**: Most robust - uses platform-specific OS sandboxing that cannot be bypassed.

**Prerequisites**:
- Codex CLI binary installed
- OpenAI API key (configured in Codex CLI)

**Installation**:

```bash
# Install Codex CLI (varies by platform)
# macOS:
brew install codex

# Linux/Windows: See Codex CLI documentation
```

**Configuration**:

```yaml
# ai_config.yaml
default:
  provider: codex
  model: gpt-5-codex  # or gpt-5-codex-mini (faster)
```

**Verification**:

```bash
codex --version
# Should show: codex-cli 0.61.0 or higher
```

**Security Features**:
- ✅ OS-level sandboxing via `--sandbox read-only` flag
- ✅ macOS: Seatbelt sandbox policy
- ✅ Linux: Landlock LSM + seccomp filters
- ✅ Windows: Restricted token + job objects
- ✅ Cannot be bypassed by pipe commands or tool name tricks

**Allowed Operations**:
- Read files, search, list directories
- Read-only git operations
- File analysis tools
- System information (ps, top, uname)

**Limitations**:
- Requires Codex CLI installation (not just API key)
- Subscription/API costs

**Best For**: Production use, maximum security requirements, critical codebases

---

### 2. Claude Provider

**Description**: Anthropic Claude CLI with tool allowlist/denylist filtering.

**Security**: Strong - explicit tool filtering with detailed Bash command patterns.

**Prerequisites**:
- Claude CLI (official Anthropic CLI)
- Anthropic API key

**Installation**:

```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-cli
# or
brew install claude-cli

# Configure API key
claude configure
```

**Configuration**:

```yaml
# ai_config.yaml
default:
  provider: claude
  model: sonnet  # or haiku (faster)
```

**Verification**:

```bash
claude --version
# Should show Claude CLI version
```

**Security Features**:
- ✅ Explicit allowlist: ~120 read-only operations
- ✅ Explicit denylist: blocks Write, Edit, destructive Bash
- ✅ Granular Bash patterns: `Bash(git log:*)` allows specific git commands
- ⚠️ Pipe command bypass: only first command in pipe is validated

**Allowed Operations**:
- Read, Grep, Glob, Task
- Bash (read-only): cat, ls, grep, git log, find, stat, jq, etc.
- ~120 total allowed operations

**Disallowed Operations**:
- Write, Edit, Delete
- WebSearch, WebFetch (prevents data exfiltration)
- Bash (write): rm, mv, cp, chmod, sed, awk
- Git write: add, commit, push, merge, rebase
- Package installs: npm/pip/apt/brew install
- System operations: sudo, reboot, shutdown

**Known Limitations**:
- ⚠️ Piped commands bypass tool checks: `cat file.txt | dangerous-command`
- System prompt warns about this limitation

**Best For**: General code analysis, documentation generation, high security needs

---

### 3. Gemini Provider

**Description**: Google Gemini CLI with large context window (1M tokens).

**Security**: Strong - similar to Claude with tool allowlist filtering.

**Prerequisites**:
- Gemini CLI
- Google AI API key

**Installation**:

```bash
# Install Gemini CLI
npm install -g @google/generative-ai-cli
# or
pip install google-generativeai-cli

# Configure API key
export GOOGLE_API_KEY="your-api-key"
```

**Configuration**:

```yaml
# ai_config.yaml
default:
  provider: gemini
  model: gemini-2.5-flash  # or gemini-2.5-pro
```

**Verification**:

```bash
gemini --version
# Should show Gemini CLI version
```

**Security Features**:
- ✅ Tool allowlist with class and function names
- ✅ Supports both naming conventions: `ReadFileTool` and `read_file`
- ⚠️ Pipe command bypass: similar to Claude

**Allowed Operations**:
- ReadFileTool, GrepTool, LSTool, GlobTool
- ShellTool (read-only): cat, ls, grep, git log, etc.
- Web operations excluded for security

**Known Limitations**:
- ⚠️ Piped commands bypass tool checks
- ⚠️ `PIPED_COMMAND_WARNING` injected into system prompts

**Best For**: Large context needs (1M tokens), complex codebases, high security

---

### 4. Opencode Provider

**Description**: OpenCode AI with Node.js SDK integration and dual-layer security.

**Security**: Good - config-based tool blocking with permission denial.

**Prerequisites**:
- Node.js >= 18.x
- OpenCode AI account and API key
- npm (for dependency installation)

**Installation**:

See [detailed Opencode documentation](./OPENCODE.md) for complete setup instructions.

**Quick Setup**:

```bash
# 1. Install OpenCode SDK globally
npm install -g @opencode-ai/sdk

# 2. Install provider dependencies
cd "$(python -c 'import claude_skills.common.providers as p; from pathlib import Path; print(Path(p.__file__).parent)')"
npm install

# 3. Set API key
export OPENCODE_API_KEY="your-api-key"
```

**Configuration**:

```yaml
# ai_config.yaml
default:
  provider: opencode
  model: default  # Uses ai_config.yaml routing
```

**Security Features**:
- ✅ Dual-layer protection: tool config + permission denial
- ✅ Temporary config file per provider instance
- ✅ No shell access (stricter than Claude/Gemini)
- ⚠️ MCP tool bypass: MCP tools may not respect config blocks

**Allowed Operations**:
- Read, Grep, Glob, List, Task
- **No shell/Bash access** (more restrictive)
- **No web operations** (prevents data exfiltration)

**Known Limitations**:
- ⚠️ MCP tool blocking may not work ([issue #3756](https://github.com/opencode-ai/opencode/issues/3756))
- ⚠️ Server-wide config affects all sessions
- ⚠️ Requires Node.js runtime and npm dependencies

**Best For**: OpenCode ecosystem users, projects requiring MCP servers

---

### 5. Cursor Agent Provider

**Description**: Cursor IDE's AI agent accessible via CLI with 1M context window.

**Security**: Good - temporary config file with permission system.

**Prerequisites**:
- Cursor subscription (Pro or Business)
- Cursor Agent CLI installed
- macOS or Linux (Windows support pending)

**Installation**:

```bash
# Install Cursor Agent CLI
curl https://cursor.com/install -fsSL | bash

# Verify installation
cursor-agent --version
```

**Configuration**:

```yaml
# ai_config.yaml
default:
  provider: cursor-agent
  model: composer-1  # or gpt-5-codex
```

**Security Features**:
- ✅ Temporary `.cursor/cli-config.json` per execution
- ✅ Permission format: Read(pathOrGlob), Write(pathOrGlob), Shell(commandBase)
- ⚠️ Weaker security model: deprecated denylist had known bypasses
- ✅ We use allowlist approach instead

**Allowed Operations**:
- Read, Grep, Glob, List, Task
- Shell (read-only): cat, ls, grep, git log, find, stat, etc.
- Web operations excluded for security

**Known Limitations**:
- ⚠️ Weaker security compared to Codex/Claude/Gemini
- ⚠️ Shell permission granularity: only first token validated (e.g., "git" allows all git commands)
- ⚠️ macOS/Linux only (Windows not yet supported)

**Best For**: Cursor IDE users, projects with Cursor subscriptions

---

## Setup Recommendations

### For Maximum Security

**Use Codex**:
```yaml
default:
  provider: codex
  model: gpt-5-codex
```

Codex provides OS-level sandboxing that cannot be bypassed.

---

### For General Use

**Use Claude or Gemini**:
```yaml
default:
  provider: claude
  model: sonnet
```

Both provide strong security with comprehensive tool filtering.

---

### For Large Codebases

**Use Gemini** (1M context window):
```yaml
default:
  provider: gemini
  model: gemini-2.5-pro
```

---

### For OpenCode Ecosystem

**Use Opencode** (MCP support, Node.js integration):
```yaml
default:
  provider: opencode
  model: default
```

---

## Provider Routing

You can configure different providers for different tasks:

```yaml
# ai_config.yaml
default:
  provider: codex
  model: gpt-5-codex

# Fast queries use Haiku
quick_queries:
  provider: claude
  model: haiku

# Large context needs use Gemini
large_context:
  provider: gemini
  model: gemini-2.5-pro
```

---

## Common Issues

### "Provider not available"

**Symptoms**: `ProviderUnavailableError` when trying to use a provider

**Solutions**:

1. **Claude**: Verify `claude --version` works
2. **Gemini**: Check API key is set: `echo $GOOGLE_API_KEY`
3. **Opencode**: Verify Node.js dependencies: `cd providers/ && npm list`
4. **Cursor Agent**: Verify binary: `which cursor-agent`
5. **Codex**: Verify installation: `codex --version`

---

### API Key Issues

**Symptoms**: Authentication errors, 401 responses

**Solutions**:

```bash
# Claude
claude configure

# Gemini
export GOOGLE_API_KEY="your-key"

# Opencode
export OPENCODE_API_KEY="your-key"

# Codex
codex configure
```

---

### Permission Denied / Write Blocked

**Expected Behavior**: All providers block write operations for security.

**If you need write access**:
- ❌ Don't disable security features
- ✅ Use the AI for analysis only
- ✅ Apply suggested changes manually
- ✅ Review AI outputs before executing

---

## Testing Provider Setup

### Test Provider Availability

```python
from claude_skills.common.providers import available_providers

providers = available_providers()
for meta in providers:
    print(f"{meta.provider_name}: {meta.models}")
```

### Test Provider Execution

```python
from claude_skills.common.providers import resolve_provider, GenerationRequest

provider = resolve_provider("codex")
request = GenerationRequest(prompt="List files in current directory")
result = provider.generate(request)
print(result.content)
```

### Verify Security Restrictions

```python
# Should explain write operations are blocked
request = GenerationRequest(prompt="Create a file called test.txt")
result = provider.generate(request)
print(result.content)  # Should mention read-only mode
```

---

## Environment Variables

| Variable | Provider | Purpose |
|----------|----------|---------|
| `CLAUDE_API_KEY` | Claude | API authentication |
| `GOOGLE_API_KEY` | Gemini | API authentication |
| `OPENCODE_API_KEY` | Opencode | API authentication |
| `OPENCODE_SERVER_URL` | Opencode | Server endpoint (default: http://localhost:4096) |
| `CURSOR_API_KEY` | Cursor Agent | API authentication |
| `CLAUDE_CLI_BINARY` | Claude | Custom binary path |
| `GEMINI_CLI_BINARY` | Gemini | Custom binary path |
| `CODEX_CLI_BINARY` | Codex | Custom binary path |
| `CURSOR_AGENT_CLI_BINARY` | Cursor Agent | Custom binary path |

---

## Performance Comparison

| Provider | Typical Response Time | Streaming | Context Window |
|----------|----------------------|-----------|----------------|
| **Codex** | Fast (~2-5s) | ✅ Yes | Model-dependent |
| **Claude** | Fast (~2-5s) | ✅ Yes | 200K tokens |
| **Gemini** | Fast (~2-5s) | ✅ Yes | 1M tokens |
| **Opencode** | Medium (~5-10s) | ✅ Yes | Model-dependent |
| **Cursor Agent** | Medium (~5-10s) | ✅ Yes | 1M tokens |

*Times approximate, vary by query complexity and API latency*

---

## Cost Comparison

| Provider | Pricing Model | Typical Cost |
|----------|--------------|--------------|
| **Codex** | API usage | $$$ |
| **Claude** | API usage | $$ |
| **Gemini** | Free tier + paid | $ |
| **Opencode** | Subscription + API | $$ |
| **Cursor Agent** | Subscription | $$ (included in Cursor Pro) |

*Costs vary significantly by usage - check provider pricing pages*

---

## Migration Between Providers

Switching providers is simple - just update `ai_config.yaml`:

```yaml
# Before
default:
  provider: opencode
  model: default

# After
default:
  provider: codex
  model: gpt-5-codex
```

The toolkit handles provider differences automatically.

---

## Related Documentation

- [Provider Security Architecture](../security/PROVIDER_SECURITY.md) - Detailed security analysis
- [Threat Model](../security/THREAT_MODEL.md) - Attack scenarios and mitigations
- [Security Testing](../security/TESTING.md) - Validation procedures
- [Opencode Provider](./OPENCODE.md) - Detailed Opencode setup and configuration
- [Main README](../../README.md) - Project overview

---

## Support

For provider-specific issues:

- **Codex**: [Codex CLI Documentation](https://docs.openai.com/codex-cli)
- **Claude**: [Claude CLI Documentation](https://docs.anthropic.com/claude-cli)
- **Gemini**: [Gemini API Documentation](https://ai.google.dev/docs)
- **Opencode**: [OpenCode Documentation](https://opencode.ai/docs)
- **Cursor Agent**: [Cursor Documentation](https://cursor.com/docs)

For toolkit issues:
- [GitHub Issues](https://github.com/anthropics/claude-sdd-toolkit/issues)
