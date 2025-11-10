## Schema Lookup Research

### 1. Canonical Artifacts

- `documentation-schema.json` and `sdd-spec-schema.json` live in `src/claude_skills/schemas/` and ship with the package data, so both a source checkout and the installed wheel expose identical assets.
- The Claude plugin cache mirrors those files under `~/.claude/plugins/cache/sdd-toolkit/src/claude_skills/schemas/` and is now treated as the preferred lookup location.

### 2. Shared Loader Utility

- `claude_skills.common.schema_loader.load_json_schema()` centralises discovery logic. It searches in this order:
  1. `$CLAUDE_SDD_SCHEMA_CACHE/<schema>` (allows tests or alternate deployments to override).
  2. `~/.claude/plugins/cache/sdd-toolkit/src/claude_skills/schemas/<schema>` (plugin runtime).
  3. Package resources via `importlib.resources.files("claude_skills.schemas")`.
- Results are cached per schema name to avoid repeated file I/O. Callers can clear the cache via `load_json_schema.cache_clear()` if they update schemas on disk.

### 3. CLI Path Resolution Status

- `sdd-validate` invokes the loader automatically before running structural checks, so schema failures now surface as first-class validation errors (or warnings if the Draft 7 validator is unavailable).
- `code-doc` still uses an explicit `Path(__file__).parent.parent / 'documentation-schema.json'`. This works when run from source but will miss schemas inside an installed wheel. The next revision should switch to the shared loader to gain cache + fallback behaviour.

### 4. Runtime Dependencies

- Full Draft 7 validation requires the optional extra `pip install claude-skills[validation]` (installs `jsonschema>=4`). Without it, the loader still resolves schema locations and the CLI emits a warning that schema validation was skipped.
- Because both schemas remain part of package data, no additional packaging changes were required beyond documenting the optional dependency.

### 5. Recommended Usage

- Prefer calling `load_json_schema("sdd-spec-schema.json")` or `load_json_schema("documentation-schema.json")` in any future tooling.
- Tests that need deterministic schema behaviour can point `$CLAUDE_SDD_SCHEMA_CACHE` at a temp directory to supply fixtures or simulate missing schemas.
- When running inside the Claude plugin runtime, no configuration is necessary—the cache path resolution picks up the bundled schemas automatically.
