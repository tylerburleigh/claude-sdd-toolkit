"""
Tests for JavaScript/TypeScript parser.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import Language

try:
    from claude_skills.llm_doc_gen.analysis.parsers.javascript import JavaScriptParser
    JAVASCRIPT_PARSER_AVAILABLE = True
except ImportError:
    JAVASCRIPT_PARSER_AVAILABLE = False


@pytest.mark.skipif(not JAVASCRIPT_PARSER_AVAILABLE, reason="JavaScript parser not available (tree-sitter not installed)")
class TestJavaScriptParser:
    """Test JavaScript parser functionality."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a JavaScript parser instance."""
        return JavaScriptParser(tmp_path, [])




    def test_parse_simple_function(self, parser, tmp_path):
        """Test parsing a simple JavaScript function."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
function helloWorld() {
    return 'Hello, World!';
}
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "test"
        assert module.language == Language.JAVASCRIPT
        assert len(result.functions) >= 1

        hello_func = next((f for f in result.functions if f.name == 'helloWorld'), None)
        assert hello_func is not None

    def test_parse_arrow_function(self, parser, tmp_path):
        """Test parsing arrow functions."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
const greet = (name) => {
    return `Hello, ${name}!`;
};

const add = (a, b) => a + b;
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert len(module.functions) >= 1

    def test_parse_async_function(self, parser, tmp_path):
        """Test parsing async function."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
async function fetchData() {
    const response = await fetch('/api/data');
    return response.json();
}
""")

        result = parser.parse_file(js_file)
        func = next((f for f in result.functions if f.name == 'fetchData'), None)
        assert func is not None
        assert func.is_async is True

    def test_parse_simple_class(self, parser, tmp_path):
        """Test parsing a JavaScript class."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
class Person {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, I am ${this.name}`;
    }
}
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert len(result.classes) >= 1

        person_class = result.classes[0]
        assert person_class.name == 'Person'
        assert len(person_class.methods) >= 1

    def test_parse_class_with_inheritance(self, parser, tmp_path):
        """Test parsing class with extends."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
class Animal {
    move() {
        return 'moving';
    }
}

class Dog extends Animal {
    bark() {
        return 'woof';
    }
}
""")

        result = parser.parse_file(js_file)
        dog_class = next((c for c in result.classes if c.name == 'Dog'), None)
        assert dog_class is not None
        assert len(dog_class.bases) >= 1
        assert 'Animal' in dog_class.bases

    def test_parse_imports(self, parser, tmp_path):
        """Test parsing ES6 imports."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert len(module.imports) >= 1
        assert any('react' in imp.lower() for imp in module.imports)

    def test_parse_exports(self, parser, tmp_path):
        """Test parsing exports."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
export function helper() {
    return 'help';
}

export default class Main {
    run() {}
}
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert len(module.exports) >= 1

    def test_parse_typescript_types(self, parser, tmp_path):
        """Test parsing TypeScript with type annotations."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
interface User {
    name: string;
    age: number;
}

function greet(user: User): string {
    return `Hello, ${user.name}`;
}
""")

        result = parser.parse_file(ts_file)
        module = result.modules[0] if result.modules else None
        assert module.language == Language.TYPESCRIPT
        assert len(module.functions) >= 1

    def test_parse_jsx_component(self, parser, tmp_path):
        """Test parsing JSX/React component."""
        jsx_file = tmp_path / "Component.jsx"
        jsx_file.write_text("""
import React from 'react';

function MyComponent(props) {
    return (
        <div className="container">
            <h1>{props.title}</h1>
        </div>
    );
}

export default MyComponent;
""")

        result = parser.parse_file(jsx_file)
        module = result.modules[0] if result.modules else None
        assert module.language == Language.JAVASCRIPT
        assert len(module.functions) >= 1

    def test_parse_empty_file(self, parser, tmp_path):
        """Test parsing an empty JavaScript file."""
        js_file = tmp_path / "empty.js"
        js_file.write_text("")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert result is not None
        assert module.name == "empty"
        assert len(module.functions) == 0
        assert len(module.classes) == 0

    def test_line_counting(self, parser, tmp_path):
        """Test line counting."""
        js_file = tmp_path / "test.js"
        js_file.write_text("""
// Line 1
function func1() {  // Line 2
    return true;    // Line 3
}                   // Line 4
                    // Line 5
function func2() {  // Line 6
    return false;   // Line 7
}                   // Line 8
""")

        result = parser.parse_file(js_file)
        module = result.modules[0] if result.modules else None
        assert module.lines >= 8


@pytest.mark.skipif(not JAVASCRIPT_PARSER_AVAILABLE, reason="JavaScript parser not available")
class TestTypeScriptParser:
    """Test TypeScript-specific parsing."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a JavaScript parser instance."""
        return JavaScriptParser(tmp_path, [])

    def test_parse_interface(self, parser, tmp_path):
        """Test parsing TypeScript interface."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
interface Config {
    host: string;
    port: number;
    debug?: boolean;
}
""")

        result = parser.parse_file(ts_file)
        # Interfaces might be treated as classes or have their own category
        assert result is not None

    def test_parse_type_alias(self, parser, tmp_path):
        """Test parsing TypeScript type alias."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
type ID = string | number;
type User = {
    id: ID;
    name: string;
};
""")

        result = parser.parse_file(ts_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_parse_enum(self, parser, tmp_path):
        """Test parsing TypeScript enum."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
enum Color {
    Red,
    Green,
    Blue
}
""")

        result = parser.parse_file(ts_file)
        module = result.modules[0] if result.modules else None
        assert result is not None

    def test_parse_generic_function(self, parser, tmp_path):
        """Test parsing function with generics."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("""
function identity<T>(arg: T): T {
    return arg;
}
""")

        result = parser.parse_file(ts_file)
        func = next((f for f in result.functions if f.name == 'identity'), None)
        assert func is not None

    def test_parse_tsx_component(self, parser, tmp_path):
        """Test parsing TSX React component."""
        tsx_file = tmp_path / "Component.tsx"
        tsx_file.write_text("""
import React from 'react';

interface Props {
    title: string;
}

const MyComponent: React.FC<Props> = ({ title }) => {
    return <div><h1>{title}</h1></div>;
};

export default MyComponent;
""")

        result = parser.parse_file(tsx_file)
        module = result.modules[0] if result.modules else None
        assert module.language == Language.TYPESCRIPT
