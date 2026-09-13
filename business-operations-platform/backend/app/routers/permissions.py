from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"]
)


class PermissionCreate(BaseModel):
    name: str
    description: str | None = None


@router.get("/")
def get_permissions(
    current_user=Depends(require_permission("permissions.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                description
            FROM permissions
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        permissions = []

        for row in rows:
            permissions.append({
                "id": row[0],
                "name": row[1],
                "description": row[2]
            })

        cursor.close()

        return permissions

    finally:
        connection.close()


@router.get("/{permission_id}")
def get_permission(
    permission_id: int,
    current_user=Depends(require_permission("permissions.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                description
            FROM permissions
            WHERE id = %s;
        """, (permission_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Permission not found"
            }

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2]
        }

    finally:
        connection.close()


@router.post("/")
def create_permission(
    permission: PermissionCreate,
    current_user=Depends(require_permission("permissions.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO permissions (
                name,
                description
            )
            VALUES (%s, %s)
            RETURNING id;
        """, (
            permission.name,
            permission.description
        ))

        permission_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Permission created successfully",
            "permission_id": permission_id
        }

    finally:
        connection.close()


@router.put("/{permission_id}")
def update_permission(
    permission_id: int,
    permission: PermissionCreate,
    current_user=Depends(require_permission("permissions.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE permissions
            SET
                name = %s,
                description = %s
            WHERE id = %s
            RETURNING id;
        """, (
            permission.name,
            permission.description,
            permission_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Permission not found"
            }

        connection.commit()

        return {
            "message": "Permission updated successfully",
            "permission_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{permission_id}")
def delete_permission(
    permission_id: int,
    current_user=Depends(require_permission("permissions.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM permissions
            WHERE id = %s
            RETURNING id;
        """, (permission_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Permission not found"
            }

        connection.commit()

        return {
            "message": "Permission deleted successfully",
            "permission_id": row[0]
        }

    finally:
        connection.close()