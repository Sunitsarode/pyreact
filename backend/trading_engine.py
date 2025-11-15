# ============================================
# backend/trading_engine.py
# Trading Logic Engine with Entry/Exit Rules
# ============================================
import time
from datetime import datetime, timedelta

class TradingEngine:
    def __init__(self, settings):
        self.settings = settings
        self.last_trade_time = {}  # Track last trade time per symbol
        
    def check_market_filters(self, weighted_adx, current_atr, avg_atr_20):
        """
        Check if market conditions allow trading
        Returns: (can_trade, reason)
        """
        # Check ADX threshold (too choppy)
        if weighted_adx < 20:
            return False, "ADX too low (choppy market)"
        
        # Check extreme volatility
        if current_atr > 2 * avg_atr_20:
            return False, "Extreme volatility detected"
        
        return True, "Market conditions OK"
    
    def check_cooldown(self, symbol):
        """
        Check if cooldown period (10 minutes) has passed since last trade
        """
        if symbol not in self.last_trade_time:
            return True
        
        last_time = self.last_trade_time[symbol]
        current_time = time.time()
        
        if current_time - last_time < 600:  # 10 minutes = 600 seconds
            return False
        
        return True
    
    def detect_reversal_setup(self, master_score, weighted_rsi, rsi_extreme, 
                             current_price, support, resistance, weighted_adx):
        """
        Detect reversal setup conditions
        Returns: (is_reversal, direction) - direction: 'BULLISH' or 'BEARISH' or None
        """
        if not rsi_extreme:
            return False, None
        
        # Check if price is within 1% of S/R
        sr_distance_support = abs(current_price - support) / current_price
        sr_distance_resistance = abs(current_price - resistance) / current_price
        near_sr = sr_distance_support < 0.01 or sr_distance_resistance < 0.01
        
        if not near_sr:
            return False, None
        
        # Check ADX strength
        if weighted_adx < 25:
            return False, None
        
        # Bearish Reversal: RSI > 70 but Master Score < 45
        if weighted_rsi > 70 and master_score < 45:
            return True, 'BEARISH'
        
        # Bullish Reversal: RSI < 30 but Master Score > 55
        if weighted_rsi < 30 and master_score > 55:
            return True, 'BULLISH'
        
        return False, None
    
    def detect_breakout_setup(self, master_score, weighted_rsi, current_price,
                              support, resistance, weighted_adx, adx_history):
        """
        Detect breakout setup conditions
        Returns: (is_breakout, direction)
        """
        # RSI must NOT be in extreme zone
        if weighted_rsi > 70 or weighted_rsi < 30:
            return False, None
        
        # Check ADX rising
        if len(adx_history) < 4:
            return False, None
        
        current_adx = adx_history[-1]
        avg_prev_3 = sum(adx_history[-4:-1]) / 3
        adx_rising = current_adx > avg_prev_3
        
        if not adx_rising:
            return False, None
        
        # Check if price consolidating near S/R (within 1%)
        near_resistance = abs(current_price - resistance) / current_price < 0.01
        near_support = abs(current_price - support) / current_price < 0.01
        
        # Bullish Breakout Setup
        if master_score > 55 and near_resistance:
            return True, 'BULLISH'
        
        # Bearish Breakout Setup
        if master_score < 45 and near_support:
            return True, 'BEARISH'
        
        return False, None
    
    def check_long_entry_breakout(self, master_score, supertrend_scores, 
                                   current_price, resistance, high_volume):
        """
        Check LONG Entry - Breakout Scenario
        Returns: (should_enter, reason)
        """
        # Master Score > 60
        if master_score <= 60:
            return False, "Master Score not > 60"
        
        # All timeframes Supertrend = Uptrend (100)
        all_uptrend = all(score == 100 for score in supertrend_scores.values())
        if not all_uptrend:
            return False, "Not all timeframes in uptrend"
        
        # Price breaks above resistance + 0.2%
        breakout_level = resistance * 1.002
        if current_price <= breakout_level:
            return False, "Price not above resistance + 0.2%"
        
        # Volume > 1.5x average
        if not high_volume:
            return False, "Volume not elevated"
        
        return True, "Bullish Breakout Confirmed"
    
    def check_long_entry_reversal(self, reversal_setup, master_score, 
                                   weighted_macd, current_price, support):
        """
        Check LONG Entry - Reversal Scenario
        Returns: (should_enter, reason)
        """
        if not reversal_setup or reversal_setup != 'BULLISH':
            return False, "No bullish reversal setup"
        
        # Master Score crosses above 55
        if master_score <= 55:
            return False, "Master Score not > 55"
        
        # MACD crosses positive (> 50 in our 0-100 scale)
        if weighted_macd <= 50:
            return False, "MACD not positive"
        
        # Price bounces from support (within 1%)
        bounce_range = abs(current_price - support) / support
        if bounce_range > 0.01:
            return False, "Price not near support"
        
        return True, "Bullish Reversal Confirmed"
    
    def check_short_entry_breakout(self, master_score, supertrend_scores,
                                    current_price, support, high_volume):
        """
        Check SHORT Entry - Breakout Scenario
        """
        # Master Score < 40
        if master_score >= 40:
            return False, "Master Score not < 40"
        
        # All timeframes Supertrend = Downtrend (0)
        all_downtrend = all(score == 0 for score in supertrend_scores.values())
        if not all_downtrend:
            return False, "Not all timeframes in downtrend"
        
        # Price breaks below support - 0.2%
        breakout_level = support * 0.998
        if current_price >= breakout_level:
            return False, "Price not below support - 0.2%"
        
        # Volume > 1.5x average
        if not high_volume:
            return False, "Volume not elevated"
        
        return True, "Bearish Breakout Confirmed"
    
    def check_short_entry_reversal(self, reversal_setup, master_score,
                                    weighted_macd, current_price, resistance):
        """
        Check SHORT Entry - Reversal Scenario
        """
        if not reversal_setup or reversal_setup != 'BEARISH':
            return False, "No bearish reversal setup"
        
        # Master Score crosses below 45
        if master_score >= 45:
            return False, "Master Score not < 45"
        
        # MACD crosses negative (< 50 in our 0-100 scale)
        if weighted_macd >= 50:
            return False, "MACD not negative"
        
        # Price rejected from resistance (within 1%)
        rejection_range = abs(current_price - resistance) / resistance
        if rejection_range > 0.01:
            return False, "Price not near resistance"
        
        return True, "Bearish Reversal Confirmed"
    
    def calculate_stop_loss(self, direction, entry_price, swing_low, swing_high, 
                           atr, supertrend_1h):
        """
        Calculate stop loss using 3 methods, return nearest (tightest)
        direction: 'LONG' or 'SHORT'
        Returns: stop_loss_price
        """
        stop_losses = []
        
        if direction == 'LONG':
            # Swing-based: Recent swing low - 0.1%
            swing_sl = swing_low * 0.999
            stop_losses.append(swing_sl)
            
            # ATR-based: Entry - (2 × ATR)
            atr_sl = entry_price - (2 * atr)
            stop_losses.append(atr_sl)
            
            # Supertrend-based: Use 1hr Supertrend value
            if supertrend_1h > 0:
                stop_losses.append(supertrend_1h)
            
            # Return highest (nearest to entry)
            return max(stop_losses)
        
        else:  # SHORT
            # Swing-based: Recent swing high + 0.1%
            swing_sl = swing_high * 1.001
            stop_losses.append(swing_sl)
            
            # ATR-based: Entry + (2 × ATR)
            atr_sl = entry_price + (2 * atr)
            stop_losses.append(atr_sl)
            
            # Supertrend-based
            if supertrend_1h > 0:
                stop_losses.append(supertrend_1h)
            
            # Return lowest (nearest to entry)
            return min(stop_losses)
    
    def calculate_target_price(self, direction, entry_price, stop_loss):
        """
        Calculate target price using 1:2 Risk:Reward ratio
        """
        risk = abs(entry_price - stop_loss)
        
        if direction == 'LONG':
            target = entry_price + (2 * risk)
        else:
            target = entry_price - (2 * risk)
        
        return round(target, 2)
    
    def calculate_position_size(self, account_balance, entry_price, stop_loss, risk_percent=1.5):
        """
        Calculate position size based on risk management
        Position Size = (Account × Risk%) / (Entry - Stop Loss)
        """
        risk_amount = account_balance * (risk_percent / 100)
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        return round(position_size, 4)
    
    def check_exit_conditions(self, position, current_price, master_score, 
                             weighted_supertrend, entry_time):
        """
        Check if any exit condition is met
        Returns: (should_exit, reason)
        """
        direction = position['direction']
        entry_price = position['entry_price']
        stop_loss = position['stop_loss']
        target = position['target']
        
        # 1. Target Hit
        if direction == 'LONG' and current_price >= target:
            return True, "Target Hit"
        if direction == 'SHORT' and current_price <= target:
            return True, "Target Hit"
        
        # 2. Stop Loss Hit
        if direction == 'LONG' and current_price <= stop_loss:
            return True, "Stop Loss Hit"
        if direction == 'SHORT' and current_price >= stop_loss:
            return True, "Stop Loss Hit"
        
        # 3. Master Score Reversal
        if direction == 'LONG' and master_score < 45:
            return True, "Master Score Reversal"
        if direction == 'SHORT' and master_score > 55:
            return True, "Master Score Reversal"
        
        # 4. Supertrend Flip
        if direction == 'LONG' and weighted_supertrend < 40:
            return True, "Supertrend Flip"
        if direction == 'SHORT' and weighted_supertrend > 60:
            return True, "Supertrend Flip"
        
        # 5. Time-Based Exit (4 hours)
        current_time = time.time()
        time_elapsed = current_time - entry_time
        if time_elapsed > 14400:  # 4 hours = 14400 seconds
            pnl = self.calculate_pnl(position, current_price)
            if pnl <= 0:
                return True, "Time Exit (No Profit)"
        
        return False, None
    
    def calculate_pnl(self, position, current_price):
        """
        Calculate P&L for a position
        """
        direction = position['direction']
        entry_price = position['entry_price']
        position_size = position['position_size']
        
        if direction == 'LONG':
            pnl = (current_price - entry_price) * position_size
        else:
            pnl = (entry_price - current_price) * position_size
        
        return round(pnl, 2)
    
    def update_trailing_stop(self, position, current_price):
        """
        Update trailing stop if profit thresholds are reached
        Returns: new_stop_loss or None
        """
        direction = position['direction']
        entry_price = position['entry_price']
        stop_loss = position['stop_loss']
        target = position['target']
        
        risk = abs(entry_price - stop_loss)
        
        if direction == 'LONG':
            current_profit = current_price - entry_price
            
            # 1:1 R:R reached - Move SL to breakeven
            if current_profit >= risk and stop_loss < entry_price:
                return entry_price
            
            # 1.5:1 R:R reached - Trail at 50% of profit
            if current_profit >= 1.5 * risk:
                new_sl = entry_price + (current_profit * 0.5)
                if new_sl > stop_loss:
                    return new_sl
        
        else:  # SHORT
            current_profit = entry_price - current_price
            
            # 1:1 R:R reached
            if current_profit >= risk and stop_loss > entry_price:
                return entry_price
            
            # 1.5:1 R:R reached
            if current_profit >= 1.5 * risk:
                new_sl = entry_price - (current_profit * 0.5)
                if new_sl < stop_loss:
                    return new_sl
        
        return None
