from datetime import datetime

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/production-tasks",
    tags=["Production Tasks"]
)


class ProductionTaskCreate(BaseModel):
    production_id: int
    task_name: str
    assigned_employee_id: int | None = None
    status: str
    priority: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


@router.get("/")
def get_production_tasks(
    current_user=Depends(require_permission("production.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                pt.id,
                pt.production_id,
                o.order_number,
                pt.task_name,
                pt.assigned_employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS assigned_employee,
                pt.status,
                pt.priority,
                pt.started_at,
                pt.completed_at,
                pt.notes,
                pt.created_at
            FROM production_tasks pt
            JOIN production p
                ON pt.production_id = p.id
            JOIN orders o
                ON p.order_id = o.id
            LEFT JOIN employees e
                ON pt.assigned_employee_id = e.id
            ORDER BY pt.id;
        """)

        rows = cursor.fetchall()

        tasks = []

        for row in rows:
            tasks.append({
                "id": row[0],
                "production_id": row[1],
                "order_number": row[2],
                "task_name": row[3],
                "assigned_employee_id": row[4],
                "assigned_employee": row[5],
                "status": row[6],
                "priority": row[7],
                "started_at": row[8],
                "completed_at": row[9],
                "notes": row[10],
                "created_at": row[11]
            })

        return tasks

    finally:
        connection.close()


@router.get("/{task_id}")
def get_production_task(
    task_id: int,
    current_user=Depends(require_permission("production.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                pt.id,
                pt.production_id,
                o.order_number,
                pt.task_name,
                pt.assigned_employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS assigned_employee,
                pt.status,
                pt.priority,
                pt.started_at,
                pt.completed_at,
                pt.notes,
                pt.created_at
            FROM production_tasks pt
            JOIN production p
                ON pt.production_id = p.id
            JOIN orders o
                ON p.order_id = o.id
            LEFT JOIN employees e
                ON pt.assigned_employee_id = e.id
            WHERE pt.id = %s;
        """, (task_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Production task not found"
            }

        return {
            "id": row[0],
            "production_id": row[1],
            "order_number": row[2],
            "task_name": row[3],
            "assigned_employee_id": row[4],
            "assigned_employee": row[5],
            "status": row[6],
            "priority": row[7],
            "started_at": row[8],
            "completed_at": row[9],
            "notes": row[10],
            "created_at": row[11]
        }

    finally:
        connection.close()