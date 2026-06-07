import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/mmas_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.testclient import TestClient

from app.main import app
from app.core.database import get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_db_not_found():
    async def override_get_db():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
