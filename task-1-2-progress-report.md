# Task 1-2 Progress Report: Cross-Reference Tracking in AST Analysis

**Task**: Add cross-reference tracking during AST analysis to capture caller/callee relationships
**Estimated Hours**: 16
**Current Status**: In Progress (Approximately 45% complete - task-1-2-1 complete)
**Time Spent**: ~8 hours

---

## ✅ Completed Work

### 1. Created ast_analysis.py Module

**File**: `src/claude_skills/claude_skills/code_doc/ast_analysis.py`

**Created Data Structures:**

1. **ReferenceType Enum** - Types of cross-references (function_call, method_call, class_instantiation, import, inheritance)

2. **DynamicPattern Enum** - Dynamic patterns that may affect accuracy (decorator, monkey_patch, reflection, dynamic_import, eval_exec, getattr_setattr)

3. **CallSite Dataclass** - Represents a location where a function/method is called
   - Tracks: caller, callee, file paths, line numbers, call type, metadata

4. **InstantiationSite Dataclass** - Represents where a class is instantiated
   - Tracks: class_name, instantiator, file, line, metadata

5. **DynamicPatternWarning Dataclass** - Warnings about dynamic patterns
   - Tracks: pattern type, location, file, line, description, impact

6. **CrossReferenceGraph Class** - Main bidirectional graph tracking system
   - **Forward lookups**: What does X call/instantiate?
   - **Reverse lookups**: What calls/instantiates X?
   - **Statistics**: Total calls, instantiations, warnings, dynamic pattern counts

**Key Methods Implemented:**
- `add_call()` - Add function/method call with bidirectional indexing
- `add_instantiation()` - Add class instantiation with bidirectional indexing
- `add_import()` - Add import relationships (forward and reverse)
- `add_warning()` - Add dynamic pattern warnings
- `get_callers()` - Query who calls a function
- `get_callees()` - Query what a function calls
- `get_instantiation_sites()` - Query where a class is instantiated
- `get_imported_by()` - Query reverse dependencies
- `to_dict()` - Serialize to JSON

### 2. Updated ParseResult in base.py

**File**: `src/claude_skills/claude_skills/code_doc/parsers/base.py`

**Changes:**
- Added `cross_references: Optional[Any]` field to ParseResult
- Updated `to_dict()` to include cross-references in JSON output
- Enhanced `merge()` method to merge cross-reference graphs from multiple files
  - Merges calls, instantiations, imports, warnings
  - Aggregates statistics across files

---

## ✅ Recently Completed

### task-1-2-1: Function Call Tracking During AST Traversal

**Status**: ✅ COMPLETED

**What Was Done:**
- ✅ Created _CallTracker AST visitor class in Python parser
- ✅ Implemented context tracking (current function/class via context stack)
- ✅ Implemented visit_Call() to capture function and method calls
- ✅ Integrated tracker into parse_file() method
- ✅ Added CrossReferenceGraph creation and assignment to ParseResult
- ✅ Wrote 11 comprehensive unit tests (all pass)
- ✅ Verified on real file: tracks 82 calls in python.py

**Key Features:**
- Distinguishes between function calls and method calls
- Tracks caller context (function, class, or module-level)
- Records line numbers for each call
- Maintains bidirectional indexing (callers and callees)
- Handles nested functions, class methods, decorators, module-level calls

**Test Results:**
- 11 new tests added to TestPythonParserCrossReferences class
- All 27 tests pass (16 existing + 11 new)
- Manual verification: successfully tracks calls in python.py parser itself

## 🔄 In Progress

### task-1-2-2: Import Tracking for Class Instantiation

**Status**: Pending - ready to start next

**What Remains:**
- Implement class instantiation detection in CallTracker
- Track `ClassName()` constructor calls
- Store instantiation sites in CrossReferenceGraph
- Build instantiated_by and instantiators indexes

---

## ⏳ Pending Work

### task-1-2-2: Import Tracking for Class Instantiation

**Estimated Remaining**: 3-4 hours

**Required Work:**
1. Add AST visitor logic to detect class instantiation (e.g., `Foo()` calls)
2. Track constructor calls and link to class definitions
3. Record instantiation sites with file/line info
4. Build `instantiated_by` and `instantiators` indexes
5. Handle edge cases:
   - Factory functions
   - Class decorators
   - Metaclasses

### task-1-2-3: Build Bidirectional Reference Graph

**Estimated Remaining**: 2-3 hours

**Required Work:**
1. Ensure all cross-references are bidirectional
2. Test forward lookups (what does X call?)
3. Test reverse lookups (what calls X?)
4. Optimize query performance for large codebases
5. Add caching for frequently-accessed lookups
6. Document graph query API

### task-1-2-4: Add Warning System for Dynamic Python Patterns

**Estimated Remaining**: 3-4 hours

**Required Work:**
1. Add AST visitor logic to detect:
   - Decorators (`@decorator`)
   - Monkey-patching (runtime attribute assignment)
   - Reflection (`getattr`, `setattr`, `hasattr`)
   - Dynamic imports (`__import__`, `importlib`)
   - `eval()` and `exec()` calls
2. Create DynamicPatternWarning instances
3. Add warnings to CrossReferenceGraph
4. Document impact on cross-reference accuracy
5. Generate warning statistics
6. Add coverage metrics (static vs dynamic code detection)

---

## 📊 Integration Tasks

### Remaining Parser Updates

**Priority 1: Python Parser** (3-4 hours)
- Add CrossReferenceGraph instance to parse_file()
- Implement call tracking visitor
- Implement instantiation tracking
- Add dynamic pattern detection
- Include graph in ParseResult

**Priority 2: JavaScript/TypeScript Parser** (2-3 hours)
- Adapt call tracking for JavaScript syntax
- Handle module.exports and ES6 imports
- Track `new` expressions for instantiation

**Priority 3: Go Parser** (2-3 hours)
- Adapt call tracking for Go syntax
- Handle package imports
- Track struct initialization

---

## 🧪 Testing Requirements

**Unit Tests Needed:**
1. Test CrossReferenceGraph.add_call()
2. Test CrossReferenceGraph.add_instantiation()
3. Test bidirectional lookups
4. Test graph merging across files
5. Test dynamic pattern detection
6. Test serialization to JSON

**Integration Tests Needed:**
1. Parse sample Python file with calls
2. Parse sample file with class instantiations
3. Parse file with decorators/dynamic patterns
4. Parse multi-file project
5. Verify cross-references in output JSON

**Test Files to Create:**
- `tests/test_ast_analysis.py` - Unit tests for CrossReferenceGraph
- `tests/test_cross_reference_integration.py` - Integration tests
- `tests/fixtures/sample_calls.py` - Sample Python with function calls
- `tests/fixtures/sample_instantiation.py` - Sample with class instantiation

---

## 📝 Documentation Requirements

**Code Documentation:**
- ✅ Docstrings for ast_analysis.py classes and methods
- ⏳ Usage examples in docstrings
- ⏳ Architecture decision records (ADR) for design choices

**User Documentation:**
- ⏳ Update code-doc SKILL.md with cross-reference features
- ⏳ Add examples of querying cross-references
- ⏳ Document limitations (dynamic patterns)

---

## 🎯 Success Criteria (from Spec)

**Task Complete When:**
- ✅ Cross-reference data structures defined
- ✅ ParseResult updated to include cross-references
- ⏳ Function calls tracked during AST traversal
- ⏳ Class instantiations tracked
- ⏳ Bidirectional graph built and queryable
- ⏳ Dynamic patterns detected and logged
- ⏳ All tests pass
- ⏳ Documentation updated

---

## 🚀 Next Steps

**Immediate (Next Session):**
1. Complete Python Parser integration
   - Add CrossReferenceGraph instance creation
   - Implement call tracking visitor logic
   - Add instantiation detection
2. Write unit tests for CrossReferenceGraph
3. Test with sample Python file

**Short-term:**
1. Add dynamic pattern detection
2. Complete Python parser integration
3. Add integration tests
4. Update schema (task-1-3) to store cross-references

**Long-term:**
1. Extend to JavaScript/TypeScript parser
2. Extend to Go parser
3. Add query CLI commands for cross-references
4. Optimize performance for large codebases

---

## 📈 Progress Summary

**Overall Progress**: ~45% (7/16 hours estimated)

**Completed:**
- Core data structures ✅
- Graph algorithms ✅
- ParseResult integration ✅
- Python parser call tracking integration ✅
- Unit tests for call tracking (11 tests) ✅

**In Progress:**
- task-1-2-2: Class instantiation tracking (next)

**Not Started:**
- task-1-2-3: Bidirectional reference graph (may already be complete via existing methods)
- task-1-2-4: Dynamic pattern detection ⏸️
- JavaScript/Go parsers ⏸️

---

## 💡 Key Design Decisions

1. **Bidirectional Indexing**: Store both forward and reverse lookups for O(1) query performance
2. **Separate Graph Class**: CrossReferenceGraph is independent of ParseResult for modularity
3. **Metadata Extensibility**: Each cross-reference has metadata dict for future extensions
4. **Warning System**: Explicit warnings for dynamic patterns help users understand accuracy limits
5. **Merge Support**: Graph can be merged across files for multi-file analysis

---

**Report Date**: 2025-10-26
**Author**: Claude (Sonnet 4.5)
**Task Status**: In Progress - Foundational work complete, integration pending
