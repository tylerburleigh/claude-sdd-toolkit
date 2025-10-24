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
- `skills-dev setup-permissions --` - Checks/manages SDD permissions
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
- `skills-dev setup-permissions --` - Manages permission configuration
- Python 3 - For JSON processing

**Tracked State**:
- Declined projects stored in `~/.claude/.sdd-permissions-declined`

## Configuration

Hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "session-start": ".claude/hooks/session-start",
    "pre-tool-use": ".claude/hooks/pre-tool-use"
  }
}
```

## Permissions

The following permissions are required for hooks to function:

```json
{
  "permissions": {
    "allow": [
      "Bash(skills-dev:*)",
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

### skills-dev setup-permissions
**Accessed via**: `skills-dev setup-permissions -- <command>`
**Commands**:
- `check <project_root>` - Check if permissions are configured
- `update <project_root>` - Add SDD permissions to project settings

**Output**: JSON with configuration status

### skills-dev start-helper
**Accessed via**: `skills-dev start-helper -- <command>`
**Commands**:
- `check-permissions` - Verify SDD permissions
- `find-active-work` - Locate active specifications
- `format-output` - Format SDD status for display

**Note**: All helper commands now use the unified CLI: `skills-dev <tool> -- <command>`

## Troubleshooting

### Hooks not running
1. Check hooks are registered in `.claude/settings.json`
2. Verify hook scripts are executable: `chmod +x .claude/hooks/*`
3. Check hook scripts have proper shebang: `#!/bin/bash`

### Permission prompts not appearing
1. Verify `auto_offer_permissions` is `true` in settings
2. Check if project was declined (remove from `~/.claude/.sdd-permissions-declined`)
3. Run manually: `skills-dev setup-permissions -- check /path/to/project`

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

## Integration with CLAUDE.md

These hooks integrate with the instructions in `~/.claude/CLAUDE.md`:

1. **Session Start**: Claude checks for marker files and proactively greets users with SDD context
2. **Permission Setup**: Hooks ensure required permissions are configured before skill usage
3. **State Tracking**: Declined projects are tracked to avoid repeated prompts

See `~/.claude/CLAUDE.md` for Claude's session start behavior and workflow guidance.
