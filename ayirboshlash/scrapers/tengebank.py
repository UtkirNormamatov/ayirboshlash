import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://tengebank.uz/"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}

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
            logger.info("Tenge bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            text = page.inner_text("body")

            # Format: USD\nSotib olish\n11950 сум\nSotish\n12070 сум
            pattern = re.compile(
                r'^(USD|EUR|RUB|GBP|CHF|JPY|KZT)\nSotib olish\n([\d\s]+)\s*[a-zA-Zа-яёА-ЯЁ]*\nSotish\n([\d\s]+)',
                re.MULTILINE
            )

            def clean(s):
                try:
                    return float(s.replace(" ", "").strip())
                except:
                    return None

            for m in pattern.finditer(text):
                cur = m.group(1).strip()
                if cur in seen:
                    continue

                buy  = clean(m.group(2))
                sell = clean(m.group(3))

                if not buy and not sell:
                    continue

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
        save_rates("tengebank", rates)
        logger.success("Tenge bank bazaga saqlandi!")
