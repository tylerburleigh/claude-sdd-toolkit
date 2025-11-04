# Migration Guide: Compact JSON Output (v2.0)

This guide documents the migration path for the compact JSON output format changes introduced in the SDD Toolkit.

## Overview

The SDD CLI commands are transitioning from verbose JSON output (with emoji decorators and formatting) to a compact, machine-readable JSON format. This migration happens in two phases to ensure backward compatibility.

## Migration Timeline

### Phase 1: Opt-in via `--compact` flag (Current)

**Status:** Available now (v1.x)

**What's Changed:**
- New `--compact` flag available for all JSON-outputting commands
- Opt-in: Commands still use verbose format by default
- Both formats supported simultaneously

**Affected Commands:**
- `sdd prepare-task`
- `sdd task-info`
- `sdd check-deps`
- `sdd progress`
- `sdd next-task`
- `sdd query-tasks`
- `sdd list-blockers`
- `sdd list-phases`
- `sdd check-complete`
- `sdd spec-stats`
- `sdd find-specs`

**How to Use:**
```bash
# Old verbose format (default in Phase 1)
sdd prepare-task my-spec-001 --json

# New compact format (opt-in in Phase 1)
sdd prepare-task my-spec-001 --json --compact
```

**Recommended Actions:**
1. **Test your integrations** with `--compact` flag
2. **Update scripts and automation** to use `--compact` where appropriate
3. **Update documentation** to reference `--compact` examples
4. **Provide feedback** if you encounter issues

### Phase 2: Compact by default (v2.0) - Planned

**Status:** Planned for v2.0 release

**What Will Change:**
- `--json` flag will output compact format by default
- New `--verbose` flag will restore old decorated format
- Reverse of current behavior

**How It Will Work:**
```bash
# Compact format (default in Phase 2)
sdd prepare-task my-spec-001 --json

# Verbose format (opt-in in Phase 2)
sdd prepare-task my-spec-001 --json --verbose
```

**Migration Path:**
1. Update scripts using `--json` to explicitly use `--json --compact` (Phase 1)
2. After v2.0 release, remove `--compact` flag (it becomes default)
3. Use `--verbose` flag only if you specifically need decorated output

## Format Differences

### Verbose Format (Phase 1 default, Phase 2 via `--verbose`)

**Characteristics:**
- Includes emoji decorators (⚠️, ✅, 🚧, etc.)
- Human-readable formatting in JSON values
- Colored output markers
- Formatted text blocks

**Example:**
```json
{
  "success": true,
  "task_id": "task-1-1",
  "message": "✅ Task prepared successfully",
  "warnings": [
    "⚠️  Spec validation warning: Missing estimated_hours"
  ]
}
```

**Best For:**
- Direct human consumption
- Interactive terminal sessions
- Debugging and troubleshooting
- One-off command execution

### Compact Format (Phase 1 via `--compact`, Phase 2 default)

**Characteristics:**
- No emoji decorators
- Plain text values
- Optimized for parsing
- Consistent structure

**Example:**
```json
{
  "success": true,
  "task_id": "task-1-1",
  "message": "Task prepared successfully",
  "warnings": [
    "Spec validation warning: Missing estimated_hours"
  ]
}
```

**Best For:**
- Scripting and automation
- CI/CD pipelines
- Integration with other tools
- JSON parsing libraries
- Long-term data storage

## Backward Compatibility

### During Phase 1 (Current)

**Guarantees:**
- All existing scripts continue to work unchanged
- Default behavior remains verbose format
- `--compact` flag is optional

**No Breaking Changes:**
- Existing integrations unaffected
- All JSON fields preserved
- Output structure unchanged (only decorators removed)

### During Phase 2 (v2.0)

**Breaking Change:**
- `--json` flag changes default from verbose to compact
- Scripts relying on emoji decorators will need updates

**Mitigation:**
- Use `--verbose` flag to restore Phase 1 behavior
- Update parsers to ignore/strip decorators
- Transition period with deprecation warnings

**What's Preserved:**
- All JSON field names stay the same
- Data structure remains identical
- Only text decorations change

## Migration Checklist

### For Script/Tool Authors

- [ ] Test integration with `--compact` flag (Phase 1)
- [ ] Update JSON parsers to handle both formats
- [ ] Remove assumptions about emoji presence in strings
- [ ] Add `--compact` to command invocations
- [ ] Update documentation examples
- [ ] Plan for v2.0 default behavior change

### For Interactive Users

- [ ] Familiarize yourself with `--compact` output
- [ ] Use `--compact` for script/automation contexts
- [ ] Continue using default format for interactive sessions
- [ ] Prepare for `--verbose` flag in v2.0

### For Documentation Maintainers

- [ ] Update command examples to use `--compact`
- [ ] Document both format options
- [ ] Add migration timeline to guides
- [ ] Highlight behavior change in v2.0 release notes

## Common Migration Scenarios

### Scenario 1: Parsing Task Information

**Phase 1 (Before):**
```bash
# Script expecting verbose format
TASK_ID=$(sdd next-task my-spec --json | jq -r '.task_id')
# Works, but may encounter "✅ task-1-1" instead of "task-1-1"
```

**Phase 1 (Recommended):**
```bash
# Script using compact format
TASK_ID=$(sdd next-task my-spec --json --compact | jq -r '.task_id')
# Always returns "task-1-1" (no decorators)
```

**Phase 2 (v2.0):**
```bash
# Compact is default, no flag needed
TASK_ID=$(sdd next-task my-spec --json | jq -r '.task_id')
```

### Scenario 2: CI/CD Pipeline Integration

**Phase 1 (Before):**
```yaml
# .github/workflows/ci.yml
- name: Prepare next task
  run: |
    sdd prepare-task $SPEC_ID --json > task.json
    # May need to strip emojis from output
```

**Phase 1 (Recommended):**
```yaml
# .github/workflows/ci.yml
- name: Prepare next task
  run: |
    sdd prepare-task $SPEC_ID --json --compact > task.json
    # Clean JSON output, no emoji stripping needed
```

**Phase 2 (v2.0):**
```yaml
# .github/workflows/ci.yml
- name: Prepare next task
  run: |
    sdd prepare-task $SPEC_ID --json > task.json
    # Compact format by default
```

### Scenario 3: Custom Tooling

**Phase 1 (Before):**
```python
import subprocess
import json
import re

# Custom tool parsing SDD output
result = subprocess.run(['sdd', 'task-info', spec_id, task_id, '--json'],
                       capture_output=True, text=True)
data = json.loads(result.stdout)

# Need to strip emojis from text fields
def strip_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

task_title = strip_emojis(data['task_data']['title'])
```

**Phase 1 (Recommended):**
```python
import subprocess
import json

# Custom tool using compact format
result = subprocess.run(['sdd', 'task-info', spec_id, task_id, '--json', '--compact'],
                       capture_output=True, text=True)
data = json.loads(result.stdout)

# No emoji stripping needed
task_title = data['task_data']['title']
```

**Phase 2 (v2.0):**
```python
import subprocess
import json

# Compact format is default
result = subprocess.run(['sdd', 'task-info', spec_id, task_id, '--json'],
                       capture_output=True, text=True)
data = json.loads(result.stdout)

task_title = data['task_data']['title']
```

## Troubleshooting

### Issue: Script breaks with `--compact` flag

**Symptom:** Script fails when adding `--compact` flag

**Cause:** Script may be checking for specific emoji strings

**Solution:**
1. Update regex patterns to not expect emojis
2. Check field values directly without string matching on decorators
3. Use JSON field values as-is without transformation

### Issue: Missing visual cues in output

**Symptom:** Hard to read JSON output interactively

**Solution:** Use `jq` or similar formatters for pretty-printing:
```bash
sdd prepare-task my-spec --json --compact | jq .
```

### Issue: Need verbose format after v2.0

**Symptom:** Prefer emoji decorators for readability

**Solution:** Use `--verbose` flag in v2.0:
```bash
sdd prepare-task my-spec --json --verbose
```

## Frequently Asked Questions

### Q: When should I use `--compact`?

**A:** Use `--compact` when:
- Writing scripts or automation
- Integrating with CI/CD pipelines
- Storing JSON for later processing
- Parsing output with JSON libraries
- Building tools on top of SDD CLI

### Q: When should I use verbose format?

**A:** Use verbose format (default in Phase 1, `--verbose` in Phase 2) when:
- Interactively reading command output
- Debugging issues manually
- Needing visual cues for status (✅, ⚠️, etc.)
- Working directly in terminal

### Q: Will my existing scripts break in v2.0?

**A:** Scripts using `--json` flag without `--compact` will get compact output by default in v2.0. If your scripts:
- **Parse JSON properly**: No changes needed (structure is identical)
- **Expect emoji decorators**: Add `--verbose` flag or update to handle both formats

### Q: What's the timeline for v2.0?

**A:** The v2.0 release timeline will be announced separately. Phase 1 provides a transition period to migrate scripts before the default behavior changes.

### Q: Can I mix formats in my workflow?

**A:** Yes! You can use compact format for scripts and verbose format for interactive commands in the same workflow.

## Additional Resources

- **Compact JSON Output Specification**: See spec `compact-json-output-2025-11-03-001.json`
- **CLI Reference**: Run `sdd --help` for command-specific options
- **Examples**: See `docs/examples/` for updated script examples
- **Release Notes**: Check release notes for v2.0 announcement

## Support

If you encounter issues during migration:

1. **Check this guide** for common scenarios
2. **Review examples** in `docs/examples/`
3. **Open an issue** on GitHub with details about your use case
4. **Provide feedback** on the migration process

## Version History

- **v1.x (Phase 1)**: `--compact` flag available, verbose format default
- **v2.0 (Phase 2)**: Compact format default, `--verbose` flag available

---

**Last Updated:** 2025-11-03
**Status:** Phase 1 (Opt-in compact format)
