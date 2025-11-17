# Proposal: Enhance `sdd fix` Robustness for Missing Dependencies

## 1. The Problem

The `sdd fix` command, while powerful, exhibits inconsistency and potential brittleness when attempting to repair bidirectional dependency errors in SDD specs. The core issue arises when a node within the spec's hierarchy is entirely missing the `dependencies` object.

Currently, the auto-fix logic in `_build_bidirectional_deps_action` uses `setdefault("dependencies", {})` to ensure the object exists. This creates an empty dictionary (`{}`). While the subsequent code uses `setdefault` again for `blocks` and `blocked_by` (which technically works), this approach is inconsistent with the pattern used in `_build_missing_deps_structure_action`, which initializes the complete dependencies structure upfront.

**Example Scenario:**
```json
{
  "hierarchy": {
    "task-1": {
      "id": "task-1",
      "type": "task",
      "dependencies": {
        "blocks": ["task-2"]
      }
    },
    "task-2": {
      "id": "task-2",
      "type": "task"
      // Missing dependencies object entirely
    }
  }
}
```

When `sdd fix` attempts to synchronize the bidirectional relationship, it creates an empty `dependencies: {}` for `task-2`, then uses `setdefault` to add `blocks` and `blocked_by` piecemeal. While this works, it's inconsistent with the established pattern and doesn't create the complete structure that validation expects (including the `depends` field).

Additionally, if `dependencies` exists but is malformed (e.g., `null` or a non-dict type), the current code may not handle it gracefully.

## 2. The Proposed Solution

To address this, I propose a modification to the `_build_bidirectional_deps_action` function located in `src/claude_skills/sdd_validate/fix.py` (lines 685-687).

The solution aligns with the pattern used in `_build_missing_deps_structure_action` (lines 727-732) by initializing the `dependencies` object with the complete, required structure whenever it is found to be missing, malformed, or incomplete.

### Current Code:
```python
# Ensure dependencies dicts exist
blocker_deps = blocker.setdefault("dependencies", {})
blocked_deps = blocked.setdefault("dependencies", {})
```

### Proposed Change (Robust Solution):
```python
# Ensure dependencies dicts exist with complete structure
# Handle missing, malformed, AND partial dependencies
for node in [blocker, blocked]:
    if not isinstance(node.get("dependencies"), dict):
        # Replace missing/malformed with complete structure
        node["dependencies"] = {"blocks": [], "blocked_by": [], "depends": []}
    else:
        # Ensure all required fields exist in existing dict
        node["dependencies"].setdefault("blocks", [])
        node["dependencies"].setdefault("blocked_by", [])
        node["dependencies"].setdefault("depends", [])

blocker_deps = blocker["dependencies"]
blocked_deps = blocked["dependencies"]
```

**Why This Solution is Better:**

This approach handles ALL edge cases that the original proposal missed:

1. **Missing dependencies** (`"dependencies"` key doesn't exist)
   - Creates complete structure: `{"blocks": [], "blocked_by": [], "depends": []}`

2. **Malformed dependencies** (`dependencies: null` or non-dict type)
   - Replaces with complete structure

3. **Partial dependencies** (e.g., `{"blocks": ["task-1"]}`)
   - Adds missing `blocked_by` and `depends` fields
   - This is the critical case that simple `setdefault` misses

4. **Complete dependencies** (all fields present)
   - No-op, preserves existing structure

5. **Empty dependencies** (`{}`)
   - Adds all three required fields

**Improvements over original approaches:**
- **More robust** than the "simpler" approach (which fails on partial structures)
- **More efficient** than the first proposal (eliminates redundant `setdefault` after `isinstance` check)
- **Consistent** with `_build_missing_deps_structure_action` pattern
- **Defensive** like other parts of the codebase (e.g., `dependency_analysis.py`)

## 3. Relationship to Existing Code

This proposal aligns with the existing `_build_missing_deps_structure_action` function (lines 709-742), which already creates the complete dependencies structure:

```python
if not isinstance(node.get("dependencies"), dict):
    node["dependencies"] = {
        "blocks": [],
        "blocked_by": [],
        "depends": [],
    }
```

By adopting the same pattern in `_build_bidirectional_deps_action`, we ensure consistent behavior across all dependency-related fix actions.

## 4. Existing Safeguards and Their Limitations

The current implementation has a **fragile safeguard** based on execution order. In `fix.py` (lines 66-82), the fix action builders execute in this sequence:

```python
# Position 14
(_build_bidirectional_deps_action, "dependency"),
# Position 15
(_build_missing_deps_structure_action, "dependency"),
```

This means `_build_missing_deps_structure_action` runs **immediately after** `_build_bidirectional_deps_action`. In theory, this could catch incomplete structures created by the bidirectional action.

**However, this safeguard is unreliable because:**

1. **Incomplete structures pass validation**: If `_build_bidirectional_deps_action` creates `{"blocks": [], "blocked_by": []}`, the `isinstance(deps, dict)` check in `_build_missing_deps_structure_action` returns `True`, so it won't add the missing `depends` field.

2. **Undocumented dependency**: The execution order is not documented as a deliberate safeguard, making it fragile and prone to breaking during refactoring.

3. **Inconsistent with defensive patterns**: Other parts of the codebase (e.g., `dependency_analysis.py` lines 60-66, 109-114) use defensive `isinstance` checks, suggesting that each function should ensure complete structures rather than relying on execution order.

**Validation Expectations**: The validation code in `hierarchy_validation.py` (lines 401-409) explicitly checks all three dependency fields:
```python
for dep_key in ['blocks', 'blocked_by', 'depends']:
    if dep_key in deps and not isinstance(deps[dep_key], list):
        errors.append(...)
```

This confirms that the complete structure is expected throughout the codebase.

## 5. Edge Cases Analysis

The original proposal identified the main issue but overlooked several edge cases:

1. **Partial Dependencies**: What if `dependencies` exists as `{"blocks": ["task-1"]}` but is missing `blocked_by` and `depends`? The simpler approach using `setdefault` wouldn't add the missing fields to an existing dict.

2. **Malformed Dependencies**: If `dependencies` is `null` or a non-dict type, only the robust approach with `isinstance` checks would handle it properly.

3. **Both Nodes Missing Dependencies**: When both the blocker and blocked nodes lack dependency structures simultaneously, the fix must handle both correctly.

4. **Empty vs Missing**: There's a difference between `dependencies: {}` (empty dict) and no `dependencies` key at all. Both should result in the complete structure.

## 6. Testing Recommendations

To validate this change, the following test cases should be added to `claude_skills/tests/unit/test_sdd_validate/test_fix.py`:

### Test Case 1: Missing Dependencies Structure
```python
def test_build_bidirectional_deps_action_missing_dependencies():
    """Test that bidirectional deps action handles missing dependencies structure."""
    error = EnhancedError(
        message="'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Sync bidirectional dependency",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": {"blocks": ["task-2"]},
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                # Missing dependencies object
            },
        }
    }

    action = _build_bidirectional_deps_action(error, spec_data)
    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": {"blocks": ["task-2"]},
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
            },
        }
    }
    action.apply(test_data)

    # Verify complete structure was created
    deps = test_data["hierarchy"]["task-2"]["dependencies"]
    assert isinstance(deps, dict)
    assert "blocks" in deps
    assert "blocked_by" in deps
    assert "depends" in deps
    assert isinstance(deps["blocks"], list)
    assert isinstance(deps["blocked_by"], list)
    assert isinstance(deps["depends"], list)

    # Verify bidirectional relationship was established
    assert "task-1" in deps["blocked_by"]
    assert "task-2" in test_data["hierarchy"]["task-1"]["dependencies"]["blocks"]
```

### Test Case 2: Partial Dependencies Structure
```python
def test_build_bidirectional_deps_action_partial_dependencies():
    """Test that bidirectional deps action completes partial dependencies structure."""
    error = EnhancedError(
        message="'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Sync bidirectional dependency",
    )

    # task-2 has partial dependencies (only 'blocks', missing 'blocked_by' and 'depends')
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": {"blocks": ["task-2"]},
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "dependencies": {"blocks": ["task-3"]},  # Partial structure
            },
        }
    }

    action = _build_bidirectional_deps_action(error, test_data)
    action.apply(test_data)

    # Verify all fields exist now
    deps = test_data["hierarchy"]["task-2"]["dependencies"]
    assert "blocks" in deps
    assert "blocked_by" in deps
    assert "depends" in deps

    # Verify existing data preserved and new relationship added
    assert "task-3" in deps["blocks"]  # Original data preserved
    assert "task-1" in deps["blocked_by"]  # New relationship added
```

### Test Case 3: Malformed Dependencies
```python
def test_build_bidirectional_deps_action_malformed_dependencies():
    """Test that bidirectional deps action handles malformed dependencies (null/non-dict)."""
    error = EnhancedError(
        message="'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Sync bidirectional dependency",
    )

    # task-2 has null dependencies
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": {"blocks": ["task-2"]},
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "dependencies": None,  # Malformed
            },
        }
    }

    action = _build_bidirectional_deps_action(error, test_data)
    action.apply(test_data)

    # Verify malformed dependencies replaced with complete structure
    deps = test_data["hierarchy"]["task-2"]["dependencies"]
    assert isinstance(deps, dict)
    assert set(deps.keys()) == {"blocks", "blocked_by", "depends"}
    assert "task-1" in deps["blocked_by"]
```

### Test Case 4: Both Nodes Missing Dependencies
```python
def test_build_bidirectional_deps_action_both_missing():
    """Test that both blocker and blocked nodes get complete structures when both are missing."""
    error = EnhancedError(
        message="'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Sync bidirectional dependency",
    )

    # Both tasks missing dependencies
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
            },
        }
    }

    action = _build_bidirectional_deps_action(error, test_data)
    action.apply(test_data)

    # Verify both nodes have complete structures
    for task_id in ["task-1", "task-2"]:
        deps = test_data["hierarchy"][task_id]["dependencies"]
        assert isinstance(deps, dict)
        assert set(deps.keys()) == {"blocks", "blocked_by", "depends"}
        assert all(isinstance(deps[k], list) for k in deps.keys())

    # Verify relationship established
    assert "task-2" in test_data["hierarchy"]["task-1"]["dependencies"]["blocks"]
    assert "task-1" in test_data["hierarchy"]["task-2"]["dependencies"]["blocked_by"]
```

**Note on Test Coverage**: Currently, there are **no tests** for `_build_bidirectional_deps_action` handling missing or malformed dependencies. These tests are critical to prevent regressions.

## 7. Impact Assessment

By implementing this change, the `sdd fix` command will:

### Improvements

1. **Enhanced Consistency**: Aligns with the pattern used in `_build_missing_deps_structure_action` (lines 722-732), ensuring uniform initialization across all dependency-related fix actions.

2. **Complete Structure Guarantees**: All three required dependency fields (`blocks`, `blocked_by`, `depends`) will be initialized, matching validation expectations in `hierarchy_validation.py` (lines 401-409).

3. **Robust Edge Case Handling**: Properly handles:
   - Missing dependencies (creates complete structure)
   - Malformed dependencies (replaces null/non-dict with complete structure)
   - Partial dependencies (adds missing fields to existing dict)
   - Empty dependencies (populates all required fields)

4. **Defensive Programming Alignment**: Matches defensive patterns found throughout the codebase:
   - `dependency_analysis.py` (lines 60-66): Checks `isinstance(deps, dict)` before access
   - `dependency_analysis.py` (lines 109-114, 121-125): More defensive checks
   - This shows the codebase expects robust handling of dependencies

5. **Reduced Fragility**: Eliminates reliance on undocumented execution order between `_build_bidirectional_deps_action` and `_build_missing_deps_structure_action`.

6. **Improved Maintainability**: Using a consistent pattern makes the code easier to understand and maintain, reducing cognitive load for future developers.

7. **Prevention of Subtle Bugs**: Tools that access dependency structures won't encounter `KeyError` or unexpected missing fields.

### Risk Assessment

**Risk Level: LOW**

- The change only affects initialization of missing/incomplete dependencies
- Existing valid structures are preserved (the else branch only adds missing fields)
- The logic is additive—it doesn't remove or modify existing valid data
- Aligns with existing patterns, so it's unlikely to introduce inconsistencies
- Comprehensive test coverage (4 test cases) will catch regressions

### Priority

**HIGH PRIORITY**: This should be implemented soon to:
- Fix the legitimate bug where `depends` field is not initialized
- Prevent potential issues in code that expects complete dependency structures
- Establish a robust, consistent pattern for future development

## 8. Implementation Notes

### Why This Solution Over the Original Proposals

The refined solution addresses limitations in both original approaches:

1. **Original "Simpler" Approach Failed On**:
   - Partial dependencies (e.g., `{"blocks": ["task-1"]}`)
   - `setdefault` is a no-op when the key exists, so missing fields in existing dicts weren't added

2. **Original "Robust" Approach Had**:
   - Redundant code (checking `isinstance` then using `setdefault` with the same default)
   - Less efficient due to redundancy
   - Didn't explicitly handle partial structures

3. **Refined Solution Advantages**:
   - Single responsibility: `isinstance` check handles malformed, `setdefault` handles partial
   - More efficient: no redundant operations
   - Explicitly handles all four edge cases (missing, malformed, partial, empty)
   - Clearer intent: the if/else structure makes the two scenarios obvious

### Location and Scope

- **File**: `src/claude_skills/sdd_validate/fix.py`
- **Function**: `_build_bidirectional_deps_action` (lines 685-687)
- **Lines to Replace**: Currently lines 686-687

### Implementation Steps

1. Replace the current dependency initialization logic with the refined solution
2. Add all four test cases to `test_fix.py`
3. Run the full test suite to ensure no regressions
4. Validate with specs that have missing/partial dependencies

### Potential Refactoring Opportunity

Both `_build_bidirectional_deps_action` and `_build_missing_deps_structure_action` could benefit from a shared helper function:

```python
def _ensure_complete_dependencies(node: dict) -> dict:
    """Ensure node has complete dependencies structure with all required fields."""
    if not isinstance(node.get("dependencies"), dict):
        node["dependencies"] = {"blocks": [], "blocked_by": [], "depends": []}
    else:
        node["dependencies"].setdefault("blocks", [])
        node["dependencies"].setdefault("blocked_by", [])
        node["dependencies"].setdefault("depends", [])
    return node["dependencies"]
```

This would:
- Centralize the pattern for consistency
- Make future changes easier (single source of truth)
- Improve testability (can test the helper in isolation)
- Reduce code duplication

However, this refactoring is optional and can be done separately.
