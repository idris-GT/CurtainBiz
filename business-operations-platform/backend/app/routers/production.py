from datetime import datetime

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/production",
    tags=["Production"]
)


class ProductionCreate(BaseModel):
    order_id: int
    assigned_department_id: int | None = None
    assigned_employee_id: int | None = None
    status: str
    start_date: datetime | None = None
    completion_date: datetime | None = None
    notes: str | None = None


@router.get("/")
def get_production(current_user=Depends(require_permission("production.view"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.order_id,
                o.order_number,
                p.assigned_department_id,
                d.name AS department,
                p.assigned_employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS assigned_employee,
                p.status,
                p.start_date,
                p.completion_date,
                p.notes,
                p.created_at,
                p.updated_at
            FROM production p
            JOIN orders o
                ON p.order_id = o.id
            LEFT JOIN departments d
                ON p.assigned_department_id = d.id
            LEFT JOIN employees e
                ON p.assigned_employee_id = e.id
            ORDER BY p.id;
        """)

        rows = cursor.fetchall()

        production = []

        for row in rows:
            production.append({
                "id": row[0],
                "order_id": row[1],
                "order_number": row[2],
                "assigned_department_id": row[3],
                "department": row[4],
                "assigned_employee_id": row[5],
                "assigned_employee": row[6],
                "status": row[7],
                "start_date": row[8],
                "completion_date": row[9],
                "notes": row[10],
                "created_at": row[11],
                "updated_at": row[12]
            })

        return production

    finally:
        connection.close()


@router.get("/{production_id}")
def get_production_item(
    production_id: int,
    current_user=Depends(require_permission("production.view"))):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.order_id,
                o.order_number,
                p.assigned_department_id,
                d.name AS department,
                p.assigned_employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS assigned_employee,
                p.status,
                p.start_date,
                p.completion_date,
                p.notes,
                p.created_at,
                p.updated_at
            FROM production p
            JOIN orders o
                ON p.order_id = o.id
            LEFT JOIN departments d
                ON p.assigned_department_id = d.id
            LEFT JOIN employees e
                ON p.assigned_employee_id = e.id
            WHERE p.id = %s;
        """, (production_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Production record not found"
            }

        return {
            "id": row[0],
            "order_id": row[1],
            "order_number": row[2],
            "assigned_department_id": row[3],
            "department": row[4],
            "assigned_employee_id": row[5],
            "assigned_employee": row[6],
            "status": row[7],
            "start_date": row[8],
            "completion_date": row[9],
            "notes": row[10],
            "created_at": row[11],
            "updated_at": row[12]
        }

    finally:
        connection.close()


@router.post("/")
def create_production(
    data: ProductionCreate,
    current_user=Depends(require_permission("production.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO production (
                order_id,
                assigned_department_id,
                assigned_employee_id,
                status,
                start_date,
                completion_date,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.order_id,
            data.assigned_department_id,
            data.assigned_employee_id,
            data.status,
            data.start_date,
            data.completion_date,
            data.notes
        ))

        production_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Production record created successfully",
            "production_id": production_id
        }

    finally:
        connection.close()