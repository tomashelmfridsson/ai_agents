from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkflowNode:
    stage_key: str
    agent_key: str
    stage_index: int
    description: str


@dataclass
class WorkflowGraph:
    start_stage: str
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)

    def add_node(self, node: WorkflowNode) -> None:
        self.nodes[node.stage_key] = node

    def get_node(self, stage_key: str) -> WorkflowNode:
        return self.nodes[stage_key]


def build_default_workflow_graph() -> WorkflowGraph:
    graph = WorkflowGraph(start_stage="orchestrator")
    graph.add_node(
        WorkflowNode(
            stage_key="orchestrator",
            agent_key="orchestrator",
            stage_index=0,
            description="Route the workflow to the next valid agent.",
        )
    )
    graph.add_node(
        WorkflowNode(
            stage_key="requirements",
            agent_key="requirements_analyst",
            stage_index=1,
            description="Extract structured requirements from raw scenario text.",
        )
    )
    graph.add_node(
        WorkflowNode(
            stage_key="design",
            agent_key="test_design",
            stage_index=2,
            description="Create concrete test-case designs from requirements.",
        )
    )
    graph.add_node(
        WorkflowNode(
            stage_key="review",
            agent_key="review",
            stage_index=3,
            description="Review coverage, oracle strength, and routing focus.",
        )
    )
    return graph
