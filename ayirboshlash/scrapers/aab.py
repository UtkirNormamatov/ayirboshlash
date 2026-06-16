import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://aab.uz/uz/private/currency-operations/"
CURRENCIES = ["USD", "EUR", "RUB", "GBP"]

def scrape() -> list[dict]:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0",
            ignore_https_errors=True
        )
        page = context.new_page()
        try:
            logger.info("Asia Alliance Bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            def clean(s):
                s = re.sub(r'[^\d.]', '', s.replace(',', '.').strip())
                try:
                    return float(s)
                except:
                    return None

            for cur in CURRENCIES:
                try:
                    btn = page.query_selector(f"text={cur}")
                    if btn:
                        btn.click()
                        page.wait_for_timeout(1000)

                    text = page.inner_text("body")
                    idx = text.find("Sotib olish")
                    if idx < 0:
                        continue

                    chunk = text[idx:idx+150]
                    buy_m  = re.search(r'Sotib olish\n([\d\s.,]+)\s*uzs', chunk)
                    sell_m = re.search(r'Sotish\n([\d\s.,]+)\s*uzs', chunk)
                    cb_m   = re.search(r'MB kursi\n([\d\s.,]+)\s*uzs', chunk)

                    buy  = clean(buy_m.group(1))  if buy_m  else None
                    sell = clean(sell_m.group(1)) if sell_m else None
                    cb   = clean(cb_m.group(1))   if cb_m   else None

                    if not buy and not sell:
                        continue

                    results.append({"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb})
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
        save_rates("aab", rates)
        logger.success("Asia Alliance Bank bazaga saqlandi!")
