from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
import os
import sys

# Import modules
from config_loader import load_configuration, run_preflight_checks
from db_manager import init_db
from trading_engine import TradingEngine
from position_manager import PositionManager
from notification_handler import NotificationHandler
from signal_processor import SignalProcessor
from data_processor import DataProcessor
from background_worker import BackgroundWorker
from api_routes import register_routes

def main():
    """Main application entry point"""
    
    # Load configuration
    settings, account_balance, config_file = load_configuration()
    settings['account_balance'] = account_balance
    
    # Run preflight checks
    run_preflight_checks(config_file, settings)
    
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )
    
    # Initialize components
    print(f"\n{'='*60}")
    print("🗄️  Initializing components...")
    print(f"{'='*60}")
    
    trading_engine = TradingEngine(settings)
    position_manager = PositionManager()
    notification_handler = NotificationHandler(settings)
    signal_processor = SignalProcessor(
        settings, trading_engine, position_manager, notification_handler
    )
    data_processor = DataProcessor(settings, socketio)
    background_worker = BackgroundWorker(
        settings, data_processor, signal_processor
    )
    
    # Initialize databases
    for symbol in settings['symbols']:
        init_db(symbol, settings['intervals'])
        print(f"  ✅ {symbol}: db/{symbol}.sqlite")
    
    # Register API routes
    register_routes(app, settings, position_manager)
    
    # WebSocket events
    @socketio.on('connect')
    def handle_connect():
        print('🔌 Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('🔌 Client disconnected')
    
    # Start background worker
    print("\n📊 Starting Background Worker...")
    worker_thread = threading.Thread(target=background_worker.run, daemon=True)
    worker_thread.start()
    print("✅ Background worker started")
    
    # Print server info
    host = settings['api_server']['host']
    port = settings['api_server']['port']
    
    print(f"\n{'='*60}")
    print("📡 SERVER CONFIGURATION")
    print(f"{'='*60}")
    print(f"🌐 API Server: http://{host}:{port}")
    print(f"📊 Symbols: {', '.join(settings['symbols'])}")
    print(f"💰 Account: ${account_balance:,.2f}")
    print(f"⏱️  Update: {settings['updateIntervalMinutes']} minutes")
    print(f"📈 Timeframes: {', '.join(settings['intervals'])}")
    print(f"🔔 Notifications: {'Enabled' if settings['notifications']['enabled'] else 'Disabled'}")
    print(f"{'='*60}\n")
    
    print("🎯 Server starting...")
    print("📝 API: http://localhost:5001/api/health")
    print("🌐 Frontend: http://localhost:3000\n")
    
    # Start server
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()