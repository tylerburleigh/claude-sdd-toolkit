# Core Concepts

This guide explains the fundamental concepts of the SDD Toolkit and how they work together to provide structured, trackable development.

## Table of Contents

- [Specifications (Specs)](#specifications-specs)
- [Tasks: Atomic Work Units](#tasks-atomic-work-units)
- [Dependencies & Orchestration](#dependencies--orchestration)
- [Multi-Model Consultation](#multi-model-consultation)
- [Documentation Integration](#documentation-integration)
- [Context Tracking](#context-tracking)
- [Subagent Architecture](#subagent-architecture)

---

## Specifications (Specs)

Specifications are the foundation of the SDD workflow. They are machine-readable JSON files that define features, break them into tasks, track dependencies, and record progress.

### Structure

A specification contains metadata, phases, tasks, and a journal:

```json
{
  "metadata": {
    "name": "User Authentication",
    "version": "1.0.0",
    "complexity": "medium"
  },
  "phases": [
    {
      "id": "phase-1",
      "title": "Core Auth System",
      "tasks": [...]
    }
  ],
  "tasks": [
    {
      "id": "task-1-1",
      "title": "Create User model",
      "phase_id": "phase-1",
      "dependencies": [],
      "status": "pending",
      "verification": ["Model validates email", "Password hashing works"]
    }
  ],
  "journal": []
}
```

### Schema Validation

All specs are validated against `specification-schema.json` to ensure:
- Required fields are present
- Task IDs are unique
- Dependencies reference valid tasks
- Status transitions are valid

Use `sdd validate <spec>` to check spec validity and `sdd validate <spec> --fix` to auto-correct common issues.

### Lifecycle Folders

Specs move through different folders as they progress:

| Folder | Purpose | When Used |
|--------|---------|-----------|
| `pending/` | Backlog awaiting activation | After creation with `sdd-plan` |
| `active/` | Current work | After activation (supports parallel specs) |
| `completed/` | Finished features | After all tasks complete |
| `archived/` | Cancelled/deprecated | For abandoned work |

**Example workflow:**
```bash
specs/pending/auth-feature-001.json
  → sdd activate-spec auth-feature-001
specs/active/auth-feature-001.json
  → [complete all tasks]
specs/completed/auth-feature-001.json
```

---

## Tasks: Atomic Work Units

Each task represents a single, focused change. Tasks are the smallest unit of work in SDD.

### Task Structure

```json
{
  "id": "task-1-1",
  "title": "Implement JWT token generation",
  "description": "Create TokenService.generateToken() method...",
  "phase_id": "phase-1",
  "dependencies": ["task-1-0"],
  "verification": [
    "Token contains user ID and expiry",
    "Token passes signature validation"
  ],
  "status": "pending",
  "category": "implementation",
  "estimated_hours": 2.0,
  "actual_hours": null,
  "started_at": null,
  "completed_at": null
}
```

### Automatic Time Tracking

The toolkit automatically tracks task timing:

- **`started_at`**: Recorded when status changes to `in-progress`
- **`completed_at`**: Recorded when status changes to `completed`
- **`actual_hours`**: Calculated from the difference between timestamps
- **Spec totals**: Aggregated from all completed tasks

**Example:**
```bash
sdd update-status my-spec-001 task-1-1 in_progress
# started_at: "2025-11-22T14:30:00Z"

sdd complete-task my-spec-001 task-1-1
# completed_at: "2025-11-22T16:45:00Z"
# actual_hours: 2.25
```

### Task Categories

Tasks are categorized by their purpose:

| Category | Purpose | Example |
|----------|---------|---------|
| `investigation` | Explore codebase, understand patterns | "Analyze existing auth implementations" |
| `implementation` | Write new code or features | "Create JWT token service" |
| `refactoring` | Improve code structure | "Extract auth logic to separate module" |
| `decision` | Make architecture choices | "Choose between JWT vs session tokens" |
| `research` | External research needed | "Research OAuth 2.0 best practices" |

Categories help with:
- Estimating task complexity
- Organizing phase structure
- Understanding work distribution

---

## Dependencies & Orchestration

Dependencies define the order in which tasks must be completed. The SDD toolkit uses dependency information to determine which tasks are ready to start.

### Dependency Declaration

Tasks declare dependencies using task IDs:

```json
{
  "id": "task-2-1",
  "title": "Add rate limiting middleware",
  "dependencies": ["task-1-1", "task-1-2"]
}
```

This means `task-2-1` cannot start until both `task-1-1` and `task-1-2` are completed.

### Dependency Resolution

The `sdd-next` skill uses dependencies to:

1. **Determine which tasks are ready** - Tasks with no incomplete dependencies
2. **Provide correct execution order** - Ensures prerequisites are met
3. **Enable parallel work** - Independent tasks can be worked on simultaneously

**Example:**
```
Phase 1:
├── task-1-1 (no deps) ✅ ready
├── task-1-2 (no deps) ✅ ready
└── task-1-3 (depends on task-1-1, task-1-2) ❌ blocked

After completing task-1-1 and task-1-2:
└── task-1-3 ✅ ready
```

### Validation

The `sdd-validate` skill detects:
- Circular dependencies (A depends on B, B depends on A)
- Missing dependency targets (depends on non-existent task)
- Cross-phase dependency issues

**Visualize dependencies:**
```bash
sdd validate <spec> --show-graph
```

This generates a visual representation of task dependencies.

---

## Multi-Model Consultation

Several skills use multi-model AI consultation to get diverse perspectives and reduce bias.

### Skills Using Multi-Model Consultation

- **`sdd-plan-review`**: Spec quality assessment before implementation
- **`sdd-fidelity-review`**: Implementation verification against spec
- **`llm-doc-gen`**: AI-enhanced documentation generation

### Consultation Process

1. **Parallel consultation** of 2+ AI models (default: cursor-agent + gemini)
2. **Independent analysis** by each model
3. **Consensus detection** for common findings
4. **Synthesis** into unified report
5. **Results cached** to reduce API costs on subsequent runs

### Trade-offs

| Aspect | Benefit | Cost |
|--------|---------|------|
| **Quality** | Multiple perspectives reduce bias and blind spots | Higher API usage |
| **Reliability** | Redundancy (succeeds if ≥1 model succeeds) | More complex error handling |
| **Performance** | Parallel execution minimizes latency | Requires multiple API keys |
| **Cost** | Caching reduces repeated calls | Initial runs more expensive |

### Configuration

Default models are configured in `.claude/ai_config.yaml`:

```yaml
sdd-plan-review:
  tool_priority:
    - gemini
    - cursor-agent
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1
```

Override per-invocation:
```bash
sdd plan-review my-spec.json \
  --model gemini=gemini-2.5-flash \
  --model cursor-agent=composer-2
```

---

## Documentation Integration

The toolkit generates and queries machine-readable documentation of your codebase, which is then used by skills to understand context.

### Generated Documentation

Run documentation analysis:

```bash
sdd doc analyze-with-ai . --name "MyProject" --version "1.0.0"
```

**Outputs:**

| File | Purpose |
|------|---------|
| `docs/codebase.json` | Machine-readable data (AST, dependencies, metrics) |
| `docs/index.md` | Human-readable structural reference with shard files |
| `docs/project-overview.md` | Executive summary |
| `docs/architecture.md` | Architecture overview |
| `docs/component-inventory.md` | Component catalog |

### How Skills Use Documentation

- **`sdd-plan`**: Understands existing patterns and code structure
- **`sdd-next`**: Provides code context for task implementation
- **`doc-query`**: Fast queries without re-parsing source files

### Query Capabilities

Fast lookups without parsing source code:

```bash
# Project statistics
sdd doc stats

# Find code by keyword
sdd doc search "authentication"

# High-complexity functions
sdd doc complexity --threshold 10

# Module dependencies
sdd doc dependencies src/auth.py

# Who calls this function?
sdd doc callers authenticate_user

# What does this function call?
sdd doc callees authenticate_user

# Full call graph
sdd doc call-graph login_endpoint

# Refactoring impact analysis
sdd doc impact change_function

# Find refactoring candidates
sdd doc refactor-candidates
```

### Scoped Context for Planning vs Implementation

Use `sdd doc scope` to get targeted documentation context:

```bash
# Lightweight context for planning (function signatures, summaries)
sdd doc scope src/auth.py --plan

# Detailed context for implementation (full code, patterns, examples)
sdd doc scope src/auth.py --implement
```

See [CLI Reference](cli-reference.md) for complete documentation commands.

---

## Context Tracking

Claude Code has finite context limits. The toolkit monitors context usage to prevent hitting limits mid-task.

### Context Limits

- **Total context window**: 200k tokens
- **Usable before auto-compaction**: 160k tokens (80% threshold)
- **Recommended clear point**: 85% (136k tokens)

### Automatic Monitoring

The `sdd-next` skill automatically monitors context during autonomous mode:

```
Claude: [Completes task-1-1]
        Context: 45% (72k/160k tokens)

        [Completes task-1-2]
        Context: 62% (99k/160k)

        [Completes task-1-3]
        Context: 78% (125k/160k)

        Warning: Context approaching threshold
```

### Managing Context

When context exceeds 85%:

1. **Save progress**: Current task status is already saved
2. **Clear context**: Use `/clear` command
3. **Resume work**: Use `/sdd-begin` to continue where you left off

The spec tracks all progress, so resuming is seamless.

### Manual Context Check

During long sessions, check context manually:

```bash
# Two-step process
sdd session-marker
sdd context --session-marker "SESSION_MARKER_<hash>"
```

Output:
```json
{"context_percentage_used": 78}
```

---

## Subagent Architecture

Some skills use **subagents** - specialized Claude instances for complex, multi-step tasks.

### How Subagents Work

```
User Request → Main Claude → Task Tool → Subagent → Execute → Report Back
```

The main Claude instance delegates work to a specialized subagent, which executes autonomously and reports results.

### Skills Using Subagents

**Quality & Validation:**
- `sdd-validate` - Spec validation and auto-fixing
- `sdd-plan-review` - Multi-model spec review
- `sdd-fidelity-review` - Implementation verification
- `sdd-modify` - Apply spec modifications

**Progress & Testing:**
- `sdd-update` - Status updates and journal entries
- `run-tests` - Test execution with AI debugging

**Pull Requests:**
- `sdd-pr` - AI-powered PR creation

### Skills Running Directly

These skills run in the main Claude instance (no subagent):
- `sdd-plan` - Spec creation
- `sdd-next` - Task orchestration
- `doc-query` - Documentation queries

### Why Use Subagents?

| Benefit | Description |
|---------|-------------|
| **Isolation** | Complex tasks don't pollute main context |
| **Specialization** | Subagents have task-specific instructions |
| **Autonomy** | Can execute multi-step workflows independently |
| **Reporting** | Clean summary of results returned to main instance |

---

## Next Steps

Now that you understand the core concepts:

1. **Learn the workflows**: See [Workflows](workflows.md) for common development patterns
2. **Explore skills**: Check [Skills Reference](skills-reference.md) for detailed skill documentation
3. **Try examples**: Walk through [Complete Task Workflow](examples/complete_task_workflow.md)
4. **Configure your project**: Run `/sdd-setup` to initialize SDD in your project

---

**Related Documentation:**
- [Skills Reference](skills-reference.md) - Detailed skill documentation
- [Workflows](workflows.md) - Common development patterns
- [Configuration](configuration.md) - Setup and configuration options
- [CLI Reference](cli-reference.md) - Command-line interface
