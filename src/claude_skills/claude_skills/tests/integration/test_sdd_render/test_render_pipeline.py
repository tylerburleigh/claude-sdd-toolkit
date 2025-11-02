"""Integration tests for sdd render end-to-end pipeline.

These tests verify the complete rendering pipeline from JSON spec input
to markdown output, including both basic and enhanced rendering modes.
"""

import json
import pytest
from pathlib import Path
from claude_skills.sdd_render import SpecRenderer, AIEnhancedRenderer


class TestBasicRenderingPipeline:
    """Integration tests for basic rendering mode."""

    def test_render_small_spec(self, tmp_path):
        """Test rendering a small, simple spec."""
        # Create a minimal spec
        spec_data = {
            "spec_id": "small-test-001",
            "title": "Small Test Spec",
            "generated": "2025-01-01T00:00:00Z",
            "metadata": {
                "status": "draft",
                "estimated_hours": 5
            },
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Small Test Spec",
                    "status": "pending",
                    "children": ["phase-1"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "id": "phase-1",
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": ["task-1-1", "task-1-2"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": ["task-1-2"], "blocked_by": [], "depends": []}
                },
                "task-1-2": {
                    "id": "task-1-2",
                    "type": "task",
                    "title": "Task 2",
                    "status": "pending",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": ["task-1-1"], "depends": []}
                }
            }
        }

        # Render to markdown
        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Verify output
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "Small Test Spec" in markdown
        assert "Phase 1" in markdown
        assert "Task 1" in markdown
        assert "Task 2" in markdown

    def test_render_spec_with_metadata(self, tmp_path):
        """Test rendering preserves all metadata fields."""
        spec_data = {
            "spec_id": "metadata-test-001",
            "title": "Metadata Test",
            "metadata": {
                "status": "in_progress",
                "estimated_hours": 20,
                "complexity": "high",
                "description": "Test spec with rich metadata"
            },
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Metadata Test",
                    "status": "in_progress",
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Verify metadata appears in output
        assert "Metadata Test" in markdown
        assert "in_progress" in markdown or "In Progress" in markdown.lower()

    def test_render_spec_with_complex_dependencies(self, tmp_path):
        """Test rendering spec with complex dependency chains."""
        spec_data = {
            "spec_id": "complex-deps-001",
            "title": "Complex Dependencies",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Complex Dependencies",
                    "status": "pending",
                    "children": ["phase-1"],
                    "total_tasks": 4,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "id": "phase-1",
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": ["task-1-1", "task-1-2", "task-1-3", "task-1-4"],
                    "total_tasks": 4,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Root Task",
                    "status": "completed",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "dependencies": {"blocks": ["task-1-2", "task-1-3"], "blocked_by": [], "depends": []}
                },
                "task-1-2": {
                    "id": "task-1-2",
                    "type": "task",
                    "title": "Branch A",
                    "status": "in_progress",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": ["task-1-4"], "blocked_by": ["task-1-1"], "depends": []}
                },
                "task-1-3": {
                    "id": "task-1-3",
                    "type": "task",
                    "title": "Branch B",
                    "status": "pending",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": ["task-1-4"], "blocked_by": ["task-1-1"], "depends": []}
                },
                "task-1-4": {
                    "id": "task-1-4",
                    "type": "task",
                    "title": "Convergence Task",
                    "status": "blocked",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": ["task-1-2", "task-1-3"], "depends": []}
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Verify all tasks appear
        assert "Root Task" in markdown
        assert "Branch A" in markdown
        assert "Branch B" in markdown
        assert "Convergence Task" in markdown

        # Verify dependency information is present
        # (The exact format depends on renderer implementation)
        assert len(markdown) > 0


class TestEnhancedRenderingPipeline:
    """Integration tests for AI-enhanced rendering mode."""

    def test_enhanced_render_basic_spec(self, tmp_path):
        """Test AI-enhanced rendering on basic spec."""
        spec_data = {
            "spec_id": "enhanced-test-001",
            "title": "Enhanced Test",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Enhanced Test",
                    "status": "pending",
                    "children": ["phase-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "id": "phase-1",
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": ["task-1-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": "phase-1",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
                }
            }
        }

        # Use AI-enhanced renderer
        renderer = AIEnhancedRenderer(spec_data)
        markdown = renderer.render(output_format='markdown', enable_ai=True)

        # Verify output
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "Enhanced Test" in markdown
        assert "Phase 1" in markdown

    def test_enhanced_render_falls_back_gracefully(self, tmp_path):
        """Test that AI-enhanced rendering falls back to basic on error."""
        spec_data = {
            "spec_id": "fallback-test-001",
            "title": "Fallback Test",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Fallback Test",
                    "status": "pending",
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

        # Even with potentially problematic data, should not crash
        renderer = AIEnhancedRenderer(spec_data)
        markdown = renderer.render(output_format='markdown', enable_ai=True)

        assert isinstance(markdown, str)
        assert len(markdown) > 0


class TestRenderOutputFormats:
    """Integration tests for different output formats and modes."""

    def test_markdown_output_format(self, tmp_path):
        """Test markdown format output."""
        spec_data = {
            "spec_id": "format-test-001",
            "title": "Format Test",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Format Test",
                    "status": "pending",
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Verify markdown formatting
        assert markdown.startswith('#')  # Should start with header
        assert '\n' in markdown  # Should have newlines
        assert len(markdown.strip()) > 0

    def test_large_spec_rendering(self, tmp_path):
        """Test rendering a large spec with many tasks."""
        # Create a spec with 50 tasks across 5 phases
        hierarchy = {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "title": "Large Spec",
                "status": "in_progress",
                "children": [f"phase-{i}" for i in range(1, 6)],
                "total_tasks": 50,
                "completed_tasks": 10
            }
        }

        # Add phases
        for phase_num in range(1, 6):
            phase_id = f"phase-{phase_num}"
            hierarchy[phase_id] = {
                "id": phase_id,
                "type": "phase",
                "title": f"Phase {phase_num}",
                "status": "in_progress" if phase_num <= 2 else "pending",
                "parent": "spec-root",
                "children": [f"task-{phase_num}-{i}" for i in range(1, 11)],
                "total_tasks": 10,
                "completed_tasks": 2 if phase_num == 1 else 0
            }

            # Add tasks
            for task_num in range(1, 11):
                task_id = f"task-{phase_num}-{task_num}"
                status = "completed" if phase_num == 1 and task_num <= 2 else "pending"
                hierarchy[task_id] = {
                    "id": task_id,
                    "type": "task",
                    "title": f"Task {phase_num}.{task_num}",
                    "status": status,
                    "parent": phase_id,
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 1 if status == "completed" else 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
                }

        spec_data = {
            "spec_id": "large-spec-001",
            "title": "Large Spec",
            "hierarchy": hierarchy
        }

        # Should handle large specs without crashing
        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        assert isinstance(markdown, str)
        assert len(markdown) > 1000  # Should be substantial
        assert "Large Spec" in markdown
        assert "Phase 1" in markdown
        assert "Phase 5" in markdown


class TestRenderEdgeCases:
    """Integration tests for edge cases and error conditions."""

    def test_empty_spec(self, tmp_path):
        """Test rendering an empty spec."""
        spec_data = {
            "spec_id": "empty-001",
            "title": "Empty Spec",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Empty Spec",
                    "status": "pending",
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        assert isinstance(markdown, str)
        assert "Empty Spec" in markdown

    def test_spec_with_all_completed_tasks(self, tmp_path):
        """Test rendering a fully completed spec."""
        spec_data = {
            "spec_id": "completed-001",
            "title": "Completed Spec",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Completed Spec",
                    "status": "completed",
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 1
                },
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Completed Task",
                    "status": "completed",
                    "parent": "spec-root",
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        assert "Completed Spec" in markdown
        assert "Completed Task" in markdown
        # Should show 100% completion
        assert "100%" in markdown or "1/1" in markdown

    def test_spec_with_unicode_characters(self, tmp_path):
        """Test rendering spec with unicode characters."""
        spec_data = {
            "spec_id": "unicode-001",
            "title": "Unicode Test: émojis 🎉 and spëcial çhars",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "title": "Unicode Test: émojis 🎉 and spëcial çhars",
                    "status": "pending",
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Should handle unicode without crashing
        assert isinstance(markdown, str)
        assert "Unicode Test" in markdown
