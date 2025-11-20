"""
LLM-based documentation generation skill.

This skill generates comprehensive, navigable documentation using Large Language Model
consultation. It creates sharded documentation (organized topic files) by having LLMs
read and analyze source code directly, then synthesizing their insights into structured,
human-readable guides.

Key exports:
- WorkflowEngine: Core workflow orchestration engine
- DocumentationWorkflow: Specialized documentation generation workflow
- ExecutionMode: Workflow execution modes (NORMAL, YOLO)
- WorkflowState: State management for resumability
"""

from claude_skills.llm_doc_gen.workflow_engine import (
    DocumentationWorkflow,
    ExecutionMode,
    StepStatus,
    WorkflowEngine,
    WorkflowState,
    WorkflowStep,
    WorkflowVariable,
)

__all__ = [
    "WorkflowEngine",
    "DocumentationWorkflow",
    "ExecutionMode",
    "StepStatus",
    "WorkflowState",
    "WorkflowStep",
    "WorkflowVariable",
]

__version__ = "0.1.0"
