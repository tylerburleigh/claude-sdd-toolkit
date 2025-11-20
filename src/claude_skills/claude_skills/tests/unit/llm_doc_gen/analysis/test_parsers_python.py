"""
Tests for Python parser.
"""

import pytest
from pathlib import Path
from claude_skills.llm_doc_gen.analysis.parsers.base import Language
from claude_skills.llm_doc_gen.analysis.parsers.python import PythonParser


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


class TestPythonParserCrossReferences:
    """Test cross-reference tracking in Python parser."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_track_simple_function_call(self, parser, tmp_path):
        """Test tracking a simple function call."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def helper():
    return 42

def main():
    result = helper()
    return result
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None
        assert len(result.cross_references.calls) >= 1

        # Find the call to helper()
        helper_calls = [c for c in result.cross_references.calls if c.callee == 'helper']
        assert len(helper_calls) >= 1
        call = helper_calls[0]
        assert call.caller == 'main'
        assert call.callee == 'helper'

    def test_track_nested_function_calls(self, parser, tmp_path):
        """Test tracking nested function calls."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

def calculate():
    a = add(1, 2)
    b = multiply(3, 4)
    return add(a, b)
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None

        # Should have tracked calls from calculate to add and multiply
        add_calls = [c for c in result.cross_references.calls if c.callee == 'add']
        assert len(add_calls) >= 2  # Two calls to add

        multiply_calls = [c for c in result.cross_references.calls if c.callee == 'multiply']
        assert len(multiply_calls) >= 1  # One call to multiply

    def test_track_method_calls(self, parser, tmp_path):
        """Test tracking method calls."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Calculator:
    def add(self, a, b):
        return a + b

    def compute(self):
        result = self.add(1, 2)
        return result
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None

        # Should have tracked the method call
        add_calls = [c for c in result.cross_references.calls if c.callee == 'add']
        assert len(add_calls) >= 1
        call = add_calls[0]
        assert call.caller == 'compute'

    def test_track_calls_in_class_methods(self, parser, tmp_path):
        """Test tracking calls inside class methods."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    def method1(self):
        return 42

    def method2(self):
        value = self.method1()
        return value * 2
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None
        assert len(result.cross_references.calls) >= 1

        # Verify the call was tracked with class context
        calls = result.cross_references.calls
        assert any(c.metadata.get('in_class') == 'MyClass' for c in calls)

    def test_track_module_level_calls(self, parser, tmp_path):
        """Test tracking calls at module level."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def setup():
    return "initialized"

# Module-level call
config = setup()
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None

        # Should have tracked module-level call
        setup_calls = [c for c in result.cross_references.calls if c.callee == 'setup']
        assert len(setup_calls) >= 1
        call = setup_calls[0]
        assert call.caller == '<module>'

    def test_cross_reference_bidirectional(self, parser, tmp_path):
        """Test that cross-references maintain bidirectional indexing."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def helper():
    return 42

def caller1():
    return helper()

def caller2():
    return helper()
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Test get_callers (reverse lookup)
        callers = graph.get_callers('helper')
        assert len(callers) >= 2
        caller_names = {c.caller for c in callers}
        assert 'caller1' in caller_names
        assert 'caller2' in caller_names

        # Test get_callees (forward lookup)
        callees1 = graph.get_callees('caller1')
        assert len(callees1) >= 1
        assert callees1[0].callee == 'helper'

    def test_cross_reference_in_result(self, parser, tmp_path):
        """Test that cross-references are included in ParseResult."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def foo():
    bar()

def bar():
    pass
""")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None
        assert hasattr(result.cross_references, 'calls')
        assert hasattr(result.cross_references, 'callers')
        assert hasattr(result.cross_references, 'callees')

    def test_multiple_callers(self, parser, tmp_path):
        """Test tracking multiple callers to the same function."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def shared():
    return 42

def caller1():
    return shared()

def caller2():
    return shared()

def caller3():
    return shared()
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have three calls to shared
        shared_calls = graph.get_callers('shared')
        assert len(shared_calls) == 3

        # Verify statistics
        assert graph.stats['total_calls'] >= 3

    def test_call_tracking_with_decorators(self, parser, tmp_path):
        """Test that decorators don't interfere with call tracking."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def decorator(func):
    return func

@decorator
def decorated_func():
    return helper()

def helper():
    return 42
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should still track the call to helper from decorated_func
        helper_calls = [c for c in graph.calls if c.callee == 'helper']
        assert len(helper_calls) >= 1
        assert helper_calls[0].caller == 'decorated_func'

    def test_empty_file_has_graph(self, parser, tmp_path):
        """Test that even empty files have a cross-reference graph."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")

        result = parser.parse_file(py_file)
        assert result.cross_references is not None
        assert len(result.cross_references.calls) == 0
        assert result.cross_references.stats['total_calls'] == 0

    def test_line_numbers_tracked(self, parser, tmp_path):
        """Test that call line numbers are tracked correctly."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def helper():
    return 42

def main():
    x = helper()  # Line 6
    return x
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        helper_calls = [c for c in graph.calls if c.callee == 'helper']
        assert len(helper_calls) >= 1
        call = helper_calls[0]
        assert call.caller_line == 6

    def test_import_tracking_integration(self, parser, tmp_path):
        """Test that imports are tracked in the cross-reference graph."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Dict, List
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Verify imports are tracked in graph
        relative_path = "test.py"
        assert relative_path in graph.imports
        imports = graph.imports[relative_path]
        assert 'os' in imports
        assert 'sys' in imports

        # Verify bidirectional lookup (imported_by)
        assert 'os' in graph.imported_by
        assert relative_path in graph.imported_by['os']

    def test_class_instantiation_detection(self, parser, tmp_path):
        """Test that class instantiations are detected and tracked."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    pass

def create_instance():
    obj = MyClass()
    return obj
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Verify instantiation was detected
        assert len(graph.instantiations) >= 1
        inst = graph.instantiations[0]
        assert inst.class_name == 'MyClass'
        assert inst.instantiator == 'create_instance'

        # Verify bidirectional lookup
        inst_sites = graph.get_instantiation_sites('MyClass')
        assert len(inst_sites) >= 1
        assert inst_sites[0].instantiator == 'create_instance'

    def test_instantiation_vs_function_call(self, parser, tmp_path):
        """Test distinguishing class instantiation from function calls."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    pass

def my_function():
    return 42

def main():
    obj = MyClass()  # Should be instantiation
    result = my_function()  # Should be function call
    return result
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # MyClass should be in instantiations
        instantiations = [i.class_name for i in graph.instantiations]
        assert 'MyClass' in instantiations

        # my_function should be in calls
        function_calls = [c.callee for c in graph.calls]
        assert 'my_function' in function_calls

        # MyClass should NOT be in calls
        assert 'MyClass' not in function_calls

        # Verify statistics
        assert graph.stats['total_instantiations'] >= 1
        assert graph.stats['total_calls'] >= 1

    def test_method_call_not_instantiation(self, parser, tmp_path):
        """Test that method calls (even with uppercase) are not treated as instantiations."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    def MyMethod(self):
        return 42

def caller():
    obj = MyClass()
    result = obj.MyMethod()  # Method call, not instantiation
    return result
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # MyClass should be instantiation
        instantiations = [i.class_name for i in graph.instantiations]
        assert 'MyClass' in instantiations

        # MyMethod should be a call, NOT an instantiation
        assert 'MyMethod' not in instantiations
        method_calls = [c.callee for c in graph.calls if c.callee == 'MyMethod']
        assert len(method_calls) >= 1

    def test_multiple_instantiations(self, parser, tmp_path):
        """Test tracking multiple instantiations of the same class."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Person:
    pass

def create_people():
    alice = Person()
    bob = Person()
    charlie = Person()
    return [alice, bob, charlie]
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have three instantiations
        person_insts = graph.get_instantiation_sites('Person')
        assert len(person_insts) == 3
        assert all(i.instantiator == 'create_people' for i in person_insts)

    def test_module_level_instantiation(self, parser, tmp_path):
        """Test tracking instantiations at module level."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Config:
    pass

# Module-level instantiation
config = Config()
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should track module-level instantiation
        config_insts = graph.get_instantiation_sites('Config')
        assert len(config_insts) >= 1
        assert config_insts[0].instantiator == '<module>'

    def test_get_instantiators_method(self, parser, tmp_path):
        """Test get_instantiators() method for forward lookup."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Person:
    pass

class Animal:
    pass

def create_instances():
    person = Person()
    animal = Animal()
    return person, animal

def other_function():
    return Person()
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Test forward lookup: what does create_instances instantiate?
        insts = graph.get_instantiators('create_instances')
        assert len(insts) == 2
        class_names = {inst.class_name for inst in insts}
        assert 'Person' in class_names
        assert 'Animal' in class_names

        # Test with file parameter
        insts_with_file = graph.get_instantiators('create_instances', 'test.py')
        assert len(insts_with_file) == 2

        # Test function that instantiates one class
        other_insts = graph.get_instantiators('other_function')
        assert len(other_insts) == 1
        assert other_insts[0].class_name == 'Person'

    def test_get_imports_method(self, parser, tmp_path):
        """Test get_imports() method for forward lookup."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Dict, List
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Test forward lookup: what does test.py import?
        imports = graph.get_imports('test.py')
        assert 'os' in imports
        assert 'sys' in imports
        assert 'pathlib.Path' in imports

        # Test empty file
        empty_imports = graph.get_imports('nonexistent.py')
        assert len(empty_imports) == 0
        assert isinstance(empty_imports, set)

    def test_bidirectional_symmetry_complete(self, parser, tmp_path):
        """Test that all bidirectional lookups work symmetrically."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
import os
import sys

class MyClass:
    pass

def helper():
    return 42

def main():
    result = helper()
    obj = MyClass()
    return result
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Test call symmetry: forward (callees) and reverse (callers)
        # Forward: what does main call?
        callees = graph.get_callees('main')
        assert len(callees) >= 1
        assert any(c.callee == 'helper' for c in callees)

        # Reverse: who calls helper?
        callers = graph.get_callers('helper')
        assert len(callers) >= 1
        assert any(c.caller == 'main' for c in callers)

        # Test instantiation symmetry: forward (instantiators) and reverse (instantiation_sites)
        # Forward: what does main instantiate?
        instantiators = graph.get_instantiators('main')
        assert len(instantiators) >= 1
        assert any(inst.class_name == 'MyClass' for inst in instantiators)

        # Reverse: where is MyClass instantiated?
        inst_sites = graph.get_instantiation_sites('MyClass')
        assert len(inst_sites) >= 1
        assert any(inst.instantiator == 'main' for inst in inst_sites)

        # Test import symmetry: forward (imports) and reverse (imported_by)
        # Forward: what does test.py import?
        imports = graph.get_imports('test.py')
        assert 'os' in imports
        assert 'sys' in imports

        # Reverse: who imports os?
        importers = graph.get_imported_by('os')
        assert 'test.py' in importers

    def test_get_instantiators_empty_result(self, parser, tmp_path):
        """Test get_instantiators() returns empty list for function with no instantiations."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def simple_function():
    return 42
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Function that doesn't instantiate anything
        insts = graph.get_instantiators('simple_function')
        assert len(insts) == 0
        assert isinstance(insts, list)


class TestPythonParserDynamicPatterns:
    """Test dynamic pattern warning detection."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_decorator_warning(self, parser, tmp_path):
        """Test that decorators generate warnings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def my_decorator(func):
    return func

@my_decorator
def decorated_function():
    return 42

@staticmethod
@property
def multi_decorated():
    return 'test'
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have warnings for decorated functions
        decorator_warnings = [w for w in graph.warnings if w.pattern_type.value == 'decorator']
        assert len(decorator_warnings) >= 3  # 1 + 2 decorators

        # Check warning details
        decorated_warning = next((w for w in decorator_warnings if 'decorated_function' in w.location), None)
        assert decorated_warning is not None
        assert decorated_warning.file == 'test.py'
        assert 'decorator' in decorated_warning.description.lower()
        assert 'behavior' in decorated_warning.impact.lower()

    def test_eval_exec_warning(self, parser, tmp_path):
        """Test that eval/exec calls generate warnings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def dangerous_function():
    code = "print('hello')"
    eval(code)
    exec("x = 1")
    return True
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have warnings for eval and exec
        eval_exec_warnings = [w for w in graph.warnings if w.pattern_type.value == 'eval_exec']
        assert len(eval_exec_warnings) == 2

        # Check eval warning
        eval_warning = next((w for w in eval_exec_warnings if 'eval()' in w.description), None)
        assert eval_warning is not None
        assert eval_warning.location == 'dangerous_function'
        assert 'arbitrary code' in eval_warning.impact.lower()

        # Check exec warning
        exec_warning = next((w for w in eval_exec_warnings if 'exec()' in w.description), None)
        assert exec_warning is not None
        assert exec_warning.location == 'dangerous_function'

    def test_getattr_setattr_warning(self, parser, tmp_path):
        """Test that getattr/setattr/hasattr/delattr generate warnings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def dynamic_access(obj, attr_name):
    value = getattr(obj, attr_name)
    setattr(obj, attr_name, 'new_value')
    exists = hasattr(obj, attr_name)
    delattr(obj, attr_name)
    return value
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have warnings for all four functions
        attr_warnings = [w for w in graph.warnings if w.pattern_type.value == 'getattr_setattr']
        assert len(attr_warnings) == 4

        # Check all functions detected
        functions = [w.description for w in attr_warnings]
        assert any('getattr()' in f for f in functions)
        assert any('setattr()' in f for f in functions)
        assert any('hasattr()' in f for f in functions)
        assert any('delattr()' in f for f in functions)

        # Check impact message
        assert all('dynamic attribute' in w.impact.lower() for w in attr_warnings)

    def test_dynamic_import_warning(self, parser, tmp_path):
        """Test that dynamic imports generate warnings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def load_module(name):
    mod1 = __import__(name)

    import importlib
    mod2 = importlib.import_module(name)

    return mod1, mod2
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have warnings for both dynamic imports
        import_warnings = [w for w in graph.warnings if w.pattern_type.value == 'dynamic_import']
        assert len(import_warnings) == 2

        # Check __import__ warning
        import_warning = next((w for w in import_warnings if '__import__()' in w.description), None)
        assert import_warning is not None
        assert 'statically determined' in import_warning.impact.lower()

        # Check import_module warning
        importlib_warning = next((w for w in import_warnings if 'import_module()' in w.description), None)
        assert importlib_warning is not None

    def test_warning_statistics(self, parser, tmp_path):
        """Test that warning statistics are tracked correctly."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
@my_decorator
def function_with_issues():
    code = input()
    eval(code)
    obj_attr = getattr(obj, 'attr')
    mod = __import__('module')
    return obj_attr
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Check total warnings
        assert graph.stats['total_warnings'] >= 4

        # Check breakdown by pattern type
        patterns = graph.stats['dynamic_patterns']
        assert 'decorator' in patterns
        assert 'eval_exec' in patterns
        assert 'getattr_setattr' in patterns
        assert 'dynamic_import' in patterns

    def test_no_warnings_for_clean_code(self, parser, tmp_path):
        """Test that clean code doesn't generate false positive warnings."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def clean_function(x, y):
    result = x + y
    return result

class CleanClass:
    def method(self):
        return self.clean_function(1, 2)

    def clean_function(self, a, b):
        return a * b
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Should have no warnings
        assert len(graph.warnings) == 0
        assert graph.stats['total_warnings'] == 0

    def test_warnings_in_to_dict(self, parser, tmp_path):
        """Test that warnings are included in to_dict() output."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
@decorator
def func():
    eval('x')
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        # Convert to dict
        graph_dict = graph.to_dict()

        # Check warnings are in dict
        assert 'warnings' in graph_dict
        assert len(graph_dict['warnings']) >= 2

        # Check warning structure
        warning = graph_dict['warnings'][0]
        assert 'pattern_type' in warning
        assert 'location' in warning
        assert 'file' in warning
        assert 'line' in warning
        assert 'description' in warning
        assert 'impact' in warning

    def test_decorator_in_class_method(self, parser, tmp_path):
        """Test decorator warnings include class context."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    @property
    def my_property(self):
        return 42

    @staticmethod
    def my_static():
        return 'static'
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        decorator_warnings = [w for w in graph.warnings if w.pattern_type.value == 'decorator']
        assert len(decorator_warnings) >= 2

        # Check class context is included
        property_warning = next((w for w in decorator_warnings if 'my_property' in w.location), None)
        assert property_warning is not None
        assert 'MyClass' in property_warning.location

    def test_module_level_dynamic_pattern(self, parser, tmp_path):
        """Test dynamic patterns at module level."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""
# Module-level eval
config = eval('{"key": "value"}')
""")

        result = parser.parse_file(py_file)
        graph = result.cross_references
        assert graph is not None

        eval_warnings = [w for w in graph.warnings if w.pattern_type.value == 'eval_exec']
        assert len(eval_warnings) == 1
        assert eval_warnings[0].location == '<module>'


class TestSchemaEnhancements:
    """Test schema v1.1 enhancements with cross-reference fields."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_call_reference_creation(self):
        """Test creating CallReference objects."""
        from claude_skills.llm_doc_gen.analysis.schema import CallReference

        ref = CallReference(
            name="process_data",
            file="src/utils.py",
            line=42,
            call_type="function_call"
        )

        assert ref.name == "process_data"
        assert ref.file == "src/utils.py"
        assert ref.line == 42
        assert ref.call_type == "function_call"

    def test_call_reference_to_dict(self):
        """Test CallReference serialization to dictionary."""
        from claude_skills.llm_doc_gen.analysis.schema import CallReference

        ref = CallReference(
            name="helper",
            file="app.py",
            line=10,
            call_type="method_call"
        )

        ref_dict = ref.to_dict()

        assert ref_dict['name'] == "helper"
        assert ref_dict['file'] == "app.py"
        assert ref_dict['line'] == 10
        assert ref_dict['call_type'] == "method_call"
        assert len(ref_dict) == 4  # Exactly 4 fields

    def test_enhance_function_with_callers(self, parser, tmp_path):
        """Test enhancing function with callers field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def target_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Add callers (functions that call target_func)
        callers = [
            CallReference("caller1", "app.py", 10, "function_call"),
            CallReference("caller2", "utils.py", 25, "function_call")
        ]

        enhanced = enhance_function_with_cross_refs(func, callers=callers)

        assert 'callers' in enhanced
        assert len(enhanced['callers']) == 2
        assert enhanced['callers'][0]['name'] == "caller1"
        assert enhanced['callers'][0]['file'] == "app.py"
        assert enhanced['callers'][0]['line'] == 10
        assert enhanced['callers'][1]['name'] == "caller2"

    def test_enhance_function_with_calls(self, parser, tmp_path):
        """Test enhancing function with calls field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def caller_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Add calls (functions called by caller_func)
        calls = [
            CallReference("helper", "utils.py", 5, "function_call"),
            CallReference("validate", "validators.py", 12, "function_call")
        ]

        enhanced = enhance_function_with_cross_refs(func, calls=calls)

        assert 'calls' in enhanced
        assert len(enhanced['calls']) == 2
        assert enhanced['calls'][0]['name'] == "helper"
        assert enhanced['calls'][1]['name'] == "validate"

    def test_enhance_function_with_call_count(self, parser, tmp_path):
        """Test enhancing function with optional call_count field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def popular_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Add call_count
        enhanced = enhance_function_with_cross_refs(func, call_count=15)

        assert 'call_count' in enhanced
        assert enhanced['call_count'] == 15

    def test_enhance_function_without_call_count(self, parser, tmp_path):
        """Test that call_count is omitted when not provided."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def some_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Don't provide call_count
        enhanced = enhance_function_with_cross_refs(func)

        # call_count should not be in the output
        assert 'call_count' not in enhanced

    def test_enhance_function_preserves_base_fields(self, parser, tmp_path):
        """Test that enhancement preserves all base ParsedFunction fields."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def test_func(x: int, y: str = 'default') -> bool:
    '''A test function with parameters'''
    return True
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        callers = [CallReference("main", "app.py", 1, "function_call")]
        enhanced = enhance_function_with_cross_refs(func, callers=callers)

        # Check base fields are preserved
        assert enhanced['name'] == 'test_func'
        assert enhanced['file'].endswith('test.py')
        assert enhanced['line'] == 2
        assert enhanced['docstring'] == 'A test function with parameters'
        assert 'parameters' in enhanced
        assert enhanced['return_type'] is not None
        assert enhanced['complexity'] >= 1
        assert 'is_async' in enhanced
        assert 'is_exported' in enhanced
        assert 'is_public' in enhanced

        # Check new fields are added
        assert 'callers' in enhanced
        assert 'calls' in enhanced

    def test_enhance_function_with_empty_cross_refs(self, parser, tmp_path):
        """Test enhancing function with empty callers/calls lists."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def isolated_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Pass empty lists explicitly
        enhanced = enhance_function_with_cross_refs(func, callers=[], calls=[])

        assert 'callers' in enhanced
        assert 'calls' in enhanced
        assert len(enhanced['callers']) == 0
        assert len(enhanced['calls']) == 0

    def test_enhance_function_with_none_cross_refs(self, parser, tmp_path):
        """Test enhancing function with None for callers/calls."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Pass None (should default to empty lists)
        enhanced = enhance_function_with_cross_refs(func, callers=None, calls=None)

        assert 'callers' in enhanced
        assert 'calls' in enhanced
        assert len(enhanced['callers']) == 0
        assert len(enhanced['calls']) == 0

    def test_enhance_function_complete_example(self, parser, tmp_path):
        """Test complete enhancement with callers, calls, and call_count."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def middleware_func():
    '''A function that calls others and is called by others'''
    return True
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        # Add complete cross-reference data
        callers = [
            CallReference("route_handler", "routes.py", 15, "function_call"),
            CallReference("api_endpoint", "api.py", 42, "function_call")
        ]
        calls = [
            CallReference("validate", "validators.py", 8, "function_call"),
            CallReference("log", "logger.py", 3, "function_call"),
            CallReference("process", "processors.py", 20, "function_call")
        ]
        call_count = 127

        enhanced = enhance_function_with_cross_refs(
            func,
            callers=callers,
            calls=calls,
            call_count=call_count
        )

        # Verify all fields present
        assert enhanced['name'] == 'middleware_func'
        assert len(enhanced['callers']) == 2
        assert len(enhanced['calls']) == 3
        assert enhanced['call_count'] == 127

        # Verify callers details
        assert enhanced['callers'][0]['name'] == 'route_handler'
        assert enhanced['callers'][1]['file'] == 'api.py'

        # Verify calls details
        assert enhanced['calls'][0]['name'] == 'validate'
        assert enhanced['calls'][1]['name'] == 'log'
        assert enhanced['calls'][2]['name'] == 'process'

    def test_schema_version_constants(self):
        """Test that schema version constants are defined."""
        from claude_skills.llm_doc_gen.analysis import schema

        assert hasattr(schema, 'SCHEMA_VERSION')
        assert hasattr(schema, 'SCHEMA_VERSION_MAJOR')
        assert hasattr(schema, 'SCHEMA_VERSION_MINOR')

        assert schema.SCHEMA_VERSION == "2.0"
        assert schema.SCHEMA_VERSION_MAJOR == 2
        assert schema.SCHEMA_VERSION_MINOR == 0

    def test_call_reference_different_types(self):
        """Test CallReference with different call types."""
        from claude_skills.llm_doc_gen.analysis.schema import CallReference

        # Function call
        func_call = CallReference("func", "app.py", 1, "function_call")
        assert func_call.to_dict()['call_type'] == "function_call"

        # Method call
        method_call = CallReference("method", "app.py", 2, "method_call")
        assert method_call.to_dict()['call_type'] == "method_call"

        # Class instantiation
        class_inst = CallReference("MyClass", "app.py", 3, "class_instantiation")
        assert class_inst.to_dict()['call_type'] == "class_instantiation"

    def test_enhance_with_method_calls(self, parser, tmp_path):
        """Test enhancement distinguishes function calls from method calls."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_function_with_cross_refs, CallReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
def my_func():
    return 42
""")

        result = parser.parse_file(py_file)
        func = result.functions[0]

        calls = [
            CallReference("helper", "utils.py", 5, "function_call"),
            CallReference("process", "obj.py", 10, "method_call")
        ]

        enhanced = enhance_function_with_cross_refs(func, calls=calls)

        assert enhanced['calls'][0]['call_type'] == "function_call"
        assert enhanced['calls'][1]['call_type'] == "method_call"


class TestClassSchemaEnhancements:
    """Test class schema v1.1 enhancements with usage tracking fields."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path, [])

    def test_instantiation_reference_creation(self):
        """Test creating InstantiationReference objects."""
        from claude_skills.llm_doc_gen.analysis.schema import InstantiationReference

        ref = InstantiationReference(
            instantiator="create_user",
            file="services/user.py",
            line=42,
            context="function"
        )

        assert ref.instantiator == "create_user"
        assert ref.file == "services/user.py"
        assert ref.line == 42
        assert ref.context == "function"

    def test_instantiation_reference_to_dict(self):
        """Test InstantiationReference serialization to dictionary."""
        from claude_skills.llm_doc_gen.analysis.schema import InstantiationReference

        ref = InstantiationReference(
            instantiator="main",
            file="app.py",
            line=10,
            context="module"
        )

        ref_dict = ref.to_dict()

        assert ref_dict['instantiator'] == "main"
        assert ref_dict['file'] == "app.py"
        assert ref_dict['line'] == 10
        assert ref_dict['context'] == "module"

    def test_instantiation_reference_without_context(self):
        """Test InstantiationReference without optional context field."""
        from claude_skills.llm_doc_gen.analysis.schema import InstantiationReference

        ref = InstantiationReference(
            instantiator="factory",
            file="utils.py",
            line=5
        )

        ref_dict = ref.to_dict()

        assert 'instantiator' in ref_dict
        assert 'file' in ref_dict
        assert 'line' in ref_dict
        # Context should not be in dict when None
        assert 'context' not in ref_dict

    def test_import_reference_creation(self):
        """Test creating ImportReference objects."""
        from claude_skills.llm_doc_gen.analysis.schema import ImportReference

        ref = ImportReference(
            importer="app.py",
            line=5,
            import_type="from",
            alias="User"
        )

        assert ref.importer == "app.py"
        assert ref.line == 5
        assert ref.import_type == "from"
        assert ref.alias == "User"

    def test_import_reference_to_dict(self):
        """Test ImportReference serialization to dictionary."""
        from claude_skills.llm_doc_gen.analysis.schema import ImportReference

        ref = ImportReference(
            importer="services.py",
            line=1,
            import_type="direct",
            alias="MyClass"
        )

        ref_dict = ref.to_dict()

        assert ref_dict['importer'] == "services.py"
        assert ref_dict['line'] == 1
        assert ref_dict['import_type'] == "direct"
        assert ref_dict['alias'] == "MyClass"

    def test_import_reference_without_alias(self):
        """Test ImportReference without optional alias field."""
        from claude_skills.llm_doc_gen.analysis.schema import ImportReference

        ref = ImportReference(
            importer="main.py",
            line=3,
            import_type="from"
        )

        ref_dict = ref.to_dict()

        assert 'importer' in ref_dict
        assert 'line' in ref_dict
        assert 'import_type' in ref_dict
        # Alias should not be in dict when None
        assert 'alias' not in ref_dict

    def test_enhance_class_with_instantiated_by(self, parser, tmp_path):
        """Test enhancing class with instantiated_by field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking, InstantiationReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class User:
    '''A user class'''
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Add instantiation tracking
        instantiations = [
            InstantiationReference("create_user", "app.py", 10, "function"),
            InstantiationReference("main", "main.py", 5, "module")
        ]

        enhanced = enhance_class_with_usage_tracking(cls, instantiated_by=instantiations)

        assert 'instantiated_by' in enhanced
        assert len(enhanced['instantiated_by']) == 2
        assert enhanced['instantiated_by'][0]['instantiator'] == "create_user"
        assert enhanced['instantiated_by'][0]['file'] == "app.py"
        assert enhanced['instantiated_by'][1]['instantiator'] == "main"

    def test_enhance_class_with_imported_by(self, parser, tmp_path):
        """Test enhancing class with imported_by field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking, ImportReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Product:
    '''A product class'''
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Add import tracking
        imports = [
            ImportReference("app.py", 1, "from", "Product"),
            ImportReference("services.py", 3, "from", None)
        ]

        enhanced = enhance_class_with_usage_tracking(cls, imported_by=imports)

        assert 'imported_by' in enhanced
        assert len(enhanced['imported_by']) == 2
        assert enhanced['imported_by'][0]['importer'] == "app.py"
        assert enhanced['imported_by'][0]['import_type'] == "from"
        assert enhanced['imported_by'][0]['alias'] == "Product"

    def test_enhance_class_with_instantiation_count(self, parser, tmp_path):
        """Test enhancing class with optional instantiation_count field."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Config:
    '''A configuration class'''
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Add instantiation count
        enhanced = enhance_class_with_usage_tracking(cls, instantiation_count=25)

        assert 'instantiation_count' in enhanced
        assert enhanced['instantiation_count'] == 25

    def test_enhance_class_without_instantiation_count(self, parser, tmp_path):
        """Test that instantiation_count is omitted when not provided."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Helper:
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Don't provide instantiation_count
        enhanced = enhance_class_with_usage_tracking(cls)

        # instantiation_count should not be in the output
        assert 'instantiation_count' not in enhanced

    def test_enhance_class_preserves_base_fields(self, parser, tmp_path):
        """Test that enhancement preserves all base ParsedClass fields."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking, InstantiationReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Animal:
    '''An animal base class'''
    def speak(self):
        pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        instantiations = [InstantiationReference("zoo", "zoo.py", 1)]
        enhanced = enhance_class_with_usage_tracking(cls, instantiated_by=instantiations)

        # Check base fields are preserved
        assert enhanced['name'] == 'Animal'
        assert enhanced['file'].endswith('test.py')
        assert enhanced['line'] == 2
        assert 'animal' in enhanced['docstring'].lower()
        assert 'methods' in enhanced
        assert 'bases' in enhanced
        assert 'properties' in enhanced
        assert 'is_exported' in enhanced
        assert 'is_public' in enhanced

        # Check new fields are added
        assert 'instantiated_by' in enhanced
        assert 'imported_by' in enhanced

    def test_enhance_class_with_empty_tracking(self, parser, tmp_path):
        """Test enhancing class with empty instantiated_by/imported_by lists."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Unused:
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Pass empty lists explicitly
        enhanced = enhance_class_with_usage_tracking(cls, instantiated_by=[], imported_by=[])

        assert 'instantiated_by' in enhanced
        assert 'imported_by' in enhanced
        assert len(enhanced['instantiated_by']) == 0
        assert len(enhanced['imported_by']) == 0

    def test_enhance_class_with_none_tracking(self, parser, tmp_path):
        """Test enhancing class with None for instantiated_by/imported_by."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Pass None (should default to empty lists)
        enhanced = enhance_class_with_usage_tracking(cls, instantiated_by=None, imported_by=None)

        assert 'instantiated_by' in enhanced
        assert 'imported_by' in enhanced
        assert len(enhanced['instantiated_by']) == 0
        assert len(enhanced['imported_by']) == 0

    def test_enhance_class_complete_example(self, parser, tmp_path):
        """Test complete enhancement with instantiated_by, imported_by, and instantiation_count."""
        from claude_skills.llm_doc_gen.analysis.schema import enhance_class_with_usage_tracking, InstantiationReference, ImportReference

        py_file = tmp_path / "test.py"
        py_file.write_text("""
class Database:
    '''A database connection class'''
    def connect(self):
        pass
""")

        result = parser.parse_file(py_file)
        cls = result.classes[0]

        # Add complete usage tracking data
        instantiations = [
            InstantiationReference("init_db", "setup.py", 15, "function"),
            InstantiationReference("get_connection", "db.py", 42, "function"),
            InstantiationReference("<module>", "config.py", 5, "module")
        ]
        imports = [
            ImportReference("app.py", 3, "from", "Database"),
            ImportReference("setup.py", 1, "from", "Database"),
            ImportReference("tests/test_db.py", 2, "from", None)
        ]
        instantiation_count = 47

        enhanced = enhance_class_with_usage_tracking(
            cls,
            instantiated_by=instantiations,
            imported_by=imports,
            instantiation_count=instantiation_count
        )

        # Verify all fields present
        assert enhanced['name'] == 'Database'
        assert len(enhanced['instantiated_by']) == 3
        assert len(enhanced['imported_by']) == 3
        assert enhanced['instantiation_count'] == 47

        # Verify instantiation details
        assert enhanced['instantiated_by'][0]['instantiator'] == 'init_db'
        assert enhanced['instantiated_by'][1]['file'] == 'db.py'
        assert enhanced['instantiated_by'][2]['context'] == 'module'

        # Verify import details
        assert enhanced['imported_by'][0]['importer'] == 'app.py'
        assert enhanced['imported_by'][1]['alias'] == 'Database'
        assert enhanced['imported_by'][2]['import_type'] == 'from'

    def test_different_import_types(self):
        """Test ImportReference with different import types."""
        from claude_skills.llm_doc_gen.analysis.schema import ImportReference

        # Direct import: import module
        direct = ImportReference("app.py", 1, "direct")
        assert direct.to_dict()['import_type'] == "direct"

        # From import: from module import Class
        from_import = ImportReference("app.py", 2, "from", "MyClass")
        assert from_import.to_dict()['import_type'] == "from"

        # Dynamic import: __import__() or importlib
        dynamic = ImportReference("plugin.py", 10, "dynamic")
        assert dynamic.to_dict()['import_type'] == "dynamic"

    def test_instantiation_context_types(self):
        """Test InstantiationReference with different context types."""
        from claude_skills.llm_doc_gen.analysis.schema import InstantiationReference

        # Module-level instantiation
        module_inst = InstantiationReference("config_loader", "config.py", 20, "module")
        assert module_inst.to_dict()['context'] == "module"

        # Function instantiation
        func_inst = InstantiationReference("create_obj", "factory.py", 5, "function")
        assert func_inst.to_dict()['context'] == "function"

        # Method instantiation
        method_inst = InstantiationReference("build", "builder.py", 15, "method")
        assert method_inst.to_dict()['context'] == "method"
