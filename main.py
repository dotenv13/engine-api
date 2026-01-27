import os
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Create .env with DATABASE_URL=postgresql://...")

app = FastAPI(title="Engine Catalog API")

# CORS (чтобы фронт мог стучаться)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для учебы ок; позже ограничишь доменом фронта
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    # dict_row => результаты сразу как dict
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

@app.get("/filters/makes")
def get_makes():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT make
            FROM engines
            WHERE make IS NOT NULL AND make <> ''
            ORDER BY make;
        """)
        rows = cur.fetchall()
    return [r["make"] for r in rows]

@app.get("/filters/models")
def get_models(make: str = Query(..., min_length=1)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT model
            FROM engines
            WHERE make = %s
              AND model IS NOT NULL AND model <> ''
            ORDER BY model;
        """, (make,))
        rows = cur.fetchall()
    return [r["model"] for r in rows]

@app.get("/filters/years")
def get_years(make: Optional[str] = None, model: Optional[str] = None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT year
            FROM engines
            WHERE make = COALESCE(%s, make)
              AND model = COALESCE(%s, model)
              AND year IS NOT NULL AND year <> ''
            ORDER BY year;
        """, (make, model))
        rows = cur.fetchall()
    return [r["year"] for r in rows]


@app.get("/engines")
def list_engines(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[str] = None,
    engine_code: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    limit: int = Query(24, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    engine_code_like = None if engine_code is None else f"%{engine_code}%"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              e.product_id, e.title, e.make, e.model, e.year,
              e.engine_code, e.engine_type, e.price, e.currency, e.stock_text,
              (
                SELECT image_url
                FROM engine_images i
                WHERE i.product_id = e.product_id
                ORDER BY i.sort_order ASC
                LIMIT 1
              ) AS preview_image
            FROM engines e
            WHERE e.make  = COALESCE(%s, e.make)
              AND e.model = COALESCE(%s, e.model)
              AND e.year  = COALESCE(%s, e.year)
              AND (CAST(%s AS text)   IS NULL OR e.engine_code ILIKE %s)
              AND (CAST(%s AS bigint) IS NULL OR e.price >= %s)
              AND (CAST(%s AS bigint) IS NULL OR e.price <= %s)
            ORDER BY e.product_id DESC
            LIMIT %s OFFSET %s;
            """,
            (
                make,
                model,
                year,
                engine_code, engine_code_like,
                price_min, price_min,
                price_max, price_max,
                limit, offset,
            ),
        )
        items = cur.fetchall()

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM engines e
            WHERE e.make  = COALESCE(%s, e.make)
              AND e.model = COALESCE(%s, e.model)
              AND e.year  = COALESCE(%s, e.year)
              AND (CAST(%s AS text)   IS NULL OR e.engine_code ILIKE %s)
              AND (CAST(%s AS bigint) IS NULL OR e.price >= %s)
              AND (CAST(%s AS bigint) IS NULL OR e.price <= %s);
            """,
            (
                make,
                model,
                year,
                engine_code, engine_code_like,
                price_min, price_min,
                price_max, price_max,
            ),
        )
        total = cur.fetchone()["total"]

    return {"total": total, "limit": limit, "offset": offset, "items": items}


@app.get("/engines/{product_id}")
def get_engine(product_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM engines WHERE product_id = %s;", (product_id,))
        engine = cur.fetchone()
        if not engine:
            raise HTTPException(status_code=404, detail="Engine not found")

        cur.execute(
            """
            SELECT image_url, sort_order
            FROM engine_images
            WHERE product_id = %s
            ORDER BY sort_order ASC;
            """,
            (product_id,),
        )
        images = cur.fetchall()

    engine["images"] = [img["image_url"] for img in images]
    return engine
