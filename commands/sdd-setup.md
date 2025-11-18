---
name: sdd-setup
description: First-time setup for SDD toolkit - configures project permissions and git integration
---

# SDD First-Time Setup

This command performs first-time setup for the SDD (Spec-Driven Development) toolkit in your project.

## What This Does

1. Configures `.claude/settings.local.json` with the necessary permissions for SDD skills and tools
2. **Interactively prompts for git/GitHub CLI permissions** with clear risk warnings
3. Optionally configures `.claude/git_config.json` for git integration features (branches, commits, AI-powered PRs)
4. Creates `.claude/sdd_config.json` for SDD CLI output formatting preferences (if missing)

## Workflow

### Before You Begin

Run a quick inspection to document current state (saves user surprises later):

```bash
sdd skills-dev start-helper inspect-config .
```

Use the JSON (or human-readable output) to capture whether `.claude/` exists and which of the three config files are already present. Mention in your notes if any files will be created.

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
✅ SDD permissions are fully configured!
```

**If `configured: false` AND `status: "partially_configured"`:**

Display warning with details:
```
⚠️  SDD permissions are partially configured

Missing permissions detected.
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
- Create `.claude/settings.local.json` if it doesn't exist
- Prompt for SDD CLI output preferences (if not already configured)
- Add all required SDD permissions to the `allow` list
- **Interactively prompt for git integration permissions** (see Git Permission Prompts below)
- Preserve any existing permissions

#### Git Permission Prompts

During permission setup, you'll be prompted about git integration:

**Prompt 1: Enable git integration?**
- If **Yes**: Automatically adds safe read-only permissions:
  - `git status`, `git log`, `git branch`, `git diff`, `git show`, etc.
  - `gh pr view` (GitHub CLI read operations)
- If **No**: Skips all git permissions (can be added manually later)

**Prompt 2: Enable git write operations?** (only if Prompt 1 = Yes)
- Shows risk warning about repository modifications
- If **Yes**: Adds write permissions using **three-tier model**:
  - **ALLOW list** (local writes): `git checkout`, `git add`, `git commit`, `git mv`
  - **ASK list (approval-only)**: `git push`, `git rm`, `gh pr create`
  - **ASK list (dangerous ops)**: force push, hard reset, rebase, history rewriting, force deletions
- If **No**: Keeps read-only git access only

**Risk Warning Displayed:**
```
⚠️  Git Write Operations

Write operations allow Claude to:
  • Switch branches (git checkout)
  • Stage changes (git add)
  • Create commits (git commit)
  • Push to remote (git push)
  • Remove files (git rm)
  • Create pull requests (gh pr create)

RISK: These operations can modify your repository and push changes.
Always review Claude's proposed changes before approval.

Dangerous operations requiring approval:
  • Force push (git push --force)
  • Hard reset (git reset --hard)
  • Rebase operations (git rebase)
  • History rewriting (git commit --amend)
  • Force deletion (git branch -D, git clean -f)
```

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

Gather all git configuration preferences using AskUserQuestion (you can ask up to 4 questions at once). Use the following map to translate answers directly into CLI flags:

| Feature          | AskUserQuestion prompt                                                                 | Flag when user selects "Yes"        | Flag when user selects "No" | Notes |
|------------------|----------------------------------------------------------------------------------------|-------------------------------------|-----------------------------|-------|
| Git integration  | **Header**: "Git Features" — "Enable git integration?"                                 | `--enabled`                         | `--no-enabled`              | If the user selects **No**, run the minimal command below and skip the rest. |
| Auto branch      | **Header**: "Auto Branch" — "Auto-create feature branches when starting specs?"        | `--auto-branch`                     | `--no-auto-branch`          | Only ask if git integration stays enabled. |
| Auto commit      | **Header**: "Auto Commit" — "Auto-commit changes when completing tasks?"               | `--auto-commit`                     | `--no-auto-commit`          | Controls whether to ask the commit cadence question. |
| Commit cadence   | **Header**: "Commit When" — "When should commits be created?" (task/phase/manual)      | `--commit-cadence task/phase/manual`| _N/A_ (omit flag)           | Only ask if auto-commit = Yes. |
| Show files       | **Header**: "File Review" — "Show files for review before committing?"                 | `--show-files`                      | `--no-show-files`           | Applies to staging UI. |
| Auto push        | **Header**: "Auto Push" — "⚠️ Auto-push commits to remote? (Use with caution)"         | `--auto-push`                       | `--no-auto-push`            | Highlight the risk banner before asking. |
| AI PRs           | **Header**: "AI PRs" — "Enable AI-powered pull request creation?"                      | `--ai-pr`                           | `--no-ai-pr`                | The model is always Sonnet; no extra flag required. |

**If user chooses "No, disable"** on the Git Features prompt:

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

Ask the remaining questions using the table above, collect all answers, and then build the CLI command with the corresponding flags (always use sonnet model for AI PRs):

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
sdd skills-dev start-helper setup-git-config . --non-interactive --enabled --auto-branch --auto-commit --commit-cadence task --show-files --no-auto-push --ai-pr
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

### Step 5: Configure SDD CLI Output Settings

Check if `.claude/sdd_config.json` exists and create it if missing.

**Check for existing config:**

```bash
test -f .claude/sdd_config.json && echo "exists" || echo "missing"
```

**If file is missing:**

Create `.claude/sdd_config.json` with recommended defaults by running:

```bash
sdd skills-dev start-helper ensure-sdd-config .
```

If Python fallback fails for some reason, fall back to `Write` tool with the default payload:

```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

Display:
```
✅ Created .claude/sdd_config.json with recommended settings
   (json: true, compact: true for ~30% token savings)
```

**If file already exists:**

Display:
```
✅ SDD output config already exists at .claude/sdd_config.json
   (Modify manually as needed)
```

### Step 6: Show Success & Next Steps

After successful configuration, display a summary:

```
═══════════════════════════════════════════════════════════
               SDD Toolkit Setup Complete
═══════════════════════════════════════════════════════════

✅ Permissions: Configured

✅ Git Integration: [Status]

✅ SDD CLI Config: [Status]

Files updated:
  • `.claude/settings.local.json` (permissions)
  • `.claude/git_config.json` (only list if created/updated in this run)
  • `.claude/sdd_config.json` (only list if created in this run)
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

**For SDD CLI Config status:**

**If sdd_config.json was created in this session**, show:
```
✅ SDD CLI Config: Created
   (json: true, compact: true for ~30% token savings)
```

**If sdd_config.json already existed**, show:
```
✅ SDD CLI Config: Already configured
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

### Permissions (`.claude/settings.local.json`)

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
- Bash(cursor-agent:*)
- Bash(gemini:*)
- Bash(codex:*)

**File Access:**
- Read(//**/specs/**)
- Write(//**/specs/pending/**)
- Write(//**/specs/active/**)
- Write(//**/specs/completed/**)
- Write(//**/specs/archived/**)
- Edit(//**/specs/pending/**)
- Edit(//**/specs/active/**)

**Git/GitHub Permissions (Prompted During Setup):**

During the interactive setup, you'll be prompted to enable git integration permissions. The setup uses a **three-tier permission model** for safety:

**If you enable git integration + write operations:**
- **ALLOW list** (read operations): `git status`, `git log`, `git branch`, `git diff`, `git show`, `git describe`, `git rev-parse`, `gh pr view`
- **ALLOW list** (local write operations): `git checkout`, `git add`, `git commit`, `git mv`
- **ASK list** (approval-required operations): `git push`, `git rm`, `gh pr create`
- **ASK list** (dangerous operations requiring approval):
  - Force operations: `git push --force`, `git push -f`, `git push --force-with-lease`, `git clean -f*`
  - History rewriting: `git reset --hard`, `git reset --mixed`, `git reset`, `git rebase`, `git commit --amend`, `git filter-branch`, `git filter-repo`
  - Deletion operations: `git branch -D`, `git push origin --delete`, `git tag -d`
  - Reflog/stash: `git reflog expire`, `git reflog delete`, `git stash drop`, `git stash clear`
  - Aggressive GC: `git gc --prune=now`

**If you enable git integration (read-only):**
- **ALLOW list**: `git status`, `git log`, `git branch`, `git diff`, `git show`, `git describe`, `git rev-parse`, `gh pr view`
- No write permissions added

**If you skip git setup:**
- No git permissions added (you can manually add them to `.claude/settings.local.json` later)

**Three-Tier Permission Model:**
1. **ALLOW**: Read-only operations and safe writes execute automatically without prompts
2. **ASK**: Dangerous operations (data loss risk, history rewriting) require explicit user approval
3. **DENY**: Blocked operations (not used by default in SDD setup)

This model provides a balance between workflow efficiency and safety - routine git operations (commit, push, checkout) work automatically, while potentially destructive operations (force push, hard reset, rebase) always require your explicit approval.

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

### SDD CLI Output Configuration (`.claude/sdd_config.json`)

The setup creates a configuration file for SDD CLI output formatting:

**Output Settings:**
- `output.json` - Output JSON format (default: `true`)
- `output.compact` - Use compact JSON formatting (default: `true`)

**Benefits:**
- ~30% token savings with compact JSON output
- Consistent output formatting across all SDD commands
- Can be overridden with CLI flags (`--json`, `--compact`, etc.)

**Default configuration:**
```json
{
  "output": {
    "json": true,
    "compact": true
  }
}
```

**Configuration precedence:**
1. Built-in defaults (`json: true`, `compact: true`)
2. Global config (`~/.claude/sdd_config.json`)
3. Project config (`./.claude/sdd_config.json`)
4. CLI arguments (highest priority)

## Important Notes

**Permissions:**
- Setup is **non-destructive** - only adds permissions, never removes existing ones
- Can be run multiple times safely (idempotent)
- Permissions are project-specific (stored in project's `.claude/settings.local.json`)

**Git Configuration:**
- Git setup is optional - you can skip and configure later
- Git config can be reconfigured anytime with `--force` flag
- All git features are opt-in with safe defaults (auto_push and auto_pr default to false)
- Configuration is stored in `.claude/git_config.json`

**SDD CLI Output Configuration:**
- Setup creates `.claude/sdd_config.json` automatically if missing
- Uses safe defaults (`json: true`, `compact: true`)
- Non-destructive - won't overwrite existing configuration
- Can be modified manually or via CLI flags on individual commands

**Frequency:**
- You only need to run this once per project
- Run again to reconfigure git settings or if permissions need updating
- sdd_config.json is created automatically but can be edited anytime

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
