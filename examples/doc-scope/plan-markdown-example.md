# doc scope --plan Example Output

**Command:**
```bash
sdd doc scope src/claude_skills/claude_skills/doc_query/codebase_query.py --plan
```

**Target Module:** `src/claude_skills/claude_skills/doc_query/codebase_query.py`
**Commit Hash:** `c43903d28fce5b16f7a23db09108a3010d0c86d8`
**Generated:** 2025-11-21

---

## Output

**Module: codebase_query**

*CodebaseQuery: LLM-friendly interface for querying codebase analysis. This module extends DocumentationQuery to provide formatted responses specifically...*

**Statistics:**
- Classes: 1
- Functions: 1
- Avg Complexity: 1.0
- Max Complexity: 1
- High Complexity Functions: 0
- Dependencies: 7
- Reverse Dependencies: 0

**Top Complex Functions:**
- create_codebase_query (complexity: 1)
  Convenience function to create and load a CodebaseQuery instance. Args: docs_path: Path to documentation.json or its directory Returns: Loaded CodebaseQuery...


No complex functions found in src/claude_skills/claude_skills/doc_query/codebase_query.py (threshold: 5)

---

## What This Shows

The `--plan` preset provides:

1. **Module Summary**: Overview with docstring excerpt
2. **Statistics**: Class count, function count, complexity metrics, dependency counts
3. **Top Complex Functions**: Functions sorted by complexity (helps identify areas needing attention)
4. **Complex Function Details**: When functions exceed threshold (5), shows top 10 with locations

This information is useful when planning implementations or refactoring, as it helps you understand:
- Module architecture and scope
- Complexity hotspots
- Dependency relationships
- Key functions that may need special attention
