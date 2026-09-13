from fastapi import APIRouter, Depends
from app.auth import require_permission, get_current_user_role
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/role-permissions",
    tags=["Role Permissions"]
)


class RolePermissionCreate(BaseModel):
    role_id: int
    permission_id: int


@router.get("/me")
def get_my_role_permissions(
    current_user=Depends(get_current_user_role)
):
    """
    Return the authenticated user's active role and its permissions.

    This endpoint intentionally does not require roles.view because
    a user needs to know their own access rights for the application
    to enforce frontend RBAC. It does not expose another user's data.
    """
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.name,
                p.description
            FROM role_permissions rp
            JOIN permissions p
                ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.id;
        """, (current_user["role_id"],))

        rows = cursor.fetchall()

        permissions = []

        for row in rows:
            permissions.append({
                "id": row[0],
                "name": row[1],
                "description": row[2]
            })

        cursor.close()

        return {
            "user_id": current_user["user_id"],
            "email": current_user.get("email"),
            "role_id": current_user["role_id"],
            "role": current_user["role"],
            "role_description": current_user["role_description"],
            "permissions": permissions
        }

    finally:
        connection.close()


@router.get("/{role_id}")
def get_role_permissions(
    role_id: int,
    current_user=Depends(require_permission("roles.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                r.id AS role_id,
                r.name AS role,
                p.id AS permission_id,
                p.name AS permission,
                p.description
            FROM role_permissions rp
            JOIN roles r
                ON rp.role_id = r.id
            JOIN permissions p
                ON rp.permission_id = p.id
            WHERE r.id = %s
            ORDER BY p.id;
        """, (role_id,))

        rows = cursor.fetchall()

        permissions = []

        for row in rows:
            permissions.append({
                "role_id": row[0],
                "role": row[1],
                "permission_id": row[2],
                "permission": row[3],
                "description": row[4]
            })

        cursor.close()

        return permissions

    finally:
        connection.close()


@router.post("/")
def assign_permission(
    data: RolePermissionCreate,
    current_user=Depends(require_permission("roles.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO role_permissions (
                role_id,
                permission_id
            )
            VALUES (%s, %s)
            RETURNING role_id, permission_id;
        """, (
            data.role_id,
            data.permission_id
        ))

        row = cursor.fetchone()

        connection.commit()

        return {
            "message": "Permission assigned to role successfully",
            "role_id": row[0],
            "permission_id": row[1]
        }

    finally:
        connection.close()


@router.delete("/")
def remove_permission(
    data: RolePermissionCreate,
    current_user=Depends(require_permission("roles.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM role_permissions
            WHERE role_id = %s
              AND permission_id = %s
            RETURNING role_id, permission_id;
        """, (
            data.role_id,
            data.permission_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Role-permission assignment not found"
            }

        connection.commit()

        return {
            "message": "Permission removed from role successfully",
            "role_id": row[0],
            "permission_id": row[1]
        }

    finally:
        connection.close()
