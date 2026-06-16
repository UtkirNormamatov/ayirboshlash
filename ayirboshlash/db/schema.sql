-- Banklar jadvali
CREATE TABLE IF NOT EXISTS banks (
    id        SERIAL PRIMARY KEY,
    code      VARCHAR(30) UNIQUE NOT NULL,  -- 'kapitalbank'
    name      VARCHAR(100) NOT NULL,         -- 'Kapitalbank'
    url       TEXT,
    active    BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Valyuta kurslari jadvali
CREATE TABLE IF NOT EXISTS rates (
    id         SERIAL PRIMARY KEY,
    bank_id    INT REFERENCES banks(id) ON DELETE CASCADE,
    currency   VARCHAR(10) NOT NULL,   -- 'USD', 'EUR', ...
    buy        NUMERIC(14,2),
    sell       NUMERIC(14,2),
    cb_rate    NUMERIC(14,2),          -- Markaziy bank kursi
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tezroq qidirish uchun index
CREATE INDEX IF NOT EXISTS idx_rates_bank_currency
    ON rates(bank_id, currency, scraped_at DESC);

-- Eng so'nggi kurslarni ko'rish uchun view
CREATE OR REPLACE VIEW latest_rates AS
SELECT DISTINCT ON (r.bank_id, r.currency)
    b.code        AS bank_code,
    b.name        AS bank_name,
    r.currency,
    r.buy,
    r.sell,
    r.cb_rate,
    r.scraped_at
FROM rates r
JOIN banks b ON b.id = r.bank_id
ORDER BY r.bank_id, r.currency, r.scraped_at DESC;

-- Kapitalbank ni qo'shib qo'yamiz
INSERT INTO banks (code, name, url)
VALUES ('kapitalbank', 'Kapitalbank', 'https://kapitalbank.uz/uz/services/exchange-rates/')
ON CONFLICT (code) DO NOTHING;
