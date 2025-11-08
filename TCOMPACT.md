# Comprehensive Compact/Pretty JSON Testing Plan

## Overview

This document outlines the plan to implement and test consistent compact/pretty JSON formatting across all SDD toolkit commands.

## Current Status

### ✅ Completed (sdd_update module)

**Implementation:**
- Created `output_json(data, compact)` helper function in `sdd_update/cli.py`
- Replaced 23+ hardcoded `print(json.dumps(..., indent=2))` calls
- All sdd_update commands now support `--compact` and `--no-compact` flags

**Verified Commands:**
- `list-specs` - ✅ Working
- `list-phases` - ✅ Working
- `query-tasks` - ✅ Working (with `--simple` mode)
- Plus 20+ other sdd_update commands

**Verification:**
- `--compact` flag produces single-line compact JSON
- `--no-compact` flag produces indented pretty-printed JSON
- Config `json_compact: true` defaults to compact
- Config `json_compact: false` defaults to pretty
- Flags override config settings correctly

---

## Remaining Work

### Modules with JSON Output

Based on code analysis, the following modules have `json.dumps` calls that need standardization:

| Module | File | json.dumps Count | Priority |
|--------|------|------------------|----------|
| sdd_next | `sdd_next/cli.py` | 10 | High |
| cache | `common/cache/cli.py` | 5 | Medium |
| sdd_validate | `sdd_validate/cli.py` | 4 | High |
| context_tracker | `context_tracker/cli.py` | 3 | Low |
| sdd_fidelity_review | `sdd_fidelity_review/cli.py` | 2 | Medium |
| sdd_update | `sdd_update/cli.py` | 2 | High (missed instances) |
| sdd_plan_review | `sdd_plan_review/cli.py` | 1 | Medium |

**Total:** 27 instances across 7 modules

### Other Modules to Check

Modules that might have JSON output but need investigation:
- `code_doc/cli.py` - Documentation generation
- `doc_query/cli.py` - Query results
- `run_tests/cli.py` - Test results
- `sdd_plan/cli.py` - Plan output
- `sdd_pr/cli.py` - PR creation
- `sdd_render/cli.py` - Spec rendering
- `sdd_spec_mod/cli.py` - Spec modifications

---

## Implementation Plan

### Phase 1: Create Shared Helper (Priority: Immediate)

**Goal:** Centralize JSON output logic in one location

**Steps:**
1. Create `common/json_output.py` with `output_json(data, compact)` function
2. Add documentation and type hints
3. Include examples

**Implementation:**
```python
# src/claude_skills/claude_skills/common/json_output.py
"""
Centralized JSON output formatting for SDD toolkit.

Provides consistent compact/pretty-print JSON formatting based on
--compact/--no-compact flags and json_compact config setting.
"""

import json
from typing import Any


def output_json(data: Any, compact: bool = False) -> None:
    """
    Output JSON data with formatting based on compact flag.

    Args:
        data: Data to serialize to JSON
        compact: If True, output compact JSON on single line with minimal whitespace;
                if False, pretty-print with 2-space indentation

    Examples:
        >>> output_json({"foo": "bar"}, compact=True)
        {"foo":"bar"}

        >>> output_json({"foo": "bar"}, compact=False)
        {
          "foo": "bar"
        }
    """
    if compact:
        # Compact: single line, no spaces after separators
        print(json.dumps(data, separators=(',', ':')))
    else:
        # Pretty: indented with 2 spaces
        print(json.dumps(data, indent=2))
```

**Location:** `src/claude_skills/claude_skills/common/json_output.py`

---

### Phase 2: Update Each Module (Priority: By module priority)

**For each module, follow this process:**

#### Step 1: Add Import
```python
from claude_skills.common.json_output import output_json
```

#### Step 2: Find and Replace
- Pattern: `print(json.dumps(EXPRESSION, indent=2))`
- Replace with: `output_json(EXPRESSION, args.compact)`
- Also check for: `print(json.dumps(EXPRESSION))` (no indent specified)

#### Step 3: Verify args.compact Available
Ensure each command function has access to `args.compact`:
- Check if command handler receives `args` parameter
- Verify `args.compact` is set by global parser (it should be from `options.py`)

#### Step 4: Test Command
```bash
# Test compact
sdd COMMAND --json --compact | python -m json.tool > /dev/null && echo "Valid compact JSON"

# Test pretty
sdd COMMAND --json --no-compact | head -5 | grep "^  " && echo "Pretty printed"

# Test default (should use config)
sdd COMMAND --json | head -c 100
```

---

### Phase 3: High Priority Modules

#### 3.1: sdd_next (10 instances)

**Commands affected:**
```bash
sdd next-task --json
sdd task-info --json
sdd prepare-task --json
# ... others
```

**Test script:**
```bash
# Create test script
cat > /tmp/test_sdd_next_compact.sh << 'EOF'
#!/bin/bash
echo "Testing sdd_next compact JSON..."

# Test with compact
echo "=== next-task --compact ==="
sdd next-task SPEC_ID --json --compact | wc -l
# Should be 1 line

# Test with pretty
echo "=== next-task --no-compact ==="
sdd next-task SPEC_ID --json --no-compact | head -5
# Should have indentation

# Test other commands...
EOF

chmod +x /tmp/test_sdd_next_compact.sh
```

#### 3.2: sdd_update (2 missed instances)

**Action:** Check for any remaining `json.dumps` in sdd_update and update them

```bash
grep -n "json.dumps" src/claude_skills/claude_skills/sdd_update/cli.py
```

#### 3.3: sdd_validate (4 instances)

**Commands affected:**
```bash
sdd validate --json
sdd fix --json
sdd report --json
sdd stats --json
```

**Note:** Some commands might have `--format` flags that need removal (like we did for list-specs)

---

### Phase 4: Medium Priority Modules

#### 4.1: cache (5 instances)

**Commands:**
```bash
sdd cache list --json
sdd cache get --json
sdd cache stats --json
```

#### 4.2: sdd_fidelity_review (2 instances)

**Commands:**
```bash
sdd fidelity-review --json
```

#### 4.3: sdd_plan_review (1 instance)

**Commands:**
```bash
sdd review --json
```

---

### Phase 5: Low Priority Modules

#### 5.1: context_tracker (3 instances)

**Commands:**
```bash
sdd context --json
```

**Note:** This is a monitoring tool, JSON output may be less critical

---

## Testing Strategy

### Test Matrix

For each command with JSON output, verify:

| Test Case | Command | Expected Result |
|-----------|---------|-----------------|
| Compact flag | `cmd --json --compact` | Single-line JSON, no spaces |
| Pretty flag | `cmd --json --no-compact` | Multi-line JSON with indent |
| Config compact=true | `cmd --json` (with config) | Compact output |
| Config compact=false | `cmd --json` (with config) | Pretty output |
| Flag overrides config | `cmd --json --no-compact` (compact config) | Pretty output |
| Valid JSON | All outputs | Passes `jq` validation |

### Automated Test Script

Create comprehensive test script:

```bash
#!/bin/bash
# test_all_compact_json.sh

# List of all commands with JSON output
COMMANDS=(
    "sdd list-specs"
    "sdd list-phases SPEC_ID"
    "sdd query-tasks SPEC_ID"
    "sdd next-task SPEC_ID"
    "sdd validate SPEC_ID"
    "sdd progress SPEC_ID"
    # ... add all commands
)

echo "Testing compact/pretty JSON for all SDD commands..."
echo "=================================================="

PASSED=0
FAILED=0

for cmd in "${COMMANDS[@]}"; do
    echo "Testing: $cmd"

    # Test compact
    OUTPUT=$($cmd --json --compact 2>/dev/null)
    LINES=$(echo "$OUTPUT" | wc -l)
    if [ $LINES -le 3 ]; then
        echo "  ✅ Compact: $LINES lines"
        ((PASSED++))
    else
        echo "  ❌ Compact: $LINES lines (expected ≤3)"
        ((FAILED++))
    fi

    # Test pretty
    OUTPUT=$($cmd --json --no-compact 2>/dev/null)
    INDENTED=$(echo "$OUTPUT" | grep "^  " | wc -l)
    if [ $INDENTED -gt 0 ]; then
        echo "  ✅ Pretty: $INDENTED indented lines"
        ((PASSED++))
    else
        echo "  ❌ Pretty: No indentation found"
        ((FAILED++))
    fi

    # Validate JSON
    if echo "$OUTPUT" | jq . > /dev/null 2>&1; then
        echo "  ✅ Valid JSON"
        ((PASSED++))
    else
        echo "  ❌ Invalid JSON"
        ((FAILED++))
    fi

    echo ""
done

echo "=================================================="
echo "Results: $PASSED passed, $FAILED failed"
echo "Pass rate: $(( PASSED * 100 / (PASSED + FAILED) ))%"

exit $FAILED
```

---

## Verification Checklist

### Per Module

- [ ] `output_json` imported from `common.json_output`
- [ ] All `json.dumps` calls replaced with `output_json`
- [ ] `args.compact` passed to all `output_json` calls
- [ ] Command-specific `--format` flags removed (if applicable)
- [ ] Manual testing confirms compact/pretty work
- [ ] Automated tests pass

### Global

- [ ] All 7 CLI modules updated
- [ ] Common helper function in place
- [ ] Config `json_compact` setting respected
- [ ] Flags override config correctly
- [ ] No regressions in existing functionality
- [ ] Documentation updated

---

## Special Cases & Edge Cases

### 1. Commands with Multiple Output Formats

Some commands have `--format json|markdown|text`:

**Example:** `sdd report --format json`

**Solution:**
- Keep command-specific `--format` if it offers multiple non-JSON formats
- For commands with only `--format json|text`, remove it and use global `--json`

### 2. Commands with Streaming Output

**Example:** Progress indicators, live updates

**Solution:**
- JSON output should be final result only
- Suppress progress in JSON mode
- Document behavior

### 3. Error Output

**Current:** Some errors print to stderr, some to stdout

**Solution:**
- In JSON mode, errors should be valid JSON: `{"error": "message"}`
- Use `output_json({"error": msg}, args.compact)` for errors in JSON mode
- Keep stderr for non-JSON error messages

### 4. Empty Results

**Options:**
1. Output `[]` for empty arrays
2. Output `{}` for empty objects
3. Output `null` for no result

**Decision:** Use appropriate type:
- Lists/arrays: `[]`
- Objects/dicts: `{}`
- Optional/None: `null`

### 5. Commands without `args` Parameter

**Example:** Utility functions that print JSON

**Solution:**
- Refactor to accept `compact` parameter
- Default to `False` (pretty) for backward compatibility
- Document in function docstring

---

## Documentation Updates

### 1. User Documentation

**File:** `docs/OUTPUT_MODES.md` (create)

**Content:**
```markdown
# SDD Toolkit Output Modes

## JSON Output

### Compact vs Pretty-Printed

All SDD commands support two JSON formatting modes:

**Compact (single-line):**
```bash
sdd list-specs --json --compact
```

**Pretty-printed (indented):**
```bash
sdd list-specs --json --no-compact
```

### Configuration

Set default in `.claude/sdd_config.json`:

```json
{
  "output": {
    "json_compact": true   // or false for pretty
  }
}
```

### Flag Precedence

Command-line flags override config:
- `--compact` forces compact JSON
- `--no-compact` forces pretty JSON
- No flag uses config setting (default: compact)
```

### 2. Developer Documentation

**File:** `docs/CONTRIBUTING.md` (update)

**Add section:**
```markdown
## Adding JSON Output to Commands

When adding JSON output to a command:

1. Import the helper:
   ```python
   from claude_skills.common.json_output import output_json
   ```

2. Use it instead of print:
   ```python
   # DON'T:
   print(json.dumps(data, indent=2))

   # DO:
   output_json(data, args.compact)
   ```

3. Ensure `args.compact` is available (it's set by global parser)

4. Test both modes:
   ```bash
   sdd YOUR_COMMAND --json --compact
   sdd YOUR_COMMAND --json --no-compact
   ```
```

---

## Timeline

### Week 1: Foundation
- **Day 1:** Create `common/json_output.py`
- **Day 2:** Update high-priority modules (sdd_next, sdd_update, sdd_validate)
- **Day 3:** Test high-priority modules

### Week 2: Completion
- **Day 4:** Update medium-priority modules (cache, fidelity_review, plan_review)
- **Day 5:** Update low-priority modules (context_tracker)
- **Day 6:** Create comprehensive test script

### Week 3: Verification
- **Day 7:** Run all tests, fix issues
- **Day 8:** Update documentation
- **Day 9:** Final verification and sign-off

---

## Success Criteria

### Must Have
- ✅ All 27+ `json.dumps` calls use `output_json` helper
- ✅ `--compact` and `--no-compact` flags work on all JSON-outputting commands
- ✅ Config `json_compact` setting respected
- ✅ Flags override config correctly
- ✅ All outputs are valid JSON

### Should Have
- ✅ Automated test suite covers all commands
- ✅ 90%+ pass rate on automated tests
- ✅ Documentation updated
- ✅ No regressions in existing functionality

### Nice to Have
- ✅ Performance benchmarks (compact vs pretty)
- ✅ CI/CD integration for ongoing validation
- ✅ Examples in docs for all commands

---

## Risk Mitigation

### Risk 1: Breaking Existing Scripts

**Mitigation:**
- Default to pretty-print (current behavior)
- Config setting allows users to choose default
- Flags provide explicit control

### Risk 2: Inconsistent Implementation

**Mitigation:**
- Centralized helper function
- Clear documentation
- Code review checklist
- Automated testing

### Risk 3: Performance Impact

**Mitigation:**
- Compact JSON uses optimized separators
- Pretty JSON same as current (indent=2)
- No significant performance difference expected

---

## Appendix

### A. Full Command List

Commands that output JSON (to be verified):

**sdd_update module:**
- list-specs, list-phases, query-tasks, get-task, get-journal
- progress, status-report, audit-spec
- check-complete, phase-time, list-blockers
- reconcile-state, check-journaling
- add-assumption, list-assumptions, update-estimate
- add-task, remove-task, complete-task
- time-report

**sdd_next module:**
- next-task, task-info, prepare-task
- check-deps, find-pattern
- detect-project, find-tests, check-environment
- find-circular-deps, find-related-files
- validate-paths

**sdd_validate module:**
- validate, fix, report, stats
- analyze-deps

**cache module:**
- cache list, cache get, cache delete, cache clear
- cache stats

**sdd_fidelity_review module:**
- fidelity-review, list-review-tools

**sdd_plan_review module:**
- review, list-plan-review-tools

**context_tracker module:**
- context

### B. Reference Implementation

See `sdd_update/cli.py:56-67` for reference `output_json()` implementation.

### C. Testing Resources

- Test script: `/tmp/test_compact_json.py`
- Test results: `/tmp/compact_json_test_results.json`
- Manual test commands in this document

---

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Status:** Planning Complete - Ready for Implementation
