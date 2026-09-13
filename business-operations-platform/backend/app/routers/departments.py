from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


@router.get("/")
def get_departments(
    current_user=Depends(require_permission("employees.view"))
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
            FROM departments
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        departments = []

        for row in rows:
            departments.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "is_active": row[3]
            })

        cursor.close()

        return departments

    finally:
        connection.close()


@router.get("/{department_id}")
def get_department(
    department_id: int,
    current_user=Depends(require_permission("employees.view"))
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
            FROM departments
            WHERE id = %s;
        """, (department_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Department not found"
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
def create_department(
    department: DepartmentCreate,
    current_user=Depends(require_permission("employees.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO departments (
                name,
                description,
                is_active
            )
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (
            department.name,
            department.description,
            department.is_active
        ))

        department_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Department created successfully",
            "department_id": department_id
        }

    finally:
        connection.close()


@router.put("/{department_id}")
def update_department(
    department_id: int,
    department: DepartmentCreate,
     current_user=Depends(require_permission("employees.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE departments
            SET
                name = %s,
                description = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            department.name,
            department.description,
            department.is_active,
            department_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Department not found"
            }

        connection.commit()

        return {
            "message": "Department updated successfully",
            "department_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{department_id}")
def deactivate_department(
    department_id: int,
    current_user=Depends(require_permission("employees.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE departments
            SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (department_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Department not found"
            }

        connection.commit()

        return {
            "message": "Department deactivated successfully",
            "department_id": row[0]
        }

    finally:
        connection.close()