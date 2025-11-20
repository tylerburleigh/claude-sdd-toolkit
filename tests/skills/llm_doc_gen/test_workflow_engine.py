"""
Tests for workflow_engine module.

Basic functionality tests for WorkflowEngine and DocumentationWorkflow classes.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from claude_skills.llm_doc_gen.workflow_engine import (
    DocumentationWorkflow,
    ExecutionMode,
    StepStatus,
    WorkflowEngine,
    WorkflowState,
    WorkflowStep,
    WorkflowVariable,
)


class TestWorkflowVariable:
    """Tests for WorkflowVariable dataclass."""

    def test_create_variable(self):
        """Test creating a workflow variable."""
        var = WorkflowVariable(name="test_var", value="test_value", source="user")
        assert var.name == "test_var"
        assert var.value == "test_value"
        assert var.source == "user"
        assert var.resolved is False

    def test_variable_defaults(self):
        """Test variable default values."""
        var = WorkflowVariable(name="test")
        assert var.value is None
        assert var.source == "unknown"
        assert var.resolved is False


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_create_step(self):
        """Test creating a workflow step."""
        step = WorkflowStep(number=1, title="Test Step")
        assert step.number == 1
        assert step.title == "Test Step"
        assert step.status == StepStatus.PENDING
        assert step.optional is False
        assert step.actions == []
        assert step.substeps == []

    def test_step_with_substeps(self):
        """Test step with substeps."""
        substep = WorkflowStep(number="1a", title="Substep")
        step = WorkflowStep(number=1, title="Main Step", substeps=[substep])
        assert len(step.substeps) == 1
        assert step.substeps[0].number == "1a"


class TestWorkflowState:
    """Tests for WorkflowState class."""

    def test_create_state(self):
        """Test creating workflow state."""
        state = WorkflowState(workflow_id="test-workflow")
        assert state.workflow_id == "test-workflow"
        assert state.current_step is None
        assert state.completed_steps == []
        assert state.variables == {}
        assert state.mode == ExecutionMode.NORMAL

    def test_state_serialization(self):
        """Test state to_dict and from_dict."""
        state = WorkflowState(
            workflow_id="test",
            current_step="step-1",
            completed_steps=["step-0"],
            variables={"var1": "value1"},
            mode=ExecutionMode.YOLO,
        )

        # Serialize
        data = state.to_dict()
        assert data["workflow_id"] == "test"
        assert data["current_step"] == "step-1"
        assert data["completed_steps"] == ["step-0"]
        assert data["variables"] == {"var1": "value1"}
        assert data["mode"] == "yolo"

        # Deserialize
        restored = WorkflowState.from_dict(data)
        assert restored.workflow_id == state.workflow_id
        assert restored.current_step == state.current_step
        assert restored.completed_steps == state.completed_steps
        assert restored.variables == state.variables
        assert restored.mode == state.mode


class TestWorkflowEngine:
    """Tests for WorkflowEngine class."""

    @pytest.fixture
    def simple_config(self):
        """Simple workflow configuration for testing."""
        return {
            "id": "test-workflow",
            "instructions": [
                {"number": 1, "title": "Step 1", "actions": ["Action 1"]},
                {"number": 2, "title": "Step 2", "actions": ["Action 2"]},
            ],
        }

    @pytest.fixture
    def temp_state_file(self):
        """Temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)
        yield path
        if path.exists():
            path.unlink()

    def test_engine_initialization(self, simple_config):
        """Test workflow engine initialization."""
        engine = WorkflowEngine(workflow_config=simple_config)
        assert engine.config == simple_config
        assert engine.state.workflow_id == "test-workflow"
        assert engine.state.mode == ExecutionMode.NORMAL

    def test_system_variable_resolution(self, simple_config):
        """Test system variable resolution."""
        engine = WorkflowEngine(workflow_config=simple_config)
        engine._resolve_system_variables()

        assert "date" in engine.variables
        assert "project-root" in engine.variables
        assert engine.variables["date"].resolved is True
        assert engine.variables["project-root"].resolved is True

        # Verify date format
        date_value = engine.variables["date"].value
        assert len(date_value) == 10  # YYYY-MM-DD format
        assert date_value.count("-") == 2

    def test_path_resolution(self, simple_config):
        """Test path resolution with variables."""
        engine = WorkflowEngine(workflow_config=simple_config)
        engine.variables["test_dir"] = WorkflowVariable(
            name="test_dir", value="/tmp/test", resolved=True
        )

        path = engine._resolve_path("{test_dir}/file.txt")
        assert path == Path("/tmp/test/file.txt")

    def test_condition_evaluation_file_exists(self, simple_config, tmp_path):
        """Test conditional evaluation for file existence."""
        engine = WorkflowEngine(workflow_config=simple_config)

        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Test file exists condition
        result = engine.evaluate_condition(f"file exists '{test_file}'")
        assert result is True

        # Test file not exists
        result = engine.evaluate_condition(f"file exists '/nonexistent/file.txt'")
        assert result is False

    def test_condition_evaluation_else(self, simple_config):
        """Test else condition always returns True."""
        engine = WorkflowEngine(workflow_config=simple_config)
        assert engine.evaluate_condition("else") is True

    def test_condition_evaluation_variable_equality(self, simple_config):
        """Test variable equality conditions."""
        engine = WorkflowEngine(workflow_config=simple_config)
        engine.variables["status"] = WorkflowVariable(
            name="status", value="ready", resolved=True
        )

        assert engine.evaluate_condition("status == ready") is True
        assert engine.evaluate_condition("status == pending") is False

    def test_state_persistence(self, simple_config, temp_state_file):
        """Test state file save and load."""
        # Create engine with state file
        engine = WorkflowEngine(
            workflow_config=simple_config, state_file=temp_state_file
        )
        engine.state.current_step = "step-1"
        engine.state.completed_steps = ["step-0"]
        engine._save_state()

        # Verify file was created
        assert temp_state_file.exists()

        # Load state in new engine
        engine2 = WorkflowEngine(
            workflow_config=simple_config, state_file=temp_state_file
        )
        assert engine2.state.current_step == "step-1"
        assert engine2.state.completed_steps == ["step-0"]

    def test_load_instructions(self, simple_config):
        """Test loading instructions into step list."""
        engine = WorkflowEngine(workflow_config=simple_config)
        engine._load_instructions()

        assert len(engine.steps) == 2
        assert engine.steps[0].number == 1
        assert engine.steps[0].title == "Step 1"
        assert engine.steps[1].number == 2
        assert engine.steps[1].title == "Step 2"

    def test_protocol_registration(self, simple_config):
        """Test registering and retrieving protocols."""
        engine = WorkflowEngine(workflow_config=simple_config)

        called = []

        def test_protocol():
            called.append(True)

        engine.register_protocol("test_protocol", test_protocol)
        assert "test_protocol" in engine.protocols

        # Invoke protocol
        engine.protocols["test_protocol"]()
        assert len(called) == 1


class TestDocumentationWorkflow:
    """Tests for DocumentationWorkflow class."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "src" / "main.py").write_text("print('hello')")
        return project_dir

    @pytest.fixture
    def temp_output(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "docs"
        output_dir.mkdir()
        return output_dir

    def test_documentation_workflow_initialization(self, temp_project, temp_output):
        """Test DocumentationWorkflow initialization."""
        workflow = DocumentationWorkflow(
            project_root=temp_project, output_dir=temp_output
        )
        assert workflow.project_root == temp_project
        assert workflow.output_dir == temp_output
        assert workflow.state_file == temp_output / "workflow-state.json"
        assert workflow.engine is None

    def test_load_workflow_config(self, temp_project, temp_output):
        """Test loading workflow configuration."""
        workflow = DocumentationWorkflow(
            project_root=temp_project, output_dir=temp_output
        )

        config = {
            "id": "doc-gen",
            "instructions": [
                {"number": 1, "title": "Initialize", "actions": ["Scan project"]},
            ],
        }

        workflow.load_workflow(config)
        assert workflow.engine is not None
        assert workflow.engine.config == config

    def test_protocol_registration(self, temp_project, temp_output):
        """Test that documentation-specific protocols are registered."""
        workflow = DocumentationWorkflow(
            project_root=temp_project, output_dir=temp_output
        )

        config = {"id": "test", "instructions": []}
        workflow.load_workflow(config)

        assert "discover_inputs" in workflow.engine.protocols
        assert "advanced_elicitation" in workflow.engine.protocols


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_execution_modes(self):
        """Test execution mode enum values."""
        assert ExecutionMode.NORMAL.value == "normal"
        assert ExecutionMode.YOLO.value == "yolo"


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_step_statuses(self):
        """Test step status enum values."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.SKIPPED.value == "skipped"
        assert StepStatus.FAILED.value == "failed"
