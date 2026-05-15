from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.deps import get_current_user_claims


async def _fake_current_user_claims() -> dict:
    return {
        "sub": "functional-test-user",
        "preferred_username": "functional-test-user",
        "realm_access": {"roles": ["admin"]},
    }


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user_claims] = _fake_current_user_claims
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unique_code() -> str:
    return uuid.uuid4().hex[:10]


def assert_validation_error(response) -> None:
    assert response.status_code == 422
    assert "detail" in response.json()


def missing_uuid() -> str:
    return "00000000-0000-4000-8000-000000000000"
