from decimal import Decimal
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"]
)


class QuotationCreate(BaseModel):
    quotation_number: str
    customer_id: int
    created_by: UUID
    quotation_date: date
    valid_until: date
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: str | None = None


@router.get("/")
def get_quotations(
    current_user=Depends(require_permission("quotations.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                q.id,
                q.quotation_number,
                q.customer_id,
                c.name AS customer,
                q.created_by,
                q.quotation_date,
                q.valid_until,
                q.status,
                q.subtotal,
                q.tax_amount,
                q.total_amount,
                q.notes
            FROM quotations q
            JOIN customers c
                ON q.customer_id = c.id
            ORDER BY q.id;
        """)

        rows = cursor.fetchall()

        quotations = []

        for row in rows:
            quotations.append({
                "id": row[0],
                "quotation_number": row[1],
                "customer_id": row[2],
                "customer": row[3],
                "created_by": str(row[4]) if row[4] else None,
                "quotation_date": row[5],
                "valid_until": row[6],
                "status": row[7],
                "subtotal": row[8],
                "tax_amount": row[9],
                "total_amount": row[10],
                "notes": row[11]
            })

        cursor.close()

        return quotations

    finally:
        connection.close()


@router.get("/{quotation_id}")
def get_quotation(quotation_id: int,
                  current_user=Depends(require_permission("quotations.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                q.id,
                q.quotation_number,
                q.customer_id,
                c.name AS customer,
                q.created_by,
                q.quotation_date,
                q.valid_until,
                q.status,
                q.subtotal,
                q.tax_amount,
                q.total_amount,
                q.notes
            FROM quotations q
            JOIN customers c
                ON q.customer_id = c.id
            WHERE q.id = %s;
        """, (quotation_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Quotation not found"
            }

        return {
            "id": row[0],
            "quotation_number": row[1],
            "customer_id": row[2],
            "customer": row[3],
            "created_by": str(row[4]) if row[4] else None,
            "quotation_date": row[5],
            "valid_until": row[6],
            "status": row[7],
            "subtotal": row[8],
            "tax_amount": row[9],
            "total_amount": row[10],
            "notes": row[11]
        }

    finally:
        connection.close()


@router.post("/")
def create_quotation(
    data: QuotationCreate,
    current_user=Depends(require_permission("quotations.manage"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO quotations (
                quotation_number,
                customer_id,
                created_by,
                quotation_date,
                valid_until,
                status,
                subtotal,
                tax_amount,
                total_amount,
                notes
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            RETURNING id;
        """, (
            data.quotation_number,
            data.customer_id,
            str(data.created_by),
            data.quotation_date,
            data.valid_until,
            data.status,
            data.subtotal,
            data.tax_amount,
            data.total_amount,
            data.notes
        ))

        quotation_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Quotation created successfully",
            "quotation_id": quotation_id
        }

    finally:
        connection.close()