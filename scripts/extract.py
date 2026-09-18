import yfinance as yf
import pandas as pd

def extract_stock_data(ticker: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """
    NSE stock ka historical data fetch karta hai.
    ticker format: 'RELIANCE.NS', 'TCS.NS', 'INFY.NS'
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    df.reset_index(inplace=True)
    df["Ticker"] = ticker
    return df

if __name__ == "__main__":
    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    all_data = []

    for t in tickers:
        print(f"Fetching data for {t}...")
        data = extract_stock_data(t)
        all_data.append(data)

    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv("data/raw/stock_data_raw.csv", index=False)
    print("Extraction complete! Saved to data/raw/stock_data_raw.csv")