from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    scenario_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    terminal_after_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    terminal_status: Mapped[str] = mapped_column(String, nullable=False, default="success")
    never_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    pipelines: Mapped[list["Pipeline"]] = relationship(back_populates="scenario")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ref: Mapped[str] = mapped_column(String, nullable=False)
    sha: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    variables_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("scenarios.scenario_id", ondelete="SET NULL"), nullable=True)
    terminal_after_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    terminal_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    scenario: Mapped[Optional[Scenario]] = relationship(back_populates="pipelines")
