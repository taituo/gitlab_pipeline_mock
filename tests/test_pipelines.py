from __future__ import annotations

from datetime import timedelta

from app.models import Pipeline

AUTH_HEADERS = {"PRIVATE-TOKEN": "TEST_TOKEN"}


def test_trigger_and_poll_success(client, db_session):
    response = client.post(
        "/projects/123/trigger/pipeline",
        json={"token": "TRIGGER", "ref": "main", "scenario_id": 1},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "running"
    pipeline_id = payload["id"]

    pipeline = db_session.get(Pipeline, pipeline_id)
    assert pipeline is not None
    pipeline.created_at = pipeline.created_at - timedelta(seconds=5)
    db_session.add(pipeline)
    db_session.commit()

    poll = client.get(f"/projects/123/pipelines/{pipeline_id}", headers=AUTH_HEADERS)
    assert poll.status_code == 200
    assert poll.json()["status"] == "success"


def test_trigger_inline_terminal_settings(client):
    response = client.post(
        "/projects/555/trigger/pipeline",
        json={
            "token": "TRIGGER",
            "ref": "release",
            "variables": {"FOO": "bar"},
            "terminal_after_seconds": 0,
            "terminal_status": "failed",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    pipeline_id = response.json()["id"]

    poll = client.get(f"/projects/555/pipelines/{pipeline_id}", headers=AUTH_HEADERS)
    assert poll.status_code == 200
    assert poll.json()["status"] == "failed"
    assert poll.json()["terminal_status"] == "failed"


def test_trigger_form_payload(client):
    response = client.post(
        "/projects/24/trigger/pipeline",
        data={
            "token": "TRIGGER",
            "ref": "develop",
            "variables[FOO]": "bar",
            "terminal_after_seconds": "0",
            "terminal_status": "success",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["variables"] == {"FOO": "bar"}
    assert payload["status"] == "running"


def test_pipeline_list_and_delete(client):
    list_before = client.get("/_mock/pipelines", headers=AUTH_HEADERS)
    assert list_before.status_code == 200
    assert list_before.json() == []

    created = client.post(
        "/projects/1/trigger/pipeline",
        json={"token": "T", "ref": "main", "scenario_id": 0},
        headers=AUTH_HEADERS,
    )
    assert created.status_code == 201
    pipeline_id = created.json()["id"]

    listed = client.get("/_mock/pipelines", headers=AUTH_HEADERS)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(f"/_mock/pipelines/{pipeline_id}", headers=AUTH_HEADERS)
    assert deleted.status_code == 204

    list_after = client.get("/_mock/pipelines", headers=AUTH_HEADERS)
    assert list_after.status_code == 200
    assert list_after.json() == []


def test_scenario_crud(client):
    new_payload = {
        "scenario_id": 900,
        "name": "fail in 3m",
        "terminal_after_seconds": 180,
        "terminal_status": "failed",
        "never_complete": False,
    }

    created = client.post("/_mock/scenarios", json=new_payload, headers=AUTH_HEADERS)
    assert created.status_code == 201
    assert created.json()["scenario_id"] == 900

    updated_payload = new_payload | {"terminal_status": "canceled"}
    updated = client.put("/_mock/scenarios/900", json=updated_payload, headers=AUTH_HEADERS)
    assert updated.status_code == 200
    assert updated.json()["terminal_status"] == "canceled"

    scenarios = client.get("/_mock/scenarios", headers=AUTH_HEADERS)
    assert scenarios.status_code == 200
    assert any(item["scenario_id"] == 900 for item in scenarios.json())

    deleted = client.delete("/_mock/scenarios/900", headers=AUTH_HEADERS)
    assert deleted.status_code == 204

    scenarios_after = client.get("/_mock/scenarios", headers=AUTH_HEADERS)
    assert all(item["scenario_id"] != 900 for item in scenarios_after.json())
