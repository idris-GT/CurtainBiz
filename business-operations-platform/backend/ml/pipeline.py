from ml.data.database_loader import load_business_data
from ml.data.dataframe_converter import convert_to_dataframes
from ml.cleaning.data_quality import clean_business_data
from ml.validation.business_validator import validate_business_data
from ml.features.business_features import build_business_features


def load_and_validate_business_data():
    """
    Load, clean, validate, and prepare all business data
    required by the ML and recommendation engines.
    """

    # ------------------------------------------------------
    # LOAD RAW DATABASE DATA
    # ------------------------------------------------------

    raw_data = load_business_data()

    # ------------------------------------------------------
    # CONVERT TO DATAFRAMES
    # ------------------------------------------------------

    dataframes = convert_to_dataframes(
        raw_data
    )

    # ------------------------------------------------------
    # CLEAN DATA
    # ------------------------------------------------------

    cleaned_dataframes, quality_report = (
        clean_business_data(
            dataframes
        )
    )

    # ------------------------------------------------------
    # BUSINESS VALIDATION
    # ------------------------------------------------------

    validation_report = (
        validate_business_data(
            cleaned_dataframes
        )
    )

    # ------------------------------------------------------
    # BUILD ML BUSINESS FEATURES
    # ------------------------------------------------------

    business_features = (
        build_business_features(
            cleaned_dataframes
        )
    )

    # ------------------------------------------------------
    # KEEP MATERIAL MASTER DATA AVAILABLE
    # ------------------------------------------------------
    #
    # The forecasting feature pipeline uses material
    # demand data, but the recommendation engine also
    # needs the material master table for:
    #
    #   - material names
    #   - categories
    #   - units
    #   - cost per unit
    #
    # This does not alter the ML features. It simply
    # exposes the cleaned material master data alongside
    # the generated business features.
    # ------------------------------------------------------

    if "materials" in cleaned_dataframes:
        business_features["materials"] = (
            cleaned_dataframes["materials"]
        )

    return (
        business_features,
        quality_report,
        validation_report,
    )