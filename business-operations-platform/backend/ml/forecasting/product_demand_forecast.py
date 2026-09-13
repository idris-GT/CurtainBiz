import math

import pandas as pd

from app.database.connection import get_connection
from ml.models.model_selector import select_best_regression_model
from ml.models.model_registry import get_regression_models


# ==========================================================
# SAFE NUMBER
# ==========================================================

def _safe_float(value, default=0.0):
    try:
        value = float(value)
        return default if math.isnan(value) else value
    except (TypeError, ValueError):
        return default


# ==========================================================
# LOAD PRODUCT NAMES
# ==========================================================

def _load_product_names_from_database():
    """
    Load active product names directly from the products
    master table.

    This is used only when the upstream ML pipeline does not
    preserve the original products dataframe.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name
            FROM products
            WHERE is_active = TRUE
            ORDER BY id;
            """
        )

        rows = cursor.fetchall()

        return {
            str(row[0]): str(row[1])
            for row in rows
            if row[0] is not None and row[1]
        }

    finally:
        connection.close()


# ==========================================================
# PREPARE PRODUCT DEMAND DATA
# ==========================================================

def _prepare(df):
    if df is None or df.empty:
        return pd.DataFrame()

    required = [
        "date",
        "product_id",
        "quantity",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Product demand data is missing required "
            f"columns: {missing}"
        )

    result = df.copy()

    result["date"] = pd.to_datetime(
        result["date"],
        errors="coerce",
        utc=True,
    )

    result["product_id"] = pd.to_numeric(
        result["product_id"],
        errors="coerce",
    )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce",
    )

    result = result.dropna(
        subset=required
    )

    result["quantity"] = result[
        "quantity"
    ].clip(lower=0)

    return (
        result
        .sort_values(
            ["product_id", "date"]
        )
        .reset_index(drop=True)
    )


# ==========================================================
# WEEKLY PRODUCT DEMAND
# ==========================================================

def _weekly(df):
    df = _prepare(df)

    if df.empty:
        return pd.DataFrame()

    parts = []

    for product_id, group in df.groupby(
        "product_id"
    ):
        series = (
            group
            .set_index("date")["quantity"]
            .resample("W")
            .sum()
            .fillna(0)
            .reset_index()
        )

        series["product_id"] = product_id

        parts.append(series)

    if not parts:
        return pd.DataFrame()

    return (
        pd.concat(
            parts,
            ignore_index=True,
        )[
            [
                "date",
                "product_id",
                "quantity",
            ]
        ]
        .sort_values(
            [
                "product_id",
                "date",
            ]
        )
        .reset_index(drop=True)
    )


# ==========================================================
# FEATURE ENGINEERING
# ==========================================================

def _features(history):
    w = history.copy()

    w["trend"] = range(len(w))

    w["month"] = (
        w["date"].dt.month
    )

    w["week_of_year"] = (
        w["date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    for lag in (
        1,
        2,
        4,
        8,
    ):
        w[f"lag_{lag}"] = (
            w["quantity"]
            .shift(lag)
        )

    for window in (
        4,
        8,
        12,
    ):
        w[f"rolling_{window}"] = (
            w["quantity"]
            .shift(1)
            .rolling(window)
            .mean()
        )

    return (
        w
        .dropna()
        .reset_index(drop=True)
    )


FEATURES = [
    "trend",
    "month",
    "week_of_year",
    "lag_1",
    "lag_2",
    "lag_4",
    "lag_8",
    "rolling_4",
    "rolling_8",
    "rolling_12",
]


# ==========================================================
# HISTORICAL-MEAN BASELINE
# ==========================================================

def _baseline(history, periods):
    value = max(
        0.0,
        _safe_float(
            history["quantity"].mean()
        ),
    )

    last = history["date"].max()

    forecasts = []

    for period in range(
        1,
        periods + 1,
    ):
        last = (
            last
            + pd.Timedelta(
                weeks=1
            )
        )

        forecasts.append(
            {
                "period": period,
                "date": last.strftime(
                    "%Y-%m-%d"
                ),
                "predicted_value": value,
                "method": "historical_mean",
            }
        )

    return forecasts


# ==========================================================
# RECURSIVE ML FORECAST
# ==========================================================

def _recursive_ml(
    history,
    model,
    periods,
):
    working = history.copy()

    forecasts = []

    for period in range(
        1,
        periods + 1,
    ):
        last = working["date"].max()

        next_date = (
            last
            + pd.Timedelta(
                weeks=1
            )
        )

        temp = _features(
            working
        )

        if temp.empty:
            return None

        latest = temp.iloc[-1:]

        prediction = max(
            0.0,
            float(
                model.predict(
                    latest[FEATURES]
                )[0]
            ),
        )

        forecasts.append(
            {
                "period": period,
                "date": next_date.strftime(
                    "%Y-%m-%d"
                ),
                "predicted_value": prediction,
                "method": "ml_model",
            }
        )

        working = pd.concat(
            [
                working,
                pd.DataFrame(
                    {
                        "date": [
                            next_date
                        ],
                        "quantity": [
                            prediction
                        ],
                    }
                ),
            ],
            ignore_index=True,
        )

    return forecasts


# ==========================================================
# SINGLE PRODUCT FORECAST
# ==========================================================

def forecast_single_product(
    product_df,
    product_id,
    periods=8,
):
    history = (
        product_df[
            [
                "date",
                "quantity",
            ]
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )

    baseline = max(
        0.0,
        _safe_float(
            history["quantity"].mean()
        ),
    )

    # ------------------------------------------------------
    # INSUFFICIENT HISTORY
    # ------------------------------------------------------

    if len(history) < 12:
        return {
            "status": "success",
            "product_id": product_id,
            "selected_method": "historical_mean",
            "model_name": None,
            "historical_observations": len(
                history
            ),
            "historical_mean": baseline,
            "forecast": _baseline(
                history,
                periods,
            ),
            "reliability": {
                "level": "low",
                "reason": (
                    "Insufficient historical "
                    "observations for reliable "
                    "product-level ML validation."
                ),
            },
        }

    # ------------------------------------------------------
    # FEATURE ENGINEERING
    # ------------------------------------------------------

    frame = _features(
        history
    )

    if len(frame) < 12:
        return {
            "status": "success",
            "product_id": product_id,
            "selected_method": "historical_mean",
            "model_name": None,
            "historical_observations": len(
                history
            ),
            "historical_mean": baseline,
            "forecast": _baseline(
                history,
                periods,
            ),
            "reliability": {
                "level": "low",
                "reason": (
                    "Insufficient complete "
                    "feature history remained "
                    "after time-series feature "
                    "engineering."
                ),
            },
        }

    # ------------------------------------------------------
    # AUTOMATIC MODEL SELECTION
    # ------------------------------------------------------

    selection = (
        select_best_regression_model(
            frame[FEATURES],
            frame["quantity"],
            candidate_models=(
                get_regression_models()
            ),
            minimum_observations=12,
        )
    )

    # ------------------------------------------------------
    # HISTORICAL-MEAN FALLBACK
    # ------------------------------------------------------

    if (
        selection.get("status")
        != "success"
        or selection.get(
            "best_model"
        )
        is None
        or selection.get(
            "selected_method"
        )
        != "ml_model"
    ):
        return {
            "status": "success",
            "product_id": product_id,
            "selected_method": "historical_mean",
            "model_name": None,
            "historical_observations": len(
                history
            ),
            "historical_mean": baseline,
            "forecast": _baseline(
                history,
                periods,
            ),
            "reliability": {
                "level": "low",
                "reason": (
                    selection.get(
                        "reason"
                    )
                    or (
                        "The candidate ML "
                        "models did not "
                        "outperform the "
                        "historical baseline."
                    )
                ),
            },
        }

    # ------------------------------------------------------
    # ML FORECAST
    # ------------------------------------------------------

    forecasts = _recursive_ml(
        history,
        selection["best_model"],
        periods,
    )

    # ------------------------------------------------------
    # SAFE FALLBACK
    # ------------------------------------------------------

    if forecasts is None:
        return {
            "status": "success",
            "product_id": product_id,
            "selected_method": "historical_mean",
            "model_name": None,
            "historical_observations": len(
                history
            ),
            "historical_mean": baseline,
            "forecast": _baseline(
                history,
                periods,
            ),
            "reliability": {
                "level": "low",
                "reason": (
                    "The selected ML model "
                    "could not produce "
                    "complete future features."
                ),
            },
        }

    # ------------------------------------------------------
    # SUCCESSFUL ML FORECAST
    # ------------------------------------------------------

    return {
        "status": "success",
        "product_id": product_id,
        "selected_method": "ml_model",
        "model_name": selection.get(
            "best_model_name"
        ),
        "historical_observations": len(
            history
        ),
        "historical_mean": baseline,
        "forecast": forecasts,
        "reliability": selection.get(
            "reliability"
        ),
        "validation_metrics": selection.get(
            "metrics"
        ),
        "baseline_metrics": selection.get(
            "baseline_metrics"
        ),
    }


# ==========================================================
# ALL PRODUCT FORECASTS
# ==========================================================

def generate_product_demand_forecasts(
    product_demand_df,
    products_df=None,
    periods=8,
):
    weekly = _weekly(
        product_demand_df
    )

    if weekly.empty:
        return {
            "status": "no_data",
            "products": [],
            "message": (
                "No usable product-demand "
                "history is available."
            ),
        }

    # ------------------------------------------------------
    # PRODUCT NAME MAP
    # ------------------------------------------------------

    names = {}

    # First preference:
    # use products dataframe if the pipeline provides it.
    if (
        products_df is not None
        and not products_df.empty
        and "id" in products_df.columns
    ):
        name_col = next(
            (
                column
                for column in (
                    "name",
                    "product_name",
                    "title",
                )
                if column
                in products_df.columns
            ),
            None,
        )

        if name_col:
            names = {
                str(row["id"]): str(
                    row[name_col]
                )
                for _, row
                in products_df.iterrows()
                if row["id"] is not None
                and row[name_col]
            }

    # ------------------------------------------------------
    # DATABASE FALLBACK
    # ------------------------------------------------------

    if not names:
        try:
            names = (
                _load_product_names_from_database()
            )
        except Exception as exc:
            print(
                "Product name lookup failed:",
                exc,
            )

    # ------------------------------------------------------
    # FORECAST EACH PRODUCT
    # ------------------------------------------------------

    results = []

    for product_id, group in weekly.groupby(
        "product_id"
    ):
        result = forecast_single_product(
            group,
            product_id,
            periods,
        )

        result["product_name"] = (
            names.get(
                str(product_id),
                f"Product #{int(product_id)}",
            )
        )

        values = [
            _safe_float(
                item.get(
                    "predicted_value"
                )
            )
            for item
            in result.get(
                "forecast",
                [],
            )
        ]

        result["forecast_total"] = sum(
            values
        )

        result[
            "average_weekly_demand"
        ] = (
            sum(values) / len(values)
            if values
            else 0.0
        )

        results.append(result)

    # ------------------------------------------------------
    # HIGHEST DEMAND FIRST
    # ------------------------------------------------------

    results.sort(
        key=lambda item: item.get(
            "forecast_total",
            0.0,
        ),
        reverse=True,
    )

    return {
        "status": "success",
        "forecast_periods": periods,
        "products": results,
        "product_count": len(results),
        "message": (
            "Product demand forecasts "
            "generated from validated "
            "historical order-item data."
        ),
    }