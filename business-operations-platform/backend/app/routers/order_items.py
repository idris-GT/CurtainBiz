from decimal import Decimal

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/order-items",
    tags=["Order Items"]
)


class OrderItemCreate(BaseModel):
    order_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    specifications: str | None = None


@router.get("/")
def get_order_items(
    current_user=Depends(require_permission("orders.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                oi.id,
                oi.order_id,
                o.order_number,
                oi.product_id,
                p.product_code,
                p.name AS product,
                oi.quantity,
                oi.unit_price,
                oi.total_price,
                oi.specifications
            FROM order_items oi
            JOIN orders o
                ON oi.order_id = o.id
            JOIN products p
                ON oi.product_id = p.id
            ORDER BY oi.id;
        """)

        rows = cursor.fetchall()

        items = []

        for row in rows:
            items.append({
                "id": row[0],
                "order_id": row[1],
                "order_number": row[2],
                "product_id": row[3],
                "product_code": row[4],
                "product": row[5],
                "quantity": row[6],
                "unit_price": row[7],
                "total_price": row[8],
                "specifications": row[9]
            })

        return items

    finally:
        connection.close()


@router.get("/{item_id}")
def get_order_item(
    item_id: int,
    current_user=Depends(require_permission("orders.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                oi.id,
                oi.order_id,
                o.order_number,
                oi.product_id,
                p.product_code,
                p.name AS product,
                oi.quantity,
                oi.unit_price,
                oi.total_price,
                oi.specifications
            FROM order_items oi
            JOIN orders o
                ON oi.order_id = o.id
            JOIN products p
                ON oi.product_id = p.id
            WHERE oi.id = %s;
        """, (item_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Order item not found"
            }

        return {
            "id": row[0],
            "order_id": row[1],
            "order_number": row[2],
            "product_id": row[3],
            "product_code": row[4],
            "product": row[5],
            "quantity": row[6],
            "unit_price": row[7],
            "total_price": row[8],
            "specifications": row[9]
        }

    finally:
        connection.close()