from fastapi import APIRouter, Depends
from app.auth import require_permission
from app.database.connection import get_connection

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/")
def get_notifications(
    current_user=Depends(require_permission("employees.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                title,
                message,
                notification_type,
                reference_type,
                reference_id,
                is_read,
                created_at
            FROM notifications
            ORDER BY created_at DESC;
        """)

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "user_id": str(row[1]),
                "title": row[2],
                "message": row[3],
                "notification_type": row[4],
                "reference_type": row[5],
                "reference_id": row[6],
                "is_read": row[7],
                "created_at": row[8]
            }
            for row in rows
        ]

    finally:
        connection.close()