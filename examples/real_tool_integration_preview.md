# Real AI Tool Integration Preview

This document shows what the TUI progress feedback will look like when integrated with actual AI tool execution.

## Current State (Before TUI Integration)

When you run a command like `sdd plan-review` that consults multiple AI models, you see minimal feedback:

```bash
$ sdd plan-review my-spec-001.json

Sending architecture review to 2 external AI model(s)...
   ✓ gemini completed (45.2s)
   ✓ codex completed (52.1s)

Review Complete
```

**Issues:**
- No real-time feedback during execution
- Can't see which tool is running
- No progress indication for long-running operations (90-600s)
- No visibility into parallel execution

---

## Future State (With TUI Integration - Phase 4)

### Example 1: Single Tool Consultation

**Command:** `sdd fidelity-review my-spec-001.json task-2-3`

**Display:**

```
╔══════════════════════ Fidelity Review ═══════════════════════╗
║                                                              ║
║  Consulting AI for implementation review...                 ║
║                                                              ║
║  ⏳ gemini (gemini-2.5-pro)                                 ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.2s / 120s ║
║                                                              ║
║  Status: Analyzing code implementation...                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Then updates to:**

```
╔══════════════════════ Fidelity Review ═══════════════════════╗
║                                                              ║
║  ✅ Review Complete                                         ║
║                                                              ║
║  ✓ gemini (gemini-2.5-pro)                                  ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.2s        ║
║                                                              ║
║  Response: 2,048 characters                                 ║
║  Identified 3 deviations from spec                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Example 2: Parallel Multi-Tool Consultation

**Command:** `sdd plan-review my-spec-001.json --review-type architecture`

**Display (Real-time progress):**

```
╔════════════════════ Architecture Review ════════════════════╗
║                                                              ║
║  Consulting 3 AI models in parallel...                      ║
║                                                              ║
║  Overall Progress: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/3 (33%)  ║
║                                                              ║
║  ✓ cursor-agent (cheetah)        ━━━━━━━━━━━━━━ 38.2s      ║
║  ⏳ gemini (gemini-2.5-pro)      ━━━━━━━━━━━━━━ 45.8s / 600s║
║  ⏳ codex (gpt-5-codex)          ━━━━━━━━━━━━━━ 47.1s / 600s║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Then updates as each completes:**

```
╔════════════════════ Architecture Review ════════════════════╗
║                                                              ║
║  ✅ Review Complete                                         ║
║                                                              ║
║  Overall Progress: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/3 (100%) ║
║                                                              ║
║  ✓ cursor-agent (cheetah)        ━━━━━━━━━━━━━━ 38.2s      ║
║  ✓ gemini (gemini-2.5-pro)       ━━━━━━━━━━━━━━ 52.7s      ║
║  ✓ codex (gpt-5-codex)           ━━━━━━━━━━━━━━ 61.3s      ║
║                                                              ║
║  Summary:                                                    ║
║    • 3/3 models responded successfully                      ║
║    • Total time: 61.3s (parallel execution)                 ║
║    • Consensus reached on 8/10 recommendations              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Example 3: Test Execution with Consultation

**Command:** `run-tests --consult-on-failure`

**Display when tests fail:**

```
╔═══════════════════ Test Execution ════════════════════╗
║                                                        ║
║  Running pytest...                                     ║
║                                                        ║
║  ⏳ tests/unit/test_ai_tools.py                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.3s / 300s ║
║                                                        ║
║  Status: 23 passed, 1 failed                          ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

❌ Test failed: test_timeout_handling

Auto-triggering AI consultation for failure type: exception

╔════════════════ AI Consultation: Test Failure ═══════════════╗
║                                                               ║
║  Consulting 2 AI models for test failure analysis...         ║
║                                                               ║
║  Overall Progress: ━━━━━━━━━━━━━━━━━━━━━━━━ 0/2 (0%)        ║
║                                                               ║
║  ⏳ gemini (gemini-2.5-pro)    ━━━━━━━━━━━━━━ 5.2s / 90s    ║
║  ⏳ codex (gpt-5-codex)        ━━━━━━━━━━━━━━ 5.3s / 90s    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

### Example 4: Timeout Scenario

**Display when tool times out:**

```
╔═══════════════════ Code Documentation ═══════════════════╗
║                                                           ║
║  Generating codebase documentation...                    ║
║                                                           ║
║  ⏰ gemini (gemini-2.5-pro)                              ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 600.0s / 600s   ║
║                                                           ║
║  Status: ⚠️  Timeout - retrying with different model... ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Retry 1/3: Switching to codex

╔═══════════════════ Code Documentation ═══════════════════╗
║                                                           ║
║  Generating codebase documentation...                    ║
║                                                           ║
║  ⏳ codex (gpt-5-codex)                                  ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.2s / 600s    ║
║                                                           ║
║  Status: Analyzing Python files...                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Benefits of TUI Integration

### User Experience Improvements

1. **Real-Time Feedback**
   - Users see progress immediately
   - No "is it frozen?" moments
   - Clear indication of which tool is running

2. **Better Time Awareness**
   - Elapsed time visible
   - Timeout countdown for long operations
   - Realistic expectations for completion

3. **Parallel Execution Visibility**
   - See all tools running concurrently
   - Individual progress per tool
   - Aggregate progress tracking

4. **Error Context**
   - Clear visual indication of failures
   - Timeout vs error vs not-found distinction
   - Retry attempts clearly shown

5. **Professional Appearance**
   - Polished TUI with Rich library
   - Consistent design across all operations
   - Better integration with terminal workflows

---

## Implementation Timeline

### Phase 4 (Current Implementation Priority)

**Week 1:**
- ✅ Progress context managers created (task-3-2-1)
- ⏳ Integrate with execute_tool() (task-3-2-2 → task-3-4)
- ⏳ Implement RichProgressCallback
- ⏳ Add to execute_tools_parallel()

**Week 2:**
- ⏳ Integrate with verification tasks
- ⏳ Add to consultation modules (run-tests, code-doc, etc.)
- ⏳ Testing and refinement

### Phase 5 (Advanced Features)

- Real-time periodic updates during subprocess execution
- Cancellation support with Ctrl+C handling
- Adaptive update frequency based on timeout
- Output streaming for immediate feedback

---

## Technical Details

### Integration Points

**Current implementation provides:**
- `ProgressCallback` protocol (6 methods)
- `ai_consultation_progress()` context manager
- `batch_consultation_progress()` context manager
- `NoOpProgressCallback` for graceful degradation

**Next steps (Phase 4):**
- Modify `execute_tool()` to accept `progress_callback` parameter
- Modify `execute_tools_parallel()` to accept `progress_callback` parameter
- Create `RichProgressCallback` implementation
- Wire up callbacks in CLI tools (run-tests, sdd-plan-review, etc.)

### Backward Compatibility

All changes are backward compatible:
- `progress_callback` parameter is optional (defaults to None)
- When None, uses NoOpProgressCallback (no-op)
- Existing code works without changes
- New code opts-in by passing callback

---

## Demo Scripts Available

1. **examples/tui_progress_demo.py**
   - Simple print-based callback demo
   - Shows all lifecycle hooks
   - Demonstrates error handling

2. **examples/rich_tui_preview.py**
   - Full Rich TUI visualization
   - Progress bars, spinners, panels
   - Status tables and multi-progress

Run either script to see the progress feedback in action!

```bash
# Simple demo
python3 examples/tui_progress_demo.py

# Rich TUI demo (requires: pip install rich)
python3 examples/rich_tui_preview.py
```
