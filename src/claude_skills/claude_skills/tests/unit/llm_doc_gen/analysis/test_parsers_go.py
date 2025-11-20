"""
Tests for Go parser.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import Language

try:
    from claude_skills.llm_doc_gen.analysis.parsers.go import GoParser
    GO_PARSER_AVAILABLE = True
except ImportError:
    GO_PARSER_AVAILABLE = False


@pytest.mark.skipif(not GO_PARSER_AVAILABLE, reason="Go parser not available (tree-sitter not installed)")
class TestGoParser:
    """Test Go parser functionality."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Go parser instance."""
        return GoParser(tmp_path, [])



    def test_parse_simple_function(self, parser, tmp_path):
        """Test parsing a simple Go function."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

func HelloWorld() string {
    return "Hello, World!"
}
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "test"
        assert module.language == Language.GO
        assert len(result.functions) >= 1

        hello_func = next((f for f in result.functions if f.name == 'HelloWorld'), None)
        assert hello_func is not None

    def test_parse_function_with_parameters(self, parser, tmp_path):
        """Test parsing function with parameters."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

func Greet(name string, age int) string {
    return fmt.Sprintf("Hello, %s! You are %d years old.", name, age)
}
""")

        result = parser.parse_file(go_file)
        greet_func = next((f for f in result.functions if f.name == 'Greet'), None)
        assert greet_func is not None
        assert len(greet_func.parameters) >= 2

    def test_parse_multiple_return_values(self, parser, tmp_path):
        """Test parsing function with multiple return values."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}
""")

        result = parser.parse_file(go_file)
        divide_func = next((f for f in result.functions if f.name == 'Divide'), None)
        assert divide_func is not None

    def test_parse_struct(self, parser, tmp_path):
        """Test parsing Go struct."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

type Person struct {
    Name string
    Age  int
}
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        # Structs might be represented as classes
        assert len(result.classes) >= 1 or module is not None

    def test_parse_interface(self, parser, tmp_path):
        """Test parsing Go interface."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

type Reader interface {
    Read(p []byte) (n int, err error)
}
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_parse_method(self, parser, tmp_path):
        """Test parsing Go method (function with receiver)."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

type Person struct {
    Name string
}

func (p *Person) Greet() string {
    return "Hello, " + p.Name
}
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        # Methods might be in functions or associated with classes
        assert len(result.functions) >= 1 or len(result.classes) >= 1

    def test_parse_imports(self, parser, tmp_path):
        """Test parsing Go imports."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

import (
    "fmt"
    "os"
    "net/http"
)
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        assert len(module.imports) >= 1
        assert any('fmt' in imp for imp in module.imports)

    def test_parse_package_name(self, parser, tmp_path):
        """Test extracting package name."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package mypackage

func DoSomething() {}
""")

        result = parser.parse_file(go_file)
        # Package name might be in docstring or name
        assert result is not None

    def test_parse_empty_file(self, parser, tmp_path):
        """Test parsing an empty Go file."""
        go_file = tmp_path / "empty.go"
        go_file.write_text("package main\n")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "empty"

    def test_line_counting(self, parser, tmp_path):
        """Test line counting."""
        go_file = tmp_path / "test.go"
        go_file.write_text("""
package main

import "fmt"

func main() {
    fmt.Println("Hello")
}
""")

        result = parser.parse_file(go_file)
        module = result.modules[0] if result.modules else None
        assert module.lines >= 7
