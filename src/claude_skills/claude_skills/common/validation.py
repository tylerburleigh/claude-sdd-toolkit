"""
Validation utilities and result classes for SDD workflows.
Provides common validation result structures used across all SDD skills.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EnhancedError:
    """Enhanced error message with detailed location and fix information"""
    message: str
    severity: str  # 'critical', 'error', 'warning'
    category: str  # varies by validator type
    location: Optional[str] = None  # File path, line number, JSON path, etc.
    context: Optional[str] = None
    current_value: Optional[str] = None
    expected_value: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False

    def __str__(self) -> str:
        """Format error message for display"""
        icon = {
            'critical': '❌ CRITICAL:',
            'error': '❌ ERROR:',
            'warning': '⚠️  WARNING:'
        }.get(self.severity, '❓ UNKNOWN:')

        parts = [f"{icon} {self.message}"]

        if self.location:
            parts.append(f"   Location: {self.location}")

        if self.context:
            parts.append(f"   Context: {self.context}")

        if self.current_value is not None:
            parts.append(f"   Current: {self.current_value}")

        if self.expected_value is not None:
            parts.append(f"   Expected: {self.expected_value}")

        if self.suggested_fix:
            parts.append(f"   Suggested fix: {self.suggested_fix}")

        if self.auto_fixable:
            parts.append(f"   Auto-fixable: Yes ✓")

        return "\n".join(parts)


@dataclass
class SpecValidationResult:
    """Results of spec document validation"""
    spec_id: str
    spec_version: str
    spec_title: str

    # Validation categories (legacy string lists for compatibility)
    frontmatter_errors: List[str] = field(default_factory=list)
    frontmatter_warnings: List[str] = field(default_factory=list)

    anchor_errors: List[str] = field(default_factory=list)
    anchor_warnings: List[str] = field(default_factory=list)

    task_detail_errors: List[str] = field(default_factory=list)
    task_detail_warnings: List[str] = field(default_factory=list)

    structure_errors: List[str] = field(default_factory=list)
    structure_warnings: List[str] = field(default_factory=list)

    phase_errors: List[str] = field(default_factory=list)
    phase_warnings: List[str] = field(default_factory=list)

    # JSON spec validation (optional)
    json_spec_errors: List[str] = field(default_factory=list)
    json_spec_warnings: List[str] = field(default_factory=list)
    json_spec_data: Optional[Dict] = None

    # Enhanced error tracking
    enhanced_errors: List[EnhancedError] = field(default_factory=list)

    # Summary counts
    task_count: int = 0
    phase_count: int = 0
    verification_count: int = 0

    def count_all_issues(self) -> Tuple[int, int]:
        """Count total errors and warnings across all categories"""
        error_count = (
            len(self.frontmatter_errors) +
            len(self.anchor_errors) +
            len(self.task_detail_errors) +
            len(self.structure_errors) +
            len(self.phase_errors) +
            len(self.json_spec_errors)
        )
        warning_count = (
            len(self.frontmatter_warnings) +
            len(self.anchor_warnings) +
            len(self.task_detail_warnings) +
            len(self.structure_warnings) +
            len(self.phase_warnings) +
            len(self.json_spec_warnings)
        )
        return error_count, warning_count

    def is_valid(self) -> bool:
        """Check if spec passes all critical validations"""
        error_count, _ = self.count_all_issues()
        return error_count == 0

    def calculate_completion(self) -> Tuple[int, int, float]:
        """Calculate completion percentage from JSON spec"""
        if not self.json_spec_data:
            return 0, 0, 0.0

        root = self.json_spec_data.get('hierarchy', {}).get('spec-root', {})
        total = root.get('total_tasks', 0)
        completed = root.get('completed_tasks', 0)
        percentage = (completed / total * 100) if total > 0 else 0.0

        return completed, total, percentage


@dataclass
class JsonSpecValidationResult:
    """Results of JSON spec file validation"""
    spec_id: str
    generated: str
    last_updated: str

    # JSON schema validation (optional)
    schema_errors: List[str] = field(default_factory=list)
    schema_warnings: List[str] = field(default_factory=list)
    schema_source: Optional[str] = None

    # Validation categories (legacy string lists for compatibility)
    structure_errors: List[str] = field(default_factory=list)
    structure_warnings: List[str] = field(default_factory=list)

    hierarchy_errors: List[str] = field(default_factory=list)
    hierarchy_warnings: List[str] = field(default_factory=list)

    node_errors: List[str] = field(default_factory=list)
    node_warnings: List[str] = field(default_factory=list)

    count_errors: List[str] = field(default_factory=list)
    count_warnings: List[str] = field(default_factory=list)

    dependency_errors: List[str] = field(default_factory=list)
    dependency_warnings: List[str] = field(default_factory=list)

    metadata_errors: List[str] = field(default_factory=list)
    metadata_warnings: List[str] = field(default_factory=list)

    # Cross-validation with spec (optional)
    cross_val_errors: List[str] = field(default_factory=list)
    cross_val_warnings: List[str] = field(default_factory=list)

    # Enhanced error tracking
    enhanced_errors: List[EnhancedError] = field(default_factory=list)

    # Summary stats
    total_nodes: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0

    # Original spec data (optional, retained for follow-up analysis/fixes)
    spec_data: Optional[Dict[str, Any]] = None

    def count_all_issues(self) -> Tuple[int, int]:
        """Count total errors and warnings across all categories"""
        error_count = (
            len(self.schema_errors) +
            len(self.structure_errors) +
            len(self.hierarchy_errors) +
            len(self.node_errors) +
            len(self.count_errors) +
            len(self.dependency_errors) +
            len(self.metadata_errors) +
            len(self.cross_val_errors)
        )
        warning_count = (
            len(self.schema_warnings) +
            len(self.structure_warnings) +
            len(self.hierarchy_warnings) +
            len(self.node_warnings) +
            len(self.count_warnings) +
            len(self.dependency_warnings) +
            len(self.metadata_warnings) +
            len(self.cross_val_warnings)
        )
        return error_count, warning_count

    def is_valid(self) -> bool:
        """Check if JSON spec passes all critical validations"""
        error_count, _ = self.count_all_issues()
        return error_count == 0


def validate_status(status: str) -> bool:
    """Validate status field value"""
    valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
    return status in valid_statuses


def validate_node_type(node_type: str) -> bool:
    """Validate node type field value"""
    valid_types = ['spec', 'phase', 'group', 'task', 'subtask', 'verify']
    return node_type in valid_types


def validate_spec_id_format(spec_id: str) -> bool:
    """Validate spec_id follows recommended format: {feature}-{YYYY-MM-DD}-{nnn}"""
    import re
    return bool(re.match(r'^[\w-]+-\d{4}-\d{2}-\d{2}-\d{3}$', spec_id))


def validate_iso8601_date(date_str: str) -> bool:
    """Validate ISO 8601 date format"""
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$', str(date_str)))


_LEADING_MARKERS = ("❌", "⚠️", "ℹ️", "✅", "❓", "ℹ", "⚠")
_SEVERITY_PREFIX_RE = re.compile(r"^(CRITICAL|ERROR|WARNING|INFO|NOTE|TIP)\b[:\-]?\s*", re.IGNORECASE)


def normalize_message_text(raw: str) -> str:
    """Strip glyphs/severity prefixes from validation messages for consistent comparison."""

    text = (raw or "").strip()

    changed = True
    while changed and text:
        changed = False
        for marker in _LEADING_MARKERS:
            if text.startswith(marker):
                text = text[len(marker):].lstrip()
                changed = True
        if text.startswith(('- ', '* ')):
            text = text[2:].lstrip()
            changed = True

    match = _SEVERITY_PREFIX_RE.match(text)
    if match:
        text = text[match.end():].lstrip()

    if text.startswith((':', '-', '–')):
        text = text[1:].lstrip()

    return text.strip()
