# ModelChorus Provider Flows – Audit

## Scope & Sources

- Repository: `/home/tyler/Documents/GitHub/claude-model-chorus`
- Focus: files under `model_chorus/src/model_chorus/providers/`
- Goal: document responsibilities, entrypoints, and request/response contracts that should inform our Provider Abstraction Refactor.

## Shared Architecture

- **Base abstractions** (`base_provider.py`)
  - `ModelProvider` enforces `generate()` and `supports_vision()` plus shared config/modules list.
  - Dataclasses define the core contract surface:
    - `ModelConfig`: `model_id`, default temperature, capabilities (`TEXT_GENERATION`, `VISION`, `FUNCTION_CALLING`, `STREAMING`, `THINKING`), metadata dict.
    - `GenerationRequest`: prompt, optional system prompt, temperature, max tokens, streaming flag, inline images, continuation id, metadata dict.
    - `GenerationResponse`: text content, model name, token usage map, stop reason, metadata dict.
  - Provider lifecycle: instantiate with `provider_name`, `api_key`, optional config; populate `_available_models` for capability checks; `validate_api_key()` returns basic non-empty check.

- **CLI scaffolding** (`cli_provider.py`)
  - Introduces `CLIProvider` to encapsulate CLI execution, retries, and availability checks.
  - Responsibilities:
    - Build CLI commands (`build_command`) and parse outputs (`parse_response`) — delegated to concrete providers.
    - Execute commands asynchronously with `asyncio.create_subprocess_exec`, honoring `timeout` and `retry_limit`.
    - Provide exponential backoff for retryable errors; classify permanent failures (missing binaries, auth errors, 4xx).
    - `check_availability()` default uses `--version`; subclasses can override (Gemini uses `--help`).
    - Conversation continuity helper `_load_conversation_context()` loads JSON transcripts from `~/.model-chorus/conversations/{continuation_id}.json`.
  - Security posture:
    - CLI execution raises `ProviderUnavailableError` when binaries missing or blocked.
    - Ensures exceptions differentiate retryable vs permanent for orchestrator decisions.

- **Exports** (`__init__.py`) make `ModelProvider`, `CLIProvider`, all concrete providers importable as a bundle.

## Provider Implementations

### ClaudeProvider (`claude_provider.py`)

- **Responsibilities**
  - Wraps Anthropic `claude` CLI for text/vision/function-calling workloads.
  - Maintains capability lists (`VISION_MODELS`, `THINKING_MODELS`), reflecting which models support multimodal or “thinking” modes.
  - Initializes catalog of `opus`, `sonnet`, `haiku` with metadata (family, size).
- **Entry Points / Invocation**
  - Base command: `claude --print <prompt> --output-format json`.
  - Applies safety defaults: restricts tools to read-only set (`Read`, `Grep`, `Glob`, `WebSearch`, `WebFetch`, `Task`, `Explore`) and explicitly disallows `Write`, `Edit`, `Bash`.
  - System prompt appended via `--system-prompt`. Model selection pulled from `GenerationRequest.metadata["model"]`.
  - CLI lacks switches for temperature/max_tokens; those remain at model defaults or external config.
- **Data Contract**
  - Expects JSON output shaped as:
    ```json
    {
      "type": "result",
      "subtype": "success",
      "result": "...",
      "usage": {...},
      "modelUsage": {"claude-sonnet-...": {...}}
    }
    ```
  - Response parsing extracts:
    - `content` from `result`.
    - `model` from first `modelUsage` key (fallback `"unknown"`).
    - `usage` token counts.
    - Metadata retains raw payload, duration, cost estimates.
  - Raises `ValueError` on non-zero exit or invalid JSON, surfacing stderr.

### GeminiProvider (`gemini_provider.py`)

- **Responsibilities**
  - Integrates Google’s `gemini` CLI, covering Pro/Flash/Ultra.
  - Overrides `check_availability()` to run `gemini --help` (faster/more reliable than `--version`).
  - Declares `VISION_MODELS` = `{pro, flash, ultra}`; thinking-mode intentionally unsupported (CLI limitation).
- **Entry Points / Invocation**
  - Command template: `gemini "<system + prompt>" -m <model> --output-format json`.
  - System prompt is concatenated to prompt text; CLI doesn’t expose a separate flag.
  - Security: intentionally omits `--yolo`, keeping default read-only tool allowances.
  - Strict parameter gatekeeping—raises `ValueError` if caller supplies unsupported `temperature`, `max_tokens`, or non-default `thinking_mode`.
- **Data Contract**
  - CLI emits JSON like:
    ```json
    {
      "response": "...",
      "stats": {
        "models": {
          "gemini-2.5-pro": {
            "tokens": {"prompt": 10, "candidates": 50, "total": 60}
          }
        }
      }
    }
    ```
  - Parser maps `response` (or `content`) into `GenerationResponse.content`.
  - Model/usage derived from first `stats.models` entry; metadata keeps entire `stats`.
  - **Observation:** `supports_thinking()` references `self.THINKING_MODELS`, but that attribute is no longer defined (comment indicates removal). Calling this method raises `AttributeError`, signaling a maintenance gap we should avoid replicating.

### CodexProvider (`codex_provider.py`)

- **Responsibilities**
  - Bridges OpenAI `codex` CLI (`codex exec`) for GPT-4/GPT-3.5 style models.
  - Tracks which models support vision or function-calling.
  - Handles optional image inputs for multimodal prompts.
- **Entry Points / Invocation**
  - Command skeleton: `codex exec --json --sandbox read-only [--model <id>] [--image path] "<prompt>"`.
  - Sandbox enforced (`read-only`) to keep executions non-destructive; aligns with orchestrator security aims.
  - Additional temperature/token parameters assumed to live in CLI config rather than per-invocation flags.
  - Emits JSONL stream representing agent events; orchestration must consume entire stdout to reconstruct response.
- **Data Contract**
  - Parser scans each JSON line, extracting:
    - `thread.started` → thread id metadata (useful for continuation).
    - `item.completed` with `agent_message` → final text.
    - `turn.completed` → usage stats (`input_tokens`, `output_tokens`, `cached_input_tokens`).
  - Returns `GenerationResponse` with `stop_reason="completed"` and metadata containing `thread_id`.
  - Non-zero exit codes bubble up as `ValueError` with stderr context.

### CursorAgentProvider (`cursor_agent_provider.py`)

- **Responsibilities**
  - Wraps `cursor-agent` CLI for code-centric interactions.
  - Models: `default`, `fast`, `premium` (all emphasize code + function calling).
  - Supports temperature overrides, max token limits, and working-directory context injection.
- **Entry Points / Invocation**
  - Command layout: `cursor-agent chat --prompt "<prompt>" [--system ...] [--model ...] --temperature <val> [--max-tokens N] [--working-directory path] --json`.
  - Defaults temperature to 0.3 favoring deterministic code output.
  - Deliberately omits `--force`, keeping suggestions in non-mutating mode.
- **Data Contract**
  - CLI returns single JSON blob:
    ```json
    {
      "content": "...",
      "model": "cursor-default",
      "usage": {"input_tokens": 10, "output_tokens": 50},
      "finish_reason": "stop",
      "code_blocks": [...],
      "language": "python"
    }
    ```
  - Parser maps `content`, `model`, `usage`, `finish_reason`, and copies supplemental metadata (`code_blocks`, `language`, raw payload).
  - `supports_vision()` always `False`; `supports_code_generation()` true for declared models via FUNCTION_CALLING capability set.

## Additional Notes & Risks

- **Config alignment:** `.model-chorusrc` defines default provider selections and fallback order. Any abstraction we build should be able to ingest equivalent provider selection + override stacks.
- **Async execution:** All providers expect `async` orchestration. Our abstraction needs to preserve async boundaries or provide sync wrappers.
- **Capability metadata:** Each provider seeds `_available_models` immediately inside its constructor. Downstream consumers rely on `supports_capability()` queries; ensure our abstraction surfaces similar metadata for scheduling decisions.
- **Error semantics:** Providers consistently raise `ValueError` for parse/execution failures and rely on `ProviderUnavailableError` for missing CLIs. Maintaining these buckets will keep retry logic predictable.
- **Gemini bug:** Undefined `THINKING_MODELS` attribute is a concrete example of drift between design intent and implementation. When porting patterns, double-check optional capability helpers actually exist before referencing them.

## Suggested Next Steps

1. Normalize a provider registry interface mirroring the `ModelProvider` contract so our orchestrator can swap in ModelChorus-style providers without rewriting call sites.
2. Capture CLI-specific constraints (unsupported parameters, security flags) as structured metadata to prevent invalid requests before invocation.
3. Decide whether to import the JSON parsing logic as-is or wrap API/SDK equivalents to reduce CLI surface area in the long term.

