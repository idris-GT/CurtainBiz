import pandas as pd
import numpy as np


# ==========================================================
# FREQUENCY CONFIGURATION
# ==========================================================

FREQUENCY_CONFIG = {
    "D": {
        "pandas_frequency": "D",
        "lags": (1, 2, 3, 7, 14, 28),
        "windows": (3, 7, 14, 28),
        "short_window": 7,
        "long_window": 28,
        "comparison_period": 7,
        "long_comparison_period": 28,
    },

    "W": {
        "pandas_frequency": "W-MON",
        "lags": (1, 2, 4, 8, 12),
        "windows": (2, 4, 8, 12),
        "short_window": 4,
        "long_window": 12,
        "comparison_period": 1,
        "long_comparison_period": 4,
    },

    "M": {
        "pandas_frequency": "MS",
        "lags": (1, 2, 3, 6, 12),
        "windows": (2, 3, 6, 12),
        "short_window": 3,
        "long_window": 12,
        "comparison_period": 1,
        "long_comparison_period": 3,
    },
}


def get_frequency_config(frequency):
    """
    Return configuration for the requested forecast frequency.
    """

    frequency = frequency.upper()

    if frequency not in FREQUENCY_CONFIG:
        raise ValueError(
            f"Unsupported forecast frequency: {frequency}. "
            f"Supported frequencies: {list(FREQUENCY_CONFIG.keys())}"
        )

    return FREQUENCY_CONFIG[frequency]


# ==========================================================
# REGULAR TIME SERIES
# ==========================================================

def create_regular_time_series(
    df,
    date_column,
    target_column,
    frequency="D",
    fill_missing_target=0,
):
    """
    Convert sparse business-event data into a regular
    aggregated time series.

    Daily:
        Each date becomes one observation.

    Weekly:
        Daily business activity is aggregated into
        Monday-based weekly periods.

    Monthly:
        Daily business activity is aggregated into
        month-start periods.

    Missing periods are represented as zero activity.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                date_column,
                target_column,
            ]
        )

    frequency = frequency.upper()
    config = get_frequency_config(frequency)

    result = df.copy()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
        utc=True,
    )

    result[target_column] = pd.to_numeric(
        result[target_column],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            date_column,
            target_column,
        ]
    )

    if result.empty:
        return pd.DataFrame(
            columns=[
                date_column,
                target_column,
            ]
        )

    result = result.sort_values(
        date_column
    )

    # ------------------------------------------------------
    # AGGREGATE TO THE REQUESTED BUSINESS FREQUENCY
    # ------------------------------------------------------

    result = (
        result
        .set_index(date_column)[target_column]
        .resample(config["pandas_frequency"])
        .sum()
        .rename(target_column)
        .reset_index()
    )

    if result.empty:
        return result

    # ------------------------------------------------------
    # CREATE COMPLETE PERIOD RANGE
    # ------------------------------------------------------

    start_date = result[date_column].min()
    end_date = result[date_column].max()

    complete_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq=config["pandas_frequency"],
        tz="UTC",
    )

    result = (
        result
        .set_index(date_column)
        .reindex(complete_dates)
        .rename_axis(date_column)
        .reset_index()
    )

    if fill_missing_target is not None:
        result[target_column] = (
            result[target_column]
            .fillna(fill_missing_target)
        )

    return result.reset_index(drop=True)


# ==========================================================
# TIME / CALENDAR FEATURES
# ==========================================================

def add_time_features(
    df,
    date_column,
    frequency="D",
):
    """
    Add calendar and trend features appropriate for
    the requested forecast frequency.
    """

    result = df.copy()

    frequency = frequency.upper()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
        utc=True,
    )

    # ------------------------------------------------------
    # BASIC CALENDAR FEATURES
    # ------------------------------------------------------

    result["year"] = (
        result[date_column].dt.year
    )

    result["month"] = (
        result[date_column].dt.month
    )

    result["day"] = (
        result[date_column].dt.day
    )

    result["day_of_week"] = (
        result[date_column].dt.dayofweek
    )

    result["week_of_year"] = (
        result[date_column]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    result["day_of_year"] = (
        result[date_column].dt.dayofyear
    )

    # ------------------------------------------------------
    # CONTINUOUS TREND
    # ------------------------------------------------------

    first_date = result[date_column].min()

    result["trend_days"] = (
        result[date_column] - first_date
    ).dt.days
    # ------------------------------------------------------
    # FREQUENCY-AWARE TREND
    # ------------------------------------------------------

    result["trend_periods"] = np.arange(
        len(result)
    )

    # ------------------------------------------------------
    # WEEKLY CYCLICAL FEATURES
    # ------------------------------------------------------

    result["day_of_week_sin"] = np.sin(
        2 * np.pi
        * result["day_of_week"]
        / 7
    )

    result["day_of_week_cos"] = np.cos(
        2 * np.pi
        * result["day_of_week"]
        / 7
    )

    # ------------------------------------------------------
    # YEARLY CYCLICAL FEATURES
    # ------------------------------------------------------

    result["day_of_year_sin"] = np.sin(
        2 * np.pi
        * (result["day_of_year"] - 1)
        / 365.25
    )

    result["day_of_year_cos"] = np.cos(
        2 * np.pi
        * (result["day_of_year"] - 1)
        / 365.25
    )

    # ------------------------------------------------------
    # MONTHLY CYCLICAL FEATURES
    # ------------------------------------------------------

    result["month_sin"] = np.sin(
        2 * np.pi
        * (result["month"] - 1)
        / 12
    )

    result["month_cos"] = np.cos(
        2 * np.pi
        * (result["month"] - 1)
        / 12
    )

    return result


# ==========================================================
# LAG FEATURES
# ==========================================================

def add_lag_features(
    df,
    target_column,
    frequency="D",
):
    """
    Add frequency-aware lagged historical values.
    """

    result = df.copy()

    config = get_frequency_config(
        frequency
    )

    for lag in config["lags"]:

        result[
            f"{target_column}_lag_{lag}"
        ] = (
            result[target_column]
            .shift(lag)
        )

    return result


# ==========================================================
# ROLLING FEATURES
# ==========================================================

def add_rolling_features(
    df,
    target_column,
    frequency="D",
):
    """
    Add frequency-aware historical rolling statistics.

    The target is shifted before calculating statistics
    to prevent target leakage.
    """

    result = df.copy()

    config = get_frequency_config(
        frequency
    )

    historical = (
        result[target_column]
        .shift(1)
    )

    for window in config["windows"]:

        result[
            f"{target_column}_rolling_mean_{window}"
        ] = (
            historical
            .rolling(window=window)
            .mean()
        )

        result[
            f"{target_column}_rolling_std_{window}"
        ] = (
            historical
            .rolling(window=window)
            .std()
        )

        result[
            f"{target_column}_rolling_min_{window}"
        ] = (
            historical
            .rolling(window=window)
            .min()
        )

        result[
            f"{target_column}_rolling_max_{window}"
        ] = (
            historical
            .rolling(window=window)
            .max()
        )

    return result


# ==========================================================
# MOMENTUM / GROWTH FEATURES
# ==========================================================

def add_growth_features(
    df,
    target_column,
    frequency="D",
):
    """
    Add frequency-aware historical momentum features.

    All calculations use historical values only.
    """

    result = df.copy()

    config = get_frequency_config(
        frequency
    )

    historical = (
        result[target_column]
        .shift(1)
    )

    short_window = config["short_window"]
    long_window = config["long_window"]

    comparison_period = (
        config["comparison_period"]
    )

    long_comparison_period = (
        config["long_comparison_period"]
    )

    # ------------------------------------------------------
    # RECENT VS LONG-TERM AVERAGE
    # ------------------------------------------------------

    short_mean = (
        historical
        .rolling(window=short_window)
        .mean()
    )

    long_mean = (
        historical
        .rolling(window=long_window)
        .mean()
    )

    result[
        f"{target_column}_recent_vs_long_term"
    ] = (
        short_mean
        / long_mean.replace(
            0,
            np.nan,
        )
    )

    # ------------------------------------------------------
    # PERIOD-OVER-PERIOD CHANGE
    # ------------------------------------------------------

    previous_period = (
        result[target_column]
        .shift(comparison_period)
    )

    result[
        f"{target_column}_period_change"
    ] = (
        historical
        - previous_period
    )

    result[
        f"{target_column}_period_pct"
    ] = (
        (historical - previous_period)
        / previous_period.replace(
            0,
            np.nan,
        )
    )

    # ------------------------------------------------------
    # LONGER-TERM CHANGE
    # ------------------------------------------------------

    previous_long_period = (
        result[target_column]
        .shift(long_comparison_period)
    )

    result[
        f"{target_column}_long_term_change"
    ] = (
        historical
        - previous_long_period
    )

    result[
        f"{target_column}_long_term_pct"
    ] = (
        (
            historical
            - previous_long_period
        )
        / previous_long_period.replace(
            0,
            np.nan,
        )
    )

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return result


# ==========================================================
# COMPLETE TIME-SERIES PREPARATION
# ==========================================================

def prepare_regular_forecast_series(
    df,
    date_column,
    target_column,
    frequency="D",
):
    """
    Complete frequency-aware time-series preparation.

    Flow:

        Sparse business data
                ↓
        Frequency aggregation
                ↓
        Regular time series
                ↓
        Calendar features
                ↓
        Trend features
                ↓
        Cyclical seasonality
                ↓
        Frequency-aware lag features
                ↓
        Rolling statistics
                ↓
        Growth / momentum features
    """

    frequency = frequency.upper()

    result = create_regular_time_series(
        df=df,
        date_column=date_column,
        target_column=target_column,
        frequency=frequency,
        fill_missing_target=0,
    )

    if result.empty:
        return result

    result = add_time_features(
        result,
        date_column,
        frequency=frequency,
    )

    result = add_lag_features(
        result,
        target_column,
        frequency=frequency,
    )

    result = add_rolling_features(
        result,
        target_column,
        frequency=frequency,
    )

    result = add_growth_features(
        result,
        target_column,
        frequency=frequency,
    )

    return result