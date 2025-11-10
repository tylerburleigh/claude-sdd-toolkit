# CLI Output Audit: doc-query

## Audit Metadata

- **Module:** doc-query
- **CLI Path:** `/src/claude_skills/claude_skills/doc_query/cli.py`
- **SKILL.md:** `/skills/doc-query/SKILL.md`
- **Namespace:** `sdd doc query`
- **Audit Date:** 2025-11-09
- **Auditor:** Automated Analysis

---

## Executive Summary

**Overall Verdict:** ⚠️ **Minor Issues**

The doc-query CLI module demonstrates appropriate output design for query operations, with clear results and proper error handling. However, the **documentation staleness detection mechanism** introduces excessive verbosity during normal operation:

- **Normal query operation:** ✅ Appropriate (minimal, outcome-focused)
- **Staleness detection:** ⚠️ Minor issues (verbose regeneration messages)
- **Error handling:** ✅ Appropriate (clear, actionable)

**Key Finding:** The staleness mechanism adds 3-4 lines of output before the actual query result, which violates YAGNI by showing internal implementation details (checking staleness, regenerating docs) that users don't need to see during normal queries.

**Estimated Improvement:** 15-25% output reduction achievable by consolidating staleness messaging.

---

## 1. Command Analysis Summary

The doc-query module implements 20+ commands for querying auto-generated documentation:

| Category | Commands | Output Character |
|----------|----------|-----------------|
| **Basic Lookups** | find-class, find-function, find-module | Minimal, result-focused ✅ |
| **Analysis** | complexity, dependencies, callers, callees | Summary + detailed results ✅ |
| **Visualization** | call-graph, trace-entry, trace-data | Structured analysis ✅ |
| **Utilities** | stats, context, describe-module, search | Summary + breakdown ✅ |
| **Initialization** | _ensure_query (staleness detection) | **Verbose** ⚠️ |

---

## 2. Printer Output Trace

### Key Printer Calls

| Line | Function | Type | Message | Classification |
|------|----------|------|---------|-----------------|
| 67 | cmd_* | error | "Documentation not found at {docs_path}..." | ✅ Error |
| 75 | cmd_* | error | "Documentation not found at {query.docs_path}..." | ✅ Error |
| **93** | _ensure_query | info | "🔄 Documentation is stale, regenerating..." | ❌ Implementation detail |
| **120** | _ensure_query | success | "✅ Documentation regenerated successfully\n" | ⚠️ Could be silent |
| **132** | _ensure_query | warning | "⚠️ Failed to regenerate documentation: {error}" | ✅ Error reporting |
| **133** | _ensure_query | warning | "Continuing with stale documentation...\n" | ✅ Heads-up |
| **137** | _ensure_query | warning | "⚠️ Error regenerating documentation: {e}" | ✅ Error reporting |
| **138** | _ensure_query | warning | "Continuing with stale documentation...\n" | ✅ Heads-up |
| **152** | _ensure_query | warning | "⚠️ {warning_msg}" | ✅ Warning |
| **153** | _ensure_query | info | "To auto-refresh: remove --skip-refresh flag..." | ✅ Hint |
| **154** | _ensure_query | info | "To suppress this warning: use --no-staleness-check" | ✅ Hint |
| 830+ | cmd_* | error | Various error messages | ✅ Errors |

---

## 3. Simulated Command Output Examples

### Example 1: find-function (Happy Path, No Staleness Issues)

```
$ sdd doc find-function calculate_score

Found 1 result(s):

1. Function: calculate_score
  File: src/services/scoring.py
  Line: 42
  Complexity: 7
  Parameters: request, config
  Summary: Calculates score based on request data and configuration

```

**Lines:** 7 | **Classification:** ✅ Appropriate

**Analysis:** Pure outcome-focused output. No implementation details. Shows what user asked for.

---

### Example 2: find-function (With Staleness, Auto-Regenerate)

```
$ sdd doc find-function calculate_score

🔄 Documentation is stale, regenerating...
✅ Documentation regenerated successfully

Found 1 result(s):

1. Function: calculate_score
  File: src/services/scoring.py
  Line: 42
  Complexity: 7
  Parameters: request, config
  Summary: Calculates score based on request data and configuration

```

**Lines:** 11 | **Classification:** ⚠️ Minor verbosity issue

**Analysis:**
- Lines 1-2 are implementation details (internal staleness detection and auto-regeneration)
- User asked for: "find this function"
- User got: "finding this function + regenerating documentation + result"
- The regeneration is a side effect, not part of the user's request

---

### Example 3: find-function (With Staleness, Skipped Refresh)

```
$ sdd doc find-function calculate_score --skip-refresh

⚠️  Documentation is stale (generated 3 days ago, source modified 2 hours after generation)
    To auto-refresh: remove --skip-refresh flag or run 'sdd doc generate'
    To suppress this warning: use --no-staleness-check

Found 1 result(s):

1. Function: calculate_score
  File: src/services/scoring.py
  Line: 42
  Complexity: 7
  Parameters: request, config
  Summary: Calculates score based on request data and configuration

```

**Lines:** 14 | **Classification:** ❌ Too verbose

**Analysis:**
- Lines 1-4: Warning about stale docs + hints (3 lines that don't advance toward query result)
- User explicitly chose `--skip-refresh`, so they know the docs might be stale
- The hints about "--no-staleness-check" are extra noise after user made a conscious choice
- Could be condensed to: "⚠️ Using potentially stale documentation (run with 'sdd doc generate' to refresh)"

---

### Example 4: describe-module

```
$ sdd doc describe-module app/services/scoring.py

Module: app/services/scoring.py
  Docstring: Service for scoring user submissions
  Classes: 2 | Functions: 8 | Avg Complexity: 5.2 | Max Complexity: 11
  High Complexity Functions: 3
  Imports: fastapi, pydantic, sqlalchemy, numpy, sklearn, +2 more
  Outgoing Dependencies: models.py, utils.py, external_api.py
  Incoming Dependencies: api.py, admin.py

  Classes (2):
    - ScoreCalculator — Manages score calculation pipeline
    - ScoringConfig — Configuration for scoring

  Key Functions (8 listed):
    - calculate_score (complexity: 7) — Entry point for scoring
    - process_request (complexity: 11) 🔴 — Request processing
    - validate_data (complexity: 3) — Input validation
    - aggregate_scores (complexity: 6) — Aggregates multiple scores
    - cache_result (complexity: 2) — Caches scoring result
    - fetch_model (complexity: 4) — Loads ML model from disk
    - score_with_ml (complexity: 9) 🔴 — ML-based scoring
    - cleanup_resources (complexity: 1) — Resource cleanup

```

**Lines:** 21 | **Classification:** ✅ Appropriate

**Analysis:** Rich summary with multiple relevant categories. Each section is useful. Properly formatted. No implementation noise.

---

### Example 5: stats

```
$ sdd doc stats

Documentation Statistics:
  Project: claude-sdd-toolkit (version 0.1.0)
  Generated At: 2025-11-08 14:32:00
  Languages: Python
  Total Files: 48
  Total Modules: 45
  Total Classes: 127
  High Complexity Functions (≥5): 23
  Total Functions: 512
  Total Lines: 45,382
  Average Complexity: 4.2
  Max Complexity: 18

```

**Lines:** 12 | **Classification:** ✅ Appropriate

**Analysis:** Concise statistics. All metrics are requested/expected. No implementation details.

---

### Example 6: callers

```
$ sdd doc callers calculate_score

Found 3 caller(s) for 'calculate_score':

1. process_submission (function_call)
   Location: src/api/endpoints.py:156

2. batch_score_users (method_call)
   Location: src/services/batch.py:89

3. test_calculate_score (function_call)
   Location: tests/test_scoring.py:24

```

**Lines:** 11 | **Classification:** ✅ Appropriate

**Analysis:** Direct answer to question. Minimal headers, focused results. Each result shows: name, type, location.

---

### Example 7: trace-entry (Automated Workflow)

```
$ sdd doc trace-entry process_request

Call Chain for 'process_request':
  Layer: Presentation (API)
  Function: process_request (complexity: 8)
  Location: src/api/endpoints.py:45

  ↓ Calls (2 functions):
    Layer: Business Logic
    - validate_input (complexity: 3)
      ↓ Calls (1 function):
        - check_permissions (complexity: 2)

    Layer: Business Logic
    - execute_request (complexity: 11) 🔴 Hot spot
      ↓ Calls (4 functions):
        - fetch_data (complexity: 4)
        - transform_data (complexity: 5)
        - persist_result (complexity: 6)
        - notify_subscribers (complexity: 3)

Summary:
  Total functions in chain: 8
  Max depth: 4
  Average complexity: 5.4
  High-complexity functions: 2
  Recommendation: execute_request is a hot spot (complexity 11). Consider breaking into smaller functions.

```

**Lines:** 30 | **Classification:** ✅ Appropriate

**Analysis:** Hierarchical call chain with layer classification. Rich output but all lines serve analysis purpose. No implementation noise. Shows outcome of analysis.

---

## 4. YAGNI/KISS Analysis

### Issue 1: Staleness Detection Message (Lines 93)

**Classification:** ❌ **Remove** - Implementation Detail

**Reasoning:**
- User command: "Find this function"
- User intent: Get result immediately
- What's shown: "Regenerating documentation..." (internal operation)
- **YAGNI violation:** User doesn't need to know docs are being regenerated. This is an implementation detail of how the query service ensures freshness.
- **Impact:** Makes simple queries appear to hang with progress message

**Current code:**
```python
if not _maybe_json(args, {"status": "info", "message": "Regenerating stale documentation..."}):
    printer.info("\n🔄 Documentation is stale, regenerating...")
```

**Better approach:** Regenerate silently. Only warn if it fails.

---

### Issue 2: Success Message for Auto-Regeneration (Line 120)

**Classification:** 🔄 **Consolidate** - Outcome, but Unnecessary

**Reasoning:**
- When docs auto-regenerate and succeed, the next line is the actual query result
- The success message is noise—the user will see their results
- **YAGNI violation:** Announcing what was already accomplished
- **Context:** Success messages make sense for user-initiated operations (like `sdd doc generate`), not for background maintenance

**Current code:**
```python
printer.success("✅ Documentation regenerated successfully\n")
```

**Better approach:** If query results follow immediately, the regeneration is implicitly successful. No announcement needed.

---

### Issue 3: Verbose Staleness Warning with Hints (Lines 152-154)

**Classification:** ⚠️ **Consolidate** - Can be More Concise

**Reasoning:**
- When user explicitly uses `--skip-refresh`, they've made a conscious choice
- Showing hints about other flags after they've already chosen options is defensive over-explanation
- The multi-line hint structure is verbose

**Current code:**
```python
printer.warning(f"\n⚠️  {warning_msg}")
printer.info(f"    {refresh_hint}")
printer.info(f"    {suppress_hint}\n")
```

**Example with 3 lines:**
```
⚠️  Documentation is stale (generated 3 days ago, source modified 2 hours after generation)
    To auto-refresh: remove --skip-refresh flag or run 'sdd doc generate'
    To suppress this warning: use --no-staleness-check
```

**Better approach:** Single line with parenthetical hint
```
⚠️  Documentation is stale. Use 'sdd doc generate' to refresh or '--no-staleness-check' to suppress.
```

---

### Issue 4: Error Regeneration Messages (Lines 132-133, 137-138)

**Classification:** ✅ **Keep** - Errors should always be visible

**Reasoning:**
- When regeneration fails, user needs to know
- "Continuing with stale documentation..." is a heads-up about degraded state
- These are error/warning situations, not normal flow

---

### Issue 5: Query Result Formatting

**Classification:** ✅ **Keep** - All lines provide value

**Reasoning:**
- Summary lines ("Found X results")
- Entity headers (Class/Function/Module names)
- Metadata (File, Line, Complexity, etc.)
- All serve the purpose of understanding results

---

## 5. Root Cause Analysis

### Why Staleness Verbosity Exists

1. **Design Pattern:** Staleness check is in `_ensure_query()`, which runs for every command
2. **Conservative Approach:** Multiple printer calls for each path (success, failure, warning)
3. **User Guidance:** Adding hints to help users navigate multiple options
4. **Lack of Verbosity Control:** No `--quiet` or `--verbose` flags to suppress/show these messages

### Why Query Output is Clean

1. **Single Purpose:** Each command handler focuses on one query type
2. **Direct Formatting:** Print functions like `print_context()`, `print_module_summary()` are built for specific output structures
3. **Result-Driven:** Output is determined by query results, not by implementation steps

---

## 6. Output Verbosity Summary

### Current Output Levels (By Command Type)

| Category | Typical Lines | Character |
|----------|---------------|-----------|
| Basic query (find-*) | 5-10 | Minimal ✅ |
| Query + staleness check (no-refresh) | 11-15 | Verbose ⚠️ |
| Query + staleness auto-regen | 8-13 | Slightly verbose ⚠️ |
| Analysis command (callers, dependencies) | 8-12 | Minimal ✅ |
| Visualization (call-graph, trace-entry) | 25-35 | Rich, appropriate ✅ |
| Utilities (stats, describe-module) | 12-22 | Rich, appropriate ✅ |

### Reduction Opportunities

**Staleness Auto-Regeneration Path (Currently 8-13 lines):**
- Remove line 93: `printer.info("🔄 Documentation is stale, regenerating...")`
- Remove line 120: `printer.success("✅ Documentation regenerated successfully\n")`
- **Result:** 6-11 lines (reduction: 2 lines, ~15% less output)

**Staleness Skip-Refresh Path (Currently 11-15 lines):**
- Consolidate lines 152-154 into single line
- **Result:** 9-12 lines (reduction: 2 lines, ~16% less output)

---

## 7. Proposed Minimal Output Examples

### Scenario A: Query with Auto-Regeneration (Minimal)

**Current:**
```
🔄 Documentation is stale, regenerating...
✅ Documentation regenerated successfully

Found 1 result(s):

1. Function: calculate_score
  File: src/services/scoring.py
  ...
```
(11 lines)

**Proposed:**
```
Found 1 result(s):

1. Function: calculate_score
  File: src/services/scoring.py
  ...
```
(9 lines) → **18% reduction**

**Rationale:** If regeneration fails, error message appears. If it succeeds silently, user sees their results. No status updates needed for background operations.

---

### Scenario B: Query with Stale Warning (Minimal)

**Current:**
```
⚠️  Documentation is stale (generated 3 days ago...)
    To auto-refresh: remove --skip-refresh flag or run 'sdd doc generate'
    To suppress this warning: use --no-staleness-check

Found 1 result(s):
...
```
(5 header lines + results)

**Proposed:**
```
⚠️  Documentation is stale. Refresh with: sdd doc generate

Found 1 result(s):
...
```
(2 header lines + results) → **60% reduction in warning section**

**Rationale:** User explicitly chose `--skip-refresh`. Brief warning + actionable fix. Don't repeat other options.

---

## 8. JSON Output Assessment

**Standard:** ✅ **Appropriate**

The `--json` flag supports JSON output throughout the CLI. The implementation correctly uses `_maybe_json()` to branch between text and JSON modes:

```python
if _maybe_json(args, payload):
    return 0
# Text output fallback
_print_results(args, results)
```

**Compliance with JSON Output Exception:**
- ✅ Text mode: Minimal (follows YAGNI)
- ✅ JSON mode: Complete data (machines need everything)
- ✅ JSON output not affected by staleness verbosity

Example:
```bash
$ sdd doc find-function calculate_score --json
{
  "entity_type": "function",
  "name": "calculate_score",
  "file": "src/services/scoring.py",
  "line": 42,
  ...
}
```

---

## 9. Error Handling Assessment

**Classification:** ✅ **Appropriate**

Error messages are clear and actionable:

| Error | Message | Severity | Actionable |
|-------|---------|----------|-----------|
| Docs not found | "Documentation not found at {path}. Run 'doc generate' first." | Error | ✅ Yes |
| Load failure | "Failed to load regenerated documentation" | Error | ⚠️ Generic |
| Regen failure | "Failed to regenerate documentation: {stderr}" | Warning | ✅ Yes |
| Entity not found | "Function '{name}' not found in documentation" | Error | ⚠️ Generic |

**Observation:** Error messages correctly show what failed but could be more specific about recovery steps (e.g., "Function not found. Check spelling or run 'sdd doc search'").

---

## 10. Verdict & Recommendations

### Overall Assessment: ⚠️ **Minor Issues**

**Justification:**
1. **Query operations:** Clean, outcome-focused output (80% of commands)
2. **Staleness mechanism:** Adds minor verbosity to normal queries (20% of commands)
3. **Error handling:** Clear and appropriate throughout
4. **JSON support:** Properly implemented
5. **Result formatting:** Rich, relevant information for analysis commands

### Severity

- ❌ **NOT too verbose** - Most commands are appropriate
- ⚠️ **Minor improvements possible** - Staleness messages can be consolidated
- ✅ **No KISS violations** - Output structure is straightforward

### Recommended Changes (Priority Order)

#### Priority 1: Silent Auto-Regeneration (High Impact, Low Risk)

**Change:** Remove progress messages when auto-regenerating docs

**Code Location:** `/src/claude_skills/claude_skills/doc_query/cli.py`, lines 93 and 120

**Before:**
```python
if not _maybe_json(args, {"status": "info", "message": "Regenerating stale documentation..."}):
    printer.info("\n🔄 Documentation is stale, regenerating...")
# ... regeneration code ...
if result.returncode == 0:
    if not _maybe_json(args, {"status": "success", "message": "Documentation regenerated successfully"}):
        printer.success("✅ Documentation regenerated successfully\n")
```

**After:**
```python
# Silently regenerate in background
# Only show messages if regeneration fails (via error/warning messages)
```

**Impact:**
- Reduces normal query output by 2 lines when staleness detected
- 15-20% output reduction for queries with stale docs
- Makes queries feel faster (no intermediate status messages)

**Risk:** Low - Errors still reported if regeneration fails

---

#### Priority 2: Consolidate Stale-Warning Messages (Medium Impact, Low Risk)

**Change:** Combine three separate printer calls into one message

**Code Location:** `/src/claude_skills/claude_skills/doc_query/cli.py`, lines 152-154

**Before:**
```python
printer.warning(f"\n⚠️  {warning_msg}")
printer.info(f"    {refresh_hint}")
printer.info(f"    {suppress_hint}\n")
```

**After:**
```python
printer.warning(f"\n⚠️  {warning_msg}")
printer.info(f"    Refresh docs: sdd doc generate")
```

**Impact:**
- Reduces warning output by 1 line
- Cleaner, less prescriptive messaging
- Hints are still available in `sdd doc --help`

**Risk:** Low - Users can still find options via help

---

#### Priority 3: Add Verbosity Control Flags (Low Priority, Medium Effort)

**Suggested Addition:** `--quiet` and `--verbose` flags

- `--quiet`: Suppress all informational messages, show only errors and results
- `--verbose`: Show staleness detection, regeneration progress, detailed steps

**Use Case:** Enables users to control output verbosity for their workflow

---

## 11. Implementation Notes

### Files to Modify

1. **`/src/claude_skills/claude_skills/doc_query/cli.py`**
   - Lines 92-120: Staleness auto-regeneration messaging
   - Lines 152-154: Stale warning messaging

### Testing Considerations

1. Test normal queries still work without staleness messages
2. Test error messages still appear when regeneration fails
3. Test JSON output is unaffected
4. Test with `--skip-refresh` and `--no-staleness-check` flags

### Documentation Updates Needed

- **SKILL.md:** Update examples to show new output format (without regen messages)
- **Examples in SKILL.md:** Lines ~217-239 (stale documentation section) show old verbose output

---

## 12. Examples Updated for New Output Format

### Updated Example 1: Default Behavior

**Old SKILL.md Example (lines 217-224):**
```
$ sdd doc find-function calculate_score

🔄 Documentation is stale, regenerating...
✅ Documentation regenerated successfully

Found 1 result(s):
...
```

**Updated Example (Proposed):**
```
$ sdd doc find-function calculate_score

Found 1 result(s):
...
```

---

### Updated Example 2: Fast Exploration

**Old SKILL.md Example (lines 274-279):**
```
$ sdd doc find-class User --skip-refresh
⚠️  Documentation is stale (generated 3 days ago, source modified 2 hours after generation)
    To auto-refresh: remove --skip-refresh flag or run 'sdd doc generate'
    To suppress this warning: use --no-staleness-check

Found 1 result(s):
...
```

**Updated Example (Proposed):**
```
$ sdd doc find-class User --skip-refresh
⚠️  Documentation is stale. Refresh with: sdd doc generate

Found 1 result(s):
...
```

---

## Conclusion

The doc-query CLI demonstrates **appropriate output design** for a query-focused tool. The module correctly separates:

- **Text output** (minimal, outcome-focused) from
- **JSON output** (complete, machine-readable) from
- **Error messages** (clear, actionable)

The only improvement opportunity is to make the **staleness detection mechanism silent during normal operation**. This is a minor enhancement that would make queries feel faster and cleaner without sacrificing any user-facing functionality.

**Recommendation:** Implement Priority 1 changes (silent auto-regeneration) for improved user experience. This aligns with YAGNI principles by removing non-essential implementation details from normal command output.

---

## Appendix A: Command-by-Command Assessment

| Command | Output Lines | Verdict | Notes |
|---------|-------------|---------|-------|
| find-class | 5-10 | ✅ Appropriate | Minimal, focused |
| find-function | 5-10 | ✅ Appropriate | Minimal, focused |
| find-module | 5-10 | ✅ Appropriate | Minimal, focused |
| complexity | 8-15 | ✅ Appropriate | Result summary + list |
| dependencies | 6-12 | ✅ Appropriate | Dependency tree |
| search | 8-15 | ✅ Appropriate | Search results |
| context | 15-30 | ✅ Appropriate | Comprehensive breakdown |
| describe-module | 18-25 | ✅ Appropriate | Rich module summary |
| stats | 12-14 | ✅ Appropriate | Metrics only |
| list-classes | 5-20 | ✅ Appropriate | Simple list format |
| list-functions | 5-20 | ✅ Appropriate | Simple list format |
| list-modules | 5-20 | ✅ Appropriate | Simple list format |
| callers | 8-15 | ✅ Appropriate | Location-based results |
| callees | 8-15 | ✅ Appropriate | Location-based results |
| call-graph | 20-30 | ✅ Appropriate | Structured hierarchy |
| trace-entry | 25-40 | ✅ Appropriate | Rich architectural analysis |
| trace-data | 20-35 | ✅ Appropriate | CRUD operation mapping |
| impact | 25-40 | ✅ Appropriate | Risk assessment + breakdown |
| refactor-candidates | 30-50 | ✅ Appropriate | Prioritized list + analysis |

**Summary:** 18/18 commands have appropriate output. The staleness mechanism is the only area for improvement.

---

## Appendix B: YAGNI Quick Reference Applied

| Message | User Needs? | Classification | Action |
|---------|------------|-----------------|--------|
| "Documentation is stale, regenerating..." | ❌ No | Implementation detail | Remove |
| "Documentation regenerated successfully" | ❌ No | Internal operation | Remove |
| "Documentation not found at {path}" | ✅ Yes | Error | Keep |
| "Failed to regenerate documentation" | ✅ Yes | Error | Keep |
| "Found X results" | ✅ Yes | Outcome | Keep |
| "Entity not found" | ✅ Yes | Error | Keep |
| Complexity metrics | ✅ Yes | Analysis | Keep |
| File locations | ✅ Yes | Navigation | Keep |
| Docstring excerpts | ✅ Yes (context) | Helpful | Keep |
| Call graphs | ✅ Yes | Analysis | Keep |

---

**End of Report**
