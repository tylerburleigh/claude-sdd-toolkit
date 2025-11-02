"""Tests for markdown parser."""

import pytest
from claude_skills.sdd_render.markdown_parser import (
    MarkdownParser,
    ParsedSpec,
    ParsedPhase,
    ParsedGroup,
    ParsedTask,
    ParsedVerification
)


# Sample markdown fixture
SAMPLE_SPEC_MARKDOWN = """# User Authentication System

**Spec ID:** `user-auth-2025-10-24-001`
**Status:** in_progress (5/23 tasks, 22%)
**Estimated Effort:** 40 hours
**Complexity:** medium

Implement comprehensive user authentication system with JWT tokens.

## Objectives

- Secure user login and registration
- JWT-based session management
- Password reset functionality

## Phase 1: Database Schema (2/5 tasks, 40%)

**Purpose:** Set up user data models
**Risk Level:** low
**Estimated Hours:** 8

### User Models (2/3 tasks)

#### ✅ Create User model

**File:** `src/models/User.ts`
**Status:** completed
**Estimated:** 2 hours
**Changes:** Define User schema with email, password hash, timestamps
**Reasoning:** Foundation for authentication system

#### 🔄 Add password hashing

**File:** `src/models/User.ts`
**Status:** in_progress
**Estimated:** 1.5 hours
**Changes:** Implement bcrypt password hashing on save

#### ⏳ Create index on email

**File:** `migrations/001_user_indexes.sql`
**Status:** pending
**Estimated:** 0.5 hours
**Changes:** Add unique index on email column
**Depends on:** task-1-1

### Verification Steps (0/2 tasks)

#### ⏳ Test user creation

**Status:** pending
**Type:** automated

**Command:**
```bash
npm test -- tests/models/user.test.ts
```

**Expected:** All user model tests pass

#### ⏳ Verify password hashing

**Status:** pending
**Type:** manual

**Expected:** Passwords stored as bcrypt hashes
"""


SAMPLE_NESTED_TASK_MARKDOWN = """#### ⏳ Implement auth service

**File:** `src/services/authService.ts`
**Status:** pending
**Estimated:** 3 hours
**Changes:** JWT generation and validation
**Reasoning:** Core authentication logic
**Details:** Includes token refresh mechanism

**Depends on:** task-1-1, task-1-2
**Blocked by:** task-2-1
"""


class TestMarkdownParser:
    """Tests for MarkdownParser class."""

    def test_parse_header(self):
        """Test parsing spec header."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        title, spec_id, metadata = parser._parse_header()

        assert title == "User Authentication System"
        assert spec_id == "user-auth-2025-10-24-001"
        assert metadata['status'] == "in_progress"
        assert metadata['completed_tasks'] == 5
        assert metadata['total_tasks'] == 23
        assert metadata['progress_pct'] == 22.0
        assert metadata['estimated_hours'] == 40.0
        assert metadata['complexity'] == "medium"
        assert "authentication system" in metadata['description']

    def test_parse_objectives(self):
        """Test parsing objectives section."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        objectives = parser._parse_objectives()

        assert len(objectives) == 3
        assert "Secure user login and registration" in objectives
        assert "JWT-based session management" in objectives
        assert "Password reset functionality" in objectives

    def test_parse_complete_spec(self):
        """Test parsing complete spec."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        spec = parser.parse()

        assert isinstance(spec, ParsedSpec)
        assert spec.title == "User Authentication System"
        assert spec.spec_id == "user-auth-2025-10-24-001"
        assert spec.status == "in_progress"
        assert spec.completed_tasks == 5
        assert spec.total_tasks == 23
        assert spec.progress_pct == 22.0
        assert len(spec.objectives) == 3
        assert len(spec.phases) == 1

    def test_parse_phase(self):
        """Test parsing phase section."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        phases = parser._parse_phases()

        assert len(phases) == 1
        phase = phases[0]

        assert isinstance(phase, ParsedPhase)
        assert phase.title == "Phase 1: Database Schema"
        assert phase.completed_tasks == 2
        assert phase.total_tasks == 5
        assert phase.progress_pct == 40.0
        assert phase.purpose == "Set up user data models"
        assert phase.risk_level == "low"
        assert phase.estimated_hours == 8.0
        assert len(phase.groups) == 2

    def test_parse_group(self):
        """Test parsing task group."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        phases = parser._parse_phases()
        groups = phases[0].groups

        assert len(groups) == 2

        # Test User Models group
        user_models = groups[0]
        assert isinstance(user_models, ParsedGroup)
        assert user_models.title == "User Models"
        assert user_models.completed_tasks == 2
        assert user_models.total_tasks == 3
        assert len(user_models.tasks) == 3

        # Test Verification group
        verify_group = groups[1]
        assert verify_group.title == "Verification Steps"
        assert len(verify_group.verifications) == 2

    def test_parse_task(self):
        """Test parsing individual task."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        phases = parser._parse_phases()
        tasks = phases[0].groups[0].tasks

        # Test completed task
        completed_task = tasks[0]
        assert isinstance(completed_task, ParsedTask)
        assert completed_task.title == "Create User model"
        assert completed_task.status == "completed"
        assert completed_task.file_path == "src/models/User.ts"
        assert completed_task.estimated_hours == 2.0
        assert "User schema" in completed_task.changes
        assert "Foundation" in completed_task.reasoning

        # Test in_progress task
        in_progress_task = tasks[1]
        assert in_progress_task.title == "Add password hashing"
        assert in_progress_task.status == "in_progress"

        # Test pending task with dependencies
        pending_task = tasks[2]
        assert pending_task.title == "Create index on email"
        assert pending_task.status == "pending"
        assert "task-1-1" in pending_task.depends_on

    def test_parse_task_with_all_fields(self):
        """Test parsing task with all possible fields."""
        parser = MarkdownParser(SAMPLE_NESTED_TASK_MARKDOWN)
        task = parser._parse_task(SAMPLE_NESTED_TASK_MARKDOWN)

        assert task.title == "Implement auth service"
        assert task.status == "pending"
        assert task.file_path == "src/services/authService.ts"
        assert task.estimated_hours == 3.0
        assert "JWT generation" in task.changes
        assert "Core authentication" in task.reasoning
        assert "token refresh" in task.details
        assert "task-1-1" in task.depends_on
        assert "task-1-2" in task.depends_on
        assert "task-2-1" in task.blocked_by

    def test_parse_verification(self):
        """Test parsing verification steps."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        phases = parser._parse_phases()
        verifications = phases[0].groups[1].verifications

        assert len(verifications) == 2

        # Test automated verification
        auto_verify = verifications[0]
        assert isinstance(auto_verify, ParsedVerification)
        assert auto_verify.title == "Test user creation"
        assert auto_verify.status == "pending"
        assert auto_verify.verification_type == "automated"
        assert "npm test" in auto_verify.command
        assert "tests pass" in auto_verify.expected

        # Test manual verification
        manual_verify = verifications[1]
        assert manual_verify.title == "Verify password hashing"
        assert manual_verify.verification_type == "manual"
        assert manual_verify.command is None
        assert "bcrypt" in manual_verify.expected

    def test_parse_empty_spec(self):
        """Test parsing spec with minimal content."""
        minimal_markdown = """# Minimal Spec

**Spec ID:** `minimal-001`
**Status:** pending (0/1 tasks, 0%)
"""
        parser = MarkdownParser(minimal_markdown)
        spec = parser.parse()

        assert spec.title == "Minimal Spec"
        assert spec.spec_id == "minimal-001"
        assert spec.status == "pending"
        assert len(spec.objectives) == 0
        assert len(spec.phases) == 0

    def test_parse_task_status_icons(self):
        """Test parsing different task status icons."""
        markdown_with_statuses = """### Tasks (5/5 tasks)

#### ⏳ Pending task

**Status:** pending

#### 🔄 In progress task

**Status:** in_progress

#### ✅ Completed task

**Status:** completed

#### 🚫 Blocked task

**Status:** blocked

#### ❌ Failed task

**Status:** failed
"""
        parser = MarkdownParser(markdown_with_statuses)
        group = parser._parse_group(markdown_with_statuses)

        assert len(group.tasks) == 5
        assert group.tasks[0].status == "pending"
        assert group.tasks[1].status == "in_progress"
        assert group.tasks[2].status == "completed"
        assert group.tasks[3].status == "blocked"
        assert group.tasks[4].status == "failed"

    def test_parse_preserves_raw_markdown(self):
        """Test that raw markdown is preserved in parsed objects."""
        parser = MarkdownParser(SAMPLE_SPEC_MARKDOWN)
        spec = parser.parse()

        assert spec.raw_markdown == SAMPLE_SPEC_MARKDOWN
        assert len(spec.phases[0].raw_markdown) > 0
        assert len(spec.phases[0].groups[0].raw_markdown) > 0
        assert len(spec.phases[0].groups[0].tasks[0].raw_markdown) > 0


class TestMarkdownParserEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_phase_without_progress(self):
        """Test parsing phase header without progress info."""
        markdown = """## Phase 1: Setup

**Purpose:** Initial setup
"""
        parser = MarkdownParser(markdown)
        phase = parser._parse_phase(markdown)

        assert phase.title == "Phase 1: Setup"
        assert phase.completed_tasks == 0
        assert phase.total_tasks == 0

    def test_parse_task_without_file_path(self):
        """Test parsing task without file path."""
        markdown = """#### ⏳ General task

**Status:** pending
**Changes:** Do something
"""
        parser = MarkdownParser(markdown)
        task = parser._parse_task(markdown)

        assert task.title == "General task"
        assert task.file_path is None
        assert "Do something" in task.changes

    def test_parse_verification_without_command(self):
        """Test parsing manual verification without command."""
        markdown = """#### ⏳ Manual check

**Status:** pending
**Type:** manual
**Expected:** Something should work
"""
        parser = MarkdownParser(markdown)
        verify = parser._parse_verification(markdown)

        assert verify.title == "Manual check"
        assert verify.verification_type == "manual"
        assert verify.command is None
        assert "should work" in verify.expected

    def test_parse_multiple_phases(self):
        """Test parsing spec with multiple phases."""
        markdown = """# Multi-Phase Spec

**Spec ID:** `multi-001`
**Status:** pending (0/10 tasks, 0%)

## Phase 1: First (0/5 tasks, 0%)

### Tasks (0/5 tasks)

## Phase 2: Second (0/3 tasks, 0%)

### Tasks (0/3 tasks)

## Phase 3: Third (0/2 tasks, 0%)

### Tasks (0/2 tasks)
"""
        parser = MarkdownParser(markdown)
        spec = parser.parse()

        assert len(spec.phases) == 3
        assert spec.phases[0].title == "Phase 1: First"
        assert spec.phases[1].title == "Phase 2: Second"
        assert spec.phases[2].title == "Phase 3: Third"
