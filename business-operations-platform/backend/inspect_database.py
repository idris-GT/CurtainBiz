from app.database.connection import get_connection


def main():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        rows = cursor.fetchall()

        current_table = None

        for table_name, column_name, data_type in rows:
            if table_name != current_table:
                print("\n" + "=" * 60)
                print(f"TABLE: {table_name}")
                print("=" * 60)
                current_table = table_name

            print(f"  {column_name:<30} {data_type}")

        cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()