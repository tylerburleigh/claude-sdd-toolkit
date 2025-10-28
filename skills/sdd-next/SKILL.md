---
name: sdd-next
description: Task preparation skill for spec-driven workflows. Reads specifications, identifies next actionable tasks, gathers context, and creates detailed execution plans. Use when ready to implement a task from an existing spec - bridges the gap between planning and coding.
---

# Spec-Driven Development: Next Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-toolkit:sdd-plan)** - Creates specifications and task hierarchies
- **Skill(sdd-toolkit:sdd-next)** (this skill) - Identifies next tasks and creates execution plans
- **Skill(sdd-toolkit:sdd-update)** - Tracks progress and maintains documentation

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│            Spec-Driven Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌─────────┐│
│  │   PLAN   │───>│   NEXT   │───>│IMPLEMENTATION│───>│ UPDATE  ││
│  └──────────┘    └──────────┘    └─────────────┘    └─────────┘│
│       │               │                  │                │      │
│   Creates JSON    Finds next        Writes actual    Updates     │
│   spec file       actionable        code based on    status &    │
│                   task, creates     execution plan   journals    │
│                   execution plan                                  │
│       │               │                  │                │      │
│       └───────────────┴──────────────────┴────────────────┘      │
│                              │                                    │
│                         [Cycle repeats]                          │
│                                                                   │
│  Note: Implementation can be done by human developers,           │
│        Claude with coding tools, or other AI assistants          │
└─────────────────────────────────────────────────────────────────┘
```

**Your Role (NEXT)**: Identify the next actionable task from an existing spec and create a detailed execution plan for implementation.

## Core Philosophy

**Context-Driven Execution**: Every task implementation should begin with full understanding of the spec's intent, the task's role in the larger plan, and all relevant codebase context. This prevents scope creep, ensures alignment with the specification, and produces implementation that integrates cleanly.

**Key Benefits:**
- Identifies the next actionable task automatically
- Gathers all relevant context before implementation
- Creates focused execution plans for specific tasks
- Maintains alignment with overall specification
- Prevents working on wrong tasks or blocked tasks
- Provides clear handoff between spec and code

## Important Notes

**Always Use Absolute Paths:**
- After Phase 1.1/1.2, all paths (`$SPEC_FILE`, `$SPECS_DIR`) should be absolute
- Never use relative paths like `specs/active/file.json` - they fail when run from different directories
- Enhanced discovery (Phase 1.1) checks multiple common locations automatically

**JSON Is Source of Truth:**
- Specs live in `specs/<status>/<spec-id>.json`
- All task metadata, dependencies, verification steps, and risk notes are stored in the JSON hierarchy
- Query specs via `sdd` commands; avoid ad-hoc parsing

**Fast Context Checklist (daily driver):**
1. `sdd prepare-task SPEC_ID --json` (auto-discovers specs, selects the next task, and includes dependency status)
2. If you need more detail, run `sdd task-info SPEC_ID TASK_ID --json` and `sdd check-deps SPEC_ID TASK_ID --json`
3. Review task metadata, then open the mentioned source/test files; helpers like `sdd find-related-files <path>` and `sdd find-tests --source-file <path>` keep this fast
4. If `prepare-task` or `check-deps` warns about blockers, run `sdd list-blockers SPEC_ID`
5. Capture verification steps or linked docs noted in the spec before planning changes

**Command Formatting:**
- **Always use the wrapper script `sdd [command]`**
- **Always use single-line bash commands** (no backslash continuations)
- This ensures compatibility with permission rules and automation
- Long commands are acceptable - parseability matters more than formatting
- **Avoid compound commands with &&** when possible - use separate command invocations instead
- **Never use inline environment variable assignment with &&** - this adds unnecessary complexity

**Context Usage Management:**
- Monitor Claude's context window usage throughout task execution
- Use `/context` command to check current usage percentage
- **50% threshold**: At 50% or higher context usage, recommend pausing to preserve context for complex tasks
- **Recovery workflow**: `Skill(sdd-toolkit:sdd-update)` → `/clear` → `/sdd-start`
  - Always save progress with sdd-update BEFORE clearing context
  - Use /sdd-start to resume from the saved state
- **Why 50%?**: Complex tasks can consume 30-50% of context during preparation and implementation. Starting fresh ensures you won't hit limits mid-task
- **Context preservation**: The /clear command wipes conversation history, so ensure all progress is saved to the spec file first

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (prepare-task, verify-tools, task-info, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd` CLI wrapper commands (e.g., `sdd prepare-task`, `sdd verify-tools`, `sdd task-info`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python sdd_next.py`, `bash python3 scripts/next_task.py`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## Automated Workflow (Skill Invocation)

When this skill is invoked automatically (via `Skill(sdd-toolkit:sdd-next)`), use these simplified commands:

**Step 1: Verify tools**
```bash
sdd verify-tools
```

**Step 2: Prepare task (discovers specs automatically)**
```bash
sdd prepare-task SPEC_ID
```

**If prepare-task fails:**
- **Specs directory not found**: Specify path explicitly with `--path /absolute/path/to/specs`
- **Spec file not found**: Verify SPEC_ID is correct, check `specs/active/` directory
- **No actionable tasks**: All tasks may be completed or blocked (use `list-blockers` to diagnose)
- **Multiple specs found**: If you don't know the SPEC_ID, use manual workflow (Phase 1.1)
- **Circular dependencies detected**: Use `find-circular-deps SPEC_ID` to diagnose, may need spec revision

The `prepare-task` command handles spec discovery, finds the next actionable task, gathers dependencies, and extracts task details - all in one command. This is the recommended approach for automated workflows.

**Automatic Enhancements:**

The `prepare-task` command includes two automatic enhancements:

1. **Spec Validation**: Validates the JSON spec file before proceeding. If critical errors are found, shows clear error messages with suggested fixes (e.g., `sdd fix spec-id.json`). Non-critical warnings are displayed but don't block task preparation.

2. **Codebase Context Gathering**: If codebase documentation has been generated, automatically gathers task-relevant context (via `Skill(sdd-toolkit:doc-query)`) including:
   - Relevant files from the codebase
   - Similar implementations to reference
   - Dependency information

   This context appears in the execution plan output as a "Codebase Context" section.

**If you need to specify a custom specs path:**
```bash
sdd prepare-task SPEC_ID --path /absolute/path/to/specs
```

## Quick Start: Automated vs Manual Workflow

**Choose your workflow based on your needs:**

### ✅ Use Automated Workflow (Recommended for Most Cases)

**When to use:**
- Standard task preparation and execution planning
- You know the spec ID you want to work on
- You want the fastest path to creating an execution plan
- Typical development workflow

**How to use:**
```bash
# 1. Verify tools available
sdd verify-tools

# 2. Prepare task automatically (handles everything)
sdd prepare-task SPEC_ID

# This single command:
# - Discovers specs directory
# - Finds next actionable task
# - Gathers dependencies
# - Extracts task details
# - Returns everything needed for execution plan
# Tip: add --json to capture structured output you can reuse for planning
```

**Skip to:** Phase 4 (Execution Plan Creation) after `prepare-task` succeeds

**Note:** When `prepare-task` returns successfully, you do **not** need to call `next-task`, `task-info`, or `check-deps` separately unless you are troubleshooting or drilling into a different task. The JSON payload already includes the recommended task, its metadata, and dependency status.

**If prepare-task fails:**
- Check the error message for specific guidance
- Verify spec file exists and is valid
- Fall back to manual workflow if needed (see below)

---

### Decision Flow Chart

```
┌─────────────────────────────────────────┐
│ Do you know the SPEC_ID to work on?    │
└────────────┬────────────────────────────┘
             │
        ┌────▼────┐
        │   YES   │──────────> Use Automated: sdd prepare-task SPEC_ID
        └─────────┘            If succeeds: Skip to Phase 4
                               If fails: See troubleshooting or use manual

        ┌────▼────┐
        │   NO    │──────────> Use Manual: Start at Phase 1
        └─────────┘            Discover specs, review options, select spec
```

**Most users should start with automated workflow** and only use manual workflow when needed.

## Required Tools

This skill uses the `sdd` command that handles:
- JSON spec file parsing and queries
- Task metadata extraction from JSON
- Task discovery and dependency analysis
- Progress tracking and phase management

### The `sdd-next` tool

You have access to the `sdd` command.

**Available Commands:**

**Spec Operations:**
- `verify-tools` - Check system requirements
- `find-specs` - Discover specs directory (supports `-v, --verbose` to show spec files)
- `next-task <spec-id>` - Find next actionable task
- `task-info <spec-id> <task-id>` - Get task details from state
- `check-deps <spec-id> <task-id>` - Check task dependencies
- `progress <spec-id>` - Show overall progress
- `list-phases <spec-id>` - List all phases with status
- `list-blockers <spec-id>` - List all currently blocked tasks
- `query-tasks <spec-id>` - Query tasks by status, type, or parent (supports `--status`, `--type`, `--parent`)
- `check-complete <spec-id>` - Check if spec or phase is ready to be marked complete (supports `--phase <phase-id>`)
**Workflow Commands:**
- `prepare-task <spec-id> [task-id]` - Prepare task for implementation (finds next task if task-id not provided)
- `validate-spec <spec-file>` - Validate spec file structure
- `find-pattern <pattern>` - Find files matching glob pattern
- `format-plan <spec-id> <task-id>` - Format execution plan for display

**Project Analysis Commands:**
- `detect-project` - Detect project type and dependencies
- `find-tests` - Discover test files and testing framework (supports `--source-file <file>`)
- `check-environment` - Verify environmental requirements (supports `--required <deps>`)
- `find-circular-deps <spec-id>` - Detect circular dependencies
- `find-related-files <file>` - Find files related to a source file
- `validate-paths <paths...>` - Validate and normalize file paths (supports `--base-directory <dir>`)
- `spec-stats <spec-file>` - Get comprehensive spec statistics (supports `--spec-file <file>`)

**Optional Commands (Advanced/Specialized Use):**
- `init-env` - Initialize development environment (one-time setup, supports `--spec-path <path>`, `--export`)
- `--no-color` - Disable colored output
- `--verbose, -v` - Show detailed output (info messages)
- `--quiet, -q` - Minimal output (errors only)

**Command-Specific Common Options:**
- `--json` - Output as JSON (available on most commands)
- `--path <dir>` - Specify specs directory path (spec operations only)
- `--directory <dir>` - Specify project directory (project analysis commands only)
- `--status <status>` - Filter by status: pending, in_progress, completed, blocked (query-tasks only)
- `--type <type>` - Filter by type: task, verify, group, phase (query-tasks only)
- `--parent <id>` - Filter by parent node ID (query-tasks only)
- `--phase <phase-id>` - Check specific phase completion (check-complete only)

## Optional Context Enhancement Tools

The following tools are **optional** but can significantly enhance context gathering during task preparation. These tools are not required for core sdd-next functionality, but provide automated code analysis and documentation lookup when available.

### Codebase Documentation Query

**Availability**: Requires codebase documentation generated by the `Skill(sdd-toolkit:code-doc)` skill. Invoke `Skill(sdd-toolkit:doc-query)` to access these capabilities.

**Purpose**: Provides rapid structural understanding of the codebase without manual exploration

**When it's mentioned in this guide**:
- Phase 1.4 (Understand Project Context) - Optional alternative to manual exploration
- Phase 3.1 (Extract Task-Specific Details) - Smart context gathering using SDD integration
- Phase 3.3 (Examine Related Files) - Finding similar implementations and impact analysis
- Phase 3.4 (Identify Testing Requirements) - Test context discovery

**Usage**:
First check if documentation exists:
```bash
sdd doc stats
```

If available, invoke `Skill(sdd-toolkit:doc-query)` which provides commands like:
- `sdd doc list-modules` - List all modules
- `sdd doc search "keyword"` - Search for functionality
- And many more targeted queries

**If codebase documentation has not been generated**: Fall back to manual file exploration using the `Explore` tool.

### Skill(sdd-toolkit:doc-query) - Smart Context for SDD Workflows

**Availability**: Invoke `Skill(sdd-toolkit:doc-query)` to access codebase documentation query capabilities (which use `sdd doc` commands under the hood).

**Purpose**: Bridges codebase documentation with SDD workflows to provide task-specific file suggestions and impact analysis

**When it's mentioned in this guide**:
- Phase 3.1 (Extract Task-Specific Details) - Get suggested files for specific tasks
- Phase 3.3 (Examine Related Files) - Find similar implementations and dependencies
- Phase 3.4 (Identify Testing Requirements) - Test file discovery and coverage estimation

**Alternative approaches if codebase documentation has not been generated:**
- For task context: Review spec file for mentioned files, use `Explore` to search for related code
- For similar implementations: Use `Glob` to find files with similar names/patterns
- For impact analysis: Use `Grep` to find imports and references manually
- For test context: Use `sdd-next` with the `find-tests` command or `Glob` for test file patterns

**Important**: All workflows in this guide that reference `Skill(sdd-toolkit:doc-query)` are **recommendations for enhanced context**, not requirements. The core sdd-next workflow functions without them.

## When to Use This Skill

Use `Skill(sdd-toolkit:sdd-next)` when:
- Ready to start implementing from an existing spec
- Need to find the next task to work on
- Want to understand a specific task's context
- Creating execution plan for a task
- Resuming work on a partially-completed spec
- Coordinating work across multiple developers/tools
- Need to understand how a task fits in the bigger picture

**Do NOT use for:**
- Creating new specifications (use `Skill(sdd-toolkit:sdd-plan)`)
- Updating task status or progress (use `Skill(sdd-toolkit:sdd-update)`)
- Actual code implementation (use appropriate coding tools)
- Quick bug fixes or one-off changes
- Work outside of a spec-driven workflow

## Skill Handoff Points

**When to transition to other skills:**

← **From Skill(sdd-toolkit:sdd-plan)**:
  - JSON spec file has been created
  - Ready to begin implementation work
  - Need to identify first actionable task

→ **To Implementation Tools**:
  - After execution plan is created and approved
  - Hand off to coding tools (Claude, Cursor, human developers)
  - Execution plan guides the actual code writing

→ **To Skill(sdd-toolkit:sdd-update)**:
  - Before starting implementation (mark task in_progress)
  - After completing implementation (mark task completed)
  - When encountering blockers (document issue)
  - When making deviations from plan (journal decision)
  - After task completion, to unlock dependent tasks

← **From Skill(sdd-toolkit:sdd-update)**:
  - After a task is completed, find the next task
  - After resolving a blocker, resume work
  - After updating progress, continue to next work item

## Decision Tree: Which Skill to Use?

```
Have a spec already?
├─ No → Use `Skill(sdd-toolkit:sdd-plan)` first to create one
└─ Yes → Continue below

What do you need to do?
├─ Find next task to work on → Use `Skill(sdd-toolkit:sdd-next)` (this skill)
├─ Create execution plan → Use `Skill(sdd-toolkit:sdd-next)` (this skill)
├─ Update task status → Use `Skill(sdd-toolkit:sdd-update)`
├─ Journal a decision → Use `Skill(sdd-toolkit:sdd-update)`
├─ Actually write code → Use implementation tools (after Developer creates plan)
└─ Create new spec → Use `Skill(sdd-toolkit:sdd-plan)`

Ready to implement?
├─ Don't know which task → Use this skill to identify next task
├─ Know the task, need plan → Use this skill to create execution plan
├─ Have plan, ready to code → Hand off to implementation tools
└─ Task complete → Use `Skill(sdd-toolkit:sdd-update)` to update status
```

## The Developer Workflow

### Phase 1: Spec Discovery and Context Gathering

Understand the overall specification before diving into specific tasks.

**Data Source:**
- **JSON spec files** = Single source of truth for all spec data
- Contains: task details, metadata, dependencies, status, and implementation details
- Located in `specs/active/{spec-id}.json`
- All task information is queried from JSON using the `sdd` command

#### 1.0 Locate Active Specifications

Find specifications that need implementation work.

**Steps:**
1. Search multiple common locations for specs directories
2. Convert found paths to absolute paths immediately
3. List all specification files
4. Identify specs with tasks remaining

```bash
# Discover and display specs directory
sdd find-specs

# List active specs with verbose output
sdd find-specs --verbose
```

**Note:** Most commands auto-discover the specs directory, so you typically don't need to run `find-specs` separately. Use the `--path` parameter if you need to specify a custom location.

**If find-specs fails:**
- **No specs directory found**:
  - Check current directory for `specs/active/` folder
  - Check parent directory for `specs/active/` folder
  - Specify path explicitly: `--path /absolute/path/to/specs`
  - Verify spec files exist and are `.json` format
- **Permission denied**: Check read permissions on specs directory
- **Empty directory**: No active specs found - use `sdd-plan` to create one

**Multiple Specs Handling:**
`prepare-task` and other commands accept a single `SPEC_ID`. When several specs are active:
- Run `sdd find-specs --verbose` to list the available IDs with progress summaries
- Pick the target `SPEC_ID` manually (or confirm with your user) before continuing
- If the chosen spec is blocked, use `sdd list-blockers SPEC_ID` to show why before proceeding

Most spec operations auto-discover the `specs/active` directory. Only use `--path` when the specs live in a custom location.


#### 1.1 Load Spec File

Load the JSON spec file to access all specification data.

**Data Source:**
All spec information is in the JSON file at `specs/active/{spec-id}.json`:
- Metadata (spec_id, title, overview, objectives, risk level)
- Complete task hierarchy (phases, tasks, subtasks)
- Task details (changes, reasoning, integration points)
- Dependencies and verification steps
- Current status and progress

**Steps:**
1. Confirm the `SPEC_ID` you selected (see 1.1) – no manual path lookup is required unless you are using a custom specs directory
2. Use CLI commands to read structured data from the JSON JSON spec file (skip manual parsing)
3. Rely on the outputs of `sdd progress SPEC_ID --json`, `sdd list-phases SPEC_ID --json`, or `sdd prepare-task SPEC_ID --json` to obtain titles, hierarchy, and metadata

**Key Metadata Available:**
- **Spec ID**: Unique identifier (from JSON root)
- **Title**: What this spec accomplishes
- **Hierarchy**: Complete task breakdown with status
- **Metadata**: Risk level, dependencies, timestamps

**Recommended Queries:**
```bash
# Quick spec overview (auto-discovers specs directory)
sdd progress SPEC_ID --json

# Inspect phase breakdown
sdd list-phases SPEC_ID --json

# Full task + dependency bundle
sdd prepare-task SPEC_ID --json
```

#### 1.2 Discover Next Task

Retrieve current progress and task status.

**Steps:**
1. Use spec_id to locate JSON file: `specs/active/{spec-id}.json`
2. Query hierarchy structure using `sdd-next`
3. Identify task statuses
4. Find next actionable task
5. Calculate current progress

**JSON Spec File Structure:**

Use `sdd-next` for all JSON spec file queries.

```json
{
  "spec_id": "user-auth-2025-10-18-001",
  "generated": "2025-10-18T10:00:00Z",
  "last_updated": "2025-10-18T14:30:00Z",

  "hierarchy": {
    "spec-root": {
      "type": "spec",
      "title": "User Authentication",
      "status": "in_progress",
      "parent": null,
      "children": ["phase-1", "phase-2", "phase-3"],
      "total_tasks": 23,
      "completed_tasks": 7,
      "metadata": {}
    },
    
    "phase-1": {
      "type": "phase",
      "title": "Database Schema",
      "status": "completed",
      "parent": "spec-root",
      "children": ["phase-1-files", "phase-1-verify"],
      "total_tasks": 7,
      "completed_tasks": 7,
      "metadata": {}
    },
    
    "task-2-1": {
      "type": "task",
      "title": "src/services/authService.ts",
      "status": "pending",
      "parent": "phase-2-files",
      "children": ["task-2-1-1", "task-2-1-2"],
      "dependencies": {
        "blocks": [],
        "blocked_by": [],
        "depends": ["task-1-2"]
      },
      "total_tasks": 1,
      "completed_tasks": 0,
      "metadata": {
        "file_path": "src/services/authService.ts",
        "estimated_hours": 3
      }
    }
  }
}
```

**Example Queries:**
```bash
# Get overall progress
sdd progress SPEC_ID

# List all phases
sdd list-phases SPEC_ID
```

#### 1.3 Understand Project Context

Gather information about the codebase and project structure.

**Steps:**
1. Identify project type (from spec frontmatter or file structure)
2. Locate key directories (src, tests, config, etc.)
3. Identify existing patterns and conventions
4. Note related files mentioned in spec
5. Understand tech stack and dependencies

**Project Type Detection:**

Use the Python tool for automatic project detection:

```bash
sdd detect-project  # Add --json for JSON output
```

Automatically detects Node.js, Python, Rust, Go, Java projects and their dependency managers.

**Codebase Documentation Query (Optional - Recommended if available):**

If codebase documentation has been generated, use `Skill(sdd-toolkit:doc-query)` for rapid context gathering:

```bash
# First check if documentation exists (auto-detects location)
sdd doc stats
```

If documentation is available, invoke `Skill(sdd-toolkit:doc-query)` to:
- Get quick project overview (module count, class count, complexity metrics)
- List all modules
- Search for relevant entities

**If codebase documentation has not been generated:**
- Use `sdd detect-project --json` for a quick inventory of project type, dependency managers, and key config files
- Use `sdd find-related-files <path>` to surface neighbouring, similar, and test files for the task at hand
- Use `sdd find-tests --source-file <path>` (or without the flag) to map the existing test layout
- Fall back to `Explore`, `Glob`, `Read`, or manual exploration only when the CLI helpers do not provide enough detail

**Benefits when available:** Instant structural understanding without manual exploration.

#### 1.4 Understanding JSON Spec Files

**Data Source:** JSON spec files (`specs/active/*.json`) are the single source of truth for all specification data.

**What's in the JSON:**
- Complete task hierarchy (phases, tasks, subtasks)
- Current task statuses (`pending`, `in_progress`, `completed`)
- Task details (changes, reasoning, integration points)
- Dependencies (`blocks`, `blocked_by`, `depends`)
- Progress metrics (`completed_tasks`, `total_tasks`)
- File paths and metadata
- Verification procedures
- Architecture decisions

**Use JSON for:**
- Finding next available task
- Getting task implementation details
- Checking task dependencies
- Calculating progress percentages
- Verifying task completion status
- Identifying blockers
- Creating execution plans

**Query with:** `sdd-next` commands (see `next-task`, `task-info`, `check-deps`, `progress`)

**Efficient pattern:**
```bash
# Use prepare-task to get everything in one command
sdd prepare-task "$SPEC_ID"
# Returns: next task + details + dependencies from JSON
```

### Phase 2: Task Identification and Selection

Find the next actionable task that should be implemented.

#### 2.1 Query Available Tasks

Identify tasks that can be started now.

```bash
# Find the next actionable task
sdd next-task "$SPEC_ID" --path "$SPECS_DIR"

# Get detailed info about a specific task
sdd task-info "$SPEC_ID" "$TASK_ID" --path "$SPECS_DIR"

# Check if a task is ready to start
sdd check-deps "$SPEC_ID" "$TASK_ID" --path "$SPECS_DIR"
```

**Advanced Task Querying:**

For more complex filtering beyond the next single task:

```bash
# Find all pending tasks in a specific phase
sdd query-tasks "$SPEC_ID" --status pending --parent phase-2

# Find all blocked tasks to understand what's holding up progress
sdd list-blockers "$SPEC_ID"

# Find all verification tasks
sdd query-tasks "$SPEC_ID" --type verify

# Combine filters: pending tasks in phase-2
sdd query-tasks "$SPEC_ID" --status pending --parent phase-2 --json
```

**When to use each:**
- `next-task` - Simple: "What should I work on next?" (returns single task)
- `query-tasks` - Complex: "Show me all pending tasks in phase-2" (returns filtered list)
- `list-blockers` - Analysis: "What tasks are currently blocked and why?" (diagnostic)

**If next-task fails or returns no results:**
- **No actionable tasks found**:
  - All tasks may be completed - check progress: `sdd progress SPEC_ID`
  - All tasks may be blocked - check blockers: `sdd list-blockers SPEC_ID`
  - Spec may be finished - verify with `check-complete SPEC_ID`
- **All tasks blocked**:
  - Review blockers to identify what needs resolution
  - Look for external dependencies that need attention
  - Consider if circular dependencies exist: `find-circular-deps SPEC_ID`
- **Multiple specs returned**: Verify you're using correct SPEC_ID, check spelling
- **Spec file corrupt/invalid**: Validate spec with `validate-spec` command or regenerate with Skill(sdd-toolkit:sdd-plan)

#### 2.2 Apply Selection Criteria

Choose the best task to work on next based on multiple factors.

**Priority Order:**
1. **Blocked tasks are unblocked** - If dependency just completed
2. **Current phase tasks** - Stay in the active phase
3. **Sequential tasks** - Follow natural order (task-1-1 → task-1-2)
4. **High-priority tasks** - If marked in metadata
5. **Parallel-safe tasks** - Can start anytime

**Selection Algorithm:**

The Python tool handles all the logic:
- Find current in_progress phase (or first pending phase)
- Find first unblocked task in that phase
- Return the task with details

```bash
# Find next actionable task
sdd next-task SPEC_ID

# Get JSON output for programmatic use
sdd next-task SPEC_ID --json
```

**Validation:**
- Ensure task is truly unblocked
- Check if dependencies are actually completed
- Verify no circular dependencies
- Confirm task hasn't been started by another tool

#### 2.3 Present Task Options to User

Show available tasks and recommend one.

**Enhanced Presentation with Blocker Analysis:**

```bash
# Get comprehensive task status including blockers
sdd next-task "$SPEC_ID"
sdd list-blockers "$SPEC_ID"
```

**Example Presentation Format (you create this based on command outputs):**
```
📋 Next Actionable Tasks for: User Authentication

Current Phase: Phase 2 - Authentication Service (2/8 tasks, 25%)

🎯 RECOMMENDED: task-2-1
   File: src/services/authService.ts
   Purpose: Implement core authentication service
   Estimated: 3 hours
   Dependencies: ✅ task-1-2 (User model) completed

🚫 BLOCKED TASKS (2):
   task-2-3: src/middleware/auth.ts
   └─ Waiting on: task-2-1 (Implement core authentication service)

   task-3-1: src/cache/redis.ts
   └─ Waiting on: External dependency (Redis server setup)

📌 OTHER AVAILABLE TASKS:

   task-1-7: tests/user.spec.ts [PARALLEL-SAFE]
   Purpose: Write user model tests
   Estimated: 1.5 hours
   Dependencies: None (can start anytime)
   Note: From completed Phase 1

Would you like to:
1. Proceed with recommended task (task-2-1)
2. Select a different task
3. See more details about any task
```

**Benefits of showing blocked tasks:**
- Helps user understand the impact of completing recommended task
- Shows what will be unblocked by completing task-2-1
- Identifies external dependencies that need resolution

**User Response Handling:**
- If user agrees → Proceed to Phase 3 with selected task
- If user picks different task → Proceed with their choice
- If user wants details → Provide deep dive on specific task
- If user wants to defer → Exit gracefully

### Phase 3: Task Context Assembly

Gather all information needed to implement the selected task.

#### 3.1 Extract Task-Specific Details from JSON

Query the JSON spec file for task-specific implementation details.

**Task Details Location:**
All task information is in the JSON spec file hierarchy under the task's ID.

**Task Extraction:**

Use `task-info` command to get complete task details from JSON:

```bash
# Get task details from JSON
sdd task-info user-auth-2025-10-18-001 task-2-1

# Or with explicit path
sdd task-info user-auth-2025-10-18-001 task-2-1 --path /absolute/path/to/specs
```

**What you get from task-info query:**
- ✅ Complete task details from structured data
- ✅ Implementation changes list
- ✅ Reasoning and context
- ✅ Integration points
- ✅ File paths and dependencies
- ✅ Current status

**Enhanced Context with Documentation (Optional - Recommended if available):**

If codebase documentation has been generated, use `Skill(sdd-toolkit:doc-query)` for:
- Automated file suggestions based on task description
- Structured data - no parsing needed
- Complete context in single query

**If codebase documentation has not been generated:**
- Review the spec file's task details for mentioned files
- Use the `Explore` tool to explore the codebase for additional context
- Use `Grep` to search for related code patterns
- Use `Glob` to find files with similar names
- Manually examine files mentioned in integration points

#### 3.2 Gather Dependency Context

Understand what this task depends on and what depends on it.

**From Spec File:**

**⚠️ Use `sdd` commands to query dependencies - DO NOT attempt manual JSON parsing.**

```json
// Example dependency structure in spec file:
"task-2-1": {
  "dependencies": {
    "blocks": ["task-2-2", "task-2-4"],      // What this task blocks
    "blocked_by": [],                         // What blocks this task (empty = can start)
    "depends": ["task-1-2"]                   // Soft dependencies
  }
}
```

**Analysis:**
1. **Blocked By**: Must complete these first (hard dependencies)
2. **Depends**: Recommended order (soft dependencies)
3. **Blocks**: What's waiting on this task
4. **Related**: Other tasks in same file or related files

**Dependency Details:**
For each dependency, gather:
```bash
# Get dependency info using Python tool
sdd check-deps "$SPEC_ID" "$TASK_ID" --path "$SPECS_DIR" --json

# Or for human-readable output:
sdd check-deps "$SPEC_ID" "$TASK_ID" --path "$SPECS_DIR"
```

**Example Output:**
```
Dependencies for task-2-1:

✅ Completed Dependencies:
   - task-1-2: src/models/User.ts (completed 2025-10-18 14:00)
     Provides: User model interface and database access

📦 Soft Dependencies (recommended):
   - None

⏳ This Task Blocks:
   - task-2-2: src/middleware/auth.ts
   - task-2-4: src/routes/auth.ts
```

#### 3.3 Examine Related Files

Look at files that will interact with this task.

Examine these file types:
1. **Primary File** - The file being modified
2. **Dependency Files** - Files this task relies on (from `check-deps`)
3. **Integration Files** - Files that will use this task's output
4. **Pattern Files** - Similar files for convention reference (use `find-related-files`)

**Example Context Assembly (you create this based on file examination):**
```
Related Files for task-2-1:

📝 Primary File: src/services/authService.ts
   Status: Does not exist (will create)

📚 Dependencies:
   src/models/User.ts
   └─ User interface, findByEmail(), validatePassword()

   src/config/jwt.ts
   └─ JWT secret, token expiration settings

🔌 Integration Points:
   src/middleware/auth.ts (will use AuthService.verifyToken)
   src/routes/auth.ts (will use AuthService.login/logout)

📋 Pattern Reference:
   src/services/userService.ts
   └─ Shows service class structure, error handling patterns
```

**Enhanced Context with Documentation (Optional - Recommended if available):**

If codebase documentation has been generated, use `Skill(sdd-toolkit:doc-query)` for:
- Automatic discovery of integration points and affected files
- Finding similar implementation patterns
- Understanding module dependencies

**If codebase documentation has not been generated:**
- Use `Grep` to search for imports: `grep -r "import.*AuthService" .`
- Use `Glob` to find similar files: `glob "**/*Service.ts"`
- Manually review files mentioned in task dependencies
- Use `find-related-files` command for basic file relationships

#### 3.4 Identify Testing Requirements

Determine what tests need to be written or modified.

**Review Verification Requirements:**

Use `sdd query-tasks "$SPEC_ID" --type verify --json` or inspect the `verifications` array in the JSON spec to confirm what needs to be tested and how success is measured.

**Test File Discovery:**

```bash
sdd find-tests  # Find all test files
sdd find-tests --source-file src/services/authService.ts  # Find specific test
```

**Example Testing Context (you create this based on verification steps):**
```
Testing Requirements for task-2-1:

✅ Test File: tests/services/authService.spec.ts
   Status: Does not exist (will create)

📋 Test Cases Needed:
   1. login() with valid credentials → returns JWT
   2. login() with invalid password → throws error
   3. login() with non-existent user → throws error
   4. logout() → invalidates token
   5. Password hashing → bcrypt with proper salt

🔍 Verification Step (verify-2-1):
   Type: Automated test
   Command: npm test -- authService.spec.ts
   Expected: All auth service tests passing
   Status: pending

   ⚠️ All tests must pass before marking task complete
```

**Enhanced Test Context with Documentation (Optional - Recommended if available):**

If codebase documentation has been generated, use `Skill(sdd-toolkit:doc-query)` for:
- Automatic test file discovery
- Understanding test coverage patterns
- Finding similar test implementations

**If codebase documentation has not been generated:**
- Use `find-tests` command to discover test files
- Use `Glob` to search for test patterns: `**/*test*.ts`, `**/*.spec.ts`
- Manually review existing test files for patterns and structure
- Check spec file for verification steps that indicate test requirements

**Benefits when available:** Automatic discovery of test files and coverage estimation.

#### 3.5 Check for Blockers or Risks

Identify potential issues that could prevent completion.

**From Spec Risk Assessment:**
```yaml
risk_level: medium
risk_areas:
  - name: "JWT Secret Management"
    mitigation: "Use environment variables, never commit secrets"
  - name: "Password Hashing Performance"
    mitigation: "Use bcrypt with appropriate work factor (10-12)"
```

**Blocker Analysis:**
```
Potential Blockers for task-2-1:

✅ Clear:
   - Dependencies installed (bcrypt, jsonwebtoken)
   - User model available
   - TypeScript configured

⚠️  Warnings:
   - JWT_SECRET not in .env.example (need to add)
   - No bcrypt work factor constant defined (use 12)

🚫 Blocking Issues:
   - None identified
```

### Phase 4: Execution Plan Creation

Create a detailed, step-by-step plan for implementing the task.

#### 4.1 Define Implementation Steps

Break the task into concrete, ordered steps.

**Example Step Structure (you create this for the execution plan):**
```markdown
## Execution Plan: task-2-1 (src/services/authService.ts)

### Prerequisites
- [x] User model exists (src/models/User.ts)
- [x] bcrypt and jsonwebtoken installed
- [ ] JWT config file created (will create if needed)
- [x] No blocking issues

### Implementation Steps

#### Step 1: Create File Structure
**Action**: Create src/services/authService.ts
**Reasoning**: New file, establish basic structure
**Duration**: 5 minutes
**Key elements**: Import bcrypt, jwt, User model, jwtConfig; create AuthService class

#### Step 2: Implement Password Hashing
**Action**: Add login method with password verification
**Reasoning**: Core authentication logic
**Duration**: 30 minutes
**Key points**:
- Use bcrypt.compare() for password verification
- Handle timing attacks (always hash even if user not found)
- Return clear error messages
- Implement: findByEmail(), validate password, generateToken()

[Continue with remaining steps...]

**Total Estimated Time:** ~2.5 hours (within 3-hour estimate)

#### 4.2 Define Success Criteria

Specify exactly what "done" means for this task.

**Example Success Criteria (you create this based on task requirements):**
```markdown
### Task Completion Checklist

#### Implementation Complete
- [ ] File created: src/services/authService.ts
- [ ] AuthService class implements all methods:
  - [ ] login(email, password) → JWT token
  - [ ] logout(token) → void
  - [ ] generateToken(user) → JWT (private)
- [ ] Password hashing uses bcrypt.compare()
- [ ] JWT generation uses proper config
- [ ] Error handling with AuthenticationError
- [ ] TypeScript types are correct (no 'any')
- [ ] Follows existing service patterns

#### Testing Complete
- [ ] Test file created: tests/services/authService.spec.ts
- [ ] All test cases implemented
- [ ] npm test -- authService.spec.ts passes
- [ ] Test coverage >80% for AuthService

#### Integration Verified
- [ ] AuthService can be imported by other files
- [ ] No circular dependency issues
- [ ] TypeScript compilation succeeds
- [ ] Linting passes

#### Documentation
- [ ] JSDoc comments on public methods
- [ ] README updated if needed
- [ ] Comments explain non-obvious logic

#### Verification (from spec verify-2-1)
- [ ] Command executed: npm test -- authService.spec.ts
- [ ] Result: All tests passing
```

**Definition of Done:**
All checkboxes checked, no failing tests, ready for code review.

#### 4.3 Identify Potential Issues

Note possible problems and solutions.

**Example Potential Issues (you create this based on task analysis):**
```markdown
### Potential Issues and Mitigations

#### Issue 1: JWT Secret Not Configured
**Problem:** JWT_SECRET might not be in environment variables
**Mitigation:** 
1. Add JWT_SECRET to .env.example
2. Check .env file exists and has secret
3. Update src/config/jwt.ts to throw clear error if missing

#### Issue 2: Bcrypt Performance
**Problem:** Password hashing might be slow in tests
**Mitigation:**
1. Use lower work factor in test environment (6-8 vs 12)
2. Consider mocking bcrypt in some tests
3. Run integration tests separately from unit tests

[Additional issues as needed...]
```

#### 4.4 Plan Testing Strategy

Detail how to verify the implementation.

**Testing Layers:**
- Unit Tests: Isolated method testing with mocks
- Integration Tests: Full flow with real dependencies
- Manual Verification: API testing
- Security Review: Vulnerability checks

### Phase 5: Plan Presentation and Approval

Present the complete execution plan to the user for review.

#### 5.1 Format Plan for Presentation

**Use the format-plan command to generate properly formatted output:**

```bash
sdd format-plan {SPEC_ID} {TASK_ID}
```

**IMPORTANT**: The `format-plan` command returns pre-formatted text with proper newlines and indentation.
Display this output EXACTLY as returned - do not reformat or modify it.

**Example Output Structure:**
```markdown
# Execution Plan Ready: task-2-1

## 📋 Task Summary
**File:** src/services/authService.ts
**Purpose:** Implement core authentication service with login/logout
**Phase:** 2 - Authentication Service (2/8 tasks, 25%)
**Estimated Time:** 2.5 hours

## ✅ Prerequisites Verified
- [Dynamically generated based on task dependencies]

## 🎯 Implementation Details
- [Task details extracted from spec JSON]

## ✓ Success Criteria
- [Criteria based on task type and content]

## 📦 Next Tasks After This
- [Tasks that are blocked by this one]

---

## Ready to Proceed?
Options:
1. ✅ Approve plan and begin implementation
2. 📝 Request changes to plan
3. 🔍 See more details about specific steps
4. ⏸️  Defer to later
```

**Note**: The above is just a reference template. The actual output from `format-plan` includes:
- Complete task summary with file path, purpose, phase, and estimated time
- Prerequisites verification (dependencies checked dynamically)
- Implementation details from the spec JSON
- Success criteria tailored to the task type
- Next tasks that depend on this one
- Ready to proceed options

**Always use the `format-plan` command** rather than manually creating this output.

---

## Post-Implementation Checklist

**After completing the implementation and all verification steps:**

1. **Verify Phase Completion Status (Optional)**
```bash
# Check if current phase can be marked complete after this task
sdd check-complete {SPEC_ID} --phase phase-2
```

   If this task completes all tasks in the phase, the phase can be marked completed. This helps track major milestones in the spec.

2. **Update Task Status**

Use `Skill(sdd-toolkit:sdd-update)` to mark the task as completed.

**Information to provide:**
- Spec ID and Task ID
- New status: `completed`
- Completion note: "Implementation finished and verified"

**What sdd-update will do:**
- Update the task status in the spec file
- Automatically recalculate progress across the hierarchy
- Unlock any tasks that were blocked by this task
- Update phase completion status if applicable

3. **Document Deviations (if any)**

If implementation deviated from plan, use `Skill(sdd-toolkit:sdd-update)` to add a journal entry.

**Information to provide:**
- Spec file path
- Journal title: "Implementation Notes: {TASK_ID}"
- Description of deviations or decisions made during implementation

**What sdd-update will do:**
- Add timestamped journal entry to spec metadata
- Document the deviation for future reference
- Maintain audit trail of implementation decisions

4. **Check Context Usage Before Continuing**

Before moving to the next task, check Claude's context window usage to avoid running out of context mid-task:

```bash
/context
```

**Decision Logic:**

- **If context usage >= 50%**: Strongly recommend starting fresh to ensure smooth execution of the next task
  - First ensure task status is updated (step 2 above should already be complete)
  - Message to user:
    ```
    ⚠️  Context usage is at X% (Y/200k tokens). To ensure smooth execution of the next task, I recommend:

    1. First, if you haven't already, update task status: Skill(sdd-toolkit:sdd-update)
    2. Then /clear to start a fresh conversation
    3. Then /sdd-start to resume work on this specification

    This will preserve your progress while giving us a clean context window for the next task.
    ```

- **If context usage < 50%**: Ask user if they want to continue
  - Message to user:
    ```
    ✅ Task completed! Context usage is at X% (Y/200k tokens). Would you like me to prepare the next task now?
    ```

**Important**: Always invoke `Skill(sdd-toolkit:sdd-update)` to save progress BEFORE running `/clear`, as clearing the conversation will lose any unsaved state.

5. **Find Next Task** (only if user wants to continue AND context usage < 50%)

Use `Skill(sdd-toolkit:sdd-next)` skill to identify the next actionable task

**Remember:** Always use `Skill(sdd-toolkit:sdd-update)` after completion to:
- Keep the spec file current
- Unlock dependent tasks waiting on this work
- Maintain accurate progress tracking
- Enable other developers/tools to see what's completed

#### 5.2 Handle User Feedback

Respond to user's decision on the plan.

**User Approves:**
- Mark task as in_progress (handoff to `Skill(sdd-toolkit:sdd-update)`)
- Begin implementation or hand off to implementation tools
- Follow the execution plan

**User Requests Changes:**
- Analyze the requested changes
- Assess impact on scope and timeline
- Check if changes align with spec
- Update plan or recommend spec revision

**User Wants More Details:**
- Provide deep dive into specific steps
- Show code examples
- Explain technical decisions
- Answer questions about approach

## Working with Multiple Agents/Tools

This skill enables coordination across different implementation tools:

**Scenario: Claude creates plan, human implements**
1. Claude: Uses sdd-next to create plan
2. Claude: Presents plan to developer
3. Developer: Implements following the plan
4. Developer: Uses sdd-update to update status
5. Claude: Checks context usage with /context
6. Claude: If >= 50%, recommends /clear then /sdd-start; otherwise finds next task

**Scenario: Claude creates plan, Cursor implements**
1. Claude: Uses sdd-next to create plan
2. Claude: Saves plan to file or shows to user
3. User: Opens Cursor IDE
4. Cursor: Reads JSON spec file
5. Cursor: Implements following Claude's plan
6. Cursor: Updates JSON spec file when complete
7. Claude: Checks context usage with /context
8. Claude: If >= 50%, recommends /clear then /sdd-start; otherwise reads updated JSON spec file and finds next task

## Common Workflows

### Workflow 1: Starting Fresh
**Situation:** Spec exists, no tasks started yet

Steps:
1. Locate spec using enhanced discovery (Phase 1.1) - gets absolute path
2. Read specification frontmatter (Phase 1.2)
3. Load spec file (all tasks pending)
4. Identify phase-1, task-1
5. Create execution plan for first task
6. Present plan to user
7. Mark task in_progress (via sdd-update)
8. Begin implementation

### Workflow 2: Resuming Work
**Situation:** Some tasks completed, need to continue

Steps:
1. Load JSON spec file
2. Check overall progress
3. Identify current phase
4. Find next available task in that phase
5. Verify dependencies are met
6. Create execution plan
7. Present plan with context of progress
8. Continue implementation
9. After completion, check context usage with /context
10. If >= 50%, recommend sdd-update → /clear → /sdd-start workflow

### Workflow 3: Handling Blockers
**Situation:** Next task is blocked by external issue

Steps:
1. Identify next logical task (task-3-1)
2. Check dependencies
3. Discover blocker (e.g., Redis not configured)
4. Document blocker with `Skill(sdd-toolkit:sdd-update)`
5. Find alternative task:
   - Parallel-safe task from same phase
   - Task from different phase
   - Test task that's not blocked
6. Create plan for alternative task
7. Note that original task should resume after blocker cleared

### Workflow 4: Multi-Developer Coordination
**Situation:** Multiple people working on same spec

Steps:
1. Developer A: Uses sdd-next for task-2-1
2. Developer A: Marks task-2-1 in_progress
3. Developer B: Uses sdd-next
4. Developer B: Sees task-2-1 in_progress
5. Developer B: Gets next available task (task-2-3)
6. Both work in parallel
7. Both update state when complete
8. Spec file coordinates progress

### Workflow 5: Plan Refinement
**Situation:** Initial plan needs adjustment during implementation

Steps:
1. Start implementing task per plan
2. Discover issue (e.g., API different than expected)
3. Pause implementation
4. Document deviation with `Skill(sdd-toolkit:sdd-update)`
5. Revise plan with `Skill(sdd-toolkit:sdd-next)`
6. Present revised plan to user
7. Get approval for deviation
8. Update spec if needed
9. Continue with revised plan

## Advanced Query Techniques

For power users who need complex task filtering beyond simple `next-task`.

### Using query-tasks Command

The `query-tasks` command provides flexible filtering for complex scenarios:

**Find all pending tasks in a specific phase:**
```bash
sdd query-tasks "$SPEC_ID" --status pending --parent phase-2 --json
```

**Find all verification tasks:**
```bash
sdd query-tasks "$SPEC_ID" --type verify
```

**Combine filters:**
```bash
# Find all completed tasks in phase-1
sdd query-tasks "$SPEC_ID" --status completed --parent phase-1
```

### When to Use Each Approach

| Tool | Use Case | Example |
|------|----------|---------|
| `next-task` | Find single next actionable task | "What should I work on now?" |
| `query-tasks` | Filter tasks by criteria | "Show all pending tasks in phase-2" |
| `list-blockers` | Understand what's blocked | "Which tasks are waiting on dependencies?" |

### Common Advanced Queries

**1. Find all tasks that can be started right now:**
```bash
# Pending tasks with no blockers
sdd query-tasks "$SPEC_ID" --status pending
```

**2. Analyze blocked tasks:**
```bash
# See what's blocking progress
sdd list-blockers "$SPEC_ID" --json
```

**3. Check phase completion readiness:**
```bash
# Before moving to next phase, verify current phase is complete
sdd check-complete "$SPEC_ID" --phase phase-2
```

**4. Get all verification steps:**
```bash
# Find all verifications to understand testing requirements
sdd query-tasks "$SPEC_ID" --type verify
```

**5. Find tasks by parent (all tasks in a phase):**
```bash
# Get all tasks under phase-2, regardless of status
sdd query-tasks "$SPEC_ID" --parent phase-2 --json
```

## Troubleshooting

### Issue: Spec File Not Found / Path Errors

**Symptoms:**
- Error: `grep: specs/active/file.json: No such file or directory`
- Commands return "No content" or file not found errors

**Root Cause:**
The skill is run from a different working directory than where specs are located. Relative paths fail because they don't exist relative to the current directory.

**Solutions:**
1. **Provide absolute path** when invoking: Set `SPEC_PATH_PARAM="/absolute/path/to/specs/active/myspec.json"`
2. **Run from correct directory**: Navigate to directory containing `specs/`
3. **Use enhanced discovery**: Phase 1.1 checks multiple common locations automatically

**Prevention:**
Always run `sdd verify-tools` before starting spec work.

### Issue: Can't Find Next Task
**Symptoms:**
- All tasks show as blocked
- No pending tasks in current phase
- Spec file shows 100% but spec shows pending tasks

**Diagnosis:**
1. Check spec file for consistency
2. Verify dependencies are correctly marked
3. Look for circular dependencies
4. Check if phase ordering is wrong

**Solution:**

Use the Python tool for dependency analysis:

```bash
sdd find-circular-deps "$SPEC_ID"
sdd next-task "$SPEC_ID"
```

Detects circular chains, orphaned tasks, and impossible dependency chains.

### Issue: Spec File Inconsistency
**Symptom:** JSON spec file has inconsistent or incorrect data
**Solution:** Regenerate JSON spec file with `Skill(sdd-toolkit:sdd-plan)`

### Issue: Dependencies Not Clear
**Symptom:** Unsure if task dependencies are met
**Solution:** Use `sdd check-deps SPEC_ID TASK_ID` to verify status; ask user if still unclear

### Issue: Plan Too Complex
**Symptom:** Plan is too large or exceeds estimates
**Solution:** Split into smaller tasks using sdd-update

## Quick Reference

### Core Workflow Commands

**Automated Workflow (Recommended):**
```bash
# 1. Prepare task (handles discovery automatically)
sdd prepare-task SPEC_ID
```

**Manual Task Discovery:**
```bash
# Find next task
sdd next-task SPEC_ID

# Get task details
sdd task-info SPEC_ID TASK_ID

# Check dependencies
sdd check-deps SPEC_ID TASK_ID

# View progress
sdd progress SPEC_ID
```

**Advanced Querying:**
```bash
# Query tasks by criteria
sdd query-tasks SPEC_ID --status pending

# List blocked tasks
sdd list-blockers SPEC_ID

# Check completion readiness
sdd check-complete SPEC_ID --phase phase-2

```

**Project Analysis:**
```bash
# Detect project type
sdd detect-project

# Find tests
sdd find-tests

# Validate environment
sdd check-environment
```

### Optional/Advanced Commands

**Environment Setup (one-time):**
```bash
# Initialize environment variables
sdd init-env --export
```

**Note:** Most commands auto-discover specs directory. Add `--path /absolute/path/to/specs` if needed for custom locations.

## Summary

**Core Responsibility:**
Bridge specifications to implementation by identifying next tasks, gathering context, and creating detailed execution plans.

**Path Handling (IMPORTANT):**
- ✅ **Always uses absolute paths** - Works from any working directory
- ✅ **Enhanced discovery** - Checks multiple common locations automatically
- ✅ **Optional path parameter** - Can specify exact spec location
- ✅ **Early validation** - Fails fast with clear errors if paths not found

**Key Operations:**
- ✅ Find specifications in project
- ✅ Load JSON spec files (using Python for JSON parsing)
- ✅ Identify next actionable task (using Python tools)
- ✅ Gather task context and dependencies (using Python tools)
- ✅ Examine related files and patterns
- ✅ Create detailed execution plans
- ✅ Present plans for user approval
- ✅ Handle feedback and revisions
- ✅ Coordinate with Manager for status updates

**Integration Points:**
- Reads specs created by `Skill(sdd-toolkit:sdd-plan)`
- Updates status using `Skill(sdd-toolkit:sdd-update)`
- Enables handoff to coding tools
- Coordinates multi-developer workflows

**Remember:** This skill's job is to make the transition from "what to do" (spec) to "how to do it" (execution plan) as smooth and clear as possible. Always ensure full context is gathered before creating a plan.

## See Also

**Skill(sdd-toolkit:sdd-plan)** - Use before this skill to:
- Create new specifications
- Define phases and tasks
- Generate initial spec files
- Set up the project structure

**Skill(sdd-toolkit:sdd-update)** - Use alongside this skill to:
- Mark tasks as in_progress before implementing
- Mark tasks as completed after implementing
- Document deviations and decisions during implementation
- Track progress and update metrics
- Journal verification results

---

*For creating specifications, use `Skill(sdd-toolkit:sdd-plan)`. For tracking progress, use `Skill(sdd-toolkit:sdd-update)`.*
