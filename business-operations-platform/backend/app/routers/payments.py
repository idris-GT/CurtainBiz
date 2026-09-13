from decimal import Decimal
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal
    payment_method: str
    payment_date: date
    reference_number: str
    status: str
    recorded_by: UUID
    notes: str | None = None


@router.get("/")
def get_payments(
    current_user=Depends(require_permission("payments.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.order_id,
                o.order_number,
                p.amount,
                p.payment_method,
                p.payment_date,
                p.reference_number,
                p.status,
                p.recorded_by,
                p.notes,
                p.created_at
            FROM payments p
            JOIN orders o
                ON p.order_id = o.id
            ORDER BY p.id;
        """)

        rows = cursor.fetchall()

        payments = []

        for row in rows:
            payments.append({
                "id": row[0],
                "order_id": row[1],
                "order_number": row[2],
                "amount": row[3],
                "payment_method": row[4],
                "payment_date": row[5],
                "reference_number": row[6],
                "status": row[7],
                "recorded_by": str(row[8]) if row[8] else None,
                "notes": row[9],
                "created_at": row[10]
            })

        return payments

    finally:
        connection.close()


@router.get("/{payment_id}")
def get_payment(
    payment_id: int,
    current_user=Depends(require_permission("payments.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.order_id,
                o.order_number,
                p.amount,
                p.payment_method,
                p.payment_date,
                p.reference_number,
                p.status,
                p.recorded_by,
                p.notes,
                p.created_at
            FROM payments p
            JOIN orders o
                ON p.order_id = o.id
            WHERE p.id = %s;
        """, (payment_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Payment not found"
            }

        return {
            "id": row[0],
            "order_id": row[1],
            "order_number": row[2],
            "amount": row[3],
            "payment_method": row[4],
            "payment_date": row[5],
            "reference_number": row[6],
            "status": row[7],
            "recorded_by": str(row[8]) if row[8] else None,
            "notes": row[9],
            "created_at": row[10]
        }

    finally:
        connection.close()