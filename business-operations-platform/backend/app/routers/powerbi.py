import os

from fastapi import APIRouter, Header, HTTPException

from app.database.connection import get_connection


router = APIRouter(
    prefix="/powerbi",
    tags=["Power BI"]
)


# ==========================================================
# POWER BI API AUTHENTICATION
# ==========================================================

def verify_powerbi_key(
    x_powerbi_key: str | None = Header(default=None)
):
    expected_key = os.getenv("POWERBI_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Power BI API key is not configured."
        )

    if not x_powerbi_key or x_powerbi_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid Power BI API key."
        )


# ==========================================================
# SALES
# ==========================================================

@router.get("/sales")
def get_sales(
    x_powerbi_key: str | None = Header(default=None)
):
    verify_powerbi_key(x_powerbi_key)

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


# ==========================================================
# ORDERS
# ==========================================================

@router.get("/orders")
def get_orders(
    x_powerbi_key: str | None = Header(default=None)
):
    verify_powerbi_key(x_powerbi_key)

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


# ==========================================================
# PAYMENTS
# ==========================================================

@router.get("/payments")
def get_payments(
    x_powerbi_key: str | None = Header(default=None)
):
    verify_powerbi_key(x_powerbi_key)

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


# ==========================================================
# PRODUCTION
# ==========================================================

@router.get("/production")
def get_production(
    x_powerbi_key: str | None = Header(default=None)
):
    verify_powerbi_key(x_powerbi_key)

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


# ==========================================================
# DELIVERIES
# ==========================================================

@router.get("/deliveries")
def get_deliveries(
    x_powerbi_key: str | None = Header(default=None)
):
    verify_powerbi_key(x_powerbi_key)

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