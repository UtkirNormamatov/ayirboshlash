import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://turonbank.uz/uz/"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}


def scrape() -> list[dict]:
    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0",
            ignore_https_errors=True,
        )
        page = context.new_page()
        try:
            logger.info("Turonbank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            page.wait_for_function(
                "document.body.innerText.includes('USD')", timeout=15000
            )

            text = page.inner_text("body")

            # Format: USD\nAQSh dollari\n\t\n11960\n\t\n12080\n\t\n12054.03
            pattern = re.compile(
                r'\b(USD|EUR|RUB|GBP|CHF|JPY|KZT)\b'
                r'\n.+?\n\t\n'
                r'([\d.]+)'
                r'\n\t\n'
                r'([\d.]+)'
                r'\n\t\n'
                r'([\d.]+)',
                re.MULTILINE
            )

            for m in pattern.finditer(text):
                cur = m.group(1).strip()
                if cur not in TARGET or cur in seen:
                    continue
                buy  = float(m.group(2))
                sell = float(m.group(3))
                cb   = float(m.group(4))
                seen.add(cur)
                results.append({
                    "currency": cur,
                    "buy":      buy,
                    "sell":     sell,
                    "cb_rate":  cb,
                })
                logger.info(f"  {cur}: buy={buy}, sell={sell}, cb={cb}")

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
        save_rates("turonbank", rates)
        logger.success("Turonbank bazaga saqlandi!")
