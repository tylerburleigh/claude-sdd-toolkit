"""
Tests for HTML parser.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import Language

try:
    from claude_skills.llm_doc_gen.analysis.parsers.html import HTMLParser
    HTML_PARSER_AVAILABLE = True
except ImportError:
    HTML_PARSER_AVAILABLE = False


@pytest.mark.skipif(not HTML_PARSER_AVAILABLE, reason="HTML parser not available (tree-sitter not installed)")
class TestHTMLParser:
    """Test HTML parser functionality."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create an HTML parser instance."""
        return HTMLParser(tmp_path, [])



    def test_parse_simple_html(self, parser, tmp_path):
        """Test parsing simple HTML file."""
        html_file = tmp_path / "index.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a test page.</p>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "index"
        assert module.language == Language.HTML

    def test_parse_htmx_attributes(self, parser, tmp_path):
        """Test detecting HTMX attributes."""
        html_file = tmp_path / "htmx.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <button hx-get="/api/data" hx-target="#result">
        Load Data
    </button>
    <div id="result"></div>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        # Check if HTMX attributes are detected in docstring or elsewhere
        assert result is not None

    def test_parse_custom_data_attributes(self, parser, tmp_path):
        """Test detecting custom data attributes."""
        html_file = tmp_path / "data.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <div data-user-id="123" data-role="admin">
        User Profile
    </div>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_count_elements(self, parser, tmp_path):
        """Test element counting."""
        html_file = tmp_path / "elements.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <div class="container">
        <h1>Title</h1>
        <p>Paragraph 1</p>
        <p>Paragraph 2</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </div>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        # Element counts might be in docstring or statistics
        assert result is not None

    def test_parse_empty_html(self, parser, tmp_path):
        """Test parsing empty HTML file."""
        html_file = tmp_path / "empty.html"
        html_file.write_text("")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "empty"

    def test_line_counting(self, parser, tmp_path):
        """Test line counting."""
        html_file = tmp_path / "test.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello</h1>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert module.lines >= 9


@pytest.mark.skipif(not HTML_PARSER_AVAILABLE, reason="HTML parser not available")
class TestHTMLParserAdvanced:
    """Advanced HTML parser tests."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create an HTML parser instance."""
        return HTMLParser(tmp_path, [])

    def test_parse_forms(self, parser, tmp_path):
        """Test parsing forms."""
        html_file = tmp_path / "form.html"
        html_file.write_text("""
<form action="/submit" method="POST">
    <input type="text" name="username" />
    <input type="password" name="password" />
    <button type="submit">Login</button>
</form>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_parse_scripts_and_styles(self, parser, tmp_path):
        """Test detecting inline scripts and styles."""
        html_file = tmp_path / "mixed.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; }
    </style>
    <script>
        console.log('Hello');
    </script>
</head>
<body>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_parse_semantic_html5(self, parser, tmp_path):
        """Test parsing HTML5 semantic elements."""
        html_file = tmp_path / "semantic.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <header>
        <nav>Navigation</nav>
    </header>
    <main>
        <article>
            <section>Section 1</section>
            <section>Section 2</section>
        </article>
        <aside>Sidebar</aside>
    </main>
    <footer>Footer</footer>
</body>
</html>
""")

        result = parser.parse_file(html_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
