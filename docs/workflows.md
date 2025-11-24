# Common Workflows

Step-by-step guides for common development patterns using the SDD Toolkit. Each workflow includes commands, expected responses, and troubleshooting tips.

## Table of Contents

- [Plan and Implement a Feature](#plan-and-implement-a-feature)
- [Resume After Break](#resume-after-break)
- [Generate and Query Documentation](#generate-and-query-documentation)
- [Multi-Model Spec Review](#multi-model-spec-review)
- [Verify Implementation Fidelity](#verify-implementation-fidelity)
- [Debug Test Failures](#debug-test-failures)
- [Create Pull Request](#create-pull-request)

---

## Plan and Implement a Feature

**Goal**: Create a specification for a new feature and implement it task by task.

### Step-by-Step

**1. Create the specification**

```
You: Create a spec for adding rate limiting to the API endpoints

Claude: [Uses sdd-plan skill]
        Analyzing your project...

        I'll create a specification with the following structure:

        Phase 1: Core Rate Limiting (4 tasks)
        - Implement RateLimiter middleware class
        - Add Redis backend for rate limit storage
        - Configure rate limit rules per endpoint
        - Add rate limit headers to responses

        Phase 2: Testing & Monitoring (3 tasks)
        - Add unit tests for RateLimiter
        - Add integration tests for API endpoints
        - Add monitoring metrics for rate limit hits

        Created: specs/pending/rate-limiting-2025-11-22-001.json
```

**What happened:**
- sdd-plan analyzed your codebase (using docs if available)
- Created phases with atomic tasks
- Set up dependencies between tasks
- Saved spec to `specs/pending/`

**2. Activate and start**

```
You: /sdd-begin

Claude: Found 1 pending spec:

        rate-limiting-2025-11-22-001 - API Rate Limiting
        Progress: 0/7 tasks (0%)

        What would you like to do?
        1. Continue with next task
        2. Write new spec
        3. Something else

You: 1

Claude: [Activates spec, moves to specs/active/]

        Task 1-1: Implement RateLimiter middleware class

        Execution Plan:
        1. Create middleware/rate_limiter.py
        2. Implement RateLimiter class with check() method
        3. Add configurable limits (requests/window)
        4. Return 429 status when limit exceeded
        5. Add tests

        Approve this plan?

You: Yes
```

**What happened:**
- `/sdd-begin` found the pending spec
- Spec moved from `specs/pending/` to `specs/active/`
- sdd-next identified first task and created execution plan
- Waiting for your approval before implementing

**3. Implement and complete**

```
Claude: [Implements RateLimiter class]
        [Writes tests]
        [Runs tests - all passing]

        Task 1-1 completed (1.2 hours)

        Next: Task 1-2 - Add Redis backend for rate limit storage
        Continue?

You: Yes

Claude: [Continues with task 1-2]
        ...
```

**What happened:**
- Claude implemented the task according to plan
- Marked task complete with journal entry
- Automatically suggested next task

**4. Complete all tasks**

```
        ...
        Task 2-3 completed (0.8 hours)

        All tasks complete! (7/7)
        Total time: 6.5 hours

        Spec is complete. Move to specs/completed/?

You: Yes

Claude: [Moves spec to specs/completed/rate-limiting-2025-11-22-001.json]
        Spec complete ✅
```

**What happened:**
- All 7 tasks completed
- Total time calculated from individual task durations
- Spec moved to `specs/completed/` folder

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **Spec validation fails** | Run `sdd validate <spec> --fix` to auto-correct issues |
| **Task is blocked** | Blocker details are included in `sdd prepare-task` output (context.dependencies) |
| **Wrong task suggested** | Use `/sdd-begin` and choose "Browse alternatives" |
| **Need to modify spec** | Edit JSON directly, then run `sdd validate <spec>` |
| **Need phase-wide context** | Use `--include-phase-history` or `--include-spec-overview` flags with prepare-task |

---

## Resume After Break

**Goal**: Continue work on an in-progress spec after a break or session restart.

### Step-by-Step

**1. Resume session**

```
You: /sdd-begin

Claude: 📋 Active SDD Work:

        ⚡ rate-limiting-2025-11-22-001 - API Rate Limiting
           Progress: 3/7 tasks (43%)
           🕐 Last accessed: task-1-3 (2 hours ago)

        ⚡ user-auth-2025-11-19-002 - User Authentication Refactor
           Progress: 1/5 tasks (20%)
           🕐 Last accessed: task-1-1 (3 days ago)

        What would you like to do?
        1. Resume last task (task-1-3 from rate-limiting)
        2. Continue with next task
        3. Write new spec
        4. Something else
```

**What happened:**
- `/sdd-begin` scanned `specs/active/` folder
- Found 2 in-progress specs
- Showed progress and last accessed task
- Recommended resuming most recent work

**2. Choose what to work on**

```
You: 2

Claude: Which spec would you like to work on?
        1. rate-limiting-2025-11-22-001 (43% complete)
        2. user-auth-2025-11-19-002 (20% complete)

You: 1

Claude: Resuming rate-limiting-2025-11-22-001

        Next task: Task 1-4 - Add rate limit headers to responses

        Context: Previous tasks implemented RateLimiter middleware,
        Redis backend, and per-endpoint configuration. Now we need
        to add standard rate limit headers to API responses.

        Execution Plan:
        1. Add X-RateLimit-Limit header
        2. Add X-RateLimit-Remaining header
        3. Add X-RateLimit-Reset header
        4. Update middleware to include headers
        5. Add tests for header presence

        Approve this plan?
```

**What happened:**
- Asked which spec to work on (multiple active specs)
- Retrieved rich context automatically (previous tasks, dependencies, phase progress)
- Identified next actionable task
- Created execution plan with full context (no additional commands needed)

**3. Continue implementation**

```
You: Yes

Claude: [Implements headers in middleware]
        [Updates tests]
        [Verifies all tests pass]

        Task 1-4 completed (0.5 hours)
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **No active work found** | Check `specs/pending/` for specs to activate |
| **Wrong spec suggested** | Manually select from list of active specs |
| **Lost context** | Review task journal: previous task summaries provide context |
| **Can't remember what was done** | Use `sdd progress <spec>` to see detailed status |

---

## Generate and Query Documentation

**Goal**: Generate comprehensive documentation and query it for development insights.

### Step-by-Step

**1. Generate documentation with AI**

```
You: Document this codebase with AI enhancement

Claude: [Uses llm-doc-gen skill]
        Analyzing codebase structure...

        Found:
        - 183 Python modules
        - 154 classes
        - 915 functions

        Consulting cursor-agent and gemini for AI insights...
        cursor-agent: Analyzing architecture patterns... (24.3s)
        gemini: Generating component descriptions... (28.7s)

        Generating documentation files...

        ✓ docs/codebase.json (machine-readable)
        ✓ docs/index.md (navigation)
        ✓ docs/project-overview.md
        ✓ docs/architecture.md
        ✓ docs/component-inventory.md

        Documentation complete ✅
```

**What happened:**
- Scanned entire codebase
- Extracted AST, dependencies, complexity metrics
- Consulted multiple AI models for insights
- Generated both machine and human-readable docs

**2. Query for specific information**

```
You: What classes handle authentication?

Claude: [Uses doc-query skill]
        Querying docs/codebase.json...

        Found 3 authentication classes:

        1. AuthManager (src/auth/manager.py:15)
           Purpose: Main authentication orchestration
           Methods: authenticate(), validateToken(), refreshToken()
           Complexity: 8
           Dependencies: TokenValidator, UserRepository, SessionStore

        2. TokenValidator (src/auth/tokens.py:23)
           Purpose: JWT token validation and verification
           Methods: validate(), decode(), verify()
           Complexity: 5
           Dependencies: jose.jwt, cryptography

        3. SessionStore (src/auth/sessions.py:45)
           Purpose: Session persistence and retrieval
           Methods: create(), get(), delete(), cleanup()
           Complexity: 4
           Dependencies: RedisClient
```

**What happened:**
- Queried pre-generated documentation (no source parsing)
- Found classes by name/purpose
- Included complexity and dependency info

**3. Analyze call relationships**

```
You: Show call graph for authenticate()

Claude: [Uses doc-query skill]

        AuthManager.authenticate(email, password)
        ├── UserRepository.findByEmail(email)
        │   └── Database.query()
        ├── PasswordHasher.verify(password, hash)
        │   └── bcrypt.checkpw()
        ├── TokenValidator.validate(token)
        │   ├── decode()
        │   └── verify()
        └── SessionStore.create(user_id)
            └── RedisClient.set(key, value)

        Impact analysis:
        - Direct callers: 5 functions
        - Indirect callers: 12 functions
        - Total functions affected by changes: 17
```

**What happened:**
- Built call graph from documentation data
- Showed complete call tree
- Calculated refactoring impact

**4. Get scoped context for implementation**

```
You: I need to modify the authenticate() function

Claude: Let me get detailed implementation context for you.

        [Runs: sdd doc scope src/auth/manager.py --implement]

        === src/auth/manager.py Implementation Details ===

        AuthManager.authenticate(email: str, password: str) -> Token
        Lines: 42-78

        Implementation pattern:
        - Validates email format (line 45)
        - Fetches user from repository (line 48)
        - Verifies password hash (line 52)
        - Creates new session (line 65)
        - Generates JWT token (line 71)
        - Returns token with metadata (line 76)

        Error handling:
        - Raises InvalidEmailError for malformed emails
        - Raises UserNotFoundError if user doesn't exist
        - Raises InvalidPasswordError for wrong password
        - Raises SessionCreateError if session creation fails

        Dependencies used:
        - UserRepository (injected via constructor)
        - PasswordHasher (imported from auth.crypto)
        - TokenGenerator (imported from auth.tokens)

        Test coverage: 95% (19/20 lines)
        Missing coverage: Error recovery path (line 68)
```

**What happened:**
- Used `--implement` flag for detailed context
- Got full implementation details, patterns, error handling
- Received test coverage information
- Ready to make informed changes

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **Documentation not found** | Run `sdd doc analyze-with-ai .` first |
| **Query returns nothing** | Check search term, try broader keywords |
| **Outdated documentation** | Regenerate: `sdd doc analyze-with-ai . --force` |
| **Missing language support** | Install tree-sitter grammar for your language |

---

## Multi-Model Spec Review

**Goal**: Get feedback from multiple AI models before implementing a spec.

### Step-by-Step

**1. Create spec (as usual)**

```
You: Create a spec for implementing OAuth 2.0 authentication

Claude: [Creates specs/pending/oauth-implementation-001.json]
```

**2. Request multi-model review**

```
You: Review this OAuth spec before I implement it

Claude: [Uses sdd-plan-review skill]
        Consulting cursor-agent and gemini in parallel...

        cursor-agent: Analyzing spec structure... (34.2s)
        gemini: Reviewing task breakdown... (36.8s)

        Both models completed successfully ✅
```

**What happened:**
- Sent spec to both cursor-agent and gemini simultaneously
- Each model analyzed independently
- Results will be synthesized

**3. Review consensus findings**

```
        === Consensus Findings ===

        ✅ Strengths (both models agree):
        - Overall OAuth 2.0 approach follows RFC 6749 correctly
        - Task breakdown is appropriate and atomic
        - Dependencies are well-structured
        - Verification criteria are specific and testable

        ⚠️ Concerns (both models agree):
        - Missing PKCE implementation for mobile clients
        - No task for refresh token rotation
        - Token storage security not explicitly addressed
```

**What happened:**
- Identified findings where both models agreed
- High confidence in consensus items
- These should definitely be addressed

**4. Review model-specific suggestions**

```
        === cursor-agent Suggestions ===

        Additional tasks to consider:
        - Add retry logic for authorization server requests
        - Implement rate limiting on token endpoints
        - Add monitoring/alerting for failed auth attempts
        - Consider implementing device flow for IoT devices

        === gemini Suggestions ===

        Additional tasks to consider:
        - Add session timeout configuration
        - Implement token revocation endpoint
        - Add support for custom scopes
        - Consider SAML integration for enterprise SSO

        Review saved to: specs/.reviews/oauth-implementation-001-review.json
```

**What happened:**
- Each model provided unique suggestions
- Different perspectives reveal blind spots
- Review saved for reference

**5. Apply feedback**

```
You: Apply the consensus findings to the spec

Claude: [Uses sdd-modify skill]
        Analyzing review feedback...

        Proposed modifications:
        1. Add task: Implement PKCE for authorization code flow
        2. Add task: Add refresh token rotation
        3. Add task: Implement secure token storage
        4. Update dependencies for new tasks

        Backup created: specs/.backups/oauth-implementation-001-20251122.json

        Apply these changes?

You: Yes

Claude: Applied 4 modifications ✅
        Spec validated successfully
```

**What happened:**
- sdd-modify parsed review recommendations
- Proposed specific changes to spec
- Created backup before modifying
- Applied changes with validation

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **One model fails** | Review continues with successful model(s) |
| **Conflicting suggestions** | Use your judgment; both perspectives are valid |
| **API rate limits** | Results are cached; subsequent reviews are free |
| **Review takes too long** | Models run in parallel; max time ≈ slowest model |

---

## Verify Implementation Fidelity

**Goal**: Verify that your implementation matches what the specification required.

### Step-by-Step

**1. Complete implementation** (phase or full spec)

```
        [You've completed Phase 1 tasks]

        Task 1-4 completed
        Phase 1: Core OAuth System (4/4 tasks complete)
```

**2. Request fidelity review**

```
You: Did I implement what the OAuth spec said?

Claude: [Uses sdd-fidelity-review skill]
        Reviewing implementation against spec...
        Consulting cursor-agent and gemini...

        cursor-agent: Analyzing code... (42.1s)
        gemini: Comparing to spec... (38.6s)
```

**What happened:**
- Read completed tasks from spec
- Analyzed actual code implementation
- Compared actual vs. specified behavior

**3. Review compliance report**

```
        === Phase 1: Core OAuth System ===

        ✅ task-1-1: Implement authorization endpoint - COMPLIANT
           Code: routes/auth.py:15-68
           - Authorization code flow implemented correctly
           - State parameter validation present
           - Redirect URI validation matches spec

        ✅ task-1-2: Implement token endpoint - COMPLIANT
           Code: routes/token.py:22-95
           - Token exchange implemented per RFC 6749
           - Client authentication working
           - All grant types supported as specified

        ⚠️ task-1-3: Add PKCE support - DEVIATION
           Code: middleware/pkce.py:12-45

           Specified: PKCE required for all public clients
           Implemented: PKCE optional, defaults to disabled

           Impact: MEDIUM
           Security implication: Public clients not protected by default

           Recommendation: Change default to enabled, or update spec
                          to document optional PKCE

        ✅ task-1-4: Implement token storage - COMPLIANT
           Code: storage/tokens.py:8-42
           - Encrypted storage as specified
           - Automatic cleanup implemented
           - Redis backend matches spec
```

**What happened:**
- Analyzed each completed task
- Compared code to spec requirements
- Identified compliant and deviated implementations
- Assessed impact of deviations

**4. Review summary and decide**

```
        === Summary ===

        Compliant: 9/10 tasks (90%)
        Deviations: 1/10 tasks (10%)

        Overall: Implementation is mostly compliant
        Action needed: 1 medium-impact deviation requires decision

        What would you like to do?
        1. Update code to match spec (make PKCE required)
        2. Update spec to document current behavior (PKCE optional)
        3. Review details and decide later

You: 1

Claude: I'll update the code to make PKCE required by default.

        [Modifies middleware/pkce.py]
        [Updates tests]
        [Verifies implementation]

        Updated! PKCE is now required for all public clients.
        Deviation resolved ✅
```

**What happened:**
- Presented summary and options
- You chose to fix code to match spec
- Implementation updated
- Fidelity restored

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **Can't find implementation** | Ensure file paths in tasks are accurate |
| **False deviations reported** | AI may misinterpret; review manually and decide |
| **Review scope too broad** | Review by phase: `Review phase-1 in <spec>` |
| **Missing code context** | Regenerate docs: `sdd doc analyze-with-ai .` |

---

## Debug Test Failures

**Goal**: Run tests and get AI-powered debugging assistance for failures.

### Step-by-Step

**1. Run tests with AI debugging**

```
You: Run tests for the OAuth implementation and fix any failures

Claude: [Uses run-tests skill]
        Running pytest tests/oauth/...

        ===================================
        5 passed, 3 failed in 8.42s
        ===================================

        Analyzing failures with gemini...
```

**What happened:**
- Executed test suite
- Captured failures
- Sent failures to AI for analysis

**2. Review failure analysis**

```
        === test_authorization_code_flow FAILED ===

        Error:
        AssertionError: Expected redirect to contain 'code=' parameter
        Actual redirect: http://callback?error=invalid_request

        AI Analysis (gemini):
        Issue: Authorization endpoint rejecting valid requests
        Root cause: Missing 'response_type' validation allows invalid values

        Code location: routes/auth.py:28
        ```python
        if response_type != 'code':  # Bug: should be '==' not '!='
            return error_response('invalid_request')
        ```

        Suggested fix:
        ```python
        if response_type == 'code':
            # handle authorization code flow
        else:
            return error_response('unsupported_response_type')
        ```
```

**What happened:**
- AI analyzed test failure output
- Identified root cause (logic error)
- Pointed to exact code location
- Suggested specific fix

**3. Review more failures**

```
        === test_token_expiry FAILED ===

        Error:
        AssertionError: Token should be expired but is still valid

        AI Analysis (gemini):
        Issue: Token expiry time not properly tested
        Root cause: System clock advancing during test execution

        Suggested fix:
        ```python
        from freezegun import freeze_time

        @freeze_time("2025-11-22 14:00:00")
        def test_token_expiry():
            token = generate_token(expires_in=3600)

            # Advance time by 2 hours
            with freeze_time("2025-11-22 16:00:00"):
                assert is_expired(token) == True
        ```

        Additional: Install freezegun (pip install freezegun)
```

**What happened:**
- AI identified time-dependent test issue
- Suggested using time-mocking library
- Provided complete code example

**4. Apply fixes**

```
        Apply all suggested fixes?
        1. Fix authorization code flow logic error
        2. Add freezegun for token expiry test
        3. [Fix for third failure]

You: Yes

Claude: Applying fixes...

        ✓ Fixed routes/auth.py:28 (logic error)
        ✓ Added freezegun to requirements-dev.txt
        ✓ Updated test_token_expiry with freeze_time
        ✓ [Applied third fix]

        Rerunning tests...

        ===================================
        8 passed in 6.12s
        ===================================

        All tests passing ✅
```

**What happened:**
- Applied all suggested fixes
- Reran tests automatically
- Verified all tests now pass

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **AI suggests wrong fix** | Review suggestion, apply manually if needed |
| **Tests still fail after fix** | Run again with `--debug` for more detail |
| **Can't install suggested package** | Update requirements manually, ask for alternatives |
| **Too many failures** | Fix incrementally: `Run and fix test_oauth_flow` |

---

## Create Pull Request

**Goal**: Create an AI-powered pull request after completing a spec.

### Step-by-Step

**1. Complete all spec tasks**

```
        Task 3-5 completed

        All tasks complete! (15/15)
        Spec: oauth-implementation-001
        Total time: 12.3 hours
```

**2. Move spec to completed**

```
You: Move OAuth spec to completed

Claude: [Uses sdd-update skill]
        Moved to specs/completed/oauth-implementation-001.json ✅
```

**3. Create pull request**

```
You: Create a pull request for the OAuth implementation

Claude: [Uses sdd-pr skill]
        Analyzing spec metadata...
        Reviewing git commits...
        Reading journal entries...

        Found 23 commits for this spec
        Analyzed 15 tasks across 3 phases
        Extracted implementation details from journals

        Generating PR description...

        === Pull Request Preview ===

        Title: Implement OAuth 2.0 Authentication System

        Summary:
        Implements complete OAuth 2.0 authorization server following
        RFC 6749 specification with PKCE extension for public clients.

        Changes:
        - ✅ Authorization and token endpoints
        - ✅ PKCE support for public clients
        - ✅ Refresh token rotation
        - ✅ Secure encrypted token storage
        - ✅ Rate limiting on auth endpoints
        - ✅ Comprehensive test coverage (94%)

        Implementation Details:
        - Phase 1: Core OAuth System (4 tasks, 5.2 hours)
        - Phase 2: Security Enhancements (6 tasks, 4.8 hours)
        - Phase 3: Testing & Documentation (5 tasks, 2.3 hours)

        Testing:
        - 67 new tests added
        - All tests passing
        - Code coverage: 94%

        Files changed:
        - 12 files created
        - 8 files modified
        - ~2,400 lines added

        Create this PR?

You: Yes

Claude: [Pushes commits to remote]
        [Creates PR via gh cli]

        Pull Request created! 🎉
        https://github.com/user/repo/pull/42

        PR #42: Implement OAuth 2.0 Authentication System
```

**What happened:**
- Analyzed spec metadata for context
- Reviewed git history for this spec's work
- Read journal entries for implementation details
- Generated comprehensive PR description
- Created PR with all context

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **Not authorized for gh** | Run `gh auth login` first |
| **No commits found** | Ensure work was committed with task IDs in messages |
| **PR creation fails** | Check branch is pushed to remote |
| **Missing context in PR** | Ensure journal entries are detailed |

---

## Next Steps

Now that you understand common workflows:

- **Learn about skills**: See [Skills Reference](skills-reference.md) for detailed skill documentation
- **Understand concepts**: Review [Core Concepts](core-concepts.md) for underlying principles
- **Configure your setup**: Check [Configuration](configuration.md) for customization options
- **Try the examples**: Walk through [Complete Task Workflow](examples/complete_task_workflow.md)

---

**Related Documentation:**
- [Skills Reference](skills-reference.md) - Detailed skill documentation
- [Core Concepts](core-concepts.md) - Fundamental concepts
- [Configuration](configuration.md) - Setup and configuration
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
