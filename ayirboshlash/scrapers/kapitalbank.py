import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://kapitalbank.uz/uz/services/exchange-rates/"

def scrape() -> list[dict]:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--no-sandbox"]
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0"
        )
        try:
            logger.info("Kapitalbank ochilmoqda...")
            page.goto(URL, wait_until="networkidle", timeout=30000)

            # <pre> ichidagi PHP Array matnini olamiz
            pre = page.locator("pre").first.inner_text()

            # Har bir valyuta blokini ajratamiz
            blocks = re.split(r'\[\d+\]\s*=>\s*Array', pre)

            for block in blocks:
                code  = re.search(r'\[code\]\s*=>\s*(\w+)', block)
                buy   = re.search(r'\[course_buy\]\s*=>\s*([\d.]+)', block)
                sell  = re.search(r'\[course_sell\]\s*=>\s*([\d.]+)', block)

                if not code:
                    continue

                result = {
                    "currency": code.group(1).upper(),
                    "buy":  float(buy.group(1))  if buy  else None,
                    "sell": float(sell.group(1)) if sell else None,
                    "cb_rate": None,
                }
                results.append(result)
                logger.info(f"  {result['currency']}: buy={result['buy']}, sell={result['sell']}")

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
        save_rates("kapitalbank", rates)
        logger.success("Kurslar bazaga saqlandi")
    else:
        logger.error("Saqlash uchun kurs topilmadi")
