from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScenarioBase(BaseModel):
    scenario_id: int
    name: str
    terminal_after_seconds: Optional[int] = None
    terminal_status: str = Field(default="success")
    never_complete: bool = False

    model_config = ConfigDict(from_attributes=True)


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(ScenarioBase):
    pass


class ScenarioList(ScenarioBase):
    pass


class Pipeline(BaseModel):
    id: int
    project_id: int
    ref: str
    sha: str
    status: str
    web_url: str
    source: str = "trigger"
    created_at: datetime
    updated_at: datetime
    variables: Dict[str, str]
    scenario_id: Optional[int] = None
    terminal_after_seconds: Optional[int] = None
    terminal_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
