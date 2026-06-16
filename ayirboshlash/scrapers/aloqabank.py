import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://aloqabank.uz/uz/"

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
            logger.info("Aloqabank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function(
                "document.body.innerText.includes('USD')", timeout=20000
            )

            rows = page.query_selector_all("tr")
            logger.info(f"{len(rows)} ta qator topildi")

            for row in rows:
                # Valyuta kodi
                code_el = row.query_selector(".currency-name__code")
                if not code_el:
                    continue

                # USD* dan * ni olib tashlaymiz
                currency = re.sub(r'[^A-Z]', '', code_el.inner_text().strip().upper())
                if not currency or currency in seen:
                    continue

                # Raqamlar
                values = row.query_selector_all(".exchange-value span")
                nums = []
                for v in values:
                    txt = re.sub(r'[^\d.]', '', v.inner_text().strip())
                    try:
                        n = float(txt)
                        if n > 1:
                            nums.append(n)
                    except:
                        pass

                if len(nums) < 2:
                    continue

                seen.add(currency)
                result = {
                    "currency": currency,
                    "buy":      nums[0],
                    "sell":     nums[1],
                    "cb_rate":  nums[2] if len(nums) > 2 else None,
                }
                results.append(result)
                logger.info(f"  {currency}: buy={result['buy']}, sell={result['sell']}")

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
        save_rates("aloqabank", rates)
        logger.success("Aloqabank kurslari bazaga saqlandi!")
