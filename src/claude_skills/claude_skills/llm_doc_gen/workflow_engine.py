"""
Workflow orchestration engine for LLM-based documentation generation.

This module implements a flexible workflow execution system, enabling:
- Step-by-step execution with state management
- Conditional execution patterns (if/check/action)
- Template-output checkpoints with user interaction
- Protocol invocation and workflow composition
- Resumability through state persistence

The engine supports XML-based and YAML-based workflow definitions with
advanced features like variable resolution, conditional branching, and
iterative step execution.

Design inspired by the BMAD (Building Multi-Agent Documentation) methodology
(https://github.com/bmad-code-org/BMAD-METHOD) under MIT License.
BMAD™ and BMAD-METHOD™ are trademarks of BMad Code, LLC.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class ExecutionMode(Enum):
    """Workflow execution modes."""
    NORMAL = "normal"  # Full user interaction at all decision points
    YOLO = "yolo"  # Skip confirmations, minimize prompts, auto-proceed


class StepStatus(Enum):
    """Step execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowVariable:
    """Represents a workflow variable with value and metadata."""
    name: str
    value: Optional[Any] = None
    source: str = "unknown"  # config_source, system, user, computed
    resolved: bool = False


@dataclass
class WorkflowStep:
    """Represents a single workflow step."""
    number: Union[int, str]  # Can be "1" or "1a"
    title: str
    actions: List[str] = field(default_factory=list)
    optional: bool = False
    condition: Optional[str] = None  # if="condition"
    for_each: Optional[str] = None  # for-each="collection"
    repeat: Optional[int] = None  # repeat="n"
    status: StepStatus = StepStatus.PENDING
    substeps: List["WorkflowStep"] = field(default_factory=list)


@dataclass
class WorkflowState:
    """Maintains workflow execution state for resumability."""
    workflow_id: str
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.NORMAL
    timestamp: Optional[str] = None
    output_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "variables": self.variables,
            "mode": self.mode.value,
            "timestamp": self.timestamp,
            "output_files": self.output_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Deserialize state from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []),
            variables=data.get("variables", {}),
            mode=ExecutionMode(data.get("mode", "normal")),
            timestamp=data.get("timestamp"),
            output_files=data.get("output_files", []),
        )


class WorkflowEngine:
    """
    Core workflow orchestration engine.

    Executes workflows step-by-step with state management, conditional logic,
    and user interaction checkpoints.
    """

    def __init__(
        self,
        workflow_config: Dict[str, Any],
        state_file: Optional[Path] = None,
        user_interaction_handler: Optional[Callable] = None,
    ):
        """
        Initialize workflow engine.

        Args:
            workflow_config: Workflow configuration (parsed YAML/XML)
            state_file: Optional state file for resumability
            user_interaction_handler: Optional callback for user prompts
        """
        self.config = workflow_config
        self.state_file = state_file
        self.user_handler = user_interaction_handler or self._default_user_handler

        # Initialize workflow state
        workflow_id = workflow_config.get("id", "unknown")
        self.state = self._load_or_create_state(workflow_id)

        # Variable registry
        self.variables: Dict[str, WorkflowVariable] = {}

        # Steps registry
        self.steps: List[WorkflowStep] = []

        # Protocols registry (reusable sub-workflows)
        self.protocols: Dict[str, Callable] = {}

    def _load_or_create_state(self, workflow_id: str) -> WorkflowState:
        """Load existing state or create new state."""
        if self.state_file and self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        return WorkflowState.from_dict(data)
            except (json.JSONDecodeError, ValueError):
                # File is empty or invalid JSON, create new state
                pass
        return WorkflowState(workflow_id=workflow_id)

    def _save_state(self):
        """Persist workflow state to file."""
        if self.state_file:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2)

    def _default_user_handler(self, prompt: str, options: Optional[List[str]] = None) -> str:
        """Default user interaction handler (console input)."""
        print(f"\n{prompt}")
        if options:
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
        return input("> ").strip()

    def resolve_variables(self):
        """
        Resolve all workflow variables.

        Variable resolution order:
        1. Load external config from config_source
        2. Resolve {config_source:key} references
        3. Resolve system variables ({date}, {project-root})
        4. Ask user for undefined variables
        """
        # Step 1: Load config_source if specified
        config_source = self.config.get("config_source")
        if config_source:
            config_path = self._resolve_path(config_source)
            if config_path and config_path.exists():
                with open(config_path, "r") as f:
                    external_config = json.load(f)
                    for key, value in external_config.items():
                        self.variables[key] = WorkflowVariable(
                            name=key, value=value, source="config_source", resolved=True
                        )

        # Step 2: Resolve {config_source:key} references
        for key, var in self.variables.items():
            if isinstance(var.value, str) and "{config_source:" in var.value:
                var.value = self._resolve_config_refs(var.value)
                var.resolved = True

        # Step 3: Resolve system variables
        self._resolve_system_variables()

        # Step 4: Identify and prompt for undefined variables
        undefined = [v for v in self.variables.values() if not v.resolved]
        for var in undefined:
            response = self.user_handler(
                f"Variable '{var.name}' is undefined. Please provide a value:",
                None
            )
            var.value = response
            var.source = "user"
            var.resolved = True

    def _resolve_config_refs(self, text: str) -> str:
        """Resolve {config_source:key} references."""
        pattern = r"\{config_source:(\w+)\}"

        def replacer(match):
            key = match.group(1)
            if key in self.variables and self.variables[key].resolved:
                return str(self.variables[key].value)
            return match.group(0)  # Leave unresolved

        return re.sub(pattern, replacer, text)

    def _resolve_system_variables(self):
        """Resolve system-generated variables like {date}, {project-root}."""
        from datetime import datetime

        # {date} - current date
        if "date" not in self.variables:
            self.variables["date"] = WorkflowVariable(
                name="date",
                value=datetime.now().strftime("%Y-%m-%d"),
                source="system",
                resolved=True,
            )

        # {project-root} - current working directory
        if "project-root" not in self.variables:
            self.variables["project-root"] = WorkflowVariable(
                name="project-root",
                value=str(Path.cwd()),
                source="system",
                resolved=True,
            )

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """Resolve path with variable substitution."""
        # Replace {variable} with values
        for var_name, var in self.variables.items():
            if var.resolved:
                path_str = path_str.replace(f"{{{var_name}}}", str(var.value))

        return Path(path_str) if path_str else None

    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate conditional expression.

        Supports:
        - "file exists" / "file not exists"
        - "variable == value"
        - "else" (always true, for alternative branches)
        """
        if condition == "else":
            return True

        # File existence checks
        if "file exists" in condition:
            # Extract path from condition
            path_match = re.search(r"['\"](.*?)['\"]", condition)
            if path_match:
                file_path = self._resolve_path(path_match.group(1))
                exists = file_path and file_path.exists()
                return exists if "not exists" not in condition else not exists

        # Variable equality checks
        if "==" in condition:
            var_name, expected = condition.split("==", 1)
            var_name = var_name.strip()
            expected = expected.strip().strip("'\"")

            if var_name in self.variables:
                actual = str(self.variables[var_name].value)
                return actual == expected

        # Default: condition string is a variable name - check if truthy
        if condition in self.variables:
            return bool(self.variables[condition].value)

        return False

    def execute_step(self, step: WorkflowStep) -> bool:
        """
        Execute a workflow step.

        Returns:
            True if step completed successfully, False if skipped/failed
        """
        # Check if step should be skipped
        if step.condition and not self.evaluate_condition(step.condition):
            step.status = StepStatus.SKIPPED
            return False

        # Check if optional and user wants to skip (unless YOLO mode)
        if step.optional and self.state.mode == ExecutionMode.NORMAL:
            response = self.user_handler(
                f"Step {step.number}: {step.title} is optional. Include it?",
                ["Yes", "No"]
            )
            if response.lower().startswith("n"):
                step.status = StepStatus.SKIPPED
                return False

        step.status = StepStatus.IN_PROGRESS

        # Handle repeat
        iterations = step.repeat or 1

        # Handle for-each
        if step.for_each:
            collection = self.variables.get(step.for_each)
            if collection and isinstance(collection.value, list):
                iterations = len(collection.value)

        # Execute step iterations
        for i in range(iterations):
            # Execute actions
            for action in step.actions:
                self._execute_action(action)

            # Execute substeps
            for substep in step.substeps:
                self.execute_step(substep)

        step.status = StepStatus.COMPLETED
        self.state.completed_steps.append(str(step.number))
        self._save_state()

        return True

    def _execute_action(self, action: str):
        """Execute a single action."""
        # Parse action tags
        if action.startswith("<invoke-protocol"):
            self._invoke_protocol(action)
        elif action.startswith("<invoke-workflow"):
            self._invoke_workflow(action)
        elif action.startswith("<ask"):
            self._handle_ask(action)
        elif action.startswith("<template-output"):
            self._handle_template_output(action)
        else:
            # Default: action is a description to execute
            # In actual implementation, this would dispatch to appropriate handler
            print(f"  Action: {action}")

    def _invoke_protocol(self, action: str):
        """Invoke a reusable protocol."""
        # Extract protocol name
        match = re.search(r'name="([^"]+)"', action)
        if match:
            protocol_name = match.group(1)
            if protocol_name in self.protocols:
                self.protocols[protocol_name]()
            else:
                print(f"Warning: Protocol '{protocol_name}' not found")

    def _invoke_workflow(self, action: str):
        """Invoke another workflow."""
        # Extract workflow path
        match = re.search(r'path="([^"]+)"', action)
        if match:
            workflow_path = self._resolve_path(match.group(1))
            if workflow_path and workflow_path.exists():
                # Load and execute sub-workflow
                # In actual implementation, this would create a new WorkflowEngine
                print(f"  Invoking sub-workflow: {workflow_path}")

    def _handle_ask(self, action: str):
        """Handle user prompt."""
        # Extract prompt text
        prompt_match = re.search(r"<ask>(.*?)</ask>", action, re.DOTALL)
        if prompt_match:
            prompt = prompt_match.group(1).strip()
            response = self.user_handler(prompt)

            # Store response in variables if needed
            # Check for response handlers: <if response="a">...</if>
            self._handle_response_branches(action, response)

    def _handle_response_branches(self, action: str, response: str):
        """Handle conditional response branches."""
        # Find all <if response="X"> blocks
        pattern = r'<if\s+response="([^"]+)">(.*?)</if>'
        for match in re.finditer(pattern, action, re.DOTALL):
            expected_response = match.group(1)
            branch_actions = match.group(2).strip()

            if response.lower() == expected_response.lower():
                # Execute branch actions
                for line in branch_actions.split("\n"):
                    line = line.strip()
                    if line.startswith("<action"):
                        self._execute_action(line)

    def _handle_template_output(self, action: str):
        """Handle template output checkpoint."""
        # In NORMAL mode, show content and wait for approval
        if self.state.mode == ExecutionMode.NORMAL:
            print("\n" + "=" * 40)
            print("CHECKPOINT - Review generated content")
            print("=" * 40)

            response = self.user_handler(
                "Options: [a] Advanced Elicitation, [c] Continue, [p] Party-Mode, [y] YOLO",
                ["a", "c", "p", "y"]
            )

            if response.lower() == "y":
                self.state.mode = ExecutionMode.YOLO
            elif response.lower() == "a":
                # Invoke advanced elicitation
                self._invoke_protocol("<invoke-protocol name='advanced_elicitation' />")
            # Continue on 'c' or 'p'

    def register_protocol(self, name: str, handler: Callable):
        """Register a reusable protocol handler."""
        self.protocols[name] = handler

    def execute(self) -> bool:
        """
        Execute the complete workflow.

        Returns:
            True if workflow completed successfully
        """
        # Step 1: Initialize and resolve variables
        self.resolve_variables()

        # Step 2: Load instructions and build step list
        self._load_instructions()

        # Step 3: Execute steps in order
        for step in self.steps:
            # Check if step already completed (resumability)
            if str(step.number) in self.state.completed_steps:
                continue

            # Update current step
            self.state.current_step = str(step.number)
            self._save_state()

            # Execute step
            success = self.execute_step(step)
            if not success and not step.optional:
                # Required step failed
                return False

        # Step 4: Completion
        self.state.current_step = "completed"
        self._save_state()
        return True

    def _load_instructions(self):
        """Load workflow instructions and build step list."""
        # Parse instructions from config
        instructions = self.config.get("instructions", [])

        for i, instruction in enumerate(instructions, 1):
            step = WorkflowStep(
                number=instruction.get("number", i),
                title=instruction.get("title", f"Step {i}"),
                actions=instruction.get("actions", []),
                optional=instruction.get("optional", False),
                condition=instruction.get("if"),
                for_each=instruction.get("for-each"),
                repeat=instruction.get("repeat"),
            )
            self.steps.append(step)


class DocumentationWorkflow:
    """
    Specialized workflow engine for documentation generation.

    Extends WorkflowEngine with documentation-specific protocols and handlers.
    """

    def __init__(
        self,
        project_root: Path,
        output_dir: Path,
        state_file: Optional[Path] = None,
    ):
        """
        Initialize documentation workflow.

        Args:
            project_root: Root directory of project to document
            output_dir: Output directory for generated docs
            state_file: State file for resumability
        """
        self.project_root = project_root
        self.output_dir = output_dir
        self.state_file = state_file or (output_dir / "workflow-state.json")

        # Will be initialized when workflow config is loaded
        self.engine: Optional[WorkflowEngine] = None

    def load_workflow(self, workflow_config: Dict[str, Any]):
        """Load workflow configuration and initialize engine."""
        self.engine = WorkflowEngine(
            workflow_config=workflow_config,
            state_file=self.state_file,
            user_interaction_handler=self._user_handler,
        )

        # Register documentation-specific protocols
        self.engine.register_protocol("discover_inputs", self._discover_inputs_protocol)
        self.engine.register_protocol("advanced_elicitation", self._advanced_elicitation_protocol)

    def _user_handler(self, prompt: str, options: Optional[List[str]] = None) -> str:
        """User interaction handler for documentation workflow."""
        # In actual implementation, this would integrate with Claude Code's
        # AskUserQuestion tool for structured interaction
        print(f"\n{prompt}")
        if options:
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
        return input("> ").strip()

    def _discover_inputs_protocol(self):
        """
        Discover and load project input files.

        Smart loading strategies:
        - FULL_LOAD: Load all files in sharded directory
        - SELECTIVE_LOAD: Load specific shard using template variable
        - INDEX_GUIDED: Analyze index.md and load relevant docs
        """
        print("🔍 Discovering input files...")

        patterns = self.engine.config.get("input_file_patterns", {})

        for pattern_name, pattern_config in patterns.items():
            strategy = pattern_config.get("load_strategy", "FULL_LOAD")

            if strategy == "FULL_LOAD":
                self._load_all_matching(pattern_name, pattern_config)
            elif strategy == "SELECTIVE_LOAD":
                self._load_selective(pattern_name, pattern_config)
            elif strategy == "INDEX_GUIDED":
                self._load_index_guided(pattern_name, pattern_config)

    def _load_all_matching(self, name: str, config: Dict[str, Any]):
        """Load all files matching pattern."""
        pattern = config.get("pattern", "**/*.md")
        files = list(self.project_root.glob(pattern))

        content = []
        for file_path in sorted(files):
            with open(file_path, "r") as f:
                content.append(f.read())

        # Store in variables
        self.engine.variables[f"{name}_content"] = WorkflowVariable(
            name=f"{name}_content",
            value="\n\n".join(content),
            source="file_load",
            resolved=True,
        )

        print(f"  ✓ Loaded {name}: {len(files)} files")

    def _load_selective(self, name: str, config: Dict[str, Any]):
        """Load specific file using template variable."""
        # Would implement selective loading based on user input
        print(f"  ○ Selective load for {name} (not implemented)")

    def _load_index_guided(self, name: str, config: Dict[str, Any]):
        """Load files guided by index.md analysis."""
        # Would implement index-guided loading
        print(f"  ○ Index-guided load for {name} (not implemented)")

    def _advanced_elicitation_protocol(self):
        """
        Advanced elicitation protocol for content enhancement.

        Implements iterative elicitation with method selection from CSV.
        """
        print("\n📝 Advanced Elicitation")
        print("  (Interactive enhancement - not yet implemented)")

    def execute(self) -> bool:
        """Execute the documentation workflow."""
        if not self.engine:
            raise RuntimeError("Workflow not loaded. Call load_workflow() first.")

        return self.engine.execute()


# Example usage
if __name__ == "__main__":
    # Example workflow configuration
    example_config = {
        "id": "llm-doc-gen-example",
        "config_source": "./config.json",
        "instructions": [
            {
                "number": 1,
                "title": "Initialize",
                "actions": [
                    "Scan project structure",
                    "Create state file",
                    "Plan documentation sections",
                ],
            },
            {
                "number": 2,
                "title": "Discover Inputs",
                "actions": [
                    "<invoke-protocol name='discover_inputs' />",
                ],
            },
            {
                "number": 3,
                "title": "Generate Architecture Docs",
                "actions": [
                    "Analyze architecture",
                    "Create architecture/overview.md",
                    "<template-output />",
                ],
            },
        ],
        "input_file_patterns": {
            "source": {
                "pattern": "**/*.py",
                "load_strategy": "FULL_LOAD",
            },
        },
    }

    # Initialize workflow
    workflow = DocumentationWorkflow(
        project_root=Path("./example-project"),
        output_dir=Path("./docs"),
    )

    workflow.load_workflow(example_config)
    workflow.execute()
