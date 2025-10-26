#!/usr/bin/env python3
"""
Unbiased prompt generation for spec reviews.

Generates prompts that actively fight LLM sycophancy by assuming problems exist
and demanding critical analysis.
"""

from typing import Dict, Any


# Response schema that models must follow
RESPONSE_SCHEMA = """
# Review Summary

Overall Score: <1-10>/10
Recommendation: <APPROVE|REVISE|REJECT>

## Dimension Scores

- **Completeness**: <1-10>/10 - <brief notes on what's missing or well-defined>
- **Clarity**: <1-10>/10 - <brief notes on clarity issues or strengths>
- **Feasibility**: <1-10>/10 - <brief notes on realistic estimates>
- **Architecture**: <1-10>/10 - <brief notes on design quality>
- **Risk Management**: <1-10>/10 - <brief notes on risk handling>
- **Verification**: <1-10>/10 - <brief notes on testing approach>

## Critical Issues

- **[CRITICAL]** <Issue title>
  - Description: <What's wrong>
  - Impact: <Consequences if not fixed>
  - Fix: <Specific actionable recommendation>

## High Priority Issues

- **[HIGH]** <Issue title>
  - Description: <What's wrong>
  - Impact: <Consequences if not fixed>
  - Fix: <Specific actionable recommendation>

## Medium Priority Issues

- **[MEDIUM]** <Issue title>
  - Description: <What's wrong>
  - Fix: <Specific actionable recommendation>

## Low Priority Issues

- **[LOW]** <Issue title>
  - Fix: <Specific actionable recommendation>

## Strengths

- <What the spec does well>
- <Another strength>

## Recommendations

- <Actionable improvement suggestion>
- <Another recommendation>

---

**Important**:
- Use exact severity tags: [CRITICAL], [HIGH], [MEDIUM], [LOW]
- Include all sections even if empty (write "None identified" for empty sections)
- Be specific and actionable in all feedback
"""


def generate_review_prompt(
    spec_content: str,
    review_type: str,
    spec_id: str = "unknown",
    title: str = "Specification"
) -> str:
    """
    Generate an unbiased, critical review prompt.

    Args:
        spec_content: Full specification content
        review_type: Type of review (quick, full, security, feasibility)
        spec_id: Specification ID
        title: Specification title

    Returns:
        Formatted prompt string
    """
    if review_type == "quick":
        return _generate_quick_review_prompt(spec_content, spec_id, title)
    elif review_type == "security":
        return _generate_security_review_prompt(spec_content, spec_id, title)
    elif review_type == "feasibility":
        return _generate_feasibility_review_prompt(spec_content, spec_id, title)
    else:  # full
        return _generate_full_review_prompt(spec_content, spec_id, title)


def _generate_full_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate full comprehensive review prompt."""
    return f"""You are conducting a comprehensive technical review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Full (comprehensive analysis)

**Your role**: You are a skeptical senior architect whose job is to prevent production failures by finding every flaw in this specification before implementation begins.

**Critical: Avoid Confirmation Bias**

LLMs have sycophantic tendencies (agreeing with users). This undermines review quality.

**Your evaluation guidelines**:
1. **Assume nothing is correct** - Start from a skeptical position
2. **Actively search for problems** - Don't just look for what works
3. **Challenge assumptions** - Question design decisions explicitly
4. **Identify what's missing** - Note absent considerations
5. **Propose alternatives** - Show better approaches when they exist
6. **Disagree when warranted** - Low scores and REJECT are valid

**Avoid biased patterns**:
- ❌ "This approach seems sound" → ✅ "Evaluate whether this approach handles X, Y, Z"
- ❌ "The estimates look reasonable" → ✅ "Identify unrealistic estimates and explain why"
- ❌ "Overall this is good" → ✅ "What critical flaws exist in this design?"

**This specification has problems. Find them:**

1. **Identify CRITICAL issues** (security, blockers, data loss risks)
2. **Identify HIGH issues** (quality, efficiency, maintainability problems)
3. **Identify MEDIUM/LOW issues** (improvements, edge cases, enhancements)

**Evaluate across 6 dimensions** (score 1-10 each):

1. **Completeness** - Identify all missing sections, undefined requirements, ambiguous tasks
2. **Clarity** - Find vague descriptions, unclear acceptance criteria, ambiguous language
3. **Feasibility** - Identify unrealistic estimates, impossible dependencies, resource constraints
4. **Architecture** - Find design flaws, coupling issues, missing abstractions, scalability limits
5. **Risk Management** - Identify unaddressed risks, missing edge cases, failure modes
6. **Verification** - Find testing gaps, missing verification steps, inadequate coverage

**Scoring Guide** (be critical, not generous):
- 1-3: Major problems, unacceptable (common for first drafts)
- 4-6: Needs significant work (most specs fall here)
- 7-8: Good with minor issues (rare)
- 9-10: Excellent, ready to proceed (very rare - be skeptical)

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Remember**: Your goal is to **prevent expensive mistakes**, not to make the spec author feel good. Be direct, critical, and thorough. Low scores and REJECT recommendations are expected and valuable.
"""


def _generate_quick_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate quick review prompt focusing on completeness and clarity."""
    return f"""You are conducting a quick technical review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Quick (focus on completeness and clarity)

**Your role**: Identify critical gaps and ambiguities that would block implementation.

**This specification likely has problems. Find them:**

1. **Completeness**: List all missing sections, undefined requirements, gaps
2. **Clarity**: Identify vague descriptions, unclear acceptance criteria
3. **Critical Issues**: Find blockers that prevent implementation

**Focus on these questions**:
- What information is missing?
- What is ambiguous or unclear?
- What would block a developer from implementing this?
- Are acceptance criteria defined?
- Are dependencies stated?

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Note**: Focus primarily on completeness and clarity dimensions. Other dimensions can have brief notes.
"""


def _generate_security_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate security-focused review prompt."""
    return f"""You are conducting a security review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Security (focus on vulnerabilities and risks)

**Your role**: You are a security auditor who assumes malicious users and identifies vulnerabilities.

**This specification has security vulnerabilities. Find them:**

1. **Identify CRITICAL security issues**:
   - Authentication/authorization flaws
   - Data validation gaps
   - Secrets management problems
   - Access control weaknesses
   - Injection vulnerabilities

2. **Identify HIGH security issues**:
   - Missing audit logging
   - Insufficient error handling
   - Insecure defaults
   - Privacy concerns
   - Compliance gaps

3. **Identify MEDIUM/LOW security issues**:
   - Rate limiting needs
   - Input sanitization improvements
   - Security headers
   - Encryption opportunities

**Security evaluation checklist**:
- [ ] Authentication/authorization properly designed?
- [ ] Input validation comprehensive?
- [ ] Secrets management secure?
- [ ] Access control principle of least privilege?
- [ ] Audit logging sufficient?
- [ ] Error messages don't leak information?
- [ ] Data encryption at rest and in transit?
- [ ] SQL/command injection prevented?
- [ ] CSRF/XSS protections in place?
- [ ] Rate limiting and DoS protection?

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Emphasize the risk_management dimension in your scoring.**
"""


def _generate_feasibility_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate feasibility-focused review prompt."""
    return f"""You are conducting a feasibility review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Feasibility (focus on realistic implementation)

**Your role**: You are a pragmatic engineer who identifies unrealistic estimates and impossible dependencies.

**These estimates are likely wrong. Find the problems:**

1. **Identify underestimated tasks**:
   - Which tasks will take longer than estimated?
   - What hidden complexity exists?
   - What dependencies are missing?

2. **Identify overestimated tasks**:
   - Which tasks are simpler than stated?
   - Where can work be parallelized?

3. **Identify impossible requirements**:
   - What dependencies don't exist?
   - What technical constraints block this?
   - What skills are required but not available?

**Feasibility evaluation checklist**:
- [ ] Time estimates realistic for each task?
- [ ] Dependencies available and accessible?
- [ ] Required skills present in team?
- [ ] External services/APIs exist and documented?
- [ ] Performance requirements achievable?
- [ ] Complexity accurately assessed?
- [ ] Blockers identified and mitigated?
- [ ] Resource requirements feasible?

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Emphasize the feasibility dimension in your scoring. Identify specific tasks with unrealistic estimates.**
"""


def get_stance_instruction(stance: str) -> str:
    """
    Get stance-specific instruction for a model.

    Args:
        stance: for, against, or neutral

    Returns:
        Stance instruction string
    """
    if stance == "for":
        return """
**Your stance**: You are generally supportive but identify genuine problems.
- Look for strengths and good decisions
- Identify issues that genuinely need fixing
- Don't inflate problems artificially
- Acknowledge what works well
"""
    elif stance == "against":
        return """
**Your stance**: You are skeptical and search for flaws.
- Assume the spec has problems
- Challenge every design decision
- Identify what could go wrong
- Propose alternative approaches
- Don't give benefit of the doubt
"""
    else:  # neutral
        return """
**Your stance**: You are balanced and objective.
- Evaluate based on evidence
- Identify both strengths and weaknesses
- Be neither generous nor harsh
- Focus on technical merit
"""
