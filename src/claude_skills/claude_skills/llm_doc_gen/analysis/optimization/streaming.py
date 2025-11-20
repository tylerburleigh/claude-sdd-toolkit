"""
Streaming JSON output for memory-efficient codebase documentation.

Provides StreamingJSONWriter that writes JSON incrementally to disk,
avoiding large in-memory accumulation of parsed entities.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, TextIO
from contextlib import contextmanager


class StreamingJSONWriter:
    """
    Memory-efficient JSON writer that streams output incrementally.

    Instead of accumulating all parsed entities in memory and then writing
    the entire JSON at once, this class writes each entity as it becomes
    available, significantly reducing memory footprint.

    The writer produces valid JSON by:
    1. Opening the root object and writing metadata
    2. Starting arrays for modules, classes, functions
    3. Writing each entity as it arrives
    4. Properly closing all arrays and the root object

    Attributes:
        output_path: Path to the output JSON file
        file_handle: Open file handle for writing
        _first_module: Track if first module (for comma placement)
        _first_class: Track if first class (for comma placement)
        _first_function: Track if first function (for comma placement)
        _metadata_written: Track if metadata section written
        _finalized: Track if output has been finalized

    Example:
        >>> with StreamingJSONWriter('/path/to/output.json') as writer:
        ...     writer.write_metadata({'project': 'my-project'})
        ...     writer.write_module({'name': 'module1', ...})
        ...     writer.write_class({'name': 'MyClass', ...})
        ...     writer.write_function({'name': 'my_func', ...})
    """

    def __init__(self, output_path: Path):
        """
        Initialize streaming JSON writer.

        Args:
            output_path: Path where JSON output will be written
        """
        self.output_path = Path(output_path)
        self.file_handle: Optional[TextIO] = None
        self._first_module = True
        self._first_class = True
        self._first_function = True
        self._metadata_written = False
        self._dependencies_written = False
        self._errors_written = False
        self._finalized = False

    def __enter__(self):
        """Context manager entry - opens file and starts JSON structure."""
        self.file_handle = open(self.output_path, 'w', encoding='utf-8')
        # Start root JSON object
        self.file_handle.write('{\n')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - finalizes JSON and closes file."""
        if not self._finalized:
            self.finalize()
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        return False

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Write metadata section at the beginning of the JSON output.

        Must be called before writing any entities. Can only be called once.

        Args:
            metadata: Dictionary containing project metadata (project name,
                     version, timestamp, etc.)

        Raises:
            RuntimeError: If metadata already written or file not open

        Example:
            >>> writer.write_metadata({
            ...     'project': 'my-project',
            ...     'version': '1.0.0',
            ...     'timestamp': '2025-01-01T00:00:00'
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if self._metadata_written:
            raise RuntimeError("Metadata already written. Can only write metadata once.")

        # Write metadata field
        self.file_handle.write('  "metadata": ')
        json.dump(metadata, self.file_handle, indent=2)
        self.file_handle.write(',\n')

        # Start modules array
        self.file_handle.write('  "modules": [\n')

        self._metadata_written = True

    def write_module(self, module: Dict[str, Any]) -> None:
        """
        Write a single module entity to the JSON output.

        Entities are written incrementally as they arrive, avoiding
        memory accumulation.

        Args:
            module: Dictionary representation of a parsed module

        Raises:
            RuntimeError: If metadata not written or file not open

        Example:
            >>> writer.write_module({
            ...     'name': 'my_module',
            ...     'file_path': 'src/my_module.py',
            ...     'docstring': 'Module documentation'
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if not self._metadata_written:
            raise RuntimeError("Must call write_metadata() before writing entities.")

        # Add comma if not first module
        if not self._first_module:
            self.file_handle.write(',\n')
        else:
            self._first_module = False

        # Write module entity with indentation
        module_json = json.dumps(module, indent=2)
        # Indent each line by 4 spaces
        indented = '\n'.join('    ' + line for line in module_json.split('\n'))
        self.file_handle.write(indented)

    def write_class(self, class_obj: Dict[str, Any]) -> None:
        """
        Write a single class entity to the JSON output.

        Must be called after all modules have been written.

        Args:
            class_obj: Dictionary representation of a parsed class

        Raises:
            RuntimeError: If metadata not written or file not open

        Example:
            >>> writer.write_class({
            ...     'name': 'MyClass',
            ...     'file_path': 'src/module.py',
            ...     'methods': [...]
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if not self._metadata_written:
            raise RuntimeError("Must call write_metadata() before writing entities.")

        # Close modules array if this is the first class
        if self._first_class:
            self.file_handle.write('\n  ],\n')
            self.file_handle.write('  "classes": [\n')
            self._first_class = False
        else:
            # Add comma between classes
            self.file_handle.write(',\n')

        # Write class entity with indentation
        class_json = json.dumps(class_obj, indent=2)
        # Indent each line by 4 spaces
        indented = '\n'.join('    ' + line for line in class_json.split('\n'))
        self.file_handle.write(indented)

    def write_function(self, function: Dict[str, Any]) -> None:
        """
        Write a single function entity to the JSON output.

        Must be called after all classes have been written.

        Args:
            function: Dictionary representation of a parsed function

        Raises:
            RuntimeError: If metadata not written or file not open

        Example:
            >>> writer.write_function({
            ...     'name': 'my_function',
            ...     'file_path': 'src/module.py',
            ...     'parameters': [...],
            ...     'return_type': 'str'
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if not self._metadata_written:
            raise RuntimeError("Must call write_metadata() before writing entities.")

        # Close classes array if this is the first function
        if self._first_function:
            # If no classes were written, close modules array first
            if self._first_class:
                self.file_handle.write('\n  ],\n')
                self.file_handle.write('  "classes": [],\n')
            else:
                self.file_handle.write('\n  ],\n')

            self.file_handle.write('  "functions": [\n')
            self._first_function = False
        else:
            # Add comma between functions
            self.file_handle.write(',\n')

        # Write function entity with indentation
        function_json = json.dumps(function, indent=2)
        # Indent each line by 4 spaces
        indented = '\n'.join('    ' + line for line in function_json.split('\n'))
        self.file_handle.write(indented)

    def write_dependencies(self, dependencies: Dict[str, Any]) -> None:
        """
        Write dependencies section to the JSON output.

        Should be called after all entities have been written.

        Args:
            dependencies: Dictionary mapping file paths to their dependencies

        Example:
            >>> writer.write_dependencies({
            ...     'src/module.py': ['os', 'sys', 'typing']
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if self._dependencies_written:
            raise RuntimeError("Dependencies already written.")

        # Close functions array if needed
        if not self._first_function:
            self.file_handle.write('\n  ],\n')
        else:
            # If no functions written, close classes/modules
            if self._first_class:
                self.file_handle.write('\n  ],\n')
                self.file_handle.write('  "classes": [],\n')
            else:
                self.file_handle.write('\n  ],\n')
            self.file_handle.write('  "functions": [],\n')

        # Write dependencies with proper indentation
        self.file_handle.write('  "dependencies": ')
        deps_json = json.dumps(dependencies, indent=2)
        # Indent all lines except the first (which is already at correct position)
        lines = deps_json.split('\n')
        self.file_handle.write(lines[0])
        for line in lines[1:]:
            self.file_handle.write('\n  ' + line)

        self._dependencies_written = True

    def write_errors(self, errors: list) -> None:
        """
        Write errors section to the JSON output.

        Should be called after dependencies (or after entities if no dependencies).

        Args:
            errors: List of error messages encountered during parsing

        Example:
            >>> writer.write_errors(['Parse error in file.py', 'Missing import'])
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if self._errors_written:
            raise RuntimeError("Errors already written.")

        self.file_handle.write(',\n  "errors": ')
        errors_json = json.dumps(errors, indent=2)
        # Indent all lines except the first (which is already at correct position)
        lines = errors_json.split('\n')
        self.file_handle.write(lines[0])
        for line in lines[1:]:
            self.file_handle.write('\n  ' + line)

        self._errors_written = True

    def finalize(self) -> None:
        """
        Finalize the JSON output by closing all open structures.

        Called automatically by context manager, but can be called manually
        if needed. Safe to call multiple times.

        Raises:
            RuntimeError: If file not open
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        if self._finalized:
            return

        # If no entities were written, close arrays appropriately
        if not self._metadata_written:
            # No metadata written at all - write empty structure
            self.file_handle.write('  "modules": [],\n')
            self.file_handle.write('  "classes": [],\n')
            self.file_handle.write('  "functions": [],\n')
            self.file_handle.write('  "dependencies": {},\n')
            self.file_handle.write('  "errors": []\n')
        else:
            # If dependencies and errors already written, we're done - just close root
            if self._dependencies_written and self._errors_written:
                pass  # Everything written, just close root below
            elif self._first_function:
                # Modules/classes written but no functions
                if self._first_class:
                    # Only modules written
                    self.file_handle.write('\n  ],\n')
                    self.file_handle.write('  "classes": [],\n')
                    self.file_handle.write('  "functions": [],\n')
                else:
                    # Modules and classes written
                    self.file_handle.write('\n  ],\n')
                    self.file_handle.write('  "functions": [],\n')

                # Write dependencies and errors if not already written
                if not self._dependencies_written:
                    self.file_handle.write('  "dependencies": {},\n')
                if not self._errors_written:
                    if self._dependencies_written:
                        self.file_handle.write(',\n')
                    self.file_handle.write('  "errors": []\n')
            else:
                # Functions written but not dependencies/errors
                # Close functions array if not already closed
                if not self._dependencies_written and not self._errors_written:
                    self.file_handle.write('\n  ],\n')

                # Write dependencies and errors if not already written
                if not self._dependencies_written:
                    self.file_handle.write('  "dependencies": {},\n')
                if not self._errors_written:
                    if self._dependencies_written:
                        self.file_handle.write(',\n')
                    self.file_handle.write('  "errors": []\n')

        # Close root object
        self.file_handle.write('}\n')

        self._finalized = True


@contextmanager
def streaming_json_output(output_path: Path):
    """
    Convenience context manager for streaming JSON output.

    Args:
        output_path: Path where JSON output will be written

    Yields:
        StreamingJSONWriter instance for writing entities

    Example:
        >>> with streaming_json_output('/path/to/output.json') as writer:
        ...     writer.write_metadata({'project': 'my-project'})
        ...     for module in modules:
        ...         writer.write_module(module.to_dict())
    """
    writer = StreamingJSONWriter(output_path)
    try:
        with writer:
            yield writer
    finally:
        pass
