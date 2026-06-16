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
    ("tbcbank", "TBC BANK", "🇬🇪"),
    ("trustbank", "TRASTBANK", "🤲"),
    ("turonbank", "TURON BANK", "🕌"),
    ("universalbank", "UNIVERSAL", "🌍"),
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

    width = 1000
    row_height = 46
    header_height = 110
    footer_height = 50
    max_rows = max(len(left_banks), len(right_banks))
    total_height = header_height + (max_rows * row_height) + footer_height

    img = Image.new('RGB', (width, total_height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    try:
        title_font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        bank_font   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        rate_font   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        title_font = header_font = bank_font = rate_font = ImageFont.load_default()

    logo_size = 32

    left_x_logo = 30
    left_x_name = 30 + logo_size + 8
    left_x_buy  = 270
    left_x_sell = 390

    right_x_logo = 520
    right_x_name = 520 + logo_size + 8
    right_x_buy  = 760
    right_x_sell = 880

    name_max_width_left  = left_x_buy  - left_x_name - 15
    name_max_width_right = right_x_buy - right_x_name - 15

    y = 18
    draw.text((width//2, y), f"{currency} KURSLARI", fill='#000000', font=title_font, anchor="mt")
    y += 38
    draw.text((width//2, y), f"{date_str}  |  MB: {cb_str} so'm", fill='#666666', font=header_font, anchor="mt")
    y += 36

    draw.text((left_x_name, y),  "BANKLAR",     fill='#000000', font=header_font)
    draw.text((left_x_buy,  y),  "OLISH",       fill='#000000', font=header_font, anchor="ra")
    draw.text((left_x_sell, y),  "SOTISH",      fill='#000000', font=header_font, anchor="ra")

    draw.text((right_x_name, y), "BANKLAR",     fill='#000000', font=header_font)
    draw.text((right_x_buy,  y), "OLISH",       fill='#000000', font=header_font, anchor="ra")
    draw.text((right_x_sell, y), "SOTISH",      fill='#000000', font=header_font, anchor="ra")

    y += 28
    draw.line([(20, y), (width-20, y)], fill='#cccccc', width=2)
    y += 12

    def truncate(text, font, max_width):
        if draw.textlength(text, font=font) <= max_width:
            return text
        while text and draw.textlength(text + "…", font=font) > max_width:
            text = text[:-1]
        return text + "…"

    def get_logo(code):
        path = os.path.join(LOGOS_DIR, f"{code}.png")
        if os.path.exists(path):
            try:
                logo = Image.open(path).convert("RGBA")
                logo.thumbnail((logo_size, logo_size), Image.LANCZOS)
                return logo
            except Exception:
                return None
        return None

    for i in range(max_rows):
        row_y = y + i * row_height
        text_y = row_y + row_height // 2
        logo_y = row_y + (row_height - logo_size) // 2

        if i < len(left_banks):
            code, name, emoji = left_banks[i]
            buy  = fmt(data[code]["buy"])
            sell = fmt(data[code]["sell"])

            logo = get_logo(code)
            if logo:
                img.paste(logo, (left_x_logo, logo_y), logo)
                label = truncate(name, bank_font, name_max_width_left)
            else:
                label = truncate(f"{emoji} {name}", bank_font, name_max_width_left + logo_size + 8)

            draw.text((left_x_name, text_y), label, fill='#000000', font=bank_font, anchor="lm")
            draw.text((left_x_buy,  text_y), buy,  fill='#000000', font=rate_font, anchor="rm")
            draw.text((left_x_sell, text_y), sell, fill='#000000', font=rate_font, anchor="rm")

        if i < len(right_banks):
            code, name, emoji = right_banks[i]
            buy  = fmt(data[code]["buy"])
            sell = fmt(data[code]["sell"])

            logo = get_logo(code)
            if logo:
                img.paste(logo, (right_x_logo, logo_y), logo)
                label = truncate(name, bank_font, name_max_width_right)
            else:
                label = truncate(f"{emoji} {name}", bank_font, name_max_width_right + logo_size + 8)

            draw.text((right_x_name, text_y), label, fill='#000000', font=bank_font, anchor="lm")
            draw.text((right_x_buy,  text_y), buy,  fill='#000000', font=rate_font, anchor="rm")
            draw.text((right_x_sell, text_y), sell, fill='#000000', font=rate_font, anchor="rm")

        if i < max_rows - 1:
            draw.line([(20, row_y + row_height - 2), (width-20, row_y + row_height - 2)], fill='#f0f0f0', width=1)

    draw.text((width//2, total_height-28), "@bank_faoliyati", fill='#888888', font=header_font, anchor="mt")

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

        caption = f"""💰 {currency} kurslari | Eng yaxshi takliflarni tanlang!

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
