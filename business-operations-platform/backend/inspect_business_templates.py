from app.database.connection import get_connection


def print_rows(title, rows):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for row in rows:
        print(row)


def main():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id, product_code, name, category, unit, selling_price
            FROM products
            WHERE is_active = TRUE
            ORDER BY id;
        """)
        print_rows("PRODUCTS", cursor.fetchall())

        cursor.execute("""
            SELECT id, name, category, unit, minimum_stock, cost_per_unit
            FROM materials
            WHERE is_active = TRUE
            ORDER BY id;
        """)
        print_rows("MATERIALS", cursor.fetchall())

        cursor.execute("""
            SELECT status, COUNT(*)
            FROM orders
            GROUP BY status
            ORDER BY status;
        """)
        print_rows("ORDER STATUSES", cursor.fetchall())

        cursor.execute("""
            SELECT status, COUNT(*)
            FROM quotations
            GROUP BY status
            ORDER BY status;
        """)
        print_rows("QUOTATION STATUSES", cursor.fetchall())

        cursor.execute("""
            SELECT id, name, department_id
            FROM employees
            WHERE is_active = TRUE
            ORDER BY id;
        """)
        print_rows("EMPLOYEES", cursor.fetchall())

        cursor.execute("""
            SELECT id, name
            FROM departments
            ORDER BY id;
        """)
        print_rows("DEPARTMENTS", cursor.fetchall())

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()