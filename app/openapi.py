from __future__ import annotations

from fastapi import FastAPI


def _pipeline_schema() -> dict:
    return {
        "type": "object",
        "required": ["id", "project_id", "ref", "sha", "status", "created_at", "updated_at"],
        "properties": {
            "id": {"type": "integer", "example": 101},
            "project_id": {"type": "integer", "example": 123},
            "ref": {"type": "string", "example": "main"},
            "sha": {"type": "string", "example": "deadbeefcafebabe"},
            "status": {"type": "string", "example": "running"},
            "web_url": {"type": "string", "example": "http://localhost:8000/projects/123/pipelines/101"},
            "source": {"type": "string", "example": "trigger"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
            "variables": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "example": {"FOO": "bar"},
            },
            "scenario_id": {"type": "integer", "nullable": True},
            "terminal_after_seconds": {"type": "integer", "nullable": True},
            "terminal_status": {"type": "string", "nullable": True, "example": "success"},
        },
    }


def _scenario_schema() -> dict:
    return {
        "type": "object",
        "required": ["scenario_id", "name", "terminal_status", "never_complete"],
        "properties": {
            "scenario_id": {"type": "integer", "example": 500},
            "name": {"type": "string", "example": "after 5 minutes"},
            "terminal_after_seconds": {"type": "integer", "nullable": True, "example": 300},
            "terminal_status": {"type": "string", "example": "success"},
            "never_complete": {"type": "boolean", "example": False},
        },
    }


def _trigger_request_schema() -> dict:
    return {
        "type": "object",
        "required": ["token", "ref"],
        "properties": {
            "token": {"type": "string", "example": "TRIGGER_TOKEN"},
            "ref": {"type": "string", "example": "main"},
            "variables": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "example": {"DEPLOY_ENV": "staging"},
            },
            "scenario_id": {"type": "integer", "nullable": True, "example": 5},
            "terminal_after_seconds": {"type": "integer", "nullable": True, "example": 300},
            "terminal_status": {"type": "string", "nullable": True, "example": "failed"},
        },
    }


def build_openapi_schema() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Mock GitLab Pipeline Trigger Service",
            "version": "1.0.0",
            "description": "FastAPI mock for GitLab pipeline trigger & control endpoints.",
        },
        "servers": [{"url": "http://localhost:8000"}],
        "components": {
            "securitySchemes": {
                "PrivateToken": {"type": "apiKey", "in": "header", "name": "PRIVATE-TOKEN"},
                "Bearer": {"type": "http", "scheme": "bearer"},
            },
            "schemas": {
                "Pipeline": _pipeline_schema(),
                "Scenario": _scenario_schema(),
                "TriggerRequest": _trigger_request_schema(),
            },
        },
        "paths": {
            "/projects/{project_id}/trigger/pipeline": {
                "post": {
                    "summary": "Trigger pipeline",
                    "tags": ["pipelines"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "parameters": [
                        {
                            "name": "project_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/TriggerRequest"}},
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "required": ["token", "ref"],
                                    "properties": {
                                        "token": {"type": "string"},
                                        "ref": {"type": "string"},
                                        "scenario_id": {"type": "integer", "nullable": True},
                                        "terminal_after_seconds": {"type": "integer", "nullable": True},
                                        "terminal_status": {"type": "string", "nullable": True},
                                        "variables[KEY]": {"type": "string", "description": "Repeatable variable entries."},
                                    },
                                }
                            },
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Pipeline triggered",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pipeline"}
                                }
                            },
                        },
                        "404": {"description": "Scenario not found"},
                        "422": {"description": "Validation error"},
                    },
                }
            },
            "/projects/{project_id}/pipelines/{pipeline_id}": {
                "get": {
                    "summary": "Get pipeline",
                    "tags": ["pipelines"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "parameters": [
                        {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                        {"name": "pipeline_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Pipeline retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pipeline"}
                                }
                            },
                        },
                        "404": {"description": "Pipeline not found"},
                    },
                }
            },
            "/_mock/pipelines": {
                "get": {
                    "summary": "List pipelines",
                    "tags": ["pipelines"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "responses": {
                        "200": {
                            "description": "List of pipelines",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Pipeline"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/_mock/pipelines/{pipeline_id}": {
                "delete": {
                    "summary": "Delete pipeline",
                    "tags": ["pipelines"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "parameters": [
                        {"name": "pipeline_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"204": {"description": "Deleted"}, "404": {"description": "Not found"}},
                }
            },
            "/_mock/scenarios": {
                "get": {
                    "summary": "List scenarios",
                    "tags": ["scenarios"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "responses": {
                        "200": {
                            "description": "Scenario list",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Scenario"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create scenario",
                    "tags": ["scenarios"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Scenario"}}
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Scenario created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Scenario"}
                                }
                            },
                        },
                        "409": {"description": "Scenario already exists"},
                    },
                },
            },
            "/_mock/scenarios/{scenario_id}": {
                "put": {
                    "summary": "Update scenario",
                    "tags": ["scenarios"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "parameters": [
                        {"name": "scenario_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Scenario"}}
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Scenario updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Scenario"}
                                }
                            },
                        },
                        "404": {"description": "Scenario not found"},
                        "422": {"description": "ID mismatch"},
                    },
                },
                "delete": {
                    "summary": "Delete scenario",
                    "tags": ["scenarios"],
                    "security": [{"PrivateToken": []}, {"Bearer": []}],
                    "parameters": [
                        {"name": "scenario_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"204": {"description": "Deleted"}, "404": {"description": "Not found"}},
                },
            },
        },
    }


def attach_custom_openapi(app: FastAPI) -> None:
    def _custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = build_openapi_schema()
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = _custom_openapi  # type: ignore[assignment]
