from app.database.connection import get_connection


CHECKS = [
    (
        "order_items → orders",
        """
        SELECT COUNT(*)
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.id
        WHERE o.id IS NULL;
        """
    ),
    (
        "order_items → products",
        """
        SELECT COUNT(*)
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE p.id IS NULL;
        """
    ),
    (
        "orders → customers",
        """
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        WHERE c.id IS NULL;
        """
    ),
    (
        "orders → quotations",
        """
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN quotations q ON o.quotation_id = q.id
        WHERE o.quotation_id IS NOT NULL
          AND q.id IS NULL;
        """
    ),
    (
        "quotation_items → quotations",
        """
        SELECT COUNT(*)
        FROM quotation_items qi
        LEFT JOIN quotations q ON qi.quotation_id = q.id
        WHERE q.id IS NULL;
        """
    ),
    (
        "quotation_items → products",
        """
        SELECT COUNT(*)
        FROM quotation_items qi
        LEFT JOIN products p ON qi.product_id = p.id
        WHERE p.id IS NULL;
        """
    ),
    (
        "inventory → materials",
        """
        SELECT COUNT(*)
        FROM inventory i
        LEFT JOIN materials m ON i.material_id = m.id
        WHERE m.id IS NULL;
        """
    ),
    (
        "stock_transactions → materials",
        """
        SELECT COUNT(*)
        FROM stock_transactions st
        LEFT JOIN materials m ON st.material_id = m.id
        WHERE m.id IS NULL;
        """
    ),
    (
        "production → orders",
        """
        SELECT COUNT(*)
        FROM production p
        LEFT JOIN orders o ON p.order_id = o.id
        WHERE o.id IS NULL;
        """
    ),
    (
        "production → departments",
        """
        SELECT COUNT(*)
        FROM production p
        LEFT JOIN departments d ON p.assigned_department_id = d.id
        WHERE p.assigned_department_id IS NOT NULL
          AND d.id IS NULL;
        """
    ),
    (
        "production → employees",
        """
        SELECT COUNT(*)
        FROM production p
        LEFT JOIN employees e ON p.assigned_employee_id = e.id
        WHERE p.assigned_employee_id IS NOT NULL
          AND e.id IS NULL;
        """
    ),
    (
        "production_tasks → production",
        """
        SELECT COUNT(*)
        FROM production_tasks pt
        LEFT JOIN production p ON pt.production_id = p.id
        WHERE p.id IS NULL;
        """
    ),
    (
        "production_tasks → employees",
        """
        SELECT COUNT(*)
        FROM production_tasks pt
        LEFT JOIN employees e ON pt.assigned_employee_id = e.id
        WHERE pt.assigned_employee_id IS NOT NULL
          AND e.id IS NULL;
        """
    ),
    (
        "deliveries → orders",
        """
        SELECT COUNT(*)
        FROM deliveries d
        LEFT JOIN orders o ON d.order_id = o.id
        WHERE o.id IS NULL;
        """
    ),
    (
        "payments → orders",
        """
        SELECT COUNT(*)
        FROM payments p
        LEFT JOIN orders o ON p.order_id = o.id
        WHERE o.id IS NULL;
        """
    ),
]


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        print("\n" + "=" * 70)
        print("DATABASE RELATIONSHIP INTEGRITY CHECK")
        print("=" * 70)

        problems = 0

        for name, query in CHECKS:
            cursor.execute(query)
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"OK      | {name}")
            else:
                print(f"ERROR   | {name} | Broken references: {count}")
                problems += count

        print("\n" + "=" * 70)

        if problems == 0:
            print("RESULT: ALL CHECKED RELATIONSHIPS ARE VALID")
        else:
            print(f"RESULT: {problems} BROKEN REFERENCES FOUND")

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()