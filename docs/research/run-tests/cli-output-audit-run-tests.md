# CLI Output Audit: run-tests Module

**Module:** sdd-toolkit:run-tests
**Namespace:** `sdd test`
**Commands:** `run` (default), `debug`, `investigate`, `check-tools`, `consult`, `discover`
**CLI File:** `/src/claude_skills/claude_skills/run_tests/cli.py`
**SKILL.md:** `/skills/run-tests/SKILL.md`

**Audit Date:** 2025-11-09
**Auditor Notes:** Comprehensive framework for test execution and AI-powered debugging via external tools

---

## Executive Summary

The run-tests module provides a sophisticated testing and debugging framework with multiple specialized commands. Analysis reveals **significant verbosity issues** in the consultation workflow, particularly in multi-agent mode where structural output adds 20+ lines of non-essential formatting. The core test execution commands (run, discover) are appropriately concise, but consultation operations violate YAGNI/KISS principles.

**Overall Verdict: ❌ Too Verbose** (Consultation/multi-agent modes require substantial reduction)

**Issue Distribution:**
- `cmd_run`: ✅ Appropriate
- `cmd_discover`: ✅ Appropriate
- `cmd_check_tools`: ⚠️ Minor issues
- `cmd_consult`: ❌ Too verbose
- `consult_multi_agent`: ❌ Too verbose

---

## Command Analysis

### 1. `sdd test run` - Run Tests with Presets

**Current Output Simulation:**

```
$ sdd test run --preset-debug tests/test_auth.py

Running: pytest -vv -l -s tests/test_auth.py

[pytest output follows...]
```

**Line Count:** 2 lines of overhead + pytest output

**Classification:**

| Line | Type | Content | Decision |
|------|------|---------|----------|
| 1 | blank | (spacing) | ✅ Keep (readability) |
| 2 | action | `Running: pytest -vv -l -s tests/test_auth.py` | ✅ Keep (user needs to see command) |
| 3+ | pytest | [native pytest output] | ✅ Keep (outcome/verification) |

**Assessment:** ✅ **Appropriate**

The run command shows minimal overhead. The command string is useful for users to understand what flags are being applied. Error messages (path not found, pytest not installed) are necessary.

**Current Implementation:**
- `/src/claude_skills/claude_skills/run_tests/pytest_runner.py:202-203` prints action + blank
- Error handling is concise (lines 196-197, 210-211)

---

### 2. `sdd test discover` - Discover Test Structure

**Current Output Simulation:**

```
$ sdd test discover --summary

Test Discovery in: /Users/user/project

Test files found: 12
Conftest files found: 2

[Optional: --tree, --fixtures, --markers, --detailed output follows]
```

**Line Count:** 5 lines of core discovery info

**Classification:**

| Line | Type | Content | Decision |
|------|------|---------|----------|
| 1 | blank | (spacing) | ✅ Keep |
| 2 | header | `Test Discovery in: ...` | ✅ Keep (context) |
| 3 | blank | (spacing) | ✅ Keep |
| 4 | info | `Test files found: 12` | ✅ Keep (outcome) |
| 5 | info | `Conftest files found: 2` | ✅ Keep (outcome) |

**Assessment:** ✅ **Appropriate**

Discovery output is outcome-focused. Each line provides useful information about the test structure.

**Current Implementation:**
- `/src/claude_skills/claude_skills/run_tests/test_discovery.py:345-349` prints headers and summaries
- Error handling for missing directories is clear (line 333)

---

### 3. `sdd test check-tools` - Check External Tool Availability

**Current Output Simulation:**

```
$ sdd test check-tools

External Tool Availability

Found 2 tool(s):
  ✓ gemini
  ✓ codex
```

**Line Count:** 5 lines total

**Classification:**

| Line | Type | Content | Decision |
|------|------|---------|----------|
| 1 | header | `External Tool Availability` | ✅ Keep (context) |
| 2 | blank | (spacing) | ⚠️ Borderline (could consolidate) |
| 3 | success | `Found 2 tool(s):` | ✅ Keep (outcome) |
| 4-5 | info | `  ✓ gemini`, `  ✓ codex` | ✅ Keep (list items needed) |

**Assessment:** ⚠️ **Minor Issues**

The blank line between header and content is conventional but not essential. Could be consolidated, but current format is acceptable.

**Proposed Minimal Output:**
```
External Tool Availability
Found 2 tool(s):
  ✓ gemini
  ✓ codex
```

**Reduction:** 1 line (1 blank line removed) = 20% reduction, but not critical.

**Current Implementation:**
- `/src/claude_skills/claude_skills/run_tests/cli.py:64-75` prints headers, blanks, list items

---

### 4. `sdd test consult` - Single-Agent Consultation

**Current Output Simulation:**

```
$ sdd test consult assertion --error "expected False, got True" --hypothesis "missing negation"

Auto-triggering multi-agent consensus for 'assertion' failure
Using consensus pair: default

============================================================

[Tool output...]
```

**Line Count:** 5 lines of overhead + tool output

**Classification:**

| Line | Type | Content | Decision |
|------|------|---------|----------|
| 1 | info | `Auto-triggering multi-agent...` | ❌ Remove (internal decision) |
| 2 | info | `Using consensus pair: default` | ❌ Remove (internal operation) |
| 3 | blank | (spacing) | ❌ Remove |
| 4 | separator | `============================================================` | ⚠️ Questionable |
| 5+ | tool output | [actual consultation output] | ✅ Keep (user-requested) |

**Issues Found:**

1. **Auto-trigger announcement (lines 114-115 in cli.py)**
   - Lines printed: 2 + 1 blank = 3 lines
   - Problem: These announce YAGNI violations - users don't care about internal routing decisions
   - Type: Implementation detail
   - Severity: High

2. **Separator line (line 492 in consultation.py)**
   - Line printed: 1 line of 60 dashes
   - Problem: Not needed; tool output is clear on its own
   - Type: Structural formatting
   - Severity: Medium

3. **Dry-run output (lines 485-489 in consultation.py)**
   - Problem: Shows truncated command instead of actual shell invocation
   - Type: Over-explanation
   - Severity: Low

**Assessment:** ❌ **Too Verbose**

The auto-routing messages are internal implementation details that users don't need. If multi-agent is auto-triggered, that's fine, but the announcement is noise.

**Proposed Minimal Output:**
```
$ sdd test consult assertion --error "expected False, got True" --hypothesis "missing negation"

[Tool output directly...]
```

**Reduction:** Remove 3 lines of overhead = 100% of non-tool output removed

---

### 5. `sdd test consult` - Multi-Agent Consultation (The Major Issue)

**Current Output Simulation:**

```
$ sdd test consult assertion --error "expected False" --hypothesis "missing check" --multi-agent

Consulting 2 agents in parallel...
Tools: gemini, cursor-agent
============================================================

✓ gemini completed (2.3s)
✓ cursor-agent completed (1.8s)

┌─ Multi-Agent Analysis ────────────────────────────────────┐

│ CONSULTED AGENTS:
│ ✓ gemini (2.3s)
│ ✓ cursor-agent (1.8s)
│
│ CONSENSUS (Agents agree):
│ • Root cause is validation logic bypass
│ • Fix requires assertion in precondition check
│
│ CODEX INSIGHTS:
│ • Check return value from condition check
│
│ CURSOR-AGENT INSIGHTS:
│ • Similar patterns in user_auth.py line 45
│
│ SYNTHESIS:
│ All agents identify the same root cause: missing validation...
│
│ RECOMMENDATIONS:
│ → Add assertion before state mutation
│ → Review similar validation points in auth module
│
└──────────────────────────────────────────────────────────┘

============================================================
DETAILED RESPONSES:
============================================================

─── GEMINI ──────────────────────────────────────────────
[Full response from gemini tool...]

─── CURSOR-AGENT ────────────────────────────────────────
[Full response from cursor-agent tool...]
```

**Line Count:** 30+ lines of synthesis + full responses

**Classification:**

**Synthesis Output (lines 822-879 in consultation.py):**

| Line Group | Type | Content | Count | Decision |
|--------|----|---------|-------|----------|
| 1 | separator | `┌─ Multi-Agent Analysis ─...─┐` | 1 | ❌ Remove |
| 2 | blank | | 1 | ❌ Remove |
| 3 | header | `│ CONSULTED AGENTS:` | 1 | ⚠️ Consolidate |
| 4-5 | info | `│ ✓ tool (duration)` | 2 | ⚠️ Consolidate |
| 6 | blank | | 1 | ❌ Remove |
| 7 | header | `│ CONSENSUS (Agents agree):` | 1 | ✅ Keep |
| 8-10 | info | `│ • point` | 3+ | ✅ Keep |
| 11 | blank | | 1 | ❌ Remove |
| 12 | header | `│ TOOL INSIGHTS:` | 1 | ❌ Remove (internal) |
| 13-15 | info | `│ • insight` | 3+ | ❌ Remove (minor details) |
| 16 | blank | | 1 | ❌ Remove |
| 17 | header | `│ SYNTHESIS:` | 1 | ✅ Keep |
| 18 | text | `│ synthesis text...` | 1+ | ✅ Keep |
| 19 | blank | | 1 | ❌ Remove |
| 20 | header | `│ RECOMMENDATIONS:` | 1 | ✅ Keep |
| 21-23 | info | `│ → rec` | 3+ | ✅ Keep |
| 24 | blank | | 1 | ❌ Remove |
| 25 | separator | `└──...──┘` | 1 | ❌ Remove |

**Detailed Responses Section (lines 881-894):**

| Line Group | Type | Content | Count | Decision |
|--------|----|---------|-------|----------|
| 1 | separator | `============================================================` | 1 | ❌ Remove |
| 2 | header | `DETAILED RESPONSES:` | 1 | ❌ Redundant |
| 3 | separator | `============================================================` | 1 | ❌ Remove |
| 4 | blank | | 1 | ❌ Remove |
| 5+ | per-tool | `─── TOOL ─...─` + output | N | ✅ Keep (actual content) |

**Issues Found:**

1. **Structural Box Formatting (lines 823, 878 in consultation.py)**
   - Lines: 2 (top + bottom border)
   - Problem: Decorative Unicode borders add no information value; pure structural overhead
   - Type: YAGNI violation
   - Severity: High

2. **Status Headers with Separators (lines 828-834, 838-841)**
   - Lines: ~6 lines for agent list
   - Problem: "CONSULTED AGENTS:" header + list that shows success/duration is redundant
   - Type: Structural announcement
   - Severity: High

3. **Tool-Specific Insights Section (lines 851-864)**
   - Lines: ~8 lines (header + per-tool insights)
   - Problem: Minor details about what each tool thinks separately; synthesis should cover this
   - Type: Over-explanation / redundant with synthesis
   - Severity: High

4. **Blank Lines Between Sections (multiple)**
   - Lines: ~6 blank lines
   - Problem: Excessive spacing for human readability but adds 6 lines
   - Type: Formatting excess
   - Severity: Medium

5. **Duplicate Responses (lines 881-894)**
   - Lines: 2 separator lines + 1 header + full tool output
   - Problem: Shows tool output twice - once in synthesis, once in detailed section
   - Type: Redundancy
   - Severity: Critical

6. **Per-Tool Section Headers (line 890)**
   - Lines: 1 per tool
   - Problem: Duplicates agent list already shown above
   - Type: Redundancy
   - Severity: Medium

**Assessment:** ❌ **Too Verbose** - Critical Issues

The multi-agent synthesis output adds 20-30 lines of structural formatting for what should be 8-10 lines of actionable output.

**Current Implementation (Verbosity Breakdown):**
- Synthesis box borders: 2 lines
- Agent list header + list: 4 lines
- Consensus/insights/synthesis headers: 4 lines
- Blank separators: 6 lines
- Tool insights section: 8 lines (largely redundant)
- Detailed responses section: 3 header/separator lines
- Per-tool section headers: 1 per tool

**Total Overhead:** ~20 lines of structural/redundant content

**Proposed Minimal Output:**

```
$ sdd test consult assertion --error "..." --hypothesis "..." --multi-agent

Consulted: gemini, cursor-agent

CONSENSUS:
  • Root cause is validation logic bypass
  • Fix requires assertion in precondition check

SYNTHESIS:
All agents identify the same root cause: missing validation in user
authentication check. The condition evaluates True even when it should
be False due to missing negation operator.

RECOMMENDATIONS:
  → Add assertion before state mutation
  → Review similar validation points in auth module

DETAILED RESPONSES:
─ gemini ─
[full response...]

─ cursor-agent ─
[full response...]
```

**Reduction:** 20+ lines down to 12 lines = **60% reduction in structural overhead**

---

## Root Cause Analysis

### Why is consultation output verbose?

1. **Structural Enthusiasm**
   - Designer wanted to create visually impressive output with Unicode boxes
   - Added headers and separators for "clarity" that actually obscure the content
   - Each section has its own header even though content speaks for itself

2. **Tool-Centric vs User-Centric Design**
   - Output focuses on showing "what each tool said" (tool-centric)
   - Should focus on "what the user needs to do" (user-centric)
   - Tool insights are internal implementation details; synthesis should summarize

3. **Synthesis as Layer, Not Consolidation**
   - Synthesis was added as an additional layer on top of full responses
   - Instead of synthesis *replacing* per-tool output, it's added alongside
   - Result: Same information presented three times (agent list, insights, detailed responses)

4. **No Verbosity Control**
   - No `--quiet` or `--verbose` modes to let users choose detail level
   - Everything is shown, always
   - Single users might want minimal (just recommendations), while debugging scenarios want full context

### Comparison to Good Examples

**Git's model (Good):**
```
$ git commit -m "Fix auth bug"
[main a1b2c3d] Fix auth bug
 1 file changed, 5 insertions(+), 2 deletions(-)
```
- Shows outcome clearly
- No internal process ("Creating index...", "Computing delta...", "Writing objects...")
- Concise but complete

**npm's model (Bad - what we're doing):**
```
npm WARN deprecated pkg@1.0.0
npm WARN deprecated pkg@1.0.0
npm notice created a lockfile as package-lock.json
added 42 packages from 17 contributors
audited 42 packages in 2.3s
found 0 vulnerabilities
```
- Multiple warnings not requested
- Implementation details (lockfile creation, audit)
- Still not as bad as our synthesis output

---

## Detailed Findings by Function

### `cmd_run` (lines 158-176)
- Status: ✅ Appropriate
- Output: Shows command being run + blank line
- Reasoning: Command visibility is important for understanding what flags are applied
- No issues found

### `cmd_discover` (lines 146-155)
- Status: ✅ Appropriate
- Delegates to `print_discovery_report()` which handles output
- Output is outcome-focused (test count, structure)
- No issues found

### `cmd_check_tools` (lines 50-76)
- Status: ⚠️ Minor Issues
- Has unnecessary blank line (line 65)
- Output could be 1 line: `Found 2 tool(s): gemini, codex`
- Current format is acceptable but not optimal
- Impact: Low (only affects single command)

### `cmd_consult` (lines 79-143)
- Status: ❌ Too Verbose
- **Issue 1:** Lines 114-115 print auto-routing decisions (implementation detail)
- **Issue 2:** Lines 116 prints blank line
- These should only appear if explicitly requested via `--verbose`
- Calls either `consult_with_auto_routing()` or `consult_multi_agent()`

### `consult_with_auto_routing()` (lines 553-636)
- Status: ⚠️ Minor Issues
- Line 600: Prints "Auto-selected tool: {tool}" + blank (lines 600-601)
- This is helpful for understanding which tool was chosen (keep as info, not action)
- Overall output is minimal beyond tool consultation itself
- Tool timeout messages (lines 510-512) are appropriate error handling

### `run_consultation()` (lines 446-533)
- Status: ✅ Appropriate
- Line 491: Prints "Consulting {tool}..." (appropriate action)
- Line 492: Prints separator (debatable but minor)
- Output is straightforward: action + tool output + error handling
- No major issues

### `consult_multi_agent()` (lines 896-1047)
- Status: ❌ Too Verbose - Critical Issues
- Lines 1004-1006: Prints action + tool list + separator (acceptable)
- Lines 1022-1024: Shows per-tool completion status ✅ (good progress indicator)
- Lines 1041-1044: Calls synthesis functions - **This is where verbosity explodes**

### `format_synthesis_output()` (lines 806-894)
- Status: ❌ Too Verbose - Critical Issues
- **Box borders (lines 823, 878):** 2 unnecessary lines of decorative Unicode
- **Agent list section (lines 828-834):** 6 lines for information that's already shown in progress
- **Consensus section (lines 844-848):** Good, keep this ✅
- **Tool insights (lines 851-864):** 8+ lines of per-tool insights that belong in synthesis, not separate
- **Synthesis section (lines 867-870):** Good, keep ✅
- **Recommendations (lines 872-876):** Good, keep ✅
- **Detailed responses (lines 881-894):** Repeats full tool output (problematic)
- **Total overhead:** ~20 lines of structural/redundant output

### `synthesize_responses()` (lines 737-803)
- Implementation detail not directly visible to users
- Creates the data structures that feed into format_synthesis_output
- No direct output issues, but output format design is problematic

---

## Summary of YAGNI/KISS Violations

### Critical Violations (Remove Immediately)
1. **Box borders and separators** - Decorative, not informative
2. **"CONSULTED AGENTS" header + list** - Redundant after progress indicators
3. **Tool-specific insights section** - Should be merged into synthesis
4. **Duplicate detailed responses** - Shown twice

### High Priority Violations (Redesign)
1. **Auto-routing announcements** - Should only show if explicitly requested
2. **Blank line separators** - Reduce from 6 to 2-3
3. **Per-tool section headers** - Not needed

### Medium Priority (Nice-to-Have Improvements)
1. **Header borders** - Consolidate headers without Unicode boxes
2. **Status indicators** - Duration info is nice but not essential

---

## Proposed Verbosity Control

To address this properly, implement three verbosity modes:

```
--quiet or -q          : Recommendations only (2-5 lines)
--normal (default)     : Synthesis + Recommendations (8-10 lines)
--verbose or -v        : Full synthesis + detailed responses (15-20 lines)
```

This allows users to choose their preferred detail level:

**QUIET MODE OUTPUT:**
```
Root cause: Missing validation in auth check
Recommendations:
  → Add assertion before state mutation
  → Review similar validation points in auth module
```

**NORMAL MODE OUTPUT:**
```
Consulted: gemini, cursor-agent

CONSENSUS:
  • Root cause is missing validation
  • Fix requires assertion check

SYNTHESIS:
All agents identify the same root cause: missing validation...

RECOMMENDATIONS:
  → Add assertion before state mutation
  → Review similar validation points in auth module
```

**VERBOSE MODE OUTPUT:**
```
[Current output with all synthesis details and full responses]
```

---

## Files Requiring Changes

1. **`/src/claude_skills/claude_skills/run_tests/cli.py`**
   - Lines 114-116: Remove auto-routing announcements OR make conditional

2. **`/src/claude_skills/claude_skills/run_tests/consultation.py`**
   - Line 492: Consider removing separator or making it conditional
   - Lines 1004-1006: Improve clarity of multi-agent progress message
   - Lines 806-894 (`format_synthesis_output`):** Redesign entire output structure
     - Remove box borders (lines 823, 878)
     - Consolidate agent list (lines 828-834)
     - Merge insights into synthesis (lines 851-864)
     - Remove/consolidate blank lines
     - Reconsider detailed responses section (lines 881-894)

3. **`/skills/run-tests/SKILL.md`**
   - Update example outputs to match new minimal format
   - Document verbosity control modes
   - Update expected output in examples

---

## Metrics

| Metric | Current | Proposed | Reduction |
|--------|---------|----------|-----------|
| Single-agent consult overhead | 3 lines | 0 lines | 100% |
| Multi-agent synthesis output | 20+ lines | 12 lines | 40% |
| Box/border lines | 2 | 0 | 100% |
| Blank line separators | 6 | 2 | 67% |
| Section headers | 6 | 3 | 50% |
| **Total overhead (multi-agent)** | **20+ lines** | **8 lines** | **60%** |

---

## Recommendations

### Immediate Actions (High Priority)
1. **Remove auto-routing announcements** from `cmd_consult()` - these are internal decisions
2. **Remove box borders** from `format_synthesis_output()` - decorative, not informative
3. **Consolidate agent list** - either show as progress OR in final summary, not both
4. **Merge tool insights into synthesis** - don't show insights separately

### Short-Term Refactoring (Medium Priority)
1. **Implement verbosity modes** (--quiet, --normal, --verbose)
2. **Reduce blank line separators** from 6 to 2-3
3. **Consolidate section headers** - remove decorative formatting
4. **Review detailed responses section** - consider making optional or consolidating

### Long-Term Improvements (Low Priority)
1. **Redesign synthesis** to be more concise by default
2. **Add config option** for default verbosity level
3. **Implement streaming** for tool responses so they appear in real-time (reduces perception of verbosity)

---

## Verdict

**Overall Assessment: ❌ Too Verbose**

**Command Breakdown:**
- `sdd test run`: ✅ Appropriate
- `sdd test discover`: ✅ Appropriate
- `sdd test check-tools`: ⚠️ Minor issues (1 unnecessary blank line)
- `sdd test consult`: ❌ Too verbose (auto-routing announcements)
- Multi-agent mode: ❌ Too verbose (20+ lines of structural overhead)

**Impact:** Users see 20+ lines of synthesis formatting when they really only need 8-10 lines of actionable information. The structural decoration (boxes, separators, headers) adds cognitive load without adding value.

**Root Cause:** Designer optimized for visual impression and showing "what the tools said" rather than optimizing for user outcome ("what should I do").

**Fix Complexity:** Medium - Requires redesign of synthesis output format and implementation of verbosity control, but no core logic changes needed.

---

## Appendix: Current vs Proposed Outputs

### Current: Multi-Agent Consultation (30+ lines)

```
Consulting 2 agents in parallel...
Tools: gemini, cursor-agent
============================================================

✓ gemini completed (2.3s)
✓ cursor-agent completed (1.8s)

┌─ Multi-Agent Analysis ────────────────────────────────────┐

│ CONSULTED AGENTS:
│ ✓ gemini (2.3s)
│ ✓ cursor-agent (1.8s)
│
│ CONSENSUS (Agents agree):
│ • Root cause is validation logic bypass
│ • Fix requires assertion in precondition check
│
│ CODEX INSIGHTS:
│ • Check return value from condition check
│
│ CURSOR-AGENT INSIGHTS:
│ • Similar patterns in user_auth.py line 45
│
│ SYNTHESIS:
│ All agents identify the same root cause: missing validation...
│
│ RECOMMENDATIONS:
│ → Add assertion before state mutation
│ → Review similar validation points in auth module
│
└──────────────────────────────────────────────────────────┘

============================================================
DETAILED RESPONSES:
============================================================

─── GEMINI ──────────────────────────────────────────────
[Full gemini response...]

─── CURSOR-AGENT ────────────────────────────────────────
[Full cursor-agent response...]
```

### Proposed: Multi-Agent Consultation (14 lines + full responses)

```
Consulted: gemini, cursor-agent

CONSENSUS:
  • Root cause is validation logic bypass
  • Fix requires assertion in precondition check

SYNTHESIS:
All agents identify the same root cause: missing validation in user
authentication check. The condition evaluates True even when it should
be False due to missing negation operator.

RECOMMENDATIONS:
  → Add assertion before state mutation
  → Review similar validation points in auth module

DETAILED RESPONSES:
─── GEMINI ─────────────────────────────────────────────
[Full gemini response...]

─── CURSOR-AGENT ───────────────────────────────────────
[Full cursor-agent response...]
```

**Line Reduction:** 30+ lines → 14 lines of synthesis = **53% reduction** before detailed responses

---

## Conclusion

The run-tests module provides valuable functionality but violates YAGNI/KISS principles in its consultation output, particularly in multi-agent mode. The extensive structural formatting (boxes, separators, duplicate headers) adds cognitive load without providing actionable value. Recommended to implement verbosity control modes and redesign the synthesis output to show only essential information by default.
