from fastapi import APIRouter, Depends
from app.auth import require_permission
from app.database.connection import get_connection

router = APIRouter(
    prefix="/activity-logs",
    tags=["Activity Logs"]
)


@router.get("/")
def get_activity_logs(
    current_user=Depends(require_permission("users.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                action,
                entity_type,
                entity_id,
                description,
                created_at
            FROM activity_logs
            ORDER BY created_at DESC;
        """)

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "user_id": str(row[1]) if row[1] else None,
                "action": row[2],
                "entity_type": row[3],
                "entity_id": row[4],
                "description": row[5],
                "created_at": row[6]
            }
            for row in rows
        ]

    finally:
        connection.close()