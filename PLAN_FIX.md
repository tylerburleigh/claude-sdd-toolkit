# Fix Plan: Streaming Progress Events with JSON/Markdown Output Modes

## Problem Statement

### Issue
The `--stream-progress` flag conflicts with `--format json` and `--format markdown` output modes, producing invalid/corrupted output.

When both features are enabled simultaneously:
- Progress events (JSON lines) are emitted to stdout
- Final output (JSON object or markdown) also goes to stdout
- Result: Mixed output that is neither valid JSON nor clean markdown

### Example of Broken Output

**Command:**
```bash
sdd fidelity-review my-spec --phase phase-1 --format json --stream-progress
```

**Actual Output (BROKEN):**
```json
{"type":"cache_check","timestamp":"2025-11-07T10:30:00Z","data":{"cache_hit":false}}
{"type":"ai_consultation","timestamp":"2025-11-07T10:30:01Z","data":{"tools":["gemini","codex"]}}
{"type":"model_response","timestamp":"2025-11-07T10:30:15Z","data":{"tool":"gemini","status":"success"}}
{"type":"model_response","timestamp":"2025-11-07T10:30:18Z","data":{"tool":"codex","status":"success"}}
{
  "spec_id": "my-spec",
  "phase_id": "phase-1",
  "consensus_verdict": "pass",
  "issues_found": [],
  "recommendations": []
}
```

**Problem:** This is NOT valid JSON. It's multiple JSON objects on separate lines, with the final object being the intended output. Standard JSON parsers will fail.

### Impact Assessment

**Severity:** Medium-High
- **Broken:** JSON output with streaming progress
- **Broken:** Markdown output with streaming progress
- **Working:** Text output with streaming progress (no conflict)
- **Working:** All formats without streaming progress

**Affected Users:**
- Automation scripts parsing JSON output
- CI/CD pipelines using `--format json`
- Any user combining `--stream-progress` with non-text formats

**Workaround:** Don't use `--stream-progress` with `--format json` or `--format markdown`

---

## Root Cause Analysis

### Code Location
**File:** `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py`

**Lines 94-98:**
```python
# Create ProgressEmitter if --stream-progress flag is set
progress_emitter = None
if hasattr(args, 'stream_progress') and args.stream_progress:
    progress_emitter = ProgressEmitter(enabled=True, auto_detect_tty=False)
```

**Problem:** ProgressEmitter is created based only on the `--stream-progress` flag, with no consideration for `output_format`.

### Why This Happens

1. **ProgressEmitter** emits newline-delimited JSON events to stdout
2. **Output format selection** (lines 135-142) also writes to stdout
3. **No coordination** between progress events and final output
4. Both systems independently write to stdout without awareness of each other

### Architecture Issue

The current design assumes:
- Progress events are consumed by a separate process (parsing JSONL from stdout)
- Final output goes to stdout after all events are complete

But in reality:
- When `--format json` is used, the consumer expects a single JSON object
- Progress events pollute the output stream
- No clear way for consumer to distinguish events from final output

---

## Current Behavior by Format Mode

### Text Mode (Default)
**Status:** ✅ Works correctly

**Without `--stream-progress`:**
- Rich UI output with colors, panels, progress bars
- Human-readable format

**With `--stream-progress`:**
- Progress events to stdout (JSONL)
- Rich UI output also to stdout
- No conflict because text output is clearly distinguishable from JSON events

### JSON Mode
**Status:** ❌ Broken with `--stream-progress`

**Without `--stream-progress`:**
```json
{
  "spec_id": "my-spec",
  "consensus_verdict": "pass"
}
```
✅ Valid JSON

**With `--stream-progress`:**
```
{"type":"cache_check",...}
{"type":"model_response",...}
{"spec_id":"my-spec",...}
```
❌ Invalid JSON (multiple objects, not an array)

### Markdown Mode
**Status:** ❌ Broken with `--stream-progress`

**Without `--stream-progress`:**
```markdown
# Fidelity Review Report
...
```
✅ Clean markdown

**With `--stream-progress`:**
```
{"type":"cache_check",...}
{"type":"model_response",...}
# Fidelity Review Report
...
```
❌ JSON events corrupt markdown

---

## Proposed Solutions

### Option 1: Emit Progress to stderr (RECOMMENDED)

**Approach:** Redirect progress events to stderr when output format is json/markdown

**Pros:**
- Clean separation: progress → stderr, output → stdout
- Both features work simultaneously
- Standard Unix practice (progress/diagnostics → stderr, data → stdout)
- No breaking changes for text mode

**Cons:**
- Requires consumers to read from both streams if they want progress
- stderr might be ignored/discarded in some environments

**Implementation:**
```python
# In cli.py
if hasattr(args, 'stream_progress') and args.stream_progress:
    # Determine output stream based on format
    output_format = args.format if hasattr(args, 'format') else 'text'
    progress_stream = sys.stderr if output_format in ['json', 'markdown'] else sys.stdout
    progress_emitter = ProgressEmitter(
        output=progress_stream,
        enabled=True,
        auto_detect_tty=False
    )
```

**Files to modify:**
1. `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py` - Add format-aware stream selection
2. `src/claude_skills/claude_skills/common/progress.py` - Ensure ProgressEmitter accepts output stream
3. Update documentation to note stderr usage for non-text modes

---

### Option 2: Disable --stream-progress for json/markdown

**Approach:** Raise error or warning when incompatible flags are used together

**Pros:**
- Simple to implement
- Clear error message guides users
- No risk of corrupted output

**Cons:**
- Removes functionality (users can't have both)
- Less flexible
- Requires users to choose between features

**Implementation:**
```python
# In cli.py
if hasattr(args, 'stream_progress') and args.stream_progress:
    output_format = args.format if hasattr(args, 'format') else 'text'
    if output_format in ['json', 'markdown']:
        ui.print_error(
            f"Error: --stream-progress is not compatible with --format {output_format}\n"
            f"Progress events would corrupt {output_format} output.\n"
            f"Choose one: remove --stream-progress OR use --format text"
        )
        return 1
    progress_emitter = ProgressEmitter(enabled=True, auto_detect_tty=False)
```

**Files to modify:**
1. `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py` - Add validation

---

### Option 3: Use JSONL Format for All Output

**Approach:** When `--stream-progress` is enabled with `--format json`, emit final output as another event

**Pros:**
- Consistent format throughout (newline-delimited JSON)
- Parseable by JSONL consumers
- Clear distinction between events and final result

**Cons:**
- Breaking change for JSON output format
- Requires special handling by consumers
- Non-standard for most JSON use cases

**Implementation:**
```python
# In cli.py _output_json()
if progress_emitter:
    # Emit final result as an event
    progress_emitter.emit({
        "type": "result",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "spec_id": args.spec_id,
            "consensus_verdict": consensus.verdict,
            # ... rest of output
        }
    })
else:
    # Emit as single JSON object (current behavior)
    json.dump(output_data, sys.stdout, indent=2)
```

**Files to modify:**
1. `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py` - Update `_output_json()` and `_output_markdown()`
2. Documentation - Explain JSONL format when streaming

---

## Recommended Fix: Option 1 (stderr for progress)

### Why This Approach?

1. **Standard Practice:** stderr for progress/diagnostics, stdout for data
2. **No Breaking Changes:** Existing behavior preserved
3. **Full Functionality:** Both features work together
4. **Minimal Code Changes:** Small modification to stream selection
5. **Clear Separation:** Easy for consumers to handle

### Implementation Plan

#### Phase 1: Update ProgressEmitter Stream Selection

**File:** `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py`

**Changes:**
```python
# Before (lines 94-98):
progress_emitter = None
if hasattr(args, 'stream_progress') and args.stream_progress:
    progress_emitter = ProgressEmitter(enabled=True, auto_detect_tty=False)

# After:
progress_emitter = None
if hasattr(args, 'stream_progress') and args.stream_progress:
    # Determine output stream based on format mode
    output_format = args.format if hasattr(args, 'format') else 'text'

    # For json/markdown modes, emit progress to stderr to avoid corrupting stdout
    # For text mode, emit to stdout (existing behavior)
    progress_stream = sys.stderr if output_format in ['json', 'markdown'] else sys.stdout

    progress_emitter = ProgressEmitter(
        output=progress_stream,
        enabled=True,
        auto_detect_tty=False
    )
```

#### Phase 2: Verify ProgressEmitter Supports Custom Stream

**File:** `src/claude_skills/claude_skills/common/progress.py`

**Check:** Ensure `ProgressEmitter.__init__()` accepts `output` parameter (lines 296-346)

Current implementation:
```python
def __init__(self, output: Optional[TextIO] = None, ...):
    self.output = output or sys.stdout
```

✅ Already supports custom stream - no changes needed

#### Phase 3: Update Documentation

**Files to update:**
1. `skills/sdd-fidelity-review/SKILL.md`
2. CLI help text in `cli.py`

**Add note:**
```markdown
### Streaming Progress Events

The `--stream-progress` flag emits real-time progress events as newline-delimited JSON.

**Output Stream Behavior:**
- **Text mode** (`--format text`): Events emitted to stdout
- **JSON mode** (`--format json`): Events emitted to stderr (to keep stdout clean for JSON output)
- **Markdown mode** (`--format markdown`): Events emitted to stderr (to keep stdout clean for markdown output)

**Example:**
```bash
# JSON output with progress to stderr
sdd fidelity-review my-spec --format json --stream-progress > output.json 2> progress.jsonl

# Text output with progress to stdout
sdd fidelity-review my-spec --format text --stream-progress > combined.txt
```
```

#### Phase 4: Add CLI Help Text

**File:** `src/claude_skills/claude_skills/sdd_fidelity_review/cli.py`

Update argument help:
```python
parser.add_argument(
    '--stream-progress',
    action='store_true',
    help='Emit real-time progress events as newline-delimited JSON. '
         'Events go to stderr in json/markdown modes, stdout in text mode.'
)
```

---

## Implementation Steps

### Step 1: Code Changes
- [ ] Update `cli.py` to select output stream based on format mode
- [ ] Verify `ProgressEmitter` accepts custom stream (already done)
- [ ] Add import for `sys` if not already present

### Step 2: Testing
- [ ] Test text mode + streaming (should work as before)
- [ ] Test json mode + streaming (progress to stderr, json to stdout)
- [ ] Test markdown mode + streaming (progress to stderr, md to stdout)
- [ ] Test without streaming (should work as before)

### Step 3: Documentation
- [ ] Update SKILL.md with stream behavior notes
- [ ] Update CLI help text
- [ ] Add examples showing stderr redirection

### Step 4: Integration Tests
- [ ] Add test case for json + streaming
- [ ] Add test case for markdown + streaming
- [ ] Verify stderr/stdout separation

---

## Testing Plan

### Test Cases

#### TC1: JSON Output with Streaming Progress
```bash
sdd fidelity-review my-spec --format json --stream-progress > output.json 2> progress.jsonl
```

**Expected:**
- `output.json` contains valid JSON (final result only)
- `progress.jsonl` contains newline-delimited JSON events
- Both files are independently parseable

**Validation:**
```python
# Validate output.json
with open('output.json') as f:
    result = json.load(f)  # Should not raise
    assert 'spec_id' in result

# Validate progress.jsonl
with open('progress.jsonl') as f:
    events = [json.loads(line) for line in f]
    assert all(e.get('type') in ['cache_check', 'model_response', 'complete'] for e in events)
```

#### TC2: Text Output with Streaming Progress
```bash
sdd fidelity-review my-spec --format text --stream-progress > combined.txt
```

**Expected:**
- `combined.txt` contains both progress events and text output
- Events are distinguishable (JSON lines vs text)

#### TC3: JSON Output without Streaming
```bash
sdd fidelity-review my-spec --format json > output.json
```

**Expected:**
- `output.json` contains valid JSON
- No progress events
- Behavior unchanged from before fix

#### TC4: Markdown Output with Streaming
```bash
sdd fidelity-review my-spec --format markdown --stream-progress > output.md 2> progress.jsonl
```

**Expected:**
- `output.md` contains clean markdown
- `progress.jsonl` contains progress events
- No JSON in markdown output

### Integration Test Implementation

**File:** `tests/integration/test_streaming_format_modes.py`

```python
import json
import subprocess
import sys
from pathlib import Path

def test_json_output_with_streaming_progress(test_spec):
    """Test that JSON output is clean when streaming progress to stderr."""

    result = subprocess.run(
        ['sdd', 'fidelity-review', test_spec, '--format', 'json', '--stream-progress'],
        capture_output=True,
        text=True
    )

    # Validate stdout contains valid JSON
    output = json.loads(result.stdout)
    assert 'spec_id' in output
    assert 'consensus_verdict' in output

    # Validate stderr contains progress events
    events = [json.loads(line) for line in result.stderr.strip().split('\n') if line]
    assert len(events) > 0
    assert all('type' in event for event in events)


def test_text_output_with_streaming_progress(test_spec):
    """Test that text output works as before with streaming."""

    result = subprocess.run(
        ['sdd', 'fidelity-review', test_spec, '--format', 'text', '--stream-progress'],
        capture_output=True,
        text=True
    )

    # Both progress and output should be in stdout for text mode
    assert result.returncode == 0
    assert len(result.stdout) > 0


def test_json_output_without_streaming(test_spec):
    """Test that JSON output works without streaming (baseline)."""

    result = subprocess.run(
        ['sdd', 'fidelity-review', test_spec, '--format', 'json'],
        capture_output=True,
        text=True
    )

    # Validate clean JSON output
    output = json.loads(result.stdout)
    assert 'spec_id' in output

    # No events in stderr
    assert result.stderr == '' or 'ERROR' not in result.stderr
```

---

## Backward Compatibility Considerations

### Breaking Changes
**None** - This fix is backward compatible:

1. **Text mode behavior unchanged:**
   - Progress events still go to stdout
   - Existing scripts continue to work

2. **JSON/markdown without streaming unchanged:**
   - Output still goes to stdout
   - No progress events to interfere

3. **New behavior only affects broken combinations:**
   - `--format json --stream-progress` now works (was broken)
   - `--format markdown --stream-progress` now works (was broken)

### Migration Required
**None** - No user action required

### Deprecations
**None** - No features deprecated

---

## Related Issues

### Issue: Cache Works Correctly (No Fix Needed)
- Cache is format-agnostic ✅
- Cache hits skip AI calls in all modes ✅
- No interaction with streaming progress ✅

### Issue: UI Progress Bars vs ProgressEmitter
- UI progress (RichUi/PlainUi) is separate from ProgressEmitter
- No conflict between visual progress and event streaming
- Both can coexist (though rarely used together)

---

## Future Enhancements

### Consider: Unified Progress System
Currently there are two progress systems:
1. **Visual progress:** RichUi/PlainUi progress bars
2. **Event streaming:** ProgressEmitter JSON events

**Potential improvement:** Unify these systems so:
- Visual progress automatically emits events
- Single progress API for all modes
- Consistent behavior across format modes

**Complexity:** Medium-High
**Priority:** Low (current fix addresses immediate issue)

---

## Timeline Estimate

**Complexity:** Low
**Effort:** 2-3 hours
**Risk:** Low (small, targeted change)

**Breakdown:**
- Code changes: 30 minutes
- Testing: 1 hour
- Documentation: 30 minutes
- Integration tests: 1 hour

---

## Approval & Sign-off

- [ ] Technical review
- [ ] Test coverage verified
- [ ] Documentation updated
- [ ] User acceptance (example testing)
- [ ] Ready for implementation

---

*This fix plan created: 2025-11-07*
*Target implementation: Phase 6 (TUI/Output Refinement)*
