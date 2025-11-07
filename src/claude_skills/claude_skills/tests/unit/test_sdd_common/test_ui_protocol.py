"""
Unit tests for ui_protocol module.

Tests the Ui protocol definition, MessageLevel enum, and Message dataclass.
"""

import pytest
from datetime import datetime
from claude_skills.common.ui_protocol import Ui, MessageLevel, Message


class TestMessageLevel:
    """Tests for MessageLevel enum."""

    def test_message_level_values(self):
        """Test that all message levels have correct values."""
        assert MessageLevel.ACTION.value == "action"
        assert MessageLevel.SUCCESS.value == "success"
        assert MessageLevel.INFO.value == "info"
        assert MessageLevel.WARNING.value == "warning"
        assert MessageLevel.ERROR.value == "error"
        assert MessageLevel.DETAIL.value == "detail"
        assert MessageLevel.RESULT.value == "result"
        assert MessageLevel.ITEM.value == "item"
        assert MessageLevel.HEADER.value == "header"
        assert MessageLevel.BLANK.value == "blank"

    def test_message_level_count(self):
        """Test that we have all expected message levels."""
        # Should have exactly 10 levels
        assert len(MessageLevel) == 10

    def test_message_level_enum_members(self):
        """Test that message levels are enum members."""
        assert isinstance(MessageLevel.ACTION, MessageLevel)
        assert isinstance(MessageLevel.ERROR, MessageLevel)


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation_minimal(self):
        """Test creating message with minimal fields."""
        msg = Message(level=MessageLevel.INFO, text="Test message")

        assert msg.level == MessageLevel.INFO
        assert msg.text == "Test message"
        assert isinstance(msg.timestamp, datetime)
        assert msg.context == {}
        assert msg.metadata == {}
        assert msg.rendered is False

    def test_message_creation_full(self):
        """Test creating message with all fields."""
        timestamp = datetime.now()
        context = {"task_id": "task-1-1", "phase": "phase-1"}
        metadata = {"indent": 2, "key": "value"}

        msg = Message(
            level=MessageLevel.SUCCESS,
            text="Task completed",
            timestamp=timestamp,
            context=context,
            metadata=metadata,
            rendered=True
        )

        assert msg.level == MessageLevel.SUCCESS
        assert msg.text == "Task completed"
        assert msg.timestamp == timestamp
        assert msg.context == context
        assert msg.metadata == metadata
        assert msg.rendered is True

    def test_message_default_timestamp(self):
        """Test that message gets automatic timestamp."""
        msg = Message(level=MessageLevel.ACTION, text="Test")
        assert isinstance(msg.timestamp, datetime)

    def test_message_default_rendered_false(self):
        """Test that message is not rendered by default."""
        msg = Message(level=MessageLevel.INFO, text="Test")
        assert msg.rendered is False

    def test_message_context_mutable(self):
        """Test that message context can be modified."""
        msg = Message(level=MessageLevel.INFO, text="Test")
        msg.context["task_id"] = "task-1-1"

        assert "task_id" in msg.context
        assert msg.context["task_id"] == "task-1-1"

    def test_message_metadata_mutable(self):
        """Test that message metadata can be modified."""
        msg = Message(level=MessageLevel.DETAIL, text="Test")
        msg.metadata["indent"] = 3

        assert "indent" in msg.metadata
        assert msg.metadata["indent"] == 3


class TestUiProtocol:
    """Tests for Ui protocol definition."""

    def test_ui_is_runtime_checkable(self):
        """Test that Ui protocol is runtime checkable."""
        # This tests that we can use isinstance() with Ui protocol
        from claude_skills.common.ui_protocol import Ui as UiProtocol

        # Create a simple implementation
        class SimpleUi:
            def print_table(self, data, columns=None, title=None, **kwargs):
                pass

            def print_tree(self, data, label="Root", **kwargs):
                pass

            def print_diff(self, old_text, new_text, old_label="Original", new_label="Modified", **kwargs):
                pass

            def progress(self, description="Processing...", total=None, **kwargs):
                pass

            def print_panel(self, content, title=None, style="default", **kwargs):
                pass

            def print_status(self, message, level=MessageLevel.INFO, **kwargs):
                pass

        ui = SimpleUi()
        # Should be recognized as Ui implementation (structural subtyping)
        assert hasattr(ui, 'print_table')
        assert hasattr(ui, 'print_tree')
        assert hasattr(ui, 'print_diff')
        assert hasattr(ui, 'progress')
        assert hasattr(ui, 'print_panel')
        assert hasattr(ui, 'print_status')

    def test_ui_protocol_required_methods(self):
        """Test that Ui protocol defines all required methods."""
        # Check that the protocol has the expected methods
        import inspect
        from claude_skills.common.ui_protocol import Ui as UiProtocol

        # Get all abstract methods
        methods = [name for name, _ in inspect.getmembers(UiProtocol, predicate=inspect.isfunction)]

        # Should have all core UI methods
        expected_methods = [
            'print_table',
            'print_tree',
            'print_diff',
            'progress',
            'print_panel',
            'print_status'
        ]

        for method in expected_methods:
            assert method in methods, f"Ui protocol missing method: {method}"
