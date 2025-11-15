# ============================================
# backend/server_app.py
# Updated Flask Server with Trading Engine
# ============================================
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import argparse
from datetime import datetime
import os
import sqlite3

from db_manager import (
    init_db, save_candles, save_indicator_scores,
    get_candles, get_latest_scores, get_latest_score, get_db_path, sanitize_interval
)
from data_fetcher import fetch_market_data, fetch_market_data_with_timestamps, fetch_current_price
from indicators import (
    calculate_all_scores, calculate_master_score, calculate_weighted_indicators,
    calculate_sma, calculate_master_score_for_interval
)
from trading_engine import TradingEngine
from position_manager import PositionManager
from notifications import (
    send_notification, format_long_entry_signal, format_short_entry_signal,
    format_exit_signal, format_setup_alert, format_trailing_stop_update,
    format_daily_summary, format_risk_warning
)

# ============================================
# CLI Argument Parsing
# ============================================
parser = argparse.ArgumentParser(description='Live Analyser Backend Server')
parser.add_argument('--config', type=str, default='../settings.json', 
                    help='Path to settings JSON file')
parser.add_argument('--account-balance', type=float, default=10000,
                    help='Account balance for position sizing')
args = parser.parse_args()

config_file = args.config
ACCOUNT_BALANCE = args.account_balance

# ============================================
# Load Settings
# ============================================
print(f"\n{'='*60}")
print(f"📁 Loading configuration from: {config_file}")
print(f"{'='*60}")

try:
    with open(config_file, 'r') as f:
        settings = json.load(f)
    print(f"✅ Configuration loaded successfully!")
    print(f"📊 Symbols: {', '.join(settings['symbols'])}")
    print(f"💰 Account Balance: ${ACCOUNT_BALANCE:,.2f}")
except FileNotFoundError:
    print(f"❌ Error: Config file '{config_file}' not found!")
    exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Error: Invalid JSON in config file: {e}")
    exit(1)

# ============================================
# Flask App Setup
# ============================================
app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Initialize systems
trading_engine = TradingEngine(settings)
position_manager = PositionManager()

# Initialize databases for all symbols
print(f"\n{'='*60}")
print(f"🗄️  Initializing databases...")
print(f"{'='*60}")
for symbol in settings['symbols']:
    init_db(symbol, settings['intervals'])
    print(f"  ✅ {symbol}: db/{symbol}.sqlite")

# ADX history for breakout detection
adx_history = {}

def update_symbol_data(symbol, historical_limit=None):
    """Fetch data, calculate scores, detect signals"""
    print(f"\n{'='*50}")
    print(f"📊 Updating {symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    interval_scores = {}
    current_price = fetch_current_price(symbol)
    print(f"  💰 Current price: ${current_price:.2f}")
    current_timestamp = int(time.time())
    
    # Fetch and calculate scores for each interval
    for interval in settings['intervals']:
        candles_needed = settings['candlesPerInterval'].get(interval, 100)
        max_candles = settings['maxCandlesStored'].get(interval, 100)
        
        # Use historical_limit if provided, otherwise use default candles_needed
        fetch_limit = historical_limit if historical_limit else candles_needed 
        
        candles_with_ts = fetch_market_data_with_timestamps(symbol, interval, fetch_limit)
        
        if candles_with_ts:
            save_candles(symbol, interval, candles_with_ts, max_candles)
            data = fetch_market_data(symbol, interval, fetch_limit)
            
            if data:
                scores = calculate_all_scores(data, interval)
                
                # Calculate master score for this specific interval
                interval_master_score = calculate_master_score_for_interval(scores)
                scores['master_score'] = interval_master_score # Add master_score to interval's scores
                
                interval_scores[interval] = scores
                print(f"  ✅ {interval}: Total Score = {scores['total_score']:.1f}, Master Score = {interval_master_score:.2f}")
    
    if not interval_scores:
        print("  ⚠️  No interval data available")
        return
    
    # Calculate weighted indicators (for overall master score and classification)
    weighted_indicators = calculate_weighted_indicators(interval_scores, settings['timeframeWeights'])
    
    # Calculate overall Master Score and Classification
    overall_master_score, classification = calculate_master_score(weighted_indicators)
    
    print(f"\n  🎯 Overall Master Score: {overall_master_score:.2f} ({classification})")
    print(f"  📊 Weighted RSI: {weighted_indicators['rsi']:.1f}")
    print(f"  📊 Weighted MACD: {weighted_indicators['macd']:.1f}")
    print(f"  📊 Weighted ADX: {weighted_indicators['adx']:.1f}")
    print(f"  📊 Weighted Supertrend: {weighted_indicators['supertrend']:.1f}")
    
    # Retrieve master score history for SMA calculation for each interval
    # This will be a dictionary where keys are intervals and values are lists of master scores
    interval_master_score_histories = {interval: [] for interval in settings['intervals']}
    
    # Fetch enough history for SMA 21 for all intervals
    # Use historical_limit if provided, otherwise use default 50
    score_history_limit = historical_limit if historical_limit else 50
    all_scores_history = get_latest_scores(symbol, limit=score_history_limit) 

    for score_entry in all_scores_history:
        for interval_key, interval_data in score_entry['intervals'].items():
            if 'master_score' in interval_data:
                interval_master_score_histories[interval_key].append(interval_data['master_score'])

    # Calculate SMAs for each interval's master score
    interval_smas = {}
    for interval, history in interval_master_score_histories.items():
        sma9_list = calculate_sma(history, 9)
        sma21_list = calculate_sma(history, 21)
        
        interval_smas[interval] = {
            'master_score_sma9': sma9_list[-1] if sma9_list else None,
            'master_score_sma21': sma21_list[-1] if sma21_list else None
        }

    # Prepare data for saving and emitting
    scores_to_save = {
        'timestamp': current_timestamp,
        'master_score': overall_master_score, # This is the overall master score
        'classification': classification,
        'weighted_indicators': weighted_indicators,
        'intervals': interval_scores, # This now contains interval-specific master_score
        'interval_smas': interval_smas # Add this
    }
    
    # Save scores to database
    save_indicator_scores(symbol, scores_to_save)

    # Emit to frontend
    socketio.emit('score_update', {
        'symbol': symbol,
        'timestamp': current_timestamp,
        'master_score': overall_master_score, # Overall master score
        'classification': classification,
        'weighted_indicators': weighted_indicators,
        'current_price': current_price,
        'intervals': interval_scores, # Contains interval-specific master_score
        'interval_smas': interval_smas # New: interval-specific SMAs
    })
    
    # Update ADX history for breakout detection
    if symbol not in adx_history:
        adx_history[symbol] = []
    adx_history[symbol].append(weighted_indicators['adx'])
    adx_history[symbol] = adx_history[symbol][-10:]  # Keep last 10
    
    # ============================================
    # TRADING LOGIC
    # ============================================
    process_trading_signals(symbol, overall_master_score, weighted_indicators, 
                           interval_scores, current_price)

def process_trading_signals(symbol, master_score, weighted_indicators, 
                           interval_scores, current_price):
    """Process trading signals and manage positions"""
    
    # Check risk management limits
    if not check_risk_limits(symbol):
        return
    
    # Get required data for signal detection
    weighted_rsi = weighted_indicators['rsi']
    weighted_macd = weighted_indicators['macd']
    weighted_adx = weighted_indicators['adx']
    weighted_supertrend = weighted_indicators['supertrend']
    
    # Get 1h interval data for S/R and other calculations
    interval_1h = interval_scores.get('1h', {})
    support = interval_1h.get('support', current_price * 0.98)
    resistance = interval_1h.get('resistance', current_price * 1.02)
    rsi_extreme = interval_1h.get('rsi_extreme', False)
    high_volume = interval_1h.get('high_volume', False)
    atr = interval_1h.get('atr', 0)
    avg_atr_20 = interval_1h.get('avg_atr_20', 0)
    swing_low = interval_1h.get('swing_low', current_price * 0.95)
    swing_high = interval_1h.get('swing_high', current_price * 1.05)
    
    # Check market filters
    can_trade, filter_reason = trading_engine.check_market_filters(
        weighted_adx, atr, avg_atr_20
    )
    
    if not can_trade:
        print(f"  🚫 Market filter: {filter_reason}")
        return
    
    # Check existing positions and manage exits
    open_positions = position_manager.get_open_positions(symbol)
    
    for position in open_positions:
        # Check exit conditions
        should_exit, exit_reason = trading_engine.check_exit_conditions(
            position, current_price, master_score, weighted_supertrend,
            position['entry_time']
        )
        
        if should_exit:
            # Close position
            trade = position_manager.close_position(
                position['id'], current_price, exit_reason
            )
            
            if trade:
                # Send exit notification
                message = format_exit_signal(
                    trade['direction'], symbol, exit_reason,
                    trade['entry_price'], trade['exit_price'],
                    trade['pnl'], trade['pnl_percent']
                )
                send_notification(message, settings)
                
                socketio.emit('trade_closed', {
                    'symbol': symbol,
                    'trade': trade,
                    'timestamp': int(time.time())
                })
        else:
            # Check trailing stop
            new_sl = trading_engine.update_trailing_stop(position, current_price)
            if new_sl:
                old_sl = position['stop_loss']
                position_manager.update_stop_loss(position['id'], new_sl)
                
                # Send trailing stop notification
                message = format_trailing_stop_update(
                    symbol, position['direction'], old_sl, new_sl, current_price
                )
                send_notification(message, settings)
    
    # Don't look for new entries if position exists
    if len(open_positions) > 0:
        return
    
    # Check cooldown
    if not trading_engine.check_cooldown(symbol):
        print(f"  ⏱️  Cooldown active for {symbol}")
        return
    
    # ============================================
    # SIGNAL DETECTION
    # ============================================
    
    # Detect reversal setup
    is_reversal, reversal_direction = trading_engine.detect_reversal_setup(
        master_score, weighted_rsi, rsi_extreme, current_price,
        support, resistance, weighted_adx
    )
    
    if is_reversal:
        print(f"  🔔 Reversal Setup Detected: {reversal_direction}")
        
        # Log setup
        position_manager.log_signal(
            symbol, 'REVERSAL_SETUP', reversal_direction, master_score,
            {'support': support, 'resistance': resistance, 'rsi': weighted_rsi}
        )
        
        # Send setup alert
        message = format_setup_alert(
            symbol, reversal_direction, 'Reversal', master_score,
            'Waiting for confirmation'
        )
        send_notification(message, settings)
    
    # Detect breakout setup
    is_breakout, breakout_direction = trading_engine.detect_breakout_setup(
        master_score, weighted_rsi, current_price, support, resistance,
        weighted_adx, adx_history.get(symbol, [])
    )
    
    if is_breakout:
        print(f"  🔔 Breakout Setup Detected: {breakout_direction}")
        
        # Log setup
        position_manager.log_signal(
            symbol, 'BREAKOUT_SETUP', breakout_direction, master_score,
            {'support': support, 'resistance': resistance}
        )
        
        # Send setup alert
        message = format_setup_alert(
            symbol, breakout_direction, 'Breakout', master_score,
            'Waiting for breakout confirmation'
        )
        send_notification(message, settings)
    
    # ============================================
    # ENTRY SIGNALS
    # ============================================
    
    # Collect supertrend scores for all timeframes
    supertrend_scores = {
        interval: scores.get('supertrend_score', 50)
        for interval, scores in interval_scores.items()
    }
    
    # Check LONG ENTRY - Breakout
    should_enter_long_breakout, reason = trading_engine.check_long_entry_breakout(
        master_score, supertrend_scores, current_price, resistance, high_volume
    )
    
    if should_enter_long_breakout:
        execute_entry_signal(
            symbol, 'LONG', 'Breakout', current_price, master_score,
            weighted_rsi, swing_low, swing_high, atr, interval_1h
        )
        return
    
    # Check LONG ENTRY - Reversal
    should_enter_long_reversal, reason = trading_engine.check_long_entry_reversal(
        reversal_direction if is_reversal else None, master_score,
        weighted_macd, current_price, support
    )
    
    if should_enter_long_reversal:
        execute_entry_signal(
            symbol, 'LONG', 'Reversal', current_price, master_score,
            weighted_rsi, swing_low, swing_high, atr, interval_1h
        )
        return
    
    # Check SHORT ENTRY - Breakout
    should_enter_short_breakout, reason = trading_engine.check_short_entry_breakout(
        master_score, supertrend_scores, current_price, support, high_volume
    )
    
    if should_enter_short_breakout:
        execute_entry_signal(
            symbol, 'SHORT', 'Breakout', current_price, master_score,
            weighted_rsi, swing_low, swing_high, atr, interval_1h
        )
        return
    
    # Check SHORT ENTRY - Reversal
    should_enter_short_reversal, reason = trading_engine.check_short_entry_reversal(
        reversal_direction if is_reversal else None, master_score,
        weighted_macd, current_price, resistance
    )
    
    if should_enter_short_reversal:
        execute_entry_signal(
            symbol, 'SHORT', 'Reversal', current_price, master_score,
            weighted_rsi, swing_low, swing_high, atr, interval_1h
        )
        return

def execute_entry_signal(symbol, direction, setup_type, entry_price, master_score,
                        weighted_rsi, swing_low, swing_high, atr, interval_1h):
    """Execute entry signal and open position"""
    
    print(f"\n  🚀 ENTRY SIGNAL: {direction} {setup_type}")
    
    # Get supertrend value from 1h for stop loss
    supertrend_1h = interval_1h.get('supertrend_score', 50)
    
    # Calculate stop loss
    stop_loss = trading_engine.calculate_stop_loss(
        direction, entry_price, swing_low, swing_high, atr, supertrend_1h
    )
    
    # Calculate target (1:2 R:R)
    target = trading_engine.calculate_target_price(direction, entry_price, stop_loss)
    
    # Calculate position size
    position_size = trading_engine.calculate_position_size(
        ACCOUNT_BALANCE, entry_price, stop_loss
    )
    
    print(f"  💰 Entry: ${entry_price:.2f}")
    print(f"  🛑 Stop Loss: ${stop_loss:.2f}")
    print(f"  🎯 Target: ${target:.2f}")
    print(f"  📊 Position Size: {position_size:.4f}")
    
    # Open position
    position_id = position_manager.open_position(
        symbol, direction, entry_price, stop_loss, target,
        position_size, setup_type
    )
    
    # Update last trade time
    trading_engine.last_trade_time[symbol] = time.time()
    
    # Send entry notification
    if direction == 'LONG':
        message = format_long_entry_signal(
            symbol, setup_type, entry_price, stop_loss, target,
            master_score, weighted_rsi
        )
    else:
        message = format_short_entry_signal(
            symbol, setup_type, entry_price, stop_loss, target,
            master_score, weighted_rsi
        )
    
    send_notification(message, settings)
    
    # Emit to frontend
    socketio.emit('position_opened', {
        'symbol': symbol,
        'direction': direction,
        'setup_type': setup_type,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'target': target,
        'position_size': position_size,
        'master_score': master_score,
        'timestamp': int(time.time())
    })

def check_risk_limits(symbol):
    """Check all risk management limits"""
    
    # Check daily loss limit
    limit_reached, daily_pnl = position_manager.check_daily_loss_limit(
        ACCOUNT_BALANCE, limit_percent=4
    )
    
    if limit_reached:
        print(f"  🛑 Daily loss limit reached: ${daily_pnl:.2f}")
        message = format_risk_warning('DAILY_LOSS_LIMIT', {
            'daily_pnl': daily_pnl,
            'limit_percent': 4
        })
        send_notification(message, settings)
        return False
    
    # Check max concurrent positions
    open_positions = position_manager.count_open_positions()
    if open_positions >= 3:
        print(f"  🛑 Max positions reached: {open_positions}/3")
        return False
    
    # Check trades per hour limit
    trades_last_hour = position_manager.count_trades_last_hour()
    if trades_last_hour >= 2:
        print(f"  🛑 Hourly trade limit reached: {trades_last_hour}/2")
        return False
    
    return True

def background_worker():
    """Fetch data, calculate scores, and detect signals"""
    
    # Initial data load if no scores exist
    print(f"\n{'='*60}")
    print("Checking for initial data load...")
    print(f"{'='*60}")
    initial_load_needed = False
    for symbol in settings['symbols']:
        latest_score = get_latest_score(symbol)
        if latest_score is None:
            print(f"  ⚠️  No existing scores found for {symbol}. Performing initial data load...")
            # Fetch more historical data for initial load (e.g., 200 candles for each interval)
            update_symbol_data(symbol, historical_limit=200) 
            initial_load_needed = True
        else:
            print(f"  ✅ Existing scores found for {symbol}.")
    
    if initial_load_needed:
        print(f"\n{'='*60}")
        print("Initial data load complete. Starting live updates.")
        print(f"{'='*60}")

    while True:
        try:
            update_interval = settings['updateIntervalMinutes'] * 60
            
            for symbol in settings['symbols']:
                update_symbol_data(symbol)
            
            print("\n✅ Background worker finished update cycle")
        except Exception as e:
            print(f"❌ Error in background worker: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n⏰ Sleeping for {settings['updateIntervalMinutes']} minutes...")
        time.sleep(update_interval)

# ============================================
# REST API Endpoints
# ============================================

@app.route('/api/symbols')
def get_symbols():
    return jsonify(settings['symbols'])

@app.route('/api/settings')
def get_settings():
    return jsonify(settings)

@app.route('/api/positions')
def get_positions():
    positions = position_manager.get_open_positions()
    return jsonify(positions)

@app.route('/api/trades')
def get_trades():
    limit = int(request.args.get('limit', 20))
    trades = position_manager.get_recent_trades(limit)
    return jsonify(trades)

@app.route('/api/stats')
def get_stats():
    stats = position_manager.get_trading_stats()
    daily_pnl = position_manager.get_daily_pnl()
    return jsonify({
        'stats': stats,
        'daily_pnl': daily_pnl,
        'account_balance': ACCOUNT_BALANCE
    })

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ============================================
# WebSocket Events
# ============================================

@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client disconnected')

# ============================================
# Server Startup
# ============================================

if __name__ == '__main__':
    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()
    
    host = settings['api_server']['host']
    port = settings['api_server']['port']
    
    print(f"\n{'='*60}")
    print(f"🚀 Live Analyser Trading Bot Started")
    print(f"{'='*60}")
    print(f"📁 Config: {config_file}")
    print(f"🔡 Server: http://{host}:{port}")
    print(f"📊 Symbols: {', '.join(settings['symbols'])}")
    print(f"💰 Account: ${ACCOUNT_BALANCE:,.2f}")
    print(f"⏱️  Update: {settings['updateIntervalMinutes']} minutes")
    print(f"{'='*60}\n")
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
