from app.database.connection import get_connection


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        tables = {
            "quotations": "quotation_date",
            "orders": "order_date",
            "payments": "payment_date",
            "deliveries": "scheduled_date",
            "production": "start_date",
            "customers": "created_at",
            "products": "created_at",
            "materials": "created_at",
        }

        for table, date_column in tables.items():

            cursor.execute(f"""
                SELECT
                    COUNT(*),
                    MIN({date_column}),
                    MAX({date_column})
                FROM {table};
            """)

            count, minimum, maximum = cursor.fetchone()

            print("\n" + "=" * 60)
            print(f"TABLE: {table}")
            print("=" * 60)
            print(f"Records : {count}")
            print(f"Earliest: {minimum}")
            print(f"Latest  : {maximum}")

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()