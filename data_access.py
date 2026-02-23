from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL

from datetime import date
from typing import Any, Optional




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


def get_provinces() -> list[str]:
    engine = create_db_engine()
    sql = text("""
        SELECT DISTINCT c1.PROVINCIA
        FROM CENSO1 c1
        WHERE c1.PROVINCIA IS NOT NULL
          AND LTRIM(RTRIM(c1.PROVINCIA)) <> ''
        ORDER BY c1.PROVINCIA
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).scalars().all()
    return [r for r in rows if r]


def get_cities(province: Optional[str]) -> list[str]:
    """
    If province is provided, returns cities for that province only.
    """
    engine = create_db_engine()

    if province:
        sql = text("""
            SELECT DISTINCT c1.LOCALIDAD
            FROM CENSO1 c1
            WHERE c1.PROVINCIA = :province
              AND c1.LOCALIDAD IS NOT NULL
              AND LTRIM(RTRIM(c1.LOCALIDAD)) <> ''
            ORDER BY c1.LOCALIDAD
        """)
        params = {"province": province}
    else:
        # If no province, return an empty list to avoid huge dropdowns.
        return []

    with engine.connect() as conn:
        rows = conn.execute(sql, params).scalars().all()
    return [r for r in rows if r]


def get_epigraph_codes() -> list[str]:
    engine = create_db_engine()
    sql = text("""
        SELECT DISTINCT c2.EPIGRAFE
        FROM CENSO2 c2
        WHERE c2.EPIGRAFE IS NOT NULL
          AND LTRIM(RTRIM(c2.EPIGRAFE)) <> ''
        ORDER BY c2.EPIGRAFE
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).scalars().all()
    return [str(r) for r in rows if r]


def search_companies(
    reference_date: date,
    active_only: bool,
    province: Optional[str],
    city: Optional[str],
    epigraph_codes: Optional[list[str]],
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    CENSO1: one row per company (master data)
    CENSO2: multiple rows per company (epigraph history) linked by DNI

    Active rule (mandatory):
      EXISTS in CENSO2 where F_INICIO <= reference_date AND F_FIN > reference_date
    Epigraph filter:
      If epigraph_codes provided -> company must have at least one matching EPIGRAFE
      (and if active_only is also True, that matching record must be active in reference_date)
    """
    engine = create_db_engine()

    where_clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit, "reference_date": reference_date}

    # Master filters (CENSO1)
    if province:
        where_clauses.append("c1.PROVINCIA = :province")
        params["province"] = province

    if city:
        where_clauses.append("c1.LOCALIDAD = :city")
        params["city"] = city

    # Build EXISTS conditions on CENSO2
    exists_conditions: list[str] = ["c2.DNI = c1.DNI"]

    if active_only:
        exists_conditions.append("c2.F_INICIO <= :reference_date")
        exists_conditions.append("c2.F_FIN > :reference_date")

    if epigraph_codes:
        # Use expanding bind param for IN (...)
        exists_conditions.append("c2.EPIGRAFE IN :epigraph_codes")
        params["epigraph_codes"] = tuple(epigraph_codes)

    # If active_only OR epigraph filter is enabled, apply EXISTS
    if active_only or epigraph_codes:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM CENSO2 c2 WHERE " + " AND ".join(exists_conditions) + ")"
        )

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(f"({c})" for c in where_clauses)

    sql = text(f"""
        SELECT TOP (:limit)
            c1.DNI AS dni,
            c1.NOMBRE AS nombre,
            c1.PROVINCIA AS provincia,
            c1.LOCALIDAD AS localidad
        FROM CENSO1 c1
        {where_sql}
        ORDER BY c1.DNI
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return [dict(r) for r in rows]
 