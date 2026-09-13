import os
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient
from dotenv import load_dotenv

from app.database.connection import get_connection

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path="../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from .env")

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
ISSUER = f"{SUPABASE_URL}/auth/v1"

security = HTTPBearer()

jwks_client = PyJWKClient(JWKS_URL)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=ISSUER,
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )


def get_current_user_role(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ur.role_id,
                r.name,
                r.description
            FROM user_roles ur
            JOIN roles r
                ON ur.role_id = r.id
            WHERE ur.user_id = %s
              AND r.is_active = TRUE
            LIMIT 1;
        """, (current_user["user_id"],))

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role"
            )

        return {
            **current_user,
            "role_id": row[0],
            "role": row[1],
            "role_description": row[2],
        }

    finally:
        connection.close()
        
def require_permission(permission_name: str):
    def permission_checker(
        current_user=Depends(get_current_user)
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT 1
                FROM user_roles ur
                JOIN role_permissions rp
                    ON ur.role_id = rp.role_id
                JOIN permissions p
                    ON rp.permission_id = p.id
                WHERE ur.user_id = %s
                  AND p.name = %s
                LIMIT 1;
            """, (current_user["user_id"], permission_name))

            permission = cursor.fetchone()

            if permission is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission_name}"
                )

            return current_user

        finally:
            connection.close()

    return permission_checker