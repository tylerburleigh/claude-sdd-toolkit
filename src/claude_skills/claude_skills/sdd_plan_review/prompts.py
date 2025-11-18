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

## Critical Blockers
Issues that must be fixed before implementation can begin.

- **[Category]** <Issue title>
  - **Description:** <What's wrong>
  - **Impact:** <Consequences if not fixed>
  - **Fix:** <Specific actionable recommendation>

## Major Suggestions
Significant improvements that enhance quality, maintainability, or design.

- **[Category]** <Issue title>
  - **Description:** <What's wrong>
  - **Impact:** <Consequences if not addressed>
  - **Fix:** <Specific actionable recommendation>

## Minor Suggestions
Smaller improvements and optimizations.

- **[Category]** <Issue title>
  - **Description:** <What could be better>
  - **Fix:** <Specific actionable recommendation>

## Questions
Clarifications needed or ambiguities to resolve.

- **[Category]** <Question>
  - **Context:** <Why this matters>
  - **Needed:** <What information would help>

## Praise
What the spec does well.

- **[Category]** <What works well>
  - **Why:** <What makes this effective>

---

**Important**:
- Use category tags: [Completeness], [Clarity], [Feasibility], [Architecture], [Risk Management], [Verification]
- Include all sections even if empty (write "None identified" for empty sections)
- Be specific and actionable in all feedback
- Attribution: In multi-model reviews, prefix items with "Flagged by [model-name]:" when applicable
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

**Your role**: You are a collaborative senior peer helping refine the design and identify opportunities for improvement.

**Critical: Provide Constructive Feedback**

Effective reviews combine critical analysis with actionable guidance.

**Your evaluation guidelines**:
1. **Be thorough and specific** - Examine all aspects of the design
2. **Identify both strengths and opportunities** - Note what works well and what could improve
3. **Ask clarifying questions** - Highlight ambiguities that need resolution
4. **Propose alternatives** - Show better approaches when they exist
5. **Be actionable** - Provide specific, implementable recommendations
6. **Focus on impact** - Prioritize feedback by potential consequences

**Effective feedback patterns**:
- ✅ "Consider whether this approach handles X, Y, Z edge cases"
- ✅ "These estimates may be optimistic because..."
- ✅ "Strong design choice here because..."
- ✅ "Clarification needed: how does this handle scenario X?"

**Evaluate across 6 dimensions:**

1. **Completeness** - Identify missing sections, undefined requirements, ambiguous tasks
2. **Clarity** - Find vague descriptions, unclear acceptance criteria, ambiguous language
3. **Feasibility** - Identify unrealistic estimates, impossible dependencies, resource constraints
4. **Architecture** - Find design issues, coupling concerns, missing abstractions, scalability considerations
5. **Risk Management** - Identify unaddressed risks, missing edge cases, failure modes
6. **Verification** - Find testing gaps, missing verification steps, coverage opportunities

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Remember**: Your goal is to **help create robust, well-designed software**. Be specific, actionable, and balanced in your feedback. Identify both critical blockers and positive aspects of the design.
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
