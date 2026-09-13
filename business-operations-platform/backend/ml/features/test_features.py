import pandas as pd

from ml.pipeline import load_and_validate_business_data


def test_business_feature_pipeline():
    """
    Verify that the business feature pipeline loads
    validated historical data and produces the expected
    feature sets.
    """

    features, quality_report, validation_report = (
        load_and_validate_business_data()
    )

    expected_feature_sets = {
        "sales": [
            "date",
            "order_count",
            "revenue",
            "average_order_value",
        ],
        "orders": [
            "date",
            "order_count",
        ],
        "product_demand": [
            "date",
            "product_id",
            "quantity",
            "revenue",
        ],
        "inventory": [
            "material_id",
        ],
        "material_demand": [
            "date",
            "material_id",
            "inbound_quantity",
            "outbound_quantity",
        ],
        "production": [
            "date",
            "production_count",
        ],
        "deliveries": [
            "date",
            "delivery_count",
        ],
        "payments": [
            "date",
            "payment_count",
            "cash_inflow",
            "average_payment",
        ],
    }

    assert isinstance(features, dict)

    for feature_name, required_columns in expected_feature_sets.items():
        assert feature_name in features, (
            f"Missing feature set: {feature_name}"
        )

        dataframe = features[feature_name]

        assert isinstance(dataframe, pd.DataFrame), (
            f"{feature_name} is not a pandas DataFrame"
        )

        for column in required_columns:
            assert column in dataframe.columns, (
                f"{feature_name} is missing required column "
                f"'{column}'"
            )

        if not dataframe.empty:
            assert len(dataframe) > 0


def test_feature_pipeline_reports_are_available():
    """
    Verify that the pipeline also returns data-quality
    and business-validation reports.
    """

    features, quality_report, validation_report = (
        load_and_validate_business_data()
    )

    assert quality_report is not None
    assert validation_report is not None