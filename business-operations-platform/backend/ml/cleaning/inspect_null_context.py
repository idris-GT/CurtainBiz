from ml.data.database_loader import load_business_data
from ml.data.dataframe_converter import convert_to_dataframes


data = load_business_data()
dataframes = convert_to_dataframes(data)


checks = {
    "production": [
        "status",
        "start_date",
        "completion_date",
    ],
    "production_tasks": [
        "status",
        "started_at",
        "completed_at",
    ],
    "deliveries": [
        "status",
        "scheduled_date",
        "delivered_date",
        "delivered_by",
    ],
}


for table_name, columns in checks.items():

    df = dataframes[table_name]

    print("\n" + "=" * 70)
    print(f"TABLE: {table_name}")
    print("=" * 70)

    print(df[columns].to_string(index=False))