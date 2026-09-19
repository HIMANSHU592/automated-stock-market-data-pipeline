import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="config/.env")

def load_to_mysql(df: pd.DataFrame):
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO stock_prices (date, ticker, open_price, high_price, low_price, close_price, volume, daily_change_pct, ma_7)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            volume = VALUES(volume),
            daily_change_pct = VALUES(daily_change_pct),
            ma_7 = VALUES(ma_7)
    """

    for _, row in df.iterrows():
        cursor.execute(insert_query, (
            row["Date"], row["Ticker"], row["Open"], row["High"],
            row["Low"], row["Close"], row["Volume"],
            row["Daily_Change_Pct"], row["MA_7"]
        ))

    conn.commit()
    print(f"{cursor.rowcount} rows affected in last operation.")
    cursor.close()
    conn.close()
    print(f"Total {len(df)} rows processed and loaded into MySQL successfully!")

if __name__ == "__main__":
    df = pd.read_csv("data/processed/stock_data_clean.csv")
    load_to_mysql(df)
    