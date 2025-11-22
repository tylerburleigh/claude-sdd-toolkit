# Configuration

Complete configuration reference for the SDD Toolkit. This guide covers project setup, CLI configuration, AI model configuration, and git integration.

## Table of Contents

- [Quick Setup](#quick-setup)
- [Project Configuration](#project-configuration)
- [CLI Configuration](#cli-configuration)
- [AI Model Configuration](#ai-model-configuration)
- [Git Integration Configuration](#git-integration-configuration)
- [Configuration Precedence](#configuration-precedence)
- [Environment Variables](#environment-variables)
- [Configuration Examples](#configuration-examples)
- [Troubleshooting Configuration](#troubleshooting-configuration)

---

## Quick Setup

### Initial Setup

Run this once per project to create all configuration files:

```
/sdd-setup
```

This creates:
- `.claude/settings.local.json` - Required permissions for spec operations
- `.claude/sdd_config.json` - CLI output preferences and work mode
- `.claude/ai_config.yaml` - AI model defaults and tool priority

**Prerequisites:**
- Claude Code installed and running
- SDD Toolkit plugin installed
- Python package installed (`pip install -e .`)

### Verify Setup

```bash
# Check that sdd command is available
sdd --version

# Verify configuration files exist
ls -la .claude/
```

Expected output:
```
settings.local.json
sdd_config.json
ai_config.yaml
```

---

## Project Configuration

### Directory Structure

The toolkit expects this structure in your project:

```
your-project/
├── specs/
│   ├── pending/              # Backlog specs
│   ├── active/               # Current work
│   ├── completed/            # Finished specs
│   ├── archived/             # Cancelled work
│   │
│   ├── .reports/             # Gitignored - fidelity reports
│   ├── .reviews/             # Gitignored - plan reviews
│   ├── .backups/             # Gitignored - spec backups
│   └── .human-readable/      # Gitignored - rendered specs
│
├── .claude/
│   ├── settings.local.json   # Permissions (created by /sdd-setup)
│   ├── sdd_config.json       # CLI preferences
│   ├── ai_config.yaml        # AI defaults
│   └── git_config.json       # Git integration (optional)
│
├── docs/                     # Optional
│   ├── codebase.json         # Machine-readable docs
│   ├── index.md              # Human-readable docs
│   ├── project-overview.md
│   ├── architecture.md
│   └── component-inventory.md
│
└── [your source code]
```

### settings.local.json

**Location**: `.claude/settings.local.json`

**Purpose**: Grants Claude Code permissions to read/write spec files and configuration.

**Created by**: `/sdd-setup` command

**Example:**
```json
{
  "dangerouslySkipPermissionsForPaths": {
    "Write": [
      "specs/**",
      ".claude/sdd_config.json",
      ".claude/ai_config.yaml"
    ],
    "Read": [
      "specs/**",
      ".claude/**"
    ],
    "Edit": [
      "specs/**"
    ]
  }
}
```

**Do not manually edit** unless you need to add additional permission paths.

### .gitignore Recommendations

Add to your `.gitignore`:

```gitignore
# SDD Toolkit
specs/.reports/
specs/.reviews/
specs/.backups/
specs/.human-readable/

# Optional: Ignore all pending specs (team preference)
# specs/pending/
```

**Keep in git:**
- `specs/active/` - Track active work
- `specs/completed/` - Archive of finished features
- `.claude/sdd_config.json` - Share team preferences
- `.claude/ai_config.yaml` - Share AI model defaults

---

## CLI Configuration

### sdd_config.json

**Location**: `.claude/sdd_config.json`

**Purpose**: Controls CLI output formatting, work mode, and default behavior.

**Full Example:**
```json
{
  "work_mode": "single",
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "quiet"
  }
}
```

### Configuration Options

#### work_mode

Controls task execution behavior in `sdd-next` skill.

| Value | Behavior | Use When |
|-------|----------|----------|
| `"single"` (default) | Complete one task, then ask user | You want full control over each task |
| `"autonomous"` | Complete all tasks in phase automatically | You want hands-off phase completion |

**Example:**
```json
{
  "work_mode": "autonomous"
}
```

**Switching modes:**

You can change work mode at any time. The `sdd-next` skill reads this config each time it runs.

```json
// Switch to autonomous mode
{"work_mode": "autonomous"}

// Switch back to single task mode
{"work_mode": "single"}
```

#### output.default_mode

Default output format for CLI commands.

| Value | Format | Use When |
|-------|--------|----------|
| `"json"` | Machine-readable JSON | Using with Claude Code (recommended) |
| `"rich"` | Terminal-enhanced with colors/tables | Interactive terminal use |
| `"plain"` | Plain text | Scripting or simple terminals |

**Example:**
```json
{
  "output": {
    "default_mode": "json"
  }
}
```

**Override per-command:**
```bash
sdd progress my-spec --json        # Force JSON
sdd progress my-spec --rich        # Force rich output
sdd progress my-spec --plain       # Force plain text
```

#### output.json_compact

Enable compact JSON formatting (~30% token savings).

| Value | Effect |
|-------|--------|
| `true` | Compact JSON (no whitespace) |
| `false` | Pretty-printed JSON (readable) |

**Token Savings:**

| Command | Normal | Compact | Savings |
|---------|--------|---------|---------|
| `sdd progress` | ~120 tokens | ~84 tokens | 30% |
| `sdd prepare-task` | ~400 tokens | ~280 tokens | 30% |
| `sdd next-task` | ~55 tokens | ~37 tokens | 33% |

**Example:**
```json
{
  "output": {
    "json_compact": true
  }
}
```

**Override per-command:**
```bash
sdd progress my-spec --json --compact      # Force compact
sdd progress my-spec --json --no-compact   # Force pretty
```

#### output.default_verbosity

Default verbosity level for command output.

| Value | Output Level | Includes |
|-------|--------------|----------|
| `"quiet"` | Minimal | Essential data only |
| `"normal"` | Standard | Common fields |
| `"verbose"` | Maximum | All available data |

**Example:**
```json
{
  "output": {
    "default_verbosity": "quiet"
  }
}
```

**Override per-command:**
```bash
sdd progress my-spec --quiet      # Minimal output
sdd progress my-spec --normal     # Standard output
sdd progress my-spec --verbose    # Maximum detail
```

### Complete Example

**Recommended for Claude Code:**

```json
{
  "work_mode": "single",
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "quiet"
  }
}
```

**Benefits:**
- Single task mode for maximum control
- JSON output for Claude Code compatibility
- Compact formatting to save context tokens
- Quiet verbosity to reduce noise

---

## AI Model Configuration

### ai_config.yaml

**Location**: `.claude/ai_config.yaml`

**Purpose**: Configure AI model defaults and tool fallback priority.

**Full Example:**
```yaml
# Global tool fallback priority
tool_priority:
  default:
    - gemini
    - cursor-agent
    - codex
    - claude

# Per-skill configuration
run-tests:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1

sdd-plan-review:
  tool_priority:
    - cursor-agent
    - gemini
  models:
    gemini: gemini-2.5-flash
    cursor-agent: composer-1

sdd-fidelity-review:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1

llm-doc-gen:
  tool_priority:
    - cursor-agent
    - gemini
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1
```

### Configuration Options

#### tool_priority.default

Fallback order when a tool fails or is unavailable.

**Example:**
```yaml
tool_priority:
  default:
    - gemini        # Try gemini first
    - cursor-agent  # Fall back to cursor-agent
    - codex         # Then codex
    - claude        # Finally claude
```

**Use case**: If gemini API is rate-limited, automatically try cursor-agent.

#### Per-skill tool_priority

Override tool order for specific skills.

**Example:**
```yaml
run-tests:
  tool_priority:
    - gemini          # Prefer gemini for test debugging
    - cursor-agent    # Fall back to cursor-agent

sdd-plan-review:
  tool_priority:
    - cursor-agent    # Prefer cursor-agent for reviews
    - gemini
```

**Use case**: Use faster/cheaper models for some tasks, premium models for others.

#### Per-skill models

Specify which model variant to use per tool.

**Example:**
```yaml
run-tests:
  models:
    gemini: gemini-2.5-flash       # Fast, cheap for debugging
    cursor-agent: composer-1       # Standard model

sdd-plan-review:
  models:
    gemini: gemini-2.5-pro         # Premium for reviews
    cursor-agent: composer-1
```

### Available Providers

| Provider | Models | Notes |
|----------|--------|-------|
| **gemini** | `gemini-2.5-pro`, `gemini-2.5-flash` | Google's Gemini models |
| **cursor-agent** | `composer-1`, `composer-2` | Cursor IDE (1M context) |
| **codex** | `sonnet-4.5`, `haiku-4.5` | Anthropic Codex CLI |
| **claude** | `sonnet-4.5`, `haiku-4.5` | Claude with read-only restrictions |
| **opencode** | Various | OpenCode AI (requires Node.js ≥18) |

### CLI Overrides

Override models for a single command:

```bash
# Single model for all operations
sdd test run --model gemini-2.5-flash

# Tool-specific overrides
sdd doc analyze-with-ai . \
  --model gemini=gemini-2.5-flash \
  --model cursor-agent=composer-2
```

### Read-Only Providers

**Claude and OpenCode** providers enforce read-only tool access:

**Allowed:**
- Read files
- Search code (Grep, Glob)
- Web search

**Blocked:**
- Write files
- Edit files
- Run bash commands

**Use case**: Safe for untrusted or experimental prompts.

---

## Git Integration Configuration

### git_config.json (Optional)

**Location**: `.claude/git_config.json`

**Purpose**: Configure automatic git operations during SDD workflow.

**Created**: Manually copy from template

**Template location**: `~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills/common/templates/setup/git_config.json`

### Configuration Options

```json
{
  "enabled": false,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "commit_cadence": "task",
  "file_staging": {
    "show_before_commit": true
  },
  "ai_pr": {
    "enabled": true,
    "model": "sonnet",
    "include_journals": true,
    "include_diffs": true,
    "max_diff_size_kb": 50
  }
}
```

#### enabled

Master switch for git integration.

| Value | Effect |
|-------|--------|
| `false` (default) | No automatic git operations |
| `true` | Enable auto-branch, auto-commit, etc. based on settings |

#### auto_branch

Automatically create feature branches when starting specs.

**Branch naming:** `sdd/<spec-id>`

**Example:**
```bash
# Starting spec: user-auth-2025-11-22-001
# Creates branch: sdd/user-auth-2025-11-22-001
```

#### auto_commit

Automatically commit changes when completing tasks.

**Commit message format:**
```
Complete task-1-2: Implement password hashing

- Used bcrypt with cost factor 12
- Added 8 unit tests
- All tests passing

[spec: user-auth-2025-11-22-001]
```

#### auto_push

Automatically push commits to remote after committing.

**Warning:** Only enable if you're confident in auto-commits.

#### commit_cadence

When to automatically commit.

| Value | Commits |
|-------|---------|
| `"task"` | After completing each task |
| `"phase"` | After completing each phase |
| `"manual"` | Never (manual commits only) |

#### file_staging.show_before_commit

Show files before committing (safety check).

```
Files to commit:
  - src/auth/password.py
  - tests/test_auth.py

Proceed with commit? [Y/n]
```

#### ai_pr Configuration

Configure AI-powered pull request creation.

| Setting | Purpose |
|---------|---------|
| `enabled` | Enable AI PR creation |
| `model` | Model for PR description ("sonnet" or "haiku") |
| `include_journals` | Include task journals in PR context |
| `include_diffs` | Include git diffs in PR context |
| `max_diff_size_kb` | Maximum diff size to include (prevents huge context) |

### Example Configurations

**Conservative (recommended):**
```json
{
  "enabled": false,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "commit_cadence": "task"
}
```

**Aggressive:**
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": true,
  "commit_cadence": "task"
}
```

**Manual control:**
```json
{
  "enabled": false,
  "commit_cadence": "manual"
}
```

---

## Configuration Precedence

Configuration is resolved in this order (highest to lowest priority):

### 1. CLI Flags (Highest Priority)

```bash
sdd progress my-spec --json --compact --verbose
```

Overrides everything else for this command only.

### 2. Config File

`.claude/sdd_config.json` settings:

```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "quiet"
  }
}
```

### 3. Built-in Defaults (Lowest Priority)

If no config or flags provided:

```python
default_mode = "rich"
json_compact = False
default_verbosity = "normal"
```

### Example

**Config file:**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Commands:**
```bash
# Uses config: JSON, compact
sdd progress my-spec

# Overrides to rich
sdd progress my-spec --rich

# Overrides to pretty (not compact)
sdd progress my-spec --json --no-compact
```

---

## Environment Variables

The toolkit doesn't use environment variables for primary configuration, but some tools may require them.

### AI Provider API Keys

Depending on which providers you use:

| Provider | Environment Variable | Required |
|----------|---------------------|----------|
| Gemini | `GEMINI_API_KEY` | If using gemini |
| OpenCode | `OPENCODE_API_KEY` | If using opencode |
| Claude | `ANTHROPIC_API_KEY` | If using claude provider |

**Example:**
```bash
export GEMINI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

### GitHub CLI

For PR creation:

```bash
gh auth login
```

No environment variable needed; gh CLI handles authentication.

---

## Configuration Examples

### Scenario 1: Solo Developer (Maximum Automation)

**Goal**: Minimize manual steps, auto-commit everything.

**sdd_config.json:**
```json
{
  "work_mode": "autonomous",
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "quiet"
  }
}
```

**git_config.json:**
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "commit_cadence": "task",
  "ai_pr": {
    "enabled": true
  }
}
```

### Scenario 2: Team Environment (Manual Control)

**Goal**: Full control, manual commits, review before merging.

**sdd_config.json:**
```json
{
  "work_mode": "single",
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "normal"
  }
}
```

**git_config.json:**
```json
{
  "enabled": false,
  "commit_cadence": "manual"
}
```

### Scenario 3: Context-Conscious (Minimal Tokens)

**Goal**: Save maximum context tokens for large codebases.

**sdd_config.json:**
```json
{
  "work_mode": "single",
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "default_verbosity": "quiet"
  }
}
```

**ai_config.yaml:**
```yaml
tool_priority:
  default:
    - gemini    # Fast, cheap models

run-tests:
  models:
    gemini: gemini-2.5-flash

sdd-plan-review:
  models:
    gemini: gemini-2.5-flash
```

### Scenario 4: Premium Quality (Best Models)

**Goal**: Use best models for highest quality reviews and analysis.

**ai_config.yaml:**
```yaml
tool_priority:
  default:
    - cursor-agent
    - gemini

sdd-plan-review:
  models:
    cursor-agent: composer-1
    gemini: gemini-2.5-pro

sdd-fidelity-review:
  models:
    cursor-agent: composer-1
    gemini: gemini-2.5-pro

llm-doc-gen:
  models:
    cursor-agent: composer-1
    gemini: gemini-2.5-pro
```

---

## Troubleshooting Configuration

### Issue: "/sdd-setup creates no files"

**Diagnosis:**
```bash
ls -la .claude/
# Empty or doesn't exist
```

**Solution:**
1. Ensure Claude Code is running
2. Ensure SDD plugin is installed
3. Run `/sdd-setup` again
4. Check Claude Code logs for errors

### Issue: "sdd command not found"

**Diagnosis:**
```bash
which sdd
# command not found
```

**Solution:**
```bash
# Reinstall Python package
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .

# Verify installation
which sdd
sdd --version
```

### Issue: "Invalid JSON in sdd_config.json"

**Diagnosis:**
```bash
sdd progress my-spec
# Error: JSONDecodeError
```

**Solution:**
```bash
# Validate JSON
cat .claude/sdd_config.json | python -m json.tool

# If invalid, recreate from template
rm .claude/sdd_config.json
/sdd-setup
```

### Issue: "AI provider not working"

**Diagnosis:**
```bash
sdd test check-tools
# gemini: FAILED
```

**Solution:**

**For gemini:**
```bash
export GEMINI_API_KEY="your-key-here"
gemini "test"  # Verify it works
```

**For cursor-agent:**
- Ensure Cursor IDE is running
- Check Composer is accessible

**Fallback:**
Update `ai_config.yaml` to use different tool:
```yaml
tool_priority:
  default:
    - codex  # Use codex instead
```

### Issue: "Git operations failing"

**Diagnosis:**
```bash
# Error: git not configured
# Error: gh not authenticated
```

**Solution:**

**For git:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**For gh CLI:**
```bash
gh auth login
```

**Disable git integration if not needed:**
```json
{
  "enabled": false
}
```

### Issue: "Permission denied on specs/"

**Diagnosis:**
```
Error: Permission denied: specs/active/my-spec.json
```

**Solution:**

1. Verify `.claude/settings.local.json` exists
2. Check permissions include `specs/**`
3. Run `/sdd-setup` to recreate permissions
4. Restart Claude Code

---

## Next Steps

Now that you understand configuration:

- **Try different work modes**: Experiment with `single` vs `autonomous`
- **Optimize for your workflow**: Configure based on your team's needs
- **Review AI config**: Choose models that balance cost and quality
- **Explore git integration**: Consider auto-commit for solo projects

---

**Related Documentation:**
- [Core Concepts](core-concepts.md) - Understand the system
- [Skills Reference](skills-reference.md) - How to use skills
- [Workflows](workflows.md) - Common development patterns
- [Troubleshooting](troubleshooting.md) - Solve common issues
