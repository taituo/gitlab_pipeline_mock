# Mock GitLab Pipeline Trigger Service

A FastAPI + SQLite mock that simulates GitLab's pipeline trigger endpoints for deterministic integration tests.

## Quick start with Make

```sh
make help        # list available targets
make install     # create .venv and install dependencies
make test        # run pytest inside the virtualenv
make run         # launch uvicorn with auto-reload
```

Set `PYTHON` env var if you need a specific interpreter (defaults to `python3`).

Additional guides:
- `EXAMPLE.md` – step-by-step `curl` recipes for triggering, polling, and managing scenarios.
- `HOW.md` – build, test, and run instructions mapped to the project Make targets.

## Development setup (manual)

1. Create a virtualenv and install dependencies:
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Seed the default scenarios and launch the server:
   ```sh
   export MOCK_TOKEN=MOCK_SUPER_SECRET
   uvicorn app.main:app --reload
   ```

## Running tests

```sh
pytest
```

## API quick start

Trigger a pipeline that completes after 5 minutes:

```sh
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline" \
  -H "PRIVATE-TOKEN: ${MOCK_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"token": "TRIGGER", "ref": "main", "scenario_id": 500}'
```

Then poll:

```sh
curl -s -H "PRIVATE-TOKEN: ${MOCK_TOKEN}" \
  "http://localhost:8000/projects/123/pipelines/1" | jq .status
```

## Endpoints overview

- `POST /projects/{project_id}/trigger/pipeline` — trigger a new pipeline (JSON or form payloads supported).
- `GET /projects/{project_id}/pipelines/{pipeline_id}` — fetch current pipeline state, including computed status.
- `GET /_mock/pipelines` — list pipelines stored in the mock database.
- `DELETE /_mock/pipelines/{pipeline_id}` — remove a pipeline row.
- `GET /_mock/scenarios` — view seeded and user-defined scenarios.
- `POST /_mock/scenarios` — create a scenario with custom duration/status.
- `PUT /_mock/scenarios/{scenario_id}` — update a scenario definition.
- `DELETE /_mock/scenarios/{scenario_id}` — delete a scenario (pipelines fall back to inline settings).

Authentication expects `MOCK_TOKEN` via `PRIVATE-TOKEN` header (or `Authorization: Bearer`).

For more details see `SPEC.md` and `API.md`.

## License

Distributed under the MIT License. See `LICENSE` for details.
