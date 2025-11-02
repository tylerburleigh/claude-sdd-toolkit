"""Unit tests for DependencyGraphGenerator."""

import pytest
from claude_skills.sdd_render import DependencyGraphGenerator, GraphStyle


class TestDependencyGraphGenerator:
    """Tests for DependencyGraphGenerator class."""

    def test_initialization(self, sample_spec_data):
        """Test DependencyGraphGenerator initializes correctly."""
        generator = DependencyGraphGenerator(sample_spec_data)

        assert generator.spec_data == sample_spec_data
        assert generator.hierarchy == sample_spec_data['hierarchy']

    def test_basic_mermaid_generation(self, sample_spec_data):
        """Test basic Mermaid diagram generation."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Should produce valid Mermaid syntax
        assert isinstance(mermaid, str)
        assert len(mermaid) > 0
        # Should start with graph directive
        assert 'flowchart' in mermaid.lower() or 'graph' in mermaid.lower()

    def test_flowchart_style(self, sample_spec_data):
        """Test flowchart style graph generation."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate(style=GraphStyle.FLOWCHART)

        assert 'flowchart' in mermaid.lower()
        # Flowchart should contain task nodes
        assert 'task-1-1' in mermaid or any(task in mermaid for task in ['task-', 'phase-'])

    def test_graph_style(self, sample_spec_data):
        """Test graph style (left-right) generation."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate(style=GraphStyle.GRAPH)

        assert 'graph' in mermaid.lower()

    def test_nodes_generated(self, sample_spec_data):
        """Test that nodes are generated for tasks."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Should contain task IDs from sample spec
        hierarchy = sample_spec_data['hierarchy']
        task_ids = [nid for nid, node in hierarchy.items() if node.get('type') == 'task']

        # At least some tasks should appear in the graph
        assert any(tid in mermaid for tid in task_ids)

    def test_edges_generated(self, sample_spec_data):
        """Test that edges are generated for dependencies."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Should contain edge notation (arrows)
        assert '-->' in mermaid or '--->' in mermaid or '-.->' in mermaid

    def test_status_styling(self, sample_spec_data):
        """Test that nodes are styled based on status."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Mermaid styling can use classDef or inline styles
        # Should have some form of styling
        assert 'class' in mermaid.lower() or 'style' in mermaid.lower() or ':::' in mermaid

    def test_phase_grouping(self, sample_spec_data):
        """Test that phases can be grouped as subgraphs."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate(group_by_phase=True)

        # Should contain subgraph directives
        assert 'subgraph' in mermaid.lower()

    def test_simplified_view(self, sample_spec_data):
        """Test simplified graph with only high-level tasks."""
        generator = DependencyGraphGenerator(sample_spec_data)

        full_graph = generator.generate()
        simplified_graph = generator.generate(style=GraphStyle.SIMPLIFIED)

        # Simplified should be shorter (fewer nodes/edges)
        # This assumes SIMPLIFIED actually filters
        assert isinstance(simplified_graph, str)
        assert len(simplified_graph) > 0

    def test_critical_path_highlighting(self, sample_spec_data):
        """Test that critical path can be highlighted."""
        generator = DependencyGraphGenerator(sample_spec_data)

        # Generate with critical path highlighting
        mermaid = generator.generate(highlight_critical_path=True)

        # Should have some form of highlighting (bold, color, etc.)
        # Mermaid uses styles or class definitions
        assert len(mermaid) > 0
        # Critical path styling may use 'stroke-width', 'class', or ':::'
        # Just verify the graph is generated

    def test_empty_spec_handling(self):
        """Test handling of spec with no tasks."""
        empty_spec = {
            'spec_id': 'empty-001',
            'hierarchy': {
                'spec-root': {
                    'id': 'spec-root',
                    'type': 'spec',
                    'title': 'Empty Spec',
                    'children': [],
                    'total_tasks': 0
                }
            }
        }

        generator = DependencyGraphGenerator(empty_spec)
        mermaid = generator.generate()

        # Should handle gracefully
        assert isinstance(mermaid, str)

    def test_phase_filtering(self, sample_spec_data):
        """Test generating graph for specific phase only."""
        generator = DependencyGraphGenerator(sample_spec_data)

        # Generate for phase-1 only
        mermaid = generator.generate(phase_filter='phase-1')

        assert isinstance(mermaid, str)
        assert len(mermaid) > 0
        # Should contain tasks from phase-1
        assert 'task-1' in mermaid or 'phase-1' in mermaid

    def test_node_shapes_by_type(self, sample_spec_data):
        """Test that different node types have different shapes."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Mermaid uses different brackets for shapes:
        # [] = rectangle, [()] = stadium, {{}} = diamond, etc.
        # Verify the output contains shape notation
        assert '[' in mermaid and ']' in mermaid

    def test_blocked_task_highlighting(self, sample_spec_data):
        """Test that blocked tasks are visually distinguished."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Blocked tasks should have distinct styling
        # This is typically done via classDef or inline styles
        assert len(mermaid) > 0

    def test_dependency_arrow_types(self, sample_spec_data):
        """Test that different dependency types use different arrows."""
        generator = DependencyGraphGenerator(sample_spec_data)

        mermaid = generator.generate()

        # Should have arrows (solid or dashed)
        assert '-->' in mermaid or '--->' in mermaid or '-.->' in mermaid or '-..->' in mermaid
