from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .database import Base, get_engine, init_engine, session_scope
from .routes import pipelines, scenarios
from .seeding import seed_scenarios


@asynccontextmanager
async def _lifespan(app: FastAPI):
    with session_scope() as session:
        seed_scenarios(session)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    init_engine(settings.database_url)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Mock GitLab Pipeline Trigger Service",
        version="1.0.0",
        description="FastAPI mock for GitLab pipeline trigger & control endpoints.",
        lifespan=_lifespan,
    )

    app.include_router(pipelines.router)
    app.include_router(scenarios.router)

    return app


app = create_app()
