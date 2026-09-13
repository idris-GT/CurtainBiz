import math
from typing import Any, Dict, List

import pandas as pd


# ==========================================================
# HELPERS
# ==========================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        value = float(value)

        if math.isnan(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def _find_column(df, candidates):
    for column in candidates:
        if column in df.columns:
            return column

    return None


def _build_material_lookup(materials_df):
    """
    Build a lookup containing material master data.
    """

    lookup = {}

    if materials_df is None or materials_df.empty:
        return lookup

    material_id_column = _find_column(
        materials_df,
        [
            "id",
            "material_id",
        ],
    )

    if material_id_column is None:
        return lookup

    name_column = _find_column(
        materials_df,
        [
            "name",
            "material_name",
        ],
    )

    category_column = _find_column(
        materials_df,
        [
            "category",
            "material_category",
        ],
    )

    unit_column = _find_column(
        materials_df,
        [
            "unit",
            "unit_type",
        ],
    )

    cost_column = _find_column(
        materials_df,
        [
            "cost_per_unit",
            "unit_cost",
        ],
    )

    minimum_column = _find_column(
        materials_df,
        [
            "minimum_stock",
            "min_stock",
            "minimum_quantity",
        ],
    )

    for _, row in materials_df.iterrows():

        material_id = row.get(
            material_id_column
        )

        if material_id is None:
            continue

        lookup[str(material_id)] = {
            "material_id": material_id,
            "name": (
                str(row.get(name_column))
                if name_column
                and pd.notna(row.get(name_column))
                else f"Material {material_id}"
            ),
            "category": (
                str(row.get(category_column))
                if category_column
                and pd.notna(row.get(category_column))
                else None
            ),
            "unit": (
                str(row.get(unit_column))
                if unit_column
                and pd.notna(row.get(unit_column))
                else None
            ),
            "cost_per_unit": (
                _safe_float(
                    row.get(cost_column)
                )
                if cost_column
                else 0.0
            ),
            "master_minimum_stock": (
                _safe_float(
                    row.get(minimum_column)
                )
                if minimum_column
                else 0.0
            ),
        }

    return lookup


def _get_material_metadata(
    material_id,
    material_lookup,
):
    metadata = material_lookup.get(
        str(material_id)
    )

    if metadata:
        return metadata.copy()

    return {
        "material_id": material_id,
        "name": f"Material {material_id}",
        "category": None,
        "unit": None,
        "cost_per_unit": 0.0,
        "master_minimum_stock": 0.0,
    }


def _extract_forecast_total(
    material_result
):
    forecast_records = material_result.get(
        "forecast",
        [],
    )

    values = []

    for item in forecast_records:

        value = max(
            0.0,
            _safe_float(
                item.get(
                    "predicted_value"
                )
            ),
        )

        values.append(value)

    return {
        "values": values,
        "total": sum(values),
        "periods": len(values),
    }


# ==========================================================
# CURRENT INVENTORY RISK
# ==========================================================

def analyze_inventory_risk(
    inventory_df,
    material_lookup=None,
) -> List[Dict[str, Any]]:

    if inventory_df is None or inventory_df.empty:
        return []

    material_lookup = material_lookup or {}

    material_id_column = _find_column(
        inventory_df,
        [
            "material_id",
            "id_material",
            "id",
        ],
    )

    available_column = _find_column(
        inventory_df,
        [
            "quantity_available",
            "available_quantity",
            "quantity",
            "stock",
        ],
    )

    reserved_column = _find_column(
        inventory_df,
        [
            "reserved_quantity",
            "quantity_reserved",
        ],
    )

    minimum_column = _find_column(
        inventory_df,
        [
            "minimum_stock",
            "min_stock",
            "minimum_quantity",
        ],
    )

    if available_column is None:
        return []

    recommendations = []

    for _, row in inventory_df.iterrows():

        material_id = (
            row.get(material_id_column)
            if material_id_column
            else None
        )

        metadata = _get_material_metadata(
            material_id,
            material_lookup,
        )

        available = _safe_float(
            row.get(available_column)
        )

        reserved = (
            _safe_float(
                row.get(reserved_column)
            )
            if reserved_column
            else 0.0
        )

        minimum_stock = (
            _safe_float(
                row.get(minimum_column)
            )
            if minimum_column
            else metadata[
                "master_minimum_stock"
            ]
        )

        usable_stock = max(
            0.0,
            available - reserved,
        )

        shortage = max(
            0.0,
            minimum_stock - usable_stock,
        )

        if usable_stock <= 0:

            recommendations.append({
                "department": "inventory",
                "type": "stock_out",
                "priority": "critical",
                "title": (
                    f"{metadata['name']} "
                    "is out of stock"
                ),
                "message": (
                    "No usable stock remains after "
                    "accounting for reservations."
                ),
                "recommended_action": (
                    "Arrange material replenishment "
                    "as soon as possible."
                ),
                "evidence": {
                    **metadata,
                    "available_stock": available,
                    "reserved_stock": reserved,
                    "usable_stock": usable_stock,
                    "minimum_stock": minimum_stock,
                },
            })

        elif shortage > 0:

            recommendations.append({
                "department": "inventory",
                "type": "below_minimum_stock",
                "priority": "high",
                "title": (
                    f"{metadata['name']} is below "
                    "minimum stock"
                ),
                "message": (
                    f"Usable stock is "
                    f"{usable_stock:.2f}, "
                    f"below the minimum level of "
                    f"{minimum_stock:.2f}."
                ),
                "recommended_action": (
                    f"Consider replenishing at least "
                    f"{shortage:.2f} units."
                ),
                "evidence": {
                    **metadata,
                    "available_stock": available,
                    "reserved_stock": reserved,
                    "usable_stock": usable_stock,
                    "minimum_stock": minimum_stock,
                    "minimum_stock_shortage": shortage,
                },
            })

    return recommendations


# ==========================================================
# FORECAST-BASED STOCK RISK
# ==========================================================

def analyze_forecast_stock_risk(
    inventory_df,
    material_demand_forecast=None,
    material_lookup=None,
) -> List[Dict[str, Any]]:

    recommendations = []

    if (
        inventory_df is None
        or inventory_df.empty
        or not material_demand_forecast
    ):
        return recommendations

    material_lookup = material_lookup or {}

    material_id_column = _find_column(
        inventory_df,
        [
            "material_id",
            "id_material",
            "id",
        ],
    )

    available_column = _find_column(
        inventory_df,
        [
            "quantity_available",
            "available_quantity",
            "quantity",
            "stock",
        ],
    )

    reserved_column = _find_column(
        inventory_df,
        [
            "reserved_quantity",
            "quantity_reserved",
        ],
    )

    minimum_column = _find_column(
        inventory_df,
        [
            "minimum_stock",
            "min_stock",
            "minimum_quantity",
        ],
    )

    if (
        material_id_column is None
        or available_column is None
    ):
        return recommendations

    for material_result in (
        material_demand_forecast.get(
            "materials",
            [],
        )
    ):

        material_id = material_result.get(
            "material_id"
        )

        if material_id is None:
            continue

        forecast = _extract_forecast_total(
            material_result
        )

        if forecast["periods"] == 0:
            continue

        matching_rows = inventory_df[
            inventory_df[
                material_id_column
            ].astype(str)
            == str(material_id)
        ]

        if matching_rows.empty:
            continue

        row = matching_rows.iloc[0]

        metadata = _get_material_metadata(
            material_id,
            material_lookup,
        )

        available = _safe_float(
            row.get(available_column)
        )

        reserved = (
            _safe_float(
                row.get(reserved_column)
            )
            if reserved_column
            else 0.0
        )

        minimum_stock = (
            _safe_float(
                row.get(minimum_column)
            )
            if minimum_column
            else metadata[
                "master_minimum_stock"
            ]
        )

        usable_stock = max(
            0.0,
            available - reserved,
        )

        projected_stock = (
            usable_stock
            - forecast["total"]
        )

        average_weekly_demand = (
            forecast["total"]
            / forecast["periods"]
        )

        if projected_stock < 0:

            priority = "critical"

        elif projected_stock < minimum_stock:

            priority = "high"

        elif (
            average_weekly_demand > 0
            and usable_stock
            < average_weekly_demand * 2
        ):

            priority = "medium"

        else:

            continue

        recommendations.append({
            "department": "inventory",
            "type": "forecasted_material_shortage",
            "priority": priority,
            "title": (
                f"Forecast inventory risk: "
                f"{metadata['name']}"
            ),
            "message": (
                f"Forecasted demand is "
                f"{forecast['total']:.2f} "
                f"{metadata.get('unit') or 'units'} "
                f"over the next "
                f"{forecast['periods']} weeks. "
                f"Projected stock is "
                f"{projected_stock:.2f}."
            ),
            "recommended_action": (
                "Plan replenishment before "
                "forecasted demand consumes "
                "available stock."
            ),
            "evidence": {
                **metadata,
                "available_stock": available,
                "reserved_stock": reserved,
                "usable_stock": usable_stock,
                "minimum_stock": minimum_stock,
                "forecast_periods": (
                    forecast["periods"]
                ),
                "forecasted_demand": (
                    forecast["total"]
                ),
                "average_weekly_demand": (
                    average_weekly_demand
                ),
                "projected_stock": projected_stock,
            },
        })

    return recommendations


# ==========================================================
# UNTRACKED MATERIAL DETECTION
# ==========================================================

def analyze_untracked_materials(
    inventory_df,
    material_demand_forecast=None,
    material_lookup=None,
) -> List[Dict[str, Any]]:

    recommendations = []

    if not material_demand_forecast:
        return recommendations

    material_lookup = material_lookup or {}

    tracked_ids = set()

    if (
        inventory_df is not None
        and not inventory_df.empty
    ):

        material_id_column = _find_column(
            inventory_df,
            [
                "material_id",
                "id_material",
                "id",
            ],
        )

        if material_id_column:

            tracked_ids = {
                str(value)
                for value in inventory_df[
                    material_id_column
                ]
                .dropna()
                .tolist()
            }

    for material_result in (
        material_demand_forecast.get(
            "materials",
            [],
        )
    ):

        material_id = material_result.get(
            "material_id"
        )

        if material_id is None:
            continue

        if str(material_id) in tracked_ids:
            continue

        forecast = _extract_forecast_total(
            material_result
        )

        if forecast["total"] <= 0:
            continue

        metadata = _get_material_metadata(
            material_id,
            material_lookup,
        )

        average_weekly_demand = (
            forecast["total"]
            / forecast["periods"]
        )

        unit = (
            metadata.get("unit")
            or "units"
        )

        recommendations.append({
            "department": "inventory",
            "type": "untracked_material",
            "priority": "high",
            "title": (
                f"{metadata['name']} has "
                "forecasted demand but no "
                "inventory record"
            ),
            "message": (
                f"Historical material consumption "
                f"indicates future demand of "
                f"approximately "
                f"{forecast['total']:.2f} "
                f"{unit} over the next "
                f"{forecast['periods']} weeks."
            ),
            "recommended_action": (
                "Verify whether this material is "
                "physically stocked. If it is, "
                "create or restore its inventory "
                "record before relying on "
                "automated purchase planning."
            ),
            "evidence": {
                **metadata,
                "forecast_periods": (
                    forecast["periods"]
                ),
                "forecasted_demand": (
                    forecast["total"]
                ),
                "average_weekly_demand": (
                    average_weekly_demand
                ),
                "inventory_record_exists": False,
            },
        })

    return recommendations


# ==========================================================
# PURCHASE RECOMMENDATIONS
# ==========================================================

def generate_purchase_recommendations(
    inventory_df,
    material_demand_forecast=None,
    material_lookup=None,
) -> List[Dict[str, Any]]:

    recommendations = []

    if inventory_df is None or inventory_df.empty:
        return recommendations

    material_lookup = material_lookup or {}

    material_id_column = _find_column(
        inventory_df,
        [
            "material_id",
            "id_material",
            "id",
        ],
    )

    available_column = _find_column(
        inventory_df,
        [
            "quantity_available",
            "available_quantity",
            "quantity",
            "stock",
        ],
    )

    reserved_column = _find_column(
        inventory_df,
        [
            "reserved_quantity",
            "quantity_reserved",
        ],
    )

    minimum_column = _find_column(
        inventory_df,
        [
            "minimum_stock",
            "min_stock",
            "minimum_quantity",
        ],
    )

    if available_column is None:
        return recommendations

    # ------------------------------------------------------
    # BUILD FORECAST LOOKUP
    # ------------------------------------------------------

    forecast_lookup = {}

    if material_demand_forecast:

        for material_result in (
            material_demand_forecast.get(
                "materials",
                [],
            )
        ):

            material_id = (
                material_result.get(
                    "material_id"
                )
            )

            if material_id is None:
                continue

            forecast = _extract_forecast_total(
                material_result
            )

            forecast_lookup[
                str(material_id)
            ] = forecast

    # ------------------------------------------------------
    # ANALYZE EACH INVENTORY ITEM
    # ------------------------------------------------------

    for _, row in inventory_df.iterrows():

        material_id = (
            row.get(
                material_id_column
            )
            if material_id_column
            else None
        )

        metadata = _get_material_metadata(
            material_id,
            material_lookup,
        )

        available = _safe_float(
            row.get(
                available_column
            )
        )

        reserved = (
            _safe_float(
                row.get(
                    reserved_column
                )
            )
            if reserved_column
            else 0.0
        )

        minimum_stock = (
            _safe_float(
                row.get(
                    minimum_column
                )
            )
            if minimum_column
            else metadata[
                "master_minimum_stock"
            ]
        )

        usable_stock = max(
            0.0,
            available - reserved,
        )

        forecast = forecast_lookup.get(
            str(material_id),
            {
                "total": 0.0,
                "periods": 0,
                "values": [],
            },
        )

        forecast_demand = forecast[
            "total"
        ]

        # --------------------------------------------------
        # TARGET STOCK
        # --------------------------------------------------
        #
        # Target = forecast demand + safety/minimum stock
        #
        # This means we don't merely replenish the
        # minimum. We plan for expected future demand too.
        # --------------------------------------------------

        target_stock = (
            forecast_demand
            + minimum_stock
        )

        purchase_quantity = max(
            0.0,
            target_stock
            - usable_stock,
        )

        if purchase_quantity <= 0:
            continue

        # --------------------------------------------------
        # ESTIMATED COST
        # --------------------------------------------------

        unit_cost = _safe_float(
            metadata.get(
                "cost_per_unit"
            )
        )

        estimated_purchase_cost = (
            purchase_quantity
            * unit_cost
        )

        # --------------------------------------------------
        # DEMAND COVERAGE
        # --------------------------------------------------

        if forecast_demand > 0:

            current_coverage_weeks = (
                usable_stock
                / forecast_demand
                * forecast["periods"]
            )

            post_purchase_coverage_weeks = (
                (
                    usable_stock
                    + purchase_quantity
                )
                / forecast_demand
                * forecast["periods"]
            )

        else:

            current_coverage_weeks = None

            post_purchase_coverage_weeks = None

        # --------------------------------------------------
        # PRIORITY
        # --------------------------------------------------

        if usable_stock <= 0:

            priority = "critical"

        elif (
            forecast_demand > 0
            and usable_stock
            < forecast_demand
        ):

            priority = "critical"

        elif usable_stock < minimum_stock:

            priority = "high"

        elif forecast_demand > 0:

            priority = "medium"

        else:

            priority = "low"

        unit = (
            metadata.get("unit")
            or "units"
        )

        # --------------------------------------------------
        # RECOMMENDATION
        # --------------------------------------------------

        recommendations.append({
            "department": "inventory",
            "type": "purchase_recommendation",
            "priority": priority,
            "title": (
                f"Purchase recommendation: "
                f"{metadata['name']}"
            ),
            "message": (
                f"Forecast demand is "
                f"{forecast_demand:.2f} {unit}. "
                f"Usable stock is "
                f"{usable_stock:.2f} {unit}. "
                f"Recommended purchase is "
                f"{purchase_quantity:.2f} {unit}."
            ),
            "recommended_action": (
                f"Consider purchasing "
                f"{purchase_quantity:.2f} {unit}"
                + (
                    f" at an estimated cost of "
                    f"{estimated_purchase_cost:.2f}."
                    if unit_cost > 0
                    else "."
                )
            ),
            "evidence": {
                **metadata,
                "available_stock": available,
                "reserved_stock": reserved,
                "usable_stock": usable_stock,
                "minimum_stock": minimum_stock,
                "forecasted_demand": (
                    forecast_demand
                ),
                "forecast_periods": (
                    forecast["periods"]
                ),
                "target_stock": target_stock,
                "recommended_purchase_quantity": (
                    purchase_quantity
                ),
                "unit_cost": unit_cost,
                "estimated_purchase_cost": (
                    estimated_purchase_cost
                ),
                "current_coverage_weeks": (
                    current_coverage_weeks
                ),
                "post_purchase_coverage_weeks": (
                    post_purchase_coverage_weeks
                ),
            },
        })

    return recommendations


# ==========================================================
# COMPLETE INVENTORY INTELLIGENCE
# ==========================================================

def generate_inventory_recommendations(
    inventory_df,
    demand_forecast=None,
    material_demand_forecast=None,
    materials_df=None,
) -> Dict[str, Any]:
    """
    Generate complete inventory intelligence.

    Includes:

        1. Current stock risk
        2. Forecasted stock risk
        3. Untracked material detection
        4. Purchase quantity recommendations
        5. Estimated purchase cost
        6. Demand coverage
        7. Material metadata
    """

    material_lookup = _build_material_lookup(
        materials_df
    )

    recommendations = []

    # ------------------------------------------------------
    # CURRENT STOCK
    # ------------------------------------------------------

    recommendations.extend(
        analyze_inventory_risk(
            inventory_df=inventory_df,
            material_lookup=material_lookup,
        )
    )

    # ------------------------------------------------------
    # FORECASTED STOCK RISK
    # ------------------------------------------------------

    recommendations.extend(
        analyze_forecast_stock_risk(
            inventory_df=inventory_df,
            material_demand_forecast=(
                material_demand_forecast
            ),
            material_lookup=material_lookup,
        )
    )

    # ------------------------------------------------------
    # UNTRACKED MATERIALS
    # ------------------------------------------------------

    recommendations.extend(
        analyze_untracked_materials(
            inventory_df=inventory_df,
            material_demand_forecast=(
                material_demand_forecast
            ),
            material_lookup=material_lookup,
        )
    )

    # ------------------------------------------------------
    # PURCHASE RECOMMENDATIONS
    # ------------------------------------------------------

    recommendations.extend(
        generate_purchase_recommendations(
            inventory_df=inventory_df,
            material_demand_forecast=(
                material_demand_forecast
            ),
            material_lookup=material_lookup,
        )
    )

    # ------------------------------------------------------
    # SORT BY PRIORITY
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

    type_counts = {}

    total_estimated_purchase_cost = 0.0

    total_recommended_purchase_quantity = 0.0

    purchase_recommendation_count = 0

    for item in recommendations:

        priority = item.get(
            "priority",
            "info",
        )

        if priority in priority_counts:

            priority_counts[
                priority
            ] += 1

        recommendation_type = item.get(
            "type",
            "unknown",
        )

        type_counts[
            recommendation_type
        ] = (
            type_counts.get(
                recommendation_type,
                0,
            )
            + 1
        )

        if (
            recommendation_type
            == "purchase_recommendation"
        ):

            purchase_recommendation_count += 1

            evidence = item.get(
                "evidence",
                {},
            )

            total_estimated_purchase_cost += (
                _safe_float(
                    evidence.get(
                        "estimated_purchase_cost"
                    )
                )
            )

            total_recommended_purchase_quantity += (
                _safe_float(
                    evidence.get(
                        "recommended_purchase_quantity"
                    )
                )
            )

    return {
        "status": "success",
        "recommendation_count": len(
            recommendations
        ),
        "priority_counts": (
            priority_counts
        ),
        "type_counts": type_counts,
        "purchase_recommendation_count": (
            purchase_recommendation_count
        ),
        "total_estimated_purchase_cost": (
            total_estimated_purchase_cost
        ),
        "total_recommended_purchase_quantity": (
            total_recommended_purchase_quantity
        ),
        "recommendations": (
            recommendations
        ),
    }