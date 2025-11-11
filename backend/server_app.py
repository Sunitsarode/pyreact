# ============================================
# backend/server_app.py
# Flask + WebSocket Server with SMA Crossover Detection
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
    get_candles, get_latest_scores, get_latest_score, get_db_path, sanitize_interval,
    get_indicator_scores_history
)
from data_fetcher import fetch_market_data, fetch_market_data_with_timestamps, fetch_current_price
from indicators import calculate_all_scores, calculate_sma_on_scores, detect_sma_crossover
from notifications import send_notification

# ============================================
# CLI Argument Parsing
# ============================================
parser = argparse.ArgumentParser(description='Live Analyser Backend Server')
parser.add_argument('--config', type=str, default='../settings.json', 
                    help='Path to settings JSON file (default: settings.json)')
args = parser.parse_args()

config_file = args.config

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
except FileNotFoundError:
    print(f"❌ Error: Config file '{config_file}' not found!")
    print(f"💡 Usage: python server_app.py --config your_settings.json")
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

# Initialize databases for all symbols
print(f"\n{'='*60}")
print(f"🗄️  Initializing databases...")
print(f"{'='*60}")
for symbol in settings['symbols']:
    init_db(symbol, settings['intervals'])
    print(f"  ✅ {symbol}: db/{symbol}.sqlite")

# Alert tracking
last_alert_time = {}
last_crossover_state = {}  # Track last crossover to avoid duplicate alerts

def update_symbol_data(symbol):
    """Fetch data, calculate scores, and store in the database for a single symbol."""
    print(f"\n{'='*50}")
    print(f"📊 Updating {symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    interval_scores = {}
    current_price = fetch_current_price(symbol)
    print(f"  💰 Current price: {current_price}")
    current_timestamp = int(time.time())
    
    for interval in settings['intervals']:
        candles_needed = settings['candlesPerInterval'].get(interval, 100)
        max_candles = settings['maxCandlesStored'].get(interval, 100)
        
        candles_with_ts = fetch_market_data_with_timestamps(symbol, interval, candles_needed)
        
        if candles_with_ts:
            save_candles(symbol, interval, candles_with_ts, max_candles)
            
            data = fetch_market_data(symbol, interval, candles_needed)
            
            if data:
                scores = calculate_all_scores(data, interval)
                interval_scores[interval] = scores
                
                print(f"  ✅ {interval}: Score = {scores['total_score']:.1f} | S/R = {scores['support']:.2f} / {scores['resistance']:.2f}")

    if interval_scores:
        weights = settings['timeframeWeights']
        weighted_total = 0
        total_weight = 0
        
        for interval, scores in interval_scores.items():
            weight = weights.get(interval, 0)
            weighted_total += scores['total_score'] * weight
            total_weight += weight
        
        final_score = weighted_total / total_weight if total_weight > 0 else 0
        
        scores_data = {
            'timestamp': current_timestamp,
            'weighted_total_score': round(final_score, 2),
            'intervals': {}
        }
        
        for interval, scores in interval_scores.items():
            scores_data['intervals'][interval] = {
                'total_score': scores['total_score'],
                'support': scores['support'],
                'resistance': scores['resistance'],
                'rsi_score': scores.get('rsi_score', 0),
                'rsi_value': scores.get('rsi_value', 50),
                'macd_score': scores.get('macd_score', 0),
                'adx_score': scores.get('adx_score', 0),
                'bb_score': scores.get('bb_score', 0),
                'sma_score': scores.get('sma_score', 0),
                'supertrend_score': scores.get('supertrend_score', 0),
                'current_price': scores.get('current_price', 0)
            }
        
        save_indicator_scores(symbol, scores_data)
        
        # Get score history for SMA calculation
        score_history = get_latest_scores(symbol, limit=100)
        
        # Calculate SMAs on weighted scores
        sma_config = settings.get('score_sma', {'fast_period': 9, 'slow_period': 11})
        fast_period = sma_config['fast_period']
        slow_period = sma_config['slow_period']
        
        if len(score_history) >= max(fast_period, slow_period):
            scores_list = [s['weighted_total_score'] for s in score_history]
            fast_sma = calculate_sma_on_scores(scores_list, fast_period)
            slow_sma = calculate_sma_on_scores(scores_list, slow_period)
            
            print(f"  📈 SMA-{fast_period}: {fast_sma:.2f} | SMA-{slow_period}: {slow_sma:.2f}")
            
            # Add SMAs to data for frontend
            scores_data['sma_fast'] = fast_sma
            scores_data['sma_slow'] = slow_sma
            scores_data['sma_fast_period'] = fast_period
            scores_data['sma_slow_period'] = slow_period
        
        # Check for crossover alerts
        check_sma_crossover_alerts(symbol, score_history)
        
        # Check other alerts
        check_breakout_rules(symbol, scores_data)
        
        # Emit to WebSocket
        socketio.emit('score_update', {
            'symbol': symbol,
            'timestamp': current_timestamp,
            'weighted_total_score': final_score,
            'current_price': current_price,
            'intervals': scores_data['intervals'],
            'sma_fast': scores_data.get('sma_fast'),
            'sma_slow': scores_data.get('sma_slow'),
            'sma_fast_period': scores_data.get('sma_fast_period'),
            'sma_slow_period': scores_data.get('sma_slow_period')
        })
        
        print(f"\n  🎯 Final Weighted Score: {final_score:.2f}")
        print(f"  💾 Saved to database: db/{symbol}.sqlite")

def check_and_repopulate_database():
    """Check if the database is empty and prompt the user to repopulate it."""
    print(f"\n{'='*60}")
    print("🕵️  Checking database integrity...")
    print(f"{'='*60}")

    for symbol in settings['symbols']:
        db_path = get_db_path(symbol)
        db_is_empty = not os.path.exists(db_path)

        if not db_is_empty:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if the main candle table has data
                main_interval = settings['intervals'][0]
                safe_interval = sanitize_interval(main_interval)
                cursor.execute(f"SELECT COUNT(*) FROM candles_{safe_interval}")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    db_is_empty = True
            except Exception as e:
                print(f"  ⚠️  Could not check DB for {symbol}, assuming it's empty. Error: {e}")
                db_is_empty = True

        if db_is_empty:
            print(f"\n❓ Database for {symbol} is empty or corrupted.")
            answer = input(f"   Do you want to fetch historical data and calculate indicators for {symbol}? (y/n): ").lower()
            
            if answer == 'y':
                print(f"\n⏳ Repopulating data for {symbol}, please wait...")
                update_symbol_data(symbol)
                print(f"\n✅ Data repopulation for {symbol} complete.")
            else:
                print(f"\nSkipping repopulation for {symbol}.")

def check_breakout_rules(symbol, scores_data):
    """Check if scores trigger any alerts"""
    global last_alert_time
    
    if not settings['notifications']['enabled']:
        return
    
    rules = settings['breakout_rules']
    total_score = scores_data['weighted_total_score']
    
    rsi = 50
    for interval in ['1h', '15m', '5m', '1m', '1d']:
        interval_data = scores_data['intervals'].get(interval, {})
        if 'rsi_value' in interval_data:
            rsi = interval_data['rsi_value']
            break
    
    current_time = time.time()
    cooldown = 300
    
    alerts = []
    
    if total_score > rules['total_score_threshold']:
        alert_key = f"{symbol}_buy"
        if alert_key not in last_alert_time or (current_time - last_alert_time[alert_key]) > cooldown:
            alerts.append({
                'type': 'STRONG_BUY',
                'message': f"🚀 {symbol} STRONG BUY Signal!\nTotal Score: {total_score:.1f}\nRSI: {rsi:.1f}"
            })
            last_alert_time[alert_key] = current_time
    
    elif total_score < -rules['total_score_threshold']:
        alert_key = f"{symbol}_sell"
        if alert_key not in last_alert_time or (current_time - last_alert_time[alert_key]) > cooldown:
            alerts.append({
                'type': 'STRONG_SELL',
                'message': f"⚠️ {symbol} STRONG SELL Signal!\nTotal Score: {total_score:.1f}\nRSI: {rsi:.1f}"
            })
            last_alert_time[alert_key] = current_time
    
    if rsi > rules['rsi_overbought']:
        alert_key = f"{symbol}_overbought"
        if alert_key not in last_alert_time or (current_time - last_alert_time[alert_key]) > cooldown:
            alerts.append({
                'type': 'OVERBOUGHT',
                'message': f"📈 {symbol} RSI Overbought!\nRSI: {rsi:.1f}\nTotal Score: {total_score:.1f}"
            })
            last_alert_time[alert_key] = current_time
    
    elif rsi < rules['rsi_oversold']:
        alert_key = f"{symbol}_oversold"
        if alert_key not in last_alert_time or (current_time - last_alert_time[alert_key]) > cooldown:
            alerts.append({
                'type': 'OVERSOLD',
                'message': f"📉 {symbol} RSI Oversold!\nRSI: {rsi:.1f}\nTotal Score: {total_score:.1f}"
            })
            last_alert_time[alert_key] = current_time
    
    for alert in alerts:
        send_notification(alert['message'], settings)
        socketio.emit('alert', {
            'symbol': symbol,
            'type': alert['type'],
            'message': alert['message'],
            'timestamp': int(time.time())
        })
        print(f"🔔 Alert: {alert['type']} for {symbol}")

def check_sma_crossover_alerts(symbol, score_history):
    """Check for SMA crossover and send alerts"""
    global last_alert_time, last_crossover_state
    
    if not settings['notifications']['enabled']:
        return
    
    # Get SMA periods from settings
    sma_config = settings.get('score_sma', {'fast_period': 9, 'slow_period': 11})
    fast_period = sma_config['fast_period']
    slow_period = sma_config['slow_period']
    
    # Detect crossover
    crossover_signal = detect_sma_crossover(score_history, fast_period, slow_period)
    
    if crossover_signal is None:
        return
    
    # Check if this is a new crossover (different from last state)
    crossover_key = f"{symbol}_sma_crossover"
    if last_crossover_state.get(crossover_key) == crossover_signal:
        return  # Same signal, don't alert again
    
    # Check cooldown
    current_time = time.time()
    cooldown = 300
    
    alert_key = f"{symbol}_crossover_{crossover_signal.lower()}"
    if alert_key in last_alert_time and (current_time - last_alert_time[alert_key]) < cooldown:
        return
    
    # Update state
    last_crossover_state[crossover_key] = crossover_signal
    last_alert_time[alert_key] = current_time
    
    # Get current score and SMAs
    latest_score = score_history[-1]['weighted_total_score']
    scores = [s['weighted_total_score'] for s in score_history]
    fast_sma = calculate_sma_on_scores(scores, fast_period)
    slow_sma = calculate_sma_on_scores(scores, slow_period)
    
    # Create alert
    alert = {
        'type': f'SMA_CROSSOVER_{crossover_signal}',
        'message': f"{'🟢' if crossover_signal == 'BUY' else '🔴'} {symbol} SMA Crossover {crossover_signal}!\n"
                   f"Score: {latest_score:.1f}\n"
                   f"SMA-{fast_period}: {fast_sma:.1f} | SMA-{slow_period}: {slow_sma:.1f}"
    }
    
    send_notification(alert['message'], settings)
    socketio.emit('alert', {
        'symbol': symbol,
        'type': alert['type'],
        'message': alert['message'],
        'timestamp': int(time.time())
    })
    print(f"🔔 SMA Crossover Alert: {crossover_signal} for {symbol}")

def background_worker():
    """Fetch data, calculate scores, SMAs, and store in database"""
    while True:
        try:
            update_interval = settings['updateIntervalMinutes'] * 60
            
            for symbol in settings['symbols']:
                update_symbol_data(symbol)
            
            print("\n✅ Background worker finished update cycle for all symbols.")
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

@app.route('/api/candles/<symbol>/<interval>')
def get_candles_api(symbol, interval):
    limit = int(request.args.get('limit', 100))
    candles = get_candles(symbol, interval, limit)
    return jsonify(candles)

@app.route('/api/scores/<symbol>')
def get_scores_api(symbol):
    score = get_latest_score(symbol)
    return jsonify(score if score else {})

@app.route('/api/scores/<symbol>/history')
def get_scores_history_api(symbol):
    limit = int(request.args.get('limit', 100))
    scores = get_latest_scores(symbol, limit)
    return jsonify(scores)

@app.route('/api/scores/<symbol>/all_intervals')
def get_all_intervals_scores_api(symbol):
    """
    New endpoint to get the latest score breakdown for all intervals.
    This is for the new Indicators Dashboard page.
    """
    score = get_latest_score(symbol)
    if score and 'intervals' in score:
        return jsonify(score['intervals'])
    return jsonify({})

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/api/scores/<symbol>/<interval>/history')
def get_indicator_scores_history_api(symbol, interval):
    print(f"Fetching indicator scores history for {symbol} and {interval}") # DEBUG LOG
    limit = int(request.args.get('limit', 100))
    scores = get_indicator_scores_history(symbol, interval, limit)
    return jsonify(scores)

@app.route('/api/repopulate', methods=['POST'])
def repopulate_data():
    """Endpoint to trigger data repopulation."""
    for symbol in settings['symbols']:
        print(f"Repopulating data for {symbol}...")
        update_symbol_data(symbol)
    return jsonify({"status": "repopulation_started"})

# ============================================
# WebSocket Events
# ============================================

@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected')
    for symbol in settings['symbols']:
        score = get_latest_score(symbol)
        if score:
            emit('score_update', {
                'symbol': symbol,
                'timestamp': score['timestamp'],
                'weighted_total_score': score['weighted_total_score'],
                'intervals': score['intervals']
            })

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client disconnected')

# ============================================
# Server Startup
# ============================================

if __name__ == '__main__':
    # Check and repopulate database if necessary
    check_and_repopulate_database()

    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()
    
    host = settings['api_server']['host']
    port = settings['api_server']['port']
    
    print(f"\n{'='*60}")
    print(f"🚀 Live Analyser Backend Started")
    print(f"{'='*60}")
    print(f"📁 Config File: {config_file}")
    print(f"🔡 Server: http://{host}:{port}")
    print(f"📊 Symbols: {', '.join(settings['symbols'])}")
    print(f"⏱️  Update Interval: {settings['updateIntervalMinutes']} minutes")
    print(f"🔔 Notifications: {'Enabled' if settings['notifications']['enabled'] else 'Disabled'}")
    print(f"💾 Database: db/{{symbol}}.sqlite")
    print(f"{'='*60}\n")
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
