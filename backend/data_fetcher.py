# ============================================
# backend/data_fetcher.py
# Yahoo Finance Data Fetcher
# ============================================
import yfinance as yf
import pandas as pd
from datetime import datetime

def get_period_for_interval(interval, candles_needed):
    """Calculate appropriate period for yfinance"""
    period_map = {
        "1m": f"{max(7, candles_needed // 390 + 2)}d",
        "5m": f"{max(7, candles_needed // 78 + 2)}d",
        "15m": f"{max(7, candles_needed // 26 + 2)}d",
        "1h": f"{max(30, candles_needed // 6 + 2)}d",
        "1d": f"{max(200, candles_needed)}d"
    }
    return period_map.get(interval, "60d")

def fetch_market_data(symbol, interval, candles_needed):
    """
    Fetch market data from Yahoo Finance
    Returns: dict with keys [open, high, low, close, volume] as lists
    """
    try:
        period = get_period_for_interval(interval, candles_needed)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"  ⚠️  No data for {symbol} {interval}")
            return None
        
        # Take only needed candles
        df = df.tail(candles_needed)
        
        # Convert to simple dict format
        data = {
            'open': df['Open'].tolist(),
            'high': df['High'].tolist(),
            'low': df['Low'].tolist(),
            'close': df['Close'].tolist(),
            'volume': df['Volume'].tolist()
        }
        
        return data
    
    except Exception as e:
        print(f"  ❌ Error fetching {symbol} {interval}: {e}")
        return None

def fetch_market_data_with_timestamps(symbol, interval, candles_needed):
    """
    Fetch market data with timestamps for database storage
    Returns: list of dicts with keys [timestamp, open, high, low, close, volume]
    """
    try:
        period = get_period_for_interval(interval, candles_needed)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"  ⚠️  No data for {symbol} {interval}")
            return None
        
        # Take only needed candles
        df = df.tail(candles_needed)
        
        # Convert to list of dicts with timestamps
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                'timestamp': int(idx.timestamp()),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })
        
        return candles
    
    except Exception as e:
        print(f"  ❌ Error fetching {symbol} {interval}: {e}")
        return None
