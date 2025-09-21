# Mock GitLab Pipeline Trigger Service — API Contract

Base URL defaults to `http://localhost:8000`. All endpoints require the same private token defined with env var `MOCK_TOKEN` (default `MOCK_SUPER_SECRET`). Supply it using either `PRIVATE-TOKEN: <token>` or `Authorization: Bearer <token>`.

## Pipeline endpoints

### POST `/projects/{project_id}/trigger/pipeline`

Trigger a new pipeline.

- **Auth:** required
- **Body:**
  - JSON: `{ "token": "<trigger token>", "ref": "main", "variables": {"FOO":"bar"}, "scenario_id": 500 }`
  - Form: `token=TRIGGER&ref=main&variables[FOO]=bar`
  - Optional controls: `scenario_id`, `terminal_after_seconds`, `terminal_status`.
- **Response:** `201 Created`
  ```json
  {
    "id": 42,
    "status": "running",
    "ref": "main",
    "sha": "deadbeefcafebabe",
    "web_url": "http://localhost:8000/projects/123/pipelines/42",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "variables": {"FOO": "bar"},
    "scenario_id": 500,
    "terminal_after_seconds": 300,
    "terminal_status": "success"
  }
  ```

### GET `/projects/{project_id}/pipelines/{pipeline_id}`

Retrieve current pipeline state.

- **Auth:** required
- **Response:** `200 OK` with the same shape as the trigger response. `status` is recomputed using the pipeline's scenario and timestamps.

## Control endpoints

### GET `/_mock/scenarios`
Returns all scenarios.

### POST `/_mock/scenarios`
Create a scenario. Body matches scenario schema: `{ "scenario_id": 900, "name": "fail in 3m", "terminal_after_seconds": 180, "terminal_status": "failed", "never_complete": false }`.

### PUT `/_mock/scenarios/{scenario_id}`
Update a scenario (full replace semantics).

### DELETE `/_mock/scenarios/{scenario_id}`
Delete a scenario. Pipelines referencing it keep their inline terminal settings.

### GET `/_mock/pipelines`
List all stored pipelines.

### DELETE `/_mock/pipelines/{pipeline_id}`
Delete a single pipeline.

## Error handling

- Missing/invalid auth → `401`
- Unknown pipeline or scenario → `404`
- Validation errors → `422`
