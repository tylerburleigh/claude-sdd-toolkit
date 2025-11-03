---
name: sdd-setup
description: First-time setup for SDD toolkit - configures project permissions and git integration
---

# SDD First-Time Setup

This command performs first-time setup for the SDD (Spec-Driven Development) toolkit in your project.

## What This Does

1. Configures `.claude/settings.json` with the necessary permissions for SDD skills and tools
2. Optionally configures `.claude/git_config.json` for git integration features (branches, commits, AI-powered PRs)

## Workflow

### Step 1: Check Permissions Configuration

First, check if SDD permissions are already configured:

```bash
sdd skills-dev setup-permissions check .
```

The script will return JSON with a `configured` field indicating whether permissions are set up.

### Step 2: Configure Permissions if Needed

**If `configured: true` AND `status: "fully_configured"`:**

Display message and proceed to Step 3:
```
✅ SDD permissions are fully configured! (41/41)
```

**If `configured: false` AND `status: "partially_configured"`:**

Display warning with details:
```
⚠️  SDD permissions are partially configured (35/41 present)

Missing 6 permissions:
  • 2 skill permissions
  • 4 bash/git permissions
```

Use AskUserQuestion tool:
- **Header**: "Permissions"
- **Question**: "Some permissions are missing. Would you like to add them?"
- **Options**:
  1. Yes, add missing permissions
  2. No, continue with current permissions

**If user chooses "Yes, add missing permissions":**
```bash
sdd skills-dev setup-permissions update .
```

This will:
- Add only the missing permissions
- Preserve all existing permissions
- Show what's being added

**If user chooses "No, continue with current permissions":**
```
⚠️  Proceeding with partial permissions. Some features may not work.
```
Then proceed to Step 3.

**If `configured: false` AND `status: "not_configured"`:**

Inform the user and run the setup:
```
Setting up SDD permissions for this project...
```

Then run:
```bash
sdd skills-dev setup-permissions update .
```

This will:
- Create `.claude/settings.json` if it doesn't exist
- Add all 41 required SDD permissions to the `allow` list
- Preserve any existing permissions

### Step 3: Check Git Configuration

Check if git integration is configured:

```bash
sdd skills-dev start-helper check-git-config .
```

The script will return JSON with a `needs_setup` field.

### Step 4: Configure Git if Needed

**If `needs_setup: false`:**

Display message with current settings:
```
✅ Git integration is already configured!

═══════════════════════════════════════════════════════════
Current Git Configuration:

  • Auto-branch: Yes
  • Auto-commit: Yes (per task)
  • Show files before commit: Yes
  • Auto-push: No
  • AI-powered PRs: Yes (model: sonnet)
═══════════════════════════════════════════════════════════
```

To generate this display:
1. Parse the `settings` object from check-git-config JSON output
2. Use the formatting pattern shown above
3. Show actual values from the user's configuration

Then proceed to Step 5.

**If `needs_setup: true`:**

Ask the user if they want to configure git integration:
```
Git integration enables automatic branch creation, commits, and AI-powered PR generation.
Would you like to configure it now?
```

Use AskUserQuestion tool:
- **Header**: "Git Setup"
- **Question**: "Configure git integration?"
- **Options**:
  1. Yes, configure now
  2. No, skip for now

**If user chooses "Yes, configure now":**

Gather all git configuration preferences using AskUserQuestion (you can ask up to 4 questions at once):

**Question Set 1 (Required):**
- **Header**: "Git Features"
- **Question**: "Enable git integration?"
- **Options**:
  1. Yes, enable (recommended)
  2. No, disable

**If user chooses "No, disable":**

Write minimal config and skip to Step 5:
```bash
sdd skills-dev start-helper setup-git-config . --non-interactive --no-enabled
```

Display:
```
✅ Git integration disabled. Config saved to .claude/git_config.json
```

Then proceed to Step 5.

**If user chooses "Yes, enable":**

Ask the remaining configuration questions (you can ask all 4 in one AskUserQuestion call):

**Question 2:**
- **Header**: "Auto Branch"
- **Question**: "Auto-create feature branches when starting specs?"
- **Options**:
  1. Yes (recommended)
  2. No

**Question 3:**
- **Header**: "Auto Commit"
- **Question**: "Auto-commit changes when completing tasks?"
- **Options**:
  1. Yes (recommended)
  2. No

**Question 4 (only if auto-commit is Yes):**
- **Header**: "Commit When"
- **Question**: "When should commits be created?"
- **Options**:
  1. Per task (recommended)
  2. Per phase
  3. Manually

**Additional Questions (if needed, ask in next batch):**

**Question 5:**
- **Header**: "File Review"
- **Question**: "Show files for review before committing?"
- **Options**:
  1. Yes (recommended)
  2. No

**Question 6:**
- **Header**: "Auto Push"
- **Question**: "⚠️ Auto-push commits to remote? (Use with caution)"
- **Options**:
  1. No (recommended)
  2. Yes

**Question 7:**
- **Header**: "AI PRs"
- **Question**: "Enable AI-powered pull request creation?"
- **Options**:
  1. Yes (recommended)
  2. No

After gathering all answers, build the CLI command with flags (always use sonnet model for AI PRs):

```bash
sdd skills-dev start-helper setup-git-config . --non-interactive \
  --enabled \
  [--auto-branch OR --no-auto-branch] \
  [--auto-commit OR --no-auto-commit] \
  --commit-cadence [task|phase|manual] \
  [--show-files OR --no-show-files] \
  [--auto-push OR --no-auto-push] \
  [--ai-pr OR --no-ai-pr]
```

**Example command:**
```bash
sdd skills-dev start-helper setup-git-config . --non-interactive \
  --enabled \
  --auto-branch \
  --auto-commit \
  --commit-cadence task \
  --show-files \
  --no-auto-push \
  --ai-pr
```

Note: AI PRs always use the Sonnet model for optimal balance of quality and speed.

After the command completes successfully, check the return code:
- **Exit code 0**: Success - proceed to Step 5
- **Exit code non-zero**: Error - display error message and provide manual instructions

**On error:**
```
❌ Failed to save git configuration.

You can manually create .claude/git_config.json or run:
  sdd skills-dev start-helper setup-git-config . --force

See error output above for details.
```

**If user chooses "No, skip for now":**

Display message and proceed to Step 5:
```
⏭️  Skipping git configuration. You can configure it later by running:
   sdd skills-dev start-helper setup-git-config .
```

### Step 5: Show Success & Next Steps

After successful configuration, display a summary:

```
═══════════════════════════════════════════════════════════
               SDD Toolkit Setup Complete
═══════════════════════════════════════════════════════════

✅ Permissions: Configured

✅ Git Integration: [Status]
```

**If git was configured in this session**, show settings:
```
   • Auto-branch: Yes
   • Auto-commit: Yes (per task)
   • Show files before commit: Yes
   • Auto-push: No
   • AI-powered PRs: Yes (model: sonnet)
```

**If git was skipped**, show:
```
✅ Git Integration: Skipped
   (Configure later with: sdd skills-dev setup-git-config .)
```

**If git was already configured**, show:
```
✅ Git Integration: Already configured
   (Reconfigure with: sdd skills-dev setup-git-config . --force)
```

**If git was disabled by user**, show:
```
✅ Git Integration: Disabled
   (Enable later with: sdd skills-dev setup-git-config . --force)
```

Then show next steps:
```

Next steps:
• Run /sdd-begin to resume existing work or start a new specification
• Run Skill(sdd-toolkit:sdd-plan) to create a new detailed specification
• See the SDD toolkit documentation for more information
═══════════════════════════════════════════════════════════
```

## What Gets Configured

### Permissions (`.claude/settings.json`)

The setup adds these permissions:

**Skills (both forms for compatibility):**
- Skill(sdd-toolkit:run-tests) + Skill(run-tests)
- Skill(sdd-toolkit:sdd-plan) + Skill(sdd-plan)
- Skill(sdd-toolkit:sdd-next) + Skill(sdd-next)
- Skill(sdd-toolkit:sdd-update) + Skill(sdd-update)
- Skill(sdd-toolkit:sdd-plan-review) + Skill(sdd-plan-review)
- Skill(sdd-toolkit:sdd-validate) + Skill(sdd-validate)
- Skill(sdd-toolkit:code-doc) + Skill(code-doc)
- Skill(sdd-toolkit:doc-query) + Skill(doc-query)

**Commands:**
- SlashCommand(/sdd-begin)

**CLI Tools:**
- Bash(sdd:*) - Unified CLI for all sdd commands (doc, test, skills-dev, etc.)

**File Access:**
- Read(//Users/tylerburleigh/.claude/skills/**)
- Read(//**/specs/**)
- Write(//**/specs/pending/**)
- Write(//**/specs/active/**)
- Write(//**/specs/completed/**)
- Write(//**/specs/archived/**)
- Edit(//**/specs/pending/**)
- Edit(//**/specs/active/**)

### Git Integration (`.claude/git_config.json`)

If you configure git integration, the wizard creates a config file with your preferences:

**Core Settings:**
- `enabled` - Master switch for git integration
- `auto_branch` - Auto-create feature branches for specs
- `auto_commit` - Auto-commit changes on task completion
- `commit_cadence` - When to commit (task/phase/manual)
- `auto_push` - Auto-push commits to remote (⚠️ use with caution)

**File Staging:**
- `file_staging.show_before_commit` - Preview files before committing

**AI-Powered PRs:**
- `ai_pr.enabled` - Enable AI-generated PR descriptions
- `ai_pr.model` - AI model to use (sonnet/haiku/opus)
- `ai_pr.include_journals` - Include journal entries in PR context
- `ai_pr.include_diffs` - Include git diffs in PR context
- `ai_pr.max_diff_size_kb` - Max diff size before truncation

Example configuration:
```json
{
  "enabled": true,
  "auto_branch": true,
  "auto_commit": true,
  "auto_push": false,
  "commit_cadence": "task",
  "file_staging": {
    "show_before_commit": true
  },
  "ai_pr": {
    "enabled": true,
    "model": "sonnet",
    "include_journals": true,
    "include_diffs": true,
    "max_diff_size_kb": 50
  }
}
```

## Important Notes

**Permissions:**
- Setup is **non-destructive** - only adds permissions, never removes existing ones
- Can be run multiple times safely (idempotent)
- Permissions are project-specific (stored in project's `.claude/settings.json`)

**Git Configuration:**
- Git setup is optional - you can skip and configure later
- Git config can be reconfigured anytime with `--force` flag
- All git features are opt-in with safe defaults (auto_push and auto_pr default to false)
- Configuration is stored in `.claude/git_config.json`

**Frequency:**
- You only need to run this once per project
- Run again to reconfigure git settings or if permissions need updating

## Error Handling

If the setup fails:
- Check that you have write permissions in the project directory
- Ensure `.claude/` directory can be created/modified
- Review error output from the setup commands
- For git setup issues, ensure you have git installed and initialized in the project

## Integration

After running this setup:
- Use `/sdd-begin` to begin your SDD workflow
- Use `sdd-plan` skill to create specifications
- Use `sdd-next` skill to work on tasks
- Use `sdd-update` skill to track progress
