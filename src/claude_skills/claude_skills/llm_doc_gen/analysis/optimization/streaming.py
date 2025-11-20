"""
Streaming JSON output for memory-efficient codebase documentation.

Provides StreamingJSONWriter that writes JSON incrementally to disk,
avoiding large in-memory accumulation of parsed entities.
"""

import gzip
import json
from pathlib import Path
from typing import Dict, Any, Optional, TextIO, Union
from contextlib import contextmanager


class CompressionWrapper:
    """
    Wrapper for optional gzip compression of output files.

    Provides transparent compression by wrapping file handles with gzip.GzipFile
    when compression is enabled, reducing disk space usage by 60-80% for JSON output.

    Attributes:
        file_path: Path to the output file
        compress: Whether to enable gzip compression
        file_handle: Underlying file handle (gzipped or plain)

    Example:
        >>> # With compression
        >>> wrapper = CompressionWrapper('/path/to/output.json.gz', compress=True)
        >>> handle = wrapper.open()
        >>> handle.write('{"data": "compressed"}')
        >>> wrapper.close()
        >>>
        >>> # Without compression
        >>> wrapper = CompressionWrapper('/path/to/output.json', compress=False)
        >>> handle = wrapper.open()
        >>> handle.write('{"data": "plain"}')
        >>> wrapper.close()
    """

    def __init__(self, file_path: Path, compress: bool = False):
        """
        Initialize compression wrapper.

        Args:
            file_path: Path to the output file
            compress: Whether to enable gzip compression (default: False)
        """
        self.file_path = Path(file_path)
        self.compress = compress
        self.file_handle: Optional[Union[TextIO, gzip.GzipFile]] = None

    def open(self, mode: str = 'wt') -> Union[TextIO, gzip.GzipFile]:
        """
        Open the file with optional compression.

        Args:
            mode: File open mode (default: 'wt' for text write)

        Returns:
            File handle (gzipped if compression enabled, plain otherwise)

        Raises:
            RuntimeError: If file is already open
        """
        if self.file_handle is not None:
            raise RuntimeError("File already open")

        if self.compress:
            # Open with gzip compression
            # Use text mode by default for JSON
            if 't' not in mode and 'b' not in mode:
                mode = mode + 't'
            self.file_handle = gzip.open(self.file_path, mode=mode, encoding='utf-8')
        else:
            # Open as plain text file
            self.file_handle = open(self.file_path, mode=mode, encoding='utf-8')

        return self.file_handle

    def close(self) -> None:
        """
        Close the file handle.

        Safe to call multiple times.
        """
        if self.file_handle is not None:
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        """Context manager entry - opens file."""
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes file."""
        self.close()
        return False


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

    def __init__(self, output_path: Path, compress: bool = False):
        """
        Initialize streaming JSON writer.

        Args:
            output_path: Path where JSON output will be written
            compress: Whether to enable gzip compression (default: False)
        """
        self.output_path = Path(output_path)
        self.compress = compress
        self.file_handle: Optional[Union[TextIO, gzip.GzipFile]] = None
        self._compression_wrapper: Optional[CompressionWrapper] = None
        self._first_module = True
        self._first_class = True
        self._first_function = True
        self._metadata_written = False
        self._dependencies_written = False
        self._errors_written = False
        self._finalized = False

    def __enter__(self):
        """Context manager entry - opens file and starts JSON structure."""
        # Use CompressionWrapper if compression enabled
        if self.compress:
            self._compression_wrapper = CompressionWrapper(self.output_path, compress=True)
            self.file_handle = self._compression_wrapper.open('wt')
        else:
            self.file_handle = open(self.output_path, 'w', encoding='utf-8')

        # Start root JSON object
        self.file_handle.write('{\n')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - finalizes JSON and closes file."""
        if not self._finalized:
            self.finalize()
        if self.file_handle:
            # Use CompressionWrapper's close if available
            if self._compression_wrapper:
                self._compression_wrapper.close()
            else:
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


class NDJSONWriter:
    """
    Newline-delimited JSON writer for extremely memory-efficient streaming.

    NDJSON format writes each entity as a complete JSON object on its own line,
    making it ideal for:
    - Processing with line-oriented Unix tools (grep, sed, awk)
    - Streaming processing where entities arrive one at a time
    - Parallel processing (each line is independent)
    - Extremely large datasets that don't fit in memory

    Unlike regular JSON, NDJSON doesn't require the entire document to be
    valid JSON - each line is independently parseable.

    Attributes:
        output_path: Path to the output NDJSON file
        compress: Whether to enable gzip compression
        file_handle: Open file handle for writing
        _entity_count: Number of entities written

    Example:
        >>> with NDJSONWriter('/path/to/output.ndjson') as writer:
        ...     writer.write_metadata({'project': 'my-project'})
        ...     writer.write_entity('module', {'name': 'mod1'})
        ...     writer.write_entity('class', {'name': 'Class1'})
    """

    def __init__(self, output_path: Path, compress: bool = False):
        """
        Initialize NDJSON writer.

        Args:
            output_path: Path where NDJSON output will be written
            compress: Whether to enable gzip compression (default: False)
        """
        self.output_path = Path(output_path)
        self.compress = compress
        self.file_handle: Optional[Union[TextIO, gzip.GzipFile]] = None
        self._compression_wrapper: Optional[CompressionWrapper] = None
        self._entity_count = 0

    def __enter__(self):
        """Context manager entry - opens file."""
        if self.compress:
            self._compression_wrapper = CompressionWrapper(self.output_path, compress=True)
            self.file_handle = self._compression_wrapper.open('wt')
        else:
            self.file_handle = open(self.output_path, 'w', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes file."""
        if self.file_handle:
            if self._compression_wrapper:
                self._compression_wrapper.close()
            else:
                self.file_handle.close()
            self.file_handle = None
        return False

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Write metadata as the first line.

        Args:
            metadata: Dictionary containing project metadata

        Example:
            >>> writer.write_metadata({
            ...     'type': 'metadata',
            ...     'project': 'my-project',
            ...     'version': '1.0.0'
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        # Add type field if not present
        if 'type' not in metadata:
            metadata = {'type': 'metadata', **metadata}

        self.file_handle.write(json.dumps(metadata) + '\n')
        self._entity_count += 1

    def write_entity(self, entity_type: str, entity: Dict[str, Any]) -> None:
        """
        Write a single entity as one line of JSON.

        Args:
            entity_type: Type of entity ('module', 'class', 'function', etc.)
            entity: Dictionary representation of the entity

        Example:
            >>> writer.write_entity('module', {
            ...     'name': 'my_module',
            ...     'file_path': 'src/my_module.py'
            ... })
        """
        if not self.file_handle:
            raise RuntimeError("File not open. Use context manager (with statement).")

        # Add type field if not present
        if 'type' not in entity:
            entity = {'type': entity_type, **entity}

        self.file_handle.write(json.dumps(entity) + '\n')
        self._entity_count += 1

    def write_module(self, module: Dict[str, Any]) -> None:
        """Write a module entity."""
        self.write_entity('module', module)

    def write_class(self, class_obj: Dict[str, Any]) -> None:
        """Write a class entity."""
        self.write_entity('class', class_obj)

    def write_function(self, function: Dict[str, Any]) -> None:
        """Write a function entity."""
        self.write_entity('function', function)

    def write_dependencies(self, dependencies: Dict[str, Any]) -> None:
        """
        Write dependencies as a single entity.

        Args:
            dependencies: Dictionary mapping file paths to their dependencies
        """
        self.write_entity('dependencies', {'data': dependencies})

    def write_error(self, error: str) -> None:
        """
        Write a single error as an entity.

        Args:
            error: Error message

        Example:
            >>> writer.write_error('Parse error in file.py')
        """
        self.write_entity('error', {'message': error})

    def write_errors(self, errors: list) -> None:
        """
        Write multiple errors as separate entities.

        Args:
            errors: List of error messages
        """
        for error in errors:
            self.write_error(error)

    def get_entity_count(self) -> int:
        """
        Get the number of entities written.

        Returns:
            Total number of JSON lines written
        """
        return self._entity_count


@contextmanager
def ndjson_output(output_path: Path, compress: bool = False):
    """
    Convenience context manager for NDJSON output.

    Args:
        output_path: Path where NDJSON output will be written
        compress: Whether to enable gzip compression

    Yields:
        NDJSONWriter instance for writing entities

    Example:
        >>> with ndjson_output('/path/to/output.ndjson') as writer:
        ...     writer.write_metadata({'project': 'my-project'})
        ...     for module in modules:
        ...         writer.write_module(module.to_dict())
    """
    writer = NDJSONWriter(output_path, compress=compress)
    try:
        with writer:
            yield writer
    finally:
        pass
