# SDD CLI Configuration

This document explains how to configure the SDD CLI tool's output behavior using configuration files.

## Overview

The SDD CLI supports configuration files that control output formatting defaults. This allows you to set preferences once rather than passing flags on every command.

## Configuration File Locations

Configuration files are loaded in order of precedence:

1. **Project-local**: `{project_root}/.claude/sdd_config.json` (highest priority)
2. **Global**: `~/.claude/sdd_config.json`
3. **Built-in defaults**: Used if no config file exists

Project-local settings override global settings, and command-line arguments override both.

## Configuration Structure

**Current format** (recommended):
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Legacy format** (still supported):
```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

### Configuration Options

#### `output.default_mode` (string, default: `"text"`)

Controls the default output format for commands.

- `"json"`: Commands output JSON format by default (automation-friendly)
- `"text"`: Commands output human-readable text format by default

**Example:**
```json
{
  "output": {
    "default_mode": "json"
  }
}
```

**Legacy equivalent:** `output.json` (boolean) - still supported for backward compatibility

#### `output.json_compact` (boolean, default: `true`)

Controls whether JSON output uses compact formatting (single line) or pretty-printed formatting (multi-line with indentation).

- `true`: Compact JSON - single line, no whitespace (optimized for tokens)
- `false`: Pretty-print JSON - multi-line with 2-space indentation (optimized for readability)

**Example:**
```json
{
  "output": {
    "json_compact": false
  }
}
```

**Legacy equivalent:** `output.compact` (boolean) - still supported for backward compatibility

## Precedence Rules

Settings are applied in this order (later sources override earlier):

1. **Built-in defaults** (`default_mode: "text"`, `json_compact: true`)
2. **Global config** (`~/.claude/sdd_config.json`)
3. **Project config** (`./.claude/sdd_config.json`)
4. **CLI arguments** (`--json`, `--no-json`, `--compact`, `--no-compact`)

**CLI flags always have highest priority** and override all configuration file settings.

### CLI Flags

**Output format flags:**
- `--json` - Force JSON output (overrides config)
- `--no-json` - Force text output (overrides config)

**JSON formatting flags:**
- `--compact` - Force compact JSON output (overrides config)
- `--no-compact` - Force pretty-print JSON output (overrides config)

**Example usage:**
```bash
# Override config to use pretty-print
sdd progress spec-id --json --no-compact

# Override config to use compact
sdd progress spec-id --json --compact
```

### Example Precedence Scenarios

**Scenario 1: Project config overrides global**
- Global config: `{"output": {"default_mode": "text"}}`
- Project config: `{"output": {"default_mode": "json"}}`
- Result: JSON output (project config wins)

**Scenario 2: CLI flag overrides all configs**
- Config: `{"output": {"json_compact": true}}`
- Command: `sdd progress spec-id --json --no-compact`
- Result: Pretty-print JSON (CLI flag wins)

**Scenario 3: Partial configuration uses defaults**
- Config: `{"output": {"json_compact": false}}`
- Missing setting: `default_mode` not specified
- Result: `default_mode: "text"` (from defaults), `json_compact: false` (from config)

**Scenario 4: Config sets pretty-print, flag overrides to compact**
- Config: `{"output": {"json_compact": false}}`
- Command: `sdd progress spec-id --json --compact`
- Result: Compact JSON (CLI flag overrides config)

## Creating a Configuration File

### Project-Local Configuration

Create a file at `.claude/sdd_config.json` in your project root:

```bash
# Create .claude directory if it doesn't exist
mkdir -p .claude

# Copy the template from toolkit
cp docs/sdd_config.json.template .claude/sdd_config.json

# Edit with your preferred settings
nano .claude/sdd_config.json
```

### Global Configuration

Create a file at `~/.claude/sdd_config.json`:

```bash
# Create .claude directory in home if it doesn't exist
mkdir -p ~/.claude

# Create config file
cat > ~/.claude/sdd_config.json << 'EOF'
{
  "output": {
    "json": true,
    "compact": true
  }
}
EOF
```

## Common Use Cases

### Use Case 1: Automation Scripts

For scripts that parse JSON output, ensure JSON is always enabled with compact formatting:

```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

This configuration ensures all commands return compact, single-line JSON by default - perfect for automated parsing and token efficiency.

### Use Case 2: Human-Readable Defaults

For interactive terminal use with readable text output:

```json
{
  "output": {
    "default_mode": "text"
  }
}
```

With this config, commands return human-readable text by default. You can still get JSON when needed with `--json` flag.

### Use Case 3: Debugging with Pretty-Print JSON

For development/debugging with readable, well-formatted JSON:

```json
{
  "output": {
    "default_mode": "json",
    "json_compact": false
  }
}
```

This outputs multi-line, indented JSON that's easy to read and inspect during debugging sessions.

### Use Case 4: Mixed Workflow (Recommended)

For developers who want JSON by default but with flexibility:

```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

Then use CLI flags when you need different formatting:
```bash
# Get pretty-print when debugging
sdd progress spec-id --no-compact

# Get text output when you need it
sdd progress spec-id --no-json
```

## Validation and Error Handling

The configuration loader includes validation:

- **Invalid JSON**: Falls back to defaults, logs warning
- **Invalid types**: Falls back to defaults for that setting, logs warning
- **Unknown keys**: Ignored with warning
- **Missing file**: Uses defaults (no error)

**Example warning for invalid type:**
```
WARNING: Invalid type for sdd config 'output.json': expected bool, got string. Using default: True
```

The SDD CLI will always work even with invalid configuration - it simply falls back to safe defaults.

## Troubleshooting

### Config not being applied

**Check 1: Verify file location**
```bash
# For project config
ls -la .claude/sdd_config.json

# For global config
ls -la ~/.claude/sdd_config.json
```

**Check 2: Verify JSON is valid**
```bash
python3 -c "import json; print(json.load(open('.claude/sdd_config.json')))"
```

**Check 3: Check for CLI argument overrides**

Remember that CLI arguments always override config files. If you pass `--no-json`, the config setting will be ignored.

### Config file is ignored

Possible causes:
1. JSON syntax error (run validation above)
2. File in wrong location (check paths above)
3. CLI argument is overriding (remove CLI flags to test)
4. Invalid value type (check logs for warnings)

## FAQ

**Q: Can I have both global and project configs?**

A: Yes! Project config overrides global config. This is useful for setting personal defaults globally while having project-specific overrides.

**Q: What happens if I delete the config file?**

A: The CLI falls back to built-in defaults (`json: true`, `compact: true`). No errors occur.

**Q: Can I disable JSON output entirely?**

A: Yes, set `"json": false` in your config. You can still force JSON with `--json` on specific commands.

**Q: Do I need to restart anything after changing config?**

A: No, configuration is loaded fresh on every command invocation.

**Q: Can I have comments in the JSON file?**

A: JSON doesn't support comments. However, the config structure is simple enough that the template and this README should provide sufficient documentation.

## See Also

- `docs/sdd_config.json.template` - Template configuration file
- `docs/GIT_CONFIG_README.md` - Git integration configuration (similar pattern)
- Main SDD documentation for CLI command reference
