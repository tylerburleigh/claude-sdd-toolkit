# Plan: Prepare-Task Enriched Context (Phase 2)

## Background

Phase 1 refinements are complete:
- ✅ Debug logging added to doc_helper.py, doc_integration.py, discovery.py
- ✅ Lazy evaluation for doc context (skips abstract tasks)
- ✅ Removed unused `count_files_changed_between` function

This plan focuses on **enriching task context** using underutilized doc-query capabilities.

---

## Problem Statement

doc-query has 20+ query methods, but prepare-task only uses 1 (`get_task_context()`). The current `file_docs` payload is minimal:

```json
"file_docs": {
  "files": ["src/auth.py"],
  "dependencies": ["json", "pathlib"],
  "similar": []
}
```

Agents would benefit from richer context: call graphs, test files, complexity hotspots.

---

## Proposed Enhancements

### 1. Call Graph Context (High Value, Low Effort)

**What**: Show which functions call the target code and what it calls.

**Why**: Helps agents understand impact of changes and integration points.

**Implementation**:
- Use existing `get_callers()` and `get_callees()` from doc_query_lib
- Add to SDDContextGatherer in sdd_integration.py

**Output**:
```json
"call_graph": {
  "callers": [
    {"name": "handle_login", "file": "api/routes.py", "line": 45}
  ],
  "callees": [
    {"name": "hash_password", "file": "utils/crypto.py", "line": 12}
  ]
}
```

**Files to modify**:
- `src/claude_skills/claude_skills/doc_query/sdd_integration.py` - Add `get_call_context()` method
- `src/claude_skills/claude_skills/common/doc_helper.py` - Add call to new method
- `src/claude_skills/claude_skills/sdd_next/discovery.py` - Include in file_docs

---

### 2. Test Context (High Value, Medium Effort)

**What**: Show relevant test files and coverage hints.

**Why**: Agents need to know which tests to run and where coverage gaps exist.

**Implementation**:
- Use existing `get_test_context()` from SDDContextGatherer (currently unused)
- Add test file discovery based on naming conventions

**Output**:
```json
"test_context": {
  "test_files": ["tests/test_auth.py", "tests/integration/test_login.py"],
  "test_functions": ["test_validate_token", "test_hash_password"],
  "coverage_hint": "3 functions lack direct test coverage"
}
```

**Files to modify**:
- `src/claude_skills/claude_skills/doc_query/sdd_integration.py` - Enhance `get_test_context()`
- `src/claude_skills/claude_skills/common/doc_helper.py` - Call test context method

---

### 3. Complexity Hotspots (Medium Value, Low Effort)

**What**: Identify high-complexity functions in the task's target area.

**Why**: Helps agents focus attention on code that needs careful handling.

**Implementation**:
- Use existing `get_high_complexity(threshold, module)` from doc_query_lib
- Filter to task's file_path

**Output**:
```json
"complexity_hotspots": [
  {"name": "validate_token", "complexity": 8, "line": 45},
  {"name": "parse_claims", "complexity": 6, "line": 120}
]
```

**Files to modify**:
- `src/claude_skills/claude_skills/doc_query/sdd_integration.py` - Add complexity query
- `src/claude_skills/claude_skills/common/doc_helper.py` - Include in context

---

### 4. Impact Analysis (High Value, Medium Effort)

**What**: Show blast radius of changes - what other code depends on this.

**Why**: Risk assessment before making changes.

**Implementation**:
- Use existing `analyze_impact()` workflow from doc_query
- Provide risk level and dependent count

**Output**:
```json
"impact": {
  "direct_dependents": 5,
  "indirect_dependents": 12,
  "risk_level": "medium",
  "risk_factors": ["High call count", "Used by API layer"]
}
```

**Files to modify**:
- `src/claude_skills/claude_skills/doc_query/sdd_integration.py` - Call impact workflow
- `src/claude_skills/claude_skills/common/doc_helper.py` - Include in context

---

## Implementation Order

| Priority | Enhancement | Effort | Value | Rationale |
|----------|-------------|--------|-------|-----------|
| P0 | Call Graph | Low | High | Direct use of existing methods |
| P1 | Test Context | Medium | High | Already partially implemented |
| P2 | Complexity Hotspots | Low | Medium | Simple filter on existing data |
| P3 | Impact Analysis | Medium | High | Uses existing workflow |

---

## Enhanced file_docs Schema

```json
"file_docs": {
  "files": ["src/auth.py"],
  "dependencies": ["json", "pathlib"],

  "call_graph": {
    "callers": [...],
    "callees": [...]
  },

  "test_context": {
    "test_files": [...],
    "test_functions": [...],
    "coverage_hint": "..."
  },

  "complexity_hotspots": [...],

  "impact": {
    "direct_dependents": 5,
    "risk_level": "medium"
  },

  "provenance": {
    "generated_at": "...",
    "freshness_ms": 45
  }
}
```

---

## Key Files

- `src/claude_skills/claude_skills/doc_query/sdd_integration.py` - SDDContextGatherer class
- `src/claude_skills/claude_skills/doc_query/doc_query_lib.py` - Core query methods
- `src/claude_skills/claude_skills/doc_query/workflows/` - Impact/trace workflows
- `src/claude_skills/claude_skills/common/doc_helper.py` - prepare-task integration
- `src/claude_skills/claude_skills/sdd_next/discovery.py` - Context assembly

---

## Testing Strategy

1. **Unit tests** for each new context method in sdd_integration.py
2. **Integration test** verifying enriched file_docs structure
3. **Performance test** ensuring <100ms total latency budget maintained

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Token bloat | Add config to enable/disable each enrichment |
| Latency increase | Parallel queries, early termination on timeout |
| Schema v1 docs lack call data | Graceful fallback to basic context |
