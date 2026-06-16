import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://www.infinbank.com/uz/private/exchange-rates/"
CURRENCIES = ["USD", "EUR", "GBP", "RUB", "JPY", "CHF"]

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
            logger.info("Infin bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            text = page.inner_text("body")

            def clean(s):
                s = s.replace(" ", "").replace(",", ".").strip()
                try:
                    v = float(s)
                    return v if v > 0 else None
                except:
                    return None

            def parse_row(label):
                pattern = re.compile(
                    rf'{label}\t([\d\s.,\-]+)\t([\d\s.,\-]+)\t([\d\s.,\-]+)\t([\d\s.,\-]+)\t([\d\s.,\-]+)\t([\d\s.,\-]+)'
                )
                m = pattern.search(text)
                if m:
                    return [clean(m.group(i)) for i in range(1, 7)]
                return [None] * 6

            cb_vals   = parse_row("MB kurs\t")
            buy_vals  = parse_row(r"Ayrboshlash shoxobchasi\tOlish")
            sell_vals = parse_row("Sotish")

            for i, cur in enumerate(CURRENCIES):
                buy  = buy_vals[i]
                sell = sell_vals[i]
                cb   = cb_vals[i]

                if not buy and not sell:
                    continue

                results.append({"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb})
                logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")

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
        save_rates("infinbank", rates)
        logger.success("Infin bank bazaga saqlandi!")
