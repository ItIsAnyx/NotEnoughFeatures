from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Position(ContractModel):
    x: float = 0
    y: float = 0


class WorkflowNode(ContractModel):
    id: UUID
    block_type: str = Field(alias="blockType")
    block_version: str = Field(alias="blockVersion")
    label: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    position: Position = Field(default_factory=Position)
    group: str | None = None


class WorkflowEdge(ContractModel):
    source_node_id: UUID = Field(alias="sourceNodeId")
    source_port: str = Field(alias="sourcePort")
    target_node_id: UUID = Field(alias="targetNodeId")
    target_port: str = Field(alias="targetPort")


class Workflow(ContractModel):
    schema_version: Literal["1"] = Field(alias="schemaVersion")
    application_version: Literal["0.1"] = Field(alias="applicationVersion")
    id: UUID
    name: str = Field(min_length=1)
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]


Capability = str | bool | list[str]


class Port(ContractModel):
    type: str
    cardinality: Literal["single", "collection"] = "single"
    required: bool = True
    capabilities: dict[str, Capability] = Field(default_factory=dict)
    requires: dict[str, Capability] = Field(default_factory=dict)


class BlockDefinition(ContractModel):
    type: str
    version: str = "1.0.0"
    name: str
    description: str
    category: str
    config_schema: dict[str, Any] = Field(alias="configSchema")
    inputs: dict[str, Port] = Field(default_factory=dict)
    outputs: dict[str, Port] = Field(default_factory=dict)
    execution_supported: Literal[False] = Field(default=False, alias="executionSupported")


class Diagnostic(ContractModel):
    severity: Literal["error", "warning", "info"] = "error"
    code: str
    message: str
    node_id: UUID | None = Field(default=None, alias="nodeId")
    edge_index: int | None = Field(default=None, alias="edgeIndex")
    port: str | None = None
    config_path: list[str | int] | None = Field(default=None, alias="configPath")


class ValidationResult(ContractModel):
    valid: bool
    diagnostics: list[Diagnostic]
    topological_order: list[UUID] = Field(default_factory=list, alias="topologicalOrder")
