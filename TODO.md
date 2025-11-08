# SDD Toolkit - TODO: Output Mode Testing

## Overview

We've comprehensively tested JSON output mode (`--json` flag and `default_mode: json` config). This document outlines testing for other output modes and configurations.

## Current Status

✅ **JSON Mode Testing Complete**
- 34/34 testable commands output valid JSON
- All rich UI properly suppressed in JSON mode
- Config `default_mode: json` properly respected
- 100% pass rate achieved

## Remaining Output Modes to Test

### 1. Text Mode (Default Rich UI)

**What to Test:**
- Default output when `default_mode: text` (or not set)
- Rich UI output (colors, formatting, tables)
- Proper use of PrettyPrinter for human-readable output

**Test Cases:**
```bash
# With config default_mode: text
sdd list-specs                    # Should show rich table
sdd progress <spec>                # Should show progress bars
sdd status-report <spec>           # Should show formatted report

# With --no-json flag (override config)
sdd list-specs --no-json           # Force text output
sdd progress <spec> --no-json      # Force rich UI
```

**Success Criteria:**
- Commands output human-readable, formatted text
- Colors and formatting work correctly
- Tables, progress bars, and other rich UI elements display properly
- No JSON output when in text mode

---

### 2. Compact vs Pretty JSON

**What to Test:**
- `--compact` flag produces single-line JSON
- `--no-compact` flag produces indented JSON
- Config `json_compact: true/false` respected

**Test Cases:**
```bash
# Test compact flag
sdd list-specs --json --compact    # Should be one line
sdd progress <spec> --json --compact

# Test pretty-print flag
sdd list-specs --json --no-compact  # Should be indented
sdd progress <spec> --json --no-compact

# Test config setting
# Set json_compact: true in config
sdd list-specs --json               # Should be compact

# Set json_compact: false in config
sdd list-specs --json               # Should be pretty
```

**Success Criteria:**
- `--compact` produces valid JSON on single line (or minimal lines)
- `--no-compact` produces indented, pretty-printed JSON
- Config setting properly respected when no flag provided
- Flag overrides config when specified

---

### 3. Quiet Mode

**What to Test:**
- `--quiet` suppresses non-essential output
- Still outputs data/results
- Works in both JSON and text modes

**Test Cases:**
```bash
# Test quiet mode with text output
sdd list-specs --quiet              # Should minimize output
sdd progress <spec> --quiet         # Should skip progress messages

# Test quiet mode with JSON output
sdd list-specs --json --quiet       # Should output just JSON
sdd progress <spec> --json --quiet  # No [ACTION] messages

# Test quiet mode with mutations
sdd add-journal <spec> "entry" --quiet  # Should skip confirmation messages
```

**Success Criteria:**
- No informational messages (like "[ACTION] Processing...")
- Data/results still output correctly
- Errors still shown (not suppressed)
- Works consistently across all commands

---

### 4. Verbose Mode

**What to Test:**
- `--verbose` shows detailed output
- Additional debug/info messages
- Works in both JSON and text modes

**Test Cases:**
```bash
# Test verbose mode with text output
sdd list-specs --verbose            # Should show extra details
sdd validate <spec> --verbose       # Should show validation steps

# Test verbose mode with JSON (edge case)
sdd list-specs --json --verbose     # What should happen?
```

**Success Criteria:**
- Shows additional informational messages
- Helpful for debugging and understanding operations
- Doesn't break JSON output (if used together)
- Consistently implemented across commands

---

### 5. No-Color Mode

**What to Test:**
- `--no-color` disables ANSI color codes
- Output still readable without colors
- Works in text mode

**Test Cases:**
```bash
# Test no-color flag
sdd list-specs --no-color           # No ANSI codes
sdd progress <spec> --no-color      # Plain text output

# Test with JSON (should have no effect)
sdd list-specs --json --no-color    # JSON unaffected
```

**Success Criteria:**
- No ANSI escape codes in output
- Text still formatted and readable
- JSON output unaffected (already has no colors)
- Works consistently across all commands

---

### 6. Command-Specific Formats

**What to Test:**
- Commands with `--format` flags (like `report`)
- Format options work independently of global `--json`
- Outputs correct format

**Test Cases:**
```bash
# report command has --format flag
sdd report <spec> --format json       # JSON format
sdd report <spec> --format markdown   # Markdown format

# Check interaction with global --json flag
sdd report <spec> --json              # Uses global JSON mode
sdd report <spec> --format markdown --json  # Which takes precedence?
```

**Success Criteria:**
- Command-specific format flags work correctly
- Clear precedence when both format flag and global flag used
- Documented behavior for edge cases

---

### 7. Config vs Flag Precedence

**What to Test:**
- Command-line flags override config settings
- Config provides defaults when no flags specified
- Precedence is clear and documented

**Test Scenarios:**

| Config Setting | Command Flag | Expected Output |
|----------------|--------------|-----------------|
| `default_mode: text` | (none) | Text output |
| `default_mode: text` | `--json` | JSON output |
| `default_mode: json` | (none) | JSON output |
| `default_mode: json` | `--no-json` | Text output |
| `json_compact: true` | (none) | Compact JSON |
| `json_compact: true` | `--no-compact` | Pretty JSON |
| `json_compact: false` | (none) | Pretty JSON |
| `json_compact: false` | `--compact` | Compact JSON |

**Test Cases:**
```bash
# Test each scenario in table above
# Example:
echo '{"output": {"default_mode": "text", "json_compact": true}}' > .sdd_config_test.json
sdd list-specs                     # Should use text
sdd list-specs --json              # Should use JSON (override)
sdd list-specs --json --no-compact # Should use pretty JSON (override both)
```

**Success Criteria:**
- Flags always override config
- Config provides sensible defaults
- Behavior is predictable and documented
- No conflicts or unexpected interactions

---

### 8. Output Mode Combinations

**What to Test:**
- Multiple flags used together
- Edge cases and unusual combinations
- Consistent behavior

**Test Cases:**
```bash
# Valid combinations
sdd list-specs --json --compact --quiet
sdd progress <spec> --json --no-compact --verbose
sdd validate <spec> --no-json --no-color

# Conflicting combinations (what happens?)
sdd list-specs --json --no-json           # Last flag wins?
sdd list-specs --compact --no-compact     # Last flag wins?

# Nonsensical combinations
sdd list-specs --compact                  # Without --json, ignored?
sdd list-specs --no-color --json          # No-color irrelevant for JSON
```

**Success Criteria:**
- Sensible behavior for all combinations
- Conflicts resolved predictably (e.g., last flag wins)
- Warning messages for nonsensical combinations?
- Documented expected behavior

---

## Testing Strategy

### Phase 1: Individual Mode Testing
1. Create test suite for each output mode
2. Test with representative commands from each category
3. Verify behavior matches expectations
4. Document any issues or unexpected behavior

### Phase 2: Config Testing
1. Test different config file combinations
2. Verify config defaults work correctly
3. Test config in different locations (.claude/, project root, etc.)

### Phase 3: Flag Precedence Testing
1. Test all config vs flag combinations
2. Verify override behavior
3. Document precedence rules

### Phase 4: Edge Case Testing
1. Test unusual flag combinations
2. Test conflicting options
3. Test with different command types (read, write, subsystem)

### Phase 5: Integration Testing
1. Test output modes in real workflows
2. Test with piping and redirection
3. Test with different terminal types

---

## Test Automation

### Recommended Test Scripts

**1. `test_output_modes.py`**
- Tests all output modes systematically
- Verifies text, JSON, compact, quiet, verbose, no-color
- Generates report of findings

**2. `test_config_precedence.py`**
- Tests config vs flag precedence
- Verifies all override scenarios
- Documents unexpected behavior

**3. `test_output_combinations.py`**
- Tests multiple flags together
- Identifies conflicts and edge cases
- Ensures consistent behavior

### Test Coverage Goals
- 100% of output modes tested
- All representative commands tested in each mode
- All config/flag combinations tested
- Edge cases documented

---

## Success Criteria

### Must Have
- ✅ Text mode works correctly (rich UI displays properly)
- ✅ JSON compact vs pretty works as expected
- ✅ Quiet mode properly suppresses non-essential output
- ✅ Config settings respected when no flags provided
- ✅ Flags override config settings correctly

### Should Have
- ✅ Verbose mode provides useful additional information
- ✅ No-color mode produces clean, plain text
- ✅ Command-specific format flags work correctly
- ✅ All flag combinations behave predictably

### Nice to Have
- ✅ Helpful warnings for unusual flag combinations
- ✅ Documentation of all output modes and precedence
- ✅ Examples for common use cases
- ✅ Integration with CI/CD for ongoing validation

---

## Known Issues / Questions

### Questions to Answer
1. What happens when `--compact` is used without `--json`? (Ignored?)
2. What happens when conflicting flags are provided? (Last wins? Error?)
3. Should `--verbose` affect JSON output? (Add verbose field? Ignore?)
4. How does `--quiet` interact with `--verbose`? (Conflict? Last wins?)
5. Are there other output modes we haven't considered?

### Potential Issues
1. Some commands might not respect all modes consistently
2. Config file location precedence might be unclear
3. Some flag combinations might have undefined behavior
4. Documentation might be missing for some modes

---

## Implementation Plan

### Step 1: Document Current Behavior
- Test current behavior of each mode
- Document what works and what doesn't
- Identify inconsistencies

### Step 2: Create Test Suites
- Build comprehensive test scripts
- Cover all modes and combinations
- Generate detailed reports

### Step 3: Fix Issues
- Address any broken modes
- Standardize behavior across commands
- Update documentation

### Step 4: Validate
- Run full test suite
- Verify all modes work correctly
- Update tests to match final behavior

### Step 5: Document
- Write user-facing documentation
- Add examples for each mode
- Document precedence rules clearly

---

## Related Files

- **Current Test:** `/tmp/test_all_sdd_commands.py` (JSON mode only)
- **Config Template:** `src/claude_skills/claude_skills/common/templates/sdd_config.json`
- **CLI Options:** `src/claude_skills/claude_skills/cli/sdd/options.py`
- **Test Results:** `/tmp/COMPREHENSIVE_TEST_SUMMARY.md`

---

## Priority

**Priority:** Medium-High
- JSON mode is critical and now working ✅
- Text mode is default and should be verified
- Other modes (quiet, verbose, etc.) enhance usability
- Comprehensive testing ensures consistent user experience

**Estimated Effort:** 4-8 hours
- Test suite creation: 2-3 hours
- Testing and validation: 2-3 hours
- Documentation: 1-2 hours

---

## Notes

- This builds on the comprehensive JSON mode testing already completed
- Focus on ensuring consistency across all output modes
- Some modes may already work correctly but haven't been systematically tested
- Goal is 100% confidence in all output modes, not just JSON

**Last Updated:** 2025-11-08
