# ============================================
# backend/notifications.py
# Updated Notification Templates
# ============================================
import requests
from datetime import datetime

def send_notification(message, settings):
    """Send notification via configured method"""
    if not settings['notifications']['enabled']:
        return
    
    method = settings['notifications']['method']
    
    if method == 'telegram':
        send_telegram(message, settings)
    elif method == 'ntfy':
        send_ntfy(message, settings)
    else:
        print(f"⚠️  Unknown notification method: {method}")

def send_telegram(message, settings):
    """Send notification via Telegram bot"""
    token = settings['notifications']['telegram']['token']
    chat_id = settings['notifications']['telegram']['chat_id']
    
    if not token or token == 'YOUR_BOT_TOKEN':
        print("⚠️  Telegram not configured")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram notification sent")
        else:
            print(f"❌ Telegram error: {response.text}")
    except Exception as e:
        print(f"❌ Telegram exception: {e}")

def send_ntfy(message, settings):
    """Send notification via ntfy.sh"""
    endpoint = settings['notifications']['ntfy']['endpoint']
    
    if not endpoint or 'your-topic' in endpoint:
        print("⚠️  Ntfy not configured")
        return
    
    try:
        response = requests.post(
            endpoint,
            data=message.encode('utf-8'),
            headers={'Title': 'Live Analyser Alert'},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Ntfy notification sent")
        else:
            print(f"❌ Ntfy error: {response.text}")
    except Exception as e:
        print(f"❌ Ntfy exception: {e}")

# ============================================
# New Notification Templates
# ============================================

def format_long_entry_signal(symbol, setup_type, entry_price, stop_loss, target, 
                             master_score, weighted_rsi):
    """Format LONG entry signal notification"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rr_ratio = round(abs(target - entry_price) / abs(entry_price - stop_loss), 1)
    
    message = f"""🟢 <b>LONG ENTRY SIGNAL</b>
🚀 <b>LONG SETUP DETECTED</b>

<b>Symbol:</b> {symbol}
<b>Type:</b> {setup_type}
<b>Entry:</b> ${entry_price:.2f}
<b>Stop Loss:</b> ${stop_loss:.2f}
<b>Target:</b> ${target:.2f}
<b>Risk:Reward:</b> 1:{rr_ratio}

<b>Master Score:</b> {master_score:.1f}/100
<b>RSI:</b> {weighted_rsi:.1f}
<b>Timeframe Alignment:</b> ✅

⏰ {timestamp}"""
    
    return message

def format_short_entry_signal(symbol, setup_type, entry_price, stop_loss, target,
                              master_score, weighted_rsi):
    """Format SHORT entry signal notification"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rr_ratio = round(abs(target - entry_price) / abs(entry_price - stop_loss), 1)
    
    message = f"""🔴 <b>SHORT ENTRY SIGNAL</b>
📉 <b>SHORT SETUP DETECTED</b>

<b>Symbol:</b> {symbol}
<b>Type:</b> {setup_type}
<b>Entry:</b> ${entry_price:.2f}
<b>Stop Loss:</b> ${stop_loss:.2f}
<b>Target:</b> ${target:.2f}
<b>Risk:Reward:</b> 1:{rr_ratio}

<b>Master Score:</b> {master_score:.1f}/100
<b>RSI:</b> {weighted_rsi:.1f}
<b>Timeframe Alignment:</b> ✅

⏰ {timestamp}"""
    
    return message

def format_exit_signal(direction, symbol, exit_reason, entry_price, exit_price, pnl, pnl_percent):
    """Format EXIT signal notification"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pnl_sign = '+' if pnl >= 0 else ''
    
    message = f"""⚠️ <b>EXIT SIGNAL</b>
⛔ <b>EXIT SIGNAL</b>

<b>Position:</b> {direction}
<b>Symbol:</b> {symbol}
<b>Exit Reason:</b> {exit_reason}
<b>Entry:</b> ${entry_price:.2f}
<b>Exit:</b> ${exit_price:.2f}
<b>P&L:</b> {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_percent:.2f}%)

⏰ {timestamp}"""
    
    return message

def format_setup_alert(symbol, direction, setup_type, master_score, status):
    """Format SETUP alert notification (pre-entry warning)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""🔔 <b>SETUP ALERT</b>
👀 <b>POTENTIAL SETUP FORMING</b>

<b>Symbol:</b> {symbol}
<b>Direction:</b> {direction}
<b>Type:</b> {setup_type}
<b>Master Score:</b> {master_score:.1f}/100
<b>Status:</b> {status}

⏰ {timestamp}"""
    
    return message

def format_trailing_stop_update(symbol, direction, old_sl, new_sl, current_price):
    """Format trailing stop update notification"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""🔄 <b>TRAILING STOP UPDATED</b>

<b>Symbol:</b> {symbol}
<b>Position:</b> {direction}
<b>Current Price:</b> ${current_price:.2f}
<b>Old Stop:</b> ${old_sl:.2f}
<b>New Stop:</b> ${new_sl:.2f}

⏰ {timestamp}"""
    
    return message

def format_daily_summary(stats, daily_pnl):
    """Format daily trading summary"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pnl_sign = '+' if daily_pnl >= 0 else ''
    
    message = f"""📊 <b>DAILY TRADING SUMMARY</b>

<b>Total Trades:</b> {stats['total_trades']}
<b>Winning:</b> {stats['winning_trades']}
<b>Losing:</b> {stats['losing_trades']}
<b>Win Rate:</b> {stats['win_rate']:.1f}%

<b>Daily P&L:</b> {pnl_sign}${daily_pnl:.2f}
<b>Total P&L:</b> ${stats['total_pnl']:.2f}
<b>Avg P&L:</b> ${stats['avg_pnl']:.2f}

⏰ {timestamp}"""
    
    return message

def format_risk_warning(warning_type, details):
    """Format risk management warnings"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if warning_type == 'DAILY_LOSS_LIMIT':
        message = f"""⚠️ <b>RISK WARNING</b>
🛑 <b>DAILY LOSS LIMIT REACHED</b>

<b>Daily P&L:</b> ${details['daily_pnl']:.2f}
<b>Limit:</b> {details['limit_percent']}%

<b>Trading stopped for today</b>

⏰ {timestamp}"""
    
    elif warning_type == 'MAX_POSITIONS':
        message = f"""⚠️ <b>RISK WARNING</b>
🛑 <b>MAX POSITIONS REACHED</b>

<b>Current Positions:</b> {details['current_positions']}
<b>Max Allowed:</b> {details['max_positions']}

<b>Cannot open new positions</b>

⏰ {timestamp}"""
    
    elif warning_type == 'HOURLY_TRADE_LIMIT':
        message = f"""⚠️ <b>RISK WARNING</b>
⏱️ <b>HOURLY TRADE LIMIT REACHED</b>

<b>Trades in last hour:</b> {details['trades_last_hour']}
<b>Max Allowed:</b> {details['max_trades_per_hour']}

<b>Wait before next trade</b>

⏰ {timestamp}"""
    
    else:
        message = f"""⚠️ <b>RISK WARNING</b>
{warning_type}

⏰ {timestamp}"""
    
    return message
