# doc scope Command Examples

This directory contains example outputs from the `sdd doc scope` command, demonstrating both the `--plan` and `--implement` presets in Markdown and JSON formats.

## Example Files

| File | Format | Preset | Description |
|------|--------|--------|-------------|
| `plan-markdown-example.md` | Markdown | `--plan` | Module summary and complexity analysis for planning |
| `plan-json-example.json` | JSON | `--plan` | JSON output of planning data |
| `implement-markdown-example.md` | Markdown | `--implement` | Function callers, call graph, and class usage for implementation |
| `implement-json-example.json` | JSON | `--implement` | JSON output of implementation data |

## When to Use Each Preset

### --plan Preset

**Use when:** You're planning a feature, refactoring, or need to understand a module's architecture.

**Provides:**
- Module summary with docstring
- Statistics (class count, function count, complexity metrics)
- Top complex functions (helps identify hotspots)
- Dependency counts

**Example use cases:**
- Planning a refactoring: identify complex functions that need attention
- Estimating implementation effort: review module statistics
- Understanding module architecture before making changes

**Command:**
```bash
sdd doc scope <module-path> --plan
```

### --implement Preset

**Use when:** You're implementing changes and need to understand function relationships and dependencies.

**Provides:**
- Function callers (who calls this function)
- Call graph (what this function calls, bidirectional)
- Instantiated classes in the module (runtime dependencies)

**Example use cases:**
- Modifying a function: see who calls it to assess impact
- Understanding dependencies: review the call graph
- Finding runtime patterns: see which classes are frequently instantiated

**Command:**
```bash
sdd doc scope <module-path> --implement --function <function-name>
```

**Note:** The `--function` flag is optional but highly recommended for `--implement`. Without it, you'll only see instantiated classes.

## Regenerating Examples

These examples are deterministic snapshots tied to a specific commit. To regenerate them:

### Step 1: Checkout the Commit

```bash
git checkout c43903d28fce5b16f7a23db09108a3010d0c86d8
```

### Step 2: Generate Documentation

```bash
sdd doc generate src --output-dir docs --format both
```

### Step 3: Run scope Commands

**Plan examples:**
```bash
# Markdown (extract 'output' field from JSON)
sdd doc scope src/claude_skills/claude_skills/doc_query/codebase_query.py --plan | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(d['output'])" \
  > plan-markdown-example-output.txt

# JSON
sdd doc scope src/claude_skills/claude_skills/doc_query/codebase_query.py --plan \
  > plan-json-example-raw.json
```

**Implement examples:**
```bash
# Markdown (extract 'output' field from JSON)
sdd doc scope src/claude_skills/claude_skills/doc_query/cli.py --implement --function cmd_scope | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(d['output'])" \
  > implement-markdown-example-output.txt

# JSON
sdd doc scope src/claude_skills/claude_skills/doc_query/cli.py --implement --function cmd_scope \
  > implement-json-example-raw.json
```

### Step 4: Add Metadata

Manually add the metadata sections to the files:
- Command used
- Target module/function
- Commit hash
- Generation date
- Explanatory notes

## How Deterministic Inputs Are Enforced

The examples in this directory are deterministic because:

1. **Commit Hash**: All examples are tied to commit `c43903d28fce5b16f7a23db09108a3010d0c86d8`
2. **Fixed Target Modules**:
   - Plan examples use `src/claude_skills/claude_skills/doc_query/codebase_query.py`
   - Implement examples use `src/claude_skills/claude_skills/doc_query/cli.py` with function `cmd_scope`
3. **Fixed Analysis Parameters**:
   - Complexity threshold: 5
   - Top N functions: 10
   - Call graph depth: 2
4. **Documentation Regeneration**: Running `sdd doc generate` at the specified commit produces consistent `documentation.json`

To ensure deterministic output when regenerating:
- Always checkout the exact commit hash first
- Use the exact module paths and function names specified
- Regenerate documentation from the same source directory
- Use the same command flags and parameters

## Output Format

Both presets support two output formats:

1. **JSON** (default): Structured data with `preset`, `module`, `function`, and `output` fields
2. **Markdown** (in output field): Human-readable formatted text

The examples show both formats to demonstrate API usage patterns.
