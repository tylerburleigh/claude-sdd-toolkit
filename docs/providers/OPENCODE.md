# OpenCode Provider

The OpenCode provider integrates OpenCode AI into the SDD Toolkit's multi-provider AI orchestration system. This provider enables you to use OpenCode AI models for spec reviews, fidelity analysis, test debugging, and other AI-assisted development tasks.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Architecture](#architecture)

## Prerequisites

### Required Software

1. **Node.js >= 16.x**

   OpenCode runs on Node.js. Verify your installation:
   ```bash
   node --version
   ```

   If not installed, download from [nodejs.org](https://nodejs.org/) or use a version manager:
   ```bash
   # Using nvm
   nvm install 16
   nvm use 16

   # Using brew (macOS)
   brew install node@16
   ```

2. **OpenCode AI SDK**

   Install the OpenCode AI Node.js SDK and CLI:
   ```bash
   npm install -g @opencode-ai/sdk
   ```

   This installs both the SDK package and the `opencode` CLI binary.

### API Credentials

You'll need an OpenCode API key. Obtain one from your OpenCode AI account dashboard.

## Installation

### 1. Install OpenCode Dependencies

From your project root (where the SDD Toolkit is installed):

```bash
# Install OpenCode SDK globally or in your project
npm install -g @opencode-ai/sdk

# Or install locally in your project
npm install @opencode-ai/sdk
```

### 2. Verify Installation

Check that the OpenCode provider is available:

```bash
sdd provider-status
```

You should see `opencode` listed among available providers.

Alternatively, check manually:

```bash
# Verify Node.js
node --version

# Verify OpenCode binary
which opencode
opencode --version
```

## Configuration

### Environment Variables

The OpenCode provider requires two environment variables:

1. **`OPENCODE_API_KEY`** (Required)

   Your OpenCode API authentication key.

2. **`OPENCODE_SERVER_URL`** (Optional)

   The OpenCode server endpoint. Defaults to `http://localhost:4096`.

### Setting Environment Variables

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export OPENCODE_API_KEY="your-api-key-here"
export OPENCODE_SERVER_URL="http://localhost:4096"  # Optional, uses default if not set
```

Or create a `.env` file in your project root:

```bash
OPENCODE_API_KEY=your-api-key-here
OPENCODE_SERVER_URL=http://localhost:4096
```

### Enabling in ai_config.yaml

Configure OpenCode in your project's `.claude/ai_config.yaml`:

```yaml
providers:
  opencode:
    enabled: true
    models:
      - default
    default_model: default

tools:
  # Example: Use OpenCode for spec reviews
  sdd-plan-review:
    model_override: opencode:default

  # Example: Use OpenCode for fidelity reviews
  sdd-fidelity-review:
    model_override: opencode:default
```

### Multi-Provider Configuration

You can configure different providers for different tools:

```yaml
providers:
  claude:
    enabled: true
    models:
      - sonnet
      - opus
    default_model: sonnet

  gemini:
    enabled: true
    models:
      - pro
      - flash
    default_model: pro

  opencode:
    enabled: true
    models:
      - default
    default_model: default

tools:
  sdd-plan:
    model_override: claude:sonnet      # Use Claude for planning

  sdd-plan-review:
    model_override: opencode:default   # Use OpenCode for reviews

  sdd-fidelity-review:
    model_override: opencode:default   # Use OpenCode for fidelity checks

  run-tests:
    model_override: gemini:flash       # Use Gemini for test debugging
```

## Usage

### Server Management

The OpenCode provider automatically manages the OpenCode server lifecycle:

1. **Auto-Start**: If the server isn't running, the provider automatically starts it when needed
2. **Port Detection**: Checks if port 4096 (or your configured port) is available
3. **Environment Passing**: Passes `OPENCODE_API_KEY` and `OPENCODE_SERVER_URL` to the server
4. **Graceful Shutdown**: Cleans up server process when the provider is destroyed

### Manual Server Control

You can also manually control the OpenCode server:

```bash
# Start server manually
opencode serve

# Check if server is running
curl http://localhost:4096/health

# Stop server (if started manually)
pkill -f "opencode serve"
```

### Using OpenCode in SDD Workflows

Once configured, OpenCode is automatically used for tools with `model_override: opencode:default`:

```bash
# Run spec review with OpenCode
sdd plan-review my-spec-001

# Run fidelity review with OpenCode
sdd fidelity-review my-spec-001 --scope phase --target phase-2

# Run tests with OpenCode debugging
sdd run-tests pytest tests/
```

### Programmatic Usage

You can also use the OpenCode provider programmatically:

```python
from claude_skills.common.providers import create_provider_context, ProviderHooks

# Create provider
provider = create_provider_context(
    provider_id="opencode",
    hooks=ProviderHooks(),
    model="default"
)

# Generate text
result = provider.generate(
    prompt="Review this code for potential issues",
    max_tokens=2000,
    temperature=0.7
)

print(result.content)
print(f"Tokens used: {result.usage.total_tokens}")
```

## Troubleshooting

### Common Issues

#### 1. Provider Not Available

**Error**: `OpenCode provider not available`

**Causes**:
- Node.js not installed or not in PATH
- OpenCode SDK not installed
- Wrapper script missing

**Solutions**:
```bash
# Check Node.js
node --version
# If missing: brew install node (macOS) or download from nodejs.org

# Check OpenCode SDK
npm list -g @opencode-ai/sdk
# If missing: npm install -g @opencode-ai/sdk

# Verify installation
sdd provider-status
```

#### 2. Server Won't Start

**Error**: `OpenCode server failed to start within 30 seconds`

**Causes**:
- Port 4096 already in use
- Missing API key
- Network/firewall issues

**Solutions**:
```bash
# Check if port is in use
lsof -i :4096

# Kill conflicting process if needed
kill -9 <PID>

# Verify API key is set
echo $OPENCODE_API_KEY

# Try starting server manually to see errors
opencode serve
```

#### 3. API Key Not Found

**Error**: `OpenCode wrapper exited with code 1: API key not configured`

**Solution**:
```bash
# Set API key in environment
export OPENCODE_API_KEY="your-api-key-here"

# Or add to ~/.bashrc or ~/.zshrc
echo 'export OPENCODE_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc

# Verify
echo $OPENCODE_API_KEY
```

#### 4. Invalid JSON Response

**Error**: `Invalid JSON from wrapper`

**Causes**:
- Wrapper script outdated
- Node.js version incompatibility
- Corrupted SDK installation

**Solutions**:
```bash
# Reinstall OpenCode SDK
npm uninstall -g @opencode-ai/sdk
npm install -g @opencode-ai/sdk

# Update Node.js to latest LTS
nvm install --lts
nvm use --lts

# Clear npm cache
npm cache clean --force
```

#### 5. Timeout Errors

**Error**: `OpenCode wrapper timed out after 360s`

**Causes**:
- Large prompt or complex request
- Slow network connection
- Server overloaded

**Solutions**:
```bash
# Increase timeout in provider config (programmatic usage)
provider = create_provider_context(
    provider_id="opencode",
    hooks=ProviderHooks(),
    model="default",
    overrides={"timeout": 600}  # 10 minutes
)

# Or set via environment
export OPENCODE_TIMEOUT=600
```

### Diagnostic Commands

```bash
# Check provider status
sdd provider-status

# List available providers
sdd list-providers

# Test OpenCode directly
echo '{"prompt": "Hello"}' | node src/claude_skills/claude_skills/common/providers/opencode_wrapper.js

# Check server health (if running)
curl http://localhost:4096/health

# View server logs (if started by provider)
ps aux | grep opencode
```

## Advanced Configuration

### Custom Binary Path

Override the Node.js binary location:

```bash
export OPENCODE_BINARY=/usr/local/bin/node
```

### Custom Wrapper Script

Use a custom wrapper script:

```bash
export OPENCODE_WRAPPER_SCRIPT=/path/to/custom/wrapper.js
```

### Custom Server URL

Change the server URL (useful for remote servers):

```bash
export OPENCODE_SERVER_URL=https://opencode-server.example.com:8080
```

### Availability Override

Force enable/disable provider (for testing):

```bash
export OPENCODE_AVAILABLE_OVERRIDE=true   # Force enable
export OPENCODE_AVAILABLE_OVERRIDE=false  # Force disable
```

### Provider Dependencies Injection

For testing or custom setups:

```python
from claude_skills.common.providers.opencode import create_provider

# Custom runner function
def custom_runner(command, *, timeout=None, env=None, input_data=None):
    # Your custom execution logic
    pass

provider = create_provider(
    hooks=ProviderHooks(),
    model="default",
    dependencies={
        "runner": custom_runner,
        "env": {"CUSTOM_VAR": "value"},
        "binary": "/custom/node/path"
    }
)
```

## Architecture

### Component Overview

The OpenCode provider consists of several components:

1. **Provider Class** (`OpenCodeProvider`)
   - Implements `ProviderContext` interface
   - Manages server lifecycle
   - Handles request/response translation

2. **Wrapper Script** (`opencode_wrapper.js`)
   - Node.js script that calls OpenCode SDK
   - Reads JSON from stdin
   - Outputs line-delimited JSON to stdout

3. **Server Management**
   - Auto-detects if server is running (port check)
   - Starts server if needed (`opencode serve`)
   - Passes environment variables to server
   - Cleans up on provider destruction

4. **Response Parser**
   - Parses line-delimited JSON output
   - Aggregates streaming chunks
   - Extracts token usage from metadata

### Request Flow

```
User Request
    ↓
SDD Toolkit (ai_config.yaml routing)
    ↓
OpenCodeProvider._execute()
    ↓
Server Check → Start if needed
    ↓
Build JSON payload
    ↓
Execute: node opencode_wrapper.js --stream
    ↓
Wrapper reads JSON from stdin
    ↓
Wrapper calls @opencode-ai/sdk
    ↓
SDK sends request to OpenCode server
    ↓
Server calls OpenCode AI API
    ↓
Streaming response → Wrapper
    ↓
Wrapper outputs line-delimited JSON
    ↓
Provider parses JSON chunks
    ↓
Aggregated GenerationResult
    ↓
Return to SDD Toolkit
```

### Error Handling

The provider handles several error types:

- **`ProviderUnavailableError`**: Node.js or OpenCode not installed
- **`ProviderTimeoutError`**: Request or server startup timeout
- **`ProviderExecutionError`**: Wrapper script errors, invalid JSON, non-zero exit codes

### Token Usage

Token usage is extracted from the OpenCode response metadata:

```json
{
  "type": "done",
  "response": {
    "text": "...",
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 200,
      "total_tokens": 350
    }
  }
}
```

### Security

- API keys are passed via environment variables (not command-line arguments)
- Server process runs in a new session (detached from parent)
- Wrapper script validates JSON input before processing
- Provider cleans up server process on destruction

## See Also

- [SDD Toolkit AI Configuration](../AI_CONTEXT.md#6-provider---ai-tool-abstraction)
- [Provider Architecture](../ARCHITECTURE.md)
- [Adding New Providers](../AI_CONTEXT.md#adding-a-new-ai-provider)
- [Multi-Provider Workflows](../AI_CONTEXT.md#multi-provider-workflows)
