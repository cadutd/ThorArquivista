import pytest
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def require_isolated_databases():
    assert settings.database_url.rsplit("/", 1)[-1].endswith("_test"), "Use PostgreSQL de teste isolado."
    assert settings.mongodb_database.endswith("_test"), "Use MongoDB de teste isolado."
