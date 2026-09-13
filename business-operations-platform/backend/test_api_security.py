import os

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import get_current_user, require_permission
from app.server import app


client = TestClient(app)


def test_health_endpoint_is_public():
    """
    The health endpoint should be accessible without authentication.
    """

    response = client.get("/health")

    assert response.status_code == 200


def test_protected_endpoint_rejects_missing_token():
    """
    Protected endpoints must reject requests without a JWT.
    """

    response = client.get("/ml/sales-intelligence")

    assert response.status_code in (401, 403)


def test_protected_endpoint_rejects_invalid_token(monkeypatch):
    """
    An invalid JWT must result in HTTP 401.
    """

    def fake_get_signing_key_from_jwt(token):
        raise Exception("Invalid token")

    monkeypatch.setattr(
        "app.auth.jwks_client.get_signing_key_from_jwt",
        fake_get_signing_key_from_jwt,
    )

    response = client.get(
        "/ml/sales-intelligence",
        headers={
            "Authorization": "Bearer definitely-invalid-token"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired authentication token"
    )


def test_protected_customer_endpoint_rejects_missing_token():
    """
    Customer APIs must also require authentication.
    """

    response = client.get("/customers")

    assert response.status_code in (401, 403)


def test_protected_inventory_endpoint_rejects_missing_token():
    """
    Inventory APIs must require authentication.
    """

    response = client.get("/inventory")

    assert response.status_code in (401, 403)


def test_protected_orders_endpoint_rejects_missing_token():
    """
    Order APIs must require authentication.
    """

    response = client.get("/orders")

    assert response.status_code in (401, 403)


def test_protected_reports_endpoint_rejects_missing_token():
    """
    Report APIs must require authentication.
    """

    response = client.get("/ml/admin-intelligence")

    assert response.status_code in (401, 403)


def test_login_returns_500_when_supabase_configuration_is_missing(
    monkeypatch,
):
    """
    Login must fail safely if Supabase configuration is unavailable.
    """

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Supabase configuration is missing"
    )


def test_permission_checker_denies_missing_permission(monkeypatch):
    """
    RBAC must deny access when the current user does not have
    the requested permission.
    """

    class FakeCursor:
        def execute(self, query, params):
            self.params = params

        def fetchone(self):
            return None

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        "app.auth.get_connection",
        lambda: FakeConnection(),
    )

    permission_checker = require_permission("reports.view")

    with pytest.raises(Exception) as exc_info:
        permission_checker(
            current_user={
                "user_id": "test-user-id",
                "email": "test@example.com",
            }
        )

    exception = exc_info.value

    assert getattr(exception, "status_code", None) == 403
    assert getattr(exception, "detail", None) == (
        "Permission required: reports.view"
    )


def test_permission_checker_allows_existing_permission(monkeypatch):
    """
    RBAC must allow access when the requested permission exists.
    """

    class FakeCursor:
        def execute(self, query, params):
            self.params = params

        def fetchone(self):
            return (1,)

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        "app.auth.get_connection",
        lambda: FakeConnection(),
    )

    permission_checker = require_permission("reports.view")

    current_user = {
        "user_id": "test-user-id",
        "email": "test@example.com",
    }

    result = permission_checker(
        current_user=current_user
    )

    assert result == current_user


def test_login_requires_email_and_password():
    """
    Login must reject malformed requests that do not contain
    the required credentials.
    """

    response = client.post(
        "/auth/login",
        json={},
    )

    assert response.status_code == 422