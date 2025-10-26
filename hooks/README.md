# SDD Hooks Configuration

This directory contains Claude Code hooks that automate SDD (Spec-Driven Development) workflows.

## Active Hooks

### 1. session-start
**Event**: `session-start`
**Purpose**: Detects SDD projects at session initialization and creates proactive prompts

**Behavior**:
- Runs when a new Claude Code session starts
- Checks for `specs/active/` directory (SDD project marker)
- Detects if permission setup is needed
- Finds active specification files
- Creates marker files in `/tmp/.claude-sdd-start-*.json` for Claude to read
- Outputs JSON with project context

**Dependencies**:
- `sdd skills-dev setup-permissions --` - Checks/manages SDD permissions
- Python 3 - For JSON processing

### 2. pre-tool-use
**Event**: `pre-tool-use`
**Purpose**: Offers to set up SDD permissions when SDD skills are first used

**Behavior**:
- Triggers when SDD-related skills/commands are invoked (sdd-plan, sdd-next, code-doc, etc.)
- Checks if project needs permission setup
- Prompts user once per project (tracks declined state)
- Non-blocking (always exits 0)

**Dependencies**:
- `sdd skills-dev setup-permissions --` - Manages permission configuration
- Python 3 - For JSON processing

**Tracked State**:
- Declined projects stored in `~/.claude/.sdd-permissions-declined`

## Configuration

Hooks are configured in this plugin via `hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Skill|SlashCommand",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use"
          }
        ]
      }
    ]
  }
}
```

**How it works**:
- Hooks are **plugin-level** configuration (not project-level)
- Claude Code automatically loads hooks from installed plugins
- `${CLAUDE_PLUGIN_ROOT}` ensures portable paths across installations
- The `matcher` field matches tool names (e.g., "Skill", "SlashCommand", "Write", "Edit")
- The pre-tool-use script filters for SDD-specific tools internally

## Permissions

The following permissions are required for hooks to function:

```json
{
  "permissions": {
    "allow": [
      "Bash(sdd:*)",
      "Write(//**/specs/active/**)",
      "Write(//**/specs/completed/**)",
      "Write(//**/specs/archived/**)",
      "Edit(//**/specs/active/**)",
      "Edit(//**/specs/completed/**)",
      "Edit(//**/specs/archived/**)"
    ]
  }
}
```

## SDD Configuration

Hook behavior is controlled via settings:

```json
{
  "sdd": {
    "auto_suggest_resume": true,
    "auto_offer_permissions": true,
    "session_timeout_hours": 1,
    "recent_activity_days": 7
  }
}
```

**Options**:
- `auto_suggest_resume`: Enable proactive SDD work suggestions
- `auto_offer_permissions`: Enable permission setup prompts
- `session_timeout_hours`: Time gap to consider new session
- `recent_activity_days`: Days to consider specs "active"

## Helper Scripts

### sdd skills-dev setup-permissions
**Accessed via**: `sdd skills-dev setup-permissions -- <command>`
**Commands**:
- `check <project_root>` - Check if permissions are configured
- `update <project_root>` - Add SDD permissions to project settings

**Output**: JSON with configuration status

### sdd skills-dev start-helper
**Accessed via**: `sdd skills-dev start-helper -- <command>`
**Commands**:
- `check-permissions` - Verify SDD permissions
- `find-active-work` - Locate active specifications
- `format-output` - Format SDD status for display

**Note**: All helper commands now use the unified CLI: `sdd skills-dev <tool> -- <command>`

## Troubleshooting

### Hooks not running
1. Verify `hooks/hooks.json` exists in the plugin root
2. Check hook scripts are executable: `chmod +x hooks/*`
3. Check hook scripts have proper shebang: `#!/bin/bash`
4. Restart Claude Code to reload plugin configuration

### Permission prompts not appearing
1. Verify `auto_offer_permissions` is `true` in settings
2. Check if project was declined (remove from `~/.claude/.sdd-permissions-declined`)
3. Run manually: `sdd skills-dev setup-permissions -- check /path/to/project`

### Session detection not working
1. Ensure `specs/active/` directory exists
2. Check marker files: `ls /tmp/.claude-sdd-start-*.json`
3. Review hook logs: `/tmp/session-start.log`

## Maintenance

### Clearing declined state
To reset permission prompts:
```bash
rm ~/.claude/.sdd-permissions-declined
```

### Clearing marker files
Old marker files are auto-cleaned (>1 hour), but can be manually removed:
```bash
rm /tmp/.claude-sdd-start-*.json
```

### Viewing hook logs
```bash
tail -f /tmp/session-start.log
```

## Plugin Integration

These hooks are automatically loaded by Claude Code when the plugin is installed:

1. **Session Start**: Hook runs when a session starts, checks for active specs, and creates marker files for Claude to read
2. **Permission Setup**: PreToolUse hook ensures required permissions are configured before SDD skills run
3. **State Tracking**: Declined projects are tracked to avoid repeated prompts
4. **Non-intrusive**: Hooks only activate in projects with `specs/active/` directories

**No manual registration needed** - Claude Code automatically discovers and loads plugin hooks from `hooks/hooks.json`.
