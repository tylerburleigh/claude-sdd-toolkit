# CLI Output Audit: sdd-plan

**Command Module:** sdd-plan
**CLI Location:** `/src/claude_skills/claude_skills/sdd_plan/cli.py`
**SKILL.md:** `/skills/sdd-plan/SKILL.md`
**Audit Date:** 2025-11-09
**Methodology:** YAGNI/KISS Principle Application

---

## Overview

The `sdd-plan` CLI module provides three main commands for specification creation and planning:
1. `sdd create` - Creates new specifications from templates
2. `sdd analyze` - Analyzes codebase for planning context
3. `sdd template` - Manages and displays spec templates

This audit evaluates whether output follows YAGNI (You Aren't Gonna Need It) and KISS (Keep It Simple, Stupid) principles, ensuring users see outcomes rather than process details.

---

## Command Analysis

### 1. Command: `sdd create`

**Purpose:** Create a new specification from a template

#### 1.1 Current Output Simulation

```
$ sdd create "User Authentication" --template medium

Creating new specification: User Authentication
Spec created in pending/. Spec created: specs/pending/user-auth-2025-11-09-001.json
Template: medium
Spec ID: user-auth-2025-11-09-001
Phases: 3
Estimated hours: 24

Next steps:
1. Edit the spec file to add detailed tasks
2. Validate: sdd validate user-auth-2025-11-09-001
3. Review: sdd review (if sdd-plan-review is available)
4. Activate: sdd activate-spec user-auth-2025-11-09-001
5. Start work: sdd next-task
```

**Current Line Count:** 11 lines

#### 1.2 Printer Call Trace

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 22 | `info` | Creating new specification: {name} | Action (internal) |
| 51 | `success` | Spec created in pending/. {message} | Outcome + Verbose |
| 54 | `detail` | Template: {template} | Metadata |
| 55 | `detail` | Spec ID: {spec['spec_id']} | Metadata |
| 56 | `detail` | Phases: {count} | Metadata |
| 57 | `detail` | Estimated hours: {hours} | Metadata |
| 59 | `info` | Next steps: | Guidance |
| 60-64 | `detail` | 1-5. [steps] | Guidance |

#### 1.3 YAGNI/KISS Classification

| Line | Classification | Reasoning |
|------|-----------------|-----------|
| 22 | ❌ Remove | Implementation detail - "Creating..." announces internal process |
| 51 | 🔄 Consolidate | Redundant success message + path; too much in one line |
| 54-57 | ✅ Keep | Metadata users need: template, ID, scope, effort estimate |
| 59-64 | 🔄 Consolidate | Guidance is helpful but format is verbose; can be more concise |

#### 1.4 Proposed Minimal Output

```
$ sdd create "User Authentication" --template medium

✓ Specification created
  Spec ID: user-auth-2025-11-09-001
  Location: specs/pending/user-auth-2025-11-09-001.json
  Template: medium (3 phases, 24h estimated)

Next: sdd validate <spec-id>, then sdd activate-spec <spec-id>
```

**Proposed Line Count:** 6 lines
**Reduction:** 45% (11 → 6 lines)

#### 1.5 Output Quality Issues

**Issue 1: Duplicate Success Message**
- Line 22: `printer.info("Creating new specification: {args.name}")` — announces process
- Line 51: `printer.success("Spec created in pending/. {message}")` — announces outcome
- **Problem:** Two messages for same outcome; first is internal detail
- **Impact:** Verbose, users don't care about "creating" process step

**Issue 2: Path Redundancy**
- `printer.success()` says "Spec created in pending/"
- `printer.detail()` shows Spec ID
- Users must infer path from both messages
- **Problem:** Users don't care about "pending/" subfolder; it's implementation detail
- **Impact:** Confuses users about directory structure

**Issue 3: Verbose Next Steps**
- Lines 60-64 show 5 separate `.detail()` calls
- Each step takes its own line with numbering
- Format doesn't match typical CLI guidance
- **Problem:** Could be more concise
- **Impact:** Takes 5 lines for what could be 1-2

#### 1.6 Root Cause Analysis

**Root Cause:** Each operation was designed to announce its own workflow because it can be called independently or composed. When composed in `cmd_create`, all these messages accumulate.

The design assumes users want to see every sub-step of spec creation, but YAGNI principle says: show outcomes only.

---

### 2. Command: `sdd analyze`

**Purpose:** Analyze codebase to help with planning context (checks for specs directory, generates documentation stats)

#### 2.1 Current Output Simulation

```
$ sdd analyze .

Analyzing codebase: /Users/user/myproject
Project Context
✓ Specs directory: /Users/user/myproject/specs
Codebase Documentation
✓ Documentation available (doc-query)
  Total modules: 42
  Total classes: 156
  Total functions: 1247
  Average complexity: 2.3

You can use doc-query for faster spec planning:
  doc-query search <keyword>
  doc-query context <feature>
  doc-query dependencies <file>
```

**Current Line Count:** 13 lines

#### 2.2 Printer Call Trace

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 77 | `info` | Analyzing codebase: {directory} | Action (internal) |
| 83 | `header` | Project Context | Structure |
| 86 | `success` | ✓ Specs directory: {path} | Outcome |
| 94 | `header` | Codebase Documentation | Structure |
| 97 | `success` | ✓ Documentation available (doc-query) | Outcome |
| 100-103 | `detail` | Total modules, classes, functions, complexity | Metadata |
| 105 | `info` | You can use doc-query for faster spec planning: | Guidance |
| 106-108 | `detail` | Command examples | Guidance |

#### 2.3 YAGNI/KISS Classification

| Line | Classification | Reasoning |
|------|-----------------|-----------|
| 77 | ❌ Remove | Internal process announcement |
| 83 | 🔄 Consolidate | Structural header; could be implicit |
| 86 | ✅ Keep | Outcome: specs directory exists/location |
| 88-89 (not shown, warning case) | ❌ Remove/Consolidate | If no specs, just indicate that — no mkdir suggestion in output |
| 94 | 🔄 Consolidate | Structural header; could be implicit |
| 97 | ✅ Keep | Outcome: documentation is available |
| 100-103 | ✅ Keep | Metadata users need for planning decisions |
| 105-108 | 🔄 Consolidate | Helpful but could be more concise |

#### 2.4 Proposed Minimal Output

**When documentation IS available:**
```
$ sdd analyze .

✓ Project ready for planning
  Specs directory: /Users/user/myproject/specs
  Codebase analyzed: 42 modules, 156 classes, 1247 functions (avg complexity: 2.3)

Tip: Use doc-query search <keyword> for faster planning
```

**When documentation is NOT available:**
```
$ sdd analyze .

✓ Project structure found
  Specs directory: /Users/user/myproject/specs
  ⚠ Codebase documentation not available

Generate documentation for faster analysis:
  sdd doc generate
```

**Proposed Line Count:** 4-6 lines
**Reduction:** 50-65% (13 → 4-6 lines)

#### 2.5 Output Quality Issues

**Issue 1: Structural Headers as Announcements**
- Lines 83 & 94: `printer.header()` used for "Project Context" and "Codebase Documentation"
- These are structural markers, not user-facing information
- **Problem:** Headers suggest separate output sections when they're really one unified outcome
- **Impact:** Users see redundant structure rather than cohesive result

**Issue 2: Action Announcement**
- Line 77: `printer.info("Analyzing codebase: {directory}")` announces the process
- This is shown BEFORE analysis completes
- **Problem:** Users don't need to know about internal process
- **Impact:** Extra noise; outcome is what matters

**Issue 3: Verbose Guidance**
- Lines 105-108: Three separate `printer.detail()` calls for command examples
- Could be condensed into single line or tip
- **Problem:** Guidance takes 4 lines when 1 would suffice
- **Impact:** Output feels verbose

**Issue 4: Misaligned Error Messaging**
- Lines 88-89 (warning case): If specs directory missing, shows mkdir suggestion
- This is implementation guidance, not analysis outcome
- **Problem:** Conflates missing specs (user responsibility) with analysis failure
- **Impact:** Users confused about what `analyze` actually does

#### 2.6 Root Cause Analysis

**Root Cause:** The command tries to teach users about best practices (generating docs, creating specs directories) rather than simply reporting what it found.

The design assumes all information is equally valuable, but KISS principle says: separate outcomes from teaching. Show what exists; let users decide on next steps.

---

### 3. Command: `sdd template`

**Purpose:** List, show, or apply spec templates

#### 3.1 Current Output Simulation (list action)

```
$ sdd template list

Available Templates
simple
  Name: Simple Feature
  Description: Basic feature with 1-2 phases, < 5 files
  Phases: 2
  Est. hours: 8
  Recommended for: Small features, bug fixes, simple refactoring

medium
  Name: Medium Feature
  Description: Standard feature with 2-4 phases, 5-15 files
  Phases: 3
  Est. hours: 24
  Recommended for: New features, moderate refactoring, API changes

[... complex and security templates follow with same format ...]

Usage: sdd create <name> --template <template-id>
```

**Current Line Count:** ~20+ lines (4 templates × 5 detail lines each + header + usage)

#### 3.2 Printer Call Trace (list action)

| Line | Type | Message | Classification |
|------|------|---------|-----------------|
| 131 | `header` | Available Templates | Structure |
| 135 | `info` | {template_id} | Metadata |
| 136 | `detail` | Name: {template_info['name']} | Metadata |
| 137 | `detail` | Description: {template_info['description']} | Metadata |
| 138 | `detail` | Phases: {template_info['phases']} | Metadata |
| 139 | `detail` | Est. hours: {template_info['estimated_hours']} | Metadata |
| 140 | `detail` | Recommended for: {template_info['recommended_for']} | Metadata |
| 142 | `info` | Usage: sdd create <name> --template <template-id> | Guidance |

#### 3.3 YAGNI/KISS Classification

| Line | Classification | Reasoning |
|------|-----------------|-----------|
| 131 | 🔄 Consolidate | Header is structural; doesn't communicate outcome |
| 135-140 | ✅ Keep | Template metadata is critical decision-making info |
| 142 | 🔄 Consolidate | Usage tip could be implicit in command output |

#### 3.4 Proposed Minimal Output

```
$ sdd template list

simple       2 phases, 8h   Small features, bug fixes
medium       3 phases, 24h  New features, moderate refactoring
complex      5 phases, 60h  Major features, architecture changes
security     4 phases, 40h  Auth/authz, validation, encryption

Usage: sdd create <name> --template <template-id>
```

**Proposed Line Count:** 6 lines
**Reduction:** 70% (20 → 6 lines)

#### 3.5 Output Quality Issues

**Issue 1: Over-Detailed Template Display**
- Each template shows: Name, Description, Phases, Hours, Recommended
- 5 `printer.detail()` calls per template
- For 4 templates = 20+ lines just for metadata
- **Problem:** Users don't need every field to make a choice
- **Impact:** Hard to scan; takes too long to choose

**Issue 2: Structural Noise**
- Each template ID printed as separate `printer.info()` line
- Wastes vertical space
- **Problem:** Could be table format or CSV
- **Impact:** Output is hard to scan

**Issue 3: Redundant Description Field**
- Lines 137-140 show: Name, Description, Phases, Hours, Recommended
- Description often overlaps with "Recommended for"
- **Problem:** Two fields saying similar things
- **Impact:** Verbose

#### 3.6 Root Cause Analysis

**Root Cause:** Template display was designed for individual inspection (`sdd template show`) and reused for list view.

The design assumes all fields are necessary for decision-making, but list view benefits from compact presentation. KISS principle: show just enough to choose, then drill down with `show` action if needed.

---

### 4. Command: `sdd template show`

**Purpose:** Show detailed information about a specific template

#### 4.1 Current Output Simulation

```
$ sdd template show medium

Medium Feature
Standard feature with 2-4 phases, 5-15 files
Recommended for: New features, moderate refactoring, API changes
Phases: 3
Estimated hours: 24
Complexity: medium
Risk level: medium
```

**Current Line Count:** 7 lines

#### 4.2 YAGNI/KISS Classification

**Assessment:** This command is appropriate. `show` action exists to provide detailed information for users who want to drill down. The verbose output is justified because users explicitly asked for details.

**Verdict:** ✅ **Appropriate** — Show command is designed for detailed inspection, so current output is justified.

---

## Summary Analysis

### Overall Metrics

| Command | Current Lines | Proposed Lines | Reduction | Verdict |
|---------|---------------|----------------|-----------|---------|
| create | 11 | 6 | 45% | Minor issues |
| analyze | 13 | 4-6 | 50-65% | Minor issues |
| template list | 20+ | 6 | 70% | Too verbose |
| template show | 7 | 7 | 0% | Appropriate |

### Common Issues Across Commands

1. **Process Announcements** (Lines 22, 77)
   - `"Creating new specification..."` and `"Analyzing codebase..."` announce internal workflow
   - Should be silent; users only care about outcome
   - **Pattern:** `printer.info()` calls that say "I am starting task X"

2. **Structural Headers** (Lines 83, 94, 131)
   - `"Project Context"`, `"Codebase Documentation"`, `"Available Templates"`
   - Serve no functional purpose except breaking output into sections
   - Could use formatting instead (blank lines, indentation)
   - **Pattern:** `printer.header()` for organization rather than information

3. **Metadata Over-Formatting** (Lines 54-57, 136-140)
   - Each metadata field on its own line with `printer.detail()`
   - Creates verbose output that's hard to scan
   - Could be consolidated into table or single-line format
   - **Pattern:** Multiple `printer.detail()` calls that form a logical group

4. **Verbose Guidance** (Lines 60-64, 105-108, 142)
   - Next steps shown as numbered list or command examples
   - Takes multiple lines when could be implicit or terse
   - **Pattern:** `printer.info()` + multiple `printer.detail()` for instructional content

### Quality Categories

**Appropriate (No Changes Needed)**
- `sdd template show` — Detail justified by explicit request

**Minor Issues (1-2 Improvements)**
- `sdd create` — Remove process announcement, consolidate guidance
- `sdd analyze` — Remove process announcement, flatten structure, consolidate guidance

**Too Verbose (Significant Reduction Possible)**
- `sdd template list` — 70% of output is redundant formatting

---

## Detailed Findings

### Finding 1: Unnecessary Process Announcements

**Files Affected:**
- `cli.py:22` — `printer.info("Creating new specification: {args.name}")`
- `cli.py:77` — `printer.info("Analyzing codebase: {directory}")`

**Classification:** Implementation Detail (internal)

**Evidence:**
- These announce the START of a process, not the OUTCOME
- Shown before operation completes
- Redundant with success/warning messages that follow
- Users don't ask "what operation is starting"; they ask "what happened"

**Impact:** +2 unnecessary lines per command

**Recommendation:** Remove both process announcements. Success/warning messages that follow are sufficient.

---

### Finding 2: Structural Headers Without Information

**Files Affected:**
- `cli.py:83` — `printer.header("Project Context")`
- `cli.py:94` — `printer.header("\nCodebase Documentation")`
- `cli.py:131` — `printer.header("Available Templates")`

**Classification:** Structural noise (over-organization)

**Evidence:**
- Headers separate related information that should be presented together
- "Project Context" just contains specs directory status
- "Codebase Documentation" just contains doc-query stats
- "Available Templates" just lists templates
- No structural information communicated; just visual break

**Impact:** +3 lines of overhead, +1 blank line each; reduces scannability

**Recommendation:** Use indentation or blank lines instead of headers. Headers should reserve their use for actual information (like phase names), not just structural breaks.

**Alternative:** Keep headers but reduce verbosity of content (combine multiple related fields into fewer lines)

---

### Finding 3: Over-Detailed Metadata Display

**Files Affected:**
- `cli.py:54-57` — Template metadata in create command
- `cli.py:136-140` — Template metadata in template list command
- `cli.py:100-103` — Codebase stats in analyze command

**Classification:** Verbose formatting (excessive lines per item)

**Evidence:**
```python
# Current (4 lines per template)
printer.detail(f"Template: {template}")
printer.detail(f"Spec ID: {spec['spec_id']}")
printer.detail(f"Phases: {len(...)}")
printer.detail(f"Estimated hours: {spec['metadata']['estimated_hours']}")

# Could be (1-2 lines)
printer.detail(f"{template} template: {phases} phases, {hours}h estimated")
```

**Impact:**
- Create command: 4 lines → could be 1-2 lines (50% reduction)
- Template list: 5 lines per template × 4 templates = 20 lines → could be 1 line per template (80% reduction)
- Analyze command: 4 detail lines → could be 1 line (75% reduction)

**Recommendation:** Consolidate related metadata into single lines. Use compact notation like "3 phases, 24h" instead of separate "Phases: 3" and "Est. hours: 24" lines.

---

### Finding 4: Verbose Guidance and Next Steps

**Files Affected:**
- `cli.py:59-64` — Next steps in create command (5 numbered steps)
- `cli.py:105-108` — Doc-query examples in analyze command (3 examples)
- `cli.py:142` — Usage in template list command (1 line but isolated)

**Classification:** Over-explanation (guidance that could be terse)

**Evidence:**
```python
# Current (5 lines)
printer.info("\nNext steps:")
printer.detail("1. Edit the spec file to add detailed tasks")
printer.detail("2. Validate: sdd validate {spec_id}")
printer.detail("3. Review: sdd review (if sdd-plan-review is available)")
printer.detail("4. Activate: sdd activate-spec {spec_id}")
printer.detail("5. Start work: sdd next-task")

# Could be (1-2 lines)
printer.info("Next: sdd validate <spec-id>, then sdd activate-spec <spec-id>")
```

**Impact:**
- Takes 6 lines when could be 1-2 lines
- Creates cognitive overload with 5 steps when only 2 are required next
- "Edit the spec file" (step 1) is obvious, not a next step

**Recommendation:** Show only REQUIRED next steps, not optional guidance. Keep terse.

---

### Finding 5: Confusing Spec Path Presentation

**Files Affected:**
- `cli.py:33` — `printer.warning("No specs/ directory found, creating specs/active/")`
- `cli.py:43` — Spec saved to `specs/pending/` but message says it
- `cli.py:51` — Success message includes "Spec created in pending/."

**Classification:** Redundant information (implementation detail)

**Evidence:**
- Users don't care about "pending/" subfolder structure
- That's an internal convention (pending → active → completed)
- Should just say "Spec created: /path/to/spec.json"
- Current messages mix folder structure with outcome

**Impact:** Confuses users about where spec is and why

**Recommendation:**
- Success message should be: `✓ Specification created: {spec['spec_id']}`
- Show full path in metadata: `Location: specs/pending/{spec_id}.json`
- Remove references to "pending/" subfolder from user-facing messages

---

## Verdict Summary

| Category | Assessment |
|----------|------------|
| **Overall Verbosity** | ⚠️ **Minor issues** — Most commands are reasonable but could be more concise |
| **Process Announcements** | ❌ **Remove** — Two commands announce internal processes unnecessarily |
| **Structural Organization** | ⚠️ **Reorganize** — Headers and formatting should be subtle, not prominent |
| **Metadata Presentation** | ⚠️ **Consolidate** — Too many single-field detail lines; combine related fields |
| **Guidance Output** | ⚠️ **Abbreviate** — Next steps and examples too verbose |
| **Information Clarity** | ✅ **Appropriate** — Users get the information they need, just formatted verbosely |

### Final Assessment

**Overall: ⚠️ Minor Issues**

The `sdd-plan` CLI is generally well-designed and not egregiously verbose. However, it violates YAGNI/KISS principles in specific areas:

1. **Process announcements** should be removed (silent operations)
2. **Structural headers** should be replaced with subtle formatting
3. **Metadata should be consolidated** (combine related fields)
4. **Guidance should be terse** (essential next steps only)

These improvements would reduce output by 30-50% while maintaining clarity and usability.

### Priority for Fixes

**High Priority:**
- Remove process announcements (lines 22, 77)
- Consolidate template metadata in list view (70% reduction possible)

**Medium Priority:**
- Flatten structure in analyze command (remove headers)
- Consolidate metadata fields into logical groups

**Low Priority:**
- Abbreviate guidance output
- Improve path presentation

---

## Recommended Refactored Output Examples

### Refactored `sdd create`

```
$ sdd create "User Authentication" --template medium

✓ Specification created
  ID: user-auth-2025-11-09-001
  Template: medium (3 phases, 24h)
  Location: specs/pending/user-auth-2025-11-09-001.json

Next: sdd validate <spec-id> && sdd activate-spec <spec-id>
```

**Lines:** 6 (vs 11) — 45% reduction

### Refactored `sdd analyze`

```
$ sdd analyze .

✓ Ready for planning
  Specs: /Users/user/myproject/specs
  Codebase: 42 modules, 156 classes, 1247 functions (avg complexity: 2.3)

Tip: sdd doc generate for faster semantic analysis
```

**Lines:** 5 (vs 13) — 62% reduction

### Refactored `sdd template list`

```
$ sdd template list

simple       2 phases, 8h   Small features, bug fixes
medium       3 phases, 24h  New features, moderate refactoring
complex      5 phases, 60h  Major features, architecture changes
security     4 phases, 40h  Auth/authz, validation, encryption

Use: sdd create <name> --template <template-id>
```

**Lines:** 6 (vs 20) — 70% reduction

---

## Implementation Notes

### Code Changes Required

1. **Remove process announcements:**
   - Delete line 22: `printer.info(f"Creating new specification: {args.name}")`
   - Delete line 77: `printer.info(f"Analyzing codebase: {directory}")`

2. **Consolidate metadata display:**
   - In `cmd_create`: Combine template, ID, phases, hours into 1-2 lines
   - In `cmd_template` list action: Format as table or CSV instead of nested detail lines

3. **Flatten structure:**
   - Remove header calls; use blank lines instead
   - Keep content dense and scannable

4. **Abbreviate guidance:**
   - Show only essential next steps
   - Make messages concise

### Testing Considerations

After refactoring:
- Run each command and verify output still communicates essential information
- Check that users can:
  - Understand command succeeded or failed
  - Know where files were saved
  - Have path to next action
- Verify no information loss for actual decision-making

---

## Conclusion

The `sdd-plan` CLI module demonstrates good design overall but has opportunities to better follow YAGNI/KISS principles. By removing process announcements, consolidating metadata displays, and abbreviating verbose guidance, the CLI can reduce output by 30-50% while maintaining or improving clarity.

The **primary issue** is that the CLI shows *how* it works (process steps, internal structure) rather than just *what* users need (outcomes and decisions). This is a common pattern in CLI tools and easily corrected by focusing on user intent: users want to know if the operation succeeded and what to do next. Everything else is optional.

**Recommendation:** Implement the suggested changes to align with YAGNI/KISS principles. The refactored output examples above provide a template for the improved version.
