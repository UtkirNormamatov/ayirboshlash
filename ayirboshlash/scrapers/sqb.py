import requests
from loguru import logger

URL = "https://sqb.uz/api/site-kurs-api/"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}

def scrape() -> list[dict]:
    results = []
    seen = set()

    try:
        logger.info("SQB API so'rovi...")
        resp = requests.get(URL, verify=False, timeout=15)
        data = resp.json().get("data", {})

        # offline dan olamiz, lekin raqamlar 100 ga bo'linadi
        offline = data.get("offline", [])
        logger.info(f"{len(offline)} ta valyuta topildi")

        for item in offline:
            cur = item.get("code", "").upper()
            if cur not in TARGET or cur in seen:
                continue

            try:
                buy  = item.get("buy",  0) / 100
                sell = item.get("sell", 0) / 100
                cb   = item.get("rate", 0) / 100

                if not buy and not sell:
                    continue

                seen.add(cur)
                results.append({"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb})
                logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")
            except Exception as e:
                logger.warning(f"  {cur} xato: {e}")

    except Exception as e:
        logger.exception(f"SQB xatosi: {e}")

    logger.success(f"Jami: {len(results)} ta valyuta")
    return results

if __name__ == "__main__":
    from db.database import save_rates
    rates = scrape()
    if rates:
        save_rates("sqb", rates)
        logger.success("SQB bazaga saqlandi!")
