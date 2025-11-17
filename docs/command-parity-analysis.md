# Command Parity Analysis: Text vs JSON Output

## Overview

This document analyzes field parity between text and JSON output modes across multiple SDD commands.

## list-phases Command

### JSON Mode Fields (6 fields)

```json
{
  "id": "phase-1",
  "title": "Investigation & Analysis",
  "status": "in_progress",
  "completed_tasks": 3,
  "total_tasks": 10,
  "percentage": 30
}
```

**Fields:**
1. **id** - Phase identifier
2. **title** - Phase name/description
3. **status** - Current status (in_progress, pending, completed, blocked)
4. **completed_tasks** - Number of completed tasks
5. **total_tasks** - Total number of tasks in phase
6. **percentage** - Completion percentage (0-100)

**Implementation Reference:** `/src/claude_skills/claude_skills/common/progress.py:228-257`

### Text Mode Display (5 columns)

The text mode displays a formatted table with these columns:

1. **Phase** - Combined display of phase ID and title (two lines)
   - Line 1: `phase-1`
   - Line 2: `Investigation & Analysis`
2. **Status** - Status with emoji
   - 🔄 In Progress
   - ⏳ Pending
   - ✅ Completed
   - 🚫 Blocked
3. **Tasks** - Task count (completed/total format)
   - Example: `3/10`
4. **Progress** - Visual progress bar + percentage
   - Example: `███░░░░░░░ 30%`
5. **Dependencies** - Dependency indicators (emoji arrows)
   - ➡️ Has dependents
   - ⬅️ Has dependencies

**Implementation Reference:** `/src/claude_skills/claude_skills/common/query_operations.py:215-262` (calls progress.py)

### Field Mapping

| JSON Field | Text Column | Notes |
|------------|-------------|-------|
| id + title | Phase | Combined into two-line display |
| status | Status | Text adds emoji decoration |
| completed_tasks + total_tasks | Tasks | Combined as "X/Y" format |
| percentage | Progress | Includes visual bar + percentage |
| - | Dependencies | Text-only (not in JSON output) |

### Key Differences

1. **Field Count**: JSON has 6 discrete fields, text displays 5 columns
2. **Aggregation**: Text combines `id` + `title` and `completed_tasks` + `total_tasks`
3. **Visual Enhancement**: Text mode adds progress bars and emojis
4. **Exclusive Fields**: Text mode includes dependency indicators not present in JSON
5. **Parity**: High parity - all JSON fields are represented in text display

## list-specs Command

(See `/docs/list-specs-field-analysis.md` for detailed analysis)

### Summary

- **JSON mode**: 10 fields
- **Text mode**: 6 display columns
- **Parity**: Moderate - some JSON fields (version, created_at) not shown in text

## Comparison Summary

| Command | JSON Fields | Text Columns | Parity Level | Notes |
|---------|-------------|--------------|--------------|-------|
| list-phases | 6 | 5 | High | All JSON data visible in text, plus dependency indicators |
| list-specs | 10 | 6 | Moderate | version and created_at missing from text display |

### Parity Patterns

**High Parity (list-phases):**
- All JSON fields have text representation
- Text mode adds visual enhancements without losing data
- Field aggregation (combining id+title, counts) improves readability

**Moderate Parity (list-specs):**
- Some JSON fields omitted from text (version: 88.6% null, created_at: 100% null)
- Omissions are fields with high null rates
- Core information (id, title, progress, status) fully represented

## Recommendations

1. **list-phases**: Excellent parity - no changes needed
2. **list-specs**: Consider if rarely-used fields (version, created_at) should be in verbose/detailed mode
3. **General pattern**: Text mode should prioritize frequently-populated, high-value fields
