"""
Cache key generation utilities.

Generates deterministic cache keys based on spec ID, file contents, model, and prompt version.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Optional, Dict, Any


def generate_cache_key(
    spec_id: str,
    file_paths: Optional[List[str]] = None,
    model: Optional[str] = None,
    prompt_version: str = "v1",
    extra_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate deterministic cache key based on consultation inputs.

    The cache key includes:
    - Spec ID
    - Hash of file contents (if file paths provided)
    - Model name
    - Prompt version (for cache invalidation on prompt changes)
    - Extra parameters (optional)

    Args:
        spec_id: Specification identifier
        file_paths: List of file paths to include in hash (optional)
        model: Model name (e.g., "gemini", "codex")
        prompt_version: Version identifier for prompt template (default: "v1")
        extra_params: Additional parameters to include in key (optional)

    Returns:
        Deterministic cache key (hex string)

    Example:
        key = generate_cache_key(
            spec_id="my-spec-001",
            file_paths=["src/auth.py", "tests/test_auth.py"],
            model="gemini",
            prompt_version="v2"
        )
    """
    # Build hashable components
    components = {
        "spec_id": spec_id,
        "model": model or "default",
        "prompt_version": prompt_version
    }

    # Add file contents hash if files provided
    if file_paths:
        file_hash = _hash_files(file_paths)
        components["file_hash"] = file_hash

    # Add extra parameters if provided
    if extra_params:
        # Sort keys for deterministic ordering
        components["extra"] = {k: extra_params[k] for k in sorted(extra_params.keys())}

    # Generate hash from components
    components_json = json.dumps(components, sort_keys=True)
    hash_obj = hashlib.sha256(components_json.encode("utf-8"))
    cache_key = hash_obj.hexdigest()

    return cache_key


def _hash_files(file_paths: List[str]) -> str:
    """
    Generate hash of file contents.

    Args:
        file_paths: List of file paths to hash

    Returns:
        Hex string hash of all file contents combined

    Note:
        If a file doesn't exist or can't be read, it's skipped with a warning marker.
        This ensures cache keys can still be generated even with missing files.
    """
    hasher = hashlib.sha256()

    for file_path in sorted(file_paths):  # Sort for deterministic ordering
        try:
            path = Path(file_path)
            if path.exists():
                hasher.update(file_path.encode("utf-8"))  # Include filename
                hasher.update(path.read_bytes())  # Include content
            else:
                # File doesn't exist - include marker in hash
                hasher.update(f"MISSING:{file_path}".encode("utf-8"))
        except Exception as e:
            # Error reading file - include error marker in hash
            hasher.update(f"ERROR:{file_path}:{str(e)}".encode("utf-8"))

    return hasher.hexdigest()


def generate_fidelity_review_key(
    spec_id: str,
    scope: str,
    target: str,
    file_paths: Optional[List[str]] = None,
    model: Optional[str] = None
) -> str:
    """
    Generate cache key for fidelity review consultations.

    Args:
        spec_id: Specification identifier
        scope: Review scope ("task", "phase", or "spec")
        target: Target identifier (task ID, phase ID, or spec ID)
        file_paths: Files being reviewed (optional)
        model: Model name (optional)

    Returns:
        Deterministic cache key
    """
    extra_params = {
        "scope": scope,
        "target": target,
        "review_type": "fidelity"
    }

    return generate_cache_key(
        spec_id=spec_id,
        file_paths=file_paths,
        model=model,
        prompt_version="fidelity-v1",
        extra_params=extra_params
    )


def generate_plan_review_key(
    spec_id: str,
    models: List[str],
    review_focus: Optional[List[str]] = None
) -> str:
    """
    Generate cache key for plan review consultations.

    Args:
        spec_id: Specification identifier
        models: List of models consulted
        review_focus: Focus areas (e.g., ["architecture", "security"])

    Returns:
        Deterministic cache key
    """
    extra_params = {
        "models": sorted(models),  # Sort for deterministic ordering
        "review_type": "plan"
    }

    if review_focus:
        extra_params["focus"] = sorted(review_focus)

    return generate_cache_key(
        spec_id=spec_id,
        model=",".join(sorted(models)),  # Composite model key
        prompt_version="plan-review-v1",
        extra_params=extra_params
    )


def is_cache_key_valid(key: str) -> bool:
    """
    Validate cache key format.

    Args:
        key: Cache key to validate

    Returns:
        True if key is a valid hex string of appropriate length
    """
    if not key:
        return False

    # SHA256 produces 64 hex characters
    if len(key) != 64:
        return False

    # Check all characters are hex
    try:
        int(key, 16)
        return True
    except ValueError:
        return False
