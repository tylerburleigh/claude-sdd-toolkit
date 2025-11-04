# Git Integration Configuration

This directory contains configuration files for the SDD Toolkit's git integration feature.

## Quick Start

1. **Copy the template:**
   ```bash
   cp git_config.json.template git_config.json
   ```

2. **Edit your settings:**
   Open `git_config.json` and set `enabled: true` plus any other preferences.

3. **Configuration locations:**
   - **Project-local**: `{project_root}/.claude/git_config.json` (highest precedence)
   - **Global**: `~/.claude/git_config.json` (fallback)

## Available Settings

### `enabled` (boolean, default: `false`)
Master switch for git integration. Must be set to `true` to enable automatic git operations.

**Why disabled by default:** Safety - prevents unexpected git operations in your repositories.

### `auto_branch` (boolean, default: `true`)
Automatically create feature branches when starting work on a spec.

- **Branch naming:** `feat/{spec-id}` (e.g., `feat/user-auth-2025-10-24-001`)
- **Base branch:** Detected from current branch or defaults to `main`

### `auto_commit` (boolean, default: `true`)
Automatically commit changes when completing tasks.

- **Commit message format:** Includes task ID, title, and spec reference
- **When commits happen:** Controlled by `commit_cadence` setting

### `auto_push` (boolean, default: `false`)
Automatically push commits to remote repository.

**Why disabled by default:** Safety - allows you to review commits locally before pushing.

### `auto_pr` (boolean, default: `false`)
Automatically create pull requests when specs are completed.

**Requirements:**
- `gh` CLI must be installed and configured
- Remote repository must exist

**Why disabled by default:** PR creation is a significant action that should be explicit.

### `commit_cadence` (string, default: `"task"`)
Controls when commits are created automatically.

**Options:**
- `"task"`: Commit after completing each task (recommended for granular history)
- `"phase"`: Commit after completing each phase (fewer, larger commits)
- `"manual"`: No automatic commits (user controls when to commit)

## Example Configurations

### Conservative (Recommended for First-Time Users)
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "auto_pr": false,
  "commit_cadence": "task"
}
```

This enables basic git integration but requires manual confirmation for push/PR operations.

### Fully Automated (For Experienced Users)
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": true,
  "auto_pr": true,
  "commit_cadence": "phase"
}
```

⚠️ **Warning:** This configuration automatically pushes and creates PRs. Only use if you're comfortable with fully automated workflows.

### Manual Control
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": false,
  "auto_push": false,
  "auto_pr": false,
  "commit_cadence": "manual"
}
```

Creates branches automatically but leaves all commit/push/PR operations under manual control.

## Configuration Precedence

When loading settings, the toolkit checks locations in this order:

1. **Project-local** (`{project_root}/.claude/git_config.json`)
2. **Global** (`~/.claude/git_config.json`)
3. **Built-in defaults** (if no config file found)

Project-local settings override global settings. This allows you to have different configurations for different projects.

## Validation

The configuration loader validates all settings:

- **Boolean fields** must be `true` or `false` (not strings like `"yes"` or numbers like `1`)
- **commit_cadence** must be one of: `"task"`, `"phase"`, or `"manual"`
- Invalid values are replaced with defaults and warnings are logged

## Disabling Git Integration

To disable git integration entirely, set `enabled: false` in your config file.

Alternatively, delete or rename your `git_config.json` file - the defaults disable git integration by default.

## Troubleshooting

### Git integration not working
- Check that `enabled: true` in your config
- Verify config file is valid JSON (no syntax errors)
- Check logs for validation warnings

### Wrong config file being used
- Check precedence order above
- Use absolute paths to verify which file is being loaded
- Project-local config takes precedence over global

### Invalid configuration values
- Check that boolean fields use `true`/`false` (not strings)
- Verify `commit_cadence` is one of the three allowed values
- Review logs for validation warnings

## Related Documentation

- **git_config.py**: Core configuration loading module
- **git_metadata.py**: Git operations and metadata management (Phase 1, Task 1-3)
- **Spec schema**: Git metadata structure in JSON specs
