# Mock GitLab Pipeline Trigger Service — Technical Spec

This project implements a lightweight FastAPI application that mimics a subset of the GitLab API v4 trigger and pipeline endpoints. It exists to support deterministic integration tests that need to simulate triggering and polling GitLab pipelines without hitting the real service.

## Functional requirements

- Accept `POST /projects/{project_id}/trigger/pipeline` requests using either `application/json` or `application/x-www-form-urlencoded` payloads.
- Require a static token (`MOCK_TOKEN`, default `MOCK_SUPER_SECRET`) supplied via either the `PRIVATE-TOKEN` header or a bearer token.
- Persist triggered pipelines to SQLite and return GitLab-shaped pipeline objects (`id`, `status`, `ref`, `sha`, timestamps, etc.).
- Expose `GET /projects/{project_id}/pipelines/{pipeline_id}` to retrieve the latest pipeline status. The status must be recomputed on each read according to the scenario rules below.
- Provide a control namespace `/_mock/*` for manipulating scenarios and inspecting or deleting pipelines.

## Scenario engine

- Pipelines reference an optional scenario that drives how and when they reach a terminal state.
- Built-in scenarios:
  - `0`: never complete (always `running`).
  - `1..99`: transition to `success` after the matching number of seconds.
  - `100`: succeed after 60 seconds.
  - `200`: succeed after 120 seconds.
  - `500`: succeed after 300 seconds.
- Custom scenarios can be created via control endpoints.
- If a pipeline provides inline `terminal_after_seconds` / `terminal_status` values they override the scenario preset.
- When `never_complete` is true, the computed status must stay `running` regardless of elapsed time.

## Data model

SQLite database `mock.db` with two tables:

- `scenarios`
  - `scenario_id` (PK integer)
  - `name` (text, required)
  - `terminal_after_seconds` (integer, nullable)
  - `terminal_status` (text, default `success`)
  - `never_complete` (integer bool, default `0`)
- `pipelines`
  - `id` (PK autoincrement)
  - `project_id` (int, required)
  - `ref` (text, required)
  - `sha` (text, required)
  - `status` (text, defaults to `running`)
  - `variables_json` (text JSON encoded map)
  - `scenario_id` (int, FK to `scenarios`)
  - `terminal_after_seconds` (int, nullable)
  - `terminal_status` (text, nullable)
  - `created_at`, `updated_at` (datetime)

## Non-functional requirements

- Deterministic behaviour suitable for unit/integration tests; no background threads required.
- Pure Python standard library randomness is acceptable for generating fake SHAs and URLs.
- Codebase must be covered by automated tests using `pytest` and FastAPI's `TestClient`.
- Provide documentation for running, testing, and interacting with the API.

## Future enhancements (non-MVP)

- Implement optional `/reset` endpoint guarded by env flag to drop all data.
- Add filtering/query options for pipeline listing.
- Support persistence of per-project trigger tokens.

## OpenAPI contract

- The canonical contract is defined in `API.md` and served dynamically by the FastAPI application at `/openapi.json` (with Swagger UI at `/docs` and ReDoc at `/redoc`).
- Keep the generated OpenAPI document aligned with code changes by updating `app/openapi.py` alongside any endpoint modifications.
