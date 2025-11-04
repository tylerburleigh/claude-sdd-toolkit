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

```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

### Configuration Options

#### `output.json` (boolean, default: `true`)

Controls whether commands output JSON format by default.

- `true`: Commands output JSON format (automation-friendly)
- `false`: Commands output human-readable format

**Example:**
```json
{
  "output": {
    "json": true
  }
}
```

#### `output.compact` (boolean, default: `true`)

Controls whether JSON output uses compact formatting (single line) or pretty-printed formatting.

- `true`: Compact JSON (single line, smaller output)
- `false`: Pretty-printed JSON (multi-line, more readable)

**Example:**
```json
{
  "output": {
    "compact": false
  }
}
```

## Precedence Rules

Settings are applied in this order (later sources override earlier):

1. **Built-in defaults** (`json: true`, `compact: true`)
2. **Global config** (`~/.claude/sdd_config.json`)
3. **Project config** (`./.claude/sdd_config.json`)
4. **CLI arguments** (`--json`, `--compact`, `--no-json`, etc.)

### Example Precedence Scenarios

**Scenario 1: Project overrides global**
- Global config: `{"output": {"json": false}}`
- Project config: `{"output": {"json": true}}`
- Result: `json: true` (project wins)

**Scenario 2: CLI argument overrides all**
- Config: `{"output": {"json": true}}`
- Command: `sdd prepare-task spec-id --no-json`
- Result: Human-readable output (CLI flag wins)

**Scenario 3: Partial configuration**
- Config: `{"output": {"compact": false}}`
- Missing setting: `json` not specified
- Result: `json: true` (from defaults), `compact: false` (from config)

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

For scripts that parse JSON output, ensure JSON is always enabled:

```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

### Use Case 2: Human-Readable Defaults

For interactive terminal use with readable output:

```json
{
  "output": {
    "json": false
  }
}
```

### Use Case 3: Debugging with Pretty JSON

For development/debugging with readable JSON:

```json
{
  "output": {
    "json": true,
    "compact": false
  }
}
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
