from fastapi import APIRouter, Depends

from app.auth import require_permission
from app.database.connection import get_connection


router = APIRouter(
    prefix="/queries",
    tags=["Queries"]
)


@router.get("/")
def get_queries(
    current_user=Depends(require_permission("queries.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                q.id,
                q.order_id,
                o.order_number,
                q.created_by,
                q.assigned_department_id,
                d.name AS department,
                q.subject,
                q.description,
                q.priority,
                q.status,
                q.created_at,
                q.updated_at
            FROM queries q
            LEFT JOIN orders o
                ON q.order_id = o.id
            LEFT JOIN departments d
                ON q.assigned_department_id = d.id
            ORDER BY q.id;
        """)

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "order_id": row[1],
                "order_number": row[2],
                "created_by": str(row[3]) if row[3] else None,
                "assigned_department_id": row[4],
                "department": row[5],
                "subject": row[6],
                "description": row[7],
                "priority": row[8],
                "status": row[9],
                "created_at": row[10],
                "updated_at": row[11]
            }
            for row in rows
        ]

    finally:
        connection.close()


@router.get("/{query_id}")
def get_query(
    query_id: int,
    current_user=Depends(require_permission("queries.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                q.id,
                q.order_id,
                o.order_number,
                q.created_by,
                q.assigned_department_id,
                d.name AS department,
                q.subject,
                q.description,
                q.priority,
                q.status,
                q.created_at,
                q.updated_at
            FROM queries q
            LEFT JOIN orders o
                ON q.order_id = o.id
            LEFT JOIN departments d
                ON q.assigned_department_id = d.id
            WHERE q.id = %s;
        """, (query_id,))

        row = cursor.fetchone()

        if row is None:
            return {"message": "Query not found"}

        return {
            "id": row[0],
            "order_id": row[1],
            "order_number": row[2],
            "created_by": str(row[3]) if row[3] else None,
            "assigned_department_id": row[4],
            "department": row[5],
            "subject": row[6],
            "description": row[7],
            "priority": row[8],
            "status": row[9],
            "created_at": row[10],
            "updated_at": row[11]
        }

    finally:
        connection.close()