# ============================================
# backend/db_manager.py
# Database Manager with Auto-Cleanup
# ============================================
import sqlite3
import json
import os
from datetime import datetime

DB_DIR = 'db'

def ensure_db_directory():
    """Create db directory if it doesn't exist"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"✅ Created directory: {DB_DIR}/")

def get_db_path(symbol):
    """Get database path for a symbol"""
    ensure_db_directory()
    # Replace special characters in symbol for filename
    safe_symbol = symbol.replace('/', '-').replace('^', '')
    return os.path.join(DB_DIR, f"{safe_symbol}.sqlite")

def get_connection(symbol):
    """Get database connection for a symbol"""
    db_path = get_db_path(symbol)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_interval(interval):
    """Convert interval to safe table name"""
    return interval.replace('m', 'min').replace('h', 'hr').replace('d', 'day')

def init_db(symbol, intervals):
    """Initialize database tables for a symbol"""
    conn = get_connection(symbol)
    cursor = conn.cursor()
    
    # Create candle tables for each interval
    for interval in intervals:
        safe_interval = sanitize_interval(interval)
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS candles_{safe_interval} (
                timestamp INTEGER PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )
        ''')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_candles_{safe_interval}_ts ON candles_{safe_interval}(timestamp DESC)')
    
    # Create indicators_score table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicators_score (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER UNIQUE,
            intervals_json TEXT,
            master_score REAL,
            classification TEXT,
            weighted_indicators_json TEXT,
            interval_smas_json TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicators_ts ON indicators_score(timestamp DESC)')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized for {symbol}")

def save_candles(symbol, interval, candles_data, max_candles):
    """
    Save candles to database and cleanup old data
    candles_data: list of dicts with keys [timestamp, open, high, low, close, volume]
    """
    if not candles_data:
        return
    
    conn = get_connection(symbol)
    cursor = conn.cursor()
    safe_interval = sanitize_interval(interval)
    
    # Insert or replace candles
    for candle in candles_data:
        cursor.execute(f'''
            INSERT OR REPLACE INTO candles_{safe_interval}
            (timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            candle['timestamp'],
            candle['open'],
            candle['high'],
            candle['low'],
            candle['close'],
            candle['volume']
        ))
    
    conn.commit()
    
    # Cleanup old candles
    cleanup_old_candles(cursor, safe_interval, max_candles)
    
    conn.commit()
    conn.close()

def cleanup_old_candles(cursor, safe_interval, max_candles):
    """Delete oldest candles to keep only max_candles"""
    cursor.execute(f'SELECT COUNT(*) FROM candles_{safe_interval}')
    total = cursor.fetchone()[0]
    
    if total > max_candles:
        delete_count = total - max_candles
        cursor.execute(f'''
            DELETE FROM candles_{safe_interval}
            WHERE timestamp IN (
                SELECT timestamp FROM candles_{safe_interval}
                ORDER BY timestamp ASC
                LIMIT ?
            )
        ''', (delete_count,))
        print(f"  🗑️  Deleted {delete_count} old candles from {safe_interval}")

def save_indicator_scores(symbol, scores_dict, max_scores=500):
    """
    Save indicator scores to database
    scores_dict: {
        'timestamp': int,
        'intervals': { ... },
        'master_score': float,
        'classification': str,
        'weighted_indicators': dict,
        'interval_smas': dict # New field
    }
    """
    conn = get_connection(symbol)
    cursor = conn.cursor()
    
    timestamp = scores_dict['timestamp']
    intervals_json = json.dumps(scores_dict.get('intervals', {}))
    master_score = scores_dict.get('master_score', 0)
    classification = scores_dict.get('classification', 'NEUTRAL')
    weighted_indicators_json = json.dumps(scores_dict.get('weighted_indicators', {}))
    interval_smas_json = json.dumps(scores_dict.get('interval_smas', {})) # New line
    
    cursor.execute('''
        INSERT OR REPLACE INTO indicators_score
        (timestamp, intervals_json, master_score, classification, weighted_indicators_json, interval_smas_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, intervals_json, master_score, classification, weighted_indicators_json, interval_smas_json))
    
    conn.commit()    
    # Cleanup old scores
    cursor.execute('SELECT COUNT(*) FROM indicators_score')
    total = cursor.fetchone()[0]
    
    if total > max_scores:
        delete_count = total - max_scores
        cursor.execute('''
            DELETE FROM indicators_score
            WHERE id IN (
                SELECT id FROM indicators_score
                ORDER BY timestamp ASC
                LIMIT ?
            )
        ''', (delete_count,))
        print(f"  🗑️  Deleted {delete_count} old indicator scores")
    
    conn.commit()
    conn.close()

def get_candles(symbol, interval, limit=100):
    """Get candles for charting"""
    conn = get_connection(symbol)
    cursor = conn.cursor()
    safe_interval = sanitize_interval(interval)
    
    cursor.execute(f'''
        SELECT * FROM candles_{safe_interval}
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to list of dicts (reverse for chronological order)
    candles = []
    for row in reversed(rows):
        candles.append({
            'timestamp': row['timestamp'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        })
    
    return candles

def get_latest_scores(symbol, limit=100):
    """Get latest indicator scores"""
    conn = get_connection(symbol)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, master_score, classification, intervals_json, weighted_indicators_json, interval_smas_json
        FROM indicators_score
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to list of dicts (reverse for chronological order)
    scores = []
    for row in reversed(rows):
        scores.append({
            'timestamp': row['timestamp'],
            'master_score': row['master_score'],
            'classification': row['classification'],
            'intervals': json.loads(row['intervals_json']),
            'weighted_indicators': json.loads(row['weighted_indicators_json'] or '{}'),
            'interval_smas': json.loads(row['interval_smas_json'] or '{}')
        })
    
    return scores
def get_latest_score(symbol):
    """Get the most recent score"""
    scores = get_latest_scores(symbol, limit=1)
    return scores[0] if scores else None

def get_indicator_scores_history(symbol, interval, limit=100):
    """Get historical indicator scores for a specific interval."""
    conn = get_connection(symbol)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, intervals_json
        FROM indicators_score
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    scores = []
    for row in reversed(rows):
        intervals = json.loads(row['intervals_json'])
        if interval in intervals:
            interval_scores = intervals[interval]
            score_data = {
                'timestamp': row['timestamp'],
                'rsi_score': interval_scores.get('rsi_score', 0),
                'macd_score': interval_scores.get('macd_score', 0),
                'bb_score': interval_scores.get('bb_score', 0),
                'adx_score': interval_scores.get('adx_score', 0),
                'supertrend_score': interval_scores.get('supertrend_score', 0),
                'sma_score': interval_scores.get('sma_score', 0),
            }
            scores.append(score_data)
            
    return scores
