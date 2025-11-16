# Evolving `code-doc` and `doc-query`: A Synthesized Improvement Plan

## 1. Executive Summary

This document synthesizes competitive analysis and internal research to propose a strategic evolution for the toolkit's documentation capabilities. The core recommendation is to transform `code-doc` from a code-centric analyzer into a **Project Intelligence Engine** and `doc-query` from a simple parser into a comprehensive **Context Retrieval System**.

This will be achieved by adopting the high-leverage, AI-first principles from `document-project` (like multi-file outputs and project-type awareness) and combining them with `code-doc`'s unique strength: deep, language-aware AST analysis.

### Why This Evolution Matters

**Current Pain Points:**
- Single-file documentation causes context exhaustion on large projects (>500 files)
- Manual file path management in workflows is error-prone and brittle
- No standardized way for AI agents to discover and load context automatically
- Documentation generation doesn't scale to enterprise codebases without memory issues
- Workflows must repeatedly read entire documentation files to access small sections

**Post-Evolution Benefits:**
- **60-70% reduction in context tokens** when loading documentation (load only relevant shards)
- **Zero manual file management** - automatic content discovery via `{code_doc_content}` variables
- **Self-describing documentation** optimized for AI consumption with usage guidance
- **Handles projects of any size** without context exhaustion via write-as-you-go pattern
- **Intelligent loading** - INDEX_GUIDED strategy loads only what's needed for each workflow

## 2. Code-Doc Evolution

The goal is to enhance `code-doc` with the robustness and context-awareness of `document-project` without sacrificing its analytical depth.

*   **Default to Multi-File Markdown Output:** The multi-file structure should become the default to ensure large projects can be consumed piecemeal. The `index.md` will serve as the master entry point, combining a **Quick Reference** section, a **document map** (links to shards), and **"For AI-Assisted Development"** guidance that downstream tools can parse to decide what context to load.

*   **Preserve JSON for Machine Use:** The single, comprehensive `documentation.json` artifact will be preserved for machine use. It will be surfaced through the new index under a "Machine-Readable Documentation" heading, allowing `doc-query` to continue anchoring on structured data while other agents consume the Markdown shards.

*   **Implement a Discovery Protocol:** A discovery protocol will be layered in to automatically load required documentation shards into a standardized `{code_doc_content}` variable. This `INDEX_GUIDED` loading strategy mirrors BMAD’s `discover_inputs` pattern and eliminates manual file path management in downstream workflows.

*   **Adopt Robustness Features:** To handle large-scale projects effectively, `code-doc` will incorporate key features where `document-project` currently excels:
    *   **Project-Type Detection:** To focus analysis on UI, API, or data layers as appropriate.
    *   **Scan Levels:** To allow for quick overviews or deep, exhaustive analysis.
    *   **Resumability:** To recover gracefully from interruptions during long scans.
    *   **Write-as-you-go Flushing:** To avoid holding entire codebases in memory.

### Example: Multi-File Structure

**Before (current):**
```
docs/
  ├── DOCUMENTATION.md (single file, ~150k tokens)
  └── documentation.json (5MB, 150k tokens)
```

**After (proposed):**
```
docs/
  ├── index.md (5k tokens - master entry point)
  ├── documentation.json (5MB, preserved for doc-query)
  ├── statistics.md (2k tokens)
  ├── classes.md (30k tokens)
  ├── functions.md (40k tokens)
  ├── dependencies.md (10k tokens)
  └── cross-references.md (25k tokens)
```

**AI Agent Use Case Example:**

*Query:* "Find all API endpoints"

*Before:* Loads entire `DOCUMENTATION.md` → **150k tokens**

*After:* INDEX_GUIDED loads only:
- `index.md` (5k tokens) - to understand structure
- `functions.md` (40k tokens) - contains endpoint definitions
- `classes.md` (30k tokens) - contains controller classes

**Total: ~75k tokens (50% reduction)**

For more targeted queries like "What are the project statistics?" → loads only `index.md` + `statistics.md` = **7k tokens (95% reduction)**

## 2.5 Phased Implementation Strategy

To minimize risk and validate the approach incrementally, implementation will follow this phased rollout:

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Enable multi-file output without breaking existing functionality

**Deliverables:**
- [ ] Multi-file generation in `formatter.py` with shard creation logic
- [ ] Index.md generator with "For AI-Assisted Development" section
- [ ] Make multi-file the default (add `--single-file` fallback flag)
- [ ] Preserve existing JSON schema completely unchanged
- [ ] Comprehensive test suite for multi-file generation
- [ ] Update CLI help text and documentation

**Success Criteria:**
- ✅ Generates all expected files (index.md + 5-7 shards)
- ✅ doc-query continues working with JSON without modification
- ✅ No performance degradation (±10% acceptable)
- ✅ All existing tests pass
- ✅ Manual testing on 3 sample projects (small, medium, large)

**Decision Gate:** If context reduction <50% or performance regression >20%, revisit approach

### Phase 2: Discovery Protocol (Week 3)
**Goal:** Automatic content loading via INDEX_GUIDED strategy

**Deliverables:**
- [ ] Create `doc_discovery.py` module with loading strategies
- [ ] Implement INDEX_GUIDED with link parsing from index.md
- [ ] Update `doc_helper.py` to use discovery protocol
- [ ] Add content variable support (`{code_doc_content}`)
- [ ] Update one workflow (sdd-plan) as proof of concept
- [ ] Document in SKILL.md with examples

**Success Criteria:**
- ✅ sdd-plan automatically loads code-doc content via variables
- ✅ Context size reduced by 60%+ for typical projects (measured on 5 projects)
- ✅ Zero manual file path management needed in updated workflow
- ✅ Fallback gracefully when documentation doesn't exist

**Decision Gate:** If workflow integration is complex or brittle, simplify discovery protocol

### Phase 3: Enhancements (Weeks 4-5)
**Goal:** Project-type awareness and memory efficiency

**Deliverables:**
- [ ] Project type detection (start with 4 types: web-frontend, backend-api, library, monorepo)
- [ ] Write-as-you-go pattern for incremental file writing
- [ ] Type-specific documentation sections in index.md
- [ ] Memory usage optimization and profiling
- [ ] Performance benchmarks across project sizes

**Success Criteria:**
- ✅ Successfully processes projects >1000 files without memory errors
- ✅ Memory usage stays under 500MB peak
- ✅ Project type correctly detected for 80%+ of test projects
- ✅ Generation completes even if interrupted (write-as-you-go working)

**Decision Gate:** If memory issues persist, prioritize write-as-you-go optimizations

### Phase 4: Migration & Adoption (Week 6+)
**Goal:** Migrate all workflows and validate production readiness

**Deliverables:**
- [ ] Migrate all SDD workflows to use content variables
- [ ] Create migration guide with before/after examples
- [ ] Performance benchmarks published
- [ ] Update all skill documentation
- [ ] User feedback collection mechanism

**Success Criteria:**
- ✅ 100% of workflows using new content variable system
- ✅ No regression in documentation completeness or accuracy
- ✅ Positive user feedback (≥8/10 satisfaction)
- ✅ All success metrics from table below met

**Decision Gate:** No blocker bugs; all workflows stable for 2 weeks

### Success Metrics

Track these metrics to validate the evolution:

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| Context size (tokens) | 150k | <60k | Measure on 3 sample projects (small/medium/large) |
| Generation time | 30s | <36s | claude-sdd-toolkit generation benchmark |
| Memory peak | 300MB | <500MB | Process monitoring during generation |
| Workflow file operations | 3-5 manual reads | 0 | Count Read calls in workflow traces |
| User satisfaction | N/A | ≥8/10 | Survey after 2 weeks of usage |
| Adoption rate | 0% | 80% | % of workflows using content variables |
| Documentation accuracy | 100% | 100% | Comparison with baseline (no functions/classes lost) |

## 3. Doc-Query Evolution

As the documentation artifacts become richer, `doc-query` will evolve into the primary, intelligent interface for accessing all project context.

*   **Implement `INDEX_GUIDED` Loading:** `doc-query` will be taught to read the multi-file structure by parsing `index.md` first and only loading the referenced shards relevant to a query. This keeps the tool token-efficient while allowing it to benefit from the new narrative documentation.

*   **Support Hybrid Retrieval:** `doc-query` will combine its query strategies, using the JSON graph for deep AST queries (e.g., "who calls X?") and enriching responses with narrative context from the relevant Markdown shards.

*   **Expose Project-Type Metadata:** Once project-type detection is added to the generation step, this metadata will be exposed as filters or facets in `doc-query`. This will allow users to scope queries to specific parts of the application, such as "backend API components" vs. "client UI components."

*   **Handle Stale/Partial Indexes:** When resumability is implemented, `doc-query` will learn to detect stale indexes or documentation from partial runs. It will warn users of potentially incomplete data and offer to fall back to the last complete snapshot, ensuring retrieval is reliable.

### Backward Compatibility Strategy

To ensure smooth transition without breaking existing workflows:

1. **JSON Schema Unchanged**: The `documentation.json` structure remains identical, ensuring doc-query works without any modification. All existing fields, cross-references, and metadata are preserved exactly.

2. **Fallback Loading**: If index.md doesn't exist, the system falls back to loading documentation.json directly:
   ```python
   # Hybrid approach in doc_helper.py
   def get_code_doc_content(output_folder: Path) -> str:
       if (output_folder / "index.md").exists():
           # New multi-file approach
           content = discovery.load_index_guided()
       else:
           # Fallback to legacy single-file
           json_path = output_folder / "documentation.json"
           if json_path.exists():
               content = json.loads(json_path.read_text())
       return content
   ```

3. **Gradual Enhancement**: doc-query can be enhanced to use Markdown shards for richer context while maintaining JSON support for structured queries:
   - Use JSON for precise AST queries ("who calls function X?")
   - Use Markdown for contextual queries ("explain the architecture")
   - Combine both for comprehensive answers

4. **Legacy Flag**: Provide `--single-file` flag for users who prefer the old format during transition period (1-2 releases), then deprecate with clear migration path.

## 3.5 Risks & Mitigations

### Risk 1: Breaking Existing Workflows
**Impact:** High | **Likelihood:** Medium

**Description:** Workflows that directly reference file paths or expect single-file output may break.

**Mitigation Strategies:**
- Maintain backward compatibility with single-file output via `--single-file` flag
- Preserve JSON schema exactly as-is (no breaking changes)
- Provide comprehensive migration guide with before/after examples
- Extensive testing before rollout (all existing tests must pass)
- Phased rollout allows early detection of issues
- Communication: Announce changes 2 weeks before default switch

**Validation:** All 15+ existing SDD workflows continue working after changes

### Risk 2: Over-Engineering the Discovery Protocol
**Impact:** Medium | **Likelihood:** Medium

**Description:** INDEX_GUIDED loading becomes too complex, adding maintenance burden without sufficient value.

**Mitigation Strategies:**
- Start with simple implementation (just load all .md files - FULL_LOAD strategy)
- Add INDEX_GUIDED intelligence incrementally only if simple approach insufficient
- Validate with real-world usage patterns before adding complexity
- Keep fallback to simple file loading as alternative
- Use decision gates: if complexity > value, simplify
- Document complexity budget: INDEX_GUIDED should be <200 LOC

**Validation:** Measure code complexity metrics; user feedback on loading accuracy

### Risk 3: Multi-File Fragmentation Confusion
**Impact:** Low | **Likelihood:** Low

**Description:** Users or AI agents get confused by multiple files instead of single source.

**Mitigation Strategies:**
- Clear documentation of file structure and purpose
- index.md serves as single, authoritative entry point
- Standardized naming conventions (statistics.md, classes.md, etc.)
- Examples in every workflow showing proper usage
- "For AI-Assisted Development" section provides guidance
- Visual diagrams showing file relationships

**Validation:** User comprehension testing; AI agent successfully navigates structure

### Risk 4: Performance Degradation
**Impact:** High | **Likelihood:** Low

**Description:** Multi-file generation is significantly slower than single-file approach.

**Mitigation Strategies:**
- Benchmark before and after implementation
- Write-as-you-go prevents memory buildup and speeds completion
- Parallel file writing for shards (if beneficial)
- Incremental file writing reduces peak memory, improves stability
- Target: <20% slower than current implementation
- If >20% slower, optimize hot paths before release

**Validation:** Performance benchmarks on small (50 files), medium (500 files), large (2000 files) projects

### Risk 5: Low Adoption Rate
**Impact:** High | **Likelihood:** Medium

**Description:** Users continue using old single-file format; new features underutilized.

**Mitigation Strategies:**
- Make multi-file the default (not opt-in) from day one
- Show clear benefits in examples (context reduction, faster loading)
- Automatic migration for workflows (no manual work required)
- Provide comparison metrics (context size, speed, memory)
- Highlight benefits in release notes and documentation
- Gather early feedback and iterate quickly
- Deprecation timeline for `--single-file` (warn, then remove after 2 releases)

**Validation:** Track adoption metrics; survey users after 1 month

## 4. Next Steps

The following actions are organized by timeframe with specific deliverables, decision points, and success metrics.

### Immediate Actions (Week 1)

#### Priority 1A: Proof of Concept
**Goal:** Validate multi-file approach reduces context and is technically feasible

**Tasks:**
- [ ] Create spike branch: `feature/multi-file-docs`
- [ ] Implement basic multi-file generation (no INDEX_GUIDED yet)
  - Generate index.md with links
  - Generate classes.md, functions.md, dependencies.md
  - Keep existing single-file as-is for comparison
- [ ] Test on claude-sdd-toolkit itself (medium-sized project)
- [ ] Measure context size reduction (compare tokens: single vs. multi)
- [ ] Measure generation time (compare performance)

**Decision Point:**
- If context reduction <50%, reconsider entire approach
- If performance regression >30%, optimize before proceeding
- **Go/No-Go by end of Week 1**

**Estimated Effort:** 2-3 days

#### Priority 1B: Design Review
**Goal:** Validate structure and gather early feedback

**Tasks:**
- [ ] Review index.md structure with stakeholders
- [ ] Validate "For AI-Assisted Development" content format
- [ ] Confirm shard naming conventions (classes.md vs code-classes.md)
- [ ] Document file structure in design doc

**Decision Point:**
- Finalize file structure before full implementation
- Confirm standard shard set (5-7 files)

**Estimated Effort:** 1 day

### Short-term Actions (Weeks 2-3)

#### Priority 2: Production Implementation
**Goal:** Complete multi-file generation ready for beta testing

**Tasks:**
- [ ] Complete multi-file generation in `formatter.py`:
  - Implement `generate_multi_file()` method
  - Create shard generators for each file type
  - Add index.md generator with complete structure
- [ ] Add CLI flags:
  - Make multi-file the default
  - Add `--single-file` for backward compatibility
  - Add `--output-format` flag (multi-file, single-file, both)
- [ ] Update `generator.py` to orchestrate multi-file output
- [ ] Create comprehensive test suite:
  - Test each shard is generated correctly
  - Test index.md links are valid
  - Test backward compatibility with `--single-file`
  - Test on small, medium, large projects
- [ ] Create migration guide draft (for users and workflows)
- [ ] Update CLI help text and user documentation

**Milestone:** Multi-file generation ready for beta testing

**Estimated Effort:** 4-5 days

#### Priority 3: Discovery Protocol
**Goal:** One workflow successfully using content variables

**Tasks:**
- [ ] Implement `doc_discovery.py`:
  - Create `DocumentationDiscovery` class
  - Implement FULL_LOAD strategy (load all .md files)
  - Implement INDEX_GUIDED strategy (parse index, load linked files)
  - Add error handling and fallbacks
- [ ] Integrate with `doc_helper.py`:
  - Add `get_code_doc_content()` function using discovery
  - Maintain backward compatibility
- [ ] Add content variable support to workflow system
- [ ] Update sdd-plan as proof of concept:
  - Use `{code_doc_content}` variable
  - Remove manual file reading
  - Test end-to-end workflow
- [ ] Document in SKILL.md with usage examples

**Milestone:** One workflow successfully using content variables without manual file operations

**Estimated Effort:** 3-4 days

### Medium-term Actions (Weeks 4-6)

#### Priority 4: Enhancement & Migration
**Goal:** All workflows migrated with optimizations in place

**Tasks:**
- [ ] Add project type detection:
  - Create `project_types.py` module
  - Implement detection for 4 types (web-frontend, backend-api, library, monorepo)
  - Add type metadata to index.md
  - Test accuracy on 20 diverse projects
- [ ] Implement write-as-you-go pattern:
  - Refactor to write shards incrementally during parsing
  - Free memory after each shard written
  - Test on very large project (>1000 files)
- [ ] Migrate all workflows to use discovery protocol:
  - sdd-plan ✅ (already done in Priority 3)
  - sdd-next
  - sdd-fidelity-review
  - Other workflows using code-doc
- [ ] Performance optimization:
  - Profile generation process
  - Optimize hot paths if needed
  - Ensure <20% performance impact
- [ ] Final testing and validation

**Milestone:** All workflows migrated; performance benchmarked and acceptable

**Estimated Effort:** 6-8 days

### Long-term Actions (Month 2+)

#### Priority 5: Validation & Refinement
**Goal:** Production-ready with validated benefits

**Tasks:**
- [ ] Collect user feedback:
  - Survey users (target ≥8/10 satisfaction)
  - Gather usage analytics
  - Identify pain points
- [ ] Refine INDEX_GUIDED intelligence:
  - Analyze which files are most commonly loaded together
  - Improve relevance detection based on actual usage
  - Add semantic understanding if needed
- [ ] Add resumability (if memory issues persist):
  - Implement state tracking
  - Enable resume from interruption
  - Test on very large projects
- [ ] Consider additional shard types based on usage:
  - Test coverage data?
  - API endpoints (separate from functions)?
  - Architecture diagrams?
- [ ] Documentation and communication:
  - Finalize migration guide
  - Create before/after examples
  - Write blog post or announcement
  - Update all documentation

**Milestone:** Production-ready; all success metrics met; validated at scale

**Estimated Effort:** Ongoing; 2-3 days focused work

### Success Metrics (from Section 2.5)

All metrics must be met before declaring production-ready:

| Metric | Target | Status |
|--------|--------|--------|
| Context size reduction | ≥60% | ⬜ Not measured |
| Generation time | <20% slower | ⬜ Not measured |
| Memory peak | <500MB | ⬜ Not measured |
| Workflow file operations | 0 manual reads | ⬜ Not measured |
| User satisfaction | ≥8/10 | ⬜ Not surveyed |
| Adoption rate | 80% | ⬜ Not tracked |
| Documentation accuracy | 100% (no loss) | ⬜ Not validated |

### Decision Gates

Before proceeding to each phase, validate the previous phase succeeded:

**Gate 1** (Before Week 2 - Priority 2):
- ✅ Multi-file POC working
- ✅ Context reduction ≥50% demonstrated
- ✅ No performance regression >30%
- **Decision:** Proceed with full implementation

**Gate 2** (Before Week 4 - Priority 4):
- ✅ At least one workflow successfully using discovery protocol
- ✅ Content variables working as expected
- ✅ Positive initial feedback from testing
- **Decision:** Begin migration of all workflows

**Gate 3** (Before Week 6 - Priority 5):
- ✅ Project type detection accurate (>80%)
- ✅ Write-as-you-go prevents memory issues on large projects
- ✅ All enhancements tested and stable
- **Decision:** Declare ready for production use

**Gate 4** (Before declaring production-ready):
- ✅ All workflows migrated successfully
- ✅ All success metrics met
- ✅ No critical bugs in 2 weeks
- ✅ User feedback positive
- **Decision:** Release as default; deprecate single-file

## 5. Open Questions

These questions should be resolved during implementation based on real-world usage and technical constraints.

### Technical Questions

#### Q1: Shard Granularity
**Question:** Should we shard further by module/package, or is file-type sharding sufficient?

**Considerations:**
- Very large projects (>2000 files) might benefit from module-level sharding
- Example: `classes-backend.md`, `classes-frontend.md` instead of single `classes.md`
- Adds complexity but could reduce context further

**Recommendation:**
- Start with file-type sharding (classes.md, functions.md, etc.)
- Monitor context sizes during Phase 1 testing
- If any single shard exceeds 50k tokens, add module-level sharding in Phase 3
- **Decision point:** End of Week 1 POC

#### Q2: INDEX_GUIDED Intelligence
**Question:** How should INDEX_GUIDED determine relevance when loading shards?

**Options:**
- **Simple keyword matching:** Look for keywords in workflow name/description
- **Semantic similarity:** Use embeddings to match workflow intent to shard descriptions
- **Workflow-type mapping:** Hardcoded rules (e.g., sdd-plan always loads architecture, statistics, dependencies)
- **AI-assisted selection:** Ask AI which shards are needed based on task

**Considerations:**
- Simpler = easier to debug and maintain
- Smarter = better context optimization
- Wrong selection = missing critical context (worse than loading too much)

**Recommendation:**
- Phase 2: Start with simple keyword matching + workflow-type mapping
- Phase 4: Analyze actual usage patterns and add semantic understanding if needed
- Principle: "When in doubt, load it" - prefer false positives over false negatives
- **Decision point:** End of Week 3 after initial discovery protocol testing

#### Q3: Cross-Reference Placement
**Question:** Should cross-references be in a separate file or integrated into classes/functions shards?

**Options:**
- **Separate file** (`cross-references.md`): Keeps shards focused, cleaner separation
- **Integrated**: Cross-refs embedded in classes.md and functions.md for context
- **Hybrid**: Basic refs inline, detailed graph in separate file

**Considerations:**
- Separate: Requires loading extra file for cross-ref queries
- Integrated: Larger shard files, but more complete context per shard
- Use case: "Who calls function X?" needs cross-ref data

**Recommendation:**
- Phase 1: Implement separate `cross-references.md` for simplicity
- Phase 2-3: Evaluate if cross-refs should be inline based on usage patterns
- doc-query can always access JSON for detailed cross-ref analysis
- **Decision point:** End of Week 2 during production implementation

### UX Questions

#### Q4: Default Behavior
**Question:** Should `sdd doc generate` default to multi-file or single-file?

**Options:**
- **Multi-file default:** Forces adoption, shows benefits immediately
- **Single-file default:** Safer transition, opt-in to multi-file via `--multi-file`

**Considerations:**
- Multi-file default drives adoption but risks breaking existing scripts
- Single-file default safer but delays benefits and adoption
- Users may never switch if single-file is default

**Recommendation:**
- **Make multi-file the default from day one**
- Provide `--single-file` flag for backward compatibility
- Clear messaging in release notes
- Deprecation timeline: Warn in 2 releases, remove `--single-file` in release 3
- **Decision:** Confirmed at design review (Week 1, Priority 1B)

#### Q5: Discovery Failure Handling
**Question:** What should workflows do if documentation doesn't exist when discovery protocol runs?

**Options:**
- **Silent failure:** Return empty content, workflow continues
- **Warning message:** Notify user, continue with empty content
- **Offer to generate:** Prompt user to run `sdd doc generate`
- **Auto-generate:** Automatically generate docs before workflow starts

**Considerations:**
- Silent failure: Easy to miss missing docs, poor UX
- Warning: Good visibility, user can take action
- Offer to generate: Best UX, but requires user interaction
- Auto-generate: Seamless but adds time/complexity

**Recommendation:**
- **Warning message with suggestion** for manual workflows
- Example: "⚠️  Code documentation not found. Run `sdd doc generate` to create it."
- For automated workflows: Log warning, continue with empty content
- Future: Add `--auto-generate-docs` flag for auto-generation
- **Decision point:** Week 3 during discovery protocol implementation

### Migration Questions

#### Q6: Transition Period
**Question:** Should we support both single-file and multi-file formats simultaneously?

**Options:**
- **Dual support:** Both formats work for 1-2 releases, then deprecate single-file
- **Hard cutover:** Multi-file only from day one
- **Permanent support:** Both formats supported indefinitely

**Considerations:**
- Dual support: Easier transition, more maintenance
- Hard cutover: Clean, but risky for users
- Permanent support: Maximum flexibility, maximum maintenance burden

**Recommendation:**
- **Dual support for 2 releases (approximately 2-3 months)**
- Release 1: Multi-file default, `--single-file` available
- Release 2: Deprecation warning when using `--single-file`
- Release 3: Remove `--single-file`, multi-file only
- **Decision:** Confirmed at design review (Week 1, Priority 1B)

#### Q7: Existing Documentation Migration
**Question:** How do users with existing single-file documentation migrate to multi-file?

**Options:**
- **Automatic detection and regeneration:** Detect old format, regenerate automatically with warning
- **Migration tool:** Provide `sdd doc migrate` command
- **Manual regeneration:** Users must manually delete old docs and regenerate
- **In-place upgrade:** Convert single-file to multi-file without full regeneration

**Considerations:**
- Automatic: Best UX, risk of unwanted regeneration
- Migration tool: Clear intent, extra command to learn
- Manual: Simple, but poor UX
- In-place: Fast, but complex implementation

**Recommendation:**
- **Automatic detection with user confirmation**
- When running `sdd doc generate`, detect if old single-file exists
- Prompt: "Old documentation format detected. Regenerate with new multi-file format? (Y/n)"
- Default to Yes, allow cancellation
- Store format version in index.md metadata to detect format
- **Decision point:** Week 2 during production implementation

### Validation Questions

#### Q8: Testing Strategy
**Question:** How do we validate that INDEX_GUIDED is loading the right content?

**Options:**
- **Unit tests:** Test link parsing, file loading logic
- **Integration tests:** Test with real workflows, verify expected shards loaded
- **User studies:** Observe real users, validate they get needed context
- **Telemetry:** Track which shards loaded, correlate with workflow success

**Considerations:**
- Unit tests: Test mechanics, not effectiveness
- Integration tests: Test end-to-end, but fixed scenarios
- User studies: Best validation, time-consuming
- Telemetry: Real-world data, privacy concerns

**Recommendation:**
- **All four approaches:**
- **Unit tests** for INDEX_GUIDED parsing logic (Week 3)
- **Integration tests** for each workflow migration (Weeks 4-6)
- **User studies** with 3-5 beta testers (Month 2)
- **Optional telemetry** (opt-in) to track actual usage patterns
- Validation metric: >90% of workflows get needed context without loading everything
- **Decision point:** Testing strategy confirmed Week 3 (Priority 3)

---

## Conclusion

This evolution plan transforms `code-doc` and `doc-query` from code-centric analysis tools into a comprehensive **Project Intelligence Engine** and **Context Retrieval System**. By adopting BMAD's proven patterns (multi-file structure, INDEX_GUIDED loading, project-type awareness) while preserving code-doc's unique strengths (AST analysis, cross-references), we create a documentation system that:

- **Scales effortlessly** to projects of any size
- **Optimizes AI agent context** automatically
- **Eliminates manual file management** for workflows
- **Maintains backward compatibility** during transition
- **Delivers measurable value** (60%+ context reduction, zero manual reads)

The phased approach with clear decision gates ensures we can validate benefits incrementally and course-correct if needed. The comprehensive risk mitigation strategies address the key failure modes upfront.

**Next Action:** Begin Week 1 Proof of Concept on `feature/multi-file-docs` branch.