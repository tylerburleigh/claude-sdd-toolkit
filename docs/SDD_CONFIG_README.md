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

If this fails, you have a JSON syntax error. Common issues:
- Missing comma between fields
- Trailing comma after last field
- Missing quotes around strings
- Unescaped special characters

**Check 3: Check for CLI argument overrides**

Remember that CLI arguments always override config files. If you pass `--no-json`, the config setting will be ignored.

```bash
# Test without CLI flags to see raw config behavior
sdd progress YOUR-SPEC-ID
```

**Check 4: Verify effective configuration**

Test what settings are actually being used:

```bash
# This should respect your config
sdd progress YOUR-SPEC-ID --json

# Compare with explicit overrides
sdd progress YOUR-SPEC-ID --json --compact
sdd progress YOUR-SPEC-ID --json --no-compact
```

If all three produce the same output, config is not being loaded.

### Config file is ignored

**Possible causes:**

1. **JSON syntax error** (run validation above)
2. **File in wrong location** (check paths above)
3. **CLI argument is overriding** (remove CLI flags to test)
4. **Invalid value type** (check logs for warnings)
5. **Wrong working directory** (project config only loaded from project root)
6. **File permissions** (ensure file is readable)

**Diagnostic steps:**

```bash
# 1. Check file exists and is readable
test -r .claude/sdd_config.json && echo "✅ Readable" || echo "❌ Not readable"

# 2. Validate JSON syntax
python3 -m json.tool .claude/sdd_config.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# 3. Check working directory
pwd
# Should be at project root for project config to load

# 4. Test with a simple command
sdd verify-tools
# Check output - should show info about config if loaded
```

### JSON validation errors

**Error:** `Invalid JSON in config file`

**Solution:**
```bash
# Use json.tool to find the error
python3 -m json.tool .claude/sdd_config.json
```

Common JSON errors and fixes:

**Trailing comma:**
```json
// ❌ Wrong
{
  "output": {
    "default_mode": "json",
    "json_compact": true,
  }
}

// ✅ Correct
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Missing quotes:**
```json
// ❌ Wrong
{
  "output": {
    "default_mode": json
  }
}

// ✅ Correct
{
  "output": {
    "default_mode": "json"
  }
}
```

**Unescaped quotes in strings:**
```json
// ❌ Wrong
{
  "output": {
    "default_mode": "json"
  }
}

// ✅ Correct (if you need quotes in values, which you don't here)
{
  "output": {
    "default_mode": "json"
  }
}
```

### Precedence not working as expected

**Symptom:** Config values seem to be ignored even though file is valid

**Check precedence order:**

1. CLI flags (highest priority)
2. Project config (`.claude/sdd_config.json`)
3. Global config (`~/.claude/sdd_config.json`)
4. Built-in defaults (lowest priority)

**Test precedence:**

```bash
# Set global config to json_compact: true
# Set project config to json_compact: false
# Run from project directory

sdd progress YOUR-SPEC-ID --json
# Should output pretty-print (project config wins)

sdd progress YOUR-SPEC-ID --json --compact
# Should output compact (CLI flag wins)
```

**Common mistake:** Having both global and project configs with same values, thinking project should "add to" global. Remember: project completely overrides global for any settings it defines.

### Permission issues

**Error:** `Permission denied` when reading config

**Solution:**
```bash
# Fix file permissions
chmod 644 .claude/sdd_config.json
chmod 644 ~/.claude/sdd_config.json

# Ensure directory is accessible
chmod 755 .claude
chmod 755 ~/.claude
```

### Config file in wrong format

**Symptom:** Config seems ignored, no errors shown

**Check:** You might be using an old format or wrong structure

**Correct structure:**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Wrong structures:**
```json
// ❌ Missing "output" wrapper
{
  "default_mode": "json",
  "json_compact": true
}

// ❌ Wrong nesting
{
  "config": {
    "output": {
      "default_mode": "json"
    }
  }
}
```

### Still not working?

If you've tried all the above and configuration still isn't working:

1. **Start fresh:**
   ```bash
   # Remove config files
   rm .claude/sdd_config.json
   rm ~/.claude/sdd_config.json

   # Create new one using template
   cat > .claude/sdd_config.json <<'EOF'
   {
     "output": {
       "default_mode": "json",
       "json_compact": true
     }
   }
   EOF

   # Validate
   python3 -m json.tool .claude/sdd_config.json
   ```

2. **Test defaults:**
   ```bash
   # Without any config, this should work
   sdd progress YOUR-SPEC-ID --json --compact
   ```

3. **Check SDD CLI version:**
   ```bash
   sdd --version
   # Ensure you have latest version with config support
   ```

4. **Report issue:**
   If nothing works, report at [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues) with:
   - Your config file contents
   - Command you're running
   - Expected vs actual output
   - SDD CLI version

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

## Complete Configuration Walkthrough

This section provides step-by-step instructions for setting up and verifying your SDD configuration.

### Step 1: Choose Configuration Scope

Decide whether you want global or project-specific configuration:

- **Global** (`~/.claude/sdd_config.json`): Applies to all projects
- **Project** (`./.claude/sdd_config.json`): Applies only to current project

**Recommendation:** Start with global config for personal preferences, then add project overrides as needed.

### Step 2: Create the Configuration File

**For global configuration:**
```bash
# Create .claude directory if it doesn't exist
mkdir -p ~/.claude

# Create config file
cat > ~/.claude/sdd_config.json <<'EOF'
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
EOF
```

**For project configuration:**
```bash
# Create .claude directory if it doesn't exist
mkdir -p .claude

# Create config file
cat > .claude/sdd_config.json <<'EOF'
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
EOF
```

### Step 3: Verify Configuration

**Check file exists and is valid JSON:**
```bash
# For project config
cat .claude/sdd_config.json | python3 -m json.tool

# For global config
cat ~/.claude/sdd_config.json | python3 -m json.tool
```

**Test effective configuration:**
```bash
# Run a command and observe output format
sdd progress json-output-standardization-2025-11-08-001 --json

# This should respect your json_compact setting
```

### Step 4: Test Precedence

**Test CLI flag override:**
```bash
# If your config has json_compact: true, this should output pretty-print
sdd progress YOUR-SPEC-ID --json --no-compact

# If your config has json_compact: false, this should output compact
sdd progress YOUR-SPEC-ID --json --compact
```

**Test project overrides global:**
```bash
# Set different values in global and project configs
# Project config should win

# Run from project directory
sdd progress YOUR-SPEC-ID --json
# Should use project config setting
```

### Step 5: Common Configuration Patterns

**Pattern 1: Agent-Friendly (Recommended for automation)**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```
All commands return compact JSON by default. Override with `--no-compact` when debugging.

**Pattern 2: Human-Friendly (Recommended for interactive use)**
```json
{
  "output": {
    "default_mode": "text"
  }
}
```
Commands return human-readable text by default. Use `--json` when you need structured output.

**Pattern 3: Debug-Friendly (Recommended for development)**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": false
  }
}
```
All commands return pretty-print JSON by default. Easy to read and inspect.

**Pattern 4: Mixed Team (Recommended for teams)**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```
Global: Compact JSON (efficient).
Project: Override per-project needs.
Individual developers can use CLI flags for their preferences.

## Migrating from Legacy Format

If you have an existing configuration using the legacy format, here's how to migrate to the new format.

### Legacy vs Current Format

**Legacy format** (deprecated but still supported):
```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

**Current format** (recommended):
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

### Field Mapping

| Legacy Field | Current Field | Values |
|--------------|---------------|--------|
| `output.json` | `output.default_mode` | `true` → `"json"`, `false` → `"text"` |
| `output.compact` | `output.json_compact` | `true` → `true`, `false` → `false` |

### Migration Steps

**Option 1: Manual Update**

Edit your config file and rename the fields:
```bash
# Edit global config
nano ~/.claude/sdd_config.json

# Edit project config
nano .claude/sdd_config.json
```

Change:
- `"json": true` → `"default_mode": "json"`
- `"json": false` → `"default_mode": "text"`
- `"compact": X` → `"json_compact": X`

**Option 2: Script Migration**

```bash
# Backup your config first
cp ~/.claude/sdd_config.json ~/.claude/sdd_config.json.backup

# Use Python to migrate
python3 <<'EOF'
import json
import os

config_path = os.path.expanduser("~/.claude/sdd_config.json")
with open(config_path, 'r') as f:
    config = json.load(f)

# Migrate if legacy format detected
if 'json' in config.get('output', {}):
    output = config['output']
    new_output = {}

    # Migrate json → default_mode
    if 'json' in output:
        new_output['default_mode'] = "json" if output['json'] else "text"

    # Migrate compact → json_compact
    if 'compact' in output:
        new_output['json_compact'] = output['compact']

    config['output'] = new_output

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print("✅ Migration complete!")
else:
    print("ℹ️  Config already using current format")
EOF
```

**Option 3: Both Formats (Transition Period)**

The SDD CLI supports both formats simultaneously. You can keep legacy fields for backward compatibility:

```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true,
    "json": true,
    "compact": true
  }
}
```

The current format takes precedence if both are present.

### Validation After Migration

```bash
# Verify JSON is valid
python3 -c "import json; print(json.load(open(os.path.expanduser('~/.claude/sdd_config.json'))))"

# Test that configuration works
sdd progress YOUR-SPEC-ID --json
```

## Best Practices

### When to Use Compact Mode

✅ **Use compact (`json_compact: true`) for:**

1. **Agent Workflows**
   - Claude Code skills calling SDD commands
   - Automated scripts and pipelines
   - High-frequency command execution
   - Token optimization is critical

2. **Production Pipelines**
   - CI/CD automation
   - Build scripts
   - Deployment automation
   - Monitoring and metrics collection

3. **Cost Optimization**
   - API calls with token-based pricing
   - Large-scale automation (100+ commands/day)
   - Context window conservation

**Example scenario:**
```bash
# Agent workflow in autonomous mode - wants to conserve context
sdd prepare-task spec-id --json --compact
sdd task-info spec-id task-id --json --compact
# Each command saves ~30% tokens
```

### When to Use Pretty-Print Mode

✅ **Use pretty-print (`json_compact: false`) for:**

1. **Development and Debugging**
   - Manual testing of commands
   - Inspecting output structure
   - Troubleshooting issues
   - Understanding data relationships

2. **Documentation and Examples**
   - README examples
   - Tutorial content
   - Training materials
   - API documentation

3. **Code Review and Verification**
   - Reviewing command outputs
   - Validating results manually
   - Sharing output with team members
   - Creating bug reports

**Example scenario:**
```bash
# Developer debugging why a task is blocked
sdd check-deps spec-id task-id --json --no-compact
# Pretty-print makes it easy to see the dependency tree
```

### Team Configuration Strategy

**Scenario: Mixed team (developers + automation)**

**Global config for all developers:**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Individual developer overrides:**
```bash
# Developer who prefers text output
alias sdd='sdd --no-json'

# Developer who prefers pretty-print JSON
alias sdd='sdd --no-compact'
```

**Project config for CI/CD:**
```json
{
  "output": {
    "default_mode": "json",
    "json_compact": true
  }
}
```

**Benefits:**
- ✅ Default efficiency (compact JSON)
- ✅ Individual flexibility (aliases/CLI flags)
- ✅ Consistent automation behavior
- ✅ No conflicts between preferences

### Configuration Maintenance

**Do:**
- ✅ Version control project configs (`.claude/sdd_config.json`)
- ✅ Document project-specific choices in README
- ✅ Use CLI flags for temporary changes
- ✅ Keep global config minimal (personal preferences only)
- ✅ Test configuration after changes

**Don't:**
- ❌ Commit global configs to version control
- ❌ Hard-code output preferences in scripts (use CLI flags)
- ❌ Override project configs in global config
- ❌ Use legacy format for new configurations
- ❌ Assume config will be present (scripts should handle defaults)

### Token Optimization Tips

**High-impact commands** (use compact for these):
- `sdd prepare-task` (saves ~120 tokens/call)
- `sdd task-info` (saves ~50 tokens/call)
- `sdd check-deps` (saves ~40 tokens/call)

**Low-impact commands** (compact less critical):
- `sdd verify-tools` (saves ~5 tokens/call)
- `sdd next-task` (saves ~15 tokens/call)

**Token savings accumulate:**
- 10 commands × 30% savings = ~500 tokens saved
- 100 commands × 30% savings = ~5,000 tokens saved
- Autonomous mode completing 20 tasks = ~10,000 tokens saved

**Recommendation:** Use compact mode by default in agent workflows, override with `--no-compact` only when debugging specific issues.

## See Also

- `docs/sdd_config.json.template` - Template configuration file
- `docs/GIT_CONFIG_README.md` - Git integration configuration (similar pattern)
- Main SDD documentation for CLI command reference
