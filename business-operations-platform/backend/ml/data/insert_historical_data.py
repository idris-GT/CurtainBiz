from ml.data.historical_generator import generate_historical_dataset
from app.database.connection import get_connection


def insert_rows(cursor, table, rows, columns):
    if not rows:
        return

    column_names = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    query = f"""
        INSERT INTO {table} ({column_names})
        VALUES ({placeholders});
    """

    values = [
        tuple(row[column] for column in columns)
        for row in rows
    ]

    cursor.executemany(query, values)


def main():
    print("=" * 70)
    print("HISTORICAL DATA — PERMANENT DATABASE INSERT")
    print("=" * 70)

    print("\nGenerating historical dataset...")

    dataset = generate_historical_dataset()

    if dataset["errors"]:
        print("\nERROR: Generated dataset failed validation.")

        for error in dataset["errors"]:
            print(f"- {error}")

        return

    print("Generator validation passed.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        print("\nStarting database transaction...")
        print("Data will be COMMITTED only if every insert succeeds.")

        # ----------------------------------------------------
        # QUOTATIONS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "quotations",
            dataset["quotations"],
            [
                "id",
                "quotation_number",
                "customer_id",
                "created_by",
                "quotation_date",
                "valid_until",
                "status",
                "subtotal",
                "tax_amount",
                "total_amount",
                "notes",
                "created_at",
                "updated_at",
            ],
        )

        print(f"✓ Quotations inserted: {len(dataset['quotations'])}")

        # ----------------------------------------------------
        # QUOTATION ITEMS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "quotation_items",
            dataset["quotation_items"],
            [
                "id",
                "quotation_id",
                "product_id",
                "quantity",
                "unit_price",
                "total_price",
                "specifications",
            ],
        )

        print(
            f"✓ Quotation items inserted: "
            f"{len(dataset['quotation_items'])}"
        )

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "orders",
            dataset["orders"],
            [
                "id",
                "order_number",
                "customer_id",
                "quotation_id",
                "created_by",
                "order_date",
                "expected_delivery_date",
                "status",
                "subtotal",
                "tax_amount",
                "total_amount",
                "notes",
                "created_at",
                "updated_at",
            ],
        )

        print(f"✓ Orders inserted: {len(dataset['orders'])}")

        # ----------------------------------------------------
        # ORDER ITEMS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "order_items",
            dataset["order_items"],
            [
                "id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
                "total_price",
                "specifications",
            ],
        )

        print(
            f"✓ Order items inserted: "
            f"{len(dataset['order_items'])}"
        )

        # ----------------------------------------------------
        # PRODUCTION
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "production",
            dataset["production"],
            [
                "id",
                "order_id",
                "assigned_department_id",
                "assigned_employee_id",
                "status",
                "start_date",
                "completion_date",
                "notes",
                "created_at",
                "updated_at",
            ],
        )

        print(
            f"✓ Production inserted: "
            f"{len(dataset['production'])}"
        )

        # ----------------------------------------------------
        # PRODUCTION TASKS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "production_tasks",
            dataset["production_tasks"],
            [
                "id",
                "production_id",
                "task_name",
                "assigned_employee_id",
                "status",
                "priority",
                "started_at",
                "completed_at",
                "notes",
                "created_at",
            ],
        )

        print(
            f"✓ Production tasks inserted: "
            f"{len(dataset['production_tasks'])}"
        )

        # ----------------------------------------------------
        # DELIVERIES
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "deliveries",
            dataset["deliveries"],
            [
                "id",
                "order_id",
                "delivery_address",
                "scheduled_date",
                "delivered_date",
                "status",
                "delivered_by",
                "notes",
                "created_at",
                "updated_at",
            ],
        )

        print(
            f"✓ Deliveries inserted: "
            f"{len(dataset['deliveries'])}"
        )

        # ----------------------------------------------------
        # PAYMENTS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "payments",
            dataset["payments"],
            [
                "id",
                "order_id",
                "amount",
                "payment_method",
                "payment_date",
                "reference_number",
                "status",
                "recorded_by",
                "notes",
                "created_at",
            ],
        )

        print(
            f"✓ Payments inserted: "
            f"{len(dataset['payments'])}"
        )

        # ----------------------------------------------------
        # STOCK TRANSACTIONS
        # ----------------------------------------------------

        insert_rows(
            cursor,
            "stock_transactions",
            dataset["stock_transactions"],
            [
                "id",
                "material_id",
                "transaction_type",
                "quantity",
                "reference_type",
                "reference_id",
                "notes",
                "created_by",
                "created_at",
            ],
        )

        print(
            f"✓ Stock transactions inserted: "
            f"{len(dataset['stock_transactions'])}"
        )

        # ----------------------------------------------------
        # FINAL COMMIT
        # ----------------------------------------------------

        print("\nAll database inserts succeeded.")

        connection.commit()

        print("✓ TRANSACTION COMMITTED.")
        print("✓ Historical data is now permanently stored.")

    except Exception as error:

        print("\n" + "=" * 70)
        print("DATABASE INSERT FAILED")
        print("=" * 70)

        print(type(error).__name__)
        print(error)

        print("\nRolling back transaction...")

        connection.rollback()

        print("✓ Rollback completed.")
        print("✓ No partial historical data was committed.")

    finally:
        cursor.close()
        connection.close()

    print("\n" + "=" * 70)
    print("HISTORICAL DATA INSERT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()