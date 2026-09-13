from typing import Any, Dict, List, Optional


# ==========================================================
# RISK CONFIGURATION
# ==========================================================

RISK_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0,
}

RISK_SCORES = {
    "CRITICAL": 95,
    "HIGH": 80,
    "MEDIUM": 60,
    "LOW": 25,
    "UNKNOWN": 0,
}


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        number = float(value)

        if number != number:
            return default

        return number

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_risk(
    risk: Any,
) -> str:
    if risk is None:
        return "UNKNOWN"

    normalized = str(
        risk
    ).strip().upper()

    if normalized in RISK_ORDER:
        return normalized

    return "UNKNOWN"


def _normalize_confidence(
    confidence: Any,
) -> str:
    if confidence is None:
        return "unknown"

    normalized = str(
        confidence
    ).strip().lower()

    allowed = {
        "high",
        "moderate",
        "medium",
        "low",
        "insufficient",
        "unknown",
        "baseline",
    }

    if normalized in allowed:
        return normalized

    return "unknown"


# ==========================================================
# DEPARTMENT RISK EXTRACTION
# ==========================================================

def _extract_department_risk(
    department: str,
    intelligence: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize a department intelligence result into a
    consistent Admin Intelligence representation.
    """

    if not intelligence:
        return {
            "department": department,
            "available": False,
            "risk": "UNKNOWN",
            "risk_score": 0,
            "reason": (
                f"No {department} intelligence "
                "was supplied."
            ),
            "forecast_reliability": "unknown",
        }

    risk = _normalize_risk(
        intelligence.get(
            "risk"
        )
        or intelligence.get(
            "cashflow_risk"
        )
    )

    risk_score = _safe_int(
        intelligence.get(
            "risk_score",
            RISK_SCORES.get(
                risk,
                0,
            ),
        )
    )

    confidence = _normalize_confidence(
        intelligence.get(
            "forecast_reliability"
        )
    )

    return {
        "department": department,
        "available": True,
        "risk": risk,
        "risk_score": risk_score,
        "reason": intelligence.get(
            "risk_reason",
            "",
        ),
        "forecast_reliability": confidence,
    }


# ==========================================================
# SALES SUMMARY
# ==========================================================

def _build_sales_summary(
    revenue_forecast: Optional[Dict[str, Any]],
    order_forecast: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build the Admin-level Sales summary from the existing
    revenue and order forecasting outputs.
    """

    revenue = revenue_forecast or {}
    orders = order_forecast or {}

    revenue_risk = "UNKNOWN"

    if revenue:
        reliability = _normalize_confidence(
            revenue.get(
                "reliability",
                {},
            ).get(
                "level"
            )
            if isinstance(
                revenue.get(
                    "reliability"
                ),
                dict,
            )
            else revenue.get(
                "reliability"
            )
        )

        selected_method = revenue.get(
            "selected_method"
        )

        if selected_method == "historical_mean":
            revenue_risk = "MEDIUM"

        elif reliability == "high":
            revenue_risk = "LOW"

        elif reliability in {
            "moderate",
            "medium",
        }:
            revenue_risk = "MEDIUM"

        elif reliability in {
            "low",
            "insufficient",
        }:
            revenue_risk = "MEDIUM"

    order_risk = "UNKNOWN"

    if orders:
        reliability = _normalize_confidence(
            orders.get(
                "reliability",
                {},
            ).get(
                "level"
            )
            if isinstance(
                orders.get(
                    "reliability"
                ),
                dict,
            )
            else orders.get(
                "reliability"
            )
        )

        if reliability == "high":
            order_risk = "LOW"

        elif reliability in {
            "moderate",
            "medium",
        }:
            order_risk = "MEDIUM"

        else:
            order_risk = "MEDIUM"

    risks = [
        revenue_risk,
        order_risk,
    ]

    valid_risks = [
        risk
        for risk in risks
        if risk != "UNKNOWN"
    ]

    if valid_risks:
        overall_risk = max(
            valid_risks,
            key=lambda value: RISK_ORDER[
                value
            ],
        )
    else:
        overall_risk = "UNKNOWN"

    return {
        "department": "sales",
        "available": bool(
            revenue or orders
        ),
        "risk": overall_risk,
        "revenue": {
            "selected_method": revenue.get(
                "selected_method"
            ),
            "historical_mean": revenue.get(
                "historical_mean"
            ),
            "reliability": (
                revenue.get(
                    "reliability"
                )
            ),
        },
        "orders": {
            "selected_method": orders.get(
                "selected_method"
            ),
            "reliability": (
                orders.get(
                    "reliability"
                )
            ),
        },
        "recommendation": (
            "Monitor sales and order trends "
            "alongside current customer demand."
        ),
    }


# ==========================================================
# INVENTORY SUMMARY
# ==========================================================

def _build_inventory_summary(
    inventory_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize inventory intelligence.

    The inventory module uses recommendation priorities
    rather than a single overall risk field.
    """

    if not inventory_result:
        return {
            "department": "inventory",
            "available": False,
            "risk": "UNKNOWN",
            "risk_score": 0,
            "critical_count": 0,
            "high_count": 0,
            "purchase_recommendation_count": 0,
            "estimated_purchase_cost": 0.0,
        }

    recommendations = inventory_result.get(
        "recommendations",
        [],
    )

    if not isinstance(
        recommendations,
        list,
    ):
        recommendations = []

    priority_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    purchase_count = 0
    estimated_purchase_cost = 0.0
    untracked_material_count = 0

    for item in recommendations:

        priority = str(
            item.get(
                "priority",
                "info",
            )
        ).lower()

        if priority in priority_counts:
            priority_counts[
                priority
            ] += 1

        recommendation_type = item.get(
            "type",
            "",
        )

        if recommendation_type == (
            "purchase_recommendation"
        ):
            purchase_count += 1

            evidence = item.get(
                "evidence",
                {},
            )

            if isinstance(
                evidence,
                dict,
            ):
                estimated_purchase_cost += (
                    _safe_float(
                        evidence.get(
                            "estimated_purchase_cost"
                        )
                    )
                )

        if recommendation_type == (
            "untracked_material"
        ):
            untracked_material_count += 1

    if priority_counts["critical"] > 0:
        risk = "CRITICAL"
        risk_score = 95

    elif priority_counts["high"] > 0:
        risk = "HIGH"
        risk_score = 80

    elif priority_counts["medium"] > 0:
        risk = "MEDIUM"
        risk_score = 60

    else:
        risk = "LOW"
        risk_score = 25

    return {
        "department": "inventory",
        "available": True,
        "risk": risk,
        "risk_score": risk_score,
        "priority_counts": priority_counts,
        "critical_count": priority_counts[
            "critical"
        ],
        "high_count": priority_counts[
            "high"
        ],
        "purchase_recommendation_count": (
            purchase_count
        ),
        "estimated_purchase_cost": round(
            estimated_purchase_cost,
            2,
        ),
        "untracked_material_count": (
            untracked_material_count
        ),
        "recommendation_count": len(
            recommendations
        ),
    }


# ==========================================================
# PRODUCTION SUMMARY
# ==========================================================

def _build_production_summary(
    production_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not production_result:
        return {
            "department": "production",
            "available": False,
            "risk": "UNKNOWN",
            "risk_score": 0,
        }

    risk = _normalize_risk(
        production_result.get(
            "risk"
        )
    )

    return {
        "department": "production",
        "available": True,
        "risk": risk,
        "risk_score": _safe_int(
            production_result.get(
                "risk_score",
                RISK_SCORES.get(
                    risk,
                    0,
                ),
            )
        ),
        "expected_workload": _safe_float(
            production_result.get(
                "expected_workload"
            )
        ),
        "expected_weekly_workload": _safe_float(
            production_result.get(
                "expected_weekly_workload"
            )
        ),
        "historical_weekly_capacity": _safe_float(
            production_result.get(
                "historical_weekly_capacity"
            )
        ),
        "capacity_gap": _safe_float(
            production_result.get(
                "capacity_gap"
            )
        ),
        "weekly_capacity_gap": _safe_float(
            production_result.get(
                "weekly_capacity_gap"
            )
        ),
        "current_active_workload": _safe_int(
            production_result.get(
                "current_active_workload"
            )
        ),
        "forecast_reliability": (
            _normalize_confidence(
                production_result.get(
                    "forecast_reliability"
                )
            )
        ),
        "recommendation": production_result.get(
            "recommendation",
            "",
        ),
    }


# ==========================================================
# DELIVERY SUMMARY
# ==========================================================

def _build_delivery_summary(
    delivery_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not delivery_result:
        return {
            "department": "delivery",
            "available": False,
            "risk": "UNKNOWN",
            "risk_score": 0,
        }

    risk = _normalize_risk(
        delivery_result.get(
            "risk"
        )
    )

    return {
        "department": "delivery",
        "available": True,
        "risk": risk,
        "risk_score": _safe_int(
            delivery_result.get(
                "risk_score",
                RISK_SCORES.get(
                    risk,
                    0,
                ),
            )
        ),
        "expected_workload": _safe_float(
            delivery_result.get(
                "expected_workload"
            )
        ),
        "expected_weekly_workload": _safe_float(
            delivery_result.get(
                "expected_weekly_workload"
            )
        ),
        "historical_weekly_capacity": _safe_float(
            delivery_result.get(
                "historical_weekly_capacity"
            )
        ),
        "capacity_gap": _safe_float(
            delivery_result.get(
                "capacity_gap"
            )
        ),
        "weekly_capacity_gap": _safe_float(
            delivery_result.get(
                "weekly_capacity_gap"
            )
        ),
        "current_active_deliveries": _safe_int(
            delivery_result.get(
                "current_active_deliveries"
            )
        ),
        "failed_deliveries": _safe_int(
            delivery_result.get(
                "failed_deliveries"
            )
        ),
        "forecast_reliability": (
            _normalize_confidence(
                delivery_result.get(
                    "forecast_reliability"
                )
            )
        ),
        "recommendation": delivery_result.get(
            "recommendation",
            "",
        ),
    }


# ==========================================================
# ACCOUNTS SUMMARY
# ==========================================================

def _build_accounts_summary(
    accounts_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not accounts_result:
        return {
            "department": "accounts",
            "available": False,
            "risk": "UNKNOWN",
            "risk_score": 0,
        }

    risk = _normalize_risk(
        accounts_result.get(
            "cashflow_risk"
        )
    )

    return {
        "department": "accounts",
        "available": True,
        "risk": risk,
        "risk_score": _safe_int(
            accounts_result.get(
                "risk_score",
                RISK_SCORES.get(
                    risk,
                    0,
                ),
            )
        ),
        "expected_cashflow": _safe_float(
            accounts_result.get(
                "expected_cashflow"
            )
        ),
        "expected_weekly_cashflow": _safe_float(
            accounts_result.get(
                "expected_weekly_cashflow"
            )
        ),
        "historical_weekly_cashflow": _safe_float(
            accounts_result.get(
                "historical_weekly_cashflow"
            )
        ),
        "cashflow_gap": _safe_float(
            accounts_result.get(
                "forecast_cashflow_gap"
            )
        ),
        "weekly_cashflow_gap": _safe_float(
            accounts_result.get(
                "weekly_cashflow_gap"
            )
        ),
        "historical_cashflow_trend": (
            accounts_result.get(
                "historical_cashflow_trend",
                "insufficient",
            )
        ),
        "forecast_reliability": (
            _normalize_confidence(
                accounts_result.get(
                    "forecast_reliability"
                )
            )
        ),
        "recommendation": accounts_result.get(
            "recommendation",
            "",
        ),
    }


# ==========================================================
# OVERALL BUSINESS RISK
# ==========================================================

def _calculate_overall_risk(
    department_summaries: List[
        Dict[str, Any]
    ],
) -> Dict[str, Any]:
    """
    Calculate an Admin-level business risk.

    Critical operational risks receive priority.
    The average risk score provides additional context.
    """

    available = [
        item
        for item in department_summaries
        if item.get(
            "available",
            False,
        )
    ]

    if not available:
        return {
            "risk": "UNKNOWN",
            "risk_score": 0,
            "reason": (
                "No department intelligence "
                "was available."
            ),
        }

    highest_risk = max(
        available,
        key=lambda item: RISK_ORDER.get(
            item.get(
                "risk",
                "UNKNOWN",
            ),
            0,
        ),
    )

    highest_risk_level = _normalize_risk(
        highest_risk.get(
            "risk"
        )
    )

    scores = [
        _safe_float(
            item.get(
                "risk_score"
            )
        )
        for item in available
    ]

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )

    critical_departments = [
        item.get(
            "department"
        )
        for item in available
        if item.get(
            "risk"
        ) == "CRITICAL"
    ]

    high_departments = [
        item.get(
            "department"
        )
        for item in available
        if item.get(
            "risk"
        ) == "HIGH"
    ]

    # A critical department is enough to make the
    # executive business risk critical.
    if critical_departments:

        overall_risk = "CRITICAL"

        reason = (
            "Critical operational risk was detected "
            "in: "
            + ", ".join(
                critical_departments
            )
            + "."
        )

    elif (
        highest_risk_level == "HIGH"
        or average_score >= 70
    ):

        overall_risk = "HIGH"

        reason = (
            "One or more departments show high "
            "operational or financial risk."
        )

    elif (
        highest_risk_level == "MEDIUM"
        or average_score >= 45
    ):

        overall_risk = "MEDIUM"

        reason = (
            "The business is showing moderate "
            "risk in one or more operating areas."
        )

    else:

        overall_risk = "LOW"

        reason = (
            "Available department intelligence does "
            "not indicate significant operational risk."
        )

    return {
        "risk": overall_risk,
        "risk_score": round(
            average_score,
            2,
        ),
        "highest_department_risk": (
            highest_risk_level
        ),
        "critical_departments": (
            critical_departments
        ),
        "high_departments": (
            high_departments
        ),
        "reason": reason,
    }


# ==========================================================
# EXECUTIVE RECOMMENDATIONS
# ==========================================================

def _build_executive_recommendations(
    sales: Dict[str, Any],
    inventory: Dict[str, Any],
    production: Dict[str, Any],
    delivery: Dict[str, Any],
    accounts: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate high-level recommendations for the business
    owner / administrator.

    These recommendations summarize existing intelligence.
    They do not invent new ML predictions.
    """

    recommendations = []

    # ------------------------------------------------------
    # PRODUCTION CAPACITY
    # ------------------------------------------------------

    if production.get(
        "risk"
    ) == "CRITICAL":

        recommendations.append({
            "department": "production",
            "priority": "critical",
            "type": "production_capacity",
            "title": (
                "Production capacity is under pressure"
            ),
            "message": (
                "Forecasted production workload is "
                "materially above historical production "
                "capacity."
            ),
            "recommended_action": (
                production.get(
                    "recommendation"
                )
                or
                "Review production capacity, staffing, "
                "priorities, and scheduling."
            ),
            "evidence": {
                "expected_weekly_workload": production.get(
                    "expected_weekly_workload"
                ),
                "historical_weekly_capacity": production.get(
                    "historical_weekly_capacity"
                ),
                "weekly_capacity_gap": production.get(
                    "weekly_capacity_gap"
                ),
                "risk": production.get(
                    "risk"
                ),
            },
        })

    elif production.get(
        "risk"
    ) == "HIGH":

        recommendations.append({
            "department": "production",
            "priority": "high",
            "type": "production_capacity",
            "title": (
                "Production capacity needs attention"
            ),
            "message": (
                "Expected production workload is "
                "above historical capacity."
            ),
            "recommended_action": (
                production.get(
                    "recommendation"
                )
                or
                "Review production scheduling and "
                "available capacity."
            ),
            "evidence": {
                "weekly_capacity_gap": production.get(
                    "weekly_capacity_gap"
                ),
            },
        })

    # ------------------------------------------------------
    # DELIVERY CAPACITY
    # ------------------------------------------------------

    if delivery.get(
        "risk"
    ) == "CRITICAL":

        recommendations.append({
            "department": "delivery",
            "priority": "critical",
            "type": "delivery_capacity",
            "title": (
                "Delivery capacity is under pressure"
            ),
            "message": (
                "Forecasted delivery workload is "
                "materially above historical delivery "
                "capacity."
            ),
            "recommended_action": (
                delivery.get(
                    "recommendation"
                )
                or
                "Review delivery capacity, scheduling, "
                "routes, and staffing."
            ),
            "evidence": {
                "expected_weekly_workload": delivery.get(
                    "expected_weekly_workload"
                ),
                "historical_weekly_capacity": delivery.get(
                    "historical_weekly_capacity"
                ),
                "weekly_capacity_gap": delivery.get(
                    "weekly_capacity_gap"
                ),
            },
        })

    elif delivery.get(
        "risk"
    ) == "HIGH":

        recommendations.append({
            "department": "delivery",
            "priority": "high",
            "type": "delivery_capacity",
            "title": (
                "Delivery capacity needs attention"
            ),
            "message": (
                "Expected delivery workload exceeds "
                "historical delivery capacity."
            ),
            "recommended_action": (
                delivery.get(
                    "recommendation"
                )
                or
                "Review delivery scheduling and "
                "available delivery resources."
            ),
            "evidence": {
                "weekly_capacity_gap": delivery.get(
                    "weekly_capacity_gap"
                ),
            },
        })

    # ------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------

    if inventory.get(
        "critical_count",
        0,
    ) > 0:

        recommendations.append({
            "department": "inventory",
            "priority": "critical",
            "type": "inventory_risk",
            "title": (
                "Critical inventory risks detected"
            ),
            "message": (
                f"{inventory['critical_count']} "
                "critical inventory recommendation(s) "
                "require attention."
            ),
            "recommended_action": (
                "Review stock-outs and forecasted "
                "material shortages immediately."
            ),
            "evidence": {
                "critical_count": inventory.get(
                    "critical_count"
                ),
                "high_count": inventory.get(
                    "high_count"
                ),
                "purchase_recommendation_count": (
                    inventory.get(
                        "purchase_recommendation_count"
                    )
                ),
            },
        })

    elif inventory.get(
        "high_count",
        0,
    ) > 0:

        recommendations.append({
            "department": "inventory",
            "priority": "high",
            "type": "inventory_risk",
            "title": (
                "Inventory risks need attention"
            ),
            "message": (
                f"{inventory['high_count']} high-priority "
                "inventory recommendation(s) were detected."
            ),
            "recommended_action": (
                "Review material availability and "
                "forecast-based replenishment needs."
            ),
            "evidence": {
                "high_count": inventory.get(
                    "high_count"
                ),
                "untracked_material_count": (
                    inventory.get(
                        "untracked_material_count"
                    )
                ),
            },
        })

    # ------------------------------------------------------
    # UNTRACKED MATERIALS
    # ------------------------------------------------------

    if inventory.get(
        "untracked_material_count",
        0,
    ) > 0:

        recommendations.append({
            "department": "inventory",
            "priority": "high",
            "type": "inventory_data_coverage",
            "title": (
                "Some forecasted materials are not tracked"
            ),
            "message": (
                f"{inventory['untracked_material_count']} "
                "materials have forecasted demand but no "
                "inventory record."
            ),
            "recommended_action": (
                "Verify physical stock and create or "
                "restore inventory records before using "
                "automated purchase planning."
            ),
            "evidence": {
                "untracked_material_count": (
                    inventory.get(
                        "untracked_material_count"
                    )
                ),
            },
        })

    # ------------------------------------------------------
    # ACCOUNTS / CASHFLOW
    # ------------------------------------------------------

    if accounts.get(
        "risk"
    ) == "CRITICAL":

        recommendations.append({
            "department": "accounts",
            "priority": "critical",
            "type": "cashflow_risk",
            "title": (
                "Critical cashflow pressure detected"
            ),
            "message": (
                "Expected cash inflow is materially below "
                "the historical baseline."
            ),
            "recommended_action": (
                accounts.get(
                    "recommendation"
                )
                or
                "Prioritize cash collection and control "
                "non-essential spending."
            ),
            "evidence": {
                "expected_weekly_cashflow": (
                    accounts.get(
                        "expected_weekly_cashflow"
                    )
                ),
                "historical_weekly_cashflow": (
                    accounts.get(
                        "historical_weekly_cashflow"
                    )
                ),
                "weekly_cashflow_gap": (
                    accounts.get(
                        "weekly_cashflow_gap"
                    )
                ),
            },
        })

    elif accounts.get(
        "risk"
    ) == "HIGH":

        recommendations.append({
            "department": "accounts",
            "priority": "high",
            "type": "cashflow_risk",
            "title": (
                "Cashflow needs close monitoring"
            ),
            "message": (
                "Expected cash inflow is below the "
                "historical weekly baseline."
            ),
            "recommended_action": (
                accounts.get(
                    "recommendation"
                )
                or
                "Prioritize collections and monitor "
                "near-term cash requirements."
            ),
            "evidence": {
                "weekly_cashflow_gap": (
                    accounts.get(
                        "weekly_cashflow_gap"
                    )
                ),
            },
        })

    elif accounts.get(
        "risk"
    ) == "MEDIUM":

        recommendations.append({
            "department": "accounts",
            "priority": "medium",
            "type": "cashflow_monitoring",
            "title": (
                "Monitor cashflow"
            ),
            "message": (
                "The cashflow outlook shows some "
                "short-term pressure."
            ),
            "recommended_action": (
                accounts.get(
                    "recommendation"
                )
                or
                "Monitor collections and upcoming "
                "operating cash requirements."
            ),
            "evidence": {
                "weekly_cashflow_gap": (
                    accounts.get(
                        "weekly_cashflow_gap"
                    )
                ),
                "historical_cashflow_trend": (
                    accounts.get(
                        "historical_cashflow_trend"
                    )
                ),
            },
        })

    # ------------------------------------------------------
    # CASHFLOW TREND
    # ------------------------------------------------------

    if accounts.get(
        "historical_cashflow_trend"
    ) == "decreasing":

        recommendations.append({
            "department": "accounts",
            "priority": "high",
            "type": "cashflow_trend",
            "title": (
                "Historical cash inflow is decreasing"
            ),
            "message": (
                "The available payment history shows "
                "lower cash inflow in the later part "
                "of the historical period."
            ),
            "recommended_action": (
                "Review payment collection performance "
                "and upcoming cash requirements."
            ),
            "evidence": {
                "change_percent": (
                    accounts.get(
                        "historical_cashflow_change_percent"
                    )
                ),
            },
        })

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    priority_order = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
        "info": 0,
    }

    recommendations.sort(
        key=lambda item: priority_order.get(
            item.get(
                "priority",
                "info",
            ),
            0,
        ),
        reverse=True,
    )

    return recommendations


# ==========================================================
# BUSINESS HEALTH
# ==========================================================

def _build_business_health(
    department_summaries: List[
        Dict[str, Any]
    ],
    overall_risk: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a concise executive business-health summary.
    """

    available = [
        item
        for item in department_summaries
        if item.get(
            "available",
            False,
        )
    ]

    if not available:
        return {
            "status": "unavailable",
            "health": "UNKNOWN",
            "score": 0,
            "message": (
                "Business health cannot be assessed "
                "because department intelligence is "
                "unavailable."
            ),
        }

    average_risk_score = _safe_float(
        overall_risk.get(
            "risk_score"
        )
    )

    # Convert risk score into an easy-to-understand
    # health score.
    health_score = max(
        0.0,
        min(
            100.0,
            100.0
            - average_risk_score,
        ),
    )

    if overall_risk.get(
        "risk"
    ) == "CRITICAL":

        health = "AT_RISK"

        message = (
            "The business has one or more critical "
            "operational or financial risks."
        )

    elif overall_risk.get(
        "risk"
    ) == "HIGH":

        health = "NEEDS_ATTENTION"

        message = (
            "The business has significant risks "
            "that require management attention."
        )

    elif overall_risk.get(
        "risk"
    ) == "MEDIUM":

        health = "STABLE_WITH_RISKS"

        message = (
            "The business is broadly stable, but "
            "some operating areas require monitoring."
        )

    else:

        health = "HEALTHY"

        message = (
            "Available intelligence does not show "
            "significant business-wide risk."
        )

    return {
        "status": "available",
        "health": health,
        "score": round(
            health_score,
            2,
        ),
        "message": message,
    }


# ==========================================================
# MAIN ADMIN INTELLIGENCE
# ==========================================================

def analyze_admin_intelligence(
    sales_revenue_forecast: Optional[
        Dict[str, Any]
    ] = None,
    sales_order_forecast: Optional[
        Dict[str, Any]
    ] = None,
    inventory_result: Optional[
        Dict[str, Any]
    ] = None,
    production_result: Optional[
        Dict[str, Any]
    ] = None,
    delivery_result: Optional[
        Dict[str, Any]
    ] = None,
    accounts_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:
    """
    Generate executive-level Admin Intelligence from the
    existing department intelligence modules.

    This layer does not create new predictions.

    It combines existing:
        - Sales forecasts
        - Inventory intelligence
        - Production intelligence
        - Delivery intelligence
        - Accounts intelligence
    """

    sales = _build_sales_summary(
        revenue_forecast=(
            sales_revenue_forecast
        ),
        order_forecast=(
            sales_order_forecast
        ),
    )

    inventory = _build_inventory_summary(
        inventory_result
    )

    production = _build_production_summary(
        production_result
    )

    delivery = _build_delivery_summary(
        delivery_result
    )

    accounts = _build_accounts_summary(
        accounts_result
    )

    department_summaries = [
        sales,
        inventory,
        production,
        delivery,
        accounts,
    ]

    overall_risk = _calculate_overall_risk(
        department_summaries
    )

    executive_recommendations = (
        _build_executive_recommendations(
            sales=sales,
            inventory=inventory,
            production=production,
            delivery=delivery,
            accounts=accounts,
        )
    )

    business_health = _build_business_health(
        department_summaries=(
            department_summaries
        ),
        overall_risk=overall_risk,
    )

    return {
        "status": "success",

        "analysis": (
            "admin_business_intelligence"
        ),

        "overall_risk": overall_risk,

        "business_health": business_health,

        "departments": {
            "sales": sales,
            "inventory": inventory,
            "production": production,
            "delivery": delivery,
            "accounts": accounts,
        },

        "executive_recommendations": (
            executive_recommendations
        ),

        "recommendation_count": len(
            executive_recommendations
        ),

        "department_count": len(
            department_summaries
        ),

        "available_department_count": sum(
            1
            for item in department_summaries
            if item.get(
                "available",
                False,
            )
        ),

        "message": (
            "Admin Intelligence combines existing "
            "department-level forecasts and operational "
            "risk analysis into an executive business "
            "overview. It does not create additional "
            "predictions beyond the underlying models."
        ),
    }


# ==========================================================
# CONVENIENCE WRAPPER
# ==========================================================

def generate_admin_recommendations(
    sales_revenue_forecast: Optional[
        Dict[str, Any]
    ] = None,
    sales_order_forecast: Optional[
        Dict[str, Any]
    ] = None,
    inventory_result: Optional[
        Dict[str, Any]
    ] = None,
    production_result: Optional[
        Dict[str, Any]
    ] = None,
    delivery_result: Optional[
        Dict[str, Any]
    ] = None,
    accounts_result: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:
    """
    Convenience function for API/dashboard integration.
    """

    intelligence = (
        analyze_admin_intelligence(
            sales_revenue_forecast=(
                sales_revenue_forecast
            ),
            sales_order_forecast=(
                sales_order_forecast
            ),
            inventory_result=(
                inventory_result
            ),
            production_result=(
                production_result
            ),
            delivery_result=(
                delivery_result
            ),
            accounts_result=(
                accounts_result
            ),
        )
    )

    return {
        "status": "success",
        "analysis": intelligence,
        "recommendations": (
            intelligence.get(
                "executive_recommendations",
                [],
            )
        ),
        "recommendation_count": (
            intelligence.get(
                "recommendation_count",
                0,
            )
        ),
    }