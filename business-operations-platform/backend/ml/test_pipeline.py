from ml.pipeline import load_and_validate_business_data


cleaned_dataframes, quality_report, validation_report = (
    load_and_validate_business_data()
)


print("\n" + "=" * 70)
print("BUSINESS ML DATA PIPELINE")
print("=" * 70)

print("\nDATA TABLES")
print("-" * 70)

for table_name, df in cleaned_dataframes.items():
    print(f"{table_name}: {len(df)} rows")


print("\nDATA QUALITY")
print("-" * 70)

total_missing = sum(
    report["missing_values"]
    for report in quality_report.values()
)

total_duplicates = sum(
    report["duplicate_rows"]
    for report in quality_report.values()
)

print(f"Total missing values: {total_missing}")
print(f"Total duplicate rows: {total_duplicates}")


print("\nBUSINESS VALIDATION")
print("-" * 70)

print(f"Valid: {validation_report['valid']}")

print(f"Errors: {len(validation_report['errors'])}")
print(f"Warnings: {len(validation_report['warnings'])}")


if validation_report["errors"]:
    print("\nERRORS:")
    for error in validation_report["errors"]:
        print(f"  - {error}")


if validation_report["warnings"]:
    print("\nWARNINGS:")
    for warning in validation_report["warnings"]:
        print(f"  - {warning}")


print("\n" + "=" * 70)