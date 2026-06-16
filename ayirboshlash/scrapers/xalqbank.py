import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://xb.uz/page/valyuta-ayirboshlash"

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
            logger.info("Xalq banki ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function(
                "document.body.innerText.includes('USD')", timeout=20000
            )
            page.wait_for_timeout(4000)
            text = page.inner_text("body")

            pattern = re.compile(
                r'(USD|EUR|GBP|RUB|CHF|JPY|KZT|AED)\s*\n+\s*'
                r'Sotish:\s*\n+([\d\s]+)\n+'
                r'Sotib olish:\s*\n+([\d\s]+)'
            )

            for m in pattern.finditer(text):
                cur  = m.group(1).strip()
                sell = float(m.group(2).replace(" ", "").strip())
                buy  = float(m.group(3).replace(" ", "").strip())
                if cur in seen:
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
        save_rates("xalqbank", rates)
        logger.success("Xalq banki kurslari bazaga saqlandi!")
