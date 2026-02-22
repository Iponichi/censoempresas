from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL


@dataclass(frozen=True)
class Db_config:
    host: str
    port: int
    database: str
    username: str
    password: str
    driver: str


def load_db_config() -> Db_config:
    """
    Load SQL Server settings from .env (never commit credentials).
    Supports DB_MODE=real|demo without code changes.
    """
    load_dotenv(override=True)

    db_mode = os.getenv("DB_MODE", "real").strip().lower()
    if db_mode not in {"real", "demo"}:
        raise ValueError("DB_MODE must be 'real' or 'demo'.")

    suffix = "_DEMO" if db_mode == "demo" else ""

    host = os.getenv(f"DB_HOST{suffix}") or os.getenv("DB_HOST")
    port_str = os.getenv(f"DB_PORT{suffix}") or os.getenv("DB_PORT") or "1433"
    database = os.getenv(f"DB_NAME{suffix}") or os.getenv("DB_NAME")
    username = os.getenv(f"DB_USER{suffix}") or os.getenv("DB_USER")
    password = os.getenv(f"DB_PASSWORD{suffix}") or os.getenv("DB_PASSWORD")
    driver = os.getenv(f"DB_DRIVER{suffix}") or os.getenv("DB_DRIVER") or "ODBC Driver 17 for SQL Server"

    missing = [k for k, v in {
        "DB_HOST": host,
        "DB_NAME": database,
        "DB_USER": username,
        "DB_PASSWORD": password,
        "DB_DRIVER": driver,
    }.items() if not v]

    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)} (mode={db_mode})")

    return Db_config(
        host=host,
        port=int(port_str),
        database=database,
        username=username,
        password=password,
        driver=driver,
    )


def create_db_engine() -> Engine:
    cfg = load_db_config()

    url = URL.create(
        "mssql+pyodbc",
        username=cfg.username,
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        query={
            "driver": cfg.driver,
            "TrustServerCertificate": "yes",
            "Encrypt": "no",
            },
    )

    return create_engine(url, pool_pre_ping=True, future=True)


def test_connection(engine: Engine) -> str:
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1 AS ok")).scalar_one()
    return f"Connected (SELECT 1 returned {value})"

from datetime import date
from typing import Any

def fetch_sample_companies(reference_date: date, limit: int = 10) -> list[dict[str, Any]]:
    """
    Simple query to validate end-to-end flow from Streamlit to SQL Server.
    Adjust column names if needed.
    """
    engine = create_db_engine()

    sql = text(f"""
        SELECT TOP ({limit})
            c1.dni,
            c1.NOMBRE AS nombre,
            c1.PROVINCIA AS provincia,
            c1.LOCALIDAD AS localidad
        FROM CENSO1 c1
        ORDER BY c1.dni
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    return [dict(r) for r in rows]