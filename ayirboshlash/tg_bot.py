import os
import asyncio
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from dotenv import load_dotenv
from loguru import logger
from telegram import Bot
from telegram.constants import ParseMode
from db.database import get_latest_rates
from PIL import Image, ImageDraw, ImageFont
import httpx

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

BANK_ORDER = [
    ("agrobank", "AGROBANK", "🌾"),
    ("aloqabank", "ALOQA BANK", "📞"),
    ("anorbank", "ANORBANK", "🍐"),
    ("apexbank", "APEX BANK", "⬆️"),
    ("asakabank", "ASAKA BANK", "🏦"),
    ("aab", "ASIA ALIANCE", "🌏"),
    ("brb", "BRB", "💳"),
    ("davrbank", "DAVR BANK", "⏰"),
    ("garantbank", "GARANT BANK", "🛡️"),
    ("hamkorbank", "HAMKORBANK", "🤝"),
    ("hayotbank", "HAYOT BANK", "🌿"),
    ("infinbank", "INFIN BANK", "♾️"),
    ("ipakyulibank", "IPAK YO'LI BANK", "🐛"),
    ("ipotekabank", "IPOTEKA BANK", "🏠"),
    ("kapitalbank", "KAPITAL BANK", "💰"),
    ("kdb", "KDB BANK", "🇰🇷"),
    ("mkbank", "MKBANK", "🏛️"),
    ("nbu", "MILLIY BANK", "⭐"),
    ("octobank", "OCTOBANK", "🐙"),
    ("ofb", "OFB", "🔷"),
    ("poytaxtbank", "POYTAXT BANK", "🏙️"),
    ("saderatbank", "SADERAT BANK", "🇮🇷"),
    ("sqb", "SQB", "📊"),
    ("tengebank", "TENGE BANK", "🇰🇿"),
    ("trustbank", "TRASTBANK", "🤲"),
    ("turonbank", "TURON BANK", "🕌"),
    ("universalbank", "UNIVERSAL BANK", "🌍"),
    ("xalqbank", "XALQ BANK", "👥"),
    ("ziraatbank", "ZIRAAT BANK", "🌱"),
]

LOGOS_DIR = "logos"

def fmt(value) -> str:
    if value is None:
        return "—"
    v = int(Decimal(str(value)))
    return f"{v:,}".replace(",", " ")

def create_rates_image(currency: str = "USD") -> BytesIO:
    rates = get_latest_rates()

    data = {}
    cb_rate = None
    scraped_at = None

    for r in rates:
        if r["currency"] != currency:
            continue
        data[r["bank_code"]] = {"buy": r["buy"], "sell": r["sell"]}
        if r["cb_rate"] and cb_rate is None:
            cb_rate = r["cb_rate"]
        if r["scraped_at"] and scraped_at is None:
            scraped_at = r["scraped_at"]

    now = scraped_at or datetime.now()
    date_str = now.strftime("%d.%m.%Y %H:%M")
    cb_str = fmt(cb_rate) if cb_rate else "—"

    active_banks = [(code, name, emoji) for code, name, emoji in BANK_ORDER if code in data]
    half = (len(active_banks) + 1) // 2
    left_banks = active_banks[:half]
    right_banks = active_banks[half:]

    width = 900
    row_height = 50
    header_height = 100
    footer_height = 50
    max_rows = max(len(left_banks), len(right_banks))
    total_height = header_height + (max_rows * row_height) + footer_height

    img = Image.new('RGB', (width, total_height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        bank_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
        rate_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        title_font = header_font = bank_font = rate_font = ImageFont.load_default()

    y = 20
    draw.text((width//2, y), f"{currency} KURSLARI", fill='#000000', font=title_font, anchor="mt")
    y += 35
    draw.text((width//2, y), f"{date_str}  |  MB: {cb_str} so'm", fill='#666666', font=header_font, anchor="mt")
    y += 45

    draw.text((50, y), "BANKLAR", fill='#000000', font=header_font)
    draw.text((220, y), "SOTIB OLISH", fill='#000000', font=header_font)
    draw.text((370, y), "SOTISH", fill='#000000', font=header_font)
    draw.text((500, y), "BANKLAR", fill='#000000', font=header_font)
    draw.text((670, y), "SOTIB OLISH", fill='#000000', font=header_font)
    draw.text((820, y), "SOTISH", fill='#000000', font=header_font)

    y += 30
    draw.line([(30, y), (width-30, y)], fill='#cccccc', width=2)
    y += 10

    for i in range(max_rows):
        if i < len(left_banks):
            code, name, emoji = left_banks[i]
            buy = fmt(data[code]["buy"])
            sell = fmt(data[code]["sell"])
            draw.text((50, y), f"{emoji} {name}", fill='#000000', font=bank_font)
            draw.text((230, y), buy, fill='#000000', font=rate_font, anchor="mt")
            draw.text((380, y), sell, fill='#000000', font=rate_font, anchor="mt")

        if i < len(right_banks):
            code, name, emoji = right_banks[i]
            buy = fmt(data[code]["buy"])
            sell = fmt(data[code]["sell"])
            draw.text((500, y), f"{emoji} {name}", fill='#000000', font=bank_font)
            draw.text((680, y), buy, fill='#000000', font=rate_font, anchor="mt")
            draw.text((830, y), sell, fill='#000000', font=rate_font, anchor="mt")

        y += row_height

    draw.text((width//2, total_height-30), "@bank_faoliyati", fill='#888888', font=header_font, anchor="mt")

    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

async def send_rates(currency: str = "USD"):
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHANNEL_ID .env da yo'q!")
        return

    from telegram.request import HTTPXRequest

    request = HTTPXRequest(
        http_version="1.1",
        connection_pool_size=8,
    )
    request._client = httpx.AsyncClient(verify=False)

    bot = Bot(token=BOT_TOKEN, request=request)

    now = datetime.now()
    date_str = now.strftime("%d-%B %H:%M")
    date_str = date_str.replace("January", "yanvar").replace("February", "fevral")
    date_str = date_str.replace("March", "mart").replace("April", "aprel")
    date_str = date_str.replace("May", "may").replace("June", "iyun")
    date_str = date_str.replace("July", "iyul").replace("August", "avgust")
    date_str = date_str.replace("September", "sentabr").replace("October", "oktabr")
    date_str = date_str.replace("November", "noyabr").replace("December", "dekabr")

    try:
        image_buffer = create_rates_image(currency)

        caption = f"""💰 USD kurslari | Eng yaxshi takliflarni tanlang!

#dollar_kursi   {date_str} 💸

📊 30 ta bank kurslari — yagona jadvalda, oson solishtiring!

❗️ Ushbu ma'lumotdan har kuni xabardor bo'lish uchun ushbu kanalga qo'shiling

👉 @bank_faoliyati - Bizni kuzatib boring!"""

        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_buffer,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
        logger.success(f"{currency} kurslari rasm bilan kanalga yuborildi!")
    except Exception as e:
        logger.error(f"Rasm yaratishda xato: {e}")

def build_message_text(currency: str = "USD") -> str:
    rates = get_latest_rates()
    data = {}
    cb_rate = None
    scraped_at = None

    for r in rates:
        if r["currency"] != currency:
            continue
        data[r["bank_code"]] = {"buy": r["buy"], "sell": r["sell"]}
        if r["cb_rate"] and cb_rate is None:
            cb_rate = r["cb_rate"]
        if r["scraped_at"] and scraped_at is None:
            scraped_at = r["scraped_at"]

    now = scraped_at or datetime.now()
    date_str = now.strftime("%d.%m.%Y %H:%M")
    cb_str = fmt(cb_rate) if cb_rate else "—"

    lines = [f"<b>🏦 Banklarda {currency} kursi (so'mda)</b>", ""]
    lines.append(f"🗓 <b>{date_str}</b>    💵 MB kursi: <b>1 {currency}={cb_str}</b>")
    lines.append("")
    lines.append(f"{'Bank':<20} {'Sotib olish':>11} {'Sotish':>9}")
    lines.append("─" * 42)

    for code, display_name, emoji in BANK_ORDER:
        if code not in data:
            continue
        buy = fmt(data[code]["buy"])
        sell = fmt(data[code]["sell"])
        lines.append(f"{emoji} {display_name:<18} {buy:>11} {sell:>9}")

    lines.append("")
    lines.append("📊 @bank_faoliyati")
    return "\n".join(lines)

async def send_all_currencies():
    for currency in ["USD", "EUR", "RUB"]:
        try:
            await send_rates(currency)
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"{currency} yuborishda xato: {e}")

if __name__ == "__main__":
    import sys
    currency = sys.argv[1].upper() if len(sys.argv) > 1 else "USD"
    asyncio.run(send_rates(currency))
