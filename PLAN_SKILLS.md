# Plan: Create sdd-modify Skill and Subagent

**Date:** 2025-11-06
**Status:** Proposed
**Expert Consensus:** Gemini strongly recommends creating both skill and subagent

---

## Executive Summary

Create both a **sdd-modify skill** (user-facing) and **sdd-modify-subagent** (programmatic) to provide systematic spec modification capabilities. This completes the feedback loop: review → parse → modify → validate → re-review.

### Why Create New Components?

Based on Gemini's analysis:
- ✅ **Single Responsibility Principle** - Existing skills have clear roles; spec modification is distinct
- ✅ **User Experience** - Dedicated skill provides discoverable entry point
- ✅ **Architectural Fit** - Separates review generation ("what") from application ("how")
- ✅ **Integration Benefits** - Clean programmatic API enables automation
- ✅ **Maintainability** - Isolation simplifies debugging and enhancement

---

## What We Just Built

### sdd_spec_mod Module (CLI Tools)
```bash
# Parse review feedback into structured modifications
sdd parse-review <spec-id> --review <report.md> --output suggestions.json

# Apply batch modifications with validation
sdd apply-modifications <spec-id> --from suggestions.json --dry-run
sdd apply-modifications <spec-id> --from suggestions.json
```

**Features:**
- Transaction support with automatic rollback
- Safe CRUD operations (add/remove/update/move nodes)
- Revision history tracking
- 83 unit tests, 91% coverage
- 11/12 integration tests passing

**Gap:** No user-facing skill to orchestrate the workflow

---

## Existing Skills Overview

| Skill | Purpose | Handles Spec Modification? |
|-------|---------|---------------------------|
| sdd-update | Track progress, journal decisions | ❌ No (metadata only) |
| sdd-fidelity-review | Review implementation vs spec | ❌ No (generates reports) |
| sdd-plan-review | Multi-model spec review | ❌ No (generates feedback) |
| sdd-validate | Validate spec structure | ❌ No (validates only) |

**Conclusion:** No existing skill handles systematic structural spec modification

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Spec Modification System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  USER                                                         │
│    ↓                                                          │
│  sdd-modify SKILL (Interactive)                              │
│    │                                                          │
│    ├─ 1. Parse Input (review/JSON/interactive)              │
│    ├─ 2. Analyze & Preview (dry-run)                        │
│    ├─ 3. Request Approval (AskUserQuestion)                 │
│    ├─ 4. Backup Spec                                         │
│    ├─ 5. Invoke Subagent ──────┐                            │
│    ├─ 6. Validate Result        │                            │
│    ├─ 7. Journal Changes        │                            │
│    └─ 8. Report Status          │                            │
│                                  ↓                            │
│                    sdd-modify-subagent (Programmatic)        │
│                        │                                      │
│                        ├─ Load spec & modifications          │
│                        ├─ Validate structure                 │
│                        ├─ Apply with transaction             │
│                        ├─ Run sdd-validate                   │
│                        └─ Return results                     │
│                                                               │
│  OTHER SKILLS                                                │
│    ↓                                                          │
│  sdd-fidelity-review ─────┐                                 │
│  sdd-plan-review ─────────┼─> Invoke Subagent Directly      │
│  Custom Automation ────────┘                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 1: sdd-modify-subagent

### Purpose
Programmatic interface for spec modifications invocable by other skills

### File Location
`agents/sdd-modify.md` (~400 lines)

### Contract

**Required Information:**
```json
{
  "spec_id": "my-spec-2025-11-06-001",
  "modifications_source": "path/to/modifications.json" | inline_json,
  "validate": true,
  "dry_run": false
}
```

**Returns:**
```json
{
  "success": true,
  "modifications_applied": 5,
  "validation_result": "pass",
  "error_messages": [],
  "rollback_performed": false
}
```

### Workflow
1. Load spec and modification data
2. Validate modification structure
3. Preview changes (if dry_run=true)
4. Apply with transaction rollback on failure
5. Run sdd-validate
6. Return structured results

### Invocation Pattern
```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Apply modifications from suggestions.json to spec my-spec-001. Validate and report results.",
  description: "Apply spec modifications"
)
```

### Key Features
- **Idempotent** - Safe to apply same modifications multiple times
- **Transactional** - All-or-nothing with automatic rollback
- **Validation** - Always runs sdd-validate after application
- **Error Handling** - Structured error reporting

---

## Component 2: sdd-modify Skill

### Purpose
User-facing guided modification workflow with safety checks

### File Location
`skills/sdd-modify/SKILL.md` (~800 lines)

### Workflow Steps

#### 1. Parse Input
Accept multiple input formats:
- Review report file (`.md` from sdd-fidelity-review)
- JSON modification file
- Interactive guided input

#### 2. Analyze
- Extract modifications from input
- Check feasibility (validate against spec structure)
- Identify potential risks

#### 3. Preview
Show changes with diff-style output:
```
📋 Modification Preview

Task task-2-1: Update title
  Old: "Implement auth"
  New: "Implement OAuth 2.0 authentication"

Task task-2-3: Add verification step
  Adding: "Verify token expiration handling"

5 modifications total
```

#### 4. Confirm
Use `AskUserQuestion`:
```javascript
AskUserQuestion(
  questions: [{
    question: "Apply these 5 modifications to the spec?",
    header: "Confirm",
    options: [
      { label: "Apply", description: "Apply modifications with validation" },
      { label: "Dry-run again", description: "Show preview again" },
      { label: "Cancel", description: "Don't apply any changes" }
    ]
  }]
)
```

#### 5. Backup
Automatically create spec backup before modification

#### 6. Apply
Invoke `sdd-modify-subagent` with approved modifications

#### 7. Validate
Run `sdd-validate` and report results

#### 8. Journal
Document changes via `sdd-update`

#### 9. Report
Show summary:
```
✅ Modifications Applied Successfully

Applied: 5 modifications
Validation: PASSED
Backup: specs/.backups/my-spec-001-20251106.json

Changes:
- Updated 3 task descriptions
- Added 2 verification steps
```

### Invocation Pattern
```
Skill(sdd-toolkit:sdd-modify) "Apply fidelity review feedback to spec my-spec-001"
```

### Key Features
- **Guided workflow** - Step-by-step with clear prompts
- **Safety first** - Preview, backup, rollback
- **User approval** - Explicit confirmation required
- **Clear communication** - Progress indicators and error messages
- **Integration ready** - Works with review outputs

---

## Component 3: Example Files

### Location
`skills/sdd-modify/examples/`

### Files

#### 1. apply-review.md (~300 lines)
**Scenario:** Apply feedback from sdd-fidelity-review

Shows complete workflow:
1. Run fidelity review
2. Review identifies 5 issues
3. Use sdd-modify to apply fixes
4. Validation confirms correctness
5. Re-review shows issues resolved

#### 2. bulk-modify.md (~300 lines)
**Scenario:** Apply bulk modifications from JSON file

Demonstrates:
- Creating modification JSON file
- Validating modification structure
- Applying batch changes
- Handling errors gracefully

#### 3. interactive.md (~300 lines)
**Scenario:** Interactive guided modification

Shows:
- Starting skill without input file
- Interactive prompts for each change
- Building modifications step-by-step
- Reviewing all changes before application

---

## Integration with Existing Skills

### sdd-fidelity-review Enhancement

**Current State:** Generates review reports

**Enhancement:** After review completion, offer to apply fixes

```markdown
## After Review Completion

Found 5 issues requiring spec updates.

Would you like to apply these fixes systematically?

[Invokes sdd-modify-subagent with parsed suggestions]
```

**Update Location:** `skills/sdd-fidelity-review/SKILL.md`

**Changes:**
1. Add "Applying Review Feedback" section
2. Document closed-loop workflow: review → parse → modify → validate → re-review
3. Show CLI and skill invocation patterns

### sdd-plan-review Enhancement

**Current State:** Multi-model spec review before implementation

**Enhancement:** After review, offer to apply consensus recommendations

```markdown
## After Plan Review

3 models agree on 7 improvements:
- Update 5 task descriptions for clarity
- Add 2 missing verification steps

Apply consensus recommendations?

[Invokes sdd-modify-subagent]
```

**Update Location:** `skills/sdd-plan-review/SKILL.md`

**Changes:**
1. Add "Applying Plan Review Feedback" section
2. Cross-reference sdd-modify skill
3. Show automated workflow option

### sdd-update Enhancement

**Current State:** Tracks progress, journals decisions

**Enhancement:** Reference sdd-modify for structural changes

```markdown
## When to Use sdd-modify

Use `Skill(sdd-toolkit:sdd-modify)` for:
- Applying review feedback systematically
- Bulk spec modifications
- Restructuring spec based on implementation learnings

sdd-update handles task status and metadata; sdd-modify handles structural changes.
```

**Update Location:** `skills/sdd-update/SKILL.md`

**Changes:**
1. Add "Systematic Spec Modification" section
2. Clarify when to use sdd-update vs sdd-modify
3. Show handoff pattern

---

## Documentation Updates

### README.md

**Section:** Skills Overview (after sdd-validate)

**Add:**
```markdown
| `sdd-modify` | Apply spec modifications | "Apply fidelity review feedback systematically" "Bulk modify spec from JSON file" |
```

**Section:** Quick Start - Spec Modification

**Add:**
```bash
# Apply modifications systematically
sdd-modify my-spec-001 --from review-suggestions.json
```

### docs/spec-modification.md

**New Section:** Using sdd-modify Skill

Add comprehensive guide showing:
- When to use skill vs CLI
- Complete workflow example
- Integration with review workflows
- Troubleshooting common issues

### docs/review-workflow.md

**New Section:** Systematic Feedback Application

Document the closed-loop workflow:
```
Review → Parse → Modify → Validate → Re-review
```

Show how sdd-modify integrates with existing review workflows

---

## Implementation Order

### Phase 1: Core Components (Day 1)
1. ✅ Create `agents/sdd-modify.md` (subagent contract)
   - Define interface, workflow, error handling
   - Document invocation patterns
   - Include validation requirements

2. ✅ Create `skills/sdd-modify/SKILL.md` (skill documentation)
   - Complete workflow documentation
   - Usage examples
   - Integration patterns
   - Troubleshooting guide

### Phase 2: Examples (Day 1-2)
3. ✅ Create `skills/sdd-modify/examples/apply-review.md`
4. ✅ Create `skills/sdd-modify/examples/bulk-modify.md`
5. ✅ Create `skills/sdd-modify/examples/interactive.md`

### Phase 3: Integration (Day 2)
6. ✅ Update `skills/sdd-fidelity-review/SKILL.md` - Add handoff section
7. ✅ Update `skills/sdd-plan-review/SKILL.md` - Add handoff section
8. ✅ Update `skills/sdd-update/SKILL.md` - Add reference section

### Phase 4: Documentation (Day 2-3)
9. ✅ Update `README.md` - Add sdd-modify to skills list
10. ✅ Update `docs/spec-modification.md` - Add skill usage section
11. ✅ Update `docs/review-workflow.md` - Add systematic application section

---

## Key Design Decisions

### From Gemini Consensus Analysis

1. **Skill Wraps Subagent**
   - Skill = Interactive layer (user prompts, previews, confirmations)
   - Subagent = Programmatic core (structured input/output, no interaction)
   - Clear separation of concerns

2. **Idempotency**
   - Applying same modifications twice should be safe
   - Second application results in "no changes" not error
   - Important for automation and retry logic

3. **Clear Rollback Communication**
   - User must understand when transaction fails
   - Explicit message: "Spec remains unchanged due to validation failure"
   - Show what was attempted and why it failed

4. **Discoverability**
   - Update review skill docs to mention sdd-modify
   - Cross-reference throughout documentation
   - Clear workflow diagrams showing integration

5. **Safety First**
   - Always backup before modification
   - Always validate after modification
   - Always show preview before application
   - Always require explicit user approval (skill mode)

---

## Success Criteria

### User Experience
- ✅ Users can apply review feedback in 2-3 interactions
- ✅ Clear previews show exactly what will change
- ✅ Errors are understandable with suggested fixes
- ✅ Rollback is automatic and clearly communicated

### Technical
- ✅ Other skills can invoke modifications programmatically
- ✅ All modifications go through validation
- ✅ Transaction rollback works correctly
- ✅ Idempotent operations (safe to retry)

### Documentation
- ✅ Comprehensive skill documentation (~800 lines)
- ✅ Complete subagent contract (~400 lines)
- ✅ 3 detailed examples covering common scenarios
- ✅ Integration points clearly documented
- ✅ Workflow diagrams showing system integration

### Testing
- ✅ Unit tests for skill workflow logic
- ✅ Integration tests for subagent invocation
- ✅ End-to-end tests for complete workflows
- ✅ Error handling and rollback verification

---

## Files Summary

### New Files (5)
| File | Size | Purpose |
|------|------|---------|
| `agents/sdd-modify.md` | ~400 lines | Subagent contract |
| `skills/sdd-modify/SKILL.md` | ~800 lines | Main skill documentation |
| `skills/sdd-modify/examples/apply-review.md` | ~300 lines | Review feedback example |
| `skills/sdd-modify/examples/bulk-modify.md` | ~300 lines | Bulk modification example |
| `skills/sdd-modify/examples/interactive.md` | ~300 lines | Interactive workflow example |

**Total new content:** ~2,100 lines

### Modified Files (5)
| File | Changes |
|------|---------|
| `skills/sdd-fidelity-review/SKILL.md` | +100 lines (handoff section) |
| `skills/sdd-plan-review/SKILL.md` | +80 lines (handoff section) |
| `skills/sdd-update/SKILL.md` | +60 lines (reference section) |
| `README.md` | +30 lines (skills table, examples) |
| `docs/spec-modification.md` | +150 lines (skill usage guide) |

**Total modifications:** ~420 lines

### Grand Total
**~2,520 lines of new documentation and integration**

---

## Risk Mitigation

### Risk: Overlapping Functionality with sdd-update
**Mitigation:** Clear documentation of when to use each:
- sdd-update: Task status, metadata, progress tracking
- sdd-modify: Structural changes, bulk modifications, review feedback

### Risk: User Confusion About Which Tool to Use
**Mitigation:**
- Clear skill descriptions and use cases
- Cross-references in documentation
- Examples showing typical scenarios

### Risk: Maintenance Burden
**Mitigation:**
- Well-isolated components (SRP)
- Comprehensive test coverage
- Clear contracts and interfaces
- Documentation maintenance plan

### Risk: Breaking Changes to CLI
**Mitigation:**
- Skill wraps CLI, doesn't replace it
- CLI remains stable and available
- Skill provides orchestration layer only

---

## Future Enhancements

### Phase 2 (Future)
1. **Interactive Modification Builder**
   - GUI-like prompts for building modifications
   - Step-by-step task addition/removal
   - Real-time preview of changes

2. **Modification Templates**
   - Common modification patterns as templates
   - "Add verification task" template
   - "Restructure phase" template

3. **Diff Visualization**
   - Better visual diff output
   - Highlighting of changes
   - Side-by-side comparison

4. **Undo/Redo Support**
   - History of modifications
   - Ability to rollback to any point
   - Modification replay

5. **Automated Review Application**
   - sdd-fidelity-review automatically invokes sdd-modify
   - User approval still required
   - Streamlined workflow

---

## Conclusion

Creating both sdd-modify skill and subagent:
- ✅ **Completes the SDD feedback loop** - Review → Modify → Validate
- ✅ **Maintains architectural integrity** - Clear separation of concerns
- ✅ **Improves user experience** - Guided workflow with safety checks
- ✅ **Enables automation** - Programmatic interface for other skills
- ✅ **Simplifies maintenance** - Isolated, well-documented components

**Expert Recommendation:** Gemini strongly supports this approach based on SRP, user experience, and architectural fit.

**Next Step:** Create the subagent and skill documentation files following this plan.

---

**Status:** Ready for implementation
**Estimated Effort:** 2-3 days for complete implementation and documentation
**Dependencies:** None (all CLI tools already implemented)
