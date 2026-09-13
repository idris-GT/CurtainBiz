import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_current_user_role
from app.database.connection import get_connection

from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.employees import router as employees_router
from app.routers.departments import router as departments_router
from app.routers.roles import router as roles_router
from app.routers.permissions import router as permissions_router
from app.routers.role_permissions import router as role_permissions_router
from app.routers.user_roles import router as user_roles_router
from app.routers.materials import router as materials_router
from app.routers.inventory import router as inventory_router
from app.routers.stock_transactions import router as stock_transactions_router
from app.routers.quotations import router as quotations_router
from app.routers.quotation_items import router as quotation_items_router
from app.routers.orders import router as orders_router
from app.routers.order_items import router as order_items_router
from app.routers.production import router as production_router
from app.routers.production_tasks import router as production_tasks_router
from app.routers.deliveries import router as deliveries_router
from app.routers.payments import router as payments_router
from app.routers.queries import router as queries_router
from app.routers.notifications import router as notifications_router
from app.routers.activity_logs import router as activity_logs_router
from app.routers import auth_login
from app.routers.ml import router as ml_router
from app.routers.analytics import router as analytics_router
from app.routers.powerbi import router as powerbi_router


# --------------------------------------------------
# APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Business Operations Platform API",
    version="1.0.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

configured_origins = os.getenv("FRONTEND_ORIGINS")

if configured_origins:
    allowed_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
else:
    allowed_origins = default_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


# --------------------------------------------------
# API ROUTERS
# --------------------------------------------------

app.include_router(customers_router)
app.include_router(products_router)
app.include_router(employees_router)
app.include_router(departments_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(role_permissions_router)
app.include_router(user_roles_router)
app.include_router(materials_router)
app.include_router(inventory_router)
app.include_router(stock_transactions_router)
app.include_router(quotations_router)
app.include_router(quotation_items_router)
app.include_router(orders_router)
app.include_router(order_items_router)
app.include_router(production_router)
app.include_router(production_tasks_router)
app.include_router(deliveries_router)
app.include_router(payments_router)
app.include_router(queries_router)
app.include_router(notifications_router)
app.include_router(activity_logs_router)
app.include_router(auth_login.router)
app.include_router(ml_router)
app.include_router(analytics_router)
app.include_router(powerbi_router)


# --------------------------------------------------
# BASIC ROUTES
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Business Operations Platform API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/database-test")
def database_test(
    current_user=Depends(get_current_user_role),
):
    """
    Authenticated database connectivity diagnostic.

    Internal database errors are intentionally not returned
    to the client.
    """

    connection = None

    try:
        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        cursor.close()

        return {
            "database": "connected",
            "result": result[0],
        }

    except Exception:
        return {
            "database": "connection_failed",
        }

    finally:
        if connection:
            connection.close()


@app.get("/auth-test")
def auth_test(
    current_user=Depends(get_current_user_role),
):
    return {
        "message": "Authentication successful",
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"],
    }