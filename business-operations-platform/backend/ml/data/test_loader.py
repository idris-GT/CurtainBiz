from .database_loader import load_business_data
from .dataframe_converter import convert_to_dataframes


data = load_business_data()
dataframes = convert_to_dataframes(data)

for table_name, df in dataframes.items():
    print(f"{table_name}: {len(df)} rows, {len(df.columns)} columns")