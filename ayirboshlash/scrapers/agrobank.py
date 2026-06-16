import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://agrobank.uz/uz/person/exchange_rates"

def scrape() -> list[dict]:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0"
        )
        try:
            logger.info("Agrobank ochilmoqda...")
            page.goto(URL, wait_until="networkidle", timeout=30000)
            page.wait_for_function(
                "document.body.innerText.includes('USD')", timeout=15000
            )

            # Har bir qatorni olamiz
            rows = page.query_selector_all("tbody tr")
            logger.info(f"{len(rows)} ta qator topildi")

            for row in rows:
                # Valyuta nomi
                title = row.query_selector("[class*='__title__']")
                if not title:
                    continue
                currency = title.inner_text().strip().upper()

                # Raqamlar: xarid | sotuv | MB
                values = row.query_selector_all("[class*='__value__']")
                nums = []
                for v in values:
                    txt = v.inner_text().replace("\xa0", "").replace(" ", "").replace(",", ".")
                    try:
                        nums.append(float(txt))
                    except:
                        nums.append(None)

                if len(nums) < 2:
                    continue

                result = {
                    "currency": currency,
                    "buy":     nums[0] if len(nums) > 0 else None,
                    "sell":    nums[1] if len(nums) > 1 else None,
                    "cb_rate": nums[2] if len(nums) > 2 else None,
                }
                results.append(result)
                logger.info(f"  {currency}: buy={result['buy']}, sell={result['sell']}, MB={result['cb_rate']}")

        except PWTimeout:
            logger.error("Timeout!")
        except Exception as e:
            logger.exception(f"Xato: {e}")
        finally:
            browser.close()

    # Takroriy valyutalarni olib tashlash
    unique = {}

    for r in results:
            if r["currency"] not in unique:
                unique[r["currency"]] = r

    results = list(unique.values())


    logger.success(f"Jami: {len(results)} ta valyuta")
    return results

if __name__ == "__main__":
    from db.database import save_rates

    rates = scrape()

    if rates:
        save_rates("agrobank", rates)
        logger.success("Agrobank kurslari bazaga saqlandi")

