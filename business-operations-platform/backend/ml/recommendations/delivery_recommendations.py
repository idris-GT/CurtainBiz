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
    if not forecast_result:
        return []

    forecast = forecast_result.get(
        "forecast",
        [],
    )

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
    deliveries_df: pd.DataFrame,
) -> Dict[str, Any]:

    if deliveries_df.empty:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_deliveries": [],
        }

    date_column = _find_column(
        deliveries_df,
        [
            "scheduled_date",
            "delivery_date",
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
            "historical_weekly_deliveries": [],
            "reason": (
                "Delivery data does not contain "
                "a usable date column."
            ),
        }

    dates = _to_datetime(
        deliveries_df,
        date_column,
    )

    working = deliveries_df.copy()

    working["_delivery_date"] = dates

    working = working.dropna(
        subset=["_delivery_date"]
    )

    if working.empty:
        return {
            "status": "insufficient",
            "weekly_capacity_average": 0.0,
            "weekly_capacity_median": 0.0,
            "weekly_capacity_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_deliveries": [],
            "reason": (
                "Delivery records do not contain "
                "valid dates."
            ),
        }

    # Keep zero-delivery weeks in the timeline.
    weekly_counts = (
        working
        .set_index("_delivery_date")
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
            "historical_weekly_deliveries": [],
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

    historical_weekly_deliveries = [
        {
            "week": index.strftime("%Y-%m-%d"),
            "delivery_count": int(value),
        }
        for index, value in weekly_counts.items()
    ]

    return {
        "status": (
            "sufficient"
            if len(weekly_counts) >= 8
            else "limited"
        ),
        "weekly_capacity_average": (
            average_capacity
        ),
        "weekly_capacity_median": (
            median_capacity
        ),
        "weekly_capacity_upper": (
            upper_capacity
        ),
        "weeks_observed": int(
            len(weekly_counts)
        ),
        "historical_weekly_deliveries": (
            historical_weekly_deliveries
        ),
    }


def _calculate_current_workload(
    deliveries_df: pd.DataFrame,
) -> Dict[str, Any]:

    if deliveries_df.empty:
        return {
            "active_deliveries": 0,
            "completed_deliveries": 0,
            "failed_deliveries": 0,
            "status_available": False,
        }

    status_column = _find_column(
        deliveries_df,
        [
            "status",
            "delivery_status",
        ],
    )

    if status_column is None:
        return {
            "active_deliveries": 0,
            "completed_deliveries": 0,
            "failed_deliveries": 0,
            "status_available": False,
        }

    statuses = (
        deliveries_df[status_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    active_statuses = {
        "PENDING",
        "SCHEDULED",
        "OUT_FOR_DELIVERY",
    }

    active_count = int(
        statuses.isin(
            active_statuses
        ).sum()
    )

    completed_count = int(
        (
            statuses == "DELIVERED"
        ).sum()
    )

    failed_count = int(
        (
            statuses == "FAILED"
        ).sum()
    )

    return {
        "active_deliveries": active_count,
        "completed_deliveries": completed_count,
        "failed_deliveries": failed_count,
        "status_available": True,
    }


def _classify_delivery_risk(
    expected_weekly_demand: float,
    historical_capacity: float,
    active_deliveries: float,
    failed_deliveries: float,
) -> Dict[str, Any]:

    if historical_capacity <= 0:
        return {
            "risk": "HIGH",
            "risk_score": 90,
            "reason": (
                "No reliable historical delivery "
                "capacity could be established."
            ),
        }

    capacity_ratio = (
        expected_weekly_demand
        / historical_capacity
    )

    if capacity_ratio > 1.20:

        risk = "CRITICAL"
        score = 95

        reason = (
            "Expected weekly delivery workload is "
            "more than 20% above historical capacity."
        )

    elif capacity_ratio > 1.00:

        risk = "HIGH"
        score = 80

        reason = (
            "Expected weekly delivery workload "
            "exceeds historical delivery capacity."
        )

    elif capacity_ratio >= 0.85:

        risk = "MEDIUM"
        score = 60

        reason = (
            "Expected weekly delivery workload is "
            "close to historical delivery capacity."
        )

    else:

        risk = "LOW"
        score = 25

        reason = (
            "Expected weekly delivery workload remains "
            "below historical delivery capacity."
        )

    if active_deliveries > historical_capacity:

        if risk == "LOW":
            risk = "MEDIUM"
            score = 60

        reason += (
            " Current active delivery workload is also "
            "above the historical weekly capacity level."
        )

    if failed_deliveries > 0:

        if risk == "LOW":
            risk = "MEDIUM"
            score = 60

        reason += (
            f" There are {int(failed_deliveries)} "
            "failed deliveries requiring attention."
        )

    return {
        "risk": risk,
        "risk_score": score,
        "reason": reason,
    }


def _build_recommendation(
    risk: str,
    current_active_deliveries: float,
    capacity: float,
    failed_deliveries: float,
    forecast_confidence: str,
) -> str:

    if forecast_confidence == "insufficient":

        return (
            "Collect more delivery history before making "
            "major delivery-capacity decisions."
        )

    if risk == "CRITICAL":

        return (
            "Consider increasing delivery capacity, "
            "prioritizing urgent deliveries, and "
            "rescheduling lower-priority deliveries."
        )

    if risk == "HIGH":

        return (
            "Review delivery capacity and scheduling. "
            "Consider additional delivery resources, "
            "route optimization, or workload redistribution."
        )

    if risk == "MEDIUM":

        if failed_deliveries > 0:
            return (
                "Monitor delivery workload closely and "
                "resolve failed deliveries while preparing "
                "additional capacity if demand increases."
            )

        return (
            "Monitor delivery workload closely and "
            "prepare additional capacity if incoming "
            "delivery demand increases."
        )

    if current_active_deliveries > capacity:

        return (
            "Current delivery workload is above the "
            "historical capacity level. Review the "
            "delivery queue and prioritize urgent jobs."
        )

    if failed_deliveries > 0:

        return (
            "Delivery capacity appears manageable, but "
            "failed deliveries should be reviewed and "
            "resolved."
        )

    return (
        "Current and forecast delivery workload appear "
        "manageable relative to historical capacity."
    )


def analyze_delivery_intelligence(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    deliveries_df = data.get(
        "deliveries"
    )

    if deliveries_df is None:
        deliveries_df = pd.DataFrame()

    if not isinstance(
        deliveries_df,
        pd.DataFrame,
    ):
        deliveries_df = pd.DataFrame(
            deliveries_df
        )

    capacity = _calculate_historical_capacity(
        deliveries_df
    )

    current_workload = _calculate_current_workload(
        deliveries_df
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

    if forecast_values:

        expected_workload = float(
            sum(forecast_values)
        )

        weeks_forecast = len(
            forecast_values
        )

    else:

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

    active_deliveries = current_workload.get(
        "active_deliveries",
        0,
    )

    failed_deliveries = current_workload.get(
        "failed_deliveries",
        0,
    )

    risk_result = _classify_delivery_risk(
        expected_weekly_demand=(
            weekly_expected_workload
        ),
        historical_capacity=(
            historical_capacity
        ),
        active_deliveries=(
            active_deliveries
        ),
        failed_deliveries=(
            failed_deliveries
        ),
    )

    recommendation = _build_recommendation(
        risk=risk_result["risk"],
        current_active_deliveries=(
            active_deliveries
        ),
        capacity=historical_capacity,
        failed_deliveries=failed_deliveries,
        forecast_confidence=(
            forecast_reliability
        ),
    )

    return {
        "status": "success",
        "analysis": "delivery_intelligence",

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

        "current_active_deliveries": (
            active_deliveries
        ),

        "completed_deliveries": (
            current_workload.get(
                "completed_deliveries",
                0,
            )
        ),

        "failed_deliveries": (
            failed_deliveries
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
                "historical_weekly_deliveries",
                [],
            )
        ),

        "message": (
            "Delivery intelligence combines the delivery "
            "workload forecast with empirically observed "
            "historical delivery capacity. Forecast reliability "
            "is reported separately and should be considered "
            "before making delivery-capacity decisions."
        ),
    }


def generate_delivery_recommendations(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    intelligence = analyze_delivery_intelligence(
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
                "type": "delivery_capacity_gap",
                "priority": "high",
                "title": (
                    "Delivery capacity pressure"
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
                "type": "delivery_capacity_monitoring",
                "priority": "medium",
                "title": (
                    "Monitor delivery capacity"
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
                "type": "delivery_capacity_status",
                "priority": "info",
                "title": (
                    "Delivery capacity appears manageable"
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
            "current_active_deliveries",
            0,
        )
        > intelligence.get(
            "historical_weekly_capacity",
            0,
        )
    ):

        recommendations.append(
            {
                "type": "active_delivery_workload",
                "priority": "high",
                "title": (
                    "Active delivery workload above capacity"
                ),
                "message": (
                    "Review scheduled and active deliveries "
                    "and prioritize urgent deliveries."
                ),
            }
        )

    if intelligence.get(
        "failed_deliveries",
        0,
    ) > 0:

        recommendations.append(
            {
                "type": "failed_deliveries",
                "priority": "high",
                "title": (
                    "Failed deliveries require attention"
                ),
                "message": (
                    f"{intelligence['failed_deliveries']} "
                    "delivery records are marked FAILED. "
                    "Review the affected deliveries and "
                    "schedule corrective action."
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
                    "Limited delivery capacity history"
                ),
                "message": (
                    "More historical delivery data would "
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
                    "Use the delivery forecast as decision "
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