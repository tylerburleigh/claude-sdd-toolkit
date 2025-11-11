---
title: Consolidate AI Model Resolution Across CLI Consultations
status: draft
created: 2025-11-11
owner: core-platform
---

## Overview

Multiple SDD Toolkit skills independently determine which AI model to request when invoking external CLIs (Gemini, Codex, Cursor Agent). Logic has diverged across modules (`sdd_fidelity_review`, `run_tests`, others), leading to inconsistent defaults, duplicated configuration parsing, and missing model flags for some tools. This plan unifies model selection via a shared helper so all AI consultations:

- Respect explicit CLI overrides (`--model` or skill-specific parameters)
- Derive defaults from the centralized `.claude/ai_config.yaml`
- Apply hard-coded fallbacks only when configuration data is absent
- Pass the resolved model to the underlying CLI for every supported tool

## Goals & Success Criteria

- ✅ Extract a reusable helper (e.g., `resolve_tool_model(skill_name, tool, *, override=None, context=None)`) inside `claude_skills.common.ai_config`.
- ✅ Update all skills that consult AI tools to use the helper (fidelity review, run-tests, sdd-plan, sdd-render, sdd-update, others).
- ✅ Ensure Cursor Agent invocations include `--model` when configuration provides one.
- ✅ Standardize cache keys, progress emitters, and telemetry to report the resolved model.
- ✅ Expand tests to cover configuration-driven model resolution and CLI overrides for each skill.

## Non-Goals

- Rewriting tool detection/availability logic (already shared).
- Introducing provider abstractions (covered by separate `provider-abstraction-refactor` spec).
- Changing configuration schema beyond supporting consolidated helpers.

## Current State Summary

- `sdd_fidelity_review` recently added `_resolve_tool_model` and passes model flags for Gemini/Codex but had ad-hoc logic.
- `run_tests.consultation` implements `get_model_for_tool` with failure-type overrides.
- Other skills either omit model flags or rely on manual override parsing.
- Cache keys and progress events may omit models, reducing observability.

## Proposed Implementation

### Phase 1 – Shared Helper Foundations
1. Introduce `resolve_tool_model(skill_name, tool, override=None, context=None)` inside `claude_skills.common.ai_config`.
   - Use `load_skill_config` to read priorities.
   - Support optional context dict for extensions (e.g., run-tests failure-type overrides).
   - Fall back to `DEFAULT_MODELS` if config lacks entries.
2. Provide helper to build per-tool model maps: `resolve_models_for_tools(skill_name, tools, override=None, context=None)` returning `{tool: model or None}`.
3. Add unit tests for helper functions covering:
   - Configured priorities
   - Missing config (uses defaults)
   - CLI override precedence
   - Cursor-agent support.

### Phase 2 – Skill Integrations
1. **sdd_fidelity_review**
   - Remove `_resolve_tool_model`; import helper.
   - Ensure `consult_ai_on_fidelity` and `consult_multiple_ai_on_fidelity` use shared helper.
   - Update progress emitter and cache key usage to reflect resolved model(s).
2. **run_tests.consultation**
   - Refactor `get_model_for_tool` to delegate to helper while preserving failure-type overrides (pass as context).
   - Adjust related helper functions (e.g., `get_flags_for_tool`) if needed.
3. **Other skills**
   - Audit CLI modules (`sdd_plan`, `sdd_render`, `sdd_update`, `sdd_pr`, etc.) for direct `execute_tool` calls.
   - Replace inline model handling with helper usage.
   - Ensure multi-tool flows pass per-tool models to `execute_tools_parallel`.
4. Update cache logic to incorporate resolved models when generating keys.

### Phase 3 – Testing & Verification
1. Extend unit tests for each skill to assert helper usage and expected `execute_tool` arguments.
2. Add integration tests (or update existing ones) ensuring CLI invocations include `--model` flags when configuration provides models.
3. Verify progress events and telemetry include the resolved model values.
4. Run targeted regression suite:
   - `pytest src/claude_skills/claude_skills/tests/unit/test_common/test_ai_config.py`
   - `pytest src/claude_skills/claude_skills/tests/unit/test_sdd_fidelity_review`
   - `pytest src/claude_skills/claude_skills/tests/integration/test_sdd_*`

### Phase 4 – Documentation & Cleanup
1. Update `docs/DOCUMENTATION.md` and `CHANGELOG.md` with consolidation details.
2. Refresh `.claude` template comments to mention automatic model selection.
3. Remove obsolete helper functions or duplication.

## Progress Log

- **2025-11-11 (EOD)**  
  - ✅ Completed Phase 1 helpers (`resolve_tool_model`, `resolve_models_for_tools`) with comprehensive unit coverage in `test_common/test_ai_config_models.py`.  
  - ✅ Refactored `sdd_fidelity_review` single-tool and multi-tool flows to use shared helpers. Progress emitters now include per-tool model maps and summaries; cache keys accept structured model data.  
  - ✅ Updated fidelity CLI/report pipeline to surface consulted model metadata (`count`, per-tool map, summary string).  
  - ⏳ Next: propagate helpers into `run_tests`, `code_doc`, and `sdd_plan_review` workflows; extend their CLIs & tests accordingly.  
  - ⏳ Follow-up: documentation/changelog updates once remaining skills consume the shared helpers.

## Risks & Mitigations

- **Risk:** Skills relying on bespoke overrides may lose behavior.
  - *Mitigation:* Support optional context parameter allowing specialized overrides per skill.
- **Risk:** Missing model in config could lead to unexpected `None` model.
  - *Mitigation:* Ensure helper always falls back to defaults bundled in code.
- **Risk:** Cache key changes could invalidate existing cache entries.
  - *Mitigation:* Bump cache version tag or document expected cache invalidation.

## Open Questions

- Do any skills require dynamic model selection beyond config/failure-type (e.g., per-spec overrides)? If so, incorporate into context handling.
- Should helper handle tool-specific CLI quirks (e.g., additional flags) or stay focused on model resolution?

## Deliverables

- Updated shared helper module with tests.
- Refactored skills invoking AI tools.
- Verified CLI invocations with consistent model flags.
- Documentation and changelog entries summarizing the change.
