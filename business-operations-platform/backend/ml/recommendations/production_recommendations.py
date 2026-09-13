import math
from typing import Any, Dict, List, Optional

import pandas as pd


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def _find_column(
    dataframe: pd.DataFrame,
    candidates: List[str],
) -> Optional[str]:
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    return None


def _to_datetime(
    dataframe: pd.DataFrame,
    column: Optional[str],
) -> pd.Series:
    if column is None:
        return pd.Series(pd.NaT, index=dataframe.index)

    return pd.to_datetime(
        dataframe[column],
        errors="coerce",
    )


def _extract_forecast_values(
    forecast_result: Optional[Dict[str, Any]],
) -> List[float]:
    """
    Extract forecast values from the forecast engine.

    The forecast engine currently returns:
        {
            "predicted_value": ...,
            "date": ...,
            "period": ...,
            "method": ...
        }

    The function also supports a few generic alternatives so the
    recommendation layer remains reusable.
    """

    if not forecast_result:
        return []

    forecast = forecast_result.get("forecast", [])

    if not isinstance(forecast, list):
        return []

    values = []

    for item in forecast:

        if isinstance(item, dict):

            value = None

            for key in (
                "predicted_value",
                "prediction",
                "forecast",
                "value",
            ):
                if key in item:
                    value = item[key]
                    break

            if value is not None:
                values.append(
                    max(
                        0.0,
                        _safe_float(value),
                    )
                )

        elif isinstance(item, (int, float)):
            values.append(
                max(
                    0.0,
                    _safe_float(item),
                )
            )

    return values


def _calculate_historical_capacity(
    production_df: pd.DataFrame,
) -> Dict[str, Any]:

    if production_df.empty:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "reason": "No production records are available.",
            "historical_weekly_production": [],
        }

    date_column = _find_column(
        production_df,
        [
            "start_date",
            "production_date",
            "created_at",
            "date",
        ],
    )

    if date_column is None:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "reason": (
                "Production data does not contain "
                "a usable date column."
            ),
            "historical_weekly_production": [],
        }

    dates = _to_datetime(
        production_df,
        date_column,
    )

    working = production_df.copy()

    working["_production_date"] = dates

    working = working.dropna(
        subset=["_production_date"]
    )

    if working.empty:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "reason": (
                "Production records do not contain "
                "valid dates."
            ),
            "historical_weekly_production": [],
        }

    # Build a complete weekly timeline.
    # This is important because weeks with zero production
    # should not disappear from the capacity calculation.
    weekly_counts = (
        working
        .set_index("_production_date")
        .resample("W")
        .size()
    )

    if weekly_counts.empty:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "reason": (
                "There is not enough weekly production history."
            ),
            "historical_weekly_production": [],
        }

    average_capacity = float(
        weekly_counts.mean()
    )

    median_capacity = float(
        weekly_counts.median()
    )

    upper_capacity = float(
        weekly_counts.quantile(0.75)
    )

    historical_weekly_production = [
        {
            "week": index.strftime("%Y-%m-%d"),
            "production_count": int(value),
        }
        for index, value in weekly_counts.items()
    ]

    return {
        "status": (
            "sufficient"
            if len(weekly_counts) >= 8
            else "limited"
        ),
        "weekly_capacity_average": average_capacity,
        "weekly_capacity_median": median_capacity,
        "weekly_capacity_upper": upper_capacity,
        "weeks_observed": int(
            len(weekly_counts)
        ),
        "historical_weekly_production": (
            historical_weekly_production
        ),
    }


def _calculate_current_workload(
    production_df: pd.DataFrame,
) -> Dict[str, Any]:

    if production_df.empty:
        return {
            "active_production": 0,
            "completed_production": 0,
            "cancelled_production": 0,
            "status_available": False,
        }

    status_column = _find_column(
        production_df,
        [
            "status",
            "production_status",
        ],
    )

    if status_column is None:
        return {
            "active_production": 0,
            "completed_production": 0,
            "cancelled_production": 0,
            "status_available": False,
        }

    statuses = (
        production_df[status_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    active_statuses = {
        "PENDING",
        "IN_PROGRESS",
        "PAUSED",
        "QUALITY_CHECK",
    }

    active_count = int(
        statuses.isin(
            active_statuses
        ).sum()
    )

    completed_count = int(
        (
            statuses == "COMPLETED"
        ).sum()
    )

    cancelled_count = int(
        (
            statuses == "CANCELLED"
        ).sum()
    )

    return {
        "active_production": active_count,
        "completed_production": completed_count,
        "cancelled_production": cancelled_count,
        "status_available": True,
    }


def _classify_capacity_risk(
    expected_weekly_workload: float,
    historical_capacity: float,
    current_active_workload: float,
) -> Dict[str, Any]:

    if historical_capacity <= 0:
        return {
            "risk": "HIGH",
            "risk_score": 90,
            "reason": (
                "No reliable historical production "
                "capacity could be established."
            ),
        }

    capacity_ratio = (
        expected_weekly_workload
        / historical_capacity
    )

    if capacity_ratio > 1.20:

        risk = "CRITICAL"
        score = 95

        reason = (
            "Expected weekly production workload is "
            "more than 20% above historical capacity."
        )

    elif capacity_ratio > 1.00:

        risk = "HIGH"
        score = 80

        reason = (
            "Expected weekly production workload "
            "exceeds historical production capacity."
        )

    elif capacity_ratio >= 0.85:

        risk = "MEDIUM"
        score = 60

        reason = (
            "Expected weekly production workload is "
            "close to historical production capacity."
        )

    else:

        risk = "LOW"
        score = 25

        reason = (
            "Expected weekly production workload remains "
            "below historical production capacity."
        )

    if current_active_workload > historical_capacity:

        if risk == "LOW":
            risk = "MEDIUM"
            score = 60

        reason += (
            " Current active production workload is "
            "also above the historical weekly capacity level."
        )

    return {
        "risk": risk,
        "risk_score": score,
        "reason": reason,
    }


def _build_recommendation(
    risk: str,
    capacity_gap: float,
    current_active_workload: float,
    capacity: float,
    forecast_confidence: str,
) -> str:

    if forecast_confidence == "insufficient":

        return (
            "Collect more production history before making "
            "a capacity expansion decision."
        )

    if risk == "CRITICAL":

        return (
            "Consider increasing production capacity, "
            "prioritizing urgent jobs, and rescheduling "
            "lower-priority work."
        )

    if risk == "HIGH":

        return (
            "Review production capacity and workload "
            "allocation. Consider overtime, additional "
            "staffing, or rescheduling lower-priority jobs."
        )

    if risk == "MEDIUM":

        return (
            "Monitor production workload closely and "
            "prepare additional capacity if incoming "
            "work increases."
        )

    if current_active_workload > capacity:

        return (
            "Current production workload is above the "
            "historical capacity level. Review active "
            "jobs and prioritize the production queue."
        )

    return (
        "Current and forecast production workload appear "
        "manageable relative to historical capacity."
    )


def analyze_production_intelligence(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    production_df = data.get(
        "production"
    )

    if production_df is None:
        production_df = pd.DataFrame()

    if not isinstance(
        production_df,
        pd.DataFrame,
    ):
        production_df = pd.DataFrame(
            production_df
        )

    capacity = _calculate_historical_capacity(
        production_df
    )

    current_workload = _calculate_current_workload(
        production_df
    )

    forecast_values = _extract_forecast_values(
        forecast_result
    )

    forecast_method = "historical_mean"
    forecast_reliability = "insufficient"

    if forecast_result:

        forecast_method = forecast_result.get(
            "selected_method",
            "historical_mean",
        )

        reliability = forecast_result.get(
            "reliability",
            {},
        )

        if isinstance(
            reliability,
            dict,
        ):
            forecast_reliability = reliability.get(
                "level",
                "insufficient",
            )

    # Use actual ML/baseline forecast if available.
    if forecast_values:

        expected_workload = float(
            sum(forecast_values)
        )

        weeks_forecast = len(
            forecast_values
        )

    else:

        # Only use this fallback if the forecast engine
        # did not provide usable forecast values.
        historical_capacity = capacity.get(
            "weekly_capacity_average",
            0.0,
        )

        weeks_forecast = 8

        expected_workload = (
            historical_capacity
            * weeks_forecast
        )

        forecast_method = (
            "historical_capacity_fallback"
        )

    weekly_expected_workload = (
        expected_workload
        / weeks_forecast
        if weeks_forecast > 0
        else 0.0
    )

    historical_capacity = capacity.get(
        "weekly_capacity_average",
        0.0,
    )

    total_capacity = (
        historical_capacity
        * weeks_forecast
    )

    total_capacity_gap = (
        expected_workload
        - total_capacity
    )

    weekly_capacity_gap = (
        weekly_expected_workload
        - historical_capacity
    )

    risk_result = _classify_capacity_risk(
        expected_weekly_workload=(
            weekly_expected_workload
        ),
        historical_capacity=(
            historical_capacity
        ),
        current_active_workload=(
            current_workload.get(
                "active_production",
                0,
            )
        ),
    )

    recommendation = _build_recommendation(
        risk=risk_result["risk"],
        capacity_gap=weekly_capacity_gap,
        current_active_workload=(
            current_workload.get(
                "active_production",
                0,
            )
        ),
        capacity=historical_capacity,
        forecast_confidence=(
            forecast_reliability
        ),
    )

    return {
        "status": "success",
        "analysis": "production_intelligence",

        "forecast_method": forecast_method,

        "forecast_reliability": (
            forecast_reliability
        ),

        "forecast_periods": weeks_forecast,

        "expected_workload": round(
            expected_workload,
            2,
        ),

        "expected_weekly_workload": round(
            weekly_expected_workload,
            2,
        ),

        "historical_weekly_capacity": round(
            historical_capacity,
            2,
        ),

        "historical_weekly_capacity_median": round(
            capacity.get(
                "weekly_capacity_median",
                0.0,
            ),
            2,
        ),

        "historical_weekly_capacity_upper": round(
            capacity.get(
                "weekly_capacity_upper",
                0.0,
            ),
            2,
        ),

        "forecast_capacity": round(
            total_capacity,
            2,
        ),

        "capacity_gap": round(
            total_capacity_gap,
            2,
        ),

        "weekly_capacity_gap": round(
            weekly_capacity_gap,
            2,
        ),

        "current_active_workload": (
            current_workload.get(
                "active_production",
                0,
            )
        ),

        "completed_production": (
            current_workload.get(
                "completed_production",
                0,
            )
        ),

        "cancelled_production": (
            current_workload.get(
                "cancelled_production",
                0,
            )
        ),

        "capacity_history_weeks": (
            capacity.get(
                "weeks_observed",
                0,
            )
        ),

        "risk": risk_result["risk"],

        "risk_score": (
            risk_result["risk_score"]
        ),

        "risk_reason": (
            risk_result["reason"]
        ),

        "recommendation": recommendation,

        "forecast_values": [
            round(
                value,
                2,
            )
            for value in forecast_values
        ],

        "historical_capacity_detail": (
            capacity.get(
                "historical_weekly_production",
                [],
            )
        ),

        "message": (
            "Production intelligence combines the production "
            "workload forecast with empirically observed "
            "historical production capacity. Forecast reliability "
            "is reported separately and should be considered "
            "before making capacity decisions."
        ),
    }


def generate_production_recommendations(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    intelligence = analyze_production_intelligence(
        data=data,
        forecast_result=forecast_result,
    )

    recommendations = []

    risk = intelligence.get(
        "risk",
        "LOW",
    )

    if risk in {
        "CRITICAL",
        "HIGH",
    }:

        recommendations.append(
            {
                "type": "capacity_gap",
                "priority": "high",
                "title": (
                    "Production capacity pressure"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "capacity_gap": intelligence.get(
                    "capacity_gap",
                    0,
                ),
            }
        )

    elif risk == "MEDIUM":

        recommendations.append(
            {
                "type": "capacity_monitoring",
                "priority": "medium",
                "title": (
                    "Monitor production capacity"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "capacity_gap": intelligence.get(
                    "capacity_gap",
                    0,
                ),
            }
        )

    else:

        recommendations.append(
            {
                "type": "capacity_status",
                "priority": "info",
                "title": (
                    "Production capacity appears manageable"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "capacity_gap": intelligence.get(
                    "capacity_gap",
                    0,
                ),
            }
        )

    if (
        intelligence.get(
            "current_active_workload",
            0,
        )
        > intelligence.get(
            "historical_weekly_capacity",
            0,
        )
    ):

        recommendations.append(
            {
                "type": "active_workload",
                "priority": "high",
                "title": (
                    "Active workload above historical capacity"
                ),
                "message": (
                    "Review active production jobs and "
                    "prioritize the production queue."
                ),
            }
        )

    if (
        intelligence.get(
            "capacity_history_weeks",
            0,
        )
        < 8
    ):

        recommendations.append(
            {
                "type": "data_quality",
                "priority": "medium",
                "title": (
                    "Limited production capacity history"
                ),
                "message": (
                    "More historical production data would "
                    "improve capacity estimation."
                ),
            }
        )

    if intelligence.get(
        "forecast_reliability"
    ) in {
        "low",
        "insufficient",
    }:

        recommendations.append(
            {
                "type": "forecast_confidence",
                "priority": "medium",
                "title": (
                    "Forecast confidence is limited"
                ),
                "message": (
                    "Use the production forecast as decision "
                    "support rather than as a guaranteed "
                    "workload prediction."
                ),
            }
        )

    return {
        "status": "success",
        "analysis": intelligence,
        "recommendations": recommendations,
        "recommendation_count": len(
            recommendations
        ),
    }