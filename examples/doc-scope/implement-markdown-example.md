# doc scope --implement Example Output

**Command:**
```bash
sdd doc scope src/claude_skills/claude_skills/doc_query/cli.py --implement --function cmd_scope
```

**Target Module:** `src/claude_skills/claude_skills/doc_query/cli.py`
**Target Function:** `cmd_scope`
**Commit Hash:** `c43903d28fce5b16f7a23db09108a3010d0c86d8`
**Generated:** 2025-11-21

---

## Output

No callers found for function: cmd_scope

**Call Graph for cmd_scope:**

Direction: both
Max Depth: 2
Total Nodes: 92
Total Edges: 114
*Note: Graph truncated at max depth*

**Callees (what this calls):**
- cmd_scope → getattr
- cmd_scope → _maybe_json
- cmd_scope → error
- cmd_scope → load
- cmd_scope → get_module_summary
- cmd_scope → append
- cmd_scope → get_complex_functions_in_module
- cmd_scope → get_function_callers
- cmd_scope → get_call_graph_summary
- cmd_scope → get_instantiated_classes_in_file
- cmd_scope → str
- cmd_scope → join
- cmd_scope → prepare_output
- cmd_scope → print


**Classes instantiated in src/claude_skills/claude_skills/doc_query/cli.py:**

1. PrettyPrinter (98 instantiations)
   Location: src/claude_skills/claude_skills/common/printer.py:30
   Purpose: Utility for consistent, pretty console output optimized for Claude Code.

2. PrettyPrinter (98 instantiations)
   Location: src/claude_skills/claude_skills/sdd_fidelity_review/report.py:18
   Purpose: Pretty printer for console output with optional color support.

3. ToolResponse (72 instantiations)
   Location: src/claude_skills/claude_skills/common/ai_tools.py:48
   Purpose: Standardized response from AI tool consultation.

4. ProviderHooks (62 instantiations)
   Location: src/claude_skills/claude_skills/common/providers/base.py:194
   Purpose: Optional lifecycle hooks wired by the registry.

5. FakeProcess (62 instantiations)
   Location: src/claude_skills/claude_skills/tests/unit/test_providers/test_claude_provider.py:27

6. FakeProcess (62 instantiations)
   Location: src/claude_skills/claude_skills/tests/unit/test_providers/test_codex_provider.py:25

7. FakeProcess (62 instantiations)
   Location: src/claude_skills/claude_skills/tests/unit/test_providers/test_cursor_agent_provider.py:25

8. FakeProcess (62 instantiations)
   Location: src/claude_skills/claude_skills/tests/unit/test_providers/test_gemini_provider.py:25

9. FakeProcess (62 instantiations)
   Location: src/claude_skills/claude_skills/tests/unit/test_providers/test_opencode_provider.py:31

10. GenerationRequest (49 instantiations)
   Location: src/claude_skills/claude_skills/common/providers/base.py:138
   Purpose: Normalized request payload for provider execution.

---

## What This Shows

The `--implement` preset with `--function` flag provides:

1. **Function Callers**: Shows which functions call the target function (helps understand dependencies and usage)
2. **Call Graph**: Bidirectional graph showing what the function calls (callees) and what calls it (callers)
3. **Instantiated Classes**: Classes frequently instantiated in the module (reveals runtime dependencies)

This information is useful when implementing changes, as it helps you understand:
- How the function is used throughout the codebase
- What dependencies the function relies on
- Runtime class instantiation patterns
- Potential impact areas when modifying the function
