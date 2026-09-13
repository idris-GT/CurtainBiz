from app.database.connection import get_connection


def load_business_data():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        data = {}

        tables = [
            "orders",
            "order_items",
            "products",
            "customers",
            "quotations",
            "quotation_items",
            "materials",
            "inventory",
            "stock_transactions",
            "production",
            "production_tasks",
            "deliveries",
            "payments",
        ]

        for table in tables:
            cursor.execute(f"SELECT * FROM {table};")

            rows = cursor.fetchall()

            columns = [description[0] for description in cursor.description]

            data[table] = {
                "columns": columns,
                "rows": rows,
            }

        cursor.close()

        return data

    finally:
        connection.close()