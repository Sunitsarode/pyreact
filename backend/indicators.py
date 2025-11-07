# ============================================
# backend/indicators.py
# Enhanced with Support/Resistance Calculation
# ============================================
import pandas as pd
import pandas_ta as pta
import numpy as np

def calculate_rsi_score(close_prices):
    """Calculate RSI score (-100 to +100)"""
    rsi = pta.rsi(close_prices, length=14)
    if rsi is None or rsi.empty:
        return 0, None
    
    latest_rsi = rsi.iloc[-1]
    score = (latest_rsi - 50) * 2
    return round(score, 2), round(latest_rsi, 2)

def calculate_macd_score(close_prices):
    """Calculate MACD score (-100 to +100)"""
    macd = pta.macd(close_prices)
    if macd is None or macd.empty:
        return 0
    
    macd_line = macd.iloc[-1, 0]
    signal_line = macd.iloc[-1, 1]
    diff = macd_line - signal_line
    
    return round(max(-100, min(100, diff * 10)), 2)

def calculate_adx_score(high, low, close):
    """Calculate ADX trend strength score"""
    df = pd.DataFrame({'high': high, 'low': low, 'close': close})
    adx = pta.adx(df['high'], df['low'], df['close'], length=14)
    
    if adx is None or adx.empty:
        return 0
    
    adx_val = adx.iloc[-1, 0]
    dmp = adx.iloc[-1, 1]
    dmn = adx.iloc[-1, 2]
    
    if adx_val < 25:
        return 0
    
    strength = min(100, (adx_val - 25) * 4)
    return round(strength if dmp > dmn else -strength, 2)

def calculate_bb_score(close_prices, current_price):
    """Calculate Bollinger Bands position score"""
    bb = pta.bbands(close_prices, length=20, std=2)
    if bb is None or bb.empty:
        return 0
    
    upper = bb.iloc[-1, 0]
    middle = bb.iloc[-1, 1]
    lower = bb.iloc[-1, 2]
    
    bb_range = upper - lower
    if bb_range == 0:
        return 0
    
    position = current_price - middle
    score = (position / bb_range) * 200
    return round(max(-100, min(100, score)), 2)

def calculate_sma_score(close_prices, current_price):
    """Calculate SMA trend score"""
    sma_21 = pta.sma(close_prices, length=21)
    if sma_21 is None or sma_21.empty:
        return 0
    
    sma_val = sma_21.iloc[-1]
    if sma_val == 0:
        return 0
    
    percent_diff = ((current_price - sma_val) / sma_val) * 100
    return round(max(-100, min(100, percent_diff * 10)), 2)

def calculate_supertrend_score(high, low, close):
    """Calculate Supertrend score"""
    supertrend = pta.supertrend(high=high, low=low, close=close, length=7, multiplier=3)
    if supertrend is None or supertrend.empty:
        return 0
    
    direction = supertrend.iloc[-1, 1]  # Direction column
    return 100 if direction == 1 else -100 if direction == -1 else 0

def calculate_support_resistance(high, low, close, lookback=20):
    """
    Calculate support and resistance levels using pivot points method
    Returns: (support, resistance)
    """
    try:
        # Convert to pandas Series if not already
        high = pd.Series(high) if not isinstance(high, pd.Series) else high
        low = pd.Series(low) if not isinstance(low, pd.Series) else low
        close = pd.Series(close) if not isinstance(close, pd.Series) else close
        
        # Get recent data
        recent_high = high.tail(lookback)
        recent_low = low.tail(lookback)
        recent_close = close.tail(lookback)
        
        # Calculate pivot point (simple method)
        pivot = (recent_high.max() + recent_low.min() + recent_close.iloc[-1]) / 3
        
        # Resistance levels
        resistance1 = (2 * pivot) - recent_low.min()
        resistance2 = pivot + (recent_high.max() - recent_low.min())
        
        # Support levels
        support1 = (2 * pivot) - recent_high.max()
        support2 = pivot - (recent_high.max() - recent_low.min())
        
        # Use closest levels to current price
        current_price = recent_close.iloc[-1]
        
        # Find appropriate resistance (above current price)
        if resistance1 > current_price:
            resistance = resistance1
        else:
            resistance = resistance2
        
        # Find appropriate support (below current price)
        if support1 < current_price:
            support = support1
        else:
            support = support2
        
        return round(support, 2), round(resistance, 2)
    
    except Exception as e:
        print(f"  ⚠️  Support/Resistance calculation error: {e}")
        # Return current price as fallback
        current = close.iloc[-1] if len(close) > 0 else 0
        return current * 0.98, current * 1.02

def calculate_all_scores(data, interval):
    """
    Calculate all indicator scores for a given interval
    Returns dict with scores and support/resistance levels
    """
    close = pd.Series(data['close'])
    high = pd.Series(data['high'])
    low = pd.Series(data['low'])
    current_price = data['close'][-1]
    
    # Calculate individual scores
    rsi_score, rsi_value = calculate_rsi_score(close)
    macd_score = calculate_macd_score(close)
    adx_score = calculate_adx_score(high, low, close)
    bb_score = calculate_bb_score(close, current_price)
    sma_score = calculate_sma_score(close, current_price)
    supertrend_score = calculate_supertrend_score(high, low, close)
    
    # Calculate support and resistance
    support, resistance = calculate_support_resistance(high, low, close)
    
    scores = {
        'interval': interval,
        'rsi_score': rsi_score,
        'rsi_value': rsi_value,
        'macd_score': macd_score,
        'adx_score': adx_score,
        'bb_score': bb_score,
        'sma_score': sma_score,
        'supertrend_score': supertrend_score,
        'current_price': current_price,
        'support': support,
        'resistance': resistance
    }
    
    # Calculate average score for this interval
    score_values = [
        rsi_score, macd_score, adx_score, 
        bb_score, sma_score, supertrend_score
    ]
    
    valid_scores = [s for s in score_values if s != 0]
    interval_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    scores['total_score'] = round(interval_score, 2)
    
    return scores
