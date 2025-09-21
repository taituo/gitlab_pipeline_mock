# Usage Examples

This guide shows how to exercise the mock GitLab pipeline trigger service using `curl` once the app is running locally (`make run`). Replace placeholders as needed. Explore the live API contract at `http://localhost:8000/docs` or fetch the raw schema from `/openapi.json`.

## Trigger a pipeline with preset scenario

```sh
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline" \
  -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TRIGGER_TOKEN",
    "ref": "main",
    "scenario_id": 5,
    "variables": {"DEPLOY_ENV": "staging"}
  }' | jq
```

## Poll for status until success

```sh
curl -s -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}" \
  "http://localhost:8000/projects/123/pipelines/1" | jq
```

If the scenario is terminal after 5 seconds, you can add a watch loop:

```sh
while true; do
  curl -s -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}" \
    "http://localhost:8000/projects/123/pipelines/1" | jq .status
  sleep 2
done
```

## Create and use a custom scenario

```sh
curl -s -X POST "http://localhost:8000/_mock/scenarios" \
  -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": 900,
    "name": "fail in 3 minutes",
    "terminal_after_seconds": 180,
    "terminal_status": "failed",
    "never_complete": false
  }'
```

Trigger a pipeline that uses the new scenario:

```sh
curl -s -X POST "http://localhost:8000/projects/42/trigger/pipeline" \
  -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{"token": "TRIGGER", "ref": "release", "scenario_id": 900}' | jq
```

Clean up the scenario when done:

```sh
curl -s -X DELETE "http://localhost:8000/_mock/scenarios/900" \
  -H "PRIVATE-TOKEN: ${MOCK_TOKEN:-MOCK_SUPER_SECRET}"
```
