import re
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://octobank.uz/"
TARGET = {"USD", "EUR", "RUB", "GBP", "CHF", "JPY", "KZT"}


def scrape() -> list[dict]:
    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = context.new_page()
        try:
            logger.info("Octobank ochilmoqda...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            text = page.inner_text("body")

            # Struktura: USD\n\n11 980\n\n12 060\n\n
            # Bo'shliqli raqam: "11 980" yoki "40" yoki "156"
            pattern = re.compile(
                r'\b(USD|EUR|RUB|GBP|CHF|JPY|KZT)\b'
                r'(?:\n+)'
                r'(\d[\d ]*\d|\d+)'   # buy: "11 980" yoki "40"
                r'(?:\n+)'
                r'(\d[\d ]*\d|\d+)',   # sell: "12 060" yoki "115"
                re.MULTILINE
            )

            def parse_num(s: str) -> float | None:
                clean = s.replace(" ", "").strip()
                try:
                    return float(clean) if clean else None
                except ValueError:
                    return None

            for m in pattern.finditer(text):
                cur = m.group(1).strip()
                if cur in seen:
                    continue
                buy  = parse_num(m.group(2))
                sell = parse_num(m.group(3))
                if not buy and not sell:
                    continue
                seen.add(cur)
                results.append({
                    "currency": cur,
                    "buy":      buy,
                    "sell":     sell,
                    "cb_rate":  None,
                })
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
        save_rates("octobank", rates)
        logger.success("Octobank bazaga saqlandi!")
