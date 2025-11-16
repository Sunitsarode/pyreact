# ============================================
# backend/data_processor.py - FIXED VERSION
# No problematic imports, uses direct calls
# ============================================
import time
import pandas as pd
from datetime import datetime
from data_fetcher import fetch_market_data, fetch_market_data_with_timestamps, fetch_current_price
from db_manager import save_candles, save_indicator_scores, get_latest_scores, get_latest_score

# Import the entire module instead of specific functions
import indicators

class DataProcessor:
    """Process market data and calculate scores"""
    
    def __init__(self, settings, socketio):
        self.settings = settings
        self.socketio = socketio
    
    def calculate_all_scores(self, data, interval):
        """
        Calculate all indicator scores for a given interval
        Returns dict with minimal essential data only
        """
        close = pd.Series(data['close'])
        high = pd.Series(data['high'])
        low = pd.Series(data['low'])
        volume = data['volume']
        
        # Calculate scores using indicators module
        rsi_score, rsi_value, rsi_extreme = indicators.calculate_rsi_score(close)
        macd_score = indicators.calculate_macd_score(close)
        adx_score = indicators.calculate_adx_score(high, low, close)
        supertrend_score = indicators.calculate_supertrend_score(high, low, close)
        
        # Calculate support/resistance
        support, resistance = indicators.calculate_support_resistance(high, low, close)
        
        # Calculate volume analysis
        avg_volume, volume_ratio, high_volume = indicators.calculate_volume_analysis(volume)
        
        # Calculate ATR
        current_atr, avg_atr_20 = indicators.calculate_atr(high, low, close)
        
        # Calculate swing levels
        swing_low, swing_high = indicators.calculate_swing_levels(high, low)
        
        # Calculate average total score
        avg_total_score = (rsi_score + macd_score + adx_score + supertrend_score) / 4
        
        # MINIMAL DATA - Only what's needed
        scores = {
            'interval': interval,
            'rsi_score': round(rsi_score, 2),
            'macd_score': round(macd_score, 2),
            'adx_score': round(adx_score, 2),
            'supertrend_score': round(supertrend_score, 2),
            'avg_total_score': round(avg_total_score, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            # Keep these for internal calculations
            'rsi_extreme': int(rsi_extreme),
            'high_volume': int(high_volume),
            'volume_ratio': round(volume_ratio, 2),
            'atr': round(current_atr, 4),
            'avg_atr_20': round(avg_atr_20, 4),
            'swing_low': round(swing_low, 2),
            'swing_high': round(swing_high, 2)
        }
        
        return scores
    
    def calculate_master_score_for_interval(self, interval_scores_data):
        """
        Calculate Master Score for a single interval
        """
        master_score = (
            interval_scores_data['rsi_score'] * 0.25 +
            interval_scores_data['macd_score'] * 0.30 +
            interval_scores_data['adx_score'] * 0.20 +
            interval_scores_data['supertrend_score'] * 0.25
        )
        return round(master_score, 2)
    
    def calculate_master_score(self, weighted_indicators):
        """
        Calculate Master Score using indicator weights
        Returns: master_score (0-100) and classification
        """
        master_score = (
            weighted_indicators['rsi'] * 0.25 +
            weighted_indicators['macd'] * 0.30 +
            weighted_indicators['adx'] * 0.20 +
            weighted_indicators['supertrend'] * 0.25
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
    
    def calculate_weighted_indicators(self, interval_scores, timeframe_weights):
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
    
    def calculate_sma(self, data, period):
        """
        Calculate Simple Moving Average
        """
        if len(data) < period:
            return [None] * len(data)
        
        sma_values = pd.Series(data).rolling(window=period).mean().tolist()
        return [round(x, 2) if x is not None else None for x in sma_values]
    
    def update_symbol_data(self, symbol, historical_limit=None):
        """Fetch data, calculate scores"""
        print(f"\n{'='*50}")
        print(f"📊 Updating {symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        current_price = fetch_current_price(symbol)
        print(f"  💰 Current price: ${current_price:.2f}")
        
        interval_scores = self.fetch_and_calculate_scores(
            symbol, historical_limit
        )
        
        if not interval_scores:
            print("  ⚠️  No interval data available")
            return None, None, None, None
        
        weighted_indicators = self.calculate_weighted_indicators(
            interval_scores, self.settings['timeframeWeights']
        )
        
        overall_master_score, classification = self.calculate_master_score(
            weighted_indicators
        )
        
        print(f"\n  🎯 Overall Master Score: {overall_master_score:.2f} ({classification})")
        
        interval_smas = self.calculate_interval_smas(symbol, historical_limit)
        
        self.save_and_emit_data(
            symbol, current_price, overall_master_score, classification,
            weighted_indicators, interval_scores, interval_smas
        )
        
        return overall_master_score, weighted_indicators, interval_scores, current_price
    
    def fetch_and_calculate_scores(self, symbol, historical_limit):
        """Fetch market data and calculate indicator scores"""
        interval_scores = {}
        
        for interval in self.settings['intervals']:
            candles_needed = self.settings['candlesPerInterval'].get(interval, 100)
            max_candles = self.settings['maxCandlesStored'].get(interval, 100)
            fetch_limit = historical_limit if historical_limit else candles_needed
            
            candles_with_ts = fetch_market_data_with_timestamps(
                symbol, interval, fetch_limit
            )
            
            if candles_with_ts:
                save_candles(symbol, interval, candles_with_ts, max_candles)
                data = fetch_market_data(symbol, interval, fetch_limit)
                
                if data:
                    scores = self.calculate_all_scores(data, interval)
                    interval_master_score = self.calculate_master_score_for_interval(scores)
                    scores['master_score'] = interval_master_score
                    interval_scores[interval] = scores
                    print(f"  ✅ {interval}: Master Score = {interval_master_score:.2f}")
        
        return interval_scores
    
    def calculate_interval_smas(self, symbol, historical_limit):
        """Calculate SMAs for each interval"""
        interval_master_score_histories = {
            interval: [] for interval in self.settings['intervals']
        }
        
        score_history_limit = historical_limit if historical_limit else 50
        all_scores_history = get_latest_scores(symbol, limit=score_history_limit)
        
        for score_entry in all_scores_history:
            for interval_key, interval_data in score_entry['intervals'].items():
                if 'master_score' in interval_data:
                    interval_master_score_histories[interval_key].append(
                        interval_data['master_score']
                    )
        
        interval_smas = {}
        for interval, history in interval_master_score_histories.items():
            sma9_list = self.calculate_sma(history, 9)
            sma21_list = self.calculate_sma(history, 21)
            
            interval_smas[interval] = {
                'master_score_sma9': sma9_list[-1] if sma9_list and len(sma9_list) > 0 else None,
                'master_score_sma21': sma21_list[-1] if sma21_list and len(sma21_list) > 0 else None
            }
        
        return interval_smas
    
    def save_and_emit_data(self, symbol, current_price, overall_master_score,
                          classification, weighted_indicators, interval_scores,
                          interval_smas):
        """Save to database and emit to frontend"""
        current_timestamp = int(time.time())
        
        scores_to_save = {
            'timestamp': current_timestamp,
            'master_score': overall_master_score,
            'classification': classification,
            'weighted_indicators': weighted_indicators,
            'intervals': interval_scores,
            'interval_smas': interval_smas
        }
        
        save_indicator_scores(symbol, scores_to_save)
        
        self.socketio.emit('score_update', {
            'symbol': symbol,
            'timestamp': current_timestamp,
            'master_score': overall_master_score,
            'classification': classification,
            'weighted_indicators': weighted_indicators,
            'current_price': current_price,
            'intervals': interval_scores,
            'interval_smas': interval_smas
        })
