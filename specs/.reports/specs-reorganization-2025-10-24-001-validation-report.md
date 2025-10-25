# Validation Report

**Spec ID:** specs-reorganization-2025-10-24-001
**Status:** errors

## Summary
- Errors: 2
- Warnings: 2
- Auto-fixable: 2

## Issues
- ERROR: Task node 'task-1-1' missing metadata.file_path (task-1-1) [auto-fixable]
- ERROR: ❌ ERROR: Task node 'task-1-1' missing metadata.file_path
- WARNING: 'last_updated' should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) [auto-fixable]
- WARNING: ⚠️  WARNING: 'last_updated' should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

## Statistics Snapshot
- spec_id: specs-reorganization-2025-10-24-001
- title: Specs Directory Reorganization
- version: 
- status: in_progress
- totals: {'nodes': 41, 'tasks': 13, 'phases': 5, 'verifications': 12}
- status_counts: {'pending': 12, 'completed': 1, 'in_progress': 0, 'blocked': 0}
- max_depth: 4
- avg_tasks_per_phase: 2.6
- verification_coverage: 0.9230769230769231
- progress: 0.045454545454545456
- file_size_kb: 0.0

## Dependency Findings
- Potential deadlocks:
  - task-3-1 blocked by task-1-3
  - task-4-1 blocked by task-1-2
  - task-5-1 blocked by task-2-1
  - task-5-2 blocked by task-1-2, task-4-1
  - task-5-3 blocked by task-1-3, task-3-1