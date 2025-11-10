---
name: sdd-plan-review
description: Multi-model consultation and synthesis stage for SDD specifications. Coordinates parallel AI reviewers, consolidates consensus findings, and prepares advisory reports and handoffs without modifying specs or executing fixes.
---

# Spec-Driven Development: Plan Review Skill

## Overview

`Skill(sdd-toolkit:sdd-plan-review)` is the consultative review gate for Spec-Driven Development. It convenes multiple AI reviewers, challenges assumptions with anti-sycophancy prompts, and synthesizes a consensus readiness assessment before any implementation or remediation occurs.

- Builds shared understanding of spec strengths, risks, and open questions
- Produces an advisory report that captures agreements, disagreements, and severity tags
- Recommends handoffs to the correct downstream skills instead of applying changes directly

This stage is advisory-only. The output is a synthesized report and clear guidance on where follow-up work belongs.

## Scope & Responsibilities

**This skill delivers:**
- Multi-model critique of draft specs across architecture, feasibility, risk, and verification
- Consolidated findings that highlight consensus, dissent, and severity of concerns
- Advisory recommendations on which downstream skill should address each issue
- Structured reports (Markdown and JSON) that capture review context for the broader workflow

**This skill does not:**
- Edit specifications or apply fixes
- Update spec metadata, journals, or approval status
- Green-light implementation without stakeholder review

## Position in the SDD Workflow

```
PLAN → PLAN-REVIEW (consult) → UPDATE/NEXT/VALIDATE
```

- **Entry point:** A draft spec exists and needs a critical second opinion.
- **Core activity:** `sdd-plan-review` convenes multiple AI reviewers, scores the spec across shared dimensions, and synthesizes an advisory consensus.

**Role of this skill:** Provide a rigorous, multi-perspective critique and consensus summary before any remediation starts. It informs, but never performs, follow-up edits.

## Scope Boundaries

- ✅ **Do:** Convene multi-model reviews, interrogate assumptions, aggregate perspectives, surface consensus/disagreements, and articulate advisory recommendations with severity tagging.
- ✅ **Do:** Capture review metadata, scores, and rationale in the generated report so downstream skills have clear guidance.
- ❌ **Don't:** Edit specs, adjust estimates, rewrite acceptance criteria, or change task hierarchies.
- ❌ **Don't:** Update journals, statuses, or frontmatter.
- ❌ **Don't:** Author execution plans or task breakdowns.

## Core Philosophy

**Diverse Perspectives Improve Quality**: Multiple AI models reviewing a specification catch more issues than a single review. By consulting different AI CLIs (gemini, codex, cursor-agent) in parallel, we validate design decisions, identify risks, and build confidence before costly implementation.

**Anti-Sycophancy by Design**: LLMs naturally want to agree and validate. This skill enforces critical framing and dissent-seeking defaults so reviewers actively hunt for issues instead of rubber-stamping drafts.

**Key Benefits:**
- Catches specification gaps before coding begins
- Validates architecture from multiple expert angles
- Identifies hidden risks and edge cases
- Evaluates implementation feasibility realistically
- Provides diverse perspectives on complex decisions
- Builds confidence through consensus
- Reduces expensive rework and technical debt

## When to Use This Skill

Request `Skill(sdd-toolkit:sdd-plan-review)` when you need an advisory consensus on a draft specification:
- New or revised specs that require stakeholder confidence before approval
- High-risk, high-effort, or multi-team initiatives where blind spots are expensive
- Novel architectures, emerging technologies, or unfamiliar integrations
- Security-sensitive surfaces (auth, PII, critical data flows) that demand scrutiny
- Aggressive timelines or estimates that need feasibility validation

**Do NOT request this skill when:**
- The spec is trivial, low-risk, or already well-understood (<5 tasks, standard patterns)
- Implementation is already underway
- You need someone to make direct specification edits
- The work is exploratory, disposable, or prototype-only

**Reminder:** This skill surfaces findings and next-step recommendations—actual remediation flows through the calling agent.

## Decision Guide: Should We Convene a Review?

```
Situation?
├─ Draft spec ready for approval → Engage plan-review (full)
├─ Security-critical area (auth/data/privacy) → Engage plan-review (security)
├─ Feasibility questions or aggressive estimates → Engage plan-review (feasibility)
├─ Major architectural novelty or integration risk → Engage plan-review (full)
├─ Lightweight, low-risk spec → Skip; proceed directly to sdd-next
├─ Work already executing → Use fidelity-review or update workflows instead
└─ Unsure confidence level → Engage plan-review (quick) to gain signal

After the consultation:
├─ Return to calling agent for next steps
```

## Tool Verification

**Before using this skill**, verify the required tools are available:

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

## Quick Reference: Common Commands

| Command | Purpose | Typical Duration |
|---------|---------|------------------|
| `sdd list-review-tools` | Check which AI CLIs are installed | Instant |
| `sdd review <spec> --type quick` | Fast completeness check | 10-15 min |
| `sdd review <spec> --type full` | Comprehensive analysis | 20-30 min |
| `sdd review <spec> --type security` | Security vulnerability scan | 15-20 min |
| `sdd review <spec> --type feasibility` | Estimate & dependency validation | 10-15 min |

## Typical Workflow

1. **Request the consultation**
   ```bash
   sdd review myspec --type full
   ```
   - Confirm the correct review type and tools, run once per major draft.

2. **Interpret the synthesized report**
   - Read the aggregated scores, model consensus summary, and severity-tagged findings.
   - Capture key agreements/disagreements and any open questions that need follow-up.

3. **Prepare the advisory handoff**
   - Summarize the readiness recommendation (approve / revise / reject) with rationale.

## Outputs

- **Consensus report (Markdown):** Automatically saved to `specs/.reviews/<spec-id>-review-<type>.md` and printed to stdout; captures findings, severity tags, dissent notes, and recommended handoffs.
- **JSON summary:** Automatically saved alongside the Markdown as `specs/.reviews/<spec-id>-review-<type>.json`; includes scores, recommendation, participating tools, and issue catalog for orchestration.
- **Readiness recommendation:** APPROVE / REVISE / REJECT judgement with supporting rationale embedded in both default artifacts.

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
1. **Initiate each model review** with enforced critical framing
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
    Recommended follow-up: Add JWT validation middleware to routes

### High Priority Issues (Should Fix)
2. Time estimates unrealistic for Phase 2
   Severity: HIGH | Flagged by: codex
   Impact: Timeline will slip, stakeholders disappointed
    Recommended follow-up: Revisit estimates for tasks 2.3-2.5 (suggest +50%)
```

### Phase 4: Synthesize Findings & Recommend Handoffs

1. **Prioritize by consensus severity**
   - Group findings by CRITICAL / HIGH / MEDIUM / LOW using the report metadata.
   - Note which models agreed and where dissent exists so downstream skills know when to investigate further.

2. **Identify the type of downstream work**
   - Structural or architectural redesign
   - Documentation, metadata, or journal updates
   - Implementation sequencing once APPROVE is accepted
   - Additional audits (tests, validation)

3. **Capture the advisory summary**
   - Record readiness recommendation, key blocking issues, and open questions.
   - Return the path to the JSON report for full context.

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

**Partial results:**

| Scenario | Outcome | Confidence |
|----------|---------|------------|
| 3/3 tools succeed | Full review | High |
| 2/3 tools succeed | Continue with 2 | Medium (noted in report) |
| 1/3 tools succeed | Continue with 1 | Low (single-model warning) |
| 0/3 tools succeed | Review fails | Error with troubleshooting |

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
   - Recommend when issues might be deferred

### Coordinating Follow-Up Work

**Prioritization guide for downstream teams:**

```
CRITICAL issues:
  - Security vulnerabilities
  - Blocking dependencies
  - Data loss risks
  - Compliance violations
  → Escalate immediately

HIGH issues:
  - Design flaws
  - Unrealistic estimates
  - Missing error handling
  - Quality concerns
  → Identify remediation work required before granting APPROVE

MEDIUM issues:
  - Unclear requirements
  - Missing optimizations
  - Incomplete documentation
  → Recommend whether to defer; provide rationale

LOW issues:
  - Nice-to-have improvements
  - Edge case enhancements
  - Future considerations
  → Identify as possible future work items
```

**Balance perspectives:**

When models disagree:
1. Review each perspective and note context differences.
2. Identify root causes or assumptions driving the disagreement.

Remember to include the JSON file path at the end of your report back.
