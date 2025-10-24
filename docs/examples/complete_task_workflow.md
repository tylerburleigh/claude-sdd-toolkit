# SDD Toolkit Example: Complete Task Workflow

## Overview

This example walks through using the `claude-sdd-toolkit` to complete a task from a spec. In this toolkit, a spec is a machine-readable JSON document that defines tasks, their dependencies, and tracks implementation progress. 

The toolkit itself consists of Claude skills (like `sdd-next` and `sdd-update`) that provide interactive workflows, plus a Python package with CLI tools that handle spec operations. The skills invoke CLI commands to read, update, and track progress in specs. 

This toolkit was built to create a streamlined workflow that puts Claude on guardrails - keeping it focused on one task at a time while giving it tools that allow it to efficiently create, read, and update spec files.

The Spec-Driven Development process works by defining all planned work upfront in a spec, then executing tasks systematically one at a time. Each task goes through preparation (gathering context and creating a plan), approval (user reviews and confirms), implementation (making changes with verification), and documentation (journaling what was done). This approach keeps development on track by making progress visible, preventing scope drift, and maintaining a record of decisions.

Here's what happens:

1. **User runs** `/sdd-start` to begin a session
2. **Claude checks** the environment setup and finds active specs with pending tasks
3. **User selects** "Continue with next task"
4. **Claude prepares** a detailed plan using the `sdd-next` skill - identifies the task, gathers context, shows what needs to be done
5. **User approves** the plan
6. **Claude implements** the changes, verifies them, and marks the task as completed
7. **User asks** Claude to journal the work
8. **Claude adds** a journal entry documenting what was done and why

---

## The Workflow

I begin a session by running the `/sdd-start` slash command.

This initiates the start procedure, which leads Claude to:

1. Check if my environment is configured for the toolkit
2. Discover active spec docs, and check if they have pending tasks
3. Asks me if I want to continue with the next task

```
> /sdd-start is running… 

⏺ I'll help you check for active SDD work and get you started. Let me first verify the
   project permissions.

⏺ Bash(sdd skills-dev start-helper check-permissions)
  ⎿ ✅ Success: SDD permissions are configured                                        
    Identity added: /Users/tylerburleigh/.ssh/id_ecdsa (tylerburleigh@Khans-MacBook-P
    ro.local)


⏺ Great! Permissions are already configured. Now let me discover any active work:

⏺ Bash(sdd skills-dev start-helper format-output)
  ⎿  📋 Found 1 active specification:             

     1. 📝 Semantic Search for Documentation Query
     … +4 lines (ctrl+o to expand)

⏺ Perfect! I found active work. Let me check for any last-accessed task information:

⏺ Bash(sdd skills-dev start-helper get-session-info)
  ⎿  {                             
       "has_specs": true,
       "last_task": null,
     … +13 lines (ctrl+o to expand)

⏺ 📋 Found 1 active specification:

  Semantic Search for Documentation Query
  - ID: semantic-search-2025-10-24-001
  - Progress: 0/62 tasks (0%)
  - Status: Ready to start

---

What would you like to do?
❯ 1. Continue with next task
     Start working on the semantic search specification
  2. Write new spec
     Create a new specification with sdd-plan
  3. Something else
     Exit and work on something different
  4. Type something.
```

I choose to "Continue with the next task". This leads Claude to invoke the `sdd-next` skill, which contains a workflow for gathering context about the next task.

We can see below that it uses CLI tools like `sdd prepare-task`, `sdd task-info`, `sdd progress`, and `sdd query-tasks` which are part of the underlying CLI that the skill uses to systematically discover the next task, gather complete context about it (including subtasks and dependencies), check overall progress, and format a detailed execution plan for the user to review before implementation.


```                                      
⏺ User answered Claude's questions:
  ⎿
     · What would you like to do? → Continue with next task

⏺ Perfect! I'll use the sdd-next skill to find and prepare the next task from the
  semantic search specification:

> The "sdd-next" skill is loading 

> The "sdd-next" skill is loading 

⏺ I'll help you find and prepare the next task from the semantic search specification.
   Let me start by verifying the tools are available.

⏺ Bash(sdd verify-tools)
  ⎿  🔵 Action: Checking required tools...
     ✅ Success: Python 3 is available
     ✅ Success: git is available
     … +5 lines (ctrl+o to expand)

⏺ Great! Tools are verified. Now let me prepare the next task from the semantic search
   specification:

⏺ Bash(sdd prepare-task semantic-search-2025-10-24-001 --json)
  ⎿  {                             
       "success": true,
       "task_id": "task-1-1",
     … +39 lines (ctrl+o to expand)

⏺ Perfect! I've identified the next task. Let me gather more context about this task
  and format a complete execution plan:

⏺ Bash(sdd task-info semantic-search-2025-10-24-001 task-1-1 --json)
  ⎿  {                                             
       "type": "task",
       "title": "src/claude_skills/pyproject.toml",
     … +23 lines (ctrl+o to expand)

⏺ Bash(sdd progress semantic-search-2025-10-24-001 --json)
  ⎿  {                                             
       "node_id": "spec-root",
       "spec_id": "semantic-search-2025-10-24-001",
     … +16 lines (ctrl+o to expand)

⏺ Read(src/claude_skills/pyproject.toml)
  ⎿  Read 52 lines

⏺ Excellent! Now let me check the subtask details to understand what specific changes
  need to be made:

⏺ Bash(sdd task-info semantic-search-2025-10-24-001 task-1-1-1 --json)
  ⎿  {                                                     
       "type": "subtask",
       "title": "Add [semantic] optional dependency group",
     … +17 lines (ctrl+o to expand)

⏺ Bash(sdd task-info semantic-search-2025-10-24-001 task-1-1-2 --json)
  ⎿  {                                                         
       "type": "subtask",
       "title": "Add [semantic-cpu] optional dependency group",
     … +16 lines (ctrl+o to expand)

⏺ Perfect! Now let me check for any verification requirements and create the execution
   plan:

⏺ Bash(sdd query-tasks semantic-search-2025-10-24-001 --type verify --parent phase-1
      --json)
  ⎿ Identity added: /Users/tylerburleigh/.ssh/id_ecdsa (tylerburleigh@Khans-MacBook-P
    ro.local)


⏺ Bash(sdd format-plan semantic-search-2025-10-24-001 task-1-1)
  ⎿  # Execution Plan Ready: task-1-1

     ## 📋 Task Summary
     … +33 lines (ctrl+o to expand)

⏺ Execution Plan Ready: task-1-1

  📋 Task Summary

  File: src/claude_skills/pyproject.toml
  Purpose: Add optional dependency groups for semantic search
  Phase: Phase 1 - Foundation & Configuration (0/8 tasks, 0%)
  Estimated Time: 0.5 hours

  ✅ Readiness Check

  - ✅ Ready to begin: no blocking dependencies
  - ✅ File exists and is accessible
  - ✅ All required tools verified

  🎯 Implementation Details

  What needs to be added:

  Based on the subtask analysis, I need to add two new optional dependency groups to
  the existing [project.optional-dependencies] section:

  1. [semantic] - For semantic search functionality with BM25 and embeddings:
    - rank-bm25>=0.2.2
    - sentence-transformers>=2.2.0
    - numpy>=1.21.0
  2. [semantic-cpu] - Same as semantic but with CPU-only PyTorch for non-Mac platforms

  Current state: The file currently has only a test optional dependency group (lines
  21-25)

  Changes required:
  - Add semantic dependency group after the test group
  - Add semantic-cpu dependency group for CPU-only environments
  - Maintain existing formatting and structure

  Reasoning: This enables progressive enhancement - users can opt-in to BM25 and/or
  semantic features without requiring these heavier dependencies for basic
  functionality.

  📝 Implementation Steps

  Step 1: Add [semantic] dependency group

  Action: Add semantic search dependencies to pyproject.toml
  Details:
  - Insert after existing test group
  - Include: rank-bm25, sentence-transformers, numpy
  - Follow existing formatting style

  Step 2: Add [semantic-cpu] dependency group

  Action: Add CPU-only variant for semantic dependencies
  Details:
  - Same packages as semantic group
  - Add torch CPU-specific configuration
  - Document use case (non-Mac platforms)

  ✓ Success Criteria

  Task complete when:
  - ✅ Two new optional dependency groups added: semantic and semantic-cpu
  - ✅ All specified packages included with correct version constraints
  - ✅ TOML syntax is valid (no parsing errors)
  - ✅ Existing dependencies remain unchanged
  - ✅ File formatting matches existing style

  📦 Next Tasks After This

  Completing this task will enable work on:
  - Subsequent configuration tasks in Phase 1
  - Implementation of semantic search functionality in later phases

  ---
  Ready to Proceed?

  Options:
  1. ✅ Approve plan and begin implementation - I'll add the dependency groups to
  pyproject.toml
  2. 📝 Request changes to plan - Modify the approach or dependencies
  3. 🔍 See more details - Questions about specific packages or approach
  4. ⏸️ Defer to later - Work on something else

  Which would you like to do?
```

At this point I choose option 1. This leads Claude to begin implementation.

First it sets the task to "in progress" status using the `sdd update-status` CLI tool. This updates the spec's state file to track that work has begun on task-1-1. Then it proceeds with the actual implementation by editing the pyproject.toml file.

```
> 1 

⏺ Perfect! I'll proceed with implementing the changes to pyproject.toml. Let me track
  this work and begin implementation.

⏺ Bash(sdd update-status semantic-search-2025-10-24-001 task-1-1 in_progress --note
      "Starting implementation of optional dependency groups for semantic search")
  ⎿  🔵 Action: Updating status for task-1-1...                    
     🔵 Action: Loading state for semantic-search-2025-10-24-001...
     🔵 Action: Recalculating progress...
     … +4 lines (ctrl+o to expand)

⏺ Now I'll add the semantic search dependency groups to pyproject.toml:
```

Claude follows a systematic workflow to complete the task:

1. **Implementation**: Edits `src/claude_skills/pyproject.toml` to add the two new optional dependency groups (`semantic` and `semantic-cpu`) with their required packages.

2. **Verification**: Runs a Python command to validate the TOML syntax and confirm all three optional dependency groups are present (test, semantic, semantic-cpu).

3. **Update Status**: Uses `sdd update-status` to mark task-1-1 as `completed` in the spec's state file, with a note describing what was accomplished.

4. **Report Progress**: Uses `sdd progress` to calculate and display the updated progress statistics, showing that 2 out of 62 tasks are now complete (3% overall progress) and that Phase 1 is 25% complete (2/8 tasks).

This workflow ensures that every task completion is tracked in the spec, verified for correctness, and reflected in the overall project progress.

```
⏺ Update(src/claude_skills/pyproject.toml)
  ⎿  Updated src/claude_skills/pyproject.toml with 11 additions                 
       23        "pytest>=7.4.0",
       24        "pytest-mock>=3.12.0",
       25    ]
       26 +  semantic = [
       27 +      "rank-bm25>=0.2.2",
       28 +      "sentence-transformers>=2.2.0",
       29 +      "numpy>=1.21.0",
       30 +  ]
       31 +  semantic-cpu = [
       32 +      "rank-bm25>=0.2.2",
       33 +      "sentence-transformers>=2.2.0",
       34 +      "numpy>=1.21.0",
       35 +      "torch>=2.0.0; platform_system != 'Darwin'",
       36 +  ]
       37    
       38    [project.scripts]
       39    # Unified SDD CLI - Single entry point for all SDD, doc, test, and 
            skills-dev commands

⏺ Excellent! Both dependency groups have been added. Let me update my progress and
  verify the TOML syntax:

⏺ Bash(python3 -c "import tomllib; f = open('src/claude_skills/pyproject.toml', 'rb');
      data = tomllib.load(f); print('✅ TOML syntax is valid'); print(f'Found {len(data…)
  ⎿  ✅ TOML syntax is valid             
     Found 3 optional dependency groups:
       - test
     … +4 lines (ctrl+o to expand)

⏺ Perfect! The TOML syntax is valid and all dependency groups are present. Now let me
  mark the task as completed:

⏺ Bash(sdd update-status semantic-search-2025-10-24-001 task-1-1 completed --note
      "Successfully added semantic and semantic-cpu optional dependency groups to
      pyproject…)
  ⎿  🔵 Action: Updating status for task-1-1...                    
     🔵 Action: Loading state for semantic-search-2025-10-24-001...
     🔵 Action: Recalculating progress...
     … +4 lines (ctrl+o to expand)

⏺ Bash(sdd progress semantic-search-2025-10-24-001)
  ⎿  🔵 Action: Calculating progress...                                            
     ✅ Success: Progress calculated
     Spec: Semantic Search for Documentation Query (semantic-search-2025-10-24-001)
     … +4 lines (ctrl+o to expand)

⏺ ✅ Task Complete!

  Task task-1-1 has been successfully implemented and marked as completed.

  What was accomplished:

  ✅ Added [semantic] optional dependency group with:
  - rank-bm25>=0.2.2
  - sentence-transformers>=2.2.0
  - numpy>=1.21.0

  ✅ Added [semantic-cpu] optional dependency group with:
  - Same packages as semantic
  - torch>=2.0.0 (for non-Darwin platforms only)

  ✅ Verified TOML syntax is valid
  ✅ All three optional dependency groups confirmed (test, semantic, semantic-cpu)

  Progress Update:

  - Spec Progress: 2/62 tasks completed (3%)
  - Current Phase: Foundation & Configuration - 2/8 tasks completed (25%)

  Next Steps:

  Would you like to:
  1. Continue with the next task - I can prepare the next task in the specification
  2. Review the changes - Take a look at the updated pyproject.toml
  3. Install the new dependencies - Test that the new optional groups work correctly
  4. Something else - Different action

  What would you like to do?
```

At the end of this procedure, the JSON spec file contains the following information about this task:

```
  {
    "type": "task",
    "title": "src/claude_skills/pyproject.toml",
    "status": "completed",
    "parent": "phase-1-files",
    "children": [
      "task-1-1-1",
      "task-1-1-2"
    ],
    "dependencies": {
      "blocks": [],
      "blocked_by": [],
      "depends": []
    },
    "total_tasks": 2,
    "completed_tasks": 2,
    "metadata": {
      "completed_at": "2025-10-24T16:48:23.512925+00:00",
      "needs_journaling": true,
      "status_note": "Successfully added semantic and semantic-cpu optional dependency
   groups to pyproject.toml. TOML syntax validated."
    }
  }
```

Notice the `"needs_journaling": true`. Although the task was marked as complete, the journaling process has not yet been run. We can do this by asking Claude to invoke the `sdd-update` skill.

```
> Let's run sdd-update to complete the journaling process 

⏺ Perfect! Let me invoke the sdd-update skill to complete the journaling process
  properly:

> The "sdd-update" skill is loading 

> The "sdd-update" skill is loading 

⏺ Perfect! Now that the sdd-update skill is loaded, let me add a proper journal entry
  to document the implementation of task-1-1:

⏺ Bash(sdd add-journal semantic-search-2025-10-24-001 --title "Added semantic search
      dependency groups" --content "Successfully added two new optional dependency group…)
  ⎿  🔵 Action: Adding journal entry...                
         Type: decision
         Title: Added semantic search dependency groups
     … +6 lines (ctrl+o to expand)

⏺ Excellent! Journal entry added successfully. Let me check the current status and
  verify the journaling is complete:

⏺ Bash(sdd check-journaling semantic-search-2025-10-24-001)
  ⎿ 🔵 Action: Checking for unjournaled tasks in semantic-search-2025-10-24-001...   
    ✅ Success: All completed tasks have been journaled!
    Identity added: /Users/tylerburleigh/.ssh/id_ecdsa (tylerburleigh@Khans-MacBook-P
    ro.local)


⏺ Bash(sdd status-report semantic-search-2025-10-24-001)
  ⎿  🔵 Action: Generating status report for semantic-search-2025-10-24-001...

     ════════════════════════════════════════════════════════════
     … +16 lines (ctrl+o to expand)

⏺ ✅ Journaling Complete!

  Summary of Documentation Updates:

  Journal Entry Added:
  - Type: Decision
  - Title: "Added semantic search dependency groups"
  - Task: task-1-1
  - Content: Documented the addition of [semantic] and [semantic-cpu] optional
  dependency groups with full details of the implementation and rationale

  Verification Status:
  ✅ All completed tasks have been journaled
  ✅ No unjournaled tasks remaining

  Current Spec Status:

  ════════════════════════════════════════════════════════════
     Status Report: Semantic Search for Documentation Query
  ════════════════════════════════════════════════════════════

  Overall Progress: 2/62 tasks (3%)
  Status: in_progress

  Task Breakdown:
    ✓ Completed: 1 task
    ○ Pending: 13 tasks
    ◐ In Progress: 0 tasks
    ✗ Blocked: 0 tasks

  Phase Progress:
    → Foundation & Configuration: 2/8 (25%)
    ○ BM25 Search Implementation: 0/11 (0%)
    ○ Semantic Embeddings Infrastructure: 0/19 (0%)
    ○ Hybrid Search Orchestration: 0/18 (0%)
    ○ Testing, Documentation & Polish: 0/6 (0%)
```

After this procedure is run, it adds an entry to the "journal" key in the spec JSON file, which looks like this:

```
  "journal": [
    {
      "timestamp": "2025-10-24T17:02:51.947793+00:00",
      "entry_type": "decision",
      "title": "Added semantic search dependency groups",
      "author": "claude-code",
      "content": "Successfully added two new optional dependency groups to pyproject.toml: [semantic] and [semantic-cpu]. The semantic group includes rank-bm25>=0.2.2, sentence-transformers>=2.2.0, and numpy>=1.21.0. The semantic-cpu group includes the same packages plus torch>=2.0.0 for non-Darwin platforms. This enables progressive enhancement where users can opt-in to BM25 and semantic search features without requiring these heavier dependencies for basic functionality. TOML syntax validated successfully.",
      "metadata": {},
      "task_id": "task-1-1"
    }
  ]
```