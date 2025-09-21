from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_token
from ..database import get_db
from ..logic import (
    generate_fake_sha,
    now_utc,
    pipeline_to_dict,
    serialise_variables,
    update_pipeline_status,
)
from ..models import Pipeline, Scenario
from ..schemas import Pipeline as PipelineSchema

router = APIRouter(tags=["pipelines"])


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


async def _parse_trigger_body(request: Request) -> Dict[str, object]:
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON payload")
        variables = payload.get("variables") or {}
        if not isinstance(variables, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="variables must be an object")
        return {
            "token": payload.get("token"),
            "ref": payload.get("ref"),
            "variables": {str(k): str(v) for k, v in variables.items()},
            "scenario_id": payload.get("scenario_id"),
            "terminal_after_seconds": payload.get("terminal_after_seconds"),
            "terminal_status": payload.get("terminal_status"),
        }

    form = await request.form()
    variables: Dict[str, str] = {}
    simple_fields: Dict[str, object] = {}

    for key, value in form.multi_items():
        if key.startswith("variables[") and key.endswith("]"):
            var_key = key[len("variables[") : -1]
            variables[var_key] = str(value)
        elif key == "variables" and isinstance(value, str):
            variables = {"value": value}
        else:
            simple_fields[key] = value

    return {
        "token": simple_fields.get("token"),
        "ref": simple_fields.get("ref"),
        "variables": variables,
        "scenario_id": simple_fields.get("scenario_id"),
        "terminal_after_seconds": simple_fields.get("terminal_after_seconds"),
        "terminal_status": simple_fields.get("terminal_status"),
    }


def _ensure_int(value: object, field: str) -> Optional[int]:
    if value in (None, "", b""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} must be an integer") from None


@router.post(
    "/projects/{project_id}/trigger/pipeline",
    response_model=PipelineSchema,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_pipeline(
    project_id: int,
    request: Request,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> PipelineSchema:
    payload = await _parse_trigger_body(request)

    token = payload.get("token")
    ref = payload.get("ref")

    if not token or not ref:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="token and ref are required")

    scenario_id = payload.get("scenario_id")
    terminal_after_seconds = payload.get("terminal_after_seconds")
    terminal_status = payload.get("terminal_status")

    scenario = None
    if scenario_id not in (None, "", b""):
        scenario_id_int = _ensure_int(scenario_id, "scenario_id")
        scenario = db.get(Scenario, scenario_id_int)
        if scenario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        terminal_after_seconds = None
        terminal_status = None
    else:
        scenario_id_int = None
        terminal_after_seconds = _ensure_int(terminal_after_seconds, "terminal_after_seconds")
        terminal_status = str(terminal_status) if terminal_status not in (None, "", b"") else None

    variables = payload.get("variables")
    if not isinstance(variables, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="variables must be a mapping")

    created_at = now_utc()
    pipeline = Pipeline(
        project_id=project_id,
        ref=str(ref),
        sha=generate_fake_sha(),
        status="running",
        variables_json=serialise_variables({str(k): str(v) for k, v in variables.items()}),
        scenario_id=scenario_id_int,
        terminal_after_seconds=terminal_after_seconds,
        terminal_status=terminal_status,
        created_at=created_at,
        updated_at=created_at,
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    base_url = _base_url(request)
    return PipelineSchema.model_validate(pipeline_to_dict(pipeline, base_url=base_url))


@router.get(
    "/projects/{project_id}/pipelines/{pipeline_id}",
    response_model=PipelineSchema,
)
def get_pipeline(
    project_id: int,
    pipeline_id: int,
    request: Request,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> PipelineSchema:
    stmt = select(Pipeline).where(Pipeline.id == pipeline_id, Pipeline.project_id == project_id)
    pipeline = db.execute(stmt).scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    update_pipeline_status(pipeline)
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    base_url = _base_url(request)
    return PipelineSchema.model_validate(pipeline_to_dict(pipeline, base_url=base_url))


@router.get(
    "/_mock/pipelines",
    response_model=list[PipelineSchema],
)
def list_pipelines(
    request: Request,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> list[PipelineSchema]:
    pipelines = list(db.execute(select(Pipeline)).scalars())
    base_url = _base_url(request)

    responses: list[PipelineSchema] = []
    for pipeline in pipelines:
        update_pipeline_status(pipeline)
        db.add(pipeline)
        responses.append(PipelineSchema.model_validate(pipeline_to_dict(pipeline, base_url=base_url)))

    db.commit()
    for pipeline in pipelines:
        db.refresh(pipeline)

    return responses


@router.delete(
    "/_mock/pipelines/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pipeline(
    pipeline_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> None:
    pipeline = db.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    db.delete(pipeline)
    db.commit()
