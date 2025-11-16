from flask import jsonify, request
from datetime import datetime

def register_routes(app, settings, position_manager):
    """Register all API routes"""
    
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
            'account_balance': settings.get('account_balance', 10000)
        })
    
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
