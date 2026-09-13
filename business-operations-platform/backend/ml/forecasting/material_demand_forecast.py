import math
from typing import Any, Dict, List

import pandas as pd

from ml.models.model_selector import (
    select_best_regression_model,
)
from ml.models.model_registry import (
    get_regression_models,
)


# ==========================================================
# HELPERS
# ==========================================================

def _safe_float(
    value,
    default=0.0,
):
    try:
        if value is None:
            return default

        value = float(value)

        if math.isnan(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _baseline_reliability(
    reason=None,
    insufficient=False,
):
    """
    Return a consistent reliability structure for forecasts
    that use the historical-mean baseline.
    """

    if insufficient:
        return {
            "level": "insufficient",
            "reason": (
                reason
                or
                "Not enough historical material-demand "
                "data was available for reliable "
                "material-level forecasting."
            ),
        }

    return {
        "level": "low",
        "reason": (
            reason
            or
            "The historical-mean baseline was selected "
            "because the candidate ML models did not "
            "outperform it during validation. The forecast "
            "is useful as a baseline decision-support "
            "signal, but it should not be treated as a "
            "high-confidence prediction."
        ),
    }


def _build_historical_mean_forecast(
    history,
    material_id,
    periods,
    reliability,
    selection_reason=None,
):
    """
    Build a historical-mean forecast while preserving the
    genuine latest material-demand date.

    No artificial historical dates or demand observations
    are created.
    """

    baseline = _safe_float(
        history[
            "outbound_quantity"
        ].mean()
    )

    last_date = history[
        "date"
    ].max()

    forecasts = []

    for period in range(
        1,
        periods + 1,
    ):
        next_date = (
            last_date
            + pd.Timedelta(
                weeks=1
            )
        )

        forecasts.append({
            "period": period,
            "date": next_date.strftime(
                "%Y-%m-%d"
            ),
            "predicted_value": baseline,
            "method": "historical_mean",
        })

        last_date = next_date

    result = {
        "status": "success",
        "material_id": material_id,
        "selected_method": "historical_mean",
        "model_name": None,
        "historical_observations": len(
            history
        ),
        "historical_mean": baseline,
        "reliability": reliability,
        "forecast": forecasts,
    }

    if selection_reason:
        result["selection_reason"] = (
            selection_reason
        )

    return result


# ==========================================================
# PREPARE MATERIAL DEMAND DATA
# ==========================================================

def prepare_material_demand_data(
    material_demand_df,
):
    """
    Prepare material-demand history.

    Expected columns:

        date
        material_id
        inbound_quantity
        outbound_quantity
    """

    if (
        material_demand_df is None
        or material_demand_df.empty
    ):
        return pd.DataFrame()

    df = material_demand_df.copy()

    required_columns = [
        "date",
        "material_id",
        "outbound_quantity",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Material demand data is missing "
            f"required columns: {missing_columns}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
        utc=True,
    )

    df["material_id"] = pd.to_numeric(
        df["material_id"],
        errors="coerce",
    )

    df["outbound_quantity"] = pd.to_numeric(
        df["outbound_quantity"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "date",
            "material_id",
            "outbound_quantity",
        ]
    )

    # Consumption cannot be negative.
    df["outbound_quantity"] = (
        df["outbound_quantity"]
        .clip(lower=0)
    )

    return (
        df.sort_values(
            [
                "material_id",
                "date",
            ]
        )
        .reset_index(drop=True)
    )


# ==========================================================
# BUILD WEEKLY MATERIAL DEMAND
# ==========================================================

def build_weekly_material_demand(
    material_demand_df,
):
    """
    Aggregate material consumption into weekly demand.

    Each material receives its own independent time series.
    """

    df = prepare_material_demand_data(
        material_demand_df
    )

    if df.empty:
        return pd.DataFrame()

    weekly_parts = []

    for material_id, group in df.groupby(
        "material_id"
    ):
        group = group.copy()

        group = group.set_index(
            "date"
        )

        weekly = (
            group[
                "outbound_quantity"
            ]
            .resample("W")
            .sum()
            .fillna(0)
            .reset_index()
        )

        weekly["material_id"] = (
            material_id
        )

        weekly_parts.append(
            weekly
        )

    if not weekly_parts:
        return pd.DataFrame()

    result = pd.concat(
        weekly_parts,
        ignore_index=True,
    )

    return result[
        [
            "date",
            "material_id",
            "outbound_quantity",
        ]
    ].sort_values(
        [
            "material_id",
            "date",
        ]
    ).reset_index(
        drop=True
    )


# ==========================================================
# MATERIAL FORECAST USING HISTORY
# ==========================================================

def forecast_single_material(
    material_df,
    material_id,
    periods=8,
):
    """
    Forecast demand for one material.

    The function automatically compares the available
    regression models against a historical-mean baseline.

    If no ML model genuinely beats the baseline, the
    historical baseline is used.

    Reliability is always explicitly reported.
    """

    if (
        material_df is None
        or material_df.empty
    ):
        return {
            "status": "no_data",
            "material_id": material_id,
            "forecast": [],
            "reliability": {
                "level": "insufficient",
                "reason": (
                    "No material-demand history "
                    "was available."
                ),
            },
        }

    if periods < 1:
        raise ValueError(
            "Forecast periods must be at least 1."
        )

    if periods > 52:
        raise ValueError(
            "Forecast periods cannot exceed 52."
        )

    df = material_df.copy()

    df = df.sort_values(
        "date"
    ).reset_index(
        drop=True
    )

    # ------------------------------------------------------
    # COMPLETE WEEKLY HISTORY
    # ------------------------------------------------------

    history = df[
        [
            "date",
            "outbound_quantity",
        ]
    ].copy()

    history = history.set_index(
        "date"
    )

    history = (
        history[
            "outbound_quantity"
        ]
        .resample("W")
        .sum()
        .fillna(0)
    )

    history = history.reset_index()

    if history.empty:
        return {
            "status": "no_data",
            "material_id": material_id,
            "forecast": [],
            "reliability": {
                "level": "insufficient",
                "reason": (
                    "No usable weekly material-demand "
                    "history was available."
                ),
            },
        }

    # ------------------------------------------------------
    # INSUFFICIENT HISTORY
    # ------------------------------------------------------

    if len(history) < 12:
        baseline = _safe_float(
            history[
                "outbound_quantity"
            ].mean()
        )

        reliability = _baseline_reliability(
            reason=(
                "Only "
                f"{len(history)} weekly observations "
                "were available. At least 12 are required "
                "for the material-level ML model."
            ),
            insufficient=True,
        )

        return _build_historical_mean_forecast(
            history=history,
            material_id=material_id,
            periods=periods,
            reliability=reliability,
        )

    # ------------------------------------------------------
    # FEATURE ENGINEERING
    # ------------------------------------------------------

    working = history.copy()

    working["trend"] = range(
        len(working)
    )

    working["lag_1"] = (
        working[
            "outbound_quantity"
        ]
        .shift(1)
    )

    working["lag_2"] = (
        working[
            "outbound_quantity"
        ]
        .shift(2)
    )

    working["lag_4"] = (
        working[
            "outbound_quantity"
        ]
        .shift(4)
    )

    working["lag_8"] = (
        working[
            "outbound_quantity"
        ]
        .shift(8)
    )

    working["rolling_4"] = (
        working[
            "outbound_quantity"
        ]
        .shift(1)
        .rolling(4)
        .mean()
    )

    working["rolling_8"] = (
        working[
            "outbound_quantity"
        ]
        .shift(1)
        .rolling(8)
        .mean()
    )

    working["rolling_12"] = (
        working[
            "outbound_quantity"
        ]
        .shift(1)
        .rolling(12)
        .mean()
    )

    # ------------------------------------------------------
    # TIME FEATURES
    # ------------------------------------------------------

    working["month"] = (
        working["date"]
        .dt.month
    )

    working["week_of_year"] = (
        working["date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    # ------------------------------------------------------
    # REMOVE INCOMPLETE FEATURE ROWS
    # ------------------------------------------------------

    working = (
        working
        .dropna()
        .reset_index(drop=True)
    )

    if len(working) < 12:
        reliability = _baseline_reliability(
            reason=(
                "Insufficient complete feature "
                "history remained after feature "
                "engineering."
            ),
            insufficient=True,
        )

        return _build_historical_mean_forecast(
            history=history,
            material_id=material_id,
            periods=periods,
            reliability=reliability,
        )

    # ------------------------------------------------------
    # TRAINING DATA
    # ------------------------------------------------------

    feature_columns = [
        "trend",
        "lag_1",
        "lag_2",
        "lag_4",
        "lag_8",
        "rolling_4",
        "rolling_8",
        "rolling_12",
        "month",
        "week_of_year",
    ]

    X = working[
        feature_columns
    ].copy()

    y = working[
        "outbound_quantity"
    ].copy()

    # ------------------------------------------------------
    # MODEL SELECTION
    # ------------------------------------------------------

    selection = (
        select_best_regression_model(
            X,
            y,
            candidate_models=(
                get_regression_models()
            ),
            minimum_observations=12,
        )
    )

    # ------------------------------------------------------
    # BASELINE PATH
    # ------------------------------------------------------

    if (
        selection["status"]
        != "success"
        or selection.get(
            "best_model"
        ) is None
    ):
        selection_reason = selection.get(
            "reason"
        )

        reliability = _baseline_reliability(
            reason=(
                selection_reason
                or
                "The candidate ML models could not "
                "produce a reliable model, so the "
                "historical-mean baseline was used."
            )
        )

        return _build_historical_mean_forecast(
            history=history,
            material_id=material_id,
            periods=periods,
            reliability=reliability,
            selection_reason=selection_reason,
        )

    # ------------------------------------------------------
    # ML MODEL PATH
    # ------------------------------------------------------

    model = selection[
        "best_model"
    ]

    # ------------------------------------------------------
    # RECURSIVE FORECAST
    # ------------------------------------------------------

    working_history = history.copy()

    forecasts = []

    for period in range(
        1,
        periods + 1,
    ):
        last_date = (
            working_history[
                "date"
            ].max()
        )

        next_date = (
            last_date
            + pd.Timedelta(
                weeks=1
            )
        )

        temporary = (
            working_history.copy()
        )

        temporary["trend"] = range(
            len(temporary)
        )

        temporary["lag_1"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(1)
        )

        temporary["lag_2"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(2)
        )

        temporary["lag_4"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(4)
        )

        temporary["lag_8"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(8)
        )

        temporary["rolling_4"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(1)
            .rolling(4)
            .mean()
        )

        temporary["rolling_8"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(1)
            .rolling(8)
            .mean()
        )

        temporary["rolling_12"] = (
            temporary[
                "outbound_quantity"
            ]
            .shift(1)
            .rolling(12)
            .mean()
        )

        temporary["month"] = (
            temporary["date"]
            .dt.month
        )

        temporary["week_of_year"] = (
            temporary["date"]
            .dt.isocalendar()
            .week
            .astype(int)
        )

        future_features = pd.DataFrame({
            "trend": [
                len(temporary)
            ],
            "lag_1": [
                temporary[
                    "outbound_quantity"
                ].iloc[-1]
            ],
            "lag_2": [
                temporary[
                    "outbound_quantity"
                ].iloc[-2]
            ],
            "lag_4": [
                temporary[
                    "outbound_quantity"
                ].iloc[-4]
            ],
            "lag_8": [
                temporary[
                    "outbound_quantity"
                ].iloc[-8]
            ],
            "rolling_4": [
                temporary[
                    "outbound_quantity"
                ]
                .iloc[-4:]
                .mean()
            ],
            "rolling_8": [
                temporary[
                    "outbound_quantity"
                ]
                .iloc[-8:]
                .mean()
            ],
            "rolling_12": [
                temporary[
                    "outbound_quantity"
                ]
                .iloc[-12:]
                .mean()
            ],
            "month": [
                next_date.month
            ],
            "week_of_year": [
                int(
                    next_date.isocalendar()
                    .week
                )
            ],
        })

        prediction = float(
            model.predict(
                future_features[
                    feature_columns
                ]
            )[0]
        )

        prediction = max(
            0.0,
            prediction,
        )

        forecasts.append({
            "period": period,
            "date": next_date.strftime(
                "%Y-%m-%d"
            ),
            "predicted_value": prediction,
            "method": "ml_model",
        })

        working_history = pd.concat(
            [
                working_history,
                pd.DataFrame({
                    "date": [
                        next_date
                    ],
                    "outbound_quantity": [
                        prediction
                    ],
                }),
            ],
            ignore_index=True,
        )

    return {
        "status": "success",
        "material_id": material_id,
        "selected_method": "ml_model",
        "model_name": (
            selection[
                "best_model_name"
            ]
        ),
        "historical_observations": len(
            history
        ),
        "historical_mean": _safe_float(
            history[
                "outbound_quantity"
            ].mean()
        ),
        "reliability": selection.get(
            "reliability"
        ),
        "validation_metrics": (
            selection.get(
                "metrics"
            )
        ),
        "selection_reason": (
            selection.get(
                "reason"
            )
        ),
        "forecast": forecasts,
    }


# ==========================================================
# FORECAST ALL MATERIALS
# ==========================================================

def generate_material_demand_forecasts(
    material_demand_df,
    periods=8,
):
    """
    Generate an independent demand forecast for every
    material with sufficient historical data.

    The returned structure is intentionally kept compatible
    with the inventory recommendation layer.
    """

    if periods < 1:
        raise ValueError(
            "Forecast periods must be at least 1."
        )

    if periods > 52:
        raise ValueError(
            "Forecast periods cannot exceed 52."
        )

    weekly = (
        build_weekly_material_demand(
            material_demand_df
        )
    )

    if weekly.empty:
        return {
            "status": "no_data",
            "frequency": "weekly",
            "forecast_periods": periods,
            "material_count": 0,
            "materials": [],
            "message": (
                "No usable material-demand "
                "history is available."
            ),
        }

    material_results = []

    for material_id, material_df in (
        weekly.groupby(
            "material_id"
        )
    ):
        result = forecast_single_material(
            material_df=material_df,
            material_id=material_id,
            periods=periods,
        )

        material_results.append(
            result
        )

    return {
        "status": "success",
        "frequency": "weekly",
        "forecast_periods": periods,
        "material_count": len(
            material_results
        ),
        "materials": material_results,
    }