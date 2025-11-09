# Fidelity Review Configuration Guide

This guide explains how to configure the sdd-fidelity-review skill for your environment.

## Table of Contents

- [Tool Configuration](#tool-configuration)
- [Model Configuration](#model-configuration)
- [Consensus Configuration](#consensus-configuration)
- [Auto-Trigger Behavior](#auto-trigger-behavior)
- [Configuration Best Practices](#configuration-best-practices)

---

## Tool Configuration

### Location

`skills/sdd-fidelity-review/config.yaml`

### Structure

```yaml
tools:
  gemini:
    description: "Strategic fidelity assessment, deviation impact analysis, recommendations"
    command: gemini
    enabled: true

  codex:
    description: "Code-level comparison, detailed implementation verification, fix suggestions"
    command: codex
    enabled: false

  cursor-agent:
    description: "Repository-wide pattern discovery, cross-file consistency checks"
    command: cursor-agent
    enabled: true
```

### Configuration Fields

- **name** (key): Tool identifier used in commands and routing
- **description**: Human-readable description tailored for fidelity review use cases
- **command**: Binary name to search for in PATH
- **enabled**: Boolean flag to enable/disable tool (defaults to true if omitted)

### Managing Tools

**Enable/Disable Tools:**

```yaml
tools:
  codex:
    description: "Code-level comparison..."
    command: codex
    enabled: true  # Enable for detailed code-level fidelity checks
```

---

## Model Configuration

Configure which models to use for each tool during fidelity reviews.

### Structure

```yaml
models:
  gemini:
    priority: [gemini-2.5-pro]
    flags: []

  codex:
    priority: [composer-1]
    flags: [--skip-git-repo-check]

  cursor-agent:
    priority: [composer-1]
    flags: []
```

### Configuration Fields

- **priority**: List of models to try in order of preference
- **flags**: Additional command-line flags passed to the tool

---

## Consensus Configuration

Configure multi-agent consultation pairs for consensus-based fidelity reviews.

### Agent Pairs

```yaml
consensus:
  pairs:
    default:
      - cursor-agent
      - gemini
    code-focus:
      - cursor-agent
      - gemini
    discovery-focus:
      - cursor-agent
      - gemini
```

Each pair defines which two agents should be consulted together for multi-agent analysis during fidelity reviews.

### Auto-Trigger Behavior

Automatic agent pair selection based on deviation type:

```yaml
consensus:
  auto_trigger:
    default: default
    major_deviation: code-focus
    missing_functionality: discovery-focus
    cross_file: discovery-focus
```

**Trigger scenarios:**
- `major_deviation`: Uses code-focus pair for detailed code-level analysis
- `missing_functionality`: Uses discovery-focus pair to find missing implementations
- `cross_file`: Uses discovery-focus pair for cross-file consistency checks

---

## Consultation Settings

Configure timeout and consultation behavior:

```yaml
consultation:
  timeout_seconds: 90  # Maximum time to wait for AI tool responses
```

---

## Configuration Best Practices

### Tool Selection

**For thorough reviews:**
- Enable all tools (gemini, codex, cursor-agent)
- Use consensus pairs for critical deviation analysis

**For quick reviews:**
- Enable only gemini and cursor-agent
- Disable consensus to speed up reviews

### Model Selection

**Strategic analysis:**
- Use gemini-2.5-pro for high-level fidelity assessment
- Good for deviation impact analysis and recommendations

**Code-level verification:**
- Use composer-1 (codex/cursor-agent) for detailed implementation checks
- Good for line-by-line spec compliance

### Consensus Configuration

**When to use multi-agent consensus:**
- Major deviations from spec
- Missing critical functionality
- Cross-file consistency issues
- High-impact architectural changes

**When to skip consensus:**
- Minor deviations (cosmetic changes)
- Exact spec matches
- Time-sensitive reviews

---

## Example Configurations

### Thorough Review Configuration

```yaml
tools:
  gemini:
    enabled: true
  codex:
    enabled: true
  cursor-agent:
    enabled: true

consensus:
  auto_trigger:
    major_deviation: code-focus
    missing_functionality: discovery-focus
```

### Quick Review Configuration

```yaml
tools:
  gemini:
    enabled: true
  codex:
    enabled: false
  cursor-agent:
    enabled: true

consensus:
  auto_trigger:
    default: default  # Minimal consensus usage
```

---

For more information about AI tool configuration, see `claude_skills/common/ai_config.py`.
