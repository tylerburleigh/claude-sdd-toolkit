# CLI Output Audit: Context Tracker Commands

**Audit Date:** 2025-11-09
**Auditor:** Claude Code
**Commands Analyzed:** `context`, `session-marker`
**Module:** `/src/claude_skills/claude_skills/context_tracker/cli.py`
**Type:** Utility command (no SKILL.md - context tracking is infrastructure, not user-facing feature)

---

## Executive Summary

The context tracker commands (`session-marker` and `context`) are utility commands that track Claude Code token usage and context window consumption. The CLI output is **appropriate for a utility command** with **minor verbosity issues** in error handling.

| Metric | Value |
|--------|-------|
| **Overall Verdict** | ⚠️ Minor issues |
| **Primary Command Output** | ✅ Appropriate (structured data) |
| **Error Messages** | ❌ Too verbose |
| **JSON Output** | ✅ Appropriate (complete data for machines) |
| **Human-Readable Output** | ✅ Appropriate (clear, organized) |

---

## Command Analysis

### Command 1: `session-marker`

**Purpose:** Generate a unique session marker that gets logged to the transcript, enabling reliable session identification across concurrent Claude Code sessions.

#### Current Output

```
$ sdd session-marker

SESSION_MARKER_abc12345
```

**Line Count:** 1 line (plus blank line)

#### Classification

| Output | Type | Keep/Remove | Reason |
|--------|------|-------------|--------|
| `SESSION_MARKER_abc12345` | Outcome | ✅ Keep | The entire purpose of the command - user captures this to use with `context` command |

#### Implementation Analysis

**Source:** `/src/claude_skills/claude_skills/context_tracker/cli.py`, lines 286-299

```python
def cmd_session_marker(args, printer):
    """Handler for 'sdd session-marker' command."""
    marker = generate_session_marker()
    # Output marker to stdout (not stderr) so it can be captured
    print(marker)
```

**Findings:**
- Minimal, clean implementation
- Correctly outputs to stdout for capturing in shell scripts
- No unnecessary logging or progress messages
- No implementation details exposed

#### Verdict

✅ **Appropriate** - The output is a single piece of data (the marker) that the user needs. No verbosity issues.

---

### Command 2: `context`

**Purpose:** Display Claude Code token and context window usage metrics from the current session's transcript.

#### Current Output (Success Case)

```
$ sdd context --session-marker SESSION_MARKER_abc12345

============================================================
Claude Code Context Usage
============================================================

Transcript: abc12345.jsonl

Context Used:    12,345 / 160,000 tokens (7.7%)

Session Totals:
  Input Tokens:    8,000
  Output Tokens:   2,500
  Cached Tokens:   1,845
  Total Tokens:    12,345
============================================================
```

**Line Count:** 13 lines (including separators)

#### Classification

| Output | Type | Keep/Remove | Reason |
|--------|------|-------------|--------|
| `============================================================` | Formatting | 🔄 Consolidate | Decorative; essential for readability |
| `Claude Code Context Usage` | Outcome | ✅ Keep | Clear section header |
| `Transcript: abc12345.jsonl` | Context | ⚠️ Optional | Useful for debugging but internal detail |
| `Context Used: 12,345 / 160,000 tokens (7.7%)` | Outcome | ✅ Keep | Primary metric user needs |
| `Session Totals:` | Header | 🔄 Consolidate | Could be folded into individual lines |
| `  Input Tokens: 8,000` | Outcome | ✅ Keep | Useful context breakdown |
| `  Output Tokens: 2,500` | Outcome | ✅ Keep | Useful context breakdown |
| `  Cached Tokens: 1,845` | Outcome | ✅ Keep | Useful context breakdown (cache insights) |
| `  Total Tokens: 12,345` | Outcome | ⚠️ Redundant | Already shown in "Context Used" line |

#### Implementation Analysis

**Source:** `/src/claude_skills/claude_skills/context_tracker/cli.py`, lines 224-255

The human-readable output formatter is well-structured:
- Clear section headers with visual separation
- Organized into logical groups (primary metric, session totals)
- Proper number formatting with thousands separators
- Optional transcript filename for debugging

**Positive aspects:**
- No implementation details (loading, parsing, searching) exposed
- JSON and human output are separate and appropriate for each mode
- Supports `--verbose` flag to control JSON output complexity

#### JSON Output (Default Mode)

```json
{"context_percentage_used": 7.7}
```

**Analysis:** Simplified, clean output appropriate for scripting and integration.

#### JSON Output (Verbose Mode)

```json
{
  "context_length": 12345,
  "context_percentage": 7.7,
  "max_context": 160000,
  "input_tokens": 8000,
  "output_tokens": 2500,
  "cached_tokens": 1845,
  "total_tokens": 12345,
  "transcript_path": "/path/to/transcript.jsonl"
}
```

**Analysis:** Complete data for machines. Appropriate verbosity for `--verbose` flag.

---

## Error Message Analysis

**Issue Category:** Verbosity in Error Handling
**Severity:** Minor (error cases should be verbose, but these exceed best practices)

### Error Case: Marker Not Found

**Source:** `/src/claude_skills/claude_skills/context_tracker/cli.py`, lines 312-364

```python
if not transcript_path:
    # Provide context-specific error message
    if hasattr(args, 'session_marker') and args.session_marker:
        # ... detailed error with searched directories
```

#### Current Error Output

```
Could not find transcript containing marker: SESSION_MARKER_abc12345

This usually means the marker hasn't been written to the transcript yet.

Make sure you're using the two-command pattern:
  1. Call 'sdd session-marker' first (generates and logs marker)
  2. Call 'sdd context --session-marker <marker>' in a SEPARATE command

Important: 'SEPARATE command' means a separate conversation turn,
not just separate bash commands. The marker must be logged to the
transcript file before it can be found.

Searched in 2 transcript directories:
  • /Users/user/.claude/projects/home-user-Documents-project (~transcript file(s))
  • /Users/user/.claude/projects/home-user-Documents (~transcript file(s))

Troubleshooting:
  • Wait a few seconds after generating the marker
  • Ensure both commands run from the same working directory
  • If multiple sessions are active, use a fresh marker
  • Try running 'sdd session-marker' again in a new message
```

**Line Count:** ~18 lines

#### Classification

| Section | Keep/Remove | Reason |
|---------|-------------|--------|
| Initial error statement | ✅ Keep | Tells user what went wrong |
| Explanation | ✅ Keep | Helps user understand root cause |
| Correct usage pattern | ✅ Keep | User needs to know correct approach |
| Emphasis on SEPARATE command | 🔄 Consolidate | Important but could be one line instead of three |
| Searched directories list | ⚠️ Optional | Useful for debugging but verbose |
| Troubleshooting tips | ⚠️ Excessive | 5 bullet points may overwhelm user |

#### Root Cause of Verbosity

The error handler tries to be **maximally helpful** for a complex usage pattern (two-command session marker). This is a valid design choice for a utility command where users might be confused about the workflow. However, the implementation could be more concise:

**Current approach:** Explains everything (18 lines)
**Recommended approach:** Core guidance + optional verbose troubleshooting (8-10 lines)

#### Verdict: Acceptable with Refinement

Error verbosity is **intentionally educational** due to the complex two-command pattern. This is acceptable, but could be refined:

**Current:** ⚠️ Minor issues - Error handling exceeds YAGNI/KISS but is justified by UX needs
**Recommendation:** Simplify to 8-10 lines, keep core guidance, move detailed troubleshooting to separate help text or docs

---

## Edge Cases and Special Behaviors

### JSON Output Mode

The command implements smart JSON verbosity:
- **Default (`--json`):** Simplified output: `{"context_percentage_used": 7.7}`
- **Verbose (`--json --verbose`):** Complete metrics object

**Verdict:** ✅ Appropriate - Different output for different use cases (scripting vs. detailed analysis)

### Marker Search with Retry Logic

**Source:** Lines 48-146

The marker search includes:
- Exponential backoff retry logic (10 attempts, 100ms to 30s delay)
- Multiple transcript directory search
- Stderr progress messages: `"Waiting for marker to be written to transcript... (attempt 3/10)"`

**Verdict:** ✅ Appropriate - Progress feedback is justified for potentially slow operations

---

## Comparison with Guidelines

### YAGNI (You Aren't Gonna Need It)

The context tracker commands avoid unnecessary features:
- No speculative output (no "future enhancement" hints)
- No debug logs unless user requests verbose mode
- Minimal startup output

**Verdict:** ✅ Passes YAGNI

### KISS (Keep It Simple, Stupid)

**Strengths:**
- Simple two-command workflow (marker → context)
- Clear separation of concerns (generate marker vs. retrieve metrics)
- Single responsibility per command

**Weaknesses:**
- Marker discovery logic is complex but **hidden** from user
- Error messages are comprehensive but somewhat overwhelming

**Verdict:** ⚠️ Passes KISS for user-facing behavior, but implementation is appropriately complex for infrastructure

### Golden Rule: Outcomes, Not Process

The context tracker follows this principle well:

**Process details hidden (good):**
- How the marker is stored
- Transcript directory search algorithm
- JSON parsing of JSONL files
- Token aggregation logic

**Outcomes shown (appropriate):**
- Generated marker (for `session-marker`)
- Context usage metrics (for `context`)
- Structured breakdown of token types
- Clear error messages with remediation

**Verdict:** ✅ Passes - Process details are internal, outcomes are clear

---

## Implementation Architecture Notes

### Why This Design is Appropriate

**Two-command pattern rationale:**
The CLI uses `session-marker` → `context` because:
1. Session markers must be written to the transcript before being searched
2. A single command can't reliably capture its own marker from the transcript
3. Separate commands ensure the marker is logged and available for the second command

This architecture is sound and the UI correctly reflects the workflow.

### Printer Usage

The CLI correctly uses `PrettyPrinter` for formatted output:
- `printer.error()` for error messages (appropriate)
- `print()` for raw stdout (appropriate for machine-readable data)

No `printer.action()` or `printer.info()` calls clutter the output with implementation details.

---

## Recommendations

### Priority 1: Simplify Error Messages (Minor)

**Issue:** The "marker not found" error (18 lines) is well-intentioned but may overwhelm users.

**Recommendation:**
```
Could not find transcript containing marker: SESSION_MARKER_abc12345

The marker may not have been written to the transcript yet.

Correct usage (two separate commands):
  1. sdd session-marker
  2. sdd context --session-marker <marker-from-step-1>

For detailed troubleshooting, see: sdd context --help
```

**Impact:** Reduces error output from 18 to 7 lines, maintains clarity, references help for deep dives

**Effort:** Low (5 lines of code change)

---

### Priority 2: Consider Sensible Defaults

**Current behavior:** When no arguments provided, displays help text.

**Evaluation:** ✅ Appropriate - Utility command with required arguments should show help

---

### Priority 3: Document JSON Verbosity Control

**Current state:** `--verbose` flag controls JSON output detail (simplified vs. complete)

**Evaluation:** ✅ Appropriate - Already documented in comments (lines 445-448)

**Suggestion:** Add example in `--help` output showing both modes

---

## Final Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Human Output (success)** | 13 lines | ✅ Appropriate |
| **Human Output (error)** | ~18 lines | ⚠️ Minor issues |
| **JSON Output (simplified)** | 1 line | ✅ Appropriate |
| **JSON Output (verbose)** | 9 lines | ✅ Appropriate |
| **Implementation details exposed** | 0 lines | ✅ None |
| **YAGNI violations** | 0 | ✅ None |
| **KISS violations** | 0 (user view) | ✅ None |
| **Redundant output** | 1 line (`Total Tokens`) | ⚠️ Minor |

---

## Overall Verdict

### Primary Verdict: ⚠️ **Minor Issues**

**Justification:**

1. **Human-readable output** (success case): ✅ Appropriate
   - Clear structure with logical sections
   - Shows outcomes (context metrics) without implementation details
   - Visual formatting aids readability

2. **JSON output**: ✅ Appropriate
   - Simplified default for scripting
   - Complete verbose output for detailed analysis
   - Smart verbosity control

3. **Error messages**: ⚠️ Slightly too verbose
   - Comprehensive and helpful (good for users)
   - Exceeds YAGNI/KISS for error handling (18 lines could be 8-10)
   - Acceptable because error cases justify extra guidance

4. **Architecture**: ✅ Sound
   - Two-command pattern is appropriate for the use case
   - No implementation details leak into output
   - Clear separation of concerns

### Specific Issues

1. **Redundant output:** "Total Tokens" is already shown as "Context Used" - could consolidate
2. **Error message length:** 18-line error message could be condensed to 8-10 lines with help reference
3. **Transcript filename:** Showing full path is useful for debugging but technically an internal detail

### Recommended Actions

**High Priority:**
- Simplify error messages to 8-10 lines (move detailed troubleshooting to help text)

**Medium Priority:**
- Consider removing "Total Tokens" line if context percentage is the primary metric
- Consider compact/verbose modes for human output (like JSON)

**Low Priority:**
- Document JSON `--verbose` behavior in help text with examples
- Consider grouping error messages by severity (errors vs. warnings vs. tips)

### Why Not "Too Verbose"?

The context tracker avoids the common pitfall of **process verbosity**:
- No "Loading transcript..." messages
- No "Parsing JSONL..." messages
- No "Calculating metrics..." messages
- No "Searching directories..." messages

All internal operations are silent. The output focuses on outcomes and errors.

The error messages are comprehensive by design (not by accident), making this a **minor issue** rather than **too verbose**.

---

## Conclusion

The context tracker commands are **well-designed utility CLIs** that follow YAGNI/KISS principles for user-facing output. The infrastructure and error handling are appropriately detailed. With minor refinement to error message length, this would be an exemplary utility command.

**Recommendation:** Approve with minor enhancements to error message verbosity.

---

## Appendix: Code References

### File: `/src/claude_skills/claude_skills/context_tracker/cli.py`

**Key Functions:**

- `cmd_session_marker()` (lines 286-299): Generates marker - ✅ Minimal output
- `cmd_context()` (lines 302-390): Retrieves metrics - ✅ Appropriate structure
- `format_metrics_human()` (lines 224-255): Human format - ✅ Well-organized
- `format_metrics_json()` (lines 258-283): JSON output - ✅ Complete data
- `find_transcript_by_specific_marker()` (lines 48-146): Complex logic - ✅ Hidden from user

**Output Printer Calls:**

- Line 299: `print(marker)` - ✅ Raw stdout for marker
- Line 390: `print(format_metrics_human(...))` - ✅ Formatted human output
- Line 329-353: Multiple `printer.error()` calls - ⚠️ Verbose error handling
- No `printer.action()` or `printer.info()` calls

**Missing from Output (Good):**

- No "Loading..." messages
- No "Parsing..." messages
- No "Searching..." messages
- No progress dots or spinners
- No internal state transitions
