from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/deliveries",
    tags=["Deliveries"]
)


class DeliveryCreate(BaseModel):
    order_id: int
    delivery_address: str
    scheduled_date: date
    delivered_date: date | None = None
    status: str
    delivered_by: UUID | None = None
    notes: str | None = None


@router.get("/")
def get_deliveries(
    current_user=Depends(require_permission("deliveries.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.order_id,
                o.order_number,
                d.delivery_address,
                d.scheduled_date,
                d.delivered_date,
                d.status,
                d.delivered_by,
                d.notes,
                d.created_at,
                d.updated_at
            FROM deliveries d
            JOIN orders o
                ON d.order_id = o.id
            ORDER BY d.id;
        """)

        rows = cursor.fetchall()

        deliveries = []

        for row in rows:
            deliveries.append({
                "id": row[0],
                "order_id": row[1],
                "order_number": row[2],
                "delivery_address": row[3],
                "scheduled_date": row[4],
                "delivered_date": row[5],
                "status": row[6],
                "delivered_by": str(row[7]) if row[7] else None,
                "notes": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            })

        return deliveries

    finally:
        connection.close()


@router.get("/{delivery_id}")
def get_delivery(
    delivery_id: int,
    current_user=Depends(require_permission("deliveries.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.order_id,
                o.order_number,
                d.delivery_address,
                d.scheduled_date,
                d.delivered_date,
                d.status,
                d.delivered_by,
                d.notes,
                d.created_at,
                d.updated_at
            FROM deliveries d
            JOIN orders o
                ON d.order_id = o.id
            WHERE d.id = %s;
        """, (delivery_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Delivery not found"
            }

        return {
            "id": row[0],
            "order_id": row[1],
            "order_number": row[2],
            "delivery_address": row[3],
            "scheduled_date": row[4],
            "delivered_date": row[5],
            "status": row[6],
            "delivered_by": str(row[7]) if row[7] else None,
            "notes": row[8],
            "created_at": row[9],
            "updated_at": row[10]
        }

    finally:
        connection.close()


@router.post("/")
def create_delivery(
    data: DeliveryCreate,
    current_user=Depends(require_permission("deliveries.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO deliveries (
                order_id,
                delivery_address,
                scheduled_date,
                delivered_date,
                status,
                delivered_by,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.order_id,
            data.delivery_address,
            data.scheduled_date,
            data.delivered_date,
            data.status,
            str(data.delivered_by) if data.delivered_by else None,
            data.notes
        ))

        delivery_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Delivery created successfully",
            "delivery_id": delivery_id
        }

    finally:
        connection.close()