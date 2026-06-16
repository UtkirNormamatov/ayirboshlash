import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://ipakyulibank.uz/physical/valyuta-ayirboshlash"

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
            logger.info("Ipak Yo'li bank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            text = page.inner_text("body")

            # Format: $ AQSh dollar\t12 000\t12 090
            pattern = re.compile(
                r'[^\t\n]*?(USD|EUR|JPY|GBP|CHF|RUB|KZT)[^\t\n]*?\t([\d\s]+)\t([\d\s]+)'
            )

            # Valyuta belgilaridan kod topish
            symbol_map = {
                "dollar": "USD", "yevro": "EUR", "iyena": "JPY",
                "funt": "GBP", "frank": "CHF", "rubl": "RUB", "tenge": "KZT"
            }

            # Jadval qatorlarini olamiz
            table_pattern = re.compile(
                r'([^\t\n]+)\t([\d\s]+)\t([\d\s]+)\n'
            )

            def clean(s):
                try:
                    return float(s.replace(" ", "").strip())
                except:
                    return None

            for m in table_pattern.finditer(text):
                name = m.group(1).lower()
                buy  = clean(m.group(2))
                sell = clean(m.group(3))

                if not buy or not sell or buy < 10:
                    continue

                cur = None
                for keyword, code in symbol_map.items():
                    if keyword in name:
                        cur = code
                        break

                if not cur or cur in seen:
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
        save_rates("ipakyulibank", rates)
        logger.success("Ipak Yo'li bank bazaga saqlandi!")
