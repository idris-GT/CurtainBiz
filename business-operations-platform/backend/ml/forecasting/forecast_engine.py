import numpy as np
import pandas as pd

from ml.forecasting.forecast_problems import (
    get_forecast_problem,
)
from ml.forecasting.time_series import (
    create_regular_time_series,
    add_time_features,
    add_lag_features,
    add_rolling_features,
    add_growth_features,
)
from ml.models.model_selector import (
    select_best_regression_model,
)


# ==========================================================
# FREQUENCY HELPERS
# ==========================================================

FREQUENCY_MAP = {
    "daily": "D",
    "weekly": "W",
    "monthly": "M",
    "D": "D",
    "W": "W",
    "M": "M",
}


def get_problem_frequency(problem):
    """
    Convert the human-readable forecast frequency into
    the frequency format used by the time-series engine.
    """

    frequency_name = problem.get(
        "frequency",
        "daily",
    )

    if frequency_name not in FREQUENCY_MAP:
        raise ValueError(
            f"Unsupported forecast frequency: "
            f"{frequency_name}"
        )

    return FREQUENCY_MAP[
        frequency_name
    ]


# ==========================================================
# PREPARE RAW FORECAST DATASET
# ==========================================================

def prepare_forecast_dataset(
    dataframes,
    problem_name,
    cutoff_date=None,
):
    """
    Prepare the raw feature DataFrame for a forecasting
    problem.

    cutoff_date is optional.

    When supplied, observations after the cutoff are
    excluded. This allows the dashboard to use a common
    business forecasting date across departments.
    """

    problem = get_forecast_problem(
        problem_name
    )

    feature_set = problem[
        "feature_set"
    ]

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    if feature_set not in dataframes:
        raise ValueError(
            f"Feature set '{feature_set}' "
            f"was not found."
        )

    df = dataframes[
        feature_set
    ].copy()

    if df.empty:
        return (
            pd.DataFrame(),
            problem,
        )

    required_columns = [
        date_column,
        target_column,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{missing_columns}"
        )

    # ------------------------------------------------------
    # CLEAN DATE
    # ------------------------------------------------------

    df[date_column] = pd.to_datetime(
        df[date_column],
        errors="coerce",
        utc=True,
    )

    # ------------------------------------------------------
    # CLEAN TARGET
    # ------------------------------------------------------

    df[target_column] = pd.to_numeric(
        df[target_column],
        errors="coerce",
    )

    # ------------------------------------------------------
    # REMOVE INVALID ROWS
    # ------------------------------------------------------

    df = df.dropna(
        subset=[
            date_column,
            target_column,
        ]
    )

    # ------------------------------------------------------
    # OPTIONAL BUSINESS CUTOFF
    # ------------------------------------------------------

    if cutoff_date is not None:

        cutoff = pd.to_datetime(
            cutoff_date,
            errors="coerce",
            utc=True,
        )

        if pd.isna(cutoff):
            raise ValueError(
                "Invalid cutoff_date."
            )

        df = df[
            df[date_column] <= cutoff
        ]

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    df = df.sort_values(
        date_column
    ).reset_index(
        drop=True
    )

    return (
        df,
        problem,
    )


# ==========================================================
# BUILD MODEL FEATURES
# ==========================================================

def build_model_features(
    df,
    problem,
):
    """
    Build ML-ready features from a regular time series.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    frequency = get_problem_frequency(
        problem
    )

    # ------------------------------------------------------
    # CREATE REGULAR TIME SERIES
    # ------------------------------------------------------

    result = create_regular_time_series(
        df=df,
        date_column=date_column,
        target_column=target_column,
        frequency=frequency,
        fill_missing_target=0,
    )

    if result.empty:
        return (
            pd.DataFrame(),
            pd.Series(dtype=float),
        )

    # ------------------------------------------------------
    # TIME FEATURES
    # ------------------------------------------------------

    result = add_time_features(
        result,
        date_column,
        frequency=frequency,
    )

    # ------------------------------------------------------
    # LAG FEATURES
    # ------------------------------------------------------

    result = add_lag_features(
        result,
        target_column,
        frequency=frequency,
    )

    # ------------------------------------------------------
    # ROLLING FEATURES
    # ------------------------------------------------------

    result = add_rolling_features(
        result,
        target_column,
        frequency=frequency,
    )

    # ------------------------------------------------------
    # GROWTH FEATURES
    # ------------------------------------------------------

    result = add_growth_features(
        result,
        target_column,
        frequency=frequency,
    )

    # ------------------------------------------------------
    # REMOVE INCOMPLETE FEATURE ROWS
    # ------------------------------------------------------

    result = result.dropna().reset_index(
        drop=True
    )

    if result.empty:
        return (
            pd.DataFrame(),
            pd.Series(dtype=float),
        )

    # ------------------------------------------------------
    # EXCLUDE NON-ML COLUMNS
    # ------------------------------------------------------

    excluded_columns = [
        date_column,
        target_column,
    ]

    if "id" in result.columns:
        excluded_columns.append(
            "id"
        )

    if "product_id" in result.columns:
        excluded_columns.append(
            "product_id"
        )

    # ------------------------------------------------------
    # NUMERIC FEATURES
    # ------------------------------------------------------

    feature_columns = [
        column
        for column in result.columns
        if (
            column not in excluded_columns
            and pd.api.types.is_numeric_dtype(
                result[column]
            )
        )
    ]

    X = result[
        feature_columns
    ].copy()

    y = result[
        target_column
    ].copy()

    return (
        X,
        y,
    )


# ==========================================================
# MODEL SELECTION
# ==========================================================

def run_forecast_selection(
    dataframes,
    problem_name,
    cutoff_date=None,
):
    """
    Prepare a forecasting problem and automatically select
    the best regression model or historical baseline.
    """

    df, problem = (
        prepare_forecast_dataset(
            dataframes,
            problem_name,
            cutoff_date=cutoff_date,
        )
    )

    if df.empty:
        return {
            "status": "no_data",
            "problem": problem,
            "message": (
                "No usable data is available "
                "for this forecasting problem."
            ),
        }

    X, y = build_model_features(
        df,
        problem,
    )

    if len(X) < problem[
        "minimum_observations"
    ]:
        return {
            "status": "insufficient_data",
            "problem": problem,
            "observations": len(X),
            "required_observations": (
                problem[
                    "minimum_observations"
                ]
            ),
            "message": (
                f"Only {len(X)} usable "
                "observations remain after "
                "time-series feature engineering. "
                f"At least "
                f"{problem['minimum_observations']} "
                "are required."
            ),
        }

    selection = (
        select_best_regression_model(
            X,
            y,
            minimum_observations=problem[
                "minimum_observations"
            ],
        )
    )

    return {
        "status": selection[
            "status"
        ],

        "problem": problem,

        "observations": len(X),

        "best_model_name": (
            selection.get(
                "best_model_name"
            )
        ),

        "metrics": selection.get(
            "metrics"
        ),

        "model_results": selection.get(
            "model_results",
            [],
        ),

        "reliability": selection.get(
            "reliability"
        ),

        "data_assessment": selection.get(
            "data_assessment"
        ),

        "baseline_metrics": (
            selection.get(
                "baseline_metrics"
            )
        ),

        "baseline_value": (
            selection.get(
                "baseline_value"
            )
        ),

        "selected_method": (
            selection.get(
                "selected_method"
            )
        ),

        "model": selection.get(
            "best_model"
        ),

        "reason": selection.get(
            "reason"
        ),

        "validation_folds": (
            selection.get(
                "validation_folds"
            )
        ),
    }


# ==========================================================
# BUILD HISTORICAL REGULAR SERIES
# ==========================================================

def build_historical_series(
    df,
    problem,
):
    """
    Create the complete historical regular time series.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    frequency = get_problem_frequency(
        problem
    )

    historical = (
        create_regular_time_series(
            df=df,
            date_column=date_column,
            target_column=target_column,
            frequency=frequency,
            fill_missing_target=0,
        )
    )

    if historical.empty:
        return historical

    historical = (
        historical
        .sort_values(
            date_column
        )
        .reset_index(
            drop=True
        )
    )

    return historical


# ==========================================================
# BUILD FEATURE FRAME
# ==========================================================

def build_feature_frame(
    historical_series,
    problem,
):
    """
    Build the complete feature dataframe from a regular
    historical series.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    frequency = get_problem_frequency(
        problem
    )

    result = historical_series.copy()

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


# ==========================================================
# GET MODEL FEATURE COLUMNS
# ==========================================================

def get_feature_columns(
    feature_frame,
    problem,
):
    """
    Return numeric columns used by the ML model.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    excluded_columns = [
        date_column,
        target_column,
    ]

    if "id" in feature_frame.columns:
        excluded_columns.append(
            "id"
        )

    if "product_id" in feature_frame.columns:
        excluded_columns.append(
            "product_id"
        )

    return [
        column
        for column in feature_frame.columns
        if (
            column not in excluded_columns
            and pd.api.types.is_numeric_dtype(
                feature_frame[column]
            )
        )
    ]


# ==========================================================
# NEXT PERIOD DATE
# ==========================================================

def get_next_period_date(
    current_date,
    frequency,
):
    """
    Calculate the next forecast period.
    """

    if frequency == "D":
        return (
            current_date
            + pd.Timedelta(
                days=1
            )
        )

    if frequency == "W":
        return (
            current_date
            + pd.Timedelta(
                weeks=1
            )
        )

    if frequency == "M":
        return (
            current_date
            + pd.offsets.MonthBegin(
                1
            )
        )

    raise ValueError(
        f"Unsupported frequency: "
        f"{frequency}"
    )


# ==========================================================
# RECURSIVE ML FORECAST
# ==========================================================

def generate_ml_forecast(
    historical_series,
    problem,
    model,
    periods,
):
    """
    Generate recursive future predictions using the
    selected ML model.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    frequency = get_problem_frequency(
        problem
    )

    working_series = (
        historical_series.copy()
    )

    forecasts = []

    # ------------------------------------------------------
    # DETERMINE MODEL FEATURES
    # ------------------------------------------------------

    historical_features = (
        build_feature_frame(
            working_series,
            problem,
        )
    )

    feature_columns = (
        get_feature_columns(
            historical_features,
            problem,
        )
    )

    if not feature_columns:
        raise ValueError(
            "No usable ML features were created."
        )

    # ------------------------------------------------------
    # RECURSIVE FORECAST LOOP
    # ------------------------------------------------------

    for step in range(
        1,
        periods + 1,
    ):

        last_date = (
            working_series[
                date_column
            ].max()
        )

        next_date = (
            get_next_period_date(
                last_date,
                frequency,
            )
        )

        future_row = pd.DataFrame({
            date_column: [
                next_date
            ],
            target_column: [
                np.nan
            ],
        })

        combined = pd.concat(
            [
                working_series,
                future_row,
            ],
            ignore_index=True,
        )

        # --------------------------------------------------
        # BUILD FUTURE FEATURES
        # --------------------------------------------------

        feature_frame = (
            build_feature_frame(
                combined,
                problem,
            )
        )

        future_features = (
            feature_frame.iloc[
                [-1]
            ]
        )

        # --------------------------------------------------
        # CHECK MISSING FEATURES
        # --------------------------------------------------

        missing_features = [
            column
            for column in feature_columns
            if (
                column not in future_features.columns
                or pd.isna(
                    future_features.iloc[
                        0
                    ][column]
                )
            )
        ]

        if missing_features:
            raise ValueError(
                "Unable to generate complete "
                "future features. Missing values "
                f"in: {missing_features}"
            )

        X_future = (
            future_features[
                feature_columns
            ]
            .astype(float)
        )

        # --------------------------------------------------
        # PREDICT
        # --------------------------------------------------

        prediction = float(
            model.predict(
                X_future
            )[0]
        )

        # Business quantities cannot be negative.
        prediction = max(
            0.0,
            prediction,
        )

        forecasts.append({
            "period": step,
            "date": next_date,
            "predicted_value": prediction,
            "method": "ml_model",
        })

        # --------------------------------------------------
        # FEED PREDICTION INTO FUTURE HISTORY
        # --------------------------------------------------

        working_series = pd.concat(
            [
                working_series,
                pd.DataFrame({
                    date_column: [
                        next_date
                    ],
                    target_column: [
                        prediction
                    ],
                }),
            ],
            ignore_index=True,
        )

    return pd.DataFrame(
        forecasts
    )


# ==========================================================
# BASELINE FORECAST
# ==========================================================

def generate_baseline_forecast(
    historical_series,
    problem,
    periods,
    baseline_value=None,
):
    """
    Generate future forecasts using the complete
    historical regular-series mean.
    """

    date_column = problem[
        "date_column"
    ]

    target_column = problem[
        "target_column"
    ]

    frequency = get_problem_frequency(
        problem
    )

    # ------------------------------------------------------
    # USE COMPLETE HISTORICAL SERIES
    # ------------------------------------------------------

    if baseline_value is None:

        baseline_value = float(
            historical_series[
                target_column
            ].mean()
        )

    baseline_value = max(
        0.0,
        float(
            baseline_value
        ),
    )

    last_date = (
        historical_series[
            date_column
        ].max()
    )

    forecasts = []

    for step in range(
        1,
        periods + 1,
    ):

        next_date = (
            get_next_period_date(
                last_date,
                frequency,
            )
        )

        forecasts.append({
            "period": step,
            "date": next_date,
            "predicted_value": (
                baseline_value
            ),
            "method": (
                "historical_mean"
            ),
        })

        last_date = next_date

    return pd.DataFrame(
        forecasts
    )


# ==========================================================
# BASELINE RELIABILITY
# ==========================================================

def build_baseline_reliability(
    selection,
    historical_observations,
):
    """
    Build an honest reliability description when the
    historical-mean baseline is selected.

    A baseline selection does NOT mean that there is
    insufficient data. It means that the candidate ML
    models failed to outperform the historical baseline
    during validation.
    """

    if historical_observations < 1:

        return {
            "level": "insufficient",
            "reason": (
                "No usable historical observations "
                "are available for forecasting."
            ),
        }

    if historical_observations < 14:

        return {
            "level": "insufficient",
            "reason": (
                "The historical dataset is too small "
                "to establish a reliable forecast."
            ),
        }

    selection_status = (
        selection.get(
            "status"
        )
        if selection
        else None
    )

    if selection_status == "insufficient_data":

        return {
            "level": "insufficient",
            "reason": (
                "The available historical data is "
                "insufficient for reliable forecasting."
            ),
        }

    baseline_metrics = (
        selection.get(
            "baseline_metrics"
        )
        if selection
        else None
    )

    if baseline_metrics:

        return {
            "level": "low",
            "reason": (
                "The historical-mean baseline was "
                "selected because the candidate ML "
                "models did not outperform it during "
                "walk-forward validation. The forecast "
                "is useful as a baseline decision-support "
                "signal, but it should not be treated as "
                "a high-confidence prediction."
            ),
        }

    return {
        "level": "low",
        "reason": (
            "The historical-mean baseline is being used "
            "instead of an ML model. Additional historical "
            "data and validation would improve confidence."
        ),
    }


# ==========================================================
# ACTUAL FUTURE FORECAST
# ==========================================================

def generate_forecast(
    dataframes,
    problem_name,
    periods=8,
    cutoff_date=None,
):
    """
    Generate actual future forecasts.

    Parameters
    ----------
    dataframes:
        Business DataFrames loaded by the ML pipeline.

    problem_name:
        Forecast problem identifier.

    periods:
        Number of future periods.

    cutoff_date:
        Optional common business cutoff date.

        If omitted, each forecasting problem uses the
        latest available observation in its own feature set.

        If supplied, all observations after this date are
        excluded, allowing multiple departments to share
        one forecasting cutoff.
    """

    if periods < 1:
        raise ValueError(
            "Forecast periods must be at least 1."
        )

    if periods > 52:
        raise ValueError(
            "Forecast periods cannot exceed 52."
        )

    # ------------------------------------------------------
    # PREPARE DATA
    # ------------------------------------------------------

    df, problem = (
        prepare_forecast_dataset(
            dataframes,
            problem_name,
            cutoff_date=cutoff_date,
        )
    )

    if df.empty:
        return {
            "status": "no_data",
            "problem": problem,
            "forecast": [],
            "reliability": {
                "level": "insufficient",
                "reason": (
                    "No usable data is available "
                    "for this forecasting problem."
                ),
            },
            "message": (
                "No usable data is available "
                "for this forecasting problem."
            ),
        }

    # ------------------------------------------------------
    # COMPLETE HISTORICAL SERIES
    # ------------------------------------------------------

    historical_series = (
        build_historical_series(
            df,
            problem,
        )
    )

    if historical_series.empty:
        return {
            "status": "no_data",
            "problem": problem,
            "forecast": [],
            "reliability": {
                "level": "insufficient",
                "reason": (
                    "Unable to create a historical "
                    "time series."
                ),
            },
            "message": (
                "Unable to create a historical "
                "time series."
            ),
        }

    # ------------------------------------------------------
    # COMPLETE HISTORICAL MEAN
    # ------------------------------------------------------

    target_column = problem[
        "target_column"
    ]

    historical_values = (
        historical_series[
            target_column
        ].astype(float)
    )

    complete_historical_mean = float(
        historical_values.mean()
    )

    # ------------------------------------------------------
    # MODEL SELECTION
    # ------------------------------------------------------

    selection = (
        run_forecast_selection(
            dataframes,
            problem_name,
            cutoff_date=cutoff_date,
        )
    )

    # ------------------------------------------------------
    # DETERMINE FORECAST METHOD
    # ------------------------------------------------------

    selected_method = (
        selection.get(
            "selected_method"
        )
        if selection
        else None
    )

    # ------------------------------------------------------
    # SAFE BASELINE / NO-MODEL PATH
    # ------------------------------------------------------

    baseline_statuses = {
        "no_data",
        "insufficient_data",
        "low_variation",
        "insufficient_validation_data",
        "no_model_succeeded",
        "baseline_better",
    }

    if (
        selection.get(
            "status"
        )
        in baseline_statuses
        or selected_method
        != "ml_model"
        or selection.get(
            "model"
        ) is None
    ):

        forecast_df = (
            generate_baseline_forecast(
                historical_series=(
                    historical_series
                ),
                problem=problem,
                periods=periods,
                baseline_value=(
                    complete_historical_mean
                ),
            )
        )

        selected_method = (
            "historical_mean"
        )

    # ------------------------------------------------------
    # ML PATH
    # ------------------------------------------------------

    else:

        forecast_df = (
            generate_ml_forecast(
                historical_series=(
                    historical_series
                ),
                problem=problem,
                model=selection[
                    "model"
                ],
                periods=periods,
            )
        )

        selected_method = (
            "ml_model"
        )

    # ------------------------------------------------------
    # FORMAT DATES
    # ------------------------------------------------------

    date_column = problem[
        "date_column"
    ]

    if not forecast_df.empty:

        forecast_df[
            date_column
        ] = pd.to_datetime(
            forecast_df[
                date_column
            ],
            utc=True,
        )

        forecast_df[
            date_column
        ] = (
            forecast_df[
                date_column
            ]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

    # ------------------------------------------------------
    # JSON RECORDS
    # ------------------------------------------------------

    forecast_records = (
        forecast_df
        .to_dict(
            orient="records"
        )
    )

    # ------------------------------------------------------
    # HISTORICAL SUMMARY
    # ------------------------------------------------------

    historical_total = float(
        historical_values.sum()
    )

    # ------------------------------------------------------
    # RELIABILITY
    # ------------------------------------------------------

    if selected_method == "historical_mean":

        reliability = (
            build_baseline_reliability(
                selection=selection,
                historical_observations=len(
                    historical_series
                ),
            )
        )

    else:

        reliability = (
            selection.get(
                "reliability"
            )
            if selection
            else None
        )

        if reliability is None:

            reliability = {
                "level": "low",
                "reason": (
                    "An ML model was selected, but "
                    "the validation reliability "
                    "assessment was unavailable."
                ),
            }

    # ------------------------------------------------------
    # FINAL MESSAGE
    # ------------------------------------------------------

    if selected_method == "ml_model":

        message = (
            "Forecast generated using the "
            "automatically selected ML model."
        )

    else:

        message = (
            "Forecast generated using the complete "
            "historical-mean baseline because ML "
            "models did not outperform it during "
            "validation."
        )

    # ------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------

    return {
        "status": "success",

        "problem": problem,

        "selected_method": (
            selected_method
        ),

        "model_name": (
            selection.get(
                "best_model_name"
            )
            if selection
            else None
        ),

        "forecast_periods": periods,

        "frequency": problem.get(
            "frequency"
        ),

        "cutoff_date": (
            cutoff_date
            if cutoff_date is not None
            else None
        ),

        "historical_observations": len(
            historical_series
        ),

        "historical_mean": (
            complete_historical_mean
        ),

        "historical_total": (
            historical_total
        ),

        "reliability": reliability,

        "validation_metrics": (
            selection.get(
                "metrics"
            )
            if selection
            else None
        ),

        "baseline_metrics": (
            selection.get(
                "baseline_metrics"
            )
            if selection
            else None
        ),

        "forecast": forecast_records,

        "message": message,
    }