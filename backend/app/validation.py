from collections import defaultdict, deque

from pydantic import ValidationError

from .domain import Diagnostic, Port, ValidationResult, Workflow
from .registry import BlockRegistry


def contract_errors(output: Port, input_port: Port) -> list[tuple[str, str]]:
    errors = []
    if output.type != input_port.type:
        errors.append(("TYPE_MISMATCH", f"Expected {input_port.type}, received {output.type}."))
    if output.cardinality == "collection" and input_port.cardinality == "single":
        errors.append(("CARDINALITY_MISMATCH", "A collection output cannot feed a single input."))
    if input_port.required and not output.required:
        errors.append(("OPTIONAL_OUTPUT", "An optional output cannot guarantee a required input."))
    for key, requirement in input_port.requires.items():
        actual = output.capabilities.get(key)
        # A string requirement is exact; a list gives allowed values. Every
        # guaranteed output value must be accepted, not just an overlapping one.
        if actual is None:
            compatible = False
        elif isinstance(requirement, bool):
            compatible = type(actual) is bool and actual == requirement
        else:
            allowed = requirement if isinstance(requirement, list) else [requirement]
            produced = actual if isinstance(actual, list) else [actual]
            compatible = bool(produced) and all(value in allowed for value in produced)
        if not compatible:
            errors.append(("CAPABILITY_MISMATCH", f"Capability '{key}' requires {requirement!r}; producer declares {actual!r}."))
    return errors


def validate_workflow(workflow: Workflow, registry: BlockRegistry) -> ValidationResult:
    diagnostics: list[Diagnostic] = []

    def report(code, message, *, node=None, edge=None, port=None, path=None, severity="error"):
        diagnostics.append(Diagnostic(code=code, message=message, nodeId=node,
                                      edgeIndex=edge, port=port, configPath=path, severity=severity))

    nodes = {}
    specs = {}
    for node in workflow.nodes:
        if node.id in nodes:
            report("DUPLICATE_NODE_ID", "Node IDs must be unique.", node=node.id)
            continue
        nodes[node.id] = node
        spec = registry.get(node.block_type, node.block_version)
        if spec is None:
            report("UNKNOWN_BLOCK", f"Unknown block type/version: {node.block_type}@{node.block_version}.", node=node.id)
            continue
        specs[node.id] = spec
        try:
            spec.config_model.model_validate(node.config)
        except ValidationError as exc:
            for error in exc.errors():
                report("INVALID_CONFIG", error["msg"], node=node.id, path=list(error["loc"]))

    if not nodes:
        report("EMPTY_WORKFLOW", "A workflow must contain at least one node.")

    incoming = defaultdict(list)
    adjacent = {node_id: set() for node_id in nodes}
    degree = dict.fromkeys(nodes, 0)
    touched = set()
    seen_edges = set()
    for index, edge in enumerate(workflow.edges):
        source, target = edge.source_node_id, edge.target_node_id
        key = (source, edge.source_port, target, edge.target_port)
        if key in seen_edges:
            report("DUPLICATE_EDGE", "This port connection is already present.", edge=index)
            continue
        seen_edges.add(key)
        missing = False
        for node_id in (source, target):
            if node_id not in nodes:
                report("UNKNOWN_NODE", "Edge references a missing node.", node=node_id, edge=index)
                missing = True
        if missing:
            continue
        touched.update((source, target))
        if target not in adjacent[source]:
            adjacent[source].add(target)
            degree[target] += 1
        source_spec, target_spec = specs.get(source), specs.get(target)
        output = source_spec.definition.outputs.get(edge.source_port) if source_spec else None
        input_port = target_spec.definition.inputs.get(edge.target_port) if target_spec else None
        if source_spec and output is None:
            report("UNKNOWN_OUTPUT_PORT", "Output port does not exist.", node=source, edge=index, port=edge.source_port)
        if target_spec and input_port is None:
            report("UNKNOWN_INPUT_PORT", "Input port does not exist.", node=target, edge=index, port=edge.target_port)
        if output is None or input_port is None:
            continue
        incoming[(target, edge.target_port)].append(index)
        for code, message in contract_errors(output, input_port):
            report(code, message, node=target, edge=index, port=edge.target_port)

    for node_id, spec in specs.items():
        for name, port in spec.definition.inputs.items():
            connections = incoming[(node_id, name)]
            if port.required and not connections:
                report("MISSING_INPUT", "Required input has no connection.", node=node_id, port=name)
            if port.cardinality == "single" and len(connections) > 1:
                report("MULTIPLE_INPUTS", "Single input accepts at most one edge.", node=node_id, port=name)
        if len(nodes) > 1 and node_id not in touched:
            report("ISOLATED_NODE", "Node is disconnected from the graph.", node=node_id, severity="warning")

    queue = deque(node_id for node_id in nodes if degree[node_id] == 0)
    order = []
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for target in sorted(adjacent[node_id], key=str):
            degree[target] -= 1
            if degree[target] == 0:
                queue.append(target)
    if len(order) != len(nodes):
        report("CYCLE", "Workflow contains a cycle; only directed acyclic graphs are supported.")

    report("STATIC_ONLY", "Only declared contracts were checked. Dataset schema, actual outputs and execution are not validated.", severity="info")
    valid = not any(item.severity == "error" for item in diagnostics)
    return ValidationResult(valid=valid, diagnostics=diagnostics, topologicalOrder=order if valid else [])
