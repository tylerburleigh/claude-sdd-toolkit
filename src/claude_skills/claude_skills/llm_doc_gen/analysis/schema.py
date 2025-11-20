"""
Centralized schema definitions for codebase documentation.

This module defines the JSON schema structure for documentation output,
including support for cross-reference fields (callers/calls) to enable
bidirectional function relationship tracking and usage tracking fields
(instantiated_by/imported_by) for class usage analysis.

Schema Version History:
- v1.0: Initial schema with basic function/class/module structures
- v1.1: (Transitional) Development version with new fields
- v2.0: Stable release with cross-reference and usage tracking support
  - Functions: callers, calls, call_count fields for bidirectional call tracking
  - Classes: instantiated_by, imported_by, instantiation_count for usage analysis
  - Backward compatible: Enhancement functions are opt-in
  - Migration: Use enhance_function_with_cross_refs() and enhance_class_with_usage_tracking()

Migration Guide (v1.0 → v2.0):

The v2.0 schema is backward compatible with v1.0. Existing code using
ParsedFunction.to_dict() and ParsedClass.to_dict() will continue to work
without modifications.

To adopt v2.0 features:

1. Function Cross-References:
   ```python
   from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

   # Existing v1.0 code works unchanged
   func_dict = parsed_function.to_dict()

   # Opt-in to v2.0 features
   callers = [CallReference("main", "app.py", 10, "function_call")]
   enhanced_dict = enhance_function_with_cross_refs(parsed_function, callers=callers)
   ```

2. Class Usage Tracking:
   ```python
   from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking, InstantiationReference

   # Existing v1.0 code works unchanged
   class_dict = parsed_class.to_dict()

   # Opt-in to v2.0 features
   instantiations = [InstantiationReference("factory", "utils.py", 5)]
   enhanced_dict = enhance_class_with_usage_tracking(parsed_class, instantiated_by=instantiations)
   ```

Backward Compatibility Notes:

v2.0 maintains full backward compatibility with v1.0:

1. Base Schema Unchanged:
   - ParsedFunction.to_dict() returns same fields as v1.0
   - ParsedClass.to_dict() returns same fields as v1.0
   - No changes to ParsedModule

2. Opt-In Enhancement:
   - New fields only appear when using enhancement functions
   - Parsers can adopt v2.0 features incrementally
   - Old parsers continue to work without changes

3. JSON Compatibility:
   - v1.0 JSON consumers can safely ignore new fields
   - v2.0 JSON is a superset of v1.0 JSON
   - Field names don't conflict

4. Migration Path:
   - Phase 1: Update parsers to populate cross-reference data
   - Phase 2: Use enhancement functions in formatters
   - Phase 3: Update consumers to query new fields
   - Each phase is optional and independent

Example Usage:

    >>> # Parse a file
    >>> from claude_skills.llm_doc_gen.analysis.parsers.python import PythonParser
    >>> parser = PythonParser(root_path, [])
    >>> result = parser.parse_file("example.py")
    >>>
    >>> # v1.0 usage (still works)
    >>> func = result.functions[0]
    >>> basic_schema = func.to_dict()
    >>>
    >>> # v2.0 usage (opt-in)
    >>> from claude_skills.llm_doc_gen.analysis.schema import (
    ...     enhance_function_with_cross_refs,
    ...     CallReference
    ... )
    >>> callers = [CallReference("main", "app.py", 10, "function_call")]
    >>> enhanced_schema = enhance_function_with_cross_refs(func, callers=callers)
    >>> print(enhanced_schema['callers'])  # v2.0 field
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .parsers.base import ParsedFunction as BaseParsedFunction, ParsedClass as BaseParsedClass


# Schema versioning
SCHEMA_VERSION = "2.0"
SCHEMA_VERSION_MAJOR = 2
SCHEMA_VERSION_MINOR = 0

# Summary schema: Lightweight format with signatures only
SUMMARY_SCHEMA = "summary-v1.0"

# Detail schema: Full format with complete documentation
DETAIL_SCHEMA = "detail-v1.0"


def to_summary(data_dict: dict) -> dict:
    """
    Convert full documentation dict to summary format (signatures only).

    Strips docstrings, function bodies, and detailed analysis while
    preserving signatures, parameters, return types, and basic metadata.

    Args:
        data_dict: Full documentation dictionary (function or class)

    Returns:
        Lightweight summary dictionary with signatures only
    """
    # For functions: keep only signature-related fields
    if 'signature' in data_dict:
        return {
            'name': data_dict.get('name'),
            'signature': data_dict.get('signature'),
            'file': data_dict.get('file'),
            'line': data_dict.get('line'),
            'parameters': data_dict.get('parameters', []),
            'return_type': data_dict.get('return_type')
        }

    # For classes: keep structure but strip method details
    if 'methods' in data_dict:
        summary = {
            'name': data_dict.get('name'),
            'file': data_dict.get('file'),
            'line': data_dict.get('line'),
            'bases': data_dict.get('bases', []),
            'methods': []
        }
        for method in data_dict.get('methods', []):
            summary['methods'].append(to_summary(method))
        return summary

    # Fallback: return minimal info
    return {
        'name': data_dict.get('name'),
        'file': data_dict.get('file'),
        'line': data_dict.get('line')
    }


def to_detail(data_dict: dict) -> dict:
    """
    Convert to detail format (complete documentation).

    This is essentially a pass-through since the default format
    already includes all details. Provided for symmetry with to_summary()
    and future extensibility.

    Args:
        data_dict: Documentation dictionary (function or class)

    Returns:
        Complete detail dictionary (unchanged from input)
    """
    return data_dict


@dataclass
class CallReference:
    """
    Represents a reference to a function call.

    This structure is used to represent both:
    - callers: functions that call this function
    - calls: functions called by this function

    Attributes:
        name: Name of the function
        file: File path where the function is defined/called
        line: Line number of the call site or definition
        call_type: Type of call (e.g., "function_call", "method_call",
                   "class_instantiation")

    Example:
        >>> ref = CallReference(
        ...     name="process_data",
        ...     file="src/utils.py",
        ...     line=42,
        ...     call_type="function_call"
        ... )
        >>> ref.to_dict()
        {'name': 'process_data', 'file': 'src/utils.py', 'line': 42,
         'call_type': 'function_call'}
    """
    name: str
    file: str
    line: int
    call_type: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'file': self.file,
            'line': self.line,
            'call_type': self.call_type
        }


def enhance_function_with_cross_refs(
    func: BaseParsedFunction,
    callers: Optional[List[CallReference]] = None,
    calls: Optional[List[CallReference]] = None,
    call_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Enhance ParsedFunction with cross-reference fields for schema v1.1+.

    This function extends the base ParsedFunction schema with bidirectional
    cross-reference information, enabling queries like:
    - "What functions call this function?" (callers)
    - "What functions does this function call?" (calls)
    - "How many times is this function called?" (call_count)

    Args:
        func: Base ParsedFunction instance from parser
        callers: List of functions that call this function (who calls me)
        calls: List of functions called by this function (who do I call)
        call_count: Optional total count of calls to this function across
                   the entire codebase

    Returns:
        Enhanced dictionary with all base ParsedFunction fields plus:
        - callers: array of CallReference objects
        - calls: array of CallReference objects
        - call_count: optional integer (only if provided)

    Example:
        >>> from claude_skills.llm_doc_gen.analysis.parsers.python import PythonParser
        >>> parser = PythonParser(root_path, [])
        >>> result = parser.parse_file("example.py")
        >>> func = result.functions[0]
        >>>
        >>> # Add cross-reference data
        >>> callers = [CallReference("main", "app.py", 10, "function_call")]
        >>> calls = [CallReference("helper", "utils.py", 5, "function_call")]
        >>>
        >>> enhanced = enhance_function_with_cross_refs(
        ...     func, callers=callers, calls=calls, call_count=3
        ... )
        >>> assert 'callers' in enhanced
        >>> assert 'calls' in enhanced
        >>> assert enhanced['call_count'] == 3

    Note:
        This is a non-breaking enhancement. The base ParsedFunction.to_dict()
        remains unchanged. This function provides an opt-in way to include
        cross-reference data in the output schema.
    """
    # Start with base function schema
    result = func.to_dict()

    # Add cross-reference fields
    result['callers'] = [c.to_dict() for c in (callers or [])]
    result['calls'] = [c.to_dict() for c in (calls or [])]

    # Add optional call_count field
    if call_count is not None:
        result['call_count'] = call_count

    return result


@dataclass
class InstantiationReference:
    """
    Represents a location where a class is instantiated.

    Used to track where classes are being used/constructed throughout
    the codebase, enabling reverse lookup from class to instantiation sites.

    Attributes:
        instantiator: Name of function/method creating the instance
        file: File containing the instantiation
        line: Line number of instantiation
        context: Optional context (e.g., "module", "function", "method")

    Example:
        >>> ref = InstantiationReference(
        ...     instantiator="create_user",
        ...     file="services/user.py",
        ...     line=42,
        ...     context="function"
        ... )
        >>> ref.to_dict()
        {'instantiator': 'create_user', 'file': 'services/user.py',
         'line': 42, 'context': 'function'}
    """
    instantiator: str
    file: str
    line: int
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'instantiator': self.instantiator,
            'file': self.file,
            'line': self.line
        }
        if self.context is not None:
            result['context'] = self.context
        return result


@dataclass
class ImportReference:
    """
    Represents a location where a class/module is imported.

    Tracks import statements to enable dependency analysis and
    understand how classes/modules are being used across the codebase.

    Attributes:
        importer: File that imports the class/module
        line: Line number of import statement
        import_type: Type of import ("direct", "from", "dynamic")
        alias: Optional import alias (e.g., "import pandas as pd")

    Example:
        >>> ref = ImportReference(
        ...     importer="app.py",
        ...     line=5,
        ...     import_type="from",
        ...     alias="User"
        ... )
        >>> ref.to_dict()
        {'importer': 'app.py', 'line': 5, 'import_type': 'from',
         'alias': 'User'}
    """
    importer: str
    line: int
    import_type: str
    alias: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'importer': self.importer,
            'line': self.line,
            'import_type': self.import_type
        }
        if self.alias is not None:
            result['alias'] = self.alias
        return result


def enhance_class_with_usage_tracking(
    cls: BaseParsedClass,
    instantiated_by: Optional[List[InstantiationReference]] = None,
    imported_by: Optional[List[ImportReference]] = None,
    instantiation_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Enhance ParsedClass with usage tracking fields for schema v1.1+.

    This function extends the base ParsedClass schema with usage information
    to enable queries like:
    - "Where is this class instantiated?" (instantiated_by)
    - "Which files import this class?" (imported_by)
    - "How many times is this class instantiated?" (instantiation_count)

    Args:
        cls: Base ParsedClass instance from parser
        instantiated_by: List of locations where class is instantiated
        imported_by: List of files that import this class
        instantiation_count: Optional count of total instantiations across
                            the entire codebase

    Returns:
        Enhanced dictionary with all base ParsedClass fields plus:
        - instantiated_by: array of InstantiationReference objects
        - imported_by: array of ImportReference objects
        - instantiation_count: optional integer (only if provided)

    Example:
        >>> from claude_skills.llm_doc_gen.analysis.parsers.python import PythonParser
        >>> parser = PythonParser(root_path, [])
        >>> result = parser.parse_file("models.py")
        >>> cls = result.classes[0]
        >>>
        >>> # Add usage tracking data
        >>> instantiations = [InstantiationReference("main", "app.py", 10)]
        >>> imports = [ImportReference("app.py", 1, "from", "User")]
        >>>
        >>> enhanced = enhance_class_with_usage_tracking(
        ...     cls,
        ...     instantiated_by=instantiations,
        ...     imported_by=imports,
        ...     instantiation_count=5
        ... )
        >>> assert 'instantiated_by' in enhanced
        >>> assert 'imported_by' in enhanced
        >>> assert enhanced['instantiation_count'] == 5

    Note:
        This is a non-breaking enhancement. The base ParsedClass.to_dict()
        remains unchanged. This function provides an opt-in way to include
        usage tracking data in the output schema.
    """
    # Start with base class schema
    result = cls.to_dict()

    # Add usage tracking fields
    result['instantiated_by'] = [i.to_dict() for i in (instantiated_by or [])]
    result['imported_by'] = [i.to_dict() for i in (imported_by or [])]

    # Add optional instantiation_count
    if instantiation_count is not None:
        result['instantiation_count'] = instantiation_count

    return result
