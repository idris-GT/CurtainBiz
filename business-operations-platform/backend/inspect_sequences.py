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
        print("\nTABLE ID DEFAULTS")
        print("=" * 80)

        query = """
            SELECT
                table_name,
                column_name,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND column_name = 'id'
              AND table_name = ANY(%s)
            ORDER BY table_name;
        """

        cursor.execute(query, (TABLES,))

        for row in cursor.fetchall():
            print(row)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()