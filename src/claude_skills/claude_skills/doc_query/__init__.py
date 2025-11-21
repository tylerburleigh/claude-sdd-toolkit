"""Documentation Query Module

Tools for querying generated codebase documentation.
"""

from .doc_query_lib import DocumentationQuery, QueryResult, load_documentation
from .codebase_query import CodebaseQuery, create_codebase_query

__all__ = [
    'DocumentationQuery',
    'QueryResult',
    'load_documentation',
    'CodebaseQuery',
    'create_codebase_query',
]
