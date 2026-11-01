from fastapi import FastAPI

from .domain import BlockDefinition, ValidationResult, Workflow
from .golden_path import golden_path
from .registry import builtin_registry
from .validation import validate_workflow

app = FastAPI(title="NotEnoughFeatures Workflow API", version="0.1.0")
registry = builtin_registry()


@app.get("/api/blocks", response_model=list[BlockDefinition])
def list_blocks():
    return registry.definitions()


@app.get("/api/workflows/schema")
def workflow_schema():
    return Workflow.model_json_schema(by_alias=True)


@app.get("/api/workflows/golden-path", response_model=Workflow)
def example_workflow():
    return golden_path()


@app.post("/api/workflows/validate", response_model=ValidationResult)
def validate(workflow: Workflow):
    return validate_workflow(workflow, registry)
