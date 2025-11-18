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
- Use category tags: [Completeness], [Architecture], [Data Model], [Interface Design], [Security], [Verification]
- Include all sections even if empty (write "None identified" for empty sections)
- Be specific and actionable in all feedback
- For clarity issues, use Questions section rather than creating a separate category
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

**Evaluate across 6 technical dimensions:**

1. **Completeness** - Identify missing sections, undefined requirements, ambiguous tasks
2. **Architecture** - Find design issues, coupling concerns, missing abstractions, scalability considerations
3. **Data Model** - Evaluate data structures, relationships, consistency, migration strategies
4. **Interface Design** - Review API contracts, component boundaries, integration patterns
5. **Security** - Identify authentication, authorization, data protection, and vulnerability concerns
6. **Verification** - Find testing gaps, missing verification steps, coverage opportunities

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Remember**: Your goal is to **help create robust, well-designed software**. Be specific, actionable, and balanced in your feedback. Identify both critical blockers and positive aspects of the design.
"""


def _generate_quick_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate quick review prompt focusing on blockers and questions."""
    return f"""You are conducting a quick technical review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Quick (focus on blockers and questions)

**Your role**: Identify critical blockers and key questions that need resolution before implementation.

**Focus on finding:**

1. **Critical Blockers**: What would prevent implementation from starting?
   - Missing required sections or requirements
   - Undefined dependencies or integrations
   - Unresolved technical decisions
   - Incomplete acceptance criteria

2. **Key Questions**: What needs clarification?
   - Ambiguous requirements or acceptance criteria
   - Unclear technical approaches
   - Missing context or rationale
   - Edge cases not addressed

**Evaluation areas**:
- **Completeness**: Are all necessary sections and requirements present?
- **Questions**: What clarifications are needed?

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Note**: Focus primarily on Critical Blockers and Questions sections. Brief notes for other sections are sufficient.
"""


def _generate_security_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate security-focused review prompt."""
    return f"""You are conducting a security review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Security (focus on vulnerabilities and risks)

**Your role**: Security specialist helping identify and mitigate potential vulnerabilities.

**Focus on security considerations:**

1. **Authentication & Authorization**:
   - Are authentication mechanisms properly designed?
   - Is authorization enforced at appropriate boundaries?
   - Does access control follow principle of least privilege?

2. **Data Protection**:
   - Is input validation comprehensive?
   - Are secrets managed securely?
   - Is data encrypted at rest and in transit?
   - Do error messages avoid leaking sensitive information?

3. **Common Vulnerabilities**:
   - Are injection attacks (SQL, command, XSS, CSRF) prevented?
   - Are security headers and protections in place?
   - Is rate limiting and DoS protection addressed?
   - Are insecure defaults avoided?

4. **Audit & Compliance**:
   - Is audit logging sufficient for security events?
   - Are privacy concerns addressed?
   - Are relevant compliance requirements considered?

**Evaluation areas**:
- **Security**: Authentication, authorization, data protection, vulnerability prevention
- **Architecture**: Security-relevant design decisions
- **Data Model**: Data sensitivity, encryption, access patterns

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Note**: Focus primarily on Security category feedback. Include Critical Blockers for any security issues that must be addressed before implementation.
"""


def _generate_feasibility_review_prompt(spec_content: str, spec_id: str, title: str) -> str:
    """Generate technical complexity review prompt."""
    return f"""You are conducting a technical complexity review of a software specification.

**Spec**: {spec_id}
**Title**: {title}
**Review Type**: Technical Complexity (focus on implementation challenges)

**Your role**: Pragmatic engineer helping identify technical challenges and implementation risks.

**Focus on technical considerations:**

1. **Hidden Complexity**:
   - What technical challenges might not be obvious?
   - Where does complexity concentrate?
   - What edge cases increase difficulty?

2. **Dependencies & Integration**:
   - Are all required dependencies identified?
   - Are external services/APIs available and documented?
   - Are integration points well-defined?
   - What dependency risks exist?

3. **Technical Constraints**:
   - What technical limitations could impact the design?
   - Are performance requirements achievable?
   - Are there scalability considerations?
   - What infrastructure requirements exist?

4. **Implementation Risks**:
   - What could go wrong during implementation?
   - Where are the highest-risk technical areas?
   - What mitigation strategies are needed?

**Evaluation areas**:
- **Completeness**: Are technical requirements fully specified?
- **Architecture**: Is the technical approach sound?
- **Data Model**: Are data complexity factors addressed?
- **Interface Design**: Are integration points well-defined?

**SPECIFICATION TO REVIEW:**

{spec_content}

---

**Required Output Format** (Markdown):

{RESPONSE_SCHEMA}

**Note**: Focus on technical challenges and risks. Identify Major Suggestions for areas of hidden complexity and Critical Blockers for missing technical requirements.
"""
