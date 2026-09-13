from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/stock-transactions",
    tags=["Stock Transactions"]
)


class StockTransactionCreate(BaseModel):
    material_id: int
    transaction_type: str
    quantity: Decimal
    reference_type: str | None = None
    reference_id: int | None = None
    notes: str | None = None
    created_by: UUID


@router.get("/")
def get_stock_transactions(
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                st.id,
                st.material_id,
                m.material_code,
                m.name AS material,
                st.transaction_type,
                st.quantity,
                st.reference_type,
                st.reference_id,
                st.notes,
                st.created_by,
                st.created_at
            FROM stock_transactions st
            JOIN materials m
                ON st.material_id = m.id
            ORDER BY st.id DESC;
        """)

        rows = cursor.fetchall()

        transactions = []

        for row in rows:
            transactions.append({
                "id": row[0],
                "material_id": row[1],
                "material_code": row[2],
                "material": row[3],
                "transaction_type": row[4],
                "quantity": row[5],
                "reference_type": row[6],
                "reference_id": row[7],
                "notes": row[8],
                "created_by": str(row[9]) if row[9] else None,
                "created_at": row[10]
            })

        cursor.close()

        return transactions

    finally:
        connection.close()


@router.get("/{transaction_id}")
def get_stock_transaction(
    transaction_id: int,
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                st.id,
                st.material_id,
                m.material_code,
                m.name AS material,
                st.transaction_type,
                st.quantity,
                st.reference_type,
                st.reference_id,
                st.notes,
                st.created_by,
                st.created_at
            FROM stock_transactions st
            JOIN materials m
                ON st.material_id = m.id
            WHERE st.id = %s;
        """, (transaction_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Stock transaction not found"
            }

        return {
            "id": row[0],
            "material_id": row[1],
            "material_code": row[2],
            "material": row[3],
            "transaction_type": row[4],
            "quantity": row[5],
            "reference_type": row[6],
            "reference_id": row[7],
            "notes": row[8],
            "created_by": str(row[9]) if row[9] else None,
            "created_at": row[10]
        }

    finally:
        connection.close()


@router.post("/")
def create_stock_transaction(
    data: StockTransactionCreate,
    current_user=Depends(require_permission("inventory.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO stock_transactions (
                material_id,
                transaction_type,
                quantity,
                reference_type,
                reference_id,
                notes,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.material_id,
            data.transaction_type,
            data.quantity,
            data.reference_type,
            data.reference_id,
            data.notes,
            str(data.created_by)
        ))

        transaction_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Stock transaction created successfully",
            "transaction_id": transaction_id
        }

    finally:
        connection.close()