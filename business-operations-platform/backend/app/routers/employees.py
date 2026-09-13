from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database.connection import get_connection
from app.auth import require_permission


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: str
    department_id: int
    job_title: str
    joining_date: date
    employment_status: str = "ACTIVE"


@router.get("/")
def get_employees(
    current_user=Depends(require_permission("employees.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.employee_code,
                e.first_name,
                e.last_name,
                e.email,
                e.phone,
                e.department_id,
                d.name AS department,
                e.job_title,
                e.joining_date,
                e.employment_status
            FROM employees e
            LEFT JOIN departments d
                ON e.department_id = d.id
            ORDER BY e.id;
        """)

        rows = cursor.fetchall()

        employees = []

        for row in rows:
            employees.append({
                "id": row[0],
                "employee_code": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "email": row[4],
                "phone": row[5],
                "department_id": row[6],
                "department": row[7],
                "job_title": row[8],
                "joining_date": row[9],
                "employment_status": row[10]
            })

        cursor.close()

        return employees

    finally:
        connection.close()


@router.get("/{employee_id}")
def get_employee(
    employee_id: int,
    current_user=Depends(require_permission("employees.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.employee_code,
                e.first_name,
                e.last_name,
                e.email,
                e.phone,
                e.department_id,
                d.name AS department,
                e.job_title,
                e.joining_date,
                e.employment_status
            FROM employees e
            LEFT JOIN departments d
                ON e.department_id = d.id
            WHERE e.id = %s;
        """, (employee_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Employee not found"
            }

        return {
            "id": row[0],
            "employee_code": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "email": row[4],
            "phone": row[5],
            "department_id": row[6],
            "department": row[7],
            "job_title": row[8],
            "joining_date": row[9],
            "employment_status": row[10]
        }

    finally:
        connection.close()


@router.post("/")
def create_employee(
    employee: EmployeeCreate,
    current_user=Depends(require_permission("employees.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO employees (
                employee_code,
                first_name,
                last_name,
                email,
                phone,
                department_id,
                job_title,
                joining_date,
                employment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            employee.employee_code,
            employee.first_name,
            employee.last_name,
            employee.email,
            employee.phone,
            employee.department_id,
            employee.job_title,
            employee.joining_date,
            employee.employment_status
        ))

        employee_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Employee created successfully",
            "employee_id": employee_id
        }

    finally:
        connection.close()


@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    employee: EmployeeCreate,
    current_user=Depends(require_permission("employees.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE employees
            SET
                employee_code = %s,
                first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                department_id = %s,
                job_title = %s,
                joining_date = %s,
                employment_status = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            employee.employee_code,
            employee.first_name,
            employee.last_name,
            employee.email,
            employee.phone,
            employee.department_id,
            employee.job_title,
            employee.joining_date,
            employee.employment_status,
            employee_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Employee not found"
            }

        connection.commit()

        return {
            "message": "Employee updated successfully",
            "employee_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{employee_id}")
def deactivate_employee(employee_id: int,
                        current_user=Depends(require_permission("employees.manage"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE employees
            SET
                employment_status = 'INACTIVE',
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (employee_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Employee not found"
            }

        connection.commit()

        return {
            "message": "Employee deactivated successfully",
            "employee_id": row[0]
        }

    finally:
        connection.close()