# SDD Toolkit Best Practices

This document provides best practices, patterns, and guidelines for effective use of the SDD (Spec-Driven Development) Toolkit.

## Table of Contents

- [Before You Start](#before-you-start)
- [Your Role vs. Claude's Role](#your-role-vs-claudes-role)
- [Understanding Task Structure](#understanding-task-structure)
- [Guiding Claude to Create Better Specs](#guiding-claude-to-create-better-specs)
- [Phase Organization](#phase-organization)
- [How Task Dependencies Work](#how-task-dependencies-work)
- [Progress Tracking](#progress-tracking)
- [Working with Long Sessions](#working-with-long-sessions)

---

## Before You Start

### Generate Code Documentation First

**Recommended**: Before asking Claude to create specs, ask it to document your codebase:

> "Document this codebase"

When documentation is available, Claude can provide better quality specs and task context by understanding your existing code patterns, relationships, and architecture. Without documentation, Claude will still work but uses slower file exploration methods.

### Understanding the Spec Workflow

Specs follow a lifecycle through folders:

1. **Create** → Spec lands in `specs/pending/`
2. **Activate** → Move to `specs/active/` when ready to start work
3. **Implement** → Complete tasks one by one
4. **Complete** → Move to `specs/completed/` when all tasks done

Use `/sdd-begin` to navigate this workflow. Claude will show you pending specs and offer to activate them, or continue with active specs.

**Why pending folder?** Allows you to plan multiple features without cluttering your active workspace. You can have a backlog of planned work while focusing on current implementation.

---

## Your Role vs. Claude's Role

### What You Provide

- **Feature requirements and goals** - Tell Claude what you want to build
- **Answers to questions** - Claude will ask clarifying questions during spec creation
- **Implementation** - You write the actual code for each task
- **Feedback** - Tell Claude when specs don't match your needs or expectations

### What Claude Handles

- **Creating spec structure** - Generates the JSON spec with all metadata
- **Breaking down features** - Decomposes your feature into atomic tasks
- **Identifying dependencies** - Determines which tasks depend on others
- **Managing status** - Updates task status as you work (pending → in_progress → completed)
- **Time tracking** - Records timestamps automatically
- **Journaling** - Documents completed work and decisions

### What The Toolkit Enforces

- **One file per task** - Tasks are atomic by design
- **Dependency validation** - Prevents circular dependencies
- **Status transitions** - Ensures valid status changes
- **Automatic timestamps** - Time tracking happens automatically
- **Spec lifecycle** - Manages the pending → active → completed workflow

You work *with* Claude and the toolkit. You don't write specs manually - you describe what you want and review what Claude creates.

---

## Understanding Task Structure

### The Atomic Task Principle

**What it means**: The toolkit enforces that each task modifies exactly ONE file.

**Why this matters**: Atomic tasks enable:
- **Precise dependency tracking**: File-level dependencies are explicit and clear
- **Granular progress monitoring**: Each completed task represents concrete, verifiable progress
- **Parallel implementation**: Independent tasks can be worked on simultaneously
- **Straightforward verification**: Each task has a focused scope and clear success criteria
- **Easy rollback**: Changes can be reverted at the file level without affecting other work

### How Claude Handles Multi-File Features

When you describe a feature that spans multiple files, Claude uses two approaches:

#### Approach 1: Multiple Independent Tasks (Most Common)

Claude creates separate tasks for each file, with explicit dependencies between them.

**Example of what Claude will create:**
```json
{
  "task-1-1": {
    "title": "Create authentication middleware",
    "metadata": {
      "file_path": "middleware/auth.js",
      "task_category": "implementation"
    }
  },
  "task-1-2": {
    "title": "Update user model with auth fields",
    "metadata": {
      "file_path": "models/user.js",
      "task_category": "implementation",
      "dependencies": ["task-1-1"]
    }
  },
  "task-1-3": {
    "title": "Add authentication routes",
    "metadata": {
      "file_path": "routes/auth.js",
      "task_category": "implementation",
      "dependencies": ["task-1-1", "task-1-2"]
    }
  },
  "task-1-4": {
    "title": "Update configuration with auth settings",
    "metadata": {
      "file_path": "config/settings.js",
      "task_category": "implementation",
      "dependencies": ["task-1-1"]
    }
  }
}
```

**When Claude uses this**: Most scenarios, especially when files have clear dependency relationships.

#### Approach 2: Subtasks Under a Parent Task

Claude creates a parent task to coordinate, with child subtasks for each file.

**Example of what Claude will create:**
```json
{
  "task-1": {
    "title": "Implement user authentication system",
    "children": ["task-1-1", "task-1-2", "task-1-3"],
    "metadata": {
      "task_category": "investigation"
    }
  },
  "task-1-1": {
    "title": "Create authentication middleware",
    "metadata": {
      "file_path": "middleware/auth.js",
      "task_category": "implementation"
    }
  },
  "task-1-2": {
    "title": "Update user model",
    "metadata": {
      "file_path": "models/user.js",
      "task_category": "implementation"
    }
  },
  "task-1-3": {
    "title": "Add authentication routes",
    "metadata": {
      "file_path": "routes/auth.js",
      "task_category": "implementation"
    }
  }
}
```

**When Claude uses this**: When files are tightly coupled and logically form a single feature unit.

### What Good Task Breakdown Looks Like

**One clear file, one focused change:**
- "Create authentication middleware in middleware/auth.js"
- "Add user validation to models/user.js"
- "Update API routes in routes/api.js"
- "Add error handling to services/payment.js"
- "Create rate limiter utility in utils/rateLimit.js"

### Special Cases

#### Test Files

**Pattern 1: Separate Task**
```json
{
  "task-1-1": {
    "title": "Implement authentication service",
    "metadata": {"file_path": "src/services/auth.js"}
  },
  "task-1-2": {
    "title": "Add tests for authentication service",
    "metadata": {"file_path": "tests/services/auth.test.js"}
  }
}
```

**Pattern 2: Subtask**
```json
{
  "task-1-1": {
    "title": "Implement authentication service",
    "children": ["task-1-1-1"],
    "metadata": {"file_path": "src/services/auth.js"}
  },
  "task-1-1-1": {
    "title": "Add tests for authentication service",
    "metadata": {"file_path": "tests/services/auth.test.js"}
  }
}
```

**When to use each**: Use separate tasks when tests can be written independently. Use subtasks when tests are tightly coupled to the implementation.

#### Documentation Files

Treat documentation as first-class tasks:

```json
{
  "task-1-5": {
    "title": "Document authentication API",
    "metadata": {
      "file_path": "docs/api/authentication.md",
      "task_category": "implementation"
    }
  }
}
```

**Best practice**: Create documentation tasks alongside implementation tasks, not as an afterthought.

#### Configuration Changes

**One task per configuration file:**

```json
{
  "task-2-1": {
    "title": "Add authentication dependencies",
    "metadata": {"file_path": "package.json"}
  },
  "task-2-2": {
    "title": "Add authentication environment variables",
    "metadata": {"file_path": ".env.example"}
  },
  "task-2-3": {
    "title": "Configure authentication middleware",
    "metadata": {"file_path": "config/middleware.js"}
  }
}
```

#### Investigation and Research Tasks

Use placeholder `file_path` values for tasks that don't modify specific files:

```json
{
  "task-1-1": {
    "title": "Research authentication libraries",
    "metadata": {
      "file_path": "research",
      "task_category": "research"
    }
  },
  "task-1-2": {
    "title": "Investigate current authentication flow",
    "metadata": {
      "file_path": "investigation",
      "task_category": "investigation"
    }
  },
  "task-1-3": {
    "title": "Decide on authentication strategy",
    "metadata": {
      "file_path": "decision",
      "task_category": "decision"
    }
  }
}
```

**Allowed placeholder values**: `"investigation"`, `"research"`, `"decision"`

#### Refactoring Across Multiple Files

**Anti-pattern**: One task to "refactor module X" that touches 10 files

**Better pattern**: One task per file being refactored

```json
{
  "phase-refactoring": {
    "title": "Refactor user module to use new patterns",
    "children": ["task-3-1", "task-3-2", "task-3-3"]
  },
  "task-3-1": {
    "title": "Refactor user model",
    "metadata": {
      "file_path": "models/user.js",
      "task_category": "refactoring"
    }
  },
  "task-3-2": {
    "title": "Refactor user service",
    "metadata": {
      "file_path": "services/userService.js",
      "task_category": "refactoring"
    }
  },
  "task-3-3": {
    "title": "Refactor user controller",
    "metadata": {
      "file_path": "controllers/userController.js",
      "task_category": "refactoring"
    }
  }
}
```

### Task Decomposition Decision Tree

```
Does this task modify code/config/docs?
├─ NO → Use placeholder file_path ("investigation", "research", "decision")
└─ YES → How many files need changes?
    ├─ ONE file → Single task with that file_path ✓
    └─ MULTIPLE files → Are they tightly coupled?
        ├─ YES → Parent task + subtasks (one per file)
        └─ NO → Separate tasks with dependencies (one per file)
```

---

## Guiding Claude to Create Better Specs

### Be Specific in Your Requests

When asking Claude to create a spec, provide specific requirements rather than vague goals.

**❌ Vague requests:**
- "Improve error handling"
- "Add better logging"
- "Optimize performance"

**✅ Specific requests:**
- "Add try-catch blocks to all API calls in services/api.js with structured error responses"
- "Add debug logging to authentication middleware with request ID tracking"
- "Implement response caching in API routes to reduce database queries by 50%"

The more specific you are, the better Claude can create tasks that match your needs.

### Provide Context and Examples

**Help Claude understand** by including:
- What needs to change and why
- What success looks like
- Example input/output if applicable
- Any constraints or requirements

**Example of a good request:**

> "Create a spec for adding rate limiting to API endpoints. Use a sliding window algorithm with Redis backend. Limit should be 100 requests per minute per IP address. When limit is exceeded, return 429 status with Retry-After header."

Claude will create detailed tasks based on this.

### Mention Important Considerations

**Tell Claude about:**
- **Testing requirements**: "Make sure to include test tasks"
- **Monitoring needs**: "We need to log rate limit violations"
- **Documentation**: "Include a task to document the API changes"
- **Dependencies**: "This needs the Redis connection to be set up first"
- **Rollback concerns**: "Make this feature toggleable via config"

Claude will incorporate these into the spec.

### Let Claude Explore First

**Best practice**: Let Claude explore your codebase before creating specs.

When you have documentation generated (see "Before You Start"), Claude can:
- Verify APIs and libraries exist
- Check existing patterns and conventions
- Identify real integration points
- Understand your architecture

If you ask for something that doesn't match your codebase, Claude will ask clarifying questions or suggest alternatives.

---

## Phase Organization

### Logical Units

Each phase should:
- Have a clear, single purpose
- Be independently testable
- Produce a working state when complete
- Build on previous phases

**Example of well-organized phases:**
```
Phase 1: Foundation
  - Set up database schema
  - Create base models
  - Add validation utilities

Phase 2: Core Features
  - Implement business logic
  - Add service layer
  - Create API endpoints

Phase 3: Integration
  - Add authentication
  - Implement authorization
  - Add audit logging

Phase 4: Polish
  - Add error handling
  - Improve performance
  - Update documentation
```

### Clear Boundaries

Minimize overlap between phases. Each phase should have minimal coupling to reduce complexity.

**Anti-pattern:**
```
Phase 1: Add features A, B, and start C
Phase 2: Finish C, add D, and start E
```

**Better:**
```
Phase 1: Add feature A
Phase 2: Add feature B
Phase 3: Add feature C
Phase 4: Add features D and E (if related)
```

### Reasonable Scope

**Rule of thumb**: Each phase should be completable in one focused work session (2-4 hours for most developers).

**Too large**: Phase with 20 tasks spanning multiple subsystems
**Too small**: Phase with 1 trivial task
**Just right**: Phase with 3-7 related tasks forming a coherent unit

---

## How Task Dependencies Work

### Claude Identifies Dependencies

When Claude creates a spec, it identifies which tasks depend on others and adds them to the task metadata automatically.

**Example of what you'll see:**

```json
{
  "task-2-1": {
    "title": "Implement user service",
    "metadata": {
      "file_path": "services/userService.js",
      "dependencies": ["task-1-1", "task-1-2"]
    }
  }
}
```

This means task-2-1 can't start until task-1-1 and task-1-2 are completed.

### Common Dependency Patterns

You'll see Claude use these patterns:

#### Linear Dependencies
```
task-1 → task-2 → task-3 → task-4
```
Each task depends on the previous one.

#### Fan-Out Pattern
```
      task-1
     /  |  \
task-2 task-3 task-4
```
Multiple tasks depend on one foundation task.

#### Fan-In Pattern
```
task-1   task-2   task-3
     \    |    /
       task-4
```
One task depends on multiple prerequisite tasks.

#### Diamond Pattern
```
       task-1
      /      \
  task-2    task-3
      \      /
       task-4
```
Common in complex features.

### The Toolkit Prevents Circular Dependencies

The toolkit automatically validates dependencies and prevents circular references:

**Example of invalid dependency:**
```
task-1 depends on task-2
task-2 depends on task-3
task-3 depends on task-1  ← Circular!
```

If Claude accidentally creates a circular dependency, the validation system will catch it. Claude will then refactor the task breakdown to eliminate the cycle.

---

## Progress Tracking

### Automatic Progress Management

The toolkit automatically tracks your progress:

**Automatic Time Tracking**: When Claude marks a task as in_progress or completed, timestamps are recorded automatically:
- `started_at` - When task moved to in_progress
- `completed_at` - When task marked completed
- `actual_hours` - Calculated from the timestamp duration

No manual time entry needed.

**Automatic Completion Detection**: When the last task in a spec is completed, Claude automatically detects this and prompts you to move the spec to `specs/completed/`.

### Working with `/sdd-begin`

Use `/sdd-begin` to manage your workflow:

1. **Shows pending specs** - See your backlog and activate specs when ready
2. **Shows active specs** - Continue work on current features
3. **Tracks progress** - See how many tasks are complete
4. **Detects completion** - Prompts to finalize when all tasks done

### Task Status

Tasks progress through statuses automatically as you work:
- `pending` - Not started
- `in_progress` - Currently working (Claude marks this when starting a task)
- `completed` - Done and verified (Claude marks this when you complete the task)
- `blocked` - Can't proceed (tell Claude about blockers)

### Journal Entries

Claude automatically journals completed tasks. Important decisions and changes are recorded in the spec's journal with timestamps.

**You can also manually add journal entries** by telling Claude:

> "Add a journal entry about [decision/change]"

### Don't Edit JSON Directly

Let Claude manage the spec files. The toolkit maintains consistency in timestamps, status transitions, and metadata. Manual edits can break validation.

---

## Working with Long Sessions

### Context Usage Monitoring

Claude has a 200k token limit, with 160k "usable context" (80%) before auto-compaction kicks in. The toolkit monitors your session usage and warns you when approaching limits.

**After completing tasks**, Claude checks context usage:

```
✅ Task completed
Context usage: 45% (72k/160k tokens)
Continue to next task?
```

### When to Save Progress

**50% usage** - Consider saving progress soon
**80% usage** - Strongly recommended to save and clear context

**How to resume after clearing**:
1. Use `/clear` to reset the conversation
2. Use `/sdd-begin` to resume - Claude will show you where you left off
3. Continue with next task

The spec tracks your progress, so you never lose your place.

### Long Feature Development

For large features spanning many tasks:

1. **Work in phases** - Complete a logical phase, then take a break
2. **Clear context between sessions** - Start fresh with `/sdd-begin`
3. **Review journal** - Check what was decided in previous sessions
4. **Check progress** - `/sdd-begin` shows completion percentage

**Pro tip**: If you know a feature will be large, consider splitting it into multiple specs that can be tackled across different sessions.

---

## Common Pitfalls

### 1. Bundling Multiple Files in One Task

**Problem**: "Implement authentication" task that changes 5 files
**Solution**: Create 5 tasks, one per file

### 2. Tasks Without Clear Verification

**Problem**: Task description doesn't explain how to verify it's done
**Solution**: Add explicit verification steps or criteria

### 3. Ignoring Dependencies

**Problem**: Starting tasks in wrong order, causing rework
**Solution**: Explicitly model dependencies in task metadata

### 4. Scope Creep

**Problem**: Adding features not in original spec during implementation
**Solution**: Document new requirements and update spec, or defer to next spec

### 5. Vague Task Descriptions

**Problem**: "Fix the bug" or "Improve code quality"
**Solution**: Be specific about what's being fixed/improved and how

---

## Quick Reference

### Task Decomposition Checklist

- [ ] Each task modifies exactly one file
- [ ] Multi-file features decomposed into multiple tasks
- [ ] Dependencies explicitly declared
- [ ] Test files have their own tasks/subtasks
- [ ] Documentation tasks included
- [ ] Investigation tasks use placeholder file_path
- [ ] No circular dependencies

### Spec Quality Checklist

- [ ] Feature overview is clear and specific
- [ ] All tasks have clear file_path values
- [ ] Dependencies are explicitly modeled
- [ ] Verification steps are defined
- [ ] Edge cases are considered
- [ ] Tasks are appropriately sized
- [ ] Phases are logically organized

---

## See Also

- [README.md](../README.md) - Toolkit overview and quick start
- [skills/sdd-plan/SKILL.md](../skills/sdd-plan/SKILL.md) - Detailed planning workflow
- [docs/DOCUMENTATION.md](DOCUMENTATION.md) - Complete toolkit documentation
