"""
Output formatting module.
Generates Markdown and JSON documentation from analyzed codebase data.
Supports multi-language projects.
"""

from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict


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

    def generate(self, analysis: Dict[str, Any], statistics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON documentation with multi-language support."""
        # Detect languages present
        languages = set()
        for module in analysis.get('modules', []):
            lang = module.get('language', 'unknown')
            if lang != 'unknown':
                languages.add(lang)

        return {
            "metadata": {
                "project_name": self.project_name,
                "version": self.version,
                "generated_at": datetime.now().isoformat(),
                "languages": sorted(list(languages)) if languages else ["unknown"]
            },
            "statistics": statistics,
            "modules": analysis['modules'],
            "classes": analysis['classes'],
            "functions": analysis['functions'],
            "dependencies": analysis['dependencies']
        }
