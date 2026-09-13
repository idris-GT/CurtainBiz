from app.database.connection import get_connection


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        print("\n" + "=" * 70)
        print("1. IMPORTANT NULL VALUES")
        print("=" * 70)

        checks = [
            ("orders", "customer_id"),
            ("orders", "order_date"),
            ("orders", "total_amount"),
            ("order_items", "order_id"),
            ("order_items", "product_id"),
            ("order_items", "quantity"),
            ("order_items", "unit_price"),
            ("products", "selling_price"),
            ("materials", "cost_per_unit"),
            ("inventory", "material_id"),
            ("inventory", "quantity_available"),
            ("production", "order_id"),
            ("deliveries", "order_id"),
            ("deliveries", "scheduled_date"),
            ("payments", "order_id"),
            ("payments", "amount"),
            ("payments", "payment_date"),
        ]

        for table, column in checks:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE {column} IS NULL;
                """
            )

            count = cursor.fetchone()[0]

            if count > 0:
                print(f"{table}.{column}: {count} NULL")
            else:
                print(f"{table}.{column}: OK")

        print("\n" + "=" * 70)
        print("2. NEGATIVE / ZERO BUSINESS VALUES")
        print("=" * 70)

        value_checks = [
            ("orders", "total_amount", "<= 0"),
            ("order_items", "quantity", "<= 0"),
            ("order_items", "unit_price", "<= 0"),
            ("order_items", "total_price", "<= 0"),
            ("products", "selling_price", "<= 0"),
            ("materials", "cost_per_unit", "<= 0"),
            ("materials", "minimum_stock", "< 0"),
            ("inventory", "quantity_available", "< 0"),
            ("inventory", "reserved_quantity", "< 0"),
            ("payments", "amount", "< 0"),
        ]

        for table, column, condition in value_checks:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE {column} {condition};
                """
            )

            count = cursor.fetchone()[0]

            print(f"{table}.{column} {condition}: {count}")

        print("\n" + "=" * 70)
        print("3. DUPLICATE BUSINESS IDENTIFIERS")
        print("=" * 70)

        duplicate_checks = [
            ("orders", "order_number"),
            ("quotations", "quotation_number"),
            ("products", "product_code"),
            ("materials", "material_code"),
            ("customers", "customer_code"),
            ("employees", "employee_code"),
        ]

        for table, column in duplicate_checks:
            cursor.execute(
                f"""
                SELECT {column}, COUNT(*)
                FROM {table}
                GROUP BY {column}
                HAVING COUNT(*) > 1;
                """
            )

            rows = cursor.fetchall()

            if rows:
                print(f"{table}.{column}: DUPLICATES FOUND")
                for value, count in rows:
                    print(f"  {value} -> {count}")
            else:
                print(f"{table}.{column}: OK")

        print("\n" + "=" * 70)
        print("4. DATE CONSISTENCY")
        print("=" * 70)

        date_checks = [
            (
                "orders",
                """
                SELECT COUNT(*)
                FROM orders
                WHERE expected_delivery_date < order_date;
                """,
                "Expected delivery before order date"
            ),
            (
                "deliveries",
                """
                SELECT COUNT(*)
                FROM deliveries
                WHERE delivered_date IS NOT NULL
                AND delivered_date < scheduled_date;
                """,
                "Delivered before scheduled date"
            ),
            (
                "production",
                """
                SELECT COUNT(*)
                FROM production
                WHERE completion_date IS NOT NULL
                AND completion_date < start_date;
                """,
                "Production completed before it started"
            ),
        ]

        for table, query, description in date_checks:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"{description}: {count}")

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()