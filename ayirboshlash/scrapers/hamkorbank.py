import requests
from loguru import logger

URL = "https://api-dbo.hamkorbank.uz/webflow/v1/exchanges"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}

def scrape() -> list[dict]:
    results = []
    seen = set()
    try:
        logger.info("Hamkorbank API so'rovi...")
        resp = requests.get(URL, timeout=15, verify=False)
        items = resp.json().get("data", [])

        # Faqat begin_sum_i=0 bo'lgan asosiy kurslarni olamiz
        for item in items:
            cur = item.get("currency_char", "").upper()
            if cur not in TARGET or cur in seen:
                continue
            if item.get("begin_sum_i", 0) != 0:
                continue

            # Raqamlar 100 ga ko'paytirilgan
            buy  = item.get("buying_rate",  0) / 100
            sell = item.get("selling_rate", 0) / 100
            cb   = item.get("sb_course",    0) / 100

            seen.add(cur)
            result = {"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb}
            results.append(result)
            logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")

    except Exception as e:
        logger.exception(f"Hamkorbank xatosi: {e}")

    logger.success(f"Jami: {len(results)} ta valyuta")
    return results

if __name__ == "__main__":
    from db.database import save_rates
    rates = scrape()
    if rates:
        save_rates("hamkorbank", rates)
        logger.success("Hamkorbank bazaga saqlandi!")
