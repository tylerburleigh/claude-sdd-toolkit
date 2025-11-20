"""
Tests for base parser interface and data structures.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import (
    Language,
    ParsedParameter,
    ParsedFunction,
    ParsedClass,
    ParsedModule,
    ParseResult,
    BaseParser
)


class TestLanguageEnum:
    """Test Language enum."""

    def test_language_values(self):
        """Test all expected languages are defined."""
        expected_languages = {
            'python', 'javascript', 'typescript',
            'go', 'html', 'css', 'unknown'
        }
        actual_languages = {lang.value for lang in Language}
        assert actual_languages == expected_languages

    def test_language_from_string(self):
        """Test creating Language from string value."""
        assert Language('python') == Language.PYTHON
        assert Language('javascript') == Language.JAVASCRIPT
        assert Language('unknown') == Language.UNKNOWN


class TestParsedDataStructures:
    """Test parsed data structures."""

    def test_parsed_parameter_creation(self):
        """Test ParsedParameter dataclass."""
        param = ParsedParameter(name="arg1", type="str", default="test")
        assert param.name == "arg1"
        assert param.type == "str"
        assert param.default == "test"

    def test_parsed_function_creation(self):
        """Test ParsedFunction dataclass."""
        func = ParsedFunction(
            name="test_func",
            file="test.py",
            line=10,
            language=Language.PYTHON,
            docstring="Test function",
            parameters=[ParsedParameter(name="arg1", type="str")],
            return_type="bool",
            decorators=["@staticmethod"],
            is_async=True,
            complexity=5
        )
        assert func.name == "test_func"
        assert func.line == 10
        assert func.is_async is True
        assert func.complexity == 5
        assert len(func.parameters) == 1

    def test_parsed_class_creation(self):
        """Test ParsedClass dataclass."""
        cls = ParsedClass(
            name="TestClass",
            file="test.py",
            line=20,
            language=Language.PYTHON,
            docstring="Test class",
            bases=["BaseClass"],
            methods=["method1", "method2"],
            properties=["prop1"]
        )
        assert cls.name == "TestClass"
        assert cls.line == 20
        assert len(cls.bases) == 1
        assert len(cls.methods) == 2
        assert len(cls.properties) == 1

    def test_parsed_module_creation(self):
        """Test ParsedModule dataclass."""
        module = ParsedModule(
            name="test_module",
            file="test/module.py",
            language=Language.PYTHON,
            docstring="Test module",
            imports=["os", "sys"],
            classes=[],
            functions=[],
            exports=[],
            lines=100
        )
        assert module.name == "test_module"
        assert module.language == Language.PYTHON
        assert module.lines == 100
        assert len(module.imports) == 2


class TestParseResult:
    """Test ParseResult aggregation."""

    def test_empty_parse_result(self):
        """Test creating empty ParseResult."""
        result = ParseResult()
        assert len(result.modules) == 0
        assert len(result.classes) == 0
        assert len(result.functions) == 0
        assert len(result.dependencies) == 0

    def test_parse_result_with_data(self):
        """Test ParseResult with actual data."""
        module = ParsedModule(
            name="test",
            file="test.py",
            language=Language.PYTHON,
            imports=["os"],
            classes=[],
            functions=[],
            exports=[],
            lines=50
        )

        result = ParseResult()
        result.modules.append(module)

        assert len(result.modules) == 1
        assert result.modules[0].name == "test"

    def test_parse_result_merge(self):
        """Test merging multiple ParseResults."""
        result1 = ParseResult()
        module1 = ParsedModule(
            name="mod1", file="mod1.py", language=Language.PYTHON,
            imports=[], classes=[], functions=[], exports=[], lines=10
        )
        result1.modules.append(module1)

        result2 = ParseResult()
        module2 = ParsedModule(
            name="mod2", file="mod2.js", language=Language.JAVASCRIPT,
            imports=[], classes=[], functions=[], exports=[], lines=20
        )
        result2.modules.append(module2)

        # Merge results
        result1.modules.extend(result2.modules)

        assert len(result1.modules) == 2
        assert result1.modules[0].language == Language.PYTHON
        assert result1.modules[1].language == Language.JAVASCRIPT


class TestBaseParser:
    """Test BaseParser abstract class."""

    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseParser(Path("/tmp"), [])

    def test_base_parser_interface(self):
        """Test that BaseParser defines required methods and properties."""
        # Verify abstract methods and properties exist
        assert hasattr(BaseParser, 'parse_file')
        assert hasattr(BaseParser, 'language')
        assert hasattr(BaseParser, 'file_extensions')
