import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "ayirboshlash"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        cursor_factory=RealDictCursor,
    )

def save_rates(bank_code: str, rates: list[dict]):
    """
    rates = [
        {"currency": "USD", "buy": 12700.0, "sell": 12750.0, "cb_rate": 12710.0},
        ...
    ]
    """
    if not rates:
        logger.warning(f"{bank_code}: bo'sh natija, saqlanmadi")
        return

    with get_conn() as conn:
        with conn.cursor() as cur:
            # bank_id ni ol
            cur.execute("SELECT id FROM banks WHERE code = %s", (bank_code,))
            row = cur.fetchone()
            if not row:
                logger.error(f"Bank topilmadi: {bank_code}")
                return
            bank_id = row["id"]

            # Kurslarni yoz
            for r in rates:
                cur.execute("""
                    INSERT INTO rates (bank_id, currency, buy, sell, cb_rate)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    bank_id,
                    r["currency"],
                    r.get("buy"),
                    r.get("sell"),
                    r.get("cb_rate"),
                ))
        conn.commit()
    logger.success(f"{bank_code}: {len(rates)} ta kurs saqlandi")

def get_latest_rates():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM latest_rates ORDER BY bank_code, currency")
            return cur.fetchall()
