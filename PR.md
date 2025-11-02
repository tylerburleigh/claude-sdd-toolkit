## Summary

This PR implements comprehensive AI-powered spec rendering capabilities for the SDD toolkit, transforming `sdd-render` from basic JSON-to-Markdown conversion into an intelligent documentation system with executive summaries, dependency visualization, and strategic insights. It also includes critical bug fixes, workflow improvements, and updated architecture documentation with version bump to v0.4.0.

## Key Features

### 🤖 AI-Enhanced Rendering (NEW)

**Three rendering modes:**
- **Basic mode**: Fast rendering without AI (< 2 seconds) - maintains backward compatibility
- **Enhanced mode** with 3 levels of AI analysis:
  - **Summary**: Executive summary only (~30 seconds)
  - **Standard**: Balanced AI features (~60 seconds) - **DEFAULT**
  - **Full**: Complete AI analysis (~90 seconds)

**AI enhancement capabilities:**
- Executive summaries with objectives, scope, critical path identification, and risk assessment
- Narrative enhancements for improved readability and flow
- Priority ranking based on dependencies, complexity, and impact
- Complexity scoring (1-10 scale) for accurate time estimates
- Actionable insights and recommendations
- Dependency graph visualization using Mermaid diagrams
- Intelligent task grouping and ordering by phase/priority
- Progressive disclosure with collapsible sections

### 📊 Architecture

**Orchestrator pattern** with 4-stage rendering pipeline:
1. **Base markdown generation** (structural)
2. **Spec analysis** (complexity, dependencies, bottlenecks)
3. **AI consultation** (parallel multi-agent for comprehensive insights)
4. **Markdown enhancement** (progressive disclosure, visualizations)

**Multi-agent AI consultation:**
- Configurable AI agents: gemini, codex, cursor-agent
- Priority-based agent selection
- Parallel consultation for speed
- Graceful fallback to structural-only output when AI tools unavailable

## Changes Overview

### 🆕 New Components (14 Python modules, ~7,612 lines)

**Core rendering pipeline:**
- `orchestrator.py`: Main AI enhancement pipeline coordinator
- `spec_analyzer.py`: Critical path detection and bottleneck identification
- `priority_ranker.py`: Multi-factor priority scoring system
- `complexity_scorer.py`: Task complexity assessment (1-10 scale)
- `insight_generator.py`: Actionable recommendation generation
- `dependency_graph.py`: Mermaid diagram generation for dependencies
- `task_grouper.py`: Intelligent task grouping by phase/complexity
- `executive_summary.py`: AI-powered high-level overview generation
- `narrative_enhancer.py`: Natural language flow improvements
- `markdown_parser.py`: Markdown parsing and manipulation utilities
- `visualization_builder.py`: Chart and diagram construction
- `ai_prompts.py`: Standardized prompts for AI agents

**Shared infrastructure:**
- `common/ai_config.py`: Unified AI tool configuration for all skills (reusable across toolkit)
- `skills/sdd-render/config.yaml`: Agent priority and timeout configuration

### ✅ Test Coverage (~2,035 lines)

**Unit tests (9 files):**
- Spec analyzer (critical path, bottleneck detection)
- Priority ranker (multi-factor scoring)
- Task grouper (intelligent grouping logic)
- Complexity scorer (1-10 scale assessment)
- Dependency graph (Mermaid generation)
- Progressive disclosure (detail level calculation)
- Markdown parser (parsing and manipulation)

**Integration tests (1 file):**
- End-to-end render pipeline validation

### 🔧 CLI Enhancements

**New flags:**
```bash
--mode {basic,enhanced}              # Choose rendering strategy
--enhancement-level {summary,standard,full}  # AI enhancement depth (default: standard)
-o, --output                         # Custom output path
```

**Example usage:**
```bash
# Fast rendering (no AI)
sdd render <spec-id> --mode basic

# AI-enhanced rendering (default)
sdd render <spec-id> --mode enhanced --enhancement-level standard

# Full AI analysis
sdd render <spec-id> --mode enhanced --enhancement-level full

# Custom output path
sdd render <spec-id> -o custom/path.md
```

### 📚 Documentation Updates

- **ARCHITECTURE.md**: Updated with v0.4.0 architecture (synthesized from gemini + codex AI analyses)
- **AI_CONTEXT.md**: Updated AI assistant quick reference (synthesized from gemini + codex AI analyses)
- **DOCUMENTATION.md**: Regenerated with latest codebase changes
- **documentation.json**: Regenerated machine-readable documentation
- **sdd-render/SKILL.md**: Updated with comprehensive usage examples and AI enhancement documentation

### 📦 Version Bump

- Version: **0.1.0 → 0.4.0** (in `pyproject.toml`)

### 📋 Spec Completion

- Moved `ai-enhanced-rendering-2025-10-28-001.json` from `specs/active/` to `specs/completed/`
- Spec completion: **48/49 tasks (97% complete)**

---

## All Commits in This PR

This PR includes **7 commits** on the `feat11` branch:

### 1. Add workflow instructions to prevent spec file bypasses (6331afe)

**Problem:** Agents were sometimes bypassing efficient `sdd` commands by directly reading spec files with `Read()` or `Bash(cat)`, wasting 50KB+ of context.

**Changes:**
- Added "Reading Specifications (CRITICAL)" section to sdd-next and sdd-update skills
- Documented that `Bash(sdd:*)` permission allows command chaining but this is an accepted trade-off
- Emphasized efficiency over security: guidance-based protection to prevent context waste

**Files:**
- `skills/sdd-next/SKILL.md`
- `skills/sdd-update/SKILL.md`
- `setup_permissions.py`

---

### 2. Fix sdd-update agent errors with entry-type completion (2b5a435)

**Problem:** Exit code 2 errors when sdd-update agent incorrectly used `--entry-type completion` (which doesn't exist).

**Root Cause:** Agent confused bulk-journal's `--template completion` with add-journal's `--entry-type`, where "completion" is NOT valid.

**Changes:**
- Added explicit warning in SKILL.md that "completion" is invalid for `--entry-type`
- Added "Common Mistakes" section explaining the confusion
- Added pre-parse detection in CLI to catch invalid attempts early
- Provided helpful error message suggesting correct `--entry-type status_change`

**Files:**
- `skills/sdd-update/SKILL.md`
- `src/claude_skills/claude_skills/cli/sdd/__init__.py`

---

### 3. Implement two-command session marker system for concurrent session support (512d975)

**Problem:** Fragile port/PID-based session detection caused incorrect transcript discovery when multiple Claude Code sessions ran concurrently.

**Solution:** Explicit marker approach with unique 8-char hex IDs passed between commands.

**New Commands:**
- `sdd session-marker` - generates unique marker
- `sdd context --session-marker <id>` - searches for specific marker in transcripts

**How It Works:**
- Generate marker → marker logged to transcript → search for marker = finds current session
- No coordination files, no race conditions, no port/PID fragility

**Code Cleanup:**
- Removed `process_utils.py` (obsolete PID/process detection)
- Removed `discover_transcript_from_filesystem()` fallback
- Removed `persist_session_env()` from session-start hook
- Simplified session-start to only output marker

**Files:**
- `src/claude_skills/claude_skills/context_tracker/` (multiple)
- `hooks/session-start`
- `skills/sdd-next/SKILL.md` (updated to two-command approach)

---

### 4. Fix sdd-update journaling bug and add list-specs command (eb587dd)

**Bug Fix:**
- **Problem:** `complete-task` with `--journal-content` but no `--journal-title` would overwrite user's content with generic default
- **Root Cause:** `workflow.py:304` used `or` logic that replaced BOTH fields if EITHER was missing
- **Fix:** Changed to independent field handling - each field checked separately

**New Feature: list-specs command**
```bash
sdd list-specs                    # List all specs
sdd list-specs --status active    # Filter by status
sdd list-specs --json             # JSON output
sdd list-specs --detailed         # Show extra metadata
```

**Features:**
- Filter by status (active/completed/archived/pending/all)
- Text and JSON output formats
- Detailed mode with version, description, author, timestamps, paths
- Progress calculation and phase tracking

**Agent/Skill Contract Updates:**
- `agents/sdd-update.md`: Added task_completion operation requiring journal content
- `skills/sdd-update/SKILL.md`: Updated Workflow 5 to recommend complete-task
- `skills/sdd-next/SKILL.md`: Updated completion examples to include journal

**Files:**
- `src/claude_skills/claude_skills/sdd_update/workflow.py`
- `src/claude_skills/claude_skills/sdd_update/list_specs.py` (new)
- `src/claude_skills/claude_skills/sdd_update/cli.py`
- Agent/skill documentation

---

### 5. Integrate Plan & Explore subagent guidance in sdd-next (9f39fc3)

**Purpose:** Clarify when/how to use Claude Code's built-in Plan and Explore subagents for codebase exploration and implementation planning.

**Changes:**
- Added "Codebase Exploration Subagents" section explaining behavioral differences:
  - **Plan subagent**: Research + recommendations requiring user approval (proactive assumption verification)
  - **Explore subagent**: Direct findings without approval gates (fast lookups)
- Integrated Plan subagent into Workflow 1 (Starting Fresh)
- Added Plan subagent to Workflow 3 (Handling Blockers) for alternative analysis
- Enhanced Workflow 4 (Plan Refinement) with proactive/reactive approaches
- Included decision guide, thoroughness levels, best practices

**Benefits:**
- Clear guidance on delegation to Plan vs Explore subagents
- Proactive assumption verification reduces implementation rework
- Expert recommendations for blocked tasks and architecture decisions
- Context efficiency by offloading exploration to dedicated subagents

**Documentation:**
- Condensed for readability (63% reduction from initial draft)
- Final: 1,657 lines (263 lines net reduction)

**Files:**
- `skills/sdd-next/SKILL.md`

---

### 6. Fix sdd-render bugs and improve documentation (652f434)

**Three Critical Bugs Fixed:**
1. **HTML tags removed**: Removed `<details>` tags for pure markdown compatibility
2. **Visualization API fixed**: Corrected method calls to use proper API
   - `build_progress_chart(format='mermaid')` → `build_progress_chart_mermaid()`
   - `build_dependency_graph(max_nodes=20)` → `build_dependency_graph_mermaid(show_completed=False)`
3. **Double-wrapping fixed**: Removed duplicate mermaid code block wrapping

**Documentation Improvements:**
- Updated SKILL.md with accurate timing estimates
- Added enhancement level details (summary/standard/full)
- Removed specific AI model names for flexibility
- Added example renders showing all three modes

**Impact:**
- Visualizations now work correctly with proper formatting
- Pure markdown output compatible with all processors
- Clear performance characteristics documented

**Files:**
- `src/claude_skills/claude_skills/sdd_render/markdown_enhancer.py`
- `src/claude_skills/claude_skills/sdd_render/visualization_builder.py`
- `skills/sdd-render/SKILL.md`

---

### 7. Add AI-enhanced spec rendering with multi-level enhancement modes (v0.4.0) - 841ec49

**This is the main commit** implementing the full AI-enhanced rendering feature described at the top of this PR.

**Major Components:**
- 14 new Python modules (~7,612 lines)
- 10 new test files (~2,035 lines)
- Unified AI configuration system (`common/ai_config.py`)
- CLI enhancements with new flags
- Comprehensive documentation updates
- Version bump to 0.4.0
- Spec moved to completed/

---

## Impact Summary

- **39 files changed**
- **60,276 insertions (+)**
- **76,289 deletions (-)**
- Net: Comprehensive architecture and documentation overhaul
- **14 new Python modules** (sdd_render package)
- **10 new test files** (unit + integration)
- **3 documentation files** updated with AI-synthesized content
- **1 new config file** for AI agent management
- **Multiple bug fixes** improving stability and usability
- **Workflow improvements** for concurrent sessions and spec management

## Backward Compatibility

✅ **Fully backward compatible**
- Basic mode maintains original fast rendering behavior
- Default enhanced mode provides sensible AI features without breaking existing workflows
- Graceful fallback when AI tools not available
- All bug fixes non-breaking

## Test Plan

- [x] Unit tests pass for all new components
- [x] Integration tests validate end-to-end pipeline
- [x] Manual testing of all three enhancement levels
- [x] Documentation regenerated successfully with multi-agent AI consultation
- [x] CLI flags work as expected
- [x] Graceful degradation when AI tools unavailable
- [x] Bug fixes verified with real-world usage
- [x] Concurrent session handling tested

## Migration Guide

No migration needed. To use new features:

```bash
# Use enhanced rendering (recommended)
sdd render <spec-id> --mode enhanced

# Customize enhancement level
sdd render <spec-id> --mode enhanced --enhancement-level full

# Stick with fast rendering
sdd render <spec-id> --mode basic

# List specs with new command
sdd list-specs --status active --detailed
```

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
