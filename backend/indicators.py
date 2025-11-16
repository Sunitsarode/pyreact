# ============================================
# backend/indicators.py - UPDATED
# Complete with minimal data storage optimization
# ============================================
import pandas as pd
import pandas_ta as pta
import numpy as np

def calculate_rsi_score(close_prices):
    """
    Calculate RSI score (0-100)
    Returns: (score, rsi_value, is_extreme)
    """
    rsi = pta.rsi(close_prices, length=14)
    if rsi is None or rsi.empty:
        return 50, 50, False  # Changed from 0 to 50 for neutral
    
    latest_rsi = rsi.iloc[-1]
    score = latest_rsi  # Direct RSI value as score (0-100)
    
    # Check extreme zones
    is_extreme = latest_rsi > 70 or latest_rsi < 30
    
    return round(score, 2), round(latest_rsi, 2), is_extreme

def calculate_macd_score(close_prices):
    """
    Calculate MACD score (0-100)
    Score = 50 + (Histogram × 5)
    Capped between 0 and 100
    """
    macd = pta.macd(close_prices, fast=12, slow=26, signal=9)
    if macd is None or macd.empty:
        return 50
    
    macd_line = macd.iloc[-1, 0]
    signal_line = macd.iloc[-1, 1]
    histogram = macd_line - signal_line
    
    # Score formula
    score = 50 + (histogram * 5)
    score = max(0, min(100, score))  # Cap between 0-100
    
    return round(score, 2)

def calculate_adx_score(high, low, close):
    """
    Calculate ADX strength score (0-100)
    If +DI > -DI: Bullish → Score = ADX value
    If -DI > +DI: Bearish → Score = 100 - ADX value
    """
    df = pd.DataFrame({'high': high, 'low': low, 'close': close})
    adx = pta.adx(df['high'], df['low'], df['close'], length=14)
    
    if adx is None or adx.empty:
        return 50
    
    adx_val = adx.iloc[-1, 0]  # ADX value
    dmp = adx.iloc[-1, 1]      # +DI
    dmn = adx.iloc[-1, 2]      # -DI
    
    # Direction-based scoring
    if dmp > dmn:
        # Bullish
        score = adx_val
    else:
        # Bearish
        score = 100 - adx_val
    
    return round(score, 2)

def calculate_supertrend_score(high, low, close):
    """
    Calculate Supertrend score (0-100)
    Calculate two Supertrends: (7,3) and (11,2)
    Both Uptrend = 100
    Both Downtrend = 0
    Mixed = 50
    """
    st1 = pta.supertrend(high=high, low=low, close=close, length=7, multiplier=3)
    st2 = pta.supertrend(high=high, low=low, close=close, length=11, multiplier=2)
    
    if st1 is None or st1.empty or st2 is None or st2.empty:
        return 50
    
    # Get direction (1 = uptrend, -1 = downtrend)
    direction1 = st1.iloc[-1, 1]
    direction2 = st2.iloc[-1, 1]
    
    # Scoring logic
    if direction1 == 1 and direction2 == 1:
        score = 100  # Both uptrend
    elif direction1 == -1 and direction2 == -1:
        score = 0    # Both downtrend
    else:
        score = 50   # Mixed
    
    return round(score, 2)

def calculate_volume_analysis(volume):
    """
    Calculate average volume and check if current volume is elevated
    Returns: (avg_volume, volume_ratio, is_high_volume)
    """
    if len(volume) < 20:
        return 0, 0, False
    
    avg_volume = pd.Series(volume).tail(20).mean()
    current_volume = volume[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    is_high_volume = volume_ratio > 1.5
    
    return round(avg_volume, 2), round(volume_ratio, 2), is_high_volume

def calculate_atr(high, low, close, period=14):
    """
    Calculate Average True Range (ATR)
    Returns: current_atr, avg_atr_20day
    """
    df = pd.DataFrame({'high': high, 'low': low, 'close': close})
    atr = pta.atr(df['high'], df['low'], df['close'], length=period)
    
    if atr is None or atr.empty:
        return 0, 0
    
    current_atr = atr.iloc[-1]
    
    # Calculate 20-day average ATR for volatility filter
    if len(atr) >= 20:
        avg_atr_20 = atr.tail(20).mean()
    else:
        avg_atr_20 = current_atr
    
    return round(current_atr, 4), round(avg_atr_20, 4)

def calculate_support_resistance(high, low, close, lookback=20):
    """
    Calculate support and resistance levels using pivot points method
    Returns: (support, resistance)
    """
    try:
        high = pd.Series(high) if not isinstance(high, pd.Series) else high
        low = pd.Series(low) if not isinstance(low, pd.Series) else low
        close = pd.Series(close) if not isinstance(close, pd.Series) else close
        
        recent_high = high.tail(lookback)
        recent_low = low.tail(lookback)
        recent_close = close.tail(lookback)
        
        pivot = (recent_high.max() + recent_low.min() + recent_close.iloc[-1]) / 3
        
        resistance1 = (2 * pivot) - recent_low.min()
        resistance2 = pivot + (recent_high.max() - recent_low.min())
        
        support1 = (2 * pivot) - recent_high.max()
        support2 = pivot - (recent_high.max() - recent_low.min())
        
        current_price = recent_close.iloc[-1]
        
        if resistance1 > current_price:
            resistance = resistance1
        else:
            resistance = resistance2
        
        if support1 < current_price:
            support = support1
        else:
            support = support2
        
        return round(support, 2), round(resistance, 2)
    
    except Exception as e:
        print(f"  ⚠️  Support/Resistance calculation error: {e}")
        current = close.iloc[-1] if len(close) > 0 else 0
        return current * 0.98, current * 1.02

def calculate_swing_levels(high, low, lookback=10):
    """
    Calculate swing high and swing low for stop-loss placement
    Returns: (swing_low, swing_high)
    """
    recent_high = pd.Series(high).tail(lookback)
    recent_low = pd.Series(low).tail(lookback)
    
    swing_low = recent_low.min()
    swing_high = recent_high.max()
    
    return round(swing_low, 2), round(swing_high, 2)

def calculate_sma(data, period):
    """
    Calculate Simple Moving Average (SMA) for a given data series and period.
    Returns a list of SMA values.
    """
    if len(data) < period:
        return [None] * len(data)  # Not enough data to calculate SMA

    sma_values = pd.Series(data).rolling(window=period).mean().tolist()
    return [round(x, 2) if x is not None else None for x in sma_values]

# ============================================
# UPDATED: Minimal Data Storage
# ============================================

def calculate_all_scores(data, interval):
    """
    Calculate all indicator scores for a given interval
    Returns MINIMAL dict with only essential data
    """
    close = pd.Series(data['close'])
    high = pd.Series(data['high'])
    low = pd.Series(data['low'])
    volume = data['volume']
    
    # Calculate scores (0-100)
    rsi_score, rsi_value, rsi_extreme = calculate_rsi_score(close)
    macd_score = calculate_macd_score(close)
    adx_score = calculate_adx_score(high, low, close)
    supertrend_score = calculate_supertrend_score(high, low, close)
    
    # Calculate support/resistance
    support, resistance = calculate_support_resistance(high, low, close)
    
    # Calculate volume analysis
    avg_volume, volume_ratio, high_volume = calculate_volume_analysis(volume)
    
    # Calculate ATR
    current_atr, avg_atr_20 = calculate_atr(high, low, close)
    
    # Calculate swing levels
    swing_low, swing_high = calculate_swing_levels(high, low)
    
    # Calculate average total score
    avg_total_score = (rsi_score + macd_score + adx_score + supertrend_score) / 4
    
    # MINIMAL DATA FOR DATABASE - Only what's absolutely needed
    scores = {
        'interval': interval,
        'rsi_score': round(rsi_score, 2),
        'macd_score': round(macd_score, 2),
        'adx_score': round(adx_score, 2),
        'supertrend_score': round(supertrend_score, 2),
        'avg_total_score': round(avg_total_score, 2),
        'support': round(support, 2),
        'resistance': round(resistance, 2),
        # Additional fields kept for calculations (not stored in DB minimal version)
        'rsi_extreme': int(rsi_extreme),
        'high_volume': int(high_volume),
        'volume_ratio': round(volume_ratio, 2),
        'atr': round(current_atr, 4),
        'avg_atr_20': round(avg_atr_20, 4),
        'swing_low': round(swing_low, 2),
        'swing_high': round(swing_high, 2)
    }
    
    return scores

def calculate_master_score(weighted_scores):
    """
    Calculate Master Score using indicator weights
    MASTER_SCORE = (W_RSI × 0.25) + (W_MACD × 0.30) + (W_ADX × 0.20) + (W_Supertrend × 0.25)
    
    weighted_scores: dict with keys {rsi, macd, adx, supertrend}
    Returns: master_score (0-100) and classification
    """
    master_score = (
        weighted_scores['rsi'] * 0.25 +
        weighted_scores['macd'] * 0.30 +
        weighted_scores['adx'] * 0.20 +
        weighted_scores['supertrend'] * 0.25
    )
    
    # Classification
    if master_score > 65:
        classification = 'STRONG_BULLISH'
    elif master_score >= 55:
        classification = 'BULLISH'
    elif master_score >= 45:
        classification = 'NEUTRAL'
    elif master_score >= 35:
        classification = 'BEARISH'
    else:
        classification = 'STRONG_BEARISH'
    
    return round(master_score, 2), classification

def calculate_master_score_for_interval(interval_scores_data):
    """
    Calculate Master Score for a single interval using indicator weights.
    Assumes interval_scores_data contains 'rsi_score', 'macd_score', 'adx_score', 'supertrend_score'.
    Returns: master_score (0-100)
    """
    master_score = (
        interval_scores_data['rsi_score'] * 0.25 +
        interval_scores_data['macd_score'] * 0.30 +
        interval_scores_data['adx_score'] * 0.20 +
        interval_scores_data['supertrend_score'] * 0.25
    )
    return round(master_score, 2)

def calculate_weighted_indicators(interval_scores, timeframe_weights):
    """
    Calculate weighted indicator scores across timeframes
    Returns: dict with weighted {rsi, macd, adx, supertrend}
    """
    weighted = {
        'rsi': 0,
        'macd': 0,
        'adx': 0,
        'supertrend': 0
    }
    
    total_weight = 0
    
    for interval, scores in interval_scores.items():
        weight = timeframe_weights.get(interval, 0)
        weighted['rsi'] += scores['rsi_score'] * weight
        weighted['macd'] += scores['macd_score'] * weight
        weighted['adx'] += scores['adx_score'] * weight
        weighted['supertrend'] += scores['supertrend_score'] * weight
        total_weight += weight
    
    # Normalize
    if total_weight > 0:
        for key in weighted:
            weighted[key] = round(weighted[key] / total_weight, 2)
    
    return weighted
