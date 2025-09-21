# gitlab_pipeline_mock

Fast, deterministic pipelines for your GitLab CI/CD integration tests.

## What & Why

When testing GitLab CI/CD integrations, using the real GitLab service can be slow, unpredictable, or hard to reproduce specific cases. `gitlab_pipeline_mock` is a lightweight service that mimics GitLab’s pipeline APIs, letting you simulate different pipeline states in a fully controlled way. This keeps your integration tests fast, deterministic, and safe.

## What It Does

- Trigger mock pipelines with defined outcomes (success, failure, long running, etc.).
- Poll for pipeline status as it progresses through the scenario you set.
- Create, update, and delete scenarios for flexible test setups.
- Secure the API with token-based authentication.

## How It Works

- Runs as a FastAPI application backed by SQLite storage.
- Scenarios declare timing, status, and completion rules that drive pipeline transitions.
- Your tests talk to this mock instead of GitLab’s API.
- The mock responds with GitLab-shaped payloads so clients behave exactly as they would against the real service.

## Getting Started

1. Clone the repo and explore available commands:
   ```sh
   git clone git@github.com:taituo/gitlab_pipeline_mock.git
   cd gitlab_pipeline_mock
   make help
   ```
2. Install dependencies and run the service:
   ```sh
   make install
   make run
   ```
3. Point your integration tests at `http://localhost:8000` and trigger pipelines using your preferred HTTP client. Sample `curl` flows live in `docs/EXAMPLE.md`.

To run the automated test suite at any time:
```sh
make test
```

## Documentation & References

- `docs/HOW.md` – build, run, and test automation via Make.
- `docs/EXAMPLE.md` – hands-on examples for triggering and polling pipelines.
- `docs/SPEC.md` – technical specification of behaviours and data model.
- `docs/API.md` – detailed REST contract; also served live at `/openapi.json` with Swagger UI at `/docs` and ReDoc at `/redoc`.
- `docs/START.md` – original project brief.

## Endpoints Overview

- `POST /projects/{project_id}/trigger/pipeline` — trigger a new pipeline (JSON or form payloads supported).
- `GET /projects/{project_id}/pipelines/{pipeline_id}` — fetch current pipeline state, including computed status.
- `GET /_mock/pipelines` — list pipelines stored in the mock database.
- `DELETE /_mock/pipelines/{pipeline_id}` — remove a pipeline row.
- `GET /_mock/scenarios` — view seeded and user-defined scenarios.
- `POST /_mock/scenarios` — create a scenario with custom duration/status.
- `PUT /_mock/scenarios/{scenario_id}` — update a scenario definition.
- `DELETE /_mock/scenarios/{scenario_id}` — delete a scenario (pipelines fall back to inline settings).

Authentication expects the `MOCK_TOKEN` value via either the `PRIVATE-TOKEN` header or an `Authorization: Bearer` token.

## License

Distributed under the MIT License. See `LICENSE` for details.
