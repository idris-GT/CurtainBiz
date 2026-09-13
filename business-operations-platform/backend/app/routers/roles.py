from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


@router.get("/")
def get_roles(
    current_user=Depends(require_permission("roles.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                description,
                is_active
            FROM roles
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        roles = []

        for row in rows:
            roles.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "is_active": row[3]
            })

        cursor.close()

        return roles

    finally:
        connection.close()


@router.get("/{role_id}")
def get_role(
    role_id: int,
    current_user=Depends(require_permission("roles.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                description,
                is_active
            FROM roles
            WHERE id = %s;
        """, (role_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Role not found"
            }

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "is_active": row[3]
        }

    finally:
        connection.close()


@router.post("/")
def create_role(
    role: RoleCreate,
    current_user=Depends(require_permission("roles.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO roles (
                name,
                description,
                is_active
            )
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (
            role.name,
            role.description,
            role.is_active
        ))

        role_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Role created successfully",
            "role_id": role_id
        }

    finally:
        connection.close()


@router.put("/{role_id}")
def update_role(
    role_id: int,
    role: RoleCreate,
    current_user=Depends(require_permission("roles.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE roles
            SET
                name = %s,
                description = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            role.name,
            role.description,
            role.is_active,
            role_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Role not found"
            }

        connection.commit()

        return {
            "message": "Role updated successfully",
            "role_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{role_id}")
def deactivate_role(
    role_id: int,
    current_user=Depends(require_permission("roles.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE roles
            SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (role_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Role not found"
            }

        connection.commit()

        return {
            "message": "Role deactivated successfully",
            "role_id": row[0]
        }

    finally:
        connection.close()