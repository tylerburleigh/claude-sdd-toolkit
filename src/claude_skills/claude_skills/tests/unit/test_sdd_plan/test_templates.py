#!/usr/bin/env python3
"""
Unit tests for sdd_plan.templates module.

Tests template management and task category inference.
"""

import pytest
from claude_skills.sdd_plan.templates import (
    infer_task_category,
    list_templates,
    get_template,
)


class TestInferTaskCategory:
    """Test cases for infer_task_category() function."""

    def test_investigation_keywords(self):
        """Test that investigation keywords are correctly identified."""
        test_cases = [
            "Analyze current authentication flow",
            "Understand the database schema",
            "Explore existing API endpoints",
            "Trace the user login process",
            "Map dependencies in auth module",
            "Investigate why tests are failing",
            "Review existing implementation",
            "Examine the caching strategy",
        ]
        for title in test_cases:
            assert infer_task_category(title) == "investigation", f"Failed for: {title}"

    def test_implementation_keywords(self):
        """Test that implementation keywords are correctly identified."""
        test_cases = [
            "Create user service",
            "Add authentication middleware",
            "Implement JWT token generation",
            "Build REST API endpoints",
            "Write password hashing logic",
            "Develop user registration flow",
            "Generate migration files",
            "Setup Redis connection",
        ]
        for title in test_cases:
            assert infer_task_category(title) == "implementation", f"Failed for: {title}"

    def test_refactoring_keywords(self):
        """Test that refactoring keywords are correctly identified."""
        test_cases = [
            "Extract validation to utility",
            "Refactor authentication service",
            "Reorganize folder structure",
            "Improve code quality in auth module",
            "Restructure database models",
            "Simplify error handling",
            "Split large controller file",
            "Consolidate duplicate code",
        ]
        for title in test_cases:
            assert infer_task_category(title) == "refactoring", f"Failed for: {title}"

    def test_decision_keywords(self):
        """Test that decision keywords are correctly identified."""
        test_cases = [
            "Choose between JWT vs sessions",
            "Decide on database schema approach",
            "Select authentication library",
            "Compare Redis vs Memcached",
            "Evaluate caching strategies",
            "Architectural decision for microservices",
            "Design choice for API versioning",
            "Determine approach for error handling",
        ]
        for title in test_cases:
            assert infer_task_category(title) == "decision", f"Failed for: {title}"

    def test_research_keywords(self):
        """Test that research keywords are correctly identified."""
        test_cases = [
            "Research OAuth 2.0 best practices",
            "Learn about GraphQL federation",
            "Read documentation on Redis clustering",
            "Gather information on GDPR compliance",
            "Explore external authentication providers",
            "Study external API patterns",  # Changed: "study existing" -> investigation
            "Review docs for TypeScript decorators",
        ]
        for title in test_cases:
            assert infer_task_category(title) == "research", f"Failed for: {title}"

    def test_default_fallback(self):
        """Test that ambiguous titles default to 'implementation'."""
        test_cases = [
            "User authentication",
            "Database optimization",
            "API versioning",
            "Update README",
            "",  # Empty string
        ]
        for title in test_cases:
            result = infer_task_category(title)
            assert result == "implementation", f"Failed for: '{title}', got: {result}"

    def test_case_insensitivity(self):
        """Test that keyword matching is case-insensitive."""
        test_cases = [
            ("ANALYZE authentication flow", "investigation"),
            ("Create USER service", "implementation"),
            ("REFACTOR auth module", "refactoring"),
            ("Choose BETWEEN jwt VS sessions", "decision"),
            ("RESEARCH oauth 2.0", "research"),
        ]
        for title, expected in test_cases:
            assert infer_task_category(title) == expected, f"Failed for: {title}"

    def test_priority_order(self):
        """Test that keywords are matched in the correct priority order."""
        # "analyze" (investigation) should take priority over "create" (implementation)
        assert infer_task_category("Analyze and create new service") == "investigation"

        # "refactor" should take priority over "implement"
        assert infer_task_category("Refactor and implement new feature") == "refactoring"

        # "decide" should take priority over "implement"
        assert infer_task_category("Decide and implement approach") == "decision"

    def test_empty_and_none_handling(self):
        """Test handling of empty strings and edge cases."""
        assert infer_task_category("") == "implementation"
        assert infer_task_category("   ") == "implementation"  # Whitespace only

    def test_task_type_parameter(self):
        """Test that task_type parameter is accepted (even if unused)."""
        # Should not raise an error and should ignore task_type for now
        assert infer_task_category("Create service", task_type="task") == "implementation"
        assert infer_task_category("Analyze flow", task_type="subtask") == "investigation"

    def test_multi_word_phrases(self):
        """Test that multi-word phrases are correctly matched."""
        # "review existing" is investigation, not just "review"
        assert infer_task_category("Review existing authentication") == "investigation"

        # "explore external" is research
        assert infer_task_category("Explore external API providers") == "research"

        # "improve code" is refactoring
        assert infer_task_category("Improve code structure") == "refactoring"


class TestTemplates:
    """Test cases for template management functions."""

    def test_list_templates_returns_dict(self):
        """Test that list_templates returns a dictionary."""
        templates = list_templates()
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_get_template_valid(self):
        """Test getting a valid template."""
        template = get_template("simple")
        assert template is not None
        assert "name" in template
        assert "phases" in template

    def test_get_template_invalid(self):
        """Test getting an invalid template returns None."""
        template = get_template("nonexistent")
        assert template is None


class TestGenerateSpecWithCategory:
    """Test cases for generate_spec_from_template with default_category."""

    def test_generate_spec_with_category(self):
        """Test that default_category is stored in spec metadata."""
        from claude_skills.sdd_plan.templates import generate_spec_from_template

        spec = generate_spec_from_template(
            template_id="simple",
            title="Test Spec",
            default_category="investigation"
        )

        assert spec is not None
        assert "metadata" in spec
        assert spec["metadata"]["default_category"] == "investigation"

    def test_generate_spec_without_category(self):
        """Test that spec can be generated without default_category."""
        from claude_skills.sdd_plan.templates import generate_spec_from_template

        spec = generate_spec_from_template(
            template_id="simple",
            title="Test Spec Without Category"
        )

        assert spec is not None
        assert "metadata" in spec
        # default_category should not be in metadata when not provided
        assert "default_category" not in spec["metadata"]

    def test_generate_spec_all_categories(self):
        """Test that all valid categories can be stored."""
        from claude_skills.sdd_plan.templates import generate_spec_from_template

        categories = ["investigation", "implementation", "refactoring", "decision", "research"]

        for category in categories:
            spec = generate_spec_from_template(
                template_id="simple",
                title=f"Test {category}",
                default_category=category
            )

            assert spec["metadata"]["default_category"] == category

    def test_generate_spec_category_none(self):
        """Test that None category is handled correctly."""
        from claude_skills.sdd_plan.templates import generate_spec_from_template

        # Explicitly pass None (same as not passing)
        spec = generate_spec_from_template(
            template_id="simple",
            title="Test None Category",
            default_category=None
        )

        assert spec is not None
        assert "metadata" in spec
        # default_category should not be in metadata when None
        assert "default_category" not in spec["metadata"]
