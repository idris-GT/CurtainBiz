from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel
from uuid import UUID

from app.database.connection import get_connection


router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"]
)


class UserRoleCreate(BaseModel):
    user_id: UUID
    role_id: int


@router.get("/{user_id}")
def get_user_roles(
    user_id: UUID,
    current_user=Depends(require_permission("users.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ur.user_id,
                r.id AS role_id,
                r.name AS role,
                r.description,
                r.is_active
            FROM user_roles ur
            JOIN roles r
                ON ur.role_id = r.id
            WHERE ur.user_id = %s
            ORDER BY r.id;
        """, (str(user_id),))

        rows = cursor.fetchall()

        roles = []

        for row in rows:
            roles.append({
                "user_id": str(row[0]),
                "role_id": row[1],
                "role": row[2],
                "description": row[3],
                "is_active": row[4]
            })

        cursor.close()

        return roles

    finally:
        connection.close()


@router.post("/")
def assign_role(
    data: UserRoleCreate,
    current_user=Depends(require_permission("users.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO user_roles (
                user_id,
                role_id
            )
            VALUES (%s, %s)
            RETURNING user_id, role_id;
        """, (
            str(data.user_id),
            data.role_id
        ))

        row = cursor.fetchone()

        connection.commit()

        return {
            "message": "Role assigned to user successfully",
            "user_id": str(row[0]),
            "role_id": row[1]
        }

    finally:
        connection.close()


@router.delete("/")
def remove_role(
    data: UserRoleCreate,
    current_user=Depends(require_permission("users.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM user_roles
            WHERE user_id = %s
              AND role_id = %s
            RETURNING user_id, role_id;
        """, (
            str(data.user_id),
            data.role_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "User-role assignment not found"
            }

        connection.commit()

        return {
            "message": "Role removed from user successfully",
            "user_id": str(row[0]),
            "role_id": row[1]
        }

    finally:
        connection.close()