# Skills Reference

Complete reference for all SDD Toolkit skills. Skills are interactive workflows that you invoke using natural language with Claude Code.

## Table of Contents

- [Planning & Workflow](#planning--workflow)
- [Quality Assurance](#quality-assurance)
- [Documentation & Analysis](#documentation--analysis)
- [Workflow Commands](#workflow-commands)
- [Skill Invocation](#skill-invocation)

---

## Planning & Workflow

Core workflow skills for creating specs, orchestrating tasks, and tracking progress.

### sdd-plan

**Purpose**: Create structured specifications with tasks and dependencies

**When to use:**
- Starting a new feature or refactor
- Planning complex changes before coding
- Breaking down large projects into phases

**Example Usage:**

```
You: Create a spec for a CLI Pomodoro timer

Claude: [Uses sdd-plan skill]
        Analyzing your request...

        I'll create a specification for a CLI Pomodoro timer with the following structure:

        Phase 1: Core Timer Functionality
        - Task 1-1: Create Timer class with start/pause/stop
        - Task 1-2: Add countdown logic with 25-minute intervals
        - Task 1-3: Implement state persistence

        Phase 2: Notifications
        - Task 2-1: Add desktop notifications
        - Task 2-2: Add audio alerts

        Phase 3: CLI Interface
        - Task 3-1: Build command-line interface
        - Task 3-2: Add configuration options

        Created: specs/pending/pomodoro-timer-2025-11-22-001.json
```

**What it does:**
1. Analyzes your project structure (if docs available)
2. Breaks feature into phases and tasks
3. Identifies dependencies between tasks
4. Adds verification criteria
5. Estimates complexity
6. Creates validated JSON spec in `specs/pending/`

**Output**: JSON specification file ready for activation

**Common Patterns:**

| Pattern | Example Request |
|---------|----------------|
| New feature | "Create a spec for user authentication" |
| Refactoring | "Plan refactoring the database layer to use SQLAlchemy" |
| Bug fix | "Create a spec to fix the memory leak in the worker process" |
| Integration | "Plan integrating Stripe payment processing" |

---

### sdd-next

**Purpose**: Orchestrate workflow and find next actionable task

**When to use:**
- Starting work on a spec
- Finding what to work on after completing a task
- Resuming work after a break

**Example Usage:**

```
You: /sdd-begin

Claude: Found active spec: pomodoro-timer-2025-11-22-001
        Progress: 2/8 tasks (25%)

        Next task: Task 1-3 - Implement state persistence

        Context: Previous tasks created Timer class and countdown logic.
        Now we need to persist timer state so users can resume after restart.

        Execution Plan:
        1. Create StateManager class to handle persistence
        2. Use JSON file for state storage (~/.pomodoro/state.json)
        3. Save state on pause/stop events
        4. Load state on timer initialization
        5. Add tests for save/load functionality

        Approve this plan?

You: Yes

Claude: [Implements task-1-3]
        [Runs tests]
        [Marks complete]

        Task 1-3 completed (0.5 hours)
        Ready for Task 2-1: Add desktop notifications
```

**What it does:**
1. Finds active/pending specs
2. Identifies next actionable task (no blockers)
3. Gathers context from previous tasks
4. Creates execution plan
5. Seeks approval before implementing
6. Tracks progress and suggests next steps

**Two Modes:**

| Mode | Behavior | Configuration |
|------|----------|---------------|
| **Single Task** (default) | Complete one task, then ask user | `"work_mode": "single"` |
| **Autonomous** | Complete all tasks in phase automatically | `"work_mode": "autonomous"` |

**Common Patterns:**

| Pattern | Example |
|---------|---------|
| Continue spec | "What should I work on next?" |
| Resume work | "/sdd-begin" |
| Specific task | "Start task-2-1 from the auth spec" |
| Browse alternatives | "Show me other pending tasks" |

---

### sdd-update

**Purpose**: Update task status, journal decisions, and move specs between folders

**When to use:**
- Marking tasks complete
- Recording decisions or notes
- Moving specs to different lifecycle folders
- Tracking blockers

**Example Usage:**

```
You: Mark task-1-2 complete with note about implementation

Claude: [Uses sdd-update skill]
        Completed task-1-2 in auth-feature-001

        Journal entry created:
        - Task: Create password hashing service
        - Status: completed
        - Note: Implemented using bcrypt with cost factor 12.
                All 8 unit tests passing.
        - Duration: 1.2 hours

        Spec progress: 40% (4/10 tasks)
```

**What it does:**
1. Updates task status (pending → in_progress → completed)
2. Records timestamps and durations
3. Creates journal entries
4. Moves specs between folders
5. Updates spec-level metadata

**Status Transitions:**

```
pending → in_progress → completed
   ↓           ↓
blocked    blocked
```

**Common Operations:**

| Operation | Example |
|-----------|---------|
| Mark complete | "Complete task-1-3" |
| Add journal | "Add a note to task-2-1 about the API design decision" |
| Move spec | "Move auth-feature-001 to completed" |
| Mark blocked | "Mark task-3-2 as blocked due to missing API" |

---

### sdd-validate

**Purpose**: Check specification validity and auto-fix common issues

**When to use:**
- Before activating a spec
- After manually editing spec JSON
- When debugging task dependencies
- Checking for circular dependencies

**Example Usage:**

```
You: Validate my authentication spec

Claude: [Uses sdd-validate skill]
        Validating specs/pending/auth-feature-001.json...

        ✅ Schema validation: PASSED
        ✅ Task ID uniqueness: PASSED
        ✅ Dependency references: PASSED
        ⚠️  Found 1 issue:

        Issue: Circular dependency detected
        - task-2-1 depends on task-2-3
        - task-2-3 depends on task-2-1

        Auto-fix available: Remove task-2-1 → task-2-3 dependency

        Apply fix?

You: Yes

Claude: Fixed circular dependency
        Spec is now valid ✅
```

**What it validates:**
- JSON schema compliance
- Task ID uniqueness
- Dependency reference validity
- Circular dependency detection
- Phase structure
- Required field presence

**Validation Modes:**

| Mode | Command | Purpose |
|------|---------|---------|
| Check only | `sdd validate <spec>` | Report issues without fixing |
| Auto-fix | `sdd validate <spec> --fix` | Fix common issues automatically |
| Show graph | `sdd validate <spec> --show-graph` | Visualize dependency graph |

---

### sdd-render

**Purpose**: Generate human-readable markdown from spec JSON

**When to use:**
- Sharing specs with team members
- Reviewing spec structure
- Documentation purposes
- Getting AI-enhanced insights

**Example Usage:**

```
You: Render my authentication spec with insights

Claude: [Uses sdd-render skill]
        Generating markdown for auth-feature-001...

        Created: specs/.human-readable/auth-feature-001.md

        Contents:
        - Metadata and overview
        - Phase breakdown with progress
        - Task list with dependencies
        - Dependency graph visualization
        - Journal entries
        - AI insights on complexity and risks
```

**Output Formats:**

| Format | Details |
|--------|---------|
| Basic | Metadata, phases, tasks, journal |
| With insights | Includes AI analysis of complexity and risks |
| With visualizations | Dependency graphs and progress charts |

**Output Location**: `specs/.human-readable/` (gitignored)

---

## Quality Assurance

Skills for reviewing specs, verifying implementations, and ensuring quality.

### sdd-plan-review

**Purpose**: Multi-model review of specifications before implementation

**When to use:**
- After creating a new spec
- Before activating a spec
- When unsure about task breakdown
- For complex or critical features

**Example Usage:**

```
You: Review my authentication spec before I implement it

Claude: [Uses sdd-plan-review skill]
        Consulting cursor-agent and gemini in parallel...

        cursor-agent analysis complete (34.2s)
        gemini analysis complete (36.8s)

        === Consensus Findings ===

        ✅ Strengths (both models agree):
        - Overall approach is sound and follows best practices
        - Task breakdown is appropriate and atomic
        - Dependencies are well-structured

        💡 Suggestions (both models agree):
        - Add explicit error handling tasks
        - Consider rate limiting on auth endpoints

        === Model-Specific Suggestions ===

        cursor-agent suggests:
        - Add retry logic for token validation (transient failures)
        - Consider implementing refresh token rotation
        - Add task for session cleanup background job

        gemini suggests:
        - Add session timeout configuration task
        - Consider multi-factor authentication hooks for future
        - Add monitoring/logging tasks for auth events

        Review saved to: specs/.reviews/auth-feature-001-review.json
```

**What it does:**
1. Sends spec to multiple AI models in parallel
2. Each model independently analyzes quality
3. Detects consensus findings (both agree)
4. Synthesizes unique suggestions per model
5. Caches results to avoid repeated API calls

**Default Models**: cursor-agent + gemini (configurable in `.claude/ai_config.yaml`)

**Review Criteria:**
- Task atomicity and clarity
- Dependency correctness
- Missing tasks or edge cases
- Complexity estimation
- Best practice adherence

---

### sdd-fidelity-review

**Purpose**: Verify implementation matches specification requirements

**When to use:**
- After completing a phase
- Before creating a pull request
- When unsure if implementation matches spec
- Quality gate before deployment

**Example Usage:**

```
You: Did I implement what the authentication spec said?

Claude: [Uses sdd-fidelity-review skill]
        Reviewing implementation against spec...
        Consulting cursor-agent and gemini...

        === Phase 1: Core Auth System ===

        ✅ task-1-1: Create User model - COMPLIANT
           Code: models/user.py matches spec requirements
           - Email validation implemented
           - Password hashing with bcrypt

        ✅ task-1-2: Password hashing service - COMPLIANT
           Code: services/auth.py:15-42
           - Uses bcrypt as specified
           - Cost factor 12 as specified

        ⚠️  task-1-3: JWT token generation - DEVIATION
           Code: services/token.py:28-55

           Deviation:
           - Spec: JWT with 24-hour expiry
           - Implemented: JWT with 1-hour expiry

           Impact: Medium
           Recommendation: Update spec to document 1-hour expiry
                          or change code to 24-hour

        === Summary ===
        - Compliant: 9/10 tasks (90%)
        - Deviations: 1/10 tasks (10%)
        - Overall: Implementation is mostly compliant

        Report saved to: specs/.reports/auth-feature-001-fidelity.json
```

**What it does:**
1. Reads completed tasks from spec
2. Analyzes corresponding code implementation
3. Compares actual vs. specified behavior
4. Identifies deviations with severity levels
5. Provides remediation recommendations

**Review Scopes:**

| Scope | Usage |
|-------|-------|
| Task | `Review task-1-2 in auth-feature-001` |
| Phase | `Review phase-1 in auth-feature-001` |
| Full spec | `Review all implementation in auth-feature-001` |

**Deviation Severity:**

| Level | Meaning |
|-------|---------|
| Low | Minor difference, no functional impact |
| Medium | Noticeable difference, limited impact |
| High | Significant difference, requires decision |

---

### sdd-modify

**Purpose**: Apply systematic modifications to specifications based on review feedback

**When to use:**
- After receiving plan review feedback
- When refining specs before implementation
- Applying bulk changes to task structure
- Making systematic updates

**Example Usage:**

```
You: Apply the review feedback to my auth spec

Claude: [Uses sdd-modify skill]
        Analyzing review feedback from auth-feature-001-review.json...

        Proposed modifications:
        1. Add task-1-4: Implement retry logic for token validation
        2. Add task-2-3: Create session cleanup background job
        3. Add task-3-1: Add rate limiting middleware
        4. Update task-2-1 dependencies to include task-1-4

        Apply these changes?

You: Yes

Claude: Applied 4 modifications to auth-feature-001
        Spec validated successfully ✅

        Updated spec saved with backup at:
        specs/.backups/auth-feature-001-20251122-140215.json
```

**What it does:**
1. Parses review recommendations
2. Generates modification plan
3. Shows proposed changes
4. Creates backup before modifying
5. Applies changes with validation
6. Verifies spec integrity

**Safety Features:**
- Automatic backups before modification
- Validation after changes
- Rollback on validation failure
- Confirmation before applying

---

### run-tests

**Purpose**: Execute tests with AI-powered debugging and failure analysis

**When to use:**
- Verifying task completion
- Debugging test failures
- Understanding test errors
- Getting fix suggestions

**Example Usage:**

```
You: Run tests for the authentication module

Claude: [Uses run-tests skill]
        Running pytest tests/auth/...

        ================================
        3 passed, 2 failed in 4.21s
        ================================

        Analyzing failures with gemini...

        === test_authenticate_user FAILED ===

        Error: AttributeError: Mock object has no attribute 'find_by_email'

        AI Analysis:
        - Issue: Missing mock configuration for UserRepository
        - Root cause: Test doesn't mock the find_by_email method

        Suggested fix:
        ```python
        @patch('auth.services.user_repo')
        def test_authenticate_user(mock_repo):
            mock_repo.find_by_email.return_value = User(...)
            # rest of test
        ```

        === test_validate_token FAILED ===

        Error: AssertionError: Expected False but got True

        AI Analysis:
        - Issue: Token expiry time not properly mocked
        - Root cause: System time advancing during test

        Suggested fix:
        ```python
        from freezegun import freeze_time

        @freeze_time("2025-11-22 14:00:00")
        def test_validate_token():
            # test code here
        ```

        Apply fixes?

You: Yes

Claude: [Applies fixes and reruns tests]
        All tests passing ✅ (5/5)
```

**What it does:**
1. Runs specified tests (pytest, etc.)
2. Captures failures and errors
3. Consults AI for root cause analysis
4. Suggests specific fixes
5. Can apply fixes automatically
6. Reruns tests to verify

**Test Modes:**

| Mode | Usage |
|------|-------|
| Run all | "Run all tests" |
| Run specific | "Run tests in tests/auth/" |
| Debug failing | "Debug test_authenticate_user" |
| Run and fix | "Run tests and fix failures" |

---

## Documentation & Analysis

Skills for querying code, generating docs, and analyzing project structure.

### doc-query

**Purpose**: Query and analyze codebase using generated documentation

**When to use:**
- Finding code without parsing source
- Understanding call relationships
- Analyzing dependencies
- Refactoring impact analysis
- During task planning

**Example Usage:**

```
You: What functions call the authenticate() method?

Claude: [Uses doc-query skill]
        Querying docs/codebase.json...

        Found 5 callers of authenticate():

        1. LoginController.login() - controllers/auth.py:42
           Complexity: 6
           Calls: authenticate(email, password)

        2. APIAuthMiddleware.process() - middleware/auth.py:28
           Complexity: 4
           Calls: authenticate(token=request.token)

        3. RefreshTokenHandler.refresh() - handlers/token.py:15
           Complexity: 3
           Calls: authenticate(refresh_token=token)

        4. CLI.login_command() - cli/commands.py:89
           Complexity: 2
           Calls: authenticate(username, password)

        5. TestAuthService.test_login() - tests/test_auth.py:12
           Complexity: 1
           Test code
```

**Query Types:**

| Query | Command | Example |
|-------|---------|---------|
| Project stats | `sdd doc stats` | Overview of codebase |
| Find code | `sdd doc search "authentication"` | Keyword search |
| Complexity | `sdd doc complexity --threshold 10` | High-complexity functions |
| Dependencies | `sdd doc dependencies src/auth.py` | Module dependencies |
| Callers | `sdd doc callers function_name` | Who calls this? |
| Callees | `sdd doc callees function_name` | What does this call? |
| Call graph | `sdd doc call-graph entry_point` | Full call tree |
| Impact | `sdd doc impact function_name` | Refactoring impact |
| Refactor candidates | `sdd doc refactor-candidates` | Complex code |

**Scoped Context:**

Use `scope` for targeted documentation during planning and implementation:

```bash
# Lightweight context for planning (signatures, summaries)
sdd doc scope src/auth.py --plan

# Detailed context for implementation (full code, patterns)
sdd doc scope src/auth.py --implement
```

**Prerequisites**: Must run `sdd doc analyze-with-ai` first to generate `docs/codebase.json`

---

### llm-doc-gen

**Purpose**: Generate AI-enhanced narrative documentation for your codebase

**When to use:**
- Creating project documentation
- Onboarding documentation
- Architecture overviews
- API documentation
- Tutorial generation

**Example Usage:**

```
You: Generate comprehensive documentation for this codebase

Claude: [Uses llm-doc-gen skill]
        Analyzing codebase structure...
        Generating documentation with cursor-agent and gemini...

        Progress:
        ✓ Analyzing 183 Python files
        ✓ Extracting AST and metrics
        ✓ Generating project overview (cursor-agent: 24.3s)
        ✓ Generating architecture docs (gemini: 28.7s)
        ✓ Creating component inventory
        ✓ Writing index and navigation

        Generated documentation:

        docs/
        ├── codebase.json              # Machine-readable data
        ├── index.md                   # Main navigation
        ├── project-overview.md        # Executive summary
        ├── architecture.md            # Architecture overview
        ├── component-inventory.md     # Component catalog
        └── api/                       # API documentation
            ├── auth.md
            ├── database.md
            └── services.md

        Documentation includes:
        - Project statistics (183 modules, 154 classes, 915 functions)
        - Architecture patterns identified
        - Component relationships
        - Complexity analysis
        - Cross-references
```

**What it generates:**

| Document | Purpose |
|----------|---------|
| `project-overview.md` | Executive summary, goals, tech stack |
| `architecture.md` | Architecture patterns, data flow, design decisions |
| `component-inventory.md` | Component catalog with responsibilities |
| `index.md` | Main navigation and cross-references |
| `codebase.json` | Machine-readable structural data |

**Configuration**: Uses models configured in `.claude/ai_config.yaml`

---

## Workflow Commands

Slash commands for quick workflow actions.

### /sdd-begin

**Purpose**: Resume work - shows pending/active specs with interactive options

**When to use:**
- Starting a new session
- After completing a task
- When unsure what to work on next

**Example Usage:**

```
You: /sdd-begin

Claude: 📋 SDD Specifications (Active & Pending):

        ⚡ auth-feature-001 - User Authentication
           Progress: 3/10 tasks (30%)
           Folder: active | Status: in_progress
           🕐 Last accessed: task-1-3 (0.2 hours ago)

        ⏸️ [PENDING] rate-limiting-002 - API Rate Limiting
           Progress: 0/7 tasks (0%)
           Folder: pending | Status: pending

        What would you like to do?
        1. Resume last task (task-1-3 from auth-feature-001)
        2. Continue with next task
        3. Write new spec
        4. View pending backlog (1 spec)
        5. Something else

You: 2

Claude: Continuing with task-1-4: Add JWT refresh tokens
        [Shows execution plan and begins implementation]
```

**What it does:**
1. Scans for active and pending specs
2. Shows progress and last accessed task
3. Provides interactive options
4. Automatically invokes `sdd-next` based on selection

**Interactive Options:**

| Option | When Shown | Action |
|--------|------------|--------|
| Resume last task | Last accessed task exists | Continue specific task |
| Continue with next task | In-progress work exists | Find next task |
| Write new spec | Always | Invoke `sdd-plan` |
| View pending backlog | Pending specs exist | Show and activate pending |
| Something else | Always | Exit gracefully |

---

### /sdd-setup

**Purpose**: Configure project permissions and settings

**When to use:**
- First time using SDD in a project
- After installing/updating the plugin
- When permissions errors occur

**Example Usage:**

```
You: /sdd-setup

Claude: Configuring SDD toolkit for your project...

        Setting up project permissions:
        ✓ specs/ directory access
        ✓ .claude/ configuration access
        ✓ docs/ documentation access

        Creating configuration files:
        ✓ .claude/settings.local.json
        ✓ .claude/sdd_config.json
        ✓ .claude/ai_config.yaml

        Configuration complete ✅

        You can now:
        - Create specs with natural language
        - Use /sdd-begin to start work
        - Use sdd-plan skill to create specifications
```

**What it creates:**

| File | Purpose |
|------|---------|
| `.claude/settings.local.json` | Permission grants for spec operations |
| `.claude/sdd_config.json` | CLI output preferences and work mode |
| `.claude/ai_config.yaml` | AI model defaults and tool priority |

**Run once per project** - only needed for initial setup

---

## Skill Invocation

### How to Use Skills

Skills are invoked through natural language requests to Claude Code:

```
You: [Natural language request matching skill purpose]
Claude: [Automatically selects and invokes appropriate skill]
```

### Skill Selection

Claude automatically selects the right skill based on your request:

| Request Type | Skill Used |
|--------------|------------|
| "Create a spec for..." | `sdd-plan` |
| "What should I work on next?" | `sdd-next` |
| "Mark task complete" | `sdd-update` |
| "Review my spec" | `sdd-plan-review` |
| "Did I implement the spec?" | `sdd-fidelity-review` |
| "Run tests and debug" | `run-tests` |
| "What calls this function?" | `doc-query` |
| "Generate documentation" | `llm-doc-gen` |

### Skill Composition

Skills often work together in workflows:

```
sdd-plan → sdd-validate → /sdd-begin → sdd-next → sdd-update → sdd-fidelity-review → sdd-pr
   ↓           ↓              ↓           ↓           ↓              ↓                    ↓
Create     Validate      Resume      Execute    Complete        Verify              Create PR
 spec       spec          work         task       task         implementation
```

---

## Next Steps

- **Understand concepts**: See [Core Concepts](core-concepts.md) for underlying principles
- **Learn workflows**: Check [Workflows](workflows.md) for common development patterns
- **Try examples**: Walk through [Complete Task Workflow](examples/complete_task_workflow.md)
- **Configure**: Review [Configuration](configuration.md) for setup options

---

**Related Documentation:**
- [Core Concepts](core-concepts.md) - Fundamental concepts
- [Workflows](workflows.md) - Common development patterns
- [Configuration](configuration.md) - Setup and configuration
- [CLI Reference](cli-reference.md) - Command-line interface
