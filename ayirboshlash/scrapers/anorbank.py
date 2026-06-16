import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://www.anorbank.uz/uz/about/exchange-rates/"

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
            logger.info("Anorbank ochilmoqda...")
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            text = page.inner_text("body")

            # Format: "Evro, EUR\t13 830,00\t14 230,00\t14 024,34"
            pattern = re.compile(
                r'[^\n]+,\s*(USD|EUR|RUB|GBP|CHF|JPY|KZT|AED)'
                r'\t([\d\s]+,\d+)'
                r'\t([\d\s]+,\d+)'
                r'\t([\d\s]+,\d+)'
            )

            def clean(s):
                return float(s.replace(" ", "").replace(",", ".").strip())

            # USD ni block-container dan olamiz
            usd_block = page.query_selector(".accordion__head .block-container")
            if usd_block:
                divs = usd_block.query_selector_all("div")
                if len(divs) >= 4:
                    try:
                        buy  = clean(divs[1].inner_text())
                        sell = clean(divs[2].inner_text())
                        cb   = clean(divs[3].inner_text())
                        results.append({"currency": "USD", "buy": buy, "sell": sell, "cb_rate": cb})
                        seen.add("USD")
                        logger.info(f"  USD: buy={buy}, sell={sell}, MB={cb}")
                    except:
                        pass

            # Boshqa valyutalarni matndan olamiz
            for m in pattern.finditer(text):
                cur  = m.group(1)
                if cur in seen:
                    continue
                try:
                    buy  = clean(m.group(2))
                    sell = clean(m.group(3))
                    cb   = clean(m.group(4))

                    # 0.0 bo'lsa None
                    if sell == 0.0:
                        sell = None
                    if buy == 0.0:
                        buy = None

                    seen.add(cur)
                    result = {"currency": cur, "buy": buy, "sell": sell, "cb_rate": cb}
                    results.append(result)
                    logger.info(f"  {cur}: buy={buy}, sell={sell}, MB={cb}")
                except Exception as e:
                    logger.warning(f"  {cur} parse xatosi: {e}")

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
        save_rates("anorbank", rates)
        logger.success("Anorbank bazaga saqlandi!")
