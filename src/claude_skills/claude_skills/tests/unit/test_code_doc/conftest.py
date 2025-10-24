"""
Pytest fixtures for code-doc tests.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def sample_modules():
    """Sample module data for testing framework and layer detection."""
    return [
        {
            'name': 'main',
            'file': 'app/main.py',
            'docstring': 'Main application entry point',
            'imports': ['fastapi', 'fastapi.FastAPI', 'fastapi.APIRouter'],
            'classes': ['App'],
            'functions': ['main', 'create_app'],
            'lines': 250
        },
        {
            'name': 'config',
            'file': 'app/config.py',
            'docstring': 'Application configuration',
            'imports': ['pydantic', 'pydantic.BaseSettings'],
            'classes': ['Settings'],
            'functions': [],
            'lines': 80
        },
        {
            'name': 'user_router',
            'file': 'app/routers/users.py',
            'docstring': None,
            'imports': ['fastapi.APIRouter', 'app.models.user'],
            'classes': [],
            'functions': ['get_user', 'create_user'],
            'lines': 120
        },
        {
            'name': 'user_model',
            'file': 'app/models/user.py',
            'docstring': 'User data models',
            'imports': ['pydantic.BaseModel', 'sqlalchemy'],
            'classes': ['User', 'UserCreate'],
            'functions': [],
            'lines': 90
        },
        {
            'name': 'user_service',
            'file': 'app/services/user_service.py',
            'docstring': 'User business logic',
            'imports': ['app.models.user', 'app.repositories.user'],
            'classes': ['UserService'],
            'functions': ['validate_user'],
            'lines': 150
        },
        {
            'name': 'user_repository',
            'file': 'app/repositories/user_repo.py',
            'docstring': None,
            'imports': ['sqlalchemy.orm', 'app.models.user'],
            'classes': ['UserRepository'],
            'functions': [],
            'lines': 100
        },
        {
            'name': 'helpers',
            'file': 'app/utils/helpers.py',
            'docstring': 'Utility functions',
            'imports': [],
            'classes': [],
            'functions': ['format_date', 'parse_json'],
            'lines': 60
        },
        {
            'name': 'auth_middleware',
            'file': 'app/middleware/auth.py',
            'docstring': 'Authentication middleware',
            'imports': ['starlette.middleware'],
            'classes': ['AuthMiddleware'],
            'functions': [],
            'lines': 75
        },
        {
            'name': 'test_users',
            'file': 'tests/test_users.py',
            'docstring': None,
            'imports': ['pytest', 'app.routers.users'],
            'classes': ['TestUserAPI'],
            'functions': ['test_create_user'],
            'lines': 200
        },
        {
            'name': 'deep_util',
            'file': 'app/utils/deep/nested/helper.py',
            'docstring': None,
            'imports': [],
            'classes': [],
            'functions': ['helper_func'],
            'lines': 30
        }
    ]


@pytest.fixture
def django_modules():
    """Sample Django module data."""
    return [
        {
            'name': 'settings',
            'file': 'myproject/settings.py',
            'docstring': 'Django settings',
            'imports': ['django.conf', 'django.db'],
            'classes': [],
            'functions': [],
            'lines': 150
        },
        {
            'name': 'views',
            'file': 'myapp/views.py',
            'docstring': None,
            'imports': ['django.views', 'django.http.HttpResponse'],
            'classes': ['UserView'],
            'functions': ['index'],
            'lines': 80
        }
    ]


@pytest.fixture
def flask_modules():
    """Sample Flask module data."""
    return [
        {
            'name': 'app',
            'file': 'app.py',
            'docstring': 'Flask application',
            'imports': ['flask', 'flask.Flask', 'flask.request'],
            'classes': [],
            'functions': ['create_app', 'index'],
            'lines': 100
        }
    ]


@pytest.fixture
def plain_modules():
    """Sample plain Python library (no framework)."""
    return [
        {
            'name': 'core',
            'file': 'mylib/core.py',
            'docstring': 'Core functionality',
            'imports': ['typing', 'dataclasses'],
            'classes': ['DataProcessor'],
            'functions': ['process'],
            'lines': 150
        },
        {
            'name': 'utils',
            'file': 'mylib/utils.py',
            'docstring': None,
            'imports': [],
            'classes': [],
            'functions': ['helper'],
            'lines': 50
        }
    ]


@pytest.fixture
def sample_statistics():
    """Sample code statistics."""
    return {
        'total_files': 45,
        'total_lines': 3421,
        'total_classes': 23,
        'total_functions': 156,
        'avg_complexity': 4.2,
        'max_complexity': 15,
        'high_complexity_functions': ['process_data (15)', 'validate (12)']
    }


@pytest.fixture
def sample_framework_info():
    """Sample framework detection result."""
    return {
        'detected': {'FastAPI': True, 'Pydantic': True, 'SQLAlchemy': True},
        'confidence': {'FastAPI': 1.0, 'Pydantic': 0.67, 'SQLAlchemy': 0.5},
        'primary': 'FastAPI',
        'type': 'web'
    }


@pytest.fixture
def sample_layers():
    """Sample layer detection result."""
    return {
        'routers': ['app/routers/users.py', 'app/routers/posts.py'],
        'models': ['app/models/user.py', 'app/models/post.py'],
        'services': ['app/services/user_service.py'],
        'repositories': ['app/repositories/user_repo.py'],
        'utils': ['app/utils/helpers.py'],
        'middleware': ['app/middleware/auth.py'],
        'config': ['app/config.py'],
        'tests': ['tests/test_users.py']
    }


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Mock subprocess.run for AI tool testing."""
    def _mock_run(*args, **kwargs):
        """Return mock successful AI response."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Mock AI generated documentation content"
        mock_result.stderr = ""
        return mock_result

    import subprocess
    monkeypatch.setattr(subprocess, 'run', _mock_run)
    return _mock_run


@pytest.fixture
def mock_subprocess_run_failure(monkeypatch):
    """Mock subprocess.run returning failure."""
    def _mock_run(*args, **kwargs):
        """Return mock failed AI response."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "AI tool error"
        return mock_result

    import subprocess
    monkeypatch.setattr(subprocess, 'run', _mock_run)
    return _mock_run


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with README."""
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n\nA test project for documentation generation.")

    main_py = tmp_path / "main.py"
    main_py.write_text("# Main entry point\ndef main():\n    pass\n")

    return tmp_path
