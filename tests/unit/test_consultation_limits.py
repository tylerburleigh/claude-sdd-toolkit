import pytest
from claude_skills.common.consultation_limits import ConsultationTracker


def test_tracker_initialization():
    """Test tracker starts with empty tool set."""
    tracker = ConsultationTracker()
    assert tracker.get_count() == 0
    assert len(tracker.get_tools_used()) == 0


def test_record_consultation():
    """Test recording tool consultations."""
    tracker = ConsultationTracker()

    tracker.record_consultation("gemini")
    assert tracker.get_count() == 1
    assert "gemini" in tracker.get_tools_used()

    tracker.record_consultation("cursor-agent")
    assert tracker.get_count() == 2
    assert tracker.get_tools_used() == {"gemini", "cursor-agent"}


def test_record_same_tool_twice():
    """Test that recording the same tool twice doesn't increase count."""
    tracker = ConsultationTracker()

    tracker.record_consultation("gemini")
    tracker.record_consultation("gemini")

    assert tracker.get_count() == 1
    assert tracker.get_tools_used() == {"gemini"}


def test_check_limit_with_no_limit():
    """Test check_limit with None returns True."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")

    # No limit means always allowed
    assert tracker.check_limit("cursor-agent", None) is True


def test_check_limit_below_threshold():
    """Test check_limit returns True when under limit."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")

    # Limit of 3, used 1, should allow new tool
    assert tracker.check_limit("cursor-agent", 3) is True


def test_check_limit_at_threshold():
    """Test check_limit returns False when at limit."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    # Limit of 2, used 2, should reject new tool
    assert tracker.check_limit("codex", 2) is False


def test_check_limit_allows_existing_tool():
    """Test check_limit returns True for already-used tool."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    # Even at limit, should allow re-using existing tool
    assert tracker.check_limit("gemini", 2) is True


def test_reset():
    """Test reset clears all tracked tools."""
    tracker = ConsultationTracker()
    tracker.record_consultation("gemini")
    tracker.record_consultation("cursor-agent")

    tracker.reset()

    assert tracker.get_count() == 0
    assert len(tracker.get_tools_used()) == 0


def test_thread_safety():
    """Test tracker is thread-safe."""
    import threading

    tracker = ConsultationTracker()
    tools = ["gemini", "cursor-agent", "codex", "claude"]

    def record_tools():
        for tool in tools:
            tracker.record_consultation(tool)

    threads = [threading.Thread(target=record_tools) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have exactly 4 unique tools despite 40 recordings
    assert tracker.get_count() == 4
