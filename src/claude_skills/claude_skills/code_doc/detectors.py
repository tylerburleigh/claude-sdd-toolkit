"""
Framework and codebase pattern detection.

Simple programmatic detection of frameworks, key files, and architectural layers.
Supports multi-language projects.
"""

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from collections import defaultdict
import fnmatch


def _should_exclude_path(file_path: Path, exclude_patterns: List[str]) -> bool:
    """
    Check if a file path should be excluded based on patterns.

    Uses path component matching to avoid false positives.
    For example, '.git' will match '.git/' but not '.github/'.

    Args:
        file_path: Path to check
        exclude_patterns: List of patterns to exclude

    Returns:
        True if file should be excluded
    """
    path_parts = file_path.parts
    path_str = str(file_path)

    for pattern in exclude_patterns:
        # Check if pattern matches any path component exactly
        if pattern in path_parts:
            return True

        # Handle wildcards (e.g., '*.egg-info')
        if '*' in pattern:
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        # Special case for multi-part patterns like '.env.local'
        # Only match if pattern has multiple dots or is clearly a file pattern
        if pattern.count('.') > 1:
            # For patterns like '.env.local', match as substring
            if pattern in path_str:
                return True

    return False


def detect_languages(project_root: Path, exclude_patterns: Optional[List[str]] = None) -> Set[str]:
    """
    Detect programming languages present in a project.

    Args:
        project_root: Root directory of the project
        exclude_patterns: Optional list of patterns to exclude from scanning

    Returns:
        Set of detected language names
    """
    if exclude_patterns is None:
        exclude_patterns = []

    language_extensions = {
        'python': {'.py'},
        'javascript': {'.js', '.jsx', '.mjs', '.cjs'},
        'typescript': {'.ts', '.tsx'},
        'go': {'.go'},
        'html': {'.html', '.htm'},
        'css': {'.css', '.scss', '.sass', '.less'},
        'java': {'.java'},
        'rust': {'.rs'},
        'c': {'.c', '.h'},
        'cpp': {'.cpp', '.cxx', '.cc', '.hpp', '.hxx'},
    }

    detected = set()
    for file_path in project_root.rglob('*'):
        if file_path.is_file() and not _should_exclude_path(file_path, exclude_patterns):
            ext = file_path.suffix.lower()
            for lang, exts in language_extensions.items():
                if ext in exts:
                    detected.add(lang)

    return detected


def get_language_for_extension(extension: str) -> str:
    """
    Get language name for a file extension.

    Args:
        extension: File extension (with or without dot)

    Returns:
        Language name or 'unknown'
    """
    ext = extension.lstrip('.').lower()
    mapping = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'javascript',
        'mjs': 'javascript',
        'cjs': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'go': 'go',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'css',
        'sass': 'css',
        'less': 'css',
    }
    return mapping.get(ext, 'unknown')


def detect_framework(modules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect web framework and other major libraries.

    Args:
        modules: List of module information from CodebaseAnalyzer

    Returns:
        Dictionary with detected framework info
    """
    framework_signatures = {
        'FastAPI': ['fastapi', 'fastapi.FastAPI', 'fastapi.APIRouter'],
        'Django': ['django', 'django.conf', 'django.http'],
        'Flask': ['flask', 'flask.Flask', 'flask.request'],
        'Starlette': ['starlette', 'starlette.applications'],
        'Click': ['click', 'click.command', 'click.group'],
        'Typer': ['typer', 'typer.Typer'],
        'Pytest': ['pytest', 'pytest.fixture'],
        'SQLAlchemy': ['sqlalchemy', 'sqlalchemy.orm'],
        'Pydantic': ['pydantic', 'pydantic.BaseModel'],
        'Redis': ['redis', 'redis.asyncio'],
        'Celery': ['celery', 'celery.Celery'],
    }

    detected = {}
    confidence = {}

    # Aggregate all imports across modules
    all_imports = set()
    for module in modules:
        all_imports.update(module.get('imports', []))

    # Check each framework signature
    for framework, signatures in framework_signatures.items():
        matches = sum(1 for sig in signatures if any(sig in imp for imp in all_imports))
        if matches > 0:
            detected[framework] = True
            confidence[framework] = min(matches / len(signatures), 1.0)

    # Determine primary framework (web frameworks take precedence)
    primary = None
    web_frameworks = ['FastAPI', 'Django', 'Flask', 'Starlette']
    cli_frameworks = ['Click', 'Typer']

    for fw in web_frameworks:
        if fw in detected:
            primary = fw
            break

    if not primary:
        for fw in cli_frameworks:
            if fw in detected:
                primary = fw
                break

    return {
        'detected': detected,
        'confidence': confidence,
        'primary': primary,
        'type': 'web' if primary in web_frameworks else ('cli' if primary in cli_frameworks else 'library')
    }


def identify_key_files(modules: List[Dict[str, Any]], project_root: Path = None) -> List[str]:
    """
    Identify key files that should be read for understanding the codebase.

    Args:
        modules: List of module information
        project_root: Project root directory (optional)

    Returns:
        List of file paths (relative) in suggested reading order
    """
    key_files = []
    file_scores = {}

    # Entry point patterns (highest priority)
    entry_patterns = ['main.py', 'app.py', '__main__.py', 'cli.py', 'server.py']

    # Config patterns (high priority)
    config_patterns = ['config.py', 'settings.py', '__init__.py']

    # Core patterns (medium priority)
    core_patterns = ['models.py', 'schema.py', 'session.py', 'routes.py', 'router.py']

    for module in modules:
        file_path = module['file']
        filename = Path(file_path).name

        score = 0

        # Score based on patterns
        if filename in entry_patterns:
            score += 100
        elif filename in config_patterns:
            score += 50
        elif filename in core_patterns:
            score += 30

        # Boost score if file is at project root
        if '/' not in file_path or file_path.count('/') == 1:
            score += 20

        # Boost if has docstring
        if module.get('docstring'):
            score += 10

        # Boost if has multiple classes
        if len(module.get('classes', [])) > 2:
            score += 15

        # Boost if has functions
        if len(module.get('functions', [])) > 0:
            score += 5

        if score > 0:
            file_scores[file_path] = score

    # Sort by score and return top files
    sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
    key_files = [f[0] for f in sorted_files[:15]]  # Top 15 files

    # Add README if it exists and wasn't included
    if project_root:
        for readme in ['README.md', 'README.rst', 'README.txt']:
            readme_path = project_root / readme
            if readme_path.exists():
                readme_rel = str(readme_path.relative_to(project_root))
                if readme_rel not in key_files:
                    key_files.insert(0, readme_rel)
                break

    return key_files


def detect_layers(modules: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Detect architectural layers by grouping modules.

    Args:
        modules: List of module information

    Returns:
        Dictionary mapping layer names to file paths
    """
    layers = defaultdict(list)

    layer_patterns = {
        'routers': ['router', 'route', 'api', 'endpoint', 'handler'],
        'models': ['model', 'schema', 'entity', 'domain'],
        'services': ['service', 'business', 'logic', 'manager', 'use_case'],
        'repositories': ['repository', 'repo', 'dao', 'data'],
        'middleware': ['middleware', 'interceptor', 'filter'],
        'utils': ['util', 'helper', 'common', 'lib'],
        'config': ['config', 'setting', 'env'],
        'tests': ['test', 'spec'],
        'migrations': ['migration', 'alembic', 'migrate'],
    }

    for module in modules:
        file_path = module['file']
        file_lower = file_path.lower()

        # Check each layer pattern
        matched = False
        for layer, patterns in layer_patterns.items():
            if any(pattern in file_lower for pattern in patterns):
                layers[layer].append(file_path)
                matched = True
                break

        # If no match, try to infer from directory structure
        if not matched:
            parts = file_path.split('/')
            if len(parts) > 1:
                dir_name = parts[-2]  # Parent directory
                for layer, patterns in layer_patterns.items():
                    if any(pattern in dir_name.lower() for pattern in patterns):
                        layers[layer].append(file_path)
                        matched = True
                        break

        # Default to 'core' if still no match
        if not matched and len(parts) <= 2:
            layers['core'].append(file_path)

    return dict(layers)


def suggest_reading_order(key_files: List[str], framework_info: Dict[str, Any]) -> List[str]:
    """
    Suggest optimal reading order for key files.

    Args:
        key_files: List of identified key files
        framework_info: Framework detection result

    Returns:
        Ordered list of files to read
    """
    # Create priority groups
    priority_groups = {
        'entry': [],
        'config': [],
        'models': [],
        'routes': [],
        'services': [],
        'other': []
    }

    for file in key_files:
        filename = Path(file).name.lower()

        if any(p in filename for p in ['main', 'app', '__main__', 'cli']):
            priority_groups['entry'].append(file)
        elif any(p in filename for p in ['config', 'setting']):
            priority_groups['config'].append(file)
        elif any(p in filename for p in ['model', 'schema', 'entity']):
            priority_groups['models'].append(file)
        elif any(p in filename for p in ['route', 'router', 'api', 'endpoint']):
            priority_groups['routes'].append(file)
        elif any(p in filename for p in ['service', 'business', 'logic']):
            priority_groups['services'].append(file)
        else:
            priority_groups['other'].append(file)

    # Build reading order
    reading_order = []
    reading_order.extend(priority_groups['entry'])
    reading_order.extend(priority_groups['config'])
    reading_order.extend(priority_groups['models'])
    reading_order.extend(priority_groups['routes'])
    reading_order.extend(priority_groups['services'])
    reading_order.extend(priority_groups['other'])

    return reading_order


def extract_readme(project_root: Path) -> Optional[str]:
    """
    Extract README content if it exists.

    Args:
        project_root: Project root directory

    Returns:
        README content or None
    """
    for readme in ['README.md', 'README.rst', 'README.txt', 'README']:
        readme_path = project_root / readme
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass

    return None


def create_context_summary(
    framework_info: Dict[str, Any],
    key_files: List[str],
    layers: Dict[str, List[str]],
    statistics: Dict[str, Any],
    readme_content: Optional[str] = None
) -> str:
    """
    Create a structured summary of codebase context for AI analysis.

    Args:
        framework_info: Framework detection result
        key_files: Identified key files
        layers: Layer grouping
        statistics: Code statistics
        readme_content: README content (optional)

    Returns:
        Formatted context summary
    """
    lines = []

    # Project type and framework
    lines.append("## Codebase Context")
    lines.append("")

    if framework_info['primary']:
        lines.append(f"**Primary Framework:** {framework_info['primary']}")
        lines.append(f"**Type:** {framework_info['type']}")
    else:
        lines.append("**Type:** Python library/package")

    lines.append("")

    # Additional frameworks/libraries
    if len(framework_info['detected']) > 1:
        lines.append("**Additional Libraries:**")
        for fw, conf in framework_info['confidence'].items():
            if fw != framework_info['primary']:
                conf_pct = int(conf * 100)
                lines.append(f"- {fw} ({conf_pct}% confidence)")
        lines.append("")

    # Statistics
    lines.append("**Statistics:**")
    lines.append(f"- Total Files: {statistics['total_files']}")
    lines.append(f"- Total Lines: {statistics['total_lines']}")
    lines.append(f"- Total Classes: {statistics['total_classes']}")
    lines.append(f"- Total Functions: {statistics['total_functions']}")
    lines.append(f"- Avg Complexity: {statistics['avg_complexity']}")
    lines.append("")

    # Architectural layers
    lines.append("**Architectural Layers:**")
    for layer, files in sorted(layers.items()):
        lines.append(f"- {layer}: {len(files)} files")
    lines.append("")

    # Key files
    lines.append("**Key Files (suggested reading order):**")
    for i, file in enumerate(key_files[:10], 1):  # Top 10
        lines.append(f"{i}. {file}")
    lines.append("")

    # README excerpt
    if readme_content:
        lines.append("**README Excerpt:**")
        # Get first few non-empty lines
        readme_lines = [l for l in readme_content.split('\n')[:20] if l.strip()]
        lines.extend(readme_lines[:10])
        if len(readme_lines) > 10:
            lines.append("...")
        lines.append("")

    return '\n'.join(lines)
