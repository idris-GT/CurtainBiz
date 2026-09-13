import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

from app.auth import require_permission
from app.database.connection import get_connection


load_dotenv()


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


# ---------------------------------------------------------
# Power BI read-only authentication
# ---------------------------------------------------------

powerbi_security = HTTPBasic()


def require_powerbi_access(
    credentials: HTTPBasicCredentials = Depends(powerbi_security)
):
    expected_username = os.getenv("POWERBI_USERNAME")
    expected_password = os.getenv("POWERBI_PASSWORD")

    if not expected_username or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Power BI authentication is not configured"
        )

    username_ok = secrets.compare_digest(
        credentials.username,
        expected_username
    )

    password_ok = secrets.compare_digest(
        credentials.password,
        expected_password
    )

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Power BI credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


# ---------------------------------------------------------
# Normal authenticated analytics endpoints
# ---------------------------------------------------------

@router.get("/sales")
def get_sales_analytics(
    current_user=Depends(require_permission("reports.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(order_date) AS date,
                COUNT(*) AS order_count,
                COALESCE(SUM(total_amount), 0) AS revenue,
                COALESCE(AVG(total_amount), 0) AS average_order_value
            FROM orders
            GROUP BY DATE(order_date)
            ORDER BY DATE(order_date);
        """)

        rows = cursor.fetchall()

        return [
            {
                "date": row[0],
                "order_count": row[1],
                "revenue": float(row[2] or 0),
                "average_order_value": float(row[3] or 0),
            }
            for row in rows
        ]

    finally:
        connection.close()


@router.get("/orders")
def get_order_analytics(
    current_user=Depends(require_permission("reports.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(order_date) AS date,
                status,
                COUNT(*) AS order_count,
                COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders
            GROUP BY
                DATE(order_date),
                status
            ORDER BY
                DATE(order_date),
                status;
        """)

        rows = cursor.fetchall()

        return [
            {
                "date": row[0],
                "status": row[1],
                "order_count": row[2],
                "revenue": float(row[3] or 0),
            }
            for row in rows
        ]

    finally:
        connection.close()


@router.get("/payments")
def get_payment_analytics(
    current_user=Depends(require_permission("reports.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(payment_date) AS date,
                status,
                COUNT(*) AS payment_count,
                COALESCE(SUM(amount), 0) AS cash_inflow
            FROM payments
            GROUP BY
                DATE(payment_date),
                status
            ORDER BY
                DATE(payment_date),
                status;
        """)

        rows = cursor.fetchall()

        return [
            {
                "date": row[0],
                "status": row[1],
                "payment_count": row[2],
                "cash_inflow": float(row[3] or 0),
            }
            for row in rows
        ]

    finally:
        connection.close()


@router.get("/production")
def get_production_analytics(
    current_user=Depends(require_permission("reports.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(start_date) AS date,
                status,
                COUNT(*) AS production_count
            FROM production
            GROUP BY
                DATE(start_date),
                status
            ORDER BY
                DATE(start_date),
                status;
        """)

        rows = cursor.fetchall()

        return [
            {
                "date": row[0],
                "status": row[1],
                "production_count": row[2],
            }
            for row in rows
        ]

    finally:
        connection.close()


@router.get("/deliveries")
def get_delivery_analytics(
    current_user=Depends(require_permission("reports.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(scheduled_date) AS date,
                status,
                COUNT(*) AS delivery_count
            FROM deliveries
            GROUP BY
                DATE(scheduled_date),
                status
            ORDER BY
                DATE(scheduled_date),
                status;
        """)

        rows = cursor.fetchall()

        return [
            {
                "date": row[0],
                "status": row[1],
                "delivery_count": row[2],
            }
            for row in rows
        ]

    finally:
        connection.close()


# ---------------------------------------------------------
# Power BI dedicated read-only endpoints
# ---------------------------------------------------------

@router.get("/powerbi/sales")
def get_powerbi_sales(
    authenticated=Depends(require_powerbi_access)
):
    return get_sales_analytics.__wrapped__() if hasattr(
        get_sales_analytics,
        "__wrapped__"
    ) else _sales_data()


@router.get("/powerbi/orders")
def get_powerbi_orders(
    authenticated=Depends(require_powerbi_access)
):
    return _orders_data()


@router.get("/powerbi/payments")
def get_powerbi_payments(
    authenticated=Depends(require_powerbi_access)
):
    return _payments_data()


@router.get("/powerbi/production")
def get_powerbi_production(
    authenticated=Depends(require_powerbi_access)
):
    return _production_data()


@router.get("/powerbi/deliveries")
def get_powerbi_deliveries(
    authenticated=Depends(require_powerbi_access)
):
    return _deliveries_data()


# ---------------------------------------------------------
# Shared database functions for Power BI
# ---------------------------------------------------------

def _sales_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(order_date),
                COUNT(*),
                COALESCE(SUM(total_amount), 0),
                COALESCE(AVG(total_amount), 0)
            FROM orders
            GROUP BY DATE(order_date)
            ORDER BY DATE(order_date);
        """)

        return [
            {
                "date": row[0],
                "order_count": row[1],
                "revenue": float(row[2] or 0),
                "average_order_value": float(row[3] or 0),
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def _orders_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(order_date),
                status,
                COUNT(*),
                COALESCE(SUM(total_amount), 0)
            FROM orders
            GROUP BY DATE(order_date), status
            ORDER BY DATE(order_date), status;
        """)

        return [
            {
                "date": row[0],
                "status": row[1],
                "order_count": row[2],
                "revenue": float(row[3] or 0),
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def _payments_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(payment_date),
                status,
                COUNT(*),
                COALESCE(SUM(amount), 0)
            FROM payments
            GROUP BY DATE(payment_date), status
            ORDER BY DATE(payment_date), status;
        """)

        return [
            {
                "date": row[0],
                "status": row[1],
                "payment_count": row[2],
                "cash_inflow": float(row[3] or 0),
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def _production_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(start_date),
                status,
                COUNT(*)
            FROM production
            GROUP BY DATE(start_date), status
            ORDER BY DATE(start_date), status;
        """)

        return [
            {
                "date": row[0],
                "status": row[1],
                "production_count": row[2],
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


def _deliveries_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(scheduled_date),
                status,
                COUNT(*)
            FROM deliveries
            GROUP BY DATE(scheduled_date), status
            ORDER BY DATE(scheduled_date), status;
        """)

        return [
            {
                "date": row[0],
                "status": row[1],
                "delivery_count": row[2],
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()