---
name: sdd-plan-review
description: Multi-model specification review using direct AI CLI tools. Calls gemini, codex, or cursor-agent CLIs in parallel to evaluate specs from multiple perspectives (architecture, security, feasibility). Provides actionable feedback to improve specification quality before implementation.
---

# Spec-Driven Development: Plan Review Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-toolkit:sdd-plan)** - Creates specifications and task hierarchies
- **Skill(sdd-toolkit:sdd-plan-review)** (this skill) - Reviews specs with multi-model collaboration
- **Skill(sdd-toolkit:sdd-next)** - Identifies next tasks and creates execution plans
- **Skill(sdd-toolkit:sdd-update)** - Tracks progress and maintains documentation

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│            Spec-Driven Development Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌─────────┐│
│  │   PLAN   │───>│  REVIEW  │───>│    NEXT     │───>│  UPDATE ││
│  └──────────┘    └──────────┘    └─────────────┘    └─────────┘│
│       │               │                  │                │      │
│   Creates JSON    Multi-model     Finds next        Updates     │
│   spec file       validation      actionable        status &    │
│                   via AI CLIs     task              progress    │
│       │               │                  │                │      │
│       └───────────────┴──────────────────┴────────────────┘      │
│                              │                                    │
│                         [Cycle repeats]                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Your Role (REVIEW)**: Validate specifications using multiple AI perspectives before expensive implementation begins. Catch issues early when they're cheap to fix.

## Core Philosophy

**Diverse Perspectives Improve Quality**: Multiple AI models reviewing a specification catch more issues than a single review. By consulting different AI CLIs (gemini, codex, cursor-agent) in parallel, we validate design decisions, identify risks, and build confidence before costly implementation.

**Anti-Sycophancy by Design**: LLMs naturally want to agree and validate. This skill fights that tendency with prompts that **assume problems exist** and **demand critical analysis**. The tool automatically uses imperative, fault-finding language to extract genuine critique.

**Key Benefits:**
- Catches specification gaps before coding begins
- Validates architecture from multiple expert angles
- Identifies hidden risks and edge cases
- Evaluates implementation feasibility realistically
- Provides diverse perspectives on complex decisions
- Builds confidence through consensus
- Reduces expensive rework and technical debt

## When to Use This Skill

Use `Skill(sdd-toolkit:sdd-plan-review)` to:
- Review new specifications before approval
- Validate complex or high-risk specifications
- Evaluate specs with novel architecture decisions
- Get confidence before high-effort implementations
- Security-review auth/data handling specs
- Verify cross-team integration specs
- Check feasibility of aggressive timelines

**Do NOT use for:**
- Simple specs (< 5 tasks, well-understood patterns)
- Specs already in active implementation
- Quick prototypes or experiments
- Trivial changes or bug fixes
- Internal refactorings with no external impact

## Skill Handoff Points

**When to transition to other skills:**

← **From Skill(sdd-toolkit:sdd-plan)**:
  - After spec creation, validate before approval
  - Before committing to complex implementation
  - When uncertainty exists about approach

→ **To Skill(sdd-toolkit:sdd-update)**:
  - After review, document review status in spec metadata
  - Journal critical issues found and addressed
  - Update spec frontmatter with review scores

→ **To Skill(sdd-toolkit:sdd-next)**:
  - After APPROVE recommendation, begin implementation
  - Once critical issues are fixed and re-review passes
  - When confidence is high and risks are mitigated

← **Back to Skill(sdd-toolkit:sdd-plan)**:
  - If REJECT recommendation, redesign spec
  - When fundamental architectural changes needed
  - To split overly complex specs

## Decision Tree: When to Review?

```
What's the situation?
├─ Just created new spec → Use `Skill(sdd-toolkit:sdd-plan-review)` (validate before approval)
├─ Security-sensitive (auth/data) → Use `Skill(sdd-toolkit:sdd-plan-review)` --type security
├─ Tight deadline/aggressive estimates → Use `Skill(sdd-toolkit:sdd-plan-review)` --type feasibility
├─ Novel architecture/technology → Use `Skill(sdd-toolkit:sdd-plan-review)` --type full
├─ Simple spec (< 5 tasks) → Skip review, proceed with Skill(sdd-toolkit:sdd-next)
├─ Already implementing → Skip review (too late)
└─ Uncertain? → Use `Skill(sdd-toolkit:sdd-plan-review)` --type quick (10 min)

Review Type Selection:
├─ High risk + complex → full (20-30 min, comprehensive)
├─ Auth/security/data → security (15-20 min, vulnerability focus)
├─ Tight timeline → feasibility (10-15 min, estimate validation)
├─ Low risk + simple → quick (10 min, completeness check)
└─ Default → full (when unsure)
```

## Tool Verification

**Before using this skill**, verify the required tools are available:

```bash
# Verify sdd review CLI is installed and accessible
sdd --help
```

**Expected output**: Help text showing available commands (including review, list-review-tools)

**Check which AI CLI tools are available:**
```bash
sdd list-review-tools
```

**IMPORTANT - CLI Usage Only**:
- ✅ **DO**: Use `sdd review` CLI wrapper commands (e.g., `sdd review`, `sdd list-review-tools`)
- ❌ **DO NOT**: Execute Python scripts directly or call AI CLIs directly (e.g., `python sdd_review.py`, `bash gemini ...`, `codex ...`)

The CLI provides proper error handling, validation, argument parsing, and interface consistency. It orchestrates AI CLI calls automatically. Direct script or AI CLI execution bypasses these safeguards and may fail.

If the verification command fails, ensure the SDD toolkit is properly installed and accessible in your environment.

## Quick Start

### Check Available Tools

```bash
# List which AI CLI tools are installed
sdd list-review-tools

# Expected output:
# ✓ Available (2):
#   gemini
#   codex
# ✗ Not Available (1):
#   cursor-agent
```

### Basic Review

```bash
# Review a spec with automatic tool detection
sdd review user-auth-001

# Review with specific type
sdd review user-auth-001 --type full

# Quick review (fast, basic checks only)
sdd review user-auth-001 --type quick

# Security-focused review
sdd review user-auth-001 --type security

# Feasibility check (estimates, dependencies)
sdd review user-auth-001 --type feasibility
```

### Save Report

```bash
# Save as markdown
sdd review user-auth-001 --output review-report.md

# Save as JSON (for automation)
sdd review user-auth-001 --output review-report.json
```

### Advanced Options

```bash
# Specify which tools to use
sdd review user-auth-001 --tools gemini,codex

# Use caching (skip re-calling models for same spec)
sdd review user-auth-001 --cache

# Preview without executing
sdd review user-auth-001 --dry-run
```

## Quick Reference: Common Commands

| Command | Purpose | Typical Duration |
|---------|---------|------------------|
| `sdd list-review-tools` | Check which AI CLIs are installed | Instant |
| `sdd review <spec> --type quick` | Fast completeness check | 10-15 min |
| `sdd review <spec> --type full` | Comprehensive analysis | 20-30 min |
| `sdd review <spec> --type security` | Security vulnerability scan | 15-20 min |
| `sdd review <spec> --type feasibility` | Estimate & dependency validation | 10-15 min |
| `sdd review <spec> --output report.md` | Save review report | Variable |

## Typical Workflow

**Standard review flow:**

```bash
# 1. Create spec (via `Skill(sdd-toolkit:sdd-plan)`)

# 2. Review it
sdd review myspec --type full

# 3. If REVISE recommended, address issues
#    ... edit spec based on critical/high issues ...

# 4. Quick re-review (optional)
sdd review myspec --type quick

# 5. Document review in spec (via `Skill(sdd-toolkit:sdd-update)`)
sdd add-journal myspec --title "Review completed" --content "7.5/10 score, 2 critical issues addressed"

# 6. Approve and proceed (via `Skill(sdd-toolkit:sdd-next)`)
sdd update-frontmatter myspec status "approved"
```

## Review Types

### Overview Table

| Type | Models | Duration | Dimensions Emphasized | Use When |
|------|--------|----------|----------------------|----------|
| **quick** | 2 | 10-15 min | Completeness, Clarity | Simple specs, time-constrained, low-risk changes |
| **full** | 3-4 | 20-30 min | All 6 dimensions | Complex specs, moderate-to-high risk, novel architecture |
| **security** | 2-3 | 15-20 min | Risk Management | Auth/authz, data handling, API security, compliance |
| **feasibility** | 2-3 | 10-15 min | Feasibility | Tight deadlines, resource constraints, uncertain scope |

### Quick Review

**Focus**: Basic completeness and clarity
**Models**: 2 tools (diverse perspectives)
**Best For**: Simple specs, low-risk changes, time pressure

**What it checks:**
- All required sections present
- Tasks clearly described with acceptance criteria
- Dependencies explicitly stated
- Basic verification steps exist
- No obvious gaps or ambiguities

**Skip detailed analysis of:**
- Architecture soundness
- Performance implications
- Security edge cases
- Implementation complexity

### Full Review

**Focus**: Comprehensive analysis across all dimensions
**Models**: 3-4 tools (architecture, security, implementation, integration perspectives)
**Best For**: Complex specs, moderate-to-high risk, cross-team changes, novel patterns

**What it checks:**
- **Completeness**: All sections present, sufficient detail, no gaps
- **Clarity**: Clear descriptions, acceptance criteria, unambiguous language
- **Feasibility**: Realistic estimates, achievable dependencies, proper sizing
- **Architecture**: Sound design, proper abstractions, scalability, maintainability
- **Risk Management**: Risks identified, edge cases covered, failure modes handled
- **Verification**: Comprehensive testing plan, verification steps, quality gates

**Most thorough review type** - use when cost of failure is high.

### Security Review

**Focus**: Security vulnerabilities and risks
**Models**: 2-3 tools (offensive, defensive, compliance perspectives)
**Best For**: Auth/authz, data handling, API security, regulated domains, PII/PHI

**What it checks:**
- Authentication and authorization design
- Input validation and sanitization
- Secrets management (API keys, passwords, tokens)
- Access control and principle of least privilege
- Audit logging and monitoring
- Data encryption (at rest, in transit)
- SQL/command injection prevention
- CSRF/XSS protections
- Rate limiting and DoS protection
- Compliance requirements (GDPR, HIPAA, SOC2)

**Emphasizes risk_management dimension** in scoring.

### Feasibility Review

**Focus**: Implementation realism and estimate accuracy
**Models**: 2-3 tools (optimist, realist, pessimist perspectives)
**Best For**: Tight deadlines, resource constraints, uncertain requirements, large efforts

**What it checks:**
- Time estimates realistic for each task
- Required skills present in team
- Dependencies actually exist and are accessible
- External APIs/services available and documented
- Performance requirements achievable with approach
- Complexity accurately assessed (not underestimated)
- Blockers identified and mitigated
- Resource requirements feasible (compute, storage, budget)

**Identifies underestimated tasks** and impossible requirements.

## Scoring Dimensions

Every review evaluates specs across **6 dimensions** (1-10 scale):

1. **Completeness** (1-10)
   - All sections present
   - Sufficient detail for implementation
   - No missing requirements or undefined dependencies
   - Acceptance criteria for all tasks

2. **Clarity** (1-10)
   - Clear, unambiguous descriptions
   - Specific acceptance criteria
   - Well-defined task boundaries
   - No vague or confusing language

3. **Feasibility** (1-10)
   - Realistic time estimates
   - Achievable dependencies
   - Required skills available
   - No impossible requirements

4. **Architecture** (1-10)
   - Sound design decisions
   - Proper abstractions
   - Scalability considerations
   - Low coupling, high cohesion

5. **Risk Management** (1-10)
   - Risks identified
   - Edge cases covered
   - Failure modes addressed
   - Mitigation strategies present

6. **Verification** (1-10)
   - Comprehensive test plan
   - Verification steps defined
   - Quality gates established
   - Testing gaps identified

**Overall Score**: Average of all 6 dimensions

**Scoring Guide** (models use critical standards):
- **1-3**: Major problems, unacceptable (common for first drafts)
- **4-6**: Needs significant work (most specs fall here)
- **7-8**: Good with minor issues (rare - models are skeptical)
- **9-10**: Excellent, ready to proceed (very rare - be critical)

**Final Recommendation**:
- **APPROVE**: Overall score ≥ 8, few/no critical issues
- **REVISE**: Overall score 4-7, fixable issues exist (most common)
- **REJECT**: Overall score ≤ 3, fundamental flaws require redesign

## The Review Workflow

### Phase 1: Preparation

**Before running review, ensure:**

1. **Check tool availability**
   ```bash
   sdd list-review-tools
   ```
   - Need at least 1 tool installed
   - 2+ tools recommended for multi-model review
   - All 3 tools ideal for comprehensive analysis

2. **Load specification**
   - Spec must be complete (not draft fragments)
   - JSON format required
   - Frontmatter should include complexity/risk metadata

3. **Select review type**
   - Auto-selected based on spec metadata
   - Or explicitly specify with `--type` flag
   - See Decision Tree above for guidance

**The tool automatically:**
- Detects which AI CLI tools are available
- Parses spec frontmatter and content
- Determines appropriate review scope
- Selects models based on review type

### Phase 2: Execute Review

**Multi-model consultation (parallel execution):**

```bash
sdd review user-auth-001 --type full
```

**What happens:**
1. **Generate prompts** for each model with anti-sycophancy framing
2. **Call all AI CLI tools simultaneously** (ThreadPoolExecutor)
3. **Collect responses** as they complete (timeouts: 60-120s per tool)
4. **Handle failures gracefully** (continue with successful responses)
5. **Parse responses** (JSON extraction with fallback strategies)

**Progress indicators:**
```
Reviewing specification: user-auth-001.json
Using 3 tool(s): gemini, codex, cursor-agent

Starting full review...
✓ gemini completed (15.2s)
✓ codex completed (22.5s)
✗ cursor-agent timeout (120s)

Review Complete
Execution time: 120.1s
Models responded: 2/3
```

**Automatic error handling:**
- Timeouts → Automatic retries with backoff
- Rate limits → Sequential mode fallback
- Auth failures → Skip tool with clear message
- Parse failures → Use other model responses

### Phase 3: Interpret Results

**Understanding the report:**

**Overall Recommendation:**
- **✅ APPROVE**: Score ≥ 8, ready for implementation
- **⚠️ REVISE**: Score 4-7, needs fixes before proceeding
- **❌ REJECT**: Score ≤ 3, fundamental redesign required

**Consensus Level:**
- **Strong**: Models closely agree (score variance < 1.0)
- **Moderate**: Some disagreement (variance 1.0-2.0)
- **Weak**: Significant disagreement (variance 2.0-3.0)
- **Conflicted**: Major disagreement (variance > 3.0)

**Issue Severity:**
- **CRITICAL**: Security vulnerabilities, blockers, data loss risks → **Must fix**
- **HIGH**: Design flaws, quality issues, maintainability → **Should fix**
- **MEDIUM**: Improvements, unclear requirements → **Consider fixing**
- **LOW**: Nice-to-have enhancements → **Note for future**

**Score Interpretation:**
```
Dimension Scores:
  Completeness:     8/10  (Good)
  Clarity:          7/10  (Good)
  Feasibility:      6/10  (Needs Work)
  Architecture:     8/10  (Good)
  Risk Management:  5/10  (Needs Work)
  Verification:     7/10  (Good)
  ────────────────────────
  Overall:          6.8/10 (REVISE)
```

**Example findings:**
```
🚨 Issues Found:

### Critical Issues (Must Fix)
1. Missing authentication on admin endpoints
   Severity: CRITICAL | Flagged by: gemini, codex
   Impact: Unauthorized access to sensitive operations
   Fix: Add JWT validation middleware to routes

### High Priority Issues (Should Fix)
2. Time estimates unrealistic for Phase 2
   Severity: HIGH | Flagged by: codex
   Impact: Timeline will slip, stakeholders disappointed
   Fix: Increase estimates for tasks 2.3-2.5 by 50%
```

### Phase 4: Act on Feedback

**1. Prioritize issues:**

```markdown
CRITICAL (must fix immediately):
  - [ ] Add authentication middleware
  - [ ] Fix SQL injection vulnerability

HIGH (should fix before approval):
  - [ ] Increase time estimates for Phase 2
  - [ ] Add error handling for network failures
  - [ ] Clarify acceptance criteria for tasks 2.3-2.5

MEDIUM (consider fixing):
  - [ ] Add performance benchmarks
  - [ ] Document API rate limits
```

**2. Update specification:**

Edit the spec file to address issues found.

**3. Document review (via Skill(sdd-toolkit:sdd-update)):**

```bash
# Journal the review results
sdd add-journal user-auth-001 \
  --title "Multi-model review completed" \
  --content "Full review: 6.8/10 (REVISE). 2 critical + 3 high issues identified and fixed. Re-review pending."

# Update metadata
sdd update-frontmatter user-auth-001 review_status "revise"
sdd update-frontmatter user-auth-001 review_score "6.8"
```

**4. Re-review if needed:**

```bash
# After fixes, quick re-review
sdd review user-auth-001 --type quick

# Should see improved scores
# If APPROVE → proceed
# If still REVISE → iterate
```

**5. Approve and proceed:**

```bash
# Update status to approved
sdd update-frontmatter user-auth-001 status "approved"
sdd update-frontmatter user-auth-001 review_status "approved"

# Begin implementation (via Skill(sdd-toolkit:sdd-next))
# (Use Skill(sdd-toolkit:sdd-next) to find first task)
```

## CLI Command Reference

### `sdd review`

Review a specification using multiple AI models.

```bash
sdd review {spec-id} [OPTIONS]
```

**Arguments:**
- `{spec-id}`: Specification ID (required)

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--type` | `quick\|full\|security\|feasibility` | `full` | Review type |
| `--tools` | Comma-separated list | Auto-detect | Which AI CLIs to use |
| `--output` | File path | (stdout) | Save report to file (.md or .json) |
| `--cache` | Flag | Off | Use cached results if available |
| `--dry-run` | Flag | Off | Preview without executing |

**Examples:**

```bash
# Basic review (auto-detects tools, uses full review)
sdd review user-auth-001

# Quick review (faster, less comprehensive)
sdd review user-auth-001 --type quick

# Security-focused review
sdd review user-auth-001 --type security

# Specify which tools to use
sdd review user-auth-001 --tools gemini,codex

# Save report to markdown file
sdd review user-auth-001 --output review.md

# Save report to JSON (for automation)
sdd review user-auth-001 --output review.json

# Use caching (skip model calls if spec unchanged)
sdd review user-auth-001 --cache

# Preview what would be done
sdd review user-auth-001 --dry-run
```

### `sdd list-review-tools`

Check which AI CLI tools are installed and available.

```bash
sdd list-review-tools
```

**Output:**
```
AI CLI Tools for Reviews

✓ Available (2):
  gemini
  codex

✗ Not Available (1):
  cursor-agent

Installation Instructions:

Cursor Agent:
  Install Cursor IDE from cursor.com
  Cursor agent comes bundled with the IDE

Summary: 2/3 tools available
Multi-model reviews available
```

**Exit codes:**
- `0`: At least 2 tools available (multi-model reviews possible)
- `1`: 0-1 tools available (limited functionality)

### Common Option Combinations

```bash
# Fast check before approval (10 min)
sdd review myspec --type quick

# Comprehensive pre-implementation review (20-30 min)
sdd review myspec --type full --output full-review.md

# Security audit for auth changes (15-20 min)
sdd review auth-spec --type security --output security-audit.md

# Validate aggressive timeline (10-15 min)
sdd review big-refactor --type feasibility

# Re-review after fixes (use cache to skip unchanged parts)
sdd review myspec --type quick --cache

# Production-ready review with all checks
sdd review critical-spec --type full --tools gemini,codex,cursor-agent
```

## Integration with SDD Workflow

### With `Skill(sdd-toolkit:sdd-plan)`

**After spec creation:**

```bash
# 1. Create spec (via Skill(sdd-toolkit:sdd-plan))
#    → Generates specs/active/myspec.json

# 2. Review it
sdd review myspec --type full

# 3. If REVISE recommended, address critical/high issues
#    ... edit specs/active/myspec.json ...

# 4. Quick re-review after fixes (optional)
sdd review myspec --type quick

# 5. If APPROVE, proceed to implementation
```

**Review triggers redesign (REJECT):**

```bash
# Review identifies fundamental flaws
sdd review myspec --type full
# → Overall: 2.5/10 (REJECT)

# Back to sdd-plan to redesign
# (Use `Skill(sdd-toolkit:sdd-plan)` to create new version)
```

### With `Skill(sdd-toolkit:sdd-update)`

**Document review results:**

```bash
# After review completes
sdd review user-auth-001 --output review.md

# Journal the review
sdd add-journal user-auth-001 --title "Multi-model review completed" --content "Full review: 7.5/10 (APPROVE with minor issues). 2 critical issues fixed. Security review passed."

# Update spec metadata with review status
sdd update-frontmatter user-auth-001 review_status "approved"
sdd update-frontmatter user-auth-001 review_score "7.5"
sdd update-frontmatter user-auth-001 review_date "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Update overall status to approved
sdd update-frontmatter user-auth-001 status "approved"
```

**Track review history:**

```json
{
  "metadata": {
    "reviews": [
      {
        "date": "2025-10-20T15:30:00Z",
        "type": "full",
        "score": 6.8,
        "recommendation": "REVISE",
        "models": ["gemini", "codex"]
      },
      {
        "date": "2025-10-21T10:00:00Z",
        "type": "quick",
        "score": 7.5,
        "recommendation": "APPROVE",
        "models": ["gemini", "codex"]
      }
    ]
  }
}
```

### With `Skill(sdd-toolkit:sdd-next)`

**Review → Approve → Implement:**

```bash
# Review spec
sdd review user-auth-001 --type full
# → 8.2/10 (APPROVE)

# Document approval (via Skill(sdd-toolkit:sdd-update))
sdd update-frontmatter user-auth-001 status "approved"

# Begin implementation (via Skill(sdd-toolkit:sdd-next))
# (Use Skill(sdd-toolkit:sdd-next) to find first task)
```

**Review gates implementation:**

```
Review Score → Decision
├─ 8-10 (APPROVE)     → Proceed to sdd-next
├─ 5-7 (REVISE)       → Fix issues → Re-review
└─ 1-4 (REJECT)       → Back to sdd-plan (redesign)
```

### Complete Integrated Workflow

```bash
# 1. Create spec
# (Use Skill(sdd-toolkit:sdd-plan))
# → specs/active/myspec.json created

# 2. Review spec
sdd review myspec --type full
# → 6.5/10 (REVISE): 2 critical, 3 high issues

# 3. Fix critical/high issues
# ... edit specs/active/myspec.json ...

# 4. Re-review (quick check)
sdd review myspec --type quick
# → 8.0/10 (APPROVE)

# 5. Document review (via Skill(sdd-toolkit:sdd-update))
sdd add-journal myspec --title "Review approved" \
  --content "8.0/10, all critical issues resolved"
sdd update-frontmatter myspec status "approved"

# 6. Begin implementation (via Skill(sdd-toolkit:sdd-next))
# (Use Skill(sdd-toolkit:sdd-next) to find first task)

# 7. Track progress (via Skill(sdd-toolkit:sdd-update))
# ... as implementation proceeds ...
```

## Advanced Topics

### Error Handling

**Automatic recovery:**

| Error Type | Tool Behavior | User Impact |
|------------|---------------|-------------|
| **Timeout** (>120s) | Retry with backoff (2 attempts) | Longer wait, usually succeeds |
| **Rate limit** (HTTP 429) | Wait + retry, or sequential mode | Slower execution |
| **Auth failure** (401/403) | Skip tool, continue with others | Reduced confidence |
| **Network error** | Retry 2x with backoff | Usually recovers |
| **Parse failure** | Use other model responses | No impact if ≥2 models succeed |

**Timeouts per tool:**
- Gemini: 60s (fast API)
- Codex: 90s (thorough analysis)
- Cursor Agent: 120s (local processing)

**Partial results:**

| Scenario | Outcome | Confidence |
|----------|---------|------------|
| 3/3 tools succeed | Full review | High |
| 2/3 tools succeed | Continue with 2 | Medium (noted in report) |
| 1/3 tools succeed | Continue with 1 | Low (single-model warning) |
| 0/3 tools succeed | Review fails | Error with troubleshooting |

### Caching System

**How it works:**

Cache key = SHA-256 hash of:
- Spec file content
- Review type
- Tool names used

**Cache location:** `~/.claude/skills/sdd-plan-review/.cache/`

**Cache behavior:**

```bash
# Default: No caching (always call tools)
sdd review myspec

# Use cache if available (skip model calls if unchanged)
sdd review myspec --cache

# Clear all cache
rm -rf ~/.claude/skills/sdd-plan-review/.cache/
```

**When cache is used:**
- Spec content identical
- Same review type
- Same tools requested
- Cache entry < 7 days old

**When cache is invalidated:**
- Spec content changes (any edit)
- Different review type requested
- Different tools specified
- Cache entry > 7 days old
- Manual cache clear

**Cache benefits:**
- **Fast re-reviews** after minor fixes (instant)
- **Cost savings** (no duplicate API calls)
- **Consistent results** for same inputs

**Cache limitations:**
- Doesn't detect semantic changes (only content hash)
- Can return stale results if models improve
- Shared cache across all specs (based on hash)

**Best practices:**
- Use `--cache` for quick re-reviews after minor edits
- Don't use `--cache` for major spec changes
- Clear cache periodically (monthly)
- Don't use `--cache` for first review of new spec

## Best Practices

### When to Review

**Always review:**
- High-risk or high-priority specs
- Security-sensitive implementations (auth, data, payments)
- Novel architecture or technology choices
- Before final approval and team commitment

**Consider reviewing:**
- Medium complexity (≥ 10 tasks)
- Cross-team dependencies
- Specs with aggressive timelines
- Unclear or novel requirements

**Skip review:**
- Simple specs (< 5 tasks)
- Well-understood patterns (CRUD operations)
- Low-risk internal refactorings
- Trivial bug fixes

### Review Quality Tips

**For best results:**

1. **Review complete specs, not fragments**
   - All phases defined
   - Tasks described
   - Dependencies stated
   - Verification steps present

2. **Use appropriate review type**
   - Quick: Simple, low-risk
   - Full: Complex, moderate-to-high risk
   - Security: Auth/data handling
   - Feasibility: Tight timelines

3. **Address issues by priority**
   - CRITICAL → Must fix before proceeding
   - HIGH → Should fix, significant impact
   - MEDIUM → Consider, nice-to-have
   - LOW → Note for future improvements

4. **Don't blindly accept all feedback**
   - Consider context and tradeoffs
   - Models may misunderstand requirements
   - Use judgment on disagreements
   - Document decisions to defer issues

5. **Re-review after major changes**
   - Quick re-review after critical fixes
   - Full re-review after architectural changes
   - Validates fixes were effective

6. **Document review in spec**
   - Journal review date, score, decision
   - Track review history in metadata
   - Note deferred issues with rationale

### Acting on Feedback

**Prioritization guide:**

```
CRITICAL issues:
  - Security vulnerabilities
  - Blocking dependencies
  - Data loss risks
  - Compliance violations
  → Fix immediately, cannot proceed without

HIGH issues:
  - Design flaws
  - Unrealistic estimates
  - Missing error handling
  - Quality concerns
  → Should fix before approval

MEDIUM issues:
  - Unclear requirements
  - Missing optimizations
  - Incomplete documentation
  → Consider fixing, or defer with documentation

LOW issues:
  - Nice-to-have improvements
  - Edge case enhancements
  - Future considerations
  → Note for later, proceed
```

**Balance perspectives:**

When models disagree:
1. Read all perspectives carefully
2. Identify root cause of disagreement
3. Research the specific concern
4. Make informed decision with documentation
5. Consider getting human expert review

**Track decisions:**

```bash
# Document decision to defer an issue
sdd add-journal myspec --title "Deferred optimization concern" \
  --content "Codex flagged potential N+1 query in Phase 2. Decision: defer to Phase 3 performance optimization task. Reasoning: premature optimization, need working implementation first."
```

## Applying Plan Review Feedback Systematically

After running a multi-model plan review, you can apply consensus recommendations systematically using `Skill(sdd-toolkit:sdd-modify)`.

### When to Apply Plan Review Feedback

Plan reviews generate improvement recommendations **before implementation begins**. Unlike fidelity reviews (which compare code to spec), plan reviews evaluate the spec itself.

**Apply feedback when:**
- ✅ Multiple models agree on improvements (consensus recommendations)
- ✅ Critical or high-severity issues identified
- ✅ Clarity improvements suggested (vague task descriptions)
- ✅ Missing verification steps identified
- ✅ Architectural improvements have consensus
- ✅ Feasibility concerns about estimates

**Don't apply feedback for:**
- ❌ Low-severity suggestions (note for future)
- ❌ Conflicting recommendations (no consensus)
- ❌ Stylistic preferences without substance
- ❌ Overly conservative estimates (balance needed)

### Consensus Extraction

Multi-model reviews provide diverse perspectives. Focus on **consensus recommendations** where multiple models agree:

**Strong consensus (2-3 models agree):**
- High confidence to apply
- Clear problem identification
- Aligned solutions

**Weak consensus (1 model flags):**
- Review carefully before applying
- May be edge case or misunderstanding
- Consider with context

**Conflicting feedback:**
- Models disagree on approach
- Requires human judgment
- Document decision rationale

### Systematic Application Workflow

#### Step 1: Run Plan Review

```bash
sdd review my-spec-001 --type full --output review-report.md
```

**Example output:**
```
Overall Score: 6.5/10 (REVISE)
Models: gemini, codex, cursor-agent

Consensus recommendations (2-3 models agree):
  1. Task descriptions too vague in Phase 2 (3 models)
  2. Missing error handling verification (2 models)
  3. Time estimates unrealistic for task-3-2 (2 models)

Single-model recommendations:
  4. Consider adding performance benchmarks (codex only)
  5. Add API versioning strategy (gemini only)
```

#### Step 2: Extract Consensus Improvements

Review the report and extract modifications where models agree:

**Create consensus-improvements.json:**
```json
{
  "modifications": [
    {
      "operation": "update_task",
      "task_id": "task-2-1",
      "field": "description",
      "value": "Implement OAuth 2.0 authentication with PKCE flow, including JWT token generation, refresh token rotation, and session management",
      "rationale": "Consensus: All 3 models flagged vague description"
    },
    {
      "operation": "add_verification",
      "task_id": "task-2-3",
      "verify_id": "verify-2-3-4",
      "description": "Verify error handling for network timeouts and service unavailability",
      "command": "pytest tests/test_error_handling.py -v",
      "rationale": "Consensus: 2 models recommended error handling verification"
    },
    {
      "operation": "update_metadata",
      "task_id": "task-3-2",
      "field": "estimated_hours",
      "value": 12.0,
      "rationale": "Consensus: 2 models flagged 8 hours as unrealistic, recommend 12"
    }
  ],
  "metadata": {
    "source": "plan-review-consensus",
    "review_date": "2025-11-06",
    "review_type": "full",
    "models": ["gemini", "codex", "cursor-agent"]
  }
}
```

#### Step 3: Preview Modifications

```bash
sdd apply-modifications my-spec-001 --from consensus-improvements.json --dry-run
```

Review the preview to ensure changes align with your understanding and requirements.

#### Step 4: Apply Consensus Recommendations

```bash
sdd apply-modifications my-spec-001 --from consensus-improvements.json
```

Features:
- Automatic backup before changes
- Validation after application
- Rollback on errors
- Clear success/failure reporting

#### Step 5: Document Applied Changes

```bash
sdd add-journal my-spec-001 \
  --title "Applied Multi-Model Review Consensus Improvements" \
  --content "Applied 3 consensus recommendations from full review. Updated task-2-1 description for clarity, added error handling verification to task-2-3, increased task-3-2 estimate from 8h to 12h based on complexity assessment. 2 single-model suggestions noted for future consideration." \
  --entry-type note
```

#### Step 6: Re-Review (Optional)

After applying consensus improvements, optionally run a quick re-review to confirm score improvement:

```bash
sdd review my-spec-001 --type quick
```

**Expected outcome:**
```
Overall Score: 7.8/10 (APPROVE)
Improvement: +1.3 from previous review

Previously flagged issues:
  ✓ Vague task descriptions (resolved)
  ✓ Missing error handling verification (resolved)
  ✓ Unrealistic estimates (resolved)
```

### Using sdd-modify Subagent

For automated workflows, use the subagent programmatically:

```
Task(
  subagent_type: "sdd-toolkit:sdd-modify-subagent",
  prompt: "Apply consensus improvements from consensus-improvements.json to spec my-spec-001. These modifications were extracted from multi-model plan review where 2-3 models agreed. Validate and report results.",
  description: "Apply plan review consensus"
)
```

### Example: Complete Closed-Loop Workflow

```bash
# 1. Create spec
# (Use Skill(sdd-toolkit:sdd-plan))
# → specs/active/my-spec-001.json

# 2. Run plan review
sdd review my-spec-001 --type full --output plan-review.md
# → 6.5/10 (REVISE): 3 consensus issues, 2 single-model suggestions

# 3. Extract consensus improvements
# → Manually create consensus-improvements.json with agreed-upon fixes

# 4. Preview modifications
sdd apply-modifications my-spec-001 --from consensus-improvements.json --dry-run
# → Shows 3 modifications

# 5. Apply consensus improvements
sdd apply-modifications my-spec-001 --from consensus-improvements.json
# → 3 modifications applied, backup created, validation passed

# 6. Document changes
sdd add-journal my-spec-001 --title "Applied plan review consensus" \
  --content "Applied 3 consensus recommendations. Spec improved from 6.5/10 to estimated 7.8/10."

# 7. Re-review (optional)
sdd review my-spec-001 --type quick
# → 7.8/10 (APPROVE)

# 8. Approve and proceed
sdd update-frontmatter my-spec-001 status "approved"

# 9. Begin implementation
# (Use Skill(sdd-toolkit:sdd-next))
```

### Benefits of Systematic Application

**Compared to manual spec editing:**
- ✅ **Higher confidence** - Multiple AI models validated changes
- ✅ **Faster** - Apply consensus in batch vs. one-by-one edits
- ✅ **Safer** - Automatic backup, validation, rollback
- ✅ **Traceable** - Clear record of what changed and why (rationale field)
- ✅ **Validated** - Spec structure checked after changes

**Consensus-driven improvements:**
- Focus on changes multiple experts agree on
- Higher probability of being correct
- Reduces individual model bias
- Builds confidence in spec quality

### See Also

- **Skill(sdd-toolkit:sdd-modify)** - Full documentation on spec modification workflows
- **skills/sdd-modify/examples/bulk-modify.md** - Bulk modification walkthrough
- **sdd apply-modifications --help** - CLI command reference

## See Also

**Skill(sdd-toolkit:sdd-plan)** - Use before this skill:
- Create specifications from requirements
- Generate task hierarchies and phases
- Define dependencies and verification steps
- Set up project structure

**Skill(sdd-toolkit:sdd-next)** - Use after review:
- Find next actionable task from approved spec
- Create execution plans for implementation
- Begin implementation after APPROVE
- Handle blockers and resume work

**Skill(sdd-toolkit:sdd-update)** - Use to document review:
- Update spec metadata (status, review_score, review_date)
- Add journal entries documenting review results
- Track review history and decisions
- Mark spec as approved after successful review
- Document deferred issues

**Skill(sdd-toolkit:sdd-validate)** - Complementary validation:
- Validate JSON spec file structure
- Check for schema compliance
- Find structural errors
- Different from review (validation vs quality assessment)
