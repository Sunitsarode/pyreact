# ============================================
# backend/notifications.py
# Telegram and Ntfy Notifications
# ============================================
import requests

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
