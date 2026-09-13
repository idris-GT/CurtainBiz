from app.database.connection import get_connection


TABLES = [
    "customers",
    "products",
    "materials",
    "orders",
    "order_items",
    "quotations",
    "quotation_items",
    "production",
    "production_tasks",
    "deliveries",
    "payments",
    "stock_transactions",
]


def main():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        print("\nCURRENT COUNTS / MAX IDS")
        print("=" * 60)

        for table in TABLES:
            cursor.execute(
                f"""
                SELECT
                    COUNT(*),
                    COALESCE(MAX(id), 0)
                FROM {table};
                """
            )

            count, max_id = cursor.fetchone()

            print(
                f"{table:<22} "
                f"count={count:<5} "
                f"max_id={max_id}"
            )

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()