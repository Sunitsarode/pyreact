# ============================================
# 1. backend/config_loader.py
# ============================================
import json
import argparse
import os

def load_configuration():
    """Load and validate configuration"""
    parser = argparse.ArgumentParser(description='Live Analyser Backend Server')
    parser.add_argument('--config', type=str, default='../settings.json', 
                        help='Path to settings JSON file')
    parser.add_argument('--account-balance', type=float, default=10000,
                        help='Account balance for position sizing')
    args = parser.parse_args()
    
    config_file = args.config
    account_balance = args.account_balance
    
    print(f"\n{'='*60}")
    print(f"📁 Loading configuration from: {config_file}")
    print(f"{'='*60}")
    
    try:
        with open(config_file, 'r') as f:
            settings = json.load(f)
        print(f"✅ Configuration loaded successfully!")
        print(f"📊 Symbols: {', '.join(settings['symbols'])}")
        print(f"💰 Account Balance: ${account_balance:,.2f}")
        return settings, account_balance, config_file
    except FileNotFoundError:
        print(f"❌ Error: Config file '{config_file}' not found!")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config file: {e}")
        exit(1)

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask', 'flask_socketio', 'flask_cors', 
        'yfinance', 'pandas', 'pandas_ta', 'numpy', 'requests'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"💡 Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def is_port_available(host, port):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False

def run_preflight_checks(config_file, settings):
    """Run all pre-flight checks"""
    print("\n" + "="*60)
    print("🔍 PRE-FLIGHT CHECKS")
    print("="*60)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        print("❌ Dependency check failed!")
        exit(1)
    print("✅ All dependencies installed")
    
    # Check config file
    print(f"📁 Checking config file: {config_file}")
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        exit(1)
    print("✅ Config file found")
    
    # Check port availability
    api_port = settings['api_server']['port']
    if not is_port_available('0.0.0.0', api_port):
        print(f"❌ Port {api_port} is already in use!")
        print(f"💡 Stop the other process or change port in settings.json")
        exit(1)
    print(f"✅ Port {api_port} available")
    
    print("="*60)
    print("✅ All pre-flight checks passed!")
    print("="*60)

