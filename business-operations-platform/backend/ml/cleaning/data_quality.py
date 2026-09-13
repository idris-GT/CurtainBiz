import pandas as pd


def generate_data_quality_report(dataframes):
    """
    Analyze DataFrames and return a data-quality report.

    This function does NOT modify the input data.
    """

    report = {}

    for table_name, df in dataframes.items():

        total_rows = len(df)
        total_columns = len(df.columns)

        missing_values = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        column_details = {}

        for column in df.columns:
            column_details[column] = {
                "data_type": str(df[column].dtype),
                "missing": int(df[column].isna().sum()),
                "unique_values": int(df[column].nunique(dropna=True)),
            }

        report[table_name] = {
            "rows": total_rows,
            "columns": total_columns,
            "missing_values": missing_values,
            "duplicate_rows": duplicate_rows,
            "column_details": column_details,
        }

    return report


def clean_dataframe(df):
    """
    Create a cleaned copy of a DataFrame.

    The original DataFrame is never modified.
    """

    cleaned = df.copy()

    # Remove completely empty rows
    cleaned = cleaned.dropna(how="all")

    # Remove exact duplicate rows
    cleaned = cleaned.drop_duplicates()

    # Clean column names
    cleaned.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in cleaned.columns
    ]

    # Convert object columns containing date-like values
    for column in cleaned.columns:

        if cleaned[column].dtype == "object":

            converted = pd.to_datetime(
                cleaned[column],
                errors="coerce"
            )

            valid_date_ratio = converted.notna().mean()

            if valid_date_ratio >= 0.8:
                cleaned[column] = converted

    return cleaned.reset_index(drop=True)


def clean_business_data(dataframes):
    """
    Clean every business DataFrame.

    Returns:
        cleaned_dataframes
        quality_report
    """

    cleaned_dataframes = {}

    for table_name, df in dataframes.items():
        cleaned_dataframes[table_name] = clean_dataframe(df)

    quality_report = generate_data_quality_report(
        cleaned_dataframes
    )

    return cleaned_dataframes, quality_report