from decimal import Decimal
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderCreate(BaseModel):
    order_number: str
    customer_id: int
    quotation_id: int
    created_by: UUID
    order_date: date
    expected_delivery_date: date | None = None
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: str | None = None


@router.get("/")
def get_orders(current_user=Depends(require_permission("orders.view"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.order_number,
                o.customer_id,
                c.name AS customer,
                o.quotation_id,
                q.quotation_number,
                o.created_by,
                o.order_date,
                o.expected_delivery_date,
                o.status,
                o.subtotal,
                o.tax_amount,
                o.total_amount,
                o.notes
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.id
            LEFT JOIN quotations q
                ON o.quotation_id = q.id
            ORDER BY o.id;
        """)

        rows = cursor.fetchall()

        orders = []

        for row in rows:
            orders.append({
                "id": row[0],
                "order_number": row[1],
                "customer_id": row[2],
                "customer": row[3],
                "quotation_id": row[4],
                "quotation_number": row[5],
                "created_by": str(row[6]) if row[6] else None,
                "order_date": row[7],
                "expected_delivery_date": row[8],
                "status": row[9],
                "subtotal": row[10],
                "tax_amount": row[11],
                "total_amount": row[12],
                "notes": row[13]
            })

        return orders

    finally:
        connection.close()


@router.get("/{order_id}")
def get_order(
    order_id: int,
    current_user=Depends(require_permission("orders.view"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.order_number,
                o.customer_id,
                c.name AS customer,
                o.quotation_id,
                q.quotation_number,
                o.created_by,
                o.order_date,
                o.expected_delivery_date,
                o.status,
                o.subtotal,
                o.tax_amount,
                o.total_amount,
                o.notes
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.id
            LEFT JOIN quotations q
                ON o.quotation_id = q.id
            WHERE o.id = %s;
        """, (order_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Order not found"
            }

        return {
            "id": row[0],
            "order_number": row[1],
            "customer_id": row[2],
            "customer": row[3],
            "quotation_id": row[4],
            "quotation_number": row[5],
            "created_by": str(row[6]) if row[6] else None,
            "order_date": row[7],
            "expected_delivery_date": row[8],
            "status": row[9],
            "subtotal": row[10],
            "tax_amount": row[11],
            "total_amount": row[12],
            "notes": row[13]
        }

    finally:
        connection.close()


@router.post("/")
def create_order(
    data: OrderCreate,
    current_user=Depends(require_permission("orders.manage"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO orders (
                order_number,
                customer_id,
                quotation_id,
                created_by,
                order_date,
                expected_delivery_date,
                status,
                subtotal,
                tax_amount,
                total_amount,
                notes
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            RETURNING id;
        """, (
            data.order_number,
            data.customer_id,
            data.quotation_id,
            str(data.created_by),
            data.order_date,
            data.expected_delivery_date,
            data.status,
            data.subtotal,
            data.tax_amount,
            data.total_amount,
            data.notes
        ))

        order_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Order created successfully",
            "order_id": order_id
        }

    finally:
        connection.close()