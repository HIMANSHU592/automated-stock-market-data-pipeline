CREATE DATABASE IF NOT EXISTS stock_market_db;
USE stock_market_db;

CREATE TABLE IF NOT EXISTS stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    daily_change_pct DECIMAL(6,3),
    ma_7 DECIMAL(10,2),
    UNIQUE KEY unique_date_ticker (date, ticker)
);