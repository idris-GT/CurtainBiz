import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from the environment configuration."
    )


def get_connection():
    return psycopg2.connect(DATABASE_URL)