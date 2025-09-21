from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..auth import require_token
from ..database import get_db
from ..models import Pipeline, Scenario
from ..schemas import ScenarioCreate, ScenarioList, ScenarioUpdate

router = APIRouter(prefix="/_mock/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioList])
def list_scenarios(
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> list[ScenarioList]:
    scenarios = list(db.execute(select(Scenario)).scalars())
    return [ScenarioList.model_validate(scenario) for scenario in scenarios]


@router.post("", response_model=ScenarioList, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario: ScenarioCreate,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> ScenarioList:
    existing = db.get(Scenario, scenario.scenario_id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scenario already exists")

    db_scenario = Scenario(**scenario.model_dump())
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return ScenarioList.model_validate(db_scenario)


@router.put("/{scenario_id}", response_model=ScenarioList)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> ScenarioList:
    if scenario_id != payload.scenario_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Scenario ID mismatch")

    db_scenario = db.get(Scenario, scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    for field, value in payload.model_dump().items():
        setattr(db_scenario, field, value)

    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return ScenarioList.model_validate(db_scenario)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_scenario(
    scenario_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
) -> Response:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    db.execute(update(Pipeline).where(Pipeline.scenario_id == scenario_id).values(scenario_id=None))
    db.delete(scenario)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
