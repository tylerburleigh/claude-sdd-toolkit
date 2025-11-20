"""
Shared fixtures for code-doc unit tests.

These helpers provide consistent sample module metadata, temporary project
structures, and tool execution stubs so the detectors and consultation helpers
can run without requiring a real repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest

from claude_skills.llm_doc_gen.analysis import detectors
from claude_skills.common.ai_tools import ToolResponse, ToolStatus


def _module(
    file_path: str,
    *,
    imports: Iterable[str] | None = None,
    docstring: str = "",
    classes: Iterable[dict] | None = None,
    functions: Iterable[dict] | None = None,
    lines: int = 100,
):
    """Utility to build module dictionaries used by detectors."""
    return {
        "name": file_path.replace("/", ".").rstrip(".py"),
        "file": file_path,
        "imports": list(imports or []),
        "docstring": docstring,
        "classes": list(classes or []),
        "functions": list(functions or []),
        "exports": [],
        "lines": lines,
    }


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a throwaway project directory with a README and entry file."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    (project_dir / "README.md").write_text("# Test Project\n\nSample documentation.", encoding="utf-8")
    (project_dir / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project_dir / "app").mkdir()
    (project_dir / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")

    return project_dir


@pytest.fixture
def sample_modules() -> list[dict]:
    """Provide representative module metadata for a FastAPI-style project."""
    return [
        _module(
            "app/main.py",
            imports=["fastapi", "fastapi.FastAPI", "fastapi.APIRouter", "pydantic", "app.config", "app.routers.users"],
            docstring="FastAPI entry point.",
            functions=[{"name": "create_app"}],
        ),
        _module(
            "app/config.py",
            imports=["pydantic"],
            docstring="Application configuration.",
            classes=[{"name": "Settings"}],
        ),
        _module(
            "app/routers/users.py",
            imports=["fastapi", "app.services.user_service"],
            docstring="User routes.",
            functions=[{"name": "list_users"}],
        ),
        _module(
            "app/models/user.py",
            imports=["pydantic"],
            docstring="User models.",
            classes=[{"name": "User"}, {"name": "UserCreate"}, {"name": "UserUpdate"}],
            functions=[{"name": "as_dict"}],
        ),
        _module(
            "app/services/user_service.py",
            imports=["app.repositories.user_repo"],
            docstring="Service layer.",
            functions=[{"name": "get_user"}],
        ),
        _module(
            "app/repositories/user_repo.py",
            imports=["sqlalchemy"],
            docstring="Data access layer.",
            functions=[{"name": "fetch_user"}],
        ),
        _module(
            "app/utils/helpers.py",
            imports=["logging"],
            docstring="Helper utilities.",
            functions=[{"name": "slugify"}],
        ),
        _module(
            "app/middleware/auth.py",
            imports=["fastapi"],
            docstring="Auth middleware.",
            classes=[{"name": "AuthMiddleware"}],
        ),
        _module(
            "tests/test_users.py",
            imports=["pytest"],
            docstring="Tests.",
            functions=[{"name": "test_user_flow"}],
        ),
        _module(
            "app/deep/nested/feature.py",
            imports=["typing"],
            docstring="Deep feature file.",
            functions=[{"name": "feature_flag"}],
        ),
    ]


@pytest.fixture
def django_modules() -> list[dict]:
    """Sample modules that resemble a Django project."""
    return [
        _module(
            "project/settings.py",
            imports=["django", "django.conf"],
            docstring="Django settings.",
        ),
        _module(
            "project/urls.py",
            imports=["django.urls"],
            docstring="URL configuration.",
            functions=[{"name": "urlpatterns"}],
        ),
    ]


@pytest.fixture
def flask_modules() -> list[dict]:
    """Sample modules for a Flask project."""
    return [
        _module(
            "app/__init__.py",
            imports=["flask"],
            docstring="Flask factory.",
            functions=[{"name": "create_app"}],
        ),
        _module(
            "app/routes.py",
            imports=["flask"],
            docstring="Route definitions.",
            functions=[{"name": "register_routes"}],
        ),
    ]


@pytest.fixture
def plain_modules() -> list[dict]:
    """Modules with no recognizable framework."""
    return [
        _module("lib/core.py", imports=["math"]),
        _module("lib/helpers.py", imports=["itertools"]),
    ]


@pytest.fixture
def sample_framework_info(sample_modules: list[dict]) -> dict:
    """Detect frameworks from the shared sample modules."""
    return detectors.detect_framework(sample_modules)


@pytest.fixture
def sample_layers(sample_modules: list[dict]) -> dict:
    """Layer grouping derived from the shared sample modules."""
    return detectors.detect_layers(sample_modules)


@pytest.fixture
def sample_statistics(sample_modules: list[dict]) -> dict:
    """Lightweight statistics payload used by context summary tests."""
    total_classes = sum(len(m.get("classes", [])) for m in sample_modules)
    total_functions = sum(len(m.get("functions", [])) for m in sample_modules)
    total_lines = sum(m.get("lines", 0) for m in sample_modules)
    return {
        "total_files": len(sample_modules),
        "total_lines": total_lines or 500,
        "total_classes": total_classes,
        "total_functions": total_functions,
        "avg_complexity": 3.2,
    }


@pytest.fixture
def mock_execute_tool(monkeypatch: pytest.MonkeyPatch) -> ToolResponse:
    """Patch execute_tool_with_fallback to simulate a successful call."""
    response = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="Mock AI response",
        duration=1.0,
    )

    monkeypatch.setattr(
        "claude_skills.llm_doc_gen.analysis.ai_consultation.execute_tool_with_fallback",
        lambda *args, **kwargs: response,
    )
    return response


@pytest.fixture
def mock_execute_tool_failure(monkeypatch: pytest.MonkeyPatch) -> ToolResponse:
    """Patch execute_tool_with_fallback to simulate a failing call."""
    response = ToolResponse(
        tool="gemini",
        status=ToolStatus.ERROR,
        output="",
        error="Simulated execution error",
        duration=1.0,
    )

    monkeypatch.setattr(
        "claude_skills.llm_doc_gen.analysis.ai_consultation.execute_tool_with_fallback",
        lambda *args, **kwargs: response,
    )
    return response
