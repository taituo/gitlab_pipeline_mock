# Mock GitLab Pipeline Trigger Service — All Docs

This file contains three documents in one: SPEC.md, API.md, and README.md.

---

```sh
# cut
cat > SPEC.md << 'EOF'
# SPEC.md — Mock GitLab Pipeline Trigger Service (FastAPI + SQLite)

> **Audience:** developer agent implementing a mock of GitLab API v4 trigger/pipeline endpoints for integration tests.  
> **Goal:** provide deterministic, scriptable responses for pipeline lifecycle (trigger → running → terminal) with user‑controllable scenarios.

---

## 1) Background & references (no live fetching)

- **Primary reference:** *GitLab API v4 — Pipelines*, *Pipeline triggers* (official docs).
- **Format reference:** *OpenAPI 3.0* (for this mock’s own contract).
- **Behavioral notes from GitLab v4:**
  - Triggering a pipeline is done with `POST /projects/{id}/trigger/pipeline` using a **trigger token** plus a **ref**; optional **variables** can be supplied.
  - The trigger response returns a **pipeline object** that includes at least an `id` (numeric) and a **status** (e.g., `pending`, `running`, `success`, etc.). Clients normally poll `GET /projects/{id}/pipelines/{pipeline_id}` for updated status.
  - Canonical pipeline statuses include (non‑exhaustive): `created`, `waiting_for_resource`, `preparing`, `pending`, `running`, `success`, `failed`, `canceled`, `skipped`, `manual`, `scheduled`. “Finished” is **not** a real status; `success` (or other terminal status) indicates completion.

> We will emulate the above for a **mock**, not a real CI runner.

---

## 2) High‑level design

- **Framework:** FastAPI
- **Storage:** SQLite (file `mock.db`), using SQLAlchemy or equivalent.
- **Auth:** single hard‑coded token (config env `MOCK_TOKEN`, default `MOCK_SUPER_SECRET`). Accepted as either header `PRIVATE-TOKEN` or `Authorization: Bearer {token}`.
- **Time model:**
  - Upon trigger, a new **pipeline row** is created with `status="running"` immediately (or `pending` if you prefer to mimic initial queueing). The mock **always** returns consistent, GitLab‑shaped objects.
  - Each pipeline is bound to a **scenario** that dictates when/if it transitions to a terminal status.
  - The **status is computed on read** (GET) from `created_at` + `terminal_after_seconds` (no background jobs needed). If elapsed ≥ duration, return `terminal_status`; otherwise `running`. If scenario is “never complete”, status never changes.
- **Defaults:** a library of scenario presets is pre‑seeded in the DB (see §5).

---

## 3) Endpoints (what will be implemented)

### 3.1 GitLab‑shaped endpoints (for your system under test)

> These are the endpoints your client/test suite will call. They mimic GitLab API v4 paths/payloads.

1. **Trigger pipeline** — **POST** `/projects/{project_id}/trigger/pipeline`  
   - **Auth:** required (hard‑coded token).  
   - **Body:** accepts either `application/x-www-form-urlencoded` (GitLab‑like) or `application/json` (test convenience).  
     - Required: `token`, `ref`  
     - Optional variables:  
       - Form style: `variables[KEY]=VALUE` (repeatable)  
       - JSON style: `{ "variables": { "KEY": "VALUE", ... } }`  
     - Mock controls (optional): `scenario_id` (int), or `terminal_after_seconds` (int), `terminal_status` (string). `scenario_id` overrides raw fields.
   - **Returns:** `201` with a mock **pipeline** object: `id`, `status`, `ref`, `sha` (fake), `web_url` (fake), `created_at`, `updated_at`, `source`, `detailed_status` (optional), and an echo of provided variables.  
   - **Initial status:** **`running`** (for simplicity). You may switch to `pending` if you want closer fidelity.

2. **Get pipeline** — **GET** `/projects/{project_id}/pipelines/{pipeline_id}`  
   - **Auth:** required.  
   - **Returns:** `200` with pipeline object. The `status` is computed on read:  
     - If scenario is **never** (ID `0`), status is always `running`.  
     - Else if `now - created_at < terminal_after_seconds`, status is `running`.  
     - Else status is `terminal_status` (default `success`).

> These two endpoints are sufficient for: *“I trigger a pipeline, I poll its status until terminal (or forever).”*

### 3.2 Test‑user **controls** (“nippulat ja nappulat”)

> Separate namespace for manipulating mock behavior. Prefixed with `/_mock` to avoid collision with GitLab shapes.

3. **List scenarios** — **GET** `/_mock/scenarios`  
4. **Create scenario** — **POST** `/_mock/scenarios`  
5. **Update scenario** — **PUT** `/_mock/scenarios/{scenario_id}`  
6. **Delete scenario** — **DELETE** `/_mock/scenarios/{scenario_id}`  
   - Scenario attributes:  
     - `scenario_id` (int, unique) — see defaults below  
     - `name` (string)  
     - `terminal_after_seconds` (int|null)  
     - `terminal_status` (string, one of GitLab statuses; default `success`)  
     - `never_complete` (bool; when true, ignore duration and always `running`)

7. **List pipelines** — **GET** `/_mock/pipelines`  
8. **Delete a pipeline** — **DELETE** `/_mock/pipelines/{pipeline_id}`  
9. **Reset DB** (optional, guarded by env flag) — **POST** `/_mock/reset`

> **Mapping in trigger:** if `scenario_id` is provided, the pipeline inherits that scenario’s behavior. Otherwise it uses inline override fields if supplied, else the **default scenario** (5 minutes success).

---

## 4) Data model (SQLite)

### 4.1 Tables

**`scenarios`**
- `scenario_id` INTEGER PRIMARY KEY
- `name` TEXT NOT NULL
- `terminal_after_seconds` INTEGER NULL
- `terminal_status` TEXT NOT NULL DEFAULT 'success'
- `never_complete` INTEGER NOT NULL DEFAULT 0  -- (0/1)

**`pipelines`**
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `project_id` INTEGER NOT NULL
- `ref` TEXT NOT NULL
- `sha` TEXT NOT NULL  -- random/fake
- `status` TEXT NOT NULL DEFAULT 'running'  -- denormalized last known
- `variables_json` TEXT NULL  -- JSON dict
- `scenario_id` INTEGER NULL REFERENCES scenarios(scenario_id)
- `terminal_after_seconds` INTEGER NULL  -- inline override
- `terminal_status` TEXT NULL  -- inline override
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

> Status on reads is calculated from `created_at` and the effective scenario/overrides.

### 4.2 Scenario resolution order

1) `scenario_id` (if present)  
2) Inline `terminal_after_seconds` / `terminal_status` from trigger body  
3) **Default scenario** = 300 seconds → `success`

---

## 5) Pre‑seeded **default cases**

> These are available without user creation and may be removed if desired.

- **ID 0** → `never_complete = true` (always `running`)
- **ID 1..99** → `terminal_after_seconds = ID`
- **ID 100** → `terminal_after_seconds = 60`
- **ID 200** → `terminal_after_seconds = 120`
- **ID 500** → `terminal_after_seconds = 300`

All default scenarios use `terminal_status = "success"` unless changed.

### 5.1 SQL seeding snippets (shell blockpoints)

Create the table structure and seed defaults (example):

```sh
cat > schema.sql << 'EOF'
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  terminal_after_seconds INTEGER,
  terminal_status TEXT NOT NULL DEFAULT 'success',
  never_complete INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipelines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  ref TEXT NOT NULL,
  sha TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  variables_json TEXT,
  scenario_id INTEGER,
  terminal_after_seconds INTEGER,
  terminal_status TEXT,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  FOREIGN KEY(scenario_id) REFERENCES scenarios(scenario_id) ON DELETE SET NULL
);
EOF
```

```sh
# Seed default scenarios
cat > seed_defaults.sql << 'EOF'
INSERT OR REPLACE INTO scenarios (scenario_id, name, terminal_after_seconds, terminal_status, never_complete) VALUES
  (0,   'never complete', NULL, 'success', 1);

-- IDs 1..99 = duration in seconds
EOF

# Generate 1..99 rows (example Bash loop)
cat > seed_seconds.sql << 'EOF'
.mode csv
EOF
```

For a portable single‑file insert (no loops), you can paste explicit rows (truncated for brevity):

```sh
cat >> seed_defaults.sql << 'EOF'
INSERT OR REPLACE INTO scenarios (scenario_id, name, terminal_after_seconds, terminal_status, never_complete) VALUES
  (1, 'after 1 second', 1, 'success', 0),
  (2, 'after 2 seconds', 2, 'success', 0),
  (3, 'after 3 seconds', 3, 'success', 0),
  (4, 'after 4 seconds', 4, 'success', 0),
  (5, 'after 5 seconds', 5, 'success', 0);
-- ...continue up to 99 as needed...
INSERT OR REPLACE INTO scenarios (scenario_id, name, terminal_after_seconds, terminal_status, never_complete) VALUES
  (100, 'after 1 minute', 60, 'success', 0),
  (200, 'after 2 minutes', 120, 'success', 0),
  (500, 'after 5 minutes', 300, 'success', 0);
EOF
```

Apply:

```sh
# Create DB and apply seeds
sqlite3 mock.db < schema.sql
sqlite3 mock.db < seed_defaults.sql
```

> You may add additional seeds for failure/canceled etc. via control endpoints or more inserts.

---

## 6) Deviations vs. real GitLab

- We accept **JSON** in the trigger for convenience; GitLab historically expects **form‑urlencoded** for trigger. Clients using GitLab’s shape should still work because we also accept form variables style `variables[KEY]=VALUE`.
- We start at `running` right away. Real GitLab might show `pending` first; you can change the initial status via config if preferred.
- The `sha` is fake (random).

---

## 7) OpenAPI (contract for this mock)

A full OpenAPI document is provided in **API.md** (OpenAPI 3.0). This spec covers the two GitLab‑shaped endpoints plus the `/_mock/*` control endpoints.

---

## 8) Answers to validation questions

- **Does the pipeline trigger response include state at trigger time?**  
  Yes — it returns a pipeline object with `id` and a `status` (often `pending`/`running`). **You still need to poll** `GET /projects/{id}/pipelines/{pipeline_id}` for updates.

- **Payload shapes:**  
  - **Trigger (form):** `token=...&ref=main&variables[FOO]=bar&variables[BAZ]=qux`  
  - **Trigger (json, mock extension):** `{ "token":"...", "ref":"main", "variables": { "FOO":"bar" } }`  
  - **Mock controls:** optionally include `scenario_id` **or** `{ "terminal_after_seconds": 300, "terminal_status": "success" }`.

---

## 9) What needs to be implemented (summary checklist)

- [ ] FastAPI app with auth dependency (hard‑coded token)  
- [ ] SQLite models and migrations/DDL as above  
- [ ] POST `/projects/{id}/trigger/pipeline` (form + json)  
- [ ] GET `/projects/{id}/pipelines/{pipeline_id}` (computed status)  
- [ ] `/_mock/scenarios` CRUD  
- [ ] `/_mock/pipelines` list & delete  
- [ ] DB seeding for default scenarios (ID 0, 1..99, 100, 200, 500)  
- [ ] Tests / fixtures using canned scenarios


EOF
```

```sh
# cut
cat > API.md << 'EOF'
# API.md — OpenAPI & Usage Guide

This document defines the HTTP contract for the **Mock GitLab Pipeline Trigger Service**.

- **Base URL (dev):** `http://localhost:8000`
- **Auth:** Use header `PRIVATE-TOKEN: MOCK_SUPER_SECRET` (or `Authorization: Bearer MOCK_SUPER_SECRET`)

---

## 1) OpenAPI 3.0 (YAML)

```yaml
openapi: 3.0.3
info:
  title: Mock GitLab Pipeline Trigger Service
  version: 1.0.0
  description: >
    A FastAPI+SQLite mock that simulates GitLab API v4 pipeline triggers and status polling.
servers:
  - url: http://localhost:8000
components:
  securitySchemes:
    PrivateToken:
      type: apiKey
      in: header
      name: PRIVATE-TOKEN
    Bearer:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    Pipeline:
      type: object
      required: [id, status, ref, sha, created_at, updated_at]
      properties:
        id: { type: integer, example: 123456 }
        status: { type: string, example: running }
        ref: { type: string, example: main }
        sha: { type: string, example: "deadbeefcafebabe" }
        web_url: { type: string, example: "http://localhost:8000/projects/1/pipelines/123456" }
        source: { type: string, example: trigger }
        created_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }
        variables:
          type: object
          additionalProperties: { type: string }
        scenario_id: { type: integer, nullable: true }
        terminal_after_seconds: { type: integer, nullable: true }
        terminal_status: { type: string, nullable: true, example: success }
    Scenario:
      type: object
      required: [scenario_id, name]
      properties:
        scenario_id: { type: integer, example: 500 }
        name: { type: string, example: "after 5 minutes" }
        terminal_after_seconds: { type: integer, nullable: true, example: 300 }
        terminal_status: { type: string, example: success }
        never_complete: { type: boolean, example: false }
    ScenarioCreate:
      allOf:
        - $ref: '#/components/schemas/Scenario'
      required: [scenario_id, name]
    ScenarioUpdate:
      type: object
      properties:
        name: { type: string }
        terminal_after_seconds: { type: integer, nullable: true }
        terminal_status: { type: string }
        never_complete: { type: boolean }
  parameters:
    ProjectId:
      name: project_id
      in: path
      required: true
      schema: { type: integer }
    PipelineId:
      name: pipeline_id
      in: path
      required: true
      schema: { type: integer }
security:
  - PrivateToken: []
  - Bearer: []
paths:
  /projects/{project_id}/trigger/pipeline:
    post:
      summary: Trigger a pipeline (GitLab-shaped)
      description: >
        Accepts GitLab-like payloads (`token`, `ref`, `variables`) and returns a pipeline record.
        The mock also accepts optional `scenario_id` or direct overrides (`terminal_after_seconds`, `terminal_status`).
      security:
        - PrivateToken: []
        - Bearer: []
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [token, ref]
              properties:
                token: { type: string }
                ref: { type: string }
                scenario_id: { type: integer }
                terminal_after_seconds: { type: integer }
                terminal_status: { type: string }
                # variables[KEY]=VALUE pairs are accepted but shown here as a free-form object:
                variables:
                  type: object
                  additionalProperties: { type: string }
          application/json:
            schema:
              type: object
              required: [token, ref]
              properties:
                token: { type: string }
                ref: { type: string }
                variables:
                  type: object
                  additionalProperties: { type: string }
                scenario_id: { type: integer }
                terminal_after_seconds: { type: integer }
                terminal_status: { type: string }
      responses:
        '201':
          description: Pipeline created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pipeline'
        '401':
          description: Unauthorized
        '422':
          description: Validation error
  /projects/{project_id}/pipelines/{pipeline_id}:
    get:
      summary: Get a pipeline by id
      security:
        - PrivateToken: []
        - Bearer: []
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/PipelineId'
      responses:
        '200':
          description: Pipeline found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pipeline'
        '401':
          description: Unauthorized
        '404':
          description: Not found
  /_mock/scenarios:
    get:
      summary: List scenarios
      security:
        - PrivateToken: []
        - Bearer: []
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Scenario' }
    post:
      summary: Create a scenario
      security:
        - PrivateToken: []
        - Bearer: []
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ScenarioCreate' }
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Scenario' }
  /_mock/scenarios/{scenario_id}:
    put:
      summary: Update a scenario
      security:
        - PrivateToken: []
        - Bearer: []
      parameters:
        - name: scenario_id
          in: path
          required: true
          schema: { type: integer }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ScenarioUpdate' }
      responses:
        '200':
          description: Updated
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Scenario' }
    delete:
      summary: Delete a scenario
      security:
        - PrivateToken: []
        - Bearer: []
      parameters:
        - name: scenario_id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '204':
          description: Deleted
  /_mock/pipelines:
    get:
      summary: List pipelines
      security:
        - PrivateToken: []
        - Bearer: []
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Pipeline' }
  /_mock/pipelines/{pipeline_id}:
    delete:
      summary: Delete a pipeline
      security:
        - PrivateToken: []
        - Bearer: []
      parameters:
        - $ref: '#/components/parameters/PipelineId'
      responses:
        '204':
          description: Deleted
```

---

## 2) Usage examples

### 2.1 Trigger a pipeline (form-encoded; GitLab-like)

```sh
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline"   -H "PRIVATE-TOKEN: MOCK_SUPER_SECRET"   -H "Content-Type: application/x-www-form-urlencoded"   --data-urlencode "token=TRIGGER_TOKEN_ABC"   --data-urlencode "ref=main"   --data-urlencode "variables[FOO]=bar"   --data-urlencode "variables[RUN_MODE]=smoke"   --data-urlencode "scenario_id=500"
```

### 2.2 Trigger a pipeline (JSON with mock controls)

```sh
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline"   -H "PRIVATE-TOKEN: MOCK_SUPER_SECRET"   -H "Content-Type: application/json"   -d '{
    "token": "TRIGGER_TOKEN_ABC",
    "ref": "main",
    "variables": { "FOO": "bar", "RUN_MODE": "smoke" },
    "terminal_after_seconds": 10,
    "terminal_status": "success"
  }'
```

### 2.3 Poll status

```sh
# Repeat until status != running
curl -s -H "PRIVATE-TOKEN: MOCK_SUPER_SECRET"   "http://localhost:8000/projects/123/pipelines/456789" | jq .status
```

### 2.4 Create a custom scenario

```sh
curl -s -X POST "http://localhost:8000/_mock/scenarios"   -H "PRIVATE-TOKEN: MOCK_SUPER_SECRET"   -H "Content-Type: application/json"   -d '{
    "scenario_id": 900,
    "name": "ten minutes then fail",
    "terminal_after_seconds": 600,
    "terminal_status": "failed",
    "never_complete": false
  }'
```

### 2.5 Delete a default scenario

```sh
curl -s -X DELETE "http://localhost:8000/_mock/scenarios/500"   -H "PRIVATE-TOKEN: MOCK_SUPER_SECRET"
```

---

## 3) Response shapes (examples)

### 3.1 Trigger response (`201`)

```json
{
  "id": 456789,
  "status": "running",
  "ref": "main",
  "sha": "7c3a1d5e",
  "web_url": "http://localhost:8000/projects/123/pipelines/456789",
  "source": "trigger",
  "created_at": "2025-09-21T10:00:00Z",
  "updated_at": "2025-09-21T10:00:00Z",
  "variables": { "FOO": "bar", "RUN_MODE": "smoke" },
  "scenario_id": 500,
  "terminal_after_seconds": 300,
  "terminal_status": "success"
}
```

### 3.2 Polling response while running (`200`)

```json
{
  "id": 456789,
  "status": "running",
  "ref": "main",
  "sha": "7c3a1d5e",
  "web_url": "http://localhost:8000/projects/123/pipelines/456789",
  "created_at": "2025-09-21T10:00:00Z",
  "updated_at": "2025-09-21T10:01:23Z",
  "variables": { "FOO": "bar", "RUN_MODE": "smoke" }
}
```

### 3.3 Polling response after terminal (`200`)

```json
{
  "id": 456789,
  "status": "success",
  "ref": "main",
  "sha": "7c3a1d5e",
  "web_url": "http://localhost:8000/projects/123/pipelines/456789",
  "created_at": "2025-09-21T10:00:00Z",
  "updated_at": "2025-09-21T10:05:00Z",
  "variables": { "FOO": "bar", "RUN_MODE": "smoke" }
}
```

---

## 4) Status vocabulary

Use one of the GitLab-like statuses for `terminal_status`:
- `success` (default), `failed`, `canceled`  
- Optional others if desired: `skipped`, `manual`, `scheduled`

`running` is the non‑terminal in this mock. (You can extend to include `pending`.)

---

## 5) Error model

- `401 Unauthorized` if token missing or invalid.
- `404 Not Found` if pipeline or scenario not found.
- `409 Conflict` if creating a scenario with an existing `scenario_id`.
- `422 Unprocessable Entity` for invalid payloads.


EOF
```

```sh
# cut
cat > README.md << 'EOF'
# README.md — Mock GitLab Pipeline Trigger Service

A small FastAPI + SQLite service that **mimics GitLab API v4** pipeline triggers and status polling, with extra control endpoints to script behavior for integration tests.

---

## Features

- POST `/projects/{id}/trigger/pipeline` returns a pipeline **id** and initial **status** (`running`).  
- GET `/projects/{id}/pipelines/{pipeline_id}` returns **`running`** until the configured duration elapses, after which it becomes a terminal status (default `success`).  
- Control namespace `/_mock/*` to create/update/delete **scenarios** and inspect/delete **pipelines**.
- Pre‑seeded scenarios: ID `0` (never completes), `1..99` seconds, `100` (1 min), `200` (2 min), `500` (5 min).
- Hard‑coded auth token (env `MOCK_TOKEN`, default `MOCK_SUPER_SECRET`).

---

## Quick start

### 1) Create & seed the database

```sh
# cut
cat > schema.sql << 'EOF'
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  terminal_after_seconds INTEGER,
  terminal_status TEXT NOT NULL DEFAULT 'success',
  never_complete INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipelines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  ref TEXT NOT NULL,
  sha TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  variables_json TEXT,
  scenario_id INTEGER,
  terminal_after_seconds INTEGER,
  terminal_status TEXT,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  FOREIGN KEY(scenario_id) REFERENCES scenarios(scenario_id) ON DELETE SET NULL
);
EOF
# EOF
```

```sh
# cut
cat > seed_defaults.sql << 'EOF'
INSERT OR REPLACE INTO scenarios (scenario_id, name, terminal_after_seconds, terminal_status, never_complete) VALUES
  (0, 'never complete', NULL, 'success', 1),
  (1, 'after 1 second', 1, 'success', 0),
  (2, 'after 2 seconds', 2, 'success', 0),
  (3, 'after 3 seconds', 3, 'success', 0),
  (4, 'after 4 seconds', 4, 'success', 0),
  (5, 'after 5 seconds', 5, 'success', 0),
  (10, 'after 10 seconds', 10, 'success', 0),
  (30, 'after 30 seconds', 30, 'success', 0),
  (60, 'after 60 seconds', 60, 'success', 0),
  (100, 'after 1 minute', 60, 'success', 0),
  (200, 'after 2 minutes', 120, 'success', 0),
  (500, 'after 5 minutes', 300, 'success', 0);
EOF
# EOF
```

```sh
sqlite3 mock.db < schema.sql
sqlite3 mock.db < seed_defaults.sql
```

### 2) Run the service (example)

> **Note:** You said *do not code yet*, so this is illustrative. Replace with your actual FastAPI `app.py` later.

```sh
export MOCK_TOKEN=MOCK_SUPER_SECRET
uvicorn app:app --reload --port 8000
```

---

## How to use

### Trigger and poll (happy path: 5 minutes)

```sh
# Trigger with preset scenario 500 (5 minutes → success)
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline"   -H "PRIVATE-TOKEN: ${MOCK_TOKEN}"   -H "Content-Type: application/x-www-form-urlencoded"   --data-urlencode "token=TRIGGER_TOKEN_ABC"   --data-urlencode "ref=main"   --data-urlencode "scenario_id=500" | jq .id
```

```sh
# Poll
curl -s -H "PRIVATE-TOKEN: ${MOCK_TOKEN}"   "http://localhost:8000/projects/123/pipelines/<ID_FROM_ABOVE>" | jq .status
```

### Make one that never completes

```sh
curl -s -X POST "http://localhost:8000/projects/123/trigger/pipeline"   -H "PRIVATE-TOKEN: ${MOCK_TOKEN}"   -H "Content-Type: application/json"   -d '{ "token":"T", "ref":"main", "scenario_id": 0 }'
```

### Create a failing scenario

```sh
curl -s -X POST "http://localhost:8000/_mock/scenarios"   -H "PRIVATE-TOKEN: ${MOCK_TOKEN}"   -H "Content-Type: application/json"   -d '{ "scenario_id": 900, "name": "fail in 3m", "terminal_after_seconds": 180, "terminal_status": "failed", "never_complete": false }'
```

---

## Auth

Send `PRIVATE-TOKEN: MOCK_SUPER_SECRET` or `Authorization: Bearer MOCK_SUPER_SECRET` with every request.

---

## Notes on parity with GitLab v4

- Real GitLab **trigger** endpoint is `POST /projects/:id/trigger/pipeline` with `token`, `ref`, and optional `variables[KEY]=VALUE` form params.
- The **trigger response** includes a pipeline `id` and a `status` at creation time; clients then **poll** `GET /projects/:id/pipelines/:pipeline_id` for updated status.
- Our mock mirrors that shape and adds `/_mock/*` controls for testing.

---

## Sources / References

- GitLab **API v4** documentation: *Pipelines*, *Pipeline triggers* (official).  
- **OpenAPI 3.0** Specification (for the mock’s contract).


EOF
```

