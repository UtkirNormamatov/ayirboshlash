from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://asakabank.uz"
API_URL = "https://back.asakabank.uz/core/v1/currency-list/"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}

def scrape() -> list[dict]:
    results = []
    seen = set()
    api_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0",
            ignore_https_errors=True
        )
        page = context.new_page()

        def on_response(response):
            if "currency-list" in response.url:
                try:
                    data = response.json()
                    api_data.extend(data.get("results", []))
                except:
                    pass

        page.on("response", on_response)

        try:
            logger.info("Asaka bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)

            # Faqat Individual (currency_type=1) kurslarini olamiz
            for item in api_data:
                if item.get("currency_type") != 1:
                    continue

                cur = item.get("short_name", "").upper()
                if cur not in TARGET or cur in seen:
                    continue

                try:
                    buy  = float(item.get("purchase") or 0)
                    sell = float(item.get("sale") or 0)
                    cb   = float(item.get("rate_cb") or 0)

                    if not buy and not sell:
                        continue

                    seen.add(cur)
                    result = {
                        "currency": cur,
                        "buy":      buy  if buy  else None,
                        "sell":     sell if sell else None,
                        "cb_rate":  cb   if cb   else None,
                    }
                    results.append(result)
                    logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")
                except Exception as e:
                    logger.warning(f"  {cur} xato: {e}")

        except PWTimeout:
            logger.error("Timeout!")
        except Exception as e:
            logger.exception(f"Xato: {e}")
        finally:
            browser.close()

    logger.success(f"Jami: {len(results)} ta valyuta")
    return results

if __name__ == "__main__":
    from db.database import save_rates
    rates = scrape()
    if rates:
        save_rates("asakabank", rates)
        logger.success("Asaka bank bazaga saqlandi!")
