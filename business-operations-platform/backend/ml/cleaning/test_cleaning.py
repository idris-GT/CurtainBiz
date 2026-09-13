from ml.data.database_loader import load_business_data
from ml.data.dataframe_converter import convert_to_dataframes
from ml.cleaning.data_quality import clean_business_data


data = load_business_data()

dataframes = convert_to_dataframes(data)

cleaned_dataframes, quality_report = clean_business_data(dataframes)


for table_name, report in quality_report.items():

    print("\n" + "=" * 70)
    print(f"TABLE: {table_name}")
    print("=" * 70)

    print(f"Rows: {report['rows']}")
    print(f"Columns: {report['columns']}")
    print(f"Total missing values: {report['missing_values']}")
    print(f"Duplicate rows: {report['duplicate_rows']}")

    missing_columns = {
        column: details["missing"]
        for column, details in report["column_details"].items()
        if details["missing"] > 0
    }

    if missing_columns:
        print("\nMissing values by column:")

        for column, count in missing_columns.items():
            print(f"  {column}: {count}")
    else:
        print("\nMissing values by column: None")