# SDD Configuration File

The `sdd_config.json` file controls the default behavior of SDD toolkit commands.

## Configuration Locations

The SDD toolkit looks for configuration in the following order (first found wins):

1. **Project-local**: `{project_root}/.claude/sdd_config.json`
2. **Global**: `~/.claude/sdd_config.json`
3. **Built-in defaults** (if no config file found)

## Configuration Options

### `output.json`
**Type**: `boolean`
**Default**: `true`
**Description**: Controls whether sdd-update commands output JSON by default for automation-friendly behavior.

### `output.compact`
**Type**: `boolean`
**Default**: `true`
**Description**: Controls whether JSON output uses compact formatting (single-line) by default.

### `output.default_format`
**Type**: `string`
**Default**: `"text"`
**Allowed values**: `"text"`, `"json"`, `"markdown"`
**Description**: Sets the default output format for commands that support `--format` flag. Commands with `--format` will use this value when no explicit format is specified.

- `"text"`: Rich TUI output with colors, panels, and formatted tables (default)
- `"json"`: Machine-readable JSON output for automation and pipel ines
- `"markdown"`: Human-readable markdown format (where supported)

## Example Configuration

```json
{
  "output": {
    "json": true,
    "compact": true,
    "default_format": "text"
  }
}
```

## Command-Line Overrides

Individual commands can override these defaults:

- `sdd fidelity-review SPEC --format json` - Override default format
- `sdd --no-json list-review-tools` - Disable JSON output
- `sdd --no-compact query-tasks` - Disable compact formatting

## Environment Variables

You can also override configuration using environment variables:

- `SDD_CACHE_ENABLED`: Set cache behavior (`true` or `false`)
- `SDD_CACHE_DIR`: Custom cache directory path
- `SDD_CACHE_TTL_HOURS`: Cache expiration time in hours
- `SDD_CACHE_MAX_SIZE_MB`: Maximum cache size in megabytes

## Commands That Support `default_format`

- `sdd fidelity-review` - Supports: text, json, markdown
- `sdd list-review-tools` - Supports: text, json
- `sdd report` (validate) - Supports: markdown, json
- `sdd doc call-graph` - Supports: text, json, dot
- `sdd doc trace-entry` - Supports: text, json
- `sdd doc trace-data` - Supports: text, json
- `sdd doc impact` - Supports: text, json
- `sdd doc refactor-candidates` - Supports: text, json

## Setup

To create a configuration file:

```bash
# Global config (applies to all projects)
mkdir -p ~/.claude
cat > ~/.claude/sdd_config.json << 'EOF'
{
  "output": {
    "json": true,
    "compact": true,
    "default_format": "text"
  }
}
EOF

# Project-local config (applies to current project only)
mkdir -p ./.claude
cp ~/.claude/sdd_config.json ./.claude/
```

## Troubleshooting

### Check which config is being used

```bash
# The config loader logs which file it loads (if any)
sdd --debug --verbose <command>
```

### Validate configuration

```python
from claude_skills.common.sdd_config import load_sdd_config
config = load_sdd_config()
print(config)
```

### Reset to defaults

Simply delete the config files:

```bash
rm ~/.claude/sdd_config.json
rm .claude/sdd_config.json
```

The toolkit will use built-in defaults automatically.
