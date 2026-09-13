from fastapi import APIRouter, Depends

from app.database.connection import get_connection
from app.auth import require_permission


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.get("/")
def get_customers(
    current_user=Depends(require_permission("customers.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                customer_code,
                name,
                email,
                phone,
                address,
                city,
                state
            FROM customers
            ORDER BY id;
        """)

        rows = cursor.fetchall()

        customers = []

        for row in rows:
            customers.append({
                "id": row[0],
                "customer_code": row[1],
                "name": row[2],
                "email": row[3],
                "phone": row[4],
                "address": row[5],
                "city": row[6],
                "state": row[7]
            })

        cursor.close()

        return customers

    finally:
        connection.close()
        
@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    current_user=Depends(require_permission("customers.view"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                customer_code,
                name,
                email,
                phone,
                address,
                city,
                state
            FROM customers
            WHERE id = %s;
        """, (customer_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Customer not found"
            }

        return {
            "id": row[0],
            "customer_code": row[1],
            "name": row[2],
            "email": row[3],
            "phone": row[4],
            "address": row[5],
            "city": row[6],
            "state": row[7]
        }

    finally:
        connection.close()
        
        
from pydantic import BaseModel


class CustomerCreate(BaseModel):
    customer_code: str
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str


@router.post("/")
def create_customer(
    customer: CustomerCreate,
    current_user=Depends(require_permission("customers.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO customers (
                customer_code,
                name,
                email,
                phone,
                address,
                city,
                state
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            customer.customer_code,
            customer.name,
            customer.email,
            customer.phone,
            customer.address,
            customer.city,
            customer.state
        ))

        customer_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Customer created successfully",
            "customer_id": customer_id
        }

    finally:
        connection.close()
        
@router.put("/{customer_id}")
def update_customer(customer_id: int,
                    customer: CustomerCreate,
                    current_user=Depends(require_permission("customers.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE customers
            SET
                customer_code = %s,
                name = %s,
                email = %s,
                phone = %s,
                address = %s,
                city = %s,
                state = %s
            WHERE id = %s
            RETURNING id;
        """, (
            customer.customer_code,
            customer.name,
            customer.email,
            customer.phone,
            customer.address,
            customer.city,
            customer.state,
            customer_id
        ))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Customer not found"
            }

        connection.commit()

        return {
            "message": "Customer updated successfully",
            "customer_id": row[0]
        }

    finally:
        connection.close()
        
@router.delete("/{customer_id}")
def delete_customer(
                    customer_id: int,
                    current_user=Depends(require_permission("customers.manage"))
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM customers
            WHERE id = %s
            RETURNING id;
        """, (customer_id,))

        row = cursor.fetchone()

        if row is None:
            return {
                "message": "Customer not found"
            }

        connection.commit()

        return {
            "message": "Customer deleted successfully",
            "customer_id": row[0]
        }

    finally:
        connection.close()