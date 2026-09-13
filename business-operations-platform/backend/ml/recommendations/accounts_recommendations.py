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


def _calculate_historical_cashflow(
    payments_df: pd.DataFrame,
) -> Dict[str, Any]:

    if payments_df.empty:

        return {
            "status": "insufficient",
            "weekly_average": 0.0,
            "weekly_median": 0.0,
            "weekly_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_cashflow": [],
        }

    required_columns = {
        "date",
        "cash_inflow",
    }

    if not required_columns.issubset(
        payments_df.columns
    ):

        return {
            "status": "insufficient",
            "weekly_average": 0.0,
            "weekly_median": 0.0,
            "weekly_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_cashflow": [],
            "reason": (
                "Payment feature data must contain "
                "'date' and 'cash_inflow'."
            ),
        }

    working = payments_df[
        [
            "date",
            "cash_inflow",
        ]
    ].copy()

    working["date"] = pd.to_datetime(
        working["date"],
        errors="coerce",
    )

    working["cash_inflow"] = pd.to_numeric(
        working["cash_inflow"],
        errors="coerce",
    ).fillna(0.0)

    working = working.dropna(
        subset=["date"]
    )

    if working.empty:

        return {
            "status": "insufficient",
            "weekly_average": 0.0,
            "weekly_median": 0.0,
            "weekly_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_cashflow": [],
        }

    weekly_cashflow = (
        working
        .set_index("date")["cash_inflow"]
        .resample("W")
        .sum()
    )

    if weekly_cashflow.empty:

        return {
            "status": "insufficient",
            "weekly_average": 0.0,
            "weekly_median": 0.0,
            "weekly_upper": 0.0,
            "weeks_observed": 0,
            "historical_weekly_cashflow": [],
        }

    weekly_average = float(
        weekly_cashflow.mean()
    )

    weekly_median = float(
        weekly_cashflow.median()
    )

    weekly_upper = float(
        weekly_cashflow.quantile(0.75)
    )

    historical_weekly_cashflow = [
        {
            "week": index.strftime(
                "%Y-%m-%d"
            ),
            "cash_inflow": round(
                float(value),
                2,
            ),
        }
        for index, value
        in weekly_cashflow.items()
    ]

    return {
        "status": (
            "sufficient"
            if len(weekly_cashflow) >= 8
            else "limited"
        ),
        "weekly_average": weekly_average,
        "weekly_median": weekly_median,
        "weekly_upper": weekly_upper,
        "weeks_observed": int(
            len(weekly_cashflow)
        ),
        "historical_weekly_cashflow": (
            historical_weekly_cashflow
        ),
    }


def _calculate_cashflow_trend(
    historical_cashflow: Dict[str, Any],
) -> Dict[str, Any]:

    detail = historical_cashflow.get(
        "historical_weekly_cashflow",
        [],
    )

    if len(detail) < 4:

        return {
            "trend": "insufficient",
            "change_percent": None,
        }

    values = [
        _safe_float(
            item.get("cash_inflow")
        )
        for item in detail
    ]

    midpoint = len(values) // 2

    first_half = values[:midpoint]
    second_half = values[midpoint:]

    if not first_half or not second_half:

        return {
            "trend": "insufficient",
            "change_percent": None,
        }

    first_average = (
        sum(first_half)
        / len(first_half)
    )

    second_average = (
        sum(second_half)
        / len(second_half)
    )

    if first_average == 0:

        return {
            "trend": "insufficient",
            "change_percent": None,
        }

    change_percent = (
        (
            second_average
            - first_average
        )
        / first_average
        * 100
    )

    if change_percent > 10:
        trend = "increasing"

    elif change_percent < -10:
        trend = "decreasing"

    else:
        trend = "stable"

    return {
        "trend": trend,
        "change_percent": round(
            change_percent,
            2,
        ),
    }


def _classify_cashflow_risk(
    expected_weekly_cashflow: float,
    historical_weekly_cashflow: float,
    historical_trend: str,
) -> Dict[str, Any]:

    if historical_weekly_cashflow <= 0:

        return {
            "risk": "HIGH",
            "risk_score": 90,
            "reason": (
                "No reliable positive historical weekly "
                "cash inflow baseline could be established."
            ),
        }

    ratio = (
        expected_weekly_cashflow
        / historical_weekly_cashflow
    )

    if ratio < 0.70:

        risk = "CRITICAL"
        score = 95

        reason = (
            "Expected weekly cash inflow is more than "
            "30% below the historical weekly baseline."
        )

    elif ratio < 0.85:

        risk = "HIGH"
        score = 80

        reason = (
            "Expected weekly cash inflow is below "
            "the historical weekly baseline."
        )

    elif ratio < 1.00:

        risk = "MEDIUM"
        score = 60

        reason = (
            "Expected weekly cash inflow is somewhat "
            "below the historical weekly baseline."
        )

    else:

        risk = "LOW"
        score = 25

        reason = (
            "Expected weekly cash inflow is at or above "
            "the historical weekly baseline."
        )

    if historical_trend == "decreasing":

        if risk == "LOW":
            risk = "MEDIUM"
            score = 60

        reason += (
            " Historical cash inflow is also showing "
            "a decreasing trend."
        )

    elif historical_trend == "increasing":

        if risk == "MEDIUM" and ratio >= 0.95:
            risk = "LOW"
            score = 25

        reason += (
            " Historical cash inflow is showing "
            "an increasing trend."
        )

    return {
        "risk": risk,
        "risk_score": score,
        "reason": reason,
    }


def _build_recommendation(
    risk: str,
    historical_trend: str,
    forecast_confidence: str,
) -> str:

    if forecast_confidence == "insufficient":

        return (
            "Collect more payment history before making "
            "major cashflow planning decisions."
        )

    if risk == "CRITICAL":

        return (
            "Review near-term cashflow carefully, "
            "prioritize cash collection, and control "
            "non-essential spending."
        )

    if risk == "HIGH":

        return (
            "Monitor cash inflows closely and prioritize "
            "cash collection and essential operating expenses."
        )

    if risk == "MEDIUM":

        return (
            "Monitor cashflow closely and prepare for "
            "potential short-term cash pressure."
        )

    if historical_trend == "increasing":

        return (
            "Cashflow outlook appears manageable and "
            "historical cash inflow is trending upward."
        )

    return (
        "Cashflow outlook appears manageable relative "
        "to the historical payment baseline."
    )


def analyze_accounts_intelligence(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    payments_df = data.get(
        "payments"
    )

    if payments_df is None:
        payments_df = pd.DataFrame()

    if not isinstance(
        payments_df,
        pd.DataFrame,
    ):
        payments_df = pd.DataFrame(
            payments_df
        )

    historical = _calculate_historical_cashflow(
        payments_df
    )

    trend = _calculate_cashflow_trend(
        historical
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

        expected_cashflow = float(
            sum(forecast_values)
        )

        forecast_periods = len(
            forecast_values
        )

    else:

        historical_average = historical.get(
            "weekly_average",
            0.0,
        )

        forecast_periods = 8

        expected_cashflow = (
            historical_average
            * forecast_periods
        )

        forecast_method = (
            "historical_cashflow_fallback"
        )

    expected_weekly_cashflow = (
        expected_cashflow
        / forecast_periods
        if forecast_periods > 0
        else 0.0
    )

    historical_weekly_cashflow = historical.get(
        "weekly_average",
        0.0,
    )

    historical_expected_total = (
        historical_weekly_cashflow
        * forecast_periods
    )

    cashflow_gap = (
        expected_cashflow
        - historical_expected_total
    )

    weekly_cashflow_gap = (
        expected_weekly_cashflow
        - historical_weekly_cashflow
    )

    risk_result = _classify_cashflow_risk(
        expected_weekly_cashflow=(
            expected_weekly_cashflow
        ),
        historical_weekly_cashflow=(
            historical_weekly_cashflow
        ),
        historical_trend=(
            trend.get(
                "trend",
                "insufficient",
            )
        ),
    )

    recommendation = _build_recommendation(
        risk=risk_result["risk"],
        historical_trend=(
            trend.get(
                "trend",
                "insufficient",
            )
        ),
        forecast_confidence=(
            forecast_reliability
        ),
    )

    return {
        "status": "success",

        "analysis": (
            "accounts_intelligence"
        ),

        "forecast_method": (
            forecast_method
        ),

        "forecast_reliability": (
            forecast_reliability
        ),

        "forecast_periods": (
            forecast_periods
        ),

        "expected_cashflow": round(
            expected_cashflow,
            2,
        ),

        "expected_weekly_cashflow": round(
            expected_weekly_cashflow,
            2,
        ),

        "historical_weekly_cashflow": round(
            historical_weekly_cashflow,
            2,
        ),

        "historical_weekly_cashflow_median": round(
            historical.get(
                "weekly_median",
                0.0,
            ),
            2,
        ),

        "historical_weekly_cashflow_upper": round(
            historical.get(
                "weekly_upper",
                0.0,
            ),
            2,
        ),

        "forecast_cashflow_gap": round(
            cashflow_gap,
            2,
        ),

        "weekly_cashflow_gap": round(
            weekly_cashflow_gap,
            2,
        ),

        "historical_cashflow_trend": (
            trend.get(
                "trend",
                "insufficient",
            )
        ),

        "historical_cashflow_change_percent": (
            trend.get(
                "change_percent"
            )
        ),

        "cashflow_risk": (
            risk_result["risk"]
        ),

        "risk_score": (
            risk_result["risk_score"]
        ),

        "risk_reason": (
            risk_result["reason"]
        ),

        "recommendation": (
            recommendation
        ),

        "forecast_values": [
            round(
                value,
                2,
            )
            for value in forecast_values
        ],

        "historical_cashflow_detail": (
            historical.get(
                "historical_weekly_cashflow",
                [],
            )
        ),

        "message": (
            "Accounts intelligence uses the engineered "
            "payment history and cash inflow forecast to "
            "evaluate future cashflow pressure. Outstanding "
            "receivables are not estimated here because the "
            "current ML pipeline provides aggregated order "
            "and payment features rather than order-level "
            "payment relationships."
        ),
    }


def generate_accounts_recommendations(
    data: Dict[str, Any],
    forecast_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    intelligence = analyze_accounts_intelligence(
        data=data,
        forecast_result=forecast_result,
    )

    recommendations = []

    risk = intelligence.get(
        "cashflow_risk",
        "LOW",
    )

    if risk in {
        "CRITICAL",
        "HIGH",
    }:

        recommendations.append(
            {
                "type": "cashflow_pressure",
                "priority": "high",
                "title": (
                    "Cashflow pressure detected"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "cashflow_gap": intelligence.get(
                    "forecast_cashflow_gap",
                    0,
                ),
            }
        )

    elif risk == "MEDIUM":

        recommendations.append(
            {
                "type": "cashflow_monitoring",
                "priority": "medium",
                "title": (
                    "Monitor cashflow"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "cashflow_gap": intelligence.get(
                    "forecast_cashflow_gap",
                    0,
                ),
            }
        )

    else:

        recommendations.append(
            {
                "type": "cashflow_status",
                "priority": "info",
                "title": (
                    "Cashflow outlook appears manageable"
                ),
                "message": intelligence.get(
                    "recommendation",
                    "",
                ),
                "cashflow_gap": intelligence.get(
                    "forecast_cashflow_gap",
                    0,
                ),
            }
        )

    trend = intelligence.get(
        "historical_cashflow_trend",
        "insufficient",
    )

    if trend == "decreasing":

        recommendations.append(
            {
                "type": "cashflow_trend",
                "priority": "high",
                "title": (
                    "Cash inflow is trending downward"
                ),
                "message": (
                    "Historical weekly cash inflow has "
                    "declined between the earlier and later "
                    "parts of the available payment history."
                ),
            }
        )

    elif trend == "increasing":

        recommendations.append(
            {
                "type": "cashflow_trend",
                "priority": "info",
                "title": (
                    "Cash inflow is trending upward"
                ),
                "message": (
                    "Historical weekly cash inflow has "
                    "increased between the earlier and later "
                    "parts of the available payment history."
                ),
            }
        )

    if (
        intelligence.get(
            "forecast_reliability"
        )
        in {
            "low",
            "insufficient",
        }
    ):

        recommendations.append(
            {
                "type": "forecast_confidence",
                "priority": "medium",
                "title": (
                    "Forecast confidence is limited"
                ),
                "message": (
                    "Use the cashflow forecast as decision "
                    "support rather than as a guaranteed "
                    "financial prediction."
                ),
            }
        )

    if (
        intelligence.get(
            "forecast_periods",
            0,
        )
        < 8
    ):

        recommendations.append(
            {
                "type": "forecast_horizon",
                "priority": "medium",
                "title": (
                    "Limited forecast horizon"
                ),
                "message": (
                    "The available forecast contains fewer "
                    "than eight future periods."
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