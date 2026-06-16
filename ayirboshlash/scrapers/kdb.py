import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://kdb.uz/uz/interactive-services/exchange-rates"

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
            logger.info("KDB bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)

            text = page.inner_text("body")

            cur_line = re.search(r'\t((?:USD|EUR|RUB|GBP|CHF|JPY|KZT)(?:\t(?:USD|EUR|RUB|GBP|CHF|JPY|KZT))*)', text)
            rate_line = re.search(r'UZS\t(.+)', text)

            if not cur_line or not rate_line:
                logger.warning("Format topilmadi")
                return results

            currencies = cur_line.group(1).split("\t")
            rate_parts = rate_line.group(1).split("\t")

            def clean(s):
                s = s.replace(",", "").replace(" ", "").strip()
                try:
                    return float(s)
                except:
                    return None

            for i, cur in enumerate(currencies):
                cur = cur.strip()
                if i >= len(rate_parts):
                    continue
                pair = rate_parts[i].strip()
                if "/" not in pair:
                    continue
                parts = pair.split("/")
                if len(parts) < 2:
                    continue
                buy  = clean(parts[0])
                sell = clean(parts[-1])
                if not buy or not sell:
                    continue

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
        save_rates("kdb", rates)
        logger.success("KDB bank bazaga saqlandi!")
