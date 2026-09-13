from decimal import Decimal

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


class InventoryUpdate(BaseModel):
    material_id: int
    quantity_available: Decimal
    reserved_quantity: Decimal = Decimal("0")
    location: str


@router.get("/")
def get_inventory(
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                i.id,
                i.material_id,
                m.material_code,
                m.name AS material,
                i.quantity_available,
                i.reserved_quantity,
                i.location,
                i.updated_at
            FROM inventory i
            JOIN materials m
                ON i.material_id = m.id
            ORDER BY i.id;
        """)

        rows = cursor.fetchall()

        inventory = []

        for row in rows:
            inventory.append({
                "id": row[0],
                "material_id": row[1],
                "material_code": row[2],
                "material": row[3],
                "quantity_available": row[4],
                "reserved_quantity": row[5],
                "location": row[6],
                "updated_at": row[7]
            })

        cursor.close()

        return inventory

    finally:
        connection.close()


@router.get("/{inventory_id}")
def get_inventory_item(
    inventory_id: int,
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                i.id,
                i.material_id,
                m.material_code,
                m.name AS material,
                i.quantity_available,
                i.reserved_quantity,
                i.location,
                i.updated_at
            FROM inventory i
            JOIN materials m
                ON i.material_id = m.id
            WHERE i.id = %s;
        """, (inventory_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Inventory item not found"
            }

        return {
            "id": row[0],
            "material_id": row[1],
            "material_code": row[2],
            "material": row[3],
            "quantity_available": row[4],
            "reserved_quantity": row[5],
            "location": row[6],
            "updated_at": row[7]
        }

    finally:
        connection.close()


@router.put("/{inventory_id}")
def update_inventory(
    inventory_id: int,
    inventory: InventoryUpdate,
    current_user=Depends(require_permission("inventory.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE inventory
            SET
                material_id = %s,
                quantity_available = %s,
                reserved_quantity = %s,
                location = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            inventory.material_id,
            inventory.quantity_available,
            inventory.reserved_quantity,
            inventory.location,
            inventory_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Inventory item not found"
            }

        connection.commit()

        return {
            "message": "Inventory updated successfully",
            "inventory_id": row[0]
        }

    finally:
        connection.close()