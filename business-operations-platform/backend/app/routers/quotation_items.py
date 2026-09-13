from decimal import Decimal

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/quotation-items",
    tags=["Quotation Items"]
)


class QuotationItemCreate(BaseModel):
    quotation_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    specifications: str | None = None


@router.get("/")
def get_quotation_items(
    current_user=Depends(require_permission("quotations.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                qi.id,
                qi.quotation_id,
                q.quotation_number,
                qi.product_id,
                p.product_code,
                p.name AS product,
                qi.quantity,
                qi.unit_price,
                qi.total_price,
                qi.specifications
            FROM quotation_items qi
            JOIN quotations q
                ON qi.quotation_id = q.id
            JOIN products p
                ON qi.product_id = p.id
            ORDER BY qi.id;
        """)

        rows = cursor.fetchall()

        items = []

        for row in rows:
            items.append({
                "id": row[0],
                "quotation_id": row[1],
                "quotation_number": row[2],
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
def get_quotation_item(
    item_id: int,
    current_user=Depends(require_permission("quotations.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                qi.id,
                qi.quotation_id,
                q.quotation_number,
                qi.product_id,
                p.product_code,
                p.name AS product,
                qi.quantity,
                qi.unit_price,
                qi.total_price,
                qi.specifications
            FROM quotation_items qi
            JOIN quotations q
                ON qi.quotation_id = q.id
            JOIN products p
                ON qi.product_id = p.id
            WHERE qi.id = %s;
        """, (item_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Quotation item not found"
            }

        return {
            "id": row[0],
            "quotation_id": row[1],
            "quotation_number": row[2],
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


@router.post("/")
def create_quotation_item(
    data: QuotationItemCreate,
    current_user=Depends(require_permission("quotations.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO quotation_items (
                quotation_id,
                product_id,
                quantity,
                unit_price,
                total_price,
                specifications
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.quotation_id,
            data.product_id,
            data.quantity,
            data.unit_price,
            data.total_price,
            data.specifications
        ))

        item_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Quotation item created successfully",
            "quotation_item_id": item_id
        }

    finally:
        connection.close()