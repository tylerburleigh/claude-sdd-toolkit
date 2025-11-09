# CLI Output Audit: code-doc

**Command:** `sdd doc generate` (and related subcommands)
**Module:** code-doc
**CLI File:** `/src/claude_skills/claude_skills/code_doc/cli.py`
**SKILL.md:** `/skills/code-doc/SKILL.md`
**Date:** 2025-11-09
**Auditor:** Manual audit following SKILL_REVIEW_INSTRUCTIONS.md

---

## Executive Summary

The code-doc CLI module implements four main subcommands for documentation generation. The analysis found:

- **Overall Assessment:** ⚠️ **Minor issues** - Good output structure with one problematic command
- **Primary Concern:** `cmd_analyze_with_ai()` is excessively verbose with 40+ lines of output
- **Other Commands:** Well-designed, minimal output appropriate for their purpose
- **Key Issue:** Structural announcements and implementation details leak into user-facing output

---

## Audit Process

### Step 1-2: Identified Module and Documentation

- **Module:** code-doc (from registry: `from claude_skills.code_doc.cli import register_code_doc`)
- **Commands:** generate, validate-json, analyze, analyze-with-ai
- **SKILL.md Location:** `/skills/code-doc/SKILL.md`
- **Command Handler:** `register_code_doc()` at line 437

### Step 3: Traced Implementation

All printer calls found in `/src/claude_skills/claude_skills/code_doc/cli.py`:

#### Command: `cmd_generate`

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 102 | error | Directory error | ✅ Error handling |
| 114 | error | Directory error | ✅ Error handling |
| 132 | warning | Unknown language | ✅ Error handling |
| 133 | detail | "Continuing with all languages..." | ❌ Implementation detail |
| 157 | success | "Documentation generated at {output_dir}" | ✅ Outcome |

#### Command: `cmd_validate`

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 169 | error | File not found | ✅ Error handling |
| 177 | error | Schema not found | ✅ Error handling |
| 192 | success | "JSON documentation is valid" | ✅ Outcome |
| 201 | error | Missing required keys | ✅ Error handling |
| 206 | success | "Basic validation passed..." | ✅ Outcome |

#### Command: `cmd_analyze`

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 221 | error | Directory error | ✅ Error handling |
| 242-265 | detail | Statistics output (24 lines) | ✅ Outcomes |

#### Command: `cmd_analyze_with_ai`

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 279 | error | Directory error | ✅ Error handling |
| 283 | error | "--json not supported" | ✅ Error handling |
| 291 | detail | "📊 Analyzing {project_name} structure..." | ❌ Implementation detail |
| 303 | detail | "🔍 Detecting framework..." | ❌ Implementation detail |
| 311-313 | detail | Framework/key files/layers info | ⚠️ Mixed (useful but verbose) |
| 323 | detail | "🤖 Checking AI tool availability..." | ❌ Implementation detail |
| 326-330 | warning + detail | AI tool installation instructions | ✅ Outcome (no tools available) |
| 337 | success | "Structural documentation saved" | ✅ Outcome |
| 340 | detail | "Available tools: ..." | ⚠️ Could be consolidated |
| 345-349 | detail | "🧠 Generating AI documentation..." + mode | ❌ Implementation detail |
| 355 | detail | "📐 Gathering architecture research..." | ❌ Implementation detail |
| 367 | warning | "Failed to get architecture research" | ✅ Error reporting |
| 372 | detail | "📝 Gathering AI context research..." | ❌ Implementation detail |
| 384 | warning | "Failed to get AI context research" | ✅ Error reporting |
| 387 | detail | "🔍 Dry run complete..." | ✅ Outcome |
| 391 | detail | "💾 Saving structural documentation..." | ❌ Implementation detail |
| 398-399 | success | "✅ {md_path}", "✅ {json_path}" | ✅ Outcome |
| 404 | detail | "📤 Returning AI research..." | ❌ Implementation detail |
| 417-421 | raw print | JSON markers (RESEARCH_JSON_START/END) | ⚠️ Necessary but noisy |
| 423 | success | "✅ Research gathering complete!" | ✅ Outcome |
| 424-429 | detail | "Next steps for main agent" (6 lines) | ❌ Implementation detail |

---

## Step 4: Simulate Actual Output

### Scenario 1: `sdd doc generate ./src --name MyProject --version 1.0.0 --verbose`

**Expected Output (Typical Run):**
```
Documentation generated at /path/to/docs
```

**Actual Output:** ~3 lines (including possible errors)

### Scenario 2: `sdd doc analyze ./src --verbose`

**Expected Output:**
```
📊 Project Statistics:
   Total Files:      45
   Total Lines:      12345
   Total Classes:    23
   Total Functions:  156
   Avg Complexity:   4.2
   Max Complexity:   28

🌐 Language Breakdown:
   PYTHON:
      Files: 40, Lines: 12000, Functions: 150
   JAVASCRIPT:
      Files: 5, Lines: 345, Functions: 6

⚠️  High Complexity Functions:
   - complex_validator (file.py:45) - complexity: 28
   - parse_large_file (file.py:123) - complexity: 22
```

**Actual Output:** ~15 lines (detailed statistics - appropriate)

### Scenario 3: `sdd doc validate-json ./docs/documentation.json`

**Expected Output:**
```
JSON documentation is valid
```

**Actual Output:** ~1 line

### Scenario 4: `sdd doc analyze-with-ai ./src --name MyProject --verbose`

**Expected Output (Dry Run without AI):**
```
📊 Analyzing MyProject structure...

🔍 Detecting framework and architectural patterns...
   Framework: Django
   Key files identified: 5
   Architectural layers: 3

🤖 Checking AI tool availability...
No AI tools available. Generating structural documentation only.
Install cursor-agent, gemini, or codex for AI-generated docs:
   - cursor-agent: Check cursor.com
   - gemini: npm install -g @google/generative-ai-cli
   - codex: npm install -g @anthropic/codex

Structural documentation saved to /path/to/docs
```

**Actual Output (With AI Tools):**
```
📊 Analyzing MyProject structure...

🔍 Detecting framework and architectural patterns...
   Framework: Django
   Key files identified: 5
   Architectural layers: 3

🤖 Checking AI tool availability...
   Available tools: cursor-agent, gemini

🧠 Generating AI documentation...
   Mode: Multi-agent (parallel consultation)

📐 Gathering architecture research...

📝 Gathering AI context research...

💾 Saving structural documentation to /path/to/docs...
   ✅ /path/to/docs/DOCUMENTATION.md
   ✅ /path/to/docs/documentation.json

📤 Returning AI research for main agent synthesis...

================================================================================
RESEARCH_JSON_START
{
  "status": "success",
  ...
}
RESEARCH_JSON_END
================================================================================

✅ Research gathering complete!

📋 Next steps for main agent:
   1. Parse JSON output from stdout
   2. Synthesize architecture_research from all AI tools
   3. Synthesize ai_context_research from all AI tools
   4. Write ARCHITECTURE.md to output_dir
   5. Write AI_CONTEXT.md to output_dir
```

**Line Count: ~40 lines of verbose output**

---

## Step 5: YAGNI/KISS Analysis

### `cmd_generate()` - APPROPRIATE

Output follows principles well:
- ✅ One success message per command
- ✅ Only errors shown (no implementation details)
- ✅ Minor issue: line 133 "Continuing with all languages..." is defensive but harmless

**Verdict:** ✅ **Appropriate**

---

### `cmd_validate()` - APPROPRIATE

Output is minimal and correct:
- ✅ Only shows validation result
- ✅ Handles both success and error cases
- ✅ Distinguishes between full and basic validation

**Verdict:** ✅ **Appropriate**

---

### `cmd_analyze()` - APPROPRIATE

Output shows relevant statistics:
- ✅ Statistics are outcomes, not implementation details
- ✅ Project stats are useful for decision-making
- ✅ Complexity metrics inform code quality decisions
- ✅ Language breakdown helps understand polyglot projects

**Verdict:** ✅ **Appropriate**

---

### `cmd_analyze_with_ai()` - TOO VERBOSE

**Major Issues:**

1. **Implementation Details Leaking (Lines 291, 303, 323, 345, 355, 372, 391, 404, 424-429)**
   - "Analyzing structure..." (line 291) - user doesn't need to know about analysis phase
   - "Detecting framework..." (line 303) - framework detection is internal
   - "Checking AI tool availability..." (line 323) - this is infrastructure, not a user outcome
   - "Generating AI documentation..." (line 345) - implementation detail
   - "Gathering architecture research..." (line 355) - internal phase
   - "Gathering AI context research..." (line 372) - internal phase
   - "Saving structural documentation..." (line 391) - file I/O is internal
   - "Returning AI research..." (line 404) - implementation detail
   - "Next steps for main agent..." (lines 424-429) - debugging info, not user-facing

2. **Structural Announcements (Lines 345-349, 355-356, 372-373, 391)**
   - Multiple section headers announce each phase
   - These read like a verbose debugging log, not a user-facing workflow
   - Example: "Gathering architecture research..." followed by "Gathering AI context research..." is repetitive

3. **JSON Markers Noise (Lines 417-421)**
   - `RESEARCH_JSON_START/END` markers break the user experience
   - These are implementation details for machine parsing
   - Should be silent or wrapped in a flag

4. **Excessive Emoji Usage**
   - While friendly, emojis on every section adds visual clutter
   - Combined with verbose text, creates wall-of-text effect

**Classification Summary for `cmd_analyze_with_ai()`:**
- ✅ Keep (5 messages): Error handling, outcome on lines 367, 384, 387, 398-399, 423
- ❌ Remove (15+ messages): All phase announcements and infrastructure details
- 🔄 Consolidate (3 messages): Framework/files/layers info (lines 311-313) into one message

**Current line count:** ~40 lines
**Proposed line count:** ~12 lines
**Reduction:** 70%

---

## Step 6: Proposed Minimal Output

### Current (Verbose) Output

```
📊 Analyzing MyProject structure...

🔍 Detecting framework and architectural patterns...
   Framework: Django
   Key files identified: 5
   Architectural layers: 3

🤖 Checking AI tool availability...
   Available tools: cursor-agent, gemini

🧠 Generating AI documentation...
   Mode: Multi-agent (parallel consultation)

📐 Gathering architecture research...

📝 Gathering AI context research...

💾 Saving structural documentation to /path/to/docs...
   ✅ /path/to/docs/DOCUMENTATION.md
   ✅ /path/to/docs/documentation.json

📤 Returning AI research for main agent synthesis...

================================================================================
RESEARCH_JSON_START
{
  "status": "success",
  ...
}
RESEARCH_JSON_END
================================================================================

✅ Research gathering complete!

📋 Next steps for main agent:
   1. Parse JSON output from stdout
   2. Synthesize architecture_research from all AI tools
   3. Synthesize ai_context_research from all AI tools
   4. Write ARCHITECTURE.md to output_dir
   5. Write AI_CONTEXT.md to output_dir
```

### Proposed (Minimal) Output

```
Generating documentation for MyProject...
  Detected: Django framework, 5 key files, 3 architectural layers
  Available AI tools: cursor-agent, gemini (multi-agent mode)

✓ Documentation generation complete
  ✅ /path/to/docs/DOCUMENTATION.md
  ✅ /path/to/docs/documentation.json
```

**Comparison:**
- Current: ~40 lines
- Proposed: ~6 lines
- **Reduction: 85%**

---

## Step 7: Root Cause Analysis

**Why is `cmd_analyze_with_ai()` so verbose?**

### Root Cause 1: Phase-by-Phase Logging

The function breaks work into logical phases and announces each one:
1. Load and analyze codebase
2. Detect framework/layers
3. Check AI tool availability
4. Generate documentation
5. Save files
6. Return results

Each phase prints multiple status lines (lines 291, 303, 323, 345, 355, 372, 391, 404). This is defensive logging for a complex async operation, but it violates YAGNI - users don't need to see the orchestration.

### Root Cause 2: Implementation Detail Confusion

The code conflates two audiences:
- **User**: Wants to know: "Did my docs get generated? Where are they?"
- **Main Agent**: Needs JSON research data for synthesis

The current output tries to explain the entire workflow to the user, when really it should:
1. Run silently or show one progress indicator
2. Return JSON data to stdout (already doing this)
3. Show success message

### Root Cause 3: Mixed Responsibilities

`cmd_analyze_with_ai()` handles both CLI and skill responsibilities:
- CLI: Should show minimal user-facing output
- Skill: Returns JSON for main agent (this is correct)

But it announces every internal step, treating this like a verbose log instead of a clean interface.

### Root Cause 4: JSON Markers Break UX

Lines 417-421 print raw markers for JSON parsing. This is a machine-level concern that shouldn't be visible to users. Better approaches:
- Use exit codes + structured output to separate concerns
- Print JSON only, let parsing tools handle it
- Use a hidden flag for debug output

---

## Step 8: Detailed Findings

### Issue Categories

#### Category 1: Unnecessary Phase Announcements (HIGH PRIORITY)

**Affected Lines:** 291, 303, 323, 345, 355, 372, 391, 404

**Examples:**
```python
# Line 291 - unnecessary
printer.detail(f"📊 Analyzing {project_name} structure...")

# Line 345 - unnecessary
printer.detail("\n🧠 Generating AI documentation...")

# Line 391 - unnecessary
printer.detail(f"\n💾 Saving structural documentation to {output_dir}...")
```

**Why it's a problem:** These are internal phases of the operation. Users asked for documentation, not a play-by-play breakdown of the implementation.

**Recommendation:** Remove completely. The success message at line 423 is sufficient.

---

#### Category 2: Infrastructure Details (HIGH PRIORITY)

**Affected Lines:** 323, 340, 345-349

**Examples:**
```python
# Line 323 - unnecessary
printer.detail("\n🤖 Checking AI tool availability...")

# Lines 340, 345-349 - unnecessary
printer.detail(f"   Available tools: {', '.join(available_tools)}")
printer.detail("\n🧠 Generating AI documentation...")
if use_multi_agent and len(available_tools) >= 2:
    printer.detail("   Mode: Multi-agent (parallel consultation)")
```

**Why it's a problem:** "Checking tool availability" and "mode selection" are infrastructure concerns. Users care about: "Did it work? Where are my docs?"

**Recommendation:** Make this an optional flag. Default behavior: silent. With `--verbose`: show these details.

---

#### Category 3: File I/O Announcements (MEDIUM PRIORITY)

**Affected Lines:** 391, 398-399

**Examples:**
```python
# Line 391 - unnecessary context
printer.detail(f"\n💾 Saving structural documentation to {output_dir}...")
# Lines 398-399 - better here, but together with 391 is redundant
printer.success(f"   ✅ {md_path}")
printer.success(f"   ✅ {json_path}")
```

**Why it's a problem:** Users know files are being saved (they requested documentation). The "Saving..." announcement is defensive logging.

**Recommendation:** Keep the file paths (lines 398-399) in the success message, remove the "Saving..." announcement.

---

#### Category 4: JSON Markers Pollution (HIGH PRIORITY)

**Affected Lines:** 417-421

**Examples:**
```python
print("\n" + "=" * 80)
print("RESEARCH_JSON_START")
print(json_module.dumps(research_output, indent=2))
print("RESEARCH_JSON_END")
print("=" * 80)
```

**Why it's a problem:** These markers are for machine parsing. Having them visible in user output pollutes the CLI experience and breaks the illusion that this is a clean, professional tool.

**Recommendation:**
- Redirect JSON to stderr or a temp file
- Use exit codes to signal success/failure
- Let the calling code handle JSON extraction, not the CLI

---

#### Category 5: Main Agent Instructions (HIGH PRIORITY)

**Affected Lines:** 404, 424-429

**Examples:**
```python
# Line 404 - unnecessary
printer.detail("\n📤 Returning AI research for main agent synthesis...")

# Lines 424-429 - definitely not for end users
printer.detail("\n📋 Next steps for main agent:")
printer.detail("   1. Parse JSON output from stdout")
printer.detail("   2. Synthesize architecture_research from all AI tools")
# ... etc
```

**Why it's a problem:** This is an instruction for the skill's caller (main agent), not for the user. It has no business being in user-facing output.

**Recommendation:** Remove completely. This is internal documentation that belongs in code comments or the SKILL.md file, not in CLI output.

---

### Minor Issues

#### Issue 1: Line 133 - Defensive Message

```python
printer.detail("Continuing with all languages...")
```

**Impact:** Minimal - this only shows when user specifies invalid language
**Recommendation:** Remove - it's reassurance that's not needed. The user will see results anyway.

---

## Step 9: Verdict

### `cmd_generate()`: ✅ **Appropriate**
- Minimal output
- Shows outcome only
- No implementation details

### `cmd_validate()`: ✅ **Appropriate**
- Minimal output
- Clear success/failure
- No verbosity

### `cmd_analyze()`: ✅ **Appropriate**
- Statistics are relevant outcomes
- Help users understand code quality
- Not implementation details

### `cmd_analyze_with_ai()`: ❌ **Too Verbose**
- 40 lines of verbose output
- ~70% of output is implementation details
- Violations:
  - Phase announcements (291, 303, 323, 345, 355, 372, 391, 404)
  - Infrastructure details (340, 345-349)
  - Main agent instructions (424-429)
  - JSON markers pollution (417-421)
- Proposed reduction: 70-85%
- Root cause: Defensive logging treating users like developers debugging the code

**Overall Module Assessment:** ⚠️ **Minor Issues**
- 3 of 4 commands are appropriate
- 1 command has significant verbosity problems
- Issue is localized to `cmd_analyze_with_ai()`, not systemic

---

## Recommended Fixes (Priority Order)

### Priority 1: Remove Phase Announcements

**Remove lines:** 291, 303, 345, 355, 372, 391, 404, 424-429

**Change:** Replace with single progress indicator at start

```python
# Add at beginning of cmd_analyze_with_ai()
printer.detail(f"Generating documentation for {project_name}...")

# Remove all subsequent phase announcements

# At end, show only:
printer.success("✓ Documentation generation complete")
```

---

### Priority 2: Remove JSON Markers

**Remove lines:** 417-421

**Change:** Print JSON to stdout only (no markers)

```python
# Instead of markers:
print(json_module.dumps(research_output, indent=2))
```

**Rationale:** Calling code can detect JSON by parsing first line, or use a specific flag to separate concerns.

---

### Priority 3: Consolidate Infrastructure Output

**Lines affected:** 340, 345-349

**Change:** Either remove entirely or move to separate `--verbose` handling

```python
if getattr(args, 'verbose', False):
    printer.detail(f"Available AI tools: {', '.join(available_tools)}")
    if use_multi_agent:
        printer.detail("Using multi-agent consultation mode")
```

---

### Priority 4: Remove Defensive Messages

**Remove lines:** 133, 404

**Change:** Trust that tool works; only show results

---

## SKILL.md Alignment

Current SKILL.md (lines 291-305 section on `analyze-with-ai`) shows this example output:

```
"Generating documentation for MyProject...
  Detected: Django framework, 5 key files, 3 architectural layers
  Available AI tools: cursor-agent, gemini (multi-agent mode)

✓ Documentation generation complete"
```

**Finding:** SKILL.md describes minimal output, but CLI code produces 40+ lines. There's a **documentation-implementation mismatch**.

**Recommendation:** Update SKILL.md examples to reflect actual current output, OR update CLI code to match the minimal examples shown in SKILL.md (preferred).

---

## Implementation Notes for Fixes

### Code Changes Needed

1. **Simplify `cmd_analyze_with_ai()` output section:**
   - Add progress message at start (line 291)
   - Remove all subsequent detail() calls for phases
   - Keep error handling (warning() calls on lines 367, 384)
   - Keep file success messages (lines 398-399)
   - Replace JSON markers with direct print
   - Remove main agent instructions (lines 424-429)

2. **Update test expectations:**
   - Tests currently expect 40 lines of output
   - Will need to update to expect ~12 lines

3. **Update SKILL.md:**
   - Sync examples to match new output
   - Remove reference to "next steps for main agent" from user-facing docs

### Testing Strategy

Before submitting fix:
1. Run `sdd doc analyze-with-ai ./src --verbose`
2. Verify output is < 15 lines (excluding JSON)
3. Verify JSON is correctly returned
4. Verify all success messages are clear
5. Verify error cases still work

---

## Conclusion

The code-doc CLI module is generally well-designed with mostly appropriate output. However, `cmd_analyze_with_ai()` violates YAGNI/KISS principles with 40+ lines of verbose output that includes:

- Phase announcements (infrastructure details)
- Implementation details (AI tool checking, framework detection)
- Machine-level concerns (JSON markers)
- Developer instructions (next steps for main agent)

These can be reduced by 70-85% by removing internal workflow announcements and showing only outcomes. The fixes are straightforward, and the root cause is defensive logging treating users like developers, rather than as end-users who only care about results.

**Severity:** Medium
**Effort to Fix:** Low (straightforward removal of lines)
**Impact:** High (significantly improves user experience)

---

## Files Referenced

- `/src/claude_skills/claude_skills/code_doc/cli.py` - CLI implementation (495 lines)
- `/skills/code-doc/SKILL.md` - User-facing documentation (1078 lines)
- `/src/claude_skills/claude_skills/cli/sdd/registry.py` - Module registration
