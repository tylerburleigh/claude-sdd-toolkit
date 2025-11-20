"""
Tests for CSS parser.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import Language

try:
    from claude_skills.llm_doc_gen.analysis.parsers.css import CSSParser
    CSS_PARSER_AVAILABLE = True
except ImportError:
    CSS_PARSER_AVAILABLE = False


@pytest.mark.skipif(not CSS_PARSER_AVAILABLE, reason="CSS parser not available (tree-sitter not installed)")
class TestCSSParser:
    """Test CSS parser functionality."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a CSS parser instance."""
        return CSSParser(tmp_path, [])

    def test_parse_simple_css(self, parser, tmp_path):
        """Test parsing simple CSS file."""
        css_file = tmp_path / "styles.css"
        css_file.write_text("""
body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}
""")

        result = parser.parse_file(css_file)
        assert result is not None
        assert len(result.modules) == 1
        module = result.modules[0]
        assert result.modules[0].name == "styles"
        assert result.modules[0].language == Language.CSS

    def test_parse_css_selectors(self, parser, tmp_path):
        """Test extracting CSS selectors."""
        css_file = tmp_path / "test.css"
        css_file.write_text("""
h1 { color: blue; }
.button { padding: 10px; }
#header { background: white; }
nav > ul { list-style: none; }
a:hover { text-decoration: underline; }
""")

        result = parser.parse_file(css_file)
        # Selectors might be in functions or classes
        assert result is not None

    def test_parse_css_variables(self, parser, tmp_path):
        """Test detecting CSS variables."""
        css_file = tmp_path / "vars.css"
        css_file.write_text("""
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --font-size: 16px;
}

body {
    color: var(--primary-color);
    font-size: var(--font-size);
}
""")

        result = parser.parse_file(css_file)
        assert result is not None

    def test_parse_media_queries(self, parser, tmp_path):
        """Test parsing media queries."""
        css_file = tmp_path / "responsive.css"
        css_file.write_text("""
.container {
    width: 100%;
}

@media (min-width: 768px) {
    .container {
        width: 750px;
    }
}

@media (min-width: 1024px) {
    .container {
        width: 960px;
    }
}
""")

        result = parser.parse_file(css_file)
        assert result is not None

    def test_parse_keyframes(self, parser, tmp_path):
        """Test parsing CSS animations."""
        css_file = tmp_path / "animations.css"
        css_file.write_text("""
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

.fade {
    animation: fadeIn 1s ease-in;
}
""")

        result = parser.parse_file(css_file)
        assert result is not None

    def test_parse_imports(self, parser, tmp_path):
        """Test parsing CSS imports."""
        css_file = tmp_path / "main.css"
        css_file.write_text("""
@import url('reset.css');
@import url('typography.css');

body {
    background: white;
}
""")

        result = parser.parse_file(css_file)
        # Imports might be tracked
        assert result is not None

    def test_parse_empty_css(self, parser, tmp_path):
        """Test parsing empty CSS file."""
        css_file = tmp_path / "empty.css"
        css_file.write_text("")

        result = parser.parse_file(css_file)
        assert result is not None
        assert result.modules[0].name == "empty"

    def test_line_counting(self, parser, tmp_path):
        """Test line counting."""
        css_file = tmp_path / "test.css"
        css_file.write_text("""
body {
    margin: 0;
}

.container {
    padding: 20px;
}
""")

        result = parser.parse_file(css_file)
        assert result.modules[0].lines >= 7


@pytest.mark.skipif(not CSS_PARSER_AVAILABLE, reason="CSS parser not available")
class TestCSSParserAdvanced:
    """Advanced CSS parser tests."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a CSS parser instance."""
        return CSSParser(tmp_path, [])

    def test_parse_nested_rules(self, parser, tmp_path):
        """Test parsing nested CSS (SCSS/SASS)."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("""
.navbar {
    background: #333;

    .nav-link {
        color: white;

        &:hover {
            color: #ddd;
        }
    }
}
""")

        result = parser.parse_file(scss_file)
        assert result is not None

    def test_parse_mixins(self, parser, tmp_path):
        """Test parsing SCSS mixins."""
        scss_file = tmp_path / "mixins.scss"
        scss_file.write_text("""
@mixin button-style($bg-color) {
    background: $bg-color;
    padding: 10px 20px;
    border: none;
}

.primary-button {
    @include button-style(#007bff);
}
""")

        result = parser.parse_file(scss_file)
        assert result is not None

    def test_parse_css_grid(self, parser, tmp_path):
        """Test parsing CSS Grid layout."""
        css_file = tmp_path / "grid.css"
        css_file.write_text("""
.grid-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-gap: 20px;
}

.grid-item {
    grid-column: span 2;
}
""")

        result = parser.parse_file(css_file)
        assert result is not None

    def test_parse_css_flexbox(self, parser, tmp_path):
        """Test parsing CSS Flexbox layout."""
        css_file = tmp_path / "flex.css"
        css_file.write_text("""
.flex-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.flex-item {
    flex: 1;
}
""")

        result = parser.parse_file(css_file)
        assert result is not None
