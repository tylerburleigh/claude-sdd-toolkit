# How `sdd fidelity-review` Selects AI Models

This document clarifies how the `sdd fidelity-review` command selects which AI models to consult.

### Executive Summary

The `sdd fidelity-review` command **does not** use the `consensus.agents` list from `ai_config.yaml`. The number of models consulted is determined by one of two methods:

1.  **Command-Line Override:** Explicitly specifying tools with the `--ai-tools` flag.
2.  **Configuration-Based:** Using all tools that are both enabled in the configuration and installed locally.

---

### 1. Command-Line Control (`--ai-tools`)

If you provide the `--ai-tools` flag, the command will *only* use the tools you specify. This is the most direct way to control which models are consulted for a single run.

**Example:**
To consult only `gemini` and `claude`, regardless of the configuration file:
```bash
sdd fidelity-review <SPEC_ID> --ai-tools gemini claude
```

---

### 2. Configuration-Based Control

When the `--ai-tools` flag is **not** used, the command falls back to the `ai_config.yaml` file. It will consult **all** tools that meet the following two conditions:

1.  The tool has `enabled: true` in the `tools:` section of the configuration file.
2.  The tool's command-line interface is installed and available in the system's `PATH`.

**Example:**
To configure the system to consult only `gemini` and `claude` by default, you would edit `claude_skills/common/templates/setup/ai_config.yaml` like this:

```yaml
tools:
  gemini:
    command: gemini
    enabled: true    # This tool will be used
    description: Strategic analysis and hypothesis validation
  cursor-agent:
    command: cursor-agent
    enabled: false   # This tool will be skipped
    description: Repository-wide pattern discovery
  codex:
    command: codex
    enabled: false   # This tool will be skipped
    description: Code-level review and bug fixes
  claude:
    command: claude
    enabled: true    # This tool will be used
    description: Extended reasoning and analysis with read-only access
```
