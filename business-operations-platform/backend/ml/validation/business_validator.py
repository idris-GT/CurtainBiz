import pandas as pd


def validate_business_data(dataframes):
    """
    Validate business data without modifying it.

    Returns:
        {
            "valid": True/False,
            "errors": [],
            "warnings": [],
            "tables": {}
        }
    """

    errors = []
    warnings = []
    table_results = {}

    # --------------------------------------------------
    # Required tables
    # --------------------------------------------------

    required_tables = [
        "orders",
        "order_items",
        "products",
        "customers",
        "quotations",
        "quotation_items",
        "materials",
        "inventory",
        "production",
        "production_tasks",
        "deliveries",
        "payments",
    ]

    for table in required_tables:

        if table not in dataframes:
            errors.append(
                f"Required table '{table}' is missing."
            )

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "tables": table_results,
        }

    # --------------------------------------------------
    # Orders
    # --------------------------------------------------

    orders = dataframes["orders"]

    required_order_columns = [
        "id",
        "customer_id",
        "order_date",
        "total_amount",
        "status",
    ]

    missing = [
        column
        for column in required_order_columns
        if column not in orders.columns
    ]

    if missing:
        errors.append(
            f"Orders is missing required columns: {missing}"
        )
    else:

        if orders["id"].duplicated().any():
            errors.append(
                "Orders contains duplicate IDs."
            )

        if (orders["total_amount"] <= 0).any():
            errors.append(
                "Orders contains zero or negative total amounts."
            )

        if orders["order_date"].isna().any():
            errors.append(
                "Orders contains missing order dates."
            )

    table_results["orders"] = {
        "rows": len(orders),
        "status": "checked",
    }

    # --------------------------------------------------
    # Order Items
    # --------------------------------------------------

    order_items = dataframes["order_items"]

    required_item_columns = [
        "id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
        "total_price",
    ]

    missing = [
        column
        for column in required_item_columns
        if column not in order_items.columns
    ]

    if missing:
        errors.append(
            f"Order items is missing required columns: {missing}"
        )
    else:

        if order_items["id"].duplicated().any():
            errors.append(
                "Order items contains duplicate IDs."
            )

        if (order_items["quantity"] <= 0).any():
            errors.append(
                "Order items contains zero or negative quantities."
            )

        if (order_items["unit_price"] <= 0).any():
            errors.append(
                "Order items contains zero or negative prices."
            )

    table_results["order_items"] = {
        "rows": len(order_items),
        "status": "checked",
    }

    # --------------------------------------------------
    # Products
    # --------------------------------------------------

    products = dataframes["products"]

    required_product_columns = [
        "id",
        "name",
        "selling_price",
    ]

    missing = [
        column
        for column in required_product_columns
        if column not in products.columns
    ]

    if missing:
        errors.append(
            f"Products is missing required columns: {missing}"
        )
    else:

        if products["id"].duplicated().any():
            errors.append(
                "Products contains duplicate IDs."
            )

        if (products["selling_price"] <= 0).any():
            errors.append(
                "Products contains zero or negative selling prices."
            )

    table_results["products"] = {
        "rows": len(products),
        "status": "checked",
    }

    # --------------------------------------------------
    # Materials
    # --------------------------------------------------

    materials = dataframes["materials"]

    required_material_columns = [
        "id",
        "name",
        "cost_per_unit",
        "minimum_stock",
    ]

    missing = [
        column
        for column in required_material_columns
        if column not in materials.columns
    ]

    if missing:
        errors.append(
            f"Materials is missing required columns: {missing}"
        )
    else:

        if materials["id"].duplicated().any():
            errors.append(
                "Materials contains duplicate IDs."
            )

        if (materials["cost_per_unit"] <= 0).any():
            errors.append(
                "Materials contains zero or negative costs."
            )

        if (materials["minimum_stock"] < 0).any():
            errors.append(
                "Materials contains negative minimum stock."
            )

    table_results["materials"] = {
        "rows": len(materials),
        "status": "checked",
    }

    # --------------------------------------------------
    # Inventory
    # --------------------------------------------------

    inventory = dataframes["inventory"]

    required_inventory_columns = [
        "id",
        "material_id",
        "quantity_available",
        "reserved_quantity",
    ]

    missing = [
        column
        for column in required_inventory_columns
        if column not in inventory.columns
    ]

    if missing:
        errors.append(
            f"Inventory is missing required columns: {missing}"
        )
    else:

        if inventory["quantity_available"].lt(0).any():
            errors.append(
                "Inventory contains negative available quantities."
            )

        if inventory["reserved_quantity"].lt(0).any():
            errors.append(
                "Inventory contains negative reserved quantities."
            )

        if (
            inventory["reserved_quantity"]
            > inventory["quantity_available"]
        ).any():
            warnings.append(
                "Some inventory records have reserved quantity "
                "greater than available quantity."
            )

    table_results["inventory"] = {
        "rows": len(inventory),
        "status": "checked",
    }

    # --------------------------------------------------
    # Payments
    # --------------------------------------------------

    payments = dataframes["payments"]

    required_payment_columns = [
        "id",
        "order_id",
        "amount",
        "payment_date",
    ]

    missing = [
        column
        for column in required_payment_columns
        if column not in payments.columns
    ]

    if missing:
        errors.append(
            f"Payments is missing required columns: {missing}"
        )
    else:

        if payments["id"].duplicated().any():
            errors.append(
                "Payments contains duplicate IDs."
            )

        if (payments["amount"] < 0).any():
            errors.append(
                "Payments contains negative amounts."
            )

    table_results["payments"] = {
        "rows": len(payments),
        "status": "checked",
    }

    # --------------------------------------------------
    # Production
    # --------------------------------------------------

    production = dataframes["production"]

    if "status" in production.columns:

        if "start_date" in production.columns:
            pending_with_start = (
                (production["status"] == "PENDING")
                & production["start_date"].notna()
            )

            if pending_with_start.any():
                warnings.append(
                    "Production contains PENDING records "
                    "with a start date. These require business "
                    "interpretation and will not be automatically changed."
                )

        if "completion_date" in production.columns:
            completed_without_completion = (
                (production["status"] == "COMPLETED")
                & production["completion_date"].isna()
            )

            if completed_without_completion.any():
                errors.append(
                    "Production contains COMPLETED records "
                    "without completion dates."
                )

    table_results["production"] = {
        "rows": len(production),
        "status": "checked",
    }

    # --------------------------------------------------
    # Production Tasks
    # --------------------------------------------------

    production_tasks = dataframes["production_tasks"]

    if "status" in production_tasks.columns:

        if "completed_at" in production_tasks.columns:

            completed_without_time = (
                (production_tasks["status"] == "COMPLETED")
                & production_tasks["completed_at"].isna()
            )

            if completed_without_time.any():
                errors.append(
                    "Production tasks contain COMPLETED records "
                    "without completion timestamps."
                )

    table_results["production_tasks"] = {
        "rows": len(production_tasks),
        "status": "checked",
    }

    # --------------------------------------------------
    # Deliveries
    # --------------------------------------------------

    deliveries = dataframes["deliveries"]

    if "status" in deliveries.columns:

        if "delivered_date" in deliveries.columns:

            delivered_without_date = (
                (deliveries["status"] == "DELIVERED")
                & deliveries["delivered_date"].isna()
            )

            if delivered_without_date.any():
                errors.append(
                    "Deliveries contain DELIVERED records "
                    "without delivered dates."
                )

        if "delivered_by" in deliveries.columns:

            delivered_without_person = (
                (deliveries["status"] == "DELIVERED")
                & deliveries["delivered_by"].isna()
            )

            if delivered_without_person.any():
                errors.append(
                    "Deliveries contain DELIVERED records "
                    "without a delivery employee."
                )

    table_results["deliveries"] = {
        "rows": len(deliveries),
        "status": "checked",
    }

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "tables": table_results,
    }