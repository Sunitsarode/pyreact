from datetime import datetime
import time

class SignalProcessor:
    """Process trading signals and notifications"""
    
    def __init__(self, settings, trading_engine, position_manager, 
                 notification_handler):
        self.settings = settings
        self.trading_engine = trading_engine
        self.position_manager = position_manager
        self.notification_handler = notification_handler
        self.adx_history = {}
    
    def process_trading_signals(self, symbol, master_score, weighted_indicators, 
                               interval_scores, current_price):
        """Process trading signals and manage positions"""
        
        # Check risk limits
        if not self.check_risk_limits(symbol):
            return
        
        # Extract data
        weighted_rsi = weighted_indicators['rsi']
        weighted_macd = weighted_indicators['macd']
        weighted_adx = weighted_indicators['adx']
        weighted_supertrend = weighted_indicators['supertrend']
        
        # Get 1h interval data
        interval_1h = interval_scores.get('1h', {})
        support = interval_1h.get('support', current_price * 0.98)
        resistance = interval_1h.get('resistance', current_price * 1.02)
        rsi_extreme = weighted_rsi > 70 or weighted_rsi < 30
        high_volume = interval_1h.get('high_volume', False)
        atr = interval_1h.get('atr', 0)
        avg_atr_20 = interval_1h.get('avg_atr_20', 0)
        swing_low = interval_1h.get('swing_low', current_price * 0.95)
        swing_high = interval_1h.get('swing_high', current_price * 1.05)
        
        # Check market filters
        can_trade, filter_reason = self.trading_engine.check_market_filters(
            weighted_adx, atr, avg_atr_20
        )
        
        if not can_trade:
            print(f"  🚫 Market filter: {filter_reason}")
            return
        
        # Manage existing positions
        self.manage_existing_positions(symbol, current_price, master_score, 
                                       weighted_supertrend)
        
        # Check for new entries
        if self.position_manager.get_open_positions(symbol):
            return
        
        if not self.trading_engine.check_cooldown(symbol):
            print(f"  ⏱️  Cooldown active for {symbol}")
            return
        
        # Detect and process signals
        self.detect_and_process_signals(
            symbol, master_score, weighted_rsi, weighted_macd, weighted_adx,
            weighted_supertrend, current_price, support, resistance,
            rsi_extreme, high_volume, interval_scores, swing_low, 
            swing_high, atr, interval_1h
        )
    
    def manage_existing_positions(self, symbol, current_price, master_score, 
                                  weighted_supertrend):
        """Manage existing open positions"""
        open_positions = self.position_manager.get_open_positions(symbol)
        
        for position in open_positions:
            should_exit, exit_reason = self.trading_engine.check_exit_conditions(
                position, current_price, master_score, weighted_supertrend,
                position['entry_time']
            )
            
            if should_exit:
                self.close_position(symbol, position, current_price, exit_reason)
            else:
                self.update_trailing_stop(symbol, position, current_price)
    
    def close_position(self, symbol, position, current_price, exit_reason):
        """Close a position and send notification"""
        trade = self.position_manager.close_position(
            position['id'], current_price, exit_reason
        )
        
        if trade:
            self.notification_handler.send_exit_notification(
                symbol, trade, exit_reason
            )
    
    def update_trailing_stop(self, symbol, position, current_price):
        """Update trailing stop if applicable"""
        new_sl = self.trading_engine.update_trailing_stop(position, current_price)
        if new_sl:
            old_sl = position['stop_loss']
            self.position_manager.update_stop_loss(position['id'], new_sl)
            self.notification_handler.send_trailing_stop_notification(
                symbol, position['direction'], old_sl, new_sl, current_price
            )
    
    def detect_and_process_signals(self, symbol, master_score, weighted_rsi, 
                                   weighted_macd, weighted_adx, weighted_supertrend,
                                   current_price, support, resistance, rsi_extreme,
                                   high_volume, interval_scores, swing_low, 
                                   swing_high, atr, interval_1h):
        """Detect reversal/breakout and process entry signals"""
        
        # Detect reversal
        is_reversal, reversal_direction = self.trading_engine.detect_reversal_setup(
            master_score, weighted_rsi, rsi_extreme, current_price,
            support, resistance, weighted_adx
        )
        
        if is_reversal:
            self.notification_handler.send_setup_alert(
                symbol, reversal_direction, 'Reversal', master_score
            )
        
        # Detect breakout
        is_breakout, breakout_direction = self.trading_engine.detect_breakout_setup(
            master_score, weighted_rsi, current_price, support, resistance,
            weighted_adx, self.adx_history.get(symbol, [])
        )
        
        if is_breakout:
            self.notification_handler.send_setup_alert(
                symbol, breakout_direction, 'Breakout', master_score
            )
        
        # Check entry conditions
        supertrend_scores = {
            interval: scores.get('supertrend_score', 50)
            for interval, scores in interval_scores.items()
        }
        
        self.check_entry_signals(
            symbol, master_score, weighted_rsi, weighted_macd, 
            weighted_supertrend, supertrend_scores, current_price,
            support, resistance, high_volume, is_reversal, 
            reversal_direction, swing_low, swing_high, atr, interval_1h
        )
    
    def check_entry_signals(self, symbol, master_score, weighted_rsi, 
                           weighted_macd, weighted_supertrend, supertrend_scores,
                           current_price, support, resistance, high_volume,
                           is_reversal, reversal_direction, swing_low, 
                           swing_high, atr, interval_1h):
        """Check all entry signal conditions"""
        
        # LONG entries
        should_enter_long_breakout, _ = self.trading_engine.check_long_entry_breakout(
            master_score, supertrend_scores, current_price, resistance, high_volume
        )
        
        if should_enter_long_breakout:
            self.execute_entry('LONG', 'Breakout', symbol, current_price, 
                             master_score, weighted_rsi, swing_low, swing_high, 
                             atr, interval_1h)
            return
        
        should_enter_long_reversal, _ = self.trading_engine.check_long_entry_reversal(
            reversal_direction if is_reversal else None, master_score,
            weighted_macd, current_price, support
        )
        
        if should_enter_long_reversal:
            self.execute_entry('LONG', 'Reversal', symbol, current_price,
                             master_score, weighted_rsi, swing_low, swing_high,
                             atr, interval_1h)
            return
        
        # SHORT entries
        should_enter_short_breakout, _ = self.trading_engine.check_short_entry_breakout(
            master_score, supertrend_scores, current_price, support, high_volume
        )
        
        if should_enter_short_breakout:
            self.execute_entry('SHORT', 'Breakout', symbol, current_price,
                             master_score, weighted_rsi, swing_low, swing_high,
                             atr, interval_1h)
            return
        
        should_enter_short_reversal, _ = self.trading_engine.check_short_entry_reversal(
            reversal_direction if is_reversal else None, master_score,
            weighted_macd, current_price, resistance
        )
        
        if should_enter_short_reversal:
            self.execute_entry('SHORT', 'Reversal', symbol, current_price,
                             master_score, weighted_rsi, swing_low, swing_high,
                             atr, interval_1h)
    
    def execute_entry(self, direction, setup_type, symbol, entry_price, 
                     master_score, weighted_rsi, swing_low, swing_high, 
                     atr, interval_1h):
        """Execute entry signal"""
        print(f"\n  🚀 ENTRY SIGNAL: {direction} {setup_type}")
        
        supertrend_1h = interval_1h.get('supertrend_score', 50)
        
        stop_loss = self.trading_engine.calculate_stop_loss(
            direction, entry_price, swing_low, swing_high, atr, supertrend_1h
        )
        
        target = self.trading_engine.calculate_target_price(
            direction, entry_price, stop_loss
        )
        
        position_size = self.trading_engine.calculate_position_size(
            self.settings['account_balance'], entry_price, stop_loss
        )
        
        print(f"  💰 Entry: ${entry_price:.2f}")
        print(f"  🛑 Stop Loss: ${stop_loss:.2f}")
        print(f"  🎯 Target: ${target:.2f}")
        
        position_id = self.position_manager.open_position(
            symbol, direction, entry_price, stop_loss, target,
            position_size, setup_type
        )
        
        self.trading_engine.last_trade_time[symbol] = time.time()
        
        self.notification_handler.send_entry_notification(
            symbol, direction, setup_type, entry_price, stop_loss,
            target, master_score, weighted_rsi
        )
    
    def check_risk_limits(self, symbol):
        """Check all risk management limits"""
        
        limit_reached, daily_pnl = self.position_manager.check_daily_loss_limit(
            self.settings['account_balance'], limit_percent=4
        )
        
        if limit_reached:
            print(f"  🛑 Daily loss limit reached: ${daily_pnl:.2f}")
            self.notification_handler.send_risk_warning(
                'DAILY_LOSS_LIMIT', {'daily_pnl': daily_pnl, 'limit_percent': 4}
            )
            return False
        
        if self.position_manager.count_open_positions() >= 3:
            return False
        
        if self.position_manager.count_trades_last_hour() >= 2:
            return False
        
        return True
