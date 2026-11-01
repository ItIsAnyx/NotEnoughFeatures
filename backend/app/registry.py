from dataclasses import dataclass
from typing import Literal

from pydantic import Field

from .domain import BlockDefinition, ContractModel, Port


class EmptyConfig(ContractModel):
    pass


class DatasetConfig(ContractModel):
    dataset: Literal["sklearn.breast_cancer"] = "sklearn.breast_cancer"


class TargetConfig(ContractModel):
    target: str = Field(default="target", min_length=1)


class SplitConfig(ContractModel):
    n_splits: int = Field(default=5, ge=2, le=100, strict=True)
    shuffle: bool = Field(default=True, strict=True)
    seed: int | None = Field(default=None, ge=0, le=2**32 - 1, strict=True)


class LogisticConfig(ContractModel):
    max_iter: int = Field(default=1000, ge=1, strict=True)
    c: float = Field(default=1.0, gt=0, allow_inf_nan=False)


class ForestConfig(ContractModel):
    n_estimators: int = Field(default=100, ge=1, strict=True)
    max_depth: int | None = Field(default=None, ge=1, strict=True)


@dataclass(frozen=True)
class BlockSpec:
    definition: BlockDefinition
    config_model: type[ContractModel]


class BlockRegistry:
    def __init__(self, specs: list[BlockSpec]):
        self._specs: dict[tuple[str, str], BlockSpec] = {}
        for spec in specs:
            key = (spec.definition.type, spec.definition.version)
            if key in self._specs:
                raise ValueError(f"Duplicate block definition: {key}")
            self._specs[key] = spec

    def get(self, block_type: str, version: str) -> BlockSpec | None:
        return self._specs.get((block_type, version))

    def definitions(self) -> list[BlockDefinition]:
        return [spec.definition.model_copy(deep=True) for spec in self._specs.values()]


def builtin_registry() -> BlockRegistry:
    specs: list[BlockSpec] = []

    def add(block_type, name, description, category, config=EmptyConfig, *, inputs=None, outputs=None):
        specs.append(BlockSpec(BlockDefinition(
            type=block_type, name=name, description=description, category=category,
            configSchema=config.model_json_schema(), inputs=inputs or {}, outputs=outputs or {},
        ), config))

    dataset = {"modality": "tabular", "features": ["numeric"]}
    classification = {**dataset, "task": "binary_classification", "hasTarget": True}
    probabilities = {"task": "binary_classification", "probabilities": True}
    add("nef.dataset.breast_cancer", "Tabular Dataset", "Built-in numeric dataset reference.", "data", DatasetConfig,
        outputs={"dataset": Port(type="TabularDataset", capabilities=dataset)})
    add("nef.dataset.select_target", "Target Selection / Validation", "Declares the target; runtime schema checks are pending.", "data", TargetConfig,
        inputs={"dataset": Port(type="TabularDataset", requires=dataset)},
        outputs={"dataset": Port(type="TabularDataset", capabilities=classification)})
    add("nef.split.stratified_kfold", "Stratified K-Fold", "Declares stratified folds.", "split", SplitConfig,
        inputs={"dataset": Port(type="TabularDataset", requires=classification)},
        outputs={"folds": Port(type="FoldCollection", capabilities=classification)})
    for block_type, name, config in (
        ("nef.model.logistic_regression", "Logistic Regression", LogisticConfig),
        ("nef.model.random_forest", "Random Forest", ForestConfig),
    ):
        add(block_type, name, "Classifier definition, not a trained model.", "model", config,
            outputs={"estimator": Port(type="ClassifierDefinition", capabilities=probabilities)})
    add("nef.training.train_predict", "Train and Predict", "Declares predictions for folds and model alternatives.", "training",
        inputs={"folds": Port(type="FoldCollection", requires=classification),
                "estimators": Port(type="ClassifierDefinition", cardinality="collection", requires=probabilities)},
        outputs={"predictions": Port(type="Predictions", cardinality="collection", capabilities=probabilities)})
    add("nef.metrics.classification", "Classification Metrics", "Accuracy, F1, ROC-AUC and confusion matrix contract.", "evaluation",
        inputs={"predictions": Port(type="Predictions", cardinality="collection", requires=probabilities)},
        outputs={"metrics": Port(type="ClassificationMetrics", cardinality="collection"),
                 "artifacts": Port(type="ArtifactCollection")})
    add("nef.results", "Results", "Collects metrics and optional artifacts.", "results",
        inputs={"metrics": Port(type="ClassificationMetrics", cardinality="collection"),
                "artifacts": Port(type="ArtifactCollection", required=False)})
    return BlockRegistry(specs)
