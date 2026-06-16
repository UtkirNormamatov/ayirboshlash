#!/bin/bash
# =============================================
# Ayirboshlash.uz scraper - O'rnatish skripti
# Ubuntu 22.04 / 24.04 uchun
# Ishga tushurish: bash setup.sh
# =============================================

set -e
echo "======================================"
echo " Ayirboshlash.uz - O'rnatish"
echo "======================================"

# 1. Python va pip
echo ""
echo "[1/6] Python paketlari o'rnatilmoqda..."
pip install -r requirements.txt --break-system-packages

# 2. Playwright brauzer
echo ""
echo "[2/6] Playwright Chromium o'rnatilmoqda..."
playwright install chromium
playwright install-deps chromium

# 3. PostgreSQL tekshirish
echo ""
echo "[3/6] PostgreSQL tekshirilmoqda..."
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL topilmadi. O'rnatilmoqda..."
    sudo apt-get update -q
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
else
    echo "PostgreSQL allaqachon o'rnatilgan."
fi

# 4. .env fayli
echo ""
echo "[4/6] .env fayli tekshirilmoqda..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "DIQQAT: .env fayli yaratildi."
    echo "        DB_USER va DB_PASS ni o'zgartiring!"
    echo "        Keyin: nano .env"
else
    echo ".env allaqachon mavjud."
fi

# 5. Baza va jadvallarni yaratish
echo ""
echo "[5/6] Ma'lumotlar bazasi tayyorlanmoqda..."
source .env
sudo -u postgres psql -c "
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
      CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
    END IF;
  END
  \$\$;
" 2>/dev/null || true

sudo -u postgres psql -c "
  CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
" 2>/dev/null || echo "Baza allaqachon mavjud."

sudo -u postgres psql -d "${DB_NAME}" \
  -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null || true

PGPASSWORD="${DB_PASS}" psql \
  -h "${DB_HOST}" -p "${DB_PORT}" \
  -U "${DB_USER}" -d "${DB_NAME}" \
  -f db/schema.sql

echo "Jadvallar yaratildi."

# 6. Logs papkasi
echo ""
echo "[6/6] Logs papkasi yaratilmoqda..."
mkdir -p logs

echo ""
echo "======================================"
echo " O'rnatish TUGADI!"
echo "======================================"
echo ""
echo " Ishga tushurish:"
echo "   python main.py"
echo ""
echo " Test (bitta scrape):"
echo "   python scrapers/kapitalbank.py"
echo ""
