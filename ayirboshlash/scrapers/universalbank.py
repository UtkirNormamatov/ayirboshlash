import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://universalbank.uz/"
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
            logger.info("Universalbank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            page.wait_for_function(
                "document.body.innerText.includes('USD')", timeout=15000
            )

            text = page.inner_text("body")

            # Format: USD\t12 054.03\t11 990.00 \t12 110.00
            # Ustunlar: valyuta | cb_rate | buy | sell
            pattern = re.compile(
                r'\b(USD|EUR|RUB|GBP|CHF|JPY|KZT)\b'
                r'\t([\d. ]+)'
                r'\t([\d. ]+)'
                r'\t([\d. ]+)',
                re.MULTILINE
            )

            def parse_num(s: str) -> float | None:
                clean = s.replace(" ", "").strip()
                try:
                    v = float(clean)
                    return v if v > 0 else None
                except ValueError:
                    return None

            for m in pattern.finditer(text):
                cur = m.group(1).strip()
                if cur not in TARGET or cur in seen:
                    continue
                cb   = parse_num(m.group(2))
                buy  = parse_num(m.group(3))
                sell = parse_num(m.group(4))
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
        save_rates("universalbank", rates)
        logger.success("Universalbank bazaga saqlandi!")
