import json
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture
def doc_query_samples(tmp_path: Path) -> Dict[str, Path]:
    """Create sample documentation payloads for doc_query tests."""
    modern = tmp_path / "modern" / "codebase.json"
    modern.parent.mkdir(parents=True, exist_ok=True)
    modern_payload = {
        "metadata": {
            "project_name": "example_project",
            "version": "1.0.0",
            "generated_at": "2025-10-20T14:26:20.967520",
            "language": "python"
        },
        "statistics": {
            "total_files": 1,
            "total_lines": 176,
            "total_classes": 2,
            "total_functions": 2,
            "avg_complexity": 5.0,
            "max_complexity": 8,
            "high_complexity_functions": ["batch_calculate"]
        },
        "modules": [
            {
                "name": "calculator",
                "file": "calculator.py",
                "docstring": "Example calculator module.",
                "classes": ["Calculator", "ScientificCalculator"],
                "functions": ["format_result", "batch_calculate"],
                "imports": ["typing.Union", "typing.List", "math"],
                "lines": 176
            }
        ],
        "classes": [
            {
                "name": "Calculator",
                "file": "calculator.py",
                "line": 10,
                "docstring": "Calculator class",
                "bases": [],
                "methods": ["add"],
                "properties": []
            },
            {
                "name": "ScientificCalculator",
                "file": "calculator.py",
                "line": 91,
                "docstring": "Scientific calculator",
                "bases": ["Calculator"],
                "methods": ["sin"],
                "properties": []
            }
        ],
        "functions": [
            {
                "name": "format_result",
                "file": "calculator.py",
                "line": 120,
                "docstring": "Format result",
                "parameters": [{"name": "value", "type": "Union[float, int]"}],
                "return_type": "str",
                "decorators": [],
                "complexity": 2,
                "is_async": False
            },
            {
                "name": "batch_calculate",
                "file": "calculator.py",
                "line": 136,
                "docstring": "Batch calculate",
                "parameters": [{"name": "calculator", "type": "Calculator"}],
                "return_type": "List[float]",
                "decorators": [],
                "complexity": 8,
                "is_async": False
            }
        ],
        "dependencies": {
            "calculator.py": ["typing.Union", "typing.List", "math"]
        }
    }
    modern.write_text(json.dumps(modern_payload, indent=2))

    legacy = tmp_path / "legacy" / "codebase.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {
        "generated_at": "2024-01-01T00:00:00",
        "project_name": "legacy_project",
        "version": "0.1.0",
        "classes": [
            {
                "name": "LegacyClass",
                "file": "legacy.py"
            }
        ],
        "functions": [
            {
                "name": "legacy_func",
                "file": "legacy.py",
                "complexity": 10
            }
        ],
        "dependencies": {
            "legacy.py": ["os"]
        }
    }
    legacy.write_text(json.dumps(legacy_payload, indent=2))

    return {"modern": modern, "legacy": legacy}
