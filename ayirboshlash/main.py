import os
import sys
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

from scrapers.kapitalbank import scrape as scrape_kapitalbank
from scrapers.agrobank import scrape as scrape_agrobank
from scrapers.aloqabank import scrape as scrape_aloqabank
from scrapers.xalqbank import scrape as scrape_xalqbank
from scrapers.hamkorbank import scrape as scrape_hamkorbank
from scrapers.anorbank import scrape as scrape_anorbank
from scrapers.apexbank import scrape as scrape_apexbank
from scrapers.asakabank import scrape as scrape_asakabank
from scrapers.aab import scrape as scrape_aab
from scrapers.brb import scrape as scrape_brb
from scrapers.davrbank import scrape as scrape_davrbank
from scrapers.garantbank import scrape as scrape_garantbank
from scrapers.hayotbank import scrape as scrape_hayotbank
from scrapers.infinbank import scrape as scrape_infinbank
from scrapers.ipakyulibank import scrape as scrape_ipakyulibank
from scrapers.ipotekabank import scrape as scrape_ipotekabank
from scrapers.kdb import scrape as scrape_kdb
from scrapers.nbu import scrape as scrape_nbu
from scrapers.mkbank import scrape as scrape_mkbank
from scrapers.octobank import scrape as scrape_octobank
from scrapers.ofb import scrape as scrape_ofb
from scrapers.poytaxtbank import scrape as scrape_poytaxtbank
from scrapers.saderatbank import scrape as scrape_saderatbank
from scrapers.sqb import scrape as scrape_sqb
from scrapers.tengebank import scrape as scrape_tengebank
from scrapers.trustbank import scrape as scrape_trustbank
from scrapers.turonbank import scrape as scrape_turonbank
from scrapers.universalbank import scrape as scrape_universalbank
from scrapers.ziraatbank import scrape as scrape_ziraatbank
from scrapers.tbcbank import scrape as scrape_tbcbank
from db.database import save_rates

logger.remove()
logger.add(sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="DEBUG")
logger.add("logs/scraper.log", rotation="10 MB", retention="7 days", level="INFO")

INTERVAL = int(os.getenv("SCRAPE_INTERVAL", 30))

def run_all():
    logger.info("=" * 50)
    logger.info("Scraping boshlandi...")

    for name, func in [
        ("kapitalbank", scrape_kapitalbank),
        ("agrobank",    scrape_agrobank),
        ("aloqabank",   scrape_aloqabank),
        ("xalqbank",    scrape_xalqbank),
        ("hamkorbank",  scrape_hamkorbank),
        ("anorbank",    scrape_anorbank),
        ("apexbank",    scrape_apexbank),
        ("asakabank",   scrape_asakabank),
	("aab", scrape_aab),
	("brb", scrape_brb),
	("davrbank", scrape_davrbank),
	("garantbank", scrape_garantbank),
	("hayotbank", scrape_hayotbank),
	("infinbank", scrape_infinbank),
	("ipakyulibank", scrape_ipakyulibank),
	("ipotekabank", scrape_ipotekabank),
	("kdb", scrape_kdb),
	("nbu", scrape_nbu),
	("mkbank", scrape_mkbank),
	("octobank", scrape_octobank),
	("ofb", scrape_ofb),
	("poytaxtbank", scrape_poytaxtbank),
	("saderatbank", scrape_saderatbank),
	("sqb", scrape_sqb),
	("tengebank", scrape_tengebank),
	("trustbank", scrape_trustbank),
	("turonbank", scrape_turonbank),
	("universalbank", scrape_universalbank),
	("ziraatbank", scrape_ziraatbank),
	("tbcbank", scrape_tbcbank),
    ]:
        try:
            rates = func()
            save_rates(name, rates)
        except Exception as e:
            logger.error(f"{name} xatosi: {e}")

    logger.info("Scraping tugadi")
    logger.info("=" * 50)

if __name__ == "__main__":
    logger.info(f"Scheduler ishga tushdi. Interval: {INTERVAL} daqiqa")
    run_all()
    scheduler = BlockingScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(run_all, "interval", minutes=INTERVAL)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler to'xtatildi")
