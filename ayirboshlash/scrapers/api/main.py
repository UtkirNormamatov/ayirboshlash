from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import get_conn

app = FastAPI(title="Ayirboshlash.uz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/rates")
def get_rates():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM latest_rates ORDER BY currency, bank_code")
            rows = cur.fetchall()
    return {"status": "ok", "data": [dict(r) for r in rows]}

@app.get("/api/rates/{currency}")
def get_by_currency(currency: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM latest_rates WHERE currency = %s ORDER BY bank_code",
                (currency.upper(),)
            )
            rows = cur.fetchall()
    return {"status": "ok", "currency": currency.upper(), "data": [dict(r) for r in rows]}

@app.get("/api/best")
def get_best():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT currency,
                       MAX(buy)  AS best_buy,
                       MIN(sell) AS best_sell
                FROM latest_rates
                GROUP BY currency
                ORDER BY currency
            """)
            rows = cur.fetchall()
    return {"status": "ok", "data": [dict(r) for r in rows]}
