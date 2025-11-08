# CLI Output Audit Plan

## Purpose

This document tracks the comprehensive audit of all CLI modules in the SDD toolkit to ensure output follows YAGNI/KISS principles. Each module will be analyzed for verbosity, implementation details leaking into user-facing output, and opportunities for consolidation.

## Methodology

**All audits follow the process documented in:** [`SKILL_REVIEW_INSTRUCTIONS.md`](SKILL_REVIEW_INSTRUCTIONS.md)

### Quick Start

**To audit a module:**

1. Use the Task tool with Haiku model for cost efficiency:
   ```python
   Task(
     subagent_type="general-purpose",
     model="haiku",
     description="Audit sdd-<module-name> CLI output",
     prompt="""Follow SKILL_REVIEW_INSTRUCTIONS.md to audit sdd-<module-name>...

     Save your complete analysis to: docs/research/cli-output-audit-sdd-<module-name>.md"""
   )
   ```

2. Review the generated audit in `docs/research/`
3. Mark the checkbox below as complete: `- [x]`
4. Add completion date and link to audit file

### Where Results Are Saved

All audit reports are saved to: **`docs/research/cli-output-audit-<module-name>.md`**

---

## Progress Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Completed | 0 | 0% |
| 🔄 In Progress | 0 | 0% |
| ⏳ Not Started | 18 | 100% |
| **TOTAL** | **18** | **100%** |

---

## Priority 1: Core SDD Commands (9 modules)

These are the main workflow commands users interact with most frequently.

### - [ ] sdd-update
**Description:** Progress tracking and documentation for spec-driven development
- **CLI:** `/src/claude_skills/claude_skills/sdd_update/cli.py`
- **SKILL.md:** `/skills/sdd-update/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-update.md`
- **Priority:** High
- **Commands:** update-status, mark-blocked, unblock-task, add-journal, complete-task, complete-spec, activate-spec, add-verification, execute-verify, move-spec, time-report, status-report, audit-spec, query-tasks, get-task, list-phases, check-complete, list-blockers, reconcile-state, check-journaling, bulk-journal, sync-metadata, update-task-metadata, create-task-commit, list-specs, add-revision, add-assumption, list-assumptions, update-estimate, add-task, remove-task

### - [ ] sdd-validate
**Description:** Spec validation and auto-fix capabilities
- **CLI:** `/src/claude_skills/claude_skills/sdd_validate/cli.py`
- **SKILL.md:** `/skills/sdd-validate/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-validate.md`
- **Priority:** High
- **Commands:** validate, fix, validate-file

### - [ ] sdd-next
**Description:** Task preparation and next-task selection
- **CLI:** `/src/claude_skills/claude_skills/sdd_next/cli.py`
- **SKILL.md:** `/skills/sdd-next/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-next.md`
- **Priority:** High
- **Commands:** next-task, prepare-task, list-tasks, show-dependencies, validate-spec, detect-project, list-files, show-context, update-context, reset-context, get-next-verify, gather-context, show-prompt

### - [ ] sdd-plan
**Description:** Specification creation and planning
- **CLI:** `/src/claude_skills/claude_skills/sdd_plan/cli.py`
- **SKILL.md:** `/skills/sdd-plan/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-plan.md`
- **Priority:** High
- **Commands:** create, interactive, from-template, list-templates

### - [ ] sdd-plan-review
**Description:** Multi-model specification review
- **CLI:** `/src/claude_skills/claude_skills/sdd_plan_review/cli.py`
- **SKILL.md:** `/skills/sdd-plan-review/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-plan-review.md`
- **Priority:** High
- **Commands:** review, review-file

### - [ ] sdd-render
**Description:** Render JSON specs to human-readable markdown
- **CLI:** `/src/claude_skills/claude_skills/sdd_render/cli.py`
- **SKILL.md:** `/skills/sdd-render/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-render.md`
- **Priority:** Medium
- **Commands:** render, render-file

### - [ ] sdd-pr
**Description:** AI-powered pull request creation
- **CLI:** `/src/claude_skills/claude_skills/sdd_pr/cli.py`
- **SKILL.md:** `/skills/sdd-pr/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-pr.md`
- **Priority:** Medium
- **Commands:** create, create-from-spec

### - [ ] sdd-fidelity-review
**Description:** Compare implementation against spec requirements
- **CLI:** `/src/claude_skills/claude_skills/sdd_fidelity_review/cli.py`
- **SKILL.md:** `/skills/sdd-fidelity-review/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-fidelity-review.md`
- **Priority:** High
- **Commands:** fidelity-review, task-review, phase-review

### - [ ] sdd-modify
**Description:** Systematic spec modification and review feedback application
- **CLI:** `/src/claude_skills/claude_skills/sdd_spec_mod/cli.py`
- **SKILL.md:** `/skills/sdd-modify/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-sdd-modify.md`
- **Priority:** Medium
- **Commands:** apply-modifications, parse-review

---

## Priority 2: Documentation & Testing Commands (3 modules)

Nested CLI commands for code documentation and testing.

### - [ ] code-doc
**Description:** Multi-language codebase documentation generation
- **CLI:** `/src/claude_skills/claude_skills/code_doc/cli.py`
- **SKILL.md:** `/skills/code-doc/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-code-doc.md`
- **Priority:** Medium
- **Namespace:** `sdd doc generate`
- **Commands:** generate (default)

### - [ ] doc-query
**Description:** Query machine-readable codebase documentation
- **CLI:** `/src/claude_skills/claude_skills/doc_query/cli.py`
- **SKILL.md:** `/skills/doc-query/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-doc-query.md`
- **Priority:** Medium
- **Namespace:** `sdd doc query`
- **Commands:** query (default)

### - [ ] run-tests
**Description:** Comprehensive pytest testing and debugging framework
- **CLI:** `/src/claude_skills/claude_skills/run_tests/cli.py`
- **SKILL.md:** `/skills/run-tests/SKILL.md`
- **Audit:** `docs/research/cli-output-audit-run-tests.md`
- **Priority:** High
- **Namespace:** `sdd test run`
- **Commands:** run (default), debug, investigate

---

## Priority 3: Utility Commands (2 modules)

Support utilities for context tracking and cache management.

### - [ ] context
**Description:** Context tracking for spec-driven workflows
- **CLI:** `/src/claude_skills/claude_skills/context_tracker/cli.py`
- **SKILL.md:** N/A (utility command)
- **Audit:** `docs/research/cli-output-audit-context.md`
- **Priority:** Low
- **Commands:** context, session-marker

### - [ ] cache
**Description:** Cache management for fidelity reviews and plan reviews
- **CLI:** `/src/claude_skills/claude_skills/common/cache/cli.py`
- **SKILL.md:** N/A (utility command)
- **Audit:** `docs/research/cli-output-audit-cache.md`
- **Priority:** Low
- **Commands:** cache-info, cache-clear, cache-stats

---

## Priority 4: Development Commands (4 modules)

Internal development utilities (lower priority for YAGNI/KISS audit).

### - [ ] skills-dev start-helper
**Description:** Start Claude Code helper process
- **CLI:** `/src/claude_skills/claude_skills/cli/skills_dev/start_helper.py`
- **SKILL.md:** N/A (internal dev tool)
- **Audit:** `docs/research/cli-output-audit-skills-dev-start-helper.md`
- **Priority:** Low
- **Namespace:** `sdd skills-dev start-helper`

### - [ ] skills-dev setup-permissions
**Description:** Setup project permissions for skills
- **CLI:** `/src/claude_skills/claude_skills/cli/skills_dev/setup_permissions.py`
- **SKILL.md:** N/A (internal dev tool)
- **Audit:** `docs/research/cli-output-audit-skills-dev-setup-permissions.md`
- **Priority:** Low
- **Namespace:** `sdd skills-dev setup-permissions`

### - [ ] skills-dev gendocs
**Description:** Generate documentation for skills
- **CLI:** `/src/claude_skills/claude_skills/cli/skills_dev/gendocs.py`
- **SKILL.md:** N/A (internal dev tool)
- **Audit:** `docs/research/cli-output-audit-skills-dev-gendocs.md`
- **Priority:** Low
- **Namespace:** `sdd skills-dev gendocs`

### - [ ] skills-dev migrate
**Description:** Data migration utilities
- **CLI:** `/src/claude_skills/claude_skills/cli/skills_dev/migrate.py`
- **SKILL.md:** N/A (internal dev tool)
- **Audit:** `docs/research/cli-output-audit-skills-dev-migrate.md`
- **Priority:** Low
- **Namespace:** `sdd skills-dev migrate`

---

## Batch Audit Invocation

To audit multiple modules in parallel, use a single message with multiple Task calls:

```python
# Priority 1 batch (Core commands)
Task(
  subagent_type="general-purpose",
  model="haiku",
  description="Audit sdd-update CLI output",
  prompt="Follow SKILL_REVIEW_INSTRUCTIONS.md to audit sdd-update command. Save to: docs/research/cli-output-audit-sdd-update.md"
)

Task(
  subagent_type="general-purpose",
  model="haiku",
  description="Audit sdd-validate CLI output",
  prompt="Follow SKILL_REVIEW_INSTRUCTIONS.md to audit sdd-validate command. Save to: docs/research/cli-output-audit-sdd-validate.md"
)

Task(
  subagent_type="general-purpose",
  model="haiku",
  description="Audit sdd-next CLI output",
  prompt="Follow SKILL_REVIEW_INSTRUCTIONS.md to audit sdd-next command. Save to: docs/research/cli-output-audit-sdd-next.md"
)

# Continue for remaining Priority 1 modules...
```

**Note:** Launch in a single message for true parallel execution.

---

## Appendix

### Registry Files

**Main Registry:** `/src/claude_skills/claude_skills/cli/sdd/registry.py`
- Registers all core SDD subcommands (lines 36-47)
- Registers nested CLIs (doc, test, skills-dev)
- Optional orchestration registration (Phase 3, not yet implemented)

**Skills-Dev Nested Registry:** `/src/claude_skills/claude_skills/cli/skills_dev/registry.py`
- Registers internal development utilities

### Module Categorization

**Core SDD Commands (9):** Main workflow commands with full SKILL.md documentation
**Documentation & Testing (3):** Nested under `sdd doc` and `sdd test` namespaces
**Utility Commands (2):** Support utilities, no SKILL.md (not workflow-oriented)
**Development Commands (4):** Internal tooling, no SKILL.md (developer-only)

### Modules Without SKILL.md

The following modules intentionally have no SKILL.md:
- **context / session-marker:** Utility for internal tracking
- **cache:** Utility for cache management
- **skills-dev/* (4 modules):** Internal development tools

These are not part of the main SDD workflow and are used primarily by developers or automation.

### Optional Phase 3 Module

**Workflow Orchestration:** Not yet implemented
- Registration: `register_workflow()` (optional import)
- Location: `/src/claude_skills/orchestration/workflows.py` (planned)
- Status: Scaffolded with graceful ImportError handling
- Will be added in Phase 3 of development

---

## Completion Checklist

After completing all audits:

- [ ] Review all 18 audit reports for common patterns
- [ ] Create a consolidated findings document
- [ ] Identify toolkit-wide verbosity patterns
- [ ] Prioritize fixes by impact vs. effort
- [ ] Create implementation specs for high-priority fixes
- [ ] Update SKILL.md examples to match improved output
- [ ] Document new output standards for future commands

---

**Last Updated:** 2025-01-08
**Total Modules:** 18
**Completed:** 0
**Remaining:** 18
