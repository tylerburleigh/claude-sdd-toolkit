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
