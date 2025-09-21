from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Dict, Optional

from .models import Pipeline, Scenario


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_fake_sha() -> str:
    return secrets.token_hex(20)


def serialise_variables(variables: Dict[str, str] | None) -> str | None:
    if not variables:
        return None
    return json.dumps(variables, sort_keys=True)


def deserialise_variables(raw: str | None) -> Dict[str, str]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return {str(k): str(v) for k, v in payload.items()}
    return {}


def compute_effective_settings(pipeline: Pipeline) -> tuple[Optional[int], str, bool]:
    scenario: Optional[Scenario] = pipeline.scenario
    if scenario is not None:
        return scenario.terminal_after_seconds, scenario.terminal_status, scenario.never_complete

    terminal_after = pipeline.terminal_after_seconds
    terminal_status = pipeline.terminal_status or "success"
    never_complete = False
    return terminal_after, terminal_status, never_complete


def compute_status(pipeline: Pipeline, reference_time: datetime | None = None) -> str:
    terminal_after, terminal_status, never_complete = compute_effective_settings(pipeline)

    if never_complete:
        return "running"

    reference_time = reference_time or now_utc()
    created_at = pipeline.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    elapsed = (reference_time - created_at).total_seconds()

    if terminal_after is None:
        return terminal_status

    if elapsed >= terminal_after:
        return terminal_status
    return "running"


def update_pipeline_status(pipeline: Pipeline, reference_time: datetime | None = None) -> None:
    pipeline.status = compute_status(pipeline, reference_time=reference_time)
    pipeline.updated_at = now_utc()


def pipeline_to_dict(pipeline: Pipeline, base_url: str) -> Dict[str, object]:
    terminal_after, terminal_status, _ = compute_effective_settings(pipeline)
    return {
        "id": pipeline.id,
        "project_id": pipeline.project_id,
        "ref": pipeline.ref,
        "sha": pipeline.sha,
        "status": pipeline.status,
        "web_url": f"{base_url}/projects/{pipeline.project_id}/pipelines/{pipeline.id}",
        "source": "trigger",
        "created_at": pipeline.created_at,
        "updated_at": pipeline.updated_at,
        "variables": deserialise_variables(pipeline.variables_json),
        "scenario_id": pipeline.scenario_id,
        "terminal_after_seconds": terminal_after,
        "terminal_status": terminal_status,
    }
