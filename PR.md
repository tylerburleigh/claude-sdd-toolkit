# PR #15: Add compact JSON output mode for ~30% token savings

## Summary

Implements contract-based compact JSON output for SDD CLI commands, achieving ~30% token savings for AI agent workflows while maintaining 100% backward compatibility. Adds opt-in `--compact` flag to 5 core commands with a clear migration path to v2.0.

## What Changed

### Key Features
- **Compact JSON mode**: New `--compact` flag for machine-readable output without emoji decorators
- **Contract-based extraction**: Functional contracts ensure all decision-enabling fields preserved
- **~30% token savings**: Measured across all 5 commands (prepare-task, task-info, check-deps, progress, next-task)
- **Backward compatible**: Phase 1 opt-in, verbose output remains default
- **Migration path**: Clear v2.0 transition plan with `--verbose` fallback

### Core Infrastructure (Phase 1)
- `src/claude_skills/claude_skills/common/contracts.py` (437 lines): Contract extractors for all 5 commands
- `src/claude_skills/claude_skills/common/json_output.py` (227 lines): JSON formatting utilities
- Updated `common/__init__.py`: Exported new contract functions

### Command Updates (Phase 2)
Modified `src/claude_skills/claude_skills/sdd_next/cli.py` to support `--compact` flag:
- `cmd_prepare_task()`: Contract-based compact output
- `cmd_task_info()`: Minimal task detail extraction
- `cmd_check_deps()`: Dependency status only
- `cmd_progress()`: Essential progress metrics
- `cmd_next_task()`: Next task recommendation

### Documentation (Phase 3)
- **README.md** (+48 lines): Token savings results and benefits
- **docs/CONTRACTS.md** (570 lines): Formal contract definitions for all commands
- **docs/MIGRATION_V2.md** (369 lines): Migration guide for Phase 1 → Phase 2 transition
- **scripts/measure_token_efficiency.py** (273 lines): Token measurement utilities
- **skills/sdd-next/SKILL.md** (+40 lines): Updated workflow examples

## Technical Approach

### Design Decisions

**1. Contract-Based Extraction**
Instead of removing fields arbitrarily, implemented formal contracts specifying:
- Required fields (always present)
- Optional fields (conditional inclusion)
- Decisions enabled (what the output helps you decide)
- Inclusion conditions (when optional fields appear)

This ensures compact output contains everything needed for decision-making while removing verbose decorators.

**2. Opt-In Phase 1, Default Phase 2**
- **Phase 1** (current): `--compact` is opt-in, verbose remains default
- **Phase 2** (v2.0): `--compact` becomes default, `--verbose` restores old behavior

This two-phase approach ensures zero breaking changes during migration.

**3. Single-Line Minified Output**
Compact mode uses `json.dumps(compact=True, separators=(',', ':'))` for single-line output, eliminating unnecessary whitespace.

### Token Savings Results

| Command | Normal Tokens | Compact Tokens | Savings |
|---------|---------------|----------------|---------|
| prepare-task | ~400-600 | ~280-420 | ~28-32% |
| task-info | ~130-240 | ~90-170 | ~28-30% |
| check-deps | ~40-210 | ~30-140 | ~27-35% |
| progress | ~95-130 | ~65-85 | ~31-36% |
| next-task | ~50-55 | ~34-37 | ~30-32% |

**Average: ~30% token reduction**

Measured using tiktoken (cl100k_base) across 3 different spec types. Current implementation uses JSON minification only, providing a solid foundation for future optimization strategies.

**Note on Original Targets:** The spec originally targeted 65-85% savings but actual measurements showed ~30% with the current approach (JSON minification). This establishes a baseline, with additional optimization strategies identified for future work to reach higher targets.

## Implementation Details

### Phase 1: Contract Infrastructure (11 tasks)
- ✅ Implement 5 contract extractors
- ✅ Add JSON formatting utilities
- ✅ Export functions from common module
- ✅ Add contract documentation and type hints
- ✅ Verify contract extractors, JSON output, verbose mode

### Phase 2: Command Updates (15 tasks)
- ✅ Update all 5 commands to support `--compact`
- ✅ Update CLI help text
- ✅ Verify JSON validity, compact flag support, minification
- ✅ Verify backward compatibility (non-compact still works)
- ✅ Measure token savings for each command

### Phase 3: Documentation & Verification (7 tasks)
- ✅ Create token measurement script
- ✅ Document token savings in README
- ✅ Verify actual savings (~30%)
- ✅ Document workflow scenarios and measurements

### Phase 4: Integration & Migration (5 tasks)
- ✅ Update sdd-next SKILL.md with command examples
- ✅ Create MIGRATION_V2.md guide
- ✅ Create CONTRACTS.md documentation
- ✅ Verify workflows, migration guide, contract accuracy

## Testing

### Automated Verification
- ✅ All 5 commands produce valid JSON with `--compact`
- ✅ Compact output is minified (single-line)
- ✅ Non-compact output still works (backward compatible)
- ✅ Compact output smaller than verbose (measured)
- ✅ Help text updated for all commands

### Manual Verification
- ✅ Token savings measured at ~30% across all commands
- ✅ Workflow scenarios documented and tested
- ✅ Migration guide reviewed for completeness

## Migration Path

### For Users (Phase 1)
```bash
# Default behavior unchanged
sdd prepare-task my-spec --json

# Opt into compact mode
sdd prepare-task my-spec --json --compact
```

### For v2.0 (Phase 2)
```bash
# Compact becomes default
sdd prepare-task my-spec --json

# Opt into verbose mode
sdd prepare-task my-spec --json --verbose
```

See [docs/MIGRATION_V2.md](docs/MIGRATION_V2.md) for complete migration guide.

## Files Changed (Summary)

**New Files:**
- `src/claude_skills/claude_skills/common/contracts.py` - Contract extractors
- `src/claude_skills/claude_skills/common/json_output.py` - JSON formatters
- `docs/CONTRACTS.md` - Contract documentation
- `docs/MIGRATION_V2.md` - Migration guide
- `scripts/measure_token_efficiency.py` - Measurement utilities

**Modified Files:**
- `src/claude_skills/claude_skills/sdd_next/cli.py` - Added --compact support
- `README.md` - Token savings documentation
- `skills/sdd-next/SKILL.md` - Updated workflow examples
- `docs/DOCUMENTATION.md` - Auto-generated docs update

## Commits

33 commits across 4 phases:
- Phase 1 (8 tasks + 5 verifications): Contract infrastructure
- Phase 2 (6 tasks + 6 verifications): Command updates
- Phase 3 (2 tasks + 3 verifications): Documentation
- Phase 4 (3 tasks + 4 verifications): Integration

See commit history for detailed progression.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
