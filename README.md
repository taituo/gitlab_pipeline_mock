# Mock GitLab Pipeline Trigger Service

A FastAPI + SQLite mock that simulates GitLab's pipeline trigger endpoints for deterministic integration tests.

## Development setup

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

For more details see `SPEC.md` and `API.md`.
