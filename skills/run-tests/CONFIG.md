# Run-Tests Configuration Guide

This guide explains how to configure the run-tests skill for your environment.

## Table of Contents

- [Tool Configuration](#tool-configuration)
- [Model Configuration](#model-configuration)
- [Consensus Configuration](#consensus-configuration)
- [Default Auto-Trigger Behavior](#default-auto-trigger-behavior)
- [Configuration Best Practices](#configuration-best-practices)

---

## Tool Configuration

### Location

`/Users/tylerburleigh/.claude/skills/run-tests/config.yaml`

### Structure

```yaml
tools:
  gemini:
    description: "Strategic analysis, hypothesis validation, framework explanations"
    command: gemini  # Binary name to check with 'which'
    enabled: true

  codex:
    description: "Code-level review, specific fix suggestions, bug identification"
    command: codex
    enabled: true

  cursor-agent:
    description: "Repository-wide discovery, finding patterns, impact analysis"
    command: cursor-agent
    enabled: true
```

### Configuration Fields

- **name** (key): Tool identifier used in commands and routing
- **description**: Human-readable description shown in tool listings
- **command**: Binary name to search for in PATH (defaults to tool name if omitted)
- **enabled**: Boolean flag to enable/disable tool (defaults to true if omitted)

### Managing Tools

**Add a New Tool:**

```yaml
tools:
  my-custom-tool:
    description: "Custom analysis tool for special cases"
    command: my-tool-binary
    enabled: true
```

**Temporarily Disable a Tool:**

```yaml
tools:
  codex:
    description: "Code-level review, specific fix suggestions, bug identification"
    command: codex
    enabled: false  # Tool will be ignored
```

**Use a Custom Command Name:**

```yaml
tools:
  gemini:
    description: "Strategic analysis tool"
    command: /usr/local/bin/gemini-cli  # Full path or different binary name
    enabled: true
```

---

## Model Configuration

Configure which models to use for each tool and their priority order.

### Structure

```yaml
models:
  # Global model priorities per tool (tried in order)
  gemini:
    priority: [gemini-2.5-pro, gemini-2.0-flash-exp]
    flags: []  # Additional CLI flags

  codex:
    priority: [gpt-5-codex, gpt-5, gpt-5-mini]
    flags: [--skip-git-repo-check]

  cursor-agent:
    priority: [gpt-5-codex, claude-sonnet-4, gpt-5]
    flags: []

  # Per-failure-type overrides (optional)
  overrides:
    fixture:
      gemini: [gemini-2.5-pro]  # Use higher reasoning for fixtures
    flaky:
      codex: [gpt-5, gpt-5-codex]  # Different priority for flaky tests
```

### How Priority Works

1. **Global Priority**: Each tool has a priority list of models
2. **Failure-Type Overrides**: Specific failure types can use different models
3. **Fallback**: If first model unavailable, tries next in priority list
4. **Backward Compatible**: Falls back to hardcoded defaults if config missing

### Benefits

- **Flexibility**: Choose which models to use based on your access
- **Cost Control**: Use faster/cheaper models for simple cases
- **Quality Tuning**: Use better models for complex failure types
- **Experimentation**: Easy to test different model combinations

### Example Scenarios

```yaml
# Scenario 1: Limited model access (only have gemini-2.0-flash-exp)
models:
  gemini:
    priority: [gemini-2.0-flash-exp]

# Scenario 2: Cost optimization (use fast models by default)
models:
  gemini:
    priority: [gemini-2.0-flash-exp, gemini-2.5-pro]
  codex:
    priority: [gpt-5-mini, gpt-5, gpt-5-codex]

# Scenario 3: Quality focus with overrides for complex cases
models:
  gemini:
    priority: [gemini-2.5-pro]
  overrides:
    fixture:
      gemini: [gemini-2.5-pro]  # Complex reasoning needed
    timeout:
      gemini: [gemini-2.0-flash-exp]  # Fast analysis sufficient
```

---

## Consensus Configuration

Configure multi-agent consensus behavior and automatic triggering.

### Structure

```yaml
consensus:
  # Tool pair definitions
  pairs:
    default: [gemini, cursor-agent]
    code-focus: [codex, gemini]
    discovery-focus: [cursor-agent, gemini]

  # Auto-trigger rules per failure type
  auto_trigger:
    fixture: code-focus          # Auto-use code-focus for fixture failures
    flaky: default               # Auto-use default for flaky tests
    multi-file: discovery-focus  # Auto-use discovery for multi-file issues
    timeout: default             # Auto-use default for timeouts
```

### How Auto-Trigger Works

1. **Failure Type Detection**: When a failure type is specified in consultation
2. **Config Lookup**: Checks if that failure type has auto-trigger enabled
3. **Automatic Consensus**: If enabled, uses multi-agent mode automatically
4. **Pair Selection**: Uses the configured pair for that failure type
5. **Info Display**: Shows which pair is being used and why

### Manual Override

You can still use `--multi-agent` flag to manually trigger consensus for any failure type, even if not configured for auto-trigger.

### Example Usage

```bash
# This will auto-trigger consensus if 'fixture' is in auto_trigger
~/.claude/skills/run-tests/scripts/tools_cli.py consult fixture  --error "fixture 'db_session' not found"  --hypothesis "Fixture location issue"

# Output shows:
# Auto-triggering multi-agent consensus for 'fixture' failure
# Using consensus pair: code-focus
```

### Benefits

- **Automatic Quality**: Complex failure types get multi-agent analysis automatically
- **Consistent**: Same failure types always get same treatment
- **Configurable**: Users decide which failure types need consensus
- **Flexible**: Can still manually trigger for any failure type

---

## Default Auto-Trigger Behavior

Configure a `default` behavior that applies to all undefined failure types.

### Structure

```yaml
consensus:
  auto_trigger:
    # Default for undefined types
    default: null  # or pair name like 'default', 'code-focus'

    # Explicit overrides
    fixture: code-focus
    exception: null  # Explicitly single-agent, even if default is set
```

### How Precedence Works

1. **Explicit entry** - If failure type has explicit entry, use it
2. **Default setting** - If not found, use `default` value
3. **Fallback** - If no default, use single-agent

### Example Configurations

```yaml
# Conservative (current behavior) - undefined types use single-agent
auto_trigger:
  default: null
  fixture: code-focus
  flaky: default

# Aggressive - all undefined types auto-trigger with code-focus
auto_trigger:
  default: code-focus
  assertion: null  # Opt-out specific types

# Selective - some auto-trigger, some don't
auto_trigger:
  default: null
  fixture: code-focus
  flaky: default
  exception: default
  multi-file: discovery-focus
```

### Use Cases

| Scenario | Configuration | Behavior |
|----------|---------------|----------|
| Conservative testing | `default: null` + specific entries | Only configured types auto-trigger |
| Comprehensive analysis | `default: code-focus` + opt-outs | Most failures auto-trigger consensus |
| Targeted approach | `default: null` + many explicit entries | Fine-grained control per type |

### Benefits

- **Single configuration point**: Change default to switch modes
- **Clear overrides**: Explicit entries always take precedence
- **Easy experimentation**: Try aggressive mode by changing one line
- **Backward compatible**: No `default` = current behavior

---

## Configuration Best Practices

### Tool Configuration

1. **Keep descriptions concise** - They appear in help text and routing suggestions
2. **Use absolute paths** - For custom tool locations, use full paths in `command`
3. **Disable rather than delete** - Set `enabled: false` to preserve configuration
4. **Document custom tools** - Add comments explaining non-standard tools
5. **Test after changes** - Run `check-tools` to verify configuration is valid

### Model Configuration

1. **Start with defaults** - Current defaults are well-tested
2. **Add overrides carefully** - Only override when you have specific needs
3. **Monitor costs** - Higher-quality models may cost more
4. **Test changes** - Verify model selection with dry-run before production use

### Consensus Configuration

1. **Start conservative**: Only auto-trigger for truly complex failure types
2. **Monitor costs**: Multi-agent consultations use more API calls
3. **Adjust based on results**: Add auto-trigger if you frequently need consensus for a type
4. **Document rationale**: Add comments explaining why certain types are auto-triggered

### Default Configuration

1. **Begin with** `default: null` - Conservative approach
2. **Identify patterns** - Track which failure types you manually use `--multi-agent` for
3. **Add explicitly** - Add those types to auto_trigger
4. **Consider aggressive** - If most types need consensus, use `default: <pair-name>`
5. **Opt-out explicitly** - Set specific types to `null` when needed

---

## Checking Your Configuration

```bash
# View available tools and their status
~/.claude/skills/run-tests/scripts/tools_cli.py check-tools

# Example output:
# Available: gemini, cursor-agent
# Missing:   codex
#
# Available tools and their best uses:
#   • gemini: Strategic analysis, hypothesis validation, framework explanations
#   • cursor-agent: Repository-wide discovery, finding patterns, impact analysis
```

---

## Troubleshooting

### Tool not found

If a tool is not detected:
1. Verify the tool is installed: `which gemini` (or codex, cursor-agent)
2. Check `command` field in config.yaml matches actual binary name
3. Ensure tool is in your PATH
4. Verify `enabled: true` in config

### Model not available

If a configured model isn't working:
1. Check model name spelling in config.yaml
2. Verify you have access to that model
3. The system will try next model in priority list
4. Check tool CLI supports that model (e.g., `gemini --help`)

### Auto-trigger not working

If auto-trigger isn't behaving as expected:
1. Check failure type spelling in auto_trigger section
2. Verify `default` setting if relying on it
3. Remember: `null` means no auto-trigger
4. Check for typos in pair names (default, code-focus, discovery-focus)

---

## Version History

- **v1.1** - Added default auto-trigger behavior
- **v1.0** - Initial model and consensus configuration support
