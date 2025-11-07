"""
Unit tests for cache key generation.
"""

import pytest
from pathlib import Path
from claude_skills.common.cache import (
    generate_cache_key,
    generate_fidelity_review_key,
    generate_plan_review_key,
    is_cache_key_valid
)


def test_generate_cache_key_basic():
    """Test basic cache key generation."""
    key = generate_cache_key(spec_id="test-spec-001")

    # Should be valid hex string
    assert is_cache_key_valid(key)
    assert len(key) == 64  # SHA256 hex


def test_generate_cache_key_deterministic():
    """Test cache keys are deterministic."""
    key1 = generate_cache_key(
        spec_id="test-spec-001",
        model="gemini",
        prompt_version="v1"
    )
    key2 = generate_cache_key(
        spec_id="test-spec-001",
        model="gemini",
        prompt_version="v1"
    )

    assert key1 == key2


def test_generate_cache_key_different_specs():
    """Test different specs produce different keys."""
    key1 = generate_cache_key(spec_id="spec-001")
    key2 = generate_cache_key(spec_id="spec-002")

    assert key1 != key2


def test_generate_cache_key_different_models():
    """Test different models produce different keys."""
    key1 = generate_cache_key(spec_id="test-spec", model="gemini")
    key2 = generate_cache_key(spec_id="test-spec", model="codex")

    assert key1 != key2


def test_generate_cache_key_different_versions():
    """Test different prompt versions produce different keys."""
    key1 = generate_cache_key(spec_id="test-spec", prompt_version="v1")
    key2 = generate_cache_key(spec_id="test-spec", prompt_version="v2")

    assert key1 != key2


def test_generate_cache_key_with_files(tmp_path):
    """Test cache key includes file contents."""
    # Create test files
    file1 = tmp_path / "test1.py"
    file1.write_text("def test1(): pass")

    file2 = tmp_path / "test2.py"
    file2.write_text("def test2(): pass")

    key1 = generate_cache_key(
        spec_id="test-spec",
        file_paths=[str(file1), str(file2)]
    )

    # Modify file content
    file1.write_text("def test1(): return 42")

    key2 = generate_cache_key(
        spec_id="test-spec",
        file_paths=[str(file1), str(file2)]
    )

    # Keys should be different after file change
    assert key1 != key2


def test_generate_cache_key_file_order_deterministic(tmp_path):
    """Test file order doesn't affect key (sorted internally)."""
    file1 = tmp_path / "a.py"
    file1.write_text("content a")

    file2 = tmp_path / "b.py"
    file2.write_text("content b")

    key1 = generate_cache_key(
        spec_id="test-spec",
        file_paths=[str(file1), str(file2)]
    )

    key2 = generate_cache_key(
        spec_id="test-spec",
        file_paths=[str(file2), str(file1)]  # Reversed order
    )

    # Should be same (sorted internally)
    assert key1 == key2


def test_generate_cache_key_missing_file(tmp_path):
    """Test cache key generation with missing file."""
    missing_file = tmp_path / "missing.py"

    # Should not crash
    key = generate_cache_key(
        spec_id="test-spec",
        file_paths=[str(missing_file)]
    )

    assert is_cache_key_valid(key)


def test_generate_cache_key_with_extra_params():
    """Test cache key with extra parameters."""
    key1 = generate_cache_key(
        spec_id="test-spec",
        extra_params={"scope": "task", "target": "task-1-1"}
    )

    key2 = generate_cache_key(
        spec_id="test-spec",
        extra_params={"scope": "phase", "target": "task-1-1"}
    )

    # Different params should produce different keys
    assert key1 != key2


def test_generate_cache_key_extra_params_order():
    """Test extra params order doesn't affect key."""
    key1 = generate_cache_key(
        spec_id="test-spec",
        extra_params={"a": 1, "b": 2, "c": 3}
    )

    key2 = generate_cache_key(
        spec_id="test-spec",
        extra_params={"c": 3, "a": 1, "b": 2}  # Different order
    )

    # Should be same (sorted internally)
    assert key1 == key2


def test_generate_fidelity_review_key():
    """Test fidelity review key generation."""
    key = generate_fidelity_review_key(
        spec_id="test-spec-001",
        scope="task",
        target="task-1-1",
        model="gemini"
    )

    assert is_cache_key_valid(key)


def test_generate_fidelity_review_key_different_scopes():
    """Test different scopes produce different keys."""
    key1 = generate_fidelity_review_key(
        spec_id="test-spec",
        scope="task",
        target="task-1-1"
    )

    key2 = generate_fidelity_review_key(
        spec_id="test-spec",
        scope="phase",
        target="task-1-1"
    )

    assert key1 != key2


def test_generate_plan_review_key():
    """Test plan review key generation."""
    key = generate_plan_review_key(
        spec_id="test-spec-001",
        models=["gemini", "codex", "cursor-agent"]
    )

    assert is_cache_key_valid(key)


def test_generate_plan_review_key_models_order():
    """Test model order doesn't affect key."""
    key1 = generate_plan_review_key(
        spec_id="test-spec",
        models=["gemini", "codex"]
    )

    key2 = generate_plan_review_key(
        spec_id="test-spec",
        models=["codex", "gemini"]  # Reversed
    )

    # Should be same (sorted internally)
    assert key1 == key2


def test_generate_plan_review_key_with_focus():
    """Test plan review key with focus areas."""
    key1 = generate_plan_review_key(
        spec_id="test-spec",
        models=["gemini"],
        review_focus=["architecture"]
    )

    key2 = generate_plan_review_key(
        spec_id="test-spec",
        models=["gemini"],
        review_focus=["security"]
    )

    # Different focus should produce different keys
    assert key1 != key2


def test_is_cache_key_valid():
    """Test cache key validation."""
    # Valid key
    valid_key = "a" * 64
    assert is_cache_key_valid(valid_key)

    # Invalid: too short
    assert not is_cache_key_valid("abc123")

    # Invalid: too long
    assert not is_cache_key_valid("a" * 65)

    # Invalid: non-hex characters
    assert not is_cache_key_valid("z" * 64)

    # Invalid: empty
    assert not is_cache_key_valid("")

    # Invalid: None
    assert not is_cache_key_valid(None)


def test_generate_cache_key_complex_scenario(tmp_path):
    """Test complete cache key generation scenario."""
    # Create test files
    spec_file = tmp_path / "spec.json"
    spec_file.write_text('{"spec": "data"}')

    impl_file = tmp_path / "implementation.py"
    impl_file.write_text("def implement(): pass")

    # Generate key with all parameters
    key = generate_cache_key(
        spec_id="complex-spec-001",
        file_paths=[str(spec_file), str(impl_file)],
        model="gemini-pro",
        prompt_version="v2.1",
        extra_params={
            "scope": "phase",
            "target": "phase-2",
            "review_type": "comprehensive"
        }
    )

    assert is_cache_key_valid(key)

    # Same inputs should produce same key
    key2 = generate_cache_key(
        spec_id="complex-spec-001",
        file_paths=[str(spec_file), str(impl_file)],
        model="gemini-pro",
        prompt_version="v2.1",
        extra_params={
            "scope": "phase",
            "target": "phase-2",
            "review_type": "comprehensive"
        }
    )

    assert key == key2
