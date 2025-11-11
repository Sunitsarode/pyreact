# ============================================
# backend/server_app.py
# Flask + WebSocket Server with Database Storage
# ============================================
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import argparse
from datetime import datetime

from db_manager import (
    init_db, save_candles, save_indicator_scores,
    get_candles, get_latest_scores, get_latest_score
)
from data_fetcher import fetch_market_data, fetch_market_data_with_timestamps
from indicators import calculate_all_scores
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

#CORS(app, resources={r"/*": {"origins": "*"}})
#socketio = SocketIO(app, cors_allowed_origins="*")

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

# Enhanced SocketIO with better CORS
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

# Alert tracking (avoid duplicate alerts)
last_alert_time = {}

def check_breakout_rules(symbol, scores_data):
    """Check if scores trigger any alerts"""
    global last_alert_time
    
    if not settings['notifications']['enabled']:
        return
    
    rules = settings['breakout_rules']
    total_score = scores_data['weighted_total_score']
    
    # Get RSI from 1h interval (or any available)
    rsi = 50
    for interval in ['1h', '15m', '5m', '1m', '1d']:
        interval_data = scores_data['intervals'].get(interval, {})
        if 'rsi_value' in interval_data:
            rsi = interval_data['rsi_value']
            break
    
    current_time = time.time()
    cooldown = 300  # 5 minutes between same alerts
    
    alerts = []
    
    # Check total score threshold
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
    
    # Check RSI levels
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
    
    # Send alerts
    for alert in alerts:
        send_notification(alert['message'], settings)
        socketio.emit('alert', {
            'symbol': symbol,
            'type': alert['type'],
            'message': alert['message'],
            'timestamp': int(time.time())
        })
        print(f"🔔 Alert: {alert['type']} for {symbol}")

def background_worker():
    """Fetch data, calculate scores, and store in database"""
    while True:
        try:
            update_interval = settings['updateIntervalMinutes'] * 60
            
            for symbol in settings['symbols']:
                print(f"\n{'='*50}")
                print(f"📊 Updating {symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*50}")
                
                interval_scores = {}
                current_price = 0  # Initialize to 0
                current_timestamp = int(time.time())
                
                # Calculate scores for each timeframe
                for interval in settings['intervals']:
                    candles_needed = settings['candlesPerInterval'].get(interval, 100)
                    max_candles = settings['maxCandlesStored'].get(interval, 100)
                    
                    # Fetch data with timestamps for database
                    candles_with_ts = fetch_market_data_with_timestamps(symbol, interval, candles_needed)
                    
                    if candles_with_ts:
                        # Save candles to database
                        save_candles(symbol, interval, candles_with_ts, max_candles)
                        
                        # Fetch data for calculations (dict format)
                        data = fetch_market_data(symbol, interval, candles_needed)
                        
                        if data:
                            # Calculate scores and support/resistance
                            scores = calculate_all_scores(data, interval)
                            interval_scores[interval] = scores
                            
                            print(f"  ✅ {interval}: Score = {scores['total_score']:.1f} | S/R = {scores['support']:.2f} / {scores['resistance']:.2f}")

                # Determine the most accurate current price by checking shortest intervals first
                for interval in reversed(settings['intervals']):
                    if interval in interval_scores and interval_scores[interval].get('current_price', 0) != 0:
                        current_price = interval_scores[interval]['current_price']
                        break  # Found a valid price, no need to check longer intervals
                
                # Calculate weighted total score across all timeframes
                if interval_scores:
                    weights = settings['timeframeWeights']
                    weighted_total = 0
                    total_weight = 0
                    
                    for interval, scores in interval_scores.items():
                        weight = weights.get(interval, 0)
                        weighted_total += scores['total_score'] * weight
                        total_weight += weight
                    
                    final_score = weighted_total / total_weight if total_weight > 0 else 0
                    
                    # Prepare scores data for database
                    scores_data = {
                        'timestamp': current_timestamp,
                        'weighted_total_score': round(final_score, 2),
                        'intervals': {}
                    }
                    
                    # Add interval data
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
                    
                    # Save to database
                    save_indicator_scores(symbol, scores_data)
                    
                    # Check for alerts
                    check_breakout_rules(symbol, scores_data)
                    
                    # Emit to WebSocket clients
                    socketio.emit('score_update', {
                        'symbol': symbol,
                        'timestamp': current_timestamp,
                        'weighted_total_score': final_score,
                        'current_price': current_price,
                        'intervals': scores_data['intervals']
                    })
                    
                    print(f"\n  🎯 Final Weighted Score: {final_score:.2f}")
                    print(f"  💾 Saved to database: db/{symbol}.sqlite")
            
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
    """Get list of configured symbols"""
    return jsonify(settings['symbols'])

@app.route('/api/settings')
def get_settings():
    """Get current settings"""
    return jsonify(settings)

@app.route('/api/candles/<symbol>/<interval>')
def get_candles_api(symbol, interval):
    """Get candles for a specific symbol and interval"""
    limit = int(request.args.get('limit', 100))
    candles = get_candles(symbol, interval, limit)
    return jsonify(candles)

@app.route('/api/scores/<symbol>')
def get_scores_api(symbol):
    """Get latest score for a symbol"""
    score = get_latest_score(symbol)
    return jsonify(score if score else {})

@app.route('/api/scores/<symbol>/history')
def get_scores_history_api(symbol):
    """Get score history for a symbol"""
    limit = int(request.args.get('limit', 100))
    scores = get_latest_scores(symbol, limit)
    return jsonify(scores)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ============================================
# WebSocket Events
# ============================================

@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected')
    # Send latest scores for all symbols
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
    # Start background worker thread
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