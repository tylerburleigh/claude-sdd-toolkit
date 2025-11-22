# Troubleshooting

Common issues and solutions for the SDD Toolkit. If you don't find your issue here, check [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues).

## Table of Contents

- [Installation Issues](#installation-issues)
- [Setup and Configuration](#setup-and-configuration)
- [Skill Execution Issues](#skill-execution-issues)
- [CLI Command Issues](#cli-command-issues)
- [Validation Errors](#validation-errors)
- [AI Tool Failures](#ai-tool-failures)
- [Git Integration Issues](#git-integration-issues)
- [Documentation Generation Issues](#documentation-generation-issues)
- [Performance Issues](#performance-issues)
- [Getting More Help](#getting-more-help)

---

## Installation Issues

### Skills Not Working

**Symptoms:**
- Skills don't appear in Claude Code
- `/sdd-setup` command not found
- Slash commands missing

**Diagnosis:**
```bash
ls ~/.claude/plugins/marketplaces/claude-sdd-toolkit/skills/
# Should show: sdd-plan, sdd-next, doc-query, llm-doc-gen, etc.
```

**Solution:**

1. **Verify plugin installed:**
   ```
   Claude Code → /plugins → Manage and uninstall
   # Verify claude-sdd-toolkit is listed
   ```

2. **Reinstall if missing:**
   ```
   /plugins → Add from marketplace → tylerburleigh/claude-sdd-toolkit
   ```

3. **Restart Claude Code** after installation

---

### CLI Commands Not Found

**Symptoms:**
```bash
sdd --version
# command not found: sdd
```

**Diagnosis:**
```bash
which sdd
# sdd not found
```

**Solution:**

1. **Install Python package:**
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e .
   ```

2. **Verify installation:**
   ```bash
   which sdd
   # Should show: /usr/local/bin/sdd (or similar)

   sdd --version
   # Should show: SDD Toolkit 0.7.1
   ```

3. **Check PATH if still not found:**
   ```bash
   echo $PATH
   # Verify pip's bin directory is in PATH
   ```

---

### Python Version Incompatibility

**Symptoms:**
```bash
pip install -e .
# ERROR: Requires Python >=3.9, but you have 3.8
```

**Solution:**

1. **Check Python version:**
   ```bash
   python --version
   # or
   python3 --version
   ```

2. **Upgrade Python to 3.9+:**
   - **macOS (Homebrew):** `brew install python@3.11`
   - **Ubuntu/Debian:** `sudo apt install python3.11`
   - **Windows:** Download from [python.org](https://python.org)

3. **Use specific Python version:**
   ```bash
   python3.11 -m pip install -e .
   ```

---

### After Plugin Update

**Symptoms:**
- New features not working
- Commands behaving differently
- Skills missing or broken

**Solution:**

**Always reinstall Python package after updating plugin:**

```bash
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**Then restart Claude Code.**

---

## Setup and Configuration

### /sdd-setup Creates No Files

**Symptoms:**
```bash
ls -la .claude/
# No settings.local.json, sdd_config.json, etc.
```

**Diagnosis:**
- Claude Code not running
- Plugin not properly installed
- Permission issues

**Solution:**

1. **Verify Claude Code is running:**
   ```bash
   ps aux | grep claude
   ```

2. **Run setup again:**
   ```
   /sdd-setup
   ```

3. **Check for errors in Claude Code logs**

4. **Manual creation if needed:**
   ```bash
   mkdir -p .claude
   # Copy templates from plugin directory
   cp ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills/common/templates/setup/*.json .claude/
   ```

---

### Permission Errors

**Symptoms:**
```
Error: Permission denied: specs/active/my-spec.json
PermissionError: [Errno 13] Permission denied
```

**Diagnosis:**
- `.claude/settings.local.json` missing or incomplete
- Permissions not properly granted

**Solution:**

1. **Run setup:**
   ```
   /sdd-setup
   ```

2. **Verify permissions file:**
   ```bash
   cat .claude/settings.local.json
   # Should include specs/** in Write/Read/Edit paths
   ```

3. **Restart Claude Code** after updating permissions

4. **Manual fix if needed:**

   Edit `.claude/settings.local.json`:
   ```json
   {
     "dangerouslySkipPermissionsForPaths": {
       "Write": ["specs/**", ".claude/**"],
       "Read": ["specs/**", ".claude/**"],
       "Edit": ["specs/**"]
     }
   }
   ```

---

### Invalid JSON in Configuration

**Symptoms:**
```
JSONDecodeError: Expecting ',' delimiter: line 4 column 5
```

**Diagnosis:**
```bash
cat .claude/sdd_config.json | python -m json.tool
# Syntax error in JSON
```

**Solution:**

1. **Validate JSON:**
   ```bash
   cat .claude/sdd_config.json | python -m json.tool
   ```

2. **Common issues:**
   - Trailing commas (not allowed in JSON)
   - Missing quotes around strings
   - Unclosed brackets or braces

3. **Reset to defaults:**
   ```bash
   rm .claude/sdd_config.json
   /sdd-setup  # Recreates with defaults
   ```

---

## Skill Execution Issues

### Skill Hangs or Times Out

**Symptoms:**
- Skill starts but never completes
- "Skill is loading..." for extended time
- No response from skill

**Diagnosis:**
- AI provider timeout
- Large codebase causing slow analysis
- Network issues

**Solution:**

1. **Check AI tool availability:**
   ```bash
   sdd test check-tools
   ```

2. **Increase timeout** (if configuration supports it)

3. **Use faster models:**

   Edit `.claude/ai_config.yaml`:
   ```yaml
   sdd-plan-review:
     models:
       gemini: gemini-2.5-flash  # Faster than pro
   ```

4. **Reduce scope:**
   - Generate docs for specific directories only
   - Review smaller specs or phases

---

### "No Active Work Found"

**Symptoms:**
```
You: /sdd-begin

Claude: 📋 No active SDD work found.
```

**Diagnosis:**
```bash
ls specs/active/
# Empty directory
```

**Solution:**

1. **Check for pending specs:**
   ```bash
   sdd list-specs --status pending
   ```

2. **Activate a pending spec:**
   ```bash
   sdd activate-spec <spec-id>
   ```

3. **Or create a new spec:**
   ```
   You: Create a spec for [your feature]
   ```

---

### Task Marked as Blocked

**Symptoms:**
```
Claude: Task 1-3 is blocked by incomplete dependencies
```

**Diagnosis:**
```bash
sdd check-deps my-spec-001 task-1-3 --json
```

**Solution:**

1. **View dependencies:**
   ```bash
   sdd task-info my-spec-001 task-1-3
   # Shows: "dependencies": ["task-1-1", "task-1-2"]
   ```

2. **Complete blocking tasks first:**
   ```bash
   sdd progress my-spec-001
   # Identify incomplete tasks
   ```

3. **Or unblock if dependencies resolved:**
   ```bash
   sdd unblock-task my-spec-001 task-1-3 --resolution "Dependency resolved"
   ```

4. **Fix spec if dependency is wrong:**
   - Edit spec JSON manually
   - Remove incorrect dependency
   - Run `sdd validate <spec> --fix`

---

## CLI Command Issues

### Command Not Recognized

**Symptoms:**
```bash
sdd unknown-command
# Error: Command 'unknown-command' not found
```

**Solution:**

1. **Check command spelling:**
   ```bash
   sdd --help
   # Lists all available commands
   ```

2. **Verify correct category:**
   ```bash
   # Wrong:
   sdd stats

   # Right:
   sdd doc stats
   ```

3. **Update to latest version:**
   ```bash
   cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
   pip install -e . --upgrade
   ```

---

### Output Format Issues

**Symptoms:**
- Unexpected output format
- JSON parsing errors
- Missing fields in output

**Diagnosis:**
```bash
sdd progress my-spec
# Check default output format
```

**Solution:**

1. **Explicitly specify format:**
   ```bash
   sdd progress my-spec --json --compact
   ```

2. **Check configuration:**
   ```bash
   cat .claude/sdd_config.json
   # Verify output.default_mode setting
   ```

3. **Override config with flags:**
   ```bash
   sdd progress my-spec --rich  # Force rich output
   ```

---

## Validation Errors

### Circular Dependency Detected

**Symptoms:**
```bash
sdd validate my-spec.json
# ERROR: Circular dependency: task-1 → task-2 → task-1
```

**Diagnosis:**
```bash
sdd validate my-spec.json --show-graph
# Visualize dependency graph
```

**Solution:**

1. **Auto-fix:**
   ```bash
   sdd validate my-spec.json --fix
   ```

2. **Manual fix:**
   - Edit spec JSON
   - Remove circular dependency
   - Keep the more important dependency

3. **Verify fix:**
   ```bash
   sdd validate my-spec.json
   # Should pass
   ```

---

### Invalid Task References

**Symptoms:**
```bash
sdd validate my-spec.json
# ERROR: Task 'task-99' referenced but not defined
```

**Diagnosis:**
- Dependency references non-existent task
- Typo in task ID
- Task was deleted but dependency remains

**Solution:**

1. **Find the problematic reference:**
   ```bash
   cat my-spec.json | grep "task-99"
   ```

2. **Fix the reference:**
   - Update to correct task ID, or
   - Remove the dependency

3. **Validate:**
   ```bash
   sdd validate my-spec.json
   ```

---

### Schema Validation Failures

**Symptoms:**
```bash
sdd validate my-spec.json
# ERROR: Required field 'title' missing in task-1-1
```

**Solution:**

1. **Try auto-fix:**
   ```bash
   sdd validate my-spec.json --fix
   ```

2. **Manual fix:**
   - Open spec JSON
   - Add missing required fields
   - Follow schema at `specification-schema.json`

3. **Required fields for tasks:**
   ```json
   {
     "id": "task-1-1",
     "title": "Task title",
     "type": "task",
     "status": "pending",
     "parent": "parent-id"
   }
   ```

---

## AI Tool Failures

### AI Provider Not Available

**Symptoms:**
```bash
sdd test check-tools
# ❌ gemini: Not found in PATH
```

**Solution:**

**For gemini:**
```bash
# Install gemini CLI
pip install google-generativeai

# Set API key
export GEMINI_API_KEY="your-key-here"

# Test
gemini "test message"
```

**For cursor-agent:**
- Ensure Cursor IDE is installed and running
- Verify Composer is accessible
- Check Cursor settings

**For codex:**
```bash
# Install codex CLI
pip install anthropic-codex

# Configure
codex configure
```

**For claude:**
```bash
# Requires Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

---

### Rate Limiting

**Symptoms:**
```
Error: Rate limit exceeded (429)
Retry after: 60 seconds
```

**Solution:**

1. **Wait for rate limit to reset** (usually 60 seconds)

2. **Use different provider:**

   Edit `.claude/ai_config.yaml`:
   ```yaml
   tool_priority:
     default:
       - cursor-agent  # Switch primary provider
       - gemini
   ```

3. **Reduce frequency:**
   - Space out review requests
   - Use caching (results are cached automatically)

4. **Upgrade API tier** (if available for your provider)

---

### Multi-Model Consultation Fails

**Symptoms:**
```
Consulting cursor-agent and gemini...
cursor-agent: FAILED
gemini: FAILED
Error: No models succeeded
```

**Solution:**

1. **Check tool availability:**
   ```bash
   sdd test check-tools
   ```

2. **Configure fallback:**

   At least one model must work. Update `.claude/ai_config.yaml`:
   ```yaml
   tool_priority:
     default:
       - gemini
       - cursor-agent
       - codex  # Add fallback
   ```

3. **Use single model:**
   ```bash
   sdd plan-review my-spec.json --model gemini=gemini-2.5-flash
   ```

---

## Git Integration Issues

### Git Not Configured

**Symptoms:**
```
Error: Git user not configured
Please configure git with user.name and user.email
```

**Solution:**

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**Verify:**
```bash
git config --get user.name
git config --get user.email
```

---

### GitHub CLI Not Authenticated

**Symptoms:**
```
Error: gh not authenticated
Failed to create pull request
```

**Solution:**

```bash
gh auth login
# Follow prompts to authenticate
```

**Verify:**
```bash
gh auth status
# Should show: Logged in to github.com
```

---

### Auto-commit Fails

**Symptoms:**
```
Error: No changes to commit
Auto-commit failed
```

**Diagnosis:**
- No files modified
- Files already committed
- Git tracking issues

**Solution:**

1. **Check git status:**
   ```bash
   git status
   ```

2. **Verify files were modified:**
   ```bash
   git diff
   ```

3. **Disable auto-commit if not needed:**

   Edit `.claude/git_config.json`:
   ```json
   {
     "auto_commit": false
   }
   ```

---

## Documentation Generation Issues

### Documentation Not Generated

**Symptoms:**
```bash
sdd doc stats
# Error: docs/codebase.json not found
```

**Solution:**

1. **Generate documentation first:**
   ```bash
   sdd doc generate . --parallel
   ```

2. **Or with AI enhancement:**
   ```bash
   sdd doc analyze-with-ai . --name "MyProject"
   ```

3. **Verify output:**
   ```bash
   ls docs/
   # Should show: codebase.json, index.md, etc.
   ```

---

### Missing Language Support

**Symptoms:**
```
Warning: No parser for .rs files (Rust)
Skipping 42 Rust files
```

**Solution:**

1. **Check supported languages:**
   - Python, JavaScript, TypeScript are built-in
   - Other languages need tree-sitter grammars

2. **Install tree-sitter grammar:**
   ```bash
   # Example for Rust
   pip install tree-sitter-rust
   ```

3. **Regenerate docs:**
   ```bash
   sdd doc generate . --parallel --force
   ```

---

### Documentation Too Large

**Symptoms:**
```
Warning: codebase.json is 50MB
May cause performance issues
```

**Solution:**

1. **Use aggressive filtering:**
   ```bash
   sdd doc generate . --filter-mode aggressive
   ```

2. **Exclude directories:**
   ```bash
   sdd doc generate src/ --parallel
   # Only document src/, not tests/, etc.
   ```

3. **Use scope for specific files:**
   ```bash
   sdd doc scope src/core/app.py --plan
   ```

---

## Performance Issues

### Slow Spec Operations

**Symptoms:**
- `sdd progress` takes >5 seconds
- `/sdd-begin` very slow
- Operations timeout

**Diagnosis:**
- Very large spec files (>1MB)
- Many specs in active/

**Solution:**

1. **Use compact JSON:**

   Edit `.claude/sdd_config.json`:
   ```json
   {
     "output": {
       "json_compact": true
     }
   }
   ```

2. **Archive old specs:**
   ```bash
   mv specs/active/old-spec.json specs/archived/
   ```

3. **Split large specs into smaller ones**

---

### Context Limit Reached

**Symptoms:**
```
Warning: Context usage at 87%
Recommend /clear and /sdd-begin
```

**Solution:**

1. **Clear context:**
   ```
   /clear
   ```

2. **Resume work:**
   ```
   /sdd-begin
   ```

3. **All progress is saved** - specs track everything

4. **Use autonomous mode with context checks** (stops at 85%)

---

### High Memory Usage

**Symptoms:**
- System slowing down
- Python process using >2GB RAM
- Out of memory errors

**Diagnosis:**
```bash
ps aux | grep python
# Check memory usage
```

**Solution:**

1. **Process smaller directories:**
   ```bash
   sdd doc generate src/core/ --parallel
   sdd doc generate src/api/ --parallel
   ```

2. **Disable parallel processing:**
   ```bash
   sdd doc generate . --no-parallel
   ```

3. **Increase system swap** (if needed)

---

## Getting More Help

### Check Logs

**Claude Code logs:**
```bash
# macOS
~/Library/Logs/Claude/

# Linux
~/.config/Claude/logs/

# Windows
%APPDATA%\Claude\logs\
```

### Debug Mode

```bash
# Enable verbose output
sdd progress my-spec --verbose

# Check full errors
sdd validate my-spec.json --verbose 2>&1 | tee error.log
```

### Report Issues

**Before reporting:**
1. Check this troubleshooting guide
2. Check [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
3. Gather reproduction steps

**Report at:**
- [GitHub Issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- Include:
  - SDD Toolkit version (`sdd --version`)
  - Python version (`python --version`)
  - Operating system
  - Full error message
  - Reproduction steps

### Community Help

- GitHub Discussions: [github.com/tylerburleigh/claude-sdd-toolkit/discussions](https://github.com/tylerburleigh/claude-sdd-toolkit/discussions)
- Claude Code Documentation: [docs.claude.com/claude-code](https://docs.claude.com/claude-code)

---

## Quick Reference

**Installation:**
```bash
# Reinstall Python package
cd ~/.claude/plugins/marketplaces/claude-sdd-toolkit/src/claude_skills
pip install -e .
```

**Setup:**
```
/sdd-setup
```

**Validation:**
```bash
sdd validate my-spec.json --fix
```

**Tools Check:**
```bash
sdd test check-tools
```

**Documentation:**
```bash
sdd doc generate . --parallel
```

**Progress:**
```bash
sdd progress my-spec --json
```

---

**Related Documentation:**
- [Installation Guide](../INSTALLATION.md) - Detailed installation steps
- [Configuration](configuration.md) - Configuration options
- [Skills Reference](skills-reference.md) - How to use skills
- [CLI Reference](cli-reference.md) - Command-line reference
