---
name: sdd-plan-review
description: Multi-model specification review using direct AI CLI tools. Calls gemini, codex, or cursor-agent CLIs in parallel to evaluate specs from multiple perspectives (architecture, security, feasibility). Provides actionable feedback to improve specification quality before implementation.
---

# Spec-Driven Development: Plan Review Skill

## Skill Family

This skill is part of the **Spec-Driven Development** family:
- **Skill(sdd-plan)** - Creates specifications and task hierarchies
- **Skill(sdd-plan-review)** (this skill) - Reviews specs with multi-model collaboration
- **Skill(sdd-next)** - Identifies next tasks and creates execution plans
- **Skill(sdd-update)** - Tracks progress and maintains documentation

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

Use `Skill(sdd-plan-review)` to:
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

← **From Skill(sdd-plan)**:
  - After spec creation, validate before approval
  - Before committing to complex implementation
  - When uncertainty exists about approach

→ **To Skill(sdd-update)**:
  - After review, document review status in spec metadata
  - Journal critical issues found and addressed
  - Update spec frontmatter with review scores

→ **To Skill(sdd-next)**:
  - After APPROVE recommendation, begin implementation
  - Once critical issues are fixed and re-review passes
  - When confidence is high and risks are mitigated

← **Back to Skill(sdd-plan)**:
  - If REJECT recommendation, redesign spec
  - When fundamental architectural changes needed
  - To split overly complex specs

## Decision Tree: When to Review?

```
What's the situation?
├─ Just created new spec → Use `Skill(sdd-plan-review)` (validate before approval)
├─ Security-sensitive (auth/data) → Use `Skill(sdd-plan-review)` --type security
├─ Tight deadline/aggressive estimates → Use `Skill(sdd-plan-review)` --type feasibility
├─ Novel architecture/technology → Use `Skill(sdd-plan-review)` --type full
├─ Simple spec (< 5 tasks) → Skip review, proceed with Skill(sdd-next)
├─ Already implementing → Skip review (too late)
└─ Uncertain? → Use `Skill(sdd-plan-review)` --type quick (10 min)

Review Type Selection:
├─ High risk + complex → full (20-30 min, comprehensive)
├─ Auth/security/data → security (15-20 min, vulnerability focus)
├─ Tight timeline → feasibility (10-15 min, estimate validation)
├─ Low risk + simple → quick (10 min, completeness check)
└─ Default → full (when unsure)
```

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
sdd review specs/active/user-auth-001.json

# Review with specific type
sdd review specs/active/user-auth-001.json --type full

# Quick review (fast, basic checks only)
sdd review specs/active/user-auth-001.json --type quick

# Security-focused review
sdd review specs/active/user-auth-001.json --type security

# Feasibility check (estimates, dependencies)
sdd review specs/active/user-auth-001.json --type feasibility
```

### Save Report

```bash
# Save as markdown
sdd review specs/active/user-auth-001.json --output review-report.md

# Save as JSON (for automation)
sdd review specs/active/user-auth-001.json --output review-report.json
```

### Advanced Options

```bash
# Specify which tools to use
sdd review specs/active/user-auth-001.json --tools gemini,codex

# Use caching (skip re-calling models for same spec)
sdd review specs/active/user-auth-001.json --cache

# Preview without executing
sdd review specs/active/user-auth-001.json --dry-run
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
# 1. Create spec (via `Skill(sdd-plan)`)

# 2. Review it
sdd review specs/active/myspec.json --type full

# 3. If REVISE recommended, address issues
#    ... edit spec based on critical/high issues ...

# 4. Quick re-review (optional)
sdd review specs/active/myspec.json --type quick

# 5. Document review in spec (via `Skill(sdd-update)`)
sdd add-journal myspec --title "Review completed" --content "7.5/10 score, 2 critical issues addressed"

# 6. Approve and proceed (via `Skill(sdd-next)`)
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
sdd review specs/active/user-auth-001.json --type full
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

**3. Document review (via Skill(sdd-update)):**

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
sdd review specs/active/user-auth-001.json --type quick

# Should see improved scores
# If APPROVE → proceed
# If still REVISE → iterate
```

**5. Approve and proceed:**

```bash
# Update status to approved
sdd update-frontmatter user-auth-001 status "approved"
sdd update-frontmatter user-auth-001 review_status "approved"

# Begin implementation (via Skill(sdd-next))
# (Use Skill(sdd-next) to find first task)
```

## CLI Command Reference

### `sdd review`

Review a specification using multiple AI models.

```bash
sdd review <spec-file> [OPTIONS]
```

**Arguments:**
- `<spec-file>`: Path to JSON specification file (required)

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
sdd review specs/active/user-auth-001.json

# Quick review (faster, less comprehensive)
sdd review specs/active/user-auth-001.json --type quick

# Security-focused review
sdd review specs/active/user-auth-001.json --type security

# Specify which tools to use
sdd review specs/active/user-auth-001.json --tools gemini,codex

# Save report to markdown file
sdd review specs/active/user-auth-001.json --output review.md

# Save report to JSON (for automation)
sdd review specs/active/user-auth-001.json --output review.json

# Use caching (skip model calls if spec unchanged)
sdd review specs/active/user-auth-001.json --cache

# Preview what would be done
sdd review specs/active/user-auth-001.json --dry-run
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
sdd review myspec.json --type quick

# Comprehensive pre-implementation review (20-30 min)
sdd review myspec.json --type full --output full-review.md

# Security audit for auth changes (15-20 min)
sdd review auth-spec.json --type security --output security-audit.md

# Validate aggressive timeline (10-15 min)
sdd review big-refactor.json --type feasibility

# Re-review after fixes (use cache to skip unchanged parts)
sdd review myspec.json --type quick --cache

# Production-ready review with all checks
sdd review critical-spec.json --type full --tools gemini,codex,cursor-agent
```

## Integration with SDD Workflow

### With `Skill(sdd-plan)`

**After spec creation:**

```bash
# 1. Create spec (via Skill(sdd-plan))
#    → Generates specs/active/myspec.json

# 2. Review it
sdd review specs/active/myspec.json --type full

# 3. If REVISE recommended, address critical/high issues
#    ... edit specs/active/myspec.json ...

# 4. Quick re-review after fixes (optional)
sdd review specs/active/myspec.json --type quick

# 5. If APPROVE, proceed to implementation
```

**Review triggers redesign (REJECT):**

```bash
# Review identifies fundamental flaws
sdd review specs/active/myspec.json --type full
# → Overall: 2.5/10 (REJECT)

# Back to sdd-plan to redesign
# (Use `Skill(sdd-plan)` to create new version)
```

### With `Skill(sdd-update)`

**Document review results:**

```bash
# After review completes
sdd review specs/active/user-auth-001.json --output review.md

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

### With `Skill(sdd-next)`

**Review → Approve → Implement:**

```bash
# Review spec
sdd review specs/active/user-auth-001.json --type full
# → 8.2/10 (APPROVE)

# Document approval (via Skill(sdd-update))
sdd update-frontmatter user-auth-001 status "approved"

# Begin implementation (via Skill(sdd-next))
# (Use Skill(sdd-next) to find first task)
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
# (Use Skill(sdd-plan))
# → specs/active/myspec.json created

# 2. Review spec
sdd review specs/active/myspec.json --type full
# → 6.5/10 (REVISE): 2 critical, 3 high issues

# 3. Fix critical/high issues
# ... edit specs/active/myspec.json ...

# 4. Re-review (quick check)
sdd review specs/active/myspec.json --type quick
# → 8.0/10 (APPROVE)

# 5. Document review (via Skill(sdd-update))
sdd add-journal myspec --title "Review approved" \
  --content "8.0/10, all critical issues resolved"
sdd update-frontmatter myspec status "approved"

# 6. Begin implementation (via Skill(sdd-next))
# (Use Skill(sdd-next) to find first task)

# 7. Track progress (via Skill(sdd-update))
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
sdd review myspec.json

# Use cache if available (skip model calls if unchanged)
sdd review myspec.json --cache

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

## See Also

**Skill(sdd-plan)** - Use before this skill:
- Create specifications from requirements
- Generate task hierarchies and phases
- Define dependencies and verification steps
- Set up project structure

**Skill(sdd-next)** - Use after review:
- Find next actionable task from approved spec
- Create execution plans for implementation
- Begin implementation after APPROVE
- Handle blockers and resume work

**Skill(sdd-update)** - Use to document review:
- Update spec metadata (status, review_score, review_date)
- Add journal entries documenting review results
- Track review history and decisions
- Mark spec as approved after successful review
- Document deferred issues

**Skill(sdd-validate)** - Complementary validation:
- Validate JSON spec file structure
- Check for schema compliance
- Find structural errors
- Different from review (validation vs quality assessment)
