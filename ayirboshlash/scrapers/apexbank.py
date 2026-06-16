import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://www.apexbank.uz/about/exchange-rates/"

def scrape() -> list[dict]:
    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0",
            ignore_https_errors=True
        )
        page = context.new_page()
        try:
            logger.info("Apexbank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            text = page.inner_text("body")

            pattern = re.compile(
                r'(USD|EUR|RUB|GBP|CHF|JPY|KZT|AED)\n[^\n]+\n'
                r'\t([\d\s]+),\d+[^\t]*\t\n'
                r'([\d\s]+),\d+'
            )

            def clean(s):
                return float(s.replace(" ", "").strip())

            for m in pattern.finditer(text):
                cur = m.group(1).strip()
                if cur in seen:
                    continue
                buy  = clean(m.group(2))
                sell = clean(m.group(3))
                seen.add(cur)
                results.append({"currency": cur, "buy": buy, "sell": sell, "cb_rate": None})
                logger.info(f"  {cur}: buy={buy}, sell={sell}")

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
        save_rates("apexbank", rates)
        logger.success("Apexbank bazaga saqlandi!")
