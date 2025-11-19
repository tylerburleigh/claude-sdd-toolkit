# Spec Validation Count Mismatch Analysis

## Executive Summary

An AI agent encountered persistent validation errors where parent tasks showed `completed_tasks > 0` while all their children were `pending`. Multiple fix attempts (`sdd fix`, `sdd reconcile-state`, `sdd apply-modifications`) failed to resolve the issue. Root cause: `recalculate_progress()` has logic that preserves incorrect counts when parent nodes have `completed_at` metadata, and no tool provides a direct way to fix count mismatches.

## Problem Statement

### Validation Errors Encountered

```
❌ ERROR: Node 'task-1-1-1' completed_tasks (1) doesn't match sum of children (0)
❌ ERROR: Node 'task-1-1-4' completed_tasks (2) doesn't match sum of children (0)
```

### Actual State

- **task-1-1-1**: 
  - `completed_tasks = 1`
  - `status = "completed"`
  - Has `metadata.completed_at` timestamp
  - Child: `verify-1-1-1-2` (status: `pending`, `completed_tasks = 0`)

- **task-1-1-4**:
  - `completed_tasks = 2`
  - `status = "completed"`
  - Has `metadata.completed_at` timestamp
  - Children: `verify-1-1-4-1` and `verify-1-1-4-2` (both status: `pending`, `completed_tasks = 0`)

### Expected State

Both parent tasks should have `completed_tasks = 0` since none of their children are completed.

## Root Cause Analysis

### Primary Root Cause

The issue stems from **`recalculate_progress()` logic in `src/claude_skills/claude_skills/common/progress.py`** (lines 82-91):

```python
# Handle manually-completed tasks with children
if node.get("metadata", {}).get("completed_at") and node.get("children"):
    node["status"] = "completed"
    # Update children's completion counts if needed
    if node.get("children"):
        # Mark all children as completed to maintain consistency
        # This happens when a parent is manually marked complete
        # but children weren't individually marked
        total = node.get("total_tasks", 0)
        node["completed_tasks"] = total  # ⚠️ PROBLEM: Sets to total, not actual completed
    # Don't return early - allow parent chain to update
```

**The Problem**: When a parent node has `completed_at` metadata and children, this code sets `completed_tasks = total_tasks` regardless of whether children are actually completed. This creates a mismatch when:
1. A parent task is manually marked complete (gets `completed_at` timestamp)
2. Children remain pending
3. `recalculate_progress()` runs and preserves the incorrect count

### Why This Happened

The parent tasks (`task-1-1-1` and `task-1-1-4`) were likely marked complete before their verification children were completed. The `completed_at` timestamp was set, but the children remained pending. The validation correctly detects the mismatch, but the fix tools can't resolve it because `recalculate_progress()` preserves the incorrect count.

## Tool Failure Analysis

### 1. `sdd fix` Command

**What it does**: 
- Collects auto-fixable errors via `collect_fix_actions()`
- For count mismatches, creates a `_build_counts_action` that calls `recalculate_progress()`
- Applies fixes and saves the spec

**Why it failed**:
- `recalculate_progress()` encounters the `completed_at` check (line 82)
- Sets `completed_tasks = total_tasks` instead of calculating from children
- The count mismatch persists

**Evidence from transcript**:
```
sdd fix opencode-provider-2025-11-18-001
# Exit code 2
{"spec_id":"opencode-provider-2025-11-18-001","applied_action_count":10,"post_status":"errors"}
```

### 2. `sdd reconcile-state` Command

**What it does**:
- Fixes status inconsistencies (status vs `completed_at` timestamp)
- Calls `recalculate_progress()` at the end to update counts

**Why it failed**:
- Only fixes status mismatches, not count mismatches
- The final `recalculate_progress()` call has the same issue as `sdd fix`
- Returns empty JSON `{}` when no status fixes are needed, giving no indication it didn't fix counts

**Evidence from transcript**:
```
sdd reconcile-state opencode-provider-2025-11-18-001
# Returns: {}
# Validation still fails
```

**Critical Flaw**: The command name suggests it reconciles state, but it only reconciles status, not counts. This is misleading.

### 3. `sdd apply-modifications` Command

**What the agent tried**:
```json
{
  "modifications": [
    {
      "action": "update_metadata",
      "target": {"task_id": "task-1-1-1"},
      "changes": {"completed_tasks": 0}
    }
  ]
}
```

**Why it failed**:
1. **Wrong operation name**: Should be `"operation": "update_metadata"`, not `"action": "update_metadata"`
2. **Wrong target format**: Should use `"task_id"` or `"node_id"` at top level, not nested in `"target"`
3. **Wrong field**: `completed_tasks` is not a metadata field - it's a top-level node field
4. **Protected field**: `completed_tasks` is explicitly protected and cannot be updated via `update_node_field()` (see `modification.py` line 481)

**Evidence from transcript**:
```
sdd apply-modifications opencode-provider-2025-11-18-001 --from /tmp/fix_counts.json
# Exit code 1
{"spec_id":"opencode-provider-2025-11-18-001","success":false,"total_operations":2,"successful_operations":0,"failed_operations":2}
```

## Tool Design Flaws

### 1. `recalculate_progress()` Logic Flaw

**Location**: `src/claude_skills/claude_skills/common/progress.py:82-91`

**Problem**: The special case for manually-completed tasks with children sets `completed_tasks = total_tasks` instead of calculating from actual child completion status.

**Impact**: Makes count mismatches unfixable when parents have `completed_at` timestamps.

**Recommended Fix**: Change the logic to:
```python
# Handle manually-completed tasks with children
if node.get("metadata", {}).get("completed_at") and node.get("children"):
    # Calculate actual completed count from children
    actual_completed = sum(
        hierarchy.get(child_id, {}).get("completed_tasks", 0)
        for child_id in node.get("children", [])
    )
    node["completed_tasks"] = actual_completed
    
    # If all children are completed, status is correct
    # If not all children are completed, this is inconsistent - 
    # remove completed_at or mark children complete
    if actual_completed < node.get("total_tasks", 0):
        # Inconsistent state: parent marked complete but children aren't
        # Option 1: Remove completed_at to allow recalculation
        # Option 2: Mark all children as completed
        # For now, we'll remove completed_at to allow proper recalculation
        node["metadata"].pop("completed_at", None)
        node["status"] = "in_progress" if actual_completed > 0 else "pending"
```

### 2. `reconcile-state` Scope Mismatch

**Location**: `src/claude_skills/claude_skills/sdd_update/validation.py:237-336`

**Problem**: Command name suggests it reconciles all state inconsistencies, but it only reconciles status vs timestamp mismatches, not count mismatches.

**Impact**: Misleading name causes agents to try it for count issues, wasting time.

**Recommended Fix**: 
- Rename to `reconcile-status` to reflect actual scope, OR
- Expand scope to include count reconciliation by:
  1. Detecting count mismatches
  2. Removing `completed_at` from parents when children aren't complete
  3. Calling `recalculate_progress()` after fixes

### 3. No Direct Count Fix Mechanism

**Problem**: There's no command or modification operation that can directly fix count mismatches. All tools rely on `recalculate_progress()`, which has the flaw above.

**Impact**: Count mismatches become unfixable without manual JSON editing (which is blocked by hooks).

**Recommended Fix**: Add a new command `sdd fix-counts` that:
1. Detects count mismatches
2. For each mismatch:
   - If parent has `completed_at` but children aren't complete: remove `completed_at` and recalculate
   - Otherwise: recalculate from children
3. Validates the fix worked

### 4. `apply-modifications` Protected Fields

**Location**: `src/claude_skills/claude_skills/sdd_spec_mod/modification.py:481`

**Problem**: `completed_tasks` is protected and cannot be updated, even when it's incorrect.

**Impact**: No programmatic way to fix count mismatches via modifications API.

**Recommended Fix**: Allow updating `completed_tasks` when:
- The update matches the calculated value from children, OR
- A special flag `force_recalculate: true` is set (which triggers recalculation instead of direct update)

### 5. Poor Error Messages

**Problem**: When `sdd fix` applies actions but validation still fails, the error message doesn't explain why:
```
{"spec_id":"...","applied_action_count":10,"post_status":"errors"}
```

**Impact**: Agents can't understand why the fix didn't work.

**Recommended Fix**: Include validation errors in the response:
```json
{
  "spec_id": "...",
  "applied_action_count": 10,
  "post_status": "errors",
  "remaining_errors": [
    "Node 'task-1-1-1' completed_tasks (1) doesn't match sum of children (0)"
  ],
  "explanation": "Some errors could not be auto-fixed. Run 'sdd report' for details."
}
```

## Recommended Improvements

### Priority 1: Fix `recalculate_progress()` Logic

**File**: `src/claude_skills/claude_skills/common/progress.py`

**Change**: Modify the manually-completed task handling to calculate from actual children instead of assuming all children are complete.

**Impact**: Fixes the root cause, making count mismatches fixable via `sdd fix`.

### Priority 2: Enhance `reconcile-state` Command

**File**: `src/claude_skills/claude_skills/sdd_update/validation.py`

**Change**: Expand scope to detect and fix count mismatches:
1. Detect parents with `completed_at` but incomplete children
2. Remove `completed_at` or mark children complete (user choice)
3. Recalculate counts

**Impact**: Makes `reconcile-state` live up to its name.

### Priority 3: Add `sdd fix-counts` Command

**New file**: `src/claude_skills/claude_skills/sdd_update/counts.py`

**Purpose**: Dedicated command for fixing count mismatches with clear error messages and fix strategies.

**Impact**: Provides a reliable tool for count issues.

### Priority 4: Improve Error Messages

**Files**: `src/claude_skills/claude_skills/sdd_validate/cli.py`, `src/claude_skills/claude_skills/sdd_validate/fix.py`

**Change**: Include remaining validation errors in fix command output.

**Impact**: Helps agents understand why fixes didn't work.

### Priority 5: Document Count Mismatch Resolution

**File**: `docs/` or `analysis/`

**Content**: Guide for resolving count mismatches, explaining:
- Why they occur
- Which tools to use
- When manual intervention is needed

**Impact**: Reduces agent confusion.

## Workaround for Current Issue

Until fixes are implemented, the workaround is:

1. **Remove `completed_at` timestamps** from parent tasks:
   ```bash
   # Use sdd update-frontmatter or direct JSON edit (if hooks allow)
   # Remove metadata.completed_at from task-1-1-1 and task-1-1-4
   ```

2. **Run `sdd fix`** to recalculate counts:
   ```bash
   sdd fix opencode-provider-2025-11-18-001
   ```

3. **Verify**:
   ```bash
   sdd validate opencode-provider-2025-11-18-001
   ```

However, this workaround may not be feasible if hooks prevent direct JSON editing and no command exists to remove `completed_at` metadata.

## Conclusion

The count mismatch issue exposes multiple tool design flaws:
1. `recalculate_progress()` preserves incorrect counts for manually-completed parents
2. `reconcile-state` doesn't actually reconcile counts
3. No direct mechanism exists to fix count mismatches
4. Error messages don't explain fix failures

The highest-impact fix is correcting `recalculate_progress()` logic, which would make `sdd fix` work correctly for count mismatches.
