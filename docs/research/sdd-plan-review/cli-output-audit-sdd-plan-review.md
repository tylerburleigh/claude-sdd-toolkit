# CLI Output Audit: sdd-plan-review

**Module:** sdd-plan-review (Multi-model specification review)
**CLI File:** `/src/claude_skills/claude_skills/sdd_plan_review/cli.py`
**SKILL.md:** `/skills/sdd-plan-review/SKILL.md`
**Commands Analyzed:** `review`, `list-plan-review-tools`
**Audit Date:** 2025-11-09

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Commands Audited** | 2 (`review`, `list-plan-review-tools`) |
| **Current Output Lines** (typical) | 28-35 lines |
| **Redundant/Implementation Detail Lines** | 12-15 lines (38-45% of output) |
| **Root Cause** | Excessive sub-operation logging, over-explanation, structural verbosity |
| **Assessment** | ⚠️ **Minor Issues** |

---

## Audit Process

### Step 1: Commands Identified

**From registry:** `/src/claude_skills/claude_skills/cli/sdd/registry.py`

Two commands are registered:
1. `review` (primary command) - Reviews specs with multiple AI models
2. `list-plan-review-tools` (secondary/utility) - Lists available AI tools

### Step 2: Command Handlers

**cmd_review** (lines 32-182)
- Main specification review workflow
- Handles tool detection, spec loading, parallel review execution
- Generates markdown/JSON reports

**cmd_list_tools** (lines 185-255)
- Lists available AI CLI tools for review
- Shows installation instructions
- Provides status summary

---

## Detailed Output Analysis

### Command: `sdd review user-auth-001`

#### Current Output (Typical Success Case)

```
Reviewing specification: /path/to/specs/active/user-auth-001.json

Using 2 tool(s): gemini, codex

Starting full review...

   Sending full review to 2 external AI model(s): gemini, codex
   Evaluating: Completeness, Clarity, Feasibility, Architecture, Risk Management, Verification

   ✓ gemini completed (15.2s)
   ✓ codex completed (22.5s)

============================================================

Review Complete
Execution time: 22.7s
Models responded: 2/2

[Long markdown report follows, printed to stdout]

Report saved to: /path/to/specs/.reviews/user-auth-001-review.md
```

#### Output Classification

| Line # | Message Type | Content | Classification | Reason |
|--------|--------------|---------|-----------------|--------|
| 1 | info | "Reviewing specification: {file}" | ❌ Remove | Implementation detail (user specified the spec_id, they know what's being reviewed) |
| 2 | blank | | ✅ Keep | Spacing |
| 3 | info | "Using N tool(s): {tools}" | 🔄 Consolidate | Can be shown with other tool info, not urgent |
| 4 | blank | | ✅ Keep | Spacing |
| 5 | info | "Starting {type} review..." | 🔄 Consolidate | Implied by executing command, combine with tool messages |
| 6 | blank | | ✅ Keep | Spacing |
| 7 | print | "Sending {type} review to {N} external AI model(s)" | ❌ Remove | Implementation detail (internal orchestration) |
| 8 | print | "Evaluating: {dimensions}" | ❌ Remove | Not user-facing (dimensions are implicit in --type selection) |
| 9 | blank | | ✅ Keep | Spacing |
| 10-12 | print | "✓ {tool} completed ({time}s)" x2 | ✅ Keep | Outcome (shows parallel execution progress) |
| 13 | blank | | ✅ Keep | Spacing |
| 14 | separator | "==========" | 🔄 Consolidate | Unnecessary visual noise, merge with header |
| 15 | header | "Review Complete" | 🔄 Consolidate | Good, but can merge with execution summary |
| 16 | info | "Execution time: {time}s" | ⚠️ Consider | Useful context, but not critical for outcome |
| 17 | success | "Models responded: 2/2" | ✅ Keep | Outcome (success rate important for multi-model) |
| 18 | blank | | ✅ Keep | Spacing |
| 19+ | report | Full markdown report | ✅ Keep | Essential outcome (the actual review results) |
| 20+ | success | "Report saved to: {path}" | ✅ Keep | Outcome (user needs to know where report went) |

#### Line Count Analysis

**Current:** ~20 lines of preamble before report
**Proposed:** ~8 lines of preamble
**Reduction:** 60% fewer lines for preamble messaging

---

### Command: `sdd list-plan-review-tools`

#### Current Output (When 2/3 tools available)

```
AI CLI Tools for Reviews

✓ Available (2):
  gemini
  codex

✗ Not Available (1):
  cursor-agent

Installation Instructions:

Cursor Agent:
  Install Cursor IDE from cursor.com
  Cursor agent comes bundled with the IDE

Summary: 2/3 tools available
Multi-model reviews available
```

#### Output Classification

| Line # | Message Type | Content | Classification | Reason |
|--------|--------------|---------|-----------------|--------|
| 1 | header | "AI CLI Tools for Reviews" | ✅ Keep | Context header |
| 2 | blank | | ✅ Keep | Spacing |
| 3 | success | "✓ Available (N):" | ✅ Keep | Status header |
| 4-5 | detail | Indented tool names | ✅ Keep | Outcome (user needs this list) |
| 6 | blank | | ✅ Keep | Spacing |
| 7 | warning | "✗ Not Available (N):" | ✅ Keep | Status header |
| 8 | detail | Indented tool names | ✅ Keep | Outcome |
| 9 | blank | | ✅ Keep | Spacing |
| 10 | info | "Installation Instructions:" | 🔄 Consolidate | Can be implied/header reduced |
| 11 | blank | | ✅ Keep | Spacing |
| 12-14 | detail | Installation steps for unavailable tool | ✅ Keep | User-actionable (needed if tools missing) |
| 15 | blank | | ✅ Keep | Spacing |
| 16 | info | "Summary: 2/3 tools available" | 🔄 Consolidate | Redundant with counts above |
| 17 | success | "Multi-model reviews available" | 🔄 Consolidate | Can merge with summary |

#### Line Count Analysis

**Current:** ~17 lines
**Assessment:** Generally appropriate for the utility function (comprehensive tool status)
**Minor improvement:** Lines 10, 16, 17 could be consolidated

---

## Root Cause Analysis

### 1. Sub-operation Verbosity

**Issue:** Both `cmd_review` and the underlying `reviewer.py` module print their own progress messages.

**Evidence:**

- **cli.py lines 48, 72, 107**: Main command printing status
- **reviewer.py lines 92-94, 114, 117**: Module-level printing of tool progress
- **cli.py lines 119-126**: Summary printing after execution

When `cmd_review` calls `review_with_tools()`, the module prints directly using raw `print()` statements (lines 92-94, 114, 117 in reviewer.py), while `cmd_review` also prints using `printer.info/success/warning`.

**Result:** Users see both the internal module output AND the command wrapper output, creating redundancy.

```python
# In reviewer.py:92-94 (internal module)
print(f"\n   Sending {review_type} review to {len(tools)} external AI model(s): {', '.join(tools)}")
print(f"   Evaluating: {dimensions}")

# In cli.py:72 (command wrapper, redundant)
printer.info(f"Using {len(tools_to_use)} tool(s): {', '.join(tools_to_use)}")
```

### 2. Implementation Details in User Output

**Issue:** Messages reveal internal orchestration that doesn't affect the outcome.

**Examples:**

- "Sending full review to 2 external AI model(s)" → Implementation detail (user just needs to know review is running)
- "Evaluating: Completeness, Clarity, Feasibility..." → Implicit in `--type full` flag
- "Reviewing specification: {spec_file}" → User already specified this as argument

**These are internal operation details, not outcomes.**

### 3. Over-explanation of Tool Status

**Issue:** In `cmd_list_tools`, redundant status reporting.

```python
# Line 245
printer.info(f"\nSummary: {len(available)}/{len(tools_to_check)} tools available")

# Lines 248-255 - separate messages for the same information
if len(available) == 0:
    printer.warning("No tools available - cannot run reviews")
elif len(available) == 1:
    printer.info("Single-model reviews available (limited confidence)")
else:
    printer.success("Multi-model reviews available")
```

The summary line and the multi-line assessment are saying nearly the same thing.

### 4. Dry-Run Over-verbosity

**Issue:** Dry-run mode (lines 75-84) prints 8 lines of detail about what would happen.

```python
if args.dry_run:
    printer.info("\n[DRY RUN MODE]")
    printer.detail(f"Would review: {spec_file}")
    printer.detail(f"Review type: {args.type}")
    printer.detail(f"Tools: {', '.join(tools_to_use)}")
    printer.detail(f"Parallel: Yes")
    if args.output:
        printer.detail(f"Output: {args.output}")
    printer.detail(f"Cache: {'Yes' if args.cache else 'No'}")
    return 0
```

"Parallel: Yes" is not user-facing (it's always true). Cache status is implementation detail.

---

## Proposed Minimal Output

### Command: `sdd review user-auth-001 --type full`

**Minimal version (5-8 lines):**

```
Reviewing user-auth-001 with gemini, codex...

   ✓ gemini completed (15.2s)
   ✓ codex completed (22.5s)

============================================================

[Long markdown report follows]

Report saved to: .reviews/user-auth-001-review.md
```

**Changes:**
1. Merge file-path message into single opening line with tool list
2. Remove "Sending review to N external AI models" (internal detail)
3. Remove "Evaluating: {dimensions}" (implicit in --type)
4. Keep tool completion messages (progress indicator)
5. Keep separator for visual clarity before report
6. Keep final report save confirmation (outcome)

### Command: `sdd list-plan-review-tools` (No Changes Needed)

**Assessment:** This command is appropriately verbose for a utility function that provides installation instructions. The output directly addresses user needs (finding available tools and fixing missing ones). Minimal reduction possible without losing clarity.

Minor improvement: Lines 245-255 could consolidate from 5 lines to 2-3 lines:
```
Summary: 2/3 tools available (multi-model reviews available)
```

---

## YAGNI/KISS Violations

### Clear Violations

1. **"Reviewing specification: {file}"** (line 48)
   - **Type:** Over-explanation
   - **Impact:** User already provided spec_id; showing full path is noise
   - **Fix:** Remove or make trace-level only

2. **"Sending review to N external AI models"** (reviewer.py:92)
   - **Type:** Implementation detail
   - **Impact:** User doesn't care about internal orchestration, only that review is running
   - **Fix:** Remove entirely

3. **"Evaluating: {dimensions}"** (reviewer.py:93)
   - **Type:** Implementation detail redundancy
   - **Impact:** Dimension selection is implicit in `--type` flag; re-explaining it is noise
   - **Fix:** Remove

4. **"Parallel: Yes"** (line 80, dry-run)
   - **Type:** Implementation detail
   - **Impact:** Parallelism is not a user-facing concern
   - **Fix:** Remove from output

5. **"Cache: Yes/No"** (line 83, dry-run)
   - **Type:** Implementation detail
   - **Impact:** Cache usage is internal concern, not preview of what will happen
   - **Fix:** Remove

6. **Summary + separate status messages** (lines 245-255, list-tools)
   - **Type:** Redundancy
   - **Impact:** Lines 248-255 repeat the same information as line 245
   - **Fix:** Consolidate into single line

### Acceptable Elements

- ✅ Tool completion messages ("✓ {tool} completed {time}s") - Progress indicator, outcome
- ✅ "Models responded: 2/2" - Outcome (success rate for multi-model)
- ✅ "Report saved to: {path}" - Outcome (user needs to know file location)
- ✅ Execution time - Context (nice-to-have for long operations, not critical)

---

## Final Verdict

### Assessment: ⚠️ **Minor Issues**

**Reasoning:**

1. **Not Too Verbose (>50% reduction):** Most of the output (20-25 lines out of 28-35) is either:
   - Tool progress indicators (necessary)
   - The actual report content (essential outcome)
   - File paths and summaries (necessary information)

2. **Specific Fixable Issues:** 6-8 lines contain clear YAGNI/KISS violations:
   - File path announcement (redundant with argument)
   - "Sending review to N external models" (internal)
   - "Evaluating: {dimensions}" (implicit in flag)
   - Dry-run redundancies (Parallel, Cache flags)
   - Redundant status messages in list-tools

3. **Impact:** Removing these issues would reduce preamble from ~20 lines to ~12 lines (40% reduction in preamble, 15-20% overall), making output more concise without losing user-critical information.

**Category:** This falls between "Appropriate" (no issues) and "Too Verbose" (>50% reduction needed). Minor cleanup would bring it to "Appropriate" status.

---

## Recommendations

### Priority 1: Remove Implementation Details (Easy Fixes)

**In cli.py:**

1. **Line 48:** Remove or move to trace-level logging
   ```python
   # BEFORE
   printer.info(f"Reviewing specification: {spec_file}")

   # AFTER
   # Remove this line entirely (user knows what they asked for)
   ```

2. **Lines 75-84:** Reduce dry-run output
   ```python
   # BEFORE
   if args.dry_run:
       printer.info("\n[DRY RUN MODE]")
       printer.detail(f"Would review: {spec_file}")
       printer.detail(f"Review type: {args.type}")
       printer.detail(f"Tools: {', '.join(tools_to_use)}")
       printer.detail(f"Parallel: Yes")
       if args.output:
           printer.detail(f"Output: {args.output}")
       printer.detail(f"Cache: {'Yes' if args.cache else 'No'}")
       return 0

   # AFTER
   if args.dry_run:
       printer.info("[DRY RUN MODE]")
       printer.detail(f"Would review: {spec_file}")
       printer.detail(f"Review type: {args.type}")
       printer.detail(f"Tools: {', '.join(tools_to_use)}")
       if args.output:
           printer.detail(f"Output: {args.output}")
       return 0
   ```

3. **Lines 245-255:** Consolidate tool list output
   ```python
   # BEFORE
   printer.info(f"\nSummary: {len(available)}/{len(tools_to_check)} tools available")

   if len(available) == 0:
       printer.warning("No tools available - cannot run reviews")
       return 1
   elif len(available) == 1:
       printer.info("Single-model reviews available (limited confidence)")
       return 0
   else:
       printer.success("Multi-model reviews available")
       return 0

   # AFTER
   if len(available) == 0:
       printer.warning(f"\nNo tools available ({len(available)}/{len(tools_to_check)})")
       return 1
   else:
       printer.success(f"\nTools available: {len(available)}/{len(tools_to_check)}")
       return 0
   ```

### Priority 2: Remove Module-level Output (Requires Coordination)

**In reviewer.py:**

1. **Lines 92-94:** Remove internal tool orchestration messages
   ```python
   # BEFORE
   print(f"\n   Sending {review_type} review to {len(tools)} external AI model(s): {', '.join(tools)}")
   print(f"   Evaluating: {dimensions}")

   # AFTER
   # Remove these lines - they're internal details
   ```

**Note:** These print statements use raw `print()` instead of the printer abstraction. They should either:
- Be removed entirely (preferred for YAGNI)
- Wrapped in a logger with DEBUG level
- Moved to the CLI layer for centralized control

### Priority 3: Update SKILL.md Examples

Once output is cleaned up, update SKILL.md examples (lines 417-428) to show the minimal output:

```markdown
### Phase 2: Execute Review

**Progress indicators:**
```
sdd review user-auth-001 --type full

Reviewing user-auth-001 with gemini, codex...

   ✓ gemini completed (15.2s)
   ✓ codex completed (22.5s)

[Long markdown report follows]

Report saved to: .reviews/user-auth-001-review.md
```
```

---

## Impact Assessment

| Change | Lines Reduced | User Impact | Effort | Priority |
|--------|---------------|------------|--------|----------|
| Remove spec path message | 1 | Less noise, user knows what they asked | 5 min | Medium |
| Remove "Sending review to N models" | 1 | Clearer output, less internal detail | 5 min | High |
| Remove "Evaluating: dimensions" | 1 | Less redundancy with --type flag | 5 min | High |
| Remove dry-run details (Parallel, Cache) | 2 | Cleaner preview, less confusing | 10 min | Medium |
| Consolidate tool list messages | 3-4 | Cleaner, less repetition | 15 min | Low |
| **Total preamble reduction** | **8-10 lines** | **More focused output** | **40 min** | **Medium** |

---

## Conclusion

The sdd-plan-review CLI has **minor output verbosity issues** rather than fundamental problems. The command appropriately:
- ✅ Shows tool progress (parallel execution tracking)
- ✅ Displays the review report (primary outcome)
- ✅ Confirms file save location (outcome)
- ✅ Provides error details (when failures occur)

However, it includes **6-8 lines of implementation details and redundant explanations** that could be removed without losing user-critical information:
- Internal orchestration messages ("Sending review to N external models")
- Over-explanations ("Evaluating: dimensions" when --type flag is explicit)
- Redundant status messages ("Summary: 2/3" + separate "Multi-model reviews available")

**Recommended Action:** Apply Priority 1 and Priority 2 fixes (40 minutes of work) to reduce preamble noise and bring output fully in compliance with YAGNI/KISS principles. This will result in cleaner, more professional output without sacrificing user information.

---

## Appendix: Output Comparison

### Current Total Output (Typical Success)
~28-35 lines including:
- 3-4 lines of file/tool setup messaging
- 2-3 lines of internal orchestration (removable)
- 2-4 lines of tool progress (keep)
- 3-4 lines of summary (partially redundant)
- 12-20 lines of markdown report (keep)
- 1 line save confirmation (keep)

### Proposed Total Output (After Fixes)
~22-25 lines including:
- 1 opening line (merged tool info)
- 2-4 lines of tool progress (keep)
- 1 separator line (keep)
- 12-20 lines of markdown report (keep)
- 1 line save confirmation (keep)

**Net improvement: 20-30% reduction in preamble noise**
