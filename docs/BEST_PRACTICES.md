# SDD Toolkit Best Practices

This document provides best practices, patterns, and guidelines for effective use of the SDD (Spec-Driven Development) Toolkit.

## Table of Contents

- [Task Granularity and Decomposition](#task-granularity-and-decomposition)
- [Specification Quality](#specification-quality)
- [Phase Organization](#phase-organization)
- [Dependency Management](#dependency-management)
- [Progress Tracking](#progress-tracking)

---

## Task Granularity and Decomposition

### The Atomic Task Principle

**Core Rule**: Each task should modify exactly ONE file.

This is a fundamental design principle of SDD that enables:
- **Precise dependency tracking**: File-level dependencies are explicit and clear
- **Granular progress monitoring**: Each completed task represents concrete, verifiable progress
- **Parallel implementation**: Independent tasks can be worked on simultaneously
- **Straightforward verification**: Each task has a focused scope and clear success criteria
- **Easy rollback**: Changes can be reverted at the file level without affecting other work

### When a Feature Spans Multiple Files

You have two primary approaches:

#### Approach 1: Multiple Independent Tasks (Recommended)

Create separate tasks for each file, with explicit dependencies.

**Example:**
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

**When to use**: Most scenarios, especially when files have clear dependency relationships.

#### Approach 2: Subtasks Under a Parent Task

Use a parent task to coordinate, with child subtasks for each file.

**Example:**
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

**When to use**: When files are tightly coupled and logically form a single feature unit.

### Identifying Atomic Units

#### ✅ Good Task Granularity

**One clear file, one focused change:**
- "Create authentication middleware in middleware/auth.js"
- "Add user validation to models/user.js"
- "Update API routes in routes/api.js"
- "Add error handling to services/payment.js"
- "Create rate limiter utility in utils/rateLimit.js"

#### ❌ Too Broad - Split These

**Multiple files bundled together:**
- "Add authentication" → Split into: middleware task, model task, routes task, config task
- "Refactor user system" → Split into: one task per file being refactored
- "Update all configuration files" → One task per config file
- "Implement payment processing" → Split into: validation, API client, webhook handler, database models

**How to fix**: Identify each file that needs changes and create a separate task for each.

#### ❌ Too Narrow - Combine These

**Multiple tasks for the same file:**
- "Add import statement to file.js" + "Add function to file.js" → Combine into one task
- "Update line 42" + "Update line 43" + "Update line 44" → All same file, one task
- "Add type definition" + "Implement function using that type" → If same file, combine

**How to fix**: If all changes are to the same file and are part of the same logical change, combine into a single task.

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

## Specification Quality

### Be Specific and Concrete

**❌ Vague:**
- "Improve error handling"
- "Add better logging"
- "Optimize performance"

**✅ Specific:**
- "Add try-catch blocks to all API calls in services/api.js with structured error responses"
- "Add debug logging to authentication middleware with request ID tracking"
- "Implement response caching in API routes to reduce database queries by 50%"

### Include Context and Examples

**Good task descriptions include:**
- What is being changed
- Why it's being changed
- What success looks like
- Example input/output if applicable

**Example:**
```json
{
  "task-1-1": {
    "title": "Add rate limiting to API endpoints",
    "description": "Implement rate limiting middleware to prevent API abuse. Use sliding window algorithm with Redis backend. Limit: 100 requests per minute per IP. Return 429 status with Retry-After header when exceeded.",
    "metadata": {
      "file_path": "middleware/rateLimit.js"
    }
  }
}
```

### Think Ahead

Consider during planning:
- **Testing**: How will this be tested?
- **Monitoring**: What metrics/logs are needed?
- **Documentation**: What needs to be documented?
- **Dependencies**: What must exist first?
- **Rollback**: How can this be safely reverted?

### Stay Grounded in Reality

**Do:**
- Explore the actual codebase before planning
- Verify APIs and libraries exist
- Check existing patterns and conventions
- Identify real integration points

**Don't:**
- Assume APIs or functions exist
- Plan around imaginary utilities
- Ignore existing architecture
- Guess at implementation details

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

## Dependency Management

### Explicit Dependencies

Always declare dependencies explicitly in task metadata:

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

### Dependency Patterns

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

### Avoiding Circular Dependencies

**Anti-pattern:**
```
task-1 depends on task-2
task-2 depends on task-3
task-3 depends on task-1  ← Circular!
```

**How to detect**: Validation will catch these
**How to fix**: Refactor task breakdown to eliminate the cycle

---

## Progress Tracking

### Task Status Updates

Update task status as you work:
- `"status": "pending"` - Not started
- `"status": "in_progress"` - Currently working on it
- `"status": "completed"` - Done and verified
- `"status": "blocked"` - Can't proceed (add blocker info)

### Journal Entries

Document important decisions and changes:

```json
{
  "journal": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "author": "Claude",
      "entry": "Completed task-1-1. Chose JWT over sessions due to stateless requirement. Tests passing."
    }
  ]
}
```

### When to Update Specs

Use `Skill(sdd-toolkit:sdd-update)` to:
- Mark tasks complete
- Add journal entries
- Update progress metrics
- Document blockers
- Record decisions

**Don't** manually edit the JSON - use the skill to maintain consistency.

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
