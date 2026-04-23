from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from dotenv import load_dotenv
from sqlalchemy import Engine, bindparam, create_engine, text
from sqlalchemy.engine import URL


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    driver: str


def load_db_config() -> DbConfig:
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
    driver = (
        os.getenv(f"DB_DRIVER{suffix}")
        or os.getenv("DB_DRIVER")
        or "ODBC Driver 17 for SQL Server"
    )

    missing = [
        key
        for key, value in {
            "DB_HOST": host,
            "DB_NAME": database,
            "DB_USER": username,
            "DB_PASSWORD": password,
            "DB_DRIVER": driver,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)} (mode={db_mode})")

    return DbConfig(
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

    return [str(row) for row in rows if row]


def get_cities(province: Optional[str]) -> list[str]:
    if not province:
        return []

    engine = create_db_engine()

    sql = text("""
        SELECT DISTINCT c1.LOCALIDAD
        FROM CENSO1 c1
        WHERE c1.PROVINCIA = :province
          AND c1.LOCALIDAD IS NOT NULL
          AND LTRIM(RTRIM(c1.LOCALIDAD)) <> ''
        ORDER BY c1.LOCALIDAD
    """)

    params = {"province": province}

    with engine.connect() as conn:
        rows = conn.execute(sql, params).scalars().all()

    return [str(row) for row in rows if row]


def get_epigraph_options() -> list[dict[str, str]]:
    engine = create_db_engine()

    sql = text("""
        SELECT DISTINCT
            c2.EPIGRAFE AS codigo,
            iae.NOMBRE AS nombre
        FROM CENSO2 c2
        LEFT JOIN IAE iae
            ON iae.EPIGRAFE = c2.EPIGRAFE
        WHERE c2.EPIGRAFE IS NOT NULL
          AND LTRIM(RTRIM(c2.EPIGRAFE)) <> ''
        ORDER BY c2.EPIGRAFE
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    return [
        {
            "codigo": str(row["codigo"]),
            "nombre": str(row["nombre"]).strip() if row["nombre"] else "",
            "label": (
                f'{row["codigo"]} - {row["nombre"]}'
                if row["nombre"]
                else str(row["codigo"])
            ),
        }
        for row in rows
    ]


def search_companies_summary(
    temporal_mode: str,
    reference_date: Optional[date],
    date_from: Optional[date],
    date_to: Optional[date],
    province: Optional[str],
    cities: Optional[list[str]],
    epigraph_codes: Optional[list[str]],
    limit: int = 500,
) -> list[dict[str, Any]]:
    """
    One row per company (CENSO1).
    A company is active when there is at least one row in CENSO2
    with F_INICIO <= reference_date and F_FIN > reference_date.
    For range mode, rows overlapping the selected range are returned.
    """
    engine = create_db_engine()

    where_clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit}

    if province:
        where_clauses.append("c1.PROVINCIA = :province")
        params["province"] = province

    if cities:
        where_clauses.append("c1.LOCALIDAD IN :cities")
        params["cities"] = [str(city) for city in cities]

    exists_conditions: list[str] = ["c2.DNI = c1.DNI"]

    if epigraph_codes:
        exists_conditions.append("c2.EPIGRAFE IN :epigraph_codes")
        params["epigraph_codes"] = [str(code) for code in epigraph_codes]

    if temporal_mode == "date":
        if reference_date is None:
            raise ValueError("reference_date is required when temporal_mode='date'.")

        exists_conditions.append("c2.F_INICIO <= :reference_date")
        exists_conditions.append("c2.F_FIN > :reference_date")
        params["reference_date"] = reference_date

    elif temporal_mode == "range":
        if date_from is None or date_to is None:
            raise ValueError("date_from and date_to are required when temporal_mode='range'.")

        exists_conditions.append("c2.F_INICIO <= :date_to")
        exists_conditions.append("c2.F_FIN > :date_from")
        params["date_from"] = date_from
        params["date_to"] = date_to

    else:
        raise ValueError("temporal_mode must be 'date' or 'range'.")

    where_clauses.append(
        "EXISTS (SELECT 1 FROM CENSO2 c2 WHERE " + " AND ".join(exists_conditions) + ")"
    )

    where_sql = "WHERE " + " AND ".join(f"({clause})" for clause in where_clauses)

    sql = text(f"""
        SELECT TOP (:limit)
            c1.DNI AS dni,
            c1.NOMBRE AS nombre,
            c1.PROVINCIA AS provincia,
            c1.LOCALIDAD AS localidad
        FROM CENSO1 c1
        {where_sql}
        ORDER BY c1.NOMBRE
    """)

    if cities:
        sql = sql.bindparams(bindparam("cities", expanding=True))
    if epigraph_codes:
        sql = sql.bindparams(bindparam("epigraph_codes", expanding=True))

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return [dict(row) for row in rows]


def search_companies_detail(
    temporal_mode: str,
    reference_date: Optional[date],
    date_from: Optional[date],
    date_to: Optional[date],
    province: Optional[str],
    cities: Optional[list[str]],
    epigraph_codes: Optional[list[str]],
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """
    One row per epigraph record (JOIN CENSO1 + CENSO2).
    In date mode, active records for the reference date are returned.
    In range mode, records overlapping the selected range are returned.
    """
    engine = create_db_engine()

    where_clauses: list[str] = ["c2.DNI = c1.DNI"]
    params: dict[str, Any] = {"limit": limit}

    if province:
        where_clauses.append("c1.PROVINCIA = :province")
        params["province"] = province

    if cities:
        where_clauses.append("c1.LOCALIDAD IN :cities")
        params["cities"] = [str(city) for city in cities]

    if epigraph_codes:
        where_clauses.append("c2.EPIGRAFE IN :epigraph_codes")
        params["epigraph_codes"] = [str(code) for code in epigraph_codes]

    if temporal_mode == "date":
        if reference_date is None:
            raise ValueError("reference_date is required when temporal_mode='date'.")

        where_clauses.append("c2.F_INICIO <= :reference_date")
        where_clauses.append("c2.F_FIN > :reference_date")
        params["reference_date"] = reference_date

    elif temporal_mode == "range":
        if date_from is None or date_to is None:
            raise ValueError("date_from and date_to are required when temporal_mode='range'.")

        where_clauses.append("c2.F_INICIO <= :date_to")
        where_clauses.append("c2.F_FIN > :date_from")
        params["date_from"] = date_from
        params["date_to"] = date_to

    else:
        raise ValueError("temporal_mode must be 'date' or 'range'.")

    where_sql = "WHERE " + " AND ".join(f"({clause})" for clause in where_clauses)

    sql = text(f"""
        SELECT TOP (:limit)
            c1.DNI AS dni,
            c1.NOMBRE AS nombre,
            c1.PROVINCIA AS provincia,
            c1.LOCALIDAD AS localidad,
            c2.EPIGRAFE AS epigrafe,
            iae.NOMBRE AS nombre_epigrafe,
            c2.F_INICIO AS f_inicio,
            c2.F_FIN AS f_fin
        FROM CENSO1 c1
        JOIN CENSO2 c2
            ON c2.DNI = c1.DNI
        LEFT JOIN IAE iae
            ON iae.EPIGRAFE = c2.EPIGRAFE
        {where_sql}
        ORDER BY c1.NOMBRE, c2.EPIGRAFE, c2.F_INICIO
    """)

    if cities:
        sql = sql.bindparams(bindparam("cities", expanding=True))
    if epigraph_codes:
        sql = sql.bindparams(bindparam("epigraph_codes", expanding=True))

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return [dict(row) for row in rows]