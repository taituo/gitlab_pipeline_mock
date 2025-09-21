from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Scenario


def _default_scenarios() -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = [
        {"scenario_id": 0, "name": "never complete", "terminal_after_seconds": None, "terminal_status": "success", "never_complete": True}
    ]

    for i in range(1, 100):
        payloads.append(
            {
                "scenario_id": i,
                "name": f"after {i} second{'s' if i != 1 else ''}",
                "terminal_after_seconds": i,
                "terminal_status": "success",
                "never_complete": False,
            }
        )

    payloads.extend(
        [
            {"scenario_id": 100, "name": "after 1 minute", "terminal_after_seconds": 60, "terminal_status": "success", "never_complete": False},
            {"scenario_id": 200, "name": "after 2 minutes", "terminal_after_seconds": 120, "terminal_status": "success", "never_complete": False},
            {"scenario_id": 500, "name": "after 5 minutes", "terminal_after_seconds": 300, "terminal_status": "success", "never_complete": False},
        ]
    )

    return payloads


def seed_scenarios(session: Session) -> None:
    existing_ids = {row[0] for row in session.execute(select(Scenario.scenario_id))}
    for payload in _default_scenarios():
        if payload["scenario_id"] not in existing_ids:
            session.add(Scenario(**payload))
    session.commit()
