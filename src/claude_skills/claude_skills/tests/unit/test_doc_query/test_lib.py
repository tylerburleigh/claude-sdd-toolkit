import pytest

from claude_skills.doc_query.doc_query_lib import DocumentationQuery


def test_normalizes_modern_payload(doc_query_samples):
    docs_path = doc_query_samples["modern"].parent
    query = DocumentationQuery(str(docs_path))
    assert query.load()

    stats = query.get_stats()
    assert stats["statistics"]["total_modules"] == 1
    assert stats["statistics"]["total_classes"] == 2
    assert stats["statistics"]["high_complexity_count"] == 1
    assert stats["metadata"]["project_name"] == "example_project"

    modules = query.list_modules()
    assert len(modules) == 1
    module = modules[0].data
    assert module["statistics"]["class_count"] == 2
    assert module["statistics"]["high_complexity_count"] == 1
    assert module["docstring_excerpt"] == "Example calculator module."


def test_normalizes_legacy_payload(doc_query_samples):
    docs_path = doc_query_samples["legacy"].parent
    query = DocumentationQuery(str(docs_path))
    assert query.load()

    stats = query.get_stats()
    assert stats["metadata"]["project_name"] == "legacy_project"
    assert stats["statistics"]["total_modules"] == 1
    assert stats["statistics"]["total_functions"] == 1

    module = query.find_module("legacy.py")[0].data
    assert module["functions"][0]["name"] == "legacy_func"
    assert module["statistics"]["high_complexity_count"] == 1


def test_describe_module_returns_summary(doc_query_samples):
    docs_path = doc_query_samples["modern"].parent
    query = DocumentationQuery(str(docs_path))
    query.load()

    summary = query.describe_module("calculator.py", top_functions=1, include_docstrings=True)
    assert summary["file"] == "calculator.py"
    assert summary["statistics"]["avg_complexity"] == pytest.approx(5.0)
    assert len(summary["functions"]) == 1
    assert summary["functions"][0]["docstring_excerpt"]


def test_context_for_area_includes_docstrings_and_stats(doc_query_samples):
    docs_path = doc_query_samples["modern"].parent
    query = DocumentationQuery(str(docs_path))
    query.load()

    context = query.get_context_for_area(
        "calc",
        include_docstrings=True,
        include_stats=True,
        limit=5
    )

    assert context["functions"][0].data["docstring_excerpt"]
    assert context["modules"][0].data["statistics"]["avg_complexity"] == pytest.approx(5.0)
    dependencies = {dep.name for dep in context["dependencies"]}
    assert "typing.Union" in dependencies


# Tests for Schema v2.0 Cross-Reference Query Functions

def test_get_callers_with_v2_schema(tmp_path):
    """Test get_callers() with schema v2.0 cross-reference data."""
    # Create test documentation with v2.0 schema
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "process_data",
                "file": "utils.py",
                "line": 10,
                "callers": [
                    {"name": "main", "file": "app.py", "line": 5, "call_type": "function_call"},
                    {"name": "worker", "file": "tasks.py", "line": 20, "call_type": "function_call"}
                ],
                "calls": [],
                "call_count": 15
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    assert query.load()

    callers = query.get_callers("process_data")
    assert len(callers) == 2
    assert callers[0]['name'] == "main"
    assert callers[0]['file'] == "app.py"
    assert callers[0]['line'] == 5
    assert callers[0]['call_type'] == "function_call"
    assert callers[1]['name'] == "worker"


def test_get_callers_exclude_file(tmp_path):
    """Test get_callers() with include_file=False."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "foo",
                "file": "mod.py",
                "line": 1,
                "callers": [
                    {"name": "bar", "file": "other.py", "line": 10, "call_type": "function_call"}
                ]
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callers = query.get_callers("foo", include_file=False)
    assert len(callers) == 1
    assert 'name' in callers[0]
    assert 'file' not in callers[0]
    assert 'line' in callers[0]


def test_get_callers_exclude_line(tmp_path):
    """Test get_callers() with include_line=False."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "foo",
                "file": "mod.py",
                "line": 1,
                "callers": [
                    {"name": "bar", "file": "other.py", "line": 10, "call_type": "function_call"}
                ]
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callers = query.get_callers("foo", include_line=False)
    assert len(callers) == 1
    assert 'name' in callers[0]
    assert 'file' in callers[0]
    assert 'line' not in callers[0]


def test_get_callers_function_not_found(tmp_path):
    """Test get_callers() returns empty list when function not found."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text('{"functions": [], "classes": [], "modules": []}')

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callers = query.get_callers("nonexistent")
    assert callers == []


def test_get_callers_no_callers(tmp_path):
    """Test get_callers() returns empty list when function has no callers."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {"name": "isolated", "file": "mod.py", "line": 1, "callers": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callers = query.get_callers("isolated")
    assert callers == []


def test_get_callees_with_v2_schema(tmp_path):
    """Test get_callees() with schema v2.0 cross-reference data."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "main",
                "file": "app.py",
                "line": 5,
                "callers": [],
                "calls": [
                    {"name": "process_data", "file": "utils.py", "line": 10, "call_type": "function_call"},
                    {"name": "save_result", "file": "db.py", "line": 25, "call_type": "function_call"},
                    {"name": "log", "file": "logger.py", "line": 3, "call_type": "function_call"}
                ]
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    assert query.load()

    callees = query.get_callees("main")
    assert len(callees) == 3
    assert callees[0]['name'] == "process_data"
    assert callees[0]['file'] == "utils.py"
    assert callees[0]['line'] == 10
    assert callees[1]['name'] == "save_result"
    assert callees[2]['name'] == "log"


def test_get_callees_exclude_file(tmp_path):
    """Test get_callees() with include_file=False."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "foo",
                "file": "mod.py",
                "line": 1,
                "calls": [
                    {"name": "bar", "file": "other.py", "line": 10, "call_type": "function_call"}
                ]
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callees = query.get_callees("foo", include_file=False)
    assert len(callees) == 1
    assert 'file' not in callees[0]


def test_get_callees_function_not_found(tmp_path):
    """Test get_callees() returns empty list when function not found."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text('{"functions": [], "classes": [], "modules": []}')

    query = DocumentationQuery(str(tmp_path))
    query.load()

    callees = query.get_callees("nonexistent")
    assert callees == []


def test_get_call_count_with_value(tmp_path):
    """Test get_call_count() returns count when available."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {"name": "popular", "file": "mod.py", "line": 1, "call_count": 42}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    count = query.get_call_count("popular")
    assert count == 42


def test_get_call_count_none(tmp_path):
    """Test get_call_count() returns None when not available."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {"name": "unknown", "file": "mod.py", "line": 1}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    count = query.get_call_count("unknown")
    assert count is None


def test_get_call_count_function_not_found(tmp_path):
    """Test get_call_count() returns None when function not found."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text('{"functions": [], "classes": [], "modules": []}')

    query = DocumentationQuery(str(tmp_path))
    query.load()

    count = query.get_call_count("nonexistent")
    assert count is None


def test_normalize_v2_schema_fields(tmp_path):
    """Test that v2.0 schema fields are properly normalized."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "with_refs",
                "file": "mod.py",
                "line": 1,
                "callers": [{"name": "caller1", "file": "a.py", "line": 1, "call_type": "function_call"}],
                "calls": [{"name": "callee1", "file": "b.py", "line": 2, "call_type": "function_call"}],
                "call_count": 5
            },
            {
                "name": "without_refs",
                "file": "mod.py",
                "line": 10
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    # Function with v2.0 fields
    funcs_with = [f for f in query.data['functions'] if f['name'] == 'with_refs']
    assert len(funcs_with) == 1
    assert 'callers' in funcs_with[0]
    assert 'calls' in funcs_with[0]
    assert 'call_count' in funcs_with[0]
    assert len(funcs_with[0]['callers']) == 1
    assert len(funcs_with[0]['calls']) == 1
    assert funcs_with[0]['call_count'] == 5

    # Function without v2.0 fields (should be normalized with defaults)
    funcs_without = [f for f in query.data['functions'] if f['name'] == 'without_refs']
    assert len(funcs_without) == 1
    assert 'callers' in funcs_without[0]
    assert 'calls' in funcs_without[0]
    assert 'call_count' in funcs_without[0]
    assert funcs_without[0]['callers'] == []
    assert funcs_without[0]['calls'] == []
    assert funcs_without[0]['call_count'] is None


# Tests for build_call_graph()

def test_build_call_graph_callees_only(tmp_path):
    """Test build_call_graph() with direction='callees'."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "main",
                "file": "app.py",
                "line": 1,
                "calls": [
                    {"name": "process", "file": "utils.py", "line": 10, "call_type": "function_call"},
                    {"name": "save", "file": "db.py", "line": 20, "call_type": "function_call"}
                ]
            },
            {
                "name": "process",
                "file": "utils.py",
                "line": 10,
                "calls": [
                    {"name": "validate", "file": "validators.py", "line": 5, "call_type": "function_call"}
                ]
            },
            {"name": "save", "file": "db.py", "line": 20, "calls": []},
            {"name": "validate", "file": "validators.py", "line": 5, "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("main", direction="callees", max_depth=2)

    assert graph['root'] == "main"
    assert graph['direction'] == "callees"
    assert len(graph['nodes']) == 4  # main, process, save, validate
    assert len(graph['edges']) == 3  # main->process, main->save, process->validate


def test_build_call_graph_callers_only(tmp_path):
    """Test build_call_graph() with direction='callers'."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "target",
                "file": "utils.py",
                "line": 10,
                "callers": [
                    {"name": "caller1", "file": "app.py", "line": 5, "call_type": "function_call"},
                    {"name": "caller2", "file": "services.py", "line": 15, "call_type": "function_call"}
                ]
            },
            {
                "name": "caller1",
                "file": "app.py",
                "line": 5,
                "callers": [
                    {"name": "main", "file": "main.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {"name": "caller2", "file": "services.py", "line": 15, "callers": []},
            {"name": "main", "file": "main.py", "line": 1, "callers": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("target", direction="callers", max_depth=2)

    assert graph['root'] == "target"
    assert graph['direction'] == "callers"
    assert len(graph['nodes']) == 4  # target, caller1, caller2, main
    assert len(graph['edges']) == 3  # caller1->target, caller2->target, main->caller1


def test_build_call_graph_both_directions(tmp_path):
    """Test build_call_graph() with direction='both'."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "middle",
                "file": "middle.py",
                "line": 10,
                "callers": [
                    {"name": "upstream", "file": "up.py", "line": 5, "call_type": "function_call"}
                ],
                "calls": [
                    {"name": "downstream", "file": "down.py", "line": 20, "call_type": "function_call"}
                ]
            },
            {"name": "upstream", "file": "up.py", "line": 5, "callers": [], "calls": []},
            {"name": "downstream", "file": "down.py", "line": 20, "callers": [], "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("middle", direction="both", max_depth=1)

    assert graph['root'] == "middle"
    assert graph['direction'] == "both"
    assert len(graph['nodes']) == 3  # middle, upstream, downstream
    assert len(graph['edges']) == 2  # upstream->middle, middle->downstream


def test_build_call_graph_max_depth(tmp_path):
    """Test build_call_graph() respects max_depth."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "a",
                "file": "a.py",
                "line": 1,
                "calls": [
                    {"name": "b", "file": "b.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {
                "name": "b",
                "file": "b.py",
                "line": 1,
                "calls": [
                    {"name": "c", "file": "c.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {
                "name": "c",
                "file": "c.py",
                "line": 1,
                "calls": [
                    {"name": "d", "file": "d.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {"name": "d", "file": "d.py", "line": 1, "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    # With max_depth=2, should get a -> b -> c (not d)
    graph = query.build_call_graph("a", direction="callees", max_depth=2)

    assert graph['root'] == "a"
    assert len(graph['nodes']) == 3  # a, b, c (not d)
    assert 'd' not in graph['nodes']
    assert graph['truncated'] == True  # Depth was reached


def test_build_call_graph_handles_cycles(tmp_path):
    """Test build_call_graph() handles circular dependencies."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "a",
                "file": "a.py",
                "line": 1,
                "calls": [
                    {"name": "b", "file": "b.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {
                "name": "b",
                "file": "b.py",
                "line": 1,
                "calls": [
                    {"name": "a", "file": "a.py", "line": 1, "call_type": "function_call"}
                ]
            }
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    # Should handle cycle: a -> b -> a
    graph = query.build_call_graph("a", direction="callees", max_depth=5)

    # Should have both nodes, but not infinite loop
    assert len(graph['nodes']) == 2  # a and b
    assert 'a' in graph['nodes']
    assert 'b' in graph['nodes']
    # Should have edge a->b, but b->a won't cause revisit
    assert len(graph['edges']) == 2  # a->b and b->a edges


def test_build_call_graph_function_not_found(tmp_path):
    """Test build_call_graph() with non-existent function."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text('{"functions": [], "classes": [], "modules": []}')

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("nonexistent", direction="both", max_depth=3)

    assert graph['root'] == "nonexistent"
    assert len(graph['nodes']) == 0
    assert len(graph['edges']) == 0
    assert graph['truncated'] == False


def test_build_call_graph_isolated_function(tmp_path):
    """Test build_call_graph() with function that has no callers or callees."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {"name": "isolated", "file": "iso.py", "line": 1, "callers": [], "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("isolated", direction="both", max_depth=3)

    assert graph['root'] == "isolated"
    assert len(graph['nodes']) == 1  # Only the root
    assert len(graph['edges']) == 0
    assert graph['truncated'] == False


def test_build_call_graph_include_metadata(tmp_path):
    """Test build_call_graph() includes metadata when requested."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "foo",
                "file": "foo.py",
                "line": 10,
                "call_count": 42,
                "calls": [
                    {"name": "bar", "file": "bar.py", "line": 20, "call_type": "function_call"}
                ]
            },
            {"name": "bar", "file": "bar.py", "line": 20, "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("foo", direction="callees", max_depth=1, include_metadata=True)

    # Check root node has metadata
    assert graph['nodes']['foo']['file'] == "foo.py"
    assert graph['nodes']['foo']['line'] == 10
    assert graph['nodes']['foo']['call_count'] == 42

    # Check child node has metadata
    assert graph['nodes']['bar']['file'] == "bar.py"
    assert graph['nodes']['bar']['line'] == 20


def test_build_call_graph_without_metadata(tmp_path):
    """Test build_call_graph() excludes metadata when not requested."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "foo",
                "file": "foo.py",
                "line": 10,
                "calls": [
                    {"name": "bar", "file": "bar.py", "line": 20, "call_type": "function_call"}
                ]
            },
            {"name": "bar", "file": "bar.py", "line": 20, "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("foo", direction="callees", max_depth=1, include_metadata=False)

    # Nodes should only have name and depth
    assert 'name' in graph['nodes']['foo']
    assert 'depth' in graph['nodes']['foo']
    assert 'file' not in graph['nodes']['foo']
    assert 'line' not in graph['nodes']['foo']


def test_build_call_graph_depth_values(tmp_path):
    """Test build_call_graph() assigns correct depth values."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text("""{
        "functions": [
            {
                "name": "a",
                "file": "a.py",
                "line": 1,
                "calls": [
                    {"name": "b", "file": "b.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {
                "name": "b",
                "file": "b.py",
                "line": 1,
                "calls": [
                    {"name": "c", "file": "c.py", "line": 1, "call_type": "function_call"}
                ]
            },
            {"name": "c", "file": "c.py", "line": 1, "calls": []}
        ],
        "classes": [],
        "modules": []
    }""")

    query = DocumentationQuery(str(tmp_path))
    query.load()

    graph = query.build_call_graph("a", direction="callees", max_depth=3)

    assert graph['nodes']['a']['depth'] == 0
    assert graph['nodes']['b']['depth'] == 1
    assert graph['nodes']['c']['depth'] == 2


def test_build_call_graph_invalid_direction(tmp_path):
    """Test build_call_graph() raises error for invalid direction."""
    doc_file = tmp_path / "codebase.json"
    doc_file.write_text('{"functions": [], "classes": [], "modules": []}')

    query = DocumentationQuery(str(tmp_path))
    query.load()

    with pytest.raises(ValueError, match="Invalid direction"):
        query.build_call_graph("foo", direction="invalid")


# Tests for apply_pattern_filter() helper function

def test_apply_pattern_filter_exact_match():
    """Test exact name matching."""
    items = [
        {'name': 'Calculator'},
        {'name': 'Validator'},
        {'name': 'Parser'}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'Calculator', pattern=False)

    assert len(results) == 1
    assert results[0]['name'] == 'Calculator'


def test_apply_pattern_filter_exact_match_no_results():
    """Test exact match returns empty list when no match found."""
    items = [{'name': 'foo'}, {'name': 'bar'}]

    results = DocumentationQuery.apply_pattern_filter(items, 'baz', pattern=False)

    assert results == []


def test_apply_pattern_filter_regex_pattern():
    """Test regex pattern matching (case-insensitive)."""
    items = [
        {'name': 'Calculator'},
        {'name': 'Validator'},
        {'name': 'calc_helper'},
        {'name': 'Parser'}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'calc', pattern=True)

    assert len(results) == 2
    names = {r['name'] for r in results}
    assert 'Calculator' in names
    assert 'calc_helper' in names


def test_apply_pattern_filter_regex_case_insensitive():
    """Test that regex pattern matching is case-insensitive."""
    items = [
        {'name': 'TestClass'},
        {'name': 'test_function'},
        {'name': 'MY_TEST_CONSTANT'}
    ]

    # Search for 'test' should match all three
    results = DocumentationQuery.apply_pattern_filter(items, 'test', pattern=True)

    assert len(results) == 3


def test_apply_pattern_filter_regex_complex_pattern():
    """Test regex with more complex pattern."""
    items = [
        {'name': 'get_user'},
        {'name': 'get_product'},
        {'name': 'set_user'},
        {'name': 'delete_user'}
    ]

    # Match functions starting with 'get_'
    results = DocumentationQuery.apply_pattern_filter(items, '^get_', pattern=True)

    assert len(results) == 2
    names = {r['name'] for r in results}
    assert 'get_user' in names
    assert 'get_product' in names


def test_apply_pattern_filter_invalid_regex():
    """Test that invalid regex raises re.error."""
    import re

    items = [{'name': 'foo'}]

    with pytest.raises(re.error):
        DocumentationQuery.apply_pattern_filter(items, '[invalid(', pattern=True)


def test_apply_pattern_filter_empty_items():
    """Test with empty items list."""
    results = DocumentationQuery.apply_pattern_filter([], 'anything', pattern=False)

    assert results == []


def test_apply_pattern_filter_custom_key_function():
    """Test custom key function for nested fields."""
    items = [
        {'file': 'src/calculator.py', 'name': 'Calc'},
        {'file': 'src/validator.py', 'name': 'Valid'},
        {'file': 'tests/test_calc.py', 'name': 'TestCalc'}
    ]

    # Search in 'file' field instead of 'name'
    results = DocumentationQuery.apply_pattern_filter(
        items,
        'calc',
        pattern=True,
        key_func=lambda x: x.get('file', '')
    )

    assert len(results) == 2
    files = {r['file'] for r in results}
    assert 'src/calculator.py' in files
    assert 'tests/test_calc.py' in files


def test_apply_pattern_filter_custom_key_exact_match():
    """Test custom key function with exact matching."""
    items = [
        {'path': '/home/user/file.py'},
        {'path': '/home/admin/file.py'},
        {'path': '/home/user/other.py'}
    ]

    results = DocumentationQuery.apply_pattern_filter(
        items,
        '/home/user/file.py',
        pattern=False,
        key_func=lambda x: x.get('path', '')
    )

    assert len(results) == 1
    assert results[0]['path'] == '/home/user/file.py'


def test_apply_pattern_filter_missing_key():
    """Test graceful handling when key is missing from some items."""
    items = [
        {'name': 'foo'},
        {'other': 'bar'},  # Missing 'name' key
        {'name': 'baz'}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'foo', pattern=False)

    # Should only return items with the 'name' key
    assert len(results) == 1
    assert results[0]['name'] == 'foo'


def test_apply_pattern_filter_empty_string_values():
    """Test that empty string values are skipped."""
    items = [
        {'name': ''},
        {'name': 'valid'},
        {'name': None}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'valid', pattern=False)

    assert len(results) == 1
    assert results[0]['name'] == 'valid'


def test_apply_pattern_filter_regex_empty_string():
    """Test regex pattern with empty string values."""
    items = [
        {'name': ''},
        {'name': 'test'},
        {'name': None}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'test', pattern=True)

    assert len(results) == 1
    assert results[0]['name'] == 'test'


def test_apply_pattern_filter_key_func_exception():
    """Test that exceptions in key_func are handled gracefully."""
    items = [
        {'data': {'nested': 'value1'}},
        {'data': None},  # Will cause TypeError
        {'data': {'nested': 'value2'}}
    ]

    # This key_func will fail on the second item
    results = DocumentationQuery.apply_pattern_filter(
        items,
        'value1',
        pattern=False,
        key_func=lambda x: x['data']['nested']
    )

    # Should skip items where key_func raises exception
    assert len(results) == 1
    assert results[0]['data']['nested'] == 'value1'


def test_apply_pattern_filter_preserves_item_structure():
    """Test that filtered items maintain their full structure."""
    items = [
        {'name': 'foo', 'file': 'foo.py', 'line': 10, 'extra': 'data'},
        {'name': 'bar', 'file': 'bar.py', 'line': 20}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, 'foo', pattern=False)

    assert len(results) == 1
    assert results[0] == {'name': 'foo', 'file': 'foo.py', 'line': 10, 'extra': 'data'}


def test_apply_pattern_filter_multiple_matches():
    """Test pattern that matches multiple items."""
    items = [
        {'name': 'test_one'},
        {'name': 'test_two'},
        {'name': 'test_three'},
        {'name': 'other'}
    ]

    results = DocumentationQuery.apply_pattern_filter(items, '^test_', pattern=True)

    assert len(results) == 3
    names = [r['name'] for r in results]
    assert 'test_one' in names
    assert 'test_two' in names
    assert 'test_three' in names
    assert 'other' not in names
