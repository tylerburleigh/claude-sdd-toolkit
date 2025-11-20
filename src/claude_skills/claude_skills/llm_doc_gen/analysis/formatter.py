"""
Output formatting module.
Generates Markdown and JSON documentation from analyzed codebase data.
Supports multi-language projects.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path

# Handle both direct execution and module import
try:
    from .schema import SCHEMA_VERSION
    from .optimization.streaming import StreamingJSONWriter
except ImportError:
    from schema import SCHEMA_VERSION
    from optimization.streaming import StreamingJSONWriter


class MarkdownGenerator:
    """Generates Markdown documentation."""

    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version

    def generate(self, analysis: Dict[str, Any], statistics: Dict[str, Any]) -> str:
        """Generate complete Markdown documentation with multi-language support."""
        sections = [
            self._header(),
            self._statistics(statistics),
            self._language_breakdown(statistics),
            self._classes(analysis['classes']),
            self._functions(analysis['functions']),
            self._dependencies(analysis['dependencies'])
        ]

        return '\n\n'.join(sections)

    def _header(self) -> str:
        """Generate header section."""
        return f"""# {self.project_name} Documentation

**Version:** {self.version}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---"""

    def _statistics(self, stats: Dict) -> str:
        """Generate statistics section."""
        lines = ["## 📊 Project Statistics", ""]

        # Show overall stats (skip by_language for this section)
        for key, value in stats.items():
            if key == 'by_language':
                continue

            label = key.replace('_', ' ').title()
            if isinstance(value, list):
                lines.append(f"- **{label}:**")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"- **{label}:** {value}")
        return '\n'.join(lines)

    def _language_breakdown(self, stats: Dict) -> str:
        """Generate per-language breakdown section."""
        by_lang = stats.get('by_language', {})
        if not by_lang or len(by_lang) <= 1:
            return ""  # Skip if only one language

        lines = ["## 🌐 Language Breakdown", ""]

        for lang in sorted(by_lang.keys()):
            lang_stats = by_lang[lang]
            lines.append(f"### {lang.upper()}")
            lines.append("")
            lines.append(f"- **Files:** {lang_stats['files']}")
            lines.append(f"- **Lines:** {lang_stats['lines']}")
            lines.append(f"- **Classes:** {lang_stats['classes']}")
            lines.append(f"- **Functions:** {lang_stats['functions']}")
            if lang_stats['avg_complexity'] > 0:
                lines.append(f"- **Avg Complexity:** {lang_stats['avg_complexity']}")
            lines.append("")

        return '\n'.join(lines)

    def _classes(self, classes: List[Dict]) -> str:
        """Generate classes section."""
        if not classes:
            return "## 🏛️ Classes\n\n*No classes found.*"

        lines = ["## 🏛️ Classes", ""]

        for cls in sorted(classes, key=lambda x: x['name']):
            lines.append(f"### `{cls['name']}`")
            lines.append("")

            # Show language
            lang = cls.get('language', 'unknown')
            lines.append(f"**Language:** {lang}")

            if cls['bases']:
                bases = ', '.join(f"`{b}`" for b in cls['bases'])
                lines.append(f"**Inherits from:** {bases}")

            lines.append(f"**Defined in:** `{cls['file']}:{cls['line']}`")
            lines.append("")

            if cls['docstring']:
                lines.append("**Description:**")
                lines.append(f"> {cls['docstring']}")
                lines.append("")

            if cls['methods']:
                lines.append("**Methods:**")
                for method in cls['methods']:
                    lines.append(f"- `{method}()`")
                lines.append("")

            if cls['properties']:
                lines.append("**Properties:**")
                for prop in cls['properties']:
                    lines.append(f"- `{prop}`")
                lines.append("")

            lines.append("---")
            lines.append("")

        return '\n'.join(lines)

    def _functions(self, functions: List[Dict]) -> str:
        """Generate functions section."""
        if not functions:
            return "## ⚡ Functions\n\n*No functions found.*"

        lines = ["## ⚡ Functions", ""]

        for func in sorted(functions, key=lambda x: x['name']):
            # Build signature
            params = ', '.join(p['name'] for p in func['parameters'])
            ret_type = func['return_type'] or 'None'

            if func.get('is_async'):
                lines.append(f"### `async {func['name']}({params}) -> {ret_type}`")
            else:
                lines.append(f"### `{func['name']}({params}) -> {ret_type}`")

            lines.append("")

            # Show language
            lang = func.get('language', 'unknown')
            lines.append(f"**Language:** {lang}")
            lines.append(f"**Defined in:** `{func['file']}:{func['line']}`")

            if func.get('complexity', 1) > 10:
                lines.append(f"⚠️ **Complexity:** {func['complexity']} (High)")
            else:
                lines.append(f"**Complexity:** {func['complexity']}")

            lines.append("")

            if func['decorators']:
                lines.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in func['decorators'])}")
                lines.append("")

            if func['docstring']:
                lines.append("**Description:**")
                lines.append(f"> {func['docstring']}")
                lines.append("")

            if func['parameters']:
                lines.append("**Parameters:**")
                for param in func['parameters']:
                    param_type = param.get('type', 'Any')
                    lines.append(f"- `{param['name']}`: {param_type}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return '\n'.join(lines)

    def _dependencies(self, deps: Dict) -> str:
        """Generate dependencies section."""
        if not deps:
            return "## 📦 Dependencies\n\n*No dependencies found.*"

        lines = ["## 📦 Dependencies", ""]

        for module, imports in sorted(deps.items()):
            if imports:
                lines.append(f"### `{module}`")
                lines.append("")
                for imp in sorted(imports):
                    lines.append(f"- `{imp}`")
                lines.append("")

        return '\n'.join(lines)


class JSONGenerator:
    """Generates JSON documentation."""

    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version

    def generate(
        self,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        streaming: bool = False,
        output_path: Optional[Path] = None,
        compress: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON documentation with multi-language support.

        Args:
            analysis: Analyzed codebase data
            statistics: Code statistics
            streaming: If True, use StreamingJSONWriter for memory-efficient output
            output_path: Path for streaming output (required if streaming=True)
            compress: Enable gzip compression for streaming output

        Returns:
            Dict containing JSON documentation (if streaming=False)
            None (if streaming=True, output written to file)

        Raises:
            ValueError: If streaming=True but output_path not provided
        """
        # Detect languages present
        languages = set()
        for module in analysis.get('modules', []):
            lang = module.get('language', 'unknown')
            if lang != 'unknown':
                languages.add(lang)

        # Prepare metadata
        metadata = {
            "project_name": self.project_name,
            "version": self.version,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "languages": sorted(list(languages)) if languages else ["unknown"],
            "schema_version": SCHEMA_VERSION
        }

        if streaming:
            # Streaming mode - write incrementally to file
            if output_path is None:
                raise ValueError("output_path required when streaming=True")

            with StreamingJSONWriter(output_path, compress=compress) as writer:
                # Write metadata
                writer.write_metadata({**metadata, **statistics})

                # Write modules incrementally
                for module in analysis.get('modules', []):
                    writer.write_module(module)

                # Write classes incrementally
                for class_obj in analysis.get('classes', []):
                    writer.write_class(class_obj)

                # Write functions incrementally
                for function in analysis.get('functions', []):
                    writer.write_function(function)

                # Write dependencies
                writer.write_dependencies(analysis.get('dependencies', {}))

                # Write errors if any
                writer.write_errors(analysis.get('errors', []))

            return None  # No in-memory return for streaming
        else:
            # Traditional mode - build entire structure in memory
            return {
                "metadata": metadata,
                "statistics": statistics,
                "modules": analysis['modules'],
                "classes": analysis['classes'],
                "functions": analysis['functions'],
                "dependencies": analysis['dependencies']
            }

    def generate_streaming(
        self,
        output_file: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        compress: bool = False
    ) -> None:
        """
        Convenience method for streaming JSON output to file.

        This is a shorthand for calling generate() with streaming=True.

        Args:
            output_file: Path where JSON output will be written
            analysis: Analyzed codebase data
            statistics: Code statistics
            compress: Enable gzip compression (default: False)

        Example:
            >>> generator = JSONGenerator('my-project', '1.0.0')
            >>> generator.generate_streaming(
            ...     Path('output.json'),
            ...     analysis_data,
            ...     stats_data,
            ...     compress=True
            ... )
        """
        self.generate(
            analysis=analysis,
            statistics=statistics,
            streaming=True,
            output_path=output_file,
            compress=compress
        )


class SummaryGenerator:
    """
    Generates lightweight codebase summary JSON with signatures only.

    This generator produces a minimal summary suitable for quick reference
    and IDE integration. It includes function/class signatures and basic
    metadata but omits docstrings, function bodies, and detailed analysis
    to keep the output size small.
    """

    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version

    def generate(
        self,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate lightweight summary JSON with signatures only.

        Args:
            analysis: Analyzed codebase data
            statistics: Code statistics

        Returns:
            Dict containing minimal summary documentation
        """
        # Detect languages present
        languages = set()
        for module in analysis.get('modules', []):
            lang = module.get('language', 'unknown')
            if lang != 'unknown':
                languages.add(lang)

        # Prepare metadata
        metadata = {
            "project_name": self.project_name,
            "version": self.version,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "languages": sorted(list(languages)) if languages else ["unknown"],
            "schema_version": SCHEMA_VERSION,
            "summary": True  # Flag to indicate this is a summary format
        }

        # Generate lightweight summaries
        return {
            "metadata": metadata,
            "statistics": self._summarize_statistics(statistics),
            "modules": self._summarize_modules(analysis.get('modules', [])),
            "classes": self._summarize_classes(analysis.get('classes', [])),
            "functions": self._summarize_functions(analysis.get('functions', []))
        }

    def _summarize_statistics(self, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only essential statistics."""
        return {
            "total_files": statistics.get("total_files", 0),
            "total_classes": statistics.get("total_classes", 0),
            "total_functions": statistics.get("total_functions", 0),
            "total_lines": statistics.get("total_lines", 0)
        }

    def _summarize_modules(self, modules: List[Dict]) -> List[Dict]:
        """Generate lightweight module summaries."""
        summaries = []
        for module in modules:
            summaries.append({
                "path": module.get("path"),
                "language": module.get("language"),
                "lines": module.get("lines", 0),
                "classes": len(module.get("classes", [])),
                "functions": len(module.get("functions", []))
            })
        return summaries

    def _summarize_classes(self, classes: List[Dict]) -> List[Dict]:
        """Generate lightweight class summaries with signatures only."""
        summaries = []
        for cls in classes:
            summary = {
                "name": cls.get("name"),
                "file": cls.get("file"),
                "line": cls.get("line"),
                "bases": cls.get("bases", []),
                "methods": []
            }

            # Include only method signatures (no docstrings or bodies)
            for method in cls.get("methods", []):
                summary["methods"].append({
                    "name": method.get("name"),
                    "signature": method.get("signature"),
                    "line": method.get("line"),
                    "parameters": method.get("parameters", []),
                    "return_type": method.get("return_type")
                })

            summaries.append(summary)
        return summaries

    def _summarize_functions(self, functions: List[Dict]) -> List[Dict]:
        """Generate lightweight function summaries with signatures only."""
        summaries = []
        for func in functions:
            summaries.append({
                "name": func.get("name"),
                "signature": func.get("signature"),
                "file": func.get("file"),
                "line": func.get("line"),
                "parameters": func.get("parameters", []),
                "return_type": func.get("return_type")
            })
        return summaries


class DetailWriter:
    """
    Generates detailed per-module documentation files.

    Creates individual JSON files for each module in a docs/details/ directory,
    containing complete documentation including docstrings, function bodies,
    and full analysis data for that module.
    """

    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version

    def write_module_details(
        self,
        output_dir: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> List[Path]:
        """
        Generate detailed documentation files for each module.

        Args:
            output_dir: Base output directory (details will be in output_dir/details/)
            analysis: Analyzed codebase data
            statistics: Code statistics

        Returns:
            List of paths to generated detail files
        """
        details_dir = output_dir / "details"
        details_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Generate a detail file for each module
        for module in analysis.get('modules', []):
            module_path = Path(module['path'])
            # Create safe filename from module path
            safe_name = str(module_path).replace('/', '_').replace('\\', '_')
            detail_file = details_dir / f"{safe_name}.json"

            # Gather all classes and functions for this module
            module_classes = [
                cls for cls in analysis.get('classes', [])
                if cls.get('file') == module['path']
            ]
            module_functions = [
                func for func in analysis.get('functions', [])
                if func.get('file') == module['path']
            ]

            # Build detail document
            detail_doc = {
                "metadata": {
                    "project_name": self.project_name,
                    "version": self.version,
                    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "schema_version": SCHEMA_VERSION,
                    "module_path": module['path']
                },
                "module": module,
                "classes": module_classes,
                "functions": module_functions,
                "statistics": {
                    "classes_count": len(module_classes),
                    "functions_count": len(module_functions),
                    "lines": module.get('lines', 0)
                }
            }

            # Write detail file
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump(detail_doc, f, indent=2, ensure_ascii=False)

            generated_files.append(detail_file)

        return generated_files
