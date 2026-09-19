import pandas as pd

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    # Column names clean karo
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    # Missing values handle karo
    df.dropna(inplace=True)

    # Date format fix karo
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    # Daily % change calculate karo
    df["Daily_Change_Pct"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100

    # 7-day moving average (per ticker)
    df["MA_7"] = df.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )

    # Duplicate rows hatao (same date + ticker)
    df.drop_duplicates(subset=["Date", "Ticker"], inplace=True)

    return df

if __name__ == "__main__":
    raw_df = pd.read_csv("data/raw/stock_data_raw.csv")
    clean_df = transform_data(raw_df)
    clean_df.to_csv("data/processed/stock_data_clean.csv", index=False)
    print(f"Transformation complete! {len(clean_df)} rows saved to data/processed/stock_data_clean.csv")