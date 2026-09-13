from app.database.connection import get_connection


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                order_id,
                assigned_department_id,
                assigned_employee_id,
                status,
                start_date,
                completion_date,
                notes
            FROM production
            WHERE status = 'PENDING'
              AND start_date IS NOT NULL
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        print("\n" + "=" * 70)
        print("PRODUCTION STATUS/DATA ANOMALIES")
        print("=" * 70)

        if not rows:
            print("No anomalies found.")
        else:
            for row in rows:
                print(f"""
Production ID          : {row[0]}
Order ID               : {row[1]}
Department ID          : {row[2]}
Employee ID            : {row[3]}
Status                 : {row[4]}
Start Date             : {row[5]}
Completion Date        : {row[6]}
Notes                  : {row[7]}
""")

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()