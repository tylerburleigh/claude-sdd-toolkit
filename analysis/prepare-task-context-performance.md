# `prepare-task` Context Performance Notes

Task `task-1-3-3` requires projecting the latency impact of the new `context` payload and outlining optimizations to keep overhead under **30 ms**. This memo documents baseline measurements, expected work per subcomponent, and mitigation tactics.

## Baseline Measurements (no context field)

Command executed from repo root with compact JSON enabled:

```bash
TIMEFORMAT='%3R'; for i in {1..5}; do time sdd prepare-task sdd-next-context-optimization-2025-11-15-001 >/dev/null; done
```

Observed wall-clock times (seconds): `0.891 / 0.852 / 0.887 / 0.854 / 0.867`

- **Median:** ~0.867 s
- **Std dev:** ~0.016 s (very low; CPU cache warm)
- Git + spec validation dominate runtime; the new context layer must add **<30 ms** on top of this baseline (<3.5 % relative increase).

## Operations Required for `context`

| Component | Workload | Complexity | Pitfalls |
| --- | --- | --- | --- |
| `previous_sibling` | Walk parent’s `children` list to find current index and the prior entry | O(*s*) where *s* = siblings count (typically <10) | None if parent already in memory; avoid resorting |
| `parent_task` | Copy parent metadata and child stubs | O(*s*) for child copy | Large parents could have dozens of children; copy titles only |
| `phase` | Traverse ancestors until `type == "phase"` and pull stats | O(depth) (phases generally shallow) | Avoid re-walking full hierarchy by caching node→phase mapping |
| `sibling_files` | Filter siblings with `metadata.file_path` | O(*s*) | Skip siblings lacking paths to reduce list building |
| `task_journal` | Load journal list and slice newest 3–5 entries | O(*j*) where *j* = entries for the task | Journal arrays can be large; need early exit after slice |

All operations use data already loaded during `prepare_task` (spec JSON + dependency map + journal). No filesystem scans or doc-query calls are required, so the target is achievable if we minimize unnecessary allocations.

## Optimization Strategies

1. **Single-pass parent lookup**
   - `prepare_task` already calls `get_task_info`, which includes the parent ID.
   - Cache `parent_node = hierarchy[parent_id]` once and reuse for `previous_sibling`, `parent_task`, and `sibling_files`.
   - Avoid repeated dictionary lookups across helper functions by passing the parent node dict downstream.

2. **Child slicing without deep copies**
   - When emitting `parent_task.children`, only copy `id`, `title`, and `status`.
   - Use list comprehension with literal dicts (no deepcopy) so cost remains proportional to child count.

3. **Phase memoization**
   - Build a lightweight `phase_lookup` map when loading the spec hierarchy: each node ID → nearest ancestor with `type == "phase"`.
   - Optional: compute lazily via `get_phase_for_task(node_id, cache)` to avoid up-front work.

4. **Journal summarization**
   - Use `get_task_journal(..., limit=5)` once (or slice after retrieval) and store truncated summaries (<160 chars).
   - Track `entry_count` separately (length of filtered list) so we can avoid iterating twice.

5. **String building**
   - Reuse helper functions to format timestamps (shared `format_timestamp` util) instead of new `datetime.fromisoformat` calls scattered across functions.
   - Keep summary strings raw; do not wrap text.

6. **Optional caching hooks**
   - Because `prepare_task` is often called multiple times in a session, keep the most recent `context` payload in an LRU keyed by `(spec_id, task_id, spec_hash)`. Skip this initially but document as stretch goal if profiling shows >30 ms spikes for heavily nested specs.

## Measurement Plan Post-Implementation

1. Add a temporary instrumentation flag to log stopwatch timings for:
   - Baseline `prepare_task` runtime
   - Time spent inside each context helper (using `time.perf_counter_ns()`)
2. Run benchmarks on:
   - Small spec (≤10 tasks)
   - Medium spec (~50 tasks)
   - Large spec (≥100 tasks, multiple journals)
3. Record 10 runs per spec, drop first result (warm-up), and capture median/95th percentile.
4. Verify total overhead stays <30 ms in 95th percentile. If not, profile the slowest helper and apply targeted optimizations above.

## Risk & Mitigation Summary

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Large parents (50+ children) | Copying child data dominates time | Emit first 20 children plus `"truncated": true` flag, or stream results |
| Massive journals | Slicing entire list costs O(*J*) | Introduce optional `limit` argument to `get_task_journal` so storage layer performs filtering |
| Orphaned nodes | Extra ancestor walks trying to find parents | Detect missing `parent` early and short-circuit to defaults |
| Nested phases | Repeated ancestor traversal per call | Cache node→phase mapping as described above |

These guardrails keep the enhancement aligned with the <30 ms requirement and give future tasks a concrete set of constraints to code against.
