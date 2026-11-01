from uuid import NAMESPACE_URL, uuid5

from .domain import Workflow, WorkflowEdge, WorkflowNode


def golden_path() -> Workflow:
    def stable_id(name):
        return uuid5(NAMESPACE_URL, f"nef:golden-path:{name}")

    rows = [
        ("dataset", "nef.dataset.breast_cancer", {}, 0, 0),
        ("target", "nef.dataset.select_target", {"target": "target"}, 240, 0),
        ("split", "nef.split.stratified_kfold", {"n_splits": 5}, 480, 0),
        ("logistic", "nef.model.logistic_regression", {}, 480, 200),
        ("forest", "nef.model.random_forest", {}, 480, 400),
        ("train", "nef.training.train_predict", {}, 720, 0),
        ("metrics", "nef.metrics.classification", {}, 960, 0),
        ("results", "nef.results", {}, 1200, 0),
    ]
    connections = [
        ("dataset", "dataset", "target", "dataset"),
        ("target", "dataset", "split", "dataset"),
        ("split", "folds", "train", "folds"),
        ("logistic", "estimator", "train", "estimators"),
        ("forest", "estimator", "train", "estimators"),
        ("train", "predictions", "metrics", "predictions"),
        ("metrics", "metrics", "results", "metrics"),
        ("metrics", "artifacts", "results", "artifacts"),
    ]
    return Workflow(
        schemaVersion="1", applicationVersion="0.1", id=stable_id("workflow"),
        name="Binary classification golden path",
        nodes=[WorkflowNode(id=stable_id(name), blockType=block_type, blockVersion="1.0.0",
                            config=config, position={"x": x, "y": y})
               for name, block_type, config, x, y in rows],
        edges=[WorkflowEdge(sourceNodeId=stable_id(source), sourcePort=output,
                            targetNodeId=stable_id(target), targetPort=input_port)
               for source, output, target, input_port in connections],
    )
