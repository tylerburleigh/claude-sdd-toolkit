"""
Tests for Python parser.
"""

import pytest
from pathlib import Path
from claude_skills.code_doc.parsers.base import Language
from claude_skills.code_doc.parsers.python import PythonParser


class TestPythonParser:
    """Test Python parser functionality."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_parse_simple_function(self, parser, tmp_path):
        """Test parsing a simple function."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def hello_world():
    '''A simple greeting function'''
    return 'Hello, World!'
""")

        result = parser.parse_file(py_file)
        assert result is not None
        assert len(result.modules) == 1

        module = result.modules[0]
        assert module.name == "test"
        assert module.language == Language.PYTHON
        assert len(result.functions) >= 1

        # Find our function
        hello_func = next((f for f in result.functions if f.name == 'hello_world'), None)
        assert hello_func is not None
        assert 'greeting' in hello_func.docstring.lower()

    def test_parse_function_with_parameters(self, parser, tmp_path):
        """Test parsing function with parameters."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def greet(name: str, greeting: str = 'Hello') -> str:
    '''Greet someone by name'''
    return f'{greeting}, {name}!'
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        assert func.name == 'greet'
        assert len(func.parameters) >= 1
        # Check for name parameter
        name_param = next((p for p in func.parameters if p.name == 'name'), None)
        assert name_param is not None

    def test_parse_async_function(self, parser, tmp_path):
        """Test parsing async function."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
async def fetch_data():
    '''Async data fetcher'''
    return await get_data()
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        assert func.name == 'fetch_data'
        assert func.is_async is True

    def test_parse_function_with_decorators(self, parser, tmp_path):
        """Test parsing function with decorators."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
@staticmethod
@property
def my_property():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        assert func.name == 'my_property'
        assert len(func.decorators) >= 1

    def test_parse_simple_class(self, parser, tmp_path):
        """Test parsing a simple class."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Person:
    '''A person class'''

    def __init__(self, name):
        self.name = name

    def greet(self):
        return f'Hello, I am {self.name}'
""")

        result = parser.parse_file(py_file)
        assert len(result.classes) >= 1

        person_class = result.classes[0]
        assert person_class.name == 'Person'
        assert 'person' in person_class.docstring.lower()
        assert len(person_class.methods) >= 2

    def test_parse_class_with_inheritance(self, parser, tmp_path):
        """Test parsing class with base classes."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Animal:
    pass

class Dog(Animal):
    '''A dog class'''
    pass
""")

        result = parser.parse_file(py_file)
        dog_class = next((c for c in result.classes if c.name == 'Dog'), None)

        assert dog_class is not None
        assert len(dog_class.bases) >= 1
        assert 'Animal' in dog_class.bases

    def test_parse_class_with_properties(self, parser, tmp_path):
        """Test parsing class with properties."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Config:
    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value
""")

        result = parser.parse_file(py_file)
        config_class = result.classes[0]

        # Properties should be detected
        assert len(config_class.properties) >= 1 or len(config_class.methods) >= 1

    def test_parse_imports(self, parser, tmp_path):
        """Test parsing imports."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Dict, List
""")

        result = parser.parse_file(py_file)
        module = result.modules[0]
        assert len(module.imports) >= 2
        assert 'os' in module.imports or any('os' in imp for imp in module.imports)

    def test_parse_module_docstring(self, parser, tmp_path):
        """Test parsing module-level docstring."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
'''
This is a test module.
It has a docstring.
'''

def func():
    pass
""")

        result = parser.parse_file(py_file)
        module = result.modules[0]
        assert module.docstring is not None
        assert 'test module' in module.docstring.lower()

    def test_calculate_complexity(self, parser, tmp_path):
        """Test cyclomatic complexity calculation."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def complex_function(x):
    if x > 0:
        if x > 10:
            return 'big'
        else:
            return 'small'
    elif x < 0:
        return 'negative'
    else:
        return 'zero'
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Should have complexity > 1 due to multiple branches
        assert func.complexity > 1

    def test_parse_empty_file(self, parser, tmp_path):
        """Test parsing an empty Python file."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")

        result = parser.parse_file(py_file)
        assert result is not None
        assert len(result.modules) == 1
        module = result.modules[0]
        assert module.name == "empty"
        assert len(result.functions) == 0
        assert len(result.classes) == 0

    def test_parse_syntax_error_file(self, parser, tmp_path):
        """Test parsing file with syntax errors."""
        py_file = tmp_path / "bad.py"
        py_file.write_text("""
def broken(
    # Missing closing parenthesis
    pass
""")

        # Should handle gracefully
        result = parser.parse_file(py_file)
        # Implementation returns ParseResult with errors
        assert result is not None
        assert len(result.errors) > 0 or len(result.functions) == 0

    def test_line_counting(self, parser, tmp_path):
        """Test line counting."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
# Line 1
def func1():  # Line 2
    pass      # Line 3
              # Line 4
def func2():  # Line 5
    pass      # Line 6
""")

        result = parser.parse_file(py_file)
        module = result.modules[0]
        assert module.lines >= 6


class TestPythonParserAdvanced:
    """Advanced Python parser tests."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_parse_nested_classes(self, parser, tmp_path):
        """Test parsing nested classes."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Outer:
    class Inner:
        def inner_method(self):
            pass

    def outer_method(self):
        pass
""")

        result = parser.parse_file(py_file)
        # Should detect both Outer and potentially Inner
        assert len(result.classes) >= 1

    def test_parse_class_methods(self, parser, tmp_path):
        """Test parsing different types of methods."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    def instance_method(self):
        pass

    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method():
        pass
""")

        result = parser.parse_file(py_file)
        my_class = result.classes[0]
        assert len(my_class.methods) >= 3

    def test_parse_type_hints(self, parser, tmp_path):
        """Test parsing modern Python type hints."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
from typing import List, Dict, Optional

def process_data(items: List[str], config: Dict[str, int]) -> Optional[str]:
    '''Process data with type hints'''
    return items[0] if items else None
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]
        assert func.return_type is not None
