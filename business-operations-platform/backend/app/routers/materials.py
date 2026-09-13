from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/materials",
    tags=["Materials"]
)


class MaterialCreate(BaseModel):
    material_code: str
    name: str
    category: str
    unit: str
    minimum_stock: float
    cost_per_unit: float
    is_active: bool = True


@router.get("/")
def get_materials(
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                material_code,
                name,
                category,
                unit,
                minimum_stock,
                cost_per_unit,
                is_active
            FROM materials
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        materials = []

        for row in rows:
            materials.append({
                "id": row[0],
                "material_code": row[1],
                "name": row[2],
                "category": row[3],
                "unit": row[4],
                "minimum_stock": row[5],
                "cost_per_unit": row[6],
                "is_active": row[7]
            })

        cursor.close()

        return materials

    finally:
        connection.close()


@router.get("/{material_id}")
def get_material(
    material_id: int,
    current_user=Depends(require_permission("inventory.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                material_code,
                name,
                category,
                unit,
                minimum_stock,
                cost_per_unit,
                is_active
            FROM materials
            WHERE id = %s;
        """, (material_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Material not found"
            }

        return {
            "id": row[0],
            "material_code": row[1],
            "name": row[2],
            "category": row[3],
            "unit": row[4],
            "minimum_stock": row[5],
            "cost_per_unit": row[6],
            "is_active": row[7]
        }

    finally:
        connection.close()


@router.post("/")
def create_material(
    material: MaterialCreate,
    current_user=Depends(require_permission("inventory.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO materials (
                material_code,
                name,
                category,
                unit,
                minimum_stock,
                cost_per_unit,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            material.material_code,
            material.name,
            material.category,
            material.unit,
            material.minimum_stock,
            material.cost_per_unit,
            material.is_active
        ))

        material_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Material created successfully",
            "material_id": material_id
        }

    finally:
        connection.close()


@router.put("/{material_id}")
def update_material(
    material_id: int,
    material: MaterialCreate,
    current_user=Depends(require_permission("inventory.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE materials
            SET
                material_code = %s,
                name = %s,
                category = %s,
                unit = %s,
                minimum_stock = %s,
                cost_per_unit = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            material.material_code,
            material.name,
            material.category,
            material.unit,
            material.minimum_stock,
            material.cost_per_unit,
            material.is_active,
            material_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Material not found"
            }

        connection.commit()

        return {
            "message": "Material updated successfully",
            "material_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{material_id}")
def deactivate_material(
    material_id: int,
    current_user=Depends(require_permission("inventory.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE materials
            SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (material_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Material not found"
            }

        connection.commit()

        return {
            "message": "Material deactivated successfully",
            "material_id": row[0]
        }

    finally:
        connection.close()