# ============================================
# backend/position_manager.py
# Position and Trade Management
# ============================================
import sqlite3
import json
import time
from datetime import datetime
import os

def _ensure_db_directory(db_path):
    """Create db directory if it doesn't exist"""
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"✅ Created directory: {db_dir}/")

class PositionManager:
    def __init__(self, db_path='db/positions.sqlite'):
        self.db_path = db_path
        _ensure_db_directory(self.db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize positions and trades database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Open positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                target REAL NOT NULL,
                position_size REAL NOT NULL,
                entry_time INTEGER NOT NULL,
                setup_type TEXT,
                status TEXT DEFAULT 'OPEN'
            )
        ''')
        
        # Closed trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                target REAL NOT NULL,
                position_size REAL NOT NULL,
                entry_time INTEGER NOT NULL,
                exit_time INTEGER NOT NULL,
                exit_reason TEXT,
                pnl REAL NOT NULL,
                pnl_percent REAL NOT NULL,
                setup_type TEXT
            )
        ''')
        
        # Signals history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                direction TEXT,
                master_score REAL,
                timestamp INTEGER NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Position database initialized")
    
    def open_position(self, symbol, direction, entry_price, stop_loss, 
                     target, position_size, setup_type):
        """
        Open a new position
        Returns: position_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        entry_time = int(time.time())
        
        cursor.execute('''
            INSERT INTO positions 
            (symbol, direction, entry_price, stop_loss, target, position_size, 
             entry_time, setup_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
        ''', (symbol, direction, entry_price, stop_loss, target, 
              position_size, entry_time, setup_type))
        
        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Position opened: {symbol} {direction} @ {entry_price}")
        return position_id
    
    def close_position(self, position_id, exit_price, exit_reason):
        """
        Close a position and move to trades history
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get position details
        cursor.execute('SELECT * FROM positions WHERE id = ?', (position_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Calculate P&L
        direction = row[2]
        entry_price = row[3]
        position_size = row[6]
        
        if direction == 'LONG':
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size
        
        pnl_percent = (pnl / (entry_price * position_size)) * 100
        
        exit_time = int(time.time())
        
        # Insert into trades
        cursor.execute('''
            INSERT INTO trades
            (symbol, direction, entry_price, exit_price, stop_loss, target,
             position_size, entry_time, exit_time, exit_reason, pnl, pnl_percent, setup_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row[1], row[2], row[3], exit_price, row[4], row[5], row[6],
              row[7], exit_time, exit_reason, pnl, pnl_percent, row[8]))
        
        # Delete from positions
        cursor.execute('DELETE FROM positions WHERE id = ?', (position_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Position closed: {row[1]} {direction} | P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        return {
            'symbol': row[1],
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': exit_reason
        }
    
    def update_stop_loss(self, position_id, new_stop_loss):
        """Update trailing stop loss"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE positions SET stop_loss = ? WHERE id = ?
        ''', (new_stop_loss, position_id))
        
        conn.commit()
        conn.close()
        print(f"✅ Stop loss updated for position {position_id}: {new_stop_loss}")
    
    def get_open_positions(self, symbol=None):
        """Get all open positions, optionally filtered by symbol"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('SELECT * FROM positions WHERE symbol = ? AND status = "OPEN"', (symbol,))
        else:
            cursor.execute('SELECT * FROM positions WHERE status = "OPEN"')
        
        rows = cursor.fetchall()
        conn.close()
        
        positions = []
        for row in rows:
            positions.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'direction': row['direction'],
                'entry_price': row['entry_price'],
                'stop_loss': row['stop_loss'],
                'target': row['target'],
                'position_size': row['position_size'],
                'entry_time': row['entry_time'],
                'setup_type': row['setup_type']
            })
        
        return positions
    
    def count_open_positions(self):
        """Count total open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM positions WHERE status = "OPEN"')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_recent_trades(self, limit=20):
        """Get recent closed trades"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades 
            ORDER BY exit_time DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'direction': row['direction'],
                'entry_price': row['entry_price'],
                'exit_price': row['exit_price'],
                'pnl': row['pnl'],
                'pnl_percent': row['pnl_percent'],
                'exit_reason': row['exit_reason'],
                'entry_time': row['entry_time'],
                'exit_time': row['exit_time'],
                'setup_type': row['setup_type']
            })
        
        return trades
    
    def get_daily_pnl(self):
        """Calculate today's total P&L"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
        
        cursor.execute('''
            SELECT SUM(pnl) FROM trades 
            WHERE exit_time >= ?
        ''', (today_start,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0
    
    def get_trading_stats(self):
        """Get trading statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total trades
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]
        
        # Winning trades
        cursor.execute('SELECT COUNT(*) FROM trades WHERE pnl > 0')
        winning_trades = cursor.fetchone()[0]
        
        # Total P&L
        cursor.execute('SELECT SUM(pnl) FROM trades')
        total_pnl = cursor.fetchone()[0] or 0
        
        # Average P&L
        cursor.execute('SELECT AVG(pnl) FROM trades')
        avg_pnl = cursor.fetchone()[0] or 0
        
        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        conn.close()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(avg_pnl, 2)
        }
    
    def log_signal(self, symbol, signal_type, direction, master_score, details):
        """Log a trading signal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = int(time.time())
        details_json = json.dumps(details)
        
        cursor.execute('''
            INSERT INTO signals
            (symbol, signal_type, direction, master_score, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, signal_type, direction, master_score, timestamp, details_json))
        
        conn.commit()
        conn.close()
    
    def check_daily_loss_limit(self, account_balance, limit_percent=4):
        """Check if daily loss limit is reached"""
        daily_pnl = self.get_daily_pnl()
        loss_limit = account_balance * (limit_percent / 100)
        
        if daily_pnl < -loss_limit:
            return True, daily_pnl
        
        return False, daily_pnl
    
    def count_trades_last_hour(self):
        """Count trades in the last hour"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        one_hour_ago = int(time.time()) - 3600
        
        cursor.execute('''
            SELECT COUNT(*) FROM trades 
            WHERE entry_time >= ?
        ''', (one_hour_ago,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
