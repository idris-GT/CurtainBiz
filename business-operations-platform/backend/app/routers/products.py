from decimal import Decimal

from fastapi import APIRouter, Depends
from app.auth import require_permission
from pydantic import BaseModel

from app.database.connection import get_connection


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


class ProductCreate(BaseModel):
    product_code: str
    name: str
    category: str
    description: str | None = None
    unit: str
    selling_price: Decimal
    is_active: bool = True


@router.get("/")
def get_products(
        current_user=Depends(require_permission("products.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                product_code,
                name,
                category,
                description,
                unit,
                selling_price,
                is_active
            FROM products
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        products = []

        for row in rows:
            products.append({
                "id": row[0],
                "product_code": row[1],
                "name": row[2],
                "category": row[3],
                "description": row[4],
                "unit": row[5],
                "selling_price": row[6],
                "is_active": row[7]
            })

        cursor.close()

        return products

    finally:
        connection.close()


@router.get("/{product_id}")
def get_product(
    product_id: int,
    current_user=Depends(require_permission("products.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                product_code,
                name,
                category,
                description,
                unit,
                selling_price,
                is_active
            FROM products
            WHERE id = %s;
        """, (product_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Product not found"
            }

        return {
            "id": row[0],
            "product_code": row[1],
            "name": row[2],
            "category": row[3],
            "description": row[4],
            "unit": row[5],
            "selling_price": row[6],
            "is_active": row[7]
        }

    finally:
        connection.close()


@router.post("/")
def create_product(
    product: ProductCreate,
    current_user=Depends(require_permission("products.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO products (
                product_code,
                name,
                category,
                description,
                unit,
                selling_price,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            product.product_code,
            product.name,
            product.category,
            product.description,
            product.unit,
            product.selling_price,
            product.is_active
        ))

        product_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Product created successfully",
            "product_id": product_id
        }

    finally:
        connection.close()


@router.put("/{product_id}")
def update_product(
    product_id: int,
    product: ProductCreate,
    current_user=Depends(require_permission("products.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE products
            SET
                product_code = %s,
                name = %s,
                category = %s,
                description = %s,
                unit = %s,
                selling_price = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (
            product.product_code,
            product.name,
            product.category,
            product.description,
            product.unit,
            product.selling_price,
            product.is_active,
            product_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Product not found"
            }

        connection.commit()

        return {
            "message": "Product updated successfully",
            "product_id": row[0]
        }

    finally:
        connection.close()


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user=Depends(require_permission("products.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE products
            SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id;
        """, (product_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Product not found"
            }

        connection.commit()

        return {
            "message": "Product deactivated successfully",
            "product_id": row[0]
        }

    finally:
        connection.close()