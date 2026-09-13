from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import random

from app.database.connection import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

START_DATE = date(2025, 9, 1)
END_DATE = date(2026, 7, 11)

RANDOM_SEED = 42

QUOTATION_COUNT = 800
ORDER_COUNT = 250

QUOTATION_CONVERSION_RATE = 0.70


# ============================================================
# HELPERS
# ============================================================

def money(value):
    return Decimal(str(round(float(value), 2)))


def utc_datetime(value):
    return datetime(
        value.year,
        value.month,
        value.day,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )


def random_date(rng, start_date, end_date):
    days = (end_date - start_date).days

    return start_date + timedelta(
        days=rng.randint(0, days)
    )


def choose_weighted(rng, values, weights):
    return rng.choices(
        values,
        weights=weights,
        k=1,
    )[0]


def date_range(start_date, end_date):
    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)


# ============================================================
# DATABASE TEMPLATE LOADING
# ============================================================

def load_templates():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        templates = {}

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                customer_code,
                name,
                company_name,
                address,
                city,
                state,
                postal_code
            FROM customers
            WHERE is_active = TRUE
            ORDER BY id;
        """)

        templates["customers"] = cursor.fetchall()

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                product_code,
                name,
                category,
                unit,
                selling_price
            FROM products
            WHERE is_active = TRUE
            ORDER BY id;
        """)

        templates["products"] = cursor.fetchall()

        # ----------------------------------------------------
        # MATERIALS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                material_code,
                name,
                category,
                unit,
                minimum_stock,
                cost_per_unit
            FROM materials
            WHERE is_active = TRUE
            ORDER BY id;
        """)

        templates["materials"] = cursor.fetchall()

        # ----------------------------------------------------
        # EMPLOYEES
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                employee_code,
                first_name,
                last_name,
                department_id,
                job_title
            FROM employees
            WHERE employment_status = 'ACTIVE'
            ORDER BY id;
        """)

        templates["employees"] = cursor.fetchall()

        # ----------------------------------------------------
        # EXISTING DELIVERY USERS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT DISTINCT delivered_by
            FROM deliveries
            WHERE delivered_by IS NOT NULL;
        """)

        templates["delivery_users"] = [
            row[0]
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # DEPARTMENTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name
            FROM departments
            WHERE is_active = TRUE
            ORDER BY id;
        """)

        templates["departments"] = cursor.fetchall()

        # ----------------------------------------------------
        # NEXT IDS
        # ----------------------------------------------------

        tables = [
            "orders",
            "order_items",
            "quotations",
            "quotation_items",
            "production",
            "production_tasks",
            "deliveries",
            "payments",
            "stock_transactions",
        ]

        templates["next_ids"] = {}

        for table in tables:
            cursor.execute(
                f"""
                SELECT COALESCE(MAX(id), 0)
                FROM {table};
                """
            )

            max_id = cursor.fetchone()[0]

            templates["next_ids"][table] = int(max_id) + 1

        return templates

    finally:
        cursor.close()
        connection.close()


# ============================================================
# PRODUCT WEIGHTS
# ============================================================

def product_weight(product):
    name = str(product[2]).lower()

    category = (
        str(product[3]).lower()
        if product[3]
        else ""
    )

    weight = 1.0

    common_terms = [
        "blackout",
        "roller blind",
        "sheer",
        "cotton",
        "printed",
        "eyelet",
        "office",
    ]

    premium_terms = [
        "motorized",
        "premium",
        "wooden",
        "hotel",
    ]

    if any(
        term in name
        for term in common_terms
    ):
        weight += 2.0

    if any(
        term in name
        for term in premium_terms
    ):
        weight *= 0.55

    if category == "commercial":
        weight *= 1.15

    return weight


# ============================================================
# QUOTATIONS
# ============================================================

def generate_quotations(rng, templates):
    customers = templates["customers"]
    products = templates["products"]

    next_id = templates["next_ids"]["quotations"]
    next_item_id = templates["next_ids"]["quotation_items"]

    quotations = []
    quotation_items = []

    product_weights = [
        product_weight(product)
        for product in products
    ]

    approved_ids = []

    for index in range(QUOTATION_COUNT):

        quotation_id = next_id + index

        quotation_date = random_date(
            rng,
            START_DATE,
            END_DATE - timedelta(days=5),
        )

        customer = rng.choice(customers)

        customer_id = customer[0]

        status = choose_weighted(
            rng,
            [
                "DRAFT",
                "SENT",
                "APPROVED",
                "REJECTED",
                "EXPIRED",
            ],
            [
                0.12,
                0.24,
                0.34,
                0.15,
                0.15,
            ],
        )

        valid_until = (
            quotation_date
            + timedelta(days=rng.randint(7, 30))
        )

        selected_products = rng.choices(
            products,
            weights=product_weights,
            k=rng.randint(1, 3),
        )

        unique_products = {}

        for product in selected_products:
            unique_products[product[0]] = product

        subtotal = Decimal("0")

        for product in unique_products.values():

            quantity = rng.randint(1, 8)

            base_price = Decimal(
                str(product[5] or 0)
            )

            discount_factor = Decimal(
                str(round(
                    rng.uniform(0.92, 1.00),
                    4,
                ))
            )

            unit_price = money(
                base_price * discount_factor
            )

            total_price = money(
                unit_price * quantity
            )

            quotation_items.append({
                "id": (
                    next_item_id
                    + len(quotation_items)
                ),
                "quotation_id": quotation_id,
                "product_id": product[0],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "specifications": (
                    "Historical synthetic quotation"
                ),
            })

            subtotal += total_price

        tax_amount = money(
            subtotal * Decimal("0.18")
        )

        total_amount = money(
            subtotal + tax_amount
        )

        quotation = {
            "id": quotation_id,
            "quotation_number": (
                f"HQ-{quotation_date.year}-"
                f"{quotation_id:05d}"
            ),
            "customer_id": customer_id,
            "created_by": None,
            "quotation_date": quotation_date,
            "valid_until": valid_until,
            "status": status,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "notes": (
                "Synthetic historical data "
                "for portfolio forecasting."
            ),
            "created_at": utc_datetime(
                quotation_date
            ),
            "updated_at": utc_datetime(
                quotation_date
            ),
        }

        quotations.append(quotation)

        if status == "APPROVED":
            approved_ids.append(quotation_id)

    return (
        quotations,
        quotation_items,
        approved_ids,
    )


# ============================================================
# ORDERS
# ============================================================

def generate_orders(
    rng,
    templates,
    quotations,
    approved_quotation_ids,
):
    customers = templates["customers"]
    products = templates["products"]

    next_order_id = templates["next_ids"]["orders"]

    orders = []
    order_items = []

    product_weights = [
        product_weight(product)
        for product in products
    ]

    approved_lookup = {
        quotation["id"]: quotation
        for quotation in quotations
        if quotation["id"]
        in approved_quotation_ids
    }

    used_quotations = set()

    for index in range(ORDER_COUNT):

        order_id = next_order_id + index

        use_quotation = (
            bool(approved_lookup)
            and rng.random()
            < QUOTATION_CONVERSION_RATE
        )

        quotation_id = None

        if use_quotation:

            available = [
                qid
                for qid in approved_lookup
                if qid not in used_quotations
            ]

            if available:

                quotation_id = rng.choice(
                    available
                )

                used_quotations.add(
                    quotation_id
                )

        if quotation_id:

            quotation = approved_lookup[
                quotation_id
            ]

            customer_id = quotation[
                "customer_id"
            ]

            order_date = (
                quotation["quotation_date"]
                + timedelta(
                    days=rng.randint(1, 10)
                )
            )

            if order_date > END_DATE:
                order_date = (
                    END_DATE
                    - timedelta(
                        days=rng.randint(0, 3)
                    )
                )

        else:

            customer = rng.choice(customers)

            customer_id = customer[0]

            order_date = random_date(
                rng,
                START_DATE
                + timedelta(days=5),
                END_DATE,
            )

        selected_products = rng.choices(
            products,
            weights=product_weights,
            k=rng.randint(1, 3),
        )

        unique_products = {}

        for product in selected_products:
            unique_products[product[0]] = product

        subtotal = Decimal("0")

        for product in unique_products.values():

            quantity = rng.randint(1, 8)

            base_price = Decimal(
                str(product[5] or 0)
            )

            price_factor = Decimal(
                str(round(
                    rng.uniform(0.93, 1.02),
                    4,
                ))
            )

            unit_price = money(
                base_price * price_factor
            )

            total_price = money(
                unit_price * quantity
            )

            order_items.append({
                "id": (
                    templates["next_ids"]["order_items"]
                    + len(order_items)
                ),
                "order_id": order_id,
                "product_id": product[0],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "specifications": (
                    "Synthetic historical order"
                ),
            })

            subtotal += total_price

        tax_amount = money(
            subtotal * Decimal("0.18")
        )

        total_amount = money(
            subtotal + tax_amount
        )

        age_days = (
            END_DATE - order_date
        ).days

        if age_days > 60:

            status = choose_weighted(
                rng,
                [
                    "DELIVERED",
                    "READY",
                    "QUALITY_CHECK",
                    "IN_PRODUCTION",
                    "CONFIRMED",
                ],
                [
                    0.55,
                    0.15,
                    0.08,
                    0.12,
                    0.10,
                ],
            )

        elif age_days > 25:

            status = choose_weighted(
                rng,
                [
                    "DELIVERED",
                    "READY",
                    "QUALITY_CHECK",
                    "IN_PRODUCTION",
                    "CONFIRMED",
                ],
                [
                    0.25,
                    0.20,
                    0.15,
                    0.25,
                    0.15,
                ],
            )

        else:

            status = choose_weighted(
                rng,
                [
                    "NEW",
                    "CONFIRMED",
                    "IN_PRODUCTION",
                    "QUALITY_CHECK",
                ],
                [
                    0.10,
                    0.35,
                    0.40,
                    0.15,
                ],
            )

        expected_delivery_date = (
            order_date
            + timedelta(
                days=rng.randint(7, 25)
            )
        )

        orders.append({
            "id": order_id,
            "order_number": (
                f"HO-{order_date.year}-"
                f"{order_id:05d}"
            ),
            "customer_id": customer_id,
            "quotation_id": quotation_id,
            "created_by": None,
            "order_date": order_date,
            "expected_delivery_date": (
                expected_delivery_date
            ),
            "status": status,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "notes": (
                "Synthetic historical order "
                "for portfolio forecasting."
            ),
            "created_at": utc_datetime(
                order_date
            ),
            "updated_at": utc_datetime(
                order_date
            ),
        })

    return orders, order_items


# ============================================================
# PRODUCTION
# ============================================================

def generate_production(
    rng,
    templates,
    orders,
):
    employees = templates["employees"]

    next_id = templates["next_ids"]["production"]
    next_task_id = (
        templates["next_ids"]["production_tasks"]
    )

    production = []
    production_tasks = []

    eligible_orders = [
        order
        for order in orders
        if order["status"]
        not in {"NEW", "CANCELLED"}
    ]

    for order in eligible_orders:

        production_id = (
            next_id + len(production)
        )

        start_date = (
            order["order_date"]
            + timedelta(
                days=rng.randint(2, 8)
            )
        )

        completion_date = (
            start_date
            + timedelta(
                days=rng.randint(2, 10)
            )
        )

        if completion_date > END_DATE:
            completion_date = None

        if completion_date:

            status = "COMPLETED"

        else:

            status = choose_weighted(
                rng,
                [
                    "IN_PROGRESS",
                    "QUALITY_CHECK",
                    "PAUSED",
                    "PENDING",
                ],
                [
                    0.40,
                    0.20,
                    0.10,
                    0.30,
                ],
            )

        employee = (
            rng.choice(employees)
            if employees
            else None
        )

        employee_id = (
            employee[0]
            if employee
            else None
        )

        department_id = (
            employee[4]
            if employee
            else None
        )

        production.append({
            "id": production_id,
            "order_id": order["id"],
            "assigned_department_id": (
                department_id
            ),
            "assigned_employee_id": (
                employee_id
            ),
            "status": status,
            "start_date": utc_datetime(
                start_date
            ),
            "completion_date": (
                utc_datetime(
                    completion_date
                )
                if completion_date
                else None
            ),
            "notes": (
                "Synthetic historical "
                "production record."
            ),
            "created_at": utc_datetime(
                start_date
            ),
            "updated_at": utc_datetime(
                completion_date
                or start_date
            ),
        })

        task_names = [
            "Material Preparation",
            "Cutting",
            "Stitching / Assembly",
            "Hardware Installation",
            "Quality Inspection",
        ]

        for task_name in task_names:

            task_id = (
                next_task_id
                + len(production_tasks)
            )

            if status == "COMPLETED":

                task_status = "COMPLETED"

                task_started = (
                    start_date
                    + timedelta(
                        days=rng.randint(0, 2)
                    )
                )

                task_completed = (
                    task_started
                    + timedelta(
                        hours=rng.randint(
                            4,
                            24,
                        )
                    )
                )

            else:

                task_status = choose_weighted(
                    rng,
                    [
                        "PENDING",
                        "IN_PROGRESS",
                        "COMPLETED",
                    ],
                    [
                        0.40,
                        0.25,
                        0.35,
                    ],
                )

                task_started = None
                task_completed = None

                if task_status in {
                    "IN_PROGRESS",
                    "COMPLETED",
                }:

                    task_started = start_date

                if task_status == "COMPLETED":

                    task_completed = (
                        start_date
                        + timedelta(
                            days=rng.randint(
                                1,
                                8,
                            )
                        )
                    )

            assigned_employee = (
                rng.choice(employees)[0]
                if employees
                else None
            )

            production_tasks.append({
                "id": task_id,
                "production_id": production_id,
                "task_name": task_name,
                "assigned_employee_id": (
                    assigned_employee
                ),
                "status": task_status,
                "priority": choose_weighted(
                    rng,
                    [
                        "LOW",
                        "MEDIUM",
                        "HIGH",
                    ],
                    [
                        0.20,
                        0.65,
                        0.15,
                    ],
                ),
                "started_at": (
                    utc_datetime(
                        task_started
                    )
                    if task_started
                    else None
                ),
                "completed_at": (
                    utc_datetime(
                        task_completed
                    )
                    if task_completed
                    else None
                ),
                "notes": (
                    "Synthetic historical "
                    "production task."
                ),
                "created_at": utc_datetime(
                    start_date
                ),
            })

    return production, production_tasks


# ============================================================
# DELIVERIES
# ============================================================

def generate_deliveries(
    rng,
    templates,
    orders,
    production,
):
    next_id = templates["next_ids"]["deliveries"]

    delivery_users = templates.get(
        "delivery_users",
        [],
    )

    production_by_order = {
        record["order_id"]: record
        for record in production
    }

    deliveries = []

    for order in orders:

        production_record = (
            production_by_order.get(
                order["id"]
            )
        )

        if not production_record:
            continue

        production_completion = (
            production_record[
                "completion_date"
            ]
        )

        # ----------------------------------------------------
        # UNFINISHED PRODUCTION
        # ----------------------------------------------------

        if production_completion is None:

            if rng.random() < 0.35:

                scheduled_date = (
                    order[
                        "expected_delivery_date"
                    ]
                )

                if scheduled_date <= END_DATE:

                    deliveries.append({
                        "id": (
                            next_id
                            + len(deliveries)
                        ),
                        "order_id": order["id"],
                        "delivery_address": (
                            "Customer delivery address"
                        ),
                        "scheduled_date": (
                            scheduled_date
                        ),
                        "delivered_date": None,
                        "status": "PENDING",
                        "delivered_by": None,
                        "notes": (
                            "Synthetic historical "
                            "delivery."
                        ),
                        "created_at": utc_datetime(
                            order["order_date"]
                        ),
                        "updated_at": utc_datetime(
                            scheduled_date
                        ),
                    })

            continue

        # ----------------------------------------------------
        # COMPLETED PRODUCTION
        # ----------------------------------------------------

        completion_date = (
            production_completion.date()
        )

        scheduled_date = max(
            order["expected_delivery_date"],
            completion_date
            + timedelta(
                days=rng.randint(1, 4)
            ),
        )

        if scheduled_date > END_DATE:
            continue

        age_days = (
            END_DATE - scheduled_date
        ).days

        if age_days > 30:

            status = choose_weighted(
                rng,
                [
                    "DELIVERED",
                    "FAILED",
                ],
                [
                    0.95,
                    0.05,
                ],
            )

        else:

            status = choose_weighted(
                rng,
                [
                    "DELIVERED",
                    "OUT_FOR_DELIVERY",
                    "SCHEDULED",
                    "PENDING",
                ],
                [
                    0.65,
                    0.10,
                    0.20,
                    0.05,
                ],
            )

        delivered_date = None
        delivered_by = None

        if status == "DELIVERED":

            delivered_date = (
                scheduled_date
                + timedelta(
                    days=rng.randint(0, 3)
                )
            )

            delivered_date = min(
                delivered_date,
                END_DATE,
            )

            if delivery_users:

                delivered_by = rng.choice(
                    delivery_users
                )

        deliveries.append({
            "id": (
                next_id
                + len(deliveries)
            ),
            "order_id": order["id"],
            "delivery_address": (
                "Customer delivery address"
            ),
            "scheduled_date": scheduled_date,
            "delivered_date": delivered_date,
            "status": status,
            "delivered_by": delivered_by,
            "notes": (
                "Synthetic historical delivery."
            ),
            "created_at": utc_datetime(
                order["order_date"]
            ),
            "updated_at": utc_datetime(
                delivered_date
                or scheduled_date
            ),
        })

    return deliveries


# ============================================================
# PAYMENTS
# ============================================================

def generate_payments(
    rng,
    templates,
    orders,
):
    next_id = templates["next_ids"]["payments"]

    payments = []

    for order in orders:

        # Some orders have no payment yet.
        if rng.random() > 0.82:
            continue

        total = Decimal(
            order["total_amount"]
        )

        payment_pattern = rng.random()

        if payment_pattern < 0.60:

            amounts = [total]

        elif payment_pattern < 0.90:

            first = money(
                total * Decimal("0.50")
            )

            second = money(
                total - first
            )

            amounts = [
                first,
                second,
            ]

        else:

            first = money(
                total * Decimal("0.30")
            )

            second = money(
                total * Decimal("0.30")
            )

            third = money(
                total
                - first
                - second
            )

            amounts = [
                first,
                second,
                third,
            ]

        # ----------------------------------------------------
        # IMPORTANT:
        # Payment dates are sorted chronologically.
        # They can never occur before the order.
        # ----------------------------------------------------

        payment_dates = sorted([
            order["order_date"]
            + timedelta(
                days=rng.randint(0, 20)
            )
            for _ in amounts
        ])

        payment_dates = [
            min(
                payment_date,
                END_DATE,
            )
            for payment_date in payment_dates
        ]

        for amount, payment_date in zip(
            amounts,
            payment_dates,
        ):

            payment_id = (
                next_id
                + len(payments)
            )

            payments.append({
                "id": payment_id,
                "order_id": order["id"],
                "amount": amount,
                "payment_method": choose_weighted(
                    rng,
                    [
                        "UPI",
                        "BANK_TRANSFER",
                        "CASH",
                        "CARD",
                    ],
                    [
                        0.40,
                        0.30,
                        0.10,
                        0.20,
                    ],
                ),
                "payment_date": payment_date,
                "reference_number": (
                    f"HPAY-{payment_id:06d}"
                ),
                "status": "COMPLETED",
                "recorded_by": None,
                "notes": (
                    "Synthetic historical payment."
                ),
                "created_at": utc_datetime(
                    payment_date
                ),
            })

    return payments


# ============================================================
# STOCK TRANSACTIONS
# ============================================================

def generate_stock_transactions(
    rng,
    templates,
    orders,
):
    materials = templates["materials"]

    next_id = (
        templates["next_ids"][
            "stock_transactions"
        ]
    )

    transactions = []

    # --------------------------------------------------------
    # OPENING STOCK
    # --------------------------------------------------------

    for material in materials:

        material_id = material[0]

        minimum_stock = Decimal(
            material[5]
        )

        transaction_date = START_DATE

        quantity = money(
            minimum_stock
            * Decimal(
                str(
                    rng.uniform(
                        1.5,
                        3.5,
                    )
                )
            )
        )

        transactions.append({
            "id": (
                next_id
                + len(transactions)
            ),
            "material_id": material_id,
            "transaction_type": "PURCHASE",
            "quantity": quantity,
            "reference_type": "OPENING_STOCK",
            "reference_id": None,
            "notes": (
                "Synthetic historical "
                "opening stock."
            ),
            "created_by": None,
            "created_at": utc_datetime(
                transaction_date
            ),
        })

    # --------------------------------------------------------
    # MATERIAL USAGE
    # --------------------------------------------------------

    for order in orders:

        item_count = rng.randint(1, 3)

        selected_materials = rng.sample(
            materials,
            min(
                item_count,
                len(materials),
            ),
        )

        for material in selected_materials:

            material_id = material[0]

            quantity = money(
                rng.uniform(
                    1.0,
                    12.0,
                )
            )

            transaction_date = (
                order["order_date"]
                + timedelta(
                    days=rng.randint(
                        1,
                        10,
                    )
                )
            )

            if transaction_date > END_DATE:
                transaction_date = END_DATE

            transactions.append({
                "id": (
                    next_id
                    + len(transactions)
                ),
                "material_id": material_id,
                "transaction_type": "ISSUE",
                "quantity": quantity,
                "reference_type": "ORDER",
                "reference_id": order["id"],
                "notes": (
                    "Synthetic historical "
                    "material consumption."
                ),
                "created_by": None,
                "created_at": utc_datetime(
                    transaction_date
                ),
            })

    # --------------------------------------------------------
    # PERIODIC REPLENISHMENT
    # --------------------------------------------------------

    for material in materials:

        material_id = material[0]

        minimum_stock = Decimal(
            material[5]
        )

        for current_date in date_range(
            START_DATE
            + timedelta(days=30),
            END_DATE,
        ):

            if (
                current_date.day == 1
                and rng.random() < 0.65
            ):

                quantity = money(
                    minimum_stock
                    * Decimal(
                        str(
                            rng.uniform(
                                1.0,
                                2.5,
                            )
                        )
                    )
                )

                transactions.append({
                    "id": (
                        next_id
                        + len(transactions)
                    ),
                    "material_id": material_id,
                    "transaction_type": "PURCHASE",
                    "quantity": quantity,
                    "reference_type": "PURCHASE",
                    "reference_id": None,
                    "notes": (
                        "Synthetic historical "
                        "replenishment."
                    ),
                    "created_by": None,
                    "created_at": utc_datetime(
                        current_date
                    ),
                })

    return transactions


# ============================================================
# GENERATED DATA VALIDATION
# ============================================================

def validate_generated_data(
    quotations,
    quotation_items,
    orders,
    order_items,
    production,
    production_tasks,
    deliveries,
    payments,
    stock_transactions,
):
    quotation_ids = {
        q["id"]
        for q in quotations
    }

    order_ids = {
        o["id"]
        for o in orders
    }

    production_ids = {
        p["id"]
        for p in production
    }

    errors = []

    # --------------------------------------------------------
    # QUOTATION ITEMS
    # --------------------------------------------------------

    for item in quotation_items:

        if item["quotation_id"] not in quotation_ids:

            errors.append(
                f"Quotation item {item['id']} "
                f"references missing quotation "
                f"{item['quotation_id']}"
            )

    # --------------------------------------------------------
    # ORDER ITEMS
    # --------------------------------------------------------

    for item in order_items:

        if item["order_id"] not in order_ids:

            errors.append(
                f"Order item {item['id']} "
                f"references missing order "
                f"{item['order_id']}"
            )

    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    for order in orders:

        quotation_id = order[
            "quotation_id"
        ]

        if (
            quotation_id is not None
            and quotation_id not in quotation_ids
        ):

            errors.append(
                f"Order {order['id']} "
                f"references missing quotation "
                f"{quotation_id}"
            )

    # --------------------------------------------------------
    # PRODUCTION
    # --------------------------------------------------------

    for record in production:

        if record["order_id"] not in order_ids:

            errors.append(
                f"Production {record['id']} "
                f"references missing order "
                f"{record['order_id']}"
            )

        if (
            record["status"] == "COMPLETED"
            and record["completion_date"] is None
        ):

            errors.append(
                f"Production {record['id']} "
                f"is COMPLETED without "
                f"completion_date"
            )

        if (
            record["completion_date"]
            and record["start_date"]
            and record["completion_date"]
            < record["start_date"]
        ):

            errors.append(
                f"Production {record['id']} "
                f"has completion before start"
            )

    # --------------------------------------------------------
    # PRODUCTION TASKS
    # --------------------------------------------------------

    for task in production_tasks:

        if task["production_id"] not in production_ids:

            errors.append(
                f"Production task {task['id']} "
                f"references missing production "
                f"{task['production_id']}"
            )

        if (
            task["status"] == "COMPLETED"
            and task["completed_at"] is None
        ):

            errors.append(
                f"Production task {task['id']} "
                f"is COMPLETED without "
                f"completed_at"
            )

        if (
            task["started_at"]
            and task["completed_at"]
            and task["completed_at"]
            < task["started_at"]
        ):

            errors.append(
                f"Production task {task['id']} "
                f"has completion before start"
            )

    # --------------------------------------------------------
    # DELIVERIES
    # --------------------------------------------------------

    production_by_order = {
        record["order_id"]: record
        for record in production
    }

    for delivery in deliveries:

        order_id = delivery["order_id"]

        if order_id not in order_ids:

            errors.append(
                f"Delivery {delivery['id']} "
                f"references missing order "
                f"{order_id}"
            )

            continue

        production_record = (
            production_by_order.get(order_id)
        )

        if not production_record:
            continue

        completion_date = (
            production_record[
                "completion_date"
            ]
        )

        if (
            delivery["status"]
            == "DELIVERED"
        ):

            if delivery[
                "delivered_date"
            ] is None:

                errors.append(
                    f"Delivery {delivery['id']} "
                    f"is DELIVERED without "
                    f"delivered_date"
                )

            if delivery[
                "delivered_by"
            ] is None:

                errors.append(
                    f"Delivery {delivery['id']} "
                    f"is DELIVERED without "
                    f"delivered_by"
                )

        if (
            completion_date
            and delivery["scheduled_date"]
            < completion_date.date()
        ):

            errors.append(
                f"Delivery {delivery['id']} "
                f"is scheduled before production "
                f"completion"
            )

        if (
            delivery["delivered_date"]
            and delivery["delivered_date"]
            < delivery["scheduled_date"]
        ):

            errors.append(
                f"Delivery {delivery['id']} "
                f"has delivered_date before "
                f"scheduled_date"
            )

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    order_lookup = {
        order["id"]: order
        for order in orders
    }

    for payment in payments:

        order = order_lookup.get(
            payment["order_id"]
        )

        if not order:

            errors.append(
                f"Payment {payment['id']} "
                f"references missing order "
                f"{payment['order_id']}"
            )

            continue

        if (
            payment["payment_date"]
            < order["order_date"]
        ):

            errors.append(
                f"Payment {payment['id']} "
                f"occurs before order "
                f"{order['id']}"
            )

    # --------------------------------------------------------
    # DUPLICATE IDS
    # --------------------------------------------------------

    id_groups = {
        "quotations": [
            row["id"]
            for row in quotations
        ],
        "quotation_items": [
            row["id"]
            for row in quotation_items
        ],
        "orders": [
            row["id"]
            for row in orders
        ],
        "order_items": [
            row["id"]
            for row in order_items
        ],
        "production": [
            row["id"]
            for row in production
        ],
        "production_tasks": [
            row["id"]
            for row in production_tasks
        ],
        "deliveries": [
            row["id"]
            for row in deliveries
        ],
        "payments": [
            row["id"]
            for row in payments
        ],
        "stock_transactions": [
            row["id"]
            for row in stock_transactions
        ],
    }

    for table_name, ids in id_groups.items():

        if len(ids) != len(set(ids)):

            errors.append(
                f"Duplicate IDs detected "
                f"in {table_name}"
            )

    return errors


# ============================================================
# GENERATE COMPLETE DATASET
# ============================================================

def generate_historical_dataset():

    rng = random.Random(
        RANDOM_SEED
    )

    templates = load_templates()

    quotations, quotation_items, approved_ids = (
        generate_quotations(
            rng,
            templates,
        )
    )

    orders, order_items = generate_orders(
        rng,
        templates,
        quotations,
        approved_ids,
    )

    production, production_tasks = (
        generate_production(
            rng,
            templates,
            orders,
        )
    )

    deliveries = generate_deliveries(
        rng,
        templates,
        orders,
        production,
    )

    payments = generate_payments(
        rng,
        templates,
        orders,
    )

    stock_transactions = (
        generate_stock_transactions(
            rng,
            templates,
            orders,
        )
    )

    errors = validate_generated_data(
        quotations,
        quotation_items,
        orders,
        order_items,
        production,
        production_tasks,
        deliveries,
        payments,
        stock_transactions,
    )

    return {
        "quotations": quotations,
        "quotation_items": quotation_items,
        "orders": orders,
        "order_items": order_items,
        "production": production,
        "production_tasks": production_tasks,
        "deliveries": deliveries,
        "payments": payments,
        "stock_transactions": stock_transactions,
        "errors": errors,
    }


# ============================================================
# DRY-RUN SUMMARY
# ============================================================

def print_summary(dataset):

    print("\n")
    print("=" * 70)
    print(
        "HISTORICAL DATA GENERATOR — DRY RUN"
    )
    print("=" * 70)

    print(
        f"\nPeriod: "
        f"{START_DATE} -> {END_DATE}"
    )

    print(
        f"Random seed: {RANDOM_SEED}"
    )

    print("\nGenerated records:")
    print("-" * 70)

    for table_name in [
        "quotations",
        "quotation_items",
        "orders",
        "order_items",
        "production",
        "production_tasks",
        "deliveries",
        "payments",
        "stock_transactions",
    ]:

        print(
            f"{table_name:<22}"
            f"{len(dataset[table_name]):>6}"
        )

    print("\nValidation:")
    print("-" * 70)

    if dataset["errors"]:

        print(
            f"ERRORS FOUND: "
            f"{len(dataset['errors'])}"
        )

        for error in dataset[
            "errors"
        ][:30]:

            print(
                f"- {error}"
            )

    else:

        print(
            "No relationship, "
            "workflow, or date errors detected."
        )

    print("\nDatabase changes:")
    print("-" * 70)

    print(
        "NONE — DRY RUN ONLY"
    )

    print("\nSample records:")
    print("-" * 70)

    for table_name in [
        "quotations",
        "orders",
        "production",
        "deliveries",
        "payments",
        "stock_transactions",
    ]:

        rows = dataset[
            table_name
        ]

        print(
            f"\n{table_name.upper()}:"
        )

        for row in rows[:2]:

            print(row)

    print("\n" + "=" * 70)
    print("DRY RUN COMPLETE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    dataset = (
        generate_historical_dataset()
    )

    print_summary(dataset)