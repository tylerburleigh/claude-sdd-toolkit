---
name: sdd-setup
description: First-time setup for SDD toolkit - configures project permissions
---

# SDD First-Time Setup

This command performs first-time setup for the SDD (Spec-Driven Development) toolkit in your project.

## What This Does

Configures `.claude/settings.json` with the necessary permissions for SDD skills and tools to work properly in your project.

## Workflow

### Step 1: Check Current Configuration

First, check if SDD permissions are already configured:

```bash
sdd skills-dev setup-permissions -- check .
```

The script will return JSON with a `configured` field indicating whether permissions are set up.

### Step 2: Configure if Needed

**If `configured: true`:**

Display this message and exit:
```
✅ SDD permissions are already configured for this project!

You're all set. Run /sdd-start to begin working with specifications.
```

**If `configured: false`:**

Inform the user and run the setup:
```
Setting up SDD permissions for this project...
```

Then run:
```bash
sdd skills-dev setup-permissions -- update .
```

This will:
- Create `.claude/settings.json` if it doesn't exist
- Add all required SDD permissions to the `allow` list
- Preserve any existing permissions

### Step 3: Show Success & Next Steps

After successful configuration, display:
```
✅ SDD permissions configured successfully!

Next steps:
• Run /sdd-start to resume existing work or start a new specification
• Run sdd-plan skill to create a new detailed specification
• See the SDD toolkit documentation for more information
```

## What Gets Configured

The setup adds these permissions to `.claude/settings.json`:

**Skills:**
- Skill(run-tests)
- Skill(sdd-plan)
- Skill(sdd-next)
- Skill(sdd-update)
- Skill(sdd-plan-review)
- Skill(sdd-validate)
- Skill(code-doc)
- Skill(doc-query)

**Commands:**
- SlashCommand(/sdd-start)

**CLI Tools:**
- Bash(sdd-next:*)
- Bash(sdd-update:*)
- Bash(sdd-plan:*)
- Bash(doc-query:*)
- Bash(sdd-validate:*)
- Bash(run-tests:*)
- Bash(code-doc:*)
- Bash(sdd-review:*)
- Bash(sdd-integration:*)
- Bash(sdd-start-helper:*)
- Bash(setup-project-permissions:*)
- Bash(claude-skills-gendocs:*)

**File Access:**
- Read(//Users/tylerburleigh/.claude/skills/**)
- Read(//**/specs/**)
- Write(//**/specs/active/**)
- Write(//**/specs/completed/**)
- Write(//**/specs/archived/**)
- Edit(//**/specs/active/**)

## Important Notes

- This command is **non-destructive** - it only adds permissions, never removes existing ones
- The command can be run multiple times safely (idempotent)
- Permissions are project-specific (stored in project's `.claude/settings.json`)
- You only need to run this once per project

## Error Handling

If the setup fails:
- Check that you have write permissions in the project directory
- Ensure `.claude/` directory can be created/modified
- Review error output from the `setup-permissions` script

## Integration

After running this setup:
- Use `/sdd-start` to begin your SDD workflow
- Use `sdd-plan` skill to create specifications
- Use `sdd-next` skill to work on tasks
- Use `sdd-update` skill to track progress
