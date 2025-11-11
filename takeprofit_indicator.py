# indie:lang_version = 5

"""
Multi-Indicator Score for TakeProfit Platform
6 Technical Indicators as separate lines
Range: -100 to +100 (Positive = Bullish, Negative = Bearish)
"""

import numpy as np
from typing import Dict, List


class MultiIndicatorScore:
    """
    Multi-Indicator Score Calculator
    Outputs 6 separate indicator scores ranging from -100 to +100
    """
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.adx_period = 14
        self.bb_period = 20
        self.bb_std = 2
        self.sma_period = 21
        self.supertrend_period = 7
        self.supertrend_multiplier = 3
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI indicator"""
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_rsi_score(self, prices: List[float]) -> float:
        """RSI Score: -100 to +100"""
        rsi = self.calculate_rsi(prices)
        # RSI 50 = 0, RSI 100 = +100, RSI 0 = -100
        score = (rsi - 50) * 2
        return max(-100, min(100, score))
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def calculate_macd_score(self, prices: List[float]) -> float:
        """MACD Score: -100 to +100"""
        if len(prices) < self.macd_slow:
            return 0
        
        ema_fast = self.calculate_ema(prices[-self.macd_fast:], self.macd_fast)
        ema_slow = self.calculate_ema(prices[-self.macd_slow:], self.macd_slow)
        
        macd_line = ema_fast - ema_slow
        
        # Simplified signal line (9 EMA of MACD)
        # For real implementation, you'd need historical MACD values
        signal_line = macd_line * 0.9  # Approximation
        
        diff = macd_line - signal_line
        score = diff * 10
        
        return max(-100, min(100, score))
    
    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
        """Calculate Average True Range"""
        if len(highs) < period + 1:
            return 0
        
        true_ranges = []
        for i in range(1, len(highs)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_ranges.append(max(high_low, high_close, low_close))
        
        return np.mean(true_ranges[-period:])
    
    def calculate_adx_score(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """ADX Trend Strength Score: -100 to +100"""
        if len(highs) < self.adx_period + 1:
            return 0
        
        # Simplified ADX calculation
        up_moves = np.diff(highs[-self.adx_period-1:])
        down_moves = -np.diff(lows[-self.adx_period-1:])
        
        plus_dm = np.where(up_moves > down_moves, np.maximum(up_moves, 0), 0)
        minus_dm = np.where(down_moves > up_moves, np.maximum(down_moves, 0), 0)
        
        atr = self.calculate_atr(highs, lows, closes, self.adx_period)
        
        if atr == 0:
            return 0
        
        plus_di = 100 * np.mean(plus_dm) / atr
        minus_di = 100 * np.mean(minus_dm) / atr
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
        adx = dx  # Simplified, normally ADX is smoothed DX
        
        if adx < 25:
            return 0
        
        strength = min(100, (adx - 25) * 4)
        return strength if plus_di > minus_di else -strength
    
    def calculate_bb_score(self, prices: List[float]) -> float:
        """Bollinger Bands Position Score: -100 to +100"""
        if len(prices) < self.bb_period:
            return 0
        
        recent_prices = prices[-self.bb_period:]
        middle = np.mean(recent_prices)
        std_dev = np.std(recent_prices)
        
        upper_band = middle + (self.bb_std * std_dev)
        lower_band = middle - (self.bb_std * std_dev)
        
        current_price = prices[-1]
        bb_range = upper_band - lower_band
        
        if bb_range == 0:
            return 0
        
        position = current_price - middle
        score = (position / bb_range) * 200
        
        return max(-100, min(100, score))
    
    def calculate_sma_score(self, prices: List[float]) -> float:
        """SMA Trend Score: -100 to +100"""
        if len(prices) < self.sma_period:
            return 0
        
        sma = np.mean(prices[-self.sma_period:])
        current_price = prices[-1]
        
        if sma == 0:
            return 0
        
        percent_diff = ((current_price - sma) / sma) * 100
        score = percent_diff * 10
        
        return max(-100, min(100, score))
    
    def calculate_supertrend_score(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """Supertrend Score: -100 or +100 (binary signal)"""
        if len(highs) < self.supertrend_period:
            return 0
        
        atr = self.calculate_atr(highs, lows, closes, self.supertrend_period)
        current_price = closes[-1]
        hl_avg = (highs[-1] + lows[-1]) / 2
        
        basic_upperband = hl_avg + (self.supertrend_multiplier * atr)
        basic_lowerband = hl_avg - (self.supertrend_multiplier * atr)
        
        if current_price > basic_upperband:
            return 100  # Strong Bullish
        elif current_price < basic_lowerband:
            return -100  # Strong Bearish
        else:
            # Check previous trend
            prev_hl = (highs[-2] + lows[-2]) / 2
            if current_price > prev_hl:
                return 50  # Weak Bullish
            else:
                return -50  # Weak Bearish
    
    def calculate_all_scores(self, ohlc_data: Dict) -> Dict[str, float]:
        """
        Calculate all indicator scores
        
        Args:
            ohlc_data: Dictionary with keys ['open', 'high', 'low', 'close', 'volume']
                      Each value is a list of historical data
        
        Returns:
            Dictionary with all indicator scores
        """
        closes = ohlc_data['close']
        highs = ohlc_data['high']
        lows = ohlc_data['low']
        
        scores = {
            'rsi_score': round(self.calculate_rsi_score(closes), 2),
            'macd_score': round(self.calculate_macd_score(closes), 2),
            'adx_score': round(self.calculate_adx_score(highs, lows, closes), 2),
            'bb_score': round(self.calculate_bb_score(closes), 2),
            'sma_score': round(self.calculate_sma_score(closes), 2),
            'supertrend_score': round(self.calculate_supertrend_score(highs, lows, closes), 2)
        }
        
        return scores


# ============================================
# Indicator Function for TakeProfit Platform
# ============================================

def indicator(data):
    """
    Main indicator function for TakeProfit platform
    
    Args:
        data: OHLCV data from platform
    
    Returns:
        Dictionary with 6 indicator scores + reference lines
    """
    calculator = MultiIndicatorScore()
    
    # Extract OHLCV data
    ohlc_data = {
        'open': data['open'],
        'high': data['high'],
        'low': data['low'],
        'close': data['close'],
        'volume': data['volume']
    }
    
    # Calculate all scores
    scores = calculator.calculate_all_scores(ohlc_data)
    
    # Return as plottable series
    return {
        'rsi_score': scores['rsi_score'],
        'macd_score': scores['macd_score'],
        'adx_score': scores['adx_score'],
        'bb_score': scores['bb_score'],
        'sma_score': scores['sma_score'],
        'supertrend_score': scores['supertrend_score'],
        'zero_line': 0,
        'threshold_upper': 30,
        'threshold_lower': -30
    }


# ============================================
# Configuration for TakeProfit Platform
# ============================================

CONFIG = {
    'name': 'Multi-Indicator Score',
    'description': '6 Technical Indicators as Score Lines (-100 to +100)',
    'version': '1.0.0',
    'plots': [
        {'name': 'rsi_score', 'type': 'line', 'color': '#9333EA', 'width': 2},
        {'name': 'macd_score', 'type': 'line', 'color': '#3B82F6', 'width': 2},
        {'name': 'adx_score', 'type': 'line', 'color': '#F97316', 'width': 2},
        {'name': 'bb_score', 'type': 'line', 'color': '#10B981', 'width': 2},
        {'name': 'sma_score', 'type': 'line', 'color': '#06B6D4', 'width': 2},
        {'name': 'supertrend_score', 'type': 'line', 'color': '#EF4444', 'width': 2},
        {'name': 'zero_line', 'type': 'line', 'color': '#6B7280', 'width': 1, 'style': 'dashed'},
        {'name': 'threshold_upper', 'type': 'line', 'color': '#10B981', 'width': 1, 'style': 'dotted'},
        {'name': 'threshold_lower', 'type': 'line', 'color': '#EF4444', 'width': 1, 'style': 'dotted'}
    ],
    'parameters': [
        {'name': 'rsi_period', 'type': 'int', 'default': 14, 'min': 5, 'max': 50},
        {'name': 'bb_period', 'type': 'int', 'default': 20, 'min': 10, 'max': 50},
        {'name': 'sma_period', 'type': 'int', 'default': 21, 'min': 10, 'max': 100}
    ]
}


# ============================================
# Usage Example (Testing)
# ============================================

if __name__ == "__main__":
    """
    Example usage for testing
    """
    # Sample data
    sample_data = {
        'open': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 10,
        'high': [103, 104, 103, 105, 107, 106, 108, 110, 109, 111] * 10,
        'low': [99, 101, 100, 102, 104, 103, 105, 107, 106, 108] * 10,
        'close': [102, 101, 103, 105, 104, 106, 108, 107, 109, 110] * 10,
        'volume': [1000] * 100
    }
    
    # Calculate scores
    calculator = MultiIndicatorScore()
    scores = calculator.calculate_all_scores(sample_data)
    
    print("\nIndicator Scores:")
    print("="*50)
    for indicator, score in scores.items():
        signal = "🟢 BULLISH" if score > 30 else "🔴 BEARISH" if score < -30 else "⚪ NEUTRAL"
        print(f"{indicator:20s}: {score:6.1f}  {signal}")
    print("="*50)
