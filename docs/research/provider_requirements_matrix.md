# Provider Abstraction Requirements Matrix

## Purpose

- Translate consumer expectations into concrete requirements for the new provider abstraction so we can reuse ModelChorus patterns without regressing existing SDD workflows.
- Sources include:
  - `skills/run-tests/SKILL.md` plus `src/claude_skills/claude_skills/run_tests/consultation.py`
  - `src/claude_skills/claude_skills/sdd_fidelity_review/consultation.py`
  - `src/claude_skills/claude_skills/sdd_plan_review/{reviewer.py,synthesis.py}` and CLI docs in `README.md`
  - CLI-output research logs (`docs/research/run-tests/cli-output-audit-run-tests.md`, `docs/research/sdd-fidelity-review/cli-output-audit-sdd-fidelity-review.md`)
  - Shared tooling in `src/claude_skills/claude_skills/common/{ai_tools.py,progress.py}`

## Consumer Snapshots

### run-tests Skill
- Multi-agent consultation is mandatory after failed pytest runs; tool list rotates across Gemini, Codex, and Cursor (`skills/run-tests/SKILL.md`, lines 188–401).
- `consult_multiple_agents()` enforces a minimum of two providers, adds supplemental tools when availability is low, and relies on `ai_config.resolve_models_for_tools()` for per-tool model overrides (`src/claude_skills/claude_skills/run_tests/consultation.py`, lines 972–1060).
- Research backlog requests streaming tool output to reduce perceived verbosity (`docs/research/run-tests/cli-output-audit-run-tests.md`, lines 560–612).
- Needs graceful degradation: fall back to single-tool mode, emit friendly errors when binaries are missing, and support dry-run previews.

### sdd-fidelity-review
- Wraps `execute_tools_parallel()` but adds caching, per-tool enablement, and structured progress streaming via `ProgressEmitter` (`src/claude_skills/claude_skills/sdd_fidelity_review/consultation.py`, lines 724–840).
- CLI telemetry expects event types like `cache_check`, `ai_consultation`, `model_response`, and `cache_save` to stream in real time for long-running reviews (`docs/research/sdd-fidelity-review/cli-output-audit-sdd-fidelity-review.md`, lines 150–205).
- Requires deterministic model summaries (provider + model id) for audit trails and cache key generation.

### sdd-plan-review / plan-review CLI
- Detects available tools and always runs reviews in parallel, surfacing per-tool durations and failures (`src/claude_skills/claude_skills/sdd_plan_review/reviewer.py`, lines 1–140).
- Response synthesis must unwrap Gemini’s JSON envelope before passing raw markdown to downstream AI (`sdd_plan_review/synthesis.py`, lines 1–90) and reuses Gemini again for consensus building (lines 120–210).
- CLI UX in `README.md` demonstrates user-facing expectations: multi-model listing, consensus summaries, and explicit attribution (`README.md`, lines 430–480).

### Shared CLI Tooling (common.ai_tools + progress)
- `execute_tool()` standardizes security (read-only flags), timeout handling, cursor-agent fallbacks (strip `--json` when unsupported), and error taxonomy (success, timeout, not_found, invalid_output, error) (`common/ai_tools.py`, lines 400–640).
- `execute_tools_parallel()` requires thread-safe execution with per-tool timeouts plus aggregated stats for synthesis consumers (`common/ai_tools.py`, lines 677–760).
- `ProgressEmitter` streams JSON events to stdout/stderr and flushes after each write to avoid buffering, which consumers rely on for progress UIs.

## Requirements Matrix

| Requirement | run-tests skill | sdd-fidelity-review | sdd-plan-review / plan | Shared CLI tooling |
|-------------|-----------------|---------------------|------------------------|--------------------|
| **Tool selection & routing** | Needs auto-routing + minimum two agents, with supplemental fallbacks when preferred providers missing. | Filters enabled tools via config and skips unavailable binaries while logging warnings. | Detects installed tools (`check_tool_available`) and reports per-tool availability to users. | Must expose availability APIs plus consistent override hooks (`resolve_models_for_tools`). |
| **Prompt packaging & context** | Injects failure metadata, hypothesis, and optional code snippets; requires deterministic prompt reuse for dry-runs. | Adds scope identifiers for cache keys and includes spec/task metadata in prompts. | Generates structured spec review prompts and passes review type/context for model selection. | Base abstraction should support metadata dict, continuation ids, and optional attachments/images per ModelChorus `GenerationRequest`. |
| **Streaming / progress visibility** | Research backlog demands streamed tool output to cut verbosity (currently lacking). | ProgressEmitter already streams cache + consultation events; providers must surface streaming hooks. | Users watch live status (“✓ gemini completed (2.3s)”), so providers need per-tool completion callbacks. | Provider layer should expose optional streaming interfaces (e.g., async generators) without breaking blocking callers. |
| **Error handling & degradation** | Must recover from missing tools, timeouts, and invalid responses without aborting entire consult; degrade to single-agent mode. | Requires custom exceptions (NoToolsAvailableError, ConsultationTimeoutError) plus cache fallback semantics. | Needs clear user messaging when a tool fails yet consensus proceeds; CLI prints ✓/✗ statuses. | Provider API should emit structured statuses (success, timeout, not_found, invalid_output, error) with stderr payloads for logging. |
| **Response normalization** | Requires raw responses for synthesis plus metadata (duration, model) for logs. | Stores ToolResponse objects for caching and downstream parsing, so metadata must be serializable. | Must peel provider-specific wrappers (Gemini JSON) and retain raw markdown for AI synthesis. | Base layer should normalize content/model/usage metadata akin to ModelChorus `GenerationResponse`. |
| **Caching & persistence** | N/A today, but run-tests could reuse caches once provider responses become deterministic. | Cache keys depend on provider+model summary, so abstraction must expose canonical identifiers. | Stores parsed responses for later consensus review exports. | Provide hooks for deterministic serialization plus hashed provider/model identifiers. |
| **Security & sandboxing** | Tools must stay read-only (no `--force`/write commands) when invoked from automation. | Same constraint; CLI wrappers enforce safe flags. | Same constraint; CLI commands executed non-interactively. | Abstraction should encapsulate provider-specific safety flags (mirroring ModelChorus CLI providers). |

## Observations & Gaps

1. **Streaming parity** – run-tests lacks streaming even though fidelity-review already emits real-time events; provider abstraction should deliver a unified streaming interface so both consumers can opt-in without bespoke plumbing.
2. **Error taxonomy drift** – custom exceptions in skills map loosely to `ToolStatus` enums; aligning on a shared enum (success/timeout/not_found/error) prevents double-wrapping.
3. **Model identity** – caches and audit logs need consistent `<provider>:<model>` strings; today each skill formats this independently. Provider abstraction should expose canonical identifiers just like ModelChorus `ModelConfig`.
4. **Wrapper parsing** – plan-review manually unwraps Gemini JSON; moving wrapper stripping into providers keeps consumers focused on business logic.
5. **Configuration surface** – `ai_config.resolve_models_for_tools()` is heavily used; provider registry must integrate with config resolution to keep overrides centralized.

## Next Steps

1. Define a ProviderContext API mirroring ModelChorus `ModelProvider`/`GenerationRequest`, ensuring it surfaces streaming hooks, metadata, and canonical model identifiers.
2. Add middleware that maps ProviderContext statuses to `ToolStatus`, so legacy consumers continue to receive familiar enums while adopting the new abstraction.
3. Prototype a streaming adapter for run-tests using the same ProgressEmitter events as fidelity-review to validate parity before wiring it into the rest of the CLI.
