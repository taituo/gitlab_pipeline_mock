from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MOCK_TOKEN", "TEST_TOKEN")

    from app.config import get_settings

    get_settings.cache_clear()

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(client) -> Generator:  # type: ignore[override]
    from app.database import get_session_factory

    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
