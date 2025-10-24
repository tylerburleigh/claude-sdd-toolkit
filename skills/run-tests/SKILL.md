---
name: run-tests
description: Comprehensive pytest testing and debugging framework. Use when running tests, debugging failures, fixing broken tests, or investigating test errors. Includes systematic investigation workflow with external AI tool consultation and verification strategies.
---

# Pytest Testing and Debugging Skill

## Table of Contents

- [Key Principles](#key-principles)
- [TL;DR: Minimal Workflow](#tldr-minimal-workflow)
- [Quick Start](#quick-start)
- [Choosing Your Workflow Path](#choosing-your-workflow-path)
- [When to Use This Skill](#when-to-use-this-skill)
- [Core Testing Process](#core-testing-process)
  - [Phase 1: Run Tests](#phase-1-run-tests)
  - [Phase 2: Analyze Failures](#phase-2-analyze-failures)
  - [Phase 3: Investigation & Consultation](#phase-3-investigation--consultation)
  - [Phase 4: Develop Fix Strategy](#phase-4-develop-fix-strategy)
  - [Phase 5: Implement & Verify](#phase-5-implement--verify)
- [Appendix A: Special Scenarios](#appendix-a-special-scenarios)
- [External Tool Consultation (Consolidated)](#external-tool-consultation-consolidated)
- [Configuration](#configuration)
- [Helper Scripts](#helper-scripts)
- [Best Practices](#best-practices)
- [Complete Workflow Example](#complete-workflow-example)
- [Success Criteria](#success-criteria)
- [Appendix B: Reference Materials](#appendix-b-reference-materials)
  - [Detailed Tool Routing Matrix](#detailed-tool-routing-matrix)
  - [Advanced Techniques](#advanced-techniques)
  - [Troubleshooting Guide](#troubleshooting-guide)
  - [Integration with Development Workflow](#integration-with-development-workflow)
- [Key Reminders](#key-reminders)
- [Final Notes](#final-notes)

---

## Key Principles

> **Core Philosophy:**
> 1. **Investigation-First** - Always do your own analysis before consulting tools
> 2. **Hypothesis-Driven** - Form theories, then validate (don't ask blind questions)
> 3. **Tools Are Read-Only** - External agents suggest, YOU implement all fixes
> 4. **Tiered Approach** - Match workflow complexity to problem complexity
> 5. **Mandatory Consultation for Failures** - If tests failed and tools exist, consult them
> 6. **Skip When Passing** - Tests pass or verification succeeds? No consultation needed

---

## TL;DR: Minimal Workflow

**New to this skill? Start here:**

```
┌─ Tests failing? ────────────────────────────────────────┐
│                                                          │
│  1. Run:     sdd test run --debug                      │
│  2. Simple?  Fix directly → sdd test run {test}        │
│  3. Complex? sdd test consult {type} --error "..."     │
│              --hypothesis "your theory"                  │
│  4. Verify:  sdd test run (full suite)                 │
│                                                          │
│  Tests passed? → Done! No consultation needed.          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Quick Decision Guide:**
- ✅ **Tests pass?** → Done
- ❌ **Obvious typo/simple fix?** → Fix → Verify
- ❌ **Unclear issue?** → Investigate → Consult → Fix → Verify

See ["Choosing Your Workflow Path"](#choosing-your-workflow-path) for detailed guidance on Fast/Standard/Deep paths.

---

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd test CLI is installed and accessible
sdd test --help
```

**Expected output**: Help text showing available commands (run, consult, check-tools, discover, etc.)

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd test` CLI wrapper commands (e.g., `sdd test run`, `sdd test consult`, `sdd test check-tools`)
- ❌ **DO NOT**: Execute Python scripts directly (e.g., `python run_tests.py`, `bash pytest`, direct Python script execution)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. Direct script execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

---

## Quick Start

**Command Formatting Guidelines:**
- **Always use single-line bash commands** (no backslash continuations)
- This ensures compatibility with permission rules and automation
- Long commands are acceptable - parseability matters more than formatting

**Essential 5-Step Workflow:**

> **Note:** This is the **fast iteration path** for familiar codebases. For comprehensive analysis of unknown codebases, see the full 6-phase workflow below.

1. **Run tests** → Capture complete output (optional: discover structure first if unfamiliar)
```bash
sdd test discover --summary  # Optional: understand test structure first
sdd test run --debug  # or use preset that fits your need
```

2. **Investigate** → Analyze errors, examine code, form hypothesis
```bash
sdd test discover --detailed  # understand test structure
```

3. **Check tools** → See what's available
```bash
sdd test check-tools  # shows available external tools + routing
```

4. **Consult** → MANDATORY for test failures if external tools exist (gemini/codex/cursor-agent)
```bash
sdd test consult assertion  --error "assert x == 5"  --hypothesis "Your theory here"
```
**Skip consultation when:** Tests pass, verification runs succeed, or no actionable failure exists.

5. **Fix & Verify** → Implement based on synthesized insights, test again

---

## Choosing Your Workflow Path

Select the appropriate workflow based on your confidence level and the complexity of the issue:

### Fast Path (Trivial Fixes)
**Use when:** High confidence, single-line fix, obvious error (typo, missing import, simple assertion)

**Workflow:**
```
Run → Read error → Fix → Verify
```

**Example:** Test expects `5`, code returns `4` → Simple logic error → Fix directly → Rerun test

**Skip:** Discovery, consultation (unless fix doesn't work)

---

### Standard Path (Typical Debugging)
**Use when:** Moderate complexity, need hypothesis validation, 1-3 file scope

**Workflow:**
```
Run → Investigate → Form hypothesis → Consult (if tools available & test failed) → Fix → Verify
```

**Example:** AttributeError in test → Investigate code → Hypothesis: missing return → Consult Codex/Gemini → Fix → Rerun

**Include:** Investigation, mandatory consultation if tools exist and tests failed

---

### Deep Path (Complex/Multi-file)
**Use when:** Unclear root cause, multi-file impact, framework/architectural issues

**Workflow:**
```
Discover → Run → Investigate → Multi-agent consult → Strategize → Fix → Full suite verification
```

**Example:** Fixture not found, affects 12 tests → Discover conftest structure → Consult multi-agent → Move conftest → Verify all

**Include:** Full discovery, multi-agent consultation, comprehensive verification

---

### Decision Tree

```
Tests passed?
├─ Yes → Done (skip consultation)
└─ No → Tests failed
    ├─ Obvious fix (typo, simple)?
    │  └─ Yes → FAST PATH
    └─ No → Complex
        ├─ 1-3 files, moderate confidence?
        │  └─ Yes → STANDARD PATH (consult if tools exist)
        └─ No → Multi-file or uncertain
           └─ DEEP PATH (multi-agent recommended)
```

---

## When to Use This Skill

- Running tests or test suites
- Debugging test failures
- Fixing broken tests
- Investigating test errors or assertion failures
- Adding or modifying tests
- Setting up test infrastructure

---

## Core Testing Process

> **Workflow Selection:** Use Quick Start (above) for fast iteration on familiar codebases. Use this detailed 6-phase workflow for comprehensive analysis of unfamiliar codebases or complex issues.

### Phase 1: Run Tests

**1. Discover test structure** *(Optional: skip if already familiar with test organization)*
```bash
# Use the helper script
sdd test discover --summary

# Or manually
find . -name "test_*.py" -o -name "*_test.py"
ls -la tests/
```

**2. Run tests with appropriate settings**

Use the `sdd test` commands for common scenarios:

```bash
# Quick run - stop on first failure
sdd test run --quick

# Debug mode - verbose with locals and print statements
sdd test run --debug

# Run specific test
sdd test run tests/test_module.py::test_function

# Coverage report
sdd test run --coverage

# List all presets
sdd test run --list
```

Or run pytest directly with custom flags:
```bash
pytest -v                    # Verbose
pytest -vv -l -s            # Very verbose, show locals, show prints
pytest -x                    # Stop on first failure
pytest -k "test_user"       # Run tests matching pattern
pytest --fixtures           # Show available fixtures
pytest --markers            # Show available markers
```

**3. Capture complete output**

For small test suites, review output directly. For large suites with extensive failures:

```bash
# Save output to timestamped file for later analysis
sdd test run --debug | tee /tmp/test-run-$(date +%Y%m%d-%H%M%S).log

# Or redirect entirely
sdd test run --debug > /tmp/test-output.log 2>&1
```

**What to capture:**
- Test discovery results
- Pass/fail status for each test
- Full stack traces
- Assertion details
- Any print/log output

**Output management:** For very large failure sets, saving to `/tmp/test-run-{timestamp}.log` prevents terminal clutter while preserving full details for investigation.

### Phase 2: Analyze Failures

**1. Categorize the failure**
- **Assertion** - Expected vs actual mismatch
- **Exception** - Runtime errors (AttributeError, KeyError, TypeError, etc.)
- **Import** - Missing dependencies or module issues
- **Fixture** - Fixture or configuration issues (conftest, scopes)
- **Timeout** - Performance or hanging issues
- **Flaky** - Non-deterministic failures

**2. Extract key information**
For each failure:
- Test file and function name
- Line number where failure occurred
- Error type and message
- Full stack trace
- Relevant code context
- Input data that triggered failure

**3. Examine the code**
- View the failing test (Read tool)
- View the implementation being tested (Read tool)
- Understand what the test verifies
- Identify expected vs actual behavior

### Phase 3: Investigation & Consultation

**CRITICAL WORKFLOW:**
```
Your Investigation → Check Tool Availability → Consult External Tools (if any) → Synthesize → Implement
```

**Step 1: Your Investigation** (ALWAYS DO THIS FIRST)

Before consulting any external tools, do your own analysis:

- Read the full error message and stack trace
- Identify the exact line where failure occurred
- Understand what the test is trying to verify
- Compare expected vs actual values
- Review the implementation code being tested
- **Form your hypothesis** - What do you think is causing the failure?
- Gather context (view related tests, check for similar patterns)

**Step 2: Check Tool Availability**

```bash
# Use the helper script
sdd test check-tools
```

**Decision:**
- **If ANY tool is available AND tests failed** → Proceed to Step 3 (mandatory consultation for failures)
- **If NO tools are available** → Skip to Phase 4
- **If tests passed or verification succeeded** → Skip to Phase 5 (no consultation needed)

**Step 3: Consult External Tools** (MANDATORY for test failures if any tools are available)

**IMPORTANT:** All external tools operate in **read-only mode**. They provide analysis, validation, and suggestions. YOU (the main agent) implement all fixes.

**When to skip consultation:**
- Tests all passed
- Verification/smoke tests succeeded
- Re-running tests after successful fix (confirmation only)

**Using the Helper Script (Recommended):**

```bash
# Auto-routes to best tool based on failure type
sdd test consult assertion  --error "Full error message here"  --hypothesis "Your theory about the cause"  --test-code tests/test_file.py  --impl-code src/module.py

# See routing matrix
sdd test consult --list-routing

# Manual tool selection
sdd test consult --tool gemini  --prompt "Your custom question..."
```

**Tool Selection Guide:**

| Use This Tool | When You Need | Example |
|---------------|---------------|---------|
| **Gemini** | Hypothesis validation, framework explanations, strategic guidance, "why?" questions | "Why is this fixture not found?" |
| **Codex** | Code-level review, specific fix suggestions, "what's wrong with this code?" | "Review this code and suggest fixes" |
| **Cursor** | Repo-wide discovery, finding patterns, "where else does this occur?" | "Find all call sites" |

**Quick Routing by Failure Type:**

```bash
# Get routing suggestion for your failure type
sdd test check-tools --route assertion
sdd test check-tools --route fixture
sdd test check-tools --route exception
```

See [Reference: Detailed Tool Routing Matrix](#reference-detailed-tool-routing-matrix) for comprehensive guidance.

**Manual Consultation (if not using helper script):**

```bash
# Gemini - Strategic/conceptual validation
gemini -m gemini-2.5-pro -p "I'm getting this pytest error: [error]

My investigation: [what you found]
My hypothesis: [your theory]
My proposed fix: [your plan]

Questions:
1. Is my hypothesis correct?
2. What am I missing?
3. Is my proposed fix appropriate?"

# Codex - Code-level review
codex exec --model gpt-5-codex --skip-git-repo-check "Review this failing test:

TEST CODE:
\`\`\`python
[test code]
\`\`\`

ERROR: [error message]
MY HYPOTHESIS: [theory]

What specific code changes would fix this?"

# Cursor - Pattern discovery
cursor-agent -p --model gpt-5-codex "Find all occurrences of [pattern] in the codebase.
Context: [why you need this]
What's the full impact scope?"
```

**When to Use Multiple Tools:**
- High-risk fix (affects critical functionality)
- Uncertain between multiple approaches
- Scope is unclear (need discovery before validation)
- Complex issue requiring both strategic and tactical analysis
- First tool's answer raises new questions

**Common Multi-Tool Patterns:**
- `Cursor` (find all instances) → `Gemini` (strategize fix)
- `Gemini` (validate reasoning) → `Codex` (validate specific code)
- `Codex` (review code) → `Gemini` (validate approach & risks)

**Step 4: Optional Web Search**

Only use when:
- External tools don't have sufficient information
- Need to verify latest documentation
- Looking for known bugs in specific pytest versions
- Need community solutions for edge cases
- External tools suggest checking specific resources

### Phase 4: Develop Fix Strategy

**1. Synthesize findings**
Combine insights from:
- Your initial investigation and hypothesis
- External AI tool recommendations (if any were available)
- Any additional research (web search, docs)

**2. Formulate approach**
- What is the confirmed root cause?
- Which fix approach makes the most sense?
- If AI tools were consulted: Do their suggestions align with your analysis?
- If multiple tools consulted: Do they agree? If not, which is better and why?

**3. Plan implementation**
- Identify exactly which files to edit
- Start with simplest fix
- Consider potential side effects
- Plan to test incrementally

### Phase 5: Implement & Verify

**1. Make targeted changes**
```python
# Example: Better assertion message
# Before:
assert result == expected

# After:
assert result == expected, f"Expected {expected}, got {result}"
```

**2. Re-run tests**
```bash
# Run the specific fixed test
sdd test run tests/test_module.py::test_function

# If passing, run full suite
sdd test run
```

**3. Verify no regressions**
```bash
# Run related tests
pytest tests/test_module.py -v

# Run full suite
pytest
```

**4. Document the fix**
Add comments explaining:
- What was wrong
- Why the fix works
- Any assumptions or limitations

---

## Appendix A: Special Scenarios

This appendix covers edge cases and complex situations that don't fit the standard workflow.

### Verification Runs (Confirming Refactors)

**When running tests to verify refactoring or confirm changes:**

```bash
# Run full suite to verify refactor didn't break anything
sdd test run

# If all tests pass:
# ✓ Done! No consultation needed - tests confirm changes are safe

# If tests fail:
# → Follow standard debugging workflow (investigate → consult → fix)
```

**Key point:** Passing verification runs require no consultation. Only investigate failures.

### Multiple Failing Tests

1. Group by error type
2. Fix one group at a time
3. Look for common root causes
4. Consider whether tests need updating vs code needs fixing

### Flaky Tests
```bash
# Run test multiple times
pytest tests/test_flaky.py --count=10

# Run with random order
pytest --random-order
```

### Integration Test Failures
1. Check external dependencies
2. Verify test environment setup
3. Check database state
4. Review configuration
5. Check network connectivity

### Fixture Issues
```bash
# Show fixture setup and teardown
pytest --setup-show tests/test_module.py

# List available fixtures
pytest --fixtures
```

---

## External Tool Consultation (Consolidated)

### Multi-Agent Consultation (Enhanced Analysis)

For comprehensive analysis, you can now consult multiple AI agents in parallel and get synthesized insights.

**When to Use Multi-Agent Mode:**
- High-stakes fixes affecting critical functionality
- Complex issues with unclear root cause
- When you need validation from multiple perspectives
- Uncertain between multiple fix approaches
- First consultation raises additional questions

**How to Use:**
```bash
# Auto-selects best two agents
sdd test consult assertion  --error "Full error message"  --hypothesis "Your theory"  --multi-agent

# Select specific agent pair
sdd test consult exception  --error "AttributeError: ..."  --hypothesis "Missing return"  --multi-agent  --pair code-focus
```

**What You Get:**
```
┌─ Multi-Agent Analysis ─────────────────────┐
│ CONSULTED AGENTS:
│ ✓ gemini (2.3s)
│ ✓ cursor-agent (1.8s)
│
│ CONSENSUS (Agents agree):
│ • Both identify: missing return
│ • Both reference files: src/user.py
│
│ GEMINI INSIGHTS:
│ • Function creates User but doesn't return it
│ • This pattern appears in 3 other files
│
│ CURSOR-AGENT INSIGHTS:
│ • Found 5 call sites expecting return value
│ • All tests follow same pattern
│
│ SYNTHESIS:
│ Consulted 2 agents: gemini, cursor-agent
│
│ RECOMMENDATIONS:
│ → High confidence: 2 consensus point(s) found
│
└────────────────────────────────────────────┘

[Followed by detailed responses from each agent]
```

**Benefits:**
- **Higher Confidence**: Multiple perspectives validate findings
- **Better Coverage**: Each agent contributes unique insights
- **Risk Reduction**: Divergent views expose alternative approaches
- **Comprehensive**: Synthesis combines best of both analyses

### Core Principles

> **See "Key Principles" section at top for full philosophy. Key points:**

1. **Investigation-First Workflow**
   - Do your own analysis first
   - Form hypothesis before consulting
   - Share your thinking with tools
   - Get validation, not just answers

2. **Mandatory for Test Failures When Available**
   - ALWAYS consult if any external tool exists AND tests failed
   - Skip consultation when: tests pass, verification succeeds, or post-fix confirmation
   - ONLY skip if: no tools installed OR no actionable failure exists
   - Use helper script for easy routing
   - Learn from tool insights

### Timeout and Retry Behavior

**Consultation Timeouts:**
- External tool consultations have a 90-second timeout
- If a tool times out, you'll see a warning with retry suggestions
- Timeouts are configurable via `config.yaml` (consultation.timeout_seconds)

**When Tools Time Out:**
1. Check tool availability: `sdd test check-tools`
2. Try with a simpler/shorter prompt
3. Consider using a different tool from the routing matrix
4. Check if the tool process is hung (ps aux | grep <tool>)

**Common Timeout Causes:**
- Very large codebases or prompts
- Network issues (if tool uses cloud APIs)
- Tool process hung or unresponsive
- Insufficient system resources

### Tool Availability Fallbacks

**What if the recommended tool isn't installed?**

| Recommended | If Unavailable, Use | How to Compensate |
|-------------|---------------------|-------------------|
| **Gemini** | Codex or Cursor | Ask "why" questions with extra context; use web search for framework concepts |
| **Codex** | Gemini | Ask for very specific code examples and implementation details |
| **Cursor** | Manual Grep + Gemini | Use Grep to find patterns, ask Gemini to analyze scope |

```bash
# Check what's available and get fallback suggestions
sdd test check-tools
```

### When to Escalate to Additional Tools

Move to additional/fallback tool when:

1. **Answer is unclear** - Vague suggestions, doesn't address your question
2. **Answer contradicts your analysis** - Need second opinion
3. **Answer raises new questions** - Identifies issues you hadn't considered
4. **Partial answer** - Addresses some aspects but not others
5. **Implementation uncertain** - Validates hypothesis but unclear how to implement
6. **High-stakes scenario** - Critical functionality, want comprehensive validation

**Escalation Examples:**
- Codex: "Add return statement" → Gemini: Validate no side effects
- Gemini: "Fixture scope issue" → Cursor: Find all fixture usages
- Cursor: "Pattern in 15 files" → Gemini: Strategy for fixing all

### When Tools Disagree

**Handling Conflicting Advice:**

If two tools give different recommendations:

1. **Compare reasoning** - Which explanation is more thorough? Which addresses edge cases?
2. **Check scope** - Does one tool consider broader impact than the other?
3. **Apply critical thinking** - Which aligns better with your investigation?
4. **Try simplest first** - If uncertain, implement the less invasive fix first
5. **Document uncertainty** - Note in code comments if multiple approaches were considered

**Example:**
```
Gemini: "Change fixture scope to 'session'"
Codex: "Move conftest.py to tests/unit/"

Analysis: Both solve "fixture not found" but differently.
Gemini's fix = global change (affects all tests)
Codex's fix = local change (tests/unit only)

Decision: Try Codex's approach first (smaller scope, lower risk)
If that fails, consider Gemini's session scope change
```

**If Helper Script Fails:**

```bash
# Helper script error? Fall back to manual consultation
# Example: If the sdd test consult command fails

# Manual fallback:
gemini -m gemini-2.5-pro -p "Your question here..."
# or
codex exec --model gpt-5-codex --skip-git-repo-check "Your question..."
```

**If Tool Times Out:**

1. **Simplify prompt** - Remove large code blocks, keep error message only
2. **Try different tool** - Use routing matrix to pick alternative
3. **Check tool status** - `ps aux | grep gemini` (is it hung?)
4. **Increase timeout** - Edit config.yaml `consultation.timeout_seconds` if needed

### Effective Prompting Principles

1. **Always share your hypothesis** - Ask "is my theory correct?" not "what's wrong?"
2. **Provide complete context** - Error messages, code, stack traces
3. **Include what you've tried** - Show your investigation work
4. **Ask for explanations** - Understand "why", not just "how to fix"
5. **Be specific** - State exactly what you need (validation, suggestions, discovery)

## Helper Scripts

This skill includes a unified CLI tool (`sdd test`) with modular operations:

### Main CLI: `sdd test`

Unified command-line interface for all testing and debugging operations.

**Global Options:**
- `--no-color` - Disable colored output
- `--verbose`, `-v` - Show detailed output
- `--quiet`, `-q` - Minimal output (errors only)
- `--json` - Output results in JSON format (where applicable)

### check-tools subcommand

Check availability of external CLI tools and get routing suggestions.

```bash
# Basic check
sdd test check-tools

# Get routing for specific failure type
sdd test check-tools --route assertion
sdd test check-tools --route fixture

# JSON output
sdd test check-tools --json
```

### run subcommand

Smart pytest runner with presets for common scenarios.

```bash
# List all presets
sdd test run --list

# Quick run (stop on first failure)
sdd test run --quick

# Debug mode (verbose + locals + prints)
sdd test run --debug

# Coverage report
sdd test run --coverage

# Run specific test
sdd test run tests/test_file.py::test_name

# Skip slow tests
sdd test run --fast

# Run in parallel
sdd test run --parallel
```

### consult subcommand

External tool consultation wrapper with auto-routing and prompt formatting.

```bash
# Auto-route based on failure type
sdd test consult assertion  --error "Full error message"  --hypothesis "Your theory"

# Include code
sdd test consult exception  --error "AttributeError: ..."  --hypothesis "Missing attribute"  --test-code tests/test_file.py  --impl-code src/module.py

# Manual tool selection
sdd test consult --tool gemini  --prompt "Custom question..."

# Show routing matrix
sdd test consult --list-routing

# Dry run (see what would be executed)
sdd test consult fixture --error "..." --hypothesis "..." --dry-run
```

### discover subcommand

Test structure analyzer and discovery tool.

```bash
# Quick summary
sdd test discover --summary

# Directory tree
sdd test discover --tree

# All fixtures
sdd test discover --fixtures

# All markers
sdd test discover --markers

# Detailed analysis
sdd test discover --detailed

# Analyze specific directory
sdd test discover tests/unit --summary
```

---

## Best Practices

### Running Tests

1. Start with verbose mode (`-v`) for better visibility
2. Use `-x` to stop on first failure when debugging
3. Use helper scripts for common scenarios
4. Run specific tests to iterate faster
5. Use markers to organize test runs:
   ```python
   @pytest.mark.slow
   @pytest.mark.integration
   @pytest.mark.unit
   ```

### Debugging Strategy

1. Read error messages carefully - they often contain the answer
2. Check the last line of stack trace first - that's where it failed
3. Use `-l` flag to see local variables
4. Use `pytest.set_trace()` for interactive debugging
5. Add temporary print statements for quick debugging
6. Use logging for permanent debug output

### Research Workflow

1. **Do initial investigation first** - Understand error, form hypothesis
2. **Check tool availability** - Run `sdd test check-tools`
3. **Consult available tools** - Mandatory if tests failed and any tools exist
4. **Share your hypothesis** - Don't ask blind questions
5. **Get analysis/suggestions** - Tools provide recommendations
6. **You implement** - Main agent applies fixes
7. **Web search only if needed** - Supplement tool consultation
8. **Validate before implementing** - Understand the "why"
9. **Skip consultation when** - Tests pass, verification succeeds, or post-fix confirmation

### External Tool Usage

**FOR TEST FAILURES:** Investigate → Check availability → Consult (if tests failed & tools available) → Synthesize → Implement

**FOR VERIFICATION RUNS:** Run tests → If passed, done. If failed, follow failure workflow above.

**Tool selection by need:**
- Need to validate hypothesis? → **Gemini**
- Need code-level review? → **Codex**
- Need to find patterns? → **Cursor**
- Want multiple perspectives? → **Multiple tools**

**After consultation:**
- Synthesize insights from tools + your analysis
- Choose best approach with evidence
- YOU implement using Edit/Write tools
- Test thoroughly

### Common Patterns and Solutions

**Pattern 1: Assertion with message**
```python
assert result == expected, f"Expected {expected}, got {result}"
```

**Pattern 2: Flaky test - order independent**
```python
assert set(items) == {1, 2, 3}  # Instead of list comparison
```

**Pattern 3: Fixture scope**
```python
@pytest.fixture(scope="class")  # Reuse across test class
def database():
    db = create_db()
    yield db
    db.close()
```

**Pattern 4: Exception testing**
```python
def test_invalid_input():
    with pytest.raises(ValueError, match="Invalid email"):
        create_user("not-an-email")
```

**Pattern 5: Parametrized tests**
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(input, expected):
    assert uppercase(input) == expected
```

---

## Complete Workflow Example

### Single-Agent Example

```bash
# 1. Run tests
sdd test run --debug

# Output shows: tests/test_user.py::test_user_creation FAILED
# Error: AttributeError: 'NoneType' object has no attribute 'email'

# 2. Examine test
cat tests/test_user.py
# def test_user_creation():
#     user = create_user('test@example.com')
#     assert user.email == 'test@example.com'

# 3. Initial investigation
cat src/user.py
# def create_user(email):
#     user = User(email=email)
#     user.save()
#     # No return statement!

# Hypothesis: create_user() returns None instead of User object

# 4. Check which tools are available
sdd test check-tools
# Output: Available: gemini

# 5. MANDATORY: Consult available tool
sdd test consult exception  --error "AttributeError: 'NoneType' object has no attribute 'email'"  --hypothesis "Function missing return statement"  --test-code tests/test_user.py  --impl-code src/user.py

# Gemini responds: "Yes, exactly! Add 'return user' at the end."

# 6. Synthesize: My analysis + Gemini validation both agree
# Decision: Add return statement

# 7. Implement fix (using Edit tool)
# Edit src/user.py to add: return user

# 8. Re-run specific test
sdd test run tests/test_user.py::test_user_creation
# Test passes! ✓

# 9. Run full suite
sdd test run
# All tests pass! ✓

# 10. Document in commit
git commit -m "Fix: Add missing return statement in create_user()

Function was creating User object but not returning it. Issue
identified through code analysis and validated by Gemini CLI."
```

### Multi-Agent Example (For Complex Issues)

```bash
# 1. Run tests - multiple failures
sdd test run --debug

# Output shows: 3 tests failing in tests/test_auth.py
# Error: fixture 'db_session' not found

# 2. Initial investigation
# Found: conftest.py has @pytest.fixture but tests aren't finding it
# Hypothesis: Fixture scope or location issue

# 3. Check available tools
sdd test check-tools
# Output: Available: gemini, cursor-agent

# 4. Use MULTI-AGENT for comprehensive analysis
sdd test consult fixture  --error "fixture 'db_session' not found"  --hypothesis "Fixture defined in wrong location or scope issue"  --test-code tests/test_auth.py  --impl-code tests/conftest.py  --multi-agent

# Output:
# ┌─ Multi-Agent Analysis ─────────────────────┐
# │ CONSULTED AGENTS:
# │ ✓ gemini (1.9s)
# │ ✓ cursor-agent (2.1s)
# │
# │ CONSENSUS (Agents agree):
# │ • Both identify: fixture scope
# │ • Both reference files: tests/conftest.py
# │
# │ GEMINI INSIGHTS:
# │ • conftest.py is in tests/ but tests are in tests/unit/
# │ • Pytest looks for conftest.py in test directory hierarchy
# │
# │ CURSOR-AGENT INSIGHTS:
# │ • Found 12 tests using db_session across 3 files
# │ • All test files are in tests/unit/ subdirectory
# │
# │ SYNTHESIS:
# │ Consulted 2 agents: gemini, cursor-agent
# │
# │ RECOMMENDATIONS:
# │ → High confidence: 2 consensus point(s) found
# │
# └────────────────────────────────────────────┘

# 5. Synthesize insights from both agents
# Consensus: conftest.py needs to be in tests/unit/
# Gemini: Explains pytest's conftest discovery
# Cursor: Shows scope (12 tests affected)
# Decision: Move conftest.py to tests/unit/

# 6. Implement fix
mv tests/conftest.py tests/unit/conftest.py

# 7. Re-run tests
sdd test run tests/test_auth.py
# All 3 tests pass! ✓

# 8. Run full suite to check for regressions
sdd test run
# All tests pass! ✓
```

---

## Success Criteria

A test debugging session is successful when:
- ✓ All tests pass
- ✓ No new tests are broken
- ✓ Root cause is understood
- ✓ Fix is documented
- ✓ Learning is captured for future reference
- ✓ Code is cleaner/clearer than before (when appropriate)

---

## Appendix B: Reference Materials

This appendix contains detailed reference information for advanced usage, troubleshooting, and integration patterns.

---

## Detailed Tool Routing Matrix

**Notation:**
- **(if insufficient → Secondary)** = Start with Primary; escalate if answer unclear/incomplete
- **Primary + Secondary** = Use both together (complementary strengths)
- **Primary → Secondary** = Sequential: always use Primary first, then Secondary builds on it

| Failure Class | What to Validate | Best Tool(s) | Why |
|---------------|------------------|--------------|-----|
| **Assertion mismatch** | "Is my hypothesis about this logic bug correct?" | **Codex** (if insufficient → Gemini) | Code-level bug analysis; escalate for conceptual validation |
| **Exceptions** | "Which line is wrong and why?" | **Codex** (if insufficient → Gemini) | Precise code review; escalate for deeper checks |
| **Import/packaging errors** | "What's the structural issue?" | **Gemini** → **Cursor** | Sequential: Gemini explains, Cursor finds affected sites |
| **Fixture issues** | "How does pytest scoping work here?" | **Gemini** (if insufficient → Cursor) | Framework expertise; escalate to discover usage patterns |
| **Timeouts/performance** | "What's the bottleneck?" | **Gemini + Cursor** | Both: Gemini for strategy, Cursor for I/O patterns |
| **Flaky tests** | "What causes non-determinism?" | **Gemini + Cursor** | Both: Gemini diagnoses, Cursor finds state dependencies |
| **Multi-file consistency** | "Are there other call sites?" | **Cursor** → **Gemini** | Sequential: Cursor discovers, Gemini synthesizes strategy |
| **Unclear error messages** | "What does this mean?" | **Gemini** (if insufficient → web) | Explanation first; web search if still unclear |
| **Proposed fix validation** | "Is my fix correct and complete?" | **Gemini + Codex** | Both: Gemini strategic, Codex code-specific |

**Decision Gates:**

**Scope-based:**
- Single file, clear bug → **Codex**
- Multi-file, structural → **Gemini** + **Cursor**
- Framework/pytest internals → **Gemini**

**Query type:**
- "Why is this happening?" → **Gemini**
- "Is this code wrong?" → **Codex**
- "Where else does this occur?" → **Cursor**
- "What should I do?" → **Gemini** + **Codex**

**Complexity:**
- Simple logic error → **Codex** quick validation
- Complex interaction → **Gemini** multi-step analysis
- Unknown scope → **Cursor** for discovery first

---

## Advanced Techniques

### Using pytest-pdb for debugging
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Custom markers for test organization
```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "unit: marks unit tests")
```

### Fixtures for test data
```python
@pytest.fixture
def sample_user_data():
    """Provides sample user data for tests"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "age": 30
    }

def test_user_creation(sample_user_data):
    user = create_user(**sample_user_data)
    assert user.email == sample_user_data["email"]
```

### Mocking external services
```python
from unittest.mock import Mock, patch

def test_api_call():
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        result = fetch_data()
        assert result["status"] == "ok"
        mock_get.assert_called_once()
```

---

## Troubleshooting Guide

### "Tool gives contradictory advice"
1. Compare reasoning quality - which is more thorough?
2. Check scope of impact - which considers broader effects?
3. Try simplest/least invasive fix first
4. Document alternative approaches in code comments
5. See "When Tools Disagree" section for detailed guidance

### "Fixture not found"
1. Check fixture is defined in conftest.py or same file
2. Verify fixture name matches exactly
3. Check fixture scope is appropriate
4. Ensure conftest.py is in correct directory

### "Import error"
1. Check PYTHONPATH includes src directory
2. Verify `__init__.py` files exist
3. Check for circular imports
4. Verify package is installed in development mode

### "Tests pass locally but fail in CI"
1. Check for hardcoded paths
2. Verify all dependencies in requirements
3. Check for timezone issues
4. Look for race conditions
5. Check file system differences

### "Test is too slow"
1. Use fixtures with appropriate scope
2. Mock external services
3. Use in-memory databases
4. Parallelize: `sdd test run --parallel`

---

## Integration with Development Workflow

### Test Development Cycle (TDD)
1. Write test first
2. Run test - expect failure
3. Write minimal code to pass
4. Run test - should pass
5. Refactor if needed
6. Run test - should still pass

---

## Key Reminders

1. **Always run tests before making changes** - Establish baseline
2. **Do your own investigation first** - Understand error, form hypothesis
3. **Check tool availability** - `sdd test check-tools`
4. **MANDATORY: Consult available AI tools for failures** - Use at least one if tests failed and tools exist
5. **Share your hypothesis** - Get validation, not just answers
6. **Tools are read-only** - They suggest, YOU implement
7. **Use helper scripts** - Simplify common operations
8. **Skip consultation when** - Tests pass, verification succeeds, no tools installed, or post-fix confirmation
9. **Make small, focused changes** - Easier to identify what worked
10. **Verify comprehensively** - Run full suite, not just one test
11. **Document complex fixes** - Help future developers
12. **Learn from insights** - Understand why, not just how

---

## Final Notes

Testing is iterative and investigative. Use this skill as a framework, not a rigid checklist. Adapt based on:
- Complexity of the codebase
- Your familiarity with the code
- Time constraints
- Availability of external tools
- Nature of the failures

**Remember:** Every test failure is an opportunity to improve code quality and your understanding of the system.

The helper scripts are designed to streamline common operations. Use them to focus on problem-solving rather than command syntax.
