import os
import json
import urllib.request
import urllib.error

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest):

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration is missing"
        )

    url = f"{supabase_url}/auth/v1/token?grant_type=password"

    payload = json.dumps({
        "email": data.email,
        "password": data.password
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(
                response.read().decode()
            )

        return {
            "access_token": result["access_token"],
            "token_type": "bearer"
        }

    except urllib.error.HTTPError:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )