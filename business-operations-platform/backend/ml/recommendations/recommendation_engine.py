from typing import Any, Dict, List, Optional


# ==========================================================
# PRIORITY LEVELS
# ==========================================================

PRIORITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


# ==========================================================
# RECOMMENDATION BUILDER
# ==========================================================

def create_recommendation(
    department: str,
    recommendation_type: str,
    priority: str,
    title: str,
    message: str,
    recommended_action: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized business recommendation.
    """

    normalized_priority = (
        priority.lower().strip()
    )

    if normalized_priority not in PRIORITY_ORDER:
        raise ValueError(
            f"Unsupported priority: "
            f"{priority}"
        )

    return {
        "department": department,
        "type": recommendation_type,
        "priority": normalized_priority,
        "title": title,
        "message": message,
        "recommended_action": (
            recommended_action
        ),
        "evidence": evidence or {},
    }


# ==========================================================
# SORT RECOMMENDATIONS
# ==========================================================

def sort_recommendations(
    recommendations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Sort recommendations from highest to lowest
    priority.
    """

    return sorted(
        recommendations,
        key=lambda item: PRIORITY_ORDER.get(
            item.get(
                "priority",
                "info",
            ),
            0,
        ),
        reverse=True,
    )


# ==========================================================
# FORECAST SUMMARY
# ==========================================================

def summarize_forecast(
    forecast_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract useful business-level information from a
    forecast result.
    """

    forecast = forecast_result.get(
        "forecast",
        [],
    )

    if not forecast:
        return {
            "available": False,
            "forecast_periods": 0,
            "average_forecast": None,
            "minimum_forecast": None,
            "maximum_forecast": None,
            "total_forecast": None,
            "first_forecast": None,
            "last_forecast": None,
        }

    values = []

    for item in forecast:

        value = item.get(
            "predicted_value"
        )

        if value is None:
            continue

        try:
            values.append(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    if not values:
        return {
            "available": False,
            "forecast_periods": len(
                forecast
            ),
            "average_forecast": None,
            "minimum_forecast": None,
            "maximum_forecast": None,
            "total_forecast": None,
            "first_forecast": None,
            "last_forecast": None,
        }

    return {
        "available": True,
        "forecast_periods": len(
            values
        ),
        "average_forecast": (
            sum(values) / len(values)
        ),
        "minimum_forecast": min(
            values
        ),
        "maximum_forecast": max(
            values
        ),
        "total_forecast": sum(
            values
        ),
        "first_forecast": values[0],
        "last_forecast": values[-1],
    }


# ==========================================================
# FORECAST TREND
# ==========================================================

def calculate_forecast_trend(
    forecast_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Determine whether the forecast is generally rising,
    falling, or stable.
    """

    forecast = forecast_result.get(
        "forecast",
        [],
    )

    values = []

    for item in forecast:

        value = item.get(
            "predicted_value"
        )

        if value is None:
            continue

        try:
            values.append(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    if len(values) < 2:
        return {
            "direction": "unknown",
            "change": None,
            "percentage_change": None,
        }

    first_value = values[0]
    last_value = values[-1]

    change = (
        last_value
        - first_value
    )

    if first_value == 0:
        percentage_change = None
    else:
        percentage_change = (
            change
            / abs(first_value)
        ) * 100

    # Small movements should not be treated as meaningful
    # business trends.

    if percentage_change is None:
        direction = "unknown"

    elif percentage_change >= 10:
        direction = "increasing"

    elif percentage_change <= -10:
        direction = "decreasing"

    else:
        direction = "stable"

    return {
        "direction": direction,
        "change": float(change),
        "percentage_change": (
            float(percentage_change)
            if percentage_change is not None
            else None
        ),
    }


# ==========================================================
# FORECAST RELIABILITY
# ==========================================================

def get_forecast_reliability(
    forecast_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize the reliability information returned by
    the forecasting engine.
    """

    reliability = (
        forecast_result.get(
            "reliability"
        )
    )

    if not reliability:
        selected_method = (
            forecast_result.get(
                "selected_method"
            )
        )

        if selected_method == "historical_mean":
            return {
                "level": "baseline",
                "reason": (
                    "The historical baseline was used "
                    "because the ML candidates did not "
                    "outperform it."
                ),
            }

        return {
            "level": "unknown",
            "reason": (
                "No reliability assessment "
                "was supplied."
            ),
        }

    return {
        "level": reliability.get(
            "level",
            "unknown",
        ),
        "reason": reliability.get(
            "reason"
        ),
    }


# ==========================================================
# GENERIC FORECAST RECOMMENDATIONS
# ==========================================================

def generate_forecast_recommendations(
    forecast_result: Dict[str, Any],
    department: str,
    forecast_name: str,
) -> List[Dict[str, Any]]:
    """
    Generate generic recommendations from a forecast.

    This function does NOT pretend that a forecast alone
    can determine a purchase quantity or operational action.

    Detailed department-specific rules will be added in
    separate modules.
    """

    recommendations = []

    if forecast_result.get(
        "status"
    ) != "success":

        recommendations.append(
            create_recommendation(
                department=department,
                recommendation_type=(
                    "forecast_unavailable"
                ),
                priority="medium",
                title=(
                    f"{forecast_name} unavailable"
                ),
                message=(
                    "The forecasting system could not "
                    "produce a usable forecast."
                ),
                recommended_action=(
                    "Review the available business "
                    "data before making forecast-based "
                    "decisions."
                ),
                evidence={
                    "status": forecast_result.get(
                        "status"
                    ),
                    "reason": forecast_result.get(
                        "message"
                    ),
                },
            )
        )

        return recommendations

    summary = summarize_forecast(
        forecast_result
    )

    trend = calculate_forecast_trend(
        forecast_result
    )

    reliability = get_forecast_reliability(
        forecast_result
    )

    # ------------------------------------------------------
    # INCREASING TREND
    # ------------------------------------------------------

    if trend["direction"] == "increasing":

        priority = (
            "medium"
            if reliability["level"]
            in {
                "moderate",
                "high",
            }
            else "low"
        )

        recommendations.append(
            create_recommendation(
                department=department,
                recommendation_type=(
                    "increasing_demand"
                ),
                priority=priority,
                title=(
                    f"{forecast_name} is increasing"
                ),
                message=(
                    f"The forecast shows an increasing "
                    f"trend of approximately "
                    f"{trend['percentage_change']:.1f}% "
                    "from the first forecast period "
                    "to the last."
                ),
                recommended_action=(
                    "Review operational capacity and "
                    "resource availability before the "
                    "forecasted increase occurs."
                ),
                evidence={
                    "trend": trend,
                    "forecast_summary": summary,
                    "reliability": reliability,
                },
            )
        )

    # ------------------------------------------------------
    # DECREASING TREND
    # ------------------------------------------------------

    elif trend["direction"] == "decreasing":

        recommendations.append(
            create_recommendation(
                department=department,
                recommendation_type=(
                    "decreasing_demand"
                ),
                priority="low",
                title=(
                    f"{forecast_name} is decreasing"
                ),
                message=(
                    f"The forecast shows a decreasing "
                    f"trend of approximately "
                    f"{abs(trend['percentage_change']):.1f}%."
                ),
                recommended_action=(
                    "Review upcoming resource commitments "
                    "and avoid unnecessary increases in "
                    "capacity or stock."
                ),
                evidence={
                    "trend": trend,
                    "forecast_summary": summary,
                    "reliability": reliability,
                },
            )
        )

    # ------------------------------------------------------
    # BASELINE FORECAST
    # ------------------------------------------------------

    if (
        forecast_result.get(
            "selected_method"
        )
        == "historical_mean"
    ):

        recommendations.append(
            create_recommendation(
                department=department,
                recommendation_type=(
                    "forecast_confidence"
                ),
                priority="info",
                title=(
                    f"{forecast_name} is using "
                    "the historical baseline"
                ),
                message=(
                    "The ML candidates did not "
                    "demonstrate sufficient improvement "
                    "over the historical baseline."
                ),
                recommended_action=(
                    "Treat the forecast as a planning "
                    "baseline rather than a high-confidence "
                    "prediction."
                ),
                evidence={
                    "selected_method": (
                        "historical_mean"
                    ),
                    "forecast_summary": summary,
                    "reliability": reliability,
                },
            )
        )

    # ------------------------------------------------------
    # LOW RELIABILITY WARNING
    # ------------------------------------------------------

    if reliability["level"] == "low":

        recommendations.append(
            create_recommendation(
                department=department,
                recommendation_type=(
                    "forecast_reliability"
                ),
                priority="info",
                title=(
                    f"{forecast_name} has "
                    "low confidence"
                ),
                message=(
                    "The forecast provides useful "
                    "planning information, but the "
                    "available validation evidence is "
                    "limited."
                ),
                recommended_action=(
                    "Use the forecast together with "
                    "current business conditions and "
                    "human operational judgement."
                ),
                evidence={
                    "reliability": reliability,
                    "validation_metrics": (
                        forecast_result.get(
                            "validation_metrics"
                        )
                    ),
                },
            )
        )

    return recommendations


# ==========================================================
# MAIN RECOMMENDATION ENGINE
# ==========================================================

def generate_recommendations(
    forecasts: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate business recommendations from multiple
    forecast results.

    Expected input:

        {
            "revenue_forecast": {...},
            "order_forecast": {...},
            "production_workload_forecast": {...},
            "delivery_workload_forecast": {...},
            "cash_inflow_forecast": {...}
        }

    Department-specific recommendation modules will later
    add inventory, production capacity, delivery capacity,
    payment, and purchasing intelligence.
    """

    recommendations = []

    forecast_department_map = {
        "revenue_forecast": (
            "sales",
            "Revenue Forecast",
        ),
        "order_forecast": (
            "sales",
            "Order Forecast",
        ),
        "product_demand_forecast": (
            "sales",
            "Product Demand Forecast",
        ),
        "production_workload_forecast": (
            "production",
            "Production Workload Forecast",
        ),
        "delivery_workload_forecast": (
            "delivery",
            "Delivery Workload Forecast",
        ),
        "cash_inflow_forecast": (
            "accounts",
            "Cash Inflow Forecast",
        ),
    }

    # ------------------------------------------------------
    # PROCESS FORECASTS
    # ------------------------------------------------------

    for (
        forecast_name,
        forecast_result,
    ) in forecasts.items():

        mapping = (
            forecast_department_map.get(
                forecast_name
            )
        )

        if mapping is None:
            continue

        department, readable_name = mapping

        forecast_recommendations = (
            generate_forecast_recommendations(
                forecast_result=forecast_result,
                department=department,
                forecast_name=readable_name,
            )
        )

        recommendations.extend(
            forecast_recommendations
        )

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    recommendations = (
        sort_recommendations(
            recommendations
        )
    )

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    priority_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    for recommendation in recommendations:

        priority = recommendation.get(
            "priority",
            "info",
        )

        if priority in priority_counts:
            priority_counts[
                priority
            ] += 1

    return {
        "status": "success",

        "forecast_count": len(
            forecasts
        ),

        "recommendation_count": len(
            recommendations
        ),

        "priority_counts": (
            priority_counts
        ),

        "recommendations": (
            recommendations
        ),
    }