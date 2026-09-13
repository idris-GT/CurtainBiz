from fastapi.testclient import TestClient

from app.server import app


client = TestClient(app)


PROTECTED_GET_ENDPOINTS = [
    "/customers/",
    "/products/",
    "/employees/",
    "/departments/",
    "/materials/",
    "/inventory/",
    "/stock-transactions/",
    "/quotations/",
    "/orders/",
    "/order-items/",
    "/production/",
    "/production-tasks/",
    "/deliveries/",
    "/payments/",
    "/queries/",
    "/notifications/",
    "/activity-logs/",
    "/roles/",
    "/permissions/",
    "/role-permissions/me",
    "/user-roles/00000000-0000-0000-0000-000000000000",
    "/ml/sales-intelligence",
    "/ml/inventory-intelligence",
    "/ml/production-intelligence",
    "/ml/delivery-intelligence",
    "/ml/accounts-intelligence",
    "/ml/admin-intelligence",
]


def test_all_major_business_get_endpoints_require_authentication():
    """
    Every major business GET endpoint must reject unauthenticated
    requests.

    This test intentionally does not use a real token and therefore
    does not modify or depend on business data.
    """

    for endpoint in PROTECTED_GET_ENDPOINTS:
        response = client.get(endpoint)

        assert response.status_code in (401, 403), (
            f"{endpoint} unexpectedly allowed unauthenticated access: "
            f"{response.status_code} {response.text}"
        )


def test_business_api_rejects_malformed_integer_id():
    """
    Integer-based resource endpoints should reject invalid path IDs.
    """

    endpoints = [
        "/customers/not-an-id",
        "/products/not-an-id",
        "/orders/not-an-id",
        "/quotations/not-an-id",
        "/production/not-an-id",
        "/deliveries/not-an-id",
        "/payments/not-an-id",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code in (401, 403, 422), (
            f"{endpoint} returned unexpected status "
            f"{response.status_code}: {response.text}"
        )


def test_business_api_does_not_allow_unauthenticated_customer_creation():
    """
    Customer creation must require authentication/RBAC.
    """

    response = client.post(
        "/customers/",
        json={
            "customer_code": "TEST-SECURITY-001",
            "name": "Security Test Customer",
            "email": "security-test@example.com",
            "phone": "0000000000",
            "address": "Security Test Address",
            "city": "Test City",
            "state": "Test State",
        },
    )

    assert response.status_code in (401, 403)


def test_business_api_does_not_allow_unauthenticated_product_creation():
    """
    Product creation must require authentication/RBAC.
    """

    response = client.post(
        "/products/",
        json={
            "product_code": "TEST-SECURITY-001",
            "name": "Security Test Product",
            "category": "Security Test",
            "description": "Should never be created",
            "unit": "piece",
            "selling_price": "1.00",
            "is_active": True,
        },
    )

    assert response.status_code in (401, 403)


def test_business_api_does_not_allow_unauthenticated_customer_update():
    """
    Customer updates must require authentication/RBAC.
    """

    response = client.put(
        "/customers/1",
        json={
            "customer_code": "TEST-SECURITY-UPDATE",
            "name": "Unauthorized Update",
            "email": "security@example.com",
            "phone": "0000000000",
            "address": "Unauthorized",
            "city": "Test",
            "state": "Test",
        },
    )

    assert response.status_code in (401, 403)


def test_business_api_does_not_allow_unauthenticated_product_update():
    """
    Product updates must require authentication/RBAC.
    """

    response = client.put(
        "/products/1",
        json={
            "product_code": "TEST-SECURITY-UPDATE",
            "name": "Unauthorized Update",
            "category": "Security Test",
            "description": "Should never be updated",
            "unit": "piece",
            "selling_price": "1.00",
            "is_active": True,
        },
    )

    assert response.status_code in (401, 403)


def test_business_api_does_not_allow_unauthenticated_customer_delete():
    """
    Customer deletion must require authentication/RBAC.
    """

    response = client.delete("/customers/1")

    assert response.status_code in (401, 403)


def test_business_api_does_not_allow_unauthenticated_product_delete():
    """
    Product deactivation must require authentication/RBAC.
    """

    response = client.delete("/products/1")

    assert response.status_code in (401, 403)