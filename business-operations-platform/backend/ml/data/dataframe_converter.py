import pandas as pd


def convert_to_dataframes(data):
    dataframes = {}

    for table_name, table_data in data.items():
        dataframes[table_name] = pd.DataFrame(
            table_data["rows"],
            columns=table_data["columns"]
        )

    return dataframes