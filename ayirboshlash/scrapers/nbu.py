import requests
from loguru import logger
from datetime import date

API_URL = "https://nbu.uz/api/collections/individuals_exchange_rates/entries"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}

def clean(s):
    if not s:
        return None
    s = str(s).replace(" ", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return None

def scrape() -> list[dict]:
    results = []
    seen = set()

    try:
        logger.info("NBU API so'rovi...")
        today = date.today().isoformat()
        url = f"{API_URL}?filter[locale:contains]=uz&filter[data_sozdaniya:contains]={today}&limit=9999"
        resp = requests.get(url, verify=False, timeout=15)
        data = resp.json()
        entries = data.get("data", [])

        if not entries:
            url = f"{API_URL}?filter[locale:contains]=uz&limit=10"
            resp = requests.get(url, verify=False, timeout=15)
            data = resp.json()
            entries = data.get("data", [])

        if not entries:
            logger.warning("Ma'lumot topilmadi")
            return results

        rates = entries[0].get("rates", [])
        logger.info(f"{len(rates)} ta valyuta topildi")

        for item in rates:
            cur = item.get("rate_code", "").upper()
            if cur not in TARGET or cur in seen:
                continue

            buy  = clean(item.get("rate_buy"))
            sell = clean(item.get("rate_sell"))
            cb   = clean(item.get("rate_sb"))

            if not buy and not sell:
                continue

            seen.add(cur)
            results.append({"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb})
            logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")

    except Exception as e:
        logger.exception(f"NBU xatosi: {e}")

    logger.success(f"Jami: {len(results)} ta valyuta")
    return results

if __name__ == "__main__":
    from db.database import save_rates
    rates = scrape()
    if rates:
        save_rates("nbu", rates)
        logger.success("NBU bazaga saqlandi!")
