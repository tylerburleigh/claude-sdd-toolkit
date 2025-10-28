---
name: sdd-plan
description: Plan-first development methodology that creates detailed specifications before coding. Use when building features, refactoring code, or implementing complex changes. Creates structured plans with phases, file-level details, and verification steps to prevent drift and ensure production-ready code.
---

# Spec-Driven Development: Plan Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-toolkit:sdd-plan)** (this skill) - Creates specifications and task hierarchies
- **Skill(sdd-toolkit:sdd-next)** - Identifies next tasks and creates execution plans
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

**Your Role (PLAN)**: Create the specification and initial task structure before any implementation begins.

**Planning Modes:**
- **Staged (Recommended for complex features)**: Generate phase structure → user review → detailed tasks
- **Direct (For simple features)**: Generate complete specification in one pass

## Core Philosophy

**Plan First, Code Second**: Every development task begins with a detailed specification that acts as a contract between intent and implementation. This prevents the common failure mode where AI "works once and then falls apart" in real codebases.

**Staged Planning (Recommended)**: For complex features, create specifications in two stages: (1) high-level phase structure for user review and approval, then (2) detailed task breakdown. This reduces wasted effort and enables early course correction before detailed planning begins.

**Atomic Tasks**: Each task represents a single, focused change to one file. Tasks are the fundamental unit of work in SDD, and keeping them atomic provides:
- **Precise dependency tracking**: File-level dependencies are explicit and clear
- **Granular progress monitoring**: Each completed task represents concrete, verifiable progress
- **Parallel implementation**: Independent tasks can be worked on simultaneously
- **Straightforward verification**: Each task has a focused scope and clear success criteria
- **Easy rollback**: Changes can be reverted at the file level without affecting other work

When a feature requires changes across multiple files, decompose it into multiple tasks with proper dependencies, or use subtasks to organize related file changes under a parent task. Never bundle multiple file changes into a single task. See [docs/BEST_PRACTICES.md](../../docs/BEST_PRACTICES.md) for detailed guidance on task decomposition.

**Key Benefits:**
- Reduces hallucinated APIs and misread intent
- Prevents breaking existing functionality
- Provides clear verification criteria
- Enables confident iteration
- Creates auditable development process
- Early feedback checkpoint reduces rework (staged approach)

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (validate, fix, report, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd` CLI wrapper commands (e.g., `sdd validate`, `sdd fix`, `sdd report`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python sdd_plan.py`, `bash python3 scripts/plan.py`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail. All spec operations should go through the CLI.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## When to Use This Skill

Use Skill(sdd-toolkit:sdd-plan) for:
- New features or significant functionality additions
- Complex refactoring across multiple files
- API integrations or external service connections
- Architecture changes or system redesigns
- Any task where precision and reliability are critical
- Large codebases where context drift is a risk

**Do NOT use for:**
- Simple one-file changes or bug fixes
- Trivial modifications or formatting changes
- Exploratory prototyping or spikes
- Quick experiments or proof-of-concepts
- Updating existing specs (use Skill(sdd-toolkit:sdd-update))
- Finding what to work on next (use Skill(sdd-toolkit:sdd-next))
- Tracking task progress (use Skill(sdd-toolkit:sdd-update))

## Skill Handoff Points

**When to transition to other skills:**

→ **To Skill(sdd-toolkit:sdd-next)**:
  - After JSON spec file is created
  - When ready to begin implementation
  - User asks "what should I work on next?"
  - Need to identify the first/next actionable task

→ **To Skill(sdd-toolkit:sdd-update)**:
  - Need to update task status during planning
  - Must document a planning decision
  - Spec needs to be moved between folders
  - Progress metrics need updating

→ **To Implementation**:
  - Never directly - always go through Skill(sdd-toolkit:sdd-next) first
  - Skill(sdd-toolkit:sdd-next) creates the execution plan
  - Then implementation tools (coding assistants) execute it

## The Spec-Driven Development Process

### Phase 1: Specification Creation

Create a detailed specification document before writing any code.

#### 1.0 High-Level Phase Planning Stage (Recommended First Step)

**Purpose**: Before diving into detailed task planning, create a high-level phase structure for user review and approval. This staged approach reduces wasted effort and enables early course correction.

**When to Use Staged Planning:**
- Complex features requiring multiple phases (3+ phases expected)
- Projects where requirements might need adjustment
- Situations where you want early stakeholder feedback
- Large refactorings affecting many files

**When to Skip to Full Planning:**
- Simple, well-understood tasks (1-2 phases max)
- Urgent changes where speed is critical
- When you're highly confident in the approach

**Staged Planning Workflow:**

1. **Generate Phase-Only Plan** (Markdown format for easy review)
2. **User Review & Approval Checkpoint**
3. **Generate Detailed Tasks** (Complete JSON spec)

##### 1.0.1 Creating the Phase-Only Plan

Generate a concise markdown document outlining just the high-level phases. **Do not create detailed tasks yet.**

**Phase-Only Markdown Template:**

```markdown
# High-Level Plan: [Feature/Change Name]

## Overview
Brief description of what this change accomplishes and why.

## Objectives
- Primary objective
- Secondary objectives
- Success criteria

## Proposed Phases

### Phase 1: [Phase Name]
**Purpose**: What this phase accomplishes
**Dependencies**: What must exist before starting
**Risk Level**: Low/Medium/High
**Key Deliverables**:
- Deliverable 1
- Deliverable 2

**Estimated Files Affected**: 3-5 files
**Estimated Complexity**: Low/Medium/High

### Phase 2: [Phase Name]
[Repeat structure for each phase]

### Phase N: [Phase Name]
[Repeat structure for each phase]

## Implementation Order
1. Phase X (must complete first)
2. Phase Y (depends on X)
3. Phase Z (can run parallel to Y)

## Key Integration Points
- How phases connect to each other
- Critical dependencies between phases
- Potential breaking points or risks

## Questions for Review
- Any specific concerns about this approach?
- Are there phases missing or phases that should be combined?
- Does the order make sense?
```

**Guidelines for Phase Planning:**
- **Be concise**: Each phase description should be 3-5 sentences max
- **Focus on "what" not "how"**: Save implementation details for later
- **Identify dependencies**: Make phase ordering clear
- **Highlight risks**: Call out high-risk phases early
- **Estimate scope**: Rough file counts help set expectations
- **Ask questions**: Invite feedback on unclear areas

##### 1.0.2 User Review & Approval Checkpoint

**Present the phase-only plan to the user and explicitly request approval before proceeding.**

**Example Interaction Pattern:**

```
AI: "Let me first propose the high-level phase structure for this feature.
    This will help us ensure we're on the right track before diving into
    detailed task planning."

[AI generates phase-only markdown following template above]

AI: "I've outlined 4 phases for implementing user authentication:
    1. Database Schema (foundational)
    2. Auth Service Layer (core logic)
    3. API Integration (connects to app)
    4. Testing & Verification (ensures quality)

    Does this phase structure make sense? Any phases you'd like to add,
    remove, or reorganize before I create the detailed task breakdown?"

[User reviews and responds]

User: "Looks good, but let's add a phase for migration of existing users
       between Phase 2 and 3."

AI: "Great point! I'll add 'Phase 3: User Migration' between Auth Service
    and API Integration. Let me update the plan..."

[AI revises phase structure]

AI: "Updated plan with migration phase. Does this revised structure work?"

User: "Perfect, go ahead with the detailed planning."

AI: "Excellent! Now I'll create the complete specification with detailed
    tasks for each phase..."

[AI proceeds to section 1.1-1.3.2 to generate full JSON spec]
```

**Key Points for This Checkpoint:**
- ✅ **Explicit approval required**: Don't proceed without clear confirmation
- ✅ **Invite feedback**: Encourage the user to suggest changes
- ✅ **Be flexible**: Expect iteration on phase structure
- ✅ **Summarize changes**: Clearly state what you're updating
- ✅ **Confirm before proceeding**: Get final "go ahead" before detailed work

##### 1.0.3 Benefits of Staged Planning

**For Users:**
- Review and redirect early (5 minutes vs 30 minutes)
- Easier to understand high-level structure
- Natural checkpoint for collaboration
- Confidence that detailed work will be on target

**For AI:**
- Validated direction before detailed generation
- Clearer constraints and requirements
- Reduced rework from misunderstanding
- Better context for task generation

##### 1.0.4 Proceeding to Detailed Planning

Once the phase structure is approved:
1. **Proceed to section 1.1**: Understand the Intent (if not already done)
2. **Continue to section 1.2**: Analyze the Codebase
3. **Generate full spec in section 1.3.2**: Using approved phases as structure
4. **Reference approval**: "Based on the approved phase structure, I'll now create detailed tasks for each phase..."

**Important**: The approved phase structure should guide your detailed JSON generation. Maintain consistency between what was approved and what you generate.

---

#### 1.1 Understand the Intent

Begin by deeply understanding what needs to be accomplished:
- **Core objective**: What is the primary goal?
- **User perspective**: How will users interact with this?
- **Success criteria**: What defines "done"?
- **Constraints**: What limitations or requirements exist?

#### 1.2 Analyze the Codebase

Before creating the plan, explore the relevant parts of the codebase:
- Identify existing patterns and conventions
- Locate related functionality
- Map dependencies and integration points
- Review similar implementations for consistency
- Note potential conflicts or breaking changes

#### 1.2.1 Using `Skill(sdd-toolkit:doc-query)` for Efficient Codebase Analysis (Recommended)

**Proactive Documentation Generation**

Before starting codebase analysis, **automatically check** if documentation exists. If missing, offer to generate it for faster and more accurate planning.

**Auto-Detection Workflow:**

1. **Check for existing documentation** (fast check):
```bash
sdd doc stats
```

2. **If documentation not found**, proactively ask the user:
```
I notice this codebase doesn't have documentation yet. Would you like me to
generate it? This will enable much faster and more accurate codebase analysis.

Generating documentation will take 2-5 minutes but will speed up all future
planning tasks.

Generate documentation now? [Y/n]
```

3. **If user agrees**, run the `Skill(sdd-toolkit:code-doc)` skill to generate documentation

Then invoke `Skill(sdd-toolkit:doc-query)` for codebase analysis.

4. **If user declines** or generation fails, fall back to manual exploration using `Explore`, or alternatively Glob/Read.

**Documentation-First Approach:**
- **10x faster codebase analysis** - Seconds vs minutes of manual exploration
- **Better quality specs** - Comprehensive understanding of patterns and dependencies
- **Future time savings** - Documentation used across all subsequent planning tasks
- **Consistency** - Follow existing patterns automatically

---

**Using Existing Documentation:**

If codebase documentation has been generated, use `Skill(sdd-toolkit:doc-query)` to efficiently gather context before planning. This provides structured, comprehensive codebase understanding without manual exploration.

**Recommended Analysis Workflow:**

The `Skill(sdd-toolkit:doc-query)` provides the following capabilities (command examples shown for reference):

**Step 1: Get Codebase Overview**
```bash
# See overall structure and metrics
sdd doc stats

# Example output:
# Total Modules: 37
# Total Classes: 84
# Total Functions: 53
# Average Complexity: 2.42
# Max Complexity: 8
```

**Step 2: Search for Similar Implementations**
```bash
# Find existing implementations of similar features
sdd doc search "feature-keyword"

# Example: Planning authentication? Search for "auth"
sdd doc search "auth"
# Finds: AuthService, authentication middleware, User model, etc.
```

**Step 3: Gather Feature Area Context**
```bash
# Get all entities related to feature area
sdd doc context "feature-area"

# Example: Planning user management
sdd doc context "user"
# Returns: All classes, functions, modules related to users
```

**Step 4: Analyze Target Module Complexity**
```bash
# Identify high-complexity functions in target area
sdd doc complexity --threshold 5 --module target_module.py

# Use to:
# - Identify refactoring needs
# - Plan testing strategy
# - Estimate implementation complexity
```

**Step 5: Map Dependencies and Impact**
```bash
# Check what a module depends on
sdd doc dependencies app/services/module.py

# Check what depends on it (reverse dependencies - impact analysis)
sdd doc dependencies app/services/module.py --reverse

# Use to:
# - Understand integration points
# - Identify breaking change risks
# - Plan implementation order
```

**Step 6: Find Test Files and Coverage**
```bash
# Find tests for a module
sdd doc search "test.*module_name"
```

**Integration Example:**

When planning "Add JWT Authentication" feature:

```bash
# 1. Check docs exist
sdd doc stats

# 2. Search for existing auth
sdd doc search "auth"
# Found: app/middleware/auth.py, app/models/session.py

# 3. Get full auth context
sdd doc context "auth"
# Returns: 4 classes, 3 functions, dependencies

# 4. Check auth middleware dependencies
sdd doc dependencies app/middleware/auth.py --reverse
# Shows: 5 routes depend on this middleware

# 5. Find similar implementations
sdd doc find-class ".*Service.*" --pattern
# Identify service layer patterns to follow

# 6. Check complexity of related code
sdd doc complexity --module auth.py
# Understand existing auth complexity
```

**Benefits of Using `Skill(sdd-toolkit:doc-query)`:**
- ✅ **10x faster analysis** - Structured queries vs manual exploration
- ✅ **More accurate specs** - Based on actual structure, not assumptions
- ✅ **Better dependency awareness** - Understand impact upfront
- ✅ **Pattern consistency** - Find and follow existing patterns
- ✅ **Risk mitigation** - Identify breaking changes early
- ✅ **Comprehensive context** - Nothing missed in analysis

**When codebase documentation has not been generated:**
Fall back to manual codebase exploration:
- Use `Explore` to explore the codebase
- Use `Glob` to find files: `**/*auth*.py`
- Use `Grep` to search code: `class.*Service`
- Use `Read` to examine files directly
- **Recommend**: Generate documentation first for better planning

**After Analysis:**
Use gathered insights to create accurate, well-informed specifications in Phase 1.3.

#### 1.3 Create the Specification Document

**NOTE**: If you used staged planning (section 1.0), you should now have an approved phase structure. Use that as the foundation for your detailed specification. Maintain consistency with what the user approved.

**IMPORTANT**: The specification is a JSON file (created in section 1.3.2). The markdown template below is a **conceptual planning guide** to help you gather and organize information before creating the JSON. You will NOT create this markdown file - it shows what information to plan for.

**PLANNING GUIDE (Markdown Template for Information Gathering):**

NOTE: This template shows WHAT to plan, not WHAT to create. Use it to organize your thoughts, then proceed to section 1.3.2 to create the actual JSON spec file.

**SPECIFICATION TEMPLATE:**

```markdown
# Specification: [Feature/Change Name]

## Overview
Brief description of what this change accomplishes and why.

## Objectives
- Primary objective
- Secondary objectives
- Success criteria

## Phases

### Phase 1: [Phase Name]
**Purpose**: What this phase accomplishes
**Dependencies**: What must exist before starting
**Risk Level**: Low/Medium/High

**Files to Modify:**
- `path/to/file1.ext`
  - **Changes**: Specific modifications needed
  - **Reasoning**: Why these changes are necessary
  - **Integration points**: How this connects to other parts

- `path/to/file2.ext`
  - **Changes**: Specific modifications needed
  - **Reasoning**: Why these changes are necessary
  - **Integration points**: How this connects to other parts

**Verification Steps:**
1. Specific check to perform
2. Expected outcome
3. How to validate correctness

### Phase 2: [Phase Name]
[Repeat structure for each phase]

## Implementation Order
1. Phase X (must complete first)
2. Phase Y (depends on X)
3. Phase Z (can run parallel to Y)

## Verification Checklist
- [ ] All planned files modified
- [ ] No unintended side effects
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No regressions introduced
- [ ] Follows existing patterns
- [ ] Performance acceptable
- [ ] Security considerations addressed

## Rollback Plan
How to revert changes if issues arise.

## Post-Implementation
- Monitoring requirements
- Documentation to update
- Team communication needs
```

**Critical Specification Requirements:**
- **File-level detail**: Specify EXACTLY which files will be modified
- **Clear reasoning**: Every change must have explicit justification
- **Phase ordering**: Define clear dependencies between phases
- **Verification criteria**: Include specific, testable checks
- **Integration awareness**: Note how changes affect other systems

#### 1.3.1 Plan the Task Hierarchy (Visualization Guide)

**IMPORTANT**: This section shows hierarchy notation for PLANNING and VISUALIZATION only. You will NOT create files in this format. This is a way to conceptualize the structure before creating the JSON in section 1.3.2.

Use this notation to plan your hierarchy, then translate it into JSON structure in section 1.3.2.

**Hierarchy Levels:**
1. **[Spec]** - Root of entire specification
2. **[Phase]** - Major implementation phase from spec
3. **[Group]** - Container for related tasks ("File Modifications", "Verifications")
4. **[Task]** - Individual file modification or logical unit
5. **[Subtask]** - Specific change within a file
6. **[Verify]** - Verification step (automated or manual)

**Format Requirements:**

**Spec Level** (root of everything):
```
[Spec] Feature Name (0/total tasks, 0%) {#spec-root}
```
- Always uses ID `{#spec-root}`
- Shows total task count across all phases
- Initial progress always 0%

**Phase Level** (major implementation stages):
```
[Phase] Phase Name (0/phase_task_count tasks) {#phase-N}
```
- Sequential numbering: phase-1, phase-2, etc.
- Task count only for this phase
- All phases start as `[pending]`

**Group Level** (task containers within phase):
```
[Group] File Modifications (0/group_task_count tasks) {#phase-N-files}
[Group] Verification (0/verify_task_count tasks) {#phase-N-verify}
```
- Two standard groups per phase: `-files` and `-verify`
- File modifications group comes first
- Verification group blocked by files group

**Task Level** (individual work units):
```
[Task] path/to/file.ext [pending] {#task-N-M}
[Task] path/to/file.ext [pending] [depends: task-X-Y] {#task-N-M}
[Task] path/to/file.ext [pending] [blocked-by: task-X-Y] {#task-N-M}
[Task] path/to/file.ext [pending] [parallel-safe] {#task-N-M}
```
- One task per file or logical unit
- N = phase number, M = task number within phase
- Dependency markers optional but important

**Subtask Level** (granular steps):
```
[Subtask] Specific change description [pending] {#task-N-M-P}
```
- P = subtask number
- Use when task needs breakdown
- Each should be < 30 minutes

**Verification Level** (validation steps):
```
[Verify] What to check [pending] [auto] {#verify-N-M}
[Verify] What to check [pending] [manual] {#verify-N-M}
```
- Mark as `[auto]` if can be scripted
- Mark as `[manual]` if requires human judgment
- Include command for automated checks

**Example Hierarchy:**
```
[Spec] User Authentication (0/23 tasks, 0%) {#spec-root}
│
├─ [Phase] Database Schema (0/7 tasks) {#phase-1}
│   │
│   ├─ [Group] File Modifications (0/3 tasks) {#phase-1-files}
│   │   │
│   │   ├─ [Task] db/migrations/001_add_users.sql [pending] {#task-1-1}
│   │   │   ├─ [Subtask] Create users table [pending] {#task-1-1-1}
│   │   │   ├─ [Subtask] Add constraints [pending] {#task-1-1-2}
│   │   │   └─ [Subtask] Create indexes [pending] {#task-1-1-3}
│   │   │
│   │   ├─ [Task] src/models/User.ts [pending] [depends: task-1-1] {#task-1-2}
│   │   │   └─ [Subtask] Define interface [pending] {#task-1-2-1}
│   │   │
│   │   └─ [Task] src/types/index.ts [pending] [parallel-safe] {#task-1-3}
│   │       └─ [Subtask] Export User type [pending] {#task-1-3-1}
│   │
│   └─ [Group] Verification [blocked-by: phase-1-files] (0/4 tasks) {#phase-1-verify}
│       ├─ [Verify] Migration runs [pending] [auto] {#verify-1-1}
│       │   └─ Command: `npm run migrate`
│       ├─ [Verify] Model imports [pending] [auto] {#verify-1-2}
│       ├─ [Verify] Tests pass [pending] [auto] {#verify-1-3}
│       │   └─ Command: `npm test -- user.spec.ts`
│       └─ [Verify] Validation works [pending] [manual] {#verify-1-4}
```

**Verification Steps:**
- Group all verifications together (separate from file modifications)
- One verification per test/check
- Include command/steps for automated verifications
- Mark manual verifications clearly

**Rule of Thumb:**
- Each task/subtask should be completable in < 30 minutes
- If estimating > 30 minutes, break into subtasks
- Verification tasks can be longer (might include multiple test runs)

### Dependency Tracking

**Dependency Types:**

**Hard Dependencies** (`[blocked-by: task-id]`):
- Cannot start until dependency completes
- Used for sequential requirements
- Example: Can't write tests until model is created
```
[Task] tests/user.spec.ts [pending] [blocked-by: task-1-2] {#task-1-4}
```

**Soft Dependencies** (`[depends: task-id]`):
- Recommended order but not strictly required
- Used for logical sequencing
- Example: Should implement helper before service, but not required
```
[Task] src/services/auth.ts [pending] [depends: task-1-2] {#task-2-1}
```

**Blocks** (`[blocks: task-id]`):
- Explicit marker that this task blocks others
- Usually redundant with blocked-by but helps navigation
- Used sparingly for critical path items

**Parallel-Safe** (`[parallel-safe]`):
- Can be done in any order
- No dependencies on other tasks
- Can be implemented simultaneously
```
[Task] src/types/index.ts [pending] [parallel-safe] {#task-1-3}
```

**Phase Dependencies:**
- Phases are sequential by default
- Later phases blocked by earlier phases
- Make this explicit in hierarchy:
```
[Phase] Auth Service [blocked-by: phase-1] (0/8 tasks) {#phase-2}
```

### Progress Indicators

**Multi-Level Progress Tracking:**

Show progress at every level of hierarchy:
```
[Spec] Feature (0/23 tasks, 0%) {#spec-root}
└─ [Phase] Setup [pending] (0/7 tasks, 0%) {#phase-1}
    └─ [Group] File Modifications (0/3 tasks, 0%) {#phase-1-files}
```

**Progress Calculation (At Creation Time):**
- All tasks start at `[pending]`
- All progress percentages are 0%
- Task counts come from spec structure
- Progress format: `(completed/total tasks, percentage%)`

**Status Values (At Creation):**
- `[pending]` - All tasks initially pending
- No tasks marked as `in_progress`, `completed`, or `blocked` at creation
- Implementation status tracking happens later via sdd-update

**Display Format:**
- Spec level: Total task count and percentage
- Phase level: Task count for that phase
- Group level: Task count for that group
- Individual tasks: Status only, no count

**Automatic Task Count Calculation:**

You don't need to manually calculate task counts - the `sdd fix` command handles this automatically:

```bash
# Preview fixes without applying (recommended first step)
sdd fix specs/active/your-spec.json --preview

# Apply fixes to task counts and hierarchy integrity
sdd fix specs/active/your-spec.json
```

**How it works:**
- Uses `recalculate_progress()` from `sdd_common/progress.py`
- Recursively calculates counts from leaf nodes up through hierarchy
- Leaf nodes (individual tasks/subtasks) = 1 task each
- Parent nodes sum their children's counts
- Ensures counts stay synchronized as spec evolves

**When to use:**
- After adding/removing tasks from JSON hierarchy
- When validation reports count mismatches
- Before running sdd-next (ensures accurate counts)
- Any time counts seem out of sync

**Common pitfall:** Don't manually update `total_tasks` or `completed_tasks` in the JSON - let `sdd fix` or `sdd-update` handle it automatically to avoid arithmetic errors.

### Task ID Format

**Hierarchical ID Structure:**
- Spec: `{#spec-root}`
- Phase: `{#phase-N}`
- Group: `{#phase-N-files}` or `{#phase-N-verify}`
- Task: `{#task-N-M}` (phase number, task number)
- Subtask: `{#task-N-M-P}` (includes subtask number)
- Verification: `{#verify-N-M}`

**Examples:**
```
{#spec-root}           - Root spec
{#phase-1}            - Phase 1
{#phase-1-files}      - Phase 1 file modifications group
{#task-1-1}           - Phase 1, task 1
{#task-1-1-1}         - Phase 1, task 1, subtask 1
{#phase-1-verify}     - Phase 1 verification group
{#verify-1-1}         - Phase 1, verification 1
```

**ID Stability:**
- IDs assigned at creation time
- Remain stable during refinement if possible
- If structure changes significantly, regenerate with new IDs
- Never reuse IDs within same spec

#### 1.3.2 Create the JSON Spec File (Single Source of Truth)

**THIS IS THE ACTUAL SPEC FILE YOU WILL CREATE.** After planning your structure using the guides in sections 1.3 and 1.3.1, now create the JSON file that will be used by sdd-next, sdd-update, and all other SDD tools.

**If you completed staged planning (section 1.0):** Base your JSON hierarchy on the approved phase structure. The phase names, ordering, and dependencies should match what the user approved. Now you're adding the detailed task breakdown within each phase.

**Note:** Generate this JSON file manually following the structure described below.

**Location:**
`specs/active/{spec-id}.json`

**Initial Spec File Structure:**

```json
{
  "spec_id": "user-auth-2025-10-18-001",
  "generated": "2025-10-18T10:00:00Z",
  "last_updated": "2025-10-18T10:00:00Z",
  
  "hierarchy": {
    "spec-root": {
      "type": "spec",
      "title": "User Authentication",
      "status": "pending",
      "parent": null,
      "children": ["phase-1", "phase-2", "phase-3"],
      "total_tasks": 24,
      "completed_tasks": 0,
      "metadata": {}
    },
    
    "phase-1": {
      "type": "phase",
      "title": "Database Schema",
      "status": "pending",
      "parent": "spec-root",
      "children": ["phase-1-files", "phase-1-verify"],
      "total_tasks": 8,
      "completed_tasks": 0,
      "metadata": {}
    },
    
    "phase-1-files": {
      "type": "group",
      "title": "File Modifications",
      "status": "pending",
      "parent": "phase-1",
      "children": ["task-1-0", "task-1-1", "task-1-2", "task-1-3"],
      "total_tasks": 4,
      "completed_tasks": 0,
      "metadata": {}
    },

    "task-1-0": {
      "type": "task",
      "title": "Analyze existing user data schema",
      "status": "pending",
      "parent": "phase-1-files",
      "children": [],
      "dependencies": {
        "blocks": ["task-1-1"],
        "blocked_by": [],
        "depends": []
      },
      "total_tasks": 1,
      "completed_tasks": 0,
      "metadata": {
        "task_category": "investigation",
        "estimated_hours": 2
      }
    },

    "task-1-1": {
      "type": "task",
      "title": "db/migrations/001_add_users.sql",
      "status": "pending",
      "parent": "phase-1-files",
      "children": ["task-1-1-1", "task-1-1-2", "task-1-1-3"],
      "dependencies": {
        "blocks": [],
        "blocked_by": ["task-1-0"],
        "depends": []
      },
      "total_tasks": 3,
      "completed_tasks": 0,
      "metadata": {
        "file_path": "db/migrations/001_add_users.sql",
        "estimated_hours": 1,
        "task_category": "implementation"
      }
    },
    
    "task-1-1-1": {
      "type": "subtask",
      "title": "Create users table",
      "status": "pending",
      "parent": "task-1-1",
      "children": [],
      "dependencies": {
        "blocks": [],
        "blocked_by": [],
        "depends": []
      },
      "total_tasks": 1,
      "completed_tasks": 0,
      "metadata": {}
    },
    
    "phase-1-verify": {
      "type": "group",
      "title": "Verification",
      "status": "pending",
      "parent": "phase-1",
      "children": ["verify-1-1", "verify-1-2"],
      "dependencies": {
        "blocks": [],
        "blocked_by": ["phase-1-files"],
        "depends": []
      },
      "total_tasks": 2,
      "completed_tasks": 0,
      "metadata": {}
    },
    
    "verify-1-1": {
      "type": "verify",
      "title": "Migration runs without errors",
      "status": "pending",
      "parent": "phase-1-verify",
      "children": [],
      "dependencies": {
        "blocks": [],
        "blocked_by": [],
        "depends": []
      },
      "total_tasks": 1,
      "completed_tasks": 0,
      "metadata": {
        "verification_type": "auto",
        "command": "npm run migrate",
        "expected": "Migration completes successfully"
      }
    }
  }
}
```

**Spec File Generation Rules:**
1. Every node in the hierarchy becomes an entry
2. All statuses initially "pending"
3. All completed_tasks initially 0
4. Parent-child relationships must be bidirectional
5. Dependencies explicitly listed
6. Metadata includes file_path for tasks (required for implementation/refactoring tasks)
7. Metadata should include task_category to classify work type (optional but recommended)
8. Generated and last_updated timestamps at root

**Critical:**
- JSON spec file is the single source of truth
- Updated by sdd-update, not this skill
- Read by sdd-next to find next tasks
- Store in specs/active/, specs/completed/, or specs/archived/
- Consider adding to .gitignore (user preference)
- Human-readable views can be generated on-demand using `sdd report`

#### Task Category Metadata

Tasks should include a `task_category` field in their metadata to classify the type of work being performed. This helps with task planning, time estimation, and workflow optimization.

**Available Categories:**

- **`investigation`**: Exploring or analyzing existing code to understand behavior, trace bugs, or map dependencies
- **`implementation`**: Writing new functionality, features, or code that adds capabilities
- **`refactoring`**: Improving code structure, organization, or quality without changing external behavior
- **`decision`**: Architectural or design choices requiring analysis, comparison, or selection between alternatives
- **`research`**: Gathering information, reading documentation, exploring external libraries, or learning new technologies

**Category Selection Guidelines:**

| Category | When to Use | Typical Duration | Requires file_path |
|----------|-------------|------------------|-------------------|
| `investigation` | Need to understand existing code before making changes | Short-Medium | No (optional) |
| `implementation` | Creating new files, adding features, writing new code | Medium-Long | Yes (required) |
| `refactoring` | Reorganizing existing code without changing behavior | Medium | Yes (required) |
| `decision` | Need to choose between approaches or make architectural decisions | Short | No |
| `research` | Learning about external tools, reading specs, exploring patterns | Short-Medium | No |

**Examples:**

```json
// Investigation task - analyzing existing code
{
  "task-1-1": {
    "type": "subtask",
    "title": "Analyze current authentication flow",
    "status": "pending",
    "parent": "phase-1",
    "children": [],
    "metadata": {
      "task_category": "investigation",
      "estimated_hours": 2
    }
  }
}

// Implementation task - writing new functionality
{
  "task-2-1": {
    "type": "task",
    "title": "src/services/authService.ts",
    "status": "pending",
    "parent": "phase-2-files",
    "children": [],
    "metadata": {
      "file_path": "src/services/authService.ts",
      "task_category": "implementation",
      "estimated_hours": 4
    }
  }
}

// Refactoring task - improving code structure
{
  "task-3-1": {
    "type": "task",
    "title": "Extract validation logic to utility module",
    "status": "pending",
    "parent": "phase-3-files",
    "children": [],
    "metadata": {
      "file_path": "src/utils/validation.ts",
      "task_category": "refactoring",
      "estimated_hours": 3
    }
  }
}

// Decision task - architectural choice
{
  "task-1-2": {
    "type": "subtask",
    "title": "Choose between JWT vs session-based authentication",
    "status": "pending",
    "parent": "phase-1",
    "children": [],
    "metadata": {
      "task_category": "decision",
      "estimated_hours": 1
    }
  }
}

// Research task - external learning
{
  "task-1-3": {
    "type": "subtask",
    "title": "Review OAuth 2.0 best practices and security guidelines",
    "status": "pending",
    "parent": "phase-1",
    "children": [],
    "metadata": {
      "task_category": "research",
      "estimated_hours": 2
    }
  }
}
```

**Setting Default Category (CLI):**

When creating specs via the CLI, you can set a default category that will be stored in the spec metadata:

```bash
# Create spec with explicit default category
sdd create "User Authentication" --template medium --category investigation

# Create spec without default category
sdd create "User Authentication" --template medium
```

The `--category` flag is useful when most tasks in a spec will be the same type (e.g., an investigation-heavy spec or a refactoring-focused spec).

**Best Practices:**

**Choosing the Right Category:**
- Use **`investigation`** when you need to understand existing code, trace dependencies, or analyze current behavior before making changes
- Use **`implementation`** when creating new functionality, adding features, or writing new code files
- Use **`refactoring`** when improving code structure without changing external behavior (e.g., extracting functions, renaming variables)
- Use **`decision`** when you need to evaluate alternatives or make architectural choices (often early in phases)
- Use **`research`** when gathering external information, reading documentation, or learning about libraries/tools

**Task Ordering:**
- **Always use `investigation` before `implementation`**: Understanding code first prevents mistakes and reduces rework
- **Place `decision` and `research` tasks early in phases**: These inform later implementation work
- **Group `refactoring` separately from `implementation`**: Keep behavioral changes distinct from structural improvements
- **Combine `decision` with `research`**: Research tasks often provide the information needed for decision tasks

**Mixed-Type Phases:**
- Phases often contain multiple task categories (investigation → decision → implementation → verification)
- Start phases with investigation/research tasks to gather context
- Place decision tasks after investigation but before implementation
- End phases with verification tasks to validate the work
- Use dependencies to enforce proper ordering between different category types

**Other Guidelines:**
- **Always specify category for tasks**: Helps with accurate time estimation and resource planning
- **Optional for subtasks**: If a subtask's category is obvious from its parent, it can be omitted
- **Use file_path for implementation/refactoring**: These categories require specific files to modify
- **Skip file_path for investigation/decision/research**: These categories often span multiple files or are conceptual

### Phase 2: Spec Validation

After creating a JSON specification, validate it to ensure correct format and sdd-next compatibility.

**About Validation:**

The JSON spec file is validated for:
- Hierarchy integrity and consistency
- Task count accuracy
- Dependency graph validity
- Required field presence
- Proper node relationships

**Validation is JSON-only** - markdown files are optional generated artifacts, not validated.

**Validation tool:**

You have access to a tool for validation called `sdd-validate`.

**Recommended usage:**
- Call `sdd validate` while creating or refining specs
- Use `sdd report` for detailed issue breakdowns and guidance
- Preview fixes with `sdd fix --preview` before applying
- Integrate validation into CI/CD or pre-handoff checks before invoking sdd-next

#### 2.1 Using sdd-validate

The `sdd-validate` CLI is the single interface for spec validation and auto-fixes.

**Core Commands:**
- `validate` – Validate JSON spec structure (exit codes: 0 valid, 1 warnings, 2 errors)
- `report` – Generate Markdown/JSON reports with actionable guidance
- `fix` – Preview/apply auto-fixes for common hierarchy and metadata issues
- `stats` – Summarize hierarchy size, verification coverage, and complexity metrics

**Common Options:**
- `--json` – JSON output (available on most commands)
- `--quiet` / `-q` – Errors only
- `--verbose` / `-v` – Include extra context
- `--preview` / `--dry-run` – Show proposed fixes without writing (for `fix`)

##### validate (Recommended)

Validates the JSON spec file structure, hierarchy, and integrity.

**Usage:**
```bash
# Validate JSON spec file
sdd validate specs/active/your-spec.json

# JSON output for programmatic use
sdd validate specs/active/your-spec.json --json
```

##### report

Produces in-depth analysis, grouped by severity, with suggested remedies.

**Usage:**
```bash
# Print Markdown report
sdd report specs/active/your-spec.json

# Save to file
sdd report specs/active/your-spec.json --output specs/reports/your-spec.md
```

##### fix

Automatically fixes common JSON spec issues. Always preview first.

**Usage:**
```bash
# Preview fixes without applying
sdd fix specs/active/your-spec.json --preview

# Apply fixes once reviewed
sdd fix specs/active/your-spec.json
```

##### stats (Optional)

Summarizes hierarchy composition, depth, and verification footprint.

**Usage:**
```bash
sdd stats specs/active/your-spec.json
```

**Note:** JSON remains the source of truth. Markdown reports generated via `sdd-validate` are helpful for review, but edits must be made in the JSON and re-rendered.

### Phase 3: Rendering Specs to Human-Readable Markdown

After creating and validating your JSON spec, you can generate comprehensive human-readable markdown documentation using the `sdd render` command. This is useful for:
- Reviewing spec structure and progress
- Sharing plans with team members
- Creating documentation for project tracking
- Generating readable versions for non-technical stakeholders

#### 3.1 Using sdd render

The `sdd render` command converts JSON specifications into well-formatted markdown with full hierarchy visualization, progress tracking, and status indicators.

**Basic Usage:**

```bash
# Render by spec ID (searches specs directory)
sdd render semantic-search-2025-10-24-001 --path specs

# Render by direct file path
sdd render specs/active/my-spec.json

# Custom output location
sdd render my-spec --path specs -o documentation/my-spec.md
```

**Default Output Location:**

By default, rendered markdown is saved to:
```
.specs/human-readable/<status>/<spec-id>.md
```

Where `<status>` is the spec's status (active, approved, completed, etc.) from the metadata.

**Example:**
```bash
# Renders to: .specs/human-readable/approved/semantic-search-2025-10-24-001.md
sdd render semantic-search-2025-10-24-001 --path specs
```

#### 3.2 Generated Markdown Format

The rendered markdown includes:

**Header Section:**
- Spec ID and title
- Status and progress (completed/total tasks, percentage)
- Estimated effort and complexity
- Description and objectives

**Phase Sections:**
- Phase title with progress tracking
- Purpose, risk level, and estimated hours
- Dependencies (blocked by, blocks)
- File modifications grouped by type
- Detailed task breakdown with subtasks
- Verification steps with commands

**Status Icons:**
- ⏳ Pending tasks
- 🔄 In progress
- ✅ Completed
- 🚫 Blocked
- ❌ Failed

**Example Output Structure:**
```markdown
# Semantic Search for Documentation Query

**Spec ID:** `semantic-search-2025-10-24-001`
**Status:** approved (5/62 tasks, 8%)
**Estimated Effort:** 80 hours
**Complexity:** high

## Objectives
- Enable semantic search for natural language code queries
- Improve keyword search relevance with BM25
...

## Foundation & Configuration (2/8 tasks, 25%)

**Purpose:** Set up dependencies and configuration
**Risk Level:** low
**Estimated Hours:** 6

### File Modifications (2/6 tasks)

#### ⏳ src/claude_skills/pyproject.toml

**File:** `src/claude_skills/pyproject.toml`
**Status:** pending
**Changes:** Add optional dependency groups
...
```

#### 3.3 When to Render Specs

**Recommended Times:**
- After initial spec creation for team review
- Before starting implementation to confirm understanding
- At phase boundaries to track progress
- When presenting project status to stakeholders
- For archival documentation of completed work

**Integration with Workflow:**
```bash
# 1. Create spec (this skill)
# 2. Validate
sdd validate specs/active/my-spec.json

# 3. Render for review
sdd render my-spec --path specs

# 4. Share rendered markdown for team feedback
# 5. Update spec based on feedback
# 6. Re-render after updates
```

**Note:** The `.specs/` directory (with dot prefix) is meant for generated artifacts, similar to build directories. Consider adding it to `.gitignore` if you don't want rendered documentation in version control.

#### 2.2 Validation Checklist

**Before sdd-next Usage:**

Run validation to ensure the JSON spec file is properly formatted:

```bash
# Validate JSON spec file (recommended)
sdd validate specs/active/your-spec.json

# Check validation status
echo $?  # 0 = valid, 1 = warnings, 2 = errors

# Generate detailed report for review
sdd report specs/active/your-spec.json --output specs/reports/your-spec.md

# Quiet mode for CI/CD pipelines
sdd validate specs/active/your-spec.json --quiet
```

**Required for sdd-next:**
- ✅ All errors must be fixed (exit code 0 or 1)
- ✅ Hierarchy integrity maintained
- ✅ Task counts are accurate across hierarchy
- ✅ All required fields present
- ✅ Dependencies are valid

**If Validation Fails:**

| Error Type | Solution |
|------------|----------|
| Task count mismatch | Run `sdd fix --preview` or regenerate spec file manually |
| Hierarchy integrity issues | Use `sdd fix` or check parent/child references manually |
| Missing required fields | Add missing fields, then re-run validation |
| Invalid dependencies | Check dependency IDs match actual task IDs |
| Circular dependencies | Remove or adjust blocking relationships |

**Auto-Fix Workflow:**

If validation fails with fixable errors, use the auto-fix command:

```bash
# 1. Preview fixes (dry-run)
sdd fix specs/active/your-spec.json --preview

# 2. Apply fixes if preview looks good
sdd fix specs/active/your-spec.json

# 3. Re-validate to confirm all issues resolved
sdd validate specs/active/your-spec.json
```

## Best Practices

### Specification Quality
- **Be specific**: "Add error handling to API calls" not "improve error handling"
- **Include examples**: Show what the change looks like in context
- **Think ahead**: Consider maintenance, testing, and documentation needs
- **Stay grounded**: Base plans on actual codebase exploration, not assumptions

### Review Workflow (Integration with `Skill(sdd-toolkit:sdd-plan-review)`)

After creating and validating a spec, consider having it reviewed before implementation:

**Review Status Flow:**
```
not_reviewed (default) → in_review → reviewed → approved → implementation
                                        ↓
                                     revise (if needed)
```

**Status Meanings:**
- `not_reviewed`: Spec created but not yet reviewed
- `in_review`: Review in progress
- `reviewed`: Review complete, may have issues to address
- `approved`: Review issues addressed, ready for implementation

**Review Integration:**
1. **Create & Validate**: Use `Skill(sdd-toolkit:sdd-plan)` to create spec, validate with `validate-all`
2. **Review**: Use `Skill(sdd-toolkit:sdd-plan-review)` to get multi-perspective feedback
3. **Revise**: Address critical/high issues found in review
4. **Track**: Review metadata automatically added to spec frontmatter
5. **Link**: Revisions can reference the review that triggered them

**Example Workflow:**
```bash
# 1. Create spec
# (Use Skill(sdd-toolkit:sdd-plan) skill)

# 2. Validate JSON spec file
sdd validate specs/active/myspec.json

# 3. Review spec (sdd-plan-review runs validation automatically)
sdd-review review-spec specs/active/myspec.json --type full --auto-fix

# 4. Address review findings, update spec metadata
#    - Update revisions[] with context
#    - Track review history in metadata.review.history[]

# 5. Re-run validation before handoff
sdd validate specs/active/myspec.json --json

# 6. Begin implementation with Skill(sdd-toolkit:sdd-next)
```

**Review Metadata Structure:**

The `review` section tracks all reviews:
- `status`: Current review status
- `last_reviewed`: Most recent review timestamp
- `reviewers`: List of models/tools that have reviewed
- `total_reviews`: Count of reviews performed
- `history`: Array of all review records with:
  - Unique `review_id`
  - Tools used and perspectives applied
  - Issues found (by severity)
  - Overall recommendation and scores
  - Link to detailed report file
  - Optional link to resulting revision

**Benefits:**
- **Audit trail**: Complete history of reviews and feedback
- **Quality gate**: Catch issues before implementation starts
- **Bi-directional links**: Review → Revision and Revision → Review
- **Multi-round support**: Track re-reviews naturally
- **Shared validation**: Review uses same validation as sdd-plan

### Phase Design
- **Logical units**: Each phase should be independently testable
- **Clear boundaries**: Minimize overlap between phases
- **Dependency management**: Later phases build on earlier ones
- **Reasonable scope**: Each phase should be completable in one sitting

### Task Decomposition

**Atomic Task Principle**: Each task should modify exactly one file. When a feature requires changes across multiple files:

1. **Create multiple tasks** (one per file) with explicit dependencies, OR
2. **Use subtasks** under a parent task (parent coordinates, each subtask has its own `file_path`)

**Example**:
```
Feature: Add User Authentication
├─ Task 1: Create auth middleware (middleware/auth.js)
├─ Task 2: Update user model (models/user.js)  [depends on task-1]
└─ Task 3: Add auth routes (routes/auth.js)    [depends on task-1, task-2]
```

See [docs/BEST_PRACTICES.md](../../docs/BEST_PRACTICES.md) for detailed guidance on task granularity, special cases, and identifying atomic units.

### Verification Rigor
- **Automated where possible**: Prefer tests over manual checks
- **Comprehensive coverage**: Test happy path AND edge cases
- **Regression focus**: Existing functionality is sacred
- **User validation**: When possible, confirm with actual usage

### Communication
- **Transparent**: Share the spec before implementing
- **Collaborative**: Invite feedback and refinement
- **Traceable**: Document deviations and decisions
- **Educational**: Explain reasoning, don't just state conclusions

## Working with the Skill Family

**After Creating a Spec:**

1. **Review with user** - Ensure spec meets expectations
2. **Approve spec** - Update frontmatter status from "draft" to "approved"
3. **Hand off to Skill(sdd-toolkit:sdd-next)** - Now ready for task identification
4. **Skill(sdd-toolkit:sdd-next)** identifies first actionable task
5. **Skill(sdd-toolkit:sdd-next)** creates execution plan for that task
6. **Implementation happens** (human/AI executes the plan)
7. **Skill(sdd-toolkit:sdd-update)** updates progress and status
8. **Repeat** steps 4-7 until spec complete

**If Spec Needs Changes:**
- Use Skill(sdd-toolkit:sdd-update) to document the change decision
- Use this skill to regenerate portions if major restructuring needed
- Update spec version in frontmatter if significant

## Common Pitfalls to Avoid

❌ **Skipping codebase analysis**: Don't guess at file locations or patterns
❌ **Vague specifications**: "Improve performance" is not actionable
❌ **Premature optimization**: Don't add features not in the spec
❌ **Verification shortcuts**: Every step matters, don't skip any
❌ **Spec drift**: Keep spec updated if requirements change
❌ **Over-engineering**: Match complexity to actual requirements

## Decision Tree: Which Skill to Use?

```
Need to plan a new feature or change?
├─ Yes → Use `Skill(sdd-toolkit:sdd-plan)` (this skill)
└─ No → Continue below

Have an existing spec and ready to implement?
├─ Yes, but don't know what to work on next
│   └─ Use `Skill(sdd-toolkit:sdd-next)`
└─ Yes, and need to update status/progress
    └─ Use `Skill(sdd-toolkit:sdd-update)`

Spec already exists and needs modification?
├─ Minor updates (status, metadata, journal)
│   └─ Use `Skill(sdd-toolkit:sdd-update)`
└─ Major restructuring (new phases, tasks)
    └─ Use `Skill(sdd-toolkit:sdd-plan)` to generate new plan
```

## Quick Reference

**Short task (<5 files, simple changes)**
- **Phases**: 1-2 phases maximum
- **Hierarchy depth**: 2-3 levels (spec → phase → task, minimal subtasks)
- **Task count**: 3-8 tasks total
- **Verification**: 1-2 verifications per phase (minimum 20% coverage)
- **Spec structure**: Brief objectives, files, key changes, basic verification
- **Focus**: Verification to prevent breaks, keep hierarchy flat

**Medium task (5-15 files, moderate complexity)**
- **Phases**: 2-4 phases with clear dependencies
- **Hierarchy depth**: 3-4 levels (spec → phase → group → task → subtask)
- **Task count**: 10-25 tasks with selective subtask breakdown
- **Verification**: 2-4 verifications per phase (aim for 30-40% coverage)
- **Spec structure**: Full specification with detailed file-level planning
- **Focus**: Risk assessment, comprehensive verification steps, dependency tracking

**Large task (>15 files or high complexity)**
- **Phases**: 4-6 phases (if more, split into multiple specs)
- **Hierarchy depth**: 4-5 levels maximum (deeper = harder to manage)
- **Task count**: 25-50 tasks (>50 suggests splitting into multiple specs)
- **Verification**: 3-5 verifications per phase (target 40-50% coverage)
- **Spec structure**: Detailed multi-phase with extensive verification and rollback planning
- **Focus**: Consider splitting if >6 phases or >50 tasks; higher user involvement in refinement

**Rule of thumb**: If hierarchy exceeds 5 levels or a single phase has >15 tasks, reorganize or split the spec.

## See Also

**sdd-next** - Use after creating a spec to:
- Find the next task to work on
- Create detailed execution plans for specific tasks
- Understand task context and dependencies
- Resume work on a partially-completed spec

**sdd-update** - Use during/after implementation to:
- Mark tasks as in_progress, completed, or blocked
- Document implementation decisions and deviations
- Track progress and update metrics
- Move completed specs to appropriate folders
- Journal verification results

---

**Remember**: The time spent on specification pays exponential dividends in implementation quality and developer confidence. Never skip the planning phase. Once the spec is created, transition to the `Skill(sdd-toolkit:sdd-next)` to begin identifying and planning specific tasks for implementation.