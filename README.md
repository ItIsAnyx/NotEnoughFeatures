# NotEnoughFeatures

Local-first visual AI/ML experiment workflows. Architecture and terminology live in
[the project foundations](docs/PROJECT_FOUNDATIONS.md).

The first implemented slice is **workflow authoring and static contract validation**.
It includes an editable classification golden path, a block catalog with JSON Schema
configuration forms, and structured diagnostics for a future React/TypeScript canvas.
Blocks do not load data, train models, or produce metrics yet.

## Run the Workflow API

From the repository root, with Python 3.11+ (verified with Python 3.14):

```powershell
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload
```

Open [interactive API docs](http://127.0.0.1:8000/docs) to load the golden path and
submit it to validation. The Workflow API is independent of the older PDF experiment
in `backend/main.py`; PDF dependencies are not needed for this milestone.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/blocks` | Versioned block definitions, ports and configuration schemas |
| `GET /api/workflows/schema` | Workflow document JSON Schema |
| `GET /api/workflows/golden-path` | Editable graph with 5 folds and 2 classifier nodes |
| `POST /api/workflows/validate` | Static validation, diagnostics and topological order |

Validation returns HTTP 200 with `valid: false` for graph/configuration errors and
HTTP 422 for malformed workflow documents or unsupported document versions. Diagnostics
include stable codes and node IDs, edge indexes, port names or configuration paths where
applicable. Every response includes a `STATIC_ONLY` notice explaining the validation scope.

Try it from PowerShell while the server is running:

```powershell
$workflow = Invoke-RestMethod http://127.0.0.1:8000/api/workflows/golden-path
$body = $workflow | ConvertTo-Json -Depth 30
Invoke-RestMethod http://127.0.0.1:8000/api/workflows/validate -Method Post -ContentType application/json -Body $body
# Save and restore the same document locally; there is no backend persistence yet.
$body | Set-Content -LiteralPath workflow.json -Encoding utf8
```

The checked-in [workflow JSON](tests/fixtures/classification.json) is the same example.
Positions and labels round-trip with stable UUIDs. Canvas edits preserve an existing
node ID; newly created nodes must receive fresh UUIDs.

## Contract rules in this prototype

- Base types match exactly. No implicit conversion or block-pair compatibility matrix.
- Required input ports must be connected. Single inputs accept at most one edge.
- Collection inputs aggregate single values or collection outputs of the same base
  type; collection outputs cannot feed single inputs. Nested collections are not implied.
- Capability requirements use exact scalar/boolean equality or a list of allowed values.
  Every value declared by a producer must be accepted; missing capabilities fail validation.
- `FoldCollection` and `ArtifactCollection` are aggregate base types. Port cardinality
  describes how many values of that base type a port carries.
- Block type/version, configuration, named port direction, edge references, duplicate
  IDs/connections and DAG structure are checked. Isolated nodes produce warnings.

See [prototype recommendations and boundaries](docs/PROJECT_FOUNDATIONS.md#19-workflow-contract-prototype-2026-11-01)
for the open design choices exercised by this slice. The response is not an ExecutionPlan;
trial expansion, immutable preview, execution and runtime output validation follow later.

## Tests

```powershell
backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests -v
```

Tests cover the saved golden path, JSON round-trip, invalid graphs/configurations,
capability and cardinality rules, and the HTTP API. No ML packages or external services
are required.
