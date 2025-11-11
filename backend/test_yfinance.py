import yfinance as yf

try:
    ticker = yf.Ticker("^NSEI")
    df = ticker.history(period="1d", interval="15m")
    if df.empty:
        print("No data found for ^NSEI")
    else:
        print("Successfully fetched data for ^NSEI")
        print(df.head())
except Exception as e:
    print(f"Error fetching data for ^NSEI: {e}")
